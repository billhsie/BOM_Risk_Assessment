---
name: bom-risk
description: "BOM Risk Assessment skill. Use when user asks to: perform BOM risk assessment, generate platform migration risk report, compare RVP BOM against PCL, fill B column from PCL, or produce timestamped color-coded Low/Medium/High Excel for any Intel client platform (ARL/NVL/PTL etc)."
argument-hint: "platform name and PCL/BOM file paths"
---

# BOM Risk Assessment Skill

Automates platform-migration BOM review by cross-validating RVP BOM against the Platform Component List (PCL).

| Step | Manual | With This Skill |
|------|--------|-----------------|
| Filter ICs from RVP BOM (~1700 rows) | 2–3 hr | < 1 min |
| Look up each IC against PCL PDF | 1–2 hr | < 1 min |
| Fill B column with PCL reference parts | 1 hr | Automatic |
| Risk-rate Column D + color-code | 1–2 hr | Automatic |
| **Total** | **~6 hr** | **~10 min** |

## When to Invoke

Trigger on phrases like:
- "do BOM risk assessment", "BOM risk", "platform migration risk"
- "fill B column from PCL", "compare old vs new platform BOM"
- "which components are on the PCL"
- "generate risk Excel for <platform>"

## Inputs

| Input | Description | Required |
|-------|-------------|----------|
| Platform target | e.g. `NVL-S`, `PTL-H`, `ARL-U` | Yes |
| PCL PDF | e.g. `870781_NVL_DT_Mobile_PCL_Rev0p7.pdf` | Yes |
| BOM template (xlsx) | Subsystem list in Column A | Yes |
| Customer BOM (Col C) | Filled by customer between Phase 1 and Phase 2 | For D column |

## Output

Excel file named `<Platform>_BOM_Risk_Assessment_YYYYMMDD_HHMMSS.xlsx` (timestamped — never overwrites).

| Col | Content | Filled By |
|-----|---------|-----------|
| A | Subsystem (from template) | Template |
| B | RVP Reference BOM — `Vendor PartNumber (Device Category) [PCL Remarks]` | **AI (Phase 1)** |
| C | Customer BOM | Customer |
| D | Risk: Low / Medium / High + reason | **AI (Phase 2)** |

Color coding (Column D background):
- 🟢 `#92D050` Low · 🟡 `#FFFF00` Medium · 🔴 `#C00000` High

---

## Procedure

### Phase 1 — Build Column B from PCL

**Step 1: Convert PCL PDF → text**

```powershell
powershell -File scripts/pdf_to_text.ps1 `
    -PdfPath "<PCL.pdf>" `
    -TxtPath "$env:TEMP\pcl_text.txt"
```

**Step 2: Parse PCL into structured entries**

```powershell
py scripts/parse_pcl.py
```

Output: `$env:TEMP\pcl_entries.json` — array of  
`{ sn, subsystem, device_category, vendor, part_number, remarks }`

The PCL table columns extracted: **S/N · Sub System · Device Category · Vendor · Part Number · PCL Remarks**.

**Step 3: Map subsystems → PCL entries**

```powershell
py scripts/fill_b_column.py
```

Mapping rules (see [scripts/fill_b_column.py](./scripts/fill_b_column.py)):

| Subsystem | PCL Source |
|-----------|------------|
| CPU | User input (PCL doesn't list CPU) |
| TBT Re-timer | All entries with Device Category = `TBT Retimer` |
| HDMI2.1 Re-driver | Device Category = `HDMI Retimer` |
| Single eUSB2 re-driver | Part Number contains `PTN3222` |
| Dual eUSB2 re-driver | Part Number contains `TUSB2E22` |
| IMVP9.3 | Device Category = `IMVP` |
| VNNAON | Device Category = `Voltage Regulator` |
| USB Type-C PD controller | Device Category contains `PD Controller` |
| Embedded Controller | Device Category = `Embedded Controller` |
| Audio Codec | Device Category = `Audio Codec` |
| TPM | Device Category = `Discrete TPM` |
| LAN Controller | Device Category = `Ethernet Controller` |
| USB3 re-driver | `USB Redriver/Retimer` (excluding eUSB2) |
| Accelerometer / IMU / Magnetometer / SAR | Sensor Device Category match |
| Charger | Device Category = `Charger` |
| Memory | "Refer to Platform Memory Enablement Guide (RDC#…)" |
| **Anything else not in PCL** | **`NA` (do NOT guess)** |

**Cell format:** `Vendor PartNumber (Device Category) [PCL Remarks]`  
Multiple parts joined by newline. `[PCL Remarks]` only added if non-empty (used for platform applicability like `For PTL-UH platform` or `For NVL-S, Hx, HU, AX, AM`).

**Step 4: Generate timestamped Excel**

```powershell
powershell -File scripts/gen_bom_b.ps1
```

Produces `<Platform>_BOM_Risk_Assessment_YYYYMMDD_HHMMSS.xlsx`.

---

### Phase 2 — Risk Assessment (after Customer Returns Column C)

For each row, classify Column D risk:

| Customer Part (C) vs PCL | Risk | D-cell text |
|--------------------------|:----:|-------------|
| C in PCL as iPoR | 🟢 Low | `Low: on PCL Rev0.7 (iPoR)` |
| C in PCL as ECO / Open Lab / iPoC | 🟢 Low | `Low: on PCL (ECO category)` |
| C == B (same as RVP) | 🟢 Low | `Low: Co-using with RVP` |
| C not in PCL but established (proven silicon) | 🟡 Medium | `Medium: not on PCL, OEM validation needed` |
| C is security-critical AND not in PCL | 🔴 High | `High: security-critical, not on PCL` |
| C is brand-new with no validation data | 🔴 High | `High: no validation evidence` |

**Always check `PCL Remarks` column for platform-specific parts:**  
e.g. `For NVL-UL` ≠ applicable to NVL-S.

Full rules: [references/risk_criteria.md](./references/risk_criteria.md)

---

## Verification Policy (CRITICAL — do not violate)

1. **Never fabricate part numbers.** If a subsystem has no matching PCL entry, write `NA`. Customer will fill via Column C.
2. **Always include Device Category** after the part number so reviewers can verify.
3. **Always include PCL Remarks** in `[ ]` when present — these mark platform applicability.
4. **Filename must include timestamp** (`YYYYMMDD_HHMMSS`) — never overwrite previous reports.

---

## Files Provided by This Skill

| File | Purpose |
|------|---------|
| [scripts/pdf_to_text.ps1](./scripts/pdf_to_text.ps1) | PDF → text via Word COM (no external deps) |
| [scripts/parse_pcl.py](./scripts/parse_pcl.py) | Parse PCL text into structured JSON entries |
| [scripts/fill_b_column.py](./scripts/fill_b_column.py) | Map subsystems → PCL entries, build Column B |
| [scripts/gen_bom_b.ps1](./scripts/gen_bom_b.ps1) | Generate Slate14-style timestamped Excel |
| [scripts/bom_reader.py](./scripts/bom_reader.py) | (Optional) Read raw RVP BOM xlsx for IC extraction |
| [scripts/bom_writer.py](./scripts/bom_writer.py) | (Optional) Excel writer helper for full Phase 2 |
| [references/risk_criteria.md](./references/risk_criteria.md) | Full risk classification rules |
| [references/subsystem_template.md](./references/subsystem_template.md) | Standard subsystem list |
