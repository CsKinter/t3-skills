# Plantillas de relevo

Dos documentos que se dejan al cerrar una sesión, aunque el trabajo quede a medias.

---

## HANDOFF - <tema> - <dd-mm-aaaa>.md

Corto. Si hay varios relevos sobre el mismo tema, van en un solo archivo, numerados y con el vigente arriba.

```markdown
# HANDOFF | <tema> | <dd-mm-aaaa>

Punto de entrada vigente. Alcance acordado: <una frase>.

## Abrir primero
- <3 a 5 rutas>
- No leer: <…>

## Estado comprobado
- <archivo o escenario> | <estado> | <hash corto si es Word o fuente de cálculo>
- Procesos que quedan corriendo: <ninguno / cuál>

## Decisiones del usuario
- <N° del tablero y una línea>

## Pendientes, en orden
1. <siguiente paso exacto>

## Límites
- No tocar: <…>
- Requiere «dale»: <…>

## Lecciones
- <trampas que costaron tiempo en esta sesión>
```

---

## PROMPT - <tema>.md

Texto para pegar al abrir la sesión siguiente.

```text
Continúa <estudio>, como <rol>. Lee sólo: AGENTS.md, las decisiones <N–M> y la Bitácora del PLAN, y <HANDOFF>.
Objetivo: <una frase>. Ejecuta desde la primera fase no terminada en la Bitácora.
Fuentes vigentes: <rutas>. No usar: <rutas superadas>.
No mezclar: <cifras o conceptos que se confunden>.
Ya autorizado: <lecturas, cálculos en copia>. Requiere «dale»: <modificaciones en PF / Word / oficial>.
Si una comprobación supera <tolerancia>, detente y pregunta.
Registra avances en la Bitácora (≤ 10 líneas). Al cerrar: HANDOFF y PROMPT nuevos.
```
