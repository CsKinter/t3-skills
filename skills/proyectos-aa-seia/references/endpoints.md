# Endpoints y fuentes

Todos los ejemplos se probaron el 02-11-2026. Las URLs cambian poco, pero si un
endpoint falla, abrir la página en el navegador y mirar la pestaña Network antes
de reescribir el script.

## 1. Acceso Abierto del CEN — base pública (la más valiosa)

```
GET https://pkb3ax2pkg.execute-api.us-east-2.amazonaws.com/prod/data/public
    ?tipo=6&anio=2026&tipo_solicitud_id=0&solicitud_id=null
```

Sin token, sin cookies. Devuelve **todas** las solicitudes (~2.870 registros,
4 MB). El parámetro `anio` se ignora: no filtra. Script: `scripts/aa.py`.

Campos útiles:

| Campo | Qué es |
|---|---|
| `nup` | NUP del proyecto (vacío en solicitudes viejas desistidas) |
| `proyecto` | Nombre del proyecto tal como lo escribió el titular |
| `razon_social` | Titular o desarrollador que firma la SAC |
| `estado_solicitud` | «Proyecto autorizado para declararse en construcción», «Desistida», «Rechazada», «Evaluación Admisibilidad», «Observaciones a IAC Preliminar»... |
| `tipo_solicitud` | SASC / SUCTD |
| `tipo_proyecto_nombre` | Generación / Consumo / SAE |
| `tipo_tecnologia_nombre` | Eólico / Solar / Híbrido / Almacenamiento / Consumo |
| `potencia_nominal` | **MW de la ficha**. Es el número que se cita como «la ficha dice» |
| `potencia_nsi` | Potencia de inyección declarada (si viene) |
| `potencia_nsr` | Potencia de retiro declarada (si viene) |
| `potencia_cga` | Capacidad de generación autorizada |
| `potencia_caa` | Capacidad de almacenamiento autorizada |
| `energia_caa` | Energía del almacenamiento [MWh] |
| `horas_almacenamiento_caa` | Horas del almacenamiento |
| `nombre_se`, `pano_conexion`, `nivel_tension`, `seccion_barra_conexion` | Punto de conexión exacto |
| `fecha_informe` | Fecha del IAC (definitivo o preliminar) |
| `fecha_estimada_conexion` | PES declarada |
| `create_date`, `update_date` | Cuándo se creó y cuándo se tocó el registro |

**Trampa:** la ficha es un registro administrativo con fecha. Un proyecto puede
tener `potencia_nominal=150`, `tipo_tecnologia=Eólico` y **cero campos de
almacenamiento**, aunque su RCA diga 115,2 MW y su IAC incluya un BESS. Eso no
es un error de lectura: es que el registro no se actualizó. Se reporta como
«AA declara X (fecha)» y se contrasta con la RCA.

**Trampa 2:** `empresa_solicitante` suele venir `undefined`; el dato bueno es
`razon_social`.

## 2. Cartas del CEN

| Qué | URL |
|---|---|
| Buscador | `https://cartas.coordinador.cl/search?q=&empresa=<nombre>&model_type=todos&correlativo=&periodo_reporte=<DD/MM/YYYY HH:MM:SS> - <DD/MM/YYYY HH:MM:SS>&page=N` |
| Ficha | `https://cartas.coordinador.cl/show/<id>` |
| PDF principal | `https://cartas.coordinador.cl/download_saved_file/<id>` |
| Anexo | `https://cartas.coordinador.cl/download_anexos/<id>/<n>` |
| Lista de empresas | `https://cartas.coordinador.cl/api/empresas` |

- El `id` es un ObjectId de 24 hex. El mismo id sirve para `/show/` y para
  `/download_saved_file/`.
- **`q` está roto**: devuelve «No se encontraron resultados» para cualquier
  término, incluso uno que existe. Buscar por `empresa` + periodo y leer la
  columna «Referencia».
- El nombre de la empresa debe ser exacto: «Andes Solar S.A.» y «Andes Solar
  S.A» devuelven conjuntos distintos. Probar con y sin punto final.
- El periodo es obligatorio y con formato `DD/MM/YYYY HH:MM:SS`. Si falta, el
  servidor responde 500.
- Los anexos marcados «es confidencial» no se descargan; el PDF principal a
  veces sí. La ficha dice qué anexos son confidenciales y cuáles no.

## 3. SEIA

| Qué | Cómo |
|---|---|
| Buscar proyecto | `POST https://seia.sea.gob.cl/busqueda/buscarProyectoResumenAction.php` con `nombre`, `titular`, `folio`, `selectRegion`, `selectComuna`, `tipoPresentacion`, `projectStatus`, `PresentacionMin/Max`, `CalificaMin/Max`, `sectores_economicos`, `razoningreso`, `id_tipoexpediente`, `offset=1`, `limit=50` |
| Expediente | `https://seia.sea.gob.cl/expediente/expediente.php?id_expediente=<EXPEDIENTE_ID>` |
| Documento | `https://seia.sea.gob.cl/documentos/documento.php?idDocumento=<id>` |
| Publicación firmada | `https://firma.sea.gob.cl/publicaciones/<AAAA>/<MM>/<DD>/<epoch>_<idDocumento>` |
| Pertinencias | `POST https://seia.sea.gob.cl/pertinencia/resumenPertinenciaBuscar.php` con `p_nombre_pertinencia`, `p_proponent`, `p_region`, etc. |
| Documentos del expediente | `https://seia.sea.gob.cl/expediente/xhr_expediente.php?id_expediente=<id>` (tabla cargada por JS) |

- La búsqueda por nombre funciona mejor **sin tildes ni paréntesis**. El script
  limpia el término antes de enviarlo y lo imprime para que se sepa qué se envió.
- El campo `FECHA_PRESENTACION_FORMAT` es la fecha de **admisión**, no la de
  presentación de la DIA. La RCA suele traer la fecha real de presentación en los
  VISTOS. Si difieren, se citan las dos.
- `ESTADO_PROYECTO` («Aprobado») y `WORKFLOW_DESCRIPCION` («DIA»/«EIA») son la
  forma rápida de saber si el proyecto ya tiene RCA.
- La tabla de documentos del expediente se carga por JavaScript; para enumerarla
  hay que mirar el Network del navegador o usar `xhr_expediente.php`.
- Las pertinencias nuevas viven en `https://pertinencia.sea.gob.cl/api/public/expediente/<ID>`
  (algunas abren sin ClaveÚnica; el buscador público de `seia.sea.gob.cl` sí
  funciona sin sesión).

## 4. CNE

| Qué | URL |
|---|---|
| Reporte Mensual ERNC (potencia, RCA, almacenamiento) | `https://www.cne.cl/wp-content/uploads/<AAAA>/<MM>/RMensual_ERNC_v<AAAAMM>.pdf` |
| Tablas de Declaración en Construcción | `https://www.cne.cl/wp-content/uploads/<AAAA>/<MM>/Tablas-Declaracion-Construccion-<mes>-<AAAA>.xlsx` |
| Resoluciones (REX) | `https://www.cne.cl/archivos_bajar/REX%20<NN>-<AAAA>.PDF` |

El Reporte ERNC trae una tabla de «Proyectos con RCA Aprobada» con columnas
Tecnología / Región / Titular / Nombre / Fecha / Potencia [MW] / Inversión /
WEB / Almacenamiento. **La capa de texto desordena las columnas**: verificar el
orden de las etiquetas antes de asignar un número (ver `trampas.md`).

## 5. Otras

- **`https://accesoabierto.coordinador.cl/`**: SPA Angular con Cognito. La API
  (`pkb3ax2pkg.../prod`) responde 403 «Missing Authentication Token» sin sesión.
  Para leer el IAC hay que entrar con credenciales. La base pública del punto 1
  es el atajo para todo lo demás.
- **`https://pgp.coordinador.cl/`**: plataforma de gestión de proyectos; el
  `extra_data.capacity` aparece en la descripción del NUP.
- **`https://www.coordinador.cl/desarrollo/documentos/...`**: informes de
  proyectos en gestión de conexión y declarados en construcción (ZIP/XLSX por
  mes). Sólo listan proyectos en construcción, no todo el universo.
- **BCN / Ley Chile**: los decretos de obras nuevas se leen mal por HTTP (la
  página exige JavaScript). Citar por la referencia que hace una carta del CEN.

## 6. Herramientas ya hechas del usuario

- `C:\Users\vicen\Documents\FiltradorAA\` — Streamlit + HTML que consume la API
  pública de AA, normaliza tecnologías y exporta Excel. `app.py` es la referencia
  de los campos y de cómo se mapea `potencia_nominal` a «Capacidad [MW]».
- `C:\Users\vicen\Documents\SEIA\seia\` — cliente SEIA (búsqueda por variantes
  del nombre, pertinencias, matcher, exportador). `search_terms.py` tiene la
  limpieza de términos que conviene reutilizar.
