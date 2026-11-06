# PGP del Coordinador (pgp.coordinador.cl, sin sesión): proyectos por NUP o texto, capacidad declarada, descarga.
#
#   python pgp.py buscar "Hualqui Chiguayante"        # o un NUP: python pgp.py buscar 1087
#   python pgp.py buscar 1087 --json nup_1087.json
#   python pgp.py descargar <fileId> salida.pdf        # PEDIR OK AL USUARIO ANTES (descarga de archivo)
#
# El fileId no sale de la API de búsqueda: está en la página del proyecto (https://pgp.coordinador.cl/irequests/<id>),
# en el atributo data-for="history-<fileId>" (o data-for="<fileId>") del enlace de cada documento.
import argparse, json, re, sys, urllib.parse, urllib.request

BASE = "https://pgp.coordinador.cl"
UA = {"User-Agent": "Mozilla/5.0"}
# "al menos 90 MVA por circuito, a 25 °C con sol" | "capacidad de 46 MVA" ...
CAP = re.compile(r"((?:al|a lo) menos|m[ií]nim[ao] de|capacidad (?:de transmisi[oó]n )?(?:de )?)[^.;]{0,40}?(\d[\d.,]*)\s*MVA"
                 r"([^.;]{0,80}?(\d{2})\s*°\s*C(?:\s*(con|sin) sol)?)?", re.I)


def get(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())


def buscar(q, paginas=3):
    out = []
    for page in range(1, paginas + 1):
        d = get("%s/api/request/irs?page=%d&project=%s&company_name=&type=all" % (BASE, page, urllib.parse.quote(str(q))))
        out += d.get("items", [])
        if page >= d.get("total_pages", 1):
            break
    return out


def capacidades(texto):
    return [dict(mva=float(m.group(2).replace(".", "").replace(",", ".")), temp=m.group(4), sol=m.group(5),
                 frase=re.sub(r"\s+", " ", m.group(0)).strip()) for m in CAP.finditer(texto or "")]


def resumen(it):
    ex = it.get("extra_data") or {}
    return dict(nup=it.get("correlativo"), id=it.get("id"), nombre=it.get("name"), estado=it.get("stage"),
                fecha_estimada=it.get("service_estimate_date"), tension=ex.get("tension_level"), capacidad_declarada=ex.get("capacity"),
                punto_conexion=ex.get("connection_point"), capacidades_descripcion=capacidades(it.get("description")),
                descripcion=re.sub(r"\s+", " ", it.get("description") or ""), url="%s/irequests/%s" % (BASE, it.get("id")))


def descargar(file_id, salida):
    link = get("%s/api/task/get_file_link/%s" % (BASE, file_id))
    lid = link.get("link_id") or link.get("link") or link
    data = urllib.request.urlopen(urllib.request.Request("%s/api/task/download/%s" % (BASE, lid), headers=UA), timeout=300).read()
    open(salida, "wb").write(data)
    return len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["buscar", "descargar"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.accion == "buscar":
        q = " ".join(a.args)
        res = [resumen(it) for it in buscar(q)]
        if q.isdigit():                                  # la búsqueda por NUP también trae coincidencias parciales
            res = [r for r in res if str(r["nup"]) == q] or res
        for r in res:
            print("NUP %s | %s | %s kV | cap. declarada %s MVA | %s" % (r["nup"], r["nombre"][:90], r["tension"], r["capacidad_declarada"], r["url"]))
            for c in r["capacidades_descripcion"]:
                print("    -> %s MVA %s %s | «%s»" % (c["mva"], (c["temp"] or "") and c["temp"] + " °C", c["sol"] or "", c["frase"][:120]))
            print("    " + r["descripcion"][:300])
        if a.json:
            json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    else:
        print(descargar(a.args[0], a.args[1]), "bytes ->", a.args[1])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
