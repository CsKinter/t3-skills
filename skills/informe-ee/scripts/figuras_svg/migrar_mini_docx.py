"""Arma un docx con una sección por figura (página del tamaño de la figura, márgenes 0, dibujo anclado en (0,0)),
para que Word renderice cada grupo DrawingML tal como en el informe. Sólo lectura del docx de origen.
    python mini_docx.py fuente.docx salida.docx bloques.json [bloque ...]
"""
import copy, json, sys, zipfile
from lxml import etree as E
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
      'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
      'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'}
q = lambda t: '{%s}%s' % (NS[t.split(':')[0]], t.split(':')[1])
W = NS['w']
EMU_TW = 635

def es_leyenda(el):
    return 'SEQ Figura' in ''.join(t.text or '' for t in el.iter(q('w:instrText')))

def bbox_hijo(c):
    xf = c.find('.//a:xfrm', NS) if c.tag != q('wpg:grpSp') else c.find('wpg:grpSpPr/a:xfrm', NS)
    o, e = xf.find('a:off', NS), xf.find('a:ext', NS)
    return int(o.get('x')), int(o.get('y')), int(e.get('cx')), int(e.get('cy'))

def main(fuente, salida, info_json, *bloques):
    zin = zipfile.ZipFile(fuente)
    doc = E.fromstring(zin.read('word/document.xml'))
    body = doc.find(q('w:body'))
    blq = list(body)
    nuevo = []
    info = {}
    for k, b in enumerate(map(int, bloques)):
        bl = copy.deepcopy(blq[b])
        for ac in list(bl.iter(q('mc:AlternateContent'))):
            if list(ac.iter(q('wpg:wgp'))):
                ac.getparent().replace(ac, ac.find('mc:Choice', NS)[0])
        dib = [d for d in bl.iter(q('w:drawing')) if list(d.iter(q('wpg:wgp')))][0]
        cont = dib[0]                       # wp:inline o wp:anchor
        grupo = next(dib.iter(q('wpg:wgp')))
        xf = grupo.find('wpg:grpSpPr/a:xfrm', NS)
        ext = xf.find('a:ext', NS); chext = xf.find('a:chExt', NS); choff = xf.find('a:chOff', NS)
        cx, cy = int(ext.get('cx')), int(ext.get('cy'))
        sy = cy / int(chext.get('cy'))
        hijos = [c for c in grupo if c.tag in (q('wps:wsp'), q('pic:pic'), q('wpg:grpSp'))]
        ley = [c for c in hijos if es_leyenda(c)]
        alto = cy
        if ley:
            for c in ley: grupo.remove(c)
            fondo = max(bbox_hijo(c)[1] + bbox_hijo(c)[3] for c in hijos if c not in ley)
            alto = min(cy, round((fondo - int(choff.get('y'))) * sy))
        # Campos dentro del dibujo (p. ej. REF a una tabla): se congelan con su resultado actual, porque los marcadores
        # no existen en este docx y Word escribiría «¡Error! Origen de la referencia no encontrado».
        for p in grupo.iter(q('w:p')):
            estado = None
            for r in list(p.iter(q('w:r'))):
                fc = r.find(q('w:fldChar'))
                if fc is not None:
                    estado = {'begin': 'codigo', 'separate': 'resultado', 'end': None}[fc.get(q('w:fldCharType'))]
                    r.getparent().remove(r)
                elif estado == 'codigo' or r.find(q('w:instrText')) is not None:
                    r.getparent().remove(r)
            for fs in list(p.iter(q('w:fldSimple'))):
                for c in list(fs):
                    fs.addprevious(c)
                fs.getparent().remove(fs)
        info[b] = dict(cx=cx, cy=cy, alto=alto, leyenda_en_grupo=bool(ley), pagina=k + 1)
        grafico = cont.find('a:graphic', NS)
        docpr = cont.find('wp:docPr', NS)
        anc = E.fromstring(f'''<wp:anchor xmlns:wp="{NS['wp']}" distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="1" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">
<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>
<wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV><wp:extent cx="{cx}" cy="{cy}"/>
<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/><wp:docPr id="{5000 + k}" name="fig{b}"/><wp:cNvGraphicFramePr/></wp:anchor>''')
        anc.append(copy.deepcopy(grafico))
        p = E.SubElement(E.Element(q('w:body')), q('w:p'))
        ppr = E.SubElement(p, q('w:pPr'))
        E.SubElement(ppr, q('w:spacing'), {q('w:before'): '0', q('w:after'): '0', q('w:line'): '240', q('w:lineRule'): 'auto'})
        r = E.SubElement(p, q('w:r')); rpr = E.SubElement(r, q('w:rPr')); E.SubElement(rpr, q('w:sz'), {q('w:val'): '2'})
        d = E.SubElement(r, q('w:drawing')); d.append(anc)
        sect = E.Element(q('w:sectPr'))
        E.SubElement(sect, q('w:type'), {q('w:val'): 'nextPage'})
        E.SubElement(sect, q('w:pgSz'), {q('w:w'): str(round(cx / EMU_TW)), q('w:h'): str(max(round(alto / EMU_TW), 200))})
        E.SubElement(sect, q('w:pgMar'), {q('w:' + x): '0' for x in ('top', 'right', 'bottom', 'left', 'header', 'footer', 'gutter')})
        nuevo.append((p, sect))
    for c in list(body): body.remove(c)
    for i, (p, sect) in enumerate(nuevo):
        if i < len(nuevo) - 1:
            p.find(q('w:pPr')).append(sect)
            body.append(p)
        else:
            body.append(p); body.append(sect)
    zout = zipfile.ZipFile(salida, 'w', zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        if it.filename == 'word/document.xml':
            zout.writestr(it, E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True))
        else:
            zout.writestr(it, zin.read(it.filename))
    zout.close()
    json.dump(info, open(info_json, 'w'), indent=1)
    print(len(nuevo), 'figuras')

if __name__ == '__main__':
    main(*sys.argv[1:])
