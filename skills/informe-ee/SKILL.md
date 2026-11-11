---
name: informe-ee
description: Edita informes Word (.docx) de estudios eléctricos de EE (restricciones, flujos, contingencias) con los criterios de redacción, tablas y figuras de Vicente, por XML directo sobre el .docx del usuario y renderizando con Word. Úsala siempre que haya que escribir, completar, corregir o maquetar un capítulo, tabla, figura o leyenda de un informe de EE (p. ej. "documentemos esto en el word", "pon la tabla en el informe", "cambia las fotos de la figura"), aunque no diga "skill" ni "docx". Presentaciones: ppt-ee; datos o fotos de PowerFactory: powerfactory-python.
---

# Informes Word de EE

Los informes de EE se entregan al cliente y los lee alguien que sabe de sistemas eléctricos pero no de PowerFactory.
Esta skill reúne cómo se editó el informe del estudio de restricciones de Cumbres del Ñuble (06–10-10-2026) sin romper
el documento del usuario, y lo que Vicente espera del texto, las tablas y las figuras.

Archivos:
- `scripts/docx_zip.py` — desarmar y rearmar el .docx respetando el orden del zip (no hay `zip` en la bash de Windows).
- `scripts/render_docx.ps1` — Word COM: actualiza campos (también los de grupos), índices y tablas de figuras, guarda y
  exporta PDF; `-SoloLectura` para mirar la versión del usuario sin tocarla.
- `scripts/docx_ee.py` — helpers genéricos (párrafo, título, leyenda, tabla EE, imagen, reemplazo de la tabla antes de su
  leyenda).
- `scripts/figuras_svg/` — figuras en SVG desde una spec JSON (`estilo_ee.py`, `figuras.py`), vista previa PNG con Edge
  e inserción en el .docx como imagen simple, sin grupo (`insertar_plano.py`; `insertar_svg.py` deja un grupo y Word
  lo infla con un respaldo VML). Migración de figuras antiguas de formas a SVG renderizadas por Word
  (`migrar_mini_docx.py`, `exportar_pdf.ps1`, `migrar_pdf_a_svg.py`): ver `references/figuras.md`.
- Caso de referencia (helpers de Cumbres tal como se usaron, con figuras flotantes de objetos): `Cumbres del Ñuble\herramientas\informe_ee\`.
  No abrirlos salvo que se pida: son específicos de ese informe.
- `references/tecnica-xml.md` — receta de edición, estilos del documento EE, XML de figuras/tablas/leyendas y trampas.
- `references/figuras.md` — figuras: flujo SVG, trampas del SVG en Word, estilo (flechas, etiquetas, zonas, esquemas).
- `references/revisiones.md` — revisiones numeradas, verificación antes de aprobar y oficialización.
- Estructura y contenido de un informe de restricciones (esqueleto, plantilla por escenario, origen de cifras, lista de
  chequeo): skill `estudio-restricciones`, `references/informe.md`.

## Antes de tocar el informe

- **Trabajar sobre el .docx del usuario**, nunca regenerarlo desde un script propio: puede haber cambiado texto, flechas
  o figuras. Si hay una versión suya más nueva, releerla y comparar (`diff_doc.py`, `diff_s1.py`) antes de editar.
- Si existe `~$<nombre>.docx` en la carpeta, Word lo tiene abierto: trabajar en una copia y pedir que lo cierre (o
  combinar después sobre SU versión).
- Respaldo antes de cada cambio (`informe_respaldo_antes_<qué>.docx`). **Un solo archivo oficial**, con su nombre y
  sin sufijos de versión. Las copias de trabajo sí se numeran por revisión, cada una con su LEEME:
  `references/revisiones.md`.
- **El oficial no se edita.** Si vive en OneDrive, sólo se reemplaza con aprobación explícita del usuario, respaldo
  previo y dentro de la carpeta que autorice el AGENTS.md del proyecto. Sin esa regla escrita, OneDrive es sólo lectura.
- **Cambios de estructura** (capítulos, secciones, orden): mostrar primero el esqueleto en el chat y esperar el visto
  bueno.

## Redacción

La prosa sigue la skill `redaccion` (núcleo + `references/informe-cliente.md`). Leerla antes de escribir o corregir
texto del informe. Aquí sólo queda lo propio del Word: las leyendas describen el estado, no la iteración, y cada
escenario usa la misma estructura de títulos (p. ej. «Condición sin restricción», «Contingencia crítica» y
«Restricción aplicada» en Heading4).

## Tablas

- Estilo de la tabla del informe (`TablaEEj`) o el helper de `informe_v3.py`: ancho 100 %, encabezado negro 404040 con
  texto blanco en negrita 8,5 pt y repetido en cada página, bordes D6D6D6, filas que no se parten.
- Filas de grupo (escenario, nivel de tensión) a todo el ancho en rojo C00000 negrita; fila destacada F2F2F2.
- Formato condicional «con cariño»: verde E2EFDA sin cambio, rosado FDE9D9 reducción; carga ámbar 70–100 % y roja
  > 100 %; barras de datos como PNG pequeñas dentro de la celda cuando ayudan.
- Leyenda de tabla **debajo** de la tabla. Al reemplazar una tabla, ubicarla como «la tabla justo antes de su leyenda».

## Figuras

- Muchos zooms en vez de la página completa del unilineal; una figura por idea.
- Flotando a la derecha con el texto envolviéndola. Ancho 8,8–9,4 cm flotante, 16,4 cm a todo el ancho.
- Desde el 29-10-2026 se dibujan en **SVG desde una spec JSON** y se insertan como imagen SVG con respaldo PNG; la
  leyenda queda nativa con su campo SEQ. Ya no se exigen objetos editables (Vicente: «Convertir en forma» si hace
  falta). Iterar con la vista previa PNG; el Word se renderiza una vez al final.
- Comparaciones lado a lado con etiqueta roja sin borde abajo a la derecha («E01 | C07: 402 MW», «Red N | C02»).
- Flechas grandes azul 0070C0 opaco con sombra y texto blanco en negrita dentro, rectas sobre la línea, rótulo positivo
  con destino y tensión («+21 MW hacia Las Delicias (220 kV)», nunca «−21 MW»). Zonas en rojo translúcido con borde
  punteado. Símbolo de prohibido sobre la contingencia; recuadro rojo en la peor sobrecarga.
- Nada que tape valores del unilineal; sin coloreado de alarma ni tensiones malas en las fotos de PF.
- Detalle y XML: `references/figuras.md`.

## Flujo de una edición

1. Respaldo → `python scripts/docx_zip.py extraer informe.docx unz`.
2. Script de edición sobre `unz/word/document.xml` (+ rels y media), clonando bloques del propio informe
   (`plantillas_docx.json` en el caso de referencia) para heredar estilos.
3. `python scripts/docx_zip.py armar unz informe.docx nuevo.docx`.
4. Validar con `scripts/office/validate.py nuevo.docx --original informe.docx` de la skill docx instalada, con
   `PYTHONIOENCODING=utf-8` (si no, la consola cp1252 falla al imprimir «→»); debe decir «All validations PASSED!».
   Probado el 10-10-2026: extraer + rearmar el informe de Cumbres sin cambios pasa la validación.
5. `render_docx.ps1 -Docx nuevo.docx`: campos, índices y PDF. Revisar las páginas tocadas como PNG (pymupdf a
   70–110 dpi, mosaico con PIL) antes de dar por terminado.
6. Copiar sobre el archivo oficial (si el usuario no lo tiene abierto) y resumir qué cambió y qué quedó pendiente.
