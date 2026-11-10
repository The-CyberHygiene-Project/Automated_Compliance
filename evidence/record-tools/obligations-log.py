#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Record that a scheduled obligation (DIWAI-SCH-001) was performed.
Usage: obligations-log.py ID "what was found, or that nothing was" [--by NAME] [--date YYYY-MM-DD] [--backfill]
The outcome text is required: a dated entry must say what was found, not that a job ran."""
import sys,datetime,pathlib,re
L=pathlib.Path.home()/"diwai/obligations/CUI_DIWAI-LEDGER-001_Obligations_Ledger.md"
a=sys.argv[1:]
if len(a)<2 or a[1].startswith("--"): sys.exit(__doc__)
i,out=a[0],a[1]; by="[SYSTEM-OWNER]"; d=datetime.date.today().isoformat(); bf=False
j=2
while j<len(a):
    if a[j]=="--by": by=a[j+1]; j+=2
    elif a[j]=="--date": d=a[j+1]; j+=2
    elif a[j]=="--backfill": bf=True; j+=1
    else: sys.exit(__doc__)
sch=(pathlib.Path.home()/"diwai/obligations/CUI_DIWAI-SCH-001_Recurring_Obligations_Schedule_v1.0.md").read_text()
if not re.search(r"^\| %s \|"%re.escape(i),sch,re.M): sys.exit("unknown obligation ID "+i)
if len(out.split())<3: sys.exit("outcome too short: say what was found")
row="| %s | %s | %s%s | %s |\n"%(d,i,"BACKFILL: " if bf else "",out.replace("|","/"),by)
with L.open("a") as f: f.write(row)
print("recorded:",row.strip())
