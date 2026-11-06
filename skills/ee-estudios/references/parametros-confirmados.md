# PowerFactory | parámetros de significado confirmado

Referencia de consulta para lectura y automatización. Confirmado en **PowerFactory 2025 SP4** mediante tooltips, documentación técnica de esa instalación y las comprobaciones indicadas. Fecha de consolidación: 20-10-2026.

Cada entrada identifica el objeto propietario y el significado del campo. No es una lista de valores recomendados ni autoriza su modificación. Consultar la unidad actual mediante `GetAttributeUnit`: la configuración de unidades del proyecto puede afectar lo que devuelve la API.

## Líneas | tipo

| Objeto | Parámetro | Qué es y qué hace | Unidad habitual |
|---|---|---|---|
| TypLne | `sline` | Corriente nominal del tipo. Para un cable, corresponde al campo de instalación en suelo; la instalación en aire puede utilizar InomAir | kA |
| TypLne | `InomAir` | Corriente nominal alternativa que utiliza un cable configurado para instalación en aire | kA |
| TypLne | `tmax` | Temperatura máxima de operación del conductor. Puede utilizarse para corregir la resistencia cuando la opción del cálculo selecciona esa temperatura | °C |

La capacidad térmica ambiental y la corrección de resistencia son conceptos distintos. No cambiar tmax a la temperatura ambiente de una ficha de ampacidad por semejanza de nombres.

## Líneas | elemento

| Objeto | Parámetro | Qué es y qué hace | Unidad habitual |
|---|---|---|---|
| ElmLne | `fline` | Factor de reducción que interviene en la capacidad nominal de la línea cuando no hay un objeto térmico que sustituya esa base | Adimensional |
| ElmLne | `Imaxlim` | Corriente máxima permisible adicional. Acota la corriente nominal usada para calcular la carga, considerando la cantidad de líneas paralelas | kA |
| ElmLne | `Inom_a` | Valor actual de corriente nominal mostrado en Basic Data. Es una lectura del valor que expone el elemento; no reemplaza la revisión de factores, pRating, Imaxlim y resultados | kA |
| ElmLne | `Top` | Temperatura operativa del conductor. La corrección de resistencia utiliza esta selección cuando así lo establece el comando de cálculo | °C |
| ElmLne | `pRating` | Referencia a un objeto IntThrating que define la capacidad térmica utilizada para calcular la carga | Objeto |
| ElmLne | `commissionDate` | Fecha de puesta en servicio guardada en Description. Es un dato de descripción: una fecha por defecto no acredita la entrada real de la instalación | Fecha/hora |

La documentación de líneas PF 2025 establece, por extremo, `Inom = min(Inom_previa, Imaxlim × nlnum)`. La formación de Inom_previa depende del tipo, instalación, paralelos, factores y posible objeto térmico; no reducir toda la lógica a leer sline.

## Transformadores de dos devanados

| Objeto | Parámetro | Qué es y qué hace | Unidad habitual |
|---|---|---|---|
| TypTr2 | `strn` | Potencia nominal asignada al tipo de transformador | MVA |
| TypTr2 | `nt2ph` | Tecnología del modelo: 1 = retorno por tierra de un hilo; 2 = monofásico; 3 = trifásico | Código |
| TypTr2 | `utrn_h` | Tensión nominal del devanado de alta tensión | kV |
| TypTr2 | `utrn_l` | Tensión nominal del devanado de baja tensión | kV |
| ElmTr2 | `ratfac` | Factor de capacidad asignado al elemento, independiente del nombre del tipo | Adimensional |
| ElmTr2 | `Snom_a` | Potencia nominal actual mostrada por el elemento | MVA |

Leer campos y terminales: el texto del nombre puede contener una tensión antigua. Para bancos, comprobar la correspondencia entre potencia por unidad, potencia del conjunto y tecnología; no multiplicar automáticamente por tres.

## Flujo de carga | ComLdf

| Parámetro | Qué es y qué hace | Valores confirmados |
|---|---|---|
| `i_power` | Selecciona la formulación Newton-Raphson | 0 = ecuaciones de corriente; 1 = ecuaciones de potencia clásicas |
| `iopt_tem` | Selecciona la temperatura utilizada para las resistencias de líneas y cables | 0 = 20 °C; 1 = máxima de operación; 2 = operativa; 3 = temperatura indicada |
| `bPlimGenst` | Incluye los generadores estáticos entre los modelos a los que se aplican límites de potencia activa | Casilla desactivada/activada |
| `bQlimGenst` | Incluye los generadores estáticos entre los modelos a los que se aplican límites de potencia reactiva | Casilla desactivada/activada |
| `iopt_limScale` | Selecciona la consideración del factor de escalamiento de límites reactivos | Casilla desactivada/activada |

Los selectores por clase no sustituyen la habilitación general de límites ni los controles definidos en las máquinas. Identificar el comando por ruta: el original y una copia utilizada por un driver pueden tener configuraciones diferentes.

## Límites térmicos nativos | IntThrating

| Parámetro | Qué es y qué hace | Unidad o valores confirmados |
|---|---|---|
| `iopt_unit` | Define la unidad de los valores del objeto térmico | 0 = MVA; 1 = kA; 2 = % |
| `ContRating` | Capacidad térmica continua utilizada cuando no hay dependencias ambientales habilitadas | La seleccionada en iopt_unit |
| `contRatMat` | Tabla de capacidades continuas para las dependencias ambientales configuradas | La seleccionada en iopt_unit |
| `optTa` | Habilita dependencia respecto de la temperatura ambiente | Casilla desactivada/activada |
| `optWind` | Habilita dependencia respecto de la velocidad de viento | Casilla desactivada/activada |
| `optSolar` | Habilita dependencia respecto de la irradiancia solar | Casilla desactivada/activada |
| `table_valid` | Habilita la definición de capacidades térmicas de corta duración | Casilla desactivada/activada |

Cambiar iopt_unit no convierte automáticamente los números existentes. Las condiciones provienen de la estación asociada o de los valores por defecto documentados si falta esa asociación. En PF 2025, la selección ambiental de este objeto utiliza intervalos; no equivale a interpolación continua. La capacidad temporal no se aplica automáticamente por ejecutar un flujo manual con una línea abierta.

## Identificación y procedencia

Estos campos fueron observados en TypLne; otros objetos admiten campos equivalentes según su clase.

| Parámetro | Qué es y qué hace |
|---|---|
| `for_name` | Clave externa del objeto. La API dispone de SearchObjectByForeignKey para buscarla dentro del proyecto activo |
| `dat_src` | Campo de procedencia de datos mostrado como Data source |
| `appr_status` | Estado de aprobación interna de PF: 0 = Not Approved; 1 = Approved |

La aprobación interna no equivale al estado de validación de Infotécnica. Conservar los identificadores existentes y su significado antes de proponer otro esquema de trazabilidad.

## Diagramas | IntGrfnet

Estos campos se identificaron en **Diagram Settings** mediante hover. Son ajustes gráficos; no constituyen parámetros eléctricos.

| Parámetro | Qué es y qué hace | Valores confirmados |
|---|---|---|
| `snap_on` | Habilita el ajuste de elementos a la cuadrícula de dibujo | Casilla desactivada/activada |
| `ortho_on` | Selecciona el modo de trazado de las conexiones | 0 = no ortogonal; 1 = ortogonal; 2 = semiortogonal |
| `rNodWid` | Factor de ancho de puntos y trazos de nodos y barras | Factor gráfico |
| `rDefOffBr` | Distancia inicial de equipos de un terminal dibujados haciendo clic sobre la barra | En puntos de cuadrícula, según el manual |
| `iTrans` | Fondo de las cajas de resultados | 0 = opaco; 1 = transparente |
| `iSmallRes` | Habilita la representación compacta de resultados sobre líneas de conexión | Casilla desactivada/activada |
| `iShowLineTB` | Muestra la línea entre cajas de texto generales y sus objetos referenciados | Casilla desactivada/activada |

No interpretar `snap_on = 1` como certificación de que todas las coordenadas existentes cumplen la cuadrícula. El método `IntGrf.SnapToGrid()` actúa sobre un objeto existente; requiere su página activa y Snap habilitado. La escala de la cuadrícula debe verificarse en cada diagrama.

## Capas | SetLevelvis

Campos identificados en **View → Layers → Element Details**. La clase está documentada en el manual de usuario y en PythonReference.

| Parámetro | Qué es y qué hace | Valores confirmados |
|---|---|---|
| `symbLdfArrows` | Habilita las flechas nativas de dirección del flujo | Casilla desactivada/activada |
| `iArrow` | Selecciona qué variable determina la dirección de esas flechas | 0 = potencia activa; 1 = potencia reactiva |

El selector contiene además modos de protección. Aquí se documentan únicamente los dos modos pertinentes a los flujos de este trabajo. Una flecha requiere resultados vigentes para interpretarse como evidencia del caso.

## Cajas de texto y resultados | SetVitxt

Campos identificados mediante **Edit Graphic Object** sobre una caja y hover. Los códigos de anclaje no se deducen por el nombre del campo.

| Parámetro | Qué es y qué hace |
|---|---|
| `chars` | Ancho expresado en caracteres por línea. Un ancho insuficiente puede abreviar el contenido mostrado |
| `iOrient` | Alineación del texto dentro de su caja; no es el ángulo de rotación |
| `iBoxRefPt` | Punto de referencia de la propia caja usado para su anclaje al objeto |
| `vlpos` | Posición de la caja a lo largo de la línea de conexión |
| `iKeepPos` | Opción Fix Position de la caja |

La ubicación depende también del objeto padre, su anclaje y el giro. No trasladar una caja suponiendo que un solo campo representa coordenadas absolutas de página. Los métodos de capas para adaptar anchos y anclajes están descritos en [Gráficas y diagramas | descubrimientos](powerfactory-graficos.md).

## Evidencia

Tooltips observados el 20-10-2026, referencias locales PF 2025 de líneas, transformadores y Thermal Ratings, User Manual y PythonReference de esa instalación. Los identificadores pRating, contRatMat y utrn_h/utrn_l tienen respaldo documental; no se presentan como nombres obtenidos por hover en esta sesión.

El catálogo experimental del proyecto conserva otras observaciones y candidatos. Aquí se incluyen únicamente campos cuyo significado puede describirse con el respaldo disponible. La ausencia de una entrada no implica que el atributo no exista.
