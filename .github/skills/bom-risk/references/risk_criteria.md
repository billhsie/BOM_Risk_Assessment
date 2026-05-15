# BOM Risk Assessment Criteria (Phase 2)

Reference for Column D wording. **Mirror the Slate14 MLK BOM tone exactly** —
short, telegraphic, engineer-to-engineer. The Slate14 file (PTL→NVL migration)
is the gold standard captured here.

---

## Decision Logic (apply in order)

1. **Both B and C are `NA`** → leave D **empty**.
2. **C is empty** (customer not yet returned) → leave D empty until Phase 2.
3. **C == B verbatim, or C == "same"** → `Low: Co-using on <prev_platform>`
4. **C is found in the new PCL** (any vendor/part match) → `Low: on the Intel <PLAT>PCL.`
   - Optionally append a `(Best :<preferred PN>)` line if there's a recommended primary part.
5. **C ≠ B but customer uses a co-lay alt that's also in PCL** → combined Low form (see template below).
6. **C is Intel reference design / POR** → `Low:Inel POR` (note: typo "Inel" preserved per source).
7. **C is NOT in PCL AND is security/compliance-critical** (TPM, Tamper PLD, Security Module, Secure Boot, CNSA 2.0, FIPS) → **High**.
8. **C is NOT in PCL but is established silicon, no security risk** → **Medium**.
9. **C is brand new with no prior platform validation** → **High**.

`<PLAT>` = target platform short code. Slate14 uses `NVL` with no space (i.e. `NVLPCL`). Match exactly.

---

## Verbatim text templates (copy exactly)

### 🟢 Low (cell color `#92D050`)

```
Low: Co-using on PTL
```
```
Low: on the Intel NVLPCL.
```
```
Low: on the Intel NVLPCL.
(Best :PTN3222HMJ)
```
```
Low:Inel POR
```
```
Low:
Co-using on PTL
for PI3HDX6411BZLEX
PS8210 is on the NVL PCL.
```

### 🟡 Medium (cell color `#FFFF00`)

```
Medium:
not on the NVL PCL list
Secure boot coupling + compliance assumptions for CNSA 2.0.
```

General pattern:
```
Medium:
not on the <PLAT> PCL list
<one-line technical concern>
```

### 🔴 High (cell color `#C00000`)

```
High:
not on the NVL PCL.
New security‑critical function
```

General pattern:
```
High:
not on the <PLAT> PCL.
<one-line risk reason>
```

### Empty
Leave D blank when:
- Both B and C are `NA`
- B is reserved/no-stuff and C is `NA`

---

## Vocabulary observed in Slate14 (use these terms)

| Term | Meaning |
|------|---------|
| `Co-using on <PLAT>` | Customer reuses the RVP part |
| `on the Intel <PLAT>PCL.` | Part is on the new platform's PCL (no space before PLAT) |
| `Co-lay with <PN>` | Alternate footprint available |
| `(POR)` | Plan of Record |
| `(Best :<PN>)` | Recommended preferred part |
| `Inel POR` | Intel POR (typo preserved verbatim from source) |
| `for vPRO` | Variant qualifier (e.g. `Intel I219LM for vPRO`) |
| `Match on Chip` | Fingerprint security feature (no CV3+) |
| `PQC`, `CNSA 2.0`, `FIPS-140-3` | Compliance terms used as risk reasons |

---

## Special cases by subsystem

### CPU
- D column **empty** — CPU is Intel SoC, not a customer-selectable risk item.

### Security Module (Broadcom Citadel)
- NOT in NVL PCL by design (PCL Security = TPM only).
- CV4 (BCM58202TB1): **Medium** — new generation, PQC/CNSA 2.0 coupling.
- CV3+ (BCM58202): **High** — legacy, NVL compatibility not confirmed.

### SPI Tamper PLD
- NOT in NVL PCL.
- C == B → **Low** (Co-using).
- New part → **High** (New security-critical function).

### Thermal IC / Audio Amp / VCCST / VCCPRIM / MEMORY/3V/5V VR
- NOT in NVL PCL (these categories not covered).
- C == B → **Low: Co-using on PTL**.
- Different → **Medium: not on the NVL PCL list**.

### GPIO Expander / USB MUX / USB Current Limit / Power Share
- NOT in NVL PCL.
- Same as B → **Low**. Different → **Medium**.

### GMR / Hall sensor
- NOT in NVL PCL. Treat like above (Low if same, Medium if different).

### VNNAON (NVL-S vs NVL-H)
- `AOZ23567BQI`, `MP2961B`, `APW8634A`, `uP9313` valid for NVL-S → **Low**.
- `MP2961B` not for NVL-H (PCL says `For NVLS, HU, AX, AM`) → **High** if NVL-H customer uses it.
- `AOZ23567CQI`, `MP2961C` are NVL-UL only → **High** for NVL-S/H.

### IMVP9.3
- `MP29025`, `RTQ3700HHN`, `MP29021` valid for NVL-S/H → **Low**.
- `RRV68600` is `For PTLUH platform` only → **High** for NVL-*.

---

## PCL Category Risk Mapping

| PCL Category | Risk Weight | Notes |
|-------------|-------------|-------|
| iPoR (Intel Plan of Record) | Low | Full Intel validation |
| iPoc (Intel Proof of Concept) | Low-Medium | Partial validation only |
| ECO (OEM/ODM Validated) | Low | OEM production-proven |
| Open Lab | Low-Medium | IHV-led, limited validation |
| Heirs (Inherited) | Medium | Not yet verified on new platform — validate carefully |
| Not in PCL | Medium–High | Depends on component type and security relevance |
