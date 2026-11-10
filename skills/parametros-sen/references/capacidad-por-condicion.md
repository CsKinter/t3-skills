# Capacidad por condición y adecuación de base de datos

Lo aprendido en Cumbres del Ñuble (17-10 a 30-10-2026) sobre qué capacidad limita un elemento en N y en
post-contingencia, y cómo se lleva al modelo. Las cifras de ese estudio no se trasladan.

**Índice**: 1 Reglas · 2 Condensadores serie · 3 Procedimiento · 4 Trampas · 5 Decisiones a cerrar con el usuario.

## 1. Reglas

1. **La capacidad es de cada equipo, no del circuito.** El límite es el mínimo de la cadena serie: conductor,
   interruptor, desconectador, trampa de onda, TTCC y condensador serie, por extremo y por condición. Un valor alto en
   un equipo no le da esa capacidad a la ruta.
2. **Todo valor lleva condición, duración y temperatura.** N o post-contingencia; permanente, 15 o 30 min; 15 SS,
   25 CS o 35 CS. Sin esos tres datos, dos cifras no son comparables.
3. **Criterio usado en Cumbres** (decisión del usuario, a confirmar en cada estudio): capacidad permanente en N;
   capacidad de corta duración en post-contingencia **sólo donde exista dato aplicable** a ese equipo. No se extiende
   por analogía a conductores, transformadores ni a otros equipos del mismo tipo.
4. **El factor de sobrecarga de un tipo de equipo no se traslada a otro.** El 120 % permanente de los TTCC es de los
   TTCC. Si Infotécnica ya entrega la «Sobrecarga permanente» (TAP × factor), no se multiplica otra vez.
5. **Fuentes**: Infotécnica vigente, contrastada con el estudio de restricciones del sistema de transmisión (ERST) y
   sus anexos. El ERST es contraste histórico de su fecha y horizonte: no reemplaza la ficha actual ni autoriza
   extrapolar a equipos futuros.
6. **Un valor heredado del modelo sin documento no es evidencia de capacidad.** Se registra como «origen no
   acreditado». Una coincidencia numérica (1,2 × 1,7 ≈ 2,04) es una conjetura y se rotula así.
7. **Tres decisiones distintas**: la capacidad física, el criterio del estudio y la representación en el modelo.
   Excluir o conservar un límite es una decisión de alcance del usuario, no un cambio de capacidad.
8. **Conversión**: usar la tensión del propio objeto. Un banco con tensión nominal de 525 kV y una línea de 500 kV dan
   MVA distintos para la misma corriente. No comparar MW de un corredor con MVA de un equipo.
9. **Una línea tiene una sola capacidad en PF y dos extremos.** PF compara la mayor corriente de ambos bornes contra
   un límite único, así que un límite que es de un TTCC en un extremo se aplica también al otro. Si la diferencia
   decide, medir en el borne del equipo y decirlo.

## 2. Condensadores serie

**Sí están en Infotécnica** (corrige la versión anterior de esta skill): tipo de instalación «Condensadores Serie»,
ID 22, ruta `condensadores-series`, con fichas generales por equipo
(`…/v1/condensadores-series/<ID>/fichas-tecnicas/general/`). El 30-10-2026 el inventario tenía 22 equipos. `it.py`
todavía no los consulta y escribe `S/I` en la columna CCSS: hay que traerlos aparte.

- Conceptos: «8.3.5 Corriente nominal» y «8.3.6 Límite de sobrecarga admisible de corta duración».
- El enunciado genérico de 8.3.6 dice **15 minutos**. Sólo un texto particular de la ficha («30 min según placa») o un
  respaldo acredita 30 min. El nombre del campo no basta.
- Que un banco no figure en el inventario no prueba que no exista. Se anota «sin ficha».
- Cada fila es un equipo. No hay capacidad conjunta del circuito.
- Si Infotécnica y el ERST difieren en valor o en plazo, no se resuelve por analogía: se pide respaldo y decide el
  usuario.

## 3. Procedimiento de adecuación

1. **Inventario** de la zona de influencia: líneas con su tipo y corriente efectiva, transformadores y **bancos serie**
   (el barrido habitual de líneas y transformadores no los trae).
2. **Identidad física**: cada elemento del modelo a un tramo, sección y paño de Infotécnica, o a una obra futura. Para
   el paño, código completo y subestación. Verificar que el extremo del tramo y el de los equipos sea el mismo.
3. **Existentes**: conductor por sección y condición, y menor equipo de paño de ambos extremos.
4. **Futuros**: plan de expansión, decreto y PGP. Tomar el mínimo de la obra con su temperatura. No extender un
   repotenciamiento a equipos que el documento no incluye. Si el resumen de PGP contradice la descripción técnica,
   manda la descripción.
5. **Tabla esperada** por ruta de PF: fuente, tipo de cambio (tipo, corriente, impedancia, factor, característica) y
   valor esperado.
6. **Aplicar** en variation y stage, sobre copias de biblioteca con etiqueta de trazabilidad, con script de reversión
   que simule por defecto (skill `powerfactory-python`).
7. **Verificar con flujo**: leer la corriente efectiva de cada elemento en cada caso de estudio. Leer la matriz o
   contar triggers no basta.
8. **Barrido N y N-1 a despacho fijo** para ver factibilidad. No reemplaza al ciclo de restricción.
9. **Registro por elemento**: fuente, localización exacta, estado de certificación, valor modelado y diferencia.
   Separar lo confirmado de lo pendiente.

## 4. Trampas

| Trampa | Cómo se detectó |
|---|---|
| Factor de reducción oculto en la línea (`fline` ≠ 1) que infla o reduce la capacidad | Comparando corriente efectiva con la del tipo |
| Curva térmica asignada que no se aplica por falta del trigger de escala | Con flujo en el caso de 25 °C |
| Tipo de línea de otra tensión (tipo de 154 kV sobre barras de 66 kV) | Capacidad en MVA incoherente |
| El caso de 35 °C no era la misma red con otro clima: tenía punteros de tipo distintos | Comparando punteros entre casos |
| Matrices con valores de 15, 25 y 35 °C mezclados: la capacidad crecía con la temperatura | Revisión de monotonía |
| Unidad dudosa en Infotécnica («1,25 [A]» validado) | No se corrige ni se usa: se avisa |
| Paño genérico sin código, que mezcla equipos de varias posiciones | No se usa como mínimo inequívoco |
| `it.py` puede reintroducir TC de bushing si todos los TTCC del paño lo son (`… or eqs`) | Revisar el detalle del paño cuando el mínimo sale de un TTCC |
| Mínimo calculado sólo con TTCC, sin conductor a 35 °C | No es la capacidad de la línea |
| Nombre de archivo de un informe técnico que no corresponde a su contenido | Leer la portada. Jerarquía: preliminar → final → definitivo, más rectificaciones y decreto |
| Tablas del ERST con celdas combinadas: la extracción a texto repite valores | Cotejar las tablas decisivas contra la página renderizada |
| El texto general del ERST generaliza un valor y remite a una sección que no es la del detalle | Ir a la tabla de detalle y sus excepciones |
| Límites de corredor del ERST que mezclan puntos de estabilidad con restricciones adoptadas | Usar la columna de restricción |
| Un barrido con una solución espuria del flujo tomado como hallazgo de capacidad | Es del solver: `powerfactory-python/references/cierre-bd.md` |

## 5. Decisiones a cerrar con el usuario

1. Criterio post-contingencia: permanente, 15 o 30 min, y para qué equipos.
2. Factor de TTCC: ¿se usa la «Sobrecarga permanente» de Infotécnica? ¿Hay capacidad de emergencia?
3. Monitor por extremo o límite único de línea.
4. Temperatura y caso de estudio por escenario.
5. Si se conserva, corrige o excluye un límite heredado de otro estudio.
6. Obras futuras sin respaldo: estándar de obra equivalente (marcado como referencia) o S/I.
7. Discrepancias entre fuentes en equipos que gobiernan: pedir respaldo y decidir caso a caso.
8. Qué se menciona en el informe. La conciliación con otros estudios es interna.
