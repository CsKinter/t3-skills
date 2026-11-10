# <Proyecto> | estudio de restricciones (<Cliente>)

<Tipo de proyecto: eólico / PV / BESS / PV + BESS> de <MW> MW<; BESS de <MW> MW / <MWh> MWh>, COD <fecha>.
Punto(s) de conexión: **<POI 1: S/E y kV>**<, **<POI 2>**>. Inyección autorizada <MW>, retiro <MW>.
Usuario: <nombre> (EE). Actualizado el <dd-mm-aaaa>; si algo de aquí contradice un archivo más reciente, manda el
archivo y se corrige este.

## Coordinación vigente

- `Orquestación/PLAN - <fecha>.md` es el tablero único. Sus decisiones vigentes prevalecen sobre este archivo y las
  memorias. Registrar avances en su Bitácora (≤ 10 líneas por intervención).
- Roles: <qué agente coordina, cuál revisa, cuál ejecuta>.
- <Usuario> participa en cada decisión nueva. Antes de actuar, explicar dependencias, mecanismo e hipótesis y preguntar
  con una opción recomendada. Lo ya aprobado se ejecuta sin pedir aprobación repetida.
- Un solo agente escribe a la vez en Word y en PowerFactory. El puente de PF lo inicia <quién>.
- Skills: `estudio-restricciones` (método y fases), `powerfactory-python`, `parametros-sen`, `proyectos-aa-seia`,
  `informe-ee`, `redaccion`. Consultar sólo la necesaria.

## Informes vigentes

- **<Informe>**: revisión <N>, <páginas> páginas, <fecha>.
  Local: `<ruta de la copia de trabajo>`. Leer su `LEEME - revisión <N>.md`.
  Oficial: `<ruta en OneDrive>` (+ `.pdf`).
- **Regla del oficial**: sólo se escribe dentro de `<carpeta permitida>`, con aprobación explícita, respaldo previo y
  sin `~$…docx` abierto. Se edita siempre una copia local.
- No reconstruir sobre ediciones manuales del usuario: partir de su último guardado y respaldarlo.

## Dónde mirar (y dónde no)

- Método: `Metodología restricción - <Proyecto>.md`. Estado técnico: `<AVANCE o HANDOFF vigente>`.
- No leer salvo que se pida: `Respaldos\`, `.revision_informe\`, carpetas con punto, `herramientas\` (scripts con rutas
  de cuando corrieron).
- Los HANDOFF históricos se buscan por sección, no se leen enteros.

## PowerFactory

- Proyecto y caso activos: `python ~/.claude/skills/powerfactory-python/scripts/pf_send.py estado`.
- Casos de estudio (activar el caso antes que el escenario, porque cambia la temperatura de los límites):
  `<01_25 CS>` para <bloques diurnos>, `<02_15 SS>` para <bloques sin sol>.
- Escenarios en `Operation Scenarios\00_<Proyecto>\<POI>\`: `1_Irrestrictos` (punto de partida), `2_Restringidos`
  (resultado, 1:1 con el informe), `99_Respaldo` (trabajo e intentos, en subcarpetas fechadas). Los originales del
  cliente en `<carpeta _secure>` no se modifican.
- Escenarios: <E01_…>, <E02_…>, <E03_…>, <E04_…>.
- Activar casos y escenarios es libre. Toda modificación se propone en el chat y se aplica con el «dale» del usuario.
- Nombres de objetos sin marcas de herramientas. Variation de sesión `Trabajo_<fecha>`; stages separados ≥ 1 min.

## Escenarios y despacho

- Bloques y estado del BESS por escenario: <tabla corta>.
- Receta del irrestricto: <recurso, BESS del fondo, térmicas, hidráulicas, balance>.
- Modelado del proyecto: <componentes y potencia de cada uno>; inyección <MW> y retiro <MW>.

## Contingencias y ciclo

- Lista: <C01–Cnn>, con N + <n>. Críticas conocidas: <…>. Fuera del conjunto que restringe: <…>.
- Capacidades: permanente en N; post-contingencia <criterio y para qué equipos>.
- Ciclo: peor contingencia → factores sólo ahí → restringir → repetir, idéntico en todos los escenarios.
  Orden: <BESS, después ERNC; térmicas y pasada sin restringir; embalse si aplica>.
  Participación: <umbral>. Objetivo de carga: <%>.
- Metodología: <vigente (prorrata por potencia máxima) / DS 32>, decisión <N°> del PLAN.
- Se registra siempre el despacho disponible y el restringido.

## Decisiones cerradas (no reabrir sin que el usuario lo pida)

- <…>
- Slack y balance son internos: no van al cliente.

## Pendientes sujetos al PLAN

- <…>
- Los pendientes que aparezcan en HANDOFF antiguos no están confirmados: preguntar antes de retomarlos.
