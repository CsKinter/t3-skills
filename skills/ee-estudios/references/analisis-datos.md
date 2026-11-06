# Análisis de datos | trazabilidad e interpretación

## Separar las capas

Conservar datos originales, transformación reproducible, resultados calculados y presentación como capas distintas. Un HTML bonito o un Excel con valores constantes no prueban por sí solos cómo se obtuvieron las cifras.

Registrar fuente, fecha de descarga o versión, cobertura temporal, unidades, filtros, exclusiones, metodología y archivos de salida. No confundir fecha de modificación con fecha de los datos. Un HTML precalculado y un CSV posterior pueden describir períodos diferentes.

Separar archivos del entregable y sus fuentes de construcción de los archivos de agentes, pruebas, respaldos y notas. Respetar el destino acordado del proyecto; al mover carpetas, verificar integridad por listado y hashes antes de eliminar el origen, si la eliminación está autorizada. No reorganizar entregables mientras otro colaborador los edita.

## Unidades y tiempo

- Identificar MW, MWh, kW, kA, pu, cotas y factores de planta. Comprobar escalas, signo, base de capacidad y agregación.
- Distinguir potencia bruta/neta y disponibilidad/despacho. Generación más vertimiento solo aproxima recurso disponible si las definiciones y cobertura son compatibles.
- Documentar zona horaria y significado de horas 1–24: inicio o término del intervalo. Revisar cambios de hora, duplicados, horas ausentes y períodos incompletos.
- Diferenciar cero, dato faltante, unidad fuera de servicio y ausencia de recurso. No rellenar con cero antes de comprender la causa.
- Reportar tamaños de muestra y cobertura al comparar estaciones, bloques horarios o tipos de día.

## Estadística y escenario de operación

Una mediana o un cuantil condicionado describe registros históricos; no constituye por sí mismo un despacho operacional óptimo o factible. Explicar el paso entre esa estadística y el punto de operación elegido, conservando las hipótesis aprobadas del estudio.

Revisar filtros de estación, hidrología, tipo de día, hora y recurso. Evitar cambiar varios a la vez sin rastrear su efecto. Comprobar que el grupo comparado tiene la cobertura suficiente y que no mezcla capacidades de períodos diferentes.

**Preferencia.** Presentar tendencias y órdenes de magnitud útiles, normalmente con MW y porcentajes enteros, sin perder la precisión original de los cálculos. No borrar una diferencia relevante cerca de un umbral.

## Hidráulicas y embalses

Distinguir cota alta dentro de la muestra de embalse lleno: un cuartil superior es una posición estadística, no una fracción de llenado. Identificar la referencia física si se habla de capacidad almacenada.

Un embalse puede alimentar centrales con regulaciones distintas. Desglosar por central cuando el agregado oculte diferencias de almacenamiento, continuidad de caudal o flexibilidad. Una central con pocas horas de regulación puede sostener generación todo el día mientras otra de la cadena modula más.

Un mínimo húmedo/seco o una regla de gestión de agua es una hipótesis si no existe una restricción física documentada. No presentarlo como un límite demostrado por una curva histórica. Explicar internamente cómo se obtuvo el punto elegido y qué parte proviene de datos y qué parte del modelado.

La coherencia con criterios ya aprobados puede ser importante, pero no atribuir a un cálculo una cifra que no produjo. Conservar su trazabilidad real. Las referencias internas entre estudios no tienen que aparecer por nombre en el informe si no corresponden a su alcance.

## Comparaciones y diagnóstico

Cuando un análisis «no calza» con otro archivo, comprobar primero período, versión, unidades, población, agregación, filtros y definición del indicador. Un desacuerdo no demuestra todavía un error metodológico.

Para explicar diferencias entre escenarios, separar observación y causalidad. Si cambian demanda, disponibilidad, límites y BESS a la vez, describir el mecanismo compatible con la evidencia; una atribución numérica exige aislar variables o ejecutar sensibilidades.

Verificar sumas y balances antes de dibujar: conexiones reales por nivel de tensión, signo de BESS, sentidos de flujo, pérdidas y fronteras del agregado. No intentar cerrar el balance de una barra con proyectos conectados a otra tensión. Un esquema puede omitir demandas por alcance, pero entonces no debe sugerir un balance exhaustivo.

En un tramo con pérdidas pequeñas, un único flujo puede ser suficiente para una figura explicativa. Si se discute el balance, conservar ambos terminales o declarar la simplificación. El detalle fuente debe permitir reconstruirlo.

## Salidas reutilizables

Preferir configuración y rutas externas a scripts hardcodeados. Guardar el conjunto exacto usado por las figuras y tablas, junto con metadatos de escenario y versión. No redondear el archivo maestro de cálculo para adaptarlo al informe.

Comprobar coherencia entre gráfico, tabla y texto. Separar resultados reproducidos de resultados inferidos y no anunciar regeneración completa si alguna etapa se mantuvo manual. Los gráficos deben conservar base y unidades, no solo colores atractivos.
