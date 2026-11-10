#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Compute NIST 800-171 family status directly from the 800-171A assessment.

Why this exists
---------------
The Admin Portal's family table was hand-transcribed into the SSP and copied
from there into HTML.  The transcription was faithful, but it is a manual step
between the evidence and the display, and it reports only *requirements fully
met* — a binary measure that hides all partial progress.  A requirement at 5 of
6 objectives is indistinguishable from one at 0 of 6.

This computes both measures straight from the assessment:

  * requirements met   — every objective SATISFIED (the SPRS-relevant measure)
  * objectives passing — how much of the work is actually done

Assessment table formats handled (the document uses all four):
  1. `## 3.x.y — title` sections with `| [a] | text | STATUS |` rows
  2. the same with a Method column: `| [a] | text | T | STATUS |`
  3. condensed tables where the requirement is the first cell:
     `| 3.8.1 | [a] | text | STATUS |`
  4. rows with no objective marker: `| 3.10.3 | text | STATUS |`

A combined objective cell such as `[a]/[b]` counts as TWO objectives.

Usage:  assessment-status.py [--file PATH] [--json]
"""

import argparse
import collections
import json
import os
import re
import sys

DEFAULT = ("/opt/local/nextcloud/data/__groupfolders/1/files/Compliance/"
           "Assessment/CUI_800-171A_Self_Assessment_2026-08.md")

FAMILY = {
    "3.1": ("AC", "Access Control"),
    "3.2": ("AT", "Awareness & Training"),
    "3.3": ("AU", "Audit & Accountability"),
    "3.4": ("CM", "Configuration Management"),
    "3.5": ("IA", "Identification & Authentication"),
    "3.6": ("IR", "Incident Response"),
    "3.7": ("MA", "Maintenance"),
    "3.8": ("MP", "Media Protection"),
    "3.9": ("PS", "Personnel Security"),
    "3.10": ("PE", "Physical Protection"),
    "3.11": ("RA", "Risk Assessment"),
    "3.12": ("CA", "Security Assessment"),
    "3.13": ("SC", "System & Comms Protection"),
    "3.14": ("SI", "System & Info Integrity"),
}
ORDER = ["AC", "AT", "AU", "CM", "IA", "IR", "MA", "MP",
         "PS", "PE", "RA", "CA", "SC", "SI"]

STATUSES = {"SATISFIED", "PARTIALLY SATISFIED", "OTHER THAN SATISFIED",
            "UNVERIFIED", "NOT APPLICABLE"}

REQ_RE = re.compile(r"^3\.\d{1,2}\.\d{1,2}$")
# The assessment writes objective cells three ways:
#   [a]            one objective
#   [a]/[b]        two objectives combined in one row
#   [a]–[c]        a RANGE covering three objectives (en-dash or hyphen)
# Counting a range as one objective understates the family - it made Physical
# Protection read 1/8 when 3.10.1 alone satisfies three objectives (really 3/10).
OBJ_RE = re.compile(r"^\[[a-z]\](\s*[/–—-]\s*\[[a-z]\])*$")
RANGE_RE = re.compile(r"^\[([a-z])\]\s*[–—-]\s*\[([a-z])\]$")


def count_objectives(cell):
    """How many 800-171A objectives does this cell document?"""
    cell = cell.strip()
    rng = RANGE_RE.match(cell)
    if rng:
        return ord(rng.group(2)) - ord(rng.group(1)) + 1
    if OBJ_RE.match(cell):
        return len(re.findall(r"\[[a-z]\]", cell))
    return 1


def parse(text):
    """Return {requirement_id: [status, ...]} — one entry per objective."""
    reqs = collections.defaultdict(list)
    current = None

    for line in text.splitlines():
        head = re.match(r"^#{2,3}\s+(3\.\d{1,2}\.\d{1,2})", line)
        if head:
            current = head.group(1)
            continue
        if not line.lstrip().startswith("|"):
            continue

        cells = [re.sub(r"\*+", "", c).strip()
                 for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue

        status = cells[-1].upper()
        if status not in STATUSES:
            continue                      # header row, separator, or prose

        # Which requirement does this row belong to?
        if REQ_RE.match(cells[0]):
            rid = cells[0]
            objcell = cells[1] if len(cells) > 2 else ""
        else:
            rid = current
            objcell = cells[0]
        if not rid:
            continue

        reqs[rid].extend([status] * count_objectives(objcell))

    return dict(reqs)


def summarise(reqs):
    fam = {ab: {"abbrev": ab, "name": nm, "reqs": 0, "reqs_met": 0,
                "objs": 0, "objs_pass": 0}
           for ab, nm in FAMILY.values()}
    for rid, sts in reqs.items():
        key = ".".join(rid.split(".")[:2])
        if key not in FAMILY:
            continue
        ab = FAMILY[key][0]
        f = fam[ab]
        f["reqs"] += 1
        f["objs"] += len(sts)
        f["objs_pass"] += sum(1 for s in sts if s == "SATISFIED")
        if all(s == "SATISFIED" for s in sts):
            f["reqs_met"] += 1
    return fam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.file):
        sys.exit(f"assessment not found: {args.file}")

    reqs = parse(open(args.file).read())
    fam = summarise(reqs)

    if args.json:
        print(json.dumps({"families": [fam[a] for a in ORDER],
                          "requirements": len(reqs)}, indent=2))
        return

    tr = sum(fam[a]["reqs"] for a in ORDER)
    tm = sum(fam[a]["reqs_met"] for a in ORDER)
    to = sum(fam[a]["objs"] for a in ORDER)
    tp = sum(fam[a]["objs_pass"] for a in ORDER)

    print(f"  {'Family':<28} {'Reqs':>5} {'Met':>5} {'Objs':>6} {'Pass':>5} {'Obj %':>7}")
    print(f"  {'-'*28} {'-'*5} {'-'*5} {'-'*6} {'-'*5} {'-'*7}")
    for ab in ORDER:
        f = fam[ab]
        pct = round(100 * f["objs_pass"] / f["objs"]) if f["objs"] else 0
        print(f"  {f['name']:<28} {f['reqs']:>5} {f['reqs_met']:>5} "
              f"{f['objs']:>6} {f['objs_pass']:>5} {pct:>6}%")
    print(f"  {'-'*28} {'-'*5} {'-'*5} {'-'*6} {'-'*5} {'-'*7}")
    opct = round(100 * tp / to) if to else 0
    print(f"  {'TOTAL':<28} {tr:>5} {tm:>5} {to:>6} {tp:>5} {opct:>6}%")


if __name__ == "__main__":
    main()
