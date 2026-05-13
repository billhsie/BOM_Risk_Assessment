"""
BOM Reader Script
Reads a BOM Excel file and outputs JSON for Copilot to analyze.

Usage:
    py bom_reader.py --input <bom_file.xlsx> [--sheet <sheet_name>]

Output (stdout): JSON array of BOM rows
"""

import argparse
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
import re


def parse_shared_strings(zip_file):
    """Parse xl/sharedStrings.xml and return list of strings."""
    strings = []
    try:
        with zip_file.open("xl/sharedStrings.xml") as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in root.findall("x:si", ns):
                # Collect all <t> text inside <si>, handling rich text <r><t> 
                parts = []
                for elem in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
                    if elem.text:
                        parts.append(elem.text)
                strings.append("".join(parts))
    except KeyError:
        pass  # No shared strings
    return strings


def get_sheet_map(zip_file):
    """Return dict of sheet name -> sheet xml path."""
    sheet_map = {}
    with zip_file.open("xl/workbook.xml") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
              "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
        sheets = root.findall(".//x:sheet", ns)
        for s in sheets:
            name = s.get("name")
            rid = s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            sheet_map[name] = rid

    # Read relationships to get actual file paths
    rels = {}
    with zip_file.open("xl/_rels/workbook.xml.rels") as f:
        tree = ET.parse(f)
        root = tree.getroot()
        for rel in root.findall("*"):
            rels[rel.get("Id")] = "xl/" + rel.get("Target").lstrip("/").replace("xl/", "")

    return {name: rels.get(rid, "") for name, rid in sheet_map.items()}


def col_letter_to_index(col_str):
    """Convert column letter(s) like 'A','B','AA' to 0-based index."""
    result = 0
    for ch in col_str.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result - 1


def parse_cell_ref(ref):
    """Parse cell reference like 'A1' -> (col_index, row_index) both 0-based."""
    match = re.match(r"([A-Za-z]+)(\d+)", ref)
    if not match:
        return 0, 0
    col_str, row_str = match.group(1), match.group(2)
    return col_letter_to_index(col_str), int(row_str) - 1


def read_sheet(zip_file, sheet_path, strings):
    """Read a worksheet and return list of rows (each row is list of cell values)."""
    rows_data = {}
    try:
        with zip_file.open(sheet_path) as f:
            tree = ET.parse(f)
            root = tree.getroot()
            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for row_elem in root.findall(".//x:row", ns):
                row_idx = int(row_elem.get("r", 1)) - 1
                cells = {}
                for c in row_elem.findall("x:c", ns):
                    ref = c.get("r", "")
                    col_idx, _ = parse_cell_ref(ref)
                    t = c.get("t", "")
                    v_elem = c.find("x:v", ns)
                    v = v_elem.text if v_elem is not None else None

                    if t == "s" and v is not None:
                        # Shared string
                        val = strings[int(v)] if int(v) < len(strings) else ""
                    elif t == "inlineStr":
                        is_elem = c.find(".//x:t", ns)
                        val = is_elem.text if is_elem is not None else ""
                    else:
                        val = v or ""
                    cells[col_idx] = val
                rows_data[row_idx] = cells
    except (KeyError, ET.ParseError) as e:
        print(f"Error reading sheet: {e}", file=sys.stderr)
    return rows_data


def rows_to_list(rows_data):
    """Convert {row_idx: {col_idx: val}} to list of lists."""
    if not rows_data:
        return []
    max_row = max(rows_data.keys())
    max_col = max(max(c for c in row.keys()) for row in rows_data.values() if row)
    result = []
    for r in range(max_row + 1):
        row = rows_data.get(r, {})
        result.append([row.get(c, "") for c in range(max_col + 1)])
    return result


def main():
    parser = argparse.ArgumentParser(description="Read BOM Excel and output JSON")
    parser.add_argument("--input", required=True, help="Path to input BOM Excel (.xlsx)")
    parser.add_argument("--sheet", default=None, help="Sheet name (default: all sheets)")
    args = parser.parse_args()

    try:
        with zipfile.ZipFile(args.input, "r") as zf:
            strings = parse_shared_strings(zf)
            sheet_map = get_sheet_map(zf)

            output = {}
            sheets_to_read = [args.sheet] if args.sheet else list(sheet_map.keys())

            for sheet_name in sheets_to_read:
                if sheet_name not in sheet_map:
                    print(f"Warning: sheet '{sheet_name}' not found. Available: {list(sheet_map.keys())}", file=sys.stderr)
                    continue
                sheet_path = sheet_map[sheet_name]
                rows_data = read_sheet(zf, sheet_path, strings)
                rows_list = rows_to_list(rows_data)

                if not rows_list:
                    continue

                # First row is header
                headers = rows_list[0]
                bom_rows = []
                for row in rows_list[1:]:
                    # Pad row to header length
                    while len(row) < len(headers):
                        row.append("")
                    entry = {
                        "subsystem": row[0] if len(row) > 0 else "",
                        "old_component": row[1] if len(row) > 1 else "",
                        "new_component": row[2] if len(row) > 2 else "",
                        "existing_risk": row[3] if len(row) > 3 else "",
                    }
                    # Skip completely empty rows
                    if any(entry.values()):
                        bom_rows.append(entry)

                output[sheet_name] = {
                    "headers": {
                        "subsystem": headers[0] if len(headers) > 0 else "Subsystem",
                        "old_platform": headers[1] if len(headers) > 1 else "Old Platform",
                        "new_platform": headers[2] if len(headers) > 2 else "New Platform",
                        "risk_col": headers[3] if len(headers) > 3 else "Risk Assessment & Recommendation",
                    },
                    "rows": bom_rows
                }

        print(json.dumps(output, ensure_ascii=False, indent=2))

    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except zipfile.BadZipFile:
        print(f"Error: Not a valid xlsx file: {args.input}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
