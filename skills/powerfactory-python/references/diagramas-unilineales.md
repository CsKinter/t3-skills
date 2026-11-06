# Diagramas unilineales por script (IntGrfnet)

Aprendido armando el unilineal 154/66 kV de la ZDI de Cumbres del Ñuble (09/10-10-2026, PF 2025 SP4, vía puente). El
resultado fue un diagrama de ~55 barras (66 y 154 kV, de Itahue a Charrúa), 15 proyectos y una veintena de muñones,
con una caja de resultados por circuito, regenerable en ~3 min. El constructor completo está en `Cumbres del Ñuble\herramientas\unilineal\` (ver su README; no abrirlo salvo que se pida). Atributos de los objetos
gráficos: `object-model.md`, sección «Diagramas».

## Cuándo sirve

- El usuario quiere un unilineal «de informe» (estilo propio, legible para revisar Kirchhoff de un vistazo) en vez del
  diagrama general del modelo.
- Hay que repetirlo o ajustarlo muchas veces: con un constructor por script cada ajuste es cambiar números y regenerar.

Trabajar siempre sobre una **copia `_CdN`** del diagrama del usuario (`carpeta.AddCopy(orig, NOMBRE)`), nunca sobre el
original. Si el usuario mueve algo a mano en la copia, avisar antes de volver a correr el constructor completo (lo pisa).

## Método

1. **Explorar la topología** (sólo lectura) antes de dibujar:
   - BFS por tensión desde las barras de interés (`expl66.py`, `expl_bfs.py`): S/E por S/E, líneas con su otro extremo,
     trafos con sus tensiones, cargas y generadores. Ojo, la red de 66 kV crece rápido: definir paradas.
   - POI de cada proyecto (`expl_poi.py`): BFS desde el terminal BT del generador hasta la primera barra ≥ 60 kV dentro de
     una ElmSubstat. Los proyectos se reconocen por su terminal `TERMINAL_BT_<proyecto>`.
   - Barra real de cada conexión (`expl_bar.py`) y componentes por acoples cerrados (`expl_cp.py`): qué barra (B1, B2,
     BT, auxiliares) recibe cada elemento y qué barras son el mismo nodo. Esto decide qué hay que dibujar.
2. **Especificar** en coordenadas de diseño (px; x a la derecha, y hacia abajo) y convertir a mm de PF con
   `X = sn(30 + 0.41·(px + DX))`, `Y = sn(380 − 0.40·py)`, donde `sn` ajusta a la grilla G = 4,375 mm. Listas:
   `BARS` (terminal, x, y1, y2, vertical), `PTS` (puntos: taps, estructuras), `LINES` (línea, extremo A, extremo B,
   waypoints; un extremo puede ser una tupla (x, y) = muñón), `TRAFOS` (trafo, x, y, {borne: barra | (x, y) |
   (barra, [waypoints])}), `GENS` (gen, x, y, y del punto BT).
   - Terminales por `"SE|barra"` o `"@línea:terminal"` (extremo de una línea conocida): los nombres se repiten.
   - Elementos por nombre normalizado (sin acentos ni signos), afirmando que la coincidencia sea única.
3. **Pasada en seco**: calcular todas las rutas sin escribir, registrando dónde llega cada conexión a cada barra (ATT).
   Con eso se dimensiona cada barra (cubre sus conexiones ± 2G), se igualan los pares `||` y se alinean las bases.
4. **Pasada real**: escribir sólo lo que cambió (`fija()` compara antes de `SetAttribute`; en conexiones, punto por
   punto). Una corrida sin cambios hace ~100 escrituras en vez de ~2.700 y no provoca caídas.
5. **Cajas y anotaciones**: elegir la caja visible de cada circuito y ubicar los textos con un modelo de obstáculos
   (rectángulos de barras, símbolos, segmentos y cajas ya puestas) y una función de costo de solape.
6. **Chequeos** impresos en cada corrida: conexiones al mismo lado de una barra a menos de 2 cuadros, conexiones a menos
   de 1 cuadro del borde de la barra, cajas y textos con choque, errores por elemento. Objetivo: 0 / 0.
7. **Foto**: `dg.Close(); dg.Show()` → `exportar_grafico` → `wmf2png.ps1` (6.400 px para leer cifras) → recortes con PIL.
   Revisar la foto completa y también comparar contra la foto aprobada anterior: un cambio global puede mover lo que
   ya estaba bien.

## Estilo del usuario (Vicente)

- **Una caja de resultados por circuito S/E–S/E.** Tramos unidos por estructuras de paso puro (nodo con exactamente
  2 líneas) = una sola caja; si en el nodo cuelga carga, generación o trafo, una caja por tramo. Una caja por trafo
  (lado AT) y una por proyecto (en el «cuello» gen–punto BT). Circuitos fuera de servicio sin caja.
- **Cajas EN la línea**, cortándola, junto a un extremo (salida o llegada); pares de doble circuito con sus cajas en el
  mismo extremo.
- **Las líneas entran siempre perpendiculares a la barra** (corchete o codo en L, nunca por la punta). Conexiones al
  mismo lado de una barra separadas ≥ 2 cuadros (cabe una caja por circuito) y a ≥ 1 cuadro del borde de la barra.
- **Barras de una misma S/E juntas `||`**, mismo largo. 154 kV abajo con base común (salvo las que parecerían seccionar
  líneas) y el troncal Parral–Charrúa en una sola horizontal; 66 kV arriba, separado.
- **Proyectos**: gen + terminal BT como punto, nombre en rojo. Terciarios/medición de trafos de 3 devanados como punto
  pegado al trafo. Trafos de 3 devanados a dos barras: corchetes anidados al mismo lado.
- **Anotaciones**: S/E en negrita grande pegadas a su barra; muñones «Hacia S/E X» (nunca «Desde») en negrita gris
  pegados a la punta del «<<»; textos largos en dos líneas; capa Labels apagada.
- Sacar lo que no conecta con el resto (islas). 66 kV sólo donde hay proyectos; redes sin proyectos como muñón del trafo.
- **Compactar al final**, estilo Entre Ríos: aspecto rectangular, barras que cubren espacios, hoja ajustada al
  contenido. De a poco, mostrando foto en cada paso.

- **Prioridad de orden (regla del usuario, 10-10-2026)**: cuando se pueda, líneas continuas entre S/E (una cadena de S/E con sus
  líneas a la misma altura de punta a punta: termina una y empieza la otra a la misma altura) y barras de un mismo sistema a la misma
  altura o "nivel" (todas parten del mismo borde: base común abajo o tope común arriba).
- **Franjas por tensión**: cada sistema en su franja horizontal de ancho completo (p. ej. 220/500 kV arriba, 66 kV al medio, 154 kV
  abajo), marco gris segmentado (`Polygon(pattern = LinePattern.Dash, ...)` en la capa de anotaciones) y la tensión en la esquina;
  sólo trafos y sus corchetes cruzan entre franjas. Franjas de alto parejo. La hoja de PF se recorta desde arriba: para achicarla se
  bajan las franjas de arriba, no se sube la de abajo.
- **Muñones según geografía**: «Hacia S/E X» apunta hacia donde está esa S/E en el diagrama (todos los «Hacia Ancoa» al norte).
- **Llenar sin seccionar**: estirar barras y repartir sus elementos para llenar huecos, pero una barra nunca debe cruzar una línea que
  no llega a ella (parece que la secciona); cruzar barras de la misma S/E es normal. Salidas de trafos a una misma barra: corchetes
  anidados, nunca por el mismo camino.
- **Alcance por flujo diferencial**: ver `flujo-diferencial.md`; dibujar lo que tiene |factor| >= 3 % (o lo que el usuario pida
  completar) y lo demás como muñón.

## Calibraciones y mecánica (verificado)

- **Trafos rotación 270**: AT en (+G, 0) del centro; MT en (−G, −G) (Tr3) o (−G, 0) (Tr2); BT/terciario en (−G, +G).
  **Rotación 90**: el simétrico (AT a la izquierda): AT (−G, 0), MT (+G, +G) o (+G, 0), BT (+G, −G). Usar 90 cuando la
  barra de AT queda a la izquierda del trafo.
- **Líneas**: el IntGrf `d_lin` va en el punto medio; `iRot` 270/90 si el primer tramo es horizontal (borne 0 hacia
  +x/−x), 0/180 si es vertical. Cada mitad es un GCO desde el símbolo hacia su borne.
- **Barras**: `rSizeX = largo / 26,25` (TermStrip) con `iRot` 90 si es vertical.
- **Cajas**: `iBoxRefPt = −1` con `center_x = center_y = 0` pone la caja sobre la conexión, ~0,5 mm después del extremo
  del borne indicado por `anr` (rectángulo ~11,5 × 7,5 mm); `do_rot = 0`, `rotate = 0` las deja horizontales (el
  atributo `iOrient` NO es la rotación). `center_x/center_y` desplazan a lo largo de la conexión (+ = derecha/arriba).
  PF centra el texto: con cifras anchas (−14,3 Mvar) o cuando el extremo es un PointTerm la caja tapa la barra; ahí
  2,5–3 mm de desplazamiento. Si la línea cruza la barra vecina del par `||`, saltarla (~8,5 mm). Trafos: sin salto
  (la caja caería sobre el trafo).
- **Barras auxiliares**: si el cubículo de un elemento llega a una barra auxiliar (52B1, TAT2, AT1_aux, BT1_aux) que no
  está dibujada, el elemento queda suelto con «<<» aunque esa barra esté acoplada a la dibujada. Dibujarla como
  PointTerm exactamente sobre la barra principal (se ve como el punto de conexión) o, si recibe varios elementos, como
  barra propia corta (p. ej. la BT de transferencia). PF dibuja círculos huecos donde una conexión cruza otra barra de
  la misma S/E (seccionador abierto) y dos «pelotas» cuando conecta a dos barras.
- **Muñones**: PF dibuja sólo la mitad que llega a la barra y pone el «<<» en el símbolo de la línea. Para que el «<<»
  quede en la punta, ubicar el símbolo en el extremo libre (no en el punto medio). Largo ~5 cuadros (caja + flecha).
- **Corrimientos**: mover el diagrama en x sólo por múltiplos exactos de la grilla (`DX = n·4,375/0,41`); si no, el
  redondeo mueve un cuadro elementos ya aprobados (pasó con un trafo que quedó pegado a su barra).
- **Hoja**: crear un `SetFormat` propio `_CdN` (copia de uno existente), fijar `iSizeX/iSizeY` y asignarlo en
  `SetGrfpage.aDrwFrm`. Penalizar textos fuera de la hoja al ubicarlos.
- **Anotaciones**: ubicar cada texto con candidatos pegados a su barra/punto (arriba, abajo, a los lados) y desplazamientos
  pequeños; para «Hacia», candidatos más allá de la punta del muñón. Reescribir la capa sólo si cambió.

## Compactación (cómo se hizo)

- Acortar tramos vacíos con transformaciones de x por umbral aplicadas a toda la especificación (barras, puntos,
  waypoints, trafos, gens) y a los textos, encadenadas en orden y cada una documentada con su fecha. Una función lineal
  por tramos (0 px en un ancla, N px más allá) aprieta una cadena sin romper las demás distancias.
- Después de cada paso: revisar choques puntuales (barras de un par que caen en el mismo cuadro, generadores encima de
  una barra ajena, muñones cortos) y corregir con ajustes finos explícitos.
- El ancho mínimo lo fija la cantidad de S/E en el troncal; el alto, el bloque más alto. Lo que toca partes aprobadas se
  propone antes de hacerlo.

## Trampas (y solución)

| Síntoma | Causa | Solución |
|---|---|---|
| Líneas diagonales al origen, «<<» | se escribió el vector `rX/rY` completo | escribir punto por punto |
| Conexión con menos puntos no se acorta | PF ignora −1 al final | rellenar con el último punto |
| La foto no cambia | el diagrama abierto no se repinta con el puente activo | `Close()` + `Show()` antes de exportar |
| «<<» en un elemento conectado | su barra real (auxiliar/B2/BT) no está dibujada | dibujar esa barra (punto sobre la principal o barra propia) |
| Muñón sin «<<» visible | el «<<» va en el símbolo (punto medio) y lo tapa la caja | símbolo en la punta libre |
| Cajas verticales | `do_rot`/`rotate` | `do_rot = 0`, `rotate = 0` |
| Trazo cian suelto en un Tr3 | GCO duplicado con el mismo borne | reasignar el sobrante como terciario (2) |
| «already deleted» en el comando siguiente | miles de escrituras/SetVitxt | escribir sólo cambios; el puente hace `gc.collect()` |
| Elementos antiguos movidos un cuadro | corrimiento no múltiplo de la grilla | `DX` múltiplo exacto |
| Dos barras de un par en el mismo cuadro | compactación no uniforme | fijarlas a 1 cuadro tras transformar |
| Heredoc de bash rompe el script | comillas/backslashes | escribir el parche a archivo y ejecutarlo |
| `\n` literal dentro de un string generado | el generador inserta código como texto | escribir bytes y verificar con `repr` |

## Ediciones manuales del usuario (10-10-2026)

- Antes de reconstruir un diagrama que el usuario pudo haber tocado a mano: copiarlo (`AddCopy`), correr el constructor **sólo sobre
  la copia** y comparar objeto por objeto (pDataObj + símbolo: centro, giro, largo, puntos de cada conexión, cajas visibles y textos
  de la capa de anotaciones). Las diferencias son sus ediciones: anotarlas, preguntar lo que no se entienda e incorporarlas a la
  especificación antes de volver a correr el constructor sobre el original. Borrar la copia al final.
- Si en un par `||` una conexión aparece terminando en la otra barra, verificar la topología real (barras alcanzadas por acoples
  cerrados) y las maniobras en el stage: arrastrar en la GUI puede reconectar el elemento.
- PF recalcula el `extent` de los textos que el usuario edita en la GUI; no es un cambio de contenido.
- **Cajas de tensión de barras** (usuario, 11-10-2026): caja `ResElmTerm*` del TermStrip, paralela a la barra (verticales:
  `rotate = π/2`, `do_rot = 0`), PEGADA a la barra (abajo/arriba; en verticales a un costado, separación 0,35 mm) y con su borde
  alineado con un extremo de la barra (caja ~16,2 × 3,8 mm). `iBoxRefPt = -1` e `iParRefPt = 5` (si no, en ShortTermStrip el
  origen queda en el otro extremo). Elegir la opción sin choques (líneas que entran por ese lado, otras barras, cajas); si sólo
  choca con el nombre de la barra, correr el nombre hacia afuera (barra – caja – nombre). Barras acopladas con igual tensión:
  una sola caja. Script: `caja_barra_pos.py` (scratch pfb).
- Texto en 2 líneas (nativo, verificado 10-10-2026 con una edición del usuario en la GUI): un solo `Text` con la secuencia
  literal barra invertida + n dentro de `textString` (en código Python: `"PE Cumbres\\ndel Ñuble"`, o sea 2 caracteres `\` y `n`;
  `repr` del string leído muestra `\\n`).
  Un salto de línea real no sirve (PF junta las líneas). El `extent` es el de una línea; PF lo recalcula al editar.
  PF centra el texto de 2 líneas en `origin` (verticalmente), con interlineado ~3,2 mm a fontSize 10 (apilado era 2,64).
  **Trampa del puente**: el transporte del código reduce las barras invertidas un nivel (`"\\n"` en el código llega como salto
  real, que parte el elemento de `annotationElementsStr` en dos entradas). Escribir la barra con `chr(92)`: `NL = chr(92) + "n"`.
  Antes de escribir la lista de anotaciones, guardar un respaldo JSON y verificar al releer que el número de elementos no cambió.
- Copias de diagramas (`AddCopy`) para probar:
  - Traen IntGrf que en el original no aparecen en `GetContents` (borrados u ocultos, p. ej. un muñón que el usuario eliminó):
    borrar en la copia los que no están en el original.
  - No reutilizar el nombre de una copia borrada: el tablero conserva la pestaña vieja y `GetPage(nombre)` exporta esa
    (foto sin textos, sin resultados y en hoja A). Usar un nombre nuevo cada vez.
  - Editar la copia por script puede tardar más de 5 min con la página abierta: esperar a que el puente quede libre antes de la foto.
- Cuando el usuario ya editó el diagrama a mano, es mejor editarlo directo por script (pares, nombres, compactación)
  que traducir sus cambios al constructor: sus movimientos quedan exactos.
- Compactar: en la foto (WMF→PNG) buscar franjas de filas o columnas donde sólo cruzan trazos perpendiculares
  (ignorar flechas de flujo) y correr todo lo que está más allá un múltiplo de la grilla (4,375 mm); luego achicar la hoja.
  Si el diagrama ya es denso la ganancia es pequeña: lo grande viene de reacomodar zonas.


## Copia compacta por escala (Cumbres, 12-10-2026)

Para figuras de informe legibles: copia del diagrama con todo acercado por un factor S (0,70 quedó bien; 0,62 era demasiado),
manteniendo el tamaño de símbolos, cajas y textos. Scripts del caso en el scratchpad (`escala_dia.py`, `retrim_barras.py`,
`ajusta_dia.py`, `pares_dia.py`):
- Centros × S; en cada conexión el primer punto conserva su desplazamiento original respecto del símbolo y se repara la
  ortogonalidad tramo a tramo; los demás puntos × S. Anotaciones: orígenes × S; el anillo de realce conserva su radio.
- **Barras**: acortarlas a sus enganches (+3 mm, mínimo 18 mm para la caja de tensión), contando los **dos extremos** de cada
  conexión y las barras paralelas de una misma S/E y nivel **como grupo** con la misma extensión (si no, las dobles/triples
  barras quedan desalineadas y algunas líneas quedan colgando). Luego volver a correr la ubicación de cajas de tensión.
- Revisión por **4 × 4 cuadros** de la foto HD (6.400 px) y ajustes por lote: mover textos (por índice si traen `\n`, que el
  transporte del puente rompe), mover cajas (`center_x/center_y`, elegir la caja visible `zlvl = 1`), alargar barras, y mover
  símbolos arrastrando sus conexiones (los trafos quedan tapados por sus propias cajas al compactar: correrlos 4–7 mm hacia el
  lado de baja). Circuitos paralelos C1/C2: separar sus cajas ±2,4 mm (el de arriba sube).
