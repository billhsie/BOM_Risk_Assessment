"""
BOM Writer Script
Generates a color-coded Risk Assessment Excel from JSON assessments.

Usage:
    py bom_writer.py --config config.json [--output output.xlsx]

Config JSON format:
{
  "project": "NVL-S Slate14 MLK",
  "platform_b": "NVL-S RVP (S021)",
  "platform_c": "Customer BOM",
  "output": "NVL-S_BOM_Risk_Assessment.xlsx",
  "rows": [
    {
      "subsystem": "CPU",
      "col_b": "Intel NVL-S SoC",
      "col_c": "",
      "risk": "",
      "risk_level": ""
    },
    ...
  ]
}

risk_level values: "Low", "Medium", "High", "" (pending)
"""

import argparse
import json
import sys
import os
import subprocess
import tempfile
import shutil


# ── PowerShell template ──────────────────────────────────────────────────────

PS_TEMPLATE = r"""
param([string]$configJson, [string]$outPath)

Add-Type -AssemblyName System.IO.Compression.FileSystem

$config = $configJson | ConvertFrom-Json
$rows   = $config.rows

# Colors
$cHeader   = 0x002060   # dark navy
$cBamber   = 0xFFBF00   # amber  (B not in PCL)
$cCgreen   = 0x92D050   # green  (C input area)
$cDgray    = 0xBFBFBF   # gray   (D pending)
$cDlow     = 0x92D050   # green  (Low)
$cDmed     = 0xFFFF00   # yellow (Medium)
$cDhigh    = 0xFF0000   # red    (High)
$cRowEven  = 0xF2F2F2   # light gray alternating
$cRowOdd   = 0xFFFFFF   # white

function bgr([int]$rgb) { return ([int]($rgb -band 0xFF) -shl 16) -bor ([int](($rgb -shr 8) -band 0xFF) -shl 8) -bor (($rgb -shr 16) -band 0xFF) }

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false

$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
$ws.Name = $config.project

# ── Header row ───────────────────────────────────────────────────────────────
$headers = @("Subsystem", "RVP Reference BOM ($($config.platform_b))", "Customer BOM ($($config.platform_c))", "Risk Assessment & Recommendation")
for ($c = 1; $c -le 4; $c++) {
    $cell = $ws.Cells.Item(1, $c)
    $cell.Value2 = $headers[$c-1]
    $cell.Interior.Color = bgr $cHeader
    $cell.Font.Color = bgr 0xFFFFFF
    $cell.Font.Bold = $true
    $cell.Font.Size = 11
    $cell.WrapText = $true
}

# ── Data rows ─────────────────────────────────────────────────────────────────
$r = 2
foreach ($row in $rows) {
    $rowColor = if ($r % 2 -eq 0) { $cRowEven } else { $cRowOdd }

    # A: Subsystem
    $ca = $ws.Cells.Item($r, 1)
    $ca.Value2 = $row.subsystem
    $ca.Interior.Color = bgr $rowColor
    $ca.Font.Bold = $true

    # B: RVP reference
    $cb = $ws.Cells.Item($r, 2)
    $cb.Value2 = $row.col_b
    $cb.WrapText = $true
    if ($row.col_b -match "NOT in") {
        $cb.Interior.Color = bgr $cBamber
    } else {
        $cb.Interior.Color = bgr $rowColor
    }

    # C: Customer BOM
    $cc = $ws.Cells.Item($r, 3)
    $cc.Value2 = $row.col_c
    $cc.WrapText = $true
    if ($row.col_c -eq "" -or $null -eq $row.col_c) {
        $cc.Interior.Color = bgr $cCgreen
        $cc.Font.Italic = $true
        $cc.Font.Color = bgr 0x808080
        $cc.Value2 = "(customer to fill)"
    } else {
        $cc.Interior.Color = bgr $rowColor
    }

    # D: Risk Assessment
    $cd = $ws.Cells.Item($r, 4)
    $cd.Value2 = $row.risk
    $cd.WrapText = $true
    switch ($row.risk_level) {
        "Low"    { $cd.Interior.Color = bgr $cDlow  }
        "Medium" { $cd.Interior.Color = bgr $cDmed  }
        "High"   { $cd.Interior.Color = bgr $cDhigh }
        default  {
            if ($row.subsystem -eq "CPU") {
                $cd.Interior.Color = bgr $rowColor
            } else {
                $cd.Interior.Color = bgr $cDgray
                $cd.Font.Italic = $true
                $cd.Font.Color = bgr 0x595959
                if ($row.risk -eq "") { $cd.Value2 = "Pending" }
            }
        }
    }
    $r++
}

# ── Column widths & row height ────────────────────────────────────────────────
$ws.Columns.Item(1).ColumnWidth = 22
$ws.Columns.Item(2).ColumnWidth = 40
$ws.Columns.Item(3).ColumnWidth = 40
$ws.Columns.Item(4).ColumnWidth = 50
$ws.Rows.Item(1).RowHeight = 30
for ($i = 2; $i -le $r; $i++) { $ws.Rows.Item($i).RowHeight = 45 }

# ── Borders ───────────────────────────────────────────────────────────────────
$used = $ws.Range($ws.Cells.Item(1,1), $ws.Cells.Item($r-1, 4))
$used.Borders.LineStyle = 1
$used.Borders.Weight = 2

# ── Freeze header ─────────────────────────────────────────────────────────────
$ws.Application.ActiveWindow.SplitRow = 1
$ws.Application.ActiveWindow.FreezePanes = $true

# ── Auto-fit and save ─────────────────────────────────────────────────────────
$tmpPath = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "bom_risk_out.xlsx")
$wb.SaveAs($tmpPath, 51)
$wb.Close($false)
$xl.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($xl) | Out-Null

Copy-Item -Path $tmpPath -Destination $outPath -Force
Write-Host "Done: $outPath ($(Get-Item $outPath | Select-Object -ExpandProperty Length) bytes)"
"""


def run_ps_writer(config: dict, output_path: str) -> bool:
    """Execute PowerShell COM writer with the given config dict."""
    config_json = json.dumps(config, ensure_ascii=False)

    ps_path = os.path.join(tempfile.gettempdir(), "bom_writer_gen.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write(PS_TEMPLATE)

    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path,
         "-configJson", config_json, "-outPath", output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ERROR:", result.stderr[:500], file=sys.stderr)
        return False
    print(result.stdout.strip())
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate BOM Risk Assessment Excel")
    parser.add_argument("--config", required=True, help="JSON config file path")
    parser.add_argument("--output", help="Output .xlsx path (overrides config)")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as f:
        config = json.load(f)

    output_path = args.output or config.get("output", "BOM_Risk_Assessment.xlsx")
    output_path = os.path.abspath(output_path)

    ok = run_ps_writer(config, output_path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
