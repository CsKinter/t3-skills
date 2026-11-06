"""Helpers genéricos para editar el word/document.xml de un informe EE (extraído con docx_zip.py).

Todo es XML como texto. Ninguna función depende de un estudio: los bloques de párrafo, títulos y leyendas se clonan del
propio informe con `plantillas(xml)`, así heredan sus estilos. Uso típico:

    import sys; sys.path.insert(0, r"C:\\Users\\vicen\\.claude\\skills\\informe-ee\\scripts")
    from docx_ee import *
    x = open(doc, encoding="utf-8").read(); T = plantillas(x)
    nuevo = parrafo(T, "Texto.") + leyenda(T, "Tabla", 5, 2, "Descripción | E04.")

Las tablas usan el formato EE: cabecera 404040 con texto blanco, bordes D6D6D6, Cairo 8,5 pt, anchos en 1/50 de %.
"""
import os, re, struct

PAR = r"<w:p[ >](?:(?!<w:p[ >]).)*?</w:p>"
BLOQUE = r"<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>"
BORDE = '<w:%s w:val="single" w:sz="8" w:space="0" w:color="D6D6D6"/>'


def tx(b):
    """Texto plano de un bloque."""
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", b))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def limpio(b):
    """Quita ids de rastreo, marcadores y saltos de página renderizados de un bloque clonado."""
    b = re.sub(r' w14:(paraId|textId)="[^"]*"', "", b)
    b = re.sub(r"<w:bookmark(Start|End)[^>]*/>", "", b)
    return b.replace("<w:lastRenderedPageBreak/>", "")


# ---------------------------------------------------------------- plantillas clonadas del propio informe
def plantillas(xml):
    """Busca en el informe un bloque modelo de cada tipo: h2, h3, parrafo, leyenda_fig, leyenda_tabla, fig_img.
    Falla con el nombre del que no encuentra (el informe no tiene aún ninguno de ese tipo)."""
    bloques = re.findall(PAR, xml, re.S)

    def uno(cond, nombre):
        for b in bloques:
            if cond(b):
                return b
        raise LookupError("el informe no tiene un bloque modelo para «%s»" % nombre)

    estilo = lambda b, s: '<w:pStyle w:val="%s"/>' % s in b
    return {
        "h2": uno(lambda b: estilo(b, "Heading2") and tx(b).strip(), "h2"),
        "h3": uno(lambda b: estilo(b, "Heading3") and tx(b).strip(), "h3"),
        "parrafo": uno(lambda b: "<w:pStyle" not in b and len(tx(b)) > 60 and "<w:drawing>" not in b, "parrafo"),
        "leyenda_fig": uno(lambda b: estilo(b, "Imagenes") and tx(b).startswith("Figura") and "SEQ" in b, "leyenda_fig"),
        "leyenda_tabla": uno(lambda b: estilo(b, "Imagenes") and tx(b).startswith("Tabla") and "SEQ" in b, "leyenda_tabla"),
        "fig_img": uno(lambda b: estilo(b, "ImagenEE") and "<w:drawing>" in b, "fig_img"),
    }


def parrafo(T, texto):
    """Párrafo de cuerpo con el formato del modelo."""
    b = limpio(T["parrafo"])
    rpr = re.search(r"<w:r>(<w:rPr>.*?</w:rPr>)", b).group(1)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", b).group(0)
    head = re.match(r"<w:p[^>]*>", b).group(0)
    return '%s%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (head, ppr, rpr, esc(texto))


def con_texto(p, texto):
    """Cambia el texto de un párrafo existente conservando su pPr y el rPr del primer run."""
    head = re.match(r"<w:p[^>]*>", p).group(0)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
    m = re.search(r"<w:r[ >](?:(?!</w:r>).)*?(<w:rPr>.*?</w:rPr>)", p, re.S)
    return '%s%s<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (
        head, ppr.group(0) if ppr else "", m.group(1) if m else "", esc(texto))


def titulo(plantilla, texto):
    """Título (h2/h3) con el texto cambiado; `plantilla` es T["h2"] o T["h3"]."""
    return re.sub(r"(<w:r>(?:<w:rPr>.*?</w:rPr>)?)<w:t[^>]*>[^<]*</w:t>",
                  lambda m: m.group(1) + "<w:t>%s</w:t>" % esc(texto), limpio(plantilla), count=1)


def leyenda(T, tipo, cap, n, desc):
    """Leyenda con campos STYLEREF/SEQ. tipo: «Figura» o «Tabla». El número escrito en los campos es provisorio:
    Word lo recalcula con render_docx.ps1."""
    b = limpio(T["leyenda_tabla" if tipo == "Tabla" else "leyenda_fig"])
    vals = iter([str(cap), str(n)])
    b = re.sub(r"(<w:rPr><w:noProof/></w:rPr>)<w:t>[^<]*</w:t>", lambda m: m.group(1) + "<w:t>%s</w:t>" % next(vals), b)
    fin = '<w:fldChar w:fldCharType="end"/></w:r>'
    k = b.rfind(fin) + len(fin)
    return b[:k] + '<w:r><w:t xml:space="preserve">: %s</w:t></w:r></w:p>' % esc(desc)


# ---------------------------------------------------------------- tablas EE
def run(t, size=18, bold=False, color="000000", italic=False):
    """Run con fuente del tema; size en medios puntos (17 = 8,5 pt)."""
    rpr = ('<w:rFonts w:eastAsia="Times New Roman" w:cs="Cairo"/>%s%s<w:color w:val="%s"/><w:sz w:val="%d"/>'
           '<w:szCs w:val="%d"/><w:lang w:val="es-CL" w:eastAsia="es-CL"/>') % (
        "<w:b/><w:bCs/>" if bold else "", "<w:i/><w:iCs/>" if italic else "", color, size, size)
    return '<w:r><w:rPr>%s</w:rPr><w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(t))


def par(contenido, jc="center"):
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="%s"/></w:pPr>%s</w:p>'
            % (jc, contenido))


def celda(pars, pct, fill="FFFFFF", span=1, valign="center"):
    tcpr = '<w:tcW w:w="%d" w:type="pct"/>%s<w:tcBorders>%s%s%s%s</w:tcBorders><w:shd w:val="clear" w:color="auto" w:fill="%s"/><w:vAlign w:val="%s"/>' % (
        pct, '<w:gridSpan w:val="%d"/>' % span if span > 1 else "",
        BORDE % "top", BORDE % "left", BORDE % "bottom", BORDE % "right", fill, valign)
    return "<w:tc><w:tcPr>%s</w:tcPr>%s</w:tc>" % (tcpr, "".join(pars if isinstance(pars, list) else [pars]))


def fila(celdas, cab=False):
    return "<w:tr><w:trPr><w:cantSplit/>%s</w:trPr>%s</w:tr>" % ("<w:tblHeader/>" if cab else "", "".join(celdas))


def tabla(pcts, filas, ancho_dxa=9895):
    """pcts: ancho de cada columna en 1/50 de % (suman 5000 = ancho completo)."""
    dxa = [int(ancho_dxa * p / 5000) for p in pcts]
    pr = ('<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/><w:tblCellMar>'
          '<w:top w:w="28" w:type="dxa"/><w:left w:w="70" w:type="dxa"/><w:bottom w:w="28" w:type="dxa"/><w:right w:w="70" w:type="dxa"/>'
          '</w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>')
    return "<w:tbl>%s<w:tblGrid>%s</w:tblGrid>%s</w:tbl>" % (pr, "".join('<w:gridCol w:w="%d"/>' % d for d in dxa), "".join(filas))


def cabecera(textos, pcts):
    return fila([celda(par(run(t, 17, True, "FFFFFF")), p, "404040") for t, p in zip(textos, pcts)], cab=True)


def datos(valores, pcts, fills=None, bolds=None, jcs=None):
    """Fila de datos: primera columna a la izquierda, el resto centradas."""
    out = []
    for i, (v, p) in enumerate(zip(valores, pcts)):
        out.append(celda(par(run(v, 17, bolds[i] if bolds else False),
                             jcs[i] if jcs else ("left" if i == 0 else "center")), p, fills[i] if fills else "FFFFFF"))
    return fila(out)


def nota(t, pcts):
    """Fila de nota al pie (cursiva gris, ocupa todo el ancho)."""
    return fila([celda(par(run(t, 15, False, "595959", True), "left"), sum(pcts), "FFFFFF", len(pcts))])


def reemplazar_tabla_antes_de(xml, inicio_leyenda, nueva):
    """Reemplaza la tabla que precede a la leyenda cuyo texto empieza con `inicio_leyenda` (p. ej. «Tabla 51», sin
    guion: los números están en campos). Falla si lo anterior a la leyenda no es una tabla."""
    bl = [(m.start(), m.end(), m.group(0)) for m in re.finditer(BLOQUE, xml, re.S)]
    i = next(k for k, (s, e, b) in enumerate(bl) if b.startswith("<w:p") and tx(b).startswith(inicio_leyenda))
    s, e, b = bl[i - 1]
    assert b.startswith("<w:tbl>"), "no hay tabla antes de " + inicio_leyenda
    return xml[:s] + nueva + xml[e:]


# ---------------------------------------------------------------- imágenes
def _tam_png(ruta):
    with open(ruta, "rb") as f:
        h = f.read(24)
    assert h[:8] == b"\x89PNG\r\n\x1a\n", "no es PNG: " + ruta
    return struct.unpack(">II", h[16:24])


class Medios:
    """Registra imágenes nuevas en word/media y en document.xml.rels. Llamar `guardar()` al terminar."""

    def __init__(self, unz, id_inicial=960000):
        self.unz = unz
        self.rels_ruta = os.path.join(unz, "word", "_rels", "document.xml.rels")
        self.rels = open(self.rels_ruta, encoding="utf-8").read()
        self.rid = max(int(r) for r in re.findall(r'Id="rId(\d+)"', self.rels))
        self.img = max([int(m) for m in re.findall(r"media/image(\d+)\.", self.rels)] or [0])
        self.doc_id = id_inicial
        self.nuevas = []

    def imagen(self, png, ancho_cm, nombre, T=None):
        """Párrafo con la imagen en línea a `ancho_cm` (16,4 = ancho completo). Con T usa el estilo ImagenEE del informe;
        sin T usa un párrafo centrado con keepNext."""
        import shutil
        self.rid += 1; self.img += 1; self.doc_id += 1
        dst = "image%d.png" % self.img
        os.makedirs(os.path.join(self.unz, "word", "media"), exist_ok=True)
        shutil.copyfile(png, os.path.join(self.unz, "word", "media", dst))
        self.nuevas.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/%s"/>' % (self.rid, dst))
        w, h = _tam_png(png)
        cx = int(ancho_cm / 2.54 * 914400); cy = int(cx * h / w)
        dib = ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/><wp:docPr id="%d" name="%s"/>'
               '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="%d" name="%s.png"/><pic:cNvPicPr/></pic:nvPicPr>'
               '<pic:blipFill><a:blip r:embed="rId%d"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm>'
               '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (
            cx, cy, self.doc_id, esc(nombre), self.doc_id, esc(nombre), self.rid, cx, cy)
        if T:
            head = re.match(r"<w:p[^>]*>", limpio(T["fig_img"])).group(0)
            ppr = re.search(r"<w:pPr>.*?</w:pPr>", T["fig_img"], re.S).group(0)
        else:
            head, ppr = "<w:p>", '<w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr>'
        return head + ppr + dib + "</w:p>"

    def guardar(self):
        if self.nuevas:
            open(self.rels_ruta, "w", encoding="utf-8").write(self.rels.replace("</Relationships>", "".join(self.nuevas) + "</Relationships>"))
