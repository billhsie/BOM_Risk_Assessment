"""
Build B column for each Slate14 subsystem from PCL entries (curated mapping).
Output: timestamped Excel matching BOM_temp.xlsx format.

Mapping rules:
- Each Subsystem maps to PCL Device Category keywords
- Format per part: "Vendor PartNumber [PCL Remarks]"
- If no PCL match: write "NA"
- For CPU/Memory: special handling (use platform default)
"""
import json
import re
from datetime import datetime

# Load PCL parsed entries
with open(r'C:\Users\billhsie\AppData\Local\Temp\pcl_entries.json', encoding='utf-8') as f:
    pcl = json.load(f)

# Filter out junk entries (need device_category and a real part_number)
def is_real(e):
    pn = e.get('part_number', '')
    dc = e.get('device_category', '')
    if not pn or not dc:
        return False
    # part_number must have letter+digit and be reasonable length
    if not re.search(r'[A-Z]', pn) or not re.search(r'\d', pn):
        return False
    if 'Confidential' in pn or 'Other names' in pn:
        return False
    if len(pn) > 50:
        return False
    return True

pcl = [e for e in pcl if is_real(e)]

# Helper: format PCL entry into B-cell text
VENDOR_FIX = {
    'AlphaandOmegamiconductor Limited': 'AOS',
    'ANPECElectronics': 'ANPEC',
    'Monolithic Power Systems, Inc.(MPS)': 'MPS',
    'Texas Instruments Inc': 'TI',
    'Renesas Electronics Corporation': 'Renesas',
    'Cirrus Logic Inc': 'Cirrus Logic',
    'Nuvoton Technology Corp': 'Nuvoton',
    'BOSCH SENSORTEC GMBH': 'Bosch',
    'Robert Bosch (China)': 'Bosch',
    'NXP Semiconductors': 'NXP',
    'Diodes Incorporated': 'Diodes',
    'Parade Technologies, Ltd': 'Parade',
    'ITE TECH. INC': 'ITE',
    'STMicroelectronics': 'ST',
    'Infineon Technologies': 'Infineon',
    'Microchip Technology': 'Microchip',
    'Realtek Semiconductor Corp': 'Realtek',
    'Nationz Technologies Inc': 'Nationz',
    'ON Semiconductor': 'ON Semi',
    'Everest Semiconductor': 'Everest',
    'Richtek Technology': 'Richtek',
    'uPISemi': 'uPI',
    'SAMSUNG Electronics Co., Ltd': 'Samsung',
}

def fmt(e):
    v = e['vendor'].strip().rstrip(',.')
    v = VENDOR_FIX.get(v, v)
    pn = e['part_number'].strip().rstrip(',.').rstrip(')')
    if pn.startswith('PTPS'):
        pn = pn[1:]
    dc = e.get('device_category', '').strip().rstrip(',.')
    rem = e.get('remarks', '').strip()
    if 'Confidential' in rem or 'Other names' in rem:
        rem = ''
    if len(rem) > 80:
        rem = ''
    rem = re.sub(r'\s+', ' ', rem).strip()
    base = f"{v} {pn}".strip()
    if dc:
        base = f"{base} ({dc})"
    if rem:
        base = f"{base} [{rem}]"
    return base

# Find PCL entries by device_category keyword(s) and optional vendor filter
def find(dev_cat_kw, vendor_kw=None, exclude_kw=None):
    """Return list of entries matching device category keywords."""
    out = []
    for e in pcl:
        dc = e['device_category'].lower()
        v = e['vendor'].lower()
        if not any(k.lower() in dc for k in dev_cat_kw):
            continue
        if vendor_kw and not any(k.lower() in v for k in vendor_kw):
            continue
        if exclude_kw and any(k.lower() in dc for k in exclude_kw):
            continue
        out.append(e)
    return out

def join_parts(entries, max_n=None):
    if not entries:
        return 'NA'
    # Dedupe by (vendor, part_number)
    seen = set()
    uniq = []
    for e in entries:
        key = (e.get('vendor','').strip().lower(), e.get('part_number','').strip().lower())
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    if max_n:
        uniq = uniq[:max_n]
    return '\n'.join(fmt(e) for e in uniq)

# === Build B column for each Slate14 subsystem ===
# Default platform: NVL-S Desktop
PLATFORM = 'NVL-S'

# CPU is platform-specific, supplied by user/BOM
CPU_DEFAULT = 'Intel NVL-S (refer to platform target)'

mapping = {}

# CPU: from user/BOM (placeholder)
mapping['CPU'] = CPU_DEFAULT

# TBT Re-timer: list ALL TBT Retimer entries
tbt = [e for e in pcl if 'TBT Retimer' in e.get('device_category','')]
mapping['TBT Re-timer'] = join_parts(tbt) if tbt else 'NA'

# Security Module (Citadel/CV): NOT in PCL → NA
mapping['Security Module'] = 'NA'

# HDMI2.1 (6G) Re-driver: HDMI Retimer entries
hdmi = [e for e in pcl if 'HDMI Retimer' in e.get('device_category','')]
mapping['HDMI2.1 (6G) Re-driver'] = join_parts(hdmi) if hdmi else 'NA'

# Single eUSB2 re-driver: PTN3222 (NXP) is single eUSB2; TUSB2E22 is dual
single_eusb = [e for e in pcl if 'PTN3222' in e.get('part_number','')]
mapping['Single eUSB2 re-driver'] = join_parts(single_eusb) if single_eusb else 'NA'

# Dual eUSB2 re-driver: TUSB2E22 (TI)
dual_eusb = [e for e in pcl if 'TUSB2E22' in e.get('part_number','')]
mapping['Dual eUSB2 re-driver'] = join_parts(dual_eusb) if dual_eusb else 'NA'

# SPI Tamper PLD: not in PCL → NA
mapping['SPI Tamper PLD'] = 'NA'

# IMVP9.3
imvp = [e for e in pcl if 'IMVP' in e.get('device_category','')]
mapping['IMVP9.3'] = join_parts(imvp) if imvp else 'NA'

# VNNAON: Voltage Regulator entries with VNNAON in description (we approximate with vendor list)
vnnaon = [e for e in pcl if e.get('device_category','').strip() == 'Voltage Regulator']
mapping['VNNAON'] = join_parts(vnnaon) if vnnaon else 'NA'

# Memory: PCL Section 6 refers to separate doc
mapping['Memory'] = 'Refer to Nova Lake Platform Memory Enablement Guide (RDC#858687)'

# USB Type-C PD controller
pd = [e for e in pcl if 'PD Controller' in e.get('device_category','') or 'TypeC' in e.get('device_category','')]
mapping['USB Type-C PD controller'] = join_parts(pd) if pd else 'NA'

# Thermal IC: not present in PCL → NA
mapping['Thermal IC'] = 'NA'

# Embedded Controller
ec = [e for e in pcl if 'Embedded Controller' in e.get('device_category','')]
mapping['Embedded Controller'] = join_parts(ec) if ec else 'NA'

# GPIO expander: not in PCL → NA
mapping['GPIO expander'] = 'NA'

# Audio Codec
audio = [e for e in pcl if 'Audio Codec' in e.get('device_category','')]
mapping['Audio Codec'] = join_parts(audio) if audio else 'NA'

# Audio amplifier: not separate in PCL → NA (Cirrus codecs include integrated amps)
mapping['Audio amplifier'] = 'NA'

# TPM
tpm = [e for e in pcl if 'TPM' in e.get('device_category','')]
mapping['TPM'] = join_parts(tpm) if tpm else 'NA'

# LAN Controller (Ethernet)
lan = [e for e in pcl if 'Ethernet' in e.get('device_category','')]
mapping['LAN Controller'] = join_parts(lan) if lan else 'NA'

# USB2 re-driver: no specific USB2 redriver in PCL → NA
mapping['USB2 re-driver'] = 'NA'

# USB3 re-driver: USB3.2 only (exclude eUSB2 / PTN3222 which is eUSB2 redriver)
usb3 = [e for e in pcl if 'USB Redriver' in e.get('device_category','')]
usb3 = [e for e in usb3 if 'eUSB' not in e.get('part_number','').lower() and 'PTN3222' not in e.get('part_number','') and 'TUSB2E22' not in e.get('part_number','')]
mapping['USB3 re-driver'] = join_parts(usb3) if usb3 else 'NA'

# PCIE re-driver: not in current PCL → NA (PI3EQX12902 from Slate14 not listed)
mapping['PCIE re-driver'] = 'NA'

# Power Share (BC1.2): SILEGO SLGC55544 not in PCL → NA
mapping['Power Share (BC1.2)'] = 'NA'

# USB Current Limit IC: not in PCL → NA
mapping['USB Current Limit IC'] = 'NA'

# Accelerometer (3-axis only)
accel = [e for e in pcl if e.get('device_category','').strip().startswith('Axis Accelerometer')]
# Just accelerometer (BMA530)
accel_only = [e for e in accel if 'BMA' in e.get('part_number','') or 'LIS2' in e.get('part_number','')]
mapping['Accelerometer'] = join_parts(accel_only) if accel_only else 'NA'

# Accelerometer+Gyro for 2in1 (IMU)
imu = [e for e in pcl if 'BMI' in e.get('part_number','') or 'LSM6' in e.get('part_number','')]
mapping['Accelerometer+Gyro for 2in1'] = join_parts(imu) if imu else 'NA'

# Magnetometer for 2in1
mag = [e for e in pcl if 'Magnetometer' in e.get('device_category','') or 'BMM' in e.get('part_number','') or 'LIS2MDL' in e.get('part_number','')]
mapping['Magnetometer for 2in1'] = join_parts(mag) if mag else 'NA'

# SAR sensor
sar = [e for e in pcl if 'SAR' in e.get('device_category','')]
mapping['SAR sensor'] = join_parts(sar) if sar else 'NA'

# GMR sensor: not in PCL → NA
mapping['GMR sensor'] = 'NA'

# BIOS ROM (SPI NOR Flash) - parse manually from raw lines
# From parsed: SPINORSPINOR Macronix MX77U51250FZ4I42, Winbond QW25R512NWEI
bios = []
for e in pcl:
    pn = e.get('part_number','')
    if any(k in pn for k in ['MX77U', 'W25R', 'W25Q', 'QW25R']):
        bios.append(e)
# Also check raw entries by subsystem name pattern
mapping['BIOS ROM'] = join_parts(bios) if bios else 'NA'

# Fingerprint Reader module
fp = [e for e in pcl if 'Finger' in e.get('part_number','') or 'Fingerprint' in e.get('device_category','')]
fp = [e for e in fp if e.get('part_number') and 'Confidential' not in e.get('part_number','')]
mapping['Fingerprint Reader module'] = join_parts(fp) if fp else 'NA'

# USB2 MUX/deMUX: TS3USB221 not in PCL → NA
mapping['USB2 MUX/deMUX'] = 'NA'

# VCCST power switch: TPS22971 not in PCL → NA
mapping['VCCST power switch'] = 'NA'

# VCCPRIM_IO: NB706 not in PCL → NA
mapping['VCCPRIM_IO'] = 'NA'

# Charger
charger = [e for e in pcl if e.get('device_category','').strip() == 'Charger']
mapping['Charger'] = join_parts(charger) if charger else 'NA'

# MEMORY VR: not in current PCL extract → NA
mapping['MEMORY VR'] = 'NA'

# 3V VR / 5V VR: not in PCL → NA
mapping['3V VR'] = 'NA'
mapping['5V VR'] = 'NA'

# === Read BOM_temp subsystem list (sheet1, NVL-S) ===
import zipfile, xml.etree.ElementTree as ET
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(r'c:\Users\billhsie\OneDrive - Intel Corporation\Desktop\DATA\TOOL\AI_VB\BOM_risk\BOM_temp.xlsx') as z:
    with z.open('xl/sharedStrings.xml') as f:
        ss = ET.parse(f).getroot()
    strings = []
    for si in ss.findall('s:si', NS):
        strings.append(''.join(t.text or '' for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')))
    with z.open('xl/worksheets/sheet1.xml') as f:
        sheet1 = ET.parse(f).getroot()

subsystems_sheet1 = []
header_b = ''
header_c = ''
for row in sheet1.find('s:sheetData', NS).findall('s:row', NS):
    rownum = int(row.get('r'))
    cells = {}
    for c in row.findall('s:c', NS):
        ref = c.get('r')
        col = re.match(r'([A-Z]+)', ref).group(1)
        v = c.find('s:v', NS)
        t = c.get('t')
        if v is None:
            cells[col] = ''
        elif t == 's':
            cells[col] = strings[int(v.text)]
        else:
            cells[col] = v.text or ''
    if rownum == 1:
        header_b = cells.get('B','')
        header_c = cells.get('C','')
    elif cells.get('A','').strip():
        subsystems_sheet1.append(cells.get('A','').strip())

# Build output rows
output_rows = []
for s in subsystems_sheet1:
    b = mapping.get(s, 'NA')
    output_rows.append({'A': s, 'B': b, 'C': '', 'D': ''})

# Save JSON for Excel generator
out_json = r'C:\Users\billhsie\AppData\Local\Temp\bom_b_filled.json'
payload = {
    'header_b': header_b,
    'header_c': header_c,
    'rows': output_rows,
}
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(output_rows)} rows to {out_json}\n")
for r in output_rows:
    bp = r['B'].replace('\n', ' | ')[:90]
    print(f"  {r['A']:30} -> {bp}")
