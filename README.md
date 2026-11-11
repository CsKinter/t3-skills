# t3-skills

Fuente única de las skills de Vicente para todos los agentes (T3 Code / OpenCode, Claude Code, Codex) y todos los
equipos. Se edita aquí, se confirma en git y los demás entornos lo ven por enlaces.

## Instalar en un equipo

```bash
git clone https://github.com/CsKinter/t3-skills.git ~/t3-skills
```

**OpenCode / T3 Code**: agregar al `opencode.json` global (`~/.config/opencode/opencode.json`), conservando el resto
de la configuración, y recargar con `/reload`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["~/t3-skills/skills"]
}
```

**Claude Code y Codex (Windows)**: crear los enlaces de cada skill en `~/.claude/skills`, `~/.codex/skills` y
`~/.claude_work/skills`:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\t3-skills\instalar.ps1"
```

Se puede repetir. Los enlaces existentes se rehacen y las carpetas reales que encuentre se mueven a
`~/.claude/skills_backups/`, nunca se borran. Volver a correrlo después de agregar una skill nueva.

## Trabajar

```bash
cd ~/t3-skills && git pull          # antes de empezar en otro equipo
# editar skills/<nombre>/...
git add -A && git commit -m "<qué cambió>" && git push
```

No editar las skills desde `~/.claude/skills` pensando que es otra copia: es la misma carpeta.

## Contenido

Estudios eléctricos:

- `estudio-restricciones/` — conducción de un estudio de restricciones de principio a fin: fases, decisiones
  iniciales, ciclo, BESS e híbridos, sensibilidades, informe, plantillas de proyecto.
- `powerfactory-python/` — scripts y puente para DIgSILENT PowerFactory, receta de cálculo y cierre de la base de datos.
- `parametros-sen/` — capacidades y parámetros de instalaciones (Infotécnica, plan de expansión, PGP).
- `proyectos-aa-seia/` — qué es realmente un proyecto: Acceso Abierto, SEIA, CNE.
- `informe-ee/` — edición de informes Word de EE, figuras, revisiones y oficialización.
- `redaccion/` — estilo de redacción de Vicente.
- `ppt-ee/` — presentaciones con la plantilla de EE.
- `ee-estudios/` — preferencias de presentación y de trabajo en estudios eléctricos.

Trabajo con agentes:

- `council/` — revisión con varios modelos.
- `usage-conscious-agents/` — delegación con bajo consumo de tokens.
- `delegar-subagentes/` — protocolo vivo para delegar en subagentes (scorecard de ruteo, encargos, verificación, lecciones);
  nacido del trabajo RMS de ViQSilent.

Otros:

- `mercadolibre-api/` — búsqueda y ranking en MercadoLibre para bots.
