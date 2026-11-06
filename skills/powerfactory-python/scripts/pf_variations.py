# -*- coding: utf-8 -*-
"""
Variations, expansion stages and recording checks for PowerFactory ComPython scripts.

Paste these functions into the ComPython (PF runs one file) or put this file in a folder and
`sys.path.insert(0, folder); from pf_variations import *`. They use the module-level `app`,
`log` and `warn`; replace them if the host script defines its own.

Proven in real runs (PF, Chile, 2026):
- Activate() on a stage returns 1 (warnings) or 16 (study time adjusted) even when it works.
- An object created in a grid while recording reports the GRID as parent, so walking parents
  never finds the IntSstage. Check the stage contents instead (stage_entries before/after).
- Changes to library objects (types, characteristics, scales) are NOT recorded by variations.
- get_stage_time: the user's calibrated conversion (day at 00:00 local). Hours/minutes are
  added on top in stage_time_from() so the calibration is preserved. Check once in PF that the
  stage shows the expected time (daylight saving may shift the fixed offset by 1 h).
"""
from datetime import datetime, timedelta, timezone

import powerfactory as pf

app = pf.GetApplication()


def log(m):
    app.PrintPlain(str(m))


def warn(m):
    app.PrintWarn(str(m))


# =========================================================
# GENERAL
# =========================================================
def is_empty(value):
    return value is None or str(value).strip() == ""


def safe_name(name):
    """loc_name without characters PF may reject."""
    for ch in '\\/:*?"<>|':
        name = str(name).replace(ch, "-")
    return name.strip()


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
        raise Exception("No se pudo crear %s '%s' en %s" % (cls, name, parent.GetFullName()))
    return obj, True


# =========================================================
# FECHAS
# =========================================================
def get_stage_time(date_value):
    """
    Convierte fechas a tAcTime (día a las 00:00). Acepta:
      - 'ago-27', 'sept-27'  (mes-año, día 1)
      - '2027-08' / '08-2027' (año-mes / mes-año, día 1)
      - '01-11-2026'          (día-mes-año)
      - 46327                 (número de serie de Excel)
      - datetime
    """
    dic_months = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
                  "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12}
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
                raise ValueError(f"Número '{raw}' fuera del rango de fechas Excel")
            d = datetime(1899, 12, 30) + timedelta(days=int(serial))
            year, month, day = d.year, d.month, d.day
        else:
            s = raw.lower().replace(".", "")
            parts = s.split("-") if "-" in s else s.split("/") if "/" in s else None
            if not parts or len(parts) < 2:
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
                month, year = dic_months[a], int(b)
                if year < 100:
                    year += 2000
    target = datetime(int(year), int(month), int(day), tzinfo=timezone(timedelta(hours=-1)))
    return int((target - epoch_reference).total_seconds())


def stage_time_from(text):
    """'dd-mm-aaaa HH:MM' -> tAcTime: get_stage_time for the day + hours and minutes."""
    date_part, _, hm = str(text).strip().partition(" ")
    day = datetime.strptime(date_part, "%d-%m-%Y")
    clock = datetime.strptime(hm.strip() or "00:00", "%H:%M")
    return get_stage_time(day.strftime("%d-%m-%Y")) + clock.hour * 3600 + clock.minute * 60


def set_study_time(stage_time):
    """Moves the active study case's study time (a visible side effect: tell the user)."""
    try:
        study_case = app.GetActiveStudyCase()
    except Exception:
        study_case = None
    if study_case is None:
        warn("[AVISO] No se pudo obtener el Study Case activo. No se ajustó Study Time.")
        return False
    try:
        ierr = study_case.SetStudyTime(float(stage_time))
        if ierr not in (0, None):
            warn(f"[AVISO] SetStudyTime retornó código {ierr}.")
        return True
    except Exception as e:
        warn(f"[AVISO] No se pudo ejecutar SetStudyTime({stage_time}): {e}")
        return False


# =========================================================
# VARIATION Y STAGE
# =========================================================
def get_or_create_variation(name):
    scheme_folder = app.GetProjectFolder("scheme")
    if scheme_folder is None:
        raise Exception("No se encontró el folder 'scheme' (Variations) en el proyecto.")
    variation, created = get_or_create(scheme_folder, "IntScheme", name)
    log(f"[OK] Variation {'creada' if created else 'existente reutilizada'}: {variation.GetFullName()}")
    ierr = variation.Activate()
    if ierr not in (0, 1, None):
        raise Exception(f"No se pudo activar la variation '{name}'. Activate() retornó {ierr}")
    # Activate() returns 1 both when already active and on failure: check the real list.
    try:
        active = app.GetActiveNetworkVariations()
    except Exception:
        active = None
    if active is not None and variation not in active:
        raise Exception(f"La variation '{name}' NO quedó activa (Activate retornó {ierr}). Se aborta.")
    return variation


def get_or_create_stage(variation, name, stage_time):
    stage, created = get_or_create(variation, "IntSstage", safe_name(name))
    try:
        stage.tAcTime = stage_time
    except Exception as e:
        raise Exception(f"No se pudo asignar tAcTime al stage '{name}': {e}")
    for attr in ("outserv", "iExclude", "iExcluded", "iexclude"):
        try:
            setattr(stage, attr, 0)
        except Exception:
            pass
    log(f"[OK] Expansion Stage {'creado' if created else 'existente actualizado'}: {name}")
    return stage


def get_current_recording_stage(variation):
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
    PF records into ONE global stage: the active stage with the latest tAcTime <= study time
    across ALL active variations. Set the study time first, then activate the stage.
    """
    set_study_time(stage_time)
    try:
        ierr = stage.Activate()
    except Exception as e:
        raise Exception(f"No se pudo activar el stage '{stage.loc_name}': {e}")
    if ierr not in (0, 1, 16, None):
        raise Exception(f"El stage '{stage.loc_name}' no quedó como recording stage (Activate retornó {ierr}).")
    if ierr in (1, 16):
        log(f"[AVISO] Activate() retornó {ierr} en '{stage.loc_name}' (activación con avisos). Se verificará.")
    recording = get_current_recording_stage(variation)
    if recording is not None and recording != stage:
        raise Exception(f"El recording stage actual es '{recording.GetFullName()}', no '{stage.loc_name}'.")


def get_owner_stage(obj):
    """IntSstage in the parent chain, or None (the usual case for grid objects, see module doc)."""
    p = obj
    for _ in range(30):
        if p is None:
            return None
        try:
            if p.GetClassName() == "IntSstage":
                return p
            p = p.GetParent()
        except Exception:
            return None
    return None


PROBE_NAME = "__chk_recording__"


def stage_entries(stage):
    """Full names of everything the stage has recorded."""
    try:
        return {o.GetFullName() for o in (stage.GetContents("*", 1) or [])}
    except Exception:
        return set()


def verify_recording_with_probe(grid, stage):
    """
    Create a throwaway object in `grid`, confirm PF recorded it in `stage`, delete it.
    Abort (raise) unless recording into `stage` is confirmed: better than writing into
    someone else's variation.
    """
    before = stage_entries(stage)
    probe = grid.CreateObject("IntFolder", PROBE_NAME)
    if probe is None:
        raise Exception("No se pudo crear el objeto de prueba; no se puede confirmar el recording stage.")
    owner = get_owner_stage(probe)
    added = sorted(stage_entries(stage) - before)
    try:
        probe.Delete()
    except Exception:
        pass
    if owner is None and any(PROBE_NAME in n for n in added):
        owner = stage
    if owner is None:
        raise Exception("Verificación del recording stage no concluyente (entradas nuevas en el stage: %s). "
                        "Se aborta sin modificar nada." % (added[:10] or "ninguna"))
    if owner != stage:
        raise Exception(f"PF está registrando en '{owner.GetFullName()}', no en '{stage.loc_name}'. Abortado.")
    log(f"[OK] Verificado: los cambios se registran en '{stage.loc_name}'.")


def open_recording_stage(variation_name, stage_text, grid):
    """One call: variation active + stage at 'dd-mm-aaaa HH:MM' recording + probe verified."""
    stage_time = stage_time_from(stage_text)
    variation = get_or_create_variation(variation_name)
    stage = get_or_create_stage(variation, variation_name, stage_time)
    prepare_stage_for_recording(variation, stage, stage_time)
    verify_recording_with_probe(grid, stage)
    return variation, stage
