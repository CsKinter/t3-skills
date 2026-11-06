"""Reemplaza cada grupo DrawingML de figura por una IMAGEN SIMPLE (SVG + PNG de respaldo), sin grupo.
Word guarda los grupos con un respaldo VML (gfxdata + imagen rasterizada) que triplica el peso; una imagen simple no.
- Leyenda fuera del grupo: sólo se cambia el gráfico.
- Leyenda dentro, figura en línea: la leyenda pasa a párrafo(s) propio(s) bajo la figura (keepNext en la figura).
- Leyenda dentro, figura flotante: la leyenda queda como cuadro de texto flotante aparte, en la misma posición.
    python insertar_plano.py origen.docx destino.docx info.json carpeta_svg
"""
import copy
import json
import sys
import zipfile

from lxml import etree as E

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
      'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'}
SVG_EXT = '{96DAC541-7B7A-43D3-8B79-37D633B846F1}'
ASVG = 'http://schemas.microsoft.com/office/drawing/2016/SVG/main'
REL_IMG = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
PKG_REL = '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'


def q(t):
    p, n = t.split(':')
    return '{%s}%s' % (NS[p], n)


def es_leyenda(el):
    return 'SEQ Figura' in ''.join(t.text or '' for t in el.iter(q('w:instrText')))


def grafico_pic(id_, nombre, rpng, rsvg, cx, cy):
    return E.fromstring(
        f'<a:graphic xmlns:a="{NS["a"]}"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="{NS["pic"]}" xmlns:r="{NS["r"]}"><pic:nvPicPr><pic:cNvPr id="{id_}" name="{nombre}"/>'
        f'<pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rpng}"><a:extLst><a:ext uri="{SVG_EXT}"><asvg:svgBlip xmlns:asvg="{ASVG}" r:embed="{rsvg}"/>'
        f'</a:ext></a:extLst></a:blip><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:noFill/><a:ln><a:noFill/></a:ln></pic:spPr></pic:pic></a:graphicData></a:graphic>')


def main(origen, destino, info_json, carpeta):
    info = json.load(open(info_json))
    zin = zipfile.ZipFile(origen)
    doc = E.fromstring(zin.read('word/document.xml'))
    rels = E.fromstring(zin.read('word/_rels/document.xml.rels'))
    ct = zin.read('[Content_Types].xml').decode('utf-8')
    if 'Extension="svg"' not in ct:
        ct = ct.replace('<Default Extension="png"', '<Default Extension="svg" ContentType="image/svg+xml"/><Default Extension="png"', 1)
    usados = {r.get('Id') for r in rels}
    sig = [max(int(d.get('id')) for d in doc.iter(q('wp:docPr'))) + 1]

    def nuevo_id():
        sig[0] += 1
        return sig[0]

    bloques = list(doc.find(q('w:body')))
    media = {}
    for b, f in info.items():
        bl = bloques[int(b)]
        nombre = f'fig_{b}'
        rid = {}
        for ext in ('png', 'svg'):
            k = 1
            while f'rIdFig{k}' in usados:
                k += 1
            rid[ext] = f'rIdFig{k}'
            usados.add(rid[ext])
            E.SubElement(rels, PKG_REL, Id=rid[ext], Type=REL_IMG, Target=f'media/{nombre}.{ext}')
            media[f'word/media/{nombre}.{ext}'] = open(f'{carpeta}/{nombre}.{ext}', 'rb').read()
        for ac in list(bl.iter(q('mc:AlternateContent'))):
            if list(ac.iter(q('wpg:wgp'))):
                ac.getparent().replace(ac, ac.find('mc:Choice', NS)[0])
        dib = [d for d in bl.iter(q('w:drawing')) if list(d.iter(q('wpg:wgp')))][0]
        cont = dib[0]
        grupo = next(dib.iter(q('wpg:wgp')))
        xf = grupo.find('wpg:grpSpPr/a:xfrm', NS)
        cx = int(xf.find('a:ext', NS).get('cx'))
        cy_g = int(xf.find('a:ext', NS).get('cy'))
        chx, chy = int(xf.find('a:chOff', NS).get('x')), int(xf.find('a:chOff', NS).get('y'))
        sx = cx / int(xf.find('a:chExt', NS).get('cx'))
        sy = cy_g / int(xf.find('a:chExt', NS).get('cy'))
        alto = f['alto']
        ley = [c for c in grupo if c.tag in (q('wps:wsp'), q('wpg:grpSp')) and es_leyenda(c)]
        cont.find('wp:extent', NS).set('cy', str(alto))
        ee = cont.find('wp:effectExtent', NS)
        if ee is not None:
            for k in 'ltrb':
                ee.set(k, '0')
        cont.replace(cont.find('a:graphic', NS), grafico_pic(nuevo_id(), f'Figura {nombre}', rid['png'], rid['svg'], cx, alto))
        fr = cont.find('wp:cNvGraphicFramePr', NS)
        if fr is not None:
            for c in list(fr):
                fr.remove(c)
        if not ley:
            print(b, 'leyenda fuera')
            continue
        lw = ley[0]
        lxf = lw.find('wps:spPr/a:xfrm', NS)
        lx = round((int(lxf.find('a:off', NS).get('x')) - chx) * sx)
        ly = round((int(lxf.find('a:off', NS).get('y')) - chy) * sy)
        lcx = round(int(lxf.find('a:ext', NS).get('cx')) * sx)
        lcy = round(int(lxf.find('a:ext', NS).get('cy')) * sy)
        p_fig = dib
        while p_fig.tag != q('w:p'):
            p_fig = p_fig.getparent()
        if cont.tag == q('wp:inline'):
            ppr = p_fig.find('w:pPr', NS)
            if ppr is None:
                ppr = E.Element(q('w:pPr'))
                p_fig.insert(0, ppr)
            if ppr.find('w:keepNext', NS) is None:
                ppr.insert(0, E.Element(q('w:keepNext')))
            ancla = p_fig
            for p in lw.find('.//wps:txbx/w:txbxContent', NS).findall('w:p', NS):
                pc = copy.deepcopy(p)
                ancla.addnext(pc)
                ancla = pc
            print(b, 'leyenda en párrafo')
        else:
            a2 = copy.deepcopy(cont)
            for eje, d in (('wp:positionH', lx), ('wp:positionV', ly)):
                po = a2.find(eje, NS).find('wp:posOffset', NS)
                if po is None:      # alineación (p. ej. derecha del margen): válida sólo si la leyenda calza con la figura
                    assert eje == 'wp:positionH' and lx == 0 and abs(lcx - cx) < 20000, (b, eje, lx, lcx, cx)
                    continue
                po.text = str(int(po.text) + d)
            a2.find('wp:extent', NS).set('cx', str(lcx))
            a2.find('wp:extent', NS).set('cy', str(lcy))
            a2.set('relativeHeight', str(int(a2.get('relativeHeight', '1')) + 1))
            a2.find('wp:docPr', NS).set('id', str(nuevo_id()))
            a2.find('wp:docPr', NS).set('name', f'Leyenda {nombre}')
            wsp = copy.deepcopy(lw)
            cnv = wsp.find('wps:cNvPr', NS)
            if cnv is not None:
                wsp.remove(cnv)
            x2 = wsp.find('wps:spPr/a:xfrm', NS)
            x2.find('a:off', NS).set('x', '0')
            x2.find('a:off', NS).set('y', '0')
            x2.find('a:ext', NS).set('cx', str(lcx))
            x2.find('a:ext', NS).set('cy', str(lcy))
            g2 = E.fromstring(f'<a:graphic xmlns:a="{NS["a"]}"><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"/></a:graphic>')
            g2[0].append(wsp)
            a2.replace(a2.find('a:graphic', NS), g2)
            r2 = E.Element(q('w:r'))
            E.SubElement(r2, q('w:drawing')).append(a2)
            dib.getparent().addnext(r2)
            print(b, 'leyenda en cuadro flotante')
    zout = zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        if it.filename == 'word/document.xml':
            zout.writestr(it, E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True))
        elif it.filename == 'word/_rels/document.xml.rels':
            zout.writestr(it, E.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True))
        elif it.filename == '[Content_Types].xml':
            zout.writestr(it, ct.encode('utf-8'))
        else:
            zout.writestr(it, zin.read(it.filename))
    for k, v in media.items():
        zout.writestr(k, v)
    zout.close()


if __name__ == '__main__':
    main(*sys.argv[1:])
