# BESS, híbridos y proyectos PV + BESS

Lo aprendido sobre almacenamiento en Cumbres, donde los BESS eran **de terceros** (parte del fondo). Para un proyecto
cuyo almacenamiento es propio, varias cosas cambian de «dato del fondo» a «objeto del estudio». Esas quedan marcadas
como decisiones abiertas en §5.

Marcas: **[V]** verificado, **[C]** criterio de estudio, **[X]** exploratorio en Cumbres: no se aplicó ni se validó en
PowerFactory. Lo exploratorio orienta, no se cita.

## 1. Qué es el proyecto antes de modelarlo

- Resolver con `proyectos-aa-seia`: potencia instalada de cada parte, **inyección y retiro autorizados**, BESS en MW y
  MWh, RCA de cada componente, y si es un **conjunto renovable con almacenamiento** con tope común en el punto de
  conexión.
- El tope conjunto de inyección y el retiro son datos del informe de autorización de conexión, no supuestos. Hay
  conjuntos con retiro cero (el BESS no carga desde la red) y conjuntos cuya inyección conjunta es menor que la suma
  de sus partes.
- La etiqueta «híbrido» de una ficha no prueba nada: en el catastro de Cumbres hubo BESS puros rotulados así.
- **Modelar un conjunto como dos unidades independientes sobre el mismo punto sobrestima el irrestricto** [V]. Vale
  para el proyecto y para los vecinos del fondo.
- No está acreditado que el CEN aplique el tope conjunto en su base de datos. Si el modelo recibido no lo trae, es una
  decisión a tomar con Vicente y a declarar [C].

## 2. Estado del BESS por escenario

- El modo es parte de la definición del escenario: **carga, reposo o descarga** [C]. Un BESS cargando es un retiro
  (potencia negativa en el generador estático).
- En el irrestricto el BESS va a su techo. Su recorte sale del ciclo.
- **Dos signos de alivio**: un BESS alivia bajando su descarga cuando el factor es positivo y bajando su carga cuando
  es negativo. Limitar la carga es una restricción tan válida como limitar la descarga y se registra aparte.
- **Nivel común**: el porcentaje común de un grupo de BESS se expresa sobre la nominal (en Cumbres, 0,95·Sn) y no sobre
  el despacho base, con techo en el despacho irrestricto.
- En PowerFactory, potencia y límites de Q del generador estático son **por unidad** (total = × número de unidades), y
  el factor de potencia con BESS cargando tiene trampas de signo. Ver
  `powerfactory-python/references/estudio-restricciones.md` §5.
- Un parque y su BESS en el mismo terminal, ambos en control de tensión con consignas distintas, bloquean el flujo. Ver
  `powerfactory-python/references/cierre-bd.md`.

## 3. Orden de recorte y norma

**Criterio de Cumbres** [C]: BESS antes que ERNC, por su costo de oportunidad. Antes de tocar una eólica o solar, los
BESS participantes llegan a cero.

- Es un criterio del estudio, **no de la guía del CEN**. Presentarlo como regla del Coordinador es un error grave de
  atribución.
- Coherencia mínima en un híbrido: no recortar la parte renovable mientras su BESS está cargando. Antes se reduce la
  carga, que es un retiro de la red.

**Marco normativo leído el 02-11-2026** [X: lectura de texto, sin aplicar; verificar vigencia y norma técnica antes de
citar en un informe]:

- Régimen de la guía de prorrata vigente entonces: entre unidades de igual costo, prorrata proporcional a la potencia
  máxima, con tope en la disponible.
- El DS 32 (publicado el 17-06-2026) fija como régimen permanente la prorrata por **potencia disponible**. La prorrata
  por potencia máxima rige transitoriamente hasta el 30-06-2028.
- Para un conjunto renovable con almacenamiento, la potencia disponible es el recurso menos la carga del BESS. Si la
  carga supera al recurso, el exceso es un retiro de la red. El titular elige antes de la puesta en servicio entre
  costo único o separado.
- Transitoriamente, ERNC y almacenamiento sin costo de oportunidad forman un solo grupo de costo cero. Con un COD
  posterior a 2028 los BESS tendrán costo de oportunidad y «BESS primero» dejaría de ser un criterio para ser el
  resultado del orden de costos.
- El decreto no dice nada sobre el umbral de participación, el objetivo de carga ni el conjunto de contingencias. Siguen
  siendo criterios de EE.
- El despacho económico con restricciones de seguridad en tiempo real entra después. Un despacho estático no lo
  representa: el resultado del estudio es una línea base, no una réplica.

**Efecto medido** [X]: si todos los participantes tienen el mismo porcentaje de recurso disponible, repartir por
potencia máxima o por disponible da lo mismo. Con perfiles no coincidentes (solar alta y eólica baja en el mismo
bloque) la diferencia es grande: en un escenario de Cumbres el proyecto pasaba de 35 a 21 MW. **Un PV + BESS cae
justo en ese caso**, así que la base de la prorrata es una decisión de primer orden.

## 4. El cupo de BESS

Mecanismo útil para explicar resultados cuando hay muchos BESS en la zona:

- Si los factores de los BESS de un grupo son casi iguales, lo que importa es **el total descargado**, no cuál
  descarga. La restricción equivale a un cupo de descarga del grupo.
- Ese cupo es el colchón del proyecto: lo que se libera antes de tocar ERNC.
- Quitar BESS de la cartera no mueve al proyecto, porque se va el problema junto con el remedio. Cambia el porcentaje
  común del resto. **El riesgo real para el proyecto son más inyecciones no almacenables en el mismo nodo.**
- Cuidado con las métricas agregadas de recorte de BESS: pueden mezclar BESS bajados por balance con BESS bajados por
  la restricción.

## 5. Decisiones abiertas para un PV + BESS

Cumbres no las resolvió porque su proyecto era eólico puro. Cerrarlas con Vicente al inicio:

1. **Modelado del conjunto**: una unidad con tope conjunto y retiro, o PV y BESS separados con una restricción común.
   Qué hace el modelo del CEN con los conjuntos vecinos.
2. **Estado del BESS propio por escenario**: ¿carga de día desde el PV, desde la red o ambas? ¿Descarga en vespertino
   y madrugada a potencia nominal?
3. **Energía y estado de carga**: el ciclo de Cumbres es de potencia. ¿Basta con potencia por bloque, o hay que
   acreditar que la energía cargada en el día sostiene la descarga del bloque nocturno?
4. **Qué se restringe primero dentro del proyecto**: la descarga del BESS, la carga, o el PV. Y qué se informa al
   cliente: restricción del conjunto en el punto de conexión, o por componente.
5. **Orden frente a terceros**: ¿los BESS del fondo siguen yendo primero cuando el proyecto también tiene BESS?
6. **Base de la prorrata**: potencia máxima o disponible, según el COD del proyecto y el régimen que rija entonces.
7. **Escenario sin recurso solar**: de noche el proyecto es sólo BESS. ¿Se estudia como inyección, como retiro o ambos?
8. **Retiro**: si el conjunto puede cargar desde la red, el retiro también puede sobrecargar elementos. ¿Se estudian
   contingencias con el BESS cargando a potencia plena?
