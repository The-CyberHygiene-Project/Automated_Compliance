#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Sweep [DOMAIN.ORG] compliance documents for citations that do not resolve.

Written 2026-08-02 after three broken references surfaced by accident:
  * all 11 policies cited as DIWAI-*-001 while declaring TCC-*-001
  * DIWAI-ATP-002 cited but never written
  * SBOM citing /root/oscap-report.html, which never existed

Checks five citation classes:
  A. Nextcloud-relative paths   (Compliance/...)
  B. Markdown document names    (something_v1.2.md)
  C. Policy document IDs        (DIWAI-XXX-001)
  D. Evidence IDs               (DIWAI-EV-...)
  E. Absolute host paths        (/root/..., /usr/local/..., /etc/...)

Host paths are reported for manual checking; the rest are resolved here.
"""
import os
import re
from collections import defaultdict

NC = "/opt/local/nextcloud/data/__groupfolders/1/files/Compliance"
LOCAL = "/Users/[USERNAME]/diwai"
ROOTS = [NC, os.path.join(LOCAL, "assessment-2026-08")]
EXTRA = [os.path.join(LOCAL, f) for f in os.listdir(LOCAL)
         if f.endswith(".md") and os.path.isfile(os.path.join(LOCAL, f))]

# ---- build the inventory of what EXISTS -------------------------------------
existing_files = set()
existing_basenames = set()
for root in ROOTS:
    for dirpath, _, files in os.walk(root):
        for f in files:
            existing_files.add(os.path.join(dirpath, f))
            existing_basenames.add(f)
            existing_basenames.add(re.sub(r"^CUI_", "", f))
for f in EXTRA:
    existing_files.add(f)
    existing_basenames.add(os.path.basename(f))

# Document IDs actually declared inside documents
declared_ids = set()
declared_ev = set()
for path in sorted(existing_files):
    if not path.endswith((".md", ".txt")):
        continue
    try:
        text = open(path, errors="ignore").read()
    except OSError:
        continue
    # Documents declare their ID in two forms: prose ("**Document ID:** X")
    # and table ("| **Document ID** | **X** |"). Recognise both — missing the
    # second produced a false positive on DIWAI-BP-001.
    for m in re.finditer(r"\*\*Document ID:?\*\*[:\s|]*\*{0,2}([A-Z][A-Z0-9-]+)", text):
        declared_ids.add(m.group(1))
    # A document may carry its ID ONLY in its filename and never declare it in
    # a field — the incident records (CUI_DIWAI-INC-001_*.md) and the memo for
    # record do exactly that. Harvesting the ID from the filename removes a
    # standing false positive: before this, every citation of DIWAI-INC-001 and
    # DIWAI-INC-002 was reported unresolved while both files sat in
    # Compliance/Incident_Response/. A check that cries wolf on healthy state
    # trains the reader to skip it (the POA&M-071 defect class).
    for m in re.finditer(r"(DIWAI-[A-Z]{2,4}-\d{3}|DIWAI-MFR-\d{4}-\d{2}-\d{2})",
                         os.path.basename(path)):
        declared_ids.add(m.group(1))
    # Evidence records declare their own ID in the heading or a field
    for m in re.finditer(r"^#\s+(DIWAI-EV-[A-Za-z0-9-]+)", text, re.M):
        declared_ev.add(m.group(1))
    for m in re.finditer(r"evidence\s+\*{0,2}(DIWAI-EV-[A-Za-z0-9-]+)", text, re.I):
        declared_ev.add(m.group(1))

# ---- scan for citations -----------------------------------------------------
broken = defaultdict(list)
hostpaths = defaultdict(set)
ok_count = 0

for path in sorted(existing_files):
    if not path.endswith(".md"):
        continue
    rel = path.replace(NC, "Compliance").replace(LOCAL + "/", "")
    try:
        text = open(path, errors="ignore").read()
    except OSError:
        continue

    # B. markdown filenames cited
    for m in re.finditer(r"`?([A-Za-z0-9._-]+_v?[0-9][0-9A-Za-z.]*\.md)`?", text):
        name = m.group(1)
        if name in existing_basenames or re.sub(r"^CUI_", "", name) in existing_basenames:
            ok_count += 1
        else:
            broken["missing document"].append((rel, name))

    # C. policy document IDs
    for m in re.finditer(r"\b(DIWAI-[A-Z]{2,6}(?:-[A-Z]{2})?-\d{3})\b", text):
        did = m.group(1)
        if did in declared_ids:
            ok_count += 1
        else:
            broken["unresolved document ID"].append((rel, did))

    # D. evidence IDs
    for m in re.finditer(r"\b(DIWAI-EV-[A-Za-z0-9-]{3,})\b", text):
        eid = m.group(1).rstrip(".,;)")
        if eid in declared_ev or eid in declared_ids or any(eid in b for b in existing_basenames):
            ok_count += 1
        else:
            broken["unresolved evidence ID"].append((rel, eid))

    # E. absolute host paths — collect for manual verification
    for m in re.finditer(r"`(/(?:root|etc|usr|var|opt|Users)/[A-Za-z0-9._/-]+)`", text):
        hostpaths[m.group(1)].add(rel)

# ---- report -----------------------------------------------------------------
print(f"Resolved citations: {ok_count}")
print()
for kind in sorted(broken):
    seen = {}
    for rel, item in broken[kind]:
        seen.setdefault(item, set()).add(rel)
    print(f"=== {kind.upper()} ({len(seen)} distinct) ===")
    for item, files in sorted(seen.items()):
        print(f"  {item}")
        for f in sorted(files)[:3]:
            print(f"      cited in: {f}")
    print()

print(f"=== ABSOLUTE HOST PATHS CITED ({len(hostpaths)}) — verify separately ===")
for p in sorted(hostpaths):
    print(f"  {p}")
