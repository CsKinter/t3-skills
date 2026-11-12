# Estructura, validación final y cierre de la base de datos de un estudio

Cómo terminó organizada la BD del estudio de Cumbres del Ñuble (estado al 06-11-2026) y qué se verificó antes de
entregar. Complementa `estudio-restricciones.md`, que cubre el cálculo. PF 2025 SP4, por el puente.

**Índice**: 1 Estructura · 2 Reglas · 3 Trampas (posteriores al 10-10-2026) · 4 Lista de cierre.

## 1. Estructura recomendada

**Preferencias de Vicente (12-11-2026, mandan sobre el caso Cumbres de abajo)**
- **Un solo ComLdf para todo.** Todos los escenarios corren con el ComLdf por defecto del caso (`i_power=1`, arranque
  plano, `iopt_noinit=0`). Cambiar a ecuaciones de corriente (`i_power=0`) u otra opción sirve sólo para diagnosticar;
  si un escenario no converge con el defecto, se corrige el escenario (soporte local de tensión, despacho), no el
  ComLdf. Restituir siempre el defecto al terminar.
- **Tres variations de trabajo, nada más**: `Proyecto <nombre> (<código>)`, `Proyectos AA - Base (<horizonte>)` (toda
  la cartera de acceso abierto base en una sola, sus stages fusionados) y `Proyectos AA - Sensibilidad/expansión
  (<horizonte>)`. Las variations del CEN (generación, transmisión, otros) no se tocan.
- **Escenarios: sólo `1_Irrestrictos`, `2_Restringidos` y `99_Respaldo`.** En respaldo, sólo lo que pueda servir
  después (fondo sin proyecto, demanda escalada, origen de la BD), con nombres descriptivos.
- **Lo que no se usa se borra.** Antes, una versión del proyecto (`CreateVersion`), que es el respaldo real. No
  acumular copias de carpetas como respaldo. Variations o escenarios que aún pueden servir (p. ej., cartera por
  acordar) van a `99_Respaldo`; el resto, a la papelera.
- Preferir lo simple: pocas carpetas, nombres claros, el estado legible sin abrir scripts. Verificar el orden con
  flujos antes y después (diferencia cero) y registrar en el AGENTS.md del proyecto.

**Study Cases** (`Study Cases\00_<Proyecto>\<POI>\`)
- Un caso por condición térmica que de verdad se use, numerados por orden de uso: `01_25 CS` (con sol) y `02_15 SS`
  (sin sol). Un caso que no se usa se elimina al cierre y se renumera. Scripts y JSON anteriores a una renumeración
  conservan los nombres viejos: anotarlo.
- Las copias que crea el puente van a `99_Respaldo`, no a la raíz.
- Cada caso abre sólo las páginas de diagrama del proyecto. Una página sólo funciona si la hora de estudio del caso
  activa el stage que creó ese diagrama.

**Operation Scenarios** (`00_<Proyecto>\<POI>\`)
- Carpeta `_secure` con los originales del cliente: intocable.
- `1_Irrestrictos` (punto de partida) y `2_Restringidos` (resultado, 1:1 con el informe). **Sólo los finales**, con el
  mismo nombre en ambas carpetas (`E0x_<BLOQUE>_<DEMANDA>_<temp>_BESS-<estado>`).
- `99_Respaldo` sólo con lo que pueda servir después (ver preferencias arriba); las copias de verificación se
  borran tras una versión del proyecto. Nunca dentro de las dos carpetas oficiales.
- Una sensibilidad que forma parte del informe tiene su carpeta `3_Sensibilidad_<…>`. Nace en respaldo y se promueve.
- `loc_name` admite 40 caracteres: nombres de carpeta cortos.
- El estado debe poder revisarse sin leer scripts.

**Variations**
- Al cierre no quedan variations de trabajo sueltas. Los ajustes del proyecto se fusionan (`ApplyChanges`) en un stage
  único dentro de la carpeta del proyecto, con hora justo anterior a la hora de estudio del caso donde debe valer.
- Un stage que no debe aplicarse **se archiva con una hora futura** en lugar de borrarse.
- Las variations de terceros no se tocan.
- Variation de sesión: `Trabajo_<fecha>`; stages separados ≥ 1 min. El puente en modo modificación la crea sola al
  arrancar: no es una edición propia.

**Nombres y marcas**
- Nombre limpio y marca del proyecto en `desc`. Sin nombres de herramientas ni de agentes en casos, escenarios,
  variations ni diagramas.
- Scripts de casos en `Library\Scripts\00_<Proyecto>\`. Los lanzadores del puente en carpeta aparte, para borrarla al
  final. Los scripts copiados pueden traer rutas de archivo de otro usuario.

## 2. Reglas

1. **Estado efectivo = variation activa y hora del stage ≤ hora de estudio del caso.** Antes de mover, fusionar o
   borrar variations, inventariar horas de estudio y qué stages son efectivos en cada caso. El objetivo de un orden es
   «efectivo final idéntico al de hoy». Reubicar horas puede activar en otro caso lo que estaba inerte.
2. **Desactivar una variation en cada caso donde figura antes de borrarla.** Si no, quedan referencias colgantes. Las
   variations borradas van a la papelera del proyecto y se restauran con clic derecho → Restore.
3. **Medir antes y después de cada operación de orden**: N en todos los escenarios finales, comparando corriente por
   rama y tensión en barras ≥ 100 kV. Se exige diferencia cero, no sólo que converja.
4. **Un escenario se promueve, no se edita.** El entregado se mueve a `Previos…`, la copia validada toma el nombre
   oficial y se comparan atributos entre ambos para confirmar que sólo difiere lo esperado.
5. **Contraste entre herramientas con tolerancia y parada.** En Cumbres: ΔI ≤ 0,02 kA y ΔU ≤ 0,005 pu, o ±0,5 pp en
   los elementos sobre 98,5 %. Si se supera, se detiene y se concilia. No se ajusta PF para forzar coincidencia.
6. **El alcance de la validación se acuerda y se escribe**: «N más las contingencias críticas» no es un N-1 completo.
   Los irrestrictos conservan sus sobrecargas esperadas.
7. **Contraste sobre copias**, con límites de P y Q, taps fijos y arranque plano. Se compara P, modo de control,
   consigna y límites. La Q de una máquina en control de tensión es resultado: no se compara.
8. Antes de comparar contra un proyecto de referencia, confirmar con `estado` qué proyecto y caso están activos, y
   revisar impedancias de los equipos homologados. Un ensayo con equipos cambiados no es «reproducción sin cambios».

## 3. Trampas

| Trampa | Qué pasa | Qué hacer |
|---|---|---|
| Dos generadores en el mismo terminal en control de tensión con consignas distintas, sin controlador de estación | PF no ejecuta el flujo: «More than one element controls V…». Igualar consignas no basta | Dejar un solo regulador (el otro en Q constante) o un controlador de estación. Barrer estos casos antes de validar. **Típico de un parque con BESS** |
| Segunda solución espuria | Tensión baja y sobrecargas absurdas. Arranque en caliente y cambio de consignas no ayudan | Diagnóstico: `ComLdf.i_power = 0` muestra la solución buena. **Solución: no** dejarlo así; corregir la tensión (soporte local) hasta que converja con el ComLdf por defecto. Todos los escenarios deben correr con el mismo ComLdf. Restituir siempre el defecto: el ComLdf es del caso, no del escenario |
| Transformadores en paralelo con taps distintos tras un ajuste automático | Cada unidad llega a su propio terminal: agrupar por terminal no los encuentra | Agrupar por devanado, rango de tap y S/E@kV de cada lado (`soporte-local-tension.md`) |
| Barrido con la formulación equivocada | «Hallazgos» físicos falsos | Conservar los archivos del diagnóstico descartado marcados como tales |
| Primera extracción tras arrancar el puente | Resultados vacíos (`u = None`) | Ejecutar el ComLdf del caso sin cambiar opciones y extraer después |
| `GetOperationValue` con `av_mode` | No lo devuelve como texto | Reactivar el escenario y leer el objeto |
| Atributo operativo fuera de la lista del puente (`i_ctrl`) | No se guarda en el escenario | Ampliar la lista con respaldo y probar |
| Q escrita antes que P en Q constante | PF recalcula | Escribir Q después de P |
| «conflicts … during activation of expansion stage» al reactivar un caso | Objetos gráficos de un stage. No afecta el flujo | Confirmar con N idéntico antes y después |
| «Target object … not found» al activar un escenario | Objetos que ya no existen. No afecta el cálculo | Idem |
| Borrar o mover objetos ajenos | El puente no puede en modo normal | Modo limpieza, o lista para hacerlo en la GUI |
| Factor de reducción oculto en una línea (`fline`) | La corriente efectiva no es la del tipo | Comparar corriente efectiva con `sline` |
| Curva térmica asignada pero sin trigger de escala | La capacidad efectiva no sigue la curva | Verificar con flujo en cada caso, no leyendo la matriz |

## 4. Lista de cierre

1. `estado`: proyecto y caso activos. Activar el caso, después el escenario, y afirmar la ruta.
2. Inventario de variations, horas de estudio y stages efectivos. Medición «antes» de N en todos los finales.
3. Mover los escenarios previos a `99_Respaldo\Previos <hito>`. Comprobar que los originales siguen intactos.
4. Contraste sobre copias con la tolerancia acordada. Registrar elementos críticos, despacho y que cada proyecto
   aparece una sola vez.
5. Barrer controles de tensión en paralelo. Confirmar persistencia reactivando escenarios (`iModified = 0`).
6. Promover: entregado a `Previos…`, validado con el nombre oficial, comprobar que resuelve N.
7. Ordenar: desactivar variations de trabajo caso por caso, fusionar stages, archivar los inertes con hora futura,
   borrar variations vacías, renumerar casos, mover copias, dejar abiertas sólo las páginas del proyecto, quitar marcas
   de herramientas de nombres y descripciones.
8. Medición «después» de N en todos los finales: diferencia cero contra el punto 2. Ningún escenario modificado. Dejar
   activo un caso base.
9. Comprobante en la carpeta del proyecto (`RESULTADO.md`, JSON de promoción, diario del puente) y lista de lo que
   queda para la GUI.
10. Actualizar AGENTS.md del proyecto con los nombres finales. No repetir scripts de promoción sobre la entrega.

Todo cambio de esta lista se propone al usuario antes de aplicarlo.

## Fusionar variations y limpiar escenarios (Sidon, 12-11-2026)

- Estructura pedida por Vicente: en la carpeta de trabajo, tres variations (proyecto, AA base, AA sensibilidad); en
  escenarios, sólo `1_Irrestrictos`, `2_Restringidos` y `99_Respaldo`. Las variations del CEN (generación, transmisión,
  otros) no se tocan.
- Fusión verificada: versión del proyecto → `Deactivate()` de origen y destino en el caso activo → `destino.Move(stage)`
  (rc 0; comprobar `stage.GetParent() == destino`) → `destino.Activate()` → renombrar → `Delete()` de las variations
  vacías. Antes, revisar que no haya dos stages con el mismo `tAcTime` en el destino. El otro caso que usa la variation
  destino la mantiene activa.
- Prueba: flujo de todos los escenarios de ambos casos con el ComLdf por defecto antes y después: misma slack, ΔU = 0 en
  todas las barras ≥ 60 kV y mismo número de elementos. Los solapes por nombre entre stages (`Cub_1`, `Switch`) eran
  objetos distintos.
- Para mover una carpeta que contiene el escenario activo, desactivarlo antes (`Deactivate()`).
- `Delete()` manda a la papelera de PF; la versión previa del proyecto es el respaldo real.
