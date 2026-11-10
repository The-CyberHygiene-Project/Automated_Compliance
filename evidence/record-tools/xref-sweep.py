#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""xref-sweep - find LIVE compliance pointers that resolve but point at a SUPERSEDED version.

WHY (DIWAI-MFR-2026-08-12 §7 Action 3)
--------------------------------------
DIWAI-EV-CM-2026-08-02 proved every citation RESOLVED. It could not catch the
2026-08-12 defect: the SSP cited `Unified_POAM_v1.7.md`, which existed, was
readable, and was SUPERSEDED. A resolving pointer to a stale version misleads an
assessor as badly as a broken one, and an existence check is blind to it. That
pointer was found by accident; so was POA&M-074 on 2026-09-13. This is the
process that was missing.

SCOPE IS THE WHOLE DESIGN -- most "stale" citations are CORRECT
---------------------------------------------------------------
Per DIWAI-CR-2026-08-09 §7, point-in-time citations stay historical. A change
record dated 08-02 citing "SSP v2.15" as its Authority is RIGHT; repointing it
would falsify the record. So this sweep deliberately EXCLUDES:

  * Change_Records/, Evidence/, Assessment/  -- dated, immutable by nature
  * any document that is not the current version of its family
  * revision-history sections inside living documents

and inspects ONLY live pointers in current-version living documents (SSP, POA&M,
SBOM, policies, procedures). A first cut without these exclusions produced 136
findings, essentially all false. DIWAI-EV-CM-2026-08-02 §2: "an auditing tool
that produces false positives is worse than none."

It reports; it does not edit.
"""
import os, re, sys
from collections import defaultdict

NC = "/opt/local/nextcloud/data/__groupfolders/1/files/Compliance"
POINT_IN_TIME = ("Change_Records", "Evidence", "Assessment", "Incident_Response")
FILE_CITE = re.compile(r'([A-Za-z0-9_.\-]+)_v(\d+\.\d+)')
CITE_IN_TEXT = re.compile(r'([A-Za-z0-9_.\-]+)_v(\d+\.\d+)\.md')
PROSE = {
    r'\bSSP\s+v(\d+\.\d+)': "CUI_System_Security_Plan",
    r'\bPOA&M\s+v(\d+\.\d+)': "CUI_[DOMAIN.ORG]_Unified_POAM",
    r'\bSBOM\s+v(\d+\.\d+)': "Software_Bill_of_Materials",
}
REV_HEAD = re.compile(r'^#{1,4}\s.*REVISION HISTORY', re.I)
HEAD = re.compile(r'^#{1,4}\s')
# A line that is itself a dated record is point-in-time, wherever it sits:
#   "| 3.0 | 2026-06-11 | [SYSTEM-OWNER] | ..."   version-history row
#   "**Editorial Correction (2026-08-01):** ..."  dated editorial note
#   "| **Supersedes** | ..._v1.30.md ..."     correct BY DEFINITION
VERSION_ROW = re.compile(r'^\|\s*\*{0,2}\d+\.\d+\*{0,2}\s*\|\s*\*{0,2}\d{4}-\d{2}-\d{2}')
DATED_NOTE  = re.compile(r'\(\d{4}-\d{2}-\d{2}\)')
SUPERSEDES  = re.compile(r'Supersedes', re.I)

def historical_line(l):
    return bool(VERSION_ROW.match(l) or DATED_NOTE.search(l) or SUPERSEDES.search(l))

def vkey(v): return tuple(int(x) for x in v.split("."))

def famver(stem):
    m = FILE_CITE.fullmatch(stem)
    return (m.group(1), m.group(2)) if m else (None, None)

# ---- current version per family, from canonical -----------------------------
current, canon_files = {}, []
for dp, _, fns in os.walk(NC):
    for fn in fns:
        if not fn.endswith(".md"): continue
        p = os.path.join(dp, fn)
        canon_files.append(p)
        fam, ver = famver(fn[:-3])
        if fam and (fam not in current or vkey(ver) > vkey(current[fam])):
            current[fam] = ver

# ---- scan set: current-version LIVING documents only -------------------------
scan = []
for p in canon_files:
    rel = os.path.relpath(p, NC)
    if rel.split(os.sep)[0] in POINT_IN_TIME:
        continue
    fam, ver = famver(os.path.basename(p)[:-3])
    if fam and ver != current.get(fam):
        continue                      # superseded copy: its citations are historical
    scan.append(p)

findings, skipped_rev = [], 0
for p in sorted(scan):
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    in_rev = False
    for n, line in enumerate(lines, 1):
        if REV_HEAD.match(line): in_rev = True; continue
        if in_rev and HEAD.match(line): in_rev = False
        hits = [(m.group(1), m.group(2)) for m in CITE_IN_TEXT.finditer(line)]
        for pat, fam in PROSE.items():
            hits += [(fam, m.group(1)) for m in re.finditer(pat, line)]
        for fam, ver in hits:
            if fam not in current or ver == current[fam]:
                continue
            if in_rev or historical_line(line):
                skipped_rev += 1
                continue
            findings.append((p, n, fam, ver, current[fam], line.strip()[:160]))

print("CURRENT VERSIONS (canonical)")
for f in sorted(current): print(f"   {f:<48} v{current[f]}")
print(f"\nLiving documents inspected : {len(scan)}")
print(f"Point-in-time docs excluded: {len(canon_files)-len(scan)}")
print(f"Point-in-time citations skipped (correct as-is): {skipped_rev}")
print(f"\nSTALE LIVE POINTERS: {len(findings)}")
if findings:
    print("=" * 76)
    by = defaultdict(list)
    for f in findings: by[f[0]].append(f)
    for doc in sorted(by):
        print(f"\n{os.path.relpath(doc, NC)}")
        for _, n, fam, ver, cur, txt in by[doc]:
            print(f"   line {n}: {fam} cited v{ver}, current v{cur}")
            print(f"            {txt}")
sys.exit(1 if findings else 0)
