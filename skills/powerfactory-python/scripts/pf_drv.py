"""Driver de plantillas para el puente PF (pf_send.py): rellena marcadores __X__, ejecuta y filtra la salida.

Uso (desde la shell de Claude, no dentro de PF):
    import sys; sys.path.insert(0, r"C:\\Users\\vicen\\.claude\\skills\\powerfactory-python\\scripts")
    import pf_drv
    pf_drv.run("plantilla.py", filtro=("S1", "ERROR", "Trace", "  File", "Error"), ESC="E01", CASO="02_25 CS")

- La plantilla se busca en la carpeta actual (o ruta absoluta); el comando rellenado se escribe como drv_x.py al lado.
- Reintenta hasta 4 veces si PF invalidó la conexión («already deleted»): el comando debe ser idempotente.
- Cada script imprime sus líneas útiles con un prefijo corto; `filtro` deja sólo esas (y los errores).
- Devuelve la salida completa (texto) por si se quiere procesar.
"""
import os
import subprocess
import sys
import time

SEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pf_send.py")


def run(plantilla, filtro=("ERROR", "Trace", "  File", "Error"), timeout=3000, carpeta=None, **marcadores):
    carpeta = carpeta or os.getcwd()
    ruta = plantilla if os.path.isabs(plantilla) else os.path.join(carpeta, plantilla)
    s = open(ruta, encoding="utf-8").read()
    for k, v in marcadores.items():
        s = s.replace("__%s__" % k, str(v))
    destino = os.path.join(carpeta, "drv_x.py")
    open(destino, "w", encoding="utf-8").write(s)
    out = ""
    for _ in range(4):
        out = subprocess.run([sys.executable, SEND, "ejecutar", destino, "--timeout", str(timeout)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        if "already deleted" in out:
            time.sleep(8)
            continue
        break
    for linea in out.splitlines():
        if not filtro or linea.startswith(tuple(filtro)):
            print(linea[:600])
    sys.stdout.flush()
    return out
