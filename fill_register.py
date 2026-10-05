#!/usr/bin/env python3
"""Fill a COPY of the Rev 3 Measurement Register with (1) the Rev 2 results, carried over through NIST's mapping,
and (2) the local AI's Rev 3 scan. The original is never touched. Standard library only.

    python3 fill_register.py results/run1-r3-<model> [--out FILE] [--register FILE]

Rules that keep the sheet honest:
- Rev 2 results go on the Requirements sheet (Rev 2 ID, a note, and a status only where Rev 3 barely changed).
- AI results fill Result / Method / Evidence reference on Objectives, marked "Local AI, unreviewed".
- A parameter value the AI found is "Needs review", never "Defined": the owner decides parameters.
- Only cells for items the scan covered are changed; the rest stay as they were.
"""
import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "reference"))
import read_xlsx  # noqa: E402

DEFAULT_REGISTER = Path(os.environ.get("R3_REGISTER", str(HERE / "templates" / "NIST_800-171r3_Measurement_Register.xlsx")))
DEFAULT_OUT = Path.home() / "NIST_800-171r3_Measurement_Register_filled.xlsx"
KEY_PATH = Path(os.environ.get("R3_KEY_DIR", str(Path.home() / "compliance-private" / "r3-key"))) / "answer-key-r3.json"


def set_cell(xml, ref, text):
    """Replace cell `ref` with an inline string, keeping its style (colors, borders, dropdown cell)."""
    pat = re.compile(r'<c r="' + ref + r'"((?:\s+[A-Za-z:]+="[^"]*")*)\s*(?:/>|>.*?</c>)', re.S)
    m = pat.search(xml)
    if not m:
        raise KeyError(ref)
    style = re.search(r'\ss="(\d+)"', m.group(1))
    s = f' s="{style.group(1)}"' if style else ""
    new = f'<c r="{ref}"{s} t="inlineStr"><is><t xml:space="preserve">{escape(text)}</t></is></c>'
    return xml[:m.start()] + new + xml[m.end():]


def result_word(status):
    return {"Met": "Met", "Unmet": "Not Met", "N/A": "N/A"}.get(status, "Not assessed")


def method_word(source):
    return {"host": "Test", "document": "Examine", "library": "Examine", "both": "Combination"}.get(source, "")


def odp_status(status):
    return "Needs review" if status == "Met" else "Not defined"


def implementation_status(k):
    """Only where Rev 3 barely changed (basis carried); never claims 'Not started' from a Rev 2 result."""
    if k["basis"] != "carried":
        return ""
    return {"SATISFIED": "Implemented", "PARTIALLY SATISFIED": "Partially implemented"}.get(k["status"], "")


def _sheets(z):
    wb = z.read("xl/workbook.xml").decode()
    rels = dict(re.findall(r'<Relationship Id="([^"]+)"[^>]*Target="([^"]+)"', z.read("xl/_rels/workbook.xml.rels").decode()))
    rels.update({a: b for b, a in re.findall(r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="([^"]+)"', z.read("xl/_rels/workbook.xml.rels").decode())})
    return {name: "xl/" + rels[rid].lstrip("/").replace("xl/", "")
            for name, rid in re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb)}


def _rownums(xml):
    return [int(n) for n in re.findall(r'<row r="(\d+)"', xml)]


def _ids(rows, rownums, col):
    return {r[col]: rownums[i] for i, r in enumerate(rows) if i > 0 and len(r) > col and r[col]}


def _odp_ref(oid):
    return re.sub(r"\.ODP\.(\d+)$", r".ODP[\1]", oid)


def fill(register, out, key, results_dir, date):
    results = {}
    model = "local model"
    for p in sorted(Path(results_dir).glob("*.json")):
        d = json.loads(p.read_text())
        model = d.get("model", model)
        for r in d["results"]:
            results[r["objective"]] = r
    src = zipfile.ZipFile(register)
    names = _sheets(src)
    xml = {n: src.read(path).decode() for n, path in names.items()}
    data = read_xlsx.read(register)
    # --- Requirements: Rev 2 results
    rows, nums = data["Requirements"], _rownums(xml["Requirements"])
    where = _ids(rows, nums, 1)
    for k in key:
        row = where.get(k["r3"])
        if row is None:
            continue
        if k["r2_sources"]:
            xml["Requirements"] = set_cell(xml["Requirements"], f"H{row}", ", ".join(k["r2_sources"]))
        note = (f"Rev 2 result (derived from the Aug 2026 self-assessment through NIST's mapping; provisional, ISSO to "
                f"confirm): {k['status'] or 'none'}; basis {k['basis']}. {k.get('note', '')}").strip()
        xml["Requirements"] = set_cell(xml["Requirements"], f"L{row}", note)
        st = implementation_status(k)
        if st:
            xml["Requirements"] = set_cell(xml["Requirements"], f"J{row}", st)
    # --- Objectives: AI results
    rows, nums = data["Objectives"], _rownums(xml["Objectives"])
    where = _ids(rows, nums, 0)
    who = f"Local AI ({model}), unreviewed"
    for oid, r in results.items():
        row = where.get(oid)
        if row is None:
            continue
        xml["Objectives"] = set_cell(xml["Objectives"], f"H{row}", result_word(r["status"]))
        if method_word(r["source"]):
            xml["Objectives"] = set_cell(xml["Objectives"], f"I{row}", method_word(r["source"]))
        xml["Objectives"] = set_cell(xml["Objectives"], f"J{row}", f"AI scan ({r['status']}, source {r['source']}): {r['evidence'][:400]}")
        xml["Objectives"] = set_cell(xml["Objectives"], f"K{row}", who)
        xml["Objectives"] = set_cell(xml["Objectives"], f"L{row}", date)
    # --- ODPs: values the AI found are only proposals
    rows, nums = data["ODPs"], _rownums(xml["ODPs"])
    where = _ids(rows, nums, 0)
    for oid, r in results.items():
        if ".ODP." not in oid:
            continue
        row = where.get(_odp_ref(oid))
        if row is None:
            continue
        xml["ODPs"] = set_cell(xml["ODPs"], f"L{row}", f"AI scan {date} ({who}): {r['evidence'][:400]} "
                               "(a proposal: the ISSO decides the value)")
        xml["ODPs"] = set_cell(xml["ODPs"], f"M{row}", odp_status(r["status"]))
    # --- Read Me: say what this copy is
    notes = ["", "THIS COPY WAS PRE-FILLED (2026-10-05)",
             "Requirements sheet: Rev 2 ID(s) from NIST's Rev 2 to Rev 3 mapping; the note column carries the Rev 2 result, derived from the "
             "owner's Aug 2026 self-assessment (provisional; ISSO to confirm). Status is filled only where Rev 3 barely changed.",
             f"Objectives and ODPs sheets: results of a local-AI scan ({model}), assessor 'Local AI, unreviewed'. Items the scan did not cover are untouched.",
             "A parameter value the AI found is 'Needs review', never 'Defined'. Treat this file as CUI-marked system information: do not publish it."]
    rm = xml["Read Me"]
    last = max(_rownums(rm))
    add = "".join(f'<row r="{last + 1 + i}"><c r="A{last + 1 + i}" t="inlineStr"><is><t xml:space="preserve">{escape(t)}</t></is></c></row>'
                  for i, t in enumerate(notes))
    xml["Read Me"] = rm.replace("</sheetData>", add + "</sheetData>", 1)
    wbxml = src.read("xl/workbook.xml").decode()
    if "<calcPr" in wbxml:
        wbxml = re.sub(r"<calcPr[^>]*/>", '<calcPr fullCalcOnLoad="1"/>', wbxml)
    else:
        tag = "</definedNames>" if "</definedNames>" in wbxml else "</sheets>"
        wbxml = wbxml.replace(tag, tag + '<calcPr fullCalcOnLoad="1"/>', 1)
    changed = {names[n]: xml[n] for n in xml}
    changed["xl/workbook.xml"] = wbxml
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in src.infolist():
            payload = changed[item.filename].encode() if item.filename in changed else src.read(item.filename)
            zout.writestr(item, payload)
    return len(results)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", help="results folder of a Rev 3 run, e.g. results/run1-r3-<model>")
    ap.add_argument("--register", default=str(DEFAULT_REGISTER))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--date", default=__import__("time").strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    n = fill(a.register, a.out, json.loads(KEY_PATH.read_text()), a.results, a.date)
    print(f"Wrote {a.out}: Rev 2 results on 97 requirements, {n} AI results from {a.results}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
