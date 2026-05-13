# BOM Risk Assessment Criteria

Reference for Step 6 of the BOM Risk Assessment skill.
Compare Column B (RVP reference) vs Column C (customer component) to determine risk level.

---

## Decision Tree

```
Is C column empty?
  → Skip (no assessment possible)

Is C == "same" or C == B (identical)?
  → LOW: "Low: Co-using on <old platform>"

Is C part number found in PCL as iPoR?
  → LOW: "Low: on the Intel <PCL> platform"

Is C part number found in PCL as ECO?
  → LOW: "Low: on the Intel <PCL>\n(Category: ECO – OEM validated)"

Is C part number found in PCL as Open Lab?
  → LOW-MEDIUM: "Low: on the Intel <PCL>\n(Category: Open Lab)"

Is B marked [NOT in NVL PCL] (amber)?
  → Apply special rules below ↓

Is C a security-critical component (TPM, Secure Boot, Tamper PLD, Security Module)?
  → if NOT in PCL: HIGH
  → if in PCL: LOW

Is C a brand new component with no PTL/prior platform history?
  → HIGH: "High:\nnot on the NVL PCL\nNew component – no prior platform validation"

Is C not in PCL but same function as B with known compatibility?
  → MEDIUM: "Medium:\nnot on the NVL PCL list\n<specific technical concern>"
```

---

## Low Risk — Rules & Text Templates

| Situation | D-column text |
|-----------|--------------|
| Identical to old platform | `Low: Co-using on <OldPlatform>` |
| On PCL as iPoR | `Low: on the Intel <PCL> platform` |
| Intel POR component | `Low: Intel POR` |
| On PCL + co-using on old platform | `Low: Co-using on <OldPlatform>\non the Intel <PCL>` |
| PCL ECO category | `Low: on the Intel <PCL>\n(Category: ECO)` |
| PCL Heirs category (inherited, low risk) | `Low: on the Intel <PCL>\n(Category: Heirs – verify on NVL)` |

**Cell color:** Green background `#92D050`

---

## Medium Risk — Rules & Text Templates

| Situation | D-column text |
|-----------|--------------|
| Not on PCL, but established part | `Medium:\nnot on the <PCL> list\n<reason>` |
| Has CNSA 2.0 / FIPS compliance coupling | `Medium:\nnot on the NVL PCL.\nSecure boot coupling + compliance assumptions for CNSA 2.0.` |
| PCL Open Lab only (limited validation) | `Medium:\non the Intel <PCL> as Open Lab only\nFull OEM validation required` |
| 2nd source with uncertain compatibility | `Medium:\n<part> is 2nd source\nCompatibility with NVL not confirmed` |
| Functional but not NVL-platform validated | `Medium:\nnot validated on NVL platform\n<specific concern>` |

**Cell color:** Yellow background `#FFFF00`

---

## High Risk — Rules & Text Templates

| Situation | D-column text |
|-----------|--------------|
| New security-critical function, not PCL | `High:\nNew security-critical function\nnot on the NVL PCL` |
| Brand new component, no prior validation | `High:\nnot on the NVL PCL\nNew component with no prior platform validation` |
| Not on PCL + incompatible interface | `High:\nnot on the NVL PCL\nInterface incompatibility risk` |
| Security module with compliance gap | `High:\nNew security-critical function\nCNSA 2.0 / PQC compliance not verified` |

**Cell color:** Red background `#FF0000`

---

## Special Cases by Subsystem

### CPU
- Leave D column **empty** — CPU is Intel SoC, not a risk item.

### Security Module (Broadcom Citadel)
- NOT in NVL PCL by design (PCL Security = TPM only).
- If customer uses CV4 (BCM58202TB1): **Medium** — new generation with PQC/CNSA 2.0 coupling.
- If customer uses CV3+ (BCM58202): **High** — legacy part, NVL compatibility not confirmed.

### SPI Tamper PLD
- NOT in NVL PCL.
- If customer uses same part as B: **Low** — Co-using.
- If customer uses new part: **High** — New security-critical function.

### Thermal IC / Audio Amp / Small VRs (VCCST, VCCPRIM, MEMORY VR, 3V, 5V)
- NOT in NVL PCL (PCL does not cover these categories).
- If same as B: **Low** — Co-using on PTL.
- If different: **Medium** — not on NVL PCL, customer to validate.

### GPIO Expander / USB MUX / USB Current Limit
- NOT in NVL PCL.
- If same as B: **Low**.
- If different: **Medium** — functional validation required.

### GMR Sensor
- NOT in NVL PCL. PCL covers Hall sensors (Rohm BU52072GWZ).
- If same ALPS part: **Low** — Co-using on PTL.
- If different: **Medium** — not on PCL, no NVL validation.

### VNNAON (special NVL-S rule)
- AOZ23567BQI, MP2961B, APW8634A, uP9313 all valid for NVL-S.
- APW8634A (Open Lab) and uP9313 (ECO) = Low but note category.
- AOZ23567CQI and MP2961C = **NOT for NVL-S** (NVL-UL only) → High if customer uses these.

### IMVP9.3 (special NVL-S rule)
- RTQ3700HHN = iPoR for NVL-S → Low.
- MP29021 = iPoR for NVL-S (PCL 8.7) → Low.
- RRV68600 = Heirs, Open Lab, "For PTL-UH platform" → **Medium** for NVL-S.

---

## PCL Category Risk Mapping

| PCL Category | Risk Weight | Notes |
|-------------|-------------|-------|
| iPoR (Intel Plan of Record) | Low | Full Intel validation |
| iPoc (Intel Proof of Concept) | Low-Medium | Partial validation only |
| ECO (OEM/ODM Validated) | Low | OEM production-proven |
| Open Lab | Low-Medium | IHV-led, limited validation |
| Heirs (Inherited) | Medium | Not yet verified on NVL — validate carefully |
| Not in PCL | Medium–High | Depends on component type and function |
