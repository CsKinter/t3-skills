---
name: ppt-ee
description: Arma y edita presentaciones PowerPoint con la plantilla corporativa de Estudios Eléctricos (EE) y los criterios de Vicente para presentar estudios eléctricos a clientes. Úsala siempre que haya que hacer, completar, rehacer, fusionar o corregir una "ppt", "presentación", "láminas", "diapos" o "deck" de EE o para un cliente de EE (Engie, etc.), aunque no se mencione la plantilla, y cuando el usuario pase un .pptx de EE para revisar, modificar o combinar.
---

# Presentaciones EE

La plantilla está en `assets/plantilla_EE.pptx` y la librería en `scripts/ee_pptx.py`. Esta skill existe porque las mismas piezas (títulos, franjas de conclusión, tarjetas, gráficos con coma, copia de figuras) y los mismos tropiezos de python-pptx se repiten en cada deck. Usa la librería en vez de reescribirlas.

## Antes de empezar

- **Nunca escribas dentro de OneDrive** (`...\OneDrive - Electrical Studies Corp\...`). Leer está bien; los entregables van a la carpeta de trabajo en Documentos (p. ej. `C:\Users\vicen\Documents\<proyecto>\`) o al Escritorio. Si hay que copiar algo, primero a la carpeta temporal.
- **Nunca pises un archivo del usuario.** Cada entrega es una versión nueva (`_v2`, `_v3`…). Si el usuario editó un deck, trabaja SOBRE su archivo (no regeneres desde tu script: perderías sus imágenes pegadas, anotaciones y textos). Antes de tocarlo corre `python scripts/inspeccionar.py suyo.pptx --vs tuyo_anterior.pptx` y mira qué cambió él; conserva todo eso y díselo en el resumen.
- **Las notas del orador pueden traer instrucciones para ti** ("esta diapo es confusa…", "-- dejar espacio para…"). Léelas con `inspeccionar.py`. Una vez aplicadas, reemplázalas por el guion del orador y avisa que lo hiciste.
- Python con `python-pptx`, `lxml` y `Pillow`. Render con el PowerPoint instalado (Windows). No uses LibreOffice para el QA: no tiene Cairo ni lee bien los SVG/EMF que pega el equipo.
- Scripts largos: escríbelos a un archivo con la herramienta de escritura y ejecútalos; los heredoc largos en bash se rompen con las comillas.

## Criterios de contenido (lo que Vicente espera)

1. **El título dice dónde estamos, no la conclusión.** Formato ruta con `|`: `Resultados | Caso base | Diurno`, `Alternativas de solución | Comparación`. El último tramo en negrita (`nueva_lamina(prs, "Resultados | Caso base | ", "Diurno", …)`). Mayúsculas como en castellano: sólo al inicio de cada tramo y en nombres propios (nada de Title Case inglés).
2. **La conclusión va abajo**, en la franja naranja (`conclusion=` o `franja()`), una sola oración. Si una lámina no tiene mensaje, pregúntate si sobra.
3. **`|` como separador**, nunca `·`, en títulos, subtítulos, etiquetas, tablas y gráficos.
4. **Lógica antes que cifras.** No pongas números "porque sí": si una lámina explica un problema, que se entienda la cadena causal (pasos numerados, flechas) y apóyala en una figura. Las cifras van cuando son el resultado que se discute. Cifras con coma decimal (`17,2 MW`, `61 %`).
5. **Secuencias explícitas.** Cuando un resultado depende de pasos (maniobra → nuevo límite → obra → esquema), muéstralos numerados en la lámina y en el mismo orden que las barras del gráfico.
6. **Láminas paralelas, formato idéntico.** Si dos láminas cuentan lo mismo para casos distintos (caso base vs sensibilidad, nocturno vs diurno), usa la misma geometría. Lo más seguro es `clonar_forma()` desde una y cambiar sólo los textos.
7. **Comparaciones justas.** Si comparas alternativas contra una referencia, que sea la referencia de todas (p. ej. el caso base), no la topología propia de una sola. Si una fila de tabla no tiene corrida detrás, dilo en la nota del orador.
8. **Figuras del informe: no las inventes.** Deja `figura(slide, …, "qué va", "Informe, Figura X-Y")` para que el usuario pegue la imagen, con el número de figura para que la encuentre rápido.
9. **Contenido confidencial**: nada de estudios hechos para terceros (otros clientes) en decks para un cliente; sólo datos propios o públicos (CEN, CNE).
10. **Notas del orador** en cada lámina: el guion, las cifras de detalle que no caben, y las advertencias ("probable pregunta…", "no está en el informe").
11. **El mismo tipo de resultado se muestra siempre igual.** Si el diurno va en barras, el nocturno también; si una sección usa tarjetas con cifras, la sección paralela también. Cambiar de representación entre bloques hace que el público crea que está viendo otra cosa (comentario de Nico tras presentar a Engie, sep-2026).
12. **Si una lámina cubre un solo bloque, el título lo dice.** «Alternativas de solución | Comparación | Nocturno», no sólo «Comparación». Si después viene el diurno, que se note el cambio.
13. **Cada sección cierra con una lámina de resumen**, sobre todo la de alternativas. Lo ideal es **una sola tabla comparable**: las mismas filas (opciones) para todos los bloques (columnas), agrupando columnas por bloque con su unidad y su base de porcentaje (p. ej. «Nocturno | descarga BESS, % de 93 MW» y «Diurno | PFV, % de 150 MW»). No partir en dos tablas con filas distintas: no se pueden comparar. Marca con † los valores que no salen de una corrida sino de que la restricción de ese bloque no cambia, y explícalo al pie.
14. **Profundidad según lo que le importa al cliente.** Lo secundario (para Engie, el diurno y el PLEX/PLUS) va resumido en pocas filas; el detalle queda en respaldo.

## Lenguaje visual de la plantilla

| Elemento | Valor |
|---|---|
| Naranjo principal / oscuro | `F29100` / `F27400` (`OR`, `OR2`) |
| Negro de marca | `1D1D1B` (`NEG`) — encabezados de tabla, cifras en contraste |
| Grises | texto `595959` (`GRT`), fondo de tarjeta `F2F2F2` (`GRL`), referencia `BFBFBF` (`GRM`) |
| Tipografía | Cairo en todo (la librería la fija en cada run) |
| Viñetas | cuadradas naranjas (`bullets()`), nunca `•` literal |
| Layout de contenido | `EE Logo Izq` (barra naranja arriba, logo abajo a la izquierda) |
| Portada y cierre | los de la plantilla (`portada()`, `cierre()`); no los recrees |

Grilla en pulgadas (13,33 × 7,5): título en y=0,50; cuerpo entre y=1,45 y 6,00, x entre 0,87 y 12,45; franja en y=6,15 (alto 0,62). Deja libre la esquina inferior izquierda (logo). Separación entre bloques 0,12–0,25.

Colores con sentido: naranjo = lo que se destaca o compite; gris = referencia o contexto; negro = contraste. En gráficos: referencia `GRM`, protagonista `OR`, segunda alternativa `NEG` u `OR2`. Un solo relleno naranjo fuerte por lámina además de la franja (si no, la franja deja de leerse como el mensaje): para destacar una tarjeta usa `line=OR` sobre fondo gris o blanco.

Patrones de lámina probados, con coordenadas: `references/patrones.md`.

## Flujo de trabajo

1. **Estructura primero, en chat.** Propón el esqueleto (tabla lámina → contenido → figura del informe) y espera el visto bueno si el pedido es amplio. Si el usuario da su propia estructura, síguela tal cual.
2. **Construye con la librería** (ver abajo). Un script por entrega, guardado en la carpeta temporal.
3. **Renderiza y mira.** `python scripts/render.py deck.pptx out --hoja hoja.png`, y para las láminas que tocaste `--laminas 7 10 --hoja par.png` a mayor tamaño. Revisa desbordes, tarjetas vacías a medias, textos pegados arriba, cifras que se parten en dos líneas, franjas tapadas por figuras, gráficos con punto decimal. Corrige y vuelve a renderizar sólo lo tocado.
4. **Verifica que nada se perdió** al editar un deck ajeno: `python scripts/inspeccionar.py nuevo.pptx --imagenes` y compara la cantidad con el original.
5. **Entrega**: copia a Documentos con nombre versionado y resume en una tabla qué cambió por lámina, qué conservaste del usuario y qué queda pendiente (figuras por pegar, datos no corridos).

## Librería (`scripts/ee_pptx.py`)

```python
import sys; sys.path.insert(0, r"C:\Users\vicen\.claude\skills\ppt-ee\scripts")
from ee_pptx import *

prs = abrir_plantilla()                  # plantilla sin las láminas de ejemplo (quedan portada y cierre)
portada(prs, "Estudio de Restricciones", "PV + BESS Entre Valles  |  Engie Energía Chile", "EE-ES-2026-1732-RB  |  29 de septiembre de 2026")
s = nueva_lamina(prs, "Resultados | Caso base | ", "Nocturno",
                 conclusion="La pérdida del ATR Quelentaro deja la descarga del BESS en 12 % a 14 %",
                 notas="Guion…")
tarjeta_cifra(s, 0.87, 1.55, 2.85, 2.1, "E05 vespertino", "11,3 MW", "12 % de 93 MW")
pasos(s, 0.87, 3.85, 5.93, [("Pérdida del ATR Quelentaro", "Contingencia C01"), ("…", "…")], alto=0.64)
figura(s, 7.03, 1.43, 5.64, 4.9, "Carga del ATR N°2 Las Arañas ante C01", "Informe, Figura 5-12")
barras(s, …, ["Caso base", "T1", "T2", "T3"], [11.3, 17.6, 55.8, 56.7], colores=[GRM, OR, OR, OR], pcts=["12 %", …])
barras_agrupadas(s, …, cats, [("Caso base", vals, GRM), ("Sensibilidad N°1", vals2, OR)])
tabla(s, x, y, w, filas, anchos_columna)
ordenar(prs, [portada_slide, s1, s2, …, cierre_slide])   # o mover_lamina / quitar_lamina
cierre(prs)
guardar(prs, r"C:\Users\vicen\Documents\…\deck_v1.pptx")    # SIEMPRE con guardar(), ver trampas
```

Edición de decks existentes: `abrir()`, `buscar_lamina(prs, "título exacto")`, `quitar_formas(s, criterio)` con `es_titulo`, `es_franja`, `es_imagen`; `set_parrafos(shape, [textos])` para cambiar texto sin perder formato; `clonar_forma(origen, "nombre", destino, textos)`; `encajar_imagen(pic, x, y, w, h)`; `copiar_formas(origen, [formas], destino, x, y, w, h, quitar_origen=False)` para mover figuras con sus anotaciones (escala en bloque y conserva posiciones relativas), también entre dos presentaciones distintas (fusionar el deck de un colega).

## Trampas conocidas

Detalle completo de las trampas (ya resueltas en la librería) en `references/trampas.md`. Reglas que hay que recordar siempre:
- Guardar siempre con `guardar()`, nunca `prs.save()` directo: renumera las láminas y evita que PowerPoint no abra el archivo.
- Comparar formas con `sh._element is otro._element`, nunca con `is` entre shapes (así se borró una figura del usuario).
- Tablas: PowerPoint agranda la fila si el texto no cabe; tras cambiar textos largos, bajar la altura de las demás filas para que la tabla no toque la franja.
