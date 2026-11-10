---
name: parametros-sen
description: Busca parámetros de instalaciones del SEN para estudios de restricciones: capacidad de líneas (conductor y equipos de paño Int/Desc/TO/TTCC por extremo), transformadores, tensiones de servicio (ETS) y capacidad de obras futuras (PET, decretos, NUP en PGP). Usar cuando haya que completar o revisar tablas de capacidades/“adecuación de base de datos”, rellenar S/I, cruzar con Infotécnica, buscar un NUP o la capacidad “al menos X MVA a 35 °C” de una línea futura.
---

# Parámetros del SEN (estudios de restricciones)

Skill personal de Vicente; se va ajustando con el uso. Salida en **JSON/CSV**: el paso a Excel o Word del informe lo hace el
script de cada proyecto (o `scripts/excel_com.ps1`).

## Antes de empezar

- **Esto es para parámetros de instalaciones.** Si lo que hay que resolver es un
  **proyecto** (qué es, cuántos MW tiene, si el BESS tiene RCA, qué dice el IAC),
  usar la skill `proyectos-aa-seia`: trae la base pública de Acceso Abierto, el
  buscador de cartas y el de pertinencias, y las trampas de lectura de PDF.
- **No escribas en OneDrive** (`...\OneDrive - Electrical Studies Corp\...`) salvo que el AGENTS.md del proyecto lo
  permita para una carpeta concreta y el usuario lo apruebe. Por defecto, sólo leer y entregar a Documentos.
- **No pises archivos del usuario**: si el Excel o el informe está abierto (`~$...`) o cambió desde tu última escritura,
  construye en scratch y espera/compara antes de copiar.
- **Descargar archivos (PGP, PDF) requiere el OK del usuario** en el chat.
- Caché en `%LOCALAPPDATA%\parametros-sen\cache` (listas 14 días, fichas 7). `--refrescar` si el usuario dice que IT cambió.

## Fuentes, en orden

| Instalación | Fuente | Script |
|---|---|---|
| Existente | Infotécnica (API pública, sin sesión) | `it.py linea / pano / trafo / buscar` |
| Futura (obra PET) | ITD/decreto del PET: “al menos X MVA … a 35 °C con sol” | `pet.py A B --carpeta <PET>` |
| Futura con NUP | PGP: descripción y `extra_data.capacity` | `pgp.py buscar <NUP o texto>` |
| Sin nada de lo anterior | Tipo de línea del modelo o una obra equivalente → marcar **(ref.)** y avisar | — |
| Tensiones | ETS vía `subestaciones_tensiones.html` | `tensiones.py "Barra:kV[:PROXY]"` |

La carpeta PET del proyecto suele estar en `...\Trabajo\01_Estudio de Restricciones\00_Plan de Obras\PET`.
Detalle de endpoints y conceptos: `references/infotecnica.md`; obras futuras: `references/futuras.md`.

## Reglas (lo que Vicente espera)

1. **Estados de Infotécnica = colores.** Validado `C6EFCE` (verde), Sin Revisar `FFEB9C` (amarillo, “en revisión”),
   **Rechazado `FFC7CE` (rojo): el valor se USA igual, sólo se marca en rojo**. Sin dato en IT: `S/I` gris `D9D9D9`.
   Obtenido de PET/NUP: `9DC3E6`. Instalación futura sin dato: `S/I` amarillo claro `FFF2CC`.
2. **Todo en kA**, por circuito, **3 decimales** en la tabla (aunque sea entero), coma decimal en el informe.
3. **Conductor**: ficha `limites-termicos` de cada sección (Sin Sol 15 °C, Con Sol 25 °C, Con Sol 35 °C). Si viene
   rechazada o vacía, la ficha `general` (“1.9 Límite térmico permanente … con sol 15/25 °C”; no trae 35 °C) y se dice
   en una nota. Con varias secciones, **la menor**.
4. **Equipos de paño**: el menor de cada tipo en el paño (3 desconectadores → el menor; a igual valor, el mejor certificado).
   Int “Corriente nominal” [A]→kA; Desc y TO “Corriente nominal” [kA]; TTCC “**Sobrecarga permanente**” [kA] (TAP × factor).
   **CCSS sí está en IT** (tipo «Condensadores Serie», `condensadores-series`), pero `it.py` aún no lo consulta y
   escribe S/I: traerlo aparte según `references/capacidad-por-condicion.md` §2. Sin trampa de onda registrada →
   **N/A** (no S/I). Tap o estructura → N/A.
5. **Límite de la línea** = mín(conductor, equipos de ambos extremos) por condición, con el equipo que limita
   (`Conductor`, `Int`, `Desc`, `TO`, `TTCC`, `CCSS`). Cada valor lleva condición (N o post-contingencia), duración y
   temperatura. Capacidad de corta duración, factores de sobrecarga, fuentes y el procedimiento completo de
   adecuación de base de datos: `references/capacidad-por-condicion.md`.
6. **Doble circuito** (C1/C2 son tramos distintos en IT): una fila por línea con el circuito **más limitante**; dilo si difieren.
7. **Seccionamientos (\*)**: los tramos nuevos que cortan una línea existente toman los parámetros de la original.
8. **Líneas futuras**: una sola fila, sin detalle de paños, con la capacidad mínima del PET/NUP en kA
   (`MVA / (√3·kV)`) aplicada igual a 15 y 25 °C (y 35). Si el documento la da a 25 °C, dilo.
9. **Ficha del equipo antes que el resumen de la línea**: la ficha general de la sección repite los TTCC (“1.25/1.26”)
   pero puede contradecir al equipo (Ancoa–Pehuenche: resumen 0,6 kA vs ficha del TC multi-razón 2000×1,2 = 2,4 kA). Se
   usa la del equipo y se avisa la diferencia.
10. **Transformadores**: capacidad máxima (2.4/3.3 ONAF II si existe). Ojo con bancos monofásicos (Ancoa KT1 informa 250
    MVA por unidad → banco 750) y trafos de doble tensión primaria (Monterrico 230-154 kV, opera en 154).
11. Simple para el cliente: nada de “modelado/no modelado” ni info interna en las tablas del informe.

## Flujo típico (tabla de capacidades de líneas)

```bash
S=~/.claude/skills/parametros-sen/scripts
python $S/it.py buscar "concepcion san vicente"          # ids de tramos (C1, C2...)
python $S/it.py linea x --id 325 572 --json l.json --csv l.csv
python $S/it.py pano "CONCEPCION B8"                      # detalle por equipo, con estado (para revisar mínimos raros)
python $S/it.py trafo "ANCOA"
python $S/pet.py COIQUEN DELICIAS --carpeta "<PET>"       # futuras
python $S/pgp.py buscar 1087
python $S/tensiones.py "Ancoa:500" "Tiquel:220:CAUQUENES" "Parral:154"
```

Revisa siempre la salida de `linea`: si un mínimo viene de un único equipo rechazado muy distinto de los demás
(p. ej. TTCC 0,2 kA rechazado junto a 0,4 validado), se usa igual (regla 1) pero **avísalo** al usuario.

Para el Excel del proyecto: genera una lista de operaciones JSON y aplícala con `excel_com.ps1` sobre una copia
(`references/excel.md`). openpyxl sólo para leer.

## Cruce con el modelo (PowerFactory)

La hoja `Capacidades_script` del Excel trae los elementos del modelo (ID de la app de carga a IT, nombre PF) y la columna
M “Tramo en Capacidades_informe”. Para cruzar: tramos PF partidos en estructuras (E14, Est 7…) → la línea completa;
enroques/seccionamientos → el tramo del informe que los contiene; reactores no se cruzan. Pendiente: integrar la app del
usuario (cuando la envíe).

## Trampas conocidas

`references/infotecnica.md#trampas`. Lo principal: regex exacta de conceptos (“Factor de sobrecarga permanente” y
“admisible de corta duración” NO son la sobrecarga), paréntesis en nombres (COCHARCAS (CGE) ≠ (FFCC)), códigos PAxxx
internos, `id_conexion` no sirve para asociar equipos a paños, y los extremos de tramos a veces no traen código de paño.
