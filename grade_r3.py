#!/usr/bin/env python3
"""Grade a Rev 3 AI assessment against the provisional derived key (key_r3.py). Runs OUTSIDE the sandbox.

    python3 grade_r3.py results/run1-r3-<model>/assessment.md [MODEL-NAME] > grade-r3.md

Requirement level only (see key_r3.py). The report also lists every organization-defined parameter the AI could
not find a value for: for the owner that is a to-do list, not a score."""
import json
import os
import re
import sys
from pathlib import Path

import grade

KEY_PATH = Path(os.environ.get("R3_KEY_DIR", str(Path.home() / "compliance-private" / "r3-key"))) / "answer-key-r3.json"
ID = re.compile(r"^A\.\d{2}\.\d{2}\.\d{2}(?:\.[A-Za-z0-9]+)+$")
CLASS = {"SATISFIED": "Met", "OTHER THAN SATISFIED": "Unmet", "PARTIALLY SATISFIED": "Partial"}
ORDER = {"Met": 0, "Partial": 1, "Unmet": 2}


def parse_ai(text):
    """{objective: (status, source, evidence)} and problems."""
    rows, problems = {}, []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        oid = cols[0].replace("*", "").replace("`", "").strip()
        if not ID.match(oid):
            continue
        status = grade._ai_status(cols[1]) if len(cols) > 1 else None
        if status is None:
            problems.append(f"unreadable status for {oid}: {cols[1] if len(cols) > 1 else ''!r}")
        elif oid in rows:
            problems.append(f"duplicate answer for {oid} (first kept)")
        else:
            rows[oid] = (status, cols[2].lower() if len(cols) > 2 else "", cols[3] if len(cols) > 3 else "")
    return rows, problems


def split(rows):
    return ({k: v for k, v in rows.items() if ".ODP." not in k}, {k: v for k, v in rows.items() if ".ODP." in k})


def requirement_status(req_rows):
    """{requirement: Met | Partial | Unmet | Not checkable} from its non-parameter objectives."""
    by = {}
    for oid, (st, *_rest) in req_rows.items():
        by.setdefault(oid[2:10], []).append(st)
    out = {}
    for req, sts in by.items():
        judged = [s for s in sts if s in ("Met", "Unmet")]
        na = [s for s in sts if s == "N/A"]
        if not judged:
            out[req] = "N/A" if na and len(na) == len(sts) else "Not checkable"
        elif all(s == "Met" for s in judged):
            out[req] = "Met" if len(judged) + len(na) == len(sts) else "Partial"
        elif all(s == "Unmet" for s in judged):
            out[req] = "Unmet"
        else:
            out[req] = "Partial"
    return out


def compare(rows, key):
    req_rows, _ = split(rows)
    ai = requirement_status(req_rows)
    r = {"agree": [], "lenient": [], "stricter": [], "new": [], "no_answer": [], "not_checkable": []}
    for k in key:
        req, basis, exp = k["r3"], k["basis"], k["status"]
        got = ai.get(req)
        if got is None:
            r["no_answer"].append(req)
        elif basis == "new" or exp is None:
            r["new"].append((req, got))
        elif got in ("Not checkable", "N/A") or exp not in CLASS:
            r["not_checkable"].append((req, got, exp, basis))
        elif got == CLASS[exp]:
            r["agree"].append((req, got, exp, basis))
        elif ORDER[got] < ORDER[CLASS[exp]]:
            r["lenient"].append((req, got, exp, basis))
        else:
            r["stricter"].append((req, got, exp, basis))
    return r


def _table(items, cols):
    return "\n".join(f"| {' | '.join(str(c) for c in i)} |" for i in items) or f"| (none) |{' |' * (cols - 1)}"


def report(r, rows, problems, model):
    _, odp = split(rows)
    unmet_odp = [(k, v[2][:160]) for k, v in sorted(odp.items()) if v[0] != "Met"]
    out = [f"# 800-171A Rev 3 local-AI test: grade ({model})", "",
           "**Provisional.** The key is derived from the owner's Rev 2 determinations through NIST's mapping, at "
           "requirement level; it is not an independent Rev 3 determination. A disagreement is a question for the "
           "ISSO. For a requirement whose basis is *ceiling*, Rev 2 is a best case: AI below it may be right "
           "(Rev 3 asks for more); AI above it deserves a look.", "",
           f"| Measure | Count |", "| --- | --- |", f"| Agree | {len(r['agree'])} |",
           f"| AI more lenient than the key | {len(r['lenient'])} |", f"| AI stricter than the key | {len(r['stricter'])} |",
           f"| New in Rev 3 (no key; ISSO reviews) | {len(r['new'])} |", f"| AI said not checkable / N/A | {len(r['not_checkable'])} |",
           f"| No answer | {len(r['no_answer'])} |", f"| Parameters answered | {len(odp)} (not met: {len(unmet_odp)}) |", "",
           "## AI more lenient than the key (review first)", "", "| Requirement | AI | Key | Basis |", "| --- | --- | --- | --- |",
           _table(r["lenient"], 4), "", "## AI stricter than the key", "", "| Requirement | AI | Key | Basis |", "| --- | --- | --- | --- |",
           _table(r["stricter"], 4), "", "## New in Rev 3: the AI's view, for the ISSO", "", "| Requirement | AI |", "| --- | --- |",
           _table(r["new"], 2), "", "## Parameters with no stated value (a to-do list for the owner)", "",
           "| Parameter | What the AI found |", "| --- | --- |", _table(unmet_odp, 2), "", "## Problems reading the AI's file", ""]
    out += [f"- {p}" for p in problems] or ["- none"]
    out += ["", "## No answer from the AI", "", ", ".join(r["no_answer"]) or "none", ""]
    return "\n".join(out)


def main(argv):
    path = Path(argv[1])
    model = argv[2] if len(argv) > 2 else "model not named"
    rows, problems = parse_ai(path.read_text())
    print(report(compare(rows, json.loads(KEY_PATH.read_text())), rows, problems, model))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
