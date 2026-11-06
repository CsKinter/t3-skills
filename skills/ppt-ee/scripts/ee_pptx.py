"""
ee_pptx — piezas para armar y editar presentaciones con la plantilla de Estudios Eléctricos.

Uso típico (deck nuevo):

    import sys; sys.path.insert(0, r"<ruta de la skill>/scripts")
    from ee_pptx import *
    prs = abrir_plantilla()                       # deja sólo portada y cierre de la plantilla
    portada(prs, "Estudio de Restricciones", "PV + BESS Entre Valles  |  Engie Energía Chile",
            "EE-ES-2026-1732-RB  |  29 de septiembre de 2026")
    s = nueva_lamina(prs, "Resultados | Caso base | ", "Diurno",
                     conclusion="El modo del BESS decide la colocación del PFV",
                     notas="Guion para el orador…")
    box(s, 0.87, 1.5, 5.6, 2.0, paras=[[("Título", 14, True, NEG)], [("Texto", 12, False, GRT)]])
    figura(s, 7.25, 1.5, 5.2, 4.45, "Diagrama de la zona", "Informe, Figura 5-1")
    cierre(prs)
    guardar(prs, r"C:\\...\\Documentos\\mi_deck.pptx")

Uso típico (editar un deck que el usuario ya modificó):

    prs = abrir(r"...\\deck_del_usuario.pptx")
    s = buscar_lamina(prs, "Resultados | Caso base | Nocturno")
    quitar_formas(s, lambda sh: not es_titulo(sh) and not es_imagen(sh))
    ...
    guardar(prs, r"...\\deck_v2.pptx")           # siempre con otro nombre

Coordenadas en pulgadas sobre 13,33 × 7,5 in. Grilla de la casa:
  título  y = 0,50 (x 0,87, ancho 11,6)
  cuerpo  y = 1,45 … 6,00, x = 0,87 … 12,45
  franja de conclusión  y = 6,15, alto 0,62
"""
import copy
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.oxml.ns import qn
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from lxml import etree

# ------------------------------------------------------------------ marca EE
OR = RGBColor(0xF2, 0x91, 0x00)    # naranjo principal (accent1)
OR2 = RGBColor(0xF2, 0x74, 0x00)   # naranjo oscuro (accent2)
NEG = RGBColor(0x1D, 0x1D, 0x1B)   # negro de marca
GRT = RGBColor(0x59, 0x59, 0x59)   # gris texto secundario
GRL = RGBColor(0xF2, 0xF2, 0xF2)   # gris fondo de tarjetas
GRM = RGBColor(0xBF, 0xBF, 0xBF)   # gris medio (series de referencia, pasos neutros)
BL = RGBColor(0xFF, 0xFF, 0xFF)
AZ = RGBColor(0x2C, 0x8B, 0xCE)    # azul EPE (accent3), sólo si hace falta un contraste
FUENTE = "Cairo"

PLANTILLA = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "plantilla_EE.pptx"))
LAYOUT_CONTENIDO = "EE Logo Izq"
_RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_TITULO_XML = None


# ------------------------------------------------------------------ abrir / guardar
def _titulo_xml():
    """tabla de una celda con borde izquierdo naranjo: así se hacen los títulos en la plantilla"""
    global _TITULO_XML
    if _TITULO_XML is None:
        t = Presentation(PLANTILLA)
        for s in t.slides:
            for sh in s.shapes:
                if sh.name == "Tabla 15" and sh.has_table:
                    _TITULO_XML = copy.deepcopy(sh._element)
                    return _TITULO_XML
        raise RuntimeError("no encontré la tabla de título 'Tabla 15' en la plantilla")
    return _TITULO_XML


def abrir_plantilla(ruta=PLANTILLA):
    """Carga la plantilla y borra las láminas de ejemplo, dejando la portada y el cierre (¡Gracias!)."""
    prs = Presentation(ruta)
    keep = []
    for s in prs.slides:
        txt = " ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
        tabs = " ".join(c.text for sh in s.shapes if sh.has_table for r in sh.table.rows for c in r.cells)
        if tabs.strip().startswith("TÍTULO") or "Thank you!" in txt:
            keep.append(s)
    if len(keep) != 2:
        raise RuntimeError("no identifiqué portada y cierre en la plantilla")
    lst = prs.slides._sldIdLst
    for sid in list(lst):
        part = prs.part.related_part(sid.get(qn("r:id")))
        if part is not keep[0].part and part is not keep[1].part:
            prs.part.drop_rel(sid.get(qn("r:id"))); lst.remove(sid)
    return prs


def abrir(ruta):
    return Presentation(ruta)


def guardar(prs, ruta):
    """Renumera las partes de lámina según el orden final y guarda.
    Sin esto, borrar láminas y agregar nuevas deja dos 'slideN.xml' con el mismo nombre y PowerPoint no abre el archivo."""
    lst = prs.slides._sldIdLst
    for fase in (1000, 1):
        for k, sid in enumerate(lst):
            prs.part.related_part(sid.get(qn("r:id"))).partname = PackURI("/ppt/slides/slide%d.xml" % (k + fase))
    prs.save(ruta)
    return ruta


# ------------------------------------------------------------------ láminas
def _sids(prs):
    return list(prs.slides._sldIdLst)


def _sid_de(prs, slide):
    for sid in _sids(prs):
        if prs.part.related_part(sid.get(qn("r:id"))) is slide.part:
            return sid
    raise KeyError("lámina no encontrada")


def ordenar(prs, laminas):
    """Deja las láminas en el orden dado (lista de objetos Slide). Las que no estén en la lista se eliminan."""
    lst = prs.slides._sldIdLst
    ids = [_sid_de(prs, s) for s in laminas]
    for sid in list(lst):
        if sid not in ids:
            prs.part.drop_rel(sid.get(qn("r:id")))
        lst.remove(sid)
    for sid in ids:
        lst.append(sid)


def mover_lamina(prs, slide, posicion):
    """posicion 0-based en el deck final"""
    lst = prs.slides._sldIdLst
    sid = _sid_de(prs, slide); lst.remove(sid); lst.insert(posicion, sid)


def quitar_lamina(prs, slide):
    lst = prs.slides._sldIdLst
    sid = _sid_de(prs, slide)
    prs.part.drop_rel(sid.get(qn("r:id"))); lst.remove(sid)


def titulo_de(slide):
    t = [sh for sh in slide.shapes if es_titulo(sh)]
    return t[0].table.cell(0, 0).text if t else ""


def buscar_lamina(prs, titulo):
    for s in prs.slides:
        if titulo_de(s).strip() == titulo.strip():
            return s
    raise KeyError(titulo)


def _next_id(slide):
    ids = [int(c.get("id")) for c in slide.shapes._spTree.iter(qn("p:cNvPr")) if c.get("id", "").isdigit()]
    return max(ids + [1]) + 1


def titulo(slide, ruta, ultimo, ancho=11.6, y=0.5):
    """Título de la casa. ruta = tramo en fino (ej. 'Resultados | Caso base | '), ultimo = tramo en negrita."""
    el = copy.deepcopy(_titulo_xml())
    el.find(".//" + qn("p:cNvPr")).set("id", str(_next_id(slide)))
    for ext in el.findall(".//" + qn("p:cNvPr") + "/" + qn("a:extLst")):
        ext.getparent().remove(ext)
    off = el.find(".//" + qn("a:off")); off.set("x", str(Emu(Inches(0.87)))); off.set("y", str(Emu(Inches(y))))
    el.find(".//" + qn("p:xfrm") + "/" + qn("a:ext")).set("cx", str(Emu(Inches(ancho))))
    el.find(".//" + qn("a:gridCol")).set("w", str(Emu(Inches(ancho))))
    rs = el.findall(".//" + qn("a:r"))
    rs[0].find(qn("a:t")).text = ruta
    rs[1].find(qn("a:t")).text = ultimo
    if not ruta:
        rs[0].getparent().remove(rs[0])
    slide.shapes._spTree.append(el)


def nueva_lamina(prs, ruta, ultimo, conclusion=None, notas=""):
    lay = [l for l in prs.slide_layouts if l.name == LAYOUT_CONTENIDO][0]
    s = prs.slides.add_slide(lay)
    titulo(s, ruta, ultimo)
    if conclusion:
        franja(s, conclusion)
    if notas:
        s.notes_slide.notes_text_frame.text = notas
    return s


def portada(prs, titulo_txt, subtitulo, linea3=None, size=40):
    s = [x for x in prs.slides if titulo_de(x) == "" and any(sh.has_table for sh in x.shapes)][0]
    t = [sh for sh in s.shapes if sh.has_table][0]
    paras = [(c, p) for row in t.table.rows for c in row.cells for p in c.text_frame.paragraphs if p.runs]
    for k, txt in enumerate([titulo_txt, subtitulo]):
        c, p = paras[k]; rs = p.runs; rs[0].text = txt
        for r in rs[1:]:
            r._r.getparent().remove(r._r)
        if k == 0:
            rs[0].font.size = Pt(size)
    if linea3:
        p = paras[1][0].text_frame.add_paragraph(); run(p, linea3, 14, False, GRT)
    return s


def cierre(prs, texto="¡Gracias!"):
    for s in prs.slides:
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip() in ("Thank you!", "¡Gracias!", "Gracias"):
                rs = sh.text_frame.paragraphs[0].runs; rs[0].text = texto
                for r in rs[1:]:
                    r._r.getparent().remove(r._r)
                return s


# ------------------------------------------------------------------ texto
def run(p, text, size=14, bold=False, color=NEG):
    r = p.add_run(); r.text = text
    f = r.font; f.size = Pt(size); f.bold = bold; f.name = FUENTE; f.color.rgb = color
    rPr = r._r.get_or_add_rPr(); cs = etree.SubElement(rPr, qn("a:cs")); cs.set("typeface", FUENTE)
    return r


def _fill(tf, paras, align=PP_ALIGN.LEFT):
    """paras: lista de párrafos. Cada párrafo es una lista de runs (texto, tamaño, negrita, color),
    o un dict {"runs": [...], "bullet": True, "space": 4} para viñeta cuadrada naranja."""
    first = True
    for para in paras:
        if isinstance(para, dict):
            runs = para["runs"]; bullet = para.get("bullet", False); space = para.get("space", 4)
        else:
            runs = para; bullet = False; space = 4
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.alignment = align; p.space_after = Pt(space)
        if bullet:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Emu(Inches(0.22)))); pPr.set("indent", str(-Emu(Inches(0.22))))
            bc = etree.SubElement(pPr, qn("a:buClr")); sc = etree.SubElement(bc, qn("a:srgbClr")); sc.set("val", "F29100")
            bf = etree.SubElement(pPr, qn("a:buFont")); bf.set("typeface", "Wingdings")
            bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "\u00a7")
        for (t, sz, b, c) in runs:
            run(p, t, sz, b, c)


def bullets(items, size=12, space=4, color=NEG):
    return [{"runs": [(t, size, False, color)], "bullet": True, "space": space} for t in items]


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, margin=0.05, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(margin))
    _fill(tf, paras, align)
    return tb


def set_parrafos(shape_o_elemento, textos):
    """Reemplaza el texto párrafo a párrafo conservando el formato del primer run de cada uno.
    Útil para clonar una pieza de otra lámina y cambiarle sólo el contenido."""
    el = getattr(shape_o_elemento, "_element", shape_o_elemento)
    for p, t in zip(el.findall(".//" + qn("a:p")), textos):
        rs = p.findall(qn("a:r"))
        if not rs:
            continue
        rs[0].find(qn("a:t")).text = t
        for r in rs[1:]:
            p.remove(r)


# ------------------------------------------------------------------ piezas
def box(slide, x, y, w, h, fill=GRL, line=None, radius=0.06, paras=None, anchor=MSO_ANCHOR.TOP,
        margin=0.15, align=PP_ALIGN.LEFT, dash=False, lw=1.25):
    """Tarjeta redondeada. fill=None → sin relleno. line=OR para destacar con borde naranjo."""
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.adjustments[0] = radius; sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
        if dash:
            ln = sh.line._get_or_add_ln(); d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(margin))
    if paras:
        _fill(tf, paras, align)
    return sh


def encabezado(slide, x, y, w, texto, fill=OR, h=0.5, size=15):
    """Barra de encabezado de tarjeta (naranja para lo que compite/destaca, GRT o NEG para el contraste)."""
    return box(slide, x, y, w, h, fill=fill, radius=0.1, anchor=MSO_ANCHOR.MIDDLE, margin=0.18,
               paras=[[(texto, size, True, BL)]])


def franja(slide, texto, x=0.87, w=11.58, y=6.15, h=0.62):
    """Franja naranja de conclusión al pie. Es el mensaje de la lámina: el título sólo dice dónde estamos."""
    size = 15 if len(texto) <= 95 else 14
    return box(slide, x, y, w, h, fill=OR, anchor=MSO_ANCHOR.MIDDLE, margin=0.2, paras=[[(texto, size, True, BL)]])


def figura(slide, x, y, w, h, que, fuente):
    """Recuadro punteado para que el usuario pegue una figura del informe. Nunca inventar la imagen."""
    return box(slide, x, y, w, h, fill=BL, line=OR, dash=True, radius=0.03, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER,
               paras=[[("FIGURA A PEGAR", 11, True, OR)], [(que, 14, True, NEG)], [(fuente, 11, False, GRT)]])


def stat(slide, x, y, w, grande, etiqueta, bsize=40, color=OR, lsize=13, h=1.25):
    return text(slide, x, y, w, h, [[(grande, bsize, True, color)], [(etiqueta, lsize, False, GRT)]], margin=0)


def tarjeta_cifra(slide, x, y, w, h, encima, cifra, debajo, color=OR, csize=44):
    """Tarjeta gris con etiqueta arriba, cifra grande y comentario abajo (ej. 'E05 vespertino' / '0 MW' / 'antes 11,3 MW')."""
    return box(slide, x, y, w, h, fill=GRL, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER,
               paras=[[(encima, 13, True, GRT)], [(cifra, csize, True, color)], [(debajo, 12, False, GRT)]])


def num_circle(slide, x, y, d, n, fill=OR, size=16):
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)); c.shadow.inherit = False
    c.fill.solid(); c.fill.fore_color.rgb = fill; c.line.fill.background()
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; run(p, str(n), size, True, BL)
    return c


def pasos(slide, x, y, w, items, alto=0.85, sep=0.15, d=0.5, destacar_ultimo=True):
    """Secuencia vertical numerada (mecanismos, cadenas lógicas). items = [(titulo, detalle), ...]"""
    for k, (a, b) in enumerate(items):
        cy = y + k * (alto + sep)
        ult = destacar_ultimo and k == len(items) - 1
        num_circle(slide, x, cy + (alto - d) / 2, d, k + 1, fill=OR if ult else GRM, size=14)
        box(slide, x + d + 0.18, cy, w - d - 0.18, alto, fill=GRL, anchor=MSO_ANCHOR.MIDDLE, margin=0.14,
            paras=[[(a, 14, True, NEG)], [(b, 12, False, GRT)]])


def flecha(slide, x, y, w=0.35, h=0.35, color=OR):
    a = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Inches(x), Inches(y), Inches(w), Inches(h)); a.shadow.inherit = False
    a.fill.solid(); a.fill.fore_color.rgb = color; a.line.fill.background()
    return a


def tabla(slide, x, y, w, rows, colw, hdr_fill=NEG, size=12, rowh=0.36):
    """Tabla con encabezado negro, filas alternadas y bordes finos grises. Primera columna en negrita."""
    nr, nc = len(rows), len(rows[0])
    gf = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rowh * nr)); t = gf.table
    tblPr = t._tbl.tblPr
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"
    for j, cw in enumerate(colw):
        t.columns[j].width = Inches(cw)
    for i, r in enumerate(rows):
        t.rows[i].height = Inches(rowh)
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb = hdr_fill if i == 0 else (GRL if i % 2 == 0 else BL)
            p = c.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            run(p, v, size, i == 0 or j == 0, BL if i == 0 else NEG)
            tcPr = c._tc.get_or_add_tcPr()
            fillel = tcPr.find(qn("a:solidFill"))
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):      # los bordes van antes del relleno en el esquema
                ln = etree.Element(qn(tag)); ln.set("w", "6350")
                sf = etree.SubElement(ln, qn("a:solidFill")); cc = etree.SubElement(sf, qn("a:srgbClr")); cc.set("val", "D9D9D9")
                fillel.addprevious(ln)
    return gf


# ------------------------------------------------------------------ gráficos nativos
def _coma(v, dec=1):
    return ("{:.%df}" % dec).format(v).replace(".", ",")


def _ejes(ch, maxv):
    va = ch.value_axis; va.visible = False; va.has_major_gridlines = False; va.minimum_scale = 0
    if maxv:
        va.maximum_scale = maxv
    ca = ch.category_axis; ca.tick_labels.font.size = Pt(12); ca.tick_labels.font.name = FUENTE
    ca.format.line.color.rgb = GRM; ca.has_major_gridlines = False


def _titulo_graf(ch, t):
    if t:
        ch.has_title = True; run(ch.chart_title.text_frame.paragraphs[0], t, 13, True, NEG)
    else:
        ch.has_title = False


def barras(slide, x, y, w, h, cats, vals, colores=None, titulo_graf=None, maxv=None, pcts=None, unidad=" MW", dec=1):
    """Columnas de una serie. Etiquetas por barra escritas a mano con coma decimal (el formato numérico
    de PowerPoint sale con punto en esta máquina). pcts = segunda línea opcional por barra ('61 %')."""
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("serie", vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    ch.has_legend = False; ch.font.name = FUENTE; ch.font.size = Pt(12); ch.font.color.rgb = GRT
    _titulo_graf(ch, titulo_graf)
    pl = ch.plots[0]; pl.gap_width = 60; pl.has_data_labels = True
    ser = pl.series[0]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = OR
    for i, v in enumerate(vals):
        if colores:
            pt = ser.points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = colores[i]
        dl = ser.points[i].data_label; dl.position = XL_LABEL_POSITION.OUTSIDE_END
        tf = dl.text_frame; run(tf.paragraphs[0], _coma(v, dec) + unidad, 13, True, NEG)
        if pcts:
            run(tf.add_paragraph(), pcts[i], 11, False, GRT)
    _ejes(ch, maxv)
    return ch


def barras_agrupadas(slide, x, y, w, h, cats, series, titulo_graf=None, maxv=None, dec=1):
    """series = [(nombre, [valores], color), ...]. Referencia en GRM, protagonista en OR, contraste en NEG."""
    cd = CategoryChartData(); cd.categories = cats
    for nombre, vals, _ in series:
        cd.add_series(nombre, vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    ch.font.name = FUENTE; ch.font.size = Pt(12); ch.font.color.rgb = GRT
    ch.has_legend = True; ch.legend.include_in_layout = False; ch.legend.position = XL_LEGEND_POSITION.TOP
    ch.legend.font.size = Pt(12); ch.legend.font.name = FUENTE
    _titulo_graf(ch, titulo_graf)
    pl = ch.plots[0]; pl.gap_width = 70; pl.overlap = -10; pl.has_data_labels = True
    for k, (nombre, vals, color) in enumerate(series):
        ser = pl.series[k]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = color
        for i, v in enumerate(vals):
            dl = ser.points[i].data_label; dl.position = XL_LABEL_POSITION.OUTSIDE_END
            run(dl.text_frame.paragraphs[0], _coma(v, dec), 12, True, NEG)
    _ejes(ch, maxv)
    return ch


# ------------------------------------------------------------------ edición de láminas existentes
def es_titulo(sh):
    return sh.has_table and abs(Emu(sh.top).inches - 0.5) < 0.06


def es_franja(sh):
    return (not sh.has_table) and Emu(sh.top).inches > 6.05


def es_imagen(sh):
    return sh.shape_type == 13


def quitar_formas(slide, criterio):
    """Elimina las formas para las que criterio(shape) es True. Suelta también la relación de los gráficos."""
    for sh in list(slide.shapes):
        if not criterio(sh):
            continue
        el = sh._element
        if sh.has_chart:
            slide.part.drop_rel(el.find(".//" + qn("c:chart")).get(qn("r:id")))
        el.getparent().remove(el)


def _xfrm(el):
    for tag in ("p:spPr", "p:grpSpPr"):
        c = el.find(qn(tag))
        if c is not None and c.find(qn("a:xfrm")) is not None:
            return c.find(qn("a:xfrm"))
    return el.find(qn("p:xfrm"))


def copiar_formas(src_slide, formas, dst_slide, x, y, w, h, quitar_origen=False, alinear="centro"):
    """Copia formas (imágenes, grupos, anotaciones) a otra lámina, escaladas EN BLOQUE para caber en la caja
    destino y conservando su posición relativa (las anotaciones siguen marcando lo mismo).
    Funciona dentro de la misma presentación o entre dos presentaciones distintas: en ese caso duplica
    los archivos de imagen con nombre nuevo para no chocar con los del destino."""
    formas = list(formas)
    bx = min(s.left for s in formas); by = min(s.top for s in formas)
    bw = max(s.left + s.width for s in formas) - bx; bh = max(s.top + s.height for s in formas) - by
    TX, TY, TW, TH = (Inches(v) for v in (x, y, w, h))
    k = min(TW / bw, TH / bh)
    ox = TX + (TW - bw * k) / 2 if alinear == "centro" else TX
    oy = TY + (TH - bh * k) / 2
    misma = src_slide.part.package is dst_slide.part.package
    cache = {}
    nid = _next_id(dst_slide)
    for sh in formas:
        el = copy.deepcopy(sh._element)
        for c in el.iter(qn("p:cNvPr")):
            c.set("id", str(nid)); nid += 1
        for tag in ("a:stCxn", "a:endCxn"):                 # conectores: las referencias a ids viejos no sirven
            for c in list(el.iter(qn(tag))):
                c.getparent().remove(c)
        for node in list(el.iter()):
            for key, val in list(node.attrib.items()):
                if not key.startswith(_RNS):
                    continue
                rel = src_slide.part.rels[val]
                if rel.is_external:
                    node.set(key, dst_slide.part.relate_to(rel.target_ref, rel.reltype, is_external=True))
                elif rel.reltype.endswith("/slide"):
                    node.getparent().remove(node)            # hipervínculos a láminas de otro deck
                else:
                    tp = rel.target_part
                    if not misma:
                        if id(tp) not in cache:
                            ext = str(tp.partname).rsplit(".", 1)[-1]
                            pn = dst_slide.part.package.next_partname("/ppt/media/imgcp%d." + ext)
                            cache[id(tp)] = Part(pn, tp.content_type, dst_slide.part.package, tp.blob)
                        tp = cache[id(tp)]
                    node.set(key, dst_slide.part.relate_to(tp, rel.reltype))
        xf = _xfrm(el)
        off = xf.find(qn("a:off")); ext = xf.find(qn("a:ext"))
        off.set("x", str(int(ox + (sh.left - bx) * k))); off.set("y", str(int(oy + (sh.top - by) * k)))
        ext.set("cx", str(int(sh.width * k))); ext.set("cy", str(int(sh.height * k)))
        dst_slide.shapes._spTree.append(el)
    if quitar_origen:
        for sh in formas:
            sh._element.getparent().remove(sh._element)
    return k


def clonar_forma(src_slide, nombre, dst_slide, textos=None):
    """Copia una pieza sin imágenes (tarjeta, óvalo, franja) desde otra lámina y le cambia los textos.
    Es la forma más segura de dejar dos láminas paralelas con formato idéntico."""
    el = copy.deepcopy([sh for sh in src_slide.shapes if sh.name == nombre][0]._element)
    nid = _next_id(dst_slide)
    for c in el.iter(qn("p:cNvPr")):
        c.set("id", str(nid)); nid += 1
    if textos:
        set_parrafos(el, textos)
    dst_slide.shapes._spTree.append(el)
    return el


def encajar_imagen(pic, x, y, w, h):
    """Redimensiona una imagen para caber en la caja sin deformarla, centrada."""
    TX, TY, TW, TH = (Inches(v) for v in (x, y, w, h))
    k = min(TW / pic.width, TH / pic.height)
    nw, nh = int(pic.width * k), int(pic.height * k)
    pic.left, pic.top, pic.width, pic.height = int(TX + (TW - nw) / 2), int(TY + (TH - nh) / 2), nw, nh
