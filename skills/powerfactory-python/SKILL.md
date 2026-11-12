---
name: powerfactory-python
description: Escribe, revisa y prueba scripts Python / ComPython para DIgSILENT PowerFactory (PF) — leer y modificar parámetros del modelo en lote con variations y stages verificados, extraer datos a JSON/CSV — y, por el puente a la sesión abierta de PF, unilineales por script, flujo diferencial, N-1 y estudios de restricciones. Úsala siempre que se pida un script, macro o ComPython de PF/DIgSILENT, cambiar parámetros en lote (capacidades, tipos, tensiones, taps), crear variations/stages, dibujar un unilineal, correr flujos, N-1 o restricciones, exportar datos del modelo o depurar un script de PF, aunque no diga "skill" ni "ComPython".
---

# Scripts Python para PowerFactory

PowerFactory castiga los errores de forma silenciosa: un cambio en el objeto equivocado queda en el
caso base de todos los estudios, o en la variation de otra persona. Esta skill reúne lo que se ha
comprobado en ejecuciones reales para escribir scripts que leen con precisión y escriben solo donde
corresponde.

Qué hay en la skill:
- `references/object-model.md` — cadenas de punteros y atributos verificados. Léelo antes de leer o escribir cualquier parámetro.
- `scripts/pf_attribute_metadata.py` — etiqueta y opciones de un parámetro desde la DB de localización del PF instalado (SQLite solo lectura, sin abrir PF); cobertura y evidencia por fuente: `references/attribute-metadata.md`.
- `references/thermal-ratings-case.md` — caso completo (extractor → app → paquete → writeback). Léelo al extraer datos a otra app o aplicar cambios en lote.
- `scripts/pf_variations.py` — variation + stage + verificación de registro, listos para pegar o importar.
- `scripts/pf_bridge.py` + `scripts/pf_send.py` — puente a la sesión de PF abierta (solo lectura por defecto); ver `references/bridge.md`.
- `scripts/pf_bridge_full.py` + `scripts/pf_full_send.py` — puente de acceso total para adecuación, poda y organización cuando el usuario autoriza ese modo. Leer `references/bridge-full.md`; no cambia el modo por defecto de otras tareas.
- `scripts/fake_powerfactory.py` y `scripts/run_with_fake.py` — PowerFactory simulado para probar fuera de PF.

## Modelo mental: red vs biblioteca

La distinción que más importa: **las variations solo registran cambios en objetos de la red** (lo que
cuelga de Network Data: ElmNet, ElmLne, ElmTow, ElmTr2, ElmLod, StaCubic...). **La biblioteca**
(Equipment Type Library, Operational Library: tipos Typ*, características Cha*, escalas Tri*) **no se
registra**: editarla cambia el modelo base para todos los casos de estudio y variations.

Consecuencia práctica: muchos parámetros viven en la biblioteca. La capacidad de una línea, por
ejemplo, está en su tipo: `ElmLne.typ_id → TypLne.sline`, y la característica térmica cuelga del tipo
(`TypLne` contiene un `sline.ChaRef` que apunta a una `ChaMat`). Para cambiar esa capacidad "solo en
una variation":

1. **Copiar** los objetos de biblioteca involucrados con un sufijo (`AddCopy`), en una carpeta propia.
2. Escribir los valores nuevos **en las copias**.
3. Dentro del stage, **repuntar** el puntero que vive en la red (`ElmLne.typ_id`, `ElmTow.pGeo`...) a la copia.

Así nunca se edita un objeto existente, desactivar la variation devuelve el modelo original y los
objetos compartidos por otras líneas no se tocan. Antes de diseñar un cambio, identifica siempre qué
puntero de la cadena vive en la red: ese es el único que se debe modificar dentro del stage.

Cuando el parámetro es del propio elemento (un atributo del ElmLod, del ElmTr2...), el elemento está en
la red y el cambio se registra directo en el stage, sin copias. Si hay duda sobre dónde vive un
objeto, sube por `GetParent()` hasta ver si llega a un `ElmNet` (red) o a una carpeta de Library.

## API: lo verificado

- `app = powerfactory.GetApplication()`; salida con `app.PrintPlain / PrintWarn / PrintError`.
- **Identidad**: `obj.GetFullName()` (ruta completa con clases, ej. `...\Red.ElmNet\A - B.ElmLne`).
  Es la clave estable para cruzar datos entre ejecuciones y con otras apps. Los nombres (`loc_name`)
  se repiten entre redes: nunca identifiques solo por nombre.
- Objetos de las redes activas: `app.GetCalcRelevantObjects("*.ElmLne")`.
- Hijos: `obj.GetContents("patron.Clase", recursivo)` — ej. `tipo.GetContents("sline.ChaRef")`.
- Atributos: `obj.GetAttribute("x")` / `obj.SetAttribute("x", v)`. Vectores y matrices se leen y
  escriben como listas de Python (`ChaMat.matrix`, `TriDisc.cases`, `TypTow.pcond_c`). Un atributo
  puede venir como objeto único o como lista: normaliza con una función `as_list`.
- Envuelve lecturas en un `get_attr(obj, "x", default)` con try/except: un atributo inexistente lanza
  excepción y detiene el script a mitad de camino.
- Crear: `carpeta.CreateObject("Clase", "nombre")`. Copiar: `carpeta.AddCopy(obj, "nombre")` (copia
  también los hijos, como el `sline.ChaRef` del tipo — hay que repuntarlo en la copia).
- Carpetas del proyecto: `app.GetProjectFolder("equip" | "oplib" | "chars" | "scheme" | "netdat" | "study")`.
  Las escalas viven en una `IntScales` (normalmente "Scale") dentro de Characteristics.
- Nombres: sanea `\ / : * ? " < > |` y limita a 40 caracteres (conservador), garantizando unicidad.

Para atributos concretos (sline, dline, sernum, e:Unom, pGeo, c_ptow, scalerow/scalecol...) consulta
`references/object-model.md`. Si necesitas un atributo que no está ahí, dilo y verifícalo en la
primera ejecución (léelo y regístralo en el log) en vez de asumir el nombre.

## Etiqueta y opciones de un parámetro (metadatos GUI)

Consultas repetidas («¿qué significa cada opción de este iSimModel?») se resuelven sin abrir PF con
`scripts/pf_attribute_metadata.py --class <Clase> --attribute <param>` (o `--search`/`--list-classes`; exportar con `--output`). Es el
catálogo de la GUI localizada: etiqueta, abreviatura tras `|` y opciones tras `:`, del DB de
localización del PF instalado. **No es inventario de atributos ni de results** (ese lo da
`app.GetAvailableAttributesAsJson(clase,'',1,'e','name')` por el puente) ni trae valores activos ni
autoriza escrituras; y los códigos de enum que no estén, se reportan desconocidos — no se generan.
Cobertura, límites y casos verificados: `references/attribute-metadata.md`.

## Escribir de forma segura

Estructura todo script que modifica el modelo en dos fases:

**1. Plan (solo lectura).** Resuelve cada objeto por su ruta, comprueba que el modelo sigue como se
espera (el tipo actual es el esperado, los valores actuales coinciden con los que se revisaron, los
nombres nuevos no existen) y clasifica cada ítem: `listo`, `ya aplicado`, `omitido` con motivo.
Por defecto el script termina aquí (**dry run**) y deja un reporte CSV. Esto permite revisar sin
riesgo y hace el script re-ejecutable.

**2. Aplicar (solo si el usuario lo elige).** Orden:
1. Abrir variation + stage y **verificar que se está registrando ahí** antes de crear nada
   (`open_recording_stage` en `scripts/pf_variations.py`). Si no se puede confirmar, abortar.
2. Crear los objetos nuevos en la biblioteca (carpetas y copias con sufijo).
3. Hacer el cambio en la red (repuntar), **releer cada valor escrito** y marcar error si no coincide.
4. Resumen: aplicados / errores / entradas nuevas en el stage. Si se aplicaron cambios y el stage no
   creció, advertir.

Reglas que evitan los accidentes típicos:
- **Idempotencia**: si el puntero ya apunta a la copia con ese sufijo, es `ya aplicado`, no un error.
- **Valores esperados**: guarda en el paquete de entrada lo que el script debe encontrar (ruta del
  tipo, valores actuales); si cambió desde la extracción, omite ese ítem con el motivo.
- **Objetos compartidos**: un tipo o una característica pueden usarlo muchas líneas; un ElmTow
  (acoplamiento) afecta a todos los circuitos acoplados. Lista explícitamente lo que también cambia.
- **Nunca** borrar ni editar objetos existentes de la biblioteca; para crear una característica,
  copia una existente como plantilla (conserva su configuración de uso y unidades) y reemplaza escalas y valores.
- Cada ítem en su propio try/except: un error en una línea no deja las demás a medias sin reporte.

## Variations y stages: lo aprendido en ejecuciones reales

- PF registra en **un solo stage global**: el stage activo con `tAcTime` más reciente ≤ study time,
  considerando todas las variations activas. Por eso: fijar study time → activar el stage → verificar.
- `stage.Activate()` devuelve 1 (avisos) o 16 (ajustó el study time) aunque funcione: no son errores,
  pero obligan a verificar.
- Un objeto creado en la red mientras se registra **informa la red como padre**, no el stage. Subir por
  `GetParent()` no sirve para confirmar el registro: compara `stage.GetContents("*", 1)` antes y después
  de crear un objeto de prueba (así lo hace `verify_recording_with_probe`).
- Ajustar el study time es un efecto visible sobre el caso de estudio del usuario: menciónalo en el log.
- Fechas de stage: usa `stage_time_from("dd-mm-aaaa HH:MM")` (precisión al minuto). La conversión base
  tiene un desfase horario fijo calibrado para Chile; pide al usuario confirmar en PF que el stage
  muestra la hora ingresada en la primera ejecución.

## Ventana, intercambio, pruebas y entrega

Se leen sólo cuando el script lo necesita:
- Ventana de configuración (tkinter) o paquetes JSON/CSV con otra app → `references/scripts-con-ventana.md`.
- Probar con el PF simulado y entregar → `references/probar-y-entregar.md`.

Reglas que valen siempre, aunque no se lea ese archivo: un script que escribe se entrega en **dry run por defecto**, con
log por ítem (`[listo]`, `[ya aplicado]`, `[omitido] motivo`, `[aplicado]`, `[error]`) y conteos finales; si se probó con
el PF simulado, **decir que éste no valida la API real** (atributos, unidades, códigos de retorno) y sugerir una primera
ejecución en Simular sobre una copia del proyecto.

## Probar directo en PF (puente)

Si el usuario pide el puente **full/acceso total** o autoriza una adecuación con ese puente, usar
[`references/bridge-full.md`](references/bridge-full.md). Su autorización de modo y alcance persiste durante la tarea;
no pedir de nuevo por cada escritura incluida. El puente full permite también organización y movimientos entre carpetas,
que no deben tratarse como cambios aislados en una variation. Trabajar con respaldo, inventario y verificación del estado.

Si el puente está corriendo (`python scripts/pf_send.py estado` → vivo), úsalo para verificar atributos, punteros y valores
reales antes de entregar un script, en vez de pedirle al usuario que lo ejecute. Solo lectura por defecto. Los modos
modificación (variation de sesión, marca `[CdN]`, diario y `deshacer`) y limpieza (escritura directa, diario sin
variation) sólo se usan si el usuario autorizó ese modo para el proyecto y la tarea. Con esa autorización el agente puede
lanzarlos por la ruta GUI/PowerShell documentada, sin repetir la aprobación durante la misma tarea; si no la hay, preguntar
modo y alcance antes de arrancar. Autorizar el arranque no autoriza cambios de planta ajenos al alcance acordado ni elevar
el modo por iniciativa propia: «lanza el puente de modificación para el laboratorio» habilita ese arranque y los cambios
del laboratorio; «lee los estados» deja el puente en solo lectura. Para abrir PF/cambiar de proyecto/arrancar el
puente y para la ruta PowerShell autorizada cuando Computer Use no está disponible, leer
[Arranque por GUI](references/arranque-puente-gui.md): incluye el procedimiento real del 05-11-2026, los lanzadores
verificados `scripts/pf_bridge_modificar.py` y `scripts/pf_bridge_limpieza.py`, y el helper `scripts/pf_ui.ps1`. No usar
esa ruta para eludir restricciones de las herramientas.
Capturas de escritorio (`scripts/captura_escritorio.ps1`) sólo si el usuario lo pidió o lo acordó en la sesión.
Las tareas repetidas por escenario usan plantillas `__X__` y `scripts/pf_drv.py`. Si un comando no devuelve nada,
mirar `estado` antes de reintentar; la versión verificada tiene 120 min de inactividad y 8 h de sesión (puente full:
60 min de inactividad y sin tope de horas salvo que se active; un tope activo, `expira_en_min`, no se reinicia
con actividad). Detalle en `references/bridge-full.md`.
Detalle y límites: `references/bridge.md`.

## Recetas de estudio (verificadas con el puente)

| Tarea | Referencia | Ejemplo |
|---|---|---|
| Unilineal «de informe» por script (copia `_CdN`, cajas, anotaciones, compactación, foto) | `references/diagramas-unilineales.md` | `Cumbres del Ñuble\herramientas\unilineal\` |
| Flujo diferencial (ComDiff, B − A) con foto y factores | `references/flujo-diferencial.md` | `scripts/ejemplos/flujo_diferencial.py` |
| Fotos de diagramas (WMF → PNG) | `references/bridge.md`, «Fotos de diagramas» | `scripts/wmf2png.ps1` |
| Objetos gráficos y topología (cubículos, acoples, barras auxiliares) | `references/object-model.md` | — |
| Estudio de restricciones: preparar escenarios, convergencia y tensión, N-1, factores con ficticios, prorrata, iteraciones | `references/estudio-restricciones.md` | `Cumbres del Ñuble\herramientas\estudio_cumbres\` |
| Estructura final de la BD de un estudio, validación de escenarios, contraste entre herramientas, orden y cierre; trampas de PF posteriores al 10-10-2026 (dos reguladores de tensión en un terminal, solución espuria) | `references/cierre-bd.md` | — |
| Método del estudio, decisiones que se cierran con el usuario, BESS e híbridos, informe | skill `estudio-restricciones` | — |
| Replicar el flujo AC de PF fuera de PF (pypowsybl): qué extraer, modelo de cada equipo (taps, Tr3, acoplamientos, controles, SVC), convenciones de signo, validación por capas | `references/modelo-flujo-pf.md` | `Cumbres del Ñuble\.revision_diagrama\factores_lineales_2310\scripts\` |

Documentación oficial del modelo de cada equipo (ecuaciones y tablas de atributos): `C:\Program Files\DIgSILENT\
PowerFactory 2025 SP4\Help\TechRef\TechRef_<equipo>.pdf` (manual en `Help\UserManual_en.pdf`, API en
`Help\PythonReference_en.pdf`). Para leerlos: `pypdf` a texto y buscar por atributo. Antes de adivinar un nombre de
atributo, buscarlo ahí o pedirle al usuario el hover en el diálogo de PF (muestra `Attribute: <nombre>` y sus códigos).

Para llevar resultados y fotos al informe Word, usar la skill `informe-ee` (redacción, tablas y figuras de EE).

