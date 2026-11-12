"""Puente PowerFactory de ACCESO TOTAL, incorporado a la skill.

El modo full se usa para el alcance autorizado por el usuario; ver
`references/bridge-full.md` de la skill. No reemplaza el modo de lectura.
La copia suministrada por Vicente ya tiene CONFIRMO_ACCESO_TOTAL en True.
Para usarlo:

  1. usar este archivo de la skill en la máquina Windows con PowerFactory;
  2. mantener el alcance full autorizado y el proyecto correcto;
  3. apuntar el ComPython a este archivo y ejecutarlo.

Qué hace una vez arrancado:
  - revisa `%USERPROFILE%\\pf_bridge_full\\inbox` cada `POLL_S` segundos;
  - por cada `<id>.py`, ejecuta el código con `exec` en el hilo del script de
    PowerFactory (el mismo hilo de la API de PF), con el objeto `app` CRUDO;
  - deja la respuesta en `outbox/<id>.py` -> `outbox/<id>.json`;
  - archiva el comando en `ejecutados/<id>.py` y anota en `auditoria.jsonl`;
  - se detiene con `inbox/STOP` o por inactividad; el tope de horas es opcional (sin tope por defecto).

Qué NO hace:
  - no aplica listas de permitidos de objetos, métodos, atributos ni de código;
  - no envuelve `app` en una vista de solo lectura;
  - no aplica el filtro `PROHIBIDO_EN_FUENTE` del puente de lectura;
  - no crea variations, stages, escenarios ni comandos;
  - no cambia la hora de estudio, no activa/desactiva casos o escenarios,
    no guarda y no ejecuta cálculos al arrancar;
  - no restaura el caso/escenario al terminar (restaurar sería un cambio
    automático, justamente lo que este modo prohíbe en el arranque/cierre).

ADVERTENCIA: una vez habilitado, el código enviado tiene los permisos del
usuario de Windows que corre PowerFactory y toda la superficie de la API de PF.
La auditoría es posterior, no un sandbox. Ver references/bridge-full.md.
"""
import contextlib
import dataclasses
import typing
import datetime
import gc
import hashlib
import io
import json
import os
import re
import sys
import time
import traceback
import uuid

try:  # En PowerFactory existe. Fuera de PF (pruebas) no es obligatorio.
    import powerfactory  # noqa: F401
except Exception:  # pragma: no cover - depende del entorno
    powerfactory = None


# --------------------------------------------------------------------------- configuración
MODO = "acceso_total"
VERSION = "prototipo-1"

# Valor de la copia Windows aportada por el usuario; arrancar sólo con modo full autorizado.
CONFIRMO_ACCESO_TOTAL = True

BRIDGE_DIR = os.environ.get("PF_BRIDGE_FULL_DIR") or os.path.join(
    os.path.expanduser("~"), "pf_bridge_full"
)
IDLE_MINUTES = 60.0      # menos que el puente de lectura: aquí el riesgo es mayor
# Sin tope de horas por defecto (Vicente, 11-11-2026): el puente full sólo se detiene por STOP o inactividad.
# Tope opcional: PF_BRIDGE_FULL_MAX_HOURS=<horas> o Config(max_hours=...).
_mh = os.environ.get("PF_BRIDGE_FULL_MAX_HOURS", "").strip()
MAX_HOURS = float(_mh) if _mh else None
POLL_S = 0.5
MAX_SALIDA = 200_000
MAX_RESULTADO = 1_000_000
MAX_FUENTE = 8 * 1024 * 1024
MAX_TRACEBACK = 50_000


@dataclasses.dataclass
class Config:
    """Configuración inyectable (las pruebas usan otro directorio y límites)."""

    bridge_dir: str = BRIDGE_DIR
    confirmado: bool = CONFIRMO_ACCESO_TOTAL
    idle_min: float = IDLE_MINUTES
    max_hours: typing.Optional[float] = MAX_HOURS
    poll_s: float = POLL_S
    max_salida: int = MAX_SALIDA
    max_resultado: int = MAX_RESULTADO
    max_fuente: int = MAX_FUENTE
    capturar_output: bool = True


# --------------------------------------------------------------------------- utilidades
def ahora_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def sha256_bytes(crudo):
    return hashlib.sha256(crudo).hexdigest()


def escribir_json(ruta, datos):
    """Escritura atómica en el mismo volumen (tmp + os.replace)."""
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=a_json)
    os.replace(tmp, ruta)


def leer_json(ruta, defecto=None):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def a_json(v):
    """Serialización de última instancia: objetos PF -> nombre completo."""
    if hasattr(v, "GetFullName"):
        try:
            return v.GetFullName()
        except Exception:
            pass
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


def limitar(texto, maximo, marca="\n...[truncado]"):
    texto = texto or ""
    return texto if len(texto) <= maximo else texto[:maximo] + marca


class Auditoria:
    """JSONL append-only. Registra solicitudes, resultados, errores y eventos."""

    def __init__(self, ruta, sesion):
        self.ruta = ruta
        self.sesion = sesion

    def escribir(self, evento, **campos):
        datos = {"t": ahora_iso(), "sesion": self.sesion, "evento": evento}
        datos.update(campos)
        try:
            with open(self.ruta, "a", encoding="utf-8") as f:
                f.write(json.dumps(datos, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass


# --------------------------------------------------------------------------- Output Window (solo lectura)
TIPOS_OW = {
    "error": ("Error",),
    "warn": ("Warn", "Warning"),
    "info": ("Info",),
    "plain": ("Plain",),
    "event": ("Event",),
}


class SalidaPF:
    """Lectura de la Output Window de PF. Nunca la limpia."""

    def __init__(self, app):
        self.reconectar(app)

    def reconectar(self, app):
        self.app = app
        self.ow, self.mt, self.error = None, {}, None
        if app is None:
            self.error = "sin aplicación PF"
            return
        try:
            self.ow = app.GetOutputWindow()
            mt = getattr(self.ow, "MessageType", None) or getattr(
                type(self.ow), "MessageType", None
            )
            self.mt = {
                k: next(
                    (getattr(mt, n) for n in ns if mt is not None and hasattr(mt, n)),
                    None,
                )
                for k, ns in TIPOS_OW.items()
            }
        except Exception as e:
            self.ow, self.mt, self.error = None, {}, "Output Window no disponible: %s" % e

    def _contenido(self, tipo=None):
        if self.ow is None:
            return []
        if tipo is None:
            return list(self.ow.GetContent())
        filtro = self.mt.get(tipo)
        return list(self.ow.GetContent(filtro)) if filtro is not None else []

    def marca(self):
        if self.ow is None:
            return None
        try:
            return {
                k: len(self._contenido(k))
                for k in [None] + [t for t in ("error", "warn") if self.mt.get(t) is not None]
            }
        except Exception as e:
            self.error = "GetContent falló: %s" % e
            return None

    def desde(self, marca):
        if marca is None:
            return dict(disponible=False, nota=self.error)
        out = dict(disponible=True, filtros=sorted(k for k, v in self.mt.items() if v is not None))
        try:
            for k, n0 in marca.items():
                c = self._contenido(k)
                nuevo = c[n0:] if len(c) >= n0 else c
                clave = "lineas" if k is None else ("errores" if k == "error" else "avisos")
                out["n_" + clave] = len(nuevo)
                out[clave] = nuevo[:400]
        except Exception as e:
            out.update(disponible=False, nota="GetContent falló tras el comando: %s" % e)
        return out

    def leer(self, tipo=None, n=50, buscar=None):
        if tipo is not None and tipo not in TIPOS_OW:
            raise ValueError("tipo debe ser uno de %s" % sorted(TIPOS_OW))
        if tipo is not None and self.mt.get(tipo) is None:
            raise RuntimeError(
                "esta versión de PF no expone el filtro %r; disponibles: %s"
                % (tipo, sorted(k for k, v in self.mt.items() if v is not None))
            )
        c = self._contenido(tipo)
        if buscar:
            r = re.compile(buscar, re.I)
            c = [l for l in c if r.search(l)]
        return c[-n:] if n else c


# --------------------------------------------------------------------------- puente
class PuenteCompleto:
    """Bucle del puente. Todo ocurre en el hilo que ejecuta el ComPython."""

    def __init__(self, config, app):
        self.cfg = config
        self.app = app
        self.dir = os.path.abspath(os.path.expanduser(config.bridge_dir))
        self.dirs = {
            k: os.path.join(self.dir, k)
            for k in (
                "inbox",
                "outbox",
                "en_curso",
                "ejecutados",
                "descartados",
                "duplicados",
                "fallos",
                "files",
            )
        }
        self.sesion = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.inicio = time.time()
        self.ultimo = self.inicio
        self.procesados = 0
        self.ok = 0
        self.errores = 0
        self.rechazados = 0
        self.en_curso = None
        self.motivo = None
        self.salida = None
        self.auditoria = None

    # ---------------------------------------------------------------- arranque
    def _sesion_previa_activa(self):
        """Evita dos bucles sobre la misma carpeta (dos ComPython lanzados)."""
        prev = leer_json(os.path.join(self.dir, "status.json"))
        if not prev or not prev.get("vivo"):
            return None
        en_curso = prev.get("en_curso") or {}
        if en_curso.get("id"):
            return "hay un comando en curso (%s) segun status.json" % en_curso.get("id")
        try:
            hace = time.time() - float(prev.get("latido_epoch") or 0)
        except (TypeError, ValueError):
            hace = 1e9
        if hace < 30:
            return "otra sesion con latido reciente (pid=%s, hace %.1fs)" % (
                prev.get("pid"), hace
            )
        return None

    def preparar(self):
        """Crea el transporte y arranca. No toca datos del proyecto.

        Llamadas PF permitidas aquí: GetActiveProject/GetActiveStudyCase/
        GetActiveScenario (lectura), GetOutputWindow (lectura) y Print* (salida).
        """
        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)
        self.auditoria = Auditoria(os.path.join(self.dir, "auditoria.jsonl"), self.sesion)

        otra = self._sesion_previa_activa()
        if otra:
            self.auditoria.escribir(
                "arranque_rechazado", motivo=otra, directorio=self.dir,
                regla="una sola sesion por carpeta",
            )
            self._pf_print(
                "error",
                "Puente PF ACCESO TOTAL NO iniciado: %s. Detener la otra sesion "
                "(inbox\\STOP) o esperar a que expire; no lanzar dos ComPython sobre "
                "la misma carpeta." % otra,
            )
            return False

        # Evita que un status.json viejo (vivo=true) deje enviar comandos
        # mientras esta sesión todavía está descartando la cola anterior.
        self.estado(vivo=False, motivo="arrancando")

        if not self.cfg.confirmado:
            self.auditoria.escribir(
                "arranque_rechazado",
                motivo="CONFIRMO_ACCESO_TOTAL no es True",
                directorio=self.dir,
            )
            self.estado(vivo=False, motivo="sin confirmación explícita")
            self._pf_print(
                "error",
                "Puente PF ACCESO TOTAL NO iniciado: falta CONFIRMO_ACCESO_TOTAL = True "
                "en la copia de Windows de pf_bridge_full.py.",
            )
            return False

        stop = os.path.join(self.dirs["inbox"], "STOP")
        if os.path.exists(stop):
            try:
                os.remove(stop)
            except OSError:
                pass

        # Nada que quedó de una sesión anterior se re-ejecuta.
        for carpeta, evento in (
            ("inbox", "descartado_al_iniciar"),
            ("en_curso", "comando_interrumpido"),
        ):
            for nombre in sorted(os.listdir(self.dirs[carpeta])):
                if nombre.endswith(".py"):
                    self._mover(nombre, carpeta, "descartados", evento)

        self.salida = SalidaPF(self.app) if self.cfg.capturar_output else None
        self.auditoria.escribir(
            "inicio_sesion",
            modo=MODO,
            version=VERSION,
            full_access=True,
            directorio=self.dir,
            contexto=self.contexto(),
            confirmado=True,
            transporte="carpeta local",
        )
        self.estado(vivo=True)
        self._pf_print(
            "warn",
            "Puente PF ACCESO TOTAL activo (%s). Sin listas de permitidos: el codigo "
            "enviado se ejecuta con la API completa de PF y los permisos del usuario. "
            "Detener: crear inbox\\STOP. Sesion: %s." % (self.dir, self.sesion),
        )
        return True

    # ---------------------------------------------------------------- estado / contexto
    def contexto(self):
        """Lectura de contexto. Nunca cambia caso, escenario ni hora de estudio."""
        out = {"proyecto": None, "caso": None, "escenario": None, "escenario_modificado": None}
        if self.app is None:
            return out
        try:
            p = self.app.GetActiveProject()
            out["proyecto"] = p.GetFullName() if p is not None else None
        except Exception as e:
            out["error_proyecto"] = str(e)
        try:
            c = self.app.GetActiveStudyCase()
            out["caso"] = c.GetFullName() if c is not None else None
        except Exception as e:
            out["error_caso"] = str(e)
        try:
            e = self.app.GetActiveScenario()
            if e is not None:
                out["escenario"] = e.GetFullName()
                out["escenario_modificado"] = bool(get_attr(e, "iModified", 0))
        except Exception as exc:
            out["error_escenario"] = str(exc)
        return out

    def estado(self, vivo=True, motivo=None):
        ahora = time.time()
        datos = {
            "vivo": bool(vivo),
            "modo": MODO,
            "full_access": bool(vivo),
            "sin_restricciones": bool(vivo),
            "politica": "ejecucion arbitraria de Python; app PF crudo; sin listas de permitidos",
            "version": VERSION,
            "transporte": "carpeta local (misma maquina que PowerFactory)",
            "sesion": self.sesion,
            "pid": os.getpid(),
            "inicio": datetime.datetime.fromtimestamp(self.inicio).isoformat(timespec="seconds"),
            "latido": ahora_iso(),
            "latido_epoch": ahora,
            "proyecto": None,
            "caso": None,
            "escenario": None,
            "procesados": self.procesados,
            "ok": self.ok,
            "errores": self.errores,
            "rechazados": self.rechazados,
            "en_curso": dict(self.en_curso) if self.en_curso else None,
            "idle_min": self.cfg.idle_min,
            "max_hours": self.cfg.max_hours,
            "se_detiene_en_min": round(self.cfg.idle_min - (ahora - self.ultimo) / 60.0, 1),
            "expira_en_min": (round(self.cfg.max_hours * 60.0 - (ahora - self.inicio) / 60.0, 1)
                              if self.cfg.max_hours else None),
            "directorio": self.dir,
            "motivo": motivo if motivo is not None else self.motivo,
            "nota": "La auditoria es posterior, no un sandbox. Los comandos pueden cambiar el proyecto.",
        }
        ctx = self.contexto()
        datos.update({k: ctx.get(k) for k in ("proyecto", "caso", "escenario")})
        try:
            escribir_json(os.path.join(self.dir, "status.json"), datos)
        except Exception:
            pass
        return datos

    # ---------------------------------------------------------------- ciclo
    def motivo_fin(self, ahora=None):
        ahora = time.time() if ahora is None else ahora
        if os.path.exists(os.path.join(self.dirs["inbox"], "STOP")):
            return "STOP"
        if ahora - self.ultimo > self.cfg.idle_min * 60.0:
            return "inactividad"
        if self.cfg.max_hours and ahora - self.inicio > self.cfg.max_hours * 3600.0:
            return "tope de horas"
        return None

    def un_ciclo(self):
        """Procesa como máximo un comando. Devuelve (accion, detalle).

        acciones: "fin" (hay que detenerse), "vacio", "ok", "error",
        "rechazado", "duplicado".
        """
        motivo = self.motivo_fin()
        if motivo:
            return ("fin", motivo)
        pendientes = [
            f
            for f in os.listdir(self.dirs["inbox"])
            if f.endswith(".py")
        ]
        if not pendientes:
            return ("vacio", None)
        pendientes.sort(
            key=lambda f: (os.path.getmtime(os.path.join(self.dirs["inbox"], f)), f)
        )
        nombre = pendientes[0]
        cid = nombre[:-3]
        destino = os.path.join(self.dirs["en_curso"], nombre)
        try:
            os.replace(os.path.join(self.dirs["inbox"], nombre), destino)
        except FileNotFoundError:
            return ("vacio", None)
        return self._procesar(cid, destino)

    # ---------------------------------------------------------------- procesamiento
    def _procesar(self, cid, ruta):
        t0 = time.time()
        self.en_curso = {"id": cid, "desde": ahora_iso(), "desde_epoch": t0}
        self.estado()
        res = {
            "id": cid,
            "modo": MODO,
            "full_access": True,
            "sin_restricciones": True,
            "inicio": ahora_iso(),
            "fin": None,
            "ok": False,
            "salida": "",
            "error": None,
            "tipo_error": None,
            "traceback": None,
            "resultado": None,
            "sha256_fuente": None,
            "bytes_fuente": None,
            "fuente_archivo": os.path.relpath(ruta, self.dir),
            "output_window": None,
            "duracion_s": None,
        }
        abortar = None
        try:
            with open(ruta, "rb") as f:
                crudo = f.read()
            res["bytes_fuente"] = len(crudo)
            res["sha256_fuente"] = sha256_bytes(crudo)
            self.auditoria.escribir(
                "comando_recibido",
                id=cid,
                sha256=res["sha256_fuente"],
                bytes=res["bytes_fuente"],
                archivo=res["fuente_archivo"],
            )
            if len(crudo) > self.cfg.max_fuente:
                raise ValueError(
                    "comando de %d bytes supera MAX_FUENTE=%d"
                    % (len(crudo), self.cfg.max_fuente)
                )
            try:
                fuente = crudo.decode("utf-8-sig")
            except UnicodeDecodeError as e:
                raise ValueError("el comando no es UTF-8: %s" % e)

            salida_json = os.path.join(self.dirs["outbox"], cid + ".json")
            if os.path.exists(salida_json) or os.path.exists(
                os.path.join(self.dirs["ejecutados"], cid + ".py")
            ):
                self.rechazados += 1
                self.auditoria.escribir(
                    "comando_rechazado",
                    id=cid,
                    motivo="id duplicado: ya existe respuesta o comando ejecutado",
                    sha256=res["sha256_fuente"],
                )
                self._mover(cid + ".py", "en_curso", "duplicados")
                self.en_curso = None
                self.estado()
                return ("duplicado", cid)

            ns = {
                "__name__": "pf_bridge_full_cmd",
                "app": self.app,  # objeto CRUDO de PowerFactory
                "powerfactory": powerfactory,
                "resultado": {},
                "guardar": self.guardar,
                "as_list": as_list,
                "get_attr": get_attr,
                "contexto": self.contexto,
                "salida": self.salida.leer if self.salida is not None else (lambda *a, **k: []),
                "MODO": MODO,
                "VERSION": VERSION,
                "ACCESO_TOTAL": True,
                "dir_puente": self.dir,
            }
            marca_ow = (
                self.salida.marca()
                if self.salida is not None and self.cfg.capturar_output
                else None
            )
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    exec(compile(fuente, cid + ".py", "exec"), ns)
                res["ok"] = True
            except KeyboardInterrupt:
                res["error"] = "KeyboardInterrupt"
                res["tipo_error"] = "KeyboardInterrupt"
                res["traceback"] = limitar(traceback.format_exc(), MAX_TRACEBACK)
                self.motivo = "Break"
                abortar = "KeyboardInterrupt"
            except BaseException as e:  # incluye SystemExit del comando
                res["error"] = "%s: %s" % (type(e).__name__, e)
                res["tipo_error"] = type(e).__name__
                res["traceback"] = limitar(traceback.format_exc(), MAX_TRACEBACK)
            res["salida"] = limitar(buf.getvalue(), self.cfg.max_salida)
            self._volcar_resultado(cid, res, ns.get("resultado"))
            if self.salida is not None:
                res["output_window"] = self.salida.desde(marca_ow)
            else:
                res["output_window"] = dict(
                    disponible=False, nota="captura de Output Window desactivada"
                )
            try:
                ns.clear()
                gc.collect()
            except Exception:
                pass
        except KeyboardInterrupt:
            res["ok"] = False
            res["error"] = "KeyboardInterrupt"
            res["tipo_error"] = "KeyboardInterrupt"
            res["traceback"] = limitar(traceback.format_exc(), MAX_TRACEBACK)
            self.motivo = "Break"
            abortar = "KeyboardInterrupt"
        except BaseException as e:  # error de infraestructura: lectura, tamaño, etc.
            res["ok"] = False
            res["error"] = "%s: %s" % (type(e).__name__, e)
            res["tipo_error"] = type(e).__name__
            res["traceback"] = limitar(traceback.format_exc(), MAX_TRACEBACK)

        res["duracion_s"] = round(time.time() - t0, 3)
        res["fin"] = ahora_iso()
        self._entregar(cid, res)
        self.procesados += 1
        if res["ok"]:
            self.ok += 1
        else:
            self.errores += 1
        self.ultimo = time.time()
        self.en_curso = None
        self.estado()
        self.auditoria.escribir(
            "comando_fin" if res["ok"] else "comando_error",
            id=cid,
            ok=bool(res["ok"]),
            tipo_error=res["tipo_error"],
            error=res["error"],
            duracion_s=res["duracion_s"],
            sha256=res["sha256_fuente"],
            salida_bytes=len((res.get("salida") or "").encode("utf-8")),
            traceback_bytes=len((res.get("traceback") or "").encode("utf-8")),
            resultado_bytes=res.get("resultado_bytes"),
            resultado_sha256=res.get("resultado_sha256"),
            resultado_archivo=res.get("resultado_archivo"),
        )
        if abortar:
            raise KeyboardInterrupt
        return ("ok" if res["ok"] else "error", cid)

    def _volcar_resultado(self, cid, res, resultado):
        """Resultado pequeño va en la respuesta; grande va a files/."""
        if resultado is None:
            return
        try:
            texto = json.dumps(resultado, ensure_ascii=False, default=a_json)
            crudo = texto.encode("utf-8")
            res["resultado_bytes"] = len(crudo)
            res["resultado_sha256"] = sha256_bytes(crudo)
            if len(crudo) > self.cfg.max_resultado:
                ruta = os.path.join(self.dirs["files"], cid + "_resultado.json")
                with open(ruta + ".tmp", "w", encoding="utf-8") as f:
                    f.write(texto)
                os.replace(ruta + ".tmp", ruta)
                res["resultado_archivo"] = os.path.relpath(ruta, self.dir)
                res["resultado_nota"] = (
                    "resultado grande: se guardo completo en files/; la respuesta "
                    "no lo repite (limite MAX_RESULTADO=%d bytes)" % self.cfg.max_resultado
                )
                res["resultado"] = None
            else:
                res["resultado"] = resultado
        except Exception as e:
            try:
                rep = repr(resultado)
            except Exception:
                rep = "<no representable>"
            res["resultado"] = limitar(rep, self.cfg.max_salida)
            res["resultado_repr"] = True
            res["resultado_error"] = "%s: %s" % (type(e).__name__, e)

    def _entregar(self, cid, res):
        """Respuesta atómica + archivo de comando a ejecutados/. Nunca relanza."""
        ruta = os.path.join(self.dirs["outbox"], cid + ".json")
        try:
            escribir_json(ruta, res)
        except Exception as e:
            # Segundo intento con el resultado como texto.
            try:
                copia = dict(res)
                if copia.get("resultado") is not None:
                    copia["resultado"] = limitar(repr(copia["resultado"]), self.cfg.max_salida)
                copia["error"] = (copia.get("error") or "") + (
                    " | respuesta no serializable: %s" % e
                )
                escribir_json(ruta, copia)
            except Exception as e2:
                self.auditoria.escribir(
                    "error_infra", id=cid, motivo="no se pudo escribir la respuesta: %s" % e2
                )
        self._mover(cid + ".py", "en_curso", "ejecutados")

    # ---------------------------------------------------------------- archivos
    def _mover(self, nombre, origen, destino, evento=None, **extra):
        src = os.path.join(self.dirs[origen], nombre)
        dst = os.path.join(self.dirs[destino], nombre)
        if os.path.exists(dst):
            base, ext = os.path.splitext(nombre)
            dst = os.path.join(
                self.dirs[destino], "%s_%s%s" % (base, time.strftime("%H%M%S"), ext)
            )
        try:
            os.replace(src, dst)
        except Exception:
            return None
        if evento and self.auditoria is not None:
            self.auditoria.escribir(
                evento,
                id=nombre[:-3] if nombre.endswith(".py") else nombre,
                archivo=os.path.relpath(dst, self.dir),
                **extra
            )
        return dst

    def guardar(self, nombre, datos, formato=None):
        """Guarda datos en files/ y devuelve un descriptor (ruta, bytes, sha256).

        formato: "json" (defecto), "texto"/"txt" o "bin"/"bytes".
        Sirve para exportaciones grandes: no pasan por la respuesta JSON.
        """
        base = re.sub(r"[^\w\-.]+", "_", str(nombre or "datos")).strip("._") or "datos"
        if formato is None:
            formato = "bin" if isinstance(datos, (bytes, bytearray)) else "json"
        fmt = str(formato).lower()
        if fmt == "json":
            if not base.lower().endswith(".json"):
                base += ".json"
            crudo = json.dumps(datos, ensure_ascii=False, indent=1, default=a_json).encode(
                "utf-8"
            )
        elif fmt in ("texto", "txt", "text"):
            if not base.lower().endswith(".txt"):
                base += ".txt"
            crudo = str(datos).encode("utf-8")
        elif fmt in ("bin", "bytes", "binario"):
            if not base.lower().endswith(".bin"):
                base += ".bin"
            crudo = bytes(datos)
        else:
            raise ValueError("formato desconocido: %r (usar json, texto o bin)" % (formato,))
        ruta = os.path.join(self.dirs["files"], base)
        raiz, ext = os.path.splitext(ruta)
        n = 2
        while os.path.exists(ruta):
            ruta = "%s_%d%s" % (raiz, n, ext)
            n += 1
        with open(ruta + ".tmp", "wb") as f:
            f.write(crudo)
        os.replace(ruta + ".tmp", ruta)
        return {
            "archivo": os.path.relpath(ruta, self.dir),
            "ruta": ruta,
            "bytes": len(crudo),
            "sha256": sha256_bytes(crudo),
            "formato": fmt,
        }

    def _descartar_pendientes(self):
        """Al cerrar no se deja nada que pueda re-ejecutarse en otra sesión."""
        for carpeta, evento in (
            ("inbox", "descartado_al_terminar"),
            ("en_curso", "interrumpido_al_terminar"),
        ):
            try:
                nombres = sorted(os.listdir(self.dirs[carpeta]))
            except OSError:
                continue
            for nombre in nombres:
                if nombre.endswith(".py"):
                    self._mover(nombre, carpeta, "descartados", evento)

    # ---------------------------------------------------------------- salida PF
    def _pf_print(self, tipo, texto):
        if self.app is None:
            print(texto)
            return
        nombres = {
            "error": ("PrintError",),
            "warn": ("PrintWarn", "PrintError"),
            "plain": ("PrintPlain", "PrintInfo"),
        }.get(tipo, ("PrintPlain",))
        for nombre in nombres:
            fn = getattr(self.app, nombre, None)
            if fn is None:
                continue
            try:
                fn(texto)
                return
            except Exception:
                continue
        print(texto)

    # ---------------------------------------------------------------- ejecución
    def correr(self, max_comandos=None, dormir=True):
        """Bucle principal. `max_comandos` existe para pruebas/diagnóstico."""
        if not self.preparar():
            return 0
        procesados = 0
        latido = time.time()
        try:
            while True:
                ahora = time.time()
                if ahora - latido >= 5.0:
                    # El cliente considera vivo por latido reciente: sin esto,
                    # un puente ocioso >20 s parecería detenido.
                    self.estado()
                    latido = ahora
                accion, detalle = self.un_ciclo()
                if accion == "fin":
                    self.motivo = detalle
                    break
                if accion in ("ok", "error", "rechazado", "duplicado"):
                    procesados += 1
                    latido = time.time()
                    if max_comandos is not None and procesados >= max_comandos:
                        self.motivo = self.motivo or "limite de comandos de prueba"
                        break
                    continue
                # vacio
                if max_comandos is not None or not dormir:
                    break
                time.sleep(self.cfg.poll_s)
        except KeyboardInterrupt:
            self.motivo = "Break"
        finally:
            self._descartar_pendientes()
            self.estado(vivo=False, motivo=self.motivo or "fin")
            if self.auditoria is not None:
                self.auditoria.escribir(
                    "fin_sesion",
                    motivo=self.motivo or "fin",
                    procesados=self.procesados,
                    ok=self.ok,
                    errores=self.errores,
                    rechazados=self.rechazados,
                )
            self._pf_print(
                "plain",
                "Puente PF acceso total detenido (%s). Comandos: %d (ok=%d, errores=%d, "
                "rechazados=%d)." % (
                    self.motivo or "fin", self.procesados, self.ok, self.errores, self.rechazados
                ),
            )
        return procesados


def main(config=None):
    """Punto de entrada. No arranca nada si falta la confirmación explícita."""
    cfg = config or Config()
    if not cfg.confirmado:
        app = None
        try:
            if powerfactory is not None:
                app = powerfactory.GetApplication()
        except Exception:
            app = None
        PuenteCompleto(cfg, app).preparar()
        return 0
    if powerfactory is None:
        raise RuntimeError(
            "no se pudo importar powerfactory: este script debe ejecutarse dentro de PowerFactory"
        )
    app = powerfactory.GetApplication()
    if app is None:
        raise RuntimeError("PowerFactory.GetApplication() devolvió None")
    return PuenteCompleto(cfg, app).correr()


# En PowerFactory `__name__` no siempre es "__main__": se arranca salvo que una
# prueba ponga el centinela. Las pruebas lo definen antes de importar. Fuera de
# PF (powerfactory no importable) no se arranca nada por accidente.
if powerfactory is not None and not (
    globals().get("PF_BRIDGE_FULL_SIN_ARRANCAR")
    or os.environ.get("PF_BRIDGE_FULL_SIN_ARRANCAR") == "1"
):
    main()
