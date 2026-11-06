# Abre un .docx en Word (oculto), actualiza todos los campos (también los de las leyendas dentro de grupos), índices y
# tablas de figuras, guarda y exporta a PDF. Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File render_docx.ps1 -Docx C:\ruta\informe.docx [-Pdf C:\ruta\informe.pdf] [-SoloLectura]
# -SoloLectura: abre sin guardar (para mirar la versión del usuario sin tocarla); igual exporta el PDF.
param(
  [Parameter(Mandatory = $true)][string]$Docx,
  [string]$Pdf = ([System.IO.Path]::ChangeExtension($Docx, '.pdf')),
  [switch]$SoloLectura
)
$w = New-Object -ComObject Word.Application
$w.Visible = $false; $w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($Docx, $false, [bool]$SoloLectura)
  foreach ($st in $d.StoryRanges) { $r = $st; while ($r -ne $null) { $null = $r.Fields.Update(); $r = $r.NextStoryRange } }
  # campos de leyendas dentro de grupos (Fields.Update del documento no los alcanza)
  foreach ($s in $d.Shapes) {
    try { foreach ($gi in $s.GroupItems) { try { $null = $gi.TextFrame.TextRange.Fields.Update() } catch {} } } catch {}
    try { $null = $s.TextFrame.TextRange.Fields.Update() } catch {}
  }
  foreach ($t in $d.TablesOfContents) { $t.Update() }
  foreach ($t in $d.TablesOfFigures) { $t.Update() }
  if (-not $SoloLectura) { $d.Save() }
  $d.ExportAsFixedFormat($Pdf, 17)
  $d.Close(0)
} finally { $w.Quit() }
Write-Output $Pdf
