#!/usr/bin/env python3
"""Buscador del SEIA: proyectos y consultas de pertinencia.

Uso:
    python seia.py buscar "Andino Suiza"
    python seia.py pertinencia "Andino"
    python seia.py pertinencia "BESS" --csv pert.csv

Devuelve el expediente (id, nombre, titular, region, comuna, estado, fecha) y
arma la URL https://seia.sea.gob.cl/expediente/expediente.php?id_expediente=<id>.

La busqueda por nombre es por coincidencia parcial. El buscador del SEA funciona
mejor sin tildes ni parentesis: se limpian antes de enviar (ver clean()).

La consulta de pertinencia usa el endpoint publico del SEA (sin ClaveUnica) y
filtra en el servidor. Es la via para responder "tiene RCA propia o entro por
pertinencia": si no aparece, se dice "no hay pertinencia registrada al <fecha>",
nunca "no existe".
"""
import argparse
import csv
import json
import sys
import unicodedata
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def _dec(raw):
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _post(url, data, latin1=False):
    body = urllib.parse.urlencode(data).encode()
    ctype = ("application/x-www-form-urlencoded; charset=ISO-8859-1" if latin1
             else "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest", "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(_dec(r.read()))


def clean(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join("".join(c if c.isalnum() else " " for c in text).split())


def buscar(nombre):
    return _post("https://seia.sea.gob.cl/busqueda/buscarProyectoResumenAction.php", {
        "nombre": clean(nombre), "titular": "", "folio": "",
        "selectRegion": "", "selectComuna": "", "tipoPresentacion": "",
        "projectStatus": "", "PresentacionMin": "", "PresentacionMax": "",
        "CalificaMin": "", "CalificaMax": "", "sectores_economicos": "",
        "razoningreso": "", "id_tipoexpediente": "",
        "offset": 1, "limit": 50,
    }).get("data", [])


def pertinencia(nombre):
    return _post("https://seia.sea.gob.cl/pertinencia/resumenPertinenciaBuscar.php", {
        "p_id_pertinencia": "", "p_nombre_pertinencia": clean(nombre),
        "p_tipo_proyecto": "", "p_estado_pertinencia": "", "p_proponent": "",
        "p_fecha_presentacion_from": "", "p_fecha_presentacion_to": "",
        "p_fecha_respuesta_from": "", "p_fecha_respuesta_to": "",
        "p_region": "", "p_comuna": "",
    }, latin1=True).get("data", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["buscar", "pertinencia"])
    ap.add_argument("nombre")
    ap.add_argument("--csv", dest="csv_out")
    a = ap.parse_args()

    if a.modo == "buscar":
        rows = buscar(a.nombre)
        print(f"# termino enviado: {clean(a.nombre)} | {len(rows)} resultados", file=sys.stderr)
        for r in rows:
            print(f"{r['EXPEDIENTE_ID']} | {r['EXPEDIENTE_NOMBRE']} | {r['TITULAR']} | "
                  f"{r['WORKFLOW_DESCRIPCION']} | {r['FECHA_PRESENTACION_FORMAT']} | "
                  f"{r['ESTADO_PROYECTO']} | {r['EXPEDIENTE_URL_PPAL']}")
    else:
        rows = pertinencia(a.nombre)
        print(f"# termino enviado: {clean(a.nombre)} | {len(rows)} resultados", file=sys.stderr)
        for r in rows:
            print(f"{r['ID_PERTINENCIA']} | {r['PERTINENCIA_NOMBRE']} | {r['PROPONENTE']} | "
                  f"{r['REGION_NOMBRE']} | {r['PERTINENCIA_ESTADO']} | "
                  f"{r['FECHA_PRESENTACION_FORMAT']} | {r['FECHA_RESPUESTA_FORMAT']}")
    if a.csv_out and rows:
        keys = sorted({k for r in rows for k in r})
        with open(a.csv_out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        pass
