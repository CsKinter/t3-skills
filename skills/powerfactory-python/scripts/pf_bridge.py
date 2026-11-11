"""Puente PowerFactory <-> Claude sobre la sesión de PF abierta (ComPython).

Qué hace: mientras corre, revisa una carpeta (BRIDGE_DIR\\inbox). Cada archivo .py que aparece se ejecuta contra la
sesión activa (proyecto, caso de estudio y variations del usuario) y el resultado queda en BRIDGE_DIR\\outbox\\<id>.json
(salida de print, error con traceback, y el dict `resultado` que llene el comando). Todo queda en bridge.log.

Tres modos (el usuario autoriza modo y alcance; el agente puede arrancarlos dentro de esa autorización):

- "lectura" (este archivo): el comando recibe una vista del `app` que sólo permite leer atributos y llamar métodos
  Get*/Is*/Has*/Print*/Search*/Find*/Count*. Todo lo demás se rechaza con SoloLectura.
- "modificacion" (lanzar pf_bridge_modificar.py): al arrancar crea y activa la variation "Claude_revisar_<fecha>" con un
  stage a la hora de estudio, y verifica con una prueba que PF registra ahí. Reglas:
    * objetos de la red (bajo un ElmNet): se modifican; cada escritura se verifica (quedó en el stage de Claude o, si hay
      un escenario de operación activo, en el escenario). Si no quedó en ninguno, se revierte y se aborta el comando.
    * todo lo demás (tipos, características, escalas, comandos, caso de estudio, gráficos): NO se toca el original;
      `revisar(obj)` crea una copia junto al original, se modifica la copia y se repunta desde la red.
    * lo que crea o copia Claude lleva la marca "[CdN]" en la descripción y un nombre limpio (15-10-2026; antes el sufijo
      "_CdN"/"_revisar" en el nombre, que se sigue reconociendo). Sólo lo marcado se puede escribir, renombrar o borrar.
    * nunca se guarda el escenario de operación, ni se activan/desactivan casos, escenarios o variations ajenas.
    * cada cambio queda en un diario (BRIDGE_DIR\\diario_<variation>.json) con el valor anterior: `deshacer(n)` revierte
      los últimos n (o todos). Desactivar la variation de Claude devuelve además toda la red a su estado original.
- "limpieza" (lanzar pf_bridge_limpieza.py): escritura directa sobre el proyecto activo, sin variation de sesión; cada
  llamada que modifica queda en diario_limpieza_<fecha>.jsonl (incluidas AddCopy y Execute). Guardas: nada con "_secure"
  en la ruta y nunca Save() de escenarios. No hay deshacer: el diario registra y no revierte.

Cómo detenerlo: crear BRIDGE_DIR\\inbox\\STOP (o `python pf_send.py detener`), el botón Break de PF, o esperar
IDLE_MINUTES sin comandos. Mientras corre, PowerFactory queda ocupado (título "NON-INTERACTIVE MODE"): es normal.

Uso en PF: crear un objeto ComPython (Python Script), apuntar "Script" a este archivo (o a pf_bridge_modificar.py /
pf_bridge_limpieza.py, con autorización para ese modo y alcance) y ejecutarlo. Del lado de Claude: scripts/pf_send.py.
"""
import contextlib
import datetime
import io
import json
import os
import re
import sys
import time
import traceback

import powerfactory

# ------------------------------------------------------------------------------------------------ configuración
BRIDGE_DIR = os.path.join(os.path.expanduser("~"), "pf_bridge")
MODO = "lectura"           # pf_bridge_modificar.py lo cambia a "modificacion"
ALLOW_CALC = False         # en modo lectura, permitir Execute() de comandos de cálculo
IDLE_MINUTES = 120          # se detiene solo tras este tiempo sin comandos
MAX_HOURS = 8              # tope de la sesión del puente
POLL_S = 0.5
MAX_SALIDA = 200000        # caracteres de print que se devuelven
SUFIJO = "_CdN"          # sufijo de lo que crea Claude (usuario, 09-10-2026: "_CdN" de Cumbres del Ñuble)
SUFIJOS = ("_CdN", "_revisar")   # "_revisar" = convención anterior; los objetos que ya lo tienen siguen siendo propios
tiene_sufijo = lambda n: any(x in (n or "") for x in SUFIJOS)
termina_sufijo = lambda n: any((n or "").endswith(x) for x in SUFIJOS)
PROTEGIDO = "_secure"   # escenarios/carpetas intocables (convención invertida, 07-10-2026)
MARCA = "[claude-puente]"   # en la descripción de las variations de Claude (para reconocerlas tras renombrarlas)
MARCA_OBJ = "[CdN]"         # en la descripción de lo que crea o copia Claude (usuario, 15-10-2026: «el sufijo a la descripción,
                            # no al nombre»): el nombre queda limpio y el objeto sigue siendo reconocible como copia de trabajo


def marcado(o):
    """Objeto de trabajo de Claude: marca [CdN] en la descripción o, convención anterior, nombre terminado en _CdN/_revisar."""
    try:
        if termina_sufijo(o.loc_name):
            return True
        return MARCA_OBJ in " ".join(str(x) for x in as_list(o.GetAttribute("desc")))
    except Exception:
        return False


def marcar(o):
    """Agrega la marca a la descripción conservando lo que había. False si la clase no tiene descripción."""
    try:
        d = [str(x) for x in as_list(o.GetAttribute("desc")) if str(x)]
        if MARCA_OBJ not in " ".join(d):
            o.SetAttribute("desc", d + [MARCA_OBJ])
        return MARCA_OBJ in " ".join(str(x) for x in as_list(o.GetAttribute("desc")))
    except Exception:
        return False

PREFIJOS_LECTURA = ("Get", "Is", "Has", "Print", "Search", "Find", "Count")
BLOQUEADOS_RO = {"GetFromStudyCase"}                        # crea el comando en el caso de estudio si no existe
CALCULO = {"ComLdf", "ComShc", "ComInc", "ComSim", "ComVstab", "ComDiff", "ComSimoutage"}   # ComVstab: sensibilidades / factores de distribución (07-10-2026); ComDiff: flujo diferencial (comparación de resultados on/off), 08-10-2026

# --- Diagnóstico Ref acotado (2026-11-09, autorizado explícitamente por el usuario) -------------------------------
# Rutas exactas verificadas contra GetFullName() en PF 2025 SP4 (Ñ = U+00D1). No cambiar por loc_name ni por prefijo.
PRJ_LAB = "\\vicen.IntUser\\Estudios\\ViQSilent_RMS_Lab_20261104.IntPrj"
PRJ_REF = "\\vicen.IntUser\\Estudios\\[ER] PE Cumbres del Ñuble\\Ref\\2608-BD-OP-COORD-DMAP.IntPrj"
REF_CASOS = PRJ_REF + "\\Study Cases.IntPrjfolder"
CASO_REF = REF_CASOS + "\\Base SEN.IntCase"
CASO_SONDA = REF_CASOS + "\\Base SEN_SONDA_20261109.IntCase"
ESC_REF = PRJ_REF + "\\Operation Scenarios.IntPrjfolder\\3. Domingo.IntFolder\\Domingo Madrugada.IntScenario"
# atributos que PF guarda en el escenario de operación (no en la variation) cuando hay un escenario activo
OPERATIVOS = {"outserv", "nntap", "nntap0", "ntap", "pgini", "qgini", "sgini", "cosgini", "usetp", "qsetp", "pf_recap",
              "plini", "qlini", "slini", "coslini", "scale0", "ncapa", "ncapx", "i_mot", "av_mode", "iv_mode", "ip_ctrl",
              "Pmax_uc", "Pmin_uc", "Qmax", "Qmin", "pmaxratf", "ngnum", "nbnum", "on_off", "isw", "usp_low", "usp_up",
              "i_ctrl", "iQorient", "cQ_max", "cQ_min", "Vtarget", "vtarget", "dvmax", "dvmin"}   # Vtarget/dvmax/dvmin: consigna de tensión de la barra (ElmTerm), por escenario (usuario, 08-10-2026); iQorient: orientación de Q del controlador de estación; cQ_max/cQ_min: límites de reactivo de ElmGenstat (PF los guarda en el escenario, 07-10-2026)
# guarda contra errores propios (no contra un adversario): el comando debe usar `app`, nunca el módulo
PROHIBIDO_EN_FUENTE = [r"\bimport\s+powerfactory", r"\bfrom\s+powerfactory", r"GetApplication", r"_crudo_",
                       r"sys\.modules", r"\bsubprocess\b", r"os\.system", r"\bctypes\b", r"shutil\.rmtree",
                       r"os\.remove", r"os\.unlink", r"POLITICA"]


class SoloLectura(Exception):
    pass


class ErrorModificacion(Exception):
    pass


def _es_objeto_pf(v):
    return not isinstance(v, Vista) and hasattr(v, "GetFullName") and hasattr(v, "GetClassName")


def envolver(v):
    if isinstance(v, Vista):
        return v
    if _es_objeto_pf(v):
        return Vista(v)
    if isinstance(v, list):
        return [envolver(x) for x in v]
    if isinstance(v, tuple):
        return tuple(envolver(x) for x in v)
    return v


def desenvolver(v):
    if isinstance(v, Vista):
        return object.__getattribute__(v, "_crudo_")
    if isinstance(v, list):
        return [desenvolver(x) for x in v]
    if isinstance(v, tuple):
        return tuple(desenvolver(x) for x in v)
    return v


def _clase(obj):
    try:
        return obj.GetClassName()
    except Exception:
        return ""


def _envuelta(fn):
    def llamada(*a, **kw):
        return envolver(fn(*[desenvolver(x) for x in a], **{k: desenvolver(x) for k, x in kw.items()}))
    return llamada


# ------------------------------------------------------------------------------------------------ contexto (caso / escenario)
CONTEXTO_CLASES = ("IntScenario", "IntCase")


class Contexto(object):
    """Cambiar de caso de estudio y de escenario de operación. Permitido en ambos modos (no modifica datos), con dos
    resguardos: no se cambia si el escenario activo tiene cambios sin guardar (PF los guardaría o perdería), y al
    detener el puente se vuelve al caso y escenario con que partió.
    Orden: primero el caso de estudio (cambia los triggers, p. ej. la temperatura de los límites térmicos), después el
    escenario."""

    def __init__(self, app):
        self.app = app
        self.caso0 = app.GetActiveStudyCase()
        self.esc0 = self._esc()
        self.caso0_fn = self.caso0.GetFullName() if self.caso0 else None
        self.esc0_fn = self.esc0.GetFullName() if self.esc0 else None
        self.historial = []

    def reconectar(self, app):
        self.app = app
        self.caso0 = _resolver(app, self.caso0_fn)
        self.esc0 = _resolver(app, self.esc0_fn)

    def _esc(self):
        try:
            return self.app.GetActiveScenario()
        except Exception:
            return None

    def _sin_cambios(self):
        e = self._esc()
        if e is not None and get_attr(e, "iModified", 0):
            raise ErrorModificacion("el escenario activo '%s' tiene cambios sin guardar: guárdalo (sólo copias %s, con "
                                    "confirmación del usuario) o descártalo antes de cambiar" % (e.loc_name, SUFIJO))

    def activar(self, obj, nombre, fn):
        clase = _clase(obj)
        actual = self._esc() if clase == "IntScenario" else self.app.GetActiveStudyCase()
        if nombre == "Activate" and actual is not None and actual == obj:
            return 0
        self._sin_cambios()
        r = fn()
        self.historial.append((ahora(), nombre, obj.GetFullName()))
        return r

    def _buscar(self, carpeta, clase, nombre):
        objs = list(self.app.GetProjectFolder(carpeta).GetContents("*." + clase, 1) or [])
        ruta = lambda o: "/".join(x.rsplit(".", 1)[0] for x in o.GetFullName().split("\\"))   # sin ".IntFolder"
        buscado = "/" + nombre.replace("\\", "/").strip("/")
        c = [o for o in objs if o.loc_name == nombre] or [o for o in objs if ruta(o).endswith(buscado)]
        if len(c) != 1:
            raise ErrorModificacion("%s %r: %s" % (clase, nombre, "no existe" if not c else
                                    "ambiguo, usar la ruta (p. ej. 'Base\\\\%s'): %s" % (nombre, [o.GetFullName() for o in c])))
        return c[0]

    def cambiar_caso(self, caso, escenario=None):
        """Activa el caso de estudio y luego el escenario (nombre o ruta final 'Base\\\\Laboral Diurno (25C CS)')."""
        c = self._buscar("study", "IntCase", caso)
        self.activar(c, "Activate", c.Activate)
        if escenario:
            e = self._buscar("scen", "IntScenario", escenario)
            self.activar(e, "Activate", e.Activate)
        return self.actual()

    def actual(self):
        c, e = self.app.GetActiveStudyCase(), self._esc()
        return dict(caso=c.loc_name if c else None, escenario=e.loc_name if e else None,
                    escenario_modificado=bool(get_attr(e, "iModified", 0)) if e else None)

    def restaurar(self):
        try:
            if self.caso0 is not None and not (self.app.GetActiveStudyCase() == self.caso0):
                self.activar(self.caso0, "Activate", self.caso0.Activate)
            if self.esc0 is not None and not (self._esc() == self.esc0):
                self.activar(self.esc0, "Activate", self.esc0.Activate)
            return None
        except Exception as e:
            return str(e)


CONTEXTO = None


# ------------------------------------------------------------------------------------------------ políticas
class PoliticaLectura(object):
    nombre = "solo lectura"

    def metodo(self, obj, nombre, fn):
        if nombre in ("Activate", "Deactivate") and _clase(obj) in CONTEXTO_CLASES:
            return lambda: CONTEXTO.activar(obj, nombre, fn)
        if nombre == "Execute" and ALLOW_CALC and _clase(obj) in CALCULO:
            return _envuelta(fn)
        if nombre in BLOQUEADOS_RO or not nombre.startswith(PREFIJOS_LECTURA):
            raise SoloLectura("%s() no está permitido en modo solo lectura" % nombre)
        return _envuelta(fn)

    def asignar(self, obj, nombre, valor):
        raise SoloLectura("asignar %s no está permitido en modo solo lectura" % nombre)

    def reconectar(self, app):
        pass


def _resolver(app, ruta):
    """Objeto de PF por su ruta completa (tras una reconexión las referencias anteriores quedan inválidas).
    La API de PF 2025 no tiene SearchObject: se recorre la ruta desde el proyecto activo con GetContents."""
    if not ruta:
        return None
    try:
        prj = app.GetActiveProject()
        base = prj.GetFullName()
        if not ruta.startswith(base):
            return None
        obj = prj
        for parte in [x for x in ruta[len(base):].split("\\") if x]:
            hijos = [h for h in (obj.GetContents(parte) or []) if h.GetFullName().endswith("\\" + parte)]
            if not hijos:
                return None
            obj = hijos[0]
        return obj
    except Exception:
        return None


def _raiz(d):
    """Objeto de red al que apunta un delta de stage (None si no se puede leer)."""
    try:
        return d.GetAttribute("root_id")
    except Exception:
        return None


def _igual(a, b):
    """Igualdad tolerante: PF guarda muchos reales en precisión simple (32,8 vuelve como 32,7999992)."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_igual(x, y) for x, y in zip(a, b))
    return a == b


def es_red(obj):
    """True si el objeto cuelga de un ElmNet (red): sus cambios los registra la variation / el escenario."""
    p = obj
    for _ in range(40):
        if p is None:
            return False
        c = _clase(p)
        if c == "ElmNet":
            return True
        if c in ("IntSstage", "IntScheme", "IntPrj", "IntCase", "IntUser"):
            return False
        try:
            p = p.GetParent()
        except Exception:
            return False
    return False


def nombre_libre(padre, base, clase, sufijo=""):
    """Nombre limpio y libre en la carpeta (15-10-2026: la marca va en la descripción; si el nombre existe, « (2)», « (3)»...).
    PF exige nombres únicos por carpeta aunque la clase sea distinta: se comparan todos los hijos."""
    base = (base or clase)[:40 - len(sufijo) - 4]
    existentes = set()
    try:
        existentes = {o.loc_name for o in (padre.GetContents("*") or [])}
    except Exception:
        pass
    n, cand = 1, base + sufijo
    while cand in existentes:
        n += 1
        cand = "%s (%d)%s" % (base, n, sufijo)
    return cand


class PoliticaModificacion(object):
    nombre = "modificación"

    def __init__(self, app, bridge_dir):
        self.app, self.dir = app, bridge_dir
        self.variation = self.stage = None
        self.propios = []                     # objetos creados/copiados por Claude en esta sesión
        self.destino = {}                     # GetFullName -> "variation" | "escenario"
        self.diario, self._crudos = [], []    # entradas serializables y referencias vivas (para deshacer)
        self.ruta_diario = None

    # ---------------------------------------------------------------- arranque: variation + stage verificados
    @staticmethod
    def es_de_claude(v):
        try:
            desc = " ".join(str(x) for x in as_list(v.GetAttribute("desc")))
        except Exception:
            desc = ""
        return v.loc_name.startswith(("Claude_revisar", "Claude_CdN", "Trabajo_")) or MARCA in desc

    def abrir(self):
        """Variation + stage de Claude separados al menos 1 minuto de la última stage activa (PF marca conflicto si dos
        stages con la misma hora tocan el mismo objeto, y no activa ninguna). Reubica las stages Claude anteriores en
        +1, +2... min, reutiliza la última Claude vacía y, si hace falta, adelanta la hora de estudio."""
        app = self.app
        sello = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        nombre = "Trabajo_%s" % sello      # sin "Claude" en el nombre (usuario, 08-10-2026); la marca va en la descripción
        scheme = app.GetProjectFolder("scheme")
        if scheme is None:
            raise ErrorModificacion("no se encontró la carpeta de Variations del proyecto")
        caso = app.GetActiveStudyCase()
        T = caso.GetAttribute("iStudyTime")
        self.ruta_diario = os.path.join(self.dir, "diario_%s.jsonl" % nombre)
        activas = list(app.GetActiveNetworkVariations() or [])
        todas = list(scheme.GetContents("*.IntScheme", 1) or [])
        # Sólo las temporales (Claude_revisar_*) se reubican. Una variation de Claude ya renombrada con nombrar() es una
        # corrección consolidada: conserva su hora y cuenta como ajena para la base (07-10-2026, a pedido del usuario:
        # si se reubicaba, quedaba después de la hora de estudio de otros casos y no se activaba allí).
        mias = [v for v in todas if self.es_de_claude(v) and v.loc_name.startswith(("Claude_revisar", "Claude_CdN", "Trabajo_"))]
        etapas = lambda v: list(v.GetContents("*.IntSstage", 1) or [])
        t_de = lambda s: get_attr(s, "tAcTime", 0) or 0
        ajenas = [(t_de(s), v, s) for v in activas if not any(v == m for m in mias) for s in etapas(v)]
        base = max([t for t, _, _ in ajenas if t <= T] or [T])
        # reutilizar la última Claude vacía (p. ej. la de un arranque fallido)
        vacias = [v for v in mias if all(len(s.GetContents("*", 1) or []) == 0 for s in etapas(v))]
        reuso = max(vacias, key=lambda v: v.loc_name) if vacias else None
        # Todas las temporales, activas o no en este caso: si sólo se reubicaban las activas aquí, una inactiva podía quedar
        # en el mismo minuto que otra activa en otro caso y, si tocan el mismo objeto, PF marca "Variation conflict" y no
        # activa ninguna stage (visto el 07-10-2026: desapareció S/E Tiquel en 03_15 SS).
        previas = sorted([v for v in mias if not (reuso is not None and v == reuso)],
                         key=lambda v: (min([t_de(s) for s in etapas(v)] or [0]), v.loc_name))
        horarios = [(v, base + 60 * (i + 1)) for i, v in enumerate(previas)]
        t_nueva = base + 60 * (len(previas) + 1)
        T2 = max(T, t_nueva)
        saltadas = [(v.loc_name, s.loc_name) for t, v, s in ajenas if T < t <= T2]
        if saltadas:
            raise ErrorModificacion("adelantar la hora de estudio activaría stages ajenas: %s" % saltadas)
        for v, t in horarios:
            for s in etapas(v):
                if t_de(s) != t:
                    antes = t_de(s)
                    s.SetAttribute("tAcTime", t)
                    self._anotar(dict(tipo="hora_stage", obj=s.GetFullName(), antes=antes, despues=t), s)
        if T2 != T:
            caso.SetStudyTime(T2)
            self._anotar(dict(tipo="study_time", obj=caso.GetFullName(), antes=T, despues=T2), caso)
        if reuso is not None:
            self.variation = reuso
            self.stage = (etapas(reuso) or [reuso.CreateObject("IntSstage", reuso.loc_name)])[0]
            nombre = reuso.loc_name
        else:
            self.variation = scheme.CreateObject("IntScheme", nombre)
            self.stage = self.variation.CreateObject("IntSstage", nombre)
        try:
            self.variation.SetAttribute("desc", [MARCA])
        except Exception:
            pass
        self.stage.SetAttribute("tAcTime", t_nueva)
        self.variation.Activate()
        activas = app.GetActiveNetworkVariations() or []
        if self.variation not in list(activas):
            raise ErrorModificacion("la variation %s no quedó activa" % nombre)
        self.stage.Activate()
        rec = None
        try:
            rec = app.GetRecordingStage()
        except Exception:
            pass
        if rec is not None and rec != self.stage:
            raise ErrorModificacion("PF registra en %s, no en el stage de Claude (otro stage más reciente <= hora de "
                                    "estudio)" % rec.GetFullName())
        redes = app.GetCalcRelevantObjects("*.ElmNet") or []
        # la sonda va en una red del modelo (Network Data), nunca en la "Summary Grid" del caso de estudio: ahí PF no
        # permite crear objetos y el arranque caía a solo lectura (visto el 07-10-2026 tras reiniciar PF)
        redes = [r for r in redes if "Study Cases" not in r.GetFullName() and "Summary Grid" not in r.loc_name] or redes
        redes.sort(key=lambda r: ("Network Data" not in r.GetFullName(), r.loc_name))
        if not redes:
            raise ErrorModificacion("no hay redes activas para verificar el registro")
        n0 = self._n_stage()
        sonda = redes[0].CreateObject("IntFolder", "__sonda_claude__")
        crecio = self._n_stage() > n0
        try:
            sonda.Delete()
        except Exception:
            pass
        if not crecio:
            raise ErrorModificacion("la prueba no quedó registrada en el stage de Claude")
        self.var_fn, self.stage_fn = self.variation.GetFullName(), self.stage.GetFullName()
        self._anotar(dict(tipo="inicio", variation=self.variation.GetFullName(), escenario=self._escenario_nombre(),
                          hora_stage=t_nueva, study_time=T2), None)
        return nombre

    # ---------------------------------------------------------------- nombres resumidos
    def nombrar(self, texto):
        """Nombre resumido de la variation de esta sesión ("Ajuste longitudes D418"). Se aplica en el acto: si el puente
        se corta con Break o PF lo desconecta, el cierre no alcanza a correr."""
        self.nombre_final = str(texto).strip()[:40]
        return self._renombrar(self.variation, self.nombre_final)

    def _renombrar(self, v, nuevo):
        scheme = self.app.GetProjectFolder("scheme")
        usados = {x.loc_name for x in (scheme.GetContents("*.IntScheme", 1) or []) if not (x == v)}
        cand, k = nuevo, 2
        while cand in usados:
            cand, k = "%s %d" % (nuevo, k), k + 1
        antes = v.loc_name
        v.SetAttribute("loc_name", cand)
        for s in v.GetContents("*.IntSstage", 1) or []:
            s.SetAttribute("loc_name", cand)
        try:
            v.SetAttribute("desc", [MARCA, "antes: " + antes])
        except Exception:
            pass
        if self.variation is not None and v == self.variation:
            self.var_fn, self.stage_fn = v.GetFullName(), self.stage.GetFullName()
        self._anotar(dict(tipo="renombre", obj=v.GetFullName(), antes=antes, despues=cand), None)
        return cand

    def activar_variation(self, v, nombre="Activate", fn=None):
        """Activa una variation en el caso de estudio activo (cualquiera; p. ej. para llevar una corrección a otro caso).
        Desactivar sólo variations de Claude. Queda en el diario. Acepta el objeto o el nombre (loc_name único)."""
        if isinstance(v, str):
            vs = [x for x in (self.app.GetProjectFolder("scheme").GetContents("*.IntScheme", 1) or []) if x.loc_name == v]
            if len(vs) != 1:
                raise ErrorModificacion("variation %r: %s" % (v, "no existe" if not vs else "ambigua"))
            v = vs[0]
        if nombre == "Deactivate" and not (self.es_de_claude(v) or (self.variation is not None and v == self.variation)):
            raise ErrorModificacion("sólo se desactivan variations de Claude (%s)" % v.GetFullName())
        activas = list(self.app.GetActiveNetworkVariations() or [])
        if (nombre == "Activate") == any(x == v for x in activas):
            return 0
        r = (fn or getattr(v, nombre))()
        caso = self.app.GetActiveStudyCase()
        ok = (nombre == "Activate") == any(x == v for x in (self.app.GetActiveNetworkVariations() or []))
        self._anotar(dict(tipo="variation_" + ("activada" if nombre == "Activate" else "desactivada"), obj=v.GetFullName(),
                          caso=caso.loc_name if caso else None, resultado=r, verificado=ok), None)
        if not ok:
            raise ErrorModificacion("%s() de %s no quedó aplicado (retornó %s)" % (nombre, v.loc_name, r))
        return r

    def renombrar_claude(self, actual, nuevo):
        """Renombra una variation de Claude de sesiones anteriores (sólo Claude_revisar_* o marcadas)."""
        scheme = self.app.GetProjectFolder("scheme")
        vs = [v for v in (scheme.GetContents("*.IntScheme", 1) or []) if v.loc_name == actual and self.es_de_claude(v)]
        if not vs:
            raise ErrorModificacion("no hay una variation de Claude llamada %r" % actual)
        return self._renombrar(vs[0], nuevo)

    def cerrar(self):
        """Al terminar: la variation de la sesión toma el nombre resumido (si se dio con nombrar)."""
        if getattr(self, "nombre_final", None) and self.variation is not None and self.variation.loc_name != self.nombre_final:
            return self._renombrar(self.variation, self.nombre_final)
        return None

    # ---------------------------------------------------------------- utilidades
    def _n_stage(self):
        try:
            return len(self.stage.GetContents("*", 1) or [])
        except Exception:
            return 0

    def _en_stage(self, obj, attr, valor):
        """True si el delta del objeto en el stage de Claude ya tiene el valor nuevo."""
        try:
            deltas = self.stage.GetContents("%s.%s" % (obj.loc_name, obj.GetClassName()), 1) or []
            # nombres repetidos en otras S/E (52JT1, T_12, "2(1)"...): PF guarda el delta con otro sufijo ("52JT1(1)", "2(2)").
            # Se busca por el nombre base y se identifica por root_id (10-10-2026).
            base = re.sub(r"\(\d+\)$", "", obj.loc_name)
            deltas = [d for d in deltas if _raiz(d) in (None, obj)] + [d for d in (self.stage.GetContents(
                "%s*.%s" % (base, obj.GetClassName()), 1) or []) if d.loc_name != obj.loc_name and _raiz(d) == obj]
        except Exception:
            return False
        for d in deltas:
            try:
                if _igual(d.GetAttribute(attr), valor):
                    return True
            except Exception:
                pass
        return False

    def _escenario(self):
        try:
            return self.app.GetActiveScenario()
        except Exception:
            return None

    def _escenario_nombre(self):
        e = self._escenario()
        return e.GetFullName() if e else None

    def es_propio(self, obj):
        return any(obj == p for p in self.propios)

    def _dentro_de_propio(self, obj):
        """True si obj cuelga (hasta 6 niveles) de un objeto creado o copiado por Claude en esta sesión, p. ej. un IntGrf
        dentro de la copia _CdN de un diagrama (09-10-2026: limpiar la copia sin tocar el diagrama del usuario)."""
        p = obj.GetParent()
        for _ in range(6):
            if p is None or _clase(p) in ("IntPrjfolder", "IntPrj", "IntUser"):
                return False
            if self.es_propio(p) or marcado(p):     # también copias de trabajo de sesiones anteriores ([CdN] o _CdN)
                return True
            p = p.GetParent()
        return False

    def _anotar(self, entrada, crudo):
        entrada = dict(entrada, n=len(self.diario) + 1, t=datetime.datetime.now().isoformat(timespec="seconds"))
        self.diario.append(entrada)
        self._crudos.append(crudo)
        # Una línea JSON por cambio (07-10-2026): reescribir el diario completo tras cada cambio costaba ~0,65 s por cambio
        # con 4 000 entradas y era el cuello de botella de los barridos.
        with open(self.ruta_diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False, default=a_json) + "\n")

    # ---------------------------------------------------------------- política de la vista
    def metodo(self, obj, nombre, fn):
        if nombre == "SetAttribute":
            return lambda attr, valor: self.escribir(obj, attr, valor)
        if nombre == "CreateObject":
            return lambda clase, *partes: envolver(self.crear(obj, clase, "".join(str(p) for p in partes)))
        if nombre == "AddCopy":
            return lambda origen, *partes: envolver(self.copiar(obj, desenvolver(origen), "".join(str(p) for p in partes)))
        if nombre == "Delete":
            return lambda: self.borrar(obj)
        if nombre == "Move":
            return lambda destino: self.mover(obj, desenvolver(destino))
        if nombre == "Execute":
            if _clase(obj) in CALCULO:
                return _envuelta(fn)
            raise ErrorModificacion("Execute() sólo para comandos de cálculo (%s), no %s" % (", ".join(sorted(CALCULO)), _clase(obj)))
        if nombre == "GetFromStudyCase":
            def obtener(clase):
                caso = self.app.GetActiveStudyCase()
                if not (caso.GetContents("*." + clase.split(".")[-1]) or []):
                    raise ErrorModificacion("GetFromStudyCase(%s) crearía el comando en el caso de estudio" % clase)
                return envolver(fn(clase))
            return obtener
        if nombre in ("AddRef", "RemoveRef", "Clear") and _clase(obj) == "SetSelect" and (self.es_propio(obj) or tiene_sufijo(obj.loc_name) or marcado(obj)):
            return _envuelta(fn)                    # armar sets propios (p. ej. barras para ComVstab), 07-10-2026
        if nombre in ("Activate", "Deactivate") and _clase(obj) in CONTEXTO_CLASES:
            return lambda: CONTEXTO.activar(obj, nombre, fn)
        if nombre == "ApplyChanges" and _clase(obj) == "IntSstage" and self.es_de_claude(obj.GetParent()):
            def aplicar():                      # consolidar stages temporales (Trabajo_/Claude) en el stage que graba, 08-10-2026
                r = fn()
                self._anotar(dict(tipo="apply_stage", obj=obj.GetFullName(), ret=r, destino="variation"), obj)
                return r
            return aplicar
        if nombre == "SetStudyTime" and _clase(obj) == "IntCase" and self.stage is not None:
            def adelantar(T2):                  # 09-10-2026: llevar otro caso a la hora del stage de la sesión (misma regla que abrir())
                T = obj.GetAttribute("iStudyTime"); ts = get_attr(self.stage, "tAcTime", 0) or 0
                if not (T < T2 <= ts):
                    raise ErrorModificacion("SetStudyTime sólo adelanta la hora hasta el stage de la sesión (%s < t <= %s)" % (T, ts))
                ajenas = [(v.loc_name, s.loc_name) for v in (self.app.GetActiveNetworkVariations() or []) if not self.es_de_claude(v)
                          for s in (v.GetContents("*.IntSstage", 1) or []) if T < (get_attr(s, "tAcTime", 0) or 0) <= T2]
                if ajenas:
                    raise ErrorModificacion("adelantar la hora de estudio activaría stages ajenas: %s" % ajenas)
                r = fn(T2)
                self._anotar(dict(tipo="study_time", obj=obj.GetFullName(), antes=T, despues=T2), obj)
                return r
            return adelantar
        if nombre == "Rebuild":
            return _envuelta(fn)                    # redibujar el gráfico visible; no cambia datos (09-10-2026)
        if nombre in ("Show", "Close", "Freeze", "Unfreeze") and _clase(obj) in ("IntGrfnet", "SetDesktop", "SetDeskpage"):
            return _envuelta(fn)                    # abrir un diagrama no cambia datos (09-10-2026, diagrama _CdN)
        if nombre in ("Activate", "Deactivate") and _clase(obj) == "IntScheme":
            return lambda: self.activar_variation(obj, nombre, fn)     # 07-10-2026, a pedido del usuario
        if nombre == "Save" and _clase(obj) == "IntScenario":
            return lambda: self.guardar_escenario(obj, fn)
        if nombre in ("Save", "SaveAs", "Activate", "Deactivate", "SetStudyTime") or not nombre.startswith(PREFIJOS_LECTURA):
            raise ErrorModificacion("%s() no está permitido en modo modificación" % nombre)
        return _envuelta(fn)

    # ---------------------------------------------------------------- escenarios (copias _revisar)
    # ---------------------------------------------------------------- convención _secure (07-10-2026)
    # Pedido del usuario: en vez de marcar con _revisar lo que Claude puede tocar, se marca con _secure lo intocable
    # (escenario o cualquier carpeta que lo contenga). Salvaguarda: mientras el proyecto no tenga ningún _secure en
    # Operation Scenarios, rige la regla anterior (_revisar), para no dejar desprotegidos los originales.
    def _carpeta_esc(self):
        return self.app.GetProjectFolder("scen")

    def convencion_secure(self):
        raiz = self._carpeta_esc()
        objs = list(raiz.GetContents("*.IntScenario", 1) or []) + list(raiz.GetContents("*.IntFolder", 1) or [])
        return any((o.loc_name or "").lower().endswith(PROTEGIDO) for o in objs)

    def protegido(self, obj):
        """True si el escenario/carpeta o alguna carpeta que lo contiene termina en _secure."""
        raiz, o = self._carpeta_esc(), obj
        while o is not None and not (o == raiz):
            if (o.loc_name or "").lower().endswith(PROTEGIDO):
                return True
            o = o.GetParent()
        return False

    def _en_escenarios(self, o):
        raiz = self._carpeta_esc()
        while o is not None:
            if o == raiz:
                return True
            o = o.GetParent()
        return False

    def _libre(self, padre, base, clase):
        existentes = {x.loc_name for x in (padre.GetContents("*." + clase) or [])}
        cand, n = base[:40], 1
        while cand in existentes:
            n += 1
            suf = " (%d)" % n
            cand = base[:40 - len(suf)] + suf
        return cand

    def copiar_escenario(self, nombre, nuevo=None, carpeta=None):
        """Copia un escenario (nombre o ruta final). Con la convención _secure: nombre = `nuevo` o el original sin
        '_secure', en `carpeta` (nombre/ruta de una carpeta de Operation Scenarios no protegida) o junto al original
        (si éste está protegido, hay que dar `carpeta`). Sin la convención: copia '<escenario>_revisar' junto al original."""
        e = CONTEXTO._buscar("scen", "IntScenario", nombre)
        if not self.convencion_secure():
            return envolver(self.copiar(e.GetParent(), e))
        padre = CONTEXTO._buscar("scen", "IntFolder", carpeta) if carpeta else e.GetParent()
        if self.protegido(padre):
            raise ErrorModificacion("la carpeta destino '%s' está protegida (_secure)" % padre.loc_name)
        base = nuevo or re.sub(PROTEGIDO + "$", "", e.loc_name, flags=re.I)
        if base.lower().endswith(PROTEGIDO):
            raise ErrorModificacion("la copia no puede llamarse *_secure")
        copia = padre.AddCopy(e, self._libre(padre, base, "IntScenario"))
        if copia is None:
            raise ErrorModificacion("AddCopy de %s devolvió None" % e.GetFullName())
        self.propios.append(copia)
        self._anotar(dict(tipo="copia", obj=copia.GetFullName(), original=e.GetFullName(), destino="proyecto"), copia)
        return envolver(copia)

    def carpeta_escenarios(self, nombre, padre=None):
        """Crea una carpeta en Operation Scenarios (o dentro de `padre`, no protegida). Sólo con la convención _secure."""
        if not self.convencion_secure():
            raise ErrorModificacion("carpeta_escenarios requiere la convención _secure (ningún _secure en el proyecto)")
        p = CONTEXTO._buscar("scen", "IntFolder", padre) if padre else self._carpeta_esc()
        if self.protegido(p):
            raise ErrorModificacion("la carpeta '%s' está protegida (_secure)" % p.loc_name)
        ex = p.GetContents("%s.IntFolder" % nombre) or []
        if ex:
            return envolver(ex[0])
        c = p.CreateObject("IntFolder", nombre)
        self.propios.append(c)
        self._anotar(dict(tipo="creado", obj=c.GetFullName(), destino="proyecto"), c)
        return envolver(c)

    def renombrar_escenario(self, obj, nuevo):
        """Renombra un escenario o carpeta de Operation Scenarios no protegido (sólo con la convención _secure).
        Agregar '_secure' (proteger) se permite; quitarlo, no (lo protegido no se toca)."""
        if isinstance(obj, str):
            try:
                obj = CONTEXTO._buscar("scen", "IntScenario", obj)
            except ErrorModificacion:
                obj = CONTEXTO._buscar("scen", "IntFolder", obj)
        obj = desenvolver(obj)
        if not self.convencion_secure():
            raise ErrorModificacion("renombrar_escenario requiere la convención _secure")
        if _clase(obj) not in ("IntScenario", "IntFolder") or not self._en_escenarios(obj):
            raise ErrorModificacion("sólo escenarios/carpetas de Operation Scenarios")
        if self.protegido(obj):
            raise ErrorModificacion("'%s' está protegido (_secure)" % obj.loc_name)
        antes = obj.loc_name
        obj.loc_name = nuevo
        self._anotar(dict(tipo="renombre", obj=obj.GetFullName(), antes=antes, despues=nuevo), None)
        return obj.loc_name

    def guardar_escenario(self, esc, fn):
        """Con la convención _secure: guarda cualquier escenario no protegido. Sin ella: sólo copias _revisar.
        Guardar sólo escenarios de trabajo verificados (regla acordada con el usuario)."""
        if self.convencion_secure():
            if self.protegido(esc):
                raise ErrorModificacion("'%s' está protegido (_secure): no se guarda" % esc.loc_name)
        elif not (self.es_propio(esc) or termina_sufijo(esc.loc_name) or any(re.search(x + r"\d*$", esc.loc_name) for x in SUFIJOS)):
            raise ErrorModificacion("sólo se guardan copias %s de escenarios (no '%s')" % (SUFIJO, esc.loc_name))
        r = fn()
        self._anotar(dict(tipo="escenario_guardado", obj=esc.GetFullName()), None)
        return r

    def asignar(self, obj, nombre, valor):
        self.escribir(obj, nombre, valor)

    # ---------------------------------------------------------------- operaciones
    def escribir(self, obj, attr, valor):
        valor = desenvolver(valor)
        fn = obj.GetFullName()
        propio, red = self.es_propio(obj), es_red(obj)
        if not propio and not red and marcado(obj):
            propio = True                       # copia de trabajo de una sesión anterior ([CdN] o _CdN/_revisar): se puede escribir
        if not propio and not red and _clase(obj) == "ComDiff" and attr in ("iopt_mode", "imode", "ibase", "icomp"):
            propio = True                       # encender/apagar la comparación de resultados (flujo diferencial), 08-10-2026
        if not propio and not red and _clase(obj) == "IntSstage" and attr in ("tAcTime", "loc_name") and self.es_de_claude(obj.GetParent()):
            propio = True                       # hora de activación de stages de variations de Claude (07-10-2026)
        if not propio and not red:
            p = obj.GetParent()                 # hijo de una copia propia (p. ej. sline.ChaRef dentro de un TypLne _revisar)
            for _ in range(4):
                if p is None or _clase(p) in ("IntPrjfolder", "IntPrj", "IntUser"):
                    break
                if self.es_propio(p) or marcado(p):
                    propio = True
                    break
                p = p.GetParent()
        if not propio and not red:
            raise ErrorModificacion("%s no es de la red: sus cambios no quedan en la variation. Usa c = revisar(obj), "
                                    "modifica la copia y repunta desde la red." % fn)
        antes = obj.GetAttribute(attr)
        obj.SetAttribute(attr, valor)
        destino = "propio"
        if red and not propio:
            # Dónde quedó: se lee el delta del objeto en el stage de Claude. Con un escenario activo, los datos
            # operativos (outserv, consignas, taps...) van al escenario aunque el objeto ya tenga delta en el stage
            # (verificado en PF 2025: outserv quedó en el escenario, el delta del stage conservó el valor anterior).
            # Sólo se acepta "escenario" para datos operativos conocidos: PF NO registra en variations ni escenarios
            # cosas como loc_name (verificado: el renombre se aplicó directo al objeto base).
            if self._en_stage(obj, attr, valor):
                destino = "variation"
            elif self._escenario() is not None and attr in OPERATIVOS:
                destino = "escenario"
            else:
                obj.SetAttribute(attr, antes)
                raise ErrorModificacion("el cambio de %s.%s no quedó en la variation%s: revertido" % (
                    fn, attr, "" if self._escenario() is None else " y no es un dato operativo conocido (OPERATIVOS)"))
        self._anotar(dict(tipo="set", obj=fn, attr=attr, antes=antes, despues=valor, destino=destino), obj)
        return 0

    def crear(self, padre, clase, nombre):
        # ChaRef: PF identifica el parámetro por el nombre ("sline"); con sufijo no enlaza y renombrar después tampoco
        # (09-10-2026: "Error in load flow data"). Se crea con el nombre exacto; queda dentro de un objeto propio.
        exacto = clase == "ChaRef" and (self.es_propio(padre) or marcado(padre))
        if not tiene_sufijo(nombre) and not exacto:
            nombre = nombre_libre(padre, nombre or clase, clase)
        red = es_red(padre)
        n0 = self._n_stage()
        nuevo = padre.CreateObject(clase, nombre)
        if nuevo is None:
            raise ErrorModificacion("CreateObject(%s, %s) devolvió None" % (clase, nombre))
        if red and self._n_stage() <= n0:
            nuevo.Delete()
            raise ErrorModificacion("el objeto nuevo no quedó registrado en la variation: borrado")
        if not exacto and not marcar(nuevo) and not tiene_sufijo(nuevo.loc_name):
            nuevo.loc_name = nombre_libre(padre, nombre, clase, SUFIJO)    # clase sin descripción: sufijo en el nombre
        self.propios.append(nuevo)
        self._anotar(dict(tipo="creado", obj=nuevo.GetFullName(), clase=clase, destino="variation" if red else "proyecto"), nuevo)
        return nuevo

    def copiar(self, padre, origen, nombre=""):
        nombre = nombre_libre(padre, nombre or origen.loc_name, _clase(origen))
        red = es_red(padre)
        n0 = self._n_stage()
        copia = padre.AddCopy(origen, nombre)
        if copia is None:
            raise ErrorModificacion("AddCopy de %s devolvió None" % origen.GetFullName())
        if red and self._n_stage() <= n0:
            copia.Delete()
            raise ErrorModificacion("la copia en la red no quedó registrada en la variation: borrada")
        if not marcar(copia) and not tiene_sufijo(copia.loc_name):
            copia.loc_name = nombre_libre(padre, nombre, _clase(origen), SUFIJO)   # clase sin descripción: sufijo en el nombre
        self.propios.append(copia)
        self._anotar(dict(tipo="copia", obj=copia.GetFullName(), original=origen.GetFullName(),
                          destino="variation" if red else "proyecto"), copia)
        return copia

    def revisar(self, obj):
        """Copia junto al original (para objetos fuera de la red), con nombre limpio libre («<nombre> (2)» si choca) y la
        marca [CdN] en la descripción. Devuelve la copia (modificable)."""
        obj = desenvolver(obj)
        return envolver(self.copiar(obj.GetParent(), obj))

    def mover(self, obj, destino):
        """Ordena copias de trabajo: mueve escenarios o carpetas '_revisar' (o creados en la sesión) entre carpetas de
        Operation Scenarios. No mueve el escenario activo ni objetos fuera de Operation Scenarios.
        También mueve variations de Claude (Claude_revisar_* o marcadas [claude-puente]) entre carpetas de Network
        Variations (07-10-2026, a pedido del usuario: ordenarlas en ZDI)."""
        if _clase(obj) == "IntSstage":
            # Stage de una variation de Claude hacia otra variation (p. ej. ZDI), con ambas inactivas en el caso actual
            # (caso "Base SEN"): así el usuario consolida los cambios de Claude en sus variations (08-10-2026).
            origen = obj.GetParent()
            activas = list(self.app.GetActiveNetworkVariations() or [])
            de_vuelta = (obj.loc_name or "").startswith("Revision_parametros_") and self.es_de_claude(destino)   # consolidación (usuario, 08-10-2026)
            if (not self.es_de_claude(origen) and not de_vuelta) or (self.variation is not None and origen == self.variation):
                raise ErrorModificacion("sólo se mueven stages de variations de Claude de sesiones anteriores (%s)" % obj.GetFullName())
            if _clase(destino) != "IntScheme":
                raise ErrorModificacion("el stage se mueve a otra variation (IntScheme), no a %s" % _clase(destino))
            if any(origen == v for v in activas) or any(destino == v for v in activas):
                raise ErrorModificacion("origen o destino activos en este caso: activar primero un caso sin variations (Base SEN)")
            antes = obj.GetFullName()
            r = destino.Move(obj)
            self._anotar(dict(tipo="movido", obj=antes, destino=destino.GetFullName(), resultado=r), None)
            return r
        if _clase(obj) == "IntScheme":
            scheme = self.app.GetProjectFolder("scheme")
            def en_variations(o):
                while o is not None:
                    if o == scheme:
                        return True
                    o = o.GetParent()
                return False
            if _clase(destino) not in ("IntFolder", "IntPrjfolder") or not en_variations(destino):
                raise ErrorModificacion("las variations sólo se mueven a carpetas dentro de Network Variations")
            if not (self.es_de_claude(obj) or (self.variation is not None and obj == self.variation)):
                raise ErrorModificacion("sólo se mueven variations de Claude (%s)" % obj.GetFullName())
            antes = obj.GetFullName()
            r = destino.Move(obj)   # en PF el método se llama sobre la carpeta destino (08-10-2026: al revés devolvía 1)
            if self.variation is not None and obj == self.variation:
                self.var_fn, self.stage_fn = obj.GetFullName(), self.stage.GetFullName()
            self._anotar(dict(tipo="movido", obj=antes, destino=destino.GetFullName(), resultado=r), None)
            return r

        def en_escenarios(o):
            while o is not None:
                if o.GetClassName() == "IntPrjfolder" and o.loc_name == "Operation Scenarios":
                    return True
                o = o.GetParent()
            return False
        if _clase(obj) not in ("IntScenario", "IntFolder") or _clase(destino) not in ("IntFolder", "IntPrjfolder"):
            raise ErrorModificacion("Move sólo para escenarios/carpetas hacia una carpeta (%s → %s)" % (_clase(obj), _clase(destino)))
        if not (en_escenarios(obj) and en_escenarios(destino)):
            raise ErrorModificacion("Move sólo dentro de Operation Scenarios")
        if self.convencion_secure():
            if self.protegido(obj) or self.protegido(destino):
                raise ErrorModificacion("origen o destino protegido (_secure): %s -> %s" % (obj.GetFullName(), destino.GetFullName()))
        elif not (self.es_propio(obj) or tiene_sufijo(obj.loc_name) or marcado(obj)):
            raise ErrorModificacion("sólo se mueven copias de trabajo ('%s' o %s) o creadas en la sesión (%s)" % (SUFIJO, MARCA_OBJ, obj.GetFullName()))
        act = self._escenario()
        if act is not None and (act == obj or (_clase(obj) == "IntFolder" and act.GetFullName().startswith(obj.GetFullName() + "\\"))):
            raise ErrorModificacion("no se mueve el escenario activo (ni la carpeta que lo contiene)")
        antes = obj.GetFullName()
        r = destino.Move(obj)   # en PF el método se llama sobre la carpeta destino
        self._anotar(dict(tipo="movido", obj=antes, destino=destino.GetFullName(), resultado=r), None)
        return r

    def borrar(self, obj):
        # Variations de Claude (de sesiones anteriores, sin ser la de esta sesión) se pueden borrar si no están activas en el
        # caso actual, p. ej. con el caso "Base SEN", que tiene todas las variations desactivadas (usuario, 08-10-2026).
        if (_clase(obj) == "IntScheme" and self.es_de_claude(obj) and not (self.variation is not None and obj == self.variation)
                and not any(obj == v for v in (self.app.GetActiveNetworkVariations() or []))):
            fn = obj.GetFullName()
            n = len(obj.GetContents("*", 1) or [])
            obj.Delete()
            self._anotar(dict(tipo="borrado", obj=fn, objetos_dentro=n), None)
            return 0
        # Limpieza de escenarios (usuario, 08-10-2026): con la convención _secure se borran escenarios/carpetas de Operation
        # Scenarios no protegidos, que no sean ni contengan el escenario activo ni algo protegido. PF los manda a su papelera.
        if _clase(obj) in ("IntScenario", "IntFolder") and self.convencion_secure() and self._en_escenarios(obj):
            if self.protegido(obj):
                raise ErrorModificacion("'%s' está protegido (_secure)" % obj.loc_name)
            act = self._escenario()
            hijos = list(obj.GetContents("*.IntScenario", 1) or []) + list(obj.GetContents("*.IntFolder", 1) or []) if _clase(obj) == "IntFolder" else []
            if act is not None and (act == obj or any(act == h for h in hijos)):
                raise ErrorModificacion("no se borra el escenario activo (ni la carpeta que lo contiene)")
            if any((h.loc_name or "").lower().endswith(PROTEGIDO) for h in hijos):
                raise ErrorModificacion("la carpeta '%s' contiene algo protegido (_secure)" % obj.loc_name)
            fn = obj.GetFullName()
            r = obj.Delete()
            self._anotar(dict(tipo="borrado", obj=fn, escenarios_dentro=len([h for h in hijos if _clase(h) == "IntScenario"])), None)
            return r
        # Objetos gráficos _CdN dentro de diagramas _CdN, aunque vengan de una sesión anterior (autorizado 10-10-2026).
        if _clase(obj) == "IntGrf" and marcado(obj):
            d = obj.GetParent()
            while d is not None and _clase(d) != "IntGrfnet":
                d = d.GetParent()
            if d is not None and marcado(d):
                fn = obj.GetFullName()
                obj.Delete()
                self._anotar(dict(tipo="borrado", obj=fn, regla="grafico_CdN"), None)
                return 0
        # Copias de trabajo de biblioteca marcadas ([CdN] o _CdN) de sesiones anteriores (usuario, 15-10-2026). Nunca la red,
        # escenarios ni variations (tienen sus reglas arriba). Una carpeta sólo si todo lo que tiene directamente está marcado.
        if (not self.es_propio(obj) and marcado(obj) and not es_red(obj)
                and _clase(obj) not in ("IntScenario", "IntScheme", "IntSstage", "IntCase", "IntPrjfolder")):
            if _clase(obj) == "IntFolder":
                ajenos = [h.loc_name for h in (obj.GetContents("*", 0) or []) if not marcado(h)]
                if ajenos:
                    raise ErrorModificacion("la carpeta '%s' tiene objetos sin marca %s: %s" % (obj.loc_name, MARCA_OBJ, ", ".join(ajenos[:5])))
            fn = obj.GetFullName()
            obj.Delete()
            self._anotar(dict(tipo="borrado", obj=fn, regla="marca_CdN"), None)
            return 0
        if not self.es_propio(obj) and not self._dentro_de_propio(obj):
            raise ErrorModificacion("sólo se pueden borrar objetos creados por Claude o marcados %s (%s)" % (MARCA_OBJ, obj.GetFullName()))
        fn = obj.GetFullName()
        obj.Delete()
        self.propios = [p for p in self.propios if not (p == obj)]
        self._anotar(dict(tipo="borrado", obj=fn), None)
        return 0

    def deshacer(self, n=None):
        """Revierte las últimas n operaciones (todas si n es None). Devuelve la lista de lo revertido."""
        hechos = []
        indices = [i for i, e in enumerate(self.diario) if e["tipo"] in ("set", "creado", "copia") and not e.get("deshecho")]
        for i in reversed(indices[-n:] if n else indices):
            e, crudo = self.diario[i], self._crudos[i]
            try:
                crudo.GetFullName()
            except Exception:                       # referencia invalidada por una reconexión: buscar por ruta
                crudo = _resolver(self.app, e["obj"])
            try:
                if e["tipo"] == "set":
                    crudo.SetAttribute(e["attr"], e["antes"])
                else:
                    crudo.Delete()
                    self.propios = [p for p in self.propios if not (p == crudo)]
                e["deshecho"] = True
                hechos.append("%s %s%s" % (e["tipo"], e["obj"], "." + e["attr"] if e["tipo"] == "set" else ""))
            except Exception as ex:
                hechos.append("NO se pudo deshacer %d (%s): %s" % (e["n"], e["obj"], ex))
        self._anotar(dict(tipo="deshacer", revertidos=hechos), None)
        return hechos

    def resumen(self):
        return [e for e in self.diario if e["tipo"] != "inicio"]

    def reconectar(self, app):
        """Tras una reconexión: volver a ubicar variation, stage y objetos propios por su ruta."""
        self.app = app
        if getattr(self, "var_fn", None):
            self.variation = _resolver(app, self.var_fn)
            self.stage = _resolver(app, self.stage_fn)
        vigentes = [e["obj"] for e in self.diario if e["tipo"] in ("creado", "copia") and not e.get("deshecho")]
        self.propios = [o for o in (_resolver(app, fn) for fn in vigentes) if o is not None]


class PoliticaLimpieza(object):
    """Modo «limpieza» (06-11-2026, pedido explícito del usuario para ordenar la BD): escritura libre sobre el proyecto,
    sin variation de sesión, con diario de cada llamada que modifica. Puede lanzarlo el agente con autorización del usuario
    para ese modo y alcance (pf_bridge_limpieza.py).
    Guardas que se conservan: nada con «_secure» en la ruta se escribe, mueve ni borra; nunca se guarda un IntScenario.
    `Move` NO se traduce: usar la forma real de la API, `destino.Move(obj)`."""
    nombre = "limpieza"
    ESCRIBEN_ATRIB = ("SetAttribute",)

    def __init__(self, bridge_dir):
        self.ruta_diario = os.path.join(bridge_dir, "diario_limpieza_%s.jsonl" % datetime.datetime.now().strftime("%Y%m%d_%H%M"))
        self.n = 0

    def _anotar(self, **d):
        self.n += 1
        d.update(n=self.n, t=ahora())
        with open(self.ruta_diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, default=a_json) + "\n")

    @staticmethod
    def _ruta(o):
        try:
            return o.GetFullName()
        except Exception:
            return str(o)

    def _proteger(self, *objs):
        for o in objs:
            if _es_objeto_pf(o) and PROTEGIDO in self._ruta(o):
                raise ErrorModificacion("objeto protegido (%s): %s" % (PROTEGIDO, self._ruta(o)))

    def metodo(self, obj, nombre, fn):
        if nombre in ("Activate", "Deactivate") and _clase(obj) in CONTEXTO_CLASES:
            return lambda: CONTEXTO.activar(obj, nombre, fn)
        if nombre.startswith(PREFIJOS_LECTURA) and nombre not in BLOQUEADOS_RO:
            return _envuelta(fn)
        if nombre == "Save" and _clase(obj) == "IntScenario":
            raise ErrorModificacion("Save() de escenarios no está permitido en modo limpieza")

        def llamada(*a, **kw):
            a2 = [desenvolver(x) for x in a]
            kw2 = {k: desenvolver(x) for k, x in kw.items()}
            self._proteger(obj, *a2)
            previo = None
            if nombre in self.ESCRIBEN_ATRIB and a2:
                previo = get_attr(obj, a2[0])
            ruta_obj = self._ruta(obj)
            r = fn(*a2, **kw2)
            self._anotar(tipo="llamada", obj=ruta_obj, clase=_clase(obj), metodo=nombre,
                         args=[self._ruta(x) if _es_objeto_pf(x) else x for x in a2], antes=previo, retorno=r)
            return envolver(r)
        return llamada

    def asignar(self, obj, nombre, valor):
        valor = desenvolver(valor)
        self._proteger(obj)
        previo = get_attr(obj, nombre)
        setattr(obj, nombre, valor)
        self._anotar(tipo="asignar", obj=self._ruta(obj), clase=_clase(obj), atributo=nombre, antes=previo,
                     despues=get_attr(obj, nombre))

    def reconectar(self, app):
        pass


POLITICA = PoliticaLectura()


class Vista(object):
    """Envuelve un objeto de PF (o el app) y aplica la política del modo."""
    __slots__ = ("_crudo_",)

    def __init__(self, obj):
        object.__setattr__(self, "_crudo_", obj)

    def __getattr__(self, nombre):
        obj = object.__getattribute__(self, "_crudo_")
        v = getattr(obj, nombre)
        if callable(v):
            return POLITICA.metodo(obj, nombre, v)
        return envolver(v)

    def __setattr__(self, nombre, valor):
        POLITICA.asignar(object.__getattribute__(self, "_crudo_"), nombre, valor)

    def __repr__(self):
        o = object.__getattribute__(self, "_crudo_")
        return "<%s>" % (o.GetFullName() if hasattr(o, "GetFullName") else type(o).__name__)

    def __eq__(self, otro):
        return desenvolver(self) == desenvolver(otro)

    def __hash__(self):
        return hash(object.__getattribute__(self, "_crudo_"))


# ------------------------------------------------------------------------------------------------ utilidades
def a_json(v):
    v = desenvolver(v)
    if _es_objeto_pf(v):
        return v.GetFullName()
    return str(v)


def as_list(v):
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else [v]


def get_attr(obj, nombre, defecto=None):
    try:
        return obj.GetAttribute(nombre)
    except Exception:
        return defecto


def escribir_json(ruta, datos):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=a_json)
    os.replace(tmp, ruta)


def ahora():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------------------------------------ puente
MAX_MUERTOS = 5             # tras estos fallos seguidos por app invalidado, el puente se detiene (hay que reiniciarlo)
MAX_OW = 400                # líneas de la Output Window que se devuelven por comando
TIPOS_OW = {"error": ("Error",), "warn": ("Warn", "Warning"), "info": ("Info",), "plain": ("Plain",), "event": ("Event",)}


class SalidaPF:
    """Lectura (nunca Clear) de la Output Window de PF. Si la API no trae filtros por tipo, devuelve todo sin clasificar."""

    def __init__(self, app):
        self.reconectar(app)

    def reconectar(self, app):
        self.app, self.error = app, None
        try:
            self.ow = app.GetOutputWindow()
            mt = getattr(self.ow, "MessageType", None) or getattr(type(self.ow), "MessageType", None) \
                or getattr(powerfactory, "MessageType", None)
            self.mt = {k: next((getattr(mt, n) for n in ns if mt is not None and hasattr(mt, n)), None) for k, ns in TIPOS_OW.items()}
        except Exception as e:
            self.ow, self.mt, self.error = None, {}, "Output Window no disponible: %s" % e

    def _contenido(self, tipo=None):
        if self.ow is None:
            return []
        if tipo is None:
            return list(self.ow.GetContent())
        f = self.mt.get(tipo)
        return list(self.ow.GetContent(f)) if f is not None else []

    def marca(self):
        """Largo actual de cada vista (todo y por tipo) para luego extraer sólo lo nuevo."""
        if self.ow is None:
            return None
        try:
            return {k: len(self._contenido(k)) for k in [None] + [t for t in ("error", "warn") if self.mt.get(t) is not None]}
        except Exception as e:
            self.error = "GetContent falló: %s" % e
            return None

    def desde(self, m):
        """Lo escrito en la Output Window desde la marca m (si PF limpió la ventana, todo lo que hay)."""
        if m is None:
            return dict(disponible=False, nota=self.error)
        out = dict(disponible=True, filtros=sorted(k for k, v in self.mt.items() if v is not None))
        try:
            for k, n0 in m.items():
                c = self._contenido(k)
                nuevo = c[n0:] if len(c) >= n0 else c
                clave = "lineas" if k is None else ("errores" if k == "error" else "avisos")
                out["n_" + clave] = len(nuevo)
                out[clave] = nuevo[:MAX_OW]
        except Exception as e:
            out.update(disponible=False, nota="GetContent falló tras el comando: %s" % e)
        return out

    def leer(self, tipo=None, n=50, buscar=None):
        """Últimas n líneas de la Output Window (tipo: None/'error'/'warn'/'info'/'plain'/'event'; buscar: regex)."""
        if tipo is not None and tipo not in TIPOS_OW:
            raise ValueError("tipo debe ser uno de %s" % sorted(TIPOS_OW))
        if tipo is not None and self.mt.get(tipo) is None:
            raise RuntimeError("esta versión de PF no expone el filtro %r; filtros disponibles: %s" % (
                tipo, sorted(k for k, v in self.mt.items() if v is not None)))
        c = self._contenido(tipo)
        if buscar:
            r = re.compile(buscar, re.I)
            c = [l for l in c if r.search(l)]
        return c[-n:] if n else c


class PoliticaDiagnosticoRef(object):
    """Modo diagnóstico acotado: NO ejecuta PoliticaModificacion.abrir(); por tanto no crea variation/stage ni
    llama SetStudyTime (cero retiming al arrancar). Permisos, todos por ruta exacta y registrados en diario:
      - IntPrj.Activate solo para PRJ_REF. Activar el laboratorio queda en el bootstrap (no se expone aquí).
      - AddCopy solo de CASO_REF a CASO_SONDA en REF_CASOS, con Ref/Base SEN/Domingo Madrugada activos.
      - Execute solo de comandos de cálculo que cuelguen de CASO_SONDA, con Ref/CASO_SONDA/ESC_REF ACTIVOS.
      - SetAttribute solo dentro de CASO_SONDA, con el mismo contexto activo y atributos de simulación.
      - cambiar_caso solo reafirma CASO_SONDA/ESC_REF exactos (misma guarda de activación).
    Todo lo demás se rechaza. CreateVersion no se expone: el respaldo es un paso manual del bootstrap.
    No hay Save/SaveAs/SetStudyTime/Deactivate ni activación del laboratorio desde el puente.
    """
    nombre = "diagnóstico Ref (sin retiming)"
    ATRIBUTOS_SONDA = {"tstop", "iopt_show", "dtout", "dtgrd", "dtgrd_max", "tstart"}

    def __init__(self, app, bridge_dir):
        self.app, self.dir = app, bridge_dir
        self.diario = []
        self.ruta_diario = os.path.join(
            bridge_dir, "diario_diagnostico_ref_%s.jsonl" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.proyecto_inicial = app.GetActiveProject().GetFullName() if app.GetActiveProject() else None

    def _anotar(self, entrada, crudo=None):
        entrada = dict(entrada, n=len(self.diario) + 1, t=ahora())
        self.diario.append(entrada)
        with open(self.ruta_diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False, default=a_json) + "\n")

    def abrir(self):
        """Guardia de arranque: solo registra. No crea stages, no adelanta la hora, no escribe atributos PF."""
        self._anotar(dict(tipo="inicio_diagnostico", proyecto=self.proyecto_inicial, retiming=False,
                          nota="sin abrir()/sin SetStudyTime/sin CreateObject(IntScheme|IntSstage)"))
        return None

    def _escenario(self):
        try:
            return self.app.GetActiveScenario()
        except Exception:
            return None

    def _escenario_nombre(self):
        e = self._escenario()
        return e.GetFullName() if e else None

    def _sin_cambios(self):
        e = self._escenario()
        if e is not None and get_attr(e, "iModified", 0):
            raise ErrorModificacion("el escenario activo '%s' tiene cambios sin guardar" % e.loc_name)

    def _en_caso_sonda(self, obj):
        p = obj
        for _ in range(12):
            if p is None:
                return False
            if _clase(p) == "IntCase":
                return p.GetFullName() == CASO_SONDA
            p = p.GetParent()
        return False

    def _proyecto(self):
        try:
            return self.app.GetActiveProject()
        except Exception:
            return None

    def _exigir_ref(self, operacion):
        """Guarda de contexto: toda operación sensible exige el Ref exacto activo."""
        prj = self._proyecto()
        if prj is None or prj.GetFullName() != PRJ_REF:
            raise ErrorModificacion("%s requiere el Ref exacto activo (activo: %s)" % (
                operacion, prj.GetFullName() if prj is not None else None))
        return prj

    def _contexto_sonda(self, operacion="Execute"):
        """Execute/SetAttribute solo con Ref, Base SEN_SONDA_20261109 y Domingo Madrugada ACTIVOS.
        El padre del comando no basta: PF calcula sobre el contexto activo (User Manual, caso activo único)."""
        self._exigir_ref(operacion)
        caso = self.app.GetActiveStudyCase()
        if caso is None or caso.GetFullName() != CASO_SONDA:
            raise ErrorModificacion("%s requiere Base SEN_SONDA_20261109 activo (activo: %s)" % (
                operacion, caso.GetFullName() if caso is not None else None))
        esc = self._escenario()
        if esc is None or esc.GetFullName() != ESC_REF:
            raise ErrorModificacion("%s requiere el escenario Domingo Madrugada activo (activo: %s)" % (
                operacion, esc.GetFullName() if esc is not None else None))

    def _contexto_copia(self):
        """AddCopy solo con el Ref, Base SEN y Domingo Madrugada activos (contexto de origen verificado)."""
        self._exigir_ref("AddCopy")
        caso = self.app.GetActiveStudyCase()
        if caso is None or caso.GetFullName() != CASO_REF:
            raise ErrorModificacion("AddCopy requiere Base SEN activo (activo: %s)" % (
                caso.GetFullName() if caso is not None else None))
        esc = self._escenario()
        if esc is None or esc.GetFullName() != ESC_REF:
            raise ErrorModificacion("AddCopy requiere el escenario Domingo Madrugada activo (activo: %s)" % (
                esc.GetFullName() if esc is not None else None))

    def activar_proyecto(self, obj, nombre, fn):
        destino = obj.GetFullName()
        if nombre != "Activate":
            raise ErrorModificacion("solo IntPrj.Activate está permitido (no %s)" % nombre)
        # El puente solo puede volver al Ref; activar/desactivar el laboratorio queda en el bootstrap.
        if destino != PRJ_REF:
            raise ErrorModificacion("activación de proyecto no permitida desde el puente: %s" % destino)
        actual = self._proyecto()
        if actual is None or actual.GetFullName() not in (PRJ_LAB, PRJ_REF):
            raise ErrorModificacion("proyecto activo no autorizado para activar el Ref: %s" % (
                actual.GetFullName() if actual is not None else None))
        self._sin_cambios()
        antes = self.app.GetActiveProject().GetFullName() if self.app.GetActiveProject() else None
        r = fn()
        despues = self.app.GetActiveProject().GetFullName() if self.app.GetActiveProject() else None
        self._anotar(dict(tipo="activar_proyecto", antes=antes, destino=destino, ret=r, activo=despues))
        if despues != destino:
            raise ErrorModificacion("Activate() no dejó activo %s (activo: %s)" % (destino, despues))
        return r

    def crear_version(self, obj, fn, *a, **k):
        # El respaldo es un paso manual del bootstrap, nunca una capacidad por comando del puente.
        raise ErrorModificacion("CreateVersion no está expuesto al puente; el respaldo es un paso manual del bootstrap")

    def copiar(self, padre, origen, nombre):
        self._contexto_copia()
        if not (padre.GetFullName() == REF_CASOS and origen.GetFullName() == CASO_REF
                and nombre == "Base SEN_SONDA_20261109"):
            raise ErrorModificacion("AddCopy solo de Base SEN a Base SEN_SONDA_20261109 en %s" % REF_CASOS)
        if [o for o in (padre.GetContents("*", 0) or []) if o.loc_name == nombre]:
            raise ErrorModificacion("la copia %s ya existe" % nombre)
        copia = padre.AddCopy(origen, nombre)
        self._anotar(dict(tipo="copia_sonda", original=origen.GetFullName(),
                          copia=copia.GetFullName() if copia is not None else None))
        if copia is None:
            raise ErrorModificacion("AddCopy de Base SEN devolvió None")
        return copia

    def escribir(self, obj, attr, valor):
        if not self._en_caso_sonda(obj):
            raise ErrorModificacion("SetAttribute solo dentro de la copia SONDA: %s" % obj.GetFullName())
        self._contexto_sonda("SetAttribute")
        if attr not in self.ATRIBUTOS_SONDA:
            raise ErrorModificacion("atributo %s no permitido en la copia SONDA" % attr)
        antes = obj.GetAttribute(attr)
        obj.SetAttribute(attr, valor)
        self._anotar(dict(tipo="set_sonda", obj=obj.GetFullName(), attr=attr, antes=antes, despues=valor))
        return 0

    def cambiar_caso_diagnostico(self, caso=None, escenario=None):
        """Sustituto restringido de CONTEXTO.cambiar_caso en diagnóstico Ref.

        Solo acepta los nombres/rutas exactos de CASO_SONDA y ESC_REF y reutiliza la misma guarda de
        activación de `metodo` (allowlist + _sin_cambios). No permite casos ni escenarios arbitrarios.
        """
        if caso is None and escenario is None:
            raise ErrorModificacion("cambiar_caso en diagnóstico exige Base SEN_SONDA_20261109")
        self._exigir_ref("cambiar_caso")
        if caso is not None and str(caso) not in ("Base SEN_SONDA_20261109", CASO_SONDA):
            raise ErrorModificacion("cambiar_caso en diagnóstico solo permite Base SEN_SONDA_20261109: %r" % (caso,))
        if escenario is not None and str(escenario) not in ("Domingo Madrugada", ESC_REF):
            raise ErrorModificacion("cambiar_caso en diagnóstico solo permite Domingo Madrugada: %r" % (escenario,))
        if caso is not None:
            obj = CONTEXTO._buscar("study", "IntCase", "Base SEN_SONDA_20261109")
            if obj.GetFullName() != CASO_SONDA:
                raise ErrorModificacion("cambiar_caso resolvió un caso distinto de la copia SONDA: %s" % obj.GetFullName())
            self.metodo(obj, "Activate", obj.Activate)()
        if escenario is not None:
            obj = CONTEXTO._buscar("scen", "IntScenario", "Domingo Madrugada")
            if obj.GetFullName() != ESC_REF:
                raise ErrorModificacion("cambiar_caso resolvió un escenario distinto del Ref: %s" % obj.GetFullName())
            self.metodo(obj, "Activate", obj.Activate)()
        return CONTEXTO.actual()

    def activar_caso(self, obj, nombre, fn):
        self._exigir_ref("Activate.IntCase")
        if nombre != "Activate" or obj.GetFullName() not in (CASO_REF, CASO_SONDA):
            raise ErrorModificacion("caso de estudio no permitido: %s (%s)" % (obj.GetFullName(), nombre))
        return CONTEXTO.activar(obj, nombre, fn)

    def activar_escenario(self, obj, nombre, fn):
        self._exigir_ref("Activate.IntScenario")
        if nombre != "Activate" or obj.GetFullName() != ESC_REF:
            raise ErrorModificacion("escenario no permitido: %s (%s)" % (obj.GetFullName(), nombre))
        return CONTEXTO.activar(obj, nombre, fn)

    def metodo(self, obj, nombre, fn):
        if nombre == "SetAttribute":
            return lambda attr, valor: self.escribir(obj, attr, valor)
        if nombre == "CreateVersion" and _clase(obj) == "IntPrj":
            return lambda *a, **k: self.crear_version(obj, fn, *a, **k)
        if nombre == "AddCopy":
            return lambda origen, *partes: envolver(self.copiar(obj, desenvolver(origen), "".join(str(p) for p in partes)))
        if nombre in ("Activate", "Deactivate") and _clase(obj) == "IntPrj":
            return lambda: self.activar_proyecto(obj, nombre, fn)
        if nombre in ("Activate", "Deactivate") and _clase(obj) == "IntCase":
            return lambda: self.activar_caso(obj, nombre, fn)
        if nombre in ("Activate", "Deactivate") and _clase(obj) == "IntScenario":
            return lambda: self.activar_escenario(obj, nombre, fn)
        if nombre == "Execute":
            if _clase(obj) in CALCULO and self._en_caso_sonda(obj):
                self._contexto_sonda("Execute")
                return _envuelta(fn)
            raise ErrorModificacion("Execute() solo para comandos de cálculo dentro de Base SEN_SONDA_20261109")
        if nombre in ("Save", "SaveAs", "Deactivate", "SetStudyTime"):
            raise ErrorModificacion("%s() no está permitido en diagnóstico Ref" % nombre)
        if nombre in BLOQUEADOS_RO or not nombre.startswith(PREFIJOS_LECTURA):
            raise ErrorModificacion("%s() no está permitido en diagnóstico Ref" % nombre)
        return _envuelta(fn)

    def asignar(self, obj, nombre, valor):
        raise ErrorModificacion("asignar %s no está permitido en diagnóstico Ref" % nombre)

    def reconectar(self, app):
        self.app = app

    def resumen(self):
        return list(self.diario)


def main(modo):
    global POLITICA, CONTEXTO
    app = powerfactory.GetApplication()
    CONTEXTO = Contexto(app)
    SALIDA = SalidaPF(app)
    dirs = {k: os.path.join(BRIDGE_DIR, k) for k in ("inbox", "outbox", "done", "files")}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    stop = os.path.join(dirs["inbox"], "STOP")
    if os.path.exists(stop):
        os.remove(stop)
    log = open(os.path.join(BRIDGE_DIR, "bridge.log"), "a", encoding="utf-8")
    inicio, ultimo, n, latido, motivo = time.time(), time.time(), 0, 0.0, "?"
    reconexiones = 0
    muertos_seguidos = 0                    # comandos seguidos que fallan por 'already deleted'
    variation = None
    if modo == "modificacion":
        POLITICA = PoliticaModificacion(app, BRIDGE_DIR)
        try:
            variation = POLITICA.abrir()
        except Exception as e:
            app.PrintError("Puente Claude: no se pudo abrir el modo modificación (%s). Queda en solo lectura." % e)
            try:
                if POLITICA.variation is not None:
                    POLITICA.variation.Deactivate()
            except Exception:
                pass
            POLITICA, variation = PoliticaLectura(), None
    elif modo == "diagnostico_ref":
        POLITICA = PoliticaDiagnosticoRef(app, BRIDGE_DIR)
        try:
            POLITICA.abrir()          # solo registra; NO retiming, NO stage, NO SetStudyTime
        except Exception as e:
            app.PrintError("Puente Claude: falló la guardia de diagnóstico Ref (%s). Queda en solo lectura." % e)
            POLITICA = PoliticaLectura()
    elif modo == "limpieza":
        POLITICA = PoliticaLimpieza(BRIDGE_DIR)
    else:
        POLITICA = PoliticaLectura()
    etiqueta = POLITICA.nombre + (" + cálculo" if ALLOW_CALC and variation is None else "")
    app.PrintPlain("Puente Claude activo en %s (modo %s%s). Detener: crear inbox\\STOP." % (
        BRIDGE_DIR, etiqueta, ", variation %s" % variation if variation else ""))
    if variation and POLITICA._escenario() is not None:
        app.PrintWarn("Hay un escenario de operación activo (%s): los cambios operativos quedan en él SIN guardar. "
                      "Si PF tiene auto-guardado de escenarios, desactívalo." % POLITICA._escenario_nombre())
    log.write(json.dumps(dict(t=ahora(), evento="inicio", modo=etiqueta, variation=variation), ensure_ascii=False) + "\n")
    log.flush()

    EN_CURSO = {}

    def estado(vivo=True):
        try:
            prj, caso = app.GetActiveProject(), app.GetActiveStudyCase()
            prj, caso = (prj.GetFullName() if prj else None), (caso.GetFullName() if caso else None)
        except Exception:
            prj = caso = None
        try:
            extra = dict(contexto=CONTEXTO.actual())
        except Exception:
            extra = {}
        if isinstance(POLITICA, PoliticaModificacion):
            extra.update(variation=variation, escenario=POLITICA._escenario_nombre(), cambios=len(POLITICA.resumen()),
                         diario=POLITICA.ruta_diario)
        elif isinstance(POLITICA, PoliticaDiagnosticoRef):
            extra.update(variation=None, escenario=POLITICA._escenario_nombre(), cambios=len(POLITICA.resumen()),
                         diario=POLITICA.ruta_diario, retiming=False,
                         alcance_calculo="Execute solo en Base SEN_SONDA_20261109 con Ref/caso/escenario exactos")
        calc = bool(ALLOW_CALC) or isinstance(POLITICA, PoliticaDiagnosticoRef)
        escribir_json(os.path.join(BRIDGE_DIR, "status.json"), dict(
            vivo=vivo, pid=os.getpid(), inicio=datetime.datetime.fromtimestamp(inicio).isoformat(timespec="seconds"),
            latido=ahora(), latido_epoch=time.time(), modo=etiqueta, allow_calc=calc, reconexiones=reconexiones,
            proyecto=prj, caso=caso, procesados=n, python=sys.version.split()[0],
            se_detiene_en_min=round(IDLE_MINUTES - (time.time() - ultimo) / 60, 1), en_curso=dict(EN_CURSO) or None, **extra))

    def guardar(nombre, datos):
        """Guarda datos (JSON) en BRIDGE_DIR\\files\\<nombre>.json y devuelve la ruta."""
        nombre = re.sub(r"[^\w\-.]", "_", nombre)
        ruta = os.path.join(dirs["files"], nombre if nombre.endswith(".json") else nombre + ".json")
        escribir_json(ruta, datos)
        return ruta

    def exportar_grafico(nombre="grafico", pagina=None):
        """Exporta la página gráfica activa (o `pagina`, por nombre) a WMF en BRIDGE_DIR\\files. Devuelve la ruta."""
        board = app.GetGraphicsBoard()
        if board is None:
            raise RuntimeError("no hay tablero gráfico abierto")
        if pagina:
            pg = board.GetPage(pagina, 0)
            if pg is None:
                raise RuntimeError("no existe la página %r" % pagina)
            board.Show(pg)
        ruta = os.path.join(dirs["files"], re.sub(r"[^\w\-.]", "_", nombre) + ".wmf")
        board.WriteWMF(ruta)
        return ruta

    # Comandos que quedaron en inbox de una sesión anterior (p. ej. tras un Break) no se re-ejecutan: se apartan a
    # "descartados" y se anotan en el log (07-10-2026: un bucle largo interrumpido volvió a correr al reiniciar).
    os.makedirs(os.path.join(BRIDGE_DIR, "descartados"), exist_ok=True)
    for f in os.listdir(dirs["inbox"]):
        r = os.path.join(dirs["inbox"], f)
        if f.endswith(".py") and os.path.getmtime(r) < inicio - 60:
            os.replace(r, os.path.join(BRIDGE_DIR, "descartados", f))
            log.write(json.dumps(dict(t=ahora(), evento="descartado al iniciar", id=f[:-3]), ensure_ascii=False) + chr(10))
    log.flush()
    try:
        while True:
            if os.path.exists(stop):
                os.remove(stop)
                motivo = "STOP"
                break
            if time.time() - ultimo > IDLE_MINUTES * 60:
                motivo = "inactividad"
                break
            if time.time() - inicio > MAX_HOURS * 3600:
                motivo = "tope de horas"
                break
            if time.time() - latido > 5:
                estado()
                latido = time.time()
            pendientes = sorted((f for f in os.listdir(dirs["inbox"]) if f.endswith(".py")),
                                key=lambda f: os.path.getmtime(os.path.join(dirs["inbox"], f)))
            if not pendientes:
                time.sleep(POLL_S)
                continue
            try:                                    # PF puede invalidar el app (otro script llamó GetApplication,
                vivo_pf = app.GetActiveProject() is not None   # se cerró o desactivó el proyecto)
            except RuntimeError:
                vivo_pf = False
            if not vivo_pf:                         # p. ej. un flujo que dispara otro script Python de PF
                try:
                    nuevo = powerfactory.GetApplication()
                    if nuevo is None or nuevo.GetActiveProject() is None:
                        raise RuntimeError("sin proyecto activo")
                    app = nuevo
                    CONTEXTO.reconectar(app)
                    POLITICA.reconectar(app)
                    SALIDA.reconectar(app)
                    reconexiones += 1
                    log.write(json.dumps(dict(t=ahora(), evento="reconexión", n=reconexiones), ensure_ascii=False) + chr(10))
                    log.flush()
                except Exception as e:
                    motivo = "PF desconectado o sin proyecto activo (%s)" % e
                    break
            f = pendientes[0]
            cid = f[:-3]
            ruta = os.path.join(dirs["inbox"], f)
            fuente = open(ruta, encoding="utf-8").read()
            res = dict(id=cid, inicio=ahora(), modo=etiqueta, ok=False, salida="", error=None, traceback=None, resultado=None)
            EN_CURSO.update(id=cid, desde=ahora(), desde_epoch=time.time())   # el latido no avanza mientras corre:
            estado()                                                           # pf_send lo informa como "ocupado"
            t0 = time.time()
            prohibido = [p for p in PROHIBIDO_EN_FUENTE if re.search(p, fuente)]
            if prohibido:
                res["error"] = "Rechazado antes de ejecutar: el comando contiene %s" % ", ".join(prohibido)
            else:
                ns = dict(__name__="pf_bridge_cmd", app=Vista(app), resultado={}, guardar=guardar,
                          exportar_grafico=exportar_grafico, as_list=as_list, get_attr=get_attr, SoloLectura=SoloLectura,
                          ErrorModificacion=ErrorModificacion, MODO=etiqueta, es_red=lambda o: es_red(desenvolver(o)),
                          cambiar_caso=CONTEXTO.cambiar_caso, contexto=CONTEXTO.actual, salida=SALIDA.leer)
                if isinstance(POLITICA, PoliticaModificacion):
                    ns.update(revisar=POLITICA.revisar, deshacer=POLITICA.deshacer, diario=POLITICA.resumen,
                              nombrar=POLITICA.nombrar, renombrar_claude=POLITICA.renombrar_claude, activar_variation=POLITICA.activar_variation,
                              copiar_escenario=POLITICA.copiar_escenario, carpeta_escenarios=POLITICA.carpeta_escenarios, renombrar_escenario=POLITICA.renombrar_escenario,
                              VARIATION=variation)
                elif isinstance(POLITICA, PoliticaDiagnosticoRef):
                    ns.update(diario=POLITICA.resumen, REF=PRJ_REF, LAB=PRJ_LAB, CASO_REF=CASO_REF,
                              CASO_SONDA=CASO_SONDA, ESC_REF=ESC_REF, SONDA="Base SEN_SONDA_20261109")
                    # Sustituto restringido: misma allowlist/guarda de activación, sin casos arbitrarios.
                    ns["cambiar_caso"] = POLITICA.cambiar_caso_diagnostico
                buf = io.StringIO()
                capturar_ow = not fuente.startswith("# pf_bridge: salida_manual")
                marca_ow = SALIDA.marca() if capturar_ow else None
                try:
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                        exec(compile(fuente, cid + ".py", "exec"), ns)
                    res["ok"] = True
                except (SoloLectura, ErrorModificacion) as e:
                    res["error"] = "%s: %s" % (type(e).__name__, e)
                    res["traceback"] = traceback.format_exc()
                except KeyboardInterrupt:           # Break del usuario en PF: se respeta y se cierra
                    motivo = "Break"
                    raise
                except BaseException as e:      # incluye SystemExit del comando: el puente sigue
                    res["error"] = "%s: %s" % (type(e).__name__, e)
                    if "already deleted" in str(e):
                        res["error"] += " (PF invalidó la conexión; el puente se reconecta en el próximo comando)"
                    res["traceback"] = traceback.format_exc()
                salida = buf.getvalue()
                res["salida"] = salida if len(salida) <= MAX_SALIDA else salida[:MAX_SALIDA] + "\n...[truncado]"
                res["resultado"] = ns.get("resultado")
                res["output_window"] = SALIDA.desde(marca_ow) if capturar_ow else dict(disponible=False, nota="Captura automatica omitida por pragma salida_manual; ventana intacta; salida() sigue disponible")
                # 09-10-2026: las caídas "already deleted" aparecen en el comando SIGUIENTE a uno que recorrió miles de objetos.
                # Se sueltan las referencias del comando y se recolecta ahora, con PF en un estado conocido.
                try:
                    import gc
                    ns.clear(); gc.collect()
                except Exception:
                    pass
            res["duracion_s"] = round(time.time() - t0, 3)
            try:
                escribir_json(os.path.join(dirs["outbox"], cid + ".json"), res)
            except Exception as e:              # resultado no serializable: se devuelve como texto
                res["resultado"] = repr(res["resultado"])[:MAX_SALIDA]
                res["error"] = (res["error"] or "") + " | resultado no serializable: %s" % e
                escribir_json(os.path.join(dirs["outbox"], cid + ".json"), res)
            os.replace(ruta, os.path.join(dirs["done"], f))
            EN_CURSO.clear()
            log.write(json.dumps(dict(t=res["inicio"], id=cid, ok=res["ok"], error=res["error"], s=res["duracion_s"]),
                                 ensure_ascii=False) + "\n")
            log.flush()
            n += 1
            ultimo = time.time()
            muertos_seguidos = muertos_seguidos + 1 if "already deleted" in str(res.get("error") or "") else 0
            if muertos_seguidos >= MAX_MUERTOS:
                motivo = ("conexión con PF inutilizable: %d comandos seguidos con 'already deleted' pese a reconectar. "
                          "Reiniciar el puente" % muertos_seguidos)
                break
            estado()
    finally:
        estado(vivo=False)
        log.write(json.dumps(dict(t=ahora(), evento="fin", procesados=n, motivo=motivo), ensure_ascii=False) + "\n")
        log.close()
        if isinstance(POLITICA, PoliticaModificacion):
            try:
                final = POLITICA.cerrar()
                if final:
                    variation = final
                    app.PrintPlain("Variation de la sesión renombrada a '%s'." % final)
            except Exception as e:
                app.PrintWarn("No se pudo renombrar la variation: %s" % e)
            cambios = [e for e in POLITICA.resumen() if e["tipo"] in ("set", "creado", "copia") and not e.get("deshecho")]
            try:
                app.PrintPlain("Cambios vigentes de Claude: %d (diario: %s)." % (len(cambios), POLITICA.ruta_diario))
                app.PrintPlain("Para descartarlos: desactivar/borrar la variation %s y no guardar el escenario de operación; "
                               "borrar los objetos '*%s' que queden fuera de la red." % (variation, SUFIJO))
            except RuntimeError:
                pass
    try:
        problema = CONTEXTO.restaurar()             # volver al caso y escenario con que partió el puente
        if problema:
            app.PrintWarn("No se restauró el caso/escenario inicial: %s" % problema)
        app.PrintPlain("Puente Claude detenido (%s). Comandos procesados: %d." % (motivo, n))
    except RuntimeError:                            # app ya invalidado por PF
        pass


main(globals().get("MODO_PUENTE", MODO))      # PF no siempre define __name__ == "__main__"
