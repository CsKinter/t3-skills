---
name: ee-estudios
description: Criterios y preferencias de trabajo de Vicen para estudios eléctricos e informes de restricciones. Usar al redactar o revisar informes, figuras, tablas, referencias de Word, diagramas y cálculos de PowerFactory, análisis de datos o auditorías de parámetros del SEN. Aplicar solo los módulos pertinentes; distinguir preferencias editoriales de verificaciones técnicas y supuestos propios de cada estudio.
---

# Estudios eléctricos | conocimiento reutilizable

Esta skill reúne aprendizajes de trabajo con el usuario. Complementa las skills de herramientas disponibles; no sustituye su documentación ni convierte decisiones de un proyecto en reglas para todos.

## Seleccionar módulos

Leer solamente los módulos necesarios para la tarea. En cambios mixtos, combinar los pertinentes.

| Tarea | Módulo |
|---|---|
| Prosa, resumen ejecutivo, conclusiones, estructura | [Informe \| redacción](references/informe-redaccion.md) |
| Figuras, diagramas explicativos, gráficos y composición de páginas | [Informe \| visual](references/informe-visual.md) |
| Tablas de escenarios, resultados, síntesis y anexos | [Informe \| tablas](references/informe-tablas.md) |
| Preservar Word, campos, referencias cruzadas y publicación | [Informe \| Word](references/informe-word.md) |
| Ordenar unilineales nativos y revisar solapes | [DIgSILENT \| diagramas](references/digsilent-diagramas.md) |
| Flujos, contingencias, restricciones y topologías | [DIgSILENT \| cálculo](references/digsilent-calculo.md) |
| Series históricas, recursos, hidráulicas y trazabilidad | [Análisis de datos](references/analisis-datos.md) |
| Capacidades térmicas, paños, repotenciamientos y planificación | [Parámetros SEN](references/parametros-sen.md) |

## Interpretar correctamente las reglas

- **Preferencia:** forma habitual de escribir o presentar del usuario; aplicarla salvo instrucción actual distinta.
- **Verificación:** comprobación necesaria para sustentar una afirmación o un resultado; no reemplazarla por una preferencia estética.
- **Configuración del estudio:** horizonte, escenarios, criterios de participación, margen térmico, estrategia de restricción, paleta, alcance y fuentes. Recuperarla del proyecto; no inventarla ni copiarla de otro estudio.

La instrucción actual del usuario prevalece sobre preferencias históricas. Consultar el HANDOFF y los archivos vigentes del proyecto antes de usar scripts antiguos. Conservar una copia previa y trabajar sobre la última versión editada por el usuario.

## Secuencia común

1. Identificar el entregable vigente, el alcance autorizado y sus fuentes.
2. Separar lo comprobado de lo inferido y de lo que todavía necesita datos.
3. Aplicar cambios localizados y conservar la trazabilidad de resultados y supuestos.
4. Verificar el producto en su representación real: Word/PDF renderizado o PowerFactory con flujo corrido, según corresponda.
5. Informar cambios materiales, evidencia y límites concretos. Evitar listas de comprobaciones que no aporten al cliente.

## Límites de transferencia

No trasladar despachos, códigos de contingencia, rutas, fechas de entrada, controles de generación, umbrales de participación ni valores térmicos entre proyectos. Los estudios anteriores sirven como referencia interna de estilo o método; una cifra requiere su propia fuente y su justificación. No atribuir al Coordinador decisiones particulares del modelado.

Cuando aparezca un aprendizaje nuevo, actualizar el módulo correspondiente. Registrar las excepciones en el proyecto y promoverlas a esta skill solo si el usuario las confirma como generales. Mantener una única copia activa entre agentes cuando la instalación lo permita.

## Referencias técnicas de consulta

- [PowerFactory | parámetros confirmados](references/parametros-confirmados.md): campos cuyo significado tiene evidencia; no es una lista de valores recomendados.
- [PowerFactory | gráficas y diagramas](references/powerfactory-graficos.md): controles observados, exportación SVG probada y API documentada, con sus límites de verificación.
