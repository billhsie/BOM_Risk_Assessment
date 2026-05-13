# Subsystem Template — Fixed A-Column List

This is the **fixed 37-entry list** for Column A of the BOM Risk Assessment Excel.
Source: `Slate14 MLK BOM_0414_2 (1).xlsx` — Intel platform BOM review standard.

Do NOT add, remove, or rename these entries. If a component doesn't fit any category, map it to the closest one.

---

## Complete Subsystem List (NVL Platform)

| Row | Subsystem | PCL Category | PCL Coverage |
|-----|-----------|-------------|-------------|
| 1 | CPU | — | N/A (Intel SoC) |
| 2 | EC | Embedded Controller | ✅ In NVL PCL |
| 3 | PMIC | PMIC | ✅ In NVL PCL |
| 4 | IMVP9.3 | CPU Core VR | ✅ In NVL PCL |
| 5 | SA VR | SA/Uncore VR | ✅ In NVL PCL |
| 6 | VCCIN_AUX VR | VCCIN_AUX VR | ✅ In NVL PCL |
| 7 | VNNAON | VNNAON VR | ✅ In NVL PCL |
| 8 | SSD VR | NVMe/SSD VR | ✅ In NVL PCL |
| 9 | PCH VR | PCH VR | ✅ In NVL PCL (part of PMIC) |
| 10 | MEMORY VR | DDR VR | ⚠️ NOT in NVL PCL |
| 11 | 5V VR | 5V supply | ⚠️ NOT in NVL PCL |
| 12 | 3V VR | 3.3V supply | ⚠️ NOT in NVL PCL |
| 13 | VCCST | VCCST VR | ⚠️ NOT in NVL PCL |
| 14 | VCCPRIM_IO | VCCPRIM_IO VR | ⚠️ NOT in NVL PCL |
| 15 | Retimer | PCIe/USB Retimer | ✅ In NVL PCL |
| 16 | TCH | Thunderbolt Controller | ✅ In NVL PCL |
| 17 | Audio Codec | HD-Audio / I²S Codec | ✅ In NVL PCL |
| 18 | Audio Amp | Smart Audio Amp | ⚠️ NOT in NVL PCL |
| 19 | WLAN | WiFi / BT | ✅ In NVL PCL |
| 20 | M.2 SSD | NVMe SSD | ✅ In NVL PCL |
| 21 | eMMC / UFS | Embedded Storage | ✅ In NVL PCL (if applicable) |
| 22 | LPC SIO | Super I/O | ✅ In NVL PCL |
| 23 | SPI Tamper PLD | Security / Tamper | ⚠️ NOT in NVL PCL |
| 24 | Security Module | TPM / Security Controller | ✅ TPM in PCL; Broadcom not in PCL |
| 25 | Thermal IC | Thermal Sensor | ⚠️ NOT in NVL PCL |
| 26 | Battery Gas Gauge | FG | ✅ In NVL PCL |
| 27 | UCSI PD | USB-C PD Controller | ✅ In NVL PCL |
| 28 | USB CL | USB Current Limit | ⚠️ NOT in NVL PCL |
| 29 | USB2 MUX | USB2 Multiplexer | ⚠️ NOT in NVL PCL |
| 30 | Power Share | USB Power Share VR | ⚠️ NOT in NVL PCL |
| 31 | GPIO Expander | I²C GPIO | ⚠️ NOT in NVL PCL |
| 32 | VCCST_HDCP | HDCP / Display Auth | ✅ May be part of UCSI/Display |
| 33 | GMR | Lid Sensor (GMR/Hall) | ⚠️ NOT in NVL PCL |
| 34 | DIMM SMBUS MUX | SMBus switch | ✅ In NVL PCL |
| 35 | Ambient Light Sensor | ALS | ✅ In NVL PCL |
| 36 | EC KBC | EC Keyboard Controller | ✅ Same as EC |
| 37 | BIOS SPI Flash | SPI ROM | ✅ In NVL PCL |

---

## Keyword Mapping Table

Use these keywords to map RVP BOM components to the correct subsystem:

| Keyword in Part Desc or RefDes | Maps to Subsystem |
|-------------------------------|------------------|
| `EC`, `KBC`, `Embedded Controller`, `ITE`, `SMSC` | EC |
| `PMIC`, `Power Management IC` | PMIC |
| `IMVP`, `CPU Core VR`, `VR for CPU` | IMVP9.3 |
| `VCCIN_AUX` | VCCIN_AUX VR |
| `VNNAON`, `VNN`, `AON` | VNNAON |
| `SSD VR`, `NVMe VR` | SSD VR |
| `MEMORY VR`, `DDR VR`, `VDDQ` | MEMORY VR |
| `VCCST` | VCCST |
| `VCCPRIM` | VCCPRIM_IO |
| `Retimer`, `JHL`, `RTD`, `Redriver` | Retimer |
| `Thunderbolt`, `TBT`, `TCH` | TCH |
| `Codec`, `Audio`, `NAU`, `DA7`, `CS42` | Audio Codec |
| `Amp`, `Speaker`, `TAS`, `MAX98` | Audio Amp |
| `WLAN`, `WiFi`, `AX`, `BE`, `CNVi` | WLAN |
| `SSD`, `NVMe`, `BG4`, `BG5`, `PM9` | M.2 SSD |
| `SIO`, `Super I/O`, `W83` | LPC SIO |
| `TPM`, `SLB`, `IM77` | Security Module |
| `Citadel`, `BCM582` | Security Module |
| `Tamper`, `PLD`, `LCMXO`, `XO2`, `MAX II` | SPI Tamper PLD |
| `Thermal`, `Temp sensor`, `EMC`, `NCT`, `ADT` | Thermal IC |
| `Gas Gauge`, `BQ`, `Fuel Gauge` | Battery Gas Gauge |
| `UCSI`, `PD Controller`, `FUSB`, `CYPD`, `CCG` | UCSI PD |
| `USB CL`, `Current Limit`, `TUSB921` | USB CL |
| `USB MUX`, `TS3USB`, `PI3USB` | USB2 MUX |
| `Power Share`, `USB Pwr` | Power Share |
| `GPIO`, `TCA6`, `PCA9`, `MCP230` | GPIO Expander |
| `GMR`, `Hall`, `Lid sensor`, `ALPS` | GMR |
| `SMBUS MUX`, `PCA9544`, `LTC4306` | DIMM SMBUS MUX |
| `ALS`, `Light sensor`, `APDS`, `TSL` | Ambient Light Sensor |
| `SPI Flash`, `BIOS ROM`, `GD25`, `MX25`, `W25` | BIOS SPI Flash |

---

## Notes

- **Rows 1–37 are fixed** — do not insert or delete rows in the output Excel.
- Row 1 of Excel = header row (dark blue), rows 2–38 = subsystem data rows.
- Empty subsystems still appear in output (leave B, C, D blank if no component found).
- The CPU row (Row 2) never has risk assessment — leave D column empty.
