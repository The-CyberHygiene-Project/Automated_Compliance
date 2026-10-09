#!/usr/bin/env python3
"""Export the open items of a Rev 3 measurement register as an OSCAL plan of action and milestones (JSON).

    python3 poam.py REGISTER.xlsx [--out FILE] [--when 2026-10-09T12:00:00Z]

One poam-item per open item (see triage.py), each pointing at an observation that holds the quoted evidence.
Everything is a draft: nothing is accepted until a person accepts it. Rows the AI wrote are marked
"local-ai-unreviewed"; rows a person edited are marked "owner-edited". Item ids are derived from the objective
id, so the same register gives the same ids every time. The document names no organization or person.
Read-only on the register; never overwrites an existing output file. Standard library only.
See DESIGN-remediation-triage.md.
"""
import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import triage

OSCAL_VERSION = "1.1.2"
NAMESPACE = uuid.UUID("5c0b7a52-6f0f-4d3e-9a43-0f2f6c1d7e11")      # fixed, so ids are stable between exports
OBJ_TEXT = "What is measured"                                         # the register's header starts with this
METHODS = {"EXAMINE", "INTERVIEW", "TEST"}
SAYS = {
    "document": "Needs a document or record: the AI assessment found it Unmet from documents, or found no evidence.",
    "configuration": "Needs a configuration check or change: the AI assessment found it Unmet with host evidence. "
                     "It is done only when the same read-only check that failed now succeeds.",
    "not_checkable": "Only a person can check this (interview, inspection or similar); the AI could not.",
    "unsorted": "A person edited this row, so it was not placed automatically.",
}


def _uuid(kind, key):
    return str(uuid.uuid5(NAMESPACE, f"{kind}:{key}"))


def _load(path):
    return triage.load(path)


def _field(row, prefix):
    return next((v for k, v in row.items() if k.startswith(prefix)), "")


def _prop(name, value):
    return {"name": name, "value": value}


def _method(row):
    m = (row.get("Method used") or "").strip().upper()
    return m if m in METHODS else "EXAMINE"


def _collected(row, when):
    d = (row.get("Date assessed") or "").strip()
    return f"{d}T00:00:00Z" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else when


def build(objectives, odps, result, when):
    by_id = {o["Objective ID"]: ("objective", o) for o in objectives}
    by_id.update({p["ODP ID"]: ("parameter", p) for p in odps})
    items, observations = [], []
    for cls in triage.CLASSES:
        for oid in result.get(cls, []):
            kind, row = by_id[oid]
            control = row.get("Req ID", "")
            if kind == "parameter":
                proposed = row.get("Status") == "Needs review"
                what = _field(row, "What must be defined")
                says = ("A value was proposed by the AI and is awaiting the owner's acceptance." if proposed
                        else "No value is defined for this parameter. The owner must decide one.")
                evidence, method, source = row.get("Basis for the value", ""), "EXAMINE", "local-ai-unreviewed"
                collected = when
            else:
                what, says = _field(row, OBJ_TEXT), SAYS[cls]
                evidence, method = row.get("Evidence reference", ""), _method(row)
                source = "local-ai-unreviewed" if evidence.startswith("AI scan (") else "owner-edited"
                collected = _collected(row, when)
            obs_id = _uuid("observation", oid)
            observations.append({"uuid": obs_id, "description": evidence or "(no evidence recorded)",
                                 "methods": [method], "collected": collected})
            items.append({
                "uuid": _uuid("poam-item", oid),
                "title": f"{control} [{oid}] {cls.replace('_', ' ')}",
                "description": f"{what} (objective {oid}, requirement {control}). {says}",
                "props": [_prop("control-id", control), _prop("triage-class", cls), _prop("status", "draft"),
                          _prop("source", source)],
                "related-observations": [{"observation-uuid": obs_id}],
            })
    return {"plan-of-action-and-milestones": {
        "uuid": _uuid("poam", "register"),
        "metadata": {"title": "Plan of action and milestones (draft, AI-assisted)", "last-modified": when,
                     "version": when[:10], "oscal-version": OSCAL_VERSION,
                     "remarks": "Draft. Generated from a measurement register; AI-written rows are unreviewed. "
                                "Nothing here is accepted until a person accepts it."},
        "observations": observations,
        "poam-items": items,
    }}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("register", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--when", default="")
    argv = sys.argv[1:] if argv is None else argv
    a = ap.parse_args(argv)
    if not a.register:
        print("usage: poam.py REGISTER.xlsx [--out FILE] [--when ISO-8601 UTC]", file=sys.stderr)
        return 2
    when = a.when or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = Path(a.out) if a.out else Path(a.register).with_suffix(".poam.json")
    if out.exists():
        print(f"{out} already exists; give --out a new name", file=sys.stderr)
        return 1
    objectives, odps = _load(a.register)
    out.write_text(json.dumps(build(objectives, odps, triage.triage(objectives, odps), when), indent=2) + "\n")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
