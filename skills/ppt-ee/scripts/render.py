"""
Renderiza un .pptx con el PowerPoint instalado (fidelidad real: fuentes Cairo, SVG, EMF) y arma hojas de contacto.

    python render.py deck.pptx salida_dir                 # exporta todas las láminas a salida_dir/sNN.png
    python render.py deck.pptx salida_dir --hoja hoja.png # además, una hoja de contacto con todas
    python render.py deck.pptx salida_dir --laminas 7 10 --hoja par.png   # hoja sólo con esas láminas, grandes

Si PowerPoint falla con "file not found" es casi siempre porque otra instancia no terminó de cerrar: el script reintenta.
Requiere Windows con PowerPoint y Pillow.
"""
import argparse, glob, os, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))


def exportar(pptx, outdir, w=1600, h=900, intentos=4):
    pptx = os.path.abspath(pptx); outdir = os.path.abspath(outdir)
    for f in glob.glob(os.path.join(outdir, "s*.png")):
        os.remove(f)
    for k in range(intentos):
        r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            os.path.join(AQUI, "exportar.ps1"), "-pptx", pptx, "-outdir", outdir, "-w", str(w), "-h", str(h)],
                           capture_output=True, text=True)
        n = len(glob.glob(os.path.join(outdir, "s*.png")))
        if n:
            return n
        time.sleep(3)
    sys.exit("PowerPoint no pudo abrir el archivo:\n" + r.stdout[-800:] + r.stderr[-800:])


def hoja(pngs, salida, cols=None, ancho=None):
    from PIL import Image, ImageDraw
    cols = cols or (2 if len(pngs) <= 6 else 4)
    ancho = ancho or (1000 if cols <= 2 else 640)
    alto = int(ancho * 9 / 16)
    filas = (len(pngs) + cols - 1) // cols
    M = Image.new("RGB", (cols * ancho, filas * (alto + 24)), "white"); d = ImageDraw.Draw(M)
    for k, f in enumerate(pngs):
        im = Image.open(f).convert("RGB").resize((ancho, alto))
        x = (k % cols) * ancho; y = (k // cols) * (alto + 24)
        M.paste(im, (x, y + 24)); d.rectangle([x, y + 24, x + ancho - 1, y + 24 + alto - 1], outline=(200, 200, 200))
        d.text((x + 8, y + 6), os.path.basename(f), fill="black")
    M.save(salida)
    return salida


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx"); ap.add_argument("outdir")
    ap.add_argument("--hoja"); ap.add_argument("--laminas", type=int, nargs="*")
    ap.add_argument("--cols", type=int)
    a = ap.parse_args()
    n = exportar(a.pptx, a.outdir)
    print("exportadas", n)
    if a.hoja:
        fs = sorted(glob.glob(os.path.join(a.outdir, "s*.png")))
        if a.laminas:
            fs = [fs[i - 1] for i in a.laminas]
        print("hoja:", hoja(fs, a.hoja, a.cols))
