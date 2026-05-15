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

**Step 0: Ask user for the target platform** (REQUIRED, must be the first question)

> "Which Intel client platform are you assessing? (e.g. NVL-S, NVL-H, NVL-UL, PTL-H, ARL-H)"

The platform string is passed to `fill_b_column.py` and decides which PCL entries are applicable based on the `PCL Remarks` text. Different platforms produce **different** Column B (e.g. NVL-S includes `MP2961B`, NVL-H excludes it).

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

**Step 3: Map subsystems → PCL entries (platform-aware)**

```powershell
py scripts/fill_b_column.py <PLATFORM>     # e.g. NVL-S, NVL-H
```

Platform filter rules (applied via `PCL Remarks` substring match):
- `For NVLUL` / `For NVL-UL` → entry applies to **NVL-UL only** (excluded from NVL-S, NVL-H)
- `For PTLUH` / `For PTL-UH` → entry applies to **PTL-UH only** (excluded from NVL-*)
- `For NVL S, Hx, ...` → entry applies to listed NVL variants only
- `For NVL` (no specific suffix) → applies to all NVL platforms
- No `For ...` clause → applies to all platforms in the PCL family

Mapping rules (see [scripts/fill_b_column.py](./scripts/fill_b_column.py)):

| Subsystem | PCL Source |
|-----------|------------|
| CPU | User input (PCL doesn't list CPU) |
| TBT Re-timer | Device Category = `TBT Retimer` |
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
| USB3 re-driver | `USB Redriver/Retimer` (excluding eUSB2/PTN3222/TUSB2E22) |
| Accelerometer (3-axis) | Device Category = `3-Axis Accelerometer` (excluding IMU/Mag whitelist) |
| Accelerometer+Gyro (IMU 2in1) | Device Category = `Accelerometer + Gyroscope Sensor`, plus whitelist (`LSM6DSV32`) |
| Magnetometer for 2in1 | Device Category contains `Magnetometer`, plus whitelist (`BMM350`) |
| SAR sensor | Device Category contains `SAR` |
| Charger | Device Category = `Charger` |
| BIOS ROM (SPINOR) | Hardcoded: `MX77U51250FZ4I42`, `W25R512NWEIQ` (PCL section 12 parser is garbled) |
| Memory | "Refer to Platform Memory Enablement Guide (RDC#…)" |
| **Anything else not in PCL** | **`NA` (do NOT guess)** |

**Whitelist overrides** (parts the PCL parser miscategorized as bare `Accelerometer`):
- `BMM350` → routed to Magnetometer (DC label overridden to `Magnetometer`)
- `LSM6DSV32` → routed to Accel+Gyro IMU (DC label overridden to `Accelerometer + Gyroscope Sensor`)
- Exact part-number match used to avoid catching siblings (e.g. `LSM6DSV320X` stays in Accelerometer)

**Cell format:** `Vendor PartNumber (Device Category) [PCL Remarks]`  
Multiple parts joined by newline. `[PCL Remarks]` only added if non-empty (used for platform applicability like `For PTL-UH platform` or `For NVL-S, Hx, HU, AX, AM`).

**Step 4: Generate timestamped Excel**

```powershell
powershell -File scripts/gen_bom_b.ps1 `
    -JsonPath "$env:TEMP\bom_b_filled.json" `
    -OutDir   "<repo or output folder>"
```

Produces `<Platform>_BOM_Risk_Assessment_YYYYMMDD_HHMMSS.xlsx`. The platform prefix is read from the JSON header (set by Step 3).

---

### Phase 2 — Risk Assessment (after Customer Returns Column C)

For each row compare Column B (RVP reference) vs Column C (customer part).
Mirror the **Slate14 MLK BOM** language exactly — short, telegraphic, engineer-to-engineer.

| C vs B / PCL | Risk | Verbatim D-cell text |
|--------------|:----:|----------------------|
| C == B (or C == "same") | 🟢 Low | `Low: Co-using on <prev_platform>` |
| C is on the new PCL | 🟢 Low | `Low: on the Intel <PLAT>PCL.` |
| C on PCL + best alternative recommended | 🟢 Low | `Low: on the Intel <PLAT>PCL.\n(Best :<preferred PN>)` |
| Intel POR / reference design | 🟢 Low | `Low:Inel POR` (note: "Inel" verbatim per source) |
| C≠B but co-lay variant on PCL | 🟢 Low | `Low:\nCo-using on <prev>\nfor <C-PN>\n<B-PN> is on the <PLAT> PCL.` |
| C not in PCL, security/compliance critical | 🔴 High | `High:\nnot on the <PLAT> PCL.\n<security/compliance reason>` |
| C not in PCL, brand new with no validation | 🔴 High | `High:\nnot on the <PLAT> PCL.\nNew component with no prior validation` |
| C not in PCL, established silicon | 🟡 Medium | `Medium:\nnot on the <PLAT> PCL list\n<one-line technical concern>` |
| Both B and C are `NA` | — | **leave D empty** |

**Notation conventions** (match Slate14 source verbatim):
- `<PLAT>PCL` written with **no space** before PLAT (e.g. `NVLPCL`)
- `(Best :<PN>)` — single space between `Best` and `:` and after colon
- `\n` between the level header and reason lines

Full rules and verbatim examples: [references/risk_criteria.md](./references/risk_criteria.md)

---

## Verification Policy (CRITICAL — do not violate)

1. **Always ask for the target platform first** (Step 0). Different platforms produce different Column B due to PCL Remarks filtering.
2. **Never fabricate part numbers.** If a subsystem has no matching PCL entry, write `NA`. Customer will fill via Column C.
3. **Always include Device Category** after the part number so reviewers can verify.
4. **Always include PCL Remarks** in `[ ]` when present — these mark platform applicability.
5. **Filename must include timestamp** (`YYYYMMDD_HHMMSS`) — never overwrite previous reports.
6. **Respect platform filter exclusions:**
   - Entries marked `For NVL-UL` are excluded from NVL-S / NVL-H
   - Entries marked `For PTL-UH` are excluded from all NVL platforms

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
