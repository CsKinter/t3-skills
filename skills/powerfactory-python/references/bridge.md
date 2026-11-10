# Puente PF ↔ Claude (`scripts/pf_bridge.py` + `scripts/pf_send.py`)

**Índice** (leer sólo la sección que haga falta; ubicarla con Grep por su encabezado):
- *Puesta en marcha* y [Arranque por GUI autorizado](arranque-puente-gui.md) (incluye ruta PowerShell): *Uso (Claude)* se lee siempre antes del primer comando.
- *Modo solo lectura* y *Modo modificación*: qué permite cada modo, variation de sesión, marca `[CdN]`, diario y `deshacer`.
- *Casos de estudio y escenarios* y *Escenarios: regla de guardado*: antes de activar o guardar un escenario.
- *Pérdida de conexión* y *Límites*: cuando un comando no responde o falla.
- *Output Window*: mensajes de PF que vuelven con cada comando.
- *Drivers: plantillas con reintento* (`pf_drv.py`): tareas repetidas por escenario.
- *Fotos de diagramas* y *Capturas de escritorio*: WMF → PNG y captura de pantalla.

Permite que Claude ejecute código contra la sesión de PowerFactory que el usuario tiene abierta, sin que el usuario
corra cada script. Comunicación por carpeta local (`%USERPROFILE%\pf_bridge`), sin red.

## Puesta en marcha (una vez por sesión)

Normalmente lo hace el usuario. Con autorización expresa, el agente puede arrancar el puente de lectura por GUI;
ver [el procedimiento comprobado y su helper PowerShell](arranque-puente-gui.md). Esto no autoriza el modo modificación
ni cambiar la seguridad del puente. La autorización vigente en el chat prevalece sobre instrucciones históricas de
«sólo el usuario»; no pedirla otra vez para la misma tarea.

1. En PF, en el caso de estudio activo (o en la carpeta Scripts del proyecto): *New Object → Python Script (ComPython)*.
2. En "Script", apuntar a `C:\Users\vicen\.claude\skills\powerfactory-python\scripts\pf_bridge.py`. Ejecutar.
3. La ventana de salida muestra "Puente Claude activo … (modo solo lectura)". PF queda ocupado mientras corre
   (puede verse "No responde"): es esperado.
4. Para terminar: `python pf_send.py detener`, crear `pf_bridge\inbox\STOP` a mano, el botón Break/Stop de PF
   (llega como KeyboardInterrupt y el puente cierra limpio; verificado), o esperar `IDLE_MINUTES` (120) sin comandos.
   **Tope de 8 h por sesión (`MAX_HOURS`, versión verificada el 05-11-2026)**: pasado ese tiempo se detiene solo aunque esté en uso; `estado` muestra
   `inicio`, `latido` y `se_detiene_en_min`. Si un comando no devuelve nada, mirar `estado` antes de reintentar.

## Uso (Claude)

```bash
C=~/.claude/skills/powerfactory-python/scripts/pf_send.py
python $C estado                                  # ¿vivo?, proyecto y caso activos, modo
python $C -c 'print(app.GetActiveProject())'
python $C ejecutar consulta.py --timeout 600 --json r.json
```

En el comando hay: `app` (vista del app), `resultado` (dict → JSON de respuesta; objetos PF se serializan como
`GetFullName()`), `guardar(nombre, datos)` (JSON en `pf_bridge\files`), `as_list`, `get_attr`, `SoloLectura`, `MODO`.
`print` se captura y vuelve en `salida`. Códigos: 0 ok, 1 error del comando, 2 puente caído o sin respuesta.

Si `estado` dice detenido: arrancar el ComPython por GUI si ya hay autorización para ello; si no, pedir al usuario que
lo ejecute o autorice el arranque. No enviar comandos al puente caído en bucle.

## Modo solo lectura (por defecto)

- Se permite leer atributos y llamar `Get* / Is* / Has* / Print* / Search* / Find* / Count*`.
- Se rechaza con `SoloLectura`: asignar atributos, `SetAttribute`, `CreateObject`, `AddCopy`, `Delete`, `Move`,
  `Activate/Deactivate`, `Execute`, `SetStudyTime`, `GetFromStudyCase` (crea el comando si no existe), y cualquier
  otro método fuera de los prefijos.
- Antes de ejecutar se rechazan comandos con `import powerfactory`, `GetApplication`, `_crudo_`, `subprocess`,
  `os.system`, `os.remove`… Es una protección contra errores propios, no un sandbox: no intentar rodearla.
- `ALLOW_CALC = True` (editar el archivo) permite `Execute()` de `ComLdf/ComShc/ComInc/ComSim` obtenidos con
  `GetCalcRelevantObjects` o del caso de estudio. Cambia resultados, no datos de la red. Sólo con OK del usuario.
- `READ_ONLY = False` (modo escritura) entrega el `app` real: sólo cuando el usuario lo pida explícitamente, y siguiendo
  las reglas de escritura segura de SKILL.md (variation + stage verificado, dry run primero).

## Modo modificación (`pf_bridge_modificar.py`, lo lanza el usuario)

**Horas de las stages (aprendido en PF real, 05-10-2026):** si dos stages con la misma hora de activación modifican el
mismo objeto (o una agrega un objeto y otra lo modifica), PF marca "Variation conflict" y **no activa ninguna stage**.
Por eso, al arrancar:
- base = la última stage ajena activa con hora <= hora de estudio;
- las stages Claude anteriores (nombre `Claude_revisar_*` o descripción `[claude-puente]`) se reubican en base +1, +2...
  min; la de la sesión va al final (se reutiliza la última Claude vacía, p. ej. de un arranque fallido);
- si la nueva queda después de la hora de estudio, se adelanta la hora de estudio a esa hora (se anota en el diario);
  si eso activara alguna stage ajena, se aborta.

**Variations consolidadas (07-10-2026):** una variation de Claude renombrada con `nombrar()` deja de ser temporal: al arrancar no se reubica y cuenta como ajena para la base. Su stage se puede fijar con `stage.SetAttribute("tAcTime", t)` (permitido sólo en stages de variations de Claude) a una hora <= la hora de estudio de todos los casos donde debe valer; si no, queda inactiva en los casos con hora menor aunque la variation esté activa.

**Nombre de la variation de sesión (08-10-2026, pedido del usuario):** `Trabajo_<aaaammdd_hhmm>` (antes `Claude_revisar_*`; ambos prefijos se reconocen como temporales). Consolidación: en «Base SEN», `stage.loc_name = "Revision_parametros_N"`, `stage.Move(zdi)` (el puente lo permite sólo para stages de variations de Claude, con origen y destino inactivos) y `variation.Delete()`.

**Ordenar variations (08-10-2026, consejo del usuario):** para mover, renombrar, cambiar la hora del stage o borrar variations, activar primero un caso sin variations activas (en Cumbres: «Base SEN»). Con la variation activa, `Move` devuelve 1, y cambiar la hora del stage de la variation de la sesión hace que PF deje de registrar en ella (los cambios siguientes se revierten): fijar la hora sólo al final. El puente borra variations de Claude de sesiones anteriores si no están activas en el caso actual.

**Nombre resumido:** `nombrar("Ajuste longitudes D418")` renombra en el acto (no esperar al cierre: un Break no lo ejecuta); la variation y su stage
toman ese nombre (máx. 40 caracteres) y la descripción conserva `[claude-puente]` y el nombre anterior.
`renombrar_claude("Claude_revisar_...", "Cambio tipo Coiquén")` renombra variations de sesiones anteriores.

Al arrancar crea y activa la variation **`Claude_revisar_<aaaammdd_hhmm>`** con un stage a la hora de estudio (no mueve
el study time) y verifica con una sonda que PF registra ahí; si algo falla, el puente queda en solo lectura.

| Qué se toca | Regla |
|---|---|
| Objeto de la red (cuelga de un ElmNet) | Se escribe y **se verifica cada cambio**: quedó en el stage de Claude o, con un escenario de operación activo, en el escenario (nunca se guarda). Si no quedó en ninguno, se revierte y el comando falla. |
| Fuera de la red (tipos, características, escalas, comandos, caso de estudio) | **Prohibido tocar el original.** `c = revisar(obj)` crea una copia junto al original (nombre limpio, «<nombre> (2)» si choca, y la marca `[CdN]` en la descripción); se modifica `c` y se repunta desde la red (`linea.typ_id = c`, registrado en la variation). Las copias marcadas (`[CdN]` en la descripción, o el sufijo `_CdN`/`_revisar` de la convención anterior) de sesiones anteriores también se pueden escribir y renombrar (queda en el diario). |
| Objetos nuevos | **Desde el 15-10-2026 (pedido del usuario): nombre limpio + marca `[CdN]` en la descripción** (`MARCA_OBJ`), no sufijo en el nombre. Si el nombre está ocupado en la carpeta, ` (2)`, ` (3)`… (PF exige nombres únicos por carpeta aunque la clase sea distinta: un TypTow y un TypCon no pueden llamarse igual). Si la clase no tiene descripción, cae al sufijo `_CdN`. En la red deben quedar registrados en el stage. **Excepción `ChaRef`**: dentro de un objeto propio se crea con el nombre exacto del parámetro (`sline`) y sin marca, porque PF enlaza la característica por ese nombre (con sufijo no enlaza, y renombrarla después da «Error in load flow data» sin detalle). |
| Borrar | Objetos creados por Claude en la sesión; cualquier objeto que cuelgue (hasta 6 niveles) de un objeto propio o marcado; y copias de biblioteca marcadas de sesiones anteriores (nunca red, escenarios ni variations por esta regla; una carpeta sólo si todo lo que tiene directamente está marcado). Quedan en la papelera de PF. Objetos sin marca: no. Para que el puente reconozca objetos que el usuario quiere ceder, el usuario les pone `[CdN]` en la descripción (p. ej. con `marcar_objetos_cdn.py`); el puente nunca se marca objetos solo. |
| Diagramas | `Show`, `Close`, `Freeze`, `Unfreeze` sobre `IntGrfnet`/`SetDesktop`/`SetDeskpage` y `Rebuild` están permitidos (no cambian datos). Escribir IntGrf/IntGrfcon/SetVitxt/capas sólo dentro de diagramas propios `_CdN`. |
| Sets propios | `AddRef/RemoveRef/Clear` sobre `SetSelect` creados en la sesión o `_revisar` (p. ej. el set de barras para ComVstab). |
| Mover (`obj.Move(carpeta)` en el comando; el puente lo traduce a `carpeta.Move(obj)`, que es la forma real de la API de PF: al revés devuelve 1) | Sólo escenarios o carpetas `_revisar` (o creados en la sesión), dentro de Operation Scenarios; nunca el escenario activo ni la carpeta que lo contiene. Queda en el diario (tipo `movido`). Habilitado el 07-10-2026 a pedido del usuario para ordenar las copias de trabajo en una carpeta aparte. También variations de Claude (`Claude_revisar_*` o con `[claude-puente]`) hacia carpetas dentro de Network Variations (p. ej. ZDI). |
| Ejecutar | Sólo `ComLdf/ComShc/ComInc/ComSim/ComVstab/ComDiff` (ComVstab, sensibilidades/factores de distribución, habilitado el 07-10-2026; si el caso no lo tiene se crea con `caso.CreateObject("ComVstab", ...)`, que queda como objeto propio; ComDiff, flujo diferencial, 08-10-2026: además se permiten sus atributos `iopt_mode`, `imode`, `ibase`, `icomp` aunque el comando sea del usuario, ver `flujo-diferencial.md`); `GetFromStudyCase` sólo si el comando ya existe. |
| Variations (`IntScheme`) | `v.Activate()` o `activar_variation("nombre")` activa cualquier variation en el caso de estudio activo; `Deactivate` sólo variations de Claude. Se verifica con `GetActiveNetworkVariations()` y queda en el diario (`variation_activada`). Habilitado el 07-10-2026 a pedido del usuario (llevar una corrección a otros casos). |
| `SetStudyTime` | Sólo hacia adelante y hasta la hora del stage de la sesión, y sólo si no activa stages ajenas (09-10-2026: para que otro caso de estudio vea los cambios de la sesión). Queda en el diario. |
| Fusionar stages | `IntSstage.ApplyChanges()` sobre un stage INACTIVO copia sus cambios al stage que graba (verificado 08-10-2026, ΔP = 0 en 731 líneas). Receta: mover los stages a una variation `Trabajo_` en un caso sin variations activas, desactivarla en el caso de la sesión, aplicar en orden cronológico y comparar flujos contra una línea base; revisar antes que no haya stages del usuario intercalados que toquen los mismos objetos. |
| Activate/Deactivate (otros)/Save | Prohibidos. |

Funciones extra en el comando: `revisar(obj)`, `diario()` (lista de cambios con valor anterior/nuevo y destino),
`deshacer(n=None)` (revierte los últimos n, o todos), `VARIATION`. El diario se guarda en
`pf_bridge\diario_<variation>.jsonl` (una línea JSON por cambio, agregada al final; desde el 07-10-2026: reescribir el
archivo completo costaba ~0,65 s por cambio con miles de entradas).

Para descartar todo: `deshacer()` y luego el usuario desactiva/borra la variation `Claude_revisar_*`; los objetos
`*_revisar` fuera de la red (copias de tipos) quedan para borrar a mano si no se deshicieron. Para aceptar: el usuario
revisa la variation y la conserva (y guarda el escenario si corresponde, él mismo).

Ojo con el **auto-guardado de escenarios** de PF (configuración de usuario): si está activo, los cambios operativos se
guardarían solos. El puente lo advierte al arrancar si hay un escenario activo.

Verificado en PF 2025 SP4 real (05-10-2026, escenario "Laboral Diurno (25C CS)" activo):
- la variation y el stage se crean, `GetRecordingStage()` devuelve el stage de Claude y la sonda pasa;
- `GetActiveScenario()` funciona; el escenario marca `iModified = 1` al recibir un cambio operativo;
- `chr_name` (dato de red) quedó en el delta del stage; **`outserv` (operativo) quedó en el escenario**, aunque el objeto
  ya tenía delta en el stage (el delta conservó outserv = 0). Por eso el destino se determina leyendo el delta del stage
  (`_en_stage`), no contando entradas;
- **Renombrar (`loc_name`) NO se registra** en la variation ni en el escenario: se aplica directo al objeto base
  (verificado: se detectó y se deshizo). Por eso el destino "escenario" sólo se acepta para atributos de
  `OPERATIVOS`; cualquier otro cambio de red que no aparezca en el delta del stage se revierte. Renombres de objetos
  existentes: proponerlos al usuario, no hacerlos.
- `deshacer()` restauró ambos valores. Queda el delta en el stage (con los valores originales, efecto nulo) y el
  escenario marcado como modificado (valores iguales a los guardados): al cerrarlo, responder No a guardar.

## Casos de estudio y escenarios (ambos modos)

- `cambiar_caso("03_15 SS", "Laboral Vespertino (15C SS)")`: activa **primero el caso de estudio** (cambia los
  triggers: la temperatura de los límites térmicos de las líneas) y **después el escenario** (nombre o ruta final,
  p. ej. `r"Base\Laboral Vespertino (15C SS)"` si el nombre se repite). `contexto()` muestra caso, escenario y si el
  escenario tiene cambios sin guardar. `Activate()/Deactivate()` directos sobre IntCase/IntScenario también pasan.
- No se cambia de caso ni de escenario si el escenario activo tiene cambios sin guardar (PF los guardaría o perdería).
- Al detener el puente se vuelve al caso y escenario con que partió (si el escenario actual tiene cambios, no).
- Ojo: las variations activas son por caso de estudio. Al cambiar de caso, la variation de Claude puede no estar
  activa: los cambios de red se rechazan (se revierten); los operativos van al escenario.

## Escenarios: regla de guardado (modo modificación)

**Convención `_secure` (07-10-2026, pedido del usuario):** lo intocable se marca con `_secure` (el escenario o cualquier carpeta que lo contenga). Con al menos un `_secure` en Operation Scenarios rige esta convención: se puede guardar, mover y renombrar (`renombrar_escenario`) cualquier escenario/carpeta no protegido; `copiar_escenario(nombre, nuevo=None, carpeta=None)` copia sin sufijo (el original sin `_secure`, o `nuevo`) y `carpeta_escenarios(nombre, padre=None)` crea carpetas. Lo protegido no se guarda, no se mueve ni se renombra (agregar `_secure` sí). **Sin ningún `_secure` en el proyecto rige la regla anterior (`_revisar`)**, para no dejar desprotegidos los originales. Las copias de biblioteca (`revisar(obj)`: tipos, características) siguen con `_revisar`.
Además: las stages temporales de Claude se reubican todas en orden al arrancar (no sólo las activas en el caso), para que dos nunca queden en el mismo minuto (Variation conflict ⇒ PF no activa ninguna stage).

- Los escenarios del proyecto son la base (irrestricta). **Nunca se modifica ni guarda un escenario original.**
- Para dejar cambios guardados: `copiar_escenario("Laboral Diurno (25C CS)")` crea `..._revisar` junto al original;
  activar la copia con `cambiar_caso(caso, copia.loc_name)`, modificar y, **sólo tras confirmación del usuario en el
  chat**, `app.GetActiveScenario().Save()` (el puente sólo permite Save en copias `_revisar`).
- Cualquier modificación (red o escenario) se propone primero y se aplica cuando el usuario confirma.

## Pérdida de conexión

Si PF invalida el objeto app ("'powerfactory.Application' already deleted"; pasa típicamente en la primera lectura
pesada después de un flujo de carga), el comando falla y el puente se reconecta antes del siguiente (`reconexiones` en
el estado; objetos re-resueltos por ruta). Los drivers deben reintentar ese error (comandos idempotentes: escribir
valores absolutos, no incrementos). Si las reconexiones fallan en serie (errores en ~0,00 s, `proyecto: null` en el
estado) la sesión Python de PF quedó inutilizable (visto dos veces tras muchos flujos y lecturas de todas las barras): tras
5 comandos seguidos así el puente se detiene solo con ese motivo; pedir al usuario reiniciarlo. El estado del
escenario (cambios sin guardar) sobrevive al reinicio. Si la reconexión no encuentra
proyecto, el puente se detiene (motivo "PF desconectado").

Desde el 09-10-2026 el puente hace `ns.clear(); gc.collect()` al terminar cada comando: las caídas aparecían en el
comando SIGUIENTE a uno que recorrió miles de objetos o escribió muchos SetVitxt, cuando Python soltaba las referencias
en un momento cualquiera. Con eso dejaron de aparecer en el constructor del unilineal (~2.700 escrituras por corrida).

## Output Window (ambos modos, solo lectura)

- Cada resultado trae `output_window`: `lineas` (todo lo nuevo que escribió PF durante el comando), `errores` y `avisos`
  (con filtro por tipo de la API, `GetContent(MessageType.X)`), con sus conteos `n_*`; máximo 400 líneas por lista.
  `pf_send.py` imprime errores y avisos (40 por tipo) y con `--ow` todas las líneas. Si la API no expone la ventana o
  el app quedó invalidado tras el comando: `disponible: False` y una `nota`.
- En el comando: `salida(tipo=None, n=50, buscar=None)` devuelve las últimas n líneas (`tipo` en error/warn/info/plain/
  event; `buscar` regex; n=0 todas). Útil tras un flujo: `salida("warn", 0, "reactive power limit")`.
- Nunca se limpia la ventana (es del usuario). Las líneas nuevas se calculan por diferencia de largo; si PF la limpió
  durante el comando, se devuelve todo lo que hay.

## Límites

- Un comando que entra en un bucle largo bloquea el puente y PF: no hay timeout dentro de PF. Comandos cortos; para
  recorrer muchos objetos, por lotes.
- **Nunca `GetContents(..., 1)` recursivo sobre el usuario** (`app.GetCurrentUser()`) ni sobre carpetas que contengan
  otros proyectos: recorre toda la base de datos. El 11-10-2026 una búsqueda de `*.SetParalman` así dejó el puente
  colgado horas y PF terminó cerrándose. Buscar dentro del proyecto activo o en una ruta conocida.
- **Licencia sin análisis de contingencias** (11-10-2026): `ComSimoutage.Execute()` falla con «The selected licence does
  not allow the execution of command 'ComSimoutage'». El N-1 se hace con flujos sucesivos (outserv + ComLdf). Para armar
  un ComOutage: `SetObjs` está bloqueado por el puente y `EvtOutage` no es hijo válido; se usa `EvtSwitch` (`p_target` =
  elemento, `i_switch` 0 abre / 1 cierra).
- La GUI puede inspeccionarse con Computer Use o capturas autorizadas; gráficos y tablas también se exportan a archivo (`guardar`, o `ComRes` si se habilita el cálculo).
  Fotos de diagramas: ver «Fotos de diagramas» más abajo.
- Todo queda en `pf_bridge\bridge.log` (id, ok, error, duración) y los comandos ejecutados en `pf_bridge\done`.
- Verificado en PF 2025 SP4 real (Python 3.11, 05-10-2026): lectura de 3.210 ElmLne en 0,2 s, bloqueo de
  SetAttribute sobre un objeto real, serialización de `resultado`. También probado con `fake_powerfactory`.
- **Barras invertidas en el código enviado**: el transporte del puente las reduce un nivel (como `unicode_escape`):
  dos barras seguidas de n en el código llegan a Python como `\n` y se leen como salto de línea real. Para una barra
  literal usar `chr(92)`. Las regex `r"..."` con `\(` o `\d` no cambian (escapes desconocidos se conservan).
- **Archivos de comando sin BOM** (23-10-2026): PowerShell 5.1 `Set-Content -Encoding utf8` escribe BOM y el Python de PF
  falla con «invalid non-printable character U+FEFF». Escribir el comando con la herramienta Write o desde Python.
- **Costo fijo por comando** (23-10-2026): en la sesión del puente de las 11:34 cada comando tardó ~197 s aunque fallara al
  compilar (antes, < 1 s). Juntar lecturas grandes en un solo comando y medir con `bridge.log` (`"s"`). Causa no aislada.
- `obj.GetAttributes()` existe pero falla («getting attributes … failed»): no sirve para listar atributos. Buscar el
  nombre con `app.GetAvailableAttributesAsJson` y unir la DB de localización; ver
  [attribute-metadata.md](attribute-metadata.md). TechRef/hover sólo para ambigüedades restantes.
- `GetCalcRelevantObjects()` sin patrón de clase tarda ~3 min (158 mil objetos en el SEN): filtrar siempre por clase.
- **Escribir sólo lo que cambia**: si un `SetAttribute` deja el mismo valor, PF no crea delta y el puente rechaza la
  escritura («no quedó en la variation»), abortando el resto del objeto. Comparar antes y escribir sólo los atributos
  distintos. Ojo: el puente busca el delta por `loc_name`+clase en el stage; nombres repetidos (52JT1, T_12...) de otras
  S/E pueden dar falsos positivos o negativos (10-10-2026, límites de tensión ETS).

## Drivers: plantillas con reintento (`scripts/pf_drv.py`)

Para tareas que se repiten por escenario o caso, el script del comando es una plantilla con marcadores `__X__` y un
driver la rellena, la manda y filtra la salida por prefijo (cada script imprime sus líneas útiles con un prefijo corto,
p. ej. `DF`, `S1`, `DZ`):

```python
import sys; sys.path.insert(0, r"C:\Users\vicen\.claude\skills\powerfactory-python\scripts")
import pf_drv
pf_drv.run("s1_diff.py", filtro=("S1", "ERROR", "Trace", "  File", "Error"), ESC="E01_...", CASO="02_25 CS")
```

- Reintenta hasta 4 veces si la respuesta trae «already deleted» (el comando debe ser idempotente: valores absolutos).
- Los marcadores también sirven para opciones (`__SINLIM__` = "1" activa una variante dentro del script).
- Corridas largas (más de ~2 min) en segundo plano desde la shell, una a la vez: el puente ejecuta en serie.

## Fotos de diagramas

- `exportar_grafico(nombre, pagina=None)` (en el comando) escribe la página gráfica a WMF en `pf_bridge\files`. **PF
  agrega su propia extensión: el archivo queda `nombre.wmf.wmf`.**
- Mientras corre el puente PF no repinta: un diagrama ya abierto exporta la imagen vieja. Antes de exportar,
  `dg.Close(); dg.Show()` sobre el `IntGrfnet` (permitido) fuerza el redibujo.
- No reutilizar el nombre de un diagrama borrado (p. ej. una copia de prueba): `GetPage(nombre)` puede devolver la
  pestaña vieja y la foto sale sin textos ni resultados, en hoja A. Usar un nombre nuevo.
- Si la foto sale sin cajas de resultados en todo el diagrama, el flujo dejó de ser válido: correrlo
  (`app.GetFromStudyCase("ComLdf").Execute()`). En modo modificación el cálculo está permitido; `allow_calc: false` en
  `estado` sólo se refiere al modo lectura.
- Conversión a PNG: `scripts/wmf2png.ps1 -Nombre foto -Ancho 6400 -Salida <carpeta>` (System.Drawing, sin
  dependencias). 3.200 px alcanzan para ver la forma de una hoja de ~640 mm; para leer cifras de cajas en una hoja de
  1 m usar 6.400 px y recortar zonas con PIL.
- Para fotos de resultados sin el rojo de sobrecarga (p. ej. un flujo diferencial): apagar las alarmas del esquema de
  colores, `SetColscheme.cUseAlarm = 0` (pedido del usuario, 10-10-2026).

## Capturas de escritorio (`scripts/captura_escritorio.ps1`)

Captura todas las pantallas a PNG (`%USERPROFILE%\pf_bridge\capturas`), para ver la GUI de PF (árbol del proyecto,
diagramas, ventana de salida, diálogos) u otras ventanas. Sólo cuando el usuario lo pide o lo acordó en la sesión.

```powershell
& ~/.claude/skills/powerfactory-python/scripts/captura_escritorio.ps1 -Escala 0.6   # luego Read del PNG
```

- Dos monitores de 2400x1350 → 4800x1350; con `-Escala 0.6` se lee el texto grande (títulos, árbol, salida) pero no
  las cifras pequeñas de un diagrama: para eso, escala 1.0.
- Mientras el puente corre PF no se repinta (título "NON-INTERACTIVE MODE"): la captura puede mostrar un estado viejo.
  Para ver el efecto de un comando en la GUI, detener el puente y capturar.

- Mover escenarios/carpetas en Operation Scenarios: con el puente se llama `objeto.Move(destino)` (el envoltorio llama internamente `destino.Move(obj)`); sólo dentro de Operation Scenarios y nunca la carpeta del escenario activo (activar antes otro). Renombrar carpetas de escenarios (`loc_name`) está bloqueado: lo hace el usuario. Lo que crea el puente lleva sufijo `_CdN`.
