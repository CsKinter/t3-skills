# Enlaza cada skill de este repositorio en los entornos de agentes del equipo (Claude Code, Codex, .claude_work).
# Uso:  powershell -ExecutionPolicy Bypass -File "$HOME\t3-skills\instalar.ps1"
# Es seguro repetirlo: los enlaces existentes se rehacen y las carpetas reales se mueven a un respaldo, nunca se borran.
# OpenCode / T3 Code no necesitan enlaces: leen `skills/` desde opencode.json (ver README).

$ErrorActionPreference = 'Stop'
$repo = Join-Path $PSScriptRoot 'skills'
$respaldo = Join-Path $HOME (".claude\skills_backups\pre-enlace-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$entornos = [ordered]@{
  claude      = Join-Path $HOME '.claude\skills'
  codex       = Join-Path $HOME '.codex\skills'
  claude_work = Join-Path $HOME '.claude_work\skills'
}

foreach ($nombre in $entornos.Keys) {
  $base = $entornos[$nombre]
  # Sólo se instala en los entornos que existen en este equipo.
  if (-not (Test-Path -LiteralPath (Split-Path $base -Parent))) { "$nombre : no instalado, se omite"; continue }
  New-Item -ItemType Directory -Force $base | Out-Null
  foreach ($skill in Get-ChildItem $repo -Directory) {
    $destino = Join-Path $base $skill.Name
    if (Test-Path -LiteralPath $destino) {
      $item = Get-Item -LiteralPath $destino -Force
      if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        [IO.Directory]::Delete($destino)          # quita sólo el enlace, no su contenido
      } else {
        $dir = Join-Path $respaldo $nombre
        New-Item -ItemType Directory -Force $dir | Out-Null
        Move-Item -LiteralPath $destino -Destination (Join-Path $dir $skill.Name)
        "$nombre\$($skill.Name) : carpeta real movida a $dir"
      }
    }
    New-Item -ItemType Junction -Path $destino -Target $skill.FullName | Out-Null
    "$nombre\$($skill.Name) : enlazada"
  }
}
