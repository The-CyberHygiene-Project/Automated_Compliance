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


def default_out(date):
    """A dated name, so a new run never lands on a file the owner has been editing."""
    return Path.home() / f"NIST_800-171r3_Measurement_Register_filled_{date}.xlsx"


def load_key():
    """The provisional Rev 2 carry-over key, or [] when there is none (then Rev 2 prefill is skipped)."""
    try:
        return json.loads(KEY_PATH.read_text())
    except (OSError, ValueError):
        return []
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


def _n(text):
    """Whitespace-normalised text: the spreadsheet reader collapses line breaks and runs of spaces, so every
    comparison between a cell and what the AI wrote goes through this."""
    return " ".join(str(text).split())


class NoRecord(Exception):
    """The workbook has no record of what the AI wrote, so a merge cannot tell the AI's cells from the owner's."""


# Cells that mean "nobody has touched this yet" in the template.
DEFAULTS = {"Objectives!H": "Not assessed", "ODPs!M": "Not defined", "Requirements!J": "Not started"}
# Columns the AI never writes but the owner fills in: if any is non-blank, the owner is working on that row.
OWNER_COLUMNS = {"ODPs": "IJK", "Requirements": "IK"}


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


def _col(letter):
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


class _Book:
    """A workbook's sheet XML plus its cell values, with lookups by id and by cell reference."""

    def __init__(self, path):
        self.path = Path(path)
        z = zipfile.ZipFile(path)
        self.names = _sheets(z)
        self.xml = {n: z.read(p).decode() for n, p in self.names.items()}
        z.close()
        self.data = read_xlsx.read(path)

    def row_of(self, sheet, id_col, oid):
        return _ids(self.data[sheet], _rownums(self.xml[sheet]), id_col).get(oid)

    def value(self, sheet, ref):
        m = re.fullmatch(r"([A-Z]+)(\d+)", ref)
        nums = _rownums(self.xml[sheet])
        try:
            row = self.data[sheet][nums.index(int(m.group(2)))]
        except ValueError:
            return ""
        c = _col(m.group(1))
        return row[c] if len(row) > c else ""


def _rowof(path, sheet, id_col, oid):
    return _Book(path).row_of(sheet, id_col, oid)


def _load_results(results_dir):
    results, model = {}, "local model"
    for p in sorted(Path(results_dir).glob("*.json")):
        d = json.loads(p.read_text())
        model = d.get("model", model)
        for r in d["results"]:
            results[r["objective"]] = r
    return results, model


def plan(book, key, results, model, date):
    """Every cell the AI scan would write, as (sheet, cell, text, label)."""
    out = []
    for k in key:
        row = book.row_of("Requirements", 1, k["r3"])
        if row is None:
            continue
        if k["r2_sources"]:
            out.append(("Requirements", f"H{row}", ", ".join(k["r2_sources"]), k["r3"]))
        note = (f"Rev 2 result (derived from the Aug 2026 self-assessment through NIST's mapping; provisional, ISSO to "
                f"confirm): {k['status'] or 'none'}; basis {k['basis']}. {k.get('note', '')}").strip()
        out.append(("Requirements", f"L{row}", note, k["r3"]))
        st = implementation_status(k)
        if st:
            out.append(("Requirements", f"J{row}", st, k["r3"]))
    who = f"Local AI ({model}), unreviewed"
    for oid, r in results.items():
        if ".ODP." in oid:
            row = book.row_of("ODPs", 0, _odp_ref(oid))
            if row is None:
                continue
            out.append(("ODPs", f"L{row}", f"AI scan {date} ({who}): {r['evidence'][:400]} (a proposal: the ISSO decides the value)", oid))
            out.append(("ODPs", f"M{row}", odp_status(r["status"]), oid))
        else:
            row = book.row_of("Objectives", 0, oid)
            if row is None:
                continue
            out.append(("Objectives", f"H{row}", result_word(r["status"]), oid))
            if method_word(r["source"]):
                out.append(("Objectives", f"I{row}", method_word(r["source"]), oid))
            out.append(("Objectives", f"J{row}", f"AI scan ({r['status']}, source {r['source']}): {r['evidence'][:400]}", oid))
            out.append(("Objectives", f"K{row}", who, oid))
            out.append(("Objectives", f"L{row}", date, oid))
    return out


def _apply(src, out, writes, notes):
    z = zipfile.ZipFile(src)
    names = _sheets(z)
    xml = {n: z.read(p).decode() for n, p in names.items()}
    for sheet, ref, text, _label in writes:
        xml[sheet] = set_cell(xml[sheet], ref, text)
    if notes:
        rm = xml["Read Me"]
        last = max(_rownums(rm))
        add = "".join(f'<row r="{last + 1 + i}"><c r="A{last + 1 + i}" t="inlineStr"><is><t xml:space="preserve">{escape(t)}</t></is></c></row>'
                      for i, t in enumerate(notes))
        xml["Read Me"] = rm.replace("</sheetData>", add + "</sheetData>", 1)
    wbxml = z.read("xl/workbook.xml").decode()
    if "<calcPr" in wbxml:
        wbxml = re.sub(r"<calcPr[^>]*/>", '<calcPr fullCalcOnLoad="1"/>', wbxml)
    else:
        tag = "</definedNames>" if "</definedNames>" in wbxml else "</sheets>"
        wbxml = wbxml.replace(tag, tag + '<calcPr fullCalcOnLoad="1"/>', 1)
    changed = {names[n]: xml[n] for n in xml}
    changed["xl/workbook.xml"] = wbxml
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in z.infolist():
            zout.writestr(item, changed[item.filename].encode() if item.filename in changed else z.read(item.filename))
    z.close()


def _record_path(path):
    return Path(str(path) + ".aimeta.json")


def _fill_notes(model, date):
    return ["", f"THIS COPY WAS PRE-FILLED ({date})",
            "Requirements sheet: Rev 2 ID(s) from NIST's Rev 2 to Rev 3 mapping; the note column carries the Rev 2 result, derived from the "
            "owner's Aug 2026 self-assessment (provisional; ISSO to confirm). Status is filled only where Rev 3 barely changed.",
            f"Objectives and ODPs sheets: results of a local-AI scan ({model}), assessor 'Local AI, unreviewed'. Items the scan did not cover are untouched.",
            "A parameter value the AI found is 'Needs review', never 'Defined'. Treat this file as CUI-marked system information: do not publish it.",
            "A file named like this one plus '.aimeta.json' records what the AI wrote, so a later scan can be merged without touching your edits."]


def fill(register, out, key, results_dir, date, force=False):
    """A new filled copy of the (blank) register; never overwrites an existing file unless force."""
    if Path(out).exists() and not force:
        raise FileExistsError(f"{out} already exists and may hold your edits; give --out a new name (or --force to replace it)")
    results, model = _load_results(results_dir)
    book = _Book(register)
    writes = plan(book, key, results, model, date)
    _apply(register, out, writes, _fill_notes(model, date))
    _record_path(out).write_text(json.dumps({f"{s}!{r}": t for s, r, t, _ in writes}, indent=0))
    return len(results)


def merge(existing, out, key, results_dir, date):
    """Write a NEW file from `existing` plus a new scan, keeping every cell the owner has changed.

    A row (objective, parameter or requirement) is kept as it is when the owner changed any cell the AI wrote there,
    or typed into a column the AI never writes (a parameter's value, decided by, date; a requirement's owner or
    evidence location). Everything else is refreshed. `existing` is not modified."""
    if Path(out).exists():
        raise FileExistsError(f"{out} already exists; give --out a new name")
    rec_path = _record_path(existing)
    if not rec_path.exists():
        raise NoRecord(f"no record of what the AI wrote in {existing}: run  fill_register.py --adopt {existing} <results of the scan that filled it>")
    record = json.loads(rec_path.read_text())
    results, model = _load_results(results_dir)
    book = _Book(existing)
    writes = plan(book, key, results, model, date)
    groups = {}
    for s, ref, text, label in writes:
        groups.setdefault((s, label), []).append((ref, text))
    keep, kept = set(), []
    for (s, label), cells in groups.items():
        edited = []
        for ref, _ in cells:
            cur, rec = _n(book.value(s, ref)), record.get(f"{s}!{ref}")
            default = DEFAULTS.get(f"{s}!{re.match(r'[A-Z]+', ref).group(0)}", "")
            if (rec is not None and cur != _n(rec)) or (rec is None and cur not in ("", default)):
                edited.append(ref)
        row = re.match(r"[A-Z]+(\d+)", cells[0][0]).group(1)
        for c in OWNER_COLUMNS.get(s, ""):
            if book.value(s, f"{c}{row}"):
                edited.append(f"{c}{row}")
        if edited:
            keep.add((s, label))
            kept.append({"what": f"{s} {label}", "edited": edited})
    todo = [w for w in writes if (w[0], w[3]) not in keep]
    notes = ["", f"MERGED {date}: the AI cells were refreshed from a new scan ({model}); rows you had edited were kept as they were."]
    _apply(existing, out, todo, notes)
    record.update({f"{s}!{r}": t for s, r, t, _ in todo})
    _record_path(out).write_text(json.dumps(record, indent=0))
    return {"written": len(todo), "kept": kept, "rows_refreshed": len({(w[0], w[3]) for w in todo})}


def adopt(existing, key, results_dir, date):
    """Rebuild the record for a register that an earlier run filled (before records existed): note every cell that
    still holds exactly what that scan wrote. `date` must be the date of that earlier fill."""
    results, model = _load_results(results_dir)
    book = _Book(existing)
    writes = plan(book, key, results, model, date)
    record = {f"{s}!{r}": t for s, r, t, _ in writes if _n(book.value(s, r)) == _n(t)}
    _record_path(existing).write_text(json.dumps(record, indent=0))
    return len(record)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results", help="results folder of a Rev 3 run, e.g. results/run1-r3-<model>")
    ap.add_argument("--register", default=str(DEFAULT_REGISTER))
    ap.add_argument("--out", default=None, help="default: a dated file in your home folder")
    ap.add_argument("--into", help="merge this scan into an existing filled register (new file; yours is not touched)")
    ap.add_argument("--adopt", help="rebuild the AI record for a register filled by an earlier run (use with --date of that fill)")
    ap.add_argument("--force", action="store_true", help="replace an existing output file")
    ap.add_argument("--date", default=__import__("time").strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)
    key = load_key()
    if a.adopt:
        print(f"Recorded {adopt(a.adopt, key, a.results, a.date)} AI-written cells for {a.adopt}")
        return 0
    out = a.out or str(default_out(a.date))
    if a.into:
        try:
            r = merge(a.into, out, key, a.results, a.date)
        except (NoRecord, FileExistsError) as exc:
            print(exc)
            return 2
        print(f"Wrote {out}: {r['written']} cells refreshed on {r['rows_refreshed']} rows; kept your edits on {len(r['kept'])} rows:")
        for k in r["kept"][:40]:
            print(f"  kept {k['what']} (you changed {', '.join(k['edited'])})")
        return 0
    n = fill(a.register, out, key, a.results, a.date, force=a.force)
    print(f"Wrote {out}: Rev 2 results on {len(key)} requirements, {n} AI results from {a.results}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
