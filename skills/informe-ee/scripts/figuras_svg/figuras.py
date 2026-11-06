"""Dibuja una figura del informe desde su spec JSON (specs/fig_*.json) a SVG con el estilo de estilo_ee.

    python figuras.py specs/fig_6-1.json salida/          → salida/fig_6-1.svg

Tipos de spec: «esquema» (lista de elementos), «barras_divergentes» (despacho por central) y «recorte_pf» (captura
de PowerFactory con anotaciones: flecha, etiqueta, zona, contingencia, peor). Coordenadas en cm desde la esquina superior izquierda del dibujo, sin la leyenda:
la leyenda queda nativa en Word para conservar la numeración y las referencias cruzadas.
"""
import json
import sys
from pathlib import Path

import estilo_ee as E

AQUI = Path(__file__).resolve().parent


def _radio(w, h):
    return 0.16667 * min(w, h)          # roundRect de Word con su ajuste por defecto


def esquema(spec):
    L = E.Lienzo(spec['ancho'], spec['alto'])
    kv = {**E.POR_KV, **{int(k): v for k, v in spec.get('colores_kv', {}).items()}}

    def color(el, defecto=E.GRIS_TXT):
        if 'color' in el:
            return el['color']
        return kv[el['kv']] if 'kv' in el else defecto

    for el in spec['elementos']:
        if 'linea' in el:
            L.linea(el['linea'], color(el), el.get('grosor', 1.0), el.get('guion'), el.get('fin', False),
                    el.get('inicio', False))
        elif 'barra' in el:
            x1, x2, y = el['barra']
            L.barra(x1, x2, y, color(el), el.get('grosor', 4.0))
        elif 'barra_v' in el:
            x, y1, y2 = el['barra_v']
            L.barra_v(x, y1, y2, color(el), el.get('grosor', 2.9))
        elif 'abierto' in el:
            L.punto_abierto(*el['abierto'], color(el))
        elif 'trafo' in el:
            alto, bajo = el['kv']
            L.trafo(*el['trafo'], kv[alto], kv[bajo], el.get('d', 0.333), el.get('sep', 0.156),
                    el.get('grosor', 1.3), el.get('relleno_alto'))
        elif 'trafo_bajada' in el:
            # Trafo entre una barra alta y una baja en la misma vertical: x, y_alta, y_baja, y_centro.
            x, ya, yb, yc = el['trafo_bajada']
            alto, bajo = el['kv']
            d, sep, gl = el.get('d', 0.333), el.get('sep', 0.156), el.get('grosor_linea', 1.6)
            L.linea([(x, ya), (x, yc - sep / 2 - d / 2)], kv[alto], gl)
            L.linea([(x, yc + sep / 2 + d / 2), (x, yb)], kv[bajo], gl)
            L.trafo(x, yc, kv[alto], kv[bajo], d, sep, el.get('grosor', 1.3), el.get('relleno_alto'))
        elif 'trafo_h' in el:
            izq, der = el['kv']
            L.trafo_h(*el['trafo_h'], kv[izq], kv[der])
        elif 'eolica' in el:
            L.eolica(*el['eolica'])
        elif 'eolica_linea' in el:
            L.eolica_linea(*el['eolica_linea'])
        elif 'pfv' in el:
            L.pfv(*el['pfv'])
        elif 'bess' in el:
            L.bess(*el['bess'])
        elif 'sol' in el:
            L.sol(*el['sol'])
        elif 'inyeccion' in el:
            L.flechita(*el['inyeccion'], sube=False, color=E.VERDE_INY)
        elif 'carga' in el:
            L.flechita(*el['carga'], sube=True, color=E.ROJO)
        elif 'flujo' in el:
            L.linea(el['flujo'], el.get('color', E.AZUL), el.get('grosor', 1.9), fin=True)
        elif 'contingencia' in el:
            L.contingencia(*el['contingencia'], el.get('d', 0.38))
            if 't' in el:
                x, y = el['contingencia']
                L.texto(x - 0.27, y, el['t'], el.get('pt', 7.5), E.NARANJO, True, 'right')
        elif 'rotulo' in el:
            x, y, w, h = el['rotulo']
            L.rotulo(x, y, w, h, el['t'], el.get('color', E.AZUL), el.get('pt', 7), el.get('borde', '0070C0@45'),
                     el.get('grosor', 0.6), el.get('radio', _radio(w, h)), el.get('relleno', 'FFFFFF'),
                     el.get('guion'))
        elif 'etiqueta_linea' in el:
            # Texto sobre una línea, con fondo blanco que la interrumpe. Centro x, y; ancho y alto del fondo.
            x, y, w, h = el['etiqueta_linea']
            L.rect(x - w / 2, y - h / 2, w, h, 'FFFFFF')
            L.texto(x, y, el['t'], el.get('pt', 6.5), el.get('color', E.GRIS_TXT), True)
        elif 'caja' in el:
            x, y, w, h = el['caja']
            L.rect(x, y, w, h, el.get('relleno'), el.get('borde'), el.get('grosor', 0.75), el.get('guion'),
                   el.get('radio', 0))
        elif 'circulo' in el:
            x, y, r = el['circulo']
            L.elipse(x, y, r, relleno=el.get('relleno'), borde=el.get('borde'), grosor=el.get('grosor', 0.75))
        elif 'texto' in el:
            L.texto(*el['texto'], el['t'], el.get('pt', 7), el.get('color', E.GRIS_TXT), el.get('b', False),
                    el.get('al', 'center'))
        else:
            raise ValueError(f'Elemento desconocido: {el}')
    return L


def barras_divergentes(spec):
    """Despacho por central: barra con contorno punteado = sin restricción, barra llena = con restricción.
    Inyección a la derecha (azul), carga a la izquierda (roja)."""
    L = E.Lienzo(spec['ancho'], spec['alto'])
    g = spec['geometria']
    x0, esc = g['eje_x'], g['cm_por_mw']
    lim = spec['escala_mw']
    L.texto(0.05, g['y_titulo'], spec['titulo'], 8, E.GRIS_TXT, True, 'left')
    L.texto(x0 - 0.793, g['y_sentidos'], 'Carga ←', 7, '595959', False, 'right')
    L.texto(x0 + 0.516, g['y_sentidos'], '→ Inyección', 7, '595959', False, 'left')
    L.texto(x0, g['y_sentidos'], '0', 7.5, E.GRIS_TXT, True)
    L.texto(x0 - lim * esc, g['y_escala'], f'-{lim}', 6.5, E.GRIS_MEDIO)
    L.texto(x0 + lim * esc, g['y_escala'], f'{lim}', 6.5, E.GRIS_MEDIO)
    y = g['y_primera']
    for c in spec['centrales']:
        sin, con = c['sin'], c['con']
        L.texto(g['x_nombres'], y + g['alto_barra'] / 2 + g.get('dy_nombre', 0), c['nombre'], 7.5, E.GRIS_TXT, False,
                'right')
        xs = sorted((x0, x0 + sin * esc))
        xc = sorted((x0, x0 + con * esc))
        L.rect(xs[0], y, xs[1] - xs[0], g['alto_barra'], None, E.GRIS_MEDIO, 0.8, 'dash')
        L.rect(xc[0], y, xc[1] - xc[0], g['alto_barra'], E.AZUL if con >= 0 else E.ROJO_BARRA)
        txt = f'{abs(con)} de {abs(sin)}'
        yt = y + g['alto_barra'] + g['dy_valor']
        if con >= 0:
            L.texto(x0 + 0.13, yt, txt, 7, E.GRIS_TXT, True, 'left')
        else:
            L.texto(x0 - 0.13, yt, txt, 7, E.GRIS_TXT, True, 'right')
        y += g['paso']
    L.linea([(x0, g['eje_y'][0]), (x0, g['eje_y'][1])], E.GRIS_MEDIO, 0.75)
    return L


def recorte_pf(spec, base):
    L = E.Lienzo(spec['ancho'], spec['alto'])
    im = spec['imagen']
    L.imagen(base / im['archivo'], 0, 0, spec['ancho'], spec['alto'], im.get('borde'), im.get('grosor', 1.0),
             im.get('recorte_px'))
    for a in spec['anotaciones']:
        if a['tipo'] == 'flecha':
            L.flecha_bloque(*a['caja'], a.get('direccion', 'arriba'), a.get('color', E.AZUL), True, a.get('t'),
                            a.get('pt', 9))
        elif a['tipo'] == 'etiqueta':
            L.etiqueta_captura(*a['caja'], a['t'], a.get('color', E.AZUL_TITULO), a.get('pt', 9))
        elif a['tipo'] == 'zona':
            L.zona(*a['caja'], a.get('t'), a.get('pt', 9))
        elif a['tipo'] == 'contingencia':
            L.contingencia(*a['centro'], a.get('d', 0.5))
        elif a['tipo'] == 'peor':
            x, y, w, h = a['caja']
            L.rect(x, y, w, h, None, E.ROJO, 2.0)
        else:
            raise ValueError(a)
    return L


def dibujar(ruta_spec, salida):
    ruta_spec = Path(ruta_spec)
    spec = json.loads(ruta_spec.read_text(encoding='utf-8'))
    tipo = spec['tipo']
    if tipo == 'esquema':
        L = esquema(spec)
    elif tipo == 'barras_divergentes':
        L = barras_divergentes(spec)
    elif tipo == 'recorte_pf':
        L = recorte_pf(spec, ruta_spec.parent)
    else:
        raise ValueError(tipo)
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    return L.guardar(salida / (ruta_spec.stem + '.svg'))


if __name__ == '__main__':
    for r in sys.argv[1:-1]:
        print(dibujar(r, sys.argv[-1]))
