# Infotécnica (API pública del CEN): líneas, paños, equipos de paño y transformadores.
#
#   python it.py buscar "concepcion san vicente" [--en tramos|panos|trafos]
#   python it.py linea "CONCEPCION - SAN VICENTE" [--id 325 572] [--json x.json] [--csv x.csv]
#   python it.py pano "CONCEPCION" "B12"
#   python it.py trafo "ANCOA" [--csv x.csv]
#   (cualquiera) --refrescar   fuerza a bajar de nuevo listas y fichas
#
# Reglas (ver SKILL.md): los valores "Rechazado" se usan igual y se marcan en rojo; conductor = sección más limitante,
# límites térmicos con respaldo en la ficha general; equipos = el menor del paño; todo en kA.
import argparse, csv, glob, json, os, re, sys, time, unicodedata, urllib.request

API = "https://api-infotecnica.coordinador.cl/v1"
UA = {"User-Agent": "SuitePMGD-skill"}
CACHE = os.environ.get("PARAMETROS_SEN_CACHE") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                                                "parametros-sen", "cache")
REFRESCAR = False
COLOR = {"Validado": "C6EFCE", "Sin Revisar": "FFEB9C", "Rechazado": "FFC7CE", None: "D9D9D9", "": "D9D9D9"}
RANGO = {"Validado": 0, "Sin Revisar": 1, "Rechazado": 2}

# conceptos exactos (con ^...$: "Factor de sobrecarga permanente" y "admisible de corta duración" NO deben calzar)
EQUIPOS = {"int": ("interruptores", r"^[\d\.]+\s+Corriente nominal\s*$"),
           "desc": ("desconectadores", r"^[\d\.]+\s+Corriente nominal\s*$"),
           "to": ("trampas-ondas", r"^[\d\.]+\s+Corriente nominal\s*$"),
           "ttcc": ("transformadores-corrientes", r"^[\d\.]+\s+Sobrecarga permanente\s*$")}
ETIQ = {"int": "Int", "desc": "Desc", "to": "TO", "ttcc": "TTCC"}
LT = {"15": r"^Sin Sol 15\s*°C\.?$", "25": r"^Con Sol 25\s*°C\.?$", "35": r"^Con Sol 35\s*°C\.?$"}
GEN = {"15": r"^1\.9 Límite térmico permanente en invierno con sol 15", "25": r"^1\.9 Límite térmico permanente en verano con sol 25"}
GEN_TTCC = {"ini": r"^1\.26 .*extremo inicial", "fin": r"^1\.26 .*extremo final"}


# ----------------------------------------------------------------------------------------------------------- acceso
def get(url, nombre=None, dias=7):
    ruta = os.path.join(CACHE, nombre) if nombre else None
    if ruta and os.path.exists(ruta) and not REFRESCAR and time.time() - os.path.getmtime(ruta) < dias * 86400:
        return json.load(open(ruta, encoding="utf-8"))
    for intento in range(4):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
            break
        except Exception:
            if intento == 3:
                raise
            time.sleep(2 * (intento + 1))
    time.sleep(0.1)
    if ruta:
        os.makedirs(CACHE, exist_ok=True)
        json.dump(d, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    return d


def lista(slug, dias=14):
    """Inventario completo de un tipo de instalación (paginado de a 1000)."""
    ruta = os.path.join(CACHE, "lista_%s.json" % slug.strip("/").replace("/", "_"))
    if os.path.exists(ruta) and not REFRESCAR and time.time() - os.path.getmtime(ruta) < dias * 86400:
        return json.load(open(ruta, encoding="utf-8"))
    out, page = [], 1
    while True:
        d = get("%s/%s/?page=%d&page_size=1000&ordering=id" % (API, slug, page))
        if isinstance(d, list):
            out = d
            break
        out += d["results"]
        if not d.get("next"):
            break
        page += 1
    os.makedirs(CACHE, exist_ok=True)
    json.dump(out, open(ruta, "w", encoding="utf-8"), ensure_ascii=False)
    return out


def ficha(slug, id_, tipo="general"):
    """Ficha técnica: tipo = general | limites-termicos (secciones-tramos)."""
    return get("%s/%s/%d/fichas-tecnicas/%s/" % (API, slug, id_, tipo), "ficha_%s_%s_%d.json" % (slug.replace("/", "_"), tipo, id_))


def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9()]+", " ", s).strip()     # se conservan los paréntesis: COCHARCAS (CGE) != (FFCC)


def num(v):
    m = re.search(r"\d+(?:[.,]\d+)?", str(v or "").replace("[", "").replace("]", ""))
    return float(m.group(0).replace(",", ".")) if m else None


def conceptos(f, patron):
    """[(valor, unidad, estado, concepto, texto)] de una ficha cuyo concepto calza con el patrón (incluye rechazados)."""
    out = []
    for v in f.values():
        if isinstance(v, dict) and re.search(patron, v.get("nombre_concepto") or "", re.I):
            out.append((num(v.get("valor_texto")), v.get("unidad_nemo"), v.get("estado_certificacion_nombre"),
                        v.get("nombre_concepto"), v.get("valor_texto")))
    return out


def a_kA(x, unidad):
    return x / 1000 if x is not None and (unidad == "[A]" or x > 50) else x


# ----------------------------------------------------------------------------------------------------------- paños
_IDX = {}


def indices():
    if not _IDX:
        P = lista("panos")
        _IDX["panos"] = P
        _IDX["por_nombre"] = {norm(p["nombre"]): p for p in P}
        _IDX["eq"] = {k: lista(slug) for k, (slug, _) in EQUIPOS.items()}
    return _IDX


def pano_de_extremo(desc):
    """Paño de IT a partir de extremoN_descripcion. Devuelve (paño | None, tipo) con tipo = paño | tap | punto | ?"""
    desc = desc or ""
    if re.match(r"^\s*Tap", desc):
        return None, "tap"
    if re.match(r"^\s*Punto", desc):
        return None, "punto"
    ix = indices()
    mm = re.search(r"((?:PA )?S/E [^/]+?)\s*(?:/\s*(.*))?$", desc)   # "Paño : PA S/E X B12/PA111T0058..." | "Paño: S/E X J5"
    if not mm:
        return None, "?"
    nombre, cod = mm.group(1), mm.group(2) or ""
    pegado = re.search(r"\s(PA\d+)$", nombre)              # "PA S/E MAULE PA012": código interno sin "/"
    if pegado and not cod:
        nombre, cod = nombre[:pegado.start()], pegado.group(1)
    m = re.match(r"(PA\d+)", cod.strip())
    sub = norm(re.sub(r"^(PA )?S/E ", "", nombre.strip()))    # "CONCEPCION A3" o "ANDALIEN" (sin código de paño)
    if m:                                               # código interno PAxxx: el más preciso
        def nsub(p):
            return re.sub(r"^S E ", "", norm(p["subestacion_nombre"]))
        cand = [p for p in ix["panos"] if p["codigo"] == m.group(1) and (sub == nsub(p) or sub.startswith(nsub(p) + " "))]
        if cand:
            return max(cand, key=lambda p: len(nsub(p))), "paño"
    base = re.sub(r"^PA ", "", nombre.strip())              # IT nombra paños con y sin "PA " (S/E PARRAL B2)
    for n in (norm(nombre), norm("PA " + base), norm(base)):
        if n in ix["por_nombre"]:
            return ix["por_nombre"][n], "paño"
    return None, "?"


def equipos_de_pano(p):
    """{tipo: [equipo]} del paño: por pano_nombre o por (subestación + código del paño al final del nombre del equipo).
    No usar id_conexion: no siempre apunta a un paño y trae equipos de otros paños."""
    ix = indices()
    sub = re.sub(r"^S E ", "", norm(p["subestacion_nombre"]))
    resto = re.sub(r"^(PA )?S E ", "", norm(p["nombre"]))
    cod = resto[len(sub):].strip() if resto.startswith(sub) else resto.split(" ")[-1]
    # sin código propio (p. ej. "PA S/E ANDALIEN"): sólo por pano_nombre, si no tomaría equipos de toda la S/E
    pat = re.compile(r"(^| )%s( \d+)?$" % re.escape(cod)) if cod else None
    out = {}
    for k, L in ix["eq"].items():
        out[k] = [e for e in L if norm(e.get("pano_nombre")) == norm(p["nombre"]) or
                  (pat and e.get("id_subestacion") == p["id_subestacion"] and pat.search(norm(e["nombre"])))]
    return out


BUSHING = re.compile(r"\bT B\b|BUSHING")                  # "TC S/E PASO HONDO BT1 t.b.": TC del trafo, no del paño


def valor_equipos(k, eqs):
    """Menor valor del paño para un tipo de equipo, con su estado. Rechazados incluidos (se marcan en rojo).
    Los TC de bushing del transformador ("t.b.") se excluyen: no limitan la línea."""
    slug, patron = EQUIPOS[k]
    vals, detalle = [], []
    if k == "ttcc":
        eqs = [e for e in eqs if not BUSHING.search(norm(e["nombre"]))] or eqs
    for e in eqs:
        for x, u, est, conc, txt in conceptos(ficha(slug, e["id"]), patron):
            detalle.append(dict(equipo=e["nombre"], id=e["id"], valor=txt, unidad=u, estado=est))
            if x is not None:
                vals.append((a_kA(x, u), RANGO.get(est, 3), est))
    if not eqs:
        return dict(valor="N/A" if k == "to" else "S/I", estado=None, color=None if k == "to" else COLOR[None], n=0, detalle=[])
    if not vals:
        return dict(valor="S/I", estado=None, color=COLOR[None], n=len(eqs), detalle=detalle)
    x, _, est = min(vals, key=lambda t: (t[0], t[1]))    # el menor; a igual valor, el mejor certificado
    return dict(valor=round(x, 4), estado=est, color=COLOR[est], n=len(eqs), detalle=detalle)


def info_pano(p):
    eqs = equipos_de_pano(p)
    return {k: valor_equipos(k, eqs[k]) for k in EQUIPOS}


# ----------------------------------------------------------------------------------------------------------- líneas
def conductor_seccion(s):
    """Por condición: límites térmicos; si está rechazado o vacío, ficha general (15/25 °C con sol); si ambos están
    rechazados, el de límites térmicos (se usa igual, marcado en rojo)."""
    lt, ge = ficha("secciones-tramos", s["id"], "limites-termicos"), ficha("secciones-tramos", s["id"], "general")
    out = {}
    for c in ("15", "25", "35"):
        cand = [(x, est, "límites térmicos") for x, u, est, *_ in conceptos(lt, LT[c]) if x is not None]
        if c in GEN:
            cand += [(x, est, "ficha general (%s °C con sol)" % c) for x, u, est, *_ in conceptos(ge, GEN[c]) if x is not None]
        if cand:
            x, est, fuente = min(cand, key=lambda t: t[1] == "Rechazado")   # estable: primero límites térmicos
            out[c] = dict(valor=x, estado=est, color=COLOR[est], fuente=fuente)
        else:
            out[c] = dict(valor="S/I", estado=None, color=COLOR[None], fuente="")
    out["ttcc_ficha_linea"] = {k: [(t[4], t[2]) for t in conceptos(ge, p)] for k, p in GEN_TTCC.items()}
    return out


def linea(tramo):
    secs = [s for s in lista("secciones-tramos") if s["id_tramo"] == tramo["id"]]
    det = [dict(id=s["id"], nombre=s["nombre"], **conductor_seccion(s)) for s in secs]
    cond = {}
    for c in ("15", "25", "35"):
        v = [d[c] for d in det if isinstance(d[c]["valor"], float)]
        cond[c] = min(v, key=lambda d: d["valor"]) if v else dict(valor="S/I", estado=None, color=COLOR[None], fuente="")
    extremos = []
    for desc in (tramo["extremo1_descripcion"], tramo["extremo2_descripcion"]):
        p, tipo = pano_de_extremo(desc)
        e = dict(descripcion=desc, tipo=tipo, pano=p["nombre"] if p else None, id_pano=p["id"] if p else None)
        if p:
            e.update(info_pano(p))
        else:
            na = "N/A" if tipo in ("tap", "punto") else "S/I"
            e.update({k: dict(valor=na, estado=None, color=None if na == "N/A" else COLOR[None], n=0, detalle=[]) for k in EQUIPOS})
        extremos.append(e)
    lim = {}
    for c in ("15", "25", "35"):
        cands = [(cond[c]["valor"], "Conductor")] if isinstance(cond[c]["valor"], float) else []
        cands += [(e[k]["valor"], ETIQ[k]) for e in extremos for k in EQUIPOS if isinstance(e[k]["valor"], float)]
        lim[c] = dict(zip(("valor", "equipo"), min(cands, key=lambda t: t[0]))) if cands else dict(valor="S/I", equipo="")
    return dict(id=tramo["id"], tramo=tramo["nombre"], conductor=cond, secciones=det, extremos=extremos, limite=lim)


def buscar(texto, en="tramos"):
    q = norm(texto).split()
    if en == "trafos":
        L = lista("transformadores-2d") + lista("transformadores-3d")
        return [t for t in L if all(w in norm(t["nombre"]) + " " + norm(t["subestacion_nombre"]) for w in q)]
    L = lista({"tramos": "tramos", "panos": "panos"}[en])
    return [t for t in L if all(w in norm(t["nombre"]) for w in q)]


# ----------------------------------------------------------------------------------------------------------- transformadores
def trafo(t):
    slug = "transformadores-3d" if "id_conexion3" in t else "transformadores-2d"
    f = ficha(slug, t["id"])
    cap = [(x, est, conc) for x, u, est, conc, _ in conceptos(f, r"^[23]\.[1-4] Capacidad") if x is not None and u == "[MVA]"]
    ten = [(conc.split("nominal ")[1].split(" ")[0], txt, est) for _, _, est, conc, txt in conceptos(f, r"^[23]\.7 Tensión nominal")]
    sis = [(conc.split("sistema ")[1].strip(), txt, est) for _, _, est, conc, txt in conceptos(f, r"^Tensión nominal del sistema")]
    mx = max(cap, key=lambda t_: t_[0]) if cap else None
    return dict(id=t["id"], tipo=slug, nombre=t["nombre"], subestacion=t["subestacion_nombre"],
                tension_equipo=" / ".join(v for _, v, _ in ten), tension_sistema=" / ".join(v for _, v, _ in sis),
                mva_max=mx[0] if mx else "S/I", estado_mva=mx[1] if mx else None, concepto_mva=mx[2] if mx else "",
                capacidades=cap)


# ----------------------------------------------------------------------------------------------------------- salida
def fmt(d):
    return ("%.3f" % d["valor"] if isinstance(d.get("valor"), float) else str(d.get("valor"))) + (
        " [%s]" % d["estado"] if d.get("estado") and d["estado"] != "Validado" else "")


def filas_csv(r):
    filas = []
    for i, e in enumerate(r["extremos"]):
        f = dict(id=r["id"], tramo=r["tramo"] if i == 0 else "", extremo=e["descripcion"], pano=e["pano"] or e["tipo"])
        if i == 0:
            for c in ("15", "25", "35"):
                f["cond%s" % c], f["est_cond%s" % c] = r["conductor"][c]["valor"], r["conductor"][c]["estado"] or ""
                f["fuente_cond%s" % c] = r["conductor"][c]["fuente"]
        for k in EQUIPOS:
            f[k], f["est_" + k] = e[k]["valor"], e[k]["estado"] or ""
        f["ccss"] = "S/I"
        if i == 0:
            for c in ("15", "25", "35"):
                f["lim%s" % c], f["eq%s" % c] = r["limite"][c]["valor"], r["limite"][c]["equipo"]
        filas.append(f)
    return filas


def escribir_csv(filas, ruta):
    cols = []
    for f in filas:
        cols += [k for k in f if k not in cols]
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows(filas)


def main():
    global REFRESCAR
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["buscar", "linea", "pano", "trafo"])
    ap.add_argument("texto", nargs="+")
    ap.add_argument("--en", default="tramos", choices=["tramos", "panos", "trafos"])
    ap.add_argument("--id", type=int, nargs="*")
    ap.add_argument("--json")
    ap.add_argument("--csv")
    ap.add_argument("--refrescar", action="store_true")
    a = ap.parse_args()
    REFRESCAR = a.refrescar
    texto = " ".join(a.texto)
    if a.accion == "buscar":
        for t in buscar(texto, a.en):
            print(t["id"], "|", t["nombre"], "|", t.get("extremo1_descripcion") or t.get("subestacion_nombre"), "|",
                  t.get("extremo2_descripcion") or "")
    elif a.accion == "linea":
        tr = [t for t in lista("tramos") if t["id"] in a.id] if a.id else buscar(texto)
        res = [linea(t) for t in tr]
        for r in res:
            print("== %s [tramo %d]" % (r["tramo"], r["id"]))
            for s in r["secciones"]:
                print("   sección %-45s 15SS %-22s 25CS %-22s 35CS %s" % (s["nombre"][:45], fmt(s["15"]), fmt(s["25"]), fmt(s["35"])))
            for e in r["extremos"]:
                print("   extremo %-40s %s" % ((e["pano"] or e["tipo"])[:40], "  ".join("%s %s" % (ETIQ[k], fmt(e[k])) for k in EQUIPOS)))
            print("   límite: " + "  ".join("%s °C %s (%s)" % (c, fmt(r["limite"][c]), r["limite"][c]["equipo"]) for c in ("15", "25", "35")))
        if a.json:
            json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if a.csv:
            escribir_csv([f for r in res for f in filas_csv(r)], a.csv)
    elif a.accion == "pano":
        for p in buscar(texto, "panos"):
            r = info_pano(p)
            print(p["id"], p["nombre"], "|", "  ".join("%s %s (n=%d)" % (ETIQ[k], fmt(r[k]), r[k]["n"]) for k in EQUIPOS))
            for k in EQUIPOS:
                for d in r[k]["detalle"]:
                    print("      %-5s %-40s %s %s [%s]" % (ETIQ[k], d["equipo"][:40], d["valor"], d["unidad"], d["estado"]))
    elif a.accion == "trafo":
        res = [trafo(t) for t in buscar(texto, "trafos")]
        for r in res:
            print(r["id"], r["tipo"][-2:], "|", r["nombre"], "|", r["tension_equipo"], "kV | máx", r["mva_max"], "MVA",
                  "[%s]" % r["estado_mva"] if r["estado_mva"] != "Validado" else "", "|", r["concepto_mva"][:45])
        if a.csv:
            escribir_csv([{k: v for k, v in r.items() if k != "capacidades"} for r in res], a.csv)
        if a.json:
            json.dump(res, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
