param([string]$Src, [string]$Ops, [string]$Out)
# Aplica con Excel (COM) una lista de cambios JSON y guarda una COPIA; conserva lo que openpyxl perderia
# (comentarios encadenados, customXml, complementos). Uso:
#   & excel_com.ps1 -Src original.xlsx -Ops cambios.json -Out copia.xlsx
# Operaciones (en orden; ver references/excel.md):
#   {"op":"set","sh":hoja,"r":fila,"c":col,"v":valor|null,"fill":"RRGGBB"|"none","bold":b,"italic":b,"color":"RRGGBB","nf":"0.000","h":"center|left"}
#   {"op":"insert","sh":hoja,"a":fila_ini,"b":fila_fin}            inserta filas completas
#   {"op":"copyfmt","sh":hoja,"src":fila,"dst":fila,"n":k}          copia formato (incl. combinadas) de k filas
#   {"op":"merge"|"unmerge_clear","sh":hoja,"rng":"A1:B2"}   {"op":"colw","sh":hoja,"col":"A","w":12}
# Numeros: se escriben con .Formula en cultura invariante (Value2 con Double falla por COM). Texto que empieza con "=" queda como formula.
function Bgr($hex) { $r = [Convert]::ToInt32($hex.Substring(0,2),16); $g = [Convert]::ToInt32($hex.Substring(2,2),16); $b = [Convert]::ToInt32($hex.Substring(4,2),16); return $r + 256*$g + 65536*$b }
$cambios = ConvertFrom-Json (Get-Content -Raw -Encoding UTF8 $Ops)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
    $wb = $xl.Workbooks.Open($Src, 0, $false)
    $map = @{}; foreach ($w in $wb.Worksheets) { $map[$w.Name] = $w }
    $n = 0
    foreach ($o in $cambios) {
        $ws = $map[[string]$o.sh]
        switch ($o.op) {
            "set" {
                $cel = $ws.Cells.Item([int]$o.r, [int]$o.c)
                if ($o.v -ne $null) { $val = $o.v; if ($val -is [string]) { $cel.Value2 = [string]$val } else { $cel.Formula = ([double]$val).ToString([System.Globalization.CultureInfo]::InvariantCulture) } }
                if ($o.fill -eq "none") { $cel.Interior.Pattern = -4142 }
                elseif ($o.fill) { $cel.Interior.Pattern = 1; $cel.Interior.Color = (Bgr $o.fill) }
                if ($o.bold -ne $null) { $cel.Font.Bold = [bool]$o.bold }
                if ($o.italic -ne $null) { $cel.Font.Italic = [bool]$o.italic }
                if ($o.color) { $cel.Font.Color = (Bgr $o.color) }
                if ($o.nf) { $cel.NumberFormat = $o.nf }
                if ($o.h -eq "center") { $cel.HorizontalAlignment = -4108 } elseif ($o.h -eq "left") { $cel.HorizontalAlignment = -4131 }
            }
            "unmerge_clear" { $rg = $ws.Range($o.rng); $rg.UnMerge(); $rg.Clear() }
            "merge" { $ws.Range($o.rng).Merge() }
            "copyfmt" { $k = 1; if ($o.n) { $k = [int]$o.n }; $s0 = [int]$o.src; $d0 = [int]$o.dst
                        $ws.Range("A$($s0):A$($s0 + $k - 1)").EntireRow.Copy() | Out-Null
                        $ws.Range("A$($d0):A$($d0 + $k - 1)").EntireRow.PasteSpecial(-4122) | Out-Null }
            "insert" { $ws.Range("A$([int]$o.a):A$([int]$o.b)").EntireRow.Insert() | Out-Null }
            "colw" { $ws.Columns.Item($o.col).ColumnWidth = [double]$o.w }
        }
        $n++
    }
    $wb.SaveAs($Out, 51)
    $wb.Close($false)
    "Cambios aplicados: $n"
} finally { $xl.Quit() }








