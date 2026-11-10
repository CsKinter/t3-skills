# BESS y proyectos con almacenamiento (metodología vigente)

Lo aprendido sobre almacenamiento en Cumbres, donde los BESS eran **de terceros** (parte del fondo). Para un proyecto
cuyo almacenamiento es propio, varias cosas pasan de «dato del fondo» a «objeto del estudio»: quedan como decisiones
abiertas en §5.

El tratamiento de un híbrido como conjunto con tope común, la prorrata por potencia disponible y el costo de
oportunidad calculado por el SCED pertenecen a `metodologia-ds32.md`, que no es la vigente.

Marcas: **[V]** verificado, **[C]** criterio de estudio que se confirma con Vicente.

## 1. Qué es el proyecto antes de modelarlo

- Resolver con `proyectos-aa-seia`: potencia instalada de cada parte, inyección y retiro autorizados, BESS en MW y
  MWh, y RCA de cada componente.
- La etiqueta «híbrido» de una ficha no prueba nada: en el catastro de Cumbres hubo BESS puros rotulados así.
- En la metodología vigente el modelo **sigue la base de datos del CEN**: cada componente con su unidad y su
  potencia [C]. Se verifica que cada proyecto esté en servicio, una sola vez y con la potencia documentada.

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

## 3. Orden de recorte

**BESS antes que ERNC** [C], por su costo de oportunidad. Antes de tocar una eólica o solar, los BESS participantes
llegan a cero. El reparto dentro de cada grupo es a prorrata de la **potencia máxima** (`metodologia-vigente.md` §4).

Es un criterio del estudio, **no de la guía del CEN**. Presentarlo como regla del Coordinador es un error grave de
atribución.

## 4. El cupo de BESS

Mecanismo útil para explicar resultados cuando hay muchos BESS en la zona:

- Si los factores de los BESS de un grupo son casi iguales, lo que importa es **el total descargado**, no cuál
  descarga. La restricción equivale a un cupo de descarga del grupo.
- Ese cupo es el colchón del proyecto: lo que se libera antes de tocar ERNC.
- Quitar BESS de la cartera no mueve al proyecto, porque se va el problema junto con el remedio. Cambia el porcentaje
  común del resto. **El riesgo real para el proyecto son más inyecciones no almacenables en el mismo nodo.**
- Cuidado con las métricas agregadas de recorte de BESS: pueden mezclar BESS bajados por balance con BESS bajados por
  la restricción.

## 5. Decisiones abiertas para un proyecto con BESS propio

Cumbres no las resolvió porque su proyecto era eólico puro. Cerrarlas con Vicente al inicio:

1. **Estado del BESS propio por escenario**: ¿carga de día y descarga en vespertino y madrugada, a potencia nominal?
2. **Energía y estado de carga**: el ciclo de Cumbres es de potencia. ¿Basta con potencia por bloque, o hay que
   acreditar que la energía cargada en el día sostiene la descarga del bloque nocturno?
3. **Qué se restringe primero dentro del proyecto**: la descarga del BESS, la carga, o la generación. Y qué se informa
   al cliente: restricción en el punto de conexión, o por componente.
4. **Orden frente a terceros**: ¿los BESS del fondo siguen yendo primero cuando el proyecto también tiene BESS?
5. **Escenario sin recurso**: de noche un PV + BESS es sólo BESS. ¿Se estudia como inyección, como retiro o ambos?
6. **Retiro**: si el BESS puede cargar desde la red, el retiro también puede sobrecargar elementos. ¿Se estudian
   contingencias con el BESS cargando a potencia plena?
7. **¿Vigente o DS 32?** Si el proyecto es un conjunto con tope común, la vigente no lo representa. Decidir si se
   estudia con `metodologia-ds32.md`, o con la vigente y la otra como sensibilidad.
