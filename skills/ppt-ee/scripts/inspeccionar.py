"""
Inspecciona un deck o lo compara con otra versión. Úsalo SIEMPRE antes de tocar un archivo que el usuario editó:
así sabes qué cambió él (textos, imágenes pegadas, anotaciones, notas del orador) y no lo pisas.

    python inspeccionar.py deck.pptx                 # títulos, formas, posiciones, textos y notas
    python inspeccionar.py deck.pptx --solo 7 10     # sólo esas láminas
    python inspeccionar.py nuevo.pptx --vs viejo.pptx  # qué cambió, emparejando láminas por título
    python inspeccionar.py deck.pptx --imagenes      # imágenes por lámina (hash) para verificar que nada se perdió
"""
import argparse, hashlib, sys
from pptx import Presentation
from pptx.util import Emu
from pptx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8")
E = lambda v: round(Emu(v).inches, 2) if v is not None else None


def titulo(s):
    t = [sh for sh in s.shapes if sh.has_table and abs(Emu(sh.top).inches - 0.5) < 0.06]
    return t[0].table.cell(0, 0).text.replace("\n", " ") if t else "(sin título de casa)"


def formas(s):
    out = []
    for x in s.shapes:
        if x.has_text_frame:
            t = x.text_frame.text
        elif x.has_table:
            t = " / ".join(c.text for r in x.table.rows for c in r.cells)
        else:
            t = ""
        if x.has_chart:
            p = x.chart.plots[0]
            t += " CHART %s %s" % (list(p.categories), [(se.name, list(se.values)) for se in p.series])
        out.append((str(x.shape_type)[:12], x.name, E(x.left), E(x.top), E(x.width), E(x.height), t.replace("\n", " ⏎ ")))
    return out


def notas(s):
    return s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""


def imagenes(s):
    r = []
    for sh in s.shapes:
        for el in sh._element.iter():
            rid = el.get(qn("r:embed"))
            if rid:
                part = s.part.rels[rid].target_part
                r.append((sh.name, hashlib.md5(part.blob).hexdigest()[:8], len(part.blob) // 1024))
    return r


ap = argparse.ArgumentParser()
ap.add_argument("pptx"); ap.add_argument("--vs"); ap.add_argument("--solo", type=int, nargs="*"); ap.add_argument("--imagenes", action="store_true")
a = ap.parse_args()
P = Presentation(a.pptx)

if a.imagenes:
    tot = set()
    for i, s in enumerate(P.slides, 1):
        im = imagenes(s); tot |= {h for _, h, _ in im}
        if im:
            print(i, titulo(s)[:60], im)
    print("imágenes distintas:", len(tot))
    sys.exit()

if not a.vs:
    for i, s in enumerate(P.slides, 1):
        if a.solo and i not in a.solo:
            continue
        print("\n=== %d  %s  [%s]" % (i, titulo(s), s.slide_layout.name))
        for f in formas(s):
            print("   %-12s %-26s (%s,%s) %sx%s | %s" % (f[0], f[1][:26], f[2], f[3], f[4], f[5], f[6][:220]))
        if notas(s).strip():
            print("   NOTAS:", notas(s)[:600])
    sys.exit()

V = Presentation(a.vs)
viejas = {titulo(s): s for s in V.slides}
print("láminas: %d (antes %d)" % (len(P.slides), len(V.slides)))
for i, s in enumerate(P.slides, 1):
    t = titulo(s); o = viejas.get(t)
    if o is None:
        print("\n=== %d  %s   ← NUEVA o retitulada" % (i, t)); continue
    ka = {f[1:] for f in formas(o)}; kb = {f[1:] for f in formas(s)}
    add = [f for f in formas(s) if f[1:] not in ka]; rem = [f for f in formas(o) if f[1:] not in kb]
    if add or rem or notas(o) != notas(s):
        print("\n=== %d  %s" % (i, t))
        for f in add:
            print("   [+/~] %-12s %-26s (%s,%s) %sx%s | %s" % (f[0], f[1][:26], f[2], f[3], f[4], f[5], f[6][:200]))
        for f in rem:
            print("   [-]   %-26s | %s" % (f[1][:26], f[6][:120]))
        if notas(o) != notas(s):
            print("   NOTAS:", notas(s)[:800])
nuevas = {titulo(s) for s in P.slides}
for t in viejas:
    if t not in nuevas:
        print("\n[eliminada] %s" % t)
