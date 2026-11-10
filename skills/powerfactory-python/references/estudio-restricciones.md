# Estudio de restricciones con el puente (receta verificada en Cumbres del Ñuble, 02–10-10-2026)

**Índice** (leer las reglas generales de abajo y luego sólo la sección del paso en curso; ubicarla con Grep por su encabezado):
- §0 Preparar los escenarios irrestrictos, §1 Convergencia, tensión y reactivo, §2 N-1 y contingencias, §3 Ciclo de restricción.
- §4 ComVstab: probado y descartado para el ciclo (no repetirlo).
- §5 Hechos de API verificados en el estudio: consultar antes de escribir una llamada nueva.

Flujo completo tal como se ejecutó en PF 2025 SP4 vía puente para el PE Cumbres del Ñuble (Engie), con dos puntos de
conexión (POI 1 Tiquel 220 kV, POI 2 Bulí 154 kV) y cuatro escenarios (E01–E04). Scripts de referencia, tal como
corrieron: `Cumbres del Ñuble\herramientas\estudio_cumbres\` (ver su README; no abrirlo salvo que se pida). Fuente escrita del método en el proyecto:
`Metodología restricción - Cumbres del Ñuble.md`.

**Cómo leer esta receta en otro estudio.** La mecánica de PF (API, orden de operaciones, trampas) es general. Los
criterios (umbral del 20 %, objetivo del 99 %, BESS primero, qué contingencias cuentan) y todos los nombres y cifras
son de Cumbres: se confirman con el usuario en cada estudio. El método, las decisiones que hay que cerrar y el
tratamiento de BESS e híbridos están en la skill `estudio-restricciones`. La estructura final de la BD, la validación
y el cierre están en `cierre-bd.md`, que **manda sobre §0.1** en nombres de casos y carpetas.

Reglas generales que valen en todo el estudio:
- **Activar y afirmar antes de escribir**: `cambiar_caso(r"POI 2 - Buli\03_15 SS", r"POI 2 - Buli\1_Irrestrictos\E04_…")`
  y `assert "1_Irrestrictos" in app.GetActiveScenario().GetFullName()`. Los nombres se repiten entre carpetas de POI:
  usar siempre la ruta. (Una prorrata corrió dos veces sobre una copia de trabajo por no hacerlo.)
- **Comandos idempotentes**: planes en JSON antes de escribir; restaurar siempre desde el archivo (valores absolutos),
  nunca desde lo que «había» al reintentar.
- **No usar `raise SystemExit`** en un comando (puede botar el puente): envolver en `principal()` con `return`.
- Plantillas `__X__` con rutas de PF: cuidado con `"\0"`/`\9` en strings normales; usar raw strings o `chr(92)`.
- Cambios de método: proponerlos al usuario antes de aplicarlos. El ciclo debe ser idéntico en todos los escenarios
  («repetition legitimizes»).

## 0. Preparar los escenarios irrestrictos

1. **Estructura** (Operation Scenarios `00_<Proyecto>\<POI>\`): `Irrestrictos_secure` (originales del cliente),
   `Base_secure` (bases del modelo), `1_Irrestrictos` (punto de partida del ciclo), `2_Restringidos` (resultado, 1:1 con
   tablas y figuras del informe), `99_Respaldo` (trabajo e intentos, en subcarpetas fechadas; nada se borra). Casos:
   `Study Cases\00_…\<POI>\{01_25 CS, 02_15 SS}`. Nombres de escenario tipo `E01_DIA_DA_25_BESS-C`,
   `E04_MAD_DB_15_BESS-D`. (Durante el cálculo de Cumbres los casos se llamaron `01_35 CS`, `02_25 CS`, `03_15 SS` y la
   carpeta de pruebas `9_Trabajo`: así aparecen en los ejemplos de abajo y en los scripts anteriores al 06-11-2026.)
2. **Copiar** desde `_secure` (`carpeta_escenarios`, `copiar_escenario(..., carpeta=...)`, sin sufijo) y activar la copia.
   **PF no copia el escenario activo** (`AddCopy` devuelve None): activar otro antes.
3. **Receta de despacho escrita** (BESS del norte de Charrúa 100 / −100 / 0 %, centrales como en el perfil del cliente,
   balance del slack, ajuste mínimo para converger en N). Los irrestrictos se rehacen desde los originales con la
   receta; no se parte de un punto a medio restringir.
4. **Topología de operación normal del CEN**: buscar por subestación (`ElmSubstat.GetContents("*.ElmCoup", 1)`), no por
   línea, y aplicar sólo lo que influye. `ElmCoup.aUsage`: `'cbk'` interruptor, `'dct'` desconectador. Abrir el
   interruptor del paño puede no aislar la línea (Parral A2): abrir el desconectador y confirmar P = 0. Abrir un extremo
   de un anillo puede aislar barras (cerrar el otro extremo, revisar tensiones). `on_off` queda en el escenario
   (guardar con `Save()`); verificar en todos los escenarios releyendo `on_off` (o guardar, cambiar de escenario, volver
   y releer).
5. **Mover un proyecto a otro POI**: con el escenario desactivado, copiar generador, trafos, barras y cubículos dentro de
   la variation de sesión; renombrar la variation (`POI N2 - Bulí 154kV`), fijar el `tAcTime` de su stage igual al del
   otro POI, moverla (`variation.Move(carpeta)` en el puente) en un caso sin variations activas, y copiar el despacho
   escenario por escenario (un objeto nuevo toma el valor base en todos los escenarios hasta que se escribe y guarda).
   Verificar con `GetActiveNetworkVariations()` caso por caso que no queden ambos POI activos (el proyecto inyectaría dos
   veces).

## 1. Convergencia, tensión y reactivo

Objetivo del usuario: el escenario base converge **con límites de P y Q** (`iopt_lim = 1`, `iopt_plim = 1`) y **sin
avisos**; tensiones < 500 kV en 0,95–1,05 pu en N (0,93–1,07 post-contingencia), 500 kV en 0,97–1,03 (0,95–1,05).

Orden que funcionó (E01–E04 terminaron en 1–2 lazos externos y cero avisos):
0. Diagnóstico con la Output Window (`salida`): contar «Outer Loop: Iteration», «stagnated», «Repeated reactive power
   limitation» (máquina fijada por PF) y «limit exceeded». Con `ictrlx = 30` (el comando traía 5) converge en el lazo 5–6.
1. **Ajustar sobre el flujo SIN límites** y reducir los excesos que reportan los avisos «Maximum/Minimum reactive power
   limit exceeded (Q = x > Qmax = y)» (parseados en `medq_lib.py`); recién al final correr con límites. Con límites, el
   déficit de un equipo arrastra a todos a Qmax y PF «fija» decenas de máquinas (45 en una solución espuria).
2. Mínimos técnicos y slack: térmicas bajo `Pmin_uc` a su mínimo, compensando a prorrata del margen sobre el piso
   (`max(Pmin_uc, Pmin IT)`, 30 % de Pn sin dato), sin apagar ninguna; la slack (ElmSym con `ip_ctrl == 1`) con margen
   respecto de Pmin y Pmax (E03 no convergía con la slack en Pmax).
3. Consignas `usetp` de una central al promedio de sus unidades en V constante.
4. Excesos chicos por rondas: `usetp` ±0,005 en máquinas `constv`; en SVC/CER el signo sale de m:Q (Q > 0 absorbe: subir
   `usetp` para que absorba menos); `qgini = 0,95·lím/ngnum` en `constq`; ERNC en P-cosφ un escalón hacia 1.
5. **Reactores de barra «R» y condensadores**: causa raíz en E04 (39 reactores en barras bajo 1,0 pu absorbían 3,8 GVAr).
   Un BC está realmente conectado si está en servicio, con pasos (`ncapa`), con el `StaSwitch` del cubículo cerrado y
   con los acoples del camino cerrados: verificar que inyecte (m:Q).
6. VSC/CER/STATCOM: consignas en `ElmStactrl` (`usetp`, `i_ctrl` 0 = tensión). Invertir `iQorient` no cambió nada.
7. Bolsones de 66/154 kV en sobretensión: cosφ de ERNC hacia 1 o inductivo, por sector (`ronda_bolsa.py`).
8. Subtensiones de 66 kV: taps de los trafos que alimentan la barra (`ronda_tap.py`).
9. Limpieza de avisos de datos: taps fuera de rango al neutro, huérfanos fuera de servicio (consultando al usuario).

Mecánica de cada ronda: una acción por subestación (el escalón más grande), plan en JSON, medir, revertir si `ierr ≠ 0`,
si las barras bajo 0,93 no bajan o si las sobre 1,07 suben más de 10; en Q, exigir que el exceso baje ≥ 0,5 MVAr. Medir
la caída real de tensión, no el conteo de barras (43 barras «nuevas» bajo 0,93 eran un nudo que pasó de 0,9301 a
0,9297). Detectar oscilaciones entre dos estados. Ir de a un escalón (retirar 100 MVAr de una vez creó 237
subtensiones).

Diagnóstico de una no convergencia (`diag_conv.py`): `itrlx = 100` (si converge, era numérica); `iopt_lim = 0` (si
converge, es de reactivo); proyecto en 0 MW; BESS en pasos de 10 % (distancia a la nariz).

Criterios del usuario: V constante se queda V constante (palanca `usetp`), nunca pasar a Q constante; reactores de
barra «R» sí, de línea «RL» no (cuidado con R colgados de un nudo de línea, `clas_reac.py`); taps permitidos; gradual
por sector; no apagar térmicas (inercia); PMGD como están; en la ZDI ajustes mínimos, fuera de ella y al norte de
Charrúa se puede mover reactivo; escalar reactivo antes de cortar P (BESS en P-cosφ 0,95 todos igual, luego BC de la
zona, luego Q de eólicos); cada escenario resuelve sus propios problemas.

## 2. N-1 y contingencias

1. **Contingencias en JSON**, fuera del script: `{"id", "desc", "elementos": [[clase, loc_name, filtro_ruta?]]}`; una
   contingencia puede abrir varios tramos a la vez (C02 Bulí–Monterrico R1 abre 3 ElmLne). Vigilados en otro JSON como
   pares `[clase, nombre]`. Ejemplo: `cont_def_buli.json`, `monitoreados.json`.
2. **Resolver objetos** con un índice `(clase, loc_name) → [objs]`; con nombres repetidos (p. ej. dos «ESTRUCTURA 166 –
   CHARRUA 220KV C1») filtrar por un trozo de la ruta (`"08-Charrúa.ElmNet\ESTRUCTURA 166" in x.GetFullName()`) y exigir
   `len == 1`. Armar el índice con `ElmNet.GetContents("*.ElmLne", 1)` sobre las redes de interés: ~85 llamadas a
   `GetCalcRelevantObjects` en un bucle provocaron caídas «already deleted».
3. **Abrir** con `outserv = 1` (leer antes el original), **correr** el ComLdf del caso con `iopt_lim = 1`,
   `iopt_plim = 1`, `iopt_at = 0`. `ComLdf.Execute()` devuelve 0 si converge y 1 si no.
4. **Cascada de respaldo** si no converge: arranque plano (`iopt_noinit = 0`); si sigue, plano y sin límites de Q
   (`iopt_lim = 0`), marcado «SIN LÍMITES Q». Restituir opciones en `finally`. Después de un respaldo, un flujo plano y
   luego uno normal para no arrastrar la mala solución al caso siguiente.
5. **Medir**: ElmLne/ElmScap `c:loading`; ElmTr2 máx(`c:loading`, `c:loading_h`, `c:loading_l`); ElmTr3 máx(`c:loading`,
   `_h`, `_m`, `_l`), filtrando None; omitir elementos fuera de servicio; slack `m:P:bus1` del ElmSym con `ip_ctrl == 1`;
   flujo `m:P:bus1`, tensión `m:u`. Sobrecarga = > 100 %; en el ciclo cuentan sólo las **nuevas** (> 100 % en la
   contingencia y ≤ 100 % en N).
6. **Restaurar** en `finally` desde el original leído (o desde un JSON `n1_orig_<ESC>.json`, que hace seguro un
   reintento tras «already deleted»). Guardar resultados con `guardar("n1_<ESC>_<CID>", …)` (al releer, `d.get("datos", d)`).
7. **Cerrar**: abrir/cerrar con `outserv` deja `iModified = 1` aunque se restituya; guardar «sin cambio neto» al terminar
   (y al inicio de cada script). `IntScenario.Save()` devolvió 0 al guardar con cambios.
8. **Orquestación**: un comando por escenario con N + todas las contingencias (`verif_ext_esc.py`, `n1_poi2.py`) es
   mejor que un comando por contingencia; `cambiar_caso` antes del barrido.
9. **Foto por contingencia** (`foto_ts.py`): abrir, misma cascada y, sólo si converge, `exportar_grafico`; si no, «SIN
   FOTO»; restaurar y guardar sin cambio neto. Rótulos legibles («pérdida de Ancoa–Tiuquilemu 500 kV», no sólo «C07»).

Criterios del usuario (Cumbres, POI Bulí): lista única C01–C08 presentada como «estas son»; sin Parral–Linares (opera
abierta) ni contingencias de 500 kV (casi no mueven el 154 kV; nunca concluir una restricción en 154 kV por una de
500 kV); incluir los ATR de Charrúa; no correr el N-1 completo cuando bastan los chequeos necesarios. **Regla CEN de
cerrar Parral–Linares ante las contingencias que abren Parral–Charrúa (C01/C02): pendiente de decisión** (consulta a
Fran); dejarla como opción configurable. En Parral, Parral–Linares se abre con el desconectador `A2-2`
(`aUsage = 'dct'`; el cubículo no tiene StaSwitch): P pasó de −162,8 a 0 MW.

Antes de concluir, revisar capacidades: un Excel de límites que ignoraba el equipo del segundo extremo (TTCC 0,3 kA)
subestimaba las sobrecargas del 154 kV, y una línea con capacidad fija sin temperatura (213 A en vez de 283 A a 15 °C SS)
cambiaba el N-1.

## 3. Ciclo de restricción

1. **Paso 0 (N)**: restringir sólo las sobrecargas en N de la zona en que influye el proyecto (factor de la barra del
   proyecto ≥ 20 % del mayor factor); las preexistentes lejanas se anotan y no se tocan.
2. **N-1 → peor sobrecarga nueva** (par elemento + contingencia).
3. **Factores sólo en ese par, perturbando** (no con ComVstab, ver abajo): un `ElmGenstat` ficticio PQ por barra de
   conexión (12–13 barras ≥ 60 kV), todos a la vez, cada uno con su `StaCubic` (`term.CreateObject("StaCubic")`) y
   creado en el `ElmNet` de la barra. Atributos: `sgn = 100`, `cosn = 1`, `ngnum = 1`, `av_mode = "constq"`,
   `ip_ctrl = 0`, `pgini = qgini = 0`, **`Pmin_uc = −100`**, `Pmax_uc = 100` (con `Pmin_uc` por defecto, −5 MW se recorta
   a 0 y todos los factores salen 0). Con la contingencia abierta, −5 MW por barra en caliente; factor = Δcarga/ΔP en
   % por 100 MW; las unidades heredan el factor de su barra; borrar los ficticios al terminar. Medir en una copia del
   escenario en `9_Trabajo` y en el caso donde graba la variation de la sesión. Medir donde la restricción está activa
   (no en el borde de la solución: +5 MW ahí dio factores absurdos). Factores de ~200 %/100 MW son válidos si la
   contingencia deja una parte radial.
4. **Participantes**: factor ≥ 20 % del mayor de la iteración; si hay BESS con MW, sólo BESS; si no, el resto de
   unidades de costo marginal 0 (sin PMGD). Factores reutilizados si el par se repite. El umbral se calcula **por
   signo** (`fm = max(mx, −mn)`) y el máximo se toma entre las acciones que de verdad alivian, excluyendo PMGD antes:
   con un umbral sin signo, factores de −0,5 % dejaron en cero 815 MW de BESS. En un corredor con embalse aguas arriba
   el embalse baja antes que los BESS (decisión del 02-11-2026; ver `estudio-restricciones/references/metodo-ciclo.md` §4).
5. **Prorrata técnica (guía CDC N°1-2024)**: repartir la colocación total X a prorrata de Pmax; la unidad cuya cuota
   supera su despacho base queda en la base y se reparte de nuevo. Búsqueda de X: `x1 = base − (l0 − OBJ + BANDA/2)/fg`
   (fg = mayor factor, %/MW) y luego secante hacia OBJ − BANDA/2; si el flujo falla, y = 1e9 y punto medio. OBJ = 99 %,
   BANDA 0,2–0,3, 8–10 pasos.
6. **Cierre**: carga en (OBJ − BANDA, OBJ], o BESS en 0 sin alcanzar («BESS a 0, iteración cerrada»: se pasa a la nueva
   peor sobrecarga sin recortar eólicos en esa iteración).
7. **Registro**: `iter_<ESC>_it<N>.json` con `it, elemento, contingencia, carga0, carga1, factores, participan, grupo,
   antes, despues, cierre` y `app.GetActiveScenario().Save()`. Respaldo por corrida `prorrata_<TAG>_orig.json` (guarda el
   `pgini` original sólo la primera vez: repetir parte del mismo despacho).
8. **Repetir** hasta «N-1 sin sobrecargas nuevas» (`_fin.json`), «contingencias sin solución» o «factores nulos o
   inválidos» (máximo ≤ 0,5). `run_iter.py` salta las iteraciones que ya tienen JSON.
9. **Revertir una iteración**: `revertir_it.py` escribe `pgini = mw/ngnum` desde `antes`, corre el flujo y guarda.
10. **Contingencia sin solución** (no converge ni con límites relajados): sin factores; grupo por topología (lo que queda
    detrás del elemento), BESS primero, y bisección de la mínima reducción con la que converge con límites
    (`c02_poi2.py`).
11. **Contingencias de 500 kV**: no restringir 154 kV por una contingencia de 500 kV («el sistema no se opera así»); el
    sur se trata como un todo (ficticios en Charrúa 500, Entre Ríos 500 y Charrúa 220; prorrata del conjunto al sur de
    Charrúa, BESS primero). Después del 02-11-2026 los grupos pasaron a definirse por salto de factor y el embalse a
    bajar antes que los BESS; no se verificó si las tres puertas siguieron en uso.
12. **Medir los factores en el estado de cierre**: cerca del límite de convergencia se inflan (9,8 donde el sano era
    5,0), y corregir el reactivo del irrestricto los cambia (un factor pasó de 26 % a 9 %). Remedir tras cada corrección.
13. **Verificación independiente del cierre**: rehacer el despacho desde los cambios registrados y comprobar que
    reproduce el resultado. Un cierre que no lo pasa es inválido aunque haya circulado.

Informe: % restringido por unidad y total (sobre Pmax) en tablas, MW en la prosa; nunca «no converge»; «iteración» no va
como título. Está autorizado guardar cada copia restringida una vez verificado el N-1 completo.

## 4. ComVstab (sensibilidades) — probado y descartado para el ciclo

- `caso.CreateObject("ComVstab", …)`; `dir()` no muestra atributos a través del puente, se encontraron con
  `HasAttribute`: `iopt_mod`, `iopt_method`, `p_bus`, `p_tr`, `p_hvdc`, `calcLodf`, `calcPtdf`, `calcHvdc`, `calcModal`.
- Sensibilidad por barra: `p_bus` = ElmTerm o SetSelect y **`calcPtdf = 1`** (sin eso `ierr 1` y todo en 0). Resultados
  en la rama: `c:dLoadingdP` (%/MW), `m:dPdP:bus1/bus2`, `m:dQdP:bus1` (`c:dPdP` devuelve None). Reutiliza el flujo
  previo. Validado contra AC (29,9 vs 30,7 %/100 MW).
- Lento por barra (10 s una barra; ~200 s por barra en bucle; set con `iopt_mod 1` 7 s pero muestra una sola barra) y
  leer el ElmRes falló («method call failed»). Por eso los factores se miden con ficticios. Significado exacto de
  `iopt_mod` 0/1: supuesto.

## 5. Hechos de API verificados (estudio)

| Objeto | Hecho |
|---|---|
| ComLdf | `iopt_lim`, `iopt_plim`, `iopt_at`, `iopt_asht`, `ictrlx` (lazos externos), `itrlx` (Newton), `iopt_noinit` (1 caliente, 0 plano), `errlf`, `erreq`; `iopt_init` no existe. `iopt_at = 1` con límites no convergió (40 máquinas fijadas). `i_power = 0` (ecuaciones de corriente) saca de una segunda solución espuria de tensión baja; restituir a 1 al cambiar de escenario. `iopt_pq = 1` se descartó porque cambia la física. |
| ElmGenstat | `pgini`/`qgini` y límites de Q **por unidad** (total = × `ngnum`); BESS cargando = `pgini` < 0; `av_mode` ∈ constv/constq/constc (P-cosφ), `mode_inp`, `cosgini`, `pf_recap`, `usetp`, `cQ_max/cQ_min`, `P_max`, `Pmin_uc/Pmax_uc`, `sgn`, `cosn`. Capacidad usada `min(P_max·n, sgn·cosn·n)`. **Con `cosgini = 1` PF ignora `pf_recap`: escribir primero `cosgini`.** BESS cargando: `pf_recap = 1` inyecta Q; descargando, `pf_recap = 0` es capacitivo. Un generador justo en su Sn con cosn = 1 estanca el Newton en contingencias: llevarlo al 99,5 %. |
| ElmSym | `ip_ctrl == 1` = slack; `Pmin_uc/Pmax_uc`; `cQ_max` depende de P (curva PQ). |
| ElmTr2 / TypTr2 | `nntap` en el elemento; `ntpmn`, `ntpmx`, `nntap0`, `tap_side`, `dutap` en el tipo. Tap 0 con rango 1–5: PF usa 1 (aviso). ElmTr3 `n3tap_h/m/l`: supuesto. |
| ElmShnt | `ncapa`, `ncapx`, `qcapn`, `qrean`, `shtype`; interruptor en `bus1.GetContents("*.StaSwitch")` (`on_off`). |
| ElmStactrl | `i_ctrl`, `usetp`, `qsetp`, `p_cub`, `i_droop`, `iQorient`. |
| ElmTerm | `Vtarget` en **kV**; escribirlo no cambió el flujo y es lento (1.569 barras en 4 min). `vmax/vmin` (pu) van a la variation (rechazados en barras de otras variations). |
| ElmCoup | `on_off` (en el escenario), `aUsage` cbk/dct. |
| Recorrido | `elem.GetConnectionCount()` + `elem.GetNode(i)` → terminales; `term.GetConnectedElements()`; POI de una unidad: BFS desde `gen.bus1.cterm` por trafos y acoples hasta la primera barra ≥ 60 kV. |
| IntScenario | `Save()`, `iModified`, `Activate()/Deactivate()` → 0; `loc_name` renombra; `Delete()` de carpetas → 0 (recuperación desde papelera: no confirmada). |
| Variation / stage | En la API de PF `carpeta_destino.Move(obj)` (al revés devuelve 1; dentro del puente se escribe `obj.Move(carpeta)` y él lo traduce); con la variation activa también devuelve 1: mover en un caso sin variations activas. `IntCase.iStudyTime` e `IntSstage.tAcTime` en epoch (`datetime.utcfromtimestamp`). |
| Triggers | `caso.GetContents("*.SetTrigger", 1)` lista los triggers; su valor no se pudo leer (atributos probados → None). Si falta el trigger de una escala, PF avisa «Current trigger for scale … is not defined … characteristics are ignored». |
| Output Window | Mensajes reales: «Maximum reactive power reached (Q = Qmax = …)», «Repeated reactive power limitation detected…», «Voltage setpoint cannot be kept…», «Newton algorithm stagnated», «Minimum active power limit exceeded». Nunca limpiar la ventana (`ldf_msg.py` usa `ow.Clear()`: no reutilizar). |
| Dónde se guarda | Escenario: `outserv`, `nntap`, `ncapa`, `on_off`, `pgini`, `qgini`, `cosgini`, `pf_recap`, `usetp`, `av_mode`, `cQ_max/cQ_min`, `iQorient`, `Vtarget/dvmax/dvmin` (lista `OPERATIVOS` del puente). Variation: el resto de datos de red. |

