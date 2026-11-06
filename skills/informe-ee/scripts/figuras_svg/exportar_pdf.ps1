param([string[]]$Docs)
$ErrorActionPreference='Stop'
$app=$null;$doc=$null;$verifiedOwn=$false
$beforeIds=@(Get-Process -Name WINWORD -ErrorAction SilentlyContinue | ForEach-Object Id)
$log=Join-Path $PSScriptRoot 'Render Word.log'
function L([string]$s){"$(Get-Date -Format o) | $s" | Tee-Object -FilePath $log -Append}
try {
 $app=New-Object -ComObject Word.Application
 $new=@(Get-Process -Name WINWORD | Where-Object {$_.Id -notin $beforeIds})
 if($new.Count -ne 1){throw 'No se verificó una instancia propia'}
 $verifiedOwn=$true
 L "Word propio $($new[0].Id) | previos $beforeIds"
 $app.Visible=$false;$app.DisplayAlerts=0
 foreach($d in $Docs){
  $doc=$app.Documents.Open($d,$false,$true,$false)
  $doc.Repaginate()
  L "$([IO.Path]::GetFileName($d)) | $($doc.ComputeStatistics(2)) páginas"
  $doc.ExportAsFixedFormat([IO.Path]::ChangeExtension($d,'.pdf'),17)
  L "$([IO.Path]::GetFileName($d)) | exportado"
  $doc.Close(0);$doc=$null
 }
} finally {
 if($verifiedOwn){if($null -ne $doc){$doc.Close(0)};if($null -ne $app){$app.Quit()};L 'Cerrado Word propio'}
}
