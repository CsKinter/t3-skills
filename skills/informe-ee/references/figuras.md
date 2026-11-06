# Figuras del informe (preferencias de Vicente, verificadas en el informe de Cumbres del Ñuble)

Referencia de estilo: informe de Entre Ríos / Entre Valles RB. Desde el 29-10-2026 (fase 4 del plan de uso, prototipo
aprobado) las figuras se dibujan en **SVG desde una spec JSON** y se insertan como imagen SVG con respaldo PNG. Ya no se
arman objeto por objeto en DrawingML: Vicente casi no las edita, y si quiere hacerlo, clic derecho → «Convertir en
forma» las vuelve objetos de Word. Las figuras antiguas hechas con grupos se migran con el flujo «Migrar figuras
antiguas» (más abajo), que no las redibuja.

## Flujo (scripts en `scripts/figuras_svg/`)

1. Spec `fig_<n>.json` junto al estudio (en cm, sin la leyenda). Tipos: `esquema` (lista de elementos: barra, línea,
   trafo, eólica, PFV, BESS, flujo, rótulo, contingencia, texto…), `barras_divergentes` (despacho por central) y
   `recorte_pf` (captura de PF + anotaciones). Ejemplos aprobados:
   `Cumbres del Ñuble\.revision_diagrama\prototipo_figuras_svg_2910\specs\` (5-1, 6-1, 6-3, 7-10).
2. `python figuras.py spec.json salida/` → SVG. `python vista_previa.py salida/fig.svg` → PNG con Edge (usa las fuentes
   instaladas, Cairo incluida). Iterar mirando sólo ese PNG, no el Word.
3. `python insertar_svg.py origen.docx destino.docx <bloque>=salida/fig_<n> …` cambia las formas del dibujo por la
   imagen SVG + PNG y **conserva la leyenda nativa** (cuadro de texto con campo SEQ dentro del grupo, o párrafo aparte).
   Necesita el `.png` de respaldo junto al `.svg`. Quita el `mc:AlternateContent` del dibujo.
4. Renderizar el Word una vez al final. Para juzgar el parecido basta el PNG de Edge: Vicente comprobó el 29-10 que
   Word dibuja el SVG igual, salvo lo de la tabla siguiente.
5. Para escribir la spec de una figura existente: `extraer_formas.py` (formas a JSON en cm) y `textos.py` (anclas de
   texto según alineación).

## Migrar figuras antiguas (grupos de formas) a SVG sin redibujarlas

Verificado en la R28 de Cumbres (03-11-2026): 57 figuras, 8.158 formas → 47; `document.xml` 28,4 → 7,9 MB. Es el
render del propio Word, así que el resultado es idéntico (sólo difiere el antialiasing).

1. `python migrar_mini_docx.py informe.docx figs.docx figs.json <bloque> …` → un docx con una sección por figura
   (página del tamaño del grupo, márgenes 0, dibujo anclado en (0,0), sin la leyenda). **Congela los campos** del
   dibujo (REF a tablas/figuras); si no, Word graba «¡Error! Origen de la referencia no encontrado» en el SVG.
2. `exportar_pdf.ps1 -Docs figs.docx` (Word propio, PID verificado, sin guardar) → `figs.pdf`.
3. `python migrar_pdf_a_svg.py figs.pdf figs.json carpeta` → `fig_<bloque>.svg` (texto como texto) + PNG 96 dpi.
4. `python insertar_plano.py informe.docx salida.docx figs.json carpeta` → **imagen simple, sin grupo**. Leyenda
   dentro de un grupo en línea → párrafo propio bajo la figura (keepNext); en un grupo flotante → cuadro de texto
   flotante aparte en la misma posición (vale con `posOffset` o con alineación si la leyenda tiene el ancho del grupo).
5. Renderizar con Word, comparar leyendas (cantidad y orden) y páginas contra la revisión anterior.

Por qué sin grupo: si la imagen queda dentro de un grupo (como hace `insertar_svg.py`), Word guarda además un respaldo
VML con `gfxdata` en base64 y una copia rasterizada por figura (el docx de prueba subió de 11 a 31 MB). Aun sin grupo,
Word guarda los SVG sin comprimir y regenera el PNG de respaldo a su resolución, así que el docx puede pesar más en
disco (11 → 18 MB); lo que alivia al abrir, desplazarse y editar es el `document.xml` y la cantidad de formas.

| Trampa del SVG en Word | Solución |
|---|---|
| Word **no dibuja ningún elemento con `filter`** (ni la forma ni la sombra) | sombras con capas semitransparentes (`Lienzo._sombra`); nunca `feDropShadow` |
| Word agranda las puntas de flecha de líneas finas | punta mínima ~0,19 cm (`estilo_ee`) |
| Marcadores, SVG anidado con `viewBox` | no usar: puntas como polígonos, recortes con PIL (`recorte_px`) |

Sin verificar en Word todavía: flechas horizontales con texto, `zona`, `contingencia` y `peor` sobre capturas (sí en Edge).

## De PowerFactory a la figura

1. Foto del diagrama: `exportar_grafico` + `wmf2png.ps1` de la skill powerfactory-python (6.400 px si hay que recortar
   zonas con cifras legibles). Sin coloreado de alarma, sin tensiones malas a la vista.
2. Recortes por idea (un sistema, una S/E, una línea), no la página completa. En el 500 kV deben verse los 4 circuitos
   que llegan a Ancoa. El recorte va en la spec (`imagen.recorte_px`): para ampliarlo o achicarlo se edita la spec,
   ya no el recorte de Word.
3. Anotaciones de `recorte_pf`: `flecha` (`direccion`, texto `t`), `etiqueta`, `zona`, `contingencia`, `peor`.

## Composición

- Figura a la derecha, 8,8–9,4 cm, texto envolviendo; a todo el ancho (16,4 cm) sólo cuando hay muchas cifras.
- Leyenda nativa de Word con numeración automática, fuera del SVG.
- Comparaciones lado a lado (dos recortes, 0,4 cm de separación) con una etiqueta roja sin borde abajo a la derecha de
  cada uno: «E01 | C07: 402 MW», «Red N | C02», «E01 | 35 MW».

## Estilo (implementado en `estilo_ee.py`)

| Objeto | Cómo |
|---|---|
| Flecha de flujo sobre captura | grande, azul 0070C0 opaco, sombra, texto blanco negrita dentro; recta sobre la línea; rótulo positivo con destino y tensión («+21 MW hacia Las Delicias (220 kV)») |
| Zona | rojo C00000 translúcido (~18 %) con borde punteado; etiqueta dentro, arriba a la derecha |
| Etiqueta sobre captura | sin borde («queda más boni»), fondo blanco con sombra, ~0,6 cm de alto, 9 pt |
| Contingencia | círculo tachado sobre el elemento que sale; en esquemas, naranjo FF5A00 con su código (CT12) |
| Peor sobrecarga | recuadro rojo |
| Esquemas | color por tensión (500 kV 1F3864, 220 kV 009244, 154 kV 990000, 66 kV D000D0), tramo abierto punteado con cuadro blanco, rótulos blancos con borde azul «MW \| carga %», leyenda al pie |
| Despacho por central | barra azul (inyección) o roja (carga) con restricción; contorno gris punteado sin restricción; «X de Y» |

Nada debe tapar los valores del unilineal. Ver también la memoria del proyecto `figuras-unilineal-informe`.
