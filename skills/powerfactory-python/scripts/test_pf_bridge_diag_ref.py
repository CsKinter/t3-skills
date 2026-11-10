"""Pruebas de la política de diagnóstico Ref sin PowerFactory (mocks puros).

Cubre el invariante crítico que el test anterior no probaba:
  - Execute exige Ref + Base SEN_SONDA_20261109 + Domingo Madrugada ACTIVOS, no solo que el comando cuelgue
    de la copia; un comando del original (o copiado al original) se rechaza.
  - Deactivate de casos/escenarios y activación del laboratorio se rechazan.
  - CreateVersion no está expuesto al puente.
  - cambiar_caso inyectado solo reafirma CASO_SONDA/ESC_REF exactos.
  - Cero retiming/stages al arrancar: abrir() y main("diagnostico_ref") no crean stages ni tocan la hora.
"""
import json
import os
import sys
import tempfile
import types

sys.modules.setdefault("powerfactory", types.ModuleType("powerfactory"))

SCRIPTS = r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts"
SRC = os.path.join(SCRIPTS, "pf_bridge.py")

fuente = open(SRC, encoding="utf-8").read()
# Quitar la llamada final main(...) para cargar solo las definiciones.
fuente = fuente[:fuente.rfind("\nmain(")]
ns = {"__name__": "pf_bridge_test", "__file__": SRC}
exec(compile(fuente, SRC, "exec"), ns)

PoliticaDiagnosticoRef = ns["PoliticaDiagnosticoRef"]
ErrorModificacion = ns["ErrorModificacion"]
PRJ_LAB = ns["PRJ_LAB"]
PRJ_REF = ns["PRJ_REF"]
REF_CASOS = ns["REF_CASOS"]
CASO_REF = ns["CASO_REF"]
CASO_SONDA = ns["CASO_SONDA"]
ESC_REF = ns["ESC_REF"]


class FakeObj(object):
    def __init__(self, cls, fn, parent=None, app=None):
        self._cls, self._fn, self._parent, self._app = cls, fn, parent, app
        self.loc_name = fn.rsplit("\\", 1)[-1].split(".")[0]
        self.attrs = {"iStudyTime": 1793825170, "iModified": 0, "tstop": 1.0, "iopt_show": 0}
        self.calls = []
        self._children = []

    def GetClassName(self):
        return self._cls

    def GetFullName(self):
        return self._fn

    def GetParent(self):
        return self._parent

    def GetAttribute(self, k):
        if k not in self.attrs:
            raise AttributeError(k)
        return self.attrs[k]

    def SetAttribute(self, k, v):
        self.calls.append(("SetAttribute", k, v))
        self.attrs[k] = v

    def GetContents(self, patron="*", recursive=0):
        return list(self._children)

    def Activate(self):
        self.calls.append(("Activate",))
        if self._app is not None:
            if self._cls == "IntPrj":
                self._app.project = self
            elif self._cls == "IntCase":
                self._app.case = self
            elif self._cls == "IntScenario":
                self._app.scenario = self
        return 0

    def AddCopy(self, origen, nombre):
        self.calls.append(("AddCopy", origen.GetFullName(), nombre))
        return FakeObj("IntCase", self._fn + "\\" + nombre + ".IntCase", self, self._app)

    def CreateVersion(self, *a, **k):
        self.calls.append(("CreateVersion", a, k))
        return FakeObj("IntVersion", self._fn + "\\Versions.IntVersionman\\BACKUP.IntVersion", self, self._app)


class FakeApp(object):
    def __init__(self, proyecto):
        self.project = proyecto
        self.case = None
        self.scenario = None
        self.folders = {}
        self.calls = []
        self.msg = []

    def GetActiveProject(self):
        return self.project

    def GetActiveStudyCase(self):
        return self.case

    def GetActiveScenario(self):
        return self.scenario

    def GetProjectFolder(self, clave):
        return self.folders.get(clave)

    def GetOutputWindow(self):
        raise RuntimeError("sin Output Window en el mock")

    def PrintPlain(self, m):
        self.msg.append(("plain", str(m)))

    PrintInfo = PrintWarn = PrintError = PrintPlain


def build():
    app = FakeApp(None)
    lab = FakeObj("IntPrj", PRJ_LAB, app=app)
    ref = FakeObj("IntPrj", PRJ_REF, app=app)
    casos = FakeObj("IntPrjfolder", REF_CASOS, ref, app)
    base = FakeObj("IntCase", CASO_REF, casos, app)
    sonda = FakeObj("IntCase", CASO_SONDA, casos, app)
    casos._children = [base, sonda]
    scen_folder = FakeObj("IntPrjfolder", PRJ_REF + "\\Operation Scenarios.IntPrjfolder", ref, app)
    domingo = FakeObj("IntFolder", PRJ_REF + "\\Operation Scenarios.IntPrjfolder\\3. Domingo.IntFolder",
                      scen_folder, app)
    esc = FakeObj("IntScenario", ESC_REF, domingo, app)
    domingo._children = [esc]
    scen_folder._children = [domingo, esc]
    cominc_sonda = FakeObj("ComInc", CASO_SONDA + "\\Calculation of Initial Condition.ComInc", sonda, app)
    comsim_sonda = FakeObj("ComSim", CASO_SONDA + "\\Run Simulation.ComSim", sonda, app)
    cominc_orig = FakeObj("ComInc", CASO_REF + "\\Calculation of Initial Condition.ComInc", base, app)
    # Mismo loc_name de copia en una carpeta con prefijo parecido: _en_caso_sonda no debe confundirla.
    casos_x = FakeObj("IntPrjfolder", REF_CASOS + "_X", ref, app)
    sonda_prefijo = FakeObj("IntCase", REF_CASOS + "_X\\Base SEN_SONDA_20261109.IntCase", casos_x, app)
    otro_caso = FakeObj("IntCase", REF_CASOS + "\\Otro Caso.IntCase", casos, app)
    otro_prj = FakeObj("IntPrj", "\\vicen.IntUser\\Estudios\\Otro.IntPrj", app=app)
    casos._children = [base, sonda, otro_caso]
    app.folders = {"study": casos, "scen": scen_folder}
    app.project = lab
    return dict(app=app, lab=lab, ref=ref, casos=casos, base=base, sonda=sonda, esc=esc,
                cominc_sonda=cominc_sonda, comsim_sonda=comsim_sonda, cominc_orig=cominc_orig,
                sonda_prefijo=sonda_prefijo, otro_caso=otro_caso, otro_prj=otro_prj)


def debe_fallar(fn, etiqueta, texto=None):
    try:
        fn()
    except ErrorModificacion as e:
        if texto is not None:
            assert texto in str(e), "%s: mensaje inesperado %r" % (etiqueta, str(e))
        return
    raise AssertionError("debía rechazar: %s" % etiqueta)


def policy_tests():
    m = build()
    app, lab, ref, casos = m["app"], m["lab"], m["ref"], m["casos"]
    base, sonda, esc = m["base"], m["sonda"], m["esc"]
    cominc_sonda, comsim_sonda, cominc_orig = m["cominc_sonda"], m["comsim_sonda"], m["cominc_orig"]
    tmp = tempfile.mkdtemp(prefix="pf_diag_ref_test_")
    pol = PoliticaDiagnosticoRef(app, tmp)
    ns["CONTEXTO"] = ns["Contexto"](app)

    # 0. abrir() no retimea ni crea stages (stage counts/time unchanged).
    i_study_time = base.attrs["iStudyTime"]
    pol.abrir()
    for o in (app, lab, ref, casos, base, sonda, esc):
        for c in getattr(o, "calls", []):
            assert c[0] not in ("SetStudyTime", "CreateObject", "CreateVersion", "Activate"), (o.GetFullName(), c)
    assert base.attrs["iStudyTime"] == i_study_time
    assert pol.diario and pol.diario[0]["retiming"] is False

    # 1. Activate proyecto: solo Ref exacto; el laboratorio queda fuera del puente.
    pol.metodo(ref, "Activate", ref.Activate)()
    assert app.project is ref
    debe_fallar(lambda: pol.metodo(lab, "Activate", lab.Activate)(), "Activate laboratorio")
    debe_fallar(lambda: pol.metodo(m["otro_prj"], "Activate", m["otro_prj"].Activate)(), "Activate otro proyecto")
    debe_fallar(lambda: pol.metodo(ref, "Deactivate", ref.Activate)(), "Deactivate Ref")

    # 2. CreateVersion NO se expone al puente (respaldo = paso manual del bootstrap).
    debe_fallar(lambda: pol.metodo(lab, "CreateVersion", lab.CreateVersion)("BACKUP", 0, 0, 0, "x"),
                "CreateVersion laboratorio")
    debe_fallar(lambda: pol.metodo(ref, "CreateVersion", ref.CreateVersion)("X"), "CreateVersion Ref")

    # 3. AddCopy: exige contexto Ref + Base SEN + Domingo Madrugada activos.
    app.project, app.case, app.scenario = ref, base, esc
    casos._children = [base]          # sin copia previa
    copia = pol.metodo(casos, "AddCopy", casos.AddCopy)(base, "Base SEN_SONDA_20261109")
    assert copia.loc_name == "Base SEN_SONDA_20261109"
    casos._children = [base, sonda]
    debe_fallar(lambda: pol.metodo(casos, "AddCopy", casos.AddCopy)(base, "Otra"), "AddCopy otro nombre")
    app.case = base
    app.project = lab
    debe_fallar(lambda: pol.metodo(casos, "AddCopy", casos.AddCopy)(base, "Base SEN_SONDA_20261109"),
                "AddCopy con proyecto equivocado")
    app.project, app.case = ref, base

    # 4. Execute: el caso ACTIVO manda, no el padre del comando.
    app.project, app.case, app.scenario = ref, base, esc
    debe_fallar(lambda: pol.metodo(cominc_sonda, "Execute", cominc_sonda.Activate)(),
                "Execute SONDA con Base SEN activo", "Base SEN_SONDA_20261109")
    app.project, app.case, app.scenario = lab, sonda, esc
    debe_fallar(lambda: pol.metodo(cominc_sonda, "Execute", cominc_sonda.Activate)(),
                "Execute con proyecto no Ref")
    app.project, app.case, app.scenario = ref, sonda, None
    debe_fallar(lambda: pol.metodo(cominc_sonda, "Execute", cominc_sonda.Activate)(),
                "Execute sin escenario exacto", "Domingo Madrugada")
    app.scenario = esc
    pol.metodo(cominc_sonda, "Execute", cominc_sonda.Activate)()
    assert cominc_sonda.calls == [("Activate",)]
    # Comando del original, aunque sea el mismo tipo: se rechaza.
    debe_fallar(lambda: pol.metodo(cominc_orig, "Execute", cominc_orig.Activate)(),
                "Execute comando del original")
    # Copia del comando dentro del caso original: su ancestro es CASO_REF.
    copia_en_original = FakeObj("ComInc", CASO_REF + "\\Copia.ComInc", base, app)
    debe_fallar(lambda: pol.metodo(copia_en_original, "Execute", copia_en_original.Activate)(),
                "Execute comando copiado al original")
    # Prefijo/duplicado de nombre no confunde la ruta.
    assert pol._en_caso_sonda(sonda) is True
    assert pol._en_caso_sonda(base) is False
    assert pol._en_caso_sonda(m["sonda_prefijo"]) is False

    # 5. SetAttribute: mismo contexto activo + lista blanca.
    pol.metodo(comsim_sonda, "SetAttribute", comsim_sonda.SetAttribute)("tstop", 0.01)
    debe_fallar(lambda: pol.metodo(comsim_sonda, "SetAttribute", comsim_sonda.SetAttribute)("foo", 1),
                "atributo fuera de lista")
    debe_fallar(lambda: pol.metodo(cominc_orig, "SetAttribute", cominc_orig.SetAttribute)("tstop", 0.01),
                "SetAttribute en original")
    app.case = base
    debe_fallar(lambda: pol.metodo(comsim_sonda, "SetAttribute", comsim_sonda.SetAttribute)("tstop", 0.02),
                "SetAttribute con original activo")
    app.case = sonda

    # 6. Deactivate de casos y escenarios: rechazado.
    for obj in (base, sonda):
        debe_fallar(lambda o=obj: pol.metodo(o, "Deactivate", o.Activate)(), "Deactivate %s" % obj.loc_name)
    debe_fallar(lambda: pol.metodo(esc, "Deactivate", esc.Activate)(), "Deactivate escenario")
    # Activate escenario exacto permitido; otro escenario rechazado.
    pol.metodo(esc, "Activate", esc.Activate)()
    assert app.scenario is esc
    otro_esc = FakeObj("IntScenario", PRJ_REF + "\\Operation Scenarios.IntPrjfolder\\Otro.IntScenario", None, app)
    debe_fallar(lambda: pol.metodo(otro_esc, "Activate", otro_esc.Activate)(), "Activate otro escenario")

    # 7. cambiar_caso inyectado: misma allowlist/guarda, sin casos arbitrarios.
    app.project, app.case, app.scenario = ref, base, esc
    debe_fallar(lambda: pol.cambiar_caso_diagnostico("Base SEN"), "cambiar_caso al original")
    debe_fallar(lambda: pol.cambiar_caso_diagnostico("Otro Caso"), "cambiar_caso a otro caso")
    debe_fallar(lambda: pol.cambiar_caso_diagnostico(), "cambiar_caso sin objetivo")
    debe_fallar(lambda: pol.cambiar_caso_diagnostico("Base SEN_SONDA_20261109", "Otro"),
                "cambiar_caso a otro escenario")
    r = pol.cambiar_caso_diagnostico("Base SEN_SONDA_20261109")
    assert app.case is sonda and r["caso"] == "Base SEN_SONDA_20261109"
    r = pol.cambiar_caso_diagnostico(None, "Domingo Madrugada")
    assert app.scenario is esc and r["escenario"] == "Domingo Madrugada"
    app.project = lab
    debe_fallar(lambda: pol.cambiar_caso_diagnostico("Base SEN_SONDA_20261109"),
                "cambiar_caso con proyecto no Ref")

    # 8. Prohibidos y lectura.
    debe_fallar(lambda: pol.metodo(lab, "Save", lab.Activate)(), "Save")
    debe_fallar(lambda: pol.metodo(lab, "SaveAs", lab.Activate)("x"), "SaveAs")
    debe_fallar(lambda: pol.metodo(lab, "SetStudyTime", lab.Activate)(1), "SetStudyTime")
    pol.metodo(ref, "GetContents", lambda *a, **k: [])("*", 0)


def main_startup_tests():
    # Arranque completo main("diagnostico_ref"): cero SetStudyTime/CreateObject/retiming.
    m = build()
    app, lab, ref, base, sonda, esc = m["app"], m["lab"], m["ref"], m["base"], m["sonda"], m["esc"]
    app.project, app.case, app.scenario = lab, None, None
    tmp = tempfile.mkdtemp(prefix="pf_diag_ref_start_")
    os.makedirs(os.path.join(tmp, "inbox"), exist_ok=True)
    mod = types.ModuleType("powerfactory")
    mod.GetApplication = lambda: app
    ns["powerfactory"] = mod
    ns["BRIDGE_DIR"] = tmp
    ns["ALLOW_CALC"] = False
    ns["IDLE_MINUTES"] = 0          # el bucle sale en la primera comprobación de inactividad
    ns["main"]("diagnostico_ref")
    for o in (lab, ref, m["casos"], base, sonda, esc):
        for c in getattr(o, "calls", []):
            assert c[0] not in ("SetStudyTime", "CreateObject", "CreateVersion", "Activate"), (o.GetFullName(), c)
    st = json.load(open(os.path.join(tmp, "status.json"), encoding="utf-8"))
    assert st["modo"].startswith("diagnóstico Ref"), st["modo"]
    assert st.get("retiming") is False
    # H9: la telemetría no puede decir allow_calc=False mientras Execute está permitido.
    assert st.get("allow_calc") is True, st


def main_command_tests():
    # main end-to-end: cambiar_caso inyectado rechaza casos arbitrarios y permite solo el exacto.
    m = build()
    app, ref, base, sonda, esc = m["app"], m["ref"], m["base"], m["sonda"], m["esc"]
    app.project, app.case, app.scenario = ref, base, esc
    tmp = tempfile.mkdtemp(prefix="pf_diag_ref_cmd_")
    os.makedirs(os.path.join(tmp, "inbox"), exist_ok=True)
    mod = types.ModuleType("powerfactory")
    mod.GetApplication = lambda: app
    ns["powerfactory"] = mod
    ns["BRIDGE_DIR"] = tmp
    ns["IDLE_MINUTES"] = 60
    ns["ALLOW_CALC"] = False
    cmd = os.path.join(tmp, "inbox", "c1.py")
    open(cmd, "w", encoding="utf-8").write(
        'resultado["otro"] = "PERMITIDO"\n'
        'try:\n'
        '    cambiar_caso("Otro Caso")\n'
        'except Exception as e:\n'
        '    resultado["otro"] = type(e).__name__ + ": " + str(e)\n'
        'resultado["exacto"] = cambiar_caso("Base SEN_SONDA_20261109")["caso"]\n'
        'open(%r, "w").write("")\n' % os.path.join(tmp, "inbox", "STOP"))
    ns["main"]("diagnostico_ref")
    res = json.load(open(os.path.join(tmp, "outbox", "c1.json"), encoding="utf-8"))
    assert res.get("ok") is True, res
    assert str(res["resultado"]["otro"]).startswith("ErrorModificacion"), res["resultado"]
    assert res["resultado"]["exacto"] == "Base SEN_SONDA_20261109", res["resultado"]


if __name__ == "__main__":
    policy_tests()
    main_startup_tests()
    main_command_tests()
    print("OK test_pf_bridge_diag_ref: Execute/contexto exactos, sin retiming y adversarios")
