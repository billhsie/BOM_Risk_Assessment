"""Parse PCL text into structured entries and map to Slate14 subsystems."""
import re
import json

with open(r'C:\Users\billhsie\AppData\Local\Temp\pcl_text.txt', encoding='utf-8', errors='ignore') as f:
    raw = f.read()

# Strip page markers and normalize
text = raw.replace('---PAGE---', ' ').replace('\r', ' ')
# Replace newlines with spaces but keep structure
text = re.sub(r'\n+', ' ', text)
text = re.sub(r'\s+', ' ', text)

# Find all entries: pattern S/N (e.g. "15.4") followed by content until next S/N
# S/N is like \d+\.\d+ but must be at a real entry boundary
# Use lookahead for next S/N or end
entries_raw = re.findall(
    r'(\d{1,2}\.\d{1,2})([^0-9].*?)(?=\d{1,2}\.\d{1,2}[A-Z]|$)',
    text
)

# Status keywords mark end of entry data; PCL Remarks comes AFTER status
STATUS_PATTERNS = [
    'IHV Functional', 'IHV functional', 'IHV Test',
    'OEM Functional', 'OEM Production', 'OEM functional', 'OEM production',
    'Microsoft Functional', 'Intel Functional',
]

CATEGORY_KEYWORDS = ['iPoR', 'iPOR', 'iPoC', 'iPOC', 'Heirs', 'ECO', 'Open Lab', 'Open LAB']

def parse_entry(sn, body):
    """Extract Sub System, Device Category, Vendor, Part Number, PCL Remarks from concatenated body."""
    result = {'sn': sn, 'raw': body[:300].strip()}

    # Find PCL Remarks (after status keyword)
    remarks = ''
    for sp in STATUS_PATTERNS:
        idx = body.rfind(sp)
        if idx >= 0:
            remarks = body[idx + len(sp):].strip()
            # Clean trailing junk
            remarks = re.sub(r'^[\s\W]+', '', remarks)
            break
    result['remarks'] = remarks[:120]

    # Try to extract Sub System (first 1-2 words at start)
    # Common subsystems: USB, Audio, Display, Sensor, Power Delivery, PD Controller, Security, Memory, Connectivity, Embedded Controller, Imaging, Storage, Retimer Redriver
    SUBSYS_LIST = [
        'Embedded Controller', 'Power Delivery', 'PD Controller', 'Retimer Redriver', 'RetimerRedriver',
        'Connectivity', 'Imaging', 'Storage', 'Display', 'Security', 'Sensor', 'Memory', 'Audio', 'USB',
    ]
    subsys = ''
    body_start = body.lstrip()
    for s in SUBSYS_LIST:
        if body_start.startswith(s):
            subsys = s
            rest = body_start[len(s):]
            break
    else:
        m = re.match(r'([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)?)', body_start)
        subsys = m.group(1) if m else ''
        rest = body_start[len(subsys):] if subsys else body_start
    result['subsystem'] = subsys

    # Extract Device Category (next chunk before vendor name)
    # Vendor names often start with caps and end with Inc/Corp/Ltd/Tech/Semi/Limited
    VENDORS = [
        'Texas Instruments Inc.', 'Texas Instruments', 'TI ',
        'Renesas Electronics Corporation', 'Renesas',
        'Monolithic Power Systems, Inc.(MPS)', 'Monolithic Power Systems', 'MPS',
        'Cirrus Logic Inc', 'Cirrus Logic',
        'Diodes Incorporated', 'Diodes',
        'Parade Technologies, Ltd.', 'Parade Technologies', 'Parade',
        'NXP Semiconductors.', 'NXP Semiconductors', 'NXP',
        'Nuvoton Technology Corp', 'Nuvoton',
        'STMicroelectronics', 'ST Micro',
        'Infineon Technologies', 'Infineon',
        'Microchip Technology', 'Microchip',
        'Realtek Semiconductor Corp.', 'Realtek',
        'BOSCH SENSORTEC GMBH', 'Robert Bosch (China)', 'BOSCH',
        'OmniVision Technologies', 'OmniVision',
        'Sony Corporation', 'Sony',
        'Samsung Display Co Ltd', 'SAMSUNG Electronics Co., Ltd.', 'Samsung',
        'AU Optronics(AUO)', 'AUO',
        'BOE Technology Group Co., Ltd', 'BOE',
        'Sharp Corporation', 'Sharp',
        'ITE TECH. INC', 'ITE',
        'ELAN Microelectronics Corp', 'ELAN',
        'Wacom Technology Corporation', 'Wacom',
        'Synaptics', 'Semtech', 'ANPECElectronics', 'ANPEC',
        'AlphaandOmegamiconductor Limited', 'AOS',
        'uPISemi', 'uPI',
        'Richtek Technology', 'Richtek',
        'ON Semiconductor', 'Everest Semiconductor',
        'Intel', 'Broadcom', 'Cypress',
        'Silego', 'SILEGO',
        'ALPS', 'Honeywell',
        'Fibocom wireless Inc.', 'Fibocom',
        'Kingcome', 'Sunplusit', 'Henghao Technology Co., Ltd.', 'CSOT',
        'InfoVision Optoelectronics Co., Ltd.', 'Nationz Technologies Inc.', 'Nationz',
        'Azurewave Technologies, Inc',
    ]
    # Sort by length desc to match longest first
    VENDORS_SORTED = sorted(set(VENDORS), key=len, reverse=True)
    vendor = ''
    vendor_pos = -1
    for v in VENDORS_SORTED:
        idx = rest.find(v)
        if idx >= 0 and (vendor_pos < 0 or idx < vendor_pos):
            vendor = v
            vendor_pos = idx
    result['vendor'] = vendor.strip().rstrip(',.')

    if vendor_pos > 0:
        device_cat = rest[:vendor_pos].strip()
        after_vendor = rest[vendor_pos + len(vendor):]
    else:
        device_cat = ''
        after_vendor = rest
    result['device_category'] = device_cat[:60]

    # Part Number: first chunk after vendor up to interface (I2C/SPI/eSPI/USB/MIPI/PCIe/SVID/SoundWire/eDP/PoL)
    INTERFACES = ['I2C', 'I3C', 'SPI', 'eSPI', 'USB2.0', 'USB3.2', 'USB4', 'eUSB2', 'eUSB2.0', 'eUSB2V1',
                  'MIPI CSI', 'MIPI', 'PCIe', 'SVID', 'SoundWire', 'SDCA', 'PDM', 'SNDW', 'eDP',
                  'PoL', 'CNVi', 'CNVio3', 'GbE', 'TCSS', 'HDMI 2.1', 'HDMI', 'I2S', 'ISH I3C', 'ISH I2C',
                  'ISH_I3C', 'ISH_I2C']
    INTERFACES_SORTED = sorted(set(INTERFACES), key=len, reverse=True)
    pn = after_vendor.strip()
    cut = len(pn)
    for iface in INTERFACES_SORTED:
        idx = pn.find(iface)
        if idx >= 0 and idx < cut:
            cut = idx
    pn = pn[:cut].strip().rstrip(',.')
    result['part_number'] = pn[:80]

    return result

entries = []
for sn, body in entries_raw:
    e = parse_entry(sn, body)
    if e.get('subsystem') and e.get('part_number'):
        entries.append(e)

# Save
with open(r'C:\Users\billhsie\AppData\Local\Temp\pcl_entries.json', 'w', encoding='utf-8') as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

print(f"Parsed {len(entries)} entries")
print("\nSample by subsystem:")
from collections import defaultdict
by_subsys = defaultdict(list)
for e in entries:
    by_subsys[e['subsystem']].append(e)
for s, lst in sorted(by_subsys.items()):
    print(f"\n--- {s} ({len(lst)}) ---")
    for e in lst[:5]:
        print(f"  {e['sn']:6} | {e['device_category']:35} | {e['vendor']:30} | {e['part_number']:30} | {e['remarks'][:50]}")
