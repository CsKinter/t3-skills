# Informe | figuras y composición visual

## Diseñar desde el mensaje

Definir primero qué comparación o mecanismo debe entenderse. Cada figura debe permitir identificar el estado de operación, la topología, la contingencia, el elemento limitante y la consecuencia que se discute, según su propósito. Una ilustración conceptual no necesita todos los resultados; una comparación cuantitativa debe conservar los valores que sustentan su lectura.

**Preferencia.** Figuras editables en Word cuando la edición posterior importe: formas, conectores, rótulos e iconos nativos. Utilizar gráficos reproducibles para series y resultados; PNG/PDF o capturas de PowerFactory son adecuados como evidencia, sin prometer que serán editables.

## Geometría y legibilidad

- Alinear barras, símbolos, etiquetas y cajas con una geometría consistente. Centrar cada texto respecto de su elemento, no respecto de un espacio vacío cualquiera.
- Acercar flechas a sus líneas y rótulos al elemento correspondiente. Reservar espacio para nombres largos mediante saltos de línea antes de reducir la fuente.
- Revisar colisiones de texto con texto, texto con líneas, símbolos y bordes. Los elementos transparentes también pueden ocultar o confundir.
- Usar el espacio disponible: ampliar una figura o darle una página propia cuando la red completa lo necesite. No comprimir una red extensa en una columna estrecha.
- Mantener la extensión de red necesaria para la lectura. Un recorte no debe eliminar una conexión, apertura o rama que explica el resultado.
- En separaciones de red abreviadas, usar una interrupción visual coherente e identificar el destino. No sugerir continuidad eléctrica donde hay un punto abierto.

Usar «|» para separar conceptos o valores dentro de una etiqueta. No usar el punto medio como separador. Esto no prohíbe las listas ni los puntos suspensivos con su función habitual.

## Código visual

**Preferencia.** Mantener el proyecto en negro o con un énfasis sobrio; evitar rojo si ese color también significa restricción, falla o sobrecarga. No destacar todo al mismo tiempo.

La paleta eléctrica depende del estudio y de las convenciones acordadas. Cuando 154 kV deba conservar el rojo, un rojo profundo para la red y naranja intenso para la sobrecarga pueden separarlos bien. Registrar los colores usados; no imponer códigos hexadecimales de otro proyecto ni transmitir significado solo mediante color.

Para las plantas, un colector corto con una única bajada puede simplificar un grupo de iconos, siempre que no falsifique su conexión. Ubicar cada BESS en su nivel de tensión real; no agruparlo en otra barra por proximidad gráfica. Los iconos deben distinguir eólico, solar y batería incluso en tamaño de lectura.

Una flecha verde hacia abajo puede representar inyección y una roja hacia arriba carga, si la leyenda fija esa convención. Separar esos colores de los empleados para barras de resultados. Una planta fuera del escenario puede mostrarse en gris con una causa breve; una planta restringida a cero debe conservar una señal distinta. No representar ambas como «0» sin contexto.

Sol o luna discretos ayudan a identificar el escenario. Son un apoyo, no reemplazan la etiqueta ni las condiciones del caso.

## Resaltes, restricciones y leyenda

Una zona de sobrecarga debe abarcar el elemento físico correspondiente, incluida su línea cuando proceda, no únicamente su flecha de flujo. Preferir rectángulos de esquinas levemente redondeadas, relleno tenue y contorno legible. Evitar cajas grandes sin un objeto claro.

La etiqueta puede quedar fuera, próxima y unida por un líder corto. Si MW y porcentaje ya comunican la condición, no repetir «Sobrecarga» dentro de todas las cajas.

En comparaciones antes/después, resaltar discretamente las plantas cuyo despacho cambió y añadir «Restringido» cuando ayude. Aplicarlo a todos los paneles pertinentes. Revisar el sentido del cambio para BESS: una menor carga no es una mayor inyección de generación.

La leyenda debe ser compacta, alineada y con una caja muy sutil. Situarla en un espacio libre del propio diagrama, normalmente una esquina; no tapar la red ni dejar grandes márgenes interiores. Ajustar su tamaño al contenido real.

## Gráficos de despacho

**Preferencia.** Una barra de despacho y un contorno punteado hasta la potencia disponible facilitan comparar el resultado con su referencia. Identificar ambos valores, por ejemplo «43 de 89», sin recargar cada etiqueta.

En gráficos con generación y carga, ubicar el cero entre ambos lados: carga hacia la izquierda e inyección hacia la derecha. Dibujar también el contorno de disponibilidad con el signo correspondiente. No invertir el significado físico al representar una restricción de carga.

Mantener nombre de planta, unidad, referencia y condición del resultado. «Disponible» debe tener una definición inequívoca; no confundir capacidad instalada, recurso disponible y despacho inicial. No calcular el porcentaje de restricción con una base diferente de la declarada.

Un mapa de calor planta × escenario puede sintetizar MW admisibles y porcentaje restringido. Distinguir con gris los casos sin operación desde la construcción del escenario. Añadir la base de cálculo y no confiar solo en el color. Usarlo cuando el detalle de todos los proyectos aporte; el cliente puede necesitar solo la síntesis de su proyecto.

## Comparaciones y ampliaciones

Los paneles antes/después deben compartir escala, geometría y extensión de red; cambiar solo lo que cambia eléctricamente o se necesita destacar. Seleccionar la contingencia que limita el despacho final cuando ese sea el propósito. No usar otra contingencia solo porque su esquema se ve más llamativo.

Para un zoom, identificar una región de origen y el recuadro de detalle mediante una clave común y conexiones breves, o una franja/área de transición tenue. Evitar líderes largos con codos para esquivar todo el contenido. El recurso exacto debe probarse en una muestra antes de extenderse. No elevar una variante aprobada sin especificación gráfica a una plantilla universal.

En mapas geográficos, mostrar el entorno suficiente y distinguir claramente conexión actual y alternativa futura. Si se informa una distancia, aclarar si es recta geográfica, recorrido o longitud eléctrica y conservar su fuente/cálculo. La cercanía geográfica y las vías de evacuación deben tener representaciones distintas. Conservar los créditos del mapa que correspondan, aunque se retire una referencia bibliográfica redundante.

## Página y verificación

Alternar texto con figuras flotantes compactas cuando la información quepa con claridad. Mantener los gráficos de despacho pequeños junto al texto si siguen siendo legibles. Dar ancho completo o página propia a redes extensas y comparaciones cargadas. Evitar páginas dominadas por muchas figuras sin un párrafo que guíe la lectura.

El grupo completo y su leyenda/caption deben quedar dentro de márgenes. Medir la posición respecto de la referencia del anclaje: página, margen o columna. El ancho correcto por sí solo no garantiza la posición correcta. Mantener encabezados con su primer párrafo y pies próximos a su figura.

Verificar el Word guardado y el PDF exportado a tamaño real de lectura. Revisar también las páginas vecinas: una figura flotante puede generar huecos, títulos huérfanos o invadir otra columna. No dar por corregido un solape solo porque el código usa coordenadas diferentes.
