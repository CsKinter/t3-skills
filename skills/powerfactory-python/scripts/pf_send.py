"""Cliente del puente PF (lado Claude). Requiere que pf_bridge.py esté corriendo dentro de PowerFactory.

    python pf_send.py estado
    python pf_send.py ejecutar comando.py [--timeout 300] [--json salida.json]
    python pf_send.py -c "for l in app.GetCalcRelevantObjects('*.ElmLne')[:5]: print(l.loc_name)"
    python pf_send.py detener

Dentro del comando existen: app (vista solo lectura del app de PF), resultado (dict que se devuelve como JSON),
guardar(nombre, datos) -> archivo en pf_bridge\\files, as_list, get_attr, SoloLectura, MODO, exportar_grafico(nombre).
En modo modificación (se arranca con pf_bridge_modificar.py; el agente puede hacerlo con autorización para ese modo y
alcance) además: revisar(obj), diario(), deshacer(n=None),
VARIATION. En ambos modos: salida(tipo=None, n=50, buscar=None) lee la Output Window de PF.
Cada resultado trae output_window (líneas nuevas, errores y avisos del comando); el cliente imprime errores y
avisos, y todo con --ow. Ver references/bridge.md.
Código de salida: 0 ok, 1 error del comando, 2 puente no disponible / sin respuesta.
"""
import argparse
import json
import os
import sys
import time
import uuid

BRIDGE_DIR = os.environ.get("PF_BRIDGE_DIR") or os.path.join(os.path.expanduser("~"), "pf_bridge")


def leer_estado():
    ruta = os.path.join(BRIDGE_DIR, "status.json")
    if not os.path.exists(ruta):
        return None
    try:
        return json.load(open(ruta, encoding="utf-8"))
    except ValueError:
        time.sleep(0.2)
        return json.load(open(ruta, encoding="utf-8"))


def puente_vivo():
    """Vivo si hay latido reciente, o si está ejecutando un comando (durante un comando largo el latido no avanza; el
    comando sigue en inbox hasta terminar). Antes, un flujo largo se leía como 'detenido' (07-10-2026)."""
    e = leer_estado()
    if not (e and e.get("vivo")):
        return False, e
    if time.time() - e.get("latido_epoch", 0) < 20:
        return True, e
    c = e.get("en_curso") or {}
    return bool(c.get("id") and os.path.exists(os.path.join(BRIDGE_DIR, "inbox", c["id"] + ".py"))), e


def enviar(fuente, timeout):
    vivo, e = puente_vivo()
    if not vivo:
        print("El puente no está corriendo (sin latido reciente). Pide al usuario ejecutar pf_bridge.py en PowerFactory.")
        if e:
            print("Último estado:", json.dumps(e, ensure_ascii=False))
        sys.exit(2)
    cid = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    inbox = os.path.join(BRIDGE_DIR, "inbox")
    tmp = os.path.join(inbox, cid + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(fuente)
    os.replace(tmp, os.path.join(inbox, cid + ".py"))
    salida = os.path.join(BRIDGE_DIR, "outbox", cid + ".json")
    t0 = time.time()
    while not os.path.exists(salida):
        if time.time() - t0 > timeout:
            print("Sin respuesta en %d s (id %s). El comando puede seguir corriendo en PF." % (timeout, cid))
            sys.exit(2)
        time.sleep(0.3)
    time.sleep(0.05)
    return json.load(open(salida, encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", nargs="?", choices=["estado", "ejecutar", "detener"], default="ejecutar")
    ap.add_argument("archivo", nargs="?")
    ap.add_argument("-c", "--codigo")
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--json")
    ap.add_argument("--ow", action="store_true", help="mostrar todas las líneas nuevas de la Output Window")
    a = ap.parse_args()
    if a.accion == "estado":
        vivo, e = puente_vivo()
        c = (e or {}).get("en_curso") or {}
        txt = ("ocupado (comando %s desde %s)" % (c.get("id"), c.get("desde")) if vivo and c and time.time() - e.get("latido_epoch", 0) >= 20
               else ("vivo" if vivo else "detenido"))
        print(txt, json.dumps(e, ensure_ascii=False, indent=1) if e else "(sin status.json)")
        sys.exit(0 if vivo else 2)
    if a.accion == "detener":
        open(os.path.join(BRIDGE_DIR, "inbox", "STOP"), "w").close()
        print("STOP enviado")
        return
    fuente = a.codigo if a.codigo is not None else open(a.archivo, encoding="utf-8").read()
    r = enviar(fuente, a.timeout)
    if r.get("salida"):
        print(r["salida"], end="" if r["salida"].endswith("\n") else "\n")
    if r.get("resultado"):
        print("resultado:", json.dumps(r["resultado"], ensure_ascii=False, indent=1)[:20000])
    if r.get("error"):
        print("ERROR:", r["error"])
        if r.get("traceback"):
            print(r["traceback"])
    ow = r.get("output_window") or {}
    if ow.get("disponible"):
        for clave, rot in (("errores", "PF ERROR"), ("avisos", "PF WARN")):
            if ow.get("n_" + clave):
                print("%s (%d nuevos):" % (rot, ow["n_" + clave]))
                for l in ow[clave][:40]:
                    print("  " + l)
                if ow["n_" + clave] > 40:
                    print("  ... (%d más; --ow o --json para verlos)" % (ow["n_" + clave] - 40))
        if a.ow and ow.get("n_lineas"):
            print("PF OUTPUT (%d líneas nuevas):" % ow["n_lineas"])
            for l in ow["lineas"]:
                print("  " + l)
    elif ow:
        print("PF OUTPUT no disponible:", ow.get("nota"))
    print("[%s | %s | %.2f s | %s]" % (r["id"], "ok" if r["ok"] else "error", r.get("duracion_s", 0), r.get("modo")))
    if a.json:
        json.dump(r, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
