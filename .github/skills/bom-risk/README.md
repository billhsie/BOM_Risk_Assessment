# BOM Risk Assessment — AI-Assisted Skill for Platform Migration

> **GitHub Copilot Skill** · Intel Hardware Engineering · Platform BOM Review Automation

[![VS Code](https://img.shields.io/badge/VS%20Code-Copilot%20Skill-007ACC?logo=visualstudiocode)](https://code.visualstudio.com/)
[![Platform](https://img.shields.io/badge/Platform-Intel%20NVL%20%7C%20PTL-0071C5?logo=intel)](https://www.intel.com/)
[![License](https://img.shields.io/badge/License-Internal%20Use-lightgrey.svg)](#)

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Problem Statement](#problem-statement)
- [Solution Architecture](#solution-architecture)
- [End-to-End Workflow](#end-to-end-workflow)
- [Data Verification Pipeline](#data-verification-pipeline)
- [Output Specification](#output-specification)
- [Risk Classification Logic](#risk-classification-logic)
- [Coverage Statistics](#coverage-statistics)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Technical Stack](#technical-stack)
- [Roadmap](#roadmap)

---

## Executive Summary

A GitHub Copilot Skill that **automates platform-migration BOM risk reviews** for Intel hardware projects. The skill reads the raw RVP BOM (1,700+ rows) and the official PCL PDF, cross-validates each component against both sources, and produces a color-coded risk-assessment Excel formatted to Intel platform-review standards.

| Metric | Manual Process | With This Skill |
|---|---|---|
| BOM-to-Risk Excel turnaround | **6 – 9 hours** | **~10 minutes** |
| Subsystem rows reviewed | 38 (manual lookup each) | 38 (auto-validated) |
| Component-source verification | Tribal knowledge | **Dual-source verified (BOM ∩ PCL)** |
| Output consistency | Engineer-dependent | Standardized template |

---

## Problem Statement

Every NVL platform migration requires a BOM risk review. The manual workflow is:

1. Open the customer-supplied raw RVP BOM (~1,700 rows containing capacitors, resistors, ICs, connectors, etc.)
2. Manually filter out passives, identify 30–50 ICs of interest
3. Cross-reference each IC against the **NVL PCL PDF** (159 components, 15 categories) by hand
4. Map each finding to a fixed 38-entry Subsystem template
5. Hand-write the Risk Assessment & Recommendation column with Low / Medium / High color coding

**Pain points:**
- Highly time-consuming and repetitive
- Easy to fabricate or hallucinate part numbers when memory fails
- Inconsistent format between engineers
- No traceability — no record of *where* a part number came from

---

## Solution Architecture

```mermaid
flowchart LR
    A[("NVL PCL<br/>PDF Rev0.7")] --> P1[PDF to Text<br/>Word COM]
    B[("RVP BOM<br/>xlsx 1,700+ rows")] --> P2[BOM Parser<br/>ZipFile + XML]
    C[("Subsystem<br/>Template")] --> M[Cross-Validator]
    P1 --> M
    P2 --> M
    M --> D{Match Logic}
    D -->|in BOM and PCL| V["Verified<br/>+ source citation"]
    D -->|in BOM only| W["Amber<br/>NOT in PCL"]
    D -->|neither| N["NA"]
    V --> O[Excel Writer<br/>Excel COM]
    W --> O
    N --> O
    O --> R[("Risk Assessment<br/>Excel Slate14 format")]

    style V fill:#92D050,stroke:#333,color:#000
    style W fill:#FFEB9C,stroke:#333,color:#000
    style N fill:#E7E6E6,stroke:#333,color:#000
    style R fill:#1F3864,stroke:#333,color:#fff
```

---

## End-to-End Workflow

```mermaid
sequenceDiagram
    autonumber
    participant U as Engineer
    participant CP as GitHub Copilot
    participant SK as bom-risk Skill
    participant CU as Customer

    U->>CP: Run BOM risk assessment for NVL-S
    CP->>SK: Invoke skill with PCL.pdf + RVP_BOM.xlsx
    SK->>SK: Phase 1 — Extract & cross-validate
    SK-->>U: Excel with B column auto-filled (verified citations)
    U->>CU: Send Excel for Column C input
    CU-->>U: Returns Excel with Column C filled
    U->>CP: Complete D column risk
    CP->>SK: Apply risk rules (B vs C)
    SK-->>U: Final color-coded Excel (Low/Med/High)
```

### Phase 1 — Reference BOM Generation (Column B)

```mermaid
flowchart TD
    Start([Engineer invokes skill]) --> I1[Load PCL PDF]
    Start --> I2[Load RVP BOM xlsx]
    I1 --> P1[Word COM<br/>PDF to text]
    I2 --> P2[Parse xlsx with<br/>ZipFile + XML]
    P1 --> X1[Extract 159 PCL parts<br/>+ category + iPoR/ECO/Open Lab]
    P2 --> X2[Filter passives:<br/>keep only IC/MCU/VR/etc.]
    X1 --> J{For each<br/>Subsystem}
    X2 --> J
    J --> Q1{Part in<br/>RVP BOM?}
    Q1 -->|No| NA[Write 'NA']
    Q1 -->|Yes| Q2{Part in<br/>NVL PCL?}
    Q2 -->|Yes| OK["Cite: NVL PCL section x.y iPoR<br/>+ RVP RefDes"]
    Q2 -->|No| AMB["Cite: NOT in PCL<br/>+ RVP RefDes amber"]
    NA --> W[Excel Writer]
    OK --> W
    AMB --> W
    W --> End([Output Excel])

    style OK fill:#FFFFFF,stroke:#333
    style AMB fill:#FFEB9C,stroke:#333,color:#000
    style NA fill:#E7E6E6,stroke:#333,color:#000
```

### Phase 2 — Risk Assessment (Column D)

```mermaid
flowchart TD
    S([Customer returns Excel<br/>with Column C filled]) --> R{Compare<br/>B vs C}
    R -->|C equals B<br/>or co-using| L1[Low: Co-using on<br/>previous platform]
    R -->|C in PCL as iPoR| L2[Low: on the<br/>Intel NVL PCL]
    R -->|C in PCL as ECO/<br/>Open Lab| L3[Low: on PCL<br/>category ECO/Open Lab]
    R -->|C not in PCL,<br/>same function| M1[Medium:<br/>not on NVL PCL]
    R -->|C is security-critical,<br/>not in PCL| H1[High: New<br/>security-critical function]
    R -->|brand new,<br/>no prior validation| H2[High: not on PCL<br/>+ no validation history]

    style L1 fill:#92D050,stroke:#333,color:#000
    style L2 fill:#92D050,stroke:#333,color:#000
    style L3 fill:#92D050,stroke:#333,color:#000
    style M1 fill:#FFFF00,stroke:#333,color:#000
    style H1 fill:#C00000,stroke:#333,color:#fff
    style H2 fill:#C00000,stroke:#333,color:#fff
```

---

## Data Verification Pipeline

The skill enforces a **strict dual-source rule** to eliminate hallucinated data:

```mermaid
flowchart LR
    Q[Candidate part] --> A{Found in<br/>RVP BOM<br/>by part number?}
    A -->|No| NA["NA<br/>do not write"]
    A -->|Yes| B{Found in<br/>NVL PCL<br/>by part number?}
    B -->|Yes| V["Cite both:<br/>PCL section x.y iPoR;<br/>RVP RefDes Uxxx"]
    B -->|No| W["Cite:<br/>NOT in NVL PCL;<br/>RVP RefDes Uxxx"]

    style V fill:#FFFFFF,stroke:#333
    style W fill:#FFEB9C,stroke:#333,color:#000
    style NA fill:#E7E6E6,stroke:#333,color:#000
```

> **Zero-hallucination policy:** if a part is not present in EITHER source, the cell is written as `NA`. The skill never invents part numbers.

---

## Output Specification

The output Excel matches the Intel **Slate14 MLK BOM** review template:

| Column | Title | Header Background | Filled By |
|--------|-------|-------------------|-----------|
| A | Subsystem | Dark Blue `#1F3864` | Fixed template |
| B | NVL-S RVP Reference BOM | Mid Blue `#2E4A7A` | **AI** (auto-validated) |
| C | Customer BOM | Mid Blue `#2E4A7A` | Customer |
| D | Risk Assessment & Recommendation | Dark Red `#8B0000` | **AI** (after C) |

**Cell colors:**

| Style | Color | Meaning |
|-------|-------|---------|
| Even row | `#DCE6F1` light blue | Zebra stripe for readability |
| Odd row | `#FFFFFF` white | Zebra stripe for readability |
| D Low Risk | `#92D050` green | Co-using or in PCL iPoR |
| D Medium Risk | `#FFFF00` yellow | Not in PCL, validation needed |
| D High Risk | `#C00000` red | Security-critical new component |

---

## Risk Classification Logic

| Condition | Risk | D-column Template |
|-----------|------|-------------------|
| `C == B` (identical) | Low | `Low: Co-using on <PrevPlatform>` |
| C is in PCL as **iPoR** | Low | `Low: on the Intel NVL PCL platform` |
| C is in PCL as **ECO** | Low | `Low: on the Intel NVL PCL (Category: ECO)` |
| C is in PCL as **Open Lab** | Low | `Low: on the Intel NVL PCL (Category: Open Lab)` |
| C not in PCL, same function as B | Medium | `Medium: not on NVL PCL — <reason>` |
| C is security-critical (TPM, Tamper, Secure Boot) and not in PCL | High | `High: New security-critical function` |
| C is brand new, no validation history | High | `High: not on PCL + no prior validation` |

Full rules: [references/risk_criteria.md](references/risk_criteria.md)

---

## Coverage Statistics

> **Validated against:** `NVL-S_S021_UDIMM_1DPC_BOM.xlsx` (47 ICs after passive filtering) and `NVL_PCL_Rev0.7` (159 components)

| Status | Count | Background | Notes |
|--------|------:|------------|-------|
| Verified (in BOM and in PCL) | **9 / 38** | white | Cited with PCL section + RefDes |
| In BOM but NOT in PCL | **3 / 38** | amber | Customer must validate |
| NA (not in this BOM, or PCL doesn't cover) | **26 / 38** | gray | DT BOM has no sensors/charger/TBT |

### Verified Component Inventory (NVL-S DT)

| Subsystem | Part Number | PCL Reference | RVP RefDes |
|-----------|-------------|---------------|------------|
| Embedded Controller | `NPCX4885A0DX` | §4.3 iPoR | U9G1 |
| IMVP9.3 Controller | `RTQ3700HHN` | §8.6 iPoR | EU1B1 |
| IMVP9.3 Power Stage | `TDA21590` | (Infineon) | various |
| VNNAON | `AOZ23567BQI` | §8.9 iPoR (For NVL-S) | EU3B1 |
| HDMI Retimer | `PS8219` | §9.2 iPoR | EU1A3 |
| USB3 Redriver | `PI3EQX1014` | §15.1 iPoR | EU5A2 |
| USB3 Redriver | `PI3EQX1002E` | §15.10 iPoR | EU5T1, EU5U1 |
| USB-C Retimer | `PS8825` | §15.11 iPoR | EU5B1 |
| LAN | `I219LM` | §2.2 iPoR | EU4B1 |
| BIOS SPI Flash | `W25R512NWEIQ` | §12.2 iPoR | – |

### Amber Components (in BOM, not in PCL)

| Subsystem | Part Number | Reason |
|-----------|-------------|--------|
| USB-C PD Controller | `ANX7498` (Analogix) | PCL PD only lists TI parts |
| Audio Codec | `ALC722-CG` (Realtek) | PCL Audio only lists Cirrus/Everest/ON |
| GPIO Expander | `PCA9555PW/G` | PCL does not cover GPIO Expander category |

---

## Repository Structure

```
BOM_risk/
├── .github/
│   └── skills/
│       └── bom-risk/                     ← Copilot Skill package
│           ├── SKILL.md                  ← Skill definition (auto-loaded)
│           ├── README.md                 ← This document
│           ├── scripts/
│           │   ├── bom_reader.py         ← Parse RVP BOM xlsx
│           │   └── bom_writer.py         ← Generate output Excel
│           └── references/
│               ├── risk_criteria.md      ← Risk classification rules
│               └── subsystem_template.md ← Fixed 38-entry template
├── NVL-S_S021_UDIMM_1DPC_BOM.xlsx        ← Sample input (RVP BOM)
├── 870781_NVL_DT_Mobile_PCL_Rev0p7.pdf   ← Sample input (PCL)
├── Slate14 MLK BOM_0414_2 (1).xlsx       ← Output format template
└── NVL-S_BOM_Risk_Assessment.xlsx        ← Sample output
```

---

## Quick Start

### Prerequisites

- Windows 10/11
- Microsoft Office (Excel + Word) — for COM automation
- Python 3.x (stdlib only — no `pip install` required)
- VS Code with GitHub Copilot extension
- Network access NOT required after initial install

### Installation

```powershell
# 1. Clone repository
git clone https://github.com/<your-org>/bom-risk-skill.git
cd bom-risk-skill

# 2. Place skill in your project's .github/skills/ folder
Copy-Item -Recurse .github\skills\bom-risk <your-project>\.github\skills\
```

### Usage

1. Open VS Code in your project workspace
2. Open GitHub Copilot Chat
3. Ask:
   > *"Perform NVL-S BOM risk assessment using `<PCL.pdf>` and `<RVP_BOM.xlsx>`"*
4. Skill auto-generates `<Project>_BOM_Risk_Assessment.xlsx` with Column B filled
5. Send Excel to customer to fill Column C
6. Return to Copilot:
   > *"Complete Column D risk assessment"*

---

## Technical Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Skill definition | VS Code Copilot Skills (`SKILL.md` + YAML frontmatter) | Native Copilot discovery |
| PDF text extraction | Word 16.0 COM (`SaveAs2` format 2) | No external library; handles encrypted Intel PCL PDFs |
| BOM parsing | Python `zipfile` + `xml.etree` | No `openpyxl` dependency (network-restricted environments) |
| Excel generation | Excel COM via PowerShell | Native cell formatting, Slate14 color matching |
| Cross-validation | Python regex matching | Part-number normalization across BOM and PCL |

---

## Roadmap

- [x] NVL-S Desktop platform (S021 UDIMM 1DPC RVP)
- [ ] NVL-H / NVL-UL / NVL-AX / NVL-AM platform variants
- [ ] PTL / ARL legacy PCL support for cross-generation co-using analysis
- [ ] Multi-language risk text generation (EN/CN)
- [ ] Web-based GitHub Action (CI/CD integration)
- [ ] Auto-generation of customer-side input template
- [ ] PCL Rev tracking and diff between PCL revisions

---

## License & Attribution

This skill is for internal Intel hardware engineering use. The PCL document is Intel Confidential. Component data shown is from publicly accessible RVP reference designs.

---

*Maintained by Intel Hardware Engineering · Built with GitHub Copilot Agent Mode*
