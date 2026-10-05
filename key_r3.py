#!/usr/bin/env python3
"""Provisional Rev 3 answer key, DERIVED from the owner's Rev 2 determinations through NIST's own Rev 2 to Rev 3
mapping (sp800-171r2-to-r3-analysis.xlsx). It is not an independent determination, and it is requirement-level:
NIST publishes no objective-level mapping, and the parameter objectives (ODP) are new in Rev 3, so they have no key.

    python3 key_r3.py            writes $R3_KEY_DIR/answer-key-r3.json and .md (default ~/compliance-private/r3-key,
                                 outside the AI's reach: the sandbox blocks ~/compliance-private)

basis:  carried  Rev 2 wording changed little: the Rev 2 determination is the expected Rev 3 one
        ceiling  significant change or new parameter: the Rev 2 determination is a best case; Rev 3 may be worse
        new      no Rev 2 counterpart: no key; the ISSO decides
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reference"))

OUT = Path(os.environ.get("R3_KEY_DIR", str(Path.home() / "compliance-private" / "r3-key")))
PROVENANCE = ("derived from the owner's Rev 2 determinations (August 2026 self-assessment, re-determinations "
              "applied) through NIST's Rev 2 to Rev 3 mapping; not an independent determination; ISSO to confirm")
CARRIED = {"no significant change", "minor change"}


def aggregate(statuses):
    s = {x for x in statuses if x}
    if not s:
        return None
    if s == {"SATISFIED"} or s == {"OTHER THAN SATISFIED"} or s == {"UNVERIFIED"} or s == {"NOT APPLICABLE"}:
        return next(iter(s))
    if "UNVERIFIED" in s and "OTHER THAN SATISFIED" not in s:
        return "UNVERIFIED"
    if s <= {"SATISFIED", "NOT APPLICABLE"}:
        return "SATISFIED"
    return "PARTIALLY SATISFIED"


def r2_by_requirement(key):
    """{ '3.1.1': status } from the Rev 2 key's per-objective statuses (single objectives have no letter)."""
    grouped = {}
    for oid, st in key.items():
        grouped.setdefault(oid.split("[")[0], []).append(st)
    return {req: aggregate(v) for req, v in grouped.items()}


def build(mapping, incorporated, r2, in_force):
    """mapping: [(r2 id, r3 id, change type)]; incorporated: {withdrawn r3 id: r3 id that absorbed it};
    r2: {r2 requirement: status}; in_force: the Rev 3 requirement ids that are in force."""
    rows = {r3: (r2id, change) for r2id, r3, change in mapping if r3}
    absorbed = {}
    for wd, into in incorporated.items():
        if wd in rows and rows[wd][0]:
            absorbed.setdefault(into, []).append(rows[wd][0])
    out = []
    for r3 in in_force:
        r2id, change = rows.get(r3, ("", "New Requirement"))
        sources = ([r2id] if r2id else []) + absorbed.get(r3, [])
        if not sources:
            basis, note = "new", "new in Rev 3; no Rev 2 counterpart"
        else:
            ceiling = change.lower() not in CARRIED
            basis = "ceiling" if ceiling else "carried"
            note = f"change from Rev 2: {change}" + (f"; also absorbs withdrawn {', '.join(absorbed[r3])}" if r3 in absorbed else "")
        status = aggregate([r2.get(s) for s in sources])
        if sources and status is None:
            note += "; the Rev 2 key never assessed it"
        out.append({"r3": r3, "r2_sources": sources, "basis": basis, "status": status, "note": note,
                    "provenance": PROVENANCE})
    return out


def main():
    import grade
    import read_xlsx
    import assess
    kit2 = grade.kit_ids((HERE / "objectives.md").read_text())
    key2, _ = grade.parse_key(grade.KEY_PATH.read_text(), kit2)
    agg = r2_by_requirement(key2)
    sheet = read_xlsx.read(HERE / "reference" / "sp800-171r2-to-r3-analysis.xlsx")["Change Analysis 800-171 R2-R3"][1:]
    mapping = []
    for r in (x + [""] * (16 - len(x)) for x in sheet):
        kinds = ["No Significant Change", "Significant Change", "Minor Change", "New ODP", "New Requirement",
                 "Withdrawn"]
        flagged = [k for k, c in zip(kinds, r[9:15]) if c == "X"]
        change = "Withdrawn" if "Withdrawn" in flagged else (
            "Significant Change" if "Significant Change" in flagged else (
                "New ODP" if "New ODP" in flagged else (flagged[0] if flagged else "Minor Change")))
        mapping.append((r[2], r[6], change))
    cat = json.load(open(HERE / "reference" / "NIST_SP800-171_rev3_catalog.json"))["catalog"]
    incorporated = {}
    for g in cat["groups"]:
        for c in g.get("controls", []):
            for lk in c.get("links", []):
                if lk["rel"] in ("incorporated_into", "addressed_by"):
                    incorporated[c["id"].replace("SP_800_171_", "")] = lk["href"]
    reqs = assess.requirements((HERE / "kit-r3" / "objectives.md").read_text())
    rows = build(mapping, incorporated, agg, [r["id"] for r in reqs])
    titles = {r["id"]: r["text"] for r in reqs}
    for r in rows:
        r["title"] = titles[r["r3"]]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "answer-key-r3.json").write_text(json.dumps(rows, indent=1))
    (OUT / "answer-key-r3.md").write_text(render(rows))
    c = {}
    for r in rows:
        c[(r["basis"], r["status"])] = c.get((r["basis"], r["status"]), 0) + 1
    print(len(rows), "Rev 3 requirements;", dict(sorted(c.items(), key=str)))
    return 0


def render(rows):
    n = {b: sum(1 for r in rows if r["basis"] == b) for b in ("carried", "ceiling", "new")}
    out = ["# Rev 3 answer key (provisional, derived)", "",
           f"Derived from the owner's Rev 2 determinations through NIST's Rev 2 to Rev 3 mapping. **{PROVENANCE.split(';')[1].strip().capitalize()}; "
           "ISSO to confirm.** It is requirement-level: NIST gives no objective-level mapping, and the 88 parameter "
           "objectives are new in Rev 3, so they have no key.", "",
           f"{len(rows)} requirements in force: {n['carried']} carried (little changed), {n['ceiling']} ceiling "
           f"(Rev 2 result is a best case), {n['new']} new (no key).", "",
           "| Rev 3 | Requirement | Basis | Expected | From Rev 2 | Note |", "|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['r3']} | {r['title']} | {r['basis']} | {r['status'] or 'no key'} | {', '.join(r['r2_sources']) or '-'} | {r['note']} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
