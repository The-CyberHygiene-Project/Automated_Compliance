#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# 3.3.5 exercise: one synthetic unauthorized-access event (login attempts as a non-existent user) traced across sources by time, user and source address.
set -u
U=nosuch$(openssl rand -hex 3); T0=$(date '+%F %T'); T0U=$(date -u '+%Y-%m-%dT%H:%M')
echo "== CORRELATION EXERCISE $T0 (Mac local time); probe user: $U; source: the Mac ([LAN-IP-REDACTED])"
for i in 1 2 3; do ssh -o ControlPath=none -o BatchMode=yes -o ConnectTimeout=8 -i ~/.ssh/diwai_rsa $U@services true >/dev/null 2>&1; done
sleep 12
echo; echo "-- SOURCE 1: VM sshd journal"
ssh -o BatchMode=yes -i ~/.ssh/diwai_rsa [USERNAME]@services "sudo -n journalctl -u sshd --since '-2min' --no-pager | grep $U | cut -c1-160 | head -4"
echo; echo "-- SOURCE 2: VM auditd (kernel audit trail), same user"
ssh -o BatchMode=yes -i ~/.ssh/diwai_rsa [USERNAME]@services "sudo -n tail -n 40000 /var/log/audit/audit.log | grep $U | grep -E 'type=(USER_LOGIN|USER_AUTH|USER_ERR|USER_START)' | sed -E 's/ (exe|hostname|terminal|subj)=[^ ]*//g' | cut -c1-220 | head -4"
echo; echo "-- SOURCE 3: Wazuh alert raised on the VM (rule, level, description), same user and source address"
ssh -o BatchMode=yes -i ~/.ssh/diwai_rsa [USERNAME]@services "sudo -n grep $U /var/ossec/logs/alerts/alerts.json | python3 -c 'import sys,json
for l in sys.stdin:
    a=json.loads(l); r=a.get(\"rule\",{}); d=a.get(\"data\",{})
    print(a.get(\"timestamp\",\"\")[:19],\"rule\",r.get(\"id\"),\"level\",r.get(\"level\"),\"|\",r.get(\"description\"),\"| srcip\",d.get(\"srcip\"),\"| user\",d.get(\"srcuser\") or d.get(\"dstuser\"))' | head -4"
echo; echo "-- SOURCE 4: Mac, the originating host (unified log, ssh client)"
echo "(Mac client side: the outbound attempt is the originating event, three connections as $U at the time above)"
echo; echo "== exercise ended $(date '+%F %T')"
