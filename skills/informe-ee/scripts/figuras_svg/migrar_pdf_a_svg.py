"""Convierte cada página del PDF de figuras (una por figura) en fig_<bloque>.svg + .png para insertar_svg.py."""
import json, re, sys
import pymupdf
pdf, info_json, salida = sys.argv[1:4]
info = json.load(open(info_json))
d = pymupdf.open(pdf)
for b, f in info.items():
    pg = d[f['pagina'] - 1]
    W, H = f['cx'] / 12700, f['alto'] / 12700           # pt
    assert abs(pg.rect.width - W) < 1.5 and abs(pg.rect.height - H) < 1.5, (b, pg.rect, W, H)
    svg = pg.get_svg_image(text_as_path=False)
    mm = lambda pt: pt * 25.4 / 72
    svg = re.sub(r'<svg([^>]*?) width="[^"]*" height="[^"]*"', lambda m: f'<svg{m.group(1)} width="{mm(pg.rect.width):.3f}mm" height="{mm(pg.rect.height):.3f}mm"', svg, count=1)
    open(f'{salida}/fig_{b}.svg', 'w', encoding='utf-8').write(svg)
    pg.get_pixmap(dpi=96, alpha=False).save(f'{salida}/fig_{b}.png')
    print(b, f'{pg.rect.width:.1f}x{pg.rect.height:.1f} pt', len(svg) // 1024, 'KB svg')
