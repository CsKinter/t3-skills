"""Sólo lectura. Lista, por párrafo, el antes/después de los cambios con control de cambios y los comentarios de un .docx.

Uso: python cambios_revisor.py <archivo.docx> [autor]
No modifica el documento. Abre el .docx como zip, por lo que funciona aunque esté abierto en Word.
"""
import sys, zipfile
from lxml import etree as E

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'; N = {'w': W}; q = lambda t: '{%s}%s' % (W, t)
doc, autor = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else None)
z = zipfile.ZipFile(doc); root = E.fromstring(z.read('word/document.xml'))
TXT = lambda e: ''.join(e.xpath('.//w:t/text()', namespaces=N))


def vista(p, modo):
    out = []
    for el in p.iter(q('t'), q('delText')):
        if modo == 'antes' and any(a.tag == q('ins') for a in el.iterancestors()):
            continue
        if modo == 'despues' and el.tag == q('delText'):
            continue
        out.append(el.text or '')
    return ''.join(out)


def seccion(p):
    top = p
    while top.getparent() is not None and top.getparent().tag != q('body'):
        top = top.getparent()
    for prev in top.itersiblings(preceding=True):
        st = prev.xpath('./w:pPr/w:pStyle/@w:val', namespaces=N)
        if st and st[0].startswith('Heading'):
            return TXT(prev)
    return '?'


marcas = [x for x in root.xpath('.//w:ins|.//w:del', namespaces=N) if autor is None or x.get(q('author')) == autor]
parrafos = []
for x in marcas:
    p = next((a for a in x.iterancestors() if a.tag == q('p')), None)
    if p is not None and p not in parrafos:
        parrafos.append(p)
print(f'CAMBIOS: {len(marcas)} marcas en {len(parrafos)} párrafos')
for p in parrafos:
    f = sorted({x.get(q('date')) or '' for x in p.xpath('.//w:ins|.//w:del', namespaces=N)})
    tabla = ' | tabla' if any(a.tag == q('tbl') for a in p.iterancestors()) else ''
    print('=' * 80); print(f'{seccion(p)}{tabla} | {f[0]} – {f[-1]}')
    print('ANTES  :', vista(p, 'antes')); print('DESPUÉS:', vista(p, 'despues'))

if 'word/comments.xml' in z.namelist():
    c = E.fromstring(z.read('word/comments.xml'))
    hechos = {}
    if 'word/commentsExtended.xml' in z.namelist():
        W15 = 'http://schemas.microsoft.com/office/word/2012/wordml'
        for e in E.fromstring(z.read('word/commentsExtended.xml')):
            hechos[e.get('{%s}paraId' % W15)] = e.get('{%s}done' % W15)
    W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'
    print('\nCOMENTARIOS')
    for cm in c.findall('w:comment', N):
        if autor and cm.get(q('author')) != autor:
            continue
        i = cm.get(q('id')); pid = [p.get('{%s}paraId' % W14) for p in cm.findall('w:p', N)]
        ancla = []
        for p in root.iter(q('p')):
            if p.xpath('.//w:commentRangeStart[@w:id="%s"]' % i, namespaces=N) or ancla:
                dentro = bool(ancla)
                for el in p.iter():
                    if el.tag == q('commentRangeStart') and el.get(q('id')) == i: dentro = True
                    elif el.tag == q('commentRangeEnd') and el.get(q('id')) == i: dentro = False; break
                    elif dentro and el.tag == q('t'): ancla.append(el.text or '')
                if not dentro:
                    break
        estado = 'resuelto' if any(hechos.get(x) == '1' for x in pid) else 'abierto'
        print(f'{i} | {cm.get(q("author"))} | {cm.get(q("date"))} | {estado} | {TXT(cm)}')
        print('   ancla:', ''.join(ancla)[:200])
