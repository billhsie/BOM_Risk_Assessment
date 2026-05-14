# Convert PCL PDF -> plain text using Word COM (no external dependencies).
# Usage: powershell -File pdf_to_text.ps1 -PdfPath "<file.pdf>" -TxtPath "<file.txt>"
param(
    [Parameter(Mandatory=$true)][string]$PdfPath,
    [Parameter(Mandatory=$true)][string]$TxtPath
)
$ErrorActionPreference = 'Stop'
if (Test-Path $TxtPath) { Remove-Item $TxtPath -Force }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open([ref]$PdfPath, [ref]$false, [ref]$true, [ref]$false, [ref]"", [ref]"", [ref]$false, [ref]"", [ref]"", [ref]0)
    $doc.SaveAs2([ref]$TxtPath, [ref]2)   # wdFormatText
    $doc.Close([ref]$false)
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Host "Text saved: $TxtPath"
