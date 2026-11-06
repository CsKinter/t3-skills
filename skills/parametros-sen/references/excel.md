# Excel del proyecto (“Tablas …xlsx”) y formato de las tablas

## Editar sin romper el archivo

- **Leer con openpyxl, escribir con Excel por COM** (`scripts/excel_com.ps1`). openpyxl pierde comentarios encadenados,
  customXml y complementos.
- Flujo: script Python que lee el original y arma `cambios.json` (lista de operaciones) → `excel_com.ps1 -Src original
  -Ops cambios.json -Out copia` → revisar la copia con openpyxl (`data_only=True` para ver fórmulas calculadas) → copiar
  a Documentos.
- Insertar filas **de abajo hacia arriba** y escribir sus valores en el mismo momento; así las inserciones posteriores
  (más arriba) arrastran lo ya escrito. Copiar el formato de un par de filas de referencia (`copyfmt` con `n=2`) para
  heredar las celdas combinadas.
- PowerShell: los nombres de variables no distinguen mayúsculas (`$ops` choca con `-Ops`); `Worksheets.Item(nombre)`
  falla → mapa por nombre; números con `.Formula` en cultura invariante; no tocar `CutCopyMode`.

## Hoja `Capacidades_informe` (formato de la tabla del informe)

Columnas B..S: Fuente | Tramo | Cond. 15 °C SS | 25 °C CS | 35 °C CS | Extremo | Paño | Int | Desc | TO | TTCC | CCSS |
kA 15 | Equipo 15 | kA 25 | Equipo 25 | kA 35 | Equipo 35. Dos filas por tramo (una por extremo); B..F y N..S combinadas
verticalmente. Secciones por nivel “Capacidad en [kA] - Líneas XXXkV” que cierran con la fila “(*) Seccionamiento…”.
Fuente vacía = IT; “PET 20XX”, “NUP NNNN”, “… (ref.)” = futura.

Leyenda (también en el informe): Aprobado `C6EFCE` | Rechazado `FFC7CE` | En revisión `FFEB9C` | S/I IT `D9D9D9` |
PET o NUP `9DC3E6` | Instalación futura S/I `FFF2CC`. Encabezados `404040` con texto blanco.

## Hoja `Capacidades_script`

Elementos del modelo PF (ID de la app de carga a IT, nombre, tipo, kV, PF 15/25/35) y columna M con el tramo del informe;
J/K/L traen D/E/F con `=IFERROR(IF(INDEX(Capacidades_informe!$D:$D,MATCH($M4,Capacidades_informe!$C:$C,0))="","",INDEX(...)),"")`.
Al mapear una fila nueva, escribir M y también las tres fórmulas.

## Otras hojas

- `Tensiones de servicio`: Barra | Vs | normal 1,05/0,95 | alerta 1,07/0,93 | emergencia 1,1/0,9 | criterio; grupos por
  nivel; notas (*) tope 245, (**) barra cercana (gris), (***) categoría <200 kV.
- `Parámetros Eléctricos transf.`: agrupar por nivel de tensión; nivel según la ficha del equipo (ojo doble primario).
