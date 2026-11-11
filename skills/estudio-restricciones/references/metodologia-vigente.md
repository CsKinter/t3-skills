# Metodología vigente: método y ciclo de restricción

La que se aplicó y se entregó en Cumbres del Ñuble. Lo que cambiaría con el DS 32 (prorrata por potencia disponible,
híbridos como conjunto, costo de oportunidad) está aparte, en `metodologia-ds32.md`, y no se mezcla con esto.

Qué se decide y en qué orden. La mecánica en PowerFactory (ficticios, prorrata, JSON por iteración, atributos) está en
`powerfactory-python/references/estudio-restricciones.md` §2–3 y no se repite aquí.

**Índice**: 1 Secuencia · 2 Contingencias y monitores · 3 Factores y participantes · 4 Orden de recorte ·
5 Cierre y recuperación · 6 Casos especiales · 7 Registro · 8 Trampas.

Marcas: **[V]** verificación, **[C]** criterio de estudio que se confirma con Vicente.

## 1. Secuencia

1. El irrestricto converge con límites de P y Q y sin avisos (`escenarios-despacho.md`).
2. **N limpio antes de N-1** [V]. Se restringen las sobrecargas en N de la zona en que influye el proyecto. Las
   preexistentes lejanas se anotan y no se tocan.
3. N-1 completo → **peor sobrecarga nueva**: el par elemento + contingencia con mayor carga entre las que superan
   100 % en la contingencia y no lo superaban en N.
4. Factores **sólo en ese par**.
5. Restringir a los participantes hasta el objetivo.
6. Repetir desde 3 hasta que el N-1 no deje sobrecargas nuevas.

No se descarta una sobrecarga por pequeña. Un N saneado no elimina el N-1 previo.

## 2. Contingencias y monitores

- La lista se presenta cerrada («estas son») y se acuerda al inicio [C]. Una contingencia puede abrir varios tramos.
- Monitores y contingencias son listas distintas: un elemento puede vigilarse aunque su contingencia quede fuera del
  conjunto que restringe al proyecto.
- **Alcance por nivel de tensión** [C]. En un estudio local de 154/66 kV no se concluye una restricción por una
  contingencia de 500 kV. Si el punto de conexión carga un corredor troncal, ese corredor es el estudio y se trata
  aparte (§6).
- Los bancos de condensadores serie se monitorean: el barrido típico de líneas y transformadores no los incluye [V].
- Antes de concluir, revisar la capacidad con que se mide cada elemento vigilado
  (`parametros-sen/references/capacidad-por-condicion.md`). Un límite mal cargado cambia el N-1 entero.
- Si los documentos del proyecto citan conjuntos distintos (N + 28, N + 34, «20 contingencias»), aclarar cuál rige
  antes de escribir el informe.

## 3. Factores y participantes

- Factores **por perturbación**, con la contingencia abierta y en caliente [V]. Se miden donde la restricción está
  activa y en el estado de cierre. Cerca del límite de convergencia se inflan (un factor de 9,8 donde el sano era 5,0).
- **Umbral de participación** [C]: en Cumbres, factor ≥ 20 % del mayor de la iteración. Tres precisiones que costaron
  errores:
  - Se calcula **por signo**. Con un umbral sin signo, factores de −0,5 % dejaron en cero 815 MW de BESS.
  - El máximo se toma **entre las acciones que de verdad alivian**. Una unidad cuyo signo no permite aliviar no fija el
    umbral.
  - PMG y PMGD se excluyen antes de calcular el máximo.
- Si el mayor factor baja, puede parecer que otra unidad «empezó a influir» sin que su factor haya cambiado. Mirar el
  factor, no la pertenencia al grupo.
- El factor de una unidad en control de tensión no es el de la tabla con Q fija: Q sigue a P. Contrastar el factor
  operativo antes de usarlo para atribuir.
- **pp no equivale a MW**: restringir X MW no libera X MW del elemento. Pasar por la corriente.
- El umbral y el objetivo de carga no tienen respaldo expreso en la guía del CEN. En el informe se declaran como
  criterios del estudio.

## 4. Orden de recorte

Criterio de Cumbres [C], a confirmar:

1. **BESS primero.** Bajar la descarga si el factor es positivo, bajar la carga si es negativo.
2. **ERNC después** (eólica y solar), a prorrata y hasta el mismo porcentaje común.
3. **Térmicas no se restringen** ni se apagan. La pasada tampoco.
4. Si los BESS llegan a cero y no alcanza, la iteración se cierra («BESS a 0») y se pasa a la siguiente peor
   sobrecarga. No se recorta una ERNC mientras quede un BESS con influencia.

Excepción que apareció en un **corredor troncal con embalse aguas arriba**: el embalse baja primero, desde su
potencial hasta el mínimo del bloque, y después vienen BESS y ERNC (`escenarios-despacho.md` §4). Sin hidro en el
corredor, no aplica.

«BESS primero» es criterio del estudio y se justifica por su costo de oportunidad. No se presenta como regla del CEN
(`bess-hibridos.md` §3).

**Base de la prorrata**: potencia máxima (o un porcentaje común de la nominal). Nunca el despacho ya restringido como
si fuera la nominal. La prorrata por potencia disponible es de `metodologia-ds32.md`.

## 5. Cierre y recuperación

- **Objetivo** [C]: carga del elemento en (99 − banda, 99] %. Si otra herramienta cerró en otro valor, es dato de esa
  herramienta, no un criterio nuevo.
- **Recuperar despacho** después de un cierre conservador: por vueltas completas hasta recuperar menos de ~1 MW por
  vuelta, con factores de la topología vigente, partiendo del último cierre válido y compensando el balance de forma
  explícita. Una sola pasada subestima el margen y el orden de los grupos importa.
- **Verificación independiente** [V]: rehacer el despacho desde los cambios registrados. Si no reproduce el resultado,
  el cierre es inválido aunque ya haya circulado.
- **Balance**: decidir qué grupo compensa lo recortado y cómo se trata la slack [C]. La slack debe quedar con margen
  dentro de sus límites. Una compensación en el mismo sentido del alivio contamina el resultado.

## 6. Casos especiales

- **Contingencia sin solución.** No hay factores. El grupo sale de la topología (lo que queda detrás del elemento),
  BESS primero, y se busca por bisección **desde abajo** la mayor inyección con la que converge con límites. Desde
  arriba se cae en la rama inestable de la curva P-V y los factores salen negativos.
- **Respaldo sin límites de Q.** Si una contingencia no converge con límites, se repite sin límites de Q y se etiqueta
  así. Sirve para no ocultar una sobrecarga, no como validación física final.
- **Cascada tras una falla de convergencia.** El flujo arranca de la solución anterior y las contingencias siguientes
  fallan en cadena. Tras cualquier falla, arranque plano y resolver N de nuevo.
- **Corredor troncal.** El conjunto aguas arriba se trata como un todo. La regla de grupos que quedó vigente fue por
  salto de factor (un grupo fijo, un grupo aguas arriba del corredor, el resto), no por lista de centrales.
- **Solución espuria** (tensión baja, sobrecargas absurdas): es del solver, no de la red. Ver
  `powerfactory-python/references/cierre-bd.md`, trampas.

## 7. Registro

Por iteración y con el mismo formato en todos los escenarios: elemento, contingencia, carga antes y después, factores,
participantes, grupo, despacho antes y después, motivo de cierre. Siempre el **despacho disponible y el restringido**.
Si un factor se reutiliza, se anota por qué.

Defensa contra guardados que no persisten: guardar, cambiar de escenario, volver y releer.

## 8. Trampas

| Trampa | Cómo se evita |
|---|---|
| Atribuir todo el recorte al proyecto cuando el elemento ya estaba sobrecargado sin él | Corrida con y sin proyecto sobre el mismo fondo |
| Presentar un ensayo fallido como resultado (proyecto en 0 MW y aun con sobrecargas) | No es un despacho admisible: se informa la causa |
| Heredar el recorte de otra contingencia | Cada par se resuelve con sus factores |
| Comparar cargas de dos fondos distintos como si fuera alivio | Mismo fondo en ambas mediciones |
| Rotular un estado intermedio como «antes» | Decir si es el original o un estado ya modificado |
| Medir factores con el estado anterior a una corrección | Remedir tras corregir reactivo, capacidades o topología |
| Reutilizar cifras de una campaña superada | Lista «no usar como vigentes» en el tablero |
| Hipótesis numérica presentada como origen de un dato (1,2 × 1,7 ≈ 2,04) | Marcarla como conjetura hasta tener documento |

## Lo que Cumbres no resolvió

El estado de carga y la energía de los BESS (MWh) nunca entraron al ciclo: cada escenario fijó el modo del BESS y su
potencia. En un proyecto con almacenamiento propio hay que decidirlo al inicio (`bess-hibridos.md` §5).
