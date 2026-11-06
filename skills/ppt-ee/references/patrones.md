# Patrones de lámina probados

Coordenadas en pulgadas. Todas asumen título en y=0,50 y franja de conclusión en y=6,15 (alto 0,62), salvo indicación. Vienen del deck del Estudio de Restricciones de Entre Valles (sep-2026), revisado por Vicente y Jorge.

## Índice
1. Contexto del proyecto (ficha + mapa)
2. Tabla + dos casos (escenarios y casos de estudio)
3. Figura grande + columna angosta de tarjetas (zona de influencia)
4. Gráfico + cifras en miniatura (resultado por escenario)
5. Tarjetas de cifra + pasos + figura (mecanismo de una contingencia)
6. Dos gráficos lado a lado (caso base vs sensibilidad, PFV y BESS)
7. Cadena lógica sin cifras + figura (planteamiento del problema)
8. Escalera de medidas + imagen (soluciones topológicas)
9. Alternativa: columna de detalle + diagrama (una por alternativa)
10. Comparación: gráfico + tabla cualitativa
11. Secuencia horizontal de 4 pasos + gráfico + figura (efecto encadenado)
12. Respaldo (después del ¡Gracias!)
13. Resumen de alternativas: tabla única opciones × bloques

---

### 1. Contexto del proyecto
- Izquierda, x 0,87, ancho 4,3: 5 tarjetas `GRL` de alto 0,78 cada 0,90 (etiqueta 11 pt gris en negrita + valor 16 pt; potencias en `OR`).
- Derecha, caja 5,45 / 1,50 / 7,0 × 4,48: mapa de ubicación (`copiar_formas` o figura).
- Franja: el dato que condiciona todo (p. ej. "comparten punto de conexión, la red ve la inyección neta").

### 2. Tabla + dos casos
- Tabla ancha arriba (x 0,87, y 1,50, ancho 11,6, fila 0,38) o imagen de la tabla del informe.
- Abajo dos columnas de 5,65: `encabezado()` (NEG para el caso base, GRT para la sensibilidad) en y 4,35 y tarjeta con viñetas en y 4,90, alto 1,08.

### 3. Figura grande + columna angosta
- Figura 0,87 / 1,55 / ~8,2 × 4,35. Columna derecha x 9,16, ancho 3,3: 4 tarjetas de alto 1,0 cada 1,12. La tarjeta crítica con `line=OR` y título en naranjo.

### 4. Gráfico + cifras en miniatura
- `barras_agrupadas` 0,87 / 1,45 / 7,1 × 4,55 (p. ej. recurso disponible `GRM` vs colocado `OR` por escenario; categorías "E01 | carga").
- Derecha x 8,3, ancho 4,15: 3 mini tarjetas (cifra 24 pt + etiqueta 11 pt) alto 0,98 cada 1,10, y una tarjeta `line=OR` con el elemento limitante.

### 5. Tarjetas de cifra + pasos + figura  (formato de referencia para láminas paralelas)
- Dos `tarjeta_cifra` 2,85 × 2,10 en x 0,87 y 3,95, y 1,55 ("E05 vespertino" / "0 MW" / "antes 11,3 MW").
- `pasos` en x 0,87, y 3,85, ancho 5,93, alto 0,64, separación 0,08, círculo 0,45; el último paso en naranjo.
- Figura 7,03 / 1,43 / 5,64 × ~5,0 y leyenda debajo (y 6,44) con título en negrita + "Informe, Figura X".
- Franja angosta: x 0,87, ancho 5,93 (no pasa por debajo de la figura).

### 6. Dos gráficos lado a lado
- PFV 0,87 / 1,45 / 6,6 × 4,55 y BESS 7,75 / 1,45 / 4,7 × 4,55, ambos `barras_agrupadas` con las mismas series y colores.
- Franja que diga dónde está la diferencia relevante (y si está en la lámina siguiente, que lo anticipe).

### 7. Cadena lógica sin cifras
- 3 pasos grandes a la izquierda (círculo 0,62, tarjeta 5,45 × 1,28, separación 0,17) con flechas hacia abajo `GRM` entre ellos.
- Figura a la derecha 7,45 / 1,55 / 5,0 × 4,35.
- Textos: título del paso 16 pt, explicación 13 pt. Ninguna cifra que no sea necesaria para entender.

### 8. Escalera de medidas + imagen
- `barras` 0,87 / 1,45 / 6,0 × 3,1 con `pcts` (una barra gris = referencia, naranjas = medidas).
- Debajo, 3 tarjetas 1,9 × 1,28 (T1, T2, T3: nombre 15 pt naranjo + acción 11 pt).
- Derecha: figura 7,2 / 1,5 / 5,25 × 3,25 para la reconfiguración y tarjeta `line=OR` "A considerar" debajo.

### 9. Alternativa: detalle + diagrama
- Izquierda, ancho 6,3: `encabezado` con la receta ("T1 + T2 + T3 | 2° ATR … | automatismo"), tarjeta "Cómo funciona" (3 viñetas), tarjeta `line=OR` con el insight contraintuitivo, y fila de cifras (dos `stat` 30 pt + tarjeta "Queda limitando").
- Derecha 7,45 / 1,50 / 5,0 × 4,48: diagrama del esquema (el unilineal con el RAG/DAG dibujado).

### 10. Comparación
- `barras_agrupadas` 0,87 / 1,45 / 5,9 × 4,55 con la referencia común en `GRM`.
- Tabla cualitativa a la derecha (x 7,05, ancho 5,4): filas Topología, Obra, Qué cubre el esquema, Queda limitando; encabezado de fila de 0,55 y filas de 0,6.

### 11. Secuencia horizontal + gráfico + figura
- Arriba, y 1,45: 4 tarjetas de 2,72 × 1,22 cada 2,95, con número en círculo (0,40) y chevrons naranjos en los huecos; la última con `line=OR`.
- Abajo izquierda: gráfico 0,87 / 2,85 / 6,6 × 3,15 con las barras en el mismo orden que los pasos.
- Abajo derecha: figura (7,75 / 2,9 / 4,7 × 1,84) y una tarjeta con la dependencia clave.

### 12. Respaldo
- Después del cierre. Título "Respaldo | …". Figuras del usuario movidas con `copiar_formas(…, quitar_origen=True)` a la caja 0,87 / 1,40 / 11,58 × 5,35, con sus anotaciones.

### 13. Resumen de alternativas: tabla única opciones × bloques
- Cierre obligatorio de la sección de alternativas. Una tabla, filas = opciones en orden de esfuerzo (caso base → maniobras sin obra → cada alternativa con automatismo → versiones extendidas), columnas = Obra + un grupo por bloque (nocturno: E05, E06; diurno: E03), cada celda con MW y % sobre la base de ese bloque.
- Barras dentro de las celdas en TODAS las columnas de resultado (o en ninguna): así se lee igual el nocturno que el diurno.
- Encabezado de dos niveles: bloque con su unidad arriba, escenario abajo. Filas finales de cada alternativa en negrita.
- Valores inferidos (no corridos, porque la restricción de ese bloque no cambia) con †, y la explicación al pie en una línea.
- Franja: la conclusión comparativa de toda la sección.
