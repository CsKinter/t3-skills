# t3-skills — shared skills across all T3 Code environments

One source of truth for every machine. OpenCode discovers `skills/` via the `skills` array in `opencode.json`, so a single `git pull` syncs all environments in one go.

## Install on any machine (Mac / Windows)

```bash
git clone https://github.com/CsKinter/t3-skills.git ~/t3-skills
```

Then add to global `opencode.json` (`~/.config/opencode/opencode.json` or `%USERPROFILE%\.config\opencode\opencode.json`):

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": ["~/t3-skills/skills"]
}
```

Merge with existing config — keep your `mcp` section. Reload with `/reload`.

## Add a skill everywhere

```bash
cp -R ~/.config/opencode/skills/my-skill ~/t3-skills/skills/
cd ~/t3-skills && git add skills/my-skill && git commit -m "add my-skill" && git push
# on every other machine:
cd ~/t3-skills && git pull
```

## Contents

- `skills/mercadolibre-api/` — MercadoLibre search + AI ranking for deal bots (Telegram/WhatsApp).
- `skills/delegar-subagentes/` — living protocol for delegating to subagents (routing scorecard, briefs, verification, lessons); built on the ViQSilent RMS work.
