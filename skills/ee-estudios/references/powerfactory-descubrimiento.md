# PowerFactory | descubrir parámetros con interfaz y API

Aprendizaje comprobado el 20-10-2026 en PF 2025 SP4. Los nombres y códigos siguientes deben volver a comprobarse si cambia la versión o el modelo. Complementa las guías de cálculo y parámetros; no autoriza una migración de los modelos existentes.

## Método

1. Escoger un objeto real y confirmar ruta, clase y contexto. Visitar elemento, tipo, características y comando de cálculo: no todos los datos pertenecen al elemento.
2. Posicionar el cursor sobre el campo y leer su tooltip, incluida la enumeración. Con Computer Use Windows, se comprobó que `sky.scroll` con scrollX/scrollY cero permite posicionar el cursor sin editar; esperar brevemente y capturar un estado nuevo. Usar las coordenadas y screenshotId de la observación vigente.
3. Registrar etiqueta, nombre interno, unidad, propietario, opciones y versión. Diferenciar tooltip observado, documentación y atributo pendiente de ejecución API.
4. Complementar con `Application.GetAvailableAttributesAsJson(clase, "", 1, "e", "description,unit,data_type,subindex_dimension")`, documentado en PF 2025. Este catálogo de entradas no equivale a valores efectivos del caso ni sustituye la interpretación de los menús.
5. Leer valores y metadatos mediante GetAttribute, GetAttributeDescription, GetAttributeUnit y GetAttributeType, preservando excepciones y datos ausentes. Las unidades devueltas pueden ser las unidades actuales de presentación: no imponer una conversión sin comprobarlas.
6. Antes de escribir, inventariar referencias compartidas. GetReferences omite ocultos por defecto; contemplar variaciones y alcance de la consulta. No recorrer recursivamente todos los proyectos del usuario.

## Correspondencias observadas relevantes

| Clase | Atributo | Significado |
|---|---|---|
| TypLne | sline / InomAir | Corriente nominal; alternativa en aire para la instalación correspondiente |
| TypLne | tmax | Temperatura máxima de operación usada en el modelo de resistencia |
| ElmLne | Inom_a | Corriente nominal actual mostrada en el diálogo; contrastar toda la cadena |
| ElmLne | fline | Factor de reducción |
| ElmLne | Imaxlim | Corriente máxima permisible adicional |
| ElmLne | maxload / Top | Carga máxima configurada / temperatura operativa |
| ElmTr2 | ratfac / Snom_a | Factor de capacidad / potencia nominal actual |
| TypTr2 | nt2ph / strn | Tecnología / potencia nominal del tipo |
| ComLdf | i_power | 0: corriente; 1: potencia clásica, en la instalación observada |
| ComLdf | iopt_tem | Selección de temperatura para resistencia, independiente de la ampacidad ambiental |
| ComLdf | bPlimGenst / bQlimGenst | Inclusión de generadores estáticos en límites P/Q |
| ComLdf | iopt_limScale / iopt_lev | Factor de límites Q / adaptación automática para convergencia |
| IntThrating | iopt_unit / ContRating | Unidad / límite continuo |
| IntThrating | optTa / optWind / optSolar | Dependencias ambientales |
| IntThrating | table_valid | Habilitación de límites de corta duración |
| TypLne | for_name / dat_src / appr_status | Clave externa / procedencia / aprobación interna |

La aprobación interna de PF no es certificación de una fuente oficial. No sobrescribir claves externas o CIM existentes para añadir trazabilidad propia. Una fecha de commissioning cercana a la época Unix puede ser un valor por defecto: verificar el dato bruto y su significado.

## Oportunidades de implementación que requieren ensayo

La referencia técnica de líneas PF 2025 documenta que Imaxlim acota la corriente nominal para calcular la carga, considerando el número de líneas paralelas. Puede ser una vía para representar equipos limitantes del circuito conservando el tipo de conductor. Comprobar correspondencia física, condición, factores, ambos extremos y efecto real antes de aplicarla.

El objeto nativo IntThrating permite ratings continuos y temporales, con dependencias ambientales. Verificar vínculo pRating, unidad, estación meteorológica, valores por defecto y regla de selección. En PF 2025, los valores ambientales de ese objeto no se interpolan como una curva continua. Cambiar la unidad no convierte sus números; fline no se aplica como en la formulación sin objeto térmico. No copiar estas condiciones a otra versión sin consulta.

## Evitar conclusiones falsas

- Un nombre de tipo puede contener una tensión antigua; prevalecen parámetros y terminales verificados.
- Un panel de características vacío del elemento no demuestra que su tipo no tenga características.
- El ComLdf abierto desde la barra puede ser distinto de la copia que usa el script. Identificar todos por ruta, no solo por clase.
- Un valor presente en el esquema no prueba que esté soportado o activo en cada objeto.
- Una lectura de resultados no reemplaza un flujo nuevo ni demuestra que corresponda al comando inspeccionado.
- Una alternativa de modelado no demuestra liberación de despacho hasta recalcular.

Consultar la documentación local de la misma instalación: PythonReference, TechRef_OverheadLineModels, TechRef_ThermalRatings y la referencia del transformador correspondiente. Conservar el catálogo de evidencia y las pruebas del proyecto sin promover sus valores particulares a una regla general.
