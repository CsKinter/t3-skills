# DIgSILENT | diagramas nativos

## Separar geometría y modelo eléctrico

Identificar el diagrama y los objetos gráficos asociados a los elementos eléctricos, con rutas completas y clases. Un nombre visible no basta: puede repetirse entre elementos, gráficos o páginas. Confirmar terminales y conexiones reales antes de mover rutas.

**Verificación.** Respaldar el diagrama y capturar el estado eléctrico antes de editar. Un cambio puramente gráfico debe conservar conexiones, aperturas, despachos, controles y resultados dentro de la tolerancia correspondiente. No arreglar un solape alterando una conexión eléctrica.

Preferir una copia del diagrama. Ampliar la página si esa es la preferencia del usuario; no dividir en páginas nuevas sin considerar cómo quiere seguir la red.

## Orden de trabajo

1. Ejecutar el flujo del caso y mostrar las cajas de resultados reales.
2. Ordenar las bandas de tensión y las subestaciones principales.
3. Ajustar barras paralelas y puntos de conexión.
4. Enrutar líneas y transformadores.
5. Ubicar símbolos, nombres, flechas y cajas de resultados.
6. Revisar el conjunto y después sectores a escala de lectura.
7. Repetir el flujo y comprobar que el cambio fue solamente gráfico.

**Preferencia.** Usar ajuste a la cuadrícula cuando sea posible. Descubrir la cuadrícula, coordenadas, escalas y giros del diagrama y de la versión instalada; no imponer un paso en milímetros aprendido de otro archivo. Alinear símbolos, barras, rutas y etiquetas sin forzar un snap que rompa conexiones.

## Geometría útil

- Barras paralelas de una subestación con longitudes coherentes y suficientes para todas sus conexiones. Contar los extremos de cada línea en ambas barras; no dejar extremos colgantes.
- Entradas perpendiculares y rutas ortogonales cuando mejoren la lectura. Separar circuitos paralelos y sus cajas; no superponerlos para ahorrar espacio.
- Mover cada conjunto completo: símbolo, conectores, puntos de quiebre, texto y cajas. Un transformador que se desplaza solo puede quedar visualmente desconectado.
- Reservar espacio entre transformadores y cajas de resultados. No ocultar el símbolo bajo su propia etiqueta.
- Mantener rutas independientes para alimentadores distintos. No insinuar una conexión con un cruce sin unión ni esconder un punto de unión real.
- Centrar etiquetas sobre su barra o elemento y acercar los rótulos de salidas «Hacia…» a sus flechas. Evitar que caigan sobre barras, símbolos o stubs.
- Si dos circuitos o alimentadores tienen muchas cajas, escalonarlas en columnas alineadas con líderes claros.

No compactar solo mediante reducción de fuente. Reducir rutas innecesarias y espacios muertos antes de hacer ilegible un nombre. Las cajas de un flujo corrido pueden exigir más espacio que el diagrama sin resultados.

## Revisión sistemática

Revisar primero toda la página y luego una cuadrícula de sectores con algo de solape entre ellos. El número de sectores depende del tamaño; no hay una obligación de usar dieciséis.

Auditar texto contra texto, líneas contra texto, símbolos contra cajas y contenido contra los límites de página. Una revisión geométrica automática ayuda a localizar problemas, pero el render final decide si el circuito se entiende. Repetir únicamente los sectores afectados y sus vecinos después de una corrección.

**Verificación.** Toda captura final debe corresponder al caso identificado con flujo corrido. Guardar la evidencia del caso, contingencia y estado de resultados; no reutilizar una foto visualmente parecida de otro despacho.

## API y control visual

Las clases de gráficos y sus atributos dependen de PowerFactory. Usar documentación disponible y las recetas técnicas verificadas de la instalación antes de modificar objetos. Las skills de PowerFactory existentes pueden aportar ese detalle; esta guía no garantiza nombres de atributos ni métodos de otra versión.

Si hay control de escritorio disponible para PowerFactory, usarlo para revisar selección, zoom, rutas y resultado visual. La API o el puente sirven para precisión y repetibilidad; la pantalla sirve para comprobar la lectura real. No declarar acceso a la aplicación si la herramienta solo controla un navegador.

## Herramientas verificadas de PF 2025

Consultar [Gráficas y diagramas | descubrimientos](powerfactory-graficos.md) para los controles observados y las firmas documentadas de SnapToGrid, Orthogonalise, anchos, anclajes, capas, anotaciones y exportación SVG. El [catálogo de parámetros confirmados](parametros-confirmados.md) separa atributos de significado conocido de candidatos pendientes.

Priorizar el ancho y anclaje real de las cajas antes de reducir la fuente. Verificar la herencia de fuentes del proyecto y las excepciones individuales. La casilla Snap habilitada no acredita que todos los objetos existentes estén alineados. El SVG permite auditar geometría y texto, pero conserva las abreviaciones y solapes del dibujo de origen.
