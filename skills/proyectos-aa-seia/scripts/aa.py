#!/usr/bin/env python3
"""Consulta la base publica de Solicitudes de Acceso Abierto del CEN.

Uso:
    python aa.py --nup 3665
    python aa.py --proyecto "andino" --full
    python aa.py --se "buli"
    python aa.py --tecnologia "almacenamiento" --csv bess.csv
    python aa.py --nup 3665 --full

El endpoint es publico (sin token) y devuelve TODAS las solicitudes en un solo
JSON (~4 MB); el parametro `anio` no filtra nada, se ignora. Se cachea un dia.

Campos que importan:
    potencia_nominal  MW que muestra la ficha de AA (la que se cita como "la ficha dice")
    potencia_nsi      potencia de inyeccion declarada (si viene)
    potencia_nsr      potencia de retiro declarada (si viene)
    potencia_cga      capacidad de generacion autorizada
    potencia_caa      capacidad de almacenamiento autorizada
    energia_caa       energia del almacenamiento [MWh]
    horas_almacenamiento_caa
    tipo_proyecto_nombre   Generacion / Consumo / SAE / ...
    tipo_tecnologia_nombre Eolico / Solar / Hibrido / Almacenamiento / ...
    pano_conexion, nombre_se, nivel_tension, seccion_barra_conexion
    estado_solicitud, fecha_informe (fecha del IAC), fecha_estimada_conexion

Ojo: la ficha de AA es un registro administrativo con fecha. No se actualiza
sola. Un proyecto puede tener 150 MW en AA y 115,2 MW en la RCA; las dos cosas
son ciertas y hay que decirlo asi.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = ("https://pkb3ax2pkg.execute-api.us-east-2.amazonaws.com/prod/data/public"
       "?tipo=6&anio=2026&tipo_solicitud_id=0&solicitud_id=null")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CACHE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                     "proyectos-aa-seia", "aa.json")
MAX_AGE_H = 24

COLS = ["nup", "proyecto", "razon_social", "estado_solicitud", "tipo_solicitud",
        "tipo_proyecto_nombre", "tipo_tecnologia_nombre", "potencia_nominal",
        "potencia_nsi", "potencia_nsr", "potencia_cga", "potencia_caa",
        "energia_caa", "horas_almacenamiento_caa", "nombre_se", "pano_conexion",
        "nivel_tension", "seccion_barra_conexion", "fecha_estimada_conexion",
        "fecha_informe", "create_date"]


def load(refresh=False):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    fresh = os.path.exists(CACHE) and (time.time() - os.path.getmtime(CACHE)) < MAX_AGE_H * 3600
    if fresh and not refresh:
        return json.load(open(CACHE, encoding="utf-8"))
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    json.dump(data, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return data


def matches(d, a):
    blob = json.dumps(d, ensure_ascii=False).lower()
    if a.nup and str(d.get("nup")) != str(a.nup):
        return False
    if a.proyecto and a.proyecto.lower() not in str(d.get("proyecto", "")).lower():
        return False
    if a.se and a.se.lower() not in str(d.get("nombre_se", "")).lower():
        return False
    if a.tecnologia and a.tecnologia.lower() not in str(d.get("tipo_tecnologia_nombre", "")).lower():
        return False
    if a.estado and a.estado.lower() not in str(d.get("estado_solicitud", "")).lower():
        return False
    return True


def line(d):
    parts = []
    for k in COLS:
        v = d.get(k)
        if v in (None, "", 0) and k not in ("potencia_nominal",):
            continue
        parts.append(f"{k}={v}")
    return " | ".join(parts)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nup")
    ap.add_argument("--proyecto")
    ap.add_argument("--se")
    ap.add_argument("--tecnologia")
    ap.add_argument("--estado")
    ap.add_argument("--full", action="store_true", help="todos los campos, uno por linea")
    ap.add_argument("--csv")
    ap.add_argument("--refrescar", action="store_true")
    a = ap.parse_args()

    data = load(a.refrescar)
    hits = [d for d in data if matches(d, a)]
    print(f"# {len(hits)} de {len(data)} solicitudes", file=sys.stderr)
    for d in hits:
        if a.full:
            print("=" * 70)
            for k in sorted(d):
                if d[k] not in (None, "", [], {}):
                    print(f"{k}: {d[k]}")
        else:
            print(line(d))
    if a.csv and hits:
        keys = sorted({k for d in hits for k in d})
        with open(a.csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(hits)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
