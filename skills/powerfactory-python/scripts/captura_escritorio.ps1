param([string]$Salida = "", [double]$Escala = 1.0)
# Captura de todo el escritorio (todas las pantallas) a PNG, para que Claude vea la GUI de PF u otras ventanas.
# Sólo cuando el usuario lo pide o lo acordó en la sesión: captura todo lo visible en pantalla.
#   & captura_escritorio.ps1                      -> %USERPROFILE%\pf_bridge\capturas\escritorio_<fecha>.png
#   & captura_escritorio.ps1 -Escala 0.6          -> reducida (menos detalle, archivo más liviano)
# Mientras el puente PF corre, la ventana de PF no se repinta: la captura puede mostrar un estado anterior.
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class DpiCaptura { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware(); }
"@
[DpiCaptura]::SetProcessDPIAware() | Out-Null          # coordenadas reales en pantallas con escalado
if (-not $Salida) {
    $dir = Join-Path $env:USERPROFILE "pf_bridge\capturas"
    New-Item -ItemType Directory -Force $dir | Out-Null
    $Salida = Join-Path $dir ("escritorio_{0}.png" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
}
$v = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $v.Width, $v.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($v.Left, $v.Top, 0, 0, $bmp.Size)
$g.Dispose()
if ($Escala -lt 1.0) {
    $w = [int]($v.Width * $Escala); $h = [int]($v.Height * $Escala)
    $chico = New-Object System.Drawing.Bitmap $w, $h
    $g2 = [System.Drawing.Graphics]::FromImage($chico)
    $g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g2.DrawImage($bmp, 0, 0, $w, $h)
    $g2.Dispose(); $bmp.Dispose(); $bmp = $chico
}
$bmp.Save($Salida, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
"{0} ({1}x{2})" -f $Salida, $v.Width, $v.Height
