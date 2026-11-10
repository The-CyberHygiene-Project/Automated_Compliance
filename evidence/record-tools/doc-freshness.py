#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""doc-freshness — refuse to edit a compliance document that is behind canonical.

WHY THIS EXISTS (POA&M-048 / F-2026-08-32, 2026-08-03)
------------------------------------------------------
The canonical store is the Nextcloud CUI groupfolder. `~/diwai/assessment-2026-08/`
holds working copies with no provenance marker. On 2026-08-03 the working SSP was
byte-identical to an 08-02 09:45 snapshot -- 125 lines behind canonical -- and was
edited and prepared for reissue. Publishing it would have silently reverted a full
afternoon of canonical work. It carried the SAME VERSION NUMBER as canonical, so
nothing about its name, size on screen, or behaviour indicated it was old.

WHY A PLAIN DIFF IS NOT ENOUGH
------------------------------
"working != canonical" is the NORMAL state while you are editing. A check that
warns on every difference gets ignored within a day, and then it is decoration.
So this keeps a BASELINE: the hash of canonical as of the last time the two were
in sync. That turns one ambiguous bit into a real answer:

    W = hash(working)   C = hash(canonical)   B = baseline

    W == C                     -> IN SYNC        safe
    W != C, C == B             -> LOCAL AHEAD    safe (your edits, canonical still still)
    W != C, C != B, W == B     -> STALE          UNSAFE  <-- the 2026-08-03 case
    W != C, C != B, W != B     -> DIVERGED       UNSAFE
    no baseline, W != C        -> UNKNOWN        UNSAFE (cannot prove, so does not claim)

FAILS CLOSED. If the canonical store cannot be read -- Nextcloud moved, disk not
mounted, permissions -- this exits non-zero and says so. A freshness check that
passes when it cannot see canonical is the same defect it was written to catch:
a process that runs, reports success, and verifies nothing (cf. POA&M-031, -015).

USAGE
    doc-freshness.py status            # every tracked document
    doc-freshness.py check <file>      # exit 0 = safe to edit, 1 = do not edit
    doc-freshness.py adopt <file>      # pull canonical -> working, set baseline
    doc-freshness.py publish <file>    # push working -> canonical, set baseline
    doc-freshness.py accept <file>     # set baseline to current canonical, no copy
                                       #   (deliberate divergence, recorded not hidden)
"""
import hashlib
import json
import os
import shutil
import sys

CANON_ROOT = "/opt/local/nextcloud/data/__groupfolders/1/files/Compliance"
WORK_DIRS = [
    os.path.expanduser("~/diwai/assessment-2026-08"),
    os.path.expanduser("~/diwai/assessment-2026-08/evidence"),
]
WORK_FILES = [
    os.path.expanduser("~/diwai/Software_Bill_of_Materials_v3.18.md"),
]
BASELINE = os.path.expanduser("~/diwai/etc/doc-baseline.json")

# Working name -> canonical basename, where the two genuinely differ.
# The SBOM is versioned locally but unversioned in the canonical store, so the
# basename rule below cannot find it. Anything not listed here resolves by rule.
ALIASES = {
    "Software_Bill_of_Materials_v3.18.md": "CUI_Software_Bill_of_Materials.md",
}

# Local-only by design: never reported as a problem.
IGNORE = {"aider-system-context.md"}

SAFE = {"IN SYNC", "LOCAL AHEAD"}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_index():
    """basename -> full path, for every markdown file in the canonical store."""
    if not os.path.isdir(CANON_ROOT):
        sys.exit(f"FAIL-CLOSED: canonical store not readable: {CANON_ROOT}\n"
                 f"Nothing was checked. Do not treat this as a pass.")
    idx = {}
    for dirpath, _, files in os.walk(CANON_ROOT):
        for f in files:
            if f.endswith(".md"):
                idx.setdefault(f, os.path.join(dirpath, f))
    if not idx:
        sys.exit(f"FAIL-CLOSED: canonical store is empty: {CANON_ROOT}")
    return idx


def canonical_for(work_path, idx):
    base = os.path.basename(work_path)
    if base in ALIASES:
        return idx.get(ALIASES[base])
    if base in idx:                       # already CUI_-prefixed
        return idx[base]
    return idx.get("CUI_" + base)         # evidence/ files carry no prefix locally


def tracked():
    out = []
    for d in WORK_DIRS:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if f.endswith(".md") and os.path.isfile(p) and f not in IGNORE:
                out.append(p)
    out += [p for p in WORK_FILES if os.path.isfile(p)]
    return out


def load_baseline():
    try:
        with open(BASELINE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_baseline(b):
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    tmp = BASELINE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(b, f, indent=2, sort_keys=True)
    os.replace(tmp, BASELINE)


def classify(work, idx, base, seed=None):
    canon = canonical_for(work, idx)
    if canon is None:
        return "LOCAL ONLY", None, "no canonical counterpart — not a controlled document"
    w, c = sha(work), sha(canon)
    b = base.get(work, {}).get("canonical_sha")
    if w == c:
        # Identical means canonical IS the merge base, provably. Record it, so the
        # first local edit reads as LOCAL AHEAD rather than UNKNOWN. Without this
        # the check cries wolf on its first real use and stops being read.
        if seed is not None and b != c:
            base[work] = {"canonical": canon, "canonical_sha": c}
            seed.append(work)
        return "IN SYNC", canon, ""
    if b is None:
        return "UNKNOWN", canon, "differs from canonical and no baseline recorded — provenance unprovable"
    if c == b:
        return "LOCAL AHEAD", canon, "local edits not yet published; canonical unchanged since sync"
    if w == b:
        return "STALE", canon, "canonical MOVED AHEAD; working copy is the old canonical — DO NOT EDIT OR PUBLISH"
    return "DIVERGED", canon, "both sides changed since last sync — reconcile before editing"


def cmd_status():
    idx, base = canonical_index(), load_baseline()
    seed = []
    rows = [(w,) + classify(w, idx, base, seed) for w in tracked()]
    if seed:
        save_baseline(base)
    width = max((len(os.path.basename(r[0])) for r in rows), default=10)
    unsafe = 0
    for work, state, _canon, note in sorted(rows, key=lambda r: (r[1] in SAFE, r[1])):
        if state not in SAFE and state != "LOCAL ONLY":
            unsafe += 1
        mark = "  " if state in SAFE or state == "LOCAL ONLY" else "!!"
        print(f"{mark} {os.path.basename(work):<{width}}  {state:<12} {note}")
    print()
    print(f"{len(rows)} tracked, {unsafe} unsafe to edit")
    return 1 if unsafe else 0


def resolve(arg):
    p = os.path.abspath(os.path.expanduser(arg))
    if os.path.isfile(p):
        return p
    for d in WORK_DIRS:
        cand = os.path.join(d, os.path.basename(arg))
        if os.path.isfile(cand):
            return cand
    sys.exit(f"not found: {arg}")


def cmd_check(arg):
    work = resolve(arg)
    idx, base = canonical_index(), load_baseline()
    seed = []
    state, canon, note = classify(work, idx, base, seed)
    if seed:
        save_baseline(base)
    name = os.path.basename(work)
    if state in SAFE or state == "LOCAL ONLY":
        print(f"OK   {name}: {state}" + (f" — {note}" if note else ""))
        return 0
    print(f"STOP {name}: {state} — {note}")
    print(f"     working:   {work}")
    print(f"     canonical: {canon}")
    print(f"     To take canonical and discard local:  doc-freshness.py adopt {name}")
    print(f"     To diff:  diff '{canon}' '{work}'")
    return 1


def cmd_adopt(arg):
    work = resolve(arg)
    idx, base = canonical_index(), load_baseline()
    canon = canonical_for(work, idx)
    if canon is None:
        sys.exit(f"no canonical counterpart for {os.path.basename(work)}")
    shutil.copy2(canon, work)
    base[work] = {"canonical": canon, "canonical_sha": sha(canon)}
    save_baseline(base)
    print(f"adopted canonical -> {work}")
    return 0


def cmd_publish(arg):
    work = resolve(arg)
    idx, base = canonical_index(), load_baseline()
    state, canon, note = classify(work, idx, base)
    if canon is None:
        sys.exit(f"no canonical counterpart for {os.path.basename(work)}")
    if state in ("STALE", "DIVERGED", "UNKNOWN"):
        sys.exit(f"REFUSED: {os.path.basename(work)} is {state} — {note}\n"
                 f"Publishing would overwrite canonical with older or divergent content.")
    shutil.copy2(work, canon)
    base[work] = {"canonical": canon, "canonical_sha": sha(canon)}
    save_baseline(base)
    print(f"published -> {canon}")
    print("Remember to re-index:  cd /opt/local/nextcloud && php occ groupfolders:scan 1")
    return 0


def cmd_accept(arg):
    work = resolve(arg)
    idx, base = canonical_index(), load_baseline()
    canon = canonical_for(work, idx)
    if canon is None:
        sys.exit(f"no canonical counterpart for {os.path.basename(work)}")
    base[work] = {"canonical": canon, "canonical_sha": sha(canon)}
    save_baseline(base)
    print(f"baseline set to current canonical for {os.path.basename(work)} (no content copied)")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "status":
        return cmd_status()
    if cmd in ("check", "adopt", "publish", "accept"):
        if not args:
            sys.exit(f"{cmd} needs a file")
        return {"check": cmd_check, "adopt": cmd_adopt,
                "publish": cmd_publish, "accept": cmd_accept}[cmd](args[0])
    sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    sys.exit(main())
