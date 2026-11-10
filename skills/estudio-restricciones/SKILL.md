---
name: estudio-restricciones
description: Conduce un estudio de restricciones de EE de principio a fin (proyecto eólico, PV, BESS o híbrido que se conecta al SEN): arranque del proyecto, decisiones que se cierran con Vicente, adecuación de base de datos, escenarios y despacho irrestricto, contingencias, ciclo de restricción, tratamiento de BESS e híbridos, sensibilidades, informe y cierre. Úsala al empezar un estudio nuevo, al retomar uno en curso, al planificar una campaña de cálculo, al decidir cómo restringir o al revisar si un resultado está listo para el informe, aunque no se diga «skill». Las herramientas tienen su propia skill (powerfactory-python, parametros-sen, proyectos-aa-seia, informe-ee, redaccion, ppt-ee); ésta dice qué hacer, en qué orden y con qué criterio.
---

# Estudio de restricciones

Un estudio de restricciones responde cuánto puede inyectar un proyecto en cada escenario sin sobrecargar la red en N ni
ante contingencias, y qué hay que recortar para lograrlo. Esta skill condensa cómo se hizo el del PE Cumbres del Ñuble
(eólico, dos puntos de conexión, octubre–noviembre de 2026) en forma de método general. Lo que era propio de ese
estudio (cifras, umbrales, elementos, topologías) quedó fuera a propósito.

## Tres clases de contenido

Al leer cualquier archivo de esta skill, distinguir:

- **Verificación**: comprobación sin la cual un resultado no se sostiene. Se hace siempre.
- **Criterio de estudio**: decisión de Vicente que valió en Cumbres (umbral de participación, objetivo de carga, orden
  de recorte). Se propone como opción recomendada y **se confirma en cada estudio nuevo**; no se hereda en silencio.
- **Cifra**: MW, kA, %, nombres de elementos. Nunca se trasladan. Cada estudio obtiene las suyas de su fuente.

## Fases

| Fase | Qué se hace | Leer | Herramienta |
|---|---|---|---|
| 0. Arranque | Carpeta del proyecto, AGENTS.md, tablero, decisiones iniciales | `references/conduccion.md`, `assets/` | — |
| 1. Proyecto y cartera | Qué es el proyecto (MW, BESS, inyección y retiro), qué vecinos se modelan | `references/bess-hibridos.md` | `proyectos-aa-seia` |
| 2. Adecuación de base de datos | Obras, capacidades por condición, tensiones | `parametros-sen/references/capacidad-por-condicion.md` | `parametros-sen` |
| 3. Escenarios e irrestricto | Bloques, estado de los BESS, receta de despacho, convergencia y reactivo | `references/escenarios-despacho.md` | `powerfactory-python` (`estudio-restricciones.md` §0–1) |
| 4. Contingencias y ciclo | Lista y monitores, N limpio, peor par, factores, prorrata, cierre | `references/metodologia-vigente.md` | `powerfactory-python` (`estudio-restricciones.md` §2–3) |
| 5. Sensibilidades y coherencia | Qué preguntas vale la pena probar, contraste con estudios vecinos | `references/sensibilidades-coherencia.md` | — |
| 6. Informe | Esqueleto, plantilla por escenario, origen de cifras, revisiones | `references/informe.md` | `informe-ee`, `redaccion` |
| 7. Cierre | Validación final de escenarios, orden de la BD, oficialización | `powerfactory-python/references/cierre-bd.md` | `powerfactory-python`, `informe-ee` |

Leer sólo la referencia de la fase en curso.

## Metodología vigente y metodología DS 32

Hay dos metodologías y no se mezclan:

- **Vigente** (`references/metodologia-vigente.md`, con `escenarios-despacho.md` y `bess-hibridos.md`): la que se
  aplicó y se entregó en Cumbres. Prorrata por potencia máxima, el modelo sigue la base del CEN, «BESS primero» como
  criterio del estudio. **Es la que se usa salvo decisión expresa.**
- **DS 32** (`references/metodologia-ds32.md`): prorrata por potencia disponible, híbridos como conjunto con tope
  común, costo de oportunidad de los BESS. Quedó explorada y archivada, sin validar en PowerFactory. Se usa sólo si
  Vicente decide adoptarla en un estudio, o como sensibilidad interna.

Al empezar un estudio se pregunta cuál rige y queda como decisión en el tablero. Para un proyecto con COD posterior a
la transición del decreto, o que sea él mismo un híbrido, la pregunta no es retórica.

## Arranque de un estudio nuevo

1. Copiar las plantillas de `assets/` a la carpeta del proyecto y completarlas con Vicente:
   `AGENTS.plantilla.md` → `AGENTS.md`, `PLAN.plantilla.md` → `Orquestación/PLAN - <fecha>.md`.
2. Recorrer `assets/decisiones-iniciales.md` con él. Cada respuesta queda como decisión numerada en el tablero. Las que
   no se puedan cerrar todavía quedan como hipótesis abiertas, con la fase en que bloquean.
3. Resolver qué es el proyecto con `proyectos-aa-seia` antes de modelarlo: potencia, inyección y retiro autorizados,
   BESS (MW y MWh), si es un conjunto con tope común. El modelo no se arma desde el nombre comercial.
4. Recién entonces abrir PowerFactory.

## Reglas que valen en todo el estudio

- **Vicente decide cada cosa nueva.** Antes de actuar se explican dependencias, mecanismo e hipótesis, y se pregunta con
  una opción recomendada. Lo ya aprobado se ejecuta sin volver a preguntar. Una recomendación del agente no se anota
  como decisión.
- **El mismo ciclo en todos los escenarios.** Un cambio de método se propone antes de aplicarlo y, si se acepta, se
  rehace en todos.
- **Resultado y estado van juntos.** Toda cifra dice de qué estado sale (irrestricto, intermedio, cierre) y con qué
  capacidad se midió. Un estado intermedio no se presenta como «antes».
- **Nada se borra.** Se mueve a respaldo y se compara el despacho antes y después.
- **Se trabaja en copias**, partiendo del último guardado del usuario, con respaldo previo.
- **Un solo agente escribe a la vez** en Word, en PowerFactory y en cualquier herramienta de cálculo.
- **Verificación independiente de cada cierre**: rehacer el despacho desde los cambios registrados y comprobar que
  reproduce el resultado declarado. Un cierre que no pasa esa prueba no circula.
- **Atribución al proyecto**: se mide con y sin proyecto sobre el mismo fondo. Una sobrecarga que ya existía sin el
  proyecto no se le carga entera.
- **Slack, balance y ajustes de convergencia son internos.** No van al cliente.

## Aprender del estudio en curso

Lo nuevo se anota primero en el proyecto (tablero o HANDOFF). Se promueve a esta skill sólo cuando Vicente lo confirma
como general, indicando si es verificación o criterio de estudio. Las skills viven en `~/t3-skills` (git): editar ahí
y confirmar el cambio.
