# Flujo diferencial (ComDiff «Compare»)

Comparación de resultados de PF: corre un flujo base (caso A), se modifica la red, se corre otro flujo (caso B) y el
diagrama muestra la diferencia. Usado en Cumbres del Ñuble (08 y 10-10-2026) para medir el impacto de un proyecto
(con − sin) y de una contingencia (con − sin el elemento), en MW absolutos, con foto del diagrama y tabla de factores.
Ejemplo listo para usar: `scripts/ejemplos/flujo_diferencial.py` (plantilla para `pf_drv.run`). Es la
generalización de los scripts que corrieron en PF real (S1 con/sin proyecto, S2 ante la contingencia C07 y zona de
influencia del 10-10-2026); la plantilla generalizada en sí todavía no se ha corrido: revisar la primera salida.

## Receta (verificada)

1. Activar caso de estudio y escenario (`cambiar_caso`), afirmar que el escenario es el esperado.
2. Tomar el comando del caso: `cd = [c for c in caso.GetContents("*.ComDiff") if c.loc_name == "Compare"][0]` y fijar
   `cd.imode = 2` (diferencia absoluta **B − A**).
3. Caso A: aplicar el estado base (p. ej. `gen.outserv = 1` para «sin proyecto»), correr el flujo y leer
   `cd.icomp`. **Cada flujo con la comparación encendida agrega un caso y sube `icomp`.** Si `icomp` no cambió, la
   comparación está apagada: encenderla con `cd.iopt_mode = "start"; cd.Execute()` (equivale al botón de PF) y repetir
   el flujo A.
4. `cd.ibase = icomp − 1` (índice base 0 del caso A) **antes** de correr el flujo B.
5. Caso B: aplicar el cambio (`gen.outserv = 0`, o abrir la línea de la contingencia), correr el flujo. El diagrama ya
   muestra B − A.
6. Foto: apagar alarmas de color si se quiere ver sólo la diferencia (`SetColscheme.cUseAlarm = 0`), `dg.Close();
   dg.Show()`, `exportar_grafico(nombre, pagina)`.
7. Tabla propia en paralelo: leer `m:P:bus1` (`m:P:bushv` en Tr3, y en Tr2 si `bus1` no existe) y `c:loading` de
   líneas, trafos y capacitores serie de las redes de interés en A y en B; dP = P_B − P_A con signo; factor = dP / P del
   proyecto (o / potencia perdida en una contingencia). Filtrar |dP| ≥ 0,2 MW y agrupar por nivel de tensión.
8. **Dejar el escenario sin cambio neto**: en un `finally`, restaurar el estado (proyecto en servicio, línea cerrada,
   opciones del flujo); correr un flujo final; si el escenario quedó marcado como modificado con los mismos valores, se
   puede guardar (en Cumbres, autorizado: «sin cambio neto»).

## Detalles

- Desbalance: con el proyecto fuera, su potencia la toma el slack (no se redespacha otra generación), salvo que el
  estudio pida otra cosa. Decirlo en el informe.
- Si el flujo no converge, reintentar con arranque plano (`ldf.iopt_noinit = 0`) y, como último recurso y avisando,
  sin límites de Q (`ldf.iopt_lim = 0`); restaurar las opciones en `finally`. No reportar casos que no convergieron
  como resultado; en el informe nunca escribir «no converge» (preferencia del usuario).
- El usuario puede correr la comparación al revés a mano (primero encendido y después apagado): leer `ibase`/`icomp`
  antes de interpretar.
- Atributos de ComDiff que el puente deja escribir aunque el comando sea del usuario: `iopt_mode`, `imode`, `ibase`,
  `icomp`.

## Para el informe (preferencias del usuario)

- Muchos zooms en vez de la página completa: un recorte por sistema (500, 220, 154/66 kV) con las cifras legibles.
- Tabla en % del despacho del proyecto (factor), prosa en MW.
- Comparaciones lado a lado con etiqueta roja tipo «Red N | C02». Ver la skill del informe para la maquetación.
