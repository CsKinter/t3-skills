# Metodología DS 32

Lo que cambiaría en el estudio si se adopta el DS 32 (Ministerio de Energía, publicado el 17-06-2026, modifica el
DS 125/2017). **No es la metodología vigente**: en Cumbres del Ñuble se exploró, se archivó sin aplicar y los informes se
entregaron con `metodologia-vigente.md`. Se usa sólo si Vicente (o su supervisor) decide adoptarla, o como sensibilidad.

Estado: contrastado con el texto del decreto el 10-11-2026 (artículos citados son del DS 125 modificado, salvo los
transitorios, que son del DS 32). Las normas técnicas que el decreto encarga aún pueden cambiar el contenido práctico de
§2, §3 y §4: verificar su estado antes de citar en un informe.

**Índice**: 1 Qué cambia · 2 Prorrata · 3 Renovable con almacenamiento · 4 Costo y orden de recorte · 5 Retiros y
sumidero · 6 Despacho automático · 7 Lo que el decreto no dice · 8 Decisiones si se adopta.

## 1. Qué cambia respecto de la vigente

| Tema | Metodología vigente | DS 32 |
|---|---|---|
| Base de la prorrata | Potencia máxima | Potencia disponible (art. 45 bis, 126). Máxima hasta el 30-06-2028 (2º transitorio) |
| PV + BESS | Dos máquinas, como en la base del CEN | La disponible del PV descuenta la carga del BESS (art. 2 cc) |
| Costo del BESS | Tiene costo: por eso «BESS primero» | Costo de oportunidad (art. 37, 103), con implementación a 24 meses (4º transitorio) |
| Umbral de participación, objetivo de carga, contingencias | Criterios de EE | Sin cambio: el decreto no los trata |

## 2. Prorrata

- Entre instalaciones de **igual costo de producción** sin capacidad de colocación suficiente. En transmisión, «a
  prorrata de la Potencia Disponible» (art. 126, tiempo real) o de su pronóstico (art. 45 bis, programación). No es
  «máxima con tope en la disponible»: es proporcional a la disponible, es decir, todos bajan el mismo %.
- **Transitorio** (2º transitorio): desde el 01-07-2026 y por 24 meses, a prorrata de la **potencia máxima** de
  generación y almacenamiento.
- Distribución (PMGD): sujetos a prorrata desde 24 meses después de la publicación (3º transitorio).
- La potencia disponible excluye limitaciones de transmisión e instrucciones del Coordinador (art. 2 cc).
- El Coordinador puede apartarse de la prorrata por seguridad (último inciso de 45 bis y 126).
- **Cuándo da distinto de la vigente**: si todos tienen el mismo % de recurso, igual. Con perfiles no coincidentes
  (solar alto y eólica bajo en el mismo bloque) la diferencia es grande; en Cumbres un escenario pasaba de 35 a 21 MW.

## 3. Renovable con almacenamiento

- Figura: «Central Renovable con Capacidad de Almacenamiento». **El decreto no define un conjunto con tope común de
  inyección y retiro**; ese tope, cuando existe, viene de la autorización de conexión (`proyectos-aa-seia`) y aplica con
  cualquier metodología. Modelar PV y BESS como máquinas sueltas que pueden superarlo sobrestima el irrestricto.
- **Potencia disponible** (art. 2 cc inc. 2): «se deberá descontar la energía destinada para la carga de la componente
  de almacenamiento, según corresponda».
- **Si la carga supera al sol**: el decreto no lo dice. Lectura adoptada: peso = máx(0, sol − carga). Apoyo: si la
  energía almacenada proviene del sistema, la central se considera SAE para todos los efectos (art. 110 inc. 2), así que
  sólo se descuenta la carga cubierta por el propio sol.
- **El peso también es lo que puede ceder.** Un conjunto que retira no participa en la prorrata aunque su sol pudiera
  aliviar. Si con eso la sobrecarga no se resuelve, se informa como tal (decisión del 10-11-2026): es coherente en lo
  económico, porque la energía comprometida a la carga no se ofrece a la red.
- **Costo** (art. 112): el titular elige antes de la puesta en servicio entre (a) una central con un solo costo de
  producción, o (b) generación a su costo variable y almacenamiento como SAE (art. 103). Si no informa, rige (b).

## 4. Costo y orden de recorte

- Los BESS despachados centralizadamente **tienen costo**: hoy según el DS 125 vigente; con el DS 32, su costo de
  oportunidad, que no puede ser inferior al costo variable (art. 37, 103). Por eso «BESS primero» se mantiene.
- **Grupo de costo cero** (5º transitorio): renovables variables y almacenamiento **sin** costo de oportunidad, mientras
  no se dicte la norma técnica. Aplica a instalaciones en autodespacho (SAE de hasta 9 MW pueden optar, art. 103). No
  convierte a un BESS despachado en costo cero.
- Despacho centralizado: listado de prioridad de colocación de menor a mayor costo (art. 57).
- Dentro del conjunto propio, con costo único (opción a), qué componente cede primero es decisión del titular.

## 5. Retiros y sumidero

- El decreto **no prorratea retiros** ni menciona congestión. Sólo permite al Coordinador instruir el inicio o la
  suspensión del retiro de un SAE por seguridad (art. 96, 110 inc. 2).
- Caso sumidero (carga de BESS + demanda sobrecargan en sentido inverso): se restringe la carga, como en la vigente, y se
  declara como instrucción de seguridad, no como prorrata. El conjunto participa con su retiro neto máx(0, carga − sol);
  recortar su PV empeoraría la sobrecarga.

## 6. Despacho automático

Las herramientas automáticas de despacho (art. 117 bis) entran a los 36 meses (1º transitorio). El decreto no habla de
SCED: exige minimizar costos de operación y falla preservando la seguridad, y permite fijar los ajustes como límites
operativos (art. 126). Con esa herramienta la carga de los BESS se optimiza y el sumidero se resolvería sin prorrata. Un
despacho estático por escenarios no lo representa: el estudio es una línea base, no una réplica de la operación.

## 7. Lo que el decreto no dice

Umbral de participación, objetivo de carga, conjunto de contingencias, piso de la potencia disponible, tope común del
híbrido y prorrata de retiros. Se declaran como criterios de EE o interpretación.

## 8. Decisiones si se adopta

1. ¿DS 32 como base del informe, o vigente como base y DS 32 como sensibilidad?
2. Base de la prorrata según el COD (máxima hasta el 30-06-2028, disponible después).
3. Tope de inyección y retiro de cada híbrido según su autorización de conexión; qué se hace con los que la base del CEN
   trae como unidades sueltas.
4. Opción de costo del conjunto propio (art. 112 a o b).
5. Costo de los BESS en el estudio: regla del DS 125 vigente o costo de oportunidad.
6. Cómo se declara en el informe, con la atribución normativa correcta.
