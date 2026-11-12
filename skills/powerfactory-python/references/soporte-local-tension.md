# Soporte local de tensión por zona, barra por barra (verificado en Sidon, 11-11-2026)

Para un escenario de restricciones que converge pero deja muchas barras de la zona fuera de banda, o que cae en una
solución espuria según el arranque. Pedido de Vicente: «soporte local de tensión es lo clave, pasar renovables a control
V, revisar taps, revisar BBCC y reactores, etc, de forma local, barra por barra». Script:
`scripts/ejemplos/soporte_local_tension.py` (plantilla con marcadores, puente full). Complementa
`estudio-restricciones.md` §1, que es la receta de convergencia global de Cumbres.

## Resultado de referencia

Los dos escenarios terminaron sin cambiar P y con la misma solución desde perfil plano con el ComLdf original.

| Escenario | F (Σ desviación fuera de banda, pu) | Barras fuera de banda | Tiempo |
|---|---|---|---|
| E01 (día, BESS en carga) | 31,8 → 0,39 | 780 → 120 | 50 min |
| E02 (BESS de la zona en 0) | 3,90 → 0,77 (la F inicial incluía terminales de SVC) | 101 → 77 | 17 + 40 + 25 min |

Lo que quedó fuera de banda fue un radial de 66 kV con los recursos cercanos agotados, cerca de 0,89–0,93 pu. También
quedaron barras de centrales hidráulicas en 1,051 pu, reguladas por sus propias máquinas. El procedimiento no inventa
recursos: lo que queda fuera es dato, carga o falta de compensación real, y se informa como tal.

## Pasos

0. **Partida buena.** Correr primero con `i_power = 0` desde plano y luego con el ComLdf original en continuación. Si no
   converge, descartar los cambios y detenerse. Medir la slack y una barra de control conocida de la solución buena
   (`MONITOR`). La solución espuria tiene la misma topología, otra Q y otra slack.
1. **A: ERNC de la zona a control de tensión.** Pasan a `av_mode = "constv"` con `usetp = 1,0` en su propio terminal. El
   proyecto, los BESS, los STATCOM y los VSC quedan excluidos, igual que las unidades con P ≈ 0 (PV de noche). Se guarda
   `A_prev` con el modo, la consigna y el `qgini` previos. Si |Q| por unidad supera 0,33·Pn (fp 0,95,
   **propuesta**), la unidad queda en Q constante al tope. Se repite hasta cuatro veces.
   - Esto choca con el criterio de Cumbres («V constante se queda V constante, nunca pasar a Q constante»). Confirmar
     con el usuario cuál vale en cada estudio.
2. **B: barra por barra.** Agrupar los terminales de la zona por `red|S/E` (`cpSubstat`) y atender el peor grupo
   primero. Cada grupo usa sus propios recursos:
   - taps manuales de los Tr2 y Tr3 de la S/E (`nntap`, `n3tap_h/m/l` dentro de `ntpmn..ntpmx` y `n3tmn_*..n3tmx_*`);
   - condensadores (`shtype = 2`) y reactores de barra (`shtype = 1`), con `ncapa` dentro de `0..ncapx` y
     `outserv = 1` para 0 pasos. Los reactores de línea «RL» no se tocan.

   Cada paso se acepta sólo si converge, baja F total de la zona en más de 1e-3 y no sube la máxima tensión de 200 kV
   o más de las redes troncales sobre `max(inicial, 1,055) + 0,002`. Si no se acepta, se revierte y se reconverge. Se
   hacen hasta tres rondas, y termina cuando una ronda no mejora nada.
3. **B2 (`"V"`): S/E vecinas.** Para cada grupo que sigue fuera de banda se recorre por BFS hasta 6 saltos dentro de la
   misma red, con aristas `ElmLne`, `ElmTr2`, `ElmTr3`, `ElmZpu` y `ElmCoup` en servicio. Se prueba de la más cercana a
   la más lejana:
   - sus taps y bancos;
   - el `usetp` de las ERNC en `constv` conectadas allí, en pasos de ±0,01 dentro de 0,95–1,05.

   Además de la regla de B, un paso no puede aumentar el número de unidades `constv` sobre el tope de Q.
4. **C: validación.** Correr el ComLdf original desde plano y compararlo con la continuación. Se guarda
   (`IntScenario.Save()`) sólo si la slack difiere menos de 1,5 MW y la barra de control está sobre 0,93 pu; si no,
   `DiscardChanges()`. Después se restituyen las opciones del ComLdf. Control final: activar otro escenario y comprobar
   que los `av_mode` cambiados no se filtraron. Son atributos de operación y deben quedar sólo en el escenario tratado.

Antes de escribir: `CreateVersion` con un nombre único (ver trampas) y `AddCopy` de la carpeta de escenarios a
`99_Respaldo`. El JSON de salida registra cada paso como `[grupo, equipo, atributo, antes, después, ΔF]`. Así se puede
reconstruir o revertir con `__RESET__`, que es una lista `[tipo, loc_name, atributo, valor]` y exige que el nombre sea
único en la zona.

## Transformadores en paralelo

Se mueven juntos, con el mismo delta, y conservan su diferencia original. La clave de grupo es
`(atributo de tap, ntpmn, ntpmx, sorted("S/E@kV" de cada terminal))`.
- Agrupar por `GetFullName()` de los terminales **no encuentra paralelos**, porque cada unidad llega a su propio
  terminal o cubículo. La v2 dejó así unidades con taps distintos y hubo que reponerlas con `__RESET__`.
- Las unidades con rangos de tap distintos quedan independientes aunque compartan S/E. Pasa en San Fernando, Teno, Los
  Ángeles y Portezuelo (75 y 50 MVA en distinta S/E de 66 kV).

## Qué revisar con el usuario antes de aceptar

El orden de los recursos es por cercanía, no por pertinencia. El procedimiento mueve lo que mejora F, incluido:
- **ATR troncales** 500/220 o 220/154 kV (Polpaico, Alto Jahuel, Ancoa, Entre Ríos, Lagunillas). El mayor alivio de un
  radial de 66 kV vino de un ATR 230/161/69 a varios saltos;
- **transformadores internos de parques** (MT/BT, AT/MT), que no son recursos del sistema;
- trafos de centrales (Rapel, Los Cóndores) y reguladores 220/220 o 66/66.

Mostrar la lista de cambios por equipo y preguntar si se excluyen ATR troncales o trafos internos. La exclusión se
implementa como un filtro en la construcción de `RES`. Una tensión de origen absurda (1,36 pu en 66 kV) se reporta como
posible error de dato, no se «arregla» con taps.

## Trampas

| Trampa | Qué pasa | Qué hacer |
|---|---|---|
| Terminales internos de SVC/STATCOM (46 kV a 1,2–1,75 pu) | Dominan F y B2 mueve trafos lejanos para nada | Excluir `SVC` y `STATCOM` del conjunto objetivo |
| Barra de control con un segundo terminal desenergizado (u = 0) | `all(u > 0,93)` falla y se descarta una solución buena | Filtrar u > 0,3 y exigir lista no vacía |
| `CreateVersion` con nombre repetido en una segunda pasada | Conflicto de versiones | Nombre con escenario, pasos y `%Y%m%d_%H%M` |
| Cambiar la estructura de una clave de dict | `ValueError: too many values to unpack` antes de escribir | Desempaquetar la clave nueva en todos los bucles |
| Excepción a mitad de corrida | El escenario activo queda modificado y el siguiente `Activate` puede guardarlo | Envolver: `exec(SRC, globals())`, y en `except`, `DiscardChanges()` si `iModified` |
| `i_power = 0` desde plano se estanca en un escenario (E06 madrugada) y el original (`i_power = 1`) sí converge | No hay una partida que sirva para todos: E02 necesita `i_power = 0` para no caer en la solución espuria y E06 converge sólo con el original | Partida con respaldos en orden: `i_power = 0` plano + continuación, original plano y original en caliente. Se registra en `R["partida"]`; la validación C sigue exigiendo el original desde plano. Si todas fallan, revisar primero que el ComLdf sea el original (trampa siguiente) |
| Excepción antes de restaurar el ComLdf (E06, 12-11-2026) | El ComLdf es del caso de estudio y no se descarta con el escenario: quedó `i_power = 0` y `iopt_noinit = 1`. El reintento tomó eso como «original», nunca probó el original real y la siguiente corrida habría validado con otro ComLdf | Restaurar las opciones en `finally` de la envoltura y antes de cada `raise`. Antes de cada corrida, comparar el ComLdf con el último registrado (`R["ldf"]`) |
| Costo | Un flujo por paso probado: E01 completo agotó 3000 s | Presupuesto `PRESUP` y pasos con `__PASOS__` para repetir sólo B2 |
| Lote largo desde el agente | La tarea en segundo plano de la shell muere a las 2 h y deja el envío a medias | Lotes de ≤ 2 escenarios por tarea. Para diferir, mover los runners a una subcarpeta en vez de matar la tarea |
| Q1/Q3 de un escenario PV | Es el cuantil de P (P = q·sgn·cosn), no un Q | El paso A no lo altera; no excluir PV por eso |

## Plantilla de envoltura

```python
SRC = r"""...plantilla instanciada..."""   # o repr() del texto
_L = app.GetFromStudyCase("ComLdf")
_K = {a: _L.GetAttribute(a) for a in ("i_power", "iopt_noinit", "iopt_lim", "iopt_plim", "ictrlx", "iopt_at", "iopt_asht")}
try:
    exec(SRC, globals())
except Exception:
    _a = app.GetActiveScenario()
    if _a is not None and _a.GetAttribute("iModified"): _a.DiscardChanges()
    raise
finally:
    for _k, _v in _K.items(): _L.SetAttribute(_k, _v)   # el ComLdf es del caso, no del escenario
```
