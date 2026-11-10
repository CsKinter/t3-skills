"""Pruebas del bootstrap Ref con mocks puros (sin PowerFactory/GUI/puente).

Cubre lo que el test anterior no probaba y ahora es obligatorio:
  - Checkpoint manual H4: sin él se aborta ANTES de versión/activación y no se arranca puente.
  - Proyecto desconocido: fail-closed, ningún puente de fallback.
  - Huella del original: si AddCopy la cambia, se aborta (no solo se registra).
  - Copia SONDA preexistente: solo se reutiliza con huella y procedencia verificadas.
  - Post-copia: la copia SONDA queda ACTIVA y verificada antes de arrancar el puente.
  - Fallo parcial: artefacto de diagnóstico y rollback honesto, sin borrar copia/versión.
  - Cero retiming/stages: no SetStudyTime/CreateObject.
"""
import json
import os
import sys
import tempfile
import types

sys.modules.setdefault("powerfactory", types.ModuleType("powerfactory"))

SRC = r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_bridge_bootstrap_ref_20261109.py"
fuente = open(SRC, encoding="utf-8").read()
fuente = fuente.rsplit("\nentrada()", 1)[0]
bns = {"__name__": "bootstrap_test", "__file__": SRC}
exec(compile(fuente, SRC, "exec"), bns)

PRJ_LAB = bns["PRJ_LAB"]
PRJ_REF = bns["PRJ_REF"]
REF_CASOS = bns["REF_CASOS"]
CASO_REF = bns["CASO_REF"]
CASO_SONDA = bns["CASO_SONDA"]
ESC_REF = bns["ESC_REF"]
TOKEN_H4 = bns["TOKEN_H4"]
VERSION_RESPALDO = bns["VERSION_RESPALDO"]


class BO(object):
    def __init__(self, cls, nombre, parent=None, path=None):
        self._cls, self.loc_name, self._parent = cls, nombre, parent
        self._path = path or ((parent.GetFullName() + "\\" + nombre + "." + cls) if parent is not None else "\\" + nombre)
        self._children = []
        self.calls = []
        self.attrs = {"iStudyTime": 1786768500, "iModified": 0, "tstop": 1.0, "iopt_show": 0,
                      "dtgrd": 0.002, "dtout": 0.004, "tstart": 0.0, "projectId": 57192810}
        if parent is not None:
            parent._children.append(self)

    def GetClassName(self):
        return self._cls

    def GetParent(self):
        return self._parent

    def GetFullName(self):
        return self._path

    def GetContents(self, patron="*", recursive=0):
        return list(self._children)

    def GetAttribute(self, k):
        if k not in self.attrs:
            raise AttributeError(k)
        return self.attrs[k]

    def Activate(self):
        self.calls.append("Activate")
        if self._cls == "IntPrj":
            BAPP.project = self
        elif self._cls == "IntCase":
            if getattr(BAPP, "ignorar_activate_caso", None) == self.loc_name:
                return 0
            BAPP.case = self
        elif self._cls == "IntScenario":
            BAPP.scenario = self
        return 0

    def SetStudyTime(self, *a, **k):
        self.calls.append(("SetStudyTime", a))
        return 0

    def CreateVersion(self, *a, **k):
        self.calls.append(("CreateVersion",) + a)
        if getattr(BAPP, "fail_version", False):
            return None
        v = BO("IntVersion", VERSION_RESPALDO, None,
               path=self.GetFullName() + "\\Versions.IntVersionman\\" + VERSION_RESPALDO + ".IntVersion")
        self.versions.append(v)
        return v

    def GetVersions(self):
        return list(getattr(self, "versions", []))

    def AddCopy(self, origen, nombre):
        self.calls.append(("AddCopy", origen.GetFullName(), nombre))
        if getattr(BAPP, "fail_copy", False):
            return None
        cp = BO("IntCase", nombre, self, path=self.GetFullName() + "\\" + nombre + ".IntCase")
        copiar(origen, cp)
        if getattr(BAPP, "mutar_original", False):
            BO("ComInc", "Intruso", origen, path=origen.GetFullName() + "\\Intruso.ComInc")
        return cp


def copiar(src, dst):
    for ch in src.GetContents():
        n = BO(ch.GetClassName(), ch.loc_name, dst,
               path=dst.GetFullName() + "\\" + ch.loc_name + "." + ch.GetClassName())
        n.attrs = dict(ch.attrs)
        copiar(ch, n)


class BApp(object):
    def __init__(self):
        self.project = self.case = self.scenario = None
        self.msg = []
        self.fail_version = False
        self.fail_copy = False
        self.mutar_original = False
        self.ignorar_activate_caso = None

    def GetActiveProject(self):
        return self.project

    def GetActiveStudyCase(self):
        return self.case

    def GetActiveScenario(self):
        return self.scenario

    def PrintPlain(self, m):
        self.msg.append(str(m))

    PrintError = PrintWarn = PrintPlain


def build_bootstrap(active="lab", existing_sonda=False, sonda_distinta=False):
    global BAPP
    BAPP = BApp()
    user = BO("IntUser", "vicen", path="\\vicen.IntUser")
    est = BO("IntFolder", "Estudios", user, path="\\vicen.IntUser\\Estudios")
    cum = BO("IntFolder", "[ER] PE Cumbres del Ñuble", est, path="\\vicen.IntUser\\Estudios\\[ER] PE Cumbres del Ñuble")
    refd = BO("IntFolder", "Ref", cum, path="\\vicen.IntUser\\Estudios\\[ER] PE Cumbres del Ñuble\\Ref")
    ref = BO("IntPrj", "2608-BD-OP-COORD-DMAP", refd, path=PRJ_REF)
    ref.versions = []
    study = BO("IntPrjfolder", "Study Cases", ref, path=REF_CASOS)
    base = BO("IntCase", "Base SEN", study, path=CASO_REF)
    BO("ComInc", "Calculation of Initial Condition", base, path=CASO_REF + "\\Calculation of Initial Condition.ComInc")
    BO("ComSim", "Run Simulation", base, path=CASO_REF + "\\Run Simulation.ComSim")
    scen_root = BO("IntPrjfolder", "Operation Scenarios", ref, path=PRJ_REF + "\\Operation Scenarios.IntPrjfolder")
    dom = BO("IntFolder", "3. Domingo", scen_root, path=scen_root.GetFullName() + "\\3. Domingo.IntFolder")
    esc = BO("IntScenario", "Domingo Madrugada", dom, path=ESC_REF)
    lab = BO("IntPrj", "ViQSilent_RMS_Lab_20261104", est, path=PRJ_LAB)
    lab.versions = []
    if existing_sonda:
        sonda = BO("IntCase", "Base SEN_SONDA_20261109", study, path=CASO_SONDA)
        if sonda_distinta:
            BO("ComInc", "Otro Comando", sonda, path=CASO_SONDA + "\\Otro Comando.ComInc")
        else:
            copiar(base, sonda)
    if active == "otro":
        otro = BO("IntPrj", "Otro", est, path="\\vicen.IntUser\\Estudios\\Otro.IntPrj")
        BAPP.project = otro
    else:
        BAPP.project = ref if active == "ref" else lab
    BAPP.case = base
    BAPP.scenario = esc
    return BAPP, lab, ref, study, base, esc


def config(tmp):
    bns["LOG"] = os.path.join(tmp, "bootstrap.jsonl")
    bns["ARTEFACTO"] = os.path.join(tmp, "estado.json")
    bns["PROVENANCE"] = os.path.join(tmp, "provenance.json")
    bns["CHECKPOINT"] = os.path.join(tmp, "checkpoint.json")


def escribir_checkpoint(tmp, **cambios):
    d = dict(token=TOKEN_H4, resuelto=True, estado_sucio="RESUELTO_POR_USUARIO", proyecto=PRJ_LAB,
             fecha="2026-11-09T00:00:00", metodo="guardar/descartar explicitamente en PF",
             evidencia="captura y diario revisados por el usuario")
    d.update(cambios)
    with open(os.path.join(tmp, "checkpoint.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)


def preparar(active="lab", **kw):
    app, lab, ref, study, base, esc = build_bootstrap(active=active, **kw)
    tmp = tempfile.mkdtemp(prefix="bootstrap_ref_test_")
    config(tmp)
    bns["powerfactory"] = types.SimpleNamespace(GetApplication=lambda: app)
    arranques = []
    bns["arrancar"] = lambda script, etiqueta: arranques.append(etiqueta)
    return app, lab, ref, study, base, esc, tmp, arranques


def sin_retiming(lab, ref, study, base, esc):
    for o in (lab, ref, study, base, esc):
        for c in getattr(o, "calls", []):
            assert c[0] not in ("SetStudyTime", "CreateObject"), (o.GetFullName(), c)


def test_exito():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    i_time = base.attrs["iStudyTime"]
    bns["main"]()
    assert lab.calls and lab.calls[0][0] == "CreateVersion", lab.calls
    assert any(c == "Activate" for c in ref.calls), ref.calls
    assert app.project is ref
    assert app.case is not None and app.case.GetFullName() == CASO_SONDA, app.case
    assert app.scenario is not None and app.scenario.GetFullName() == ESC_REF, app.scenario
    assert arranques == ["diagnostico_ref"], arranques
    assert base.attrs["iStudyTime"] == i_time
    sin_retiming(lab, ref, study, base, esc)
    original = [o for o in study.GetContents() if o.loc_name == "Base SEN"][0]
    copy = [o for o in study.GetContents() if o.loc_name == "Base SEN_SONDA_20261109"][0]
    assert original is base
    assert [o.loc_name for o in copy.GetContents()] == [o.loc_name for o in base.GetContents()]
    assert os.path.exists(bns["PROVENANCE"]), "debe registrar procedencia"
    art = json.load(open(bns["ARTEFACTO"], encoding="utf-8"))
    assert art["etapa"] == "listo_para_puente", art
    assert art["caso"] == CASO_SONDA and art["escenario"] == ESC_REF, art


def test_sin_checkpoint():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    bns["main"]()
    assert not any(c[0] == "CreateVersion" for c in lab.calls), lab.calls
    assert not any(c == "Activate" for c in ref.calls), ref.calls
    assert not any(c[0] == "AddCopy" for c in study.calls), study.calls
    assert arranques == []
    art = json.load(open(bns["ARTEFACTO"], encoding="utf-8"))
    assert art["etapa"] == "abortado_estado_lab_no_verificado", art
    assert art["estado_sucio"] == "UNKNOWN", art


def test_checkpoint_invalido():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp, token="otro-token")
    bns["main"]()
    assert not any(c[0] == "CreateVersion" for c in lab.calls), lab.calls
    assert arranques == []


def test_proyecto_desconocido():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(active="otro")
    escribir_checkpoint(tmp)
    bns["main"]()
    assert arranques == [], "proyecto desconocido no debe arrancar ningún puente"
    art = json.load(open(bns["ARTEFACTO"], encoding="utf-8"))
    assert art["etapa"] == "abortado_proyecto_no_autorizado", art


def test_sin_proyecto():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    app.project = None
    escribir_checkpoint(tmp)
    bns["main"]()
    assert arranques == []
    art = json.load(open(bns["ARTEFACTO"], encoding="utf-8"))
    assert art["etapa"] == "abortado_sin_proyecto", art


def test_fallo_version():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    app.fail_version = True
    try:
        bns["main"]()
        raise AssertionError("el fallo de versión debía abortar")
    except RuntimeError:
        pass
    assert not any(c == "Activate" for c in ref.calls), ref.calls
    assert not any(c[0] == "AddCopy" for c in study.calls), study.calls
    assert arranques == []


def test_original_cambia():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    app.mutar_original = True
    try:
        bns["main"]()
        raise AssertionError("el cambio del original debía abortar")
    except RuntimeError as e:
        assert "modificó el caso original" in str(e), e
    assert arranques == [], "no debe arrancar el puente si el original cambió"


def test_copia_none():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    app.fail_copy = True
    try:
        bns["main"]()
        raise AssertionError("AddCopy None debía abortar")
    except RuntimeError as e:
        assert "devolvió None" in str(e), e
    assert arranques == []


def test_sin_caso_activo_tras_copia():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    app.ignorar_activate_caso = "Base SEN_SONDA_20261109"
    try:
        bns["main"]()
        raise AssertionError("sin caso SONDA activo debía abortar")
    except RuntimeError as e:
        assert "no quedó activa" in str(e), e
    assert arranques == [], "no debe arrancar el puente sin caso activo verificado"


def test_copia_existente_sin_procedencia():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(existing_sonda=True)
    escribir_checkpoint(tmp)
    try:
        bns["main"]()
        raise AssertionError("copia sin procedencia debía abortar")
    except RuntimeError as e:
        assert "procedencia" in str(e), e
    assert arranques == []


def test_copia_existente_con_procedencia():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(existing_sonda=True)
    escribir_checkpoint(tmp)
    foto = bns["foto_caso"](base)
    with open(bns["PROVENANCE"], "w", encoding="utf-8") as f:
        json.dump(dict(token=bns["TOKEN_PROVENANCE"], proyecto=PRJ_REF, original=CASO_REF, copia=CASO_SONDA,
                       huella=bns["huella"](foto), creada="2026-11-09T00:00:00"), f)
    bns["main"]()
    assert arranques == ["diagnostico_ref"], arranques
    assert app.case.GetFullName() == CASO_SONDA
    assert not any(c[0] == "AddCopy" for c in study.calls), "no debe crear otra copia"


def test_copia_existente_distinta():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(existing_sonda=True, sonda_distinta=True)
    escribir_checkpoint(tmp)
    foto = bns["foto_caso"](base)
    with open(bns["PROVENANCE"], "w", encoding="utf-8") as f:
        json.dump(dict(token=bns["TOKEN_PROVENANCE"], proyecto=PRJ_REF, original=CASO_REF, copia=CASO_SONDA,
                       huella=bns["huella"](foto), creada="2026-11-09T00:00:00"), f)
    try:
        bns["main"]()
        raise AssertionError("copia distinta no debía reutilizarse")
    except RuntimeError as e:
        assert "no coincide" in str(e), e
    assert arranques == []


def test_reintento_sin_respaldo():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(active="ref")
    escribir_checkpoint(tmp)
    try:
        bns["main"]()
        raise AssertionError("reintento sin respaldo debía abortar")
    except RuntimeError as e:
        assert "respaldo" in str(e), e
    assert arranques == []


def test_reintento_con_respaldo():
    app, lab, ref, study, base, esc, tmp, arranques = preparar(active="ref")
    escribir_checkpoint(tmp)
    lab.versions.append(BO("IntVersion", VERSION_RESPALDO, None,
                           path=lab.GetFullName() + "\\Versions.IntVersionman\\" + VERSION_RESPALDO + ".IntVersion"))
    bns["main"]()
    assert arranques == ["diagnostico_ref"], arranques
    assert app.case.GetFullName() == CASO_SONDA


def test_fallo_parcial_artefacto():
    app, lab, ref, study, base, esc, tmp, arranques = preparar()
    escribir_checkpoint(tmp)
    app.mutar_original = True
    bns["entrada"]()          # el handler de __main__ debe registrar y NO arrancar fallback
    assert arranques == [], "el handler de fallo no debe arrancar ningún puente"
    art = json.load(open(bns["ARTEFACTO"], encoding="utf-8"))
    assert art["etapa"] == "fallo_parcial", art
    assert art["rollback"].startswith("activar_lab"), art
    assert art["copia_puede_persistir"] is True
    assert "deshace" in art["nota_rollback"]
    assert any("AddCopy" in m for m in art["mutaciones_de_esta_corrida"]), art
    assert app.project is lab, "el rollback debe reactivar el laboratorio"


if __name__ == "__main__":
    test_exito()
    test_sin_checkpoint()
    test_checkpoint_invalido()
    test_proyecto_desconocido()
    test_sin_proyecto()
    test_fallo_version()
    test_original_cambia()
    test_copia_none()
    test_sin_caso_activo_tras_copia()
    test_copia_existente_sin_procedencia()
    test_copia_existente_con_procedencia()
    test_copia_existente_distinta()
    test_reintento_sin_respaldo()
    test_reintento_con_respaldo()
    test_fallo_parcial_artefacto()
    print("OK test_pf_bridge_bootstrap_ref: checkpoint H4, procedencia, post-copia y fallo honesto")
