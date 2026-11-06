---
name: proyectos-aa-seia
description: Investiga qué es realmente un proyecto de generación o almacenamiento en Chile cruzando Acceso Abierto del CEN, SEIA, consultas de pertinencia, CNE y prensa. Devuelve NUP, titular, potencia instalada, inyección y retiro, BESS (MW/MWh), RCA y línea de tiempo, distinguiendo lo confirmado en documento de lo inferido. Úsala cuando haya que responder «cuántos MW son de verdad», «tiene RCA el BESS», «por qué la ficha dice 150 y el informe 115», «este proyecto es CRCA o híbrido», o completar un catastro de proyectos, híbridos o CRCA. También cuando aparezca un NUP, una RCA, un expediente SEIA, una consulta de pertinencia, un IAC o un proyecto del plan de expansión.
---

# Proyectos: Acceso Abierto, SEIA y pertinencias

Skill personal de Vicente (EE). El objetivo no es «buscar el dato» sino **decidir
cuál de los varios datos que existen es el que corresponde**, porque un mismo
proyecto tiene tres registros que no siempre coinciden: el ambiental (RCA), el de
conexión (AA/IAC) y el comercial (prensa). Casi todos los errores de catastro
vienen de mezclarlos.

Salida típica: una tabla de línea de tiempo, la evaluación de unas hipótesis y una
recomendación de modelado con grado de certeza. No un volcado de links.

## Regla de oro

**Cada cifra lleva fuente y fecha, y se dice qué representa.** «150 MW» no es un
dato: es un dato de qué (nominal, inyección, retiro, autorizada) en qué documento
(AA, IAC, RCA, CNE) y en qué fecha. Si no se puede decir eso, el dato no sirve.

## Antes de empezar

- **No escribir en OneDrive** ni en carpetas del proyecto ajeno. Entregables a
  Documentos o a la carpeta que indique el usuario.
- **Descargar PDF a `%TEMP%\<tema>\`** y extraer con `pdftotext`. No dejar basura
  en el proyecto.
- **Un archivo nuevo por proyecto investigado**, no editar el catastro del otro.
- Si el dato es confidencial, decirlo. No rellenar con lo que «debería» decir.

## Flujo

### 1. Anclar el proyecto

Antes de leer nada, fijar la identidad: **NUP + punto de conexión + titular**.
Un nombre no alcanza (ver `references/trampas.md`, trampa 9). Si dos documentos
con el mismo nombre no coinciden en NUP o en SE, son proyectos distintos.

```bash
S=~/.claude/skills/proyectos-aa-seia/scripts
python $S/aa.py --nup 3665 --full          # base pública de AA
python $S/aa.py --proyecto "andino"        # familia de nombres
python $S/aa.py --se "buli"                # quién más está en esa barra
python $S/seia.py buscar "Andino Suiza"    # expediente, titular, DIA/EIA, estado
python $S/seia.py pertinencia "Andino"     # ¿hay CdP?
```

La base pública de AA (`aa.py`) es el atajo que evita el portal con login. Trae
`potencia_nominal`, `potencia_nsi`, `potencia_nsr`, `potencia_cga`,
`potencia_caa`, `energia_caa`, `horas_almacenamiento_caa`, estado, paño y fecha
del IAC. Es la forma rápida de saber si el CEN tiene el proyecto como generación
pura, como SAE o como híbrido, y con cuántos MW.

### 2. Leer el expediente ambiental

Con el `EXPEDIENTE_ID` del paso 1:

- Ficha: `https://seia.sea.gob.cl/expediente/expediente.php?id_expediente=<id>`
- La **RCA** está en la pestaña de documentos, como
  `https://firma.sea.gob.cl/publicaciones/<AAAA>/<MM>/<DD>/<epoch>_<idDoc>`.
- Los **ICSARA** y **adendas** dan la línea de tiempo real (fecha de DIA, adenda,
  adenda complementaria, ICE, COEVA, RCA).
- La RCA trae la descripción de obras: ahí están los aerogeneradores, el BESS,
  los contenedores, la potencia y el punto de conexión. **Es la fuente que manda
  para lo que se puede construir.**

### 3. Buscar el BESS explícitamente

Nunca asumir que «no hay BESS» porque la nota de prensa no lo menciona. Revisar,
en este orden:

1. ¿La RCA describe un «área BESS», contenedores, PCS? (buscar `BESS`, `batería`,
   `contenedor`, `MWh`, `PCS` en el texto).
2. ¿Hay expediente SEIA propio? (`seia.py buscar "BESS <nombre>"`).
3. ¿Hay consulta de pertinencia? (`seia.py pertinencia "<nombre>"`).
4. ¿La SAC tiene campos `potencia_caa` / `energia_caa`? (`aa.py --nup`).

Si la RCA lo incluye, **no tiene RCA propia**: está cubierto por la del parque.
Si entró por pertinencia, no hay RCA nueva pero sí una resolución de pertinencia.
Si no aparece en ninguna, se dice «sin traza pública al <fecha>».

### 4. Cerrar con la prensa y la CNE

La prensa sirve para fechas y para detectar cambios de diseño (potencia que
sube o baja, número de turbinas). El Reporte Mensual ERNC de la CNE confirma la
potencia con RCA y si tiene almacenamiento. Nunca usar la prensa para reemplazar
un documento.

### 5. Entregar

Estructura fija:

1. **Respuesta corta** (5-6 bullets con la conclusión).
2. **Línea de tiempo** documento por documento: fecha | fuente | URL | tipo |
   eólico | BESS | inyección/retiro | titular | **cita textual**.
3. **Hipótesis** (las que haya planteado el usuario), cada una confirmada,
   descartada o abierta, con la evidencia.
4. **Respuesta directa** a la pregunta que originó todo (¿tiene RCA? ¿cuántos MW?).
5. **Qué modelar**, con grado de certeza por parámetro.
6. **Lo que no se pudo verificar**, con el motivo (confidencial, login, no existe).
7. **Fuentes** numeradas con URL y fecha.

## Marcas de certeza

| Marca | Significado |
|---|---|
| **✔** | Leído en el PDF citado, con la frase textual al lado |
| **(ag)** | Verificado por otro analista o herramienta, no reproducido por mí |
| **~** | Inferido de documento oficial, sin frase explícita |
| **?** | No verificable |

Nunca mezclar. Si un dato viene de una lectura ajena, se dice; si es una
inferencia, se dice; y si no se pudo, se dice.

## Errores que hay que evitar

- **Contar dos veces el mismo proyecto.** Si el BESS comparte el transformador y
  el paño, es una CRCA, no dos centrales. Modelar dos filas duplica la inyección
  en la barra.
- **Tomar la potencia nominal como inyección.** Un proyecto de 230 MW instalados
  puede tener 150 MW de inyección por el transformador o por el paño.
- **Confundir retiro con la comuna Retiro.** Ver `references/trampas.md`.
- **Creer que la ficha está actualizada.** La ficha de AA puede tener la potencia
  de la SAC original (a veces de hace cuatro años) y la RCA la definitiva.
- **Creer que la RCA está actualizada respecto del IAC.** Puede ser al revés: el
  IAC es anterior y quedó con la potencia vieja.
- **Inventar el número de resolución.** Las RCA traen `<NUM_RES>`; se cita por
  fecha y `idDocumento`.
- **Decir «no existe» cuando sólo no se encontró.** Fecha y método.

## Referencias

- `references/endpoints.md` — endpoints exactos, parámetros y significado de cada
  campo; incluye las herramientas ya hechas del usuario (`FiltradorAA`, `SEIA`).
- `references/trampas.md` — las doce trampas de lectura de PDF, tablas y nombres.
- `references/caso-andino-suiza.md` — caso completo resuelto, con las tres
  verdades (AA 150 / IAC 150+115 / RCA 115,2+115) y qué se modeló al final.

## Scripts

```bash
python scripts/aa.py --nup <NUP> --full
python scripts/aa.py --se "buli" --csv buli.csv
python scripts/seia.py buscar "<nombre>"
python scripts/seia.py pertinencia "<nombre>" --csv pert.csv
python scripts/cartas.py buscar "<empresa>" --desde 01/01/2024 --hasta 31/12/2026 --detalle
python scripts/cartas.py show <id>
python scripts/cartas.py bajar <id> salida.pdf
```

Todos usan sólo la biblioteca estándar (sin `requests`, sin pandas) y cachean la
base de AA un día en `%LOCALAPPDATA%\proyectos-aa-seia\aa.json`.
