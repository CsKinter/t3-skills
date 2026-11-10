# Metodología DS 32

Lo que cambiaría en el estudio si se adopta el DS 32 (publicado el 17-06-2026). **No es la metodología vigente**: en
Cumbres del Ñuble se exploró el 02-11-2026, se archivó sin aplicar y los informes se entregaron con
`metodologia-vigente.md`. Se usa sólo si Vicente (o su supervisor) decide actualizar la metodología de un estudio, o
como sensibilidad interna.

Estado de este archivo: lectura del texto del decreto y corridas exploratorias fuera de PowerFactory. Antes de citar
algo de aquí en un informe, **verificar la vigencia del decreto, su norma técnica y la guía del CEN**.

**Índice**: 1 Qué cambia · 2 Prorrata por potencia disponible · 3 Híbridos · 4 Costo de oportunidad y orden ·
5 Despacho en tiempo real · 6 Lo que el decreto no dice · 7 Decisiones si se adopta.

## 1. Qué cambia respecto de la vigente

| Tema | Metodología vigente | Metodología DS 32 |
|---|---|---|
| Base de la prorrata | Potencia máxima | Potencia disponible |
| Híbrido (renovable con almacenamiento) | Como venga en la base del CEN, normalmente dos unidades independientes | Un conjunto con tope común de inyección y retiro, y potencia disponible propia |
| BESS antes que ERNC | Criterio del estudio | Resultado del orden de costos, cuando los BESS tengan costo de oportunidad |
| Umbral de participación, objetivo de carga, contingencias | Criterios de EE | Sin cambio: el decreto no los trata |

## 2. Prorrata por potencia disponible

- La guía de prorrata vigente al momento del estudio reparte, entre unidades de igual costo, en proporción a la
  potencia máxima con tope en la disponible.
- El DS 32 fija como **régimen permanente** la prorrata por potencia disponible (o su pronóstico). La prorrata por
  potencia máxima se mantiene de forma transitoria **hasta el 30-06-2028**.
- Consecuencia para elegir: importa el COD del proyecto. Con un COD posterior a la transición, la vigente describe un
  régimen que ya no regirá cuando el proyecto opere.
- **Cuándo da distinto**: si todos los participantes tienen el mismo porcentaje de recurso disponible, ambas reglas
  dan exactamente lo mismo. Con perfiles no coincidentes en el mismo bloque (solar alta y eólica baja) la diferencia
  es grande. En un escenario de Cumbres el proyecto pasaba de 35 a 21 MW. Un proyecto solar en un grupo con eólicas
  cae en ese caso.

## 3. Híbridos

- La figura es el conjunto renovable con almacenamiento, con **tope común en el punto de conexión**. El tope de
  inyección y el retiro son datos del informe de autorización de conexión: resolverlos con `proyectos-aa-seia`. Hay
  conjuntos con retiro cero (el BESS no carga desde la red) y conjuntos cuya inyección conjunta es menor que la suma
  de sus partes.
- **Potencia disponible del conjunto**: recurso menos carga del BESS. Si la carga supera al recurso, el exceso es un
  retiro de la red. (El piso en cero es interpretación, no texto.)
- El titular elige antes de la puesta en servicio entre costo único del conjunto o costos separados.
- **Efecto en el modelo**: representar un conjunto como dos unidades independientes sobre el mismo punto sobrestima el
  irrestricto. En el catastro de Cumbres varios vecinos estaban así en la base. La corrida exploratoria con los
  conjuntos corregidos no cambió al proyecto en un punto de conexión y lo movió en el otro, con cifras que no se
  validaron en PowerFactory: lo único firme es que el modelado del híbrido mueve el resultado.
- **No está acreditado que el CEN aplique el tope conjunto en su base de datos.**
- Coherencia mínima: no recortar la parte renovable de un conjunto mientras su BESS carga. Antes se reduce la carga.

## 4. Costo de oportunidad y orden de recorte

- De forma transitoria, ERNC y almacenamiento sin costo de oportunidad forman un solo grupo de costo cero.
- Después, los BESS tendrán costo de oportunidad. «BESS primero» dejaría de ser un criterio de EE para ser la
  consecuencia del orden de costos.
- No se verificó la fórmula del costo de oportunidad ni el estado de la norma técnica.
- El decreto permite al Coordinador apartarse de la prorrata por condiciones de seguridad.

## 5. Despacho en tiempo real

El despacho económico con restricciones de seguridad entra a los 36 meses de la publicación. Un despacho estático por
escenarios no lo representa. Con cualquiera de las dos metodologías, el resultado del estudio es una línea base y no
una réplica de la operación.

## 6. Lo que el decreto no dice

Nada sobre el umbral de participación, el objetivo de carga ni el conjunto de contingencias. Siguen siendo criterios
de EE y se declaran así. Los PMGD quedaron fuera del alcance explorado.

## 7. Decisiones si se adopta

1. ¿Metodología DS 32 como base del informe, o vigente como base y DS 32 como sensibilidad interna?
2. Base de la prorrata según el COD del proyecto.
3. Modelado de los conjuntos: el proyecto y cada vecino, con su tope de inyección y retiro documentado. Qué se hace
   con los que la base del CEN trae como unidades separadas.
4. Costo único o separado para el conjunto propio.
5. Orden de recorte: grupo único de costo cero, o BESS con costo de oportunidad.
6. Cómo se declara en el informe, con la atribución normativa correcta.
