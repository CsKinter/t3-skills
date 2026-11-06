# Edición del .docx por XML (técnica verificada, informe Cumbres del Ñuble 06–10-10-2026)

No se usó python-docx ni LibreOffice: XML directo con regex sobre `word/document.xml` y Word COM para renderizar.

## Estilos del documento EE (styleId → uso)

| styleId | Uso |
|---|---|
| `Heading1`–`Heading4` | títulos (Heading4 para «Condición sin restricción / Restricción / Resultado») |
| `Normal` | cuerpo: Cairo 11 pt, justificado, 12 pt después |
| `Imagenes` | leyendas de figuras y tablas (basado en Caption) |
| `ImagenEE` («Imagen_EE») | párrafo que contiene una figura a todo el ancho: centrado, `keepNext` |
| `TablaEEj` | tablas |
| `ListParagraph`, `ListaSimple1` | listas |

Clonar bloques desde el propio informe en vez de escribir XML de cero (`Cumbres del Ñuble\herramientas\informe_ee\plantillas_docx.json`: `h2`, `h3`,
`parrafo`, `leyenda_fig`, `leyenda_tabla`, `fig_img`). Para cambiar el texto de un párrafo conservando el formato:
`con_texto(p, texto)` deja el `pPr` y el `rPr` del primer run.

## Leyendas con numeración automática

`Figura ` + campo `STYLEREF 1 \s` + `<w:noBreakHyphen/>` + campo `SEQ Figura \* ARABIC \s 1` + `: Descripción | E04.`
(igual con `Tabla`). El número escrito dentro del campo es provisorio: Word lo recalcula con `render_docx.ps1`. Las
referencias en el texto («Tabla 5-2») son literales: al insertar figuras o tablas, revisar que no queden corridas.

## Figura flotante como grupo, figuras antiguas (caso de referencia: `Cumbres del Ñuble\herramientas\informe_ee\build_s1.py`, `build_s2.py`)

- Grupo `wpg:wgp` con: `pic:pic` (borde gris A6A6A6 de 12700 EMU), formas `wps:wsp` en coordenadas del grupo y un cuadro
  de texto al pie con la leyenda y sus campos.
- Flotante a la derecha: `wp:anchor` con `positionH relativeFrom="margin"` + `<wp:align>right</wp:align>`,
  `positionV relativeFrom="paragraph"` 36000, `wrapSquare wrapText="bothSides"`, `distL="180000"`; el run del dibujo va
  al inicio del párrafo de texto que acompaña. A todo el ancho: `wp:inline` dentro de un párrafo `ImagenEE`.
- Coordenadas de las formas en px del recorte, escaladas a EMU (360000 por cm). PNG reducidos a 2.000 px de ancho.
- Formas: `prst` `upArrow`/`rightArrow`/`bentArrow` (flechas), `roundRect` (etiquetas), `rect` (zonas), `noSmoking`
  (prohibido). Relleno 0070C0 opaco con `outerShdw`; texto blanco negrita Cairo; **`bodyPr wrap="square"`**.
- Cambiar sólo las fotos de un grupo conservando formas y ajustes del usuario: `swap_s2.py` (busca el grupo por
  `docPr name`, toma sus `r:embed` y reemplaza los archivos de imagen en el zip).

## Figura SVG (vigente desde el 29-10-2026; flujo y spec en `figuras.md`)

Las figuras nuevas no se arman con formas: `scripts/figuras_svg/insertar_svg.py` deja en el grupo un solo `pic:pic`
con `a:blip r:embed` = PNG de respaldo y, en `a:extLst`, la extensión `{96DAC541-7B7A-43D3-8B79-37D633B846F1}` con
`asvg:svgBlip r:embed` = SVG. Agrega `Default Extension="svg" ContentType="image/svg+xml"` a Content_Types. La leyenda
(cuadro de texto con campo SEQ) se conserva en el grupo; anclaje, ajuste y tamaño no cambian. Los cNvPr nuevos usan
ids desde 90001.

## Tablas (helpers en `informe_v3.py`, `pct_tablas.py`, `informe_formato.py`)

`tblW 5000 pct`, layout fijo, grid sobre 9895 dxa; encabezado `shd 404040`, texto blanco negrita `sz 17` y
`tblHeader`; bordes D6D6D6; `cantSplit` y `keepNext`. Barras de datos: PNG con PIL insertado inline en la celda
(`barra()`, `imagen_inline()`). `poner()` cambia el valor de una celda sin perder formato.

## Comparar versiones

- `diff_doc.py a.docx b.docx`: diff de texto por párrafo.
- `diff_s1.py`: además, dentro de una sección, tamaño y posición de dibujos, ajuste, formas (`prst`), textos de formas y
  estilos. Así se vio que el usuario había cambiado una flecha «−21 MW» por una curva «+21 MW hacia Las Delicias
  (220 kV)» y borrado un recuadro: conservarlo.
- Renderizar su copia en sólo lectura para mirarla: `render_docx.ps1 -Docx suyo.docx -SoloLectura`.

## Trampas

| Trampa | Solución |
|---|---|
| Al buscar un título aparece primero su entrada en el índice | filtrar por `<w:pStyle w:val="Heading2"/>` y tomar la última aparición |
| IDs duplicados al clonar | quitar `w14:paraId`/`w14:textId`, `bookmarkStart/End` y `lastRenderedPageBreak` (`limpio()`) |
| Colisión de ids de dibujos o relaciones | `docPr id` desde el máximo existente + 100; `rId` e `imageN` desde el máximo; `Default Extension="png"` en Content_Types |
| Archivo dañado al rearmar | respetar el orden del zip original y agregar explícitamente los media nuevos (`docx_zip.py`) |
| Formas con texto que Word achica al abrir (13 cm → 5 cm) | `bodyPr wrap="square"`, no `wrap="none"` |
| Zonas (rect) con cuadro de texto vacío y `wrap="none"`: Word las reduce a ~0,4 cm cada vez que guarda (Figura 5-3 de Cumbres, 12-10-2026) | `wrap="square"` también en formas sin texto; revisar después de `render_docx.ps1`, que guarda |
| Texto que «no cambia» en un grupo | Word guarda una copia Fallback de cada grupo: reemplazar en ambas |
| Campos de leyendas dentro de grupos sin actualizar | recorrer `Shapes` → `GroupItems` → `TextFrame.TextRange.Fields.Update()` (lo hace `render_docx.ps1`) |
| La consola rompe con «−» (U+2212) | `sys.stdout.reconfigure(encoding="utf-8")` o `PYTHONIOENCODING=utf-8` |
| Fotos de PF con rojo de alarma | apagar `SetColscheme.cUseAlarm` antes de exportar (skill powerfactory-python) |
