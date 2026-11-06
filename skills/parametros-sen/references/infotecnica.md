# Infotécnica: API pública

Base `https://api-infotecnica.coordinador.cl/v1`, header `User-Agent: SuitePMGD-skill`, sin sesión. Es la misma API que usa
la web (la ventana de ficha llama `/{slug}/{id}/fichas-tecnicas/general/`).

## Inventarios (`/{slug}/?page=N&page_size=1000&ordering=id`)

| slug | n aprox. | campos útiles |
|---|---|---|
| `tramos` | 1.900 | `nombre`, `extremo1_descripcion`, `extremo2_descripcion`, `circuito_nombre` |
| `secciones-tramos` | 2.900 | `id_tramo`, `nombre` (una línea puede tener varias secciones: E14, E15…) |
| `panos` | 20.000 | `nombre` (“PA S/E CONCEPCION B12”), `codigo` (PA111, interno), `id_subestacion` |
| `interruptores`, `desconectadores`, `trampas-ondas`, `transformadores-corrientes` | 9k/19k/0,5k/14k | `pano_nombre`, `id_subestacion`, `nombre` (“DES S/E CONCEPCION B8-2”) |
| `transformadores-2d`, `transformadores-3d` | 2.100 / 370 | `nombre`, `subestacion_nombre` |
| `centrales/extended/`, `unidades-generadoras/?id_central=` | | |
| `instalaciones-tipos/`, `tipos-fichas-tecnicas/?id_instalacion_tipo=N` | | catálogo de tipos y fichas |

## Fichas (`/{slug}/{id}/fichas-tecnicas/{general|limites-termicos}/`)

Diccionario de filas con `nombre_concepto`, `unidad_nemo`, `valor_texto`, `estado_certificacion_nombre`
(Validado / Sin Revisar / Rechazado) y `observaciones` (motivo del rechazo).

| Instalación | Concepto (regex con ^…$) | Unidad |
|---|---|---|
| interruptor | `4.5 Corriente nominal` | [A] → /1000 |
| desconectador | `23.1.4 Corriente nominal` | [kA] |
| trampa de onda | `22.1.2 Corriente nominal` | [kA] |
| TTCC | `20.1.4 Sobrecarga permanente` (= TAP × factor). Excluir `Factor de sobrecarga permanente` [p.u] y `… corta duración` | [kA] |
| sección, `limites-termicos` | `Sin Sol 15°C`, `Con Sol 25°C`, `Con Sol 35°C` (también 0–35 °C cada 5 y variantes `/50%`; hay `Sin Sol 20°C.` con punto) | [kA] |
| sección, `general` | `1.9 Límite térmico permanente en invierno con sol 15°C` / `en verano con sol 25°C`; `1.25` capacidad TTCC por extremo (`[0,6]-1,2`: el valor entre corchetes es el TAP elegido); `1.26` sobrecarga TTCC por extremo; `1.2` longitud; `1.16` conductor | [kA] |
| trafo 2D | `2.1` nominal, `2.2` máx. refrigeración forzada, `2.4` ONAF II; `2.7 Tensión nominal AT/BT (f-f) del equipo`; `Tensión nominal del sistema AT` | [MVA], [kV] |
| trafo 3D | `3.1` nominal AT/MT/BT, `3.2` forzada, `3.3` siguientes etapas; `3.7 Tensión nominal AT/MT/BT` | [MVA], [kV] |

## Asociar extremo → paño → equipos

1. `extremoN_descripcion`: `Paño : PA S/E CONCEPCION B12/PA111T0058SE012T0002` (nombre/código interno),
   `Paño: S/E ANCOA J5` (sin “PA”, sin código), `Paño : PA S/E ANDALIEN/PA017…` (sin código de paño: resolver por
   `codigo`=PA017 en esa S/E), `Tap: TAP FPC`, `Punto: ESTRUCTURA D-2`.
2. Paño: por código interno PAxxx + nombre de la S/E (el más preciso); si no, por nombre normalizado (“PA S/E …”).
3. Equipos: `pano_nombre` normalizado igual al nombre del paño, o misma `id_subestacion` y el código del paño al final del
   nombre del equipo (regex `(^| )COD( \d+)?$`, “B8-2” → “B8 2”).

## Trampas

- **Regex exacta** de conceptos (con `^[\d\.]+\s+…\s*$`); “Corriente nominal” también calza con “admisible de corta duración”.
- **Paréntesis**: normalizar sin borrarlos (COCHARCAS (CGE) y COCHARCAS (FFCC) son S/E distintas).
- **`id_conexion` no sirve**: sólo en ~25 % de los equipos coincide con el id del paño; en el resto apunta a otra tabla y
  trae equipos ajenos (Ejército B1 daba 1,6/1,2 en vez de 2/2).
- **Ñ** en “Paño” puede venir en otra codificación: no anclar regex en esa palabra, buscar `S/E`.
- **TC de bushing** (“TC S/E PASO HONDO BT1 t.b.”, “…BT1N t.b.”): son del transformador y quedan asociados al paño BT;
  se excluyen (Paso Hondo BT1 daba 0,2 kA rechazado en vez de 0,4 validado).
- **Multi-razón TTCC**: la ficha del TC tiene la razón máxima; el resumen de la línea puede indicar el TAP usado. Si difieren,
  avisar (Ancoa–Pehuenche 2,4 vs 0,6 kA).
- **Bancos monofásicos**: MVA por unidad (×3).
- Valores con texto: `"50 / 1 segundo"`, `"[0,6]-1,2"`, `"17(241.5kV)"`: `num()` toma el primer número; revisar.
- Proxy a la ubicación: para tensiones, FLORIDA calzaba con la de Santiago; usar una S/E vecina inequívoca (HUALQUI).
