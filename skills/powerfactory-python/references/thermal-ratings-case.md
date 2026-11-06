# Caso trabajado: capacidades térmicas PF ↔ Infotécnica (2026)

Proyecto real que originó esta skill. Úsalo como plantilla de arquitectura cuando un pedido implique
sacar datos de PF, trabajarlos fuera y devolver cambios en lote.

## Piezas

1. **Extractor (ComPython, solo lectura)** — recorre un set de líneas (`External Object` del ComPython
   con un `SetSelect`), resuelve los tres modelos de capacidad (TypLne, TypTow directo, acoplamiento
   ElmTow) y exporta JSON + CSV con: ruta de la línea, `sernum`, tensión, largo, objeto de rating
   (ruta/clase), característica (ruta), escalas con sus casos y la matriz en kA. Los casos no
   resolubles (varios TypCon, clases no soportadas) van a una lista `problems`, nunca como cero.
2. **App local (Python + HTML)** — compara con la fuente externa, deja que el usuario confirme
   asociaciones o cargue valores manualmente, y exporta un **paquete de writeback** JSON
   (`schema_version: thermal-writeback/1`).
3. **Writeback (ComPython)** — ventana tkinter (paquete, fecha/hora del stage, variation,
   Simular/Aplicar) → plan de solo lectura → variation+stage verificados → copias en biblioteca →
   repunte en la red → relectura → reporte CSV.

## Paquete de writeback (por ítem)

- `line.path`, `model`, `rating_object.path/class`, `tower_type`, `line_coupling`.
- `expected_pf`: lo que PF debe tener todavía (sline fijo, o ruta de la ChaMat + valores de las celdas
  comparadas con fila/columna).
- `new_type_name` = `new_characteristic_name` = `<línea>_<sufijo>` (≤ 40, saneado, único);
  en acoplamientos, `<ElmTow>_<sufijo>` y `affected_lines`.
- `matrix_kA`: matriz 2×3 (filas SS/CS × columnas 15/25/35 °C).
- `warnings` para mostrar en el dry run.
- Nivel paquete: `names` (carpeta `Capacidades_<IT|Manual>_<sufijo>`, escalas `Sol_<sufijo>` y
  `Temperatura_<sufijo>`, variation), `template_characteristic_path`, `items`, `blocked`.

## Aplicación por modelo

| Modelo | Copias en biblioteca | Cambio en la red (stage) |
|---|---|---|
| TypLne | TypLne + ChaMat nueva (desde plantilla) | `ElmLne.typ_id` → copia |
| TypTow directo | TypCon + ChaMat, TypTow con `pcond_c` → TypCon copia | `ElmLne.typ_id` → TypTow copia |
| Acoplamiento | igual que TypTow | `ElmTow.pGeo` → TypTow copia (todos los circuitos) |

Circuitos acoplados con valores distintos se bloquean: comparten un TypCon.

## Resultado real

- Dry run y aplicación correctos en PF (5 líneas TypLne con ChaMat, stage en 2033).
- Primer intento de aplicación abortó por la verificación del stage: el objeto de prueba informaba la
  red como padre. Se corrigió comparando el contenido del stage (ver SKILL.md).
- Pendiente de confirmar en PF real: escritura de `ElmTow.pGeo`, triggers de escalas nuevas.

## Carga manual

Mismo paquete con `source: manual`: el usuario ingresa 15 SS, 25 CS y 35 CS; las celdas no usadas de
la ChaMat 2×3 se completan de forma conservadora (SS25 = CS25, SS35 = CS35, CS15 = CS25).
