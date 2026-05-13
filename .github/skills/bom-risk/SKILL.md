---
name: bom-risk
description: "BOM Risk Assessment skill. Use when user asks to: perform BOM risk assessment, generate platform migration risk report, analyze component risks, compare old vs new platform BOMs, auto-filter IC from RVP BOM, fill B column from PCL, or produce color-coded Low/Medium/High Excel. Supports Intel NVL PCL PDF lookup and RVP BOM IC extraction."
argument-hint: "platform name or BOM file path (e.g. 'NVL-S' or 'C:/bom.xlsx')"
---

# BOM Risk Assessment Skill

## Overview

Automates the most time-consuming part of platform migration BOM review:

| Step | Manual (Before) | With This Skill |
|------|----------------|-----------------|
| Filter ICs from RVP BOM (~1700 rows) | 2–3 hours | < 1 min |
| Look up each IC against PCL PDF | 1–2 hours | < 1 min |
| Fill B column with RVP reference | 1 hour | Automatic |
| Write D column risk text + color | 1–2 hours | Automatic |
| **Total** | **~6 hours** | **~10 minutes** |

## When to Use

Invoke this skill when user says any of:
- "do BOM risk assessment", "generate risk report", "BOM risk"
- "fill B column from PCL", "compare old and new platform BOM"
- "which components are on the NVL PCL", "auto-filter IC from BOM"
- "produce risk Excel", "platform migration risk"

## Inputs Required

| Input | Description | Required |
|-------|-------------|----------|
| **Platform target** | e.g. `NVL-S`, `NVL-UL`, `NVL-H` | Yes |
| **PCL PDF** | e.g. `870781_NVL_DT_Mobile_PCL_Rev0p7.pdf` | Yes |
| **RVP BOM Excel** | Raw production BOM (e.g. `NVL-S_S021_UDIMM_1DPC_BOM.xlsx`) | For B column |
| **Subsystem template** | Fixed A-column list (from reference file below) | Auto-loaded |
| **Customer BOM** | Customer fills C column after receiving output | For D column |

## Output Format

Excel file with 4 columns, matching Intel platform BOM review standard:

```
Col A  Subsystem              ← FIXED (37 standard entries)
Col B  RVP Reference BOM      ← AI fills from PCL + RVP BOM
Col C  Customer BOM           ← Customer fills in
Col D  Risk Assessment        ← AI fills after C is provided
```

**Color coding (Column D cell background):**
- 🟩 **Green**  = Low risk
- 🟨 **Yellow** = Medium risk  
- 🟥 **Red**    = High risk
- 🟨 **Amber**  (Column B) = Component NOT in PCL — customer must verify

---

## Procedure

### Phase 1 — Generate B-Column Output (RVP → PCL lookup)

**Step 1: Read PCL PDF**

Use Word COM to extract PCL text:
```powershell
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($pclPdfPath, $false, $true)
$doc.SaveAs2("$env:TEMP\pcl_text.txt", 2)
$doc.Close($false); $word.Quit()
```

Parse the extracted text for each subsystem using the rules in [Risk Criteria](./references/risk_criteria.md).

**Key PCL parsing rules for NVL-S:**
- Check `PCL Remarks` column — entries marked `For NVL-UL only` are **NOT** applicable to S
- Entries marked `For NVL-S` or `For NVL-S/Hx/HU/AX/AM` ARE applicable
- `No-S` prefix on CMS column = CMS not supported, but component may still be valid
- Priority order: `iPoR` > `ECO` > `Open Lab` > `iPoc` > `Heirs`

**Step 2: Extract ICs from RVP BOM**

Read the production BOM Excel (standard Intel BOM format: IDN/Lvl/ItemTyp/ItemNo/ItemDesc/RefDes/MfrName/MfrPart).

Filter rules — **KEEP** these Item Type values:
```
ASIC, AUDIO, ANALOG-SWITCH, BUFFER/DRIVER, BUS-TRANSCEIVERS,
I/O-IC, IC-SWITCHES, IC-VOLTAGE-REG, LINEAR-DRIVER,
LINEAR-INTERFACE, LOGIC-GATES, MEMORY, MICROCONTROLLER,
OTHERVLSI, RFID_CHIP_PACKAGE, TRANSLATORS
```

For `NEW_BIZ_RDV` rows: only keep if RefDes starts with `U` (IC) or matches known IC part numbers. Skip if RefDes starts with `C`, `R`, `L`, `J`, `F`, `FB`.

**DISCARD** (passives & mechanical):
```
CERAMIC-CAP, RESISTOR-DISCRETE, HIGH-CURRENT-INDUC, FERRITE-BEADS,
CRYSTAL, DIODES, FET-*, CONNECTOR_*, POLYSWITCH, ALUM-ELEC-CAP,
SPECIALITY-CAP, SMALL-SIGNAL-INDUC, SPPRINTEDBOARD, STANDOFF,
COMMON-MODE-CHOKE, ZENER-DIODE, THRMSTR, LED*, BIPOLAR*, BATTERY*,
BOARD-TO-BOARD, SWITCHES, HEADER-CONN, SOCKET-CONNECTOR
```

**Step 3: Map ICs → Subsystem (A column)**

Use the fixed subsystem template: [Subsystem Template](./references/subsystem_template.md)

Matching logic (in order):
1. Exact Part Number match in PCL → use PCL Subsystem + PCL category tag
2. Partial Part Number match (prefix match) → use match + note version
3. Mfr Name + function keyword match → use keyword mapping table
4. No match found → mark as `[NOT in NVL PCL]` (amber background)

**Step 4: Write Output Excel**

Run: `py .github/skills/bom-risk/scripts/bom_writer.py --config config.json`

See [bom_writer.py](./scripts/bom_writer.py) for full API.

Output cell formatting:
- Column B amber = NOT in PCL
- Column C = light green empty cells (customer fills)  
- Column D = gray italic "Pending" until C is filled
- Row 1 = dark blue header, white text
- Alternating row shading for readability

---

### Phase 2 — Generate D-Column Risk Assessment (after C is filled)

**Step 5: Read the Customer-Filled Excel**

Read Column C values. For each row compare B (reference) vs C (customer).

**Step 6: Apply Risk Rules**

See full rules in [Risk Criteria](./references/risk_criteria.md). Summary:

| Condition | Risk | D-column text format |
|-----------|------|----------------------|
| C == B, or C is same family | Low | `Low: Co-using on <platform>` |
| C part is in PCL as iPoR | Low | `Low: on the Intel <PCL> platform` |
| C part is in PCL as ECO/Open Lab | Low-Medium | `Low: on the Intel <PCL>\n(Category: ECO)` |
| C part NOT in PCL, but established | Medium | `Medium:\nnot on the <PCL> list\n<reason>` |
| C part is security-critical + not PCL | High | `High:\nNew security-critical function\n<reason>` |
| C part is brand new, no validation | High | `High:\nnot on the NVL PCL\n<reason>` |

**Step 7: Color-code and Save**

Apply background color to Column D cells:
- Green  (`0x92D050`) = Low
- Yellow (`0xFFFF00`) = Medium  
- Red    (`0xFF0000`) = High

Save output as `<ProjectName>_BOM_Risk_<date>.xlsx`

---

## Important Limitations (Do Not Guess)

1. **PCL does NOT cover**: Thermal IC, Audio Amplifier, Security Module (Broadcom Citadel), GPIO expander, USB MUX, small VRs (VCCST/VCCPRIM/MEMORY VR/3V/5V). Mark these amber in B column — customer must provide own validation evidence.

2. **PCL NVL-S platform filtering**: Always check `PCL Remarks` column. `For NVL-UL` entries = NOT applicable to S.

3. **IC classification accuracy**: `NEW_BIZ_RDV` type in BOM is mixed — contains both ICs and passives. Always use RefDes prefix to confirm.

4. **Customer C-column is mandatory for D-column** — do not generate risk assessment without knowing the actual customer component.

---

## References

- [Risk Criteria Rules](./references/risk_criteria.md) — Full Low/Medium/High decision logic
- [Subsystem Template](./references/subsystem_template.md) — Fixed 37-entry A-column list
- [BOM Reader Script](./scripts/bom_reader.py) — Extracts ICs from production BOM Excel

The `assessments.json` format:
```json
[
  {
    "subsystem": "TBT Re-timer",
    "old_component": "Intel Hayden Bridge",
    "new_component": "Intel June Bridge",
    "risk_level": "Low",
    "reason": "on the Intel NVLPCL platform"
  },
  {
    "subsystem": "Security Module",
    "old_component": "Broadcom CV3+",
    "new_component": "Broadcom CV4 (BCM58202TB1KFBG10)",
    "risk_level": "Medium",
    "reason": "not on the NVL PCL.\nSecure boot coupling + compliance assumptions for CNSA 2.0."
  }
]
```

### Step 5 — Summarize to User
After generating the file, report:
- Total components assessed
- Count by risk level (High / Medium / Low)
- List all High and Medium risk items with their reasons
- Output file path

## Example Invocation
User: "Do BOM risk assessment for my new NVL platform. Here's the BOM file: C:\project\bom.xlsx"

## Notes
- If multiple memory types (e.g., LPDDR5 + SODIMM), create one Excel sheet per memory type
- The CPU row typically has no risk assessment (leave column D empty)
- "same" in new component column means identical to old → always Low: Co-using
- Security-related subsystems (TPM, Security Module, SPI Tamper PLD, Fingerprint Reader) need extra scrutiny
