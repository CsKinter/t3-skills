"""SVG → PNG con Edge sin ventana (usa las fuentes instaladas, Cairo incluida). Sirve de vista previa y de respaldo PNG.

    python vista_previa.py fig.svg [fig.png] [escala]
"""
import re, subprocess, sys, tempfile
from pathlib import Path
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

def png(svg, salida=None, escala=3):
    svg = Path(svg).resolve(); salida = Path(salida or svg.with_suffix('.png')).resolve()
    t = svg.read_text(encoding='utf-8')
    w, h = (float(x) for x in re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', t).groups())
    wp, hp = round(w / 25.4 * 96), round(h / 25.4 * 96)
    html = Path(tempfile.gettempdir()) / (svg.stem + '_vista.html')
    html.write_text(f'<html><body style="margin:0;background:#fff"><img src="{svg.as_uri()}" '
                    f'style="display:block;width:{wp}px;height:{hp}px"></body></html>', encoding='utf-8')
    with tempfile.TemporaryDirectory() as perfil:
        subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--user-data-dir={perfil}',
                        f'--force-device-scale-factor={escala}', f'--window-size={wp},{hp}',
                        f'--screenshot={salida}', html.as_uri()], check=True, capture_output=True, timeout=60)
    return salida

if __name__ == '__main__':
    print(png(sys.argv[1], *(sys.argv[2:3] or [None]), *(float(x) for x in sys.argv[3:4])))
