# Metadatos GUI de atributos: etiquetas y opciones (DB de localización)

Verificado el 04-11-2026 con PowerFactory **2025 SP4** (root
`C:\Program Files\DIgSILENT\PowerFactory 2025 SP4`). Consulta repetible con
`scripts\pf_attribute_metadata.py` (solo stdlib; no abre una sesión de PF).
La documentación de powfacpy AttributeMetadata se cita solo como referencia:
https://fraunhiee-unikassel-powsysstability.github.io/powfacpy/docs/api/powfacpy/applications/attribute_metadata.html
(no se copia código externo).

## Qué es y qué no es

La DB de localización es un **catálogo de cadenas de la GUI**, no un inventario de atributos:

| Mide | No mide |
|---|---|
| Etiqueta visible en el diálogo (con o sin abreviatura tras `\|`) | Que un atributo exista en un objeto o clase: la ausencia aquí no prueba inexistencia (**fuente de inventario**: enumerador, más abajo) |
| Texto en línea de un menú `i*_`, en el orden del mensaje | Códigos de enum: si la DB no trae tabla de códigos, se reportan como desconocidos (jamás generados) |
| Comentario/help por atributo (línea `lang=comment`) | Valores activos del proyecto (leer con GetAttribute del modelo, no de esta DB) |
| Consulta por clase + parámetro exactos | Autorización para escribir en PF: metadatos DB no implican permiso de modificación |

## Origen de los datos

- Archivo: `<instalación>\localisation\<idioma>\data.db` — SQLite de solo lectura
  (URI `?mode=ro` + PRAGMA query_only). En esta instalación hay localizaciones
  de-DE, en-GB, es-ES, fr-FR, ru-RU, tr-TR, zh-CN (qtlib no trae data.db).
- Solo la tabla `Message(lang, class, param, message)` + índices internos:
  **162,707 filas** (lang=en 162,132; lang=comment 575) y **3,957 clases** —
  filas no ≡ número de parámetros. Versiones futuras y otras localizaciones
  pueden traer otras tablas o esquemas: el CLI valida el esquema antes de
  usar una propiedad/columna y en pantalla declara las tablas halladas.

## Uso del CLI

```powershell
python scripts\pf_attribute_metadata.py --class ComInc --attribute iopt_solvinc
python scripts\pf_attribute_metadata.py --class ElmGenstat --attribute iSimModel
python scripts\pf_attribute_metadata.py --search "A-stable"          # acotada, min 3 car.
python scripts\pf_attribute_metadata.py --class ComInc               # solo: lista params (acotado)
python scripts\pf_attribute_metadata.py --list-classes               # también con --search
python scripts\pf_attribute_metadata.py --schema                     # tablas/contajes
python scripts\pf_attribute_metadata.py --class ComInc --output catalogo.csv        # exportar
python scripts\pf_attribute_metadata.py --export --output todo.csv   # tabla completa
```

- `--installation DIR` (default 2025 SP4) o `--db FILE` directo; `--loc` cambia
  idioma (default en-GB). La DB **debe existir**: si la ruta no existe se falla
  con error explícito y no se crea ningún archivo.
- Pantalla acotada a 40 filas con marcador `>> Truncado...`; para exportar
  todo, `--output ARCHIVO` (CSV `;` + utf-8-sig, o `--format json`), que nunca
  puede apuntar al propio data.db y no reemplaza un archivo existente salvo
  con `--overwrite`. La exportación resume conteo + ruta, sin volcar datos.

## Campos que entrega cada fila

- `db` **el path de donde salió el dato**, `lang` (en|comment), `class`, `param`,
  y `message` crudo **preservado íntegro**.
- `label`: todo lo anterior al primer `|` o al primer `:`; tras `|` viene
  abreviatura (`iopt_lt`). Tras el primer `:` vienen **opciones de menú inline
  en el orden del mensaje** (`iSimModel`) — marcadas `inline_sequence`
  (Message, lang=en). Si la DB trae una tabla de códigos (class,param,código,
  texto) el CLI la detecta y marca `explicit_row` con el código leído; la
  ausencia de ese par se reporta como **desconocido, sin códigos generados**.
- Filas `lang=comment` se entregan crudas (no se interpretan como menú).

## Casos con evidencia separada por fuente

**DB SP4 (04-11-2026, CLI contra data.db en-GB):**

| Par | Resultado DB |
|---|---|
| `ComInc.iopt_solvinc` | etiqueta única "Solve dynamic model equations at initialisation" (sin opciones) |
| `ComInc.iopt_fastcon` | "Fast connection of A-stable models outputs" |
| `ComInc.iopt_lt` | "A-stable integration algorithm" \| abreviatura "A-stable alg." |
| `ElmDsl.iAstabint` | "A-stable integration algorithm (only for RMS Simulation)" |
| `ElmGenstat.iSimModel` | "Model:" + opciones inline "According to connected input signals / Current source / Voltage source / Constant impedance / Constant power" |
| `ElmGenstat.ictrltp` (y ElmPvsys) | "Model:" + "const.V / const.I" — **el caso ictrltp de la DB vive en ElmGenstat/ElmPvsys, no en ComInc** (0 filas en ComInc) |
| `ComInc.iopt_lt0` | **0 filas** — la numeración de sus valores viene de la GUI, no de la DB (ver abajo) |
| `ComInc.ictrltp` | 0 filas |

**GUI, verificado por usuario (no es DB, no mezclar fuente):**

- `ComInc.iopt_lt0`: 0 = por elemento; 1 = todos; 2 = por elemento y compuesto
  (hover del diálogo; nada de esto sale de la DB, que trae 0 filas).
- `ElmDsl.iAstabint` con valor 1 «seleccionado» en el diálogo ⇒ método A-stable
  activado; el hecho lo registró el usuario en PF, no la DB.

## Errores a evitar

- `iopt_adapt` = "Automatic step size adaptation" ⇒ **0 = paso fijo, NO
  «no A-stable»**: el nombre del parámetro no indica el método.
- Un `:` no siempre separa opciones (comentarios largos, unidades): las filas
  `comment` y los mensajes que empiezan por `:` quedan crudos.
- Los códigos de enum jamás se adivinan («empieza en 0» es intuición): sin
  tabla de códigos en la DB, reporta `códigos desconocidos` y pide al usuario
  el hover en el diálogo de PF (muestra `Attribute: <nombre>` y sus códigos),
  o búscalo en `TechRef_<equipo>.pdf`.
- Esta DB **no** es el inventario de attributes ni de results: para listar lo
  que un objeto real trae, usa el enumerador del puente (más abajo).

## Inventario real de atributos

Para la lista completa de atributos de una clase con objeto real:
`app.GetAvailableAttributesAsJson(clase, '', 1, 'e', 'name')` + `obj.GetAttribute`,
por el puente de la skill (ya probado en ejecuciones reales; ver
`references/bridge.md`). Alternativas nativas si se trabaja sin puente y la
forma de conexión lo permite: `GetAttributeDescription` /
`GetAttributeUnit` / `GetAttributeType` — jamás bypasean las restricciones
del puente, y estos metadatos no autorizan por sí mismos a escribir
parámetros en PF. Detalle por equipo y tablas de atributos:
`Help\TechRef\TechRef_<equipo>.pdf` (leer con la skill `pdf`, pypdf).

## Test

`python scripts\test_pf_attribute_metadata.py` — stdlib tests con DBs
sintéticas (no usan la DB real): ruta ausente no se crea, esquema inesperado,
espacios y `#` en ruta, consultas parametrizadas, límite de pantalla,
comments crudos, opciones inline sin códigos, `explicit_row` con tabla,
exports con/protección del data.db.
