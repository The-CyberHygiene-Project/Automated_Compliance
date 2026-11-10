#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Copy duties recorded on the portal page (VM log) into the ledger DIWAI-LEDGER-001.
Needs an open ssh session to the VM (the owner's login). Skips entries already in the ledger. Run: obligations-sync.py"""
import json, pathlib, subprocess, sys, re
L = pathlib.Path.home() / "diwai/obligations/CUI_DIWAI-LEDGER-001_Obligations_Ledger.md"
r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-i", str(pathlib.Path.home() / ".ssh/diwai_rsa"), "[USERNAME]@services",
                    "sudo -n cat /var/log/diwai/duties.log 2>/dev/null || cat /var/log/diwai/duties.log"],
                   capture_output=True, text=True, timeout=40)
if r.returncode != 0:
    sys.exit("Could not read the VM log (is your ssh login open?): " + r.stderr.strip()[-200:])
txt = L.read_text()
add = []
for line in r.stdout.splitlines():
    try: e = json.loads(line)
    except ValueError: continue
    out = re.sub(r"\s+", " ", e["outcome"]).replace("|", "/")
    key = "| %s | %s | %s |" % (e["date"], e["id"], out)
    if key in txt: continue
    add.append(key + " %s (portal) |" % e["by"])
if not add: sys.exit("Nothing new to copy.")
lines = txt.split("\n")
i = max(n for n, l in enumerate(lines) if re.match(r"\| \d{4}-\d\d-\d\d \|", l))
lines[i + 1:i + 1] = add
L.write_text("\n".join(lines)); print("copied %d entries" % len(add))
