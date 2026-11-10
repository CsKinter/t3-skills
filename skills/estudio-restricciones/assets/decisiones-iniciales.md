# Decisiones iniciales de un estudio de restricciones

Lista para recorrer con Vicente al empezar. Cada respuesta pasa al tablero como decisión numerada. La columna
«Cumbres» dice qué se decidió allí: sirve como opción recomendada, **no como valor por defecto**. Lo que no se pueda
cerrar queda como hipótesis abierta, con la fase que bloquea.

## A. Proyecto

| # | Pregunta | Cumbres | Notas |
|---|---|---|---|
| A1 | ¿Qué es exactamente el proyecto? MW por componente, inyección y retiro autorizados, BESS en MW y MWh | Eólico puro | Resolver con `proyectos-aa-seia` antes de modelar |
| A2 | ¿Cuántos puntos de conexión y cuál es el horizonte (COD)? | Dos, 2034 | Con varios POI: ¿un informe o varios? |
| A3 | ¿Metodología vigente o DS 32? | Vigente; DS 32 explorada y archivada | Pesa si el COD es posterior a la transición o si el proyecto es un híbrido. Si se adopta: bloque G |
| A4 | ¿Qué recibe el cliente? Restricción en el punto de conexión, por componente, o ambas | En el POI | |

## B. Base de datos y capacidades

| # | Pregunta | Cumbres | Notas |
|---|---|---|---|
| B1 | ¿Qué base del CEN y qué obras futuras se incluyen? | Plan de obras al horizonte | |
| B2 | ¿Qué temperatura y caso de estudio usa cada escenario? | 25 °C con sol de día, 15 °C sin sol de noche | El caso se activa antes que el escenario |
| B3 | Capacidad post-contingencia: ¿permanente, 15 o 30 min, y para qué equipos? | 30 min sólo donde hay dato aplicable | `parametros-sen/references/capacidad-por-condicion.md` |
| B4 | ¿Monitor por extremo o límite único de línea? | Límite único de línea | Un equipo de paño limita un solo extremo |
| B5 | Datos rechazados en Infotécnica: ¿se usan? | Sí, marcados | |
| B6 | Obras futuras sin dato: ¿estándar de obra equivalente o S/I? | Referencia, avisando | |
| B7 | ¿Se conserva un límite heredado de otro estudio de EE? | Sí, por decisión | Es decisión de alcance, no de capacidad física |

## C. Escenarios y despacho

| # | Pregunta | Cumbres | Notas |
|---|---|---|---|
| C1 | ¿Qué bloques y qué estado de los BESS en cada uno? | Cuatro: día carga, día reposo, vespertino y madrugada descarga | |
| C2 | Receta del irrestricto: recurso, BESS del fondo, térmicas, hidráulicas | Perfil del cliente más receta escrita | |
| C3 | ¿Cómo se cubre el balance y qué máquina es la slack? | Compensación explícita, slack con margen | Interno |
| C4 | ¿Qué cartera de proyectos vecinos entra y con qué criterio de madurez? | Con respaldo en AA, SEIA y CNE | |
| C5 | Tensión y reactivo: bandas, qué se puede maniobrar y dónde | Reactores de barra sí, de línea no | |
| C6 | Si hay BESS propio: ¿de dónde carga y se verifica la energía entre bloques? | No aplicó | Hueco de Cumbres |

## D. Contingencias y ciclo

| # | Pregunta | Cumbres | Notas |
|---|---|---|---|
| D1 | ¿Lista de contingencias y de monitores? ¿Qué queda fuera? | Lista cerrada por POI | Incluir compensación serie en los monitores |
| D2 | ¿El estudio es local o incluye el troncal? | Uno local, otro de corredor | No concluir en la red local por una contingencia troncal |
| D3 | Umbral de participación | 20 % del mayor factor, por signo, sin PMGD | Criterio de EE |
| D4 | Objetivo de carga y banda | 99 % | Criterio de EE |
| D5 | Orden de recorte | BESS, después ERNC. Térmicas y pasada fijas | Criterio de EE, no del CEN |
| D6 | ¿Hay embalse aguas arriba del corredor limitante? | Sí en un POI: baja primero al mínimo del bloque | |
| D7 | ¿Los BESS cargando cuentan como restringibles? | Sí | |

## E. Sensibilidades e informe

| # | Pregunta | Cumbres | Notas |
|---|---|---|---|
| E1 | ¿Qué sensibilidades se hacen y cuáles van al informe? | Topológica en el informe, el resto interno | |
| E2 | ¿Hay otros estudios de EE en la zona con los que deba ser coherente? | Sí, dos | La conciliación es interna |
| E3 | ¿Quién revisa y qué formato espera? | Supervisor de EE | |
| E4 | ¿Dónde vive el oficial y quién autoriza escribirlo? | OneDrive, con aprobación explícita | |

## G. Sólo si se adopta la metodología DS 32

No se recorren en un estudio con la metodología vigente. Detalle en `references/metodologia-ds32.md` §7.

| # | Pregunta | Notas |
|---|---|---|
| G1 | ¿DS 32 como base del informe, o vigente como base y DS 32 como sensibilidad interna? | |
| G2 | Base de la prorrata según el COD: potencia máxima (transitoria) o disponible (permanente) | Con solar y eólica en el mismo grupo cambia el resultado |
| G3 | Modelado de híbridos: el proyecto y cada vecino como conjunto con tope común de inyección y retiro | Datos del informe de autorización de conexión |
| G4 | Costo único o separado del conjunto propio | |
| G5 | Costo de los BESS: precio de la barra de carga (antes del SCED) o costo de oportunidad (con SCED) | El orden BESS → ERNC no cambia; los BESS nunca van a costo cero |
| G6 | Verificar vigencia del decreto, norma técnica y guía del CEN antes de citar | |

## F. Trabajo con agentes

| # | Pregunta | Notas |
|---|---|---|
| F1 | ¿Qué agente coordina, cuál ejecuta y cuál revisa? | Decidirlo según cuotas reales |
| F2 | ¿Quién inicia el puente de PowerFactory y en qué modo? | |
| F3 | ¿Qué se puede hacer sin preguntar? | Lecturas y cálculos en copia |
| F4 | ¿Hay trabajo sin supervisión? ¿Con qué límite? | Sólo lo ya aprobado |
