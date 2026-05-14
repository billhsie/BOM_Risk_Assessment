param(
    [string]$JsonPath = "$env:TEMP\bom_b_filled.json",
    [string]$OutDir = "c:\Users\billhsie\OneDrive - Intel Corporation\Desktop\DATA\TOOL\AI_VB\BOM_risk"
)

$ErrorActionPreference = 'Stop'

$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$outFileName = "NVL-S_BOM_Risk_Assessment_$ts.xlsx"
$tempPath  = Join-Path $env:TEMP $outFileName
$finalPath = Join-Path $OutDir $outFileName

$payload = Get-Content -Path $JsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$rows = $payload.rows
$headerB = $payload.header_b
$headerC = $payload.header_c

function RGB($r,$g,$b) { return [int]($b * 65536 + $g * 256 + $r) }
$cHdrA   = RGB 31  56  100
$cHdrBC  = RGB 46  74  122
$cHdrD   = RGB 139 0   0
$cEven   = RGB 220 230 241
$cOdd    = RGB 255 255 255

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
$ws.Name = "NVL-S BOM Risk"

function WriteCell($row, $col, $value, $bgColor, $fontColor=0, $bold=$false) {
    $cell = $ws.Cells.Item($row, $col)
    $cell.Value2 = $value
    $cell.Interior.Color = $bgColor
    $cell.Font.Color = $fontColor
    $cell.Font.Bold = $bold
    $cell.Font.Name = 'Calibri'
    $cell.Font.Size = 10
    $cell.WrapText = $true
    $cell.VerticalAlignment = -4108
    $cell.Borders.LineStyle = 1
    $cell.Borders.Weight = 2
}

WriteCell 1 1 "Subsystem"                          $cHdrA  16777215 $true
WriteCell 1 2 $headerB                             $cHdrBC 16777215 $true
WriteCell 1 3 $headerC                             $cHdrBC 16777215 $true
WriteCell 1 4 "Risk Assessment & Recommendation"   $cHdrD  16777215 $true

$ws.Rows.Item(1).RowHeight = 50
foreach ($col in 1..4) { $ws.Cells.Item(1, $col).HorizontalAlignment = -4108 }

$r = 2
foreach ($entry in $rows) {
    $rowBg = if ($r % 2 -eq 0) { $cEven } else { $cOdd }
    WriteCell $r 1 $entry.A $rowBg 0 $true
    WriteCell $r 2 $entry.B $rowBg
    WriteCell $r 3 $entry.C $rowBg
    WriteCell $r 4 $entry.D $rowBg
    $r++
}

$ws.Columns.Item(1).ColumnWidth = 32
$ws.Columns.Item(2).ColumnWidth = 55
$ws.Columns.Item(3).ColumnWidth = 55
$ws.Columns.Item(4).ColumnWidth = 45
$ws.Rows.AutoFit() | Out-Null

$ws.Application.ActiveWindow.SplitRow = 1
$ws.Application.ActiveWindow.FreezePanes = $true

$wb.SaveAs($tempPath, 51)
$wb.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null

Copy-Item -Path $tempPath -Destination $finalPath -Force
Write-Host "Generated: $finalPath"
