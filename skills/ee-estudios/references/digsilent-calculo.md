# DIgSILENT | cálculo, restricciones y topologías

Para identificar opciones y nombres internos desde la aplicación real, consultar [descubrimiento con interfaz y API](powerfactory-descubrimiento.md). Verificar el comando exacto utilizado por los scripts y las enumeraciones de la versión instalada.

## Estado reproducible

Antes de calcular, registrar proyecto, caso de estudio, escenario de operación, fecha/hora de estudio, variaciones y etapas activas, configuración de flujo, despachos, aperturas y modos de control relevantes. Conservar una copia o respaldo y un estado inicial recuperable.

Identificar objetos por ruta completa, clase y terminales, no solo por nombre. Comprobar unidades y semántica de atributos en la versión instalada. Una lectura de caché o un resultado de otro caso no equivale a un cálculo nuevo.

Las variaciones no aíslan necesariamente bibliotecas compartidas. Al modificar tipos o características, evaluar copia y reasignación de referencias dentro de una etapa de registro verificada. Una modificación a un Typ* compartido puede afectar varios casos. Confirmar por lectura posterior qué quedó escrito y dónde.

## Flujo válido

**Verificación.** Un código de ejecución correcto es necesario, pero no suficiente. Revisar plausibilidad de flujos, balances, slack, límites P/Q, controles, suministro y magnitudes que indiquen una solución física inadecuada.

Preservar los modos de control de tensión de renovables que el estudio haya definido para contingencias. No resolver problemas numéricos cambiando silenciosamente control, límites reactivos o despacho. Si se requiere un cambio, documentar su justificación y recalcular las comparaciones afectadas.

Una formulación basada en corrientes puede ayudar en determinados casos problemáticos; no convertir una opción concreta del solver en regla universal. Verificar su significado, compatibilidad y efecto con el modelo y versión disponibles. No aceptar una solución solo porque elimina una sobrecarga inesperada.

Mantener separados tres diagnósticos: falta de convergencia, solución físicamente poco plausible y sobrecarga real. Cada uno requiere evidencia diferente.

## Límites térmicos

Evaluar corriente y capacidad efectiva del circuito con sus condiciones aplicables. La potencia activa por sí sola no determina la carga térmica: importan tensión y reactivos. Verificar qué base usa el porcentaje mostrado por PowerFactory y si incluye el equipo limitante del terminal.

Una corrección de parámetros no demuestra automáticamente que existan MW adicionales de despacho. Primero verificar el equipo y el límite; después ejecutar el ciclo de restricción y sus contingencias. Consultar [Parámetros SEN](parametros-sen.md).

## Ciclo de restricción

Definir explícitamente en la configuración del estudio:

- Casos iniciales y contingencias dentro de alcance.
- Reglas de participación, prioridades y prorrata, con su base de capacidad.
- Tratamiento de carga y descarga de BESS y límites de recurso.
- Margen térmico objetivo y tolerancias numéricas.
- Controles de generación y condiciones que permanecen fijas.

No copiar de otro proyecto porcentajes de participación, escalones MW ni un margen final de carga. La prorrata tampoco significa siempre recortar el mismo porcentaje del despacho inicial: verificar la formulación adoptada.

Registrar cada paso con el elemento que gobierna, contingencia, valor anterior/posterior y despacho actualizado. Una segunda limitación puede reducir más el despacho y dejar el primer elemento por debajo de su valor intermedio. El texto y las figuras finales deben usar el mismo estado, sin mezclar cierre de un paso con resultado definitivo.

Para comparar antes/después bajo una contingencia, precisar si el «antes» es el escenario original o un estado intermedio con ciertos BESS a plena carga. Etiquetarlo sin ambigüedad.

## Sensibilidad topológica

Separar dos preguntas:

1. ¿Cómo cambia la distribución de flujos con un mismo despacho?
2. ¿Cuánto despacho admisible del proyecto permite finalmente la alternativa, tras revisar sus restricciones?

La primera explica el mecanismo; la segunda permite afirmar un beneficio. Eliminar una sobrecarga local puede trasladar el límite a otro circuito sin liberar despacho del proyecto.

Seleccionar cambios y combinaciones por mecanismos eléctricos identificables y viabilidad operacional. Declarar las aperturas conservadas y evitar combinaciones redundantes sin otra pregunta de estudio. Justificar por qué esos interruptores modifican las vías relevantes.

En resultados, utilizar un esquema por topología con la contingencia realmente limitante del despacho final cuando ese sea el objetivo de la sección. Si se muestra otra para explicar un mecanismo, identificarla como tal y no sugerir que fija el resultado.

Resumir para cada alternativa el resultado del proyecto, la explicación física y su equivalencia o mejora respecto de la base. El beneficio de toda la zona y el beneficio del proyecto son resultados distintos.

## Eficiencia sin omitir casos necesarios

Usar experiencia previa para priorizar escenarios y contingencias potencialmente afectados. Conservar un registro de casos ejecutados, descartados y la razón de descarte. Un cambio material de límites, control o metodología requiere revisar todos los casos alcanzados por ese cambio, no solo el aparentemente más severo.

No asumir que factibilidad o convergencia son monótonas con el despacho. Los controles y reactivos pueden cambiar qué contingencia gobierna. Una extrapolación debe quedar identificada hasta comprobarla.

## Puente, restauración y entrega

Hacer operaciones temporales reversibles, restauradas en finally desde una referencia inmutable. Diseñar mutaciones idempotentes cuando sea posible. Una llamada agotada por tiempo puede haber ejecutado el cambio: inspeccionar el estado antes de repetirla.

Un puente lento no es necesariamente una sesión caída. Consultar estado y registros con esperas acotadas; no encadenar mutaciones a ciegas ni pedir reinicio sin comprobar lo disponible. No ejecutar llamadas paralelas sobre el mismo estado mutable.

Al terminar, restaurar el contexto acordado, ejecutar un flujo válido y guardar resultados con identificación de fuente, configuración y fecha. Resumir cambios materiales de despacho, contingencia limitante y supuestos. El detalle de verificaciones internas que no afecta al cliente puede quedar en el respaldo técnico.
