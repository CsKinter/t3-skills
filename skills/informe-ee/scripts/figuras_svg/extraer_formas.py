"""Vuelca las formas DrawingML de un dibujo de Word a JSON: posición absoluta en cm dentro del dibujo, geometría,
relleno, línea, texto y fuente. Sirve para leer cómo está hecha una figura original, no para editarla.

    python extraer_formas.py document.xml <bloque> salida.json
"""
import json
import sys

from lxml import etree

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
    'wpc': 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
CM = 360000


def q(t):
    p, n = t.split(':')
    return '{%s}%s' % (NS[p], n)


def col(e):
    if e is None:
        return None
    s = e.find('a:srgbClr', NS)
    if s is not None:
        a = s.find('a:alpha', NS)
        return s.get('val') + (f'@{int(a.get("val")) // 1000}' if a is not None else '')
    s = e.find('a:schemeClr', NS)
    return 'scheme:' + s.get('val') if s is not None else None


def xf(e):
    x = e.find('a:xfrm', NS) if e is not None else None
    if x is None:
        return None
    o, ex = x.find('a:off', NS), x.find('a:ext', NS)
    r = dict(x=int(o.get('x')), y=int(o.get('y')), w=int(ex.get('cx')), h=int(ex.get('cy')),
             rot=int(x.get('rot', '0')) / 60000, fh=x.get('flipH') == '1', fv=x.get('flipV') == '1')
    co, ce = x.find('a:chOff', NS), x.find('a:chExt', NS)
    if co is not None:
        r.update(cx=int(co.get('x')), cy=int(co.get('y')), cw=int(ce.get('cx')), ch=int(ce.get('cy')))
    return r


def texto(sp):
    tx = sp.find('.//wps:txbx', NS)
    if tx is None:
        return None
    pars = []
    for p in tx.iter(q('w:p')):
        runs = []
        for r in p.iter(q('w:r')):
            t = ''.join(x.text or '' for x in r.iter(q('w:t')))
            if not t:
                continue
            rp, st = r.find('w:rPr', NS), {}
            if rp is not None:
                b = rp.find('w:b', NS)
                if b is not None and b.get(q('w:val'), '1') not in ('0', 'false'):
                    st['b'] = 1
                if rp.find('w:i', NS) is not None:
                    st['i'] = 1
                c = rp.find('w:color', NS)
                if c is not None:
                    st['c'] = c.get(q('w:val'))
                s = rp.find('w:sz', NS)
                if s is not None:
                    st['pt'] = int(s.get(q('w:val'))) / 2
                f = rp.find('w:rFonts', NS)
                if f is not None and f.get(q('w:ascii')):
                    st['f'] = f.get(q('w:ascii'))
            runs.append([t, st])
        jc = p.find('w:pPr/w:jc', NS)
        pars.append(dict(jc=jc.get(q('w:val')) if jc is not None else None, runs=runs))
    return pars


def forma(sp, T, out):
    pr = sp.find('wps:spPr', NS) if sp.tag == q('wps:wsp') else sp.find('pic:spPr', NS)
    g = xf(pr)
    if g is None:
        return
    x, y = T(g['x'], g['y'])
    x2, y2 = T(g['x'] + g['w'], g['y'] + g['h'])
    d = dict(x=round(x / CM, 3), y=round(y / CM, 3), w=round((x2 - x) / CM, 3), h=round((y2 - y) / CM, 3))
    if g['rot']:
        d['rot'] = g['rot']
    if g['fh']:
        d['flipH'] = 1
    if g['fv']:
        d['flipV'] = 1
    pg = pr.find('a:prstGeom', NS)
    d['geom'] = pg.get('prst') if pg is not None else ('custom' if pr.find('a:custGeom', NS) is not None else None)
    f = pr.find('a:solidFill', NS)
    d['fill'] = col(f) if f is not None else None
    ln = pr.find('a:ln', NS)
    if ln is not None and ln.find('a:noFill', NS) is None:
        d['ln'] = col(ln.find('a:solidFill', NS))
        d['lw'] = round(int(ln.get('w', '12700')) / 12700, 2)
        pd = ln.find('a:prstDash', NS)
        if pd is not None and pd.get('val') != 'solid':
            d['dash'] = pd.get('val')
        for k in ('headEnd', 'tailEnd'):
            h = ln.find('a:' + k, NS)
            if h is not None and h.get('type', 'none') != 'none':
                d[k] = h.get('type')
    sh = pr.find('.//a:outerShdw', NS)
    if sh is not None:
        d['sombra'] = {k: sh.get(k) for k in ('blurRad', 'dist', 'dir')} | {'c': col(sh)}
    if d['geom'] == 'custom':
        pth = pr.find('.//a:path', NS)
        pts = [(int(p.get('x')), int(p.get('y'))) for p in pr.iter(q('a:pt'))]
        if pth is not None and pts:
            d['path'] = dict(w=int(pth.get('w', 0)), h=int(pth.get('h', 0)), pts=pts)
    if sp.tag == q('pic:pic'):
        d['geom'] = 'pic'
        d['blip'] = sp.find('.//a:blip', NS).get(q('r:embed'))
        sr = sp.find('.//a:srcRect', NS)
        if sr is not None:
            d['srcRect'] = {k: int(v) for k, v in sr.attrib.items()}
    t = texto(sp)
    if t:
        d['txt'] = t
        bp = sp.find('wps:bodyPr', NS)
        if bp is not None:
            d['body'] = {k: bp.get(k) for k in ('lIns', 'tIns', 'rIns', 'bIns', 'anchor', 'wrap', 'vert') if bp.get(k)}
    out.append(d)


def recorrer(node, T, out):
    for ch in node:
        if ch.tag in (q('wps:wsp'), q('pic:pic')):
            forma(ch, T, out)
        elif ch.tag == q('wpg:grpSp'):
            g = xf(ch.find('wpg:grpSpPr', NS))

            def T2(x, y, g=g, T=T):
                sx = g['w'] / g['cw'] if g['cw'] else 1
                sy = g['h'] / g['ch'] if g['ch'] else 1
                return T(g['x'] + (x - g['cx']) * sx, g['y'] + (y - g['cy']) * sy)
            recorrer(ch, T2, out)


def main(docxml, bloque, salida):
    b = list(etree.parse(docxml).getroot()[0])[int(bloque)]
    res = []
    for d in b.iter(q('wp:anchor'), q('wp:inline')):
        if any(etree.QName(a).localname in ('Fallback', 'anchor', 'inline') for a in d.iterancestors()):
            continue
        ext = d.find('wp:extent', NS)
        info = dict(tipo=etree.QName(d).localname, nombre=d.find('wp:docPr', NS).get('name'),
                    w=int(ext.get('cx')) / CM, h=int(ext.get('cy')) / CM)
        if info['tipo'] == 'anchor':
            for k in ('positionH', 'positionV'):
                p = d.find('wp:' + k, NS)
                off = p.find('wp:posOffset', NS)
                info[k] = dict(rel=p.get('relativeFrom'),
                               off=int(off.text) / CM if off is not None else p.find('wp:align', NS).text)
            info['wrap'] = [etree.QName(c).localname for c in d if etree.QName(c).localname.startswith('wrap')]
        top = d.find('a:graphic/a:graphicData', NS)[0]
        out = []
        if top.tag == q('wpg:wgp'):
            g = xf(top.find('wpg:grpSpPr', NS))
            T = (lambda x, y, g=g: ((x - g['cx']) * g['w'] / g['cw'], (y - g['cy']) * g['h'] / g['ch'])) \
                if g and 'cw' in g else (lambda x, y: (x, y))
            recorrer(top, T, out)
        elif top.tag == q('wpc:wpc'):
            recorrer(top, lambda x, y: (x, y), out)
        else:
            forma(top, lambda x, y: (x, y), out)
        info['formas'] = out
        res.append(info)
    json.dump(res, open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for r in res:
        print(r['tipo'], r['nombre'], round(r['w'], 2), round(r['h'], 2), len(r['formas']), 'formas')


if __name__ == '__main__':
    main(*sys.argv[1:])
