# Conducción del estudio con agentes

Cómo se organizó Cumbres durante un mes de trabajo con varios agentes, qué falló y qué regla lo corrigió. Las plantillas
están en `assets/`. Para costo de delegación ver `usage-conscious-agents`; para revisiones con varios modelos, `council`.

## 1. Carpeta del proyecto

```
<Proyecto>/
  AGENTS.md                  reglas permanentes y mapa (corto: algunos agentes truncan sobre ~32 KB)
  CLAUDE.md                  sólo «@AGENTS.md» y notas propias
  Metodología restricción - <Proyecto>.md
  Orquestación/
    PLAN - <fecha>.md        tablero: decisiones numeradas y bitácora
    PLAN PASO A PASO - <tarea> - <fecha>.md
    HANDOFF - <tema> - <fecha>.md
    PROMPT - <tema>.md       texto de arranque de la sesión siguiente
    <tema>_<ddmm>/           una carpeta por campaña, con su RESULTADO.md
  herramientas/              scripts tal como corrieron, con README
  Respaldos/                 no se lee por rutina
  .revision_informe/         iteraciones del Word, no se lee por rutina
```

**Precedencia**: el archivo más reciente manda. Después el tablero, AGENTS.md, la memoria y por último los HANDOFF
históricos. Si AGENTS.md contradice un archivo más nuevo, se corrige AGENTS.md.

## 2. Reglas

- **Un tablero único.** Decisiones numeradas, sólo de Vicente. Una decisión superada no se borra: la nueva dice a cuál
  sustituye. Cada intervención agrega a la bitácora una entrada corta.
- **Decisión ≠ recomendación.** Lo que propone un agente queda como propuesta hasta que Vicente lo acepte. Las hipótesis
  abiertas tienen su lista y se tachan al descartarse.
- **Un escritor por herramienta.** Los demás leen. El puente de PowerFactory lo inicia quien el proyecto diga.
- **Planes paso a paso ejecutables por otro agente.** Cada paso dice qué hacer, cómo comprobarlo y cuándo detenerse a
  preguntar. Incluyen una tabla de puntos de parada con tolerancias numéricas.
- **Cierre de sesión obligatorio**: entrada en la bitácora, HANDOFF corto y PROMPT de la sesión siguiente, aunque el
  trabajo quede a medias. Las cuotas se agotan a mitad de campaña.
- **Lectura mínima.** El PROMPT nombra dos o tres archivos. AGENTS.md dice qué carpetas no se leen.
- **Vigente frente a superado, por nombre de archivo.** Cada plan lista «fuente de resultados» y «no usar como
  vigentes».
- **Hechos, inferencias y brechas por separado**, en todo documento interno.
- **Hash antes y después** de tocar un Word o una fuente de cálculo.
- **Delegar sólo lecturas independientes**, con brief acotado y entrega de una página. Si un delegado falla por cuota,
  no se relanza por inercia.
- **Los antecedentes no autorizan retomar tareas.** Un pendiente que aparece en un HANDOFF viejo se pregunta antes.
- **Autonomía sin supervisión** (trabajo nocturno): sólo para lo ya aprobado. Nunca para decisiones nuevas.

El reparto de roles entre agentes (quién coordina, quién revisa) se decide en cada estudio según cuotas y carga. En
Cumbres quedó escrito un reparto que en la práctica no se cumplió: escribir el que de verdad se va a usar.

## 3. Qué salió mal

| Problema | Regla que lo corrigió |
|---|---|
| Resultados que circularon y luego no se pudieron reproducir desde sus cambios registrados | Verificación independiente de cada cierre y lista «no usar como vigentes» |
| Los escenarios finales de PowerFactory seguían en un estado viejo y lo nuevo vivía en respaldos | Carpetas oficiales sólo con los finales, promoción explícita y verificación del despacho antes y después |
| Riesgo de pisar ediciones manuales del usuario al regenerar el Word | Partir siempre de su último guardado y respaldarlo |
| HANDOFF de cientos de KB que nadie podía leer | HANDOFF cortos, relevo vigente arriba, los históricos se buscan por sección |
| Decisiones tomadas por el agente sin consultar | Vicente participa en cada decisión nueva |
| Cifras antiguas reutilizadas como vigentes | Identificar equipo, extremo, duración y fecha antes de comparar |
| Una conjetura numérica tratada como origen de un dato | Marcarla como conjetura hasta tener documento |
| Variations y carpetas de trabajo acumuladas en la base de PowerFactory | Variation de sesión con nombre neutro y limpieza al cierre |
| AGENTS.md desfasado respecto de la revisión real del informe | Actualizar AGENTS.md al oficializar |

## 4. Memoria entre sesiones

- La memoria del proyecto se organiza por temas y separa lo vigente de lo «histórico y superado».
- No repite AGENTS.md ni el tablero.
- Lo que resulta general se promueve a las skills (`~/t3-skills`), no se deja en la memoria de un proyecto.

No se midió el consumo de tokens por sesión. Si se quiere optimizar el reparto entre agentes, medirlo desde el inicio.
