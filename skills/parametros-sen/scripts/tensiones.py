# Tensiones de servicio y rangos (normal / alerta / emergencia) del Estudio de Tensiones de Servicio (ETS) del CEN,
# a partir del HTML del usuario (subestaciones_tensiones.html, con los JSON embebidos "rangos-data" y "kmz-data").
#
#   python tensiones.py "Ancoa:500" "Tiquel:500:CAUQUENES" "Hualqui:220:HUALQUI" "Parral:154" "Cauquenes:66" --csv t.csv
#
# Criterio (el mismo del HTML):
#   - barra listada en el ETS para ese nivel            -> valor directo ("ETS")
#   - 220/500 kV no listada (p. ej. S/E futura)         -> barra ETS más cercana del mismo nivel, ubicando la S/E por el
#                                                          KMZ; si no está en el KMZ, por una S/E existente vecina (proxy)
#   - < 200 kV                                          -> categoría del nivel (154 kV: 156; 66 kV: 67), toda la zona
#   - tope245 = "Sí" y emergencia máx. = 245            -> se marca 245(*) (acotado al límite de 245 kV)
import argparse, csv, json, math, re, sys, unicodedata

HTML = r"C:\Users\vicen\Documents\vsEErv\subestaciones_tensiones.html"


def n(x):
    return unicodedata.normalize("NFD", x or "").encode("ascii", "ignore").decode().upper().strip()


def hav(a, b):
    p1, p2, dl = math.radians(a["lat"]), math.radians(b["lat"]), math.radians(b["lon"] - a["lon"])
    return 6371 * 2 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("barras", nargs="+", help='"Nombre:kV" o "Nombre:kV:PROXY_KMZ"')
    ap.add_argument("--html", default=HTML)
    ap.add_argument("--json")
    ap.add_argument("--csv")
    a = ap.parse_args()
    s = open(a.html, encoding="utf-8-sig").read()
    K = json.loads(re.search(r'id="kmz-data"[^>]*>(.*?)</script>', s, re.S).group(1))
    R = json.loads(re.search(r'id="rangos-data"[^>]*>(.*?)</script>', s, re.S).group(1))

    def kmz(nombre):
        c = [x for x in K if re.search(r"_S/E %s$" % re.escape(n(nombre)), n(x["nombre"]))]
        return c[0] if c else None

    filas = []
    for b in a.barras:
        nombre, kv, *px = b.split(":")
        kv, proxy = int(kv), (px[0] if px else None)
        if kv < 200:
            x = next(r for r in R if r["nivel"] == "<200 kV" and r["nominal"] == kv and "Norte" not in r["nombre"])
            crit, ref, dist = "Categoría ETS", x["nombre"], None
        else:
            nivel = "%d kV" % kv
            x = next((r for r in R if n(r["nombre"]) == n(nombre) and r["nivel"] == nivel), None)
            crit, ref, dist = "ETS", x["nombre"] if x else "", None
            if not x:
                st = kmz(proxy or nombre)
                if not st:
                    print("!! %s: no está en el KMZ; indicar una S/E vecina como proxy (Nombre:kV:PROXY)" % nombre)
                    continue
                dist, x = min(((hav(st, r), r) for r in R if r["nivel"] == nivel and r.get("lat") is not None), key=lambda t: t[0])
                crit, ref = "Barra cercana", x["nombre"]
        tope = x.get("tope245") in ("Sí", "Si", "SI") and x["emergenciaMax"] == 245
        filas.append(dict(barra=nombre, kv=kv, vs=x["vservicio"], normal_min=x["normalMin"], normal_max=x["normalMax"],
                          alerta_min=x["alertaMin"], alerta_max=x["alertaMax"], emergencia_min=x["emergenciaMin"],
                          emergencia_max="245(*)" if tope else x["emergenciaMax"], criterio=crit, referencia=ref,
                          ubicacion=proxy or "", distancia_km=round(dist, 1) if dist is not None else ""))
    for f in filas:
        print("%-16s %3d kV | Vs %6s | N %s-%s | A %s-%s | E %s-%s | %s %s %s" % (
            f["barra"], f["kv"], f["vs"], f["normal_min"], f["normal_max"], f["alerta_min"], f["alerta_max"], f["emergencia_min"],
            f["emergencia_max"], f["criterio"], f["referencia"], ("(%s km, ubic. %s)" % (f["distancia_km"], f["ubicacion"] or f["barra"]))
            if f["distancia_km"] != "" else ""))
    if a.json:
        json.dump(filas, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";")
            w.writeheader()
            w.writerows(filas)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
