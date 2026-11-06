"""PREFERIR insertar_plano.py: dejar la imagen dentro de un grupo hace que Word guarde un respaldo VML con gfxdata
y una copia rasterizada (R28 de Cumbres: docx de 30,8 MB). Este script queda para casos puntuales.

Reemplaza el dibujo de una figura del informe por una imagen SVG con respaldo PNG, conservando la leyenda nativa.

La figura se identifica por el bloque (párrafo) que contiene el dibujo. Si el grupo tiene la leyenda adentro (cuadro de
texto con campo SEQ Figura), la leyenda se conserva tal cual y el resto de las formas se cambia por una sola imagen
en el área que ocupaban. Se quita el mc:AlternateContent (su respaldo VML quedaría con el dibujo antiguo).

    python insertar_svg.py origen.docx destino.docx 253=salida/fig_5-1 298=salida/fig_6-1 ...
"""
import re
import sys
import zipfile

from lxml import etree

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}
SVG_EXT = '{96DAC541-7B7A-43D3-8B79-37D633B846F1}'
ASVG = 'http://schemas.microsoft.com/office/drawing/2016/SVG/main'
CM = 360000
REL_IMG = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'


def q(t):
    p, n = t.split(':')
    return '{%s}%s' % (NS[p], n)


def _pic(id_, nombre, rid_png, rid_svg, x, y, cx, cy):
    return etree.fromstring(f'''
<pic:pic xmlns:pic="{NS['pic']}" xmlns:a="{NS['a']}" xmlns:r="{NS['r']}">
 <pic:nvPicPr><pic:cNvPr id="{id_}" name="{nombre}"/><pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr></pic:nvPicPr>
 <pic:blipFill><a:blip r:embed="{rid_png}"><a:extLst><a:ext uri="{SVG_EXT}"><asvg:svgBlip xmlns:asvg="{ASVG}" r:embed="{rid_svg}"/></a:ext></a:extLst></a:blip>
  <a:stretch><a:fillRect/></a:stretch></pic:blipFill>
 <pic:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></pic:spPr>
</pic:pic>''')


def _es_leyenda(el):
    return 'SEQ Figura' in ''.join(t.text or '' for t in el.iter(q('w:instrText')))


def _tam_svg(svg_bytes):
    m = re.search(rb'width="([\d.]+)mm" height="([\d.]+)mm"', svg_bytes)
    return float(m.group(1)) / 10, float(m.group(2)) / 10


def main(origen, destino, *pares):
    sys.stdout.reconfigure(encoding='utf-8')
    zin = zipfile.ZipFile(origen)
    doc = etree.fromstring(zin.read('word/document.xml'))
    rels = etree.fromstring(zin.read('word/_rels/document.xml.rels'))
    ct = zin.read('[Content_Types].xml').decode('utf-8')
    if 'Extension="svg"' not in ct:
        ct = ct.replace('<Default Extension="png"', '<Default Extension="svg" ContentType="image/svg+xml"/>'
                                                     '<Default Extension="png"', 1)
    usados = {r.get('Id') for r in rels}
    bloques = list(doc.find(q('w:body')))
    nuevos = {}
    id_ = 90000
    for par in pares:
        b, base = par.split('=')
        svg, png = open(base + '.svg', 'rb').read(), open(base + '.png', 'rb').read()
        nombre = base.replace('\\', '/').split('/')[-1]
        rids = []
        for ext, datos in (('png', png), ('svg', svg)):
            k = 1
            while f'rIdSvg{k}' in usados:
                k += 1
            rid = f'rIdSvg{k}'
            usados.add(rid)
            destino_media = f'media/{nombre}.{ext}'
            etree.SubElement(rels, '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',
                             Id=rid, Type=REL_IMG, Target=destino_media)
            nuevos['word/' + destino_media] = datos
            rids.append(rid)
        w_cm, h_cm = _tam_svg(svg)
        bloque = bloques[int(b)]
        # Quitar mc:AlternateContent dejando el contenido de Choice.
        for ac in list(bloque.iter(q('mc:AlternateContent'))):
            if not list(ac.iter(q('wpg:wgp'))):
                continue
            dibujo = ac.find('mc:Choice', NS)[0]
            ac.getparent().replace(ac, dibujo)
        grupo = next(bloque.iter(q('wpg:wgp')))
        xf = grupo.find('wpg:grpSpPr/a:xfrm', NS)
        off, ext = xf.find('a:off', NS), xf.find('a:ext', NS)
        choff, chext = xf.find('a:chOff', NS), xf.find('a:chExt', NS)
        sx = int(chext.get('cx')) / int(ext.get('cx'))
        sy = int(chext.get('cy')) / int(ext.get('cy'))
        x0, y0 = int(choff.get('x')), int(choff.get('y'))
        quitar = [c for c in grupo if c.tag in (q('wps:wsp'), q('pic:pic'), q('wpg:grpSp')) and not _es_leyenda(c)]
        pos = list(grupo).index(quitar[0])
        for c in quitar:
            grupo.remove(c)
        id_ += 1
        grupo.insert(pos, _pic(id_, f'Figura SVG {nombre}', rids[0], rids[1], x0, y0,
                               round(w_cm * CM * sx), round(h_cm * CM * sy)))
        print(f'bloque {b}: {len(quitar)} formas → imagen {nombre} ({w_cm:.2f} × {h_cm:.2f} cm)')
    zout = zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        if it.filename == 'word/document.xml':
            zout.writestr(it, etree.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True))
        elif it.filename == 'word/_rels/document.xml.rels':
            zout.writestr(it, etree.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True))
        elif it.filename == '[Content_Types].xml':
            zout.writestr(it, ct.encode('utf-8'))
        else:
            zout.writestr(it, zin.read(it.filename))
    for k, v in nuevos.items():
        zout.writestr(k, v)
    zout.close()


if __name__ == '__main__':
    main(*sys.argv[1:])
