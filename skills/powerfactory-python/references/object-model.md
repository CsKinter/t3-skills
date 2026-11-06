# Modelo de objetos: punteros y atributos verificados

Estado: **verificado** = confirmado en ejecuciones reales de PowerFactory; **supuesto** = usado en
código pero sin confirmación real todavía (verifícalo en la primera ejecución y avisa al usuario).

## Líneas

| Dato | Acceso | Estado |
|---|---|---|
| Tensión nominal (kV) | `ElmLne.GetAttribute("e:Unom")` | verificado |
| Serial (a veces contiene el ID de otra base de datos) | `ElmLne.sernum` | verificado |
| Largo | `ElmLne.dline` (unidad del proyecto, normalmente km) | supuesto |
| Tipo | `ElmLne.typ_id` → `TypLne`, `TypTow` o `TypGeo` | verificado |
| Acoplamiento de líneas | `ElmLne.c_ptow` → `ElmTow` (uno o varios) | verificado (lectura) |
| Branch contenedor | ruta: `...\Nombre.ElmBranch\Linea.ElmLne` | verificado |

## Capacidad térmica: tres modelos

1. **TypLne**: `ElmLne.typ_id → TypLne`. Corriente nominal `TypLne.sline` (kA).
2. **TypTow directo**: `ElmLne.typ_id → TypTow → pcond_c → TypCon`. `pcond_c` es una lista (un
   elemento por circuito/fase, normalmente el mismo TypCon repetido). La capacidad está en `TypCon.sline`.
   Si hay varios TypCon distintos, falta la relación circuito → conductor: no adivinar.
   Respaldo de lectura cuando `pcond_c` viene vacío: tabla `tc` con filas que tienen `pcond_c`.
3. **Acoplamiento ElmTow**: `ElmLne.c_ptow → ElmTow → pGeo → TypTow → pcond_c → TypCon`.
   `ElmTow` está en la red (se registra en variations) y afecta a **todos** los circuitos acoplados.
   Respaldo de lectura: `ElmTow.tab_Geo`. Escritura de `pGeo` en PF real: supuesto.

Clasificación de TypCon/TypLne `sline` como "capacidad fija" cuando no hay característica.

## Características de parámetros

- Una característica asignada a un parámetro es un hijo `ChaRef` **dentro del objeto dueño del
  parámetro**, con nombre igual al parámetro: `tipo.GetContents("sline.ChaRef")`. `ChaRef.typ_id`
  apunta a la característica (`ChaMat`, `ChaVec`...). Verificado para `sline` en TypLne y TypCon.
- Si el dueño es un tipo (biblioteca), repuntar el ChaRef cambia el modelo base → copiar el tipo.
- Para asignar una característica a una copia que no la tenía: `copia.CreateObject("ChaRef", "sline")`
  y `SetAttribute("typ_id", cha)`. Verificado.

### ChaMat (matriz 2D discreta)

| Dato | Acceso | Estado |
|---|---|---|
| Escala de filas | `ChaMat.scalerow` → `TriDisc` | verificado |
| Escala de columnas | `ChaMat.scalecol` → `TriDisc` | verificado |
| Valores | `ChaMat.matrix` (lista de filas; filas × columnas = casos de las escalas) | verificado lectura y escritura |
| Casos de la escala | `TriDisc.cases` (lista de strings: "SS", "CS", "15", "25"...) | verificado lectura y escritura |

- Los valores de las características térmicas revisadas eran absolutos en kA. Una característica puede
  estar configurada como relativa: al crear una nueva, **copiar una existente** como plantilla en vez
  de crearla desde cero, para heredar esa configuración.
- Cada escala discreta tiene un **trigger** en el caso de estudio que fija el caso activo. El script
  no los crea: al usar escalas nuevas, pide al usuario revisar/ajustar los triggers en el study case.
- Varias líneas pueden compartir tipo, ChaMat y escalas. Contar referencias antes de proponer cambios.
- **`ChaMat.usage`** (verificado 09-10-2026): `2` = valores absolutos (kA); con otro valor PF los interpreta como
  relativos al parámetro y la capacidad sale multiplicada. Las ChaMat del usuario en Cumbres (`Capacidades_Manual_CdN`)
  usan `usage = 2` y la matriz `[[15SS, 25CS, 35CS], [25CS, 25CS, 35CS]]` con escalas Sol_CdN (filas) y
  Temperatura_CdN (columnas).
- **ChaRef con nombre exacto** (verificado 09-10-2026): el hijo que asigna la característica debe llamarse exactamente
  como el parámetro (`sline`). Con sufijo no enlaza; renombrarlo después tampoco sirve y el flujo falla con «Error in
  load flow data» sin más detalle. Si pasó, copiar el tipo original de nuevo (`<tramo>_CdN`), crear el ChaRef `sline`
  y repuntar la línea.

## Topología: terminales, cubículos y acoples

| Dato | Acceso | Estado |
|---|---|---|
| Elementos conectados a un terminal | `term.GetContents("*.StaCubic")` → `cub.obj_id` (el elemento); o `term.GetConnectedElements()` | verificado |
| Terminal de un borne | `get_attr(elem, "bus1")` (o `bushv`/`busmv`/`buslv` en trafos) → StaCubic → `cubic.cterm` | verificado |
| Acople / interruptor | `ElmCoup` con `bus1`/`bus2`; cerrado si `on_off == 1` | verificado |
| Barra vs nodo interno | `ElmTerm.iUsage`: 0 = barra (busbar), otros = nodo interno o de unión | verificado |
| Subestación | `term.GetParent()` es `ElmSubstat` (si no, el terminal cuelga directo de la red) | verificado |
| Tensión nominal del terminal | `ElmTerm.uknom` (kV) | verificado |
| Elementos en servicio de la red activa | `app.GetCalcRelevantObjects("*.ElmTerm")` (filtrar por clase; el patrón por nombre con comodines no devolvió nada) | verificado |

- **Barra a la que llega un elemento** = primera barra (`iUsage == 0`) alcanzable desde el terminal de su cubículo
  recorriendo sólo `ElmCoup` cerrados dentro de la misma `ElmSubstat`. Así se detecta la B1/B2, la barra de
  transferencia o una barra auxiliar (52B1, TAT2, AT1_aux...) en vez de suponer «la barra principal».
- **Componentes de una subestación**: unir terminales por acoples cerrados (union-find) muestra qué barras forman un
  mismo nodo eléctrico y qué acoples abiertos las separan. Un devanado que llega a un componente aislado (p. ej. el
  terciario de 66 kV del ATR Itahue en «Cub») no está conectado aunque el trafo esté en servicio.
- Un extremo «(sin barra: 52B2)» (nodo interno sin camino cerrado a una barra) = la línea está abierta en ese extremo
  (p. ej. Retiro–Parral 66 y Parral–Linares 154 en operación normal del CEN).
- Nombres de terminales se repiten entre redes (Est 28, T_53...): resolver por `SE|barra` (subestación + nombre) o por
  el extremo de una línea conocida, nunca sólo por nombre.

## Diagramas (objetos gráficos)

Verificado en PF 2025 SP4 (09/10-10-2026) armando un unilineal por script. Detalle y método en `diagramas-unilineales.md`.

| Objeto | Atributos útiles |
|---|---|
| `IntGrfnet` (diagrama) | `Show()`, `Close()`, `Rebuild`; contiene `IntGrf`, carpeta `Layers` (`IntGrflayer`) y la página |
| `IntGrf` (símbolo) | `pDataObj` (elemento de red), `sSymNam` (`TermStrip`, `ShortTermStrip`, `PointTerm`, `d_lin`, `d_tr2`, `d_tr3`, `d_genstat`), `rCenterX`, `rCenterY` (mm, y hacia arriba), `iRot` (0/90/180/270), `rSizeX` (largo de barra = rSizeX × 26,25 mm en TermStrip, × 8,75 en ShortTermStrip) |
| `IntGrfcon` (conexión, hijo del IntGrf) | `iDatConNr` (borne: 0, 1, 2; -1 libre), `rX`, `rY` (vectores de 20 con relleno -1) |
| `SetVitxt` (caja de resultados, hijo del IntGrf) | Lista completa del diálogo (usuario, 10-10-2026): `zlvl` visible (1/0); `center_x`, `center_y` posición; `iBoxRefPt` Box Reference Point; `iParRefPt` punto de alineación del padre; `vlpos` posición sobre la línea de conexión; `anr` número de conexión (1 = borne 0); `do_rot` (0 = no gira con el símbolo) y `rotate` (radianes): **la rotación de la caja es esto, no `iOrient`**; `iOrient` alineación del texto; `ifont` fuente; `iCol` color; `glvl` nivel gráfico; `iLines` número de líneas; `chars` caracteres por línea; `iRot1_4` en ángulo recto; `iKeepPos` fijar posición. Cajas de barra (TermStrip): con `iBoxRefPt = -1` el origen es el extremo inicial de la barra (abajo en verticales, izquierda en horizontales), `center_x` a lo largo de la barra y `center_y` perpendicular (marco local de la barra). Antes de adivinar nombres de atributos, buscar aquí. |
| `IntGrflayer` «Annotations» | `annotationElementsStr`: lista de strings `$G` / `Text(origin = {x, y}, extent = {{-w,-h},{w,h}}, textColor = {r,g,b}, textString = "…", fontSize = n, fontName = "Arial", textStyle = {TextStyle.Bold})` / `/E` (también `Polygon(...)`); se escribe completa con `SetAttribute`; `iVis` |
| `IntGrflayer` «Labels» | `iVis = 0` oculta los nombres automáticos de PF |
| Hoja | página `SetGrfpage.aDrwFrm` → formato `SetFormat` (`iSizeX`, `iSizeY` en mm); crear un formato propio `_CdN` |
| Esquema de colores | `SetColscheme.cUseAlarm` (0 = sin colores de alarma por sobrecarga) |

- **Conexiones punto por punto**: `SetAttribute("rX:%d" % i, x)`. Escribir el vector completo rompe el enlace con la
  barra (aparecen «<<» y guías al origen). PF no acorta con -1: rellenar repitiendo el último punto.
- Objetos nuevos: `dg.AddCopy(plantilla, nombre)` de un IntGrf del mismo símbolo que ya tenga sus GCO, y luego
  `pDataObj = elemento`. Un Tr3 copiado puede traer dos GCO con el mismo `iDatConNr`: reasignar el sobrante como 2.
- Un elemento cuyo cubículo llega a una barra NO dibujada (aunque esté acoplada a la dibujada) queda suelto con «<<».
- En un muñón (línea cuyo otro extremo no está dibujado) PF dibuja sólo la mitad que llega a la barra y pone el «<<»
  en la posición del símbolo de la línea (`rCenterX/Y` del IntGrf `d_lin`).

## Carpetas

| Carpeta | Acceso |
|---|---|
| Equipment Type Library | `app.GetProjectFolder("equip")` |
| Operational Library | `app.GetProjectFolder("oplib")` |
| Characteristics | `app.GetProjectFolder("chars")` (respaldo: hijo "Characteristics" de oplib) |
| Escalas | `IntScales` dentro de Characteristics (normalmente "Scale") |
| Variations | `app.GetProjectFolder("scheme")` |
| Redes (ElmNet) | `app.GetProjectFolder("netdat")` |
| Diagramas | `app.GetProjectFolder("dia")` (IntGrfnet, recursivo) |

## Unidades y conversiones

- Corrientes de tipos y características: kA. MVA = √3 · kV · kA.
- Datos externos en A se convierten a kA solo si la unidad lo indica.
