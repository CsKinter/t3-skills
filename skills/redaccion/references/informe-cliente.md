# Informes para clientes de EE

Convenciones de los estudios de restricciones, flujos y contingencias. Complementan el núcleo de `SKILL.md`.
Formato Word, tablas y figuras: `informe-ee`.

## Resultado, no proceso

- El informe presenta resultados y su explicación física. No menciona desafíos de cálculo, límites de P/Q,
  convergencia ni iteraciones del solver. Nunca escribe «no converge». La secuencia se cuenta en prosa («primero…,
  luego…, una vez despejado…»), sin títulos «Iteración k».
- Sin rótulos internos (S1, `_revisar`, ComLdf, nombres de variations, slack, balance) ni marcas «[En elaboración]».
- No cita otros estudios para justificar hipótesis o resultados. Sirven como referencia interna de estilo, no como
  evidencia.
- En la prosa va el nombre completo del proyecto con su prefijo («PE Cumbres del Ñuble»). La forma breve queda para
  figuras, tablas y rótulos con poco espacio.

## Cifras

- MW y % enteros en la presentación, con la precisión completa en datos y cálculos. Calcula las diferencias antes
  de redondear. Coma decimal, «< 1 %» para lo despreciable y signo «−».
- % en las tablas, MW en la prosa. Todo porcentaje tiene un denominador identificable, sea capacidad instalada,
  recurso disponible, despacho base o capacidad del elemento.
- El redondeo nunca borra una diferencia que decide. 41 y 45 MW no son intercambiables, ni 99 % y 101 %.
- Mayor restricción no es lo mismo que menor despacho admisible. Mantén «restricción» para el ajuste exigido por la
  red y «despacho admisible» para el punto comprobado.
- Si varias condiciones cambian a la vez (demanda, recurso, BESS), describe su efecto conjunto. No atribuyas MW a una
  sola variable sin una comparación que la aísle.

## Alcance con naturalidad

- Los resultados valen para las topologías, escenarios, obras y contingencias evaluados. Dilo una vez por bloque, sin
  repetir salvedades en cada párrafo ni sumar advertencias genéricas.
- «Ninguna de las alternativas evaluadas mejora…», no «la mejor topología». El despacho de un escenario no es un
  límite permanente de la red ni una consigna futura del CEN.
- Criterio y referencia normativa van integrados, con atribución correcta. Evita «esto lo decidimos nosotros» y no
  atribuyas al Coordinador lo que su fuente no dice.
- Cuando un resultado depende de un supuesto (recurso, proyección), dilo junto al resultado y explica qué pasaría si
  cambiara.

## Hilo del informe

- **Resumen ejecutivo.** Lectura continua, sin subtítulos internos ni rótulos que lo fragmenten. Cierra con un punteo
  breve de conclusiones principales.
- **Desarrollo.** Primero la condición evaluada, luego el mecanismo limitante y después la restricción y su
  consecuencia para el proyecto. El contexto va antes del punto de partida que justifica, sin adelantar el desenlace.
- **Casos equivalentes.** Usan la misma plantilla. Por ejemplo, cada escenario con «Condición sin restricción»,
  «Contingencia crítica», «Restricción aplicada» y «Resultado».
- **Sensibilidades.** Di qué pregunta prueba cada cambio y compara su beneficio para el proyecto contra la base.
- **Conclusiones.** Abren con el resultado principal, se agrupan por tema y siguen el orden causa, resultado e
  implicación. Las viñetas llevan afirmaciones completas, sin titular en negrita. No repiten la cronología del trabajo.
- Distingue la ausencia de restricción del proyecto de la ausencia de restricciones en la zona.
- Listas nativas de Word con una frase que las introduce. Numeradas para secuencias, viñetas para elementos paralelos.

## Tablas y figuras en la prosa

- Antes de la tabla, una frase que diga qué compara y en qué unidad. Después, la lectura que el lector debe retener,
  con los contrastes entre grupos. No enumeres cada celda.
- Ninguna página dominada por figuras o tablas sin texto que las interprete.
- Un pie de figura que muestra una sensibilidad explica cómo leerla con un caso concreto. Por ejemplo: «Es decir,
  reducir 100 MW del proyecto disminuye en 7 pp la carga de CS3 ante CT12».

## Búsqueda final

Busca en todo el documento «iteración», «no converge», «S1», «_revisar», «[», «;» y «·», y corrígelos.
