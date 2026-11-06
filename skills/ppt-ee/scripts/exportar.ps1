param([string]$pptx, [string]$outdir, [int]$w = 1600, [int]$h = 900)
$pp = New-Object -ComObject PowerPoint.Application
$p = $pp.Presentations.Open($pptx, $true, $false, $false)
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
$n = $p.Slides.Count
for ($i = 1; $i -le $n; $i++) { $p.Slides.Item($i).Export((Join-Path $outdir ("s{0:D2}.png" -f $i)), "PNG", $w, $h) }
$p.Close()
$pp.Quit()
"exportadas $n"
