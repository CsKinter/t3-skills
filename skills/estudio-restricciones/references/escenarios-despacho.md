# Escenarios y despacho irrestricto

La mecánica en PowerFactory (copiar escenarios, rondas de reactivo, diagnóstico de convergencia) está en
`powerfactory-python/references/estudio-restricciones.md` §0–1.

Marcas: **[V]** verificación, **[C]** criterio de estudio que se confirma con Vicente.

## 1. Escenarios

- Un escenario combina **bloque horario, condición de demanda, temperatura y estado de los BESS** [C]. En Cumbres
  fueron cuatro: día con BESS en carga, día con BESS en reposo, vespertino con BESS en descarga y madrugada con BESS en
  descarga.
- Cada escenario usa el caso de estudio de su temperatura (con sol o sin sol). **El caso se activa antes que el
  escenario**, porque cambia los límites térmicos [V].
- Para un proyecto solar, revisar qué bloques tienen recurso y cuáles sólo tienen al BESS: el proyecto puede ser
  generador en un escenario y retiro en otro.
- Fecha, hora y bloques del texto deben ser los del cálculo. Es un error que apareció más de una vez.

## 2. Receta del irrestricto

- El irrestricto parte **del perfil original del cliente más una receta escrita**, nunca de un punto a medio
  restringir [V]. Si se corrige algo, se rehace desde los originales.
- La receta dice, por grupo: recurso de eólicas y solares, estado y nivel de los BESS, térmicas, hidráulicas, cómo se
  cubre el balance. Queda escrita en la metodología del proyecto.
- En el irrestricto cada BESS está en su **techo**: la potencia disponible es la nominal y su recorte es resultado del
  ciclo, no un dato de entrada.
- El recurso es un supuesto que se declara junto al resultado. «35 MW de día» es el recurso, no la capacidad de la red.
- Que un punto de operación sea factible y que el reparto sea el que haría el CEN son cosas distintas. El informe no
  afirma equivalencia con el despacho del Coordinador.

## 3. Convergencia, tensión y reactivo

- Objetivo: converger **con límites de P y Q y sin avisos**, con tensiones en banda [V].
- **Soluciones físicas antes que recortar potencia activa** [C]. Escalar reactivo por pasos y por sector. La potencia
  activa se toca sólo cuando el límite es físico, y eso se documenta como resultado del irrestricto.
- Un colapso de tensión fuera de la zona no se arregla con reactivo de la zona.
- Las máquinas en control de tensión se quedan en control de tensión. Reactores de barra se maniobran, los de línea
  no [C].
- Cada punto (irrestricto y restringido) tiene su propio control. Tras ajustar reactivo se revisa la tensión final y
  **se repite el N-1**. Corregir reactivo cambió factores y cargas del irrestricto de forma apreciable.
- Dos generadores con control de tensión en el mismo terminal y consignas distintas hacen que PowerFactory no ejecute
  el flujo. Es el caso típico de un parque con BESS. Ver `powerfactory-python/references/cierre-bd.md`.

## 4. Térmicas e hidráulicas

- **Térmicas** [C]: no se restringen ni se apagan. Las que están bajo su mínimo técnico suben a él y se compensa a
  prorrata del margen.
- **Pasada** [C]: despacho fijo.
- **Embalse en un corredor troncal** [C]: baja antes que los BESS, desde su potencial hasta el **mínimo del bloque**,
  en proporción al margen de cada central. El mínimo técnico de las unidades no es el criterio.
  - El potencial y el mínimo deben salir **de la misma población de datos**. Mezclar el potencial de una fuente con el
    mínimo de otra no es defendible.
  - El mínimo del bloque puede implicar unidades apagadas. Verificar que ninguna quede bajo su mínimo técnico.
  - Sólo aplica si el corredor limitante tiene embalse aguas arriba.
- Cambiar este criterio cambió quién paga el recorte, pero no el elemento que gobierna ni el resultado del proyecto.
  Conviene decirlo así cuando se discuta.

## 5. Cartera de proyectos vecinos

- Se modela lo que tiene respaldo documental: Acceso Abierto, SEIA y la planilla mensual de la CNE de proyectos
  declarados en construcción [C]. «Autorizado» en Acceso Abierto no es «declarado en construcción».
- Verificar en el modelo cada proyecto del fondo: que esté en servicio el que el informe cita, una sola vez, con su
  potencia. En Cumbres un proyecto figuraba en el informe y estaba fuera de servicio en el modelo.
- Un objeto nuevo en la red toma el valor base en todos los escenarios hasta que se escribe y guarda en cada uno.
- Mover el proyecto a otro punto de conexión deja el riesgo de que inyecte dos veces. Comprobar caso por caso qué
  variations están activas.

## 6. Contraste con la operación real

Vale la pena una vez, como revisión interna: comparar topología y despacho del estudio con la operación real del CEN
en bloques equivalentes. Sirve para detectar una topología de operación normal mal representada (una línea que opera
abierta) y para no escribir en el informe que el estudio replica al Coordinador.
