#!/usr/bin/env python3
"""Compare a measurement register's organization-defined parameters with the DoD values.

    python3 odp_compare.py REGISTER.xlsx DOD_MEMO.txt [KIT objectives.md]

DOD_MEMO.txt is the text of the DoD ODP memo (see dod_odp.py). For each parameter the report gives the DoD value, what
the AI found in the organization's documents, and an action: "adopt" (the documents say nothing: the DoD value is the
starting point), "compare" (the AI found a value or proposed one: a person compares it with the DoD value), or
"no DoD value" (the memo does not cover it). The owner decides; nothing is written to the register. Read-only.
"""
import re
import sys
from pathlib import Path

import dod_odp
import triage

HERE = Path(__file__).resolve().parent


def kit_id(register_id):
    return re.sub(r"\[(\d+)\]", r".\1", register_id)


def _found(basis):
    s = re.sub(r"^AI scan [^:]*\): ", "", basis or "")
    s = re.sub(r"\s*\(a proposal[^)]*\)\s*$", "", s)
    return s.strip()


def compare(odps, dod, mapping):
    rows = []
    for o in odps:
        parts = mapping.get(kit_id(o["ODP ID"]), [])
        values = [dod[p] for p in parts if p in dod]
        value = " / ".join(values)
        status = o.get("Status", "")
        action = "no DoD value" if not value else ("adopt" if status == "Not defined" else "compare")
        rows.append({"odp": o["ODP ID"], "req": o.get("Req ID", ""), "asks": o.get("What must be defined (NIST)", ""),
                     "dod": value, "found": _found(o.get("Basis for the value")), "status": status, "action": action})
    return rows


def render(rows):
    kinds = ("adopt", "compare", "no DoD value")
    lines = ["# Organization-defined parameters against the DoD values"] + \
            [f"- {k}: {sum(1 for r in rows if r['action'] == k)}" for k in kinds] + \
            ["", "| ODP | What must be defined | DoD value | What the documents say | Action |", "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: r["odp"]):
        cell = lambda s: s.replace("|", "/").replace("\n", " ")[:220]
        lines.append(f"| {r['odp']} | {cell(r['asks'])} | {cell(r['dod'])} | {cell(r['found'])} | {r['action']} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print("usage: odp_compare.py REGISTER.xlsx DOD_MEMO.txt [objectives.md]", file=sys.stderr)
        return 2
    kit = Path(argv[2]) if len(argv) > 2 else HERE / "kit-r3" / "objectives.md"
    dod = dod_odp.parse_values(Path(argv[1]).read_text())
    mapping = dod_odp.odp_parts(kit.read_text(), list(dod))
    _, odps = triage.load(argv[0])
    print(render(compare(odps, dod, mapping)), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
