"""Estilo de figuras de EE (tomado de la revisión 24 de Tiquel) y primitivas para dibujarlas en SVG.

Coordenadas en cm desde la esquina superior izquierda del dibujo, grosores en pt y tamaños de letra en pt, igual que
en Word. Las flechas se dibujan como polígonos (no marcadores) para que Word las muestre igual que un navegador.

    from estilo_ee import Lienzo
    L = Lienzo(16.2, 8.7); L.barra(...); L.guardar('fig.svg')
"""
import base64
import math
from pathlib import Path
from xml.sax.saxutils import escape

# Colores
AZUL = '0070C0'           # flujos, rótulos de flujo, barras sin restricción
AZUL_TITULO = '2E75B6'    # rótulos sobre capturas de PF
ROJO = 'C00000'           # zonas y recuadros sobre capturas, carga de BESS
ROJO_BARRA = 'EF3B2C'     # barras con restricción
NARANJO = 'FF5A00'        # sobrecarga y contingencias
VERDE_INY = '00B050'      # inyección
GRIS_TXT = '262626'
GRIS_SIMBOLO = '404040'
GRIS_MEDIO = '7F7F7F'
GRIS_NOTA = '7F858B'
POR_KV = {500: '1F3864', 220: '009244', 154: '990000', 66: 'D000D0'}
VERDE_220_ESQUEMA = '00A000'  # esquemas de Bulí (220 kV de Santa Sofía)

FUENTE = 'Cairo'
PT = 0.035278              # cm por punto
INTERLINEA = 1.2           # interlineado exacto de los cuadros de texto del informe
K = 100                    # unidades SVG por cm (décimas de mm)


def u(v):
    return f'{v * K:.2f}'


def _c(color):
    """'0070C0' o '0070C0@45' (opacidad %) → (#rrggbb, opacidad)."""
    if color is None:
        return 'none', 1
    c, _, a = color.partition('@')
    return '#' + c, (int(a) / 100 if a else 1)


class Lienzo:
    def __init__(self, ancho, alto):
        self.w, self.h = ancho, alto
        self.e = []
        self.defs = []

    # --- básicos -------------------------------------------------------------------------------------------------
    def _trazo(self, color, grosor, guion):
        c, a = _c(color)
        s = f'stroke="{c}" stroke-width="{u(grosor * PT)}"'
        if a < 1:
            s += f' stroke-opacity="{a}"'
        if guion:
            g = grosor * PT
            patron = {'dash': (4, 3), 'sysDash': (3, 1), 'sysDot': (1, 1), 'lgDash': (8, 3)}[guion]
            s += f' stroke-dasharray="{u(patron[0] * g)} {u(patron[1] * g)}"'
        return s

    def _relleno(self, color):
        c, a = _c(color)
        return f'fill="{c}"' + (f' fill-opacity="{a}"' if a < 1 else '')

    def linea(self, puntos, color, grosor=1.0, guion=None, fin=False, inicio=False, punta=None):
        """Polilínea. fin/inicio agregan punta de flecha triangular (tamaño Word «mediano» por defecto)."""
        pts = [tuple(p) for p in puntos]
        largo_punta = punta or max(grosor * PT * 3, 0.19)   # Word no achica la punta bajo ~0,19 cm
        a, b = list(pts), None
        if fin:
            pts[-1] = self._recorte(pts[-2], pts[-1], largo_punta * 0.9)
        if inicio:
            pts[0] = self._recorte(pts[1], pts[0], largo_punta * 0.9)
        d = ' '.join(f'{u(x)},{u(y)}' for x, y in pts)
        self.e.append(f'<polyline points="{d}" fill="none" {self._trazo(color, grosor, guion)} '
                      f'stroke-linejoin="round"/>')
        if fin:
            self._punta(a[-2], a[-1], color, grosor, largo_punta)
        if inicio:
            self._punta(a[1], a[0], color, grosor, largo_punta)
        return b

    @staticmethod
    def _recorte(p, q, d):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy) or 1
        return q[0] - dx / n * d, q[1] - dy / n * d

    def _punta(self, p, q, color, grosor, largo):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy) or 1
        ux, uy = dx / n, dy / n
        ancho = largo * 0.95
        bx, by = q[0] - ux * largo, q[1] - uy * largo
        pts = [q, (bx - uy * ancho / 2, by + ux * ancho / 2), (bx + uy * ancho / 2, by - ux * ancho / 2)]
        d = ' '.join(f'{u(x)},{u(y)}' for x, y in pts)
        self.e.append(f'<polygon points="{d}" {self._relleno(color)}/>')

    def rect(self, x, y, w, h, relleno=None, borde=None, grosor=0.75, guion=None, radio=0, sombra=False):
        r = f' rx="{u(radio)}"' if radio else ''
        t = self._trazo(borde, grosor, guion) if borde else 'stroke="none"'
        geom = f'<rect x="{u(x)}" y="{u(y)}" width="{u(w)}" height="{u(h)}"{r} '
        if sombra:
            self._sombra(geom)
        self.e.append(f'{geom}{self._relleno(relleno)} {t}/>')

    def elipse(self, cx, cy, rx, ry=None, relleno=None, borde=None, grosor=0.75, rot=0):
        t = self._trazo(borde, grosor, None) if borde else 'stroke="none"'
        tr = f' transform="rotate({rot} {u(cx)} {u(cy)})"' if rot else ''
        self.e.append(f'<ellipse cx="{u(cx)}" cy="{u(cy)}" rx="{u(rx)}" ry="{u((ry or rx))}" '
                      f'{self._relleno(relleno)} {t}{tr}/>')

    def poligono(self, puntos, relleno, borde=None, grosor=0.75, sombra=False):
        d = ' '.join(f'{u(x)},{u(y)}' for x, y in puntos)
        t = self._trazo(borde, grosor, None) if borde else 'stroke="none"'
        geom = f'<polygon points="{d}" '
        if sombra:
            self._sombra(geom)
        self.e.append(f'{geom}{self._relleno(relleno)} {t} stroke-linejoin="round"/>')

    def texto(self, x, y, lineas, pt=7, color=GRIS_TXT, negrita=False, alinear='center', cursiva=False):
        """Texto centrado verticalmente en y. lineas: str (con '\n') o lista. Cada línea puede ser
        [(trozo, {'b':1,'c':'0070C0'}), ...] para mezclar estilos."""
        if isinstance(lineas, str):
            lineas = lineas.split('\n')
        anchor = {'center': 'middle', 'left': 'start', 'right': 'end'}[alinear]
        alto = pt * PT * INTERLINEA
        y0 = y - alto * (len(lineas) - 1) / 2 + pt * PT * 0.36   # 0,36 em: centro de la altura de mayúsculas de Cairo
        for i, ln in enumerate(lineas):
            trozos = ln if isinstance(ln, list) else [(ln, {})]
            tsp = ''.join(
                f'<tspan{" font-weight=\"bold\"" if st.get("b") else ""}'
                f'{" fill=\"#" + st["c"] + "\"" if st.get("c") else ""}>{escape(t)}</tspan>' for t, st in trozos)
            self.e.append(
                f'<text x="{u(x)}" y="{u(y0 + i * alto)}" font-family="{FUENTE}" font-size="{u(pt * PT)}" '
                f'fill="#{color}" text-anchor="{anchor}"{" font-weight=\"bold\"" if negrita else ""}'
                f'{" font-style=\"italic\"" if cursiva else ""} xml:space="preserve">{tsp}</text>')

    def imagen(self, ruta, x, y, w, h, borde=None, grosor=1.0, recorte_px=None):
        """Imagen incrustada. recorte_px = [x0, y0, x1, y1] en px de la imagen original (se recorta con PIL; el SVG
        anidado con viewBox no es seguro en Word)."""
        if recorte_px:
            import io
            from PIL import Image
            buf = io.BytesIO()
            Image.open(ruta).crop(tuple(recorte_px)).save(buf, 'PNG')
            datos, tipo = base64.b64encode(buf.getvalue()).decode(), 'png'
        else:
            datos = base64.b64encode(Path(ruta).read_bytes()).decode()
            tipo = 'png' if str(ruta).lower().endswith('.png') else 'jpeg'
        self.e.append(f'<image x="{u(x)}" y="{u(y)}" width="{u(w)}" height="{u(h)}" preserveAspectRatio="none" '
                      f'href="data:image/{tipo};base64,{datos}"/>')
        if borde:
            self.rect(x + grosor * PT / 2, y + grosor * PT / 2, w - grosor * PT, h - grosor * PT, None, borde, grosor)

    def _sombra(self, geom, dy=0.03):
        """Sombra suave como capas negras semitransparentes con trazo decreciente, desplazadas hacia abajo.
        No usa filtros SVG: Word no dibuja ningún elemento que tenga un filtro (ni la forma ni la sombra)."""
        for ancho, opacidad in ((0.16, 0.035), (0.11, 0.045), (0.06, 0.06), (0.02, 0.08)):
            self.e.append(f'<g transform="translate(0 {u(dy)})">{geom}fill="#000" fill-opacity="{opacidad}" '
                          f'stroke="#000" stroke-opacity="{opacidad}" stroke-width="{u(ancho)}" '
                          f'stroke-linejoin="round"/></g>')

    # --- símbolos de esquema -------------------------------------------------------------------------------------
    def barra(self, x1, x2, y, color, grosor=4.0):
        self.linea([(x1, y), (x2, y)], color, grosor)

    def barra_v(self, x, y1, y2, color, grosor=2.9):
        self.linea([(x, y1), (x, y2)], color, grosor)

    def punto_abierto(self, x, y, color, lado=0.2, grosor=1.4):
        self.rect(x - lado / 2, y - lado / 2, lado, lado, 'FFFFFF', color, grosor)

    def trafo(self, x, y, color_alto, color_bajo, d=0.333, sep=0.155, grosor=1.3, relleno_alto=None):
        """Dos círculos solapados centrados en (x, y); el de arriba es el lado de alta."""
        self.elipse(x, y - sep / 2, d / 2, relleno=relleno_alto, borde=color_alto, grosor=grosor)
        self.elipse(x, y + sep / 2, d / 2, borde=color_bajo, grosor=grosor)

    def trafo_h(self, x, y, color_izq, color_der, d=0.34, sep=0.2, grosor=1.1):
        self.elipse(x - sep / 2, y, d / 2, relleno='FFFFFF', borde=color_izq, grosor=grosor)
        self.elipse(x + sep / 2, y, d / 2, borde=color_der, grosor=grosor)

    def eolica(self, x, y, escala=1.0, color=GRIS_SIMBOLO):
        """Aerogenerador con el buje en (x, y): tres aspas, buje y torre."""
        s = escala
        self.linea([(x, y), (x, y + 0.40 * s)], color, 1.4)
        for rot in (0, 120, 240):
            a = math.radians(rot)
            cx, cy = x + math.sin(a) * 0.139 * s, y - math.cos(a) * 0.139 * s
            self.elipse(cx, cy, 0.034 * s, 0.139 * s, relleno=color, rot=rot)
        self.elipse(x, y, 0.045 * s, relleno=color, borde=color, grosor=0.5)

    def eolica_linea(self, x, y, color=GRIS_TXT):
        """Aerogenerador de trazo (esquemas de 500 kV): torre y tres aspas desde (x, y)."""
        self.linea([(x, y - 0.26), (x, y + 0.4)], color, 1.1)
        self.linea([(x, y), (x + 0.225, y + 0.13)], color, 1.1)
        self.linea([(x, y), (x - 0.225, y + 0.13)], color, 1.1)
        self.elipse(x, y, 0.035, relleno=color, borde=color, grosor=0.5)

    def pfv(self, x, y, color=GRIS_SIMBOLO):
        """Panel fotovoltaico con su centro superior en (x, y) y el pie hacia abajo."""
        self.poligono([(x - 0.278, y), (x + 0.278, y), (x + 0.378, y + 0.333), (x - 0.378, y + 0.333)], color,
                      color, 0.6)
        self.linea([(x - 0.323, y + 0.166), (x + 0.323, y + 0.166)], 'FFFFFF', 0.55)
        self.linea([(x - 0.106, y + 0.011), (x - 0.139, y + 0.322)], 'FFFFFF', 0.55)
        self.linea([(x + 0.106, y + 0.011), (x + 0.139, y + 0.322)], 'FFFFFF', 0.55)
        self.linea([(x - 0.189, y + 0.333), (x - 0.189, y + 0.522)], color, 0.9)
        self.linea([(x + 0.189, y + 0.333), (x + 0.189, y + 0.522)], color, 0.9)
        self.linea([(x - 0.278, y + 0.522), (x + 0.278, y + 0.522)], color, 0.9)

    def bess(self, x, y, color=GRIS_SIMBOLO, carga='70AD47'):
        """Batería con su centro superior (borne) en (x, y)."""
        self.rect(x - 0.067, y, 0.133, 0.067, color)
        self.rect(x - 0.167, y + 0.067, 0.333, 0.422, 'FFFFFF', color, 1.2)
        self.rect(x - 0.111, y + 0.256, 0.222, 0.178, carga)

    def sol(self, x, y, r=0.145):
        for k in range(8):
            a = math.radians(k * 45)
            self.linea([(x + math.cos(a) * 0.2, y + math.sin(a) * 0.2), (x + math.cos(a) * 0.3, y + math.sin(a) * 0.3)],
                       'F2A900', 1.3)
        self.elipse(x, y, r, relleno='FFC000', borde='F2A900', grosor=0.5)

    def flechita(self, x, y, sube, color, largo=0.244):
        """Flecha corta de inyección (sube, verde) o carga (baja, roja), con el centro en (x, y)."""
        a, b = (y + largo / 2, y - largo / 2) if sube else (y - largo / 2, y + largo / 2)
        self.linea([(x, a), (x, b)], color, 1.6, fin=True, punta=0.2)

    def contingencia(self, x, y, d=0.38, color=NARANJO):
        self.elipse(x, y, d / 2, relleno='FFFFFF', borde=color, grosor=1.6)
        k = d / 2 * 0.685
        self.linea([(x - k, y - k), (x + k, y + k)], color, 1.6)

    def rotulo(self, x, y, w, h, lineas, color=AZUL, pt=7, borde='0070C0@45', grosor=0.6, radio=0.08, relleno='FFFFFF',
               guion=None):
        """Cuadro de valor: rectángulo redondeado blanco con texto en negrita centrado."""
        self.rect(x, y, w, h, relleno, borde, grosor, guion, radio)
        if lineas:
            self.texto(x + w / 2, y + h / 2, lineas, pt, color, True)

    def etiqueta_captura(self, x, y, w, h, texto, color=AZUL_TITULO, pt=9):
        """Etiqueta sobre una captura de PF: fondo blanco, sin borde, sombra suave, negrita."""
        self.rect(x, y, w, h, 'FFFFFF', None, radio=0.12, sombra=True)
        self.texto(x + w / 2, y + h / 2, texto, pt, color, True)

    def flecha_bloque(self, x, y, w, h, direccion='arriba', color=AZUL, sombra=True, texto=None, pt=9):
        """Flecha gruesa (upArrow/rightArrow de Word) dentro de la caja x, y, w, h, con texto blanco en negrita
        opcional en el cuerpo («+21 MW hacia Las Delicias (220 kV)»)."""
        vertical = direccion in ('arriba', 'abajo')
        largo, ancho = (h, w) if vertical else (w, h)
        cab = min(largo * 0.31, ancho * 0.88)   # proporción aprobada en la 5-1 (29-10-2026)
        # flecha hacia «adelante» en coordenadas locales (s a lo largo desde la punta, t a lo ancho desde el centro)
        local = [(0, 0), (cab, ancho / 2), (cab, ancho / 4), (largo, ancho / 4), (largo, -ancho / 4), (cab, -ancho / 4),
                 (cab, -ancho / 2)]
        m = {'arriba': lambda s, t: (x + w / 2 + t, y + s), 'abajo': lambda s, t: (x + w / 2 + t, y + h - s),
             'derecha': lambda s, t: (x + w - s, y + h / 2 + t), 'izquierda': lambda s, t: (x + s, y + h / 2 + t)}
        self.poligono([m[direccion](s, t) for s, t in local], color, color, 1.0, sombra)
        if texto:
            centro = m[direccion]((cab + largo) / 2, 0)
            self.texto(*centro, texto, pt, 'FFFFFF', True)

    def zona(self, x, y, w, h, texto=None, pt=9):
        """Zona destacada: rojo translúcido con borde punteado; etiqueta dentro, arriba a la derecha."""
        self.rect(x, y, w, h, 'C00000@18', ROJO, 1.5, 'dash')
        if texto:
            self.texto(x + w - 0.15, y + pt * PT * 0.9, texto, pt, ROJO, True, 'right')

    # --- salida --------------------------------------------------------------------------------------------------
    def svg(self):
        defs = f'<defs>{"".join(self.defs)}</defs>' if self.defs else ''
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w * 10:.3f}mm" height="{self.h * 10:.3f}mm" '
                f'viewBox="0 0 {u(self.w)} {u(self.h)}">{defs}' + '\n'.join(self.e) + '</svg>')

    def guardar(self, ruta):
        Path(ruta).write_text(self.svg(), encoding='utf-8')
        return ruta
