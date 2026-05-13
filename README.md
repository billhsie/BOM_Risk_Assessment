# BOM Risk Assessment Skill

GitHub Copilot Skill for Intel platform-migration BOM risk reviews. Automates the cross-validation of RVP BOM components against the official PCL PDF and produces a color-coded Excel risk-assessment report.

**For full documentation see [.github/skills/bom-risk/README.md](.github/skills/bom-risk/README.md)**

## Quick Links

- [Full Documentation & Architecture](.github/skills/bom-risk/README.md)
- [Skill Definition](.github/skills/bom-risk/SKILL.md)
- [Risk Classification Rules](.github/skills/bom-risk/references/risk_criteria.md)
- [Subsystem Template](.github/skills/bom-risk/references/subsystem_template.md)

## Highlights

- **6–9 hours → ~10 minutes** per BOM review
- **Zero-hallucination policy** — every cell cites its source (PCL section + RVP RefDes)
- **Slate14-compliant** output formatting
- Pure stdlib + Office COM — no `pip install` required, works in network-restricted environments
