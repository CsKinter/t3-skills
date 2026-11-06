# Parámetros SEN | líneas, terminales y planificación

Para investigar campos nuevos con tooltips, metadatos y el catálogo API, consultar [descubrimiento de parámetros en PowerFactory](powerfactory-descubrimiento.md). Incluye alternativas de modelado que requieren ensayo en copia antes de adoptarlas.

## Fuentes y vigencia

Esta guía no fija un ranking legal permanente entre siglas. Verificar la serie del plan, contenido, fecha, rectificaciones, documentos definitivos y decretos aplicables. Un nombre de archivo «ITF» o «ITD» no demuestra por sí solo su etapa ni vigencia. La fecha de publicación y la de puesta en servicio son hechos distintos.

Para instalaciones existentes, contrastar la información técnica oficial y su estado. Para obras futuras, reconstruir el alcance con la documentación definitiva disponible, decretos y antecedentes de proyecto pertinentes. Conservar fuente y localización exacta de cada valor. Usar las skills y conectores técnicos disponibles para acceder a fuentes vigentes; esta guía no reemplaza su consulta.

No presentar una fecha proyectada como certeza ni extender un repotenciamiento a equipos que el documento no incluye. Una obra puede cambiar conductor, un tramo o un terminal y dejar otro equipo como limitante.

## Correspondencia física

**Verificación.** Antes de asignar una capacidad a una línea, confirmar subestación, tensión, circuito, tramo, paño, destino y terminal. La proximidad en un plano o la semejanza de nombres no son prueba suficiente. Cuando haya ambigüedad, conservarla como pendiente hasta obtener la conexión exacta.

Descomponer el corredor en circuitos y tramos realmente aplicables. No fusionar dos circuitos con capacidades distintas en una única fila sin conservar su diferencia. Verificar bancos de transformadores y distinguir capacidad por unidad de capacidad del conjunto.

## Capacidad efectiva

La capacidad permanente efectiva de un circuito depende del menor límite aplicable entre conductor, secciones y equipos en serie de ambos extremos, bajo la condición evaluada. Registrar la identidad del equipo limitante, no solo el número final.

Comprobar corriente nominal/permanente de cada equipo, derivación o tap real de TTCC cuando aplique y factores de sobrecarga con su significado correcto. No confundir un factor con corriente admisible ni una capacidad de otro equipo con la del paño que transporta el circuito.

Conservar estados de validación, rechazo, sin información y no aplicable tal como están en la fuente. El tratamiento de cada estado debe seguir el criterio definido y documentado para el estudio. Ausencia de dato no es cero ni confirmación de capacidad ilimitada.

Mantener condiciones ambientales y de cálculo: temperatura, sol/viento, duración y categoría permanente/emergencia. Un valor mínimo futuro informado en una condición no demuestra la curva completa en todas las condiciones. Toda extrapolación requiere una hipótesis identificada.

## Unidades y comprobación en el modelo

Revisar A frente a kA, MW frente a MVA y tensión base. En un sistema trifásico equilibrado, la conversión de referencia es `S[MVA] = sqrt(3) × V[kV] × I[kA]`; esa S no equivale a P salvo que se cumplan las condiciones correspondientes.

Conservar suficiente precisión en corrientes y parámetros para determinar cuál equipo limita. El uso de enteros en la prosa del informe no autoriza redondear a enteros kA o impedancias.

Contrastar valor fuente, valor adoptado y valor del modelo, con razón de la diferencia. Antes de modificar PowerFactory, respaldar tipos y referencias compartidas. Después, releer atributos, ejecutar flujos y revisar contingencias alcanzadas por el cambio. Ver [cálculo](digsilent-calculo.md).

Un resultado inesperado puede provenir de la fuente, correspondencia del paño, condición térmica, solver, modo de control o despacho. No elegir la explicación que produzca el resultado deseado sin comprobar las alternativas.

## Entregable de auditoría

Registrar por elemento: identificador físico, fuente/localización, condición, conductor, terminales, límite efectivo, equipo gobernante, valor modelado, diferencia, decisión y efecto comprobado en resultados.

Separar hallazgos confirmados de pendientes. Usar el formato de [inconsistencias](informe-tablas.md) cuando el usuario pida una síntesis. «Libera despacho» requiere cálculo posterior; una corrección de capacidad por sí sola no lo demuestra.
