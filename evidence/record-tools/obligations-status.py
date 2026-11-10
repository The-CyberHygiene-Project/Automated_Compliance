#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Overdue report for DIWAI-SCH-001. Manual items: last ledger entry vs cadence.
Automated items: probed on the VM/Mac for the last run AND its result. Read-only."""
import re,pathlib,datetime,subprocess,sys
H=pathlib.Path.home()/"diwai/obligations"
sch=(H/"CUI_DIWAI-SCH-001_Recurring_Obligations_Schedule_v1.0.md").read_text()
led=(H/"CUI_DIWAI-LEDGER-001_Obligations_Ledger.md").read_text()
DAYS={"Daily":3,"Weekly":8,"Monthly":32,"Quarterly":93,"Annual":367}   # daily allows a weekend
today=datetime.date.today()
rows=[]
for l in sch.split("\n"):
    c=[x.strip() for x in l.strip().strip("|").split("|")]
    if len(c)==7 and re.match(r"^[DWMQA]\d+$",c[0]) and c[5] in("KEEP","KEEP (merged)","CHANGE"): rows.append(c)
last={}
for l in led.split("\n"):
    c=[x.strip() for x in l.strip().strip("|").split("|")]
    if len(c)==4 and re.match(r"\d{4}-\d\d-\d\d",c[0]): last[c[1]]=max(last.get(c[1],""),c[0])
# automated probes: id -> (host, command printing 'YYYY-MM-DD result')
# Each probe prints: ID date result. Results come from the job's own output, not from the timer.
cmd = r"""
echo D3 $(systemctl show wazuh-archive.service -p ExecMainExitTimestamp --value | cut -d' ' -f2) $(systemctl show wazuh-archive.service -p Result --value)
echo D5 $(systemctl show dnf-automatic.service -p ExecMainExitTimestamp --value | cut -d' ' -f2) $(systemctl show dnf-automatic.service -p Result --value)
echo M2 $(systemctl show diwai-cve-scan.service -p ExecMainExitTimestamp --value | cut -d' ' -f2) $(systemctl show diwai-cve-scan.service -p Result --value)
echo W2 $(sudo -n grep 'yara-fullscan complete' /var/log/yara-fullscan.log | tail -1 | cut -c2-11) $(sudo -n grep 'yara-fullscan complete' /var/log/yara-fullscan.log | tail -1 | sed 's/.*complete: //; s/ /_/g')
echo W3 $(sudo -n ls -t /var/log/oscap/oscap-scan-*.log | head -1 | sed 's/.*scan-//; s/.log//') scanlog-present
echo D4 $(sudo -n grep -E 'Suricata: (OK|FAIL|ERROR)' /var/log/threat-rules-update.log | tail -1 | cut -c2-11) $(sudo -n grep -E 'Suricata: (OK|FAIL|ERROR)' /var/log/threat-rules-update.log | tail -1 | sed 's/.*Suricata: //; s/ .*//')
echo D6 $(date +%F) $(sudo -n /var/ossec/bin/agent_control -l | grep -c 'Active')_agents_active
"""
probe={}
try:
    o=subprocess.run(["ssh","-o","BatchMode=yes","-i",str(pathlib.Path.home()/".ssh/diwai_rsa"),"[USERNAME]@services",cmd],capture_output=True,text=True,timeout=40).stdout
    for l in o.split("\n"):
        p=l.split()
        if len(p)>=3: probe[p[0]]=(p[1],p[2])
except Exception as e: print("VM probe failed:",e)
try:
    tm=subprocess.run(["tmutil","latestbackup"],capture_output=True,text=True).stdout.strip().split("/")[-1][:10]
    probe["D7"]=(tm,"present")
except Exception: pass
n=0
print("%-4s %-9s %-62s %-12s %s"%("ID","Cadence","Activity","Last","Status"))
for c in rows:
    i,cad,act,how=c[0],c[1],c[2][:60],c[4]
    if how=="Automated":
        d,res=probe.get(i,("",""))
        if not d: st="NO EVIDENCE (probe returned nothing)"
        else:
            age=(today-datetime.date.fromisoformat(d)).days
            ok=age<=DAYS[cad] and res not in("failed","exit-code","FAIL","ERROR") and not res.startswith("0_agents")
            st=("OK" if ok else "OVERDUE/FAILED")+" (result: %s)"%res
        print("%-4s %-9s %-62s %-12s %s"%(i,cad,act,d or "-",st)); n+= st.startswith("OK")
    else:
        d=last.get(i,"")
        if not d: st="NEVER RECORDED"
        else:
            age=(today-datetime.date.fromisoformat(d)).days
            st="OK" if age<=DAYS[cad] else "OVERDUE by %d days"%(age-DAYS[cad])
        print("%-4s %-9s %-62s %-12s %s"%(i,cad,act,d or "-",st)); n+= st=="OK"
print("\n%d of %d in order on %s"%(n,len(rows),today))
