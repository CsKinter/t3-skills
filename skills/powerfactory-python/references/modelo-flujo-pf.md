# Modelo de flujo de PF para replicarlo fuera de PowerFactory

**Índice** (leer sólo la sección que haga falta; ubicarla con Grep por su encabezado):
- §1 Estrategia, §2 Topología, §3 Convenciones de resultados (signos): leer siempre §1 y §3.
- §4 Líneas (incluye acopladas ElmTow), §5 Trafo de 2 devanados, §6 Trafo de 3 devanados: sólo el equipo que se modela.
- §7 Generadores y controles (ElmGenstat, ElmStactrl, ElmSvs), §8 Otros elementos.
- §9 pypowsybl (motor externo), §10 Validación por capas y ciclo empaquetado `ciclo_lineal.py`: antes de validar contra PF.
- §11 Pendiente de confirmar con el usuario (hover en PF).

Qué leer de PF y cómo modelar cada equipo para que una red armada fuera (pypowsybl/numpy) reproduzca el flujo AC de
PF. Fuentes: TechRef de PF 2025 SP4 (`C:\Program Files\DIgSILENT\PowerFactory 2025 SP4\Help\TechRef\`) y el piloto
del 23-10-2026 (`Cumbres del Ñuble\.revision_diagrama\factores_lineales_2310\`, ver su LEEME), validado contra PF en el
SEN completo (E04 Bulí: 21.886 terminales, N y 14 contingencias a ≤ 0,035 puntos de carga).

Etiquetas: **[verificado]** = comprobado contra resultados de PF; **[TechRef]** = documentado, no probado;
**[por confirmar]** = preguntar al usuario (puede leer el nombre del atributo con hover en el diálogo de PF).

## 1. Estrategia que funcionó

1. En PF: activar caso y escenario, correr el ComLdf **del estudio** tal cual (sin cambiar opciones). Ojo: el caso
   puede tener varios ComLdf y `app.GetFromStudyCase("ComLdf")` devuelve el por defecto; en Cumbres el del estudio es
   la copia «Load Flow Calculation_revisar» (`case.GetContents("Load Flow Calculation_revisar.ComLdf")`). Con el
   por defecto, E03 no convergía (ni en corriente ni con arranque plano); con el del estudio sí.
2. Leer por el puente, en un solo comando (cada comando tiene costo fijo), datos **y resultados**: terminales con V∠θ,
   acoples y StaSwitch, ramas con P/Q/I por borne, inyecciones con P/Q (`pf_extraer.py` del piloto).
3. Fuera de PF, validar por capas antes de calcular nada (§10). Cada capa apunta al elemento o barra que falla.
4. Inyecciones y consignas desde la solución de PF: cargas P, Q; shunts como admitancia `y = conj(S)/|V|²`; generadores
   PV con consigna = tensión resuelta por PF en la barra controlada. Así la red reproduce el estado de PF por
   construcción y sólo hay que acertar las **ramas** (que sí se pueden validar una por una).

Alcance: la red reproduce el punto de PF y su vecindad (contingencias, factores, perturbaciones chicas). Alejarse mucho
del despacho (cientos de MW) requiere modelar los controles de Q (§7) o volver a PF.

## 2. Topología [verificado]

- Barras eléctricas = componentes de `ElmTerm` unidos por `ElmCoup` con `on_off == 1`, `outserv == 0` y los
  `StaSwitch` de sus cubículos cerrados (union-find). Sólo terminales con `ciEnergized == 1`.
- Borne de un elemento: `elem.bus1` (o `bushv/busmv/buslv`) → `StaCubic` → `cterm`. Un `StaSwitch` abierto dentro
  del cubículo desconecta ese borne (mapa cubículo → `on_off` leyendo todos los `StaSwitch` y su `GetParent()`).
- Chequeo: todos los terminales de una barra deben tener la misma `m:u`/`m:phiu` en PF (E04: 0 diferencias).
- Ramas de impedancia prácticamente nula (|z| < 1e-5 pu en 100 MVA; p. ej. «Digueñes – Reactor Digueñes 500 kV»,
  `R1 = X1 = 0`) se tratan como puentes que unen barras; si no, aíslan reactores o vuelven singular un grupo acoplado.
- `GetCalcRelevantObjects()` sin filtro de clase tarda ~3 min (158 mil objetos): siempre filtrar por clase.

## 3. Convenciones de resultados [verificado]

| Elemento | `m:P:busX`, `m:Q:busX` |
|---|---|
| Ramas (ElmLne, ElmTr2/3, ElmScap, ElmSind, ElmZpu) | Potencia que entra a la rama desde ese borne |
| ElmLod, ElmShnt, ElmAsm | Convención carga (+ consume) |
| ElmSym, ElmGenstat | Convención generador (+ inyecta) |
| **ElmSvs** | **Convención carga**: Q > 0 absorbe. Sus límites también: `qmax` = Q del reactor (> 0), `qmin` = Q por condensador (< 0) [TechRef] |

Con eso, Σ por barra de todos los resultados = 0 (E04: 0 barras con residuo > 0,5 MVA): si no cierra, falta un elemento.

## 4. Líneas (ElmLne)

- `R1`, `X1` [Ω] y `B1` [µS], `G1`: totales del elemento, listos para el modelo π [verificado: 2.232 líneas no acopladas
  a ≤ 0,12 MVA]. PF puede usar modelo distribuido (TypLne/TypTow/ElmTow) [TechRef]; en el SEN el π con estos valores
  calzó, así que no hizo falta corrección hiperbólica.
- R depende de la temperatura del ComLdf (R1' = r·(1 + α(T − 20)) con tipo TypLne) [TechRef]; leer `R1` después de
  correr el flujo en el caso correcto.
- Carga: `max(|I_i|/Inom_i, |I_j|/Inom_j)·100`, Inom = Ir·`fline` o rating térmico (IntThrating), tope `Imaxlim·nlnum`
  [TechRef]. Fuera de PF conviene fijar un factor por elemento = `c:loading` / max(I/Ir) en el estado N [verificado].
- Abierta en un extremo: su carga capacitiva va como shunt en el extremo conectado:
  `ysh/2 + (ys·ysh/2)/(ys + ysh/2)`.

### Líneas acopladas (ElmTow) [verificado, con identificación]

- `ElmLne.c_ptow` → `ElmTow` (`plines` = circuitos, `pGeo` = TypTow/TypGeo, viene como **lista**). En el SEN hay 390
  grupos (386 de dos circuitos). PF usa la impedancia mutua de secuencia positiva entre circuitos: en Polpaico–Lo
  Aguirre 500 kV la X efectiva es 8,36 Ω contra `X1` = 7,79 Ω (+7 %); en otros pares −5 %.
- La matriz **está en el tipo de torre** (TypTow/TypGeo, página Load Flow, botón Calculate) [hover del usuario]:
  «Matrix of 1-Sequence-Resistances R_ij_1 [Ohm/km]», X_ij_1 [Ohm/km], G_ij_1 y B_ij_1 [µS/km], y las de secuencia
  cero (`R_c0`, `X_c0`, `G_c0`, `B_c0`, confirmados; los de secuencia positiva se leen con la extracción
  `pf_extraer2.py`). Por km: se multiplican por el largo de los circuitos. Comprobado en Polpaico–Lo Aguirre 500 kV:
  X propia 0,2650637 y mutua 0,01930809 Ω/km × 29,4 km → X efectiva 7,79 + 0,57 = 8,36 Ω, igual a la identificada
  desde la solución de PF. B mutua −0,2126 µS/km (acoplamiento capacitivo).
- El ElmTow no expone la matriz ni `GetAttributes()` lista atributos; los circuitos están en `plines` (orden = filas
  de la matriz) y el tipo en `pGeo` (lista).
- **Configuración por circuito del ElmTow** [hover + verificado 23-10, E04] (tabla «Circuits» del diálogo), vectores
  en el orden de `plines`: `dphasing` (Phasing; códigos 0 abc, 1 acb, 2 bac, **3 cab, 4 bca**, 5 cba como
  permutación de las filas de la matriz [27-10: con 3 y 4 al revés, 20 grupos de E04 no calzaban; corregidos, los
  pares [3,1], [4,2], [1,3], [2,4] quedan abc–cba como los [0,5]]), `dpolar` (Polarity: 0 «Terminal i», 1 «Terminal j» = circuito definido desde el otro
  extremo), `transp` (Transposition; ninguno en el SEN) e `i_model` (Line Model, 0 = π concentrado).
- `X_c1` del tipo vale tal cual sólo con todos los circuitos abc y la misma polaridad (272 de 389 grupos). Si no, se
  calcula desde la **matriz natural 3n×3n** del tipo (`R_c`, `X_c`, `B_c`, Ω/km y µS/km, ya reducida de cables de
  guardia): mutua sec+ = `(Aᴴ·P_i·M_ij·P_jᵀ·A)[1,1]` con `P` = permutación de fases, **simetrizada** `(Z + Zᵀ)/2`
  (así coincide con `X_c1` del tipo a 1e-16; sin simetrizar, la red de ramas deja de ser recíproca y un tramo de
  0,14 km en Pueblo Seco dio el doble de flujo). Un circuito con `dpolar` distinto al primero se arma con sus extremos
  intercambiados. Ej. Cumbres–Nueva Cardones 500 kV (abc–cba): 87 MVA de error con `X_c1`, 0,27 MVA así.
- Contraste: la orientación elegida comparando contra PF coincidió con `dpolar` en 336 de 338 grupos. Con la
  configuración leída (`acoples.desde_leido`) quedan 309 grupos; el resto cae a variantes elegidas o a identificación
  (52 grupos, sobre todo tipos sin matriz). Peor circuito acoplado: 1,0 MVA. N-1 del E04: ≤ 0,04 puntos de carga.
- Respaldo si el tipo no tiene la matriz: identificación desde la solución de PF (propia = `R1 + jX1`; mutuas por
  mínimos cuadrados sobre `ΔV_i = Σ_j Z_ij·Is_j`; residuo capacitivo como shunt en cada extremo). Exacto para pares
  paralelos; aproximado si sólo comparten parte del trazado.
- Red: matriz nodal exacta `A·Z⁻¹·Aᵀ` realizada con una rama por par de nodos + shunts. Contingencia de un circuito:
  los demás quedan con su submatriz de Z.

## 5. Trafo de 2 devanados (ElmTr2/TypTr2)

Modelo [TechRef, verificado en 992 Tr2]: T con fugas repartidas `itrdl`/`itrdr` (0,5 por defecto) y magnetización al
centro; `zsc = uktr/100`, `rsc = pcutr/1000/strn`, `xsc = √(zsc² − rsc²)`; `zM = 1/(curmg/100)`, `rFe = strn/(pfe/1000)`
(si curmg es menor que lo que exige pfe, PF usa la de pfe y lo avisa); `ntnum` unidades en paralelo.

Tap [verificado]: tensión interna `e = V / (U_rated · t)` en el lado del tap (`tap_side` 0 = HV, 1 = LV), con
`t = 1 + (nntap − nntap0)·dutap/100·e^{j·phitr}`. `phitr` = «Phase of du»: 0° cambia la razón, 180° la cambia al revés,
90° = booster en cuadratura (Tocopilla-Booster `phitr = −90`). Posición fuera del rango del tipo → PF la lleva al
límite (`ntpmn`/`ntpmx`) y avisa. (La TechRef escribe `nntapint = nntap0 − nntap` con `u' = u·t`; los datos calzan
exacto con la forma de arriba.)

Grupo de conexión [verificado]: desfase `nt2ag·30°` en el lado LV, `e_LV = V_LV·e^{+j·30·nt2ag} / U_LV` (el signo −
da errores de cientos de MW).

Atributos del tipo [TechRef] que el piloto aún no usa:
- `itapch`/`itapch2` (cambiador 1/2 habilitado), `tapchtype`/`tapchtype2` (Ratio/Asym, Ideal, Symmetrical),
  `dphitap`/`dphitap2` (ángulo por paso del desfasador ideal: `t = e^{j·n·dphitap}`), `tap_side2`, `dutap2`, `phitr2`,
  `nntap02`. Simétrico: `du1 = j·dutap/2`, `du2 = −j·dutap/2` en ambos lados.
- `itapzdep` (impedancia dependiente del tap) con `uktmn`/`uktmx`, `pcutmn`/`pcutmx` [verificado 26-10]: uk y Pcu
  por **parábola** que pasa por (ntpmn, uktmn), (nntap0, uktr), (ntpmx, uktmx). En 21–29 Tr2 con tap fuera de neutro
  el error de flujo baja de 0,39 a 0,06 MVA (mediana) y de 14 a 0,5 MVA (máximo); una recta por tramos deja 8 MVA.
  74 Tr2 en servicio lo tienen (ViQSilent `modelo_pf._uk_tap`). En el **TypTr3** [puente 26-10]: `itapzdep`,
  `uktr3mn_h/m/l`, `uktr3mx_h/m/l` [%] y `pcut3mn_*`, `pcut3mx_*` [kW] por par, con la misma parábola sobre el tap
  del devanado regulado (el de `du3tp` ≠ 0): Charrúa N8 en E03 (tap 15) pasa de 33 a 1,9 MVA, Cumbre N2 de 18 a 0,5
  (`modelo_pf._uk3_tap`). Con esto las calibraciones de taps se transfieren entre escenarios.
- Elemento: `iTaps` («According to Measurement Report»: tabla por paso en el elemento que reemplaza al tipo),
  `nntap2`, `ntrcn` (tap automático), `ratfac`, `Inom_h`/`Inom_l`. `itrmt` es el **tipo de reactancia de
  magnetización**, no el modelo de cambiador.

## 6. Trafo de 3 devanados (ElmTr3/TypTr3)

- Pares [TechRef, verificado]: `uktr3_h` = HV-MV, `uktr3_m` = MV-LV, `uktr3_l` = LV-HV, cada uno referido a la
  **menor potencia del par**; `pcut3_*` igual. Estrella: `z_H = (z_HM + z_LH − z_ML)/2`, etc. `curm3` referido a la
  potencia HV. `nt3nm` en paralelo. Desfases `nt3ag_h/m/l·30°`.
- Taps por devanado: `n3tap_h/m/l` (elemento), `du3tp_*`, `ph3tr_*`, `n3tp0_*`, `n3tmn_*`/`n3tmx_*` (tipo), misma
  fórmula compleja del Tr2. Hay **dos controladores de tap**, cada uno asignable a HV, MV o LV [TechRef].
- **Ubicación del tap** [TechRef + verificado]: por defecto en el **punto estrella** (Fig. 1.1; campo «Tap Modelled
  at» del tipo, página Load Flow), opcionalmente en los bornes (Fig. 1.2). Con el ideal modelado en el borne, el tap
  en la estrella equivale a admitancia de la pata `y·|t|²` (la impedancia en Ω vista desde el borne no cambia con el
  tap). Atributo [hover]: **`TypTr3.itapos`** (0 Star Point, 1 Terminals); en el SEN 235 tipos estrella, 42 bornes.
  Coincidió con la convención elegida contra PF en 286 de 293 Tr3 (las 7 diferencias eran Tr3 con reporte de
  mediciones, ver abajo).
- Rango de tap del tipo: `n3tmn_h/m/l`, `n3tmx_h/m/l` (leerlos: sin ellos la fila del reporte queda corrida).
- Magnetización [hover]: `i3loc` (0 estrella, 1 HV, 2 MV, 3 LV); secuencia cero `i30lc` (mismos códigos).
  «Tap dependent rating – Configuration» = `iTaploading` [TechRef].
- Terciario abierto (ATR 500/220 de Digueñes y Nueva Pichirropulli): dos patas a la estrella; no descartar el elemento.
- **Reporte de mediciones** [hover]: elemento, Load Flow → Advanced: «According to Measurement Report» = `iTaps`
  (1 = ignora los taps del tipo), «for Tap at» = `iMeasTap` (0 HV, 1 MV, 2 LV) y la tabla `mTaps` (una fila por paso: tensión [kV], ángulo [°], uk(HV-MV), uk(MV-LV), uk(LV-HV) [%],
  Pcu(HV-MV), Pcu(MV-LV), Pcu(LV-HV) [kW]). «Measured at» = `iMeasLoc`. Modelo [verificado en los 5 Tr3 del SEN con
  reporte]: fila = tap − `n3tmn` del devanado `iMeasTap`; `t = (U_fila/U_rated)·e^{+j·ángulo}`; los uk y Pcu no
  nulos de la fila reemplazan a los del tipo (`modelo_pf._datos3`). Así están definidos los desfasadores «TRDESF
  CNAVIA 230/230/69» (tipo con `du = 0`; paso 21: 230 kV, +4,7°, uk 7,48 %; calzan a 0,16 MVA) y los trafos de PE
  Atacama y Cabo Leones I/III (tensión por paso, sin ángulo; calzan exacto).
- Calibrados en el E04 que siguen sin explicación: Chillán (sin reporte de mediciones ni impedancia dependiente del
  tap; taps HV 9/neutro 0 y MV 10/neutro 8), Coronel N4/N6, Itahue, Cipreses, Condores.
- Carga [TechRef]: `Inom_X = ratfac_X · Ir_X,tap · nt3nm`, con `iTaploading` (constante, FCBN, RCBN) que puede hacer
  depender Ir del tap.

## 7. Generadores y controles

### Generador estático (ElmGenstat) [TechRef]

- Controlador local `av_mode` [hover]: `constv` Const. V (PV), `constq` Const. Q (PQ), `constc` Const. cosphi,
  `vdroop` Voltage Q-droop, `idroop` Voltage Iq-droop, `qvchar` Q(V), `qpchar` Q(P), `cpchar` cosphi(P).
- Con controlador de estación externo (`c_pstac`), PF lo indica en rojo: «The external station controller settings
  have precedence over those of the local controller» [captura del usuario]: el `av_mode` local no aplica.
- Modo de ingreso del despacho `mode_inp` (sólo cómo se ingresa P/Q): `DEF`, `PQ` (P, Q), `PC` (P, cosφ), `SC`
  (S, cosφ), `QC` (Q, cosφ), `SP` (S, P), `SQ` (S, Q) [captura del usuario].
- Implicancia: con `constq` + `PC`, Q = P·tan φ del despacho; al mover P **cambia Q**. Con `constv`, el Q lo fija el
  control de tensión y el cosφ ingresado no influye (Cumbres: Const. V, ingreso P-cosφ, Q resultante 10,3 MVAr).
  Const. cosφ mantiene el cosφ incluso si P cambia durante la solución (slack, secundario, balance distribuido).
- Límites de Q `cQ_min`/`cQ_max` por unidad (× `ngnum`); Q(P)/Q(V) por unidad y × `ngnum`.
- Slack: «Reference machine» (`ip_ctrl`); un genstat «grid-forming» es candidato a slack aunque no esté marcado.

### Controlador de estación (ElmStactrl) [TechRef]

- Atributos [hover]: `i_ctrl` (0 tensión, 1 Q, 2 factor de potencia, 3 tanφ); `rembar` barra controlada; `usetp`
  consigna [pu]; `uset_mode` (0 la del controlador, 1 la «bus target voltage» del terminal); `i_droop` droop activo;
  `Srated` Q nominal [Mvar]; droop en % (TechRef: `ddroop`); `iopt_drp` (0 %, 1 Mvar/pu, 2 ΔV); `pQmeas` cubículo de
  medición de Q; `psym` máquinas. Con droop, la tensión controlada es `usetp + Qmeas/Qdroop`, no fija.
- Reparto de Q (pestaña Distribution) [hover]: `imode` (0 P despachada, 1 potencia nominal, 2 individual, 3 máxima
  reserva, 4 adaptación de consignas) y `consQdisp` («Consider reactive power dispatch»: Q_i = Q_disp,i + ΔQ_i).
  `ΔQ_i = Kq_i · ΔQ_total` [TechRef].
- Fuera de PF (pypowsybl no reparte así): un solo regulador por barra controlada con consigna = tensión de PF y los
  demás PQ con su Q de PF. Reproduce el estado exacto; el reparto del ΔQ en perturbaciones queda simplificado.
- Consigna desde datos [verificado 26-10, 16 extracciones]: con controlador **en servicio** en V sin droop, la máquina
  regula `rembar` a la `usetp` **del controlador** (7 de 7); sin controlador, una máquina «Const. V» regula **su propio
  borne** a su `usetp` (1317 de 1317 máquina-escenario; los otros 38 están en su límite de Q). Con controlador
  **fuera de servicio** PF usa el modo propio de la máquina (Const. cosφ: Q sigue a P). Con `i_ctrl` 1 (Q) el `qsetp`
  se mide en el cubículo `pQmeas`/`p_cub`, con otro signo y pérdidas: no es la Q de la máquina.

- **Estatismo Q-V** [verificado 26-10, 3 VSC × 4 escenarios al 0,0001 pu]: con `i_droop` 1 la barra controlada
  queda en `usetp + (ddroop/100)/Srated · Q`, con Q la que entra al elemento conectado en el cubículo `pQmeas` (Q > 0
  hacia el equipo sube la tensión). `Qdroop` = Srated/(ddroop/100) [Mvar/pu]. Fuera de PF (OLF no tiene estatismo en
  generadores): intercalar +jX y −jX en serie entre la barra y ese elemento con X = k·Unom²·usetp [Ω] y regular el
  nodo del medio a `usetp` (ViQSilent `generalidad.red`); un lazo externo de punto fijo diverge en barras fuertes.

### SVC (ElmSvs) [TechRef, verificado el signo]

- Q en convención carga (ver §3). Límites en susceptancia (Qmax = ymax·|u|²): modelar como SVC con b, no Q fijo.
- `i_ctrl` 1 visto en todos los del SEN (control de tensión), `usetp`, droop opcional.
- Barra controlada [verificado 26-10, 7 SVC × 4 escenarios]: la del cubículo de medida `pQmeas` (el AT de su trafo),
  no su borne. Estatismo con la misma regla del controlador: `i_droop`, `ddroop` % sobre `Srated` del propio ElmSvs
  (100 MVA, 40 en Maitencillo y Pan de Azúcar).
- Límite en susceptancia [verificado 27-10, 5 SVC en su límite en bloque1_Qv1]: Q = `qmax`·V² con V del borne del SVC
  en pu (Cardones 152,0 = 160·0,9746²). En OLF un StaticVarCompensator con b_mín/b_máx lo reproduce exacto con
  regulación local, pero con regulación remota no converge (pypowsybl 1.16): ViQSilent deja el SVC como generador y
  reescala sus límites con V² con medio paso (con paso entero oscila: ganancia ≈ −1 detrás de su trafo).

## 8. Otros elementos [verificado]

| Elemento | Modelo |
|---|---|
| ElmScap (CCSS) | Serie `y = gcap + j·bcap` [S] (`bcap` = 1/`xcap`, `xcap` en Ω) |
| ElmSind | Serie `rrea + j·xrea` [Ω]; `ucn`, `Sn` informativos |
| ElmZpu | `r_pu + j·x_pu` (i→j), `r_pu_ji + j·x_pu_ji` (j→i), shunts `gi/bi/gj/bj_pu`, en pu de `Sn` y la tensión nominal de cada borne |
| ElmShnt | Desde resultados: `y = conj(S)/|V|²` (`bcap` en µS, `qcapn`, `ncapa` si se modela desde datos) |
| ElmLod | `m:P`/`m:Q` (difieren de `plini`/`qlini` por `scale0`); en el SEN `TypLod` con `kpu = kqu = 0` (potencia constante) |

## 9. pypowsybl (motor externo) [verificado]

- No carga su librería nativa desde rutas con «Ñ»: entorno en `C:\Users\vicen\.venvs\factores_lineales`.
- Slack: `distributed_slack=False`, `read_slack_bus=False` y `slackBusSelectionMode=NAME` con el **id de la vista de
  barras** (`bus_id`) del generador slack; si no, OLF elige otra barra en silencio. Verificar `slack_bus_results`.
- Trafo IIDM: en vacío `V2 = (rated_u2/rated_u1)·e^{jα}·V1`; impedancia en el lado 2. Desfases con un cambiador de fase
  de un paso. Poner la magnetización como shunts de barra evita depender de dónde ubica IIDM `g`, `b`.
- Tr3 como tres trafos a un nodo estrella; arrancar la estrella con su tensión exacta (eliminación con la solución de
  PF) o el residuo inicial es enorme.
- `newtonRaphsonConvEpsPerEq = 1e-7` para comparar con PF. Las corrientes de rama vienen en A.
- Sensibilidades: `BRANCH_CURRENT_1/2` (A/MW) y `BRANCH_ACTIVE_POWER_1/2`; un generador ficticio PQ por barra replica
  el método de PF. AC lineal de 7–10 barras: 0,1–0,2 s en el SEN.

## 10. Validación por capas (orden y criterio)

| Capa | Qué | Criterio usado |
|---|---|---|
| Topología | Terminales de una misma barra con igual V en PF | 0 diferencias > 0,01 kV |
| Balance | Σ resultados de PF por barra | < 0,5 MVA (si no, falta un elemento) |
| Ramas | Flujo de cada rama con V∠θ de PF | < 0,5 MVA; los que no, se diagnostican o calibran y se listan |
| Residuo IIDM | Lo mismo leyendo los parámetros desde pypowsybl | 0 barras > 1 MVA |
| Flujo N | pypowsybl desde la solución de PF | 1–2 iteraciones, slack ≈ 0 MW, ΔV ≤ 0,002 pu |
| N-1 | Contingencias contra un barrido de PF guardado | Δcarga ≤ 0,05 puntos |

Errores típicos que estas capas detectaron: signo del grupo de conexión, fórmula del tap complejo, convención de tap
del Tr3, Tr3 con terciario abierto, ramas de impedancia nula, signo del SVC.

### Ciclo empaquetado: `ciclo_lineal.py`

Con el escenario que se quiere activo en PF y el puente corriendo, en el venv del piloto: `python ciclo_lineal.py`.
1. Extrae el escenario activo tal cual (`cabecera_activo.py` y los cuatro `pf_extraer*`). Corre el ComLdf del
   estudio («Load Flow Calculation_revisar») sólo si no hay resultados vigentes. En la misma pasada lee del unilineal
   ZDI los vigilados (ElmLne/Tr2/Tr3) y las centrales candidatas, y resuelve en PF los elementos de cada contingencia
   con la regla del ciclo de PF: primera coincidencia (clase, nombre) en `GetCalcRelevantObjects`. Hay nombres
   repetidos (TR PARRAL está dos veces), por eso no se resuelve fuera de PF.
2. Valida contra PF con un semáforo. Son decisivos el flujo N, la P de la slack, ΔV y la carga de los vigilados en N
   (≤ 0,5 puntos). Topología, balance, ramas y trafos calibrados se informan sin detener el análisis.
3. N-1 en pypowsybl (~0,7 s por contingencia) y par a restringir con la regla del ciclo de PF: la mayor sobrecarga
   en N y, si no hay, la mayor sobre 100 % en contingencia.
4. Factores AC lineales por barra (y FD −5 MW con `--fd` o si el elemento es un circuito acoplado), con los
   participantes según la regla del ciclo (20 % del mayor |factor|, BESS primero, sin sincrónicas, extensión a las
   10 barras más cercanas si el ZDI no llega a 5 %/100 MW).

Para reutilizar una extracción: `--sin-extraer --suf _E04`. Necesita `factores_extraccion_zdi_E04.json`, que
`armar_cmd_escenario.armar_activo("_E04", solo_zdi=True)` genera en un comando de ~2 min.

## 11. Pendiente de confirmar con el usuario (hover en PF)

Resueltos el 23-10-2026 con hover del usuario: `i3loc`, `i30lc`, `itapos`, `iTaps`, `iMeasTap`, `mTaps`, matrices del
TypTow, `dphasing`/`dpolar`/`transp` del ElmTow, códigos de `av_mode`, atributos del ElmStactrl (`i_ctrl`,
`uset_mode`, `i_droop`, `iopt_drp`, `pQmeas`, `imode`, `consQdisp`). Quedan:
- `dphasing`: códigos resueltos el 27-10 (ver §acoples: 3 = cab, 4 = bca).
- ElmGenstat: atributo que fija inductivo/capacitivo del cosφ (`pf_recap` según notas de Cumbres; sus códigos).
- Siguen calibrados (tap efectivo): Chillán N3 y Coronel N6 (los demás Tr3 se explican con la impedancia según tap,
  §5). Chillán N3 (TypTr3 «75 MVA 154/69/14.8 kV (chillan)», visto en PF el 27-10): corriente de vacío 9,34 % en la
  estrella (dato raro), taps en alta (neutro 0) y media (neutro 8); desde la solución de PF la pata de media calza
  exacto pero la de alta no: PF se comporta como si el paso de alta fuera ~0,99 % y no 1,25 % (error de 50–60 a 0,8
  MVA en E01, E03 y E04). En el elemento: sin control de taps, sin reporte de mediciones ni características.
  «Transformer Ratio Adaptation» (`itratioadpt`, pestaña Advanced) está activo en 214 Tr3 y 609 Tr2: no lo explica.
- 52 grupos acoplados se identifican contra PF (26-10): 6 ElmCabsys sin extraer, 5 ElmTow con TypGeo sin matrices,
  13 ElmTow con TypTow de un circuito para dos líneas, 28 con configuración leída que no calza (Jadresic–Cumbre y Los
  Changos–Est. 448 500 kV, Ralco–Los Notros). Visto en PF el 26-10: **16 ElmTow tienen dos geometrías** (`pGeo` es una
  lista, un TypTow de un circuito por línea, «Distance» en la tabla) y la extracción leía sólo la primera. Los
  circuitos pueden ser ElmLne o **ElmLneroute** (tramos).
- **Matrices desde la geometría** [27-10, ViQSilent `motor/torres.py`]: con `TypTow.i_mode` 0 (338 tipos) PF calcula
  las matrices en cada flujo desde la geometría; las guardadas en el tipo (`R_c`, `X_c`, `B_c`) pueden estar viejas o
  simetrizadas (Los Changos–Est. 448: mutuas todas iguales). Con `i_mode` 1 (104 tipos) usa las ingresadas. Datos:
  TypTow `xy_c` (por circuito [x_a, x_b, x_c, y_a, y_b, y_c] m), `xy_e`, `pcond_c`, `pcond_e`; TypCon `rpha` (Ω/km por
  subconductor, DC), `erpha` (GMR mm), `diaco` (diámetro mm), `ncsub`, `dsubc` (separación entre subconductores
  vecinos, m), `iskin`; ElmTow `rearth` (Ω·m, manda sobre el del tipo), `sag_c`, `sag_e`. Carson completo (serie hasta
  k²), haz equivalente sobre un círculo de lado `dsubc`, cables de guardia por Kron, capacitancia con imágenes:
  reproduce las matrices de PF a 6·10⁻⁵ relativo. Con esto y los códigos de fase corregidos calzan sin calibrar 335
  de 376 grupos de E04 (antes 309).
