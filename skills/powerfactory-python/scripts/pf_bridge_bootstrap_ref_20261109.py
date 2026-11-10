"""Bootstrap autorizado 2026-11-09: respaldo manual, activación del Ref exacto y copia SONDA.

Se ejecuta UNA vez, como ComPython, después de detener el puente actual y SOLO con el checkpoint manual
H4 creado por el usuario (ver CHECKPOINT / TOKEN_H4). Orden:
  1. Verifica proyecto autorizado y checkpoint manual del estado del laboratorio.
  2. Crea una VERSIÓN PF del laboratorio (IntPrj.CreateVersion) y la verifica.
  3. Activa el Ref exacto 2608-BD-OP-COORD-DMAP (ruta exacta, no por nombre).
  4. Activa el caso Base SEN y el escenario Domingo Madrugada; rechaza cambios sin guardar.
  5. Crea o reutiliza Base SEN_SONDA_20261109 SOLO si su huella y procedencia están verificadas.
  6. Activa la copia SONDA y VERIFICA el contexto antes de arrancar el puente.
  7. Arranca pf_bridge_diag_ref.py (sin retiming).

Garantías deliberadas:
  - Ningún fallback arranca un puente: si el proyecto es desconocido o algo falla, se aborta y se deja un
    artefacto de diagnóstico. Un puente de solo lectura en un contexto desconocido podría ocultar el estado.
  - El rollback solo reactiva el laboratorio cuando el Ref quedó activo; NO deshace CreateVersion ni AddCopy
    y NO borra datos del usuario. El artefacto lo dice explícitamente.
  - El estado sucio del laboratorio se trata como UNKNOWN: no se inventa una API de "dirty" para IntPrj/IntCase.
    Sin el checkpoint manual verificado, el bootstrap aborta ANTES de cualquier activación o respaldo.
"""
import datetime
import hashlib
import json
import os
import traceback

import powerfactory

BRIDGE_DIR = os.path.join(os.path.expanduser("~"), "pf_bridge")
SCRIPTS = r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts"
LOG = os.path.join(BRIDGE_DIR, "files", "bootstrap_ref_20261109.jsonl")
ARTEFACTO = os.path.join(BRIDGE_DIR, "files", "bootstrap_ref_20261109_estado.json")
PROVENANCE = os.path.join(BRIDGE_DIR, "files", "sonda_provenance_20261109.json")
CHECKPOINT = os.path.join(BRIDGE_DIR, "manual_state", "H4_estado_lab_resuelto.json")

PRJ_LAB = "\\vicen.IntUser\\Estudios\\ViQSilent_RMS_Lab_20261104.IntPrj"
PRJ_REF = "\\vicen.IntUser\\Estudios\\[ER] PE Cumbres del Ñuble\\Ref\\2608-BD-OP-COORD-DMAP.IntPrj"
REF_CASOS = PRJ_REF + "\\Study Cases.IntPrjfolder"
CASO_REF = REF_CASOS + "\\Base SEN.IntCase"
CASO_SONDA = REF_CASOS + "\\Base SEN_SONDA_20261109.IntCase"
ESC_REF = PRJ_REF + "\\Operation Scenarios.IntPrjfolder\\3. Domingo.IntFolder\\Domingo Madrugada.IntScenario"

VERSION_RESPALDO = "BACKUP_20261109_antes_SONDA"
TOKEN_H4 = "H4-ESTADO-LAB-RESUELTO-20261109"      # lo escribe el usuario; no lo genera el script
TOKEN_PROVENANCE = "sonda-bootstrap-20261109"

MUTACIONES = []      # se reinicia en main(); el handler de fallo lo publica en el artefacto


def log(evento, **datos):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    e = dict(t=datetime.datetime.now().isoformat(timespec="seconds"), evento=evento)
    e.update(datos)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(e, ensure_ascii=False, default=str) + "\n")


def escribir_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, ruta)


def leer_json(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def g(o, n, defecto=None):
    try:
        return o.GetAttribute(n)
    except Exception:
        return defecto


def hijos(o):
    return list(o.GetContents("*", 0) or [])


def buscar_hijo(padre, nombre, clase=None):
    c = [o for o in hijos(padre) if o.loc_name == nombre and (clase is None or o.GetClassName() == clase)]
    if len(c) != 1:
        raise RuntimeError("no se encontró un único %r en %s (candidatos: %s)" % (
            nombre, padre.GetFullName(), [o.GetFullName() for o in c]))
    return c[0]


def resolver_ref(prj_lab):
    estudios = prj_lab.GetParent()                       # \vicen.IntUser\Estudios
    cumbres = buscar_hijo(estudios, "[ER] PE Cumbres del Ñuble")
    ref_folder = buscar_hijo(cumbres, "Ref")
    ref = buscar_hijo(ref_folder, "2608-BD-OP-COORD-DMAP", "IntPrj")
    if ref.GetFullName() != PRJ_REF:
        raise RuntimeError("resolver_ref devolvió una ruta distinta del Ref exacto: %s" % ref.GetFullName())
    return ref


def resolver_lab(prj_ref):
    # Ref\... -> Cumbres -> Estudios -> laboratorio
    estudios = prj_ref.GetParent().GetParent().GetParent()
    lab = buscar_hijo(estudios, "ViQSilent_RMS_Lab_20261104", "IntPrj")
    if lab.GetFullName() != PRJ_LAB:
        raise RuntimeError("resolver_lab devolvió una ruta distinta del laboratorio exacto: %s" % lab.GetFullName())
    return lab


def resolver_caso(prj, ruta):
    prefijo = prj.GetFullName() + "\\Study Cases.IntPrjfolder"
    if not ruta.startswith(prefijo + "\\"):
        raise RuntimeError("ruta de caso fuera de Study Cases: %s" % ruta)
    study = buscar_hijo(prj, "Study Cases", "IntPrjfolder")
    nombre = ruta.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    c = [o for o in hijos(study) if o.GetClassName() == "IntCase" and o.loc_name == nombre]
    if len(c) != 1:
        raise RuntimeError("caso %r no encontrado o ambiguo en %s" % (nombre, study.GetFullName()))
    if c[0].GetFullName() != ruta:
        raise RuntimeError("el caso resuelto no tiene la ruta exacta esperada: %s != %s" % (c[0].GetFullName(), ruta))
    return c[0]


def resolver_escenario(prj):
    raiz = buscar_hijo(prj, "Operation Scenarios", "IntPrjfolder")
    domingo = buscar_hijo(raiz, "3. Domingo")
    c = [o for o in hijos(domingo) if o.GetClassName() == "IntScenario" and o.loc_name == "Domingo Madrugada"]
    if len(c) != 1:
        raise RuntimeError("escenario Domingo Madrugada no encontrado o ambiguo")
    if c[0].GetFullName() != ESC_REF:
        raise RuntimeError("el escenario resuelto no tiene la ruta exacta esperada: %s" % c[0].GetFullName())
    return c[0]


def ajustes_comando(cmd):
    d = dict(nombre=cmd.loc_name, clase=cmd.GetClassName(), ruta=cmd.GetFullName())
    for n in ("tstop", "iopt_show", "dtgrd", "dtgrd_max", "dtout", "tstart", "iopt_int", "iopt_sim",
              "iopt_net", "ninc", "iopt_reinc", "copt_reinc"):
        d[n] = g(cmd, n, "NO_EXISTE")
    return d


def comparable(foto):
    """Huella de caso sin rutas, para comparar el original con la copia."""
    f = {k: v for k, v in foto.items() if k != "ruta"}
    for clave in ("comandos", "eventos_planos"):
        f[clave] = [{k: v for k, v in e.items() if k != "ruta"} for e in f.get(clave, [])]
    return f


def foto_caso(caso):
    cmds = [o for o in hijos(caso) if o.GetClassName() in ("ComInc", "ComSim", "ComLdf", "ComShc", "ComVstab", "ComDiff")]
    evt = [o for o in hijos(caso) if o.GetClassName() == "IntEvt"]
    return dict(
        ruta=caso.GetFullName(), iStudyTime=g(caso, "iStudyTime"),
        hijos=[dict(nombre=o.loc_name, clase=o.GetClassName()) for o in hijos(caso)],
        comandos=[ajustes_comando(c) for c in cmds],
        eventos_planos=[dict(nombre=e.loc_name, ruta=e.GetFullName(), hijos=len(hijos(e))) for e in evt],
    )


def huella(foto):
    texto = json.dumps(comparable(foto), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def estado_actual(app):
    def fn(o):
        try:
            return o.GetFullName() if o is not None else None
        except Exception:
            return None
    try:
        prj, caso, esc = app.GetActiveProject(), app.GetActiveStudyCase(), app.GetActiveScenario()
    except Exception:
        prj = caso = esc = None
    return dict(proyecto=fn(prj), caso=fn(caso), escenario=fn(esc))


def artefacto(etapa, **datos):
    """Deja un artefacto de diagnóstico legible, incluso si el fallo ocurrió a medias."""
    d = dict(t=datetime.datetime.now().isoformat(timespec="seconds"), etapa=etapa)
    try:
        d.update(estado_actual(powerfactory.GetApplication()))
    except Exception as e:
        d.update(proyecto=None, caso=None, escenario=None, error_estado="%s: %s" % (type(e).__name__, e))
    d.update(datos)
    d.setdefault("mutaciones_de_esta_corrida", list(MUTACIONES))
    d.setdefault("nota_rollback",
                 "El rollback solo reactiva el laboratorio. No deshace CreateVersion ni AddCopy y no borra "
                 "datos del usuario; la copia SONDA y la versión pueden persistir.")
    escribir_json(ARTEFACTO, d)
    log("artefacto", ruta=ARTEFACTO, etapa=etapa)
    return d


def verificar_checkpoint():
    """H4: sin resolución manual verificada, el estado del laboratorio es UNKNOWN y se aborta.

    El usuario crea CHECKPOINT a mano tras resolver los cambios pendientes en PF (guardar o descartar
    explícitamente). No se deduce con iModified de IntPrj/IntCase: ese atributo no existe.
    """
    if not os.path.exists(CHECKPOINT):
        return False, "no existe el checkpoint manual H4: %s" % CHECKPOINT
    d = leer_json(CHECKPOINT)
    if not isinstance(d, dict):
        return False, "checkpoint H4 ilegible: %s" % CHECKPOINT
    if d.get("token") != TOKEN_H4:
        return False, "token H4 inválido"
    if d.get("resuelto") is not True:
        return False, "checkpoint H4 no marcado como resuelto"
    if d.get("estado_sucio") != "RESUELTO_POR_USUARIO":
        return False, "estado_sucio debe ser RESUELTO_POR_USUARIO"
    if d.get("proyecto") != PRJ_LAB:
        return False, "el checkpoint no corresponde al laboratorio exacto"
    for clave in ("fecha", "metodo", "evidencia"):
        valor = d.get(clave)
        if not isinstance(valor, str) or not valor.strip():
            return False, "checkpoint H4 sin %s" % clave
    return True, "checkpoint H4 verificado"


def registrar_procedencia(foto_original):
    d = dict(token=TOKEN_PROVENANCE, proyecto=PRJ_REF, original=CASO_REF, copia=CASO_SONDA,
             huella=huella(foto_original), creada=datetime.datetime.now().isoformat(timespec="seconds"),
             nota="Copia creada por el bootstrap; reutilizable solo si la huella del original coincide.")
    escribir_json(PROVENANCE, d)
    log("procedencia_registrada", ruta=PROVENANCE, huella=d["huella"])
    return d


def procedencia_verificada(foto_original):
    if not os.path.exists(PROVENANCE):
        return False, "no hay registro de procedencia del bootstrap: %s" % PROVENANCE
    d = leer_json(PROVENANCE)
    if not isinstance(d, dict):
        return False, "registro de procedencia ilegible"
    if d.get("token") != TOKEN_PROVENANCE:
        return False, "token de procedencia inválido"
    if d.get("proyecto") != PRJ_REF or d.get("original") != CASO_REF or d.get("copia") != CASO_SONDA:
        return False, "la procedencia no corresponde al Ref/Base SEN/SONDA exactos"
    if d.get("huella") != huella(foto_original):
        return False, "la huella registrada no coincide con el original actual"
    return True, "procedencia verificada"


def arrancar(script, etiqueta):
    log("arrancando", script=script, etiqueta=etiqueta)
    ns = {"__name__": "__pf_bootstrap__", "__file__": script}
    exec(compile(open(script, encoding="utf-8").read(), script, "exec"), ns)


def main():
    global MUTACIONES
    MUTACIONES = []
    app = powerfactory.GetApplication()
    prj = app.GetActiveProject()
    if prj is None:
        log("abortado", motivo="sin proyecto activo")
        artefacto("abortado_sin_proyecto")
        return
    activo = prj.GetFullName()
    log("inicio_bootstrap", proyecto_activo=activo, pid=os.getpid())

    # Proyecto desconocido: fail-closed, sin puente ni fallback que pueda ocultar el contexto.
    if activo not in (PRJ_LAB, PRJ_REF):
        log("abortado", motivo="proyecto no autorizado", proyecto=activo)
        artefacto("abortado_proyecto_no_autorizado", proyecto_activo=activo,
                  instruccion="No se arranca ningún puente. Abrir manualmente el laboratorio o el Ref exactos.")
        return

    # H4: estado sucio UNKNOWN hasta que el usuario aporte el checkpoint manual verificado.
    ok_h4, motivo_h4 = verificar_checkpoint()
    if not ok_h4:
        log("abortado_h4", estado_sucio="UNKNOWN", motivo=motivo_h4, checkpoint=CHECKPOINT)
        artefacto("abortado_estado_lab_no_verificado", estado_sucio="UNKNOWN", checkpoint=CHECKPOINT,
                  motivo=motivo_h4,
                  instruccion="Resolver en PF los cambios pendientes del laboratorio (guardar o descartar "
                              "explícitamente) y crear el checkpoint manual; no se activa nada sin él.")
        return
    estado_sucio = "RESUELTO_POR_USUARIO"
    log("checkpoint_h4_ok", checkpoint=CHECKPOINT, estado_sucio=estado_sucio)

    if activo == PRJ_LAB:
        # 1. Respaldo manual PF ANTES de tocar el Ref. Sin checkpoint válido no se llega aquí.
        try:
            log("creando_version", proyecto=PRJ_LAB, nombre=VERSION_RESPALDO)
            version = prj.CreateVersion(VERSION_RESPALDO, 0, 0, 0,
                                        "Respaldo completo previo a activacion Ref 2608 y copia SONDA")
            if version is None:
                raise RuntimeError("CreateVersion devolvió None")
            versiones = [v.GetFullName() for v in (prj.GetVersions() or [])]
            if version.GetFullName() not in versiones:
                raise RuntimeError("la versión no aparece en GetVersions(): %s" % versiones)
            MUTACIONES.append("CreateVersion %s" % VERSION_RESPALDO)
            log("version_creada", version=version.GetFullName(), versiones=versiones,
                st_rec_versions=g(prj, "st_rec_versions"))
        except Exception as e:
            log("error_version", error="%s: %s" % (type(e).__name__, e), traceback=traceback.format_exc())
            raise

        # 2. Activar Ref exacto.
        ref = resolver_ref(prj)
        log("activando_ref", destino=ref.GetFullName(), projectId=g(ref, "projectId"))
        r = ref.Activate()
        if app.GetActiveProject() is None or app.GetActiveProject().GetFullName() != PRJ_REF:
            raise RuntimeError("Ref no quedó activo (ret=%s, activo=%s)" % (
                r, app.GetActiveProject().GetFullName() if app.GetActiveProject() else None))
        log("ref_activo", ret=r, activo=app.GetActiveProject().GetFullName(),
            projectId=g(app.GetActiveProject(), "projectId"))

        # 3. Caso y escenario exactos.
        base = resolver_caso(app.GetActiveProject(), CASO_REF)
        rb = base.Activate()
        if app.GetActiveStudyCase() is None or app.GetActiveStudyCase().GetFullName() != CASO_REF:
            raise RuntimeError("Base SEN no quedó activo (ret=%s)" % rb)
        esc = resolver_escenario(app.GetActiveProject())
        i_mod_antes = g(esc, "iModified", "NO_EXISTE")
        if i_mod_antes == "NO_EXISTE":
            raise RuntimeError("iModified del escenario es UNKNOWN: no se puede verificar que esté limpio; se aborta")
        if i_mod_antes not in (0, 0.0, False, None):
            raise RuntimeError("Domingo Madrugada tiene cambios sin guardar (iModified=%r); no se activa" % (i_mod_antes,))
        re = esc.Activate()
        if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
            raise RuntimeError("Domingo Madrugada no quedó activo (ret=%s)" % re)
        i_mod_despues = g(esc, "iModified", "NO_EXISTE")
        if i_mod_despues == "NO_EXISTE":
            raise RuntimeError("iModified del escenario es UNKNOWN tras activarlo; se aborta")
        if i_mod_antes in (0, 0.0, False) and i_mod_despues not in (0, 0.0, False, None):
            raise RuntimeError("el escenario quedó modificado al activarlo (iModified=%r)" % (i_mod_despues,))
        log("contexto_ref", caso=app.GetActiveStudyCase().GetFullName(),
            escenario=app.GetActiveScenario().GetFullName(), estado_sucio=estado_sucio,
            iModified_antes=i_mod_antes, iModified_despues=i_mod_despues)

        # 4. Copia diagnóstica única, preservando el original.
        foto_original_antes = foto_caso(base)
        study = base.GetParent()
        existentes = [o for o in hijos(study) if o.loc_name == "Base SEN_SONDA_20261109"]
        if existentes:
            if len(existentes) != 1:
                raise RuntimeError("hay %d copias con el nombre SONDA; no se reutiliza ninguna" % len(existentes))
            copia = existentes[0]
            if copia.GetFullName() != CASO_SONDA:
                raise RuntimeError("la copia existente no tiene la ruta exacta: %s" % copia.GetFullName())
            if comparable(foto_caso(copia)) != comparable(foto_original_antes):
                raise RuntimeError("la copia SONDA existente no coincide con Base SEN; no se reutiliza: %s"
                                   % copia.GetFullName())
            ok_prov, motivo_prov = procedencia_verificada(foto_original_antes)
            if not ok_prov:
                raise RuntimeError("la copia SONDA existente no tiene procedencia verificada (%s); "
                                   "renombrarla o eliminarla manualmente antes de reintentar" % motivo_prov)
            log("sonda_reutilizada_verificada", copia=copia.GetFullName(), procedencia=motivo_prov)
        else:
            copia = study.AddCopy(base, "Base SEN_SONDA_20261109")
            if copia is None:
                raise RuntimeError("AddCopy de Base SEN devolvió None")
            MUTACIONES.append("AddCopy Base SEN_SONDA_20261109")
            if copia.GetFullName() != CASO_SONDA:
                raise RuntimeError("la copia no tiene la ruta exacta: %s" % copia.GetFullName())
            if comparable(foto_caso(copia)) != comparable(foto_original_antes):
                raise RuntimeError("la copia SONDA no reproduce Base SEN")
            registrar_procedencia(foto_original_antes)
            log("sonda_creada", copia=copia.GetFullName(), huella=huella(foto_original_antes))

        foto_original_despues = foto_caso(base)
        if foto_original_antes != foto_original_despues:
            raise RuntimeError("AddCopy modificó el caso original Base SEN")
        log("foto_original", antes=foto_original_antes, despues=foto_original_despues, igual=True)
        log("foto_sonda", copia=foto_caso(copia))

        # 5. El puente debe calcular en la copia: activarla y verificar ANTES de arrancarlo.
        rc = copia.Activate()
        if app.GetActiveStudyCase() is None or app.GetActiveStudyCase().GetFullName() != CASO_SONDA:
            raise RuntimeError("la copia SONDA no quedó activa (ret=%s)" % rc)
        if app.GetActiveProject() is None or app.GetActiveProject().GetFullName() != PRJ_REF:
            raise RuntimeError("al activar la copia se perdió el Ref exacto")
        if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
            esc.Activate()
            if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
                raise RuntimeError("el escenario Domingo Madrugada no quedó activo tras activar la copia")
        log("sonda_activa", caso=app.GetActiveStudyCase().GetFullName(),
            escenario=app.GetActiveScenario().GetFullName(), proyecto=app.GetActiveProject().GetFullName())

    else:  # ya estamos en el Ref (reintento)
        # Este camino no crea versión: exigir que exista el respaldo antes de seguir.
        lab = resolver_lab(app.GetActiveProject())
        versiones = [v.GetFullName() for v in (lab.GetVersions() or [])]
        if not any(VERSION_RESPALDO in v for v in versiones):
            raise RuntimeError("reintento sin versión de respaldo verificable del laboratorio: %s" % versiones)

        base = resolver_caso(app.GetActiveProject(), CASO_REF)
        if app.GetActiveStudyCase() is None or app.GetActiveStudyCase().GetFullName() != CASO_REF:
            base.Activate()
            if app.GetActiveStudyCase() is None or app.GetActiveStudyCase().GetFullName() != CASO_REF:
                raise RuntimeError("Base SEN no quedó activo en el reintento")
        esc = resolver_escenario(app.GetActiveProject())
        i_mod_antes = g(esc, "iModified", "NO_EXISTE")
        if i_mod_antes == "NO_EXISTE":
            raise RuntimeError("iModified del escenario es UNKNOWN en el reintento; se aborta")
        if i_mod_antes not in (0, 0.0, False, None):
            raise RuntimeError("Domingo Madrugada tiene cambios sin guardar (iModified=%r)" % (i_mod_antes,))
        if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
            esc.Activate()
            if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
                raise RuntimeError("Domingo Madrugada no quedó activo en el reintento")
        i_mod_despues = g(esc, "iModified", "NO_EXISTE")
        if i_mod_despues == "NO_EXISTE":
            raise RuntimeError("iModified del escenario es UNKNOWN tras activarlo (reintento)")
        if i_mod_antes in (0, 0.0, False) and i_mod_despues not in (0, 0.0, False, None):
            raise RuntimeError("el escenario quedó modificado al activarlo (reintento, iModified=%r)" % (i_mod_despues,))
        foto_base = foto_caso(base)
        study = base.GetParent()
        existentes = [o for o in hijos(study) if o.loc_name == "Base SEN_SONDA_20261109"]
        if not existentes:
            copia = study.AddCopy(base, "Base SEN_SONDA_20261109")
            if copia is None:
                raise RuntimeError("AddCopy de Base SEN devolvió None (reintento)")
            MUTACIONES.append("AddCopy Base SEN_SONDA_20261109 (reintento)")
            if copia.GetFullName() != CASO_SONDA:
                raise RuntimeError("la copia no tiene la ruta exacta (reintento): %s" % copia.GetFullName())
            if comparable(foto_caso(copia)) != comparable(foto_base):
                raise RuntimeError("la copia SONDA no reproduce Base SEN (reintento)")
            registrar_procedencia(foto_base)
            log("sonda_creada_reintento", copia=copia.GetFullName())
        else:
            if len(existentes) != 1:
                raise RuntimeError("hay %d copias con el nombre SONDA; no se reutiliza ninguna" % len(existentes))
            copia = existentes[0]
            if copia.GetFullName() != CASO_SONDA:
                raise RuntimeError("la copia existente no tiene la ruta exacta: %s" % copia.GetFullName())
            if comparable(foto_caso(copia)) != comparable(foto_base):
                raise RuntimeError("la copia SONDA existente no coincide con Base SEN; no se reutiliza")
            ok_prov, motivo_prov = procedencia_verificada(foto_base)
            if not ok_prov:
                raise RuntimeError("la copia SONDA existente no tiene procedencia verificada (%s); "
                                   "renombrarla o eliminarla manualmente antes de reintentar" % motivo_prov)
            log("sonda_reutilizada_verificada", copia=copia.GetFullName(), procedencia=motivo_prov)
        rc = copia.Activate()
        if app.GetActiveStudyCase() is None or app.GetActiveStudyCase().GetFullName() != CASO_SONDA:
            raise RuntimeError("la copia SONDA no quedó activa (ret=%s)" % rc)
        if app.GetActiveProject() is None or app.GetActiveProject().GetFullName() != PRJ_REF:
            raise RuntimeError("al activar la copia se perdió el Ref exacto (reintento)")
        if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
            esc.Activate()
            if app.GetActiveScenario() is None or app.GetActiveScenario().GetFullName() != ESC_REF:
                raise RuntimeError("el escenario Domingo Madrugada no quedó activo tras activar la copia")
        log("contexto_ref", caso=app.GetActiveStudyCase().GetFullName(),
            escenario=app.GetActiveScenario().GetFullName(), estado_sucio=estado_sucio)

    # 6. Puente de diagnóstico (sin retiming), solo con el contexto ya verificado.
    artefacto("listo_para_puente", estado_sucio=estado_sucio,
              caso_esperado=CASO_SONDA, escenario_esperado=ESC_REF, proyecto_esperado=PRJ_REF,
              nota_rollback="Contexto verificado; el puente recalcula Execute solo en CASO_SONDA.")
    arrancar(os.path.join(SCRIPTS, "pf_bridge_diag_ref.py"), "diagnostico_ref")


def entrada():
    """Punto de entrada con diagnóstico honesto de fallo parcial. No arranca ningún puente de fallback."""
    try:
        main()
    except BaseException as e:
        log("fallo_bootstrap", error="%s: %s" % (type(e).__name__, e), traceback=traceback.format_exc())
        rollback = "no_intentado"
        try:
            app = powerfactory.GetApplication()
            prj = app.GetActiveProject()
            if prj is not None and prj.GetFullName() == PRJ_REF:
                lab = resolver_lab(prj)
                r = lab.Activate()
                activo = app.GetActiveProject().GetFullName() if app.GetActiveProject() else None
                rollback = "activar_lab ret=%s activo=%s" % (r, activo)
                log("rollback_lab", ret=r, activo=activo)
            else:
                rollback = "sin_cambio: proyecto activo=%s" % (
                    prj.GetFullName() if prj is not None else None)
        except Exception as e2:
            rollback = "fallido: %s: %s" % (type(e2).__name__, e2)
            log("error_rollback", error=rollback, traceback=traceback.format_exc())
        artefacto("fallo_parcial", error="%s: %s" % (type(e).__name__, e), rollback=rollback,
                  copia_puede_persistir=True, version_puede_persistir=True,
                  nota="No se elimina la copia SONDA ni la versión. El rollback solo reactiva el laboratorio "
                       "y no deshace mutaciones. No se arranca ningún puente de fallback.")
        log("sin_fallback_puente", motivo="fallo parcial: no se arranca ningún puente; revisar artefacto",
            ruta=ARTEFACTO)


# PF no siempre define __name__ == "__main__": se invoca igual que pf_bridge.py.
entrada()
