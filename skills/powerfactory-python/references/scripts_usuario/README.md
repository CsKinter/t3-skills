# Scripts del usuario (Vicente) para estudios de restricciones

Copias de referencia de los ComPython que el usuario usa en sus estudios. Se corren DENTRO de PowerFactory con
objetos externos (sets) en la pestaña Basic Options; para usarlos desde el puente hay que reimplementar la entrada
(sets → listas de objetos) y reutilizar la lógica.

| Archivo | Qué hace | Entradas (objetos externos / parámetros) |
|---|---|---|
| `prorrata_v6.py` | Prorrata técnica (guía CDC N°1-2024, IV.f): reparte la colocación total a prorrata de Pmax, iterando cuando una unidad toca su límite; busca el alivio mínimo que deja un elemento vigilado en (objetivo − banda, objetivo] con secante acotada midiendo `c:loading` (no lo deduce). Soporta BESS en carga (signo de pgini). | `VIGILADO` (set con 1 elemento), `carga_objetivo` (99.9), `banda_carga` (0.2), `max_iteraciones`, `paso_minimo_mw`, `reduccion_total_mw` (si no hay vigilado), `no_aumentar` (1), `RENOV_1..9` + `hacerF_i` (participa) + `porcent_i` (despacho base % de Pmax; negativo = cargando) |
| `setear_porcentajes.py` | Fija pgini de cada grupo `RENOV_i` a `porcent_i` % de su capacidad (min(P_max, Pmax_uc, Sn·cosφ)); reporta instalada vs despachada. | `RENOV_1..9`, `hacerF_i`, `porcent_i`, `activar_fuera_servicio` |
| `factores_influencia.py` | Factor de influencia por generador y por set: ΔP = `delta_p_mw` por central, mide Δloading y Δ|P| del elemento `line`; además perturba el set completo y mide el efecto conjunto (no supone linealidad). Ventana tkinter y TSV para Excel. | `line`, `delta_p_mw`, `RENOV_1..9` |
| `extraer_capacidades_termicas.py` | (copia exacta) Lee la capacidad térmica de las líneas de un set: TypLne, TypTow directo o acoplamiento ElmTow→pGeo→TypTow→pcond_c→TypCon; `sline.ChaRef`→ChaMat con `scalerow`/`scalecol` (TriDisc.cases) y `matrix` en kA. JSON+CSV; lo no resoluble va a `problems`. | `Lineas` (set) |
| `writeback_capacidades_termicas.py` | (copia exacta) Aplica un paquete `thermal-writeback/1`: copia el tipo (y TypCon/TypTow), crea ChaMat nueva con escalas propias Sol/Temperatura y valores IT, y en una variation verificada (stage + objeto de prueba) cambia sólo `ElmLne.typ_id` o `ElmTow.pGeo`. Nunca modifica tipos ni características existentes. Ver `../thermal-ratings-case.md`. | paquete JSON, fecha del stage, variation, Simular/Aplicar |
| `flujos_n_n1.py` | Flujos N y N-1 por pares (escenario, caso de estudio) elegidos en un diálogo; CSV de 27 columnas idéntico al DPL 'EFP_Caso Base'; exporta WMF de una página de diagrama por combinación. | `Cont`, `Lineas`, `Barras`, `Trafos2`, `Trafos3`, `TC`, `BOUND` (sets de referencias) |

En esta carpeta está la copia de `prorrata_v6.py` con toda la lógica reutilizable (prorrata iterativa, búsqueda por
carga del vigilado); el bloque de lectura de grupos y el reporte del original se omitieron. Los otros tres scripts
están descritos en la tabla (no copiados): pedir al usuario el original si hace falta su código exacto.

Hechos de API útiles (verificados por el usuario en PF 2025):

- Los `SetSelect` guardan referencias: el elemento real está en `item.obj_id`. El set de contingencias contiene
  objetos (una contingencia por item) y cada contingencia contiene referencias.
- Exportar un diagrama: `board = app.GetGraphicsBoard()`, `pag = board.GetContents("<nombre>.SetDeskpage")[0]`,
  `board.Show(pag)`, `board.WriteWMF(ruta_sin_extension)`. Los diagramas están en Network Model\Diagrams
  (carpetas Diagramas SIC / SING / Interconexión en el proyecto Cumbres del Ñuble).
- N-1: reactivar el escenario antes de abrir los elementos devuelve los interruptores a su posición; además guardar
  y restaurar `outserv` explícitamente (`SwitchOff()` / `SwitchOn()`).
- La temperatura ambiente se fija con triggers del caso de estudio: el mismo escenario cambia según el caso.
- La carga de trafos para el vigilado: máx(`c:loading_m`, `c:loading_h`); líneas `c:loading`.
- Constante √3: el DPL histórico usa 1,73 (se mantiene por compatibilidad de resultados).
