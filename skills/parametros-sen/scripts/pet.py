# Capacidad de obras futuras en los PDF del Plan de Expansión (ITD, decretos, anexos de ingeniería conceptual).
#
#   python pet.py "COIQUEN" "LAS DELICIAS" --carpeta "<...>/00_Plan de Obras/PET"
#   python pet.py "TIQUEL" --carpeta ... --todo        # todas las menciones, no sólo frases con MVA
#
# Busca frases "al menos X MVA ... 35 °C" con los dos extremos en el contexto previo. El texto de cada PDF se guarda en
# caché (por ruta y fecha de modificación). Sólo lee: nunca escribe en la carpeta (suele ser OneDrive).
import argparse, glob, hashlib, json, os, re, sys, unicodedata

CACHE = os.path.join(os.environ.get("PARAMETROS_SEN_CACHE") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                                                                             "parametros-sen", "cache"), "pdf_texto")
OBRA = re.compile(r"\d+\.\d+\.\d+ (NUEVA|NUEVO|AMPLIACION|AUMENTO|SECCIONAMIENTO|TENDIDO|CAMBIO|REEMPLAZO|NORMALIZACION|EXTENSION|REFUERZO)")
FRASE = re.compile(r"(AL MENOS|A LO MENOS|MINIMA DE)[^.]{0,60}?(\d[\d\.,]*)\s*MVA([^.]{0,80}?(\d{2})\s*°?\s*C(\s*(CON|SIN) SOL)?)?")


def norm(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper().replace("–", "-"))


def paginas(ruta):
    import pymupdf
    h = hashlib.md5(("%s|%s" % (ruta, os.path.getmtime(ruta))).encode()).hexdigest()
    c = os.path.join(CACHE, h + ".json")
    if os.path.exists(c):
        return json.load(open(c, encoding="utf-8"))
    pags = [norm(p.get_text()) for p in pymupdf.open(ruta)]
    os.makedirs(CACHE, exist_ok=True)
    json.dump(pags, open(c, "w", encoding="utf-8"))
    return pags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nombres", nargs="+", help="uno o dos extremos (S/E)")
    ap.add_argument("--carpeta", required=True)
    ap.add_argument("--contexto", type=int, default=6000)
    ap.add_argument("--todo", action="store_true")
    a = ap.parse_args()
    N = [norm(x) for x in a.nombres]
    for f in sorted(glob.glob(os.path.join(a.carpeta, "**", "*.pdf"), recursive=True)):
        try:
            pags = paginas(f)
        except Exception as e:
            print("!! no se pudo leer", f, e)
            continue
        if a.todo:
            for i, tx in enumerate(pags):
                for m in re.finditer(re.escape(N[0]), tx):
                    ctx = tx[max(0, m.start() - 150):m.end() + 250]
                    if all(n in ctx for n in N):
                        print("%s p%d | %s" % (os.path.relpath(f, a.carpeta), i + 1, ctx))
            continue
        # la frase de capacidad suele estar lejos del título de la obra: se asocia a la última obra titulada antes de ella
        todo, ini = "", []
        for tx in pags:
            ini.append(len(todo))
            todo += tx + " "
        for m in FRASE.finditer(todo):
            ventana = todo[max(0, m.start() - a.contexto):m.end()]
            obras = list(OBRA.finditer(ventana))
            titulo = ventana[obras[-1].start():obras[-1].start() + 160] if obras else ""
            if all(n in (titulo or ventana) for n in N):
                pag = max(i for i, x in enumerate(ini) if x <= m.start()) + 1
                print("%s p%d | %s MVA %s°C %s | obra: %s | frase: %s" % (os.path.relpath(f, a.carpeta), pag, m.group(2), m.group(4) or "?",
                                                                     m.group(6) or "", titulo[:120], re.sub(r"\s+", " ", m.group(0))[:160]))

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
