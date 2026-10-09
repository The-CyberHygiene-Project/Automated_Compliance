#!/usr/bin/env python3
"""Sort the open items of a Rev 3 measurement register into four classes, plus "unsorted".

    python3 triage.py REGISTER.xlsx

parameter      an organization-defined parameter with no value, or a proposed value awaiting the owner
document       an objective the AI found Unmet from documents (or found nothing): the fix is a record or a paragraph
configuration  an objective the AI found Unmet with host evidence: the fix is a setting, checked by the same probe
not_checkable  an objective only a person can check (interview, inspection)
unsorted       an open objective the rules cannot place (for example one the owner edited); never guessed

Read-only. Standard library only. See DESIGN-remediation-triage.md.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "reference"))
import read_xlsx  # noqa: E402

CLASSES = ("parameter", "document", "configuration", "not_checkable", "unsorted")
OPEN_PARAMETER = ("Not defined", "Needs review")
OPEN_OBJECTIVE = ("Not Met", "Not assessed")
MARKER = re.compile(r"^AI scan \((.+?), source (\w+)\)")


def _rows(sheet):
    header, body = sheet[0], sheet[1:]
    return [dict(zip(header, r)) for r in body if r and r[0].strip()]


def load(path):
    book = read_xlsx.read(str(path))
    return _rows(book["Objectives"]), _rows(book["ODPs"])


def _place(row):
    m = MARKER.match((row.get("Evidence reference") or "").strip())
    if not m:
        return "unsorted"
    status, source = m.groups()
    if status == "Not checkable":
        return "not_checkable"
    if status == "Unmet" and source in ("document", "none"):
        return "document"
    if status == "Unmet" and source in ("host", "both"):
        return "configuration"
    return "unsorted"


def triage(objectives, odps):
    out = {c: [] for c in CLASSES}
    for o in objectives:
        if (o.get("Result") or "").strip() in OPEN_OBJECTIVE:
            out[_place(o)].append(o["Objective ID"])
    for p in odps:
        if (p.get("Status") or "").strip() in OPEN_PARAMETER:
            out["parameter"].append(p["ODP ID"])
    return out


def render(result):
    lines = ["# Remediation triage"] + [f"- {c}: {len(result[c])}" for c in CLASSES]
    for c in CLASSES:
        if result[c]:
            lines += ["", f"## {c}"] + [f"- {i}" for i in result[c]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: triage.py REGISTER.xlsx", file=sys.stderr)
        return 2
    print(render(triage(*load(argv[0]))), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
