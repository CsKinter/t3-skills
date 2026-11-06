# Trampas de lectura (PDF, tablas y nombres)

Cada trampa de acá costó una conclusión equivocada en algún momento. Leerlas
antes de cerrar un dato.

## 1. Tablas de dos columnas y `pdftotext -layout`

Las fichas del CEN y del SEA tienen pares etiqueta/valor en dos columnas. Con
`-layout`, el texto se reordena por posición y las etiquetas quedan al lado del
valor de la fila de al lado.

Caso real: en un IAC, «Potencia Retiro» quedó junto a «130 MW» cuando el valor
era 0, y «Retiro» era el nombre de la comuna (Maule). De ahí salió un retiro de
130 MW que no existía.

**Regla:** `pdftotext` **sin** `-layout`; leer la secuencia etiqueta → valor; si
el orden no es inequívoco, descartar el dato y marcarlo `s/d`. Cuando el valor
importa, copiar la línea textual al informe.

## 2. «Retiro» es una comuna

Retiro es una comuna del Maule (Tamango, Parque Solar Parral). Nunca confundir
«Retiro» (lugar) con «potencia de retiro» (carga desde la red). Si aparece la
palabra sola en una tabla, mirar la columna.

## 3. Potencia nominal, de inyección y de retiro son tres números distintos

- **Nominal / instalada**: lo que suma la placa de los equipos.
- **Inyección**: el máximo que puede exportar el punto de conexión. Puede ser
  menor que la suma de componentes (un solo transformador, un solo paño).
- **Retiro**: el máximo que puede absorber de la red. Cero en una CRCA que sólo
  carga con su propia generación; > 0 si puede cargar del SEN.

Un mismo proyecto puede tener 150 / 150 / 115 y las tres cifras ser correctas.
No «corregir» una con otra sin decir cuál es cuál.

## 4. Placeholders sin rellenar

Las RCA del SEA salen con `<NUM_RES>`, `<FECHA_RESOLUCION>`, `<NUM_ICSARA>`,
`<CIUDAD_FECHA_INFORME>` en la capa de texto. No inventar el número de
resolución: citar fecha + `idDocumento` + expediente, y decir que el número no es
legible.

## 5. Orden de lectura con firma digital

Los PDF firmados por `sellodigital.sea.gob.cl` intercalan bloques de firma
(fecha, UTC, razón) entre párrafos. El texto extraído no sigue el orden de
lectura. Leer por secciones (VISTOS, CONSIDERANDO, RESUELVO) y no confiar en
«la frase anterior».

## 6. Encoding

- `pdftotext -enc UTF-8` y leer el `.txt` como UTF-8. Si se lee como ANSI, los
  acentos salen `A3`, `A-`, `?`.
- Los endpoints del SEA devuelven Latin-1 en algunos campos y UTF-8 en otros.
  Decodificar UTF-8 y, si falla, Latin-1.
- En PowerShell, `Get-Content` sin `-Encoding UTF8` rompe los acentos y hace
  fallar los regex de etiquetas.

## 7. Excel: `sharedStrings`

Para buscar un nombre en un `.xlsx` sin abrirlo, descomprimir y buscar en
`xl/sharedStrings.xml`. Si el nombre no está ahí, no está en el libro. Ojo: los
números no viven en `sharedStrings`, viven en `sheetN.xml`.

## 8. Confidencial no es inexistente

La ficha de la carta dice «X.pdf es confidencial» por anexo. El PDF principal de
la carta (`download_saved_file/<id>`) muchas veces sí se descarga aunque la
ficha esté marcada «Confidencial». Probar siempre; si no baja, decirlo.

## 9. Trampa de nombres

Los desarrolladores usan familias de nombres y los titulares son SPV. Caso real:
«Andino Suiza» (Bulí), «Andino Solar» (Portezuelo), «Andino Melcahue» (150 MW,
San Carlos), «Andino Huichahue», «Andino Longotoma», «Andino Occidente I/II»,
«BESS Andino» (AES Pacífico, Tarapacá). Todas distintas.

**Regla:** resolver por **NUP + punto de conexión + titular**, nunca por nombre.
Si dos documentos con el mismo nombre no coinciden en NUP o en SE, son proyectos
distintos hasta que se demuestre lo contrario.

## 10. El titular ambiental no es el titular de la conexión

Cóndor Los Lagos SpA es el titular de la RCA; Andes Solar S.A. firma las SAC.
Es la misma estructura (SPV + desarrollador), no dos proyectos. La CNE a veces
atribuye el proyecto al desarrollador. Decirlo una vez y no convertirlo en
«contradicción de titulares».

## 11. Evidencia negativa con fecha

«No hay pertinencia» es una afirmación sobre el registro al día de la consulta,
no sobre la historia. Escribir «no hay pertinencia registrada al 02-11-2026»
y decir cómo se buscó (términos, filtros, cantidad de resultados). Un cero sin
método no es evidencia.

## 12. La ficha no se actualiza; el PDF tampoco se actualiza solo

Dos registros pueden estar desfasados en direcciones opuestas: la ficha de AA
puede conservar la potencia de 2022 y la RCA puede tener la de 2026. No hay una
«fuente verdadera» única: hay que fechar cada una y decidir cuál manda para qué.
Para lo construible manda la RCA; para lo despachable, el IAC; para lo
declarado, la ficha.
