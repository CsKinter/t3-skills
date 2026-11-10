# Revisiones de Felipe Briceño (FeB, revisor)

Felipe revisa los informes de EE antes de enviarlos al cliente. Su revisión es la mejor señal de lo que un supervisor
pide al texto. Consultar este registro al redactar o revisar un informe de cliente. Sus ediciones se proponen a Vicente
y no se deshacen sin preguntar.

## Cómo registrar

- Leer el oficial **sin modificarlo**:
  `python ~/.claude/skills/redaccion/scripts/cambios_revisor.py "<oficial>.docx" "Felipe Briceño"`.
  El script abre el .docx como zip, así que no toca el archivo que Felipe tenga abierto. Correrlo desde un directorio
  propio.
- Por cada revisión, agregar en el registro una entrada con la fecha, el documento, el antes y el después de cada
  párrafo, los comentarios con su ancla y estado y, al final, la lectura que deja.
- Las ediciones sin control de cambios se detectan comparando el texto con la última versión local. Anotarlas aparte,
  porque el autor queda sin registrar.
- Cuando un patrón se repita en dos revisiones o más, subirlo a «Patrones» y, si Vicente lo confirma, al `SKILL.md`.

## Patrones (provisionales hasta que se repitan)

- **Criterio citado con su forma exacta.** Si la fuente fija un umbral, se escribe como requisito («debe mantener un
  flujo inferior a 900 MVA») y no como aproximación («debe quedar cerca de 900 MVA»). La finalidad va explícita
  («con el fin de mantener un margen…»).
- **«Restricción operativa».** Felipe califica la restricción cuando se define el resultado del estudio («la
  diferencia… corresponde a la restricción operativa», «el despacho admisible y las restricciones operativas»).
- **«Operación normal» frente a «ante una contingencia».** Para la capacidad de un equipo, opone «en operación
  normal» a «ante una contingencia». «Red completa» se mantiene para la evaluación N del método (Cap. 4).
- **Secciones introducidas por su contenido metodológico.** «Las Secciones 4.1 a 4.3 describen los criterios
  adoptados para la confección de los escenarios», en lugar de «el recurso y la construcción».
- **Fuentes identificadas.** Cuando se nombra una base de datos o un modelo («la base oficial del Coordinador»),
  Felipe pide decir cuál (versión o fecha).
- **Criterios de capacidad acordados.** Pregunta si el uso de capacidad transitoria en un equipo se conversó con
  Fran. El texto debe dejar claro qué capacidad se usa en cada tipo de equipo y con qué respaldo.

Al integrar sus ediciones, los detalles mecánicos (dobles espacios, «respecto a» y «respecto de», plurales como
«protecciones de sobrecorrientes») se pueden proponer a Vicente como ajuste menor, sin cambiar la redacción de Felipe.

## Registro

### 05-11-2026 | Cumbres del Ñuble, RB (Tiquel + Bulí)

Oficial `02_Informe\RB\EE-ES-2026-2442-RB_Restricciones - PE Cumbres del Ñuble.docx`, sobre la R35. Hubo 22 marcas
(14 inserciones y 8 eliminaciones) en 4 párrafos, entre las 14:21 y las 15:50, y 2 comentarios abiertos.

**Cambios con control de cambios**

1. Cap. 3, párrafo DAOP tras la Tabla 3-9 (14:21–14:24).
   - Antes: «Ante la pérdida de una unidad, cada autotransformador que permanece en servicio debe quedar cerca de
     900 MVA, con margen respecto del ajuste de su protección de sobrecorriente.»
   - Después: «Ante la pérdida de una unidad, cada unidad restante debe mantener un flujo inferior a 900 MVA con el fin
     de mantener un margen respecto a sus protecciones de sobrecorrientes.»
2. Cap. 3, capacidades CS3/CS4 de Ancoa (14:35).
   - «mientras que en red completa rige su corriente nominal» → «mientras que en **operación normal** rige su
     corriente nominal».
3. Cap. 4, párrafo de entrada (14:46–14:58).
   - Antes: «Las Secciones 4.1 a 4.3 describen el recurso y la construcción de los escenarios. Las Secciones 4.4 y
     4.5 establecen la evaluación en red completa y ante contingencias para determinar el despacho admisible.»
   - Después: «Las Secciones 4.1 a 4.3 describen los criterios adoptados para la confección de los escenarios. En las
     Secciones 4.4 y 4.5 se realiza una evaluación en red completa y ante contingencias para determinar el despacho
     admisible y las restricciones operativas.» (En el original quedó un doble espacio antes de «se realiza».)
4. Sección 4.1 (15:01–15:50).
   - «La diferencia entre ambos valores es la restricción.» → «**De esta forma,** la diferencia entre ambos valores
     corresponde a la restricción **operativa**.»

**Cambio sin control de cambios (autor no registrado)**

- Pie de la Figura 2-3: «de los sistemas de 220 y 500 kV» → «de los sistemas de 220 kV y 500 kV». El pie de la
  Figura 7-1 conserva «220 y 500 kV». Si se acepta el criterio, unificar.

**Comentarios (abiertos)**

- id 26, 09:30, p. 11, sobre «…flujo de potencia se desarrollan sobre la base oficial del Coordinador Eléctrico
  Nacional»: «¿Qué base? Agregar.» Falta identificar la base (versión o fecha).
- id 72, 14:08, Tabla 3-9, celda «750» (Tiquel 500/220 kV, T2): «Conversaste con Fran usar la cap transitoria para
  los ATRs?» La pregunta es técnica: hay que confirmar con Fran el criterio de capacidad de los ATR y, según la
  respuesta, explicitarlo en el texto.

**Lectura**

Felipe no cambió resultados ni cifras. Su revisión precisa criterios (umbral DAOP), fija el vocabulario del
resultado («restricción operativa», «operación normal») y pide identificar fuentes y criterios acordados.

Control del 05-11-2026, 22:40: el docx sigue con SHA-256 `015c1ed3e044…1f1d` (guardado a las 15:50). Se comparó su
texto con la R35. Sólo aparecen las 22 marcas y el pie de la Figura 2-3, sin cambios nuevos.


## Aclaración de Vicente | 06-11-2026

El uso de capacidad transitoria fue confirmado internamente. Las menciones a Fran en este registro describen una consulta interna, no texto destinado al cliente. No citar personas ni acuerdos internos en el informe. Para Cumbres, la base de partida es la BD de corto plazo de agosto de 2026. Conservar los cambios de Felipe y revisar sus comentarios contra el último guardado.


### 06-11-2026 | Cumbres RB, último guardado y council editorial

Registro íntegro antes/después y comentarios con ancla y estado en C:/Users/vicen/Documents/Projects/Cumbres del Ñuble/Orquestación/council_redaccion_0611/cambios_y_comentarios.txt. Copia de fuente y SHA en la misma carpeta. Felipe pide explicitar escenarios y contingencias en resumen y conclusiones, compactar espacios y cerrar comparando conexiones. Vicente confirma conservar códigos con su significado y mantener slack para el final. Las propuestas serán contrastadas por council antes de editar Word.

