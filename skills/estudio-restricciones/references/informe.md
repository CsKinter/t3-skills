# El informe de restricciones

Contenido y estructura. La edición del Word está en `informe-ee`, la prosa en `redaccion` (leer su
`references/informe-cliente.md` antes de escribir) y el flujo de revisiones en `informe-ee/references/revisiones.md`.

## 1. Esqueleto

Tal como quedó el informe de Cumbres en su revisión final. Es el punto de partida, no un molde: los cambios de
estructura se muestran primero como esqueleto en el chat.

| Cap. | Función | Lleva |
|---|---|---|
| 1 Resumen ejecutivo | Lectura continua, sin subtítulos. La respuesta para el proyecto en las primeras líneas. Cierra con un punteo breve | Tabla de escenarios y figura de despacho admisible frente a disponible |
| 2 Descripción del proyecto | Mapa de orientación. Distingue cercanía geográfica de posición eléctrica | Ubicación y esquema eléctrico |
| 3 Adecuación de base de datos | Qué obras y capacidades sostienen el estudio | Inventarios de obras, de proyectos y de líneas |
| 4 Criterios | Escenarios, recurso, contingencias por punto de conexión, criterio de restricción | Tablas de recurso, escenarios y contingencias. Diagrama del criterio |
| 5 Análisis base | Delimitación eléctrica de la zona y topología de operación | Capturas diferenciales |
| 6…n Resultados | Un capítulo por punto de conexión: contexto, impacto del proyecto, escenarios, resumen | Ver plantilla |
| Conclusiones | Abren con el resultado principal | — |
| Referencias | | |

**Capítulo de resultados**: contexto → impacto del proyecto (una tabla sin y con proyecto para todos los escenarios) →
escenarios diurnos → escenarios nocturnos → resumen. El contexto no anticipa el elemento ni la contingencia que
gobiernan.

**Plantilla de escenario**, idéntica en todos: título con el nombre del caso («E01 | Día, BESS en carga») y debajo
tres subtítulos iguales: «Condición sin restricción», «Contingencia crítica» y «Restricción aplicada».

**Anexo selectivo**: secuencia resumida por escenario, verificación final y despacho por central, con el mismo
universo y orden de centrales en todas las tablas. Las matrices completas de factores y las extracciones quedan como
respaldo interno.

Con varios puntos de conexión, decidir temprano si van en un informe o en varios. No dejar un capítulo de dos líneas
para un informe futuro: se anuncia en el alcance.

## 2. Contenido

- **Tres cifras que no se confunden**: recurso disponible, despacho admisible y restricción. Decir «despacho admisible
  bajo las condiciones de cada escenario», no «máxima operación admisible».
- **Tres lecturas que no se confunden**: el aporte agregado de un grupo, la influencia por MW de cada central, y el
  despacho del proyecto frente al del conjunto. Un aporte neto pequeño no prueba baja sensibilidad individual.
- **Un solo estado de cálculo por cifra.** Si conviven estado inicial y final, se rotula cuál se muestra.
- **Cada figura muestra el límite que fija el resultado.** Una figura que explica un mecanismo con despacho fijo no se
  lee como demostración del despacho final. Deben verse la contingencia y el elemento que impiden recuperar generación.
- Una afirmación no va más lejos que su prueba: «no quedan sobrecargas» se acota al conjunto supervisado.
- Dos figuras de red extensas seguidas deben cumplir funciones distintas.

## 3. Tablas y cifras

- Una tabla sin y con proyecto declara su denominador. La carga respecto de la línea no es la carga respecto de su
  compensación serie.
- Los incrementos se calculan sin redondear y se pone una nota de redondeo bajo la tabla.
- Los rangos del texto se derivan de los datos vigentes, no de memoria.
- Antes de aprobar una barra apilada, comprobar que cierra el total: aportes negativos incluidos, todas las categorías,
  grupos rotulados por su ubicación real y no por la carpeta del modelo. El residuo no se explica como pérdidas si el
  cálculo no las tiene.
- Un mismo elemento se llama igual en tablas y prosa.

## 4. Origen de las cifras

Antes de editar el informe tras un recálculo, armar una **matriz de origen**:

| Sección / tabla / figura | Punto de operación | Archivo y clave | Estado |
|---|---|---|---|
| … | irrestricto o cierre | ruta + clave del JSON | vigente / por recalcular / fuera hasta resolver |

- Una base de operación por uso: el irrestricto alimenta contexto e impacto, el cierre alimenta las figuras y tablas de
  restricción.
- Entradas congeladas con su hash. Las cifras superadas se listan como «no se usan».
- Una ficha por restricción con estado inicial, estado final, condición de red, carga y factores, para que el anexo
  corresponda al estado que se publica.

## 5. Qué no va al cliente

- Slack, balance, compensación de potencia y ajustes de convergencia.
- Nombres de revisores y acuerdos internos. Se expone el criterio y su fuente, sin atribuir a una norma lo que fue un
  acuerdo de EE.
- Otros estudios usados para justificar una hipótesis, y la conciliación entre estudios.
- Comprobaciones de vigilancia fuera del alcance (por ejemplo, el troncal en un estudio local).
- «Modelado / no modelado», nombres de variations, rótulos de trabajo.
- El fundamento económico de una prioridad, salvo que Vicente lo pida.

## 6. Lista de chequeo antes de entregar

Errores que las revisiones encontraron más de una vez:

- [ ] Fecha, hora y bloques del texto iguales a los del cálculo.
- [ ] Cifras del cuerpo iguales a las del anexo, o con el estado rotulado.
- [ ] Toda instalación decisiva aparece en los inventarios.
- [ ] Cabeceras de tabla coherentes con sus valores.
- [ ] Factores medidos en el estado que se publica.
- [ ] Ningún capítulo anticipa un resultado que se prueba después.
- [ ] Ninguna generalización más amplia que el conjunto evaluado.
- [ ] Pies de figura contrastados con su cifra.
- [ ] Sin figuras que tapen leyendas, frases partidas entre páginas ni títulos de escenario separados de su inicio.
- [ ] Tras un reemplazo masivo de texto: negritas que no queden cortadas a media palabra.
- [ ] Texto centrado dentro de las cajas de las figuras.
- [ ] Referencias cruzadas sin destinos rotos, índice y tablas de figuras actualizados.
- [ ] Búsqueda final de `redaccion` más: slack, balance y nombres de personas.
