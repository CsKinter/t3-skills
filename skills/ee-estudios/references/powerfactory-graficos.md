# PowerFactory | gráficas y diagramas: herramientas verificadas

Consolidación del 20-10-2026 | PowerFactory 2025 SP4. Complementa [Diagramas nativos](digsilent-diagramas.md) y el [catálogo de parámetros confirmados](parametros-confirmados.md). No trasladar valores o geometrías entre proyectos.

## Grados de comprobación

- **Interfaz observada:** control o atributo identificado en la aplicación. No implica haber ensayado todos sus efectos.
- **Exportación probada:** recorte real exportado a SVG y estructura XML examinada.
- **API documentada:** firma y efecto descritos en PythonReference de la instalación; no ejecutados durante esta exploración.

Las comprobaciones de esta sesión no modificaron conexiones, geometría ni parámetros eléctricos. Los diálogos de configuración terminaron con Cancel. La exportación utilizó los resultados que ya estaban mostrados; no se ejecutó un flujo nuevo y la muestra no acredita un nuevo cálculo.

## Cuadrícula y rutas

**Interfaz observada:** Diagram Settings → Schematic Diagram permite Snap, rutas no ortogonales/ortogonales/semiortogonales, factores de tamaño y separación inicial de equipos de un terminal. La separación inicial es una distancia de dibujo; no es longitud eléctrica.

**API documentada:**

| Método | Uso | Condiciones |
|---|---|---|
| `IntGrf.SnapToGrid()` | Ajustar un objeto gráfico existente a la cuadrícula | Su diagrama debe ser la página activa y Snap debe estar habilitado; retorna 0 si tiene éxito |
| `IntGrf.Orthogonalise()` | Ortogonalizar un objeto gráfico de rama | Su diagrama debe ser la página activa y Ortho debe estar habilitado; retorna 0 si tiene éxito |
| `IntGrf.MoveToLayer(layer)` | Mover la representación a una capa compatible | El objeto debe ser válido para esa capa |

Preferir estos métodos a reconstruir rutas sin conocer sus reglas internas. Ensayar primero sobre una copia y un sector pequeño. No ejecutar Snap u Orthogonalise indiscriminadamente: pueden cambiar posiciones y recorridos que ya estaban cuidados. Comprobar extremos, curvas, símbolos y cajas antes y después, con el mismo flujo corrido.

El ajuste de la cuadrícula no demuestra ausencia de solapes. Las cajas pueden seguir interceptando texto o símbolos aunque todos los centros estén alineados.

## Texto: resolver ancho y anclaje antes de reducir fuente

**Interfaz observada:** con Freeze desactivado, el menú de una caja ofrece Edit Graphic Object, Width, Text Alignment, Change Reference Points y Reset Settings. El objeto SetVitxt expone ancho en caracteres, cantidad de líneas, giro, alineación, posición sobre la conexión y anclajes. El diálogo de formato IntForm permite elegir variables, unidades y decimales.

La muestra examinada tenía cajas de seis caracteres por línea y unidades abreviadas como «Mv..». El SVG conservó esas abreviaciones: la exportación no recupera el contenido que la caja ya recorta.

Secuencia recomendada:

1. Identificar si es nombre, resultado automático o caja particular vinculada.
2. Revisar el formato y el alcance de su modificación. Un formato de ramas puede afectar muchas clases y diagramas; una caja particular permite una excepción localizada.
3. Revisar ancho, líneas y contenido. Para MW y porcentajes publicados, respetar la preferencia por enteros sin redondear los cálculos internos.
4. Ajustar el anclaje y el desplazamiento al elemento correcto. La alineación del texto dentro de una caja no centra la caja sobre una barra.
5. Uniformar la fuente solo después de revisar las excepciones individuales y la herencia desde Project Settings.

**API documentada:** IntGrflayer dispone de operaciones por grupo:

| Método | Qué modifica |
|---|---|
| `AdaptWidth(objectType, symbolName)` | Ancho según el máximo texto del grupo |
| `Align(alignPos, objectType, symbolName)` | Alineación dentro de la caja: 0 izquierda, 1 centro, 2 derecha |
| `ChangeRefPoints(parentRef, textBoxRef, objectType, symbolName)` | Anclajes del padre y de la caja |
| `ChangeFont(fontName, fontSize, fontStyle, objectType, symbolName)` | Fuente del grupo seleccionado |
| `ChangeWidthVisibilityAndColour(...)` | Ancho en caracteres, visibilidad y color del grupo |
| `Reset(mode, objectType, symbolName)` | Restablece ajustes individuales según el modo; no usar como limpieza general sin revisar las excepciones |

`objectType`: 0 nodos y ramas; 1 nodos; 2 ramas; 3 dependiente del símbolo. `symbolName` solo aplica al tipo 3; es opcional en las firmas documentadas. **Align no distribuye ni alinea físicamente subestaciones.**

Para `ChangeRefPoints`, usar los argumentos documentados `parentRef` y `textBoxRef`. Los puntos forman esta distribución:

```text
4 3 2
5 0 1
6 7 8
```

No asignar estos códigos directamente a otros atributos sin verificar que comparten la misma convención. El texto explicativo y el orden de argumentos de algunas páginas del manual pueden resultar confusos; una prueba visual localizada debe confirmar el efecto.

## Capas, contraste y líneas guía

**Interfaz observada:** View → Layers separa resultados, etiquetas, elementos, anotaciones, leyendas y otras capas. El orden de las capas controla qué queda encima. Transfer permite llevar configuraciones a otros diagramas; no se ensayó esa transferencia.

Organizar anotaciones, resaltados y nombres en capas que permitan revisar cada conjunto. Evitar resolver densidad ocultando una apertura o conexión necesaria para interpretar la topología.

**Interfaz observada:** las cajas admiten fondo opaco o transparente. El fondo opaco evita que una línea atraviese las letras, pero puede ocultar un símbolo real. Primero resolver ubicación y anclaje; después elegir el fondo.

Las cajas generales vinculadas pueden mostrar una línea hacia su objeto. SetVitxt tiene una página Reference Line para estilo, ancho, puntos y punta de flecha. Preferir esas relaciones nativas a líderes dibujados sin vínculo cuando la anotación debe seguir al equipo.

En Element Details, las flechas nativas permiten indicar dirección de potencia activa o reactiva. Una flecha de conexión y una de dirección de flujo son controles distintos. Verificar cuál se muestra y con qué resultados.

## Exportación vectorial y revisión reproducible

**Exportación probada:** Export Diagram ofrece SVG, PDF, EMF, WMF y formatos raster. Permite seleccionar un recorte o el diagrama completo. Revisar siempre el recorte en la vista previa: no asumir que coincide con toda el área visible anterior. En la prueba, al cambiar PNG por SVG cambió la presentación del recorte.

El SVG de prueba conservó:

- Grupos correspondientes a capas.
- Identificadores con nombres/rutas de elementos eléctricos.
- Trazos, símbolos, colores y textos con coordenadas, fuente y transformaciones de giro.
- El clip del recorte, incluso con geometría exterior presente en el XML.

Esto permite desarrollar una auditoría fuera de PF de textos abreviados, tamaños de fuente, capas, candidatos a recorte y posibles colisiones. **No basta comparar coordenadas x/y de texto:** hay que aplicar transformaciones, anclas, fuente, clipping y orden de dibujo. El tamaño real del texto debe obtenerse del render o de un motor tipográfico compatible.

No asumir que los IDs SVG son identificadores únicos estables entre proyectos o exportaciones. Validar duplicados y contrastar la ruta con los objetos de PF antes de aplicar un cambio. Tampoco reimportar el SVG completo suponiendo que reconstruirá una red eléctrica: el intercambio de anotaciones no equivale a crear conexiones eléctricas.

**API documentada:** `ComWr.ExportGraphicTab(graphicTab, filename)` exporta una pestaña de diagrama o plot; retorna 0 en éxito y 1 en fallo. Ensayar cada formato y recorte antes de automatizar capturas en lote. Las propiedades auxiliares del comando deben descubrirse en la versión instalada; no inventarlas.

La exportación de una capa mediante `IntGrflayer.Export(path, OpenDialog=0)` admite SVG/TXT y es distinta de exportar la página completa. `IntGrfgroup.Export` admite SVG. Son útiles para bibliotecas de anotaciones y grupos.

## Anotaciones sin editar cadenas grandes a ciegas

**API documentada:** IntGrflayer ofrece `GetNumberOfAnnotationElements`, `GetAnnotationElement`, `AddAnnotationElement`, `UpdateAnnotationElement`, `RemoveAnnotationElement` y `CheckAnnotationString`, usando IntDplmap para intercambiar atributos.

Preferir cambios dirigidos a un elemento conocido a reemplazar íntegramente annotationElementsStr. Verificar las claves del mapa con un elemento real. Las geometrías compuestas tienen limitaciones: Get/Update actúan sobre el primer componente y Add no admite ciertas composiciones, como Polyline with arrow. No suponer que una flecha compuesta es una sola geometría editable.

## Creación de diagramas a partir del modelo existente

**Manual de usuario:** Diagram Layout Tool permite generar diagramas, ampliar vecindarios e insertar elementos existentes. Incluye separación de nodos, representación de subestaciones, expansión del área y tratamiento de ramas.

Usarlo para un primer dibujo o para incorporar elementos ausentes; no presentarlo como solución probada de todos los solapes de un unilineal existente. Una base automática necesita composición editorial posterior.

El manual distingue Paste y Paste Graphically Only: el primero puede crear nuevos objetos de datos. Para crear otra vista del mismo sistema, utilizar una copia del diagrama o representación gráfica de elementos existentes, sin duplicar inadvertidamente la red.

## Gráficas de resultados

**Interfaz observada:** Insert → Plot ofrece, entre otros, curvas, barras, barras binarias, dos ejes Y, vectores y curvas XY. Se inspeccionó el selector y se canceló sin crear páginas.

**Manual de usuario:**

- Las series identifican archivo de resultados, elemento y variable. Con selección automática pueden tomar el último archivo de resultados activo; para comparaciones reproducibles es preferible fijar la procedencia de cada serie.
- Los ejes pueden ser locales, compartidos por página o compartidos por escritorio. Usar escalas comparables para paneles de escenarios; no permitir que el autoescalado sugiera diferencias inexistentes.
- La leyenda admite esquinas, columnas, posición flotante, márgenes y relleno. Esto cubre buena parte de las preferencias de leyendas discretas y separadas del contenido.
- Los ejes permiten decimales fijos. Los estilos se guardan como Plot Style Templates en Settings del proyecto.
- Export Shown Data utiliza el intervalo visible. Un zoom puede cambiar la porción de datos exportada.

**API documentada:** GrpPage y PltLinebarplot ofrecen métodos para estilos, ejes y series. No se ejecutaron en esta sesión. No extrapolar firmas antiguas de SetVi a estas clases sin consultar su documentación.

Para gráficos editoriales complejos del informe, conservar los datos y una receta reproducible aunque el diseño final se produzca fuera de PF. Elegir la herramienta por el resultado requerido; una imagen vectorial no garantiza edición semántica de todos sus objetos dentro de Word.

## Próxima mejora a ensayar

Un flujo completo sobre **una copia** del unilineal: flujo identificado → inventario gráfico → recorte SVG → auditoría de ancho/anclajes/solapes → propuesta de cambios → corrección localizada → mismo flujo → comparación del dibujo y del estado eléctrico. No declarar el proceso completo validado por haber inspeccionado sus controles.

## Fuentes locales

- `Help/UserManual_en.pdf`: §§10.3.5–10.3.7, 10.3.12, 10.5–10.7, 12.6 y 19.8. Páginas PDF 153–159, 168, 173–177, 239–244 y 383–403.
- `Help/PythonReference_en.pdf`: ComWr (PDF 407), IntGrf (510–511), IntGrflayer (512–521), IntGrfnet (521–522), GrpPage (desde 475), PltLinebarplot (desde 595). La numeración impresa difiere de la del visor PDF.
- Controles observados en `07-Sist154-66kV.IntGrfnet` de la instalación PF 2025 SP4 del proyecto Cumbres. Los valores de ese diagrama son ejemplos de contexto, no una plantilla universal.
