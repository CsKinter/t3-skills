# -*- coding: utf-8 -*-
"""
WRITEBACK DE CAPACIDADES TERMICAS  (ComPython para PowerFactory)

Aplica el paquete exportado por la app (Opciones -> Exportar writeback).

Por cada linea confirmada (TypLne, TypTow directo o acoplamiento ElmTow):
  1) Copia su TypLne (o TypCon + TypTow) -> Equipment Type Library\\Capacidades_IT_<sufijo>\\<linea>_<sufijo>
  2) Crea una ChaMat  -> Characteristics\\Capacidades_IT_<sufijo>\\<linea>_<sufijo>
     con escalas propias Sol_<sufijo> (SS, CS) y Temperatura_<sufijo> (15, 25, 35)
     y los valores IT en kA. El sline.ChaRef del TypLne/TypCon copiado apunta a esa ChaMat;
     en TypTow, la copia del TypTow apunta (pcond_c) al TypCon copiado.
  3) En la variation "Capacidades IT_<sufijo>" cambia ElmLne.typ_id al TypLne/TypTow copiado,
     o, en acoplamientos, ElmTow.pGeo al TypTow copiado (cambian todos los circuitos acoplados).

Nunca modifica tipos, caracteristicas ni escalas existentes: solo crea objetos nuevos.
El puntero a la caracteristica vive dentro del tipo (biblioteca), que las variations
no registran; por eso se copia el tipo y solo se cambia typ_id (red) dentro del stage.

Uso:
  - Ejecutar: se abre una ventana para elegir el paquete, la fecha/hora del stage,
    el nombre de la variation y el modo (Simular / Aplicar).
  - Simular: solo lee y reporta que haria (no crea nada). Revisar el reporte y
    volver a ejecutar en modo Aplicar.
  - Sin ventana (USE_DIALOG = False) se usan PACKAGE_PATH, STAGE_DATETIME y DRY_RUN.
  - Verificar con extraer_capacidades_termicas.py: con la variation activa deben
    aparecer los valores IT; con la variation inactiva, los originales.
"""
import csv
import glob
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import powerfactory as pf

# =========================================================
# CONFIGURACION
# =========================================================
USE_DIALOG = True           # Ventana de configuracion; con False se usan los valores de abajo.
PACKAGE_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "writeback_IT2609.json")
DRY_RUN = True
STAGE_DATETIME = "01-01-2026 00:00"   # dd-mm-aaaa HH:MM. El study time se ajusta a esta fecha.
STAGE_TIME = None           # tAcTime calculado desde STAGE_DATETIME o la ventana.
TOL_KA = 1e-6               # Tolerancia para confirmar que PF sigue con los valores comparados.

VARIATION_NAME = None       # Se toma del paquete: "Capacidades IT_<sufijo>".

app = pf.GetApplication()
if app is None:
    raise RuntimeError("No hay aplicacion de PowerFactory")


def log(m):
    app.PrintPlain(str(m))


def warn(m):
    app.PrintWarn(str(m))


def err(m):
    app.PrintError(str(m))


# =========================================================
# UTILERIA
# =========================================================
def is_empty(value):
    return value is None or str(value).strip() == ""


def safe_name(name):
    for ch in '\\/:*?"<>|':
        name = str(name).replace(ch, "-")
    return name.strip()


def clase(obj):
    try:
        return obj.GetClassName() if obj is not None else ""
    except Exception:
        return ""


def ruta(obj):
    try:
        return obj.GetFullName() if obj is not None else ""
    except Exception:
        return ""


def get_attr(obj, attr, default=None):
    if obj is None:
        return default
    try:
        value = obj.GetAttribute(attr)
    except Exception:
        return default
    return default if value is None else value


def find_child(parent, name, cls):
    if parent is None:
        return None
    try:
        found = parent.GetContents("%s.%s" % (name, cls))
    except Exception:
        found = []
    return found[0] if found else None


def get_or_create(parent, cls, name):
    found = find_child(parent, name, cls)
    if found is not None:
        return found, False
    obj = parent.CreateObject(cls, name)
    if obj is None:
        raise Exception("No se pudo crear %s '%s' en %s" % (cls, name, ruta(parent)))
    return obj, True


def parent_of_class(obj, cls):
    p = obj
    for _ in range(30):
        if p is None:
            return None
        if clase(p) == cls:
            return p
        try:
            p = p.GetParent()
        except Exception:
            return None
    return None


def characteristic_de(owner, parametro="sline"):
    """Igual que el extractor: la ChaMat referenciada por <parametro>.ChaRef dentro del tipo."""
    try:
        refs = owner.GetContents("%s.ChaRef" % parametro) or []
    except Exception:
        refs = []
    if not refs:
        try:
            refs = [r for r in (owner.GetContents("*.ChaRef") or []) if str(r.loc_name) == parametro]
        except Exception:
            refs = []
    return get_attr(refs[0], "typ_id", None) if refs else None


def as_list(raw):
    return list(raw) if isinstance(raw, (list, tuple)) else ([] if raw is None else [raw])


def conductors(typtow):
    """TypCon distintos referenciados en pcond_c (mismo criterio que el extractor)."""
    out = []
    for obj in as_list(get_attr(typtow, "pcond_c", None)):
        if clase(obj) == "TypCon" and obj not in out:
            out.append(obj)
    return out


def same_matrix(a, b):
    try:
        return len(a) == len(b) and all(
            len(ra) == len(rb) and all(abs(float(x) - float(y)) <= TOL_KA for x, y in zip(ra, rb))
            for ra, rb in zip(a, b))
    except Exception:
        return False


# =========================================================
# FECHAS POWERFACTORY
# =========================================================
def get_stage_time(date_value):
    """
    Convierte fechas a tAcTime. Acepta:
      - 'ago-27', 'sept-27'  (mes-año, día 1)
      - '2027-08' / '08-2027' (año-mes / mes-año, día 1)
      - '01-11-2026'          (día-mes-año)
      - 46327                 (número de serie de Excel: días desde 30-12-1899)
      - datetime / Timestamp
    """
    dic_months = {
        "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
        "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
    }

    epoch_reference = datetime(1969, 12, 31, 21, 0, 0, tzinfo=timezone.utc)

    if is_empty(date_value):
        raise ValueError("Fecha vacía")

    day = 1

    if isinstance(date_value, datetime):
        year, month, day = date_value.year, date_value.month, date_value.day
    else:
        raw = str(date_value).strip()

        try:
            serial = float(raw.replace(",", "."))
        except ValueError:
            serial = None

        if serial is not None:
            if not (20000 <= serial <= 80000):
                raise ValueError(
                    f"Número '{raw}' fuera del rango de fechas Excel "
                    f"(20000-80000 ~ años 1954-2119)")
            d = datetime(1899, 12, 30) + timedelta(days=int(serial))
            year, month, day = d.year, d.month, d.day
        else:
            s = raw.lower().replace(".", "")

            if "-" in s:
                parts = s.split("-")
            elif "/" in s:
                parts = s.split("/")
            else:
                raise ValueError(f"Formato de fecha no reconocido: {date_value}")

            if len(parts) < 2:
                raise ValueError(f"Formato de fecha no reconocido: {date_value}")

            a, b = parts[0].strip(), parts[1].strip()
            c = parts[2].strip() if len(parts) >= 3 else ""

            if a.isdigit() and b.isdigit() and c.isdigit() and len(c) == 4:
                day, month, year = int(a), int(b), int(c)
            elif a.isdigit() and len(a) == 4:
                year, month = int(a), int(b)
            elif b.isdigit() and len(b) == 4 and a.isdigit():
                month, year = int(a), int(b)
            else:
                if a not in dic_months:
                    raise ValueError(f"Mes no reconocido: '{a}' en fecha '{date_value}'")
                month = dic_months[a]
                year = int(b)
                if year < 100:
                    year += 2000

    target_date = datetime(int(year), int(month), int(day), 0, 0, 0,
                           tzinfo=timezone(timedelta(hours=-1)))

    return int((target_date - epoch_reference).total_seconds())


def set_study_time(stage_time):
    try:
        study_case = app.GetActiveStudyCase()
    except Exception:
        study_case = None

    if study_case is None:
        log("[AVISO] No se pudo obtener el Study Case activo. No se ajustó Study Time.")
        return False

    try:
        ierr = study_case.SetStudyTime(float(stage_time))
        if ierr not in (0, None):
            log(f"[AVISO] SetStudyTime retornó código {ierr}. Se continúa.")
        return True
    except Exception as e:
        log(f"[AVISO] No se pudo ejecutar SetStudyTime({stage_time}): {e}")
        return False


# =========================================================
# VARIATION Y EXPANSION STAGES
# =========================================================
def get_or_create_variation():
    scheme_folder = app.GetProjectFolder("scheme")

    if scheme_folder is None:
        raise Exception("No se encontró el folder 'scheme' en el proyecto.")

    variation, created = get_or_create(scheme_folder, "IntScheme", VARIATION_NAME)

    log(f"[OK] Variation {'creada' if created else 'existente reutilizada'}: {variation.GetFullName()}")

    ierr = variation.Activate()

    if ierr not in (0, 1, None):
        raise Exception(f"No se pudo activar la variation '{VARIATION_NAME}'. Activate() retornó {ierr}")

    # Activate() puede retornar 1 tanto si ya estaba activa como si falló:
    # se verifica contra la lista real de variations activas.
    try:
        active_variations = app.GetActiveNetworkVariations()
    except Exception:
        active_variations = None

    if active_variations is not None and variation not in active_variations:
        raise Exception(
            f"La variation '{VARIATION_NAME}' NO quedó activa "
            f"(Activate retornó {ierr}). Se aborta para no registrar "
            f"cambios en otra variation.")

    log(f"[OK] Variation activa: {variation.GetFullName()}")

    return variation


def get_or_create_stage(variation, prj_name, stage_time):
    stage_name = safe_name(prj_name)

    stage, created = get_or_create(variation, "IntSstage", stage_name)

    try:
        stage.tAcTime = stage_time
    except Exception as e:
        raise Exception(f"No se pudo asignar tAcTime al stage '{stage_name}': {e}")

    for attr in ["outserv", "iExclude", "iExcluded", "iexclude"]:
        try:
            setattr(stage, attr, 0)
        except Exception:
            pass

    log(f"[OK] Expansion Stage {'creado' if created else 'existente actualizado'}: {stage_name}")

    return stage


def get_current_recording_stage(variation):
    """
    Devuelve el recording stage actual si la versión de PF expone la API,
    o None si no se puede determinar.
    """
    for owner in (app, variation):
        fn = getattr(owner, "GetRecordingStage", None)
        if fn is not None:
            try:
                return fn()
            except Exception:
                pass
    return None


def prepare_stage_for_recording(variation, stage, stage_time):
    """
    Fuerza que 'stage' sea el recording stage.

    PowerFactory registra los cambios en UN solo stage global: el stage
    activo con tAcTime más reciente <= study time, considerando TODAS las
    variations activas. Por eso se activa el stage explícitamente y se
    verifica, abortando si no quedó registrando.
    """
    set_study_time(stage_time)

    try:
        ierr = stage.Activate()
    except Exception as e:
        raise Exception(f"No se pudo activar el stage '{stage.loc_name}': {e}")

    # 1 -> activación con avisos; 16 -> PF ajustó el study time. La confirmación
    # real la hace verify_recording_with_probe().
    if ierr not in (0, 1, 16, None):
        raise Exception(
            f"El stage '{stage.loc_name}' no quedó como recording stage "
            f"(Activate retornó {ierr}). Se aborta.")

    if ierr in (1, 16):
        log(f"[AVISO] Activate() retornó {ierr} en '{stage.loc_name}' "
            f"(activación con avisos). Se verificará el recording stage.")

    recording = get_current_recording_stage(variation)

    if recording is not None and recording != stage:
        try:
            rec_name = recording.GetFullName()
        except Exception:
            rec_name = getattr(recording, "loc_name", "desconocido")
        raise Exception(
            f"El recording stage actual es '{rec_name}', no "
            f"'{stage.loc_name}'. Se aborta para no registrar "
            f"cambios donde no corresponde.")

    log(f"[OK] Stage de registro activo: {stage.loc_name}")


def get_owner_stage(obj):
    """IntSstage donde está almacenado físicamente el objeto, o None."""
    p = obj

    for _ in range(30):
        if p is None:
            return None
        try:
            if p.GetClassName() == "IntSstage":
                return p
        except Exception:
            return None
        try:
            p = p.GetParent()
        except Exception:
            return None

    return None


PROBE_NAME = "__chk_recording__"


def stage_entries(stage):
    """Nombres completos de lo que el stage tiene registrado."""
    try:
        return {ruta(o) for o in (stage.GetContents("*", 1) or [])}
    except Exception:
        return set()


def verify_recording_with_probe(grid, stage):
    """
    Crea un objeto de prueba en la red, revisa en qué stage lo registró PF
    y lo elimina. Si no se puede confirmar que cayó en 'stage', aborta ANTES
    de crear objetos reales.

    En PF el objeto creado dentro de una variation informa la red como padre,
    así que además de la cadena de padres se revisa el contenido del stage.
    """
    before = stage_entries(stage)
    probe = None

    try:
        probe = grid.CreateObject("IntFolder", PROBE_NAME)
    except Exception:
        probe = None

    if probe is None:
        raise Exception("No se pudo crear el objeto de prueba; no se puede confirmar el recording stage.")

    owner = get_owner_stage(probe)
    added = sorted(stage_entries(stage) - before)
    parents = []
    p = probe
    for _ in range(8):
        try:
            p = p.GetParent()
        except Exception:
            p = None
        if p is None:
            break
        parents.append("%s.%s" % (getattr(p, "loc_name", "?"), clase(p)))

    try:
        probe.Delete()
    except Exception:
        pass

    leftovers = [n for n in stage_entries(stage) if PROBE_NAME in n]
    if leftovers:
        warn("[AVISO] Quedó un registro del objeto de prueba en el stage: %s" % leftovers)

    if owner is None and any(PROBE_NAME in n for n in added):
        owner = stage

    if owner is None:
        raise Exception(
            "Verificación del recording stage no concluyente. Se aborta sin modificar nada.\n"
            "  Padres del objeto de prueba: %s\n"
            "  Entradas del stage antes/después: %d / %d; nuevas: %s"
            % (" <- ".join(parents) or "ninguno", len(before), len(before) + len(added), added[:10] or "ninguna"))

    if owner != stage:
        try:
            owner_name = owner.GetFullName()
        except Exception:
            owner_name = getattr(owner, "loc_name", "desconocido")
        raise Exception(
            f"PF está registrando en '{owner_name}', no en el stage "
            f"'{stage.loc_name}'. Abortado antes de crear objetos.")

    log(f"[OK] Verificado: los cambios se registran en '{stage.loc_name}'.")


# =========================================================
# CARPETAS DE BIBLIOTECA
# =========================================================
def characteristics_folder():
    folder = None
    try:
        folder = app.GetProjectFolder("chars")
    except Exception:
        folder = None
    if folder is None:
        oplib = app.GetProjectFolder("oplib")
        folder = find_child(oplib, "Characteristics", "IntPrjfolder")
    if folder is None:
        raise Exception("No se encontró Operational Library\\Characteristics.")
    return folder


def scales_folder(chars):
    folders = chars.GetContents("*.IntScales") or []
    named = [f for f in folders if str(f.loc_name) == "Scale"]
    if not (named or folders):
        raise Exception("No se encontró la carpeta de escalas (IntScales) en Characteristics.")
    return (named or folders)[0]


def find_characteristic(chars, path):
    if not path:
        return None
    for cha in chars.GetContents("*.ChaMat", 1) or []:
        if ruta(cha) == path:
            return cha
    return None


def get_or_create_scale(folder, name, cases):
    scale, created = get_or_create(folder, "TriDisc", name)
    current = [str(c).strip() for c in (get_attr(scale, "cases", []) or [])]
    if created:
        scale.SetAttribute("cases", list(cases))
        current = [str(c).strip() for c in (get_attr(scale, "cases", []) or [])]
    if current != list(cases):
        raise Exception("La escala '%s' tiene casos %s; se esperaba %s." % (name, current, list(cases)))
    log("[OK] Escala %s: %s (%s)" % ("creada" if created else "existente", name, ", ".join(cases)))
    return scale


# =========================================================
# PLAN (solo lectura)
# =========================================================
def index_lines():
    return {ruta(line): line for line in (app.GetCalcRelevantObjects("*.ElmLne") or [])}


def plan_item(item, lines, pkg, folders):
    plan = {"item": item, "status": "omitido", "detail": "", "line": None, "type": None, "tower": None,
            "coupling": None, "cha": None}
    name = item["new_type_name"]

    line = lines.get(item["line"]["path"])
    if line is None:
        plan["detail"] = "Línea no encontrada en las redes activas"
        return plan
    plan["line"] = line

    coupling, tower = item.get("line_coupling"), item.get("tower_type")
    if coupling:
        # Acoplamiento: ElmLne.c_ptow -> ElmTow -> pGeo -> TypTow -> pcond_c -> TypCon.
        tow = next((t for t in as_list(get_attr(line, "c_ptow", None)) if ruta(t) == coupling["path"]), None)
        if tow is None:
            plan["detail"] = "La línea ya no está acoplada a %s" % coupling["name"]
            return plan
        geos = as_list(get_attr(tow, "pGeo", None))
        if any(str(g.loc_name) == name for g in geos):
            plan["status"], plan["detail"] = "ya aplicado", "pGeo de %s ya apunta a %s" % (coupling["name"], name)
            return plan
        match = [g for g in geos if ruta(g) == tower["path"]]
        if not match:
            plan["detail"] = "El TypTow exportado no está en pGeo de %s (tab_Geo no soportado)" % coupling["name"]
            return plan
        plan["coupling"], typ = tow, match[0]
    else:
        typ = get_attr(line, "typ_id", None)
        if typ is None:
            plan["detail"] = "La línea no tiene typ_id"
            return plan
        if str(typ.loc_name) == name:
            plan["status"], plan["detail"] = "ya aplicado", "typ_id ya apunta a " + name
            return plan
    if tower:
        # TypTow -> pcond_c -> TypCon (lleva la capacidad).
        if clase(typ) not in ("TypTow", "TypGeo") or ruta(typ) != tower["path"]:
            plan["detail"] = "El TypTow actual (%s) no es el exportado; volver a extraer y confirmar" % ruta(typ)
            return plan
        cons = conductors(typ)
        if len(cons) != 1 or ruta(cons[0]) != item["rating_object"]["path"]:
            plan["detail"] = "El TypTow tiene %d TypCon distintos o cambió su conductor" % len(cons)
            return plan
        plan["tower"], typ = typ, cons[0]
    elif clase(typ) != "TypLne" or ruta(typ) != item["rating_object"]["path"]:
        plan["detail"] = "El tipo actual (%s) no es el exportado; volver a extraer y confirmar" % ruta(typ)
        return plan
    plan["type"] = typ

    expected = item["expected_pf"]
    cha = characteristic_de(typ)
    if expected["mode"] == "fixed":
        if cha is not None:
            plan["detail"] = "El tipo ahora tiene característica; volver a extraer"
            return plan
        try:
            sline = float(get_attr(typ, "sline"))
        except Exception:
            sline = None
        if sline is None or abs(sline - float(expected["sline_kA"])) > TOL_KA:
            plan["detail"] = "sline cambió desde la extracción (%s kA)" % sline
            return plan
    else:
        if cha is None or ruta(cha) != expected["characteristic_path"]:
            plan["detail"] = "La característica del tipo cambió desde la extracción"
            return plan
        matrix = get_attr(cha, "matrix", None)
        try:
            changed = [c["key"] for c in expected["cells"]
                       if abs(float(matrix[c["row"]][c["column"]]) - float(c["value_kA"])) > TOL_KA]
        except Exception:
            changed = ["matriz ilegible"]
        if changed:
            plan["detail"] = "Valores PF cambiaron desde la extracción: " + ", ".join(changed)
            return plan
        plan["cha"] = cha

    values = item["matrix_kA"]
    if len(values) != len(pkg["rows"]) or any(len(r) != len(pkg["columns"]) or any(
            not isinstance(v, (int, float)) or v <= 0 for v in r) for r in values):
        plan["detail"] = "Matriz IT del paquete inválida"
        return plan

    checks = [("tipo", folders.get("types"), clase(typ)), ("característica", folders.get("chars"), "ChaMat")]
    if tower:
        checks.append(("tipo", folders.get("types"), clase(plan["tower"])))
    for label, folder, cls in checks:
        if find_child(folder, name, cls) is not None:
            plan["detail"] = "Ya existe un %s '%s' en %s; revisar o usar otro sufijo" % (label, name, ruta(folder))
            return plan

    plan["status"] = "listo"
    plan["detail"] = "%s%s -> %s" % ("ElmTow %s · " % coupling["name"] if coupling else "TypTow · " if tower else "",
                                     "capacidad fija" if expected["mode"] == "fixed" else "ChaMat", name)
    if item.get("warnings"):
        plan["detail"] += " | " + "; ".join(item["warnings"])
    return plan


# =========================================================
# APLICAR
# =========================================================
def apply_item(plan, folders, scales, template):
    item, line, typ = plan["item"], plan["line"], plan["type"]
    name = item["new_type_name"]
    base_cha = plan["cha"] or template
    if base_cha is None:
        raise Exception("Sin ChaMat de plantilla para convertir la capacidad fija")

    # Copia de una ChaMat existente: conserva su configuración (uso, unidades);
    # luego se reemplazan escalas y valores.
    new_cha = folders["chars"].AddCopy(base_cha, name)
    if new_cha is None:
        raise Exception("No se pudo copiar la característica")
    new_cha.SetAttribute("scalerow", scales["row"])
    new_cha.SetAttribute("scalecol", scales["col"])
    new_cha.SetAttribute("matrix", item["matrix_kA"])
    if not same_matrix(get_attr(new_cha, "matrix", []), item["matrix_kA"]):
        raise Exception("La matriz escrita no coincide al releerla")

    # typ es el TypLne o el TypCon: el objeto cuyo sline lleva la característica.
    new_type = folders["types"].AddCopy(typ, name)
    if new_type is None:
        raise Exception("No se pudo copiar el tipo")
    refs = new_type.GetContents("sline.ChaRef") or []
    ref = refs[0] if refs else new_type.CreateObject("ChaRef", "sline")
    if ref is None:
        raise Exception("No se pudo crear sline.ChaRef en el tipo copiado")
    ref.SetAttribute("typ_id", new_cha)
    if characteristic_de(new_type) != new_cha:
        raise Exception("El tipo copiado no quedó apuntando a la nueva característica")

    target = new_type
    if plan["tower"] is not None:
        new_tow = folders["types"].AddCopy(plan["tower"], name)
        if new_tow is None:
            raise Exception("No se pudo copiar el TypTow")
        new_tow.SetAttribute("pcond_c", [new_type if obj == typ else obj for obj in as_list(get_attr(new_tow, "pcond_c", []))])
        if conductors(new_tow) != [new_type]:
            raise Exception("El TypTow copiado no quedó apuntando al TypCon copiado")
        target = new_tow

    stage_of_type = get_owner_stage(target)
    if stage_of_type is not None:
        warn("  El tipo copiado quedó dentro del stage %s (se esperaba en la biblioteca)" % ruta(stage_of_type))

    # Único cambio en la red: queda registrado en el stage.
    tow = plan["coupling"]
    if tow is not None:
        raw = get_attr(tow, "pGeo", None)
        tow.SetAttribute("pGeo", [target if g == plan["tower"] else g for g in raw]
                         if isinstance(raw, (list, tuple)) else target)
        if target not in as_list(get_attr(tow, "pGeo", None)):
            raise Exception("pGeo del ElmTow no quedó apuntando al TypTow copiado")
        for other in item.get("affected_lines", []):
            log("  cambia también: %s" % other["name"])
        return
    line.SetAttribute("typ_id", target)
    if get_attr(line, "typ_id", None) != target:
        raise Exception("typ_id no quedó apuntando al tipo copiado")


# =========================================================
# REPORTE
# =========================================================
def write_report(plans, blocked, suffix):
    path = os.path.join(os.path.dirname(PACKAGE_PATH) or ".", "writeback_report_%s.csv" % suffix)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Linea", "Ruta", "Estado", "Detalle", "Nuevo tipo / ChaMat",
                    "SS15", "SS25", "SS35", "CS15", "CS25", "CS35"])
        for p in plans:
            it = p["item"]
            w.writerow([it["line"]["name"], it["line"]["path"], p["status"], p["detail"], it["new_type_name"]]
                       + [v for row in it["matrix_kA"] for v in row])
        for b in blocked:
            w.writerow([b["line"]["name"], b["line"]["path"], "bloqueado en la app", "; ".join(b["reasons"]), ""])
    return path


# =========================================================
# CONFIGURACION (VENTANA)
# =========================================================
def stage_time_from(text):
    """'dd-mm-aaaa HH:MM' -> tAcTime. El día usa get_stage_time (00:00, su calibración); se suman horas y minutos."""
    date_part, _, hm = str(text).strip().partition(" ")
    day = datetime.strptime(date_part, "%d-%m-%Y")
    clock = datetime.strptime(hm.strip() or "00:00", "%H:%M")
    return get_stage_time(day.strftime("%d-%m-%Y")) + clock.hour * 3600 + clock.minute * 60


def read_package(path):
    with open(path, encoding="utf-8") as f:
        pkg = json.load(f)
    if pkg.get("schema_version") != "thermal-writeback/1":
        raise Exception("Paquete no reconocido: %s" % pkg.get("schema_version"))
    return pkg


def latest_package():
    found = glob.glob(os.path.join(os.path.expanduser("~"), "Downloads", "writeback_*.json"))
    return max(found, key=os.path.getmtime) if found else PACKAGE_PATH


def config_dialog():
    """Ventana modal. Devuelve la configuración o None si se cancela."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    if not getattr(sys, "argv", None):
        sys.argv = ["powerfactory"]  # Tk lo necesita y el Python embebido de PF no siempre lo define.

    now = datetime.now()
    root = tk.Tk(className="Writeback")
    root.title("Writeback de capacidades térmicas")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    frame = ttk.Frame(root, padding=12)
    frame.grid(sticky="nsew")

    path_var = tk.StringVar(value=latest_package())
    info_var = tk.StringVar()
    date_var = tk.StringVar(value=now.strftime("%d-%m-%Y"))
    hour_var = tk.StringVar(value="%02d" % now.hour)
    minute_var = tk.StringVar(value="%02d" % now.minute)
    variation_var = tk.StringVar()
    mode_var = tk.StringVar(value="simular")
    preview_var = tk.StringVar()
    result = {}

    def load_package(*_):
        try:
            pkg = read_package(path_var.get())
            info_var.set("Sufijo %s · %d líneas listas · %d bloqueadas · generado %s" % (
                pkg["suffix"], len(pkg["items"]), len(pkg["blocked"]), str(pkg.get("generated_at", ""))[:16]))
            variation_var.set(pkg["names"]["variation"])
        except Exception as e:
            info_var.set("No se pudo leer el paquete: %s" % e)

    def browse():
        folder = os.path.dirname(path_var.get())
        chosen = filedialog.askopenfilename(
            parent=root, title="Paquete de writeback",
            initialdir=folder if os.path.isdir(folder) else os.path.expanduser("~"),
            filetypes=[("Paquete writeback", "*.json"), ("Todos los archivos", "*.*")])
        if chosen:
            path_var.set(os.path.normpath(chosen))
            load_package()

    def stamp():
        return "%s %s:%s" % (date_var.get().strip(), hour_var.get().strip().zfill(2), minute_var.get().strip().zfill(2))

    def update_preview(*_):
        try:
            stage_time_from(stamp())
            preview_var.set("Stage activo desde %s · el study time se ajusta a esa fecha" % stamp())
        except Exception:
            preview_var.set("Fecha u hora inválida (dd-mm-aaaa, 00–23, 00–59)")

    def set_now():
        current = datetime.now()
        date_var.set(current.strftime("%d-%m-%Y"))
        hour_var.set("%02d" % current.hour)
        minute_var.set("%02d" % current.minute)

    def run():
        try:
            pkg = read_package(path_var.get())
        except Exception as e:
            messagebox.showerror("Paquete", "No se pudo leer el paquete:\n%s" % e, parent=root)
            return
        try:
            stage_time = stage_time_from(stamp())
        except Exception:
            messagebox.showerror("Fecha", "Fecha u hora inválida. Use dd-mm-aaaa, hora 00–23 y minutos 00–59.", parent=root)
            return
        variation = variation_var.get().strip()
        if not variation:
            messagebox.showerror("Variation", "Indique el nombre de la variation.", parent=root)
            return
        dry = mode_var.get() == "simular"
        if not dry and not messagebox.askyesno(
                "Aplicar cambios",
                "Se crearán objetos nuevos en la biblioteca y se registrarán hasta %d cambios en la variation "
                "'%s' (stage %s).\n\n¿Continuar?" % (len(pkg["items"]), variation, stamp()),
                parent=root):
            return
        result.update(path=path_var.get(), dry_run=dry, stage_time=stage_time, stage_label=stamp(), variation=variation)
        root.destroy()

    row = 0
    ttk.Label(frame, text="Paquete").grid(row=row, column=0, sticky="w", pady=3)
    ttk.Entry(frame, textvariable=path_var, width=62).grid(row=row, column=1, columnspan=4, sticky="we", padx=6)
    ttk.Button(frame, text="Examinar…", command=browse).grid(row=row, column=5)
    row += 1
    ttk.Label(frame, textvariable=info_var, foreground="#555").grid(row=row, column=1, columnspan=5, sticky="w", padx=6)
    row += 1
    ttk.Separator(frame).grid(row=row, column=0, columnspan=6, sticky="we", pady=8)
    row += 1
    ttk.Label(frame, text="Stage: fecha").grid(row=row, column=0, sticky="w", pady=3)
    clock = ttk.Frame(frame)
    clock.grid(row=row, column=1, columnspan=5, sticky="w", padx=6)
    ttk.Entry(clock, textvariable=date_var, width=12).pack(side="left", padx=(0, 12))
    ttk.Label(clock, text="hora").pack(side="left")
    ttk.Spinbox(clock, from_=0, to=23, wrap=True, width=4, format="%02.0f", textvariable=hour_var).pack(side="left", padx=(4, 2))
    ttk.Label(clock, text=":").pack(side="left")
    ttk.Spinbox(clock, from_=0, to=59, wrap=True, width=4, format="%02.0f", textvariable=minute_var).pack(side="left", padx=(2, 8))
    ttk.Button(clock, text="Ahora", command=set_now).pack(side="left")
    row += 1
    ttk.Label(frame, textvariable=preview_var, foreground="#555").grid(row=row, column=1, columnspan=5, sticky="w", padx=6)
    row += 1
    ttk.Label(frame, text="Variation").grid(row=row, column=0, sticky="w", pady=3)
    ttk.Entry(frame, textvariable=variation_var, width=40).grid(row=row, column=1, columnspan=4, sticky="w", padx=6)
    row += 1
    ttk.Label(frame, text="Modo").grid(row=row, column=0, sticky="w", pady=3)
    modes = ttk.Frame(frame)
    modes.grid(row=row, column=1, columnspan=5, sticky="w", padx=6)
    ttk.Radiobutton(modes, text="Simular (no modifica nada)", value="simular", variable=mode_var).pack(side="left")
    ttk.Radiobutton(modes, text="Aplicar cambios", value="aplicar", variable=mode_var).pack(side="left", padx=12)
    row += 1
    buttons = ttk.Frame(frame)
    buttons.grid(row=row, column=0, columnspan=6, sticky="e", pady=(12, 0))
    ttk.Button(buttons, text="Cancelar", command=root.destroy).pack(side="right")
    ttk.Button(buttons, text="Ejecutar", command=run).pack(side="right", padx=6)

    for var in (date_var, hour_var, minute_var):
        var.trace_add("write", update_preview)
    load_package()
    update_preview()
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.lift()
    root.focus_force()
    root.mainloop()
    return result or None


def configure():
    """Fija PACKAGE_PATH, DRY_RUN, STAGE_TIME y VARIATION_NAME. False si se cancela."""
    global PACKAGE_PATH, DRY_RUN, STAGE_TIME, VARIATION_NAME
    if not USE_DIALOG:
        STAGE_TIME = stage_time_from(STAGE_DATETIME)
        log("Stage: %s" % STAGE_DATETIME)
        return True
    cfg = config_dialog()
    if cfg is None:
        return False
    PACKAGE_PATH, DRY_RUN, STAGE_TIME, VARIATION_NAME = cfg["path"], cfg["dry_run"], cfg["stage_time"], cfg["variation"]
    log("Paquete: %s" % PACKAGE_PATH)
    log("Stage: %s · Variation: %s" % (cfg["stage_label"], VARIATION_NAME))
    return True


# =========================================================
# MAIN
# =========================================================
def main():
    global VARIATION_NAME

    if not configure():
        log("Cancelado: no se ejecutó nada.")
        return

    log("=" * 72)
    log("WRITEBACK CAPACIDADES TERMICAS %s" % ("(DRY RUN: no se modifica nada)" if DRY_RUN else "(APLICAR)"))
    log("=" * 72)

    pkg = read_package(PACKAGE_PATH)
    if app.GetActiveProject() is None:
        raise Exception("No hay proyecto activo.")

    suffix, names = pkg["suffix"], pkg["names"]
    VARIATION_NAME = VARIATION_NAME or names["variation"]

    chars = characteristics_folder()
    folders = {"types": find_child(app.GetProjectFolder("equip"), names["folder"], "IntFolder"),
               "chars": find_child(chars, names["folder"], "IntFolder")}

    lines = index_lines()
    plans = [plan_item(item, lines, pkg, folders) for item in pkg["items"]]
    for p in plans:
        (log if p["status"] in ("listo", "ya aplicado") else warn)(
            "[%s] %s: %s" % (p["status"], p["item"]["line"]["name"], p["detail"]))
    for b in pkg["blocked"]:
        warn("[bloqueado en la app] %s: %s" % (b["line"]["name"], "; ".join(b["reasons"])))

    ready = [p for p in plans if p["status"] == "listo"]
    log("")
    log("Listas: %d | ya aplicadas: %d | omitidas: %d | bloqueadas en la app: %d" % (
        len(ready), sum(p["status"] == "ya aplicado" for p in plans),
        sum(p["status"] == "omitido" for p in plans), len(pkg["blocked"])))

    if DRY_RUN or not ready:
        log("Reporte: " + write_report(plans, pkg["blocked"], suffix))
        log("DRY RUN: no se creó ni modificó nada." if DRY_RUN else "Nada que aplicar.")
        return

    # 1) Variation + stage verificados ANTES de crear cualquier objeto.
    stage_time = STAGE_TIME
    variation = get_or_create_variation()
    stage = get_or_create_stage(variation, VARIATION_NAME, stage_time)
    prepare_stage_for_recording(variation, stage, stage_time)
    grid = parent_of_class(ready[0]["line"], "ElmNet")
    if grid is None:
        raise Exception("No se encontró la red (ElmNet) de la primera línea para verificar el stage.")
    verify_recording_with_probe(grid, stage)

    # 2) Objetos nuevos en la biblioteca.
    folders["types"] = get_or_create(app.GetProjectFolder("equip"), "IntFolder", names["folder"])[0]
    folders["chars"] = get_or_create(chars, "IntFolder", names["folder"])[0]
    scale_folder = scales_folder(chars)
    scales = {"row": get_or_create_scale(scale_folder, names["row_scale"], pkg["rows"]),
              "col": get_or_create_scale(scale_folder, names["column_scale"], pkg["columns"])}
    template = find_characteristic(chars, pkg.get("template_characteristic_path"))

    # 3) Por línea.
    recorded_before = stage_entries(stage)
    for p in ready:
        try:
            apply_item(p, folders, scales, template)
            p["status"] = "aplicado"
            log("[aplicado] %s -> %s" % (p["item"]["line"]["name"], p["item"]["new_type_name"]))
        except Exception as e:
            p["status"], p["detail"] = "error", str(e)
            err("[error] %s: %s" % (p["item"]["line"]["name"], e))

    applied = sum(p["status"] == "aplicado" for p in plans)
    recorded = len(stage_entries(stage) - recorded_before)
    log("")
    log("Aplicadas: %d | errores: %d | entradas nuevas en el stage: %d" % (
        applied, sum(p["status"] == "error" for p in plans), recorded))
    if applied and not recorded:
        warn("[AVISO] El stage no muestra entradas nuevas: confirmar con el extractor (variation activa/inactiva).")
    log("Reporte: " + write_report(plans, pkg["blocked"], suffix))
    log("Revisar en el study case los triggers de %s y %s." % (names["row_scale"], names["column_scale"]))
    log("Verificar con el extractor: variation activa -> valores IT; inactiva -> valores originales.")


main()
