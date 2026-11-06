# Convierte un WMF exportado por el puente (pf_bridge\files\<Nombre>.wmf.wmf; PF agrega su propia extensión) a PNG.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File wmf2png.ps1 -Nombre foto49 -Ancho 6400 -Salida C:\ruta\fotos
#   -Ancho 3200 basta para ver la forma de una hoja de ~640 mm; 6400 para leer las cifras de las cajas en una hoja de ~1 m.
param(
  [Parameter(Mandatory = $true)][string]$Nombre,
  [int]$Ancho = 3200,
  [string]$Salida = (Join-Path $env:USERPROFILE 'pf_bridge\files')
)
Add-Type -AssemblyName System.Drawing
$src = Join-Path $env:USERPROFILE ('pf_bridge\files\' + $Nombre + '.wmf.wmf')
if (-not (Test-Path $src)) { $src = Join-Path $env:USERPROFILE ('pf_bridge\files\' + $Nombre + '.wmf') }
if (-not (Test-Path $src)) { Write-Error "no existe $src (¿falló la exportación o el puente estaba detenido?)"; exit 1 }
$m = New-Object System.Drawing.Imaging.Metafile($src)
$h = [int]($Ancho * $m.Height / $m.Width)
$b = New-Object System.Drawing.Bitmap($Ancho, $h)
$g = [System.Drawing.Graphics]::FromImage($b)
$g.Clear([System.Drawing.Color]::White)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.DrawImage($m, 0, 0, $Ancho, $h)
New-Item -ItemType Directory -Force $Salida | Out-Null
$dst = Join-Path $Salida ($Nombre + '.png')
$b.Save($dst)
$g.Dispose(); $b.Dispose(); $m.Dispose()
Write-Output $dst
