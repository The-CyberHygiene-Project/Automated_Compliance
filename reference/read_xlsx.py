"""Minimal xlsx reader (standard library only): {sheet name: [[cell text, ...], ...]}."""
import re, zipfile
import xml.etree.ElementTree as ET
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
def col(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0): n = n * 26 + ord(ch) - 64
    return n - 1
def read(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    out = {}
    for s in wb.find("m:sheets", NS):
        target = rels[s.get("{%s}id" % NS["r"])]
        root = ET.fromstring(z.read("xl/" + target.lstrip("/").replace("xl/", "")))
        rows = []
        for row in root.iter("{%s}row" % NS["m"]):
            cells = {}
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS); t = c.get("t")
                if t == "s" and v is not None: val = shared[int(v.text)]
                elif t == "inlineStr": val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                else: val = v.text if v is not None else ""
                cells[col(c.get("r"))] = " ".join((val or "").split())
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)] if cells else [])
        out[s.get("name")] = rows
    return out
