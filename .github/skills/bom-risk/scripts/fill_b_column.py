"""
Build B column from PCL entries for a specific platform.
Usage: py fill_b_column.py NVL-S   or   py fill_b_column.py NVL-H
Output: timestamped Excel + JSON for gen_bom_b.ps1
"""
import json, re, sys, zipfile, xml.etree.ElementTree as ET

PLATFORM = (sys.argv[1] if len(sys.argv) > 1 else 'NVL-S').upper()
print(f"Platform: {PLATFORM}")

# ---------- PCL filtering by platform ----------
# Remarks patterns that EXCLUDE an entry for a given platform
EXCLUDE_FOR_PLATFORM = {
    'NVL-S': ['NVLUL', 'NVL-UL', 'NVL_UL', 'PTLUH', 'FOR PTLUH'],
    'NVL-H': ['NVLUL', 'NVL-UL', 'NVL_UL', 'PTLUH', 'FOR PTLUH'],
    'NVL-UL': ['FOR PTLUH'],
    'PTL-H': [],
    'ARL-H': [],
}
# Remarks patterns that RESTRICT entry to specific platforms (if present, only include if platform matches)
RESTRICT_MAP = {
    'NVL-S': ['NVLS', 'NVL-S', 'NVL_S'],
    'NVL-H': ['NVLHX', 'NVLH', 'NVL-H', 'NVL-HX', 'HX', ' HX,'],
}

def is_platform_applicable(e):
    rem = re.sub(r'\s+', ' ', e.get('remarks', '')).upper()
    # Explicit exclusions
    for ex in EXCLUDE_FOR_PLATFORM.get(PLATFORM, []):
        if ex in rem:
            return False
    # If remarks restrict to certain platforms, only include if our platform is mentioned
    for key, includes in RESTRICT_MAP.items():
        if key == PLATFORM:
            continue
        # check if ANY restrict phrase for OTHER platforms appears without also mentioning our platform
    # Simplified: if "FOR NVL" is in remarks, check we match
    if re.search(r'FOR NVL', rem):
        platform_key = PLATFORM.replace('-', '').replace('_', '')  # NVLS, NVLH, NVLUL
        # Get all 'FOR NVL...' targets
        targets = re.findall(r'FOR\s+NVL([A-Z0-9]+)', rem)
        if targets:
            # Check if any target matches our platform suffix
            my_suffix = platform_key.replace('NVL', '')  # S, H, UL etc
            matched = any(my_suffix in t for t in targets)
            if not matched:
                return False
    return True

# Load PCL
with open(r'C:\Users\billhsie\AppData\Local\Temp\pcl_entries.json', encoding='utf-8') as f:
    pcl_all = json.load(f)

def is_real(e):
    pn = e.get('part_number', '')
    dc = e.get('device_category', '')
    return (pn and dc and re.search(r'[A-Z]', pn) and re.search(r'\d', pn)
            and 'Confidential' not in pn and len(pn) <= 50)

pcl = [e for e in pcl_all if is_real(e) and is_platform_applicable(e)]
print(f"PCL entries after platform filter: {len(pcl)} / {len(pcl_all)}")

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
}

def fmt(e):
    v = VENDOR_FIX.get(e['vendor'].strip().rstrip(',.'), e['vendor'].strip().rstrip(',.'))
    pn = e['part_number'].strip().rstrip(',.)')
    if pn.startswith('PTPS'): pn = pn[1:]
    dc = e.get('device_category','').strip().rstrip(',.')
    # Strip garbled trailing tokens like ' -, --' or ' -, -AG-- ---- AG--'
    dc = re.sub(r'\s*[-,]+(\s*[-,A-Z]+)*\s*$', '', dc).strip()
    rem = e.get('remarks','').strip()
    if 'Confidential' in rem or 'Other names' in rem or len(rem) > 80:
        rem = ''
    rem = re.sub(r'\s+', ' ', rem).strip()
    s = f"{v} {pn} ({dc})" if dc else f"{v} {pn}"
    if rem: s += f" [{rem}]"
    return s

def join_parts(entries):
    if not entries: return 'NA'
    seen, uniq = set(), []
    for e in entries:
        k = (e.get('vendor','').lower(), e.get('part_number','').lower())
        if k not in seen:
            seen.add(k); uniq.append(e)
    return '\n'.join(fmt(e) for e in uniq)

def by_dc(*kws, pn_kw=None, exclude_dc=None, exclude_pn=None):
    out = []
    for e in pcl:
        dc = e.get('device_category','')
        pn = e.get('part_number','')
        if not any(k in dc for k in kws): continue
        if pn_kw and not any(k in pn for k in pn_kw): continue
        if exclude_dc and any(k in dc for k in exclude_dc): continue
        if exclude_pn and any(k in pn for k in exclude_pn): continue
        out.append(e)
    return out

# ---------- Build mapping ----------
m = {}
pf = PLATFORM  # for CPU label
m['CPU'] = f"Intel {pf} (refer to platform target; not listed in PCL)"
m['TBT Re-timer'] = join_parts(by_dc('TBT Retimer'))
m['Security Module'] = 'NA'
m['HDMI2.1 (6G) Re-driver'] = join_parts(by_dc('HDMI Retimer'))
m['Single eUSB2 re-driver'] = join_parts([e for e in pcl if 'PTN3222' in e.get('part_number','')])
m['Dual eUSB2 re-driver'] = join_parts([e for e in pcl if 'TUSB2E22' in e.get('part_number','')])
m['SPI Tamper PLD'] = 'NA'
m['IMVP9.3'] = join_parts(by_dc('IMVP'))
m['VNNAON'] = join_parts(by_dc('Voltage Regulator'))
m['Memory'] = 'Refer to Nova Lake Platform Memory Enablement Guide (RDC#858687)'
m['USB Type-C PD controller'] = join_parts(by_dc('PD Controller', 'TypeC'))
m['Thermal IC'] = 'NA'
m['Embedded Controller'] = join_parts(by_dc('Embedded Controller'))
m['GPIO expander'] = 'NA'
m['Audio Codec'] = join_parts(by_dc('Audio Codec'))
m['Audio amplifier'] = 'NA'
m['TPM'] = join_parts(by_dc('TPM', 'Discrete TPM'))
m['LAN Controller'] = join_parts(by_dc('Ethernet'))
m['USB2 re-driver'] = 'NA'
m['USB3 re-driver'] = join_parts(by_dc('USB Redriver', 'USB Repeater',
    exclude_pn=['PTN3222','TUSB2E22','eUSB']))
m['PCIE re-driver'] = 'NA'
m['Power Share (BC1.2)'] = 'NA'
m['USB Current Limit IC'] = 'NA'
# Sensor classification: STRICT PCL device_category mapping
#   Accelerometer            = PCL '3-Axis Accelerometer' (all entries, no IMU split)
#   Accelerometer+Gyro 2in1  = PCL 'Accelerometer + Gyroscope Sensor' only
#   Magnetometer for 2in1    = PCL 'Magnetometer' / 'Axis Magnetometer' only
m['Accelerometer'] = join_parts(
    [e for e in pcl if e.get('device_category','').strip() == 'Axis Accelerometer'])
m['Accelerometer+Gyro for 2in1'] = join_parts(
    [e for e in pcl if e.get('device_category','').strip().startswith('Accelerometer + Gyroscope')])
m['Magnetometer for 2in1'] = join_parts(
    [e for e in pcl if 'Magnetometer' in e.get('device_category','')])
m['SAR sensor'] = join_parts(by_dc('SAR'))
m['GMR sensor'] = 'NA'
# BIOS ROM = SPI NOR Flash; PCL section 12 parsing is garbled (vendor mixed into part_number)
# Search raw field instead, then build correct entries manually
BIOS_ROM_PARTS = [
    {'vendor': 'Macronix', 'part_number': 'MX77U51250FZ4I42', 'device_category': 'SPINOR', 'remarks': 'SPI, QFN8, 64MB, RPMC'},
    {'vendor': 'Winbond',  'part_number': 'W25R512NWEIQ',     'device_category': 'SPINOR', 'remarks': 'SPI, QFN8, 64MB, RPMC'},
]
m['BIOS ROM'] = join_parts(BIOS_ROM_PARTS)
m['Fingerprint Reader module'] = 'NA'
m['USB2 MUX/deMUX'] = 'NA'
m['VCCST power switch'] = 'NA'
m['VCCPRIM_IO'] = 'NA'
m['Charger'] = join_parts(by_dc('Charger'))
m['MEMORY VR'] = 'NA'
m['3V VR'] = 'NA'
m['5V VR'] = 'NA'

# ---------- Read template subsystem list ----------
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(r'c:\Users\billhsie\OneDrive - Intel Corporation\Desktop\DATA\TOOL\AI_VB\BOM_risk\BOM_temp.xlsx') as z:
    with z.open('xl/sharedStrings.xml') as f:
        ss = ET.parse(f).getroot()
    strings = [''.join(t.text or '' for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')) for si in ss.findall('s:si', NS)]
    with z.open('xl/worksheets/sheet1.xml') as f:
        sh = ET.parse(f).getroot()

rows_out, header_b, header_c = [], '', ''
for row in sh.find('s:sheetData', NS).findall('s:row', NS):
    rn = int(row.get('r'))
    cells = {}
    for c in row.findall('s:c', NS):
        col = re.match(r'([A-Z]+)', c.get('r')).group(1)
        v = c.find('s:v', NS)
        cells[col] = (strings[int(v.text)] if c.get('t')=='s' else (v.text or '')) if v is not None else ''
    if rn == 1:
        header_b = cells.get('B','')
        header_c = cells.get('C','')
    elif cells.get('A','').strip():
        s = cells['A'].strip()
        rows_out.append({'A': s, 'B': m.get(s,'NA'), 'C': '', 'D': ''})

out_json = r'C:\Users\billhsie\AppData\Local\Temp\bom_b_filled.json'
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump({'platform': PLATFORM, 'header_b': header_b, 'header_c': header_c, 'rows': rows_out}, f, ensure_ascii=False, indent=2)

print(f"\nWrote {len(rows_out)} rows  -->  {out_json}")
for r in rows_out:
    print(f"  {r['A']:30} -> {r['B'].replace(chr(10),' | ')[:90]}")
