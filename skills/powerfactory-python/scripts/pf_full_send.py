#!/usr/bin/env python3
"""Cliente del puente PowerFactory de ACCESO TOTAL.

El puente debe estar corriendo dentro de PowerFactory y haber sido habilitado
explícitamente (`CONFIRMO_ACCESO_TOTAL = True` en la copia de Windows de
`pf_bridge_full.py`). Este cliente no aplica listas de permitidos: una vez que
el estado dice `modo=acceso_total`, envía el código tal cual.

Uso:
    python pf_full_send.py estado
    python pf_full_send.py ejecutar comando.py --timeout 600 --json respuesta.json
    python pf_full_send.py ejecutar comando.py --id 20261109_101500_ab12cd34   # reintento sin duplicar
    python pf_full_send.py -c "resultado = {'proyecto': app.GetActiveProject().GetFullName()}"
    python pf_full_send.py detener
    python pf_full_send.py archivo <nombre> [--copiar DESTINO]
    python pf_full_send.py auditoria -n 20

Transporte: carpeta LOCAL de la máquina Windows que corre PowerFactory
(`%USERPROFILE%\\pf_bridge_full` por defecto). No hay transporte de red: si
este cliente corre en un Mac, `~/pf_bridge_full` es otra carpeta y no llega al
puente. Usar `--dir` o `PF_BRIDGE_FULL_DIR` apuntando a la carpeta real.

Códigos de salida: 0 ok; 1 error del comando; 2 puente no disponible, modo
incorrecto o timeout; 3 uso/validación.
"""
import argparse
import json
import os
import shutil
import sys
import time
import uuid

MODO = "acceso_total"
DIR_DEFECTO = os.environ.get("PF_BRIDGE_FULL_DIR") or os.path.join(
    os.path.expanduser("~"), "pf_bridge_full"
)


class PuenteNoDisponible(Exception):
    pass


class TiempoAgotado(Exception):
    pass


def resolver_dir(dir_=None):
    return os.path.abspath(os.path.expanduser(dir_ or DIR_DEFECTO))


def cargar_estado(dir_=None):
    ruta = os.path.join(resolver_dir(dir_), "status.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def esta_vivo(estado=None, dir_=None):
    """Vivo si hay latido reciente o si hay un comando en curso."""
    e = estado if estado is not None else cargar_estado(dir_)
    if not (e and e.get("vivo")):
        return False
    if time.time() - e.get("latido_epoch", 0) < 20:
        return True
    c = e.get("en_curso") or {}
    return bool(c.get("id") and os.path.exists(
        os.path.join(resolver_dir(dir_), "en_curso", c["id"] + ".py")
    ))


def _exigir_acceso_total(dir_=None):
    estado = cargar_estado(dir_)
    if not estado:
        raise PuenteNoDisponible(
            "no hay status.json en %s. El puente no esta corriendo o el directorio no es el correcto."
            % resolver_dir(dir_)
        )
    if estado.get("modo") != MODO or not estado.get("full_access"):
        raise PuenteNoDisponible(
            "el puente en %s no esta en modo acceso total (modo=%r, full_access=%r). "
            "No se envia nada." % (resolver_dir(dir_), estado.get("modo"), estado.get("full_access"))
        )
    if not esta_vivo(estado, dir_):
        raise PuenteNoDisponible(
            "el puente no tiene latido reciente (motivo=%r). No se envia nada; "
            "revisar estado antes de reintentar." % estado.get("motivo")
        )
    return estado


def escribir_comando(fuente, cid=None, dir_=None):
    """Escribe inbox/<id>.py con rename atomico. Devuelve (id, ruta)."""
    d = resolver_dir(dir_)
    cid = cid or (time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
    inbox = os.path.join(d, "inbox")
    os.makedirs(inbox, exist_ok=True)
    tmp = os.path.join(inbox, cid + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(fuente)
    os.replace(tmp, os.path.join(inbox, cid + ".py"))
    return cid, os.path.join(inbox, cid + ".py")


def _leer_respuesta(ruta, cid):
    with open(ruta, encoding="utf-8") as f:
        r = json.load(f)
    if r.get("id") != cid:
        raise PuenteNoDisponible(
            "respuesta en %s no corresponde al id %r (id=%r); no se usa"
            % (ruta, cid, r.get("id"))
        )
    return r


def enviar(fuente, timeout=600.0, cid=None, dir_=None, poll=0.3):
    """Envia y espera la respuesta. Un timeout NO cancela el comando en PF."""
    d = resolver_dir(dir_)
    salida = os.path.join(d, "outbox", cid + ".json") if cid else None
    if salida and os.path.exists(salida):
        # Reintento del mismo id: se devuelve la respuesta ya producida, incluso
        # si el puente ya se detuvo. No se reenvía nada.
        return _leer_respuesta(salida, cid)
    _exigir_acceso_total(d)
    cid = cid or (time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
    salida = os.path.join(d, "outbox", cid + ".json")
    if os.path.exists(salida):
        return _leer_respuesta(salida, cid)
    escribir_comando(fuente, cid=cid, dir_=d)
    t0 = time.time()
    while not os.path.exists(salida):
        if time.time() - t0 > timeout:
            raise TiempoAgotado(
                "sin respuesta en %.1f s (id %s). El comando PUEDE seguir corriendo en PF: "
                "no se cancelo. Revisar estado/auditoria antes de reintentar; no reenviar "
                "con otro id." % (timeout, cid)
            )
        time.sleep(poll)
    time.sleep(0.05)
    return _leer_respuesta(salida, cid)


def _imprimir_respuesta(r, args):
    if r.get("salida"):
        print(r["salida"], end="" if r["salida"].endswith("\n") else "\n")
    if r.get("resultado") is not None:
        print("resultado:", json.dumps(r["resultado"], ensure_ascii=False, indent=1, default=str)[:20000])
    elif r.get("resultado_archivo"):
        print("resultado grande:", r["resultado_archivo"], "(%s bytes)" % r.get("resultado_bytes"))
    if r.get("error"):
        print("ERROR:", r["error"])
        if r.get("traceback"):
            print(r["traceback"])
    ow = r.get("output_window") or {}
    if ow.get("disponible"):
        for clave, rot in (("errores", "PF ERROR"), ("avisos", "PF WARN")):
            if ow.get("n_" + clave):
                print("%s (%d nuevos):" % (rot, ow["n_" + clave]))
                for l in (ow.get(clave) or [])[:40]:
                    print("  " + l)
        if getattr(args, "ow", False) and ow.get("n_lineas"):
            print("PF OUTPUT (%d lineas nuevas):" % ow["n_lineas"])
            for l in ow.get("lineas") or []:
                print("  " + l)
    elif ow:
        print("PF OUTPUT no disponible:", ow.get("nota"))
    print(
        "[%s | %s | %.2f s | %s | acceso_total]"
        % (r.get("id"), "ok" if r.get("ok") else "error", r.get("duracion_s", 0), r.get("modo"))
    )
    if getattr(args, "json", None):
        json.dump(r, open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _cmd_estado(a):
    d = resolver_dir(a.dir)
    e = cargar_estado(d)
    if not e:
        print("DETENIDO: no hay status.json en %s" % d)
        return 2
    vivo = esta_vivo(e, d)
    if vivo and e.get("modo") == MODO and e.get("full_access"):
        print("ACCESO TOTAL ACTIVO | modo=%s | sin_restricciones=%s" % (
            e.get("modo"), e.get("sin_restricciones")))
    elif vivo:
        print("VIVO, PERO NO ES ACCESO TOTAL | modo=%r | full_access=%r" % (
            e.get("modo"), e.get("full_access")))
    else:
        print("DETENIDO | motivo=%r" % e.get("motivo"))
    print("directorio:", d)
    for k in ("sesion", "pid", "proyecto", "caso", "escenario", "procesados", "ok",
              "errores", "rechazados", "se_detiene_en_min", "expira_en_min", "en_curso"):
        if k in e:
            print("  %s: %s" % (k, e.get(k)))
    if e.get("nota"):
        print("  nota:", e["nota"])
    return 0 if (vivo and e.get("modo") == MODO and e.get("full_access")) else 2


def _cmd_enviar(a):
    if a.codigo is not None:
        fuente = a.codigo
    elif a.archivo:
        with open(a.archivo, encoding="utf-8") as f:
            fuente = f.read()
    else:
        print("falta un archivo o -c", file=sys.stderr)
        return 3
    print(
        "ADVERTENCIA: acceso total. El codigo se ejecuta sin listas de permitidos, "
        "con la API completa de PF y los permisos del usuario.",
        file=sys.stderr,
    )
    try:
        r = enviar(fuente, timeout=a.timeout, cid=getattr(a, "id", None), dir_=a.dir)
    except PuenteNoDisponible as e:
        print("NO ENVIADO:", e, file=sys.stderr)
        return 2
    except TiempoAgotado as e:
        print("TIMEOUT:", e, file=sys.stderr)
        return 2
    _imprimir_respuesta(r, a)
    return 0 if r.get("ok") else 1


def _cmd_detener(a):
    d = resolver_dir(a.dir)
    estado = cargar_estado(d)
    if estado and estado.get("modo") != MODO:
        print(
            "NO ENVIADO: el puente en %s no es de acceso total (modo=%r). "
            "No se crea STOP para no detener el puente equivocado."
            % (d, estado.get("modo")),
            file=sys.stderr,
        )
        return 2
    inbox = os.path.join(d, "inbox")
    os.makedirs(inbox, exist_ok=True)
    open(os.path.join(inbox, "STOP"), "w").close()
    print("STOP enviado a", d)
    print("Se detiene entre comandos. Si hay una llamada PF bloqueada, puede tardar; no se puede cancelar de forma segura.")
    return 0


def _cmd_archivo(a):
    d = resolver_dir(a.dir)
    nombre = a.nombre
    ruta = nombre if os.path.isabs(nombre) else os.path.join(d, "files", nombre)
    if not os.path.exists(ruta):
        print("no existe:", ruta, file=sys.stderr)
        return 3
    print("archivo:", ruta)
    print("bytes:", os.path.getsize(ruta))
    if a.copiar:
        shutil.copy2(ruta, a.copiar)
        print("copiado a:", os.path.abspath(a.copiar))
    return 0


def _cmd_auditoria(a):
    d = resolver_dir(a.dir)
    ruta = os.path.join(d, "auditoria.jsonl")
    if not os.path.exists(ruta):
        print("no existe:", ruta, file=sys.stderr)
        return 3
    with open(ruta, encoding="utf-8") as f:
        lineas = f.readlines()
    for linea in lineas[-max(0, a.n):] if a.n else lineas:
        print(linea.rstrip())
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", help="raiz de pf_bridge_full (la que contiene status.json/inbox/outbox)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("estado", help="estado del puente")
    p.add_argument("--dir", default=argparse.SUPPRESS)

    p = sub.add_parser("ejecutar", help="enviar un archivo .py")
    p.add_argument("archivo", nargs="?")
    p.add_argument("--timeout", type=float, default=600)
    p.add_argument("--id", help="reutilizar un id ya enviado (reintento sin duplicar)")
    p.add_argument("--json")
    p.add_argument("--ow", action="store_true")
    p.add_argument("--dir", default=argparse.SUPPRESS)

    p = sub.add_parser("detener", help="crear inbox/STOP")
    p.add_argument("--dir", default=argparse.SUPPRESS)

    p = sub.add_parser("archivo", help="ubicar un archivo exportado en files/")
    p.add_argument("nombre")
    p.add_argument("--copiar")
    p.add_argument("--dir", default=argparse.SUPPRESS)

    p = sub.add_parser("auditoria", help="ultimas lineas de auditoria.jsonl")
    p.add_argument("-n", type=int, default=20)
    p.add_argument("--dir", default=argparse.SUPPRESS)

    # -c se resuelve antes de argparse para conservar el uso corto.
    argv = list(sys.argv[1:] if argv is None else argv)
    if "-c" in argv:
        i = argv.index("-c")
        if i + 1 >= len(argv):
            print("-c necesita codigo", file=sys.stderr)
            return 3
        codigo = argv[i + 1]
        resto = argv[:i] + argv[i + 2:]
        acciones = ("estado", "ejecutar", "detener", "archivo", "auditoria")
        if not any(x in acciones for x in resto):
            resto = ["ejecutar"] + resto
        a = ap.parse_args(resto)
        if a.cmd != "ejecutar":
            print("-c solo se usa con 'ejecutar' (o sin accion)", file=sys.stderr)
            return 3
        a.codigo, a.archivo = codigo, None
        return _cmd_enviar(a)
    a = ap.parse_args(argv)
    if a.cmd == "estado":
        return _cmd_estado(a)
    if a.cmd == "ejecutar":
        a.codigo = None
        return _cmd_enviar(a)
    if a.cmd == "detener":
        return _cmd_detener(a)
    if a.cmd == "archivo":
        return _cmd_archivo(a)
    if a.cmd == "auditoria":
        return _cmd_auditoria(a)
    return 3


if __name__ == "__main__":
    sys.exit(main())
