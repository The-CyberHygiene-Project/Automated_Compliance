#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# diwai-control-health — verify that security controls are actually RUNNING.
#
# Created 2026-08-01 (DIWAI-ASMT-2026-08) after four controls were found
# believed-running but inert:
#   * wazuh-manager down ~21h, undetected (2026-07-31)
#   * wazuh Mac agent offline ~12 days (closed POA&M-009)
#   * mSCP weekly scan executing a ZERO-BYTE script since ~June
#   * VM clock 24 min adrift while chronyc reported perfect synchronisation
#
# Addresses 3.12.3 (monitor controls on an ongoing basis), 3.3.4 (alert on audit
# logging failure) and 3.14.6 (monitoring). The point is not to check health --
# it is to detect a control that has silently STOPPED.
#
# Alerting is deliberately dual-path: syslog (which Wazuh ingests) AND local
# mail. A Wazuh-only alert is useless when the thing that failed IS Wazuh.

set -u

TAG=diwai-health
MAIL_TO="${DIWAI_HEALTH_MAILTO:-root}"
# Recovery notices are informational, NOT action-required. Keep them local
# (root -> [USERNAME] Maildir) so the offsite channel carries only things that
# need someone to act. Set DIWAI_HEALTH_RECOVERY_MAILTO to override.
RECOVERY_MAIL_TO="${DIWAI_HEALTH_RECOVERY_MAILTO:-root}"
STALE_DAYS=8            # weekly jobs: alert if newer than this is absent
CLOCK_TOLERANCE=5       # seconds

FAILURES=()
CHECKS=0

ok()   { CHECKS=$((CHECKS+1)); printf "  [ OK ] %s\n" "$*"; diwai_json_line ok "$*"; }
fail() { CHECKS=$((CHECKS+1)); FAILURES+=("$*"); printf "  [FAIL] %s\n" "$*"; diwai_json_line fail "$*"; }

# --- machine-readable report (DIWAI-CR-2026-10-09): every ok/fail also becomes one
# line here; just after "# --- report" they are turned into
# /var/lib/diwai-control-health/latest.json for diwai-diagnose. Nothing in this
# block may stop the monitor or its mail: every step ends in "|| true".
DIWAI_JSON_DIR=/var/lib/diwai-control-health
SEC_ID=""; SEC_NAME=""
DIWAI_JSON_LINES=$(mktemp "$DIWAI_JSON_DIR/.lines.XXXXXX" 2>/dev/null || echo /dev/null)
diwai_json_line() {   # diwai_json_line <ok|fail> <detail>: tab-separated, tabs/newlines flattened, scrubbed, 400 chars
    local d
    d=$(printf '%s' "$2" | tr '\t\n' '  ' | sed -E 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[EMAIL]/g; s/(pass(word)?|secret|token|key)[=: ]+[^ ]+/\1=[REDACTED]/Ig' | cut -c1-400)
    printf '%s\t%s\t%s\t%s\n' "$1" "$SEC_ID" "$SEC_NAME" "$d" >> "$DIWAI_JSON_LINES" 2>/dev/null || true
}

age_days() {  # age of newest file matching a glob, in days; 9999 if none
    local newest
    newest=$(ls -t $1 2>/dev/null | head -1)
    [ -z "$newest" ] && { echo 9999; return; }
    echo $(( ( $(date +%s) - $(stat -c %Y "$newest" 2>/dev/null || echo 0) ) / 86400 ))
}

echo "diwai control health — $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo

# --- 1. SIEM is running -----------------------------------------------------
SEC_ID="1"; SEC_NAME="SIEM is running"
if systemctl is-active --quiet wazuh-manager; then
    ok "wazuh-manager active"
else
    fail "wazuh-manager NOT running — SIEM is not collecting"
fi

# --- 2. Every enrolled agent is connected -----------------------------------
SEC_ID="2"; SEC_NAME="Every enrolled agent is connected"
# Catches the Mac-agent-offline case. Counts, rather than assuming.
if [ -x /var/ossec/bin/agent_control ]; then
    agents=$(/var/ossec/bin/agent_control -l 2>/dev/null | grep -cE "^ +ID: [0-9]+")
    disc=$(/var/ossec/bin/agent_control -l 2>/dev/null | grep -E "^ +ID: [0-9]+" | grep -c "Disconnected\|Never connected")
    if [ "$agents" -eq 0 ]; then
        fail "no Wazuh agents enrolled"
    elif [ "$disc" -gt 0 ]; then
        fail "$disc of $agents Wazuh agent(s) disconnected"
    else
        ok "all $agents Wazuh agent(s) connected"
    fi
fi

# --- 3. Audit subsystem ------------------------------------------------------
SEC_ID="3"; SEC_NAME="Audit subsystem"
if systemctl is-active --quiet auditd; then
    lost=$(auditctl -s 2>/dev/null | awk '/^lost/{print $2}')
    if [ "${lost:-0}" -gt 0 ]; then
        fail "auditd reports lost=$lost records"
    else
        ok "auditd active, no lost records"
    fi
else
    fail "auditd NOT running"
fi

# Retention headroom: raised to 64MB x 100 on 2026-08-01; alert before it bites.
used=$(df --output=pcent /var/log/audit 2>/dev/null | tail -1 | tr -dc '0-9')
if [ "${used:-0}" -ge 80 ]; then
    fail "/var/log/audit ${used}% full"
else
    ok "/var/log/audit ${used}% used"
fi

# --- 4. Clock is genuinely synchronised -------------------------------------
SEC_ID="4"; SEC_NAME="Clock is genuinely synchronised"
# NOT 'chronyc tracking' -- that reported 0.000000000s off while the clock was
# 24 minutes wrong, because no source was selected. Require a SELECTED source.
if command -v chronyc >/dev/null 2>&1; then
    if chronyc sources 2>/dev/null | grep -q '^\^\*'; then
        off=$(chronyc tracking 2>/dev/null | awk -F': *' '/System time/{print $2}' | awk '{print $1}')
        offi=${off%%.*}; offi=${offi#-}
        if [ "${offi:-0}" -le "$CLOCK_TOLERANCE" ]; then
            ok "clock synchronised to a selected source (offset ${off}s)"
        else
            fail "clock offset ${off}s exceeds ${CLOCK_TOLERANCE}s"
        fi
    else
        fail "chrony has NO selected source (^*) — clock is free-running and may be wrong regardless of what 'tracking' reports"
    fi
fi

# --- 5. Scheduled scans actually produced output ----------------------------
SEC_ID="5"; SEC_NAME="Scheduled scans actually produced output"
# The mSCP failure mode was a job that ran and did nothing. Check for OUTPUT,
# never for "did the unit run".
a=$(age_days "/var/log/oscap/oscap-scan-*.log")
if [ "$a" -le "$STALE_DAYS" ]; then ok "OpenSCAP output ${a}d old"
else fail "no OpenSCAP output newer than ${STALE_DAYS}d (newest ${a}d)"; fi

if systemctl list-timers yara-fullscan.timer --all --no-pager 2>/dev/null | grep -q yara-fullscan; then
    if systemctl is-enabled --quiet yara-fullscan.timer; then ok "yara-fullscan.timer enabled"
    else fail "yara-fullscan.timer not enabled"; fi
fi

# --- 5b. Encrypted archive pipeline is actually delivering ------------------
SEC_ID="5b"; SEC_NAME="Encrypted archive pipeline is actually delivering"
# Checks OUTPUT, not unit exit status: every stage of this pipeline exited 0
# daily for months while delivering nothing (DIWAI-ASMT-2026-08).
ALOG=/var/log/wazuh-archive.log
if [ -f "$ALOG" ]; then
    last_ship=$(grep "delivered to Mac mini staging" "$ALOG" 2>/dev/null | tail -1 |
                sed -n 's/^\[\([0-9-]*\) .*/\1/p')
    if [ -z "$last_ship" ]; then
        fail "no Wazuh archive has EVER shipped (check wazuh-log-archive)"
    else
        age=$(( ( $(date +%s) - $(date -d "$last_ship" +%s 2>/dev/null || echo 0) ) / 86400 ))
        if [ "$age" -le 2 ]; then
            ok "encrypted archive shipped ${age}d ago"
        else
            fail "no encrypted archive shipped for ${age}d (last $last_ship)"
        fi
    fi
else
    fail "archive log $ALOG missing — pipeline never ran"
fi

# Mac stage: staging should drain. Files older than 2 days mean the Mac-side
# push to the NAS is failing, most often because the SMB mount is absent.
MACKEY=/root/.ssh/id_ecdsa_archive_p256
if [ -r "$MACKEY" ]; then
    stale=$(ssh -i "$MACKEY" -o BatchMode=yes -o ConnectTimeout=8 \
            -o StrictHostKeyChecking=no [USERNAME]@[LAN-IP-REDACTED] \
            'find /Users/[USERNAME]/nas-staging -name "*.enc" -mtime +2 2>/dev/null | wc -l' 2>/dev/null | tr -d " ")
    if [ -z "$stale" ]; then
        ok "Mac staging not checkable (ssh unavailable) — not treated as failure"
    elif [ "$stale" -gt 0 ]; then
        fail "$stale archive(s) stuck in Mac staging >2d — nas-archive-push or the NAS mount is failing"
    else
        ok "Mac staging draining normally"
    fi
fi

# --- 5c. CVE scanning is running AND its data is current --------------------
SEC_ID="5c"; SEC_NAME="CVE scanning is running AND its data is current"
# Two ways this control can lie: not run at all, or run against stale advisory
# data and report "clean". Both are checked.
CVE_DIR=/var/log/oval
cve_report=$(ls -t ${CVE_DIR}/cve-scan-*.json 2>/dev/null | head -1)
if [ -z "$cve_report" ]; then
    fail "CVE scan has NEVER produced a report (diwai-cve-scan / .timer)"
else
    a=$(age_days "${CVE_DIR}/cve-scan-*.json")
    if [ "$a" -le "$STALE_DAYS" ]; then ok "CVE scan output ${a}d old"
    else fail "no CVE scan output newer than ${STALE_DAYS}d (newest ${a}d)"; fi

    # Parse with python; the report is JSON and grep would be guesswork.
    read -r src crit imp < <(/usr/bin/python3 - "$cve_report" <<'PY' 2>/dev/null
import json, sys
d = json.load(open(sys.argv[1]))
f = d.get("findings", [])
patch = [x for x in f if x.get("kind") == "PATCH"]
crit = sum(1 for x in patch if x.get("severity") == "CRITICAL")
imp  = sum(1 for x in patch if x.get("severity") == "IMPORTANT")
print("STALE" if "STALE" in (d.get("source") or "") else "FRESH", crit, imp)
PY
)
    if [ -z "${src:-}" ]; then
        fail "CVE report $cve_report is unreadable or malformed"
    else
        if [ "$src" = "STALE" ]; then
            fail "CVE scan ran against STALE advisory data — results incomplete"
        else
            ok "CVE advisory data current"
        fi
        # Only PATCH-class CRITICAL alerts. E.3 gives IMPORTANT 7 days via the
        # weekly review, so alerting on it every 15 minutes would be noise.
        if [ "${crit:-0}" -gt 0 ]; then
            fail "${crit} actionable CRITICAL vulnerability(ies) — patch within 72h (DIWAI-PR-001 §6)"
        elif [ "${imp:-0}" -gt 0 ]; then
            ok "${imp} actionable IMPORTANT pending — due within 7d via weekly review"
        else
            ok "no actionable CRITICAL/IMPORTANT vulnerabilities"
        fi
    fi
fi

# --- 6. Protective services --------------------------------------------------
SEC_ID="6"; SEC_NAME="Protective services"
for svc in dirsrv@diwai httpd mariadb suricata fapolicyd firewalld chronyd postfix dovecot; do
    if systemctl is-active --quiet "$svc"; then ok "$svc active"
    else fail "$svc NOT running"; fi
done

# --- 7. SELinux + FIPS remain enforcing -------------------------------------
SEC_ID="7"; SEC_NAME="SELinux + FIPS remain enforcing"
[ "$(getenforce 2>/dev/null)" = "Enforcing" ] && ok "SELinux Enforcing" || fail "SELinux NOT Enforcing"
[ "$(cat /proc/sys/crypto/fips_enabled 2>/dev/null)" = "1" ] && ok "FIPS enabled" || fail "FIPS NOT enabled"

# --- 8. Certificate expiry ---------------------------------------------------
SEC_ID="8"; SEC_NAME="Certificate expiry"
CRT=/etc/pki/tls/certs/[DOMAIN.ORG].crt
if [ -f "$CRT" ]; then
    if openssl x509 -in "$CRT" -noout -checkend 1209600 >/dev/null 2>&1; then
        ok "TLS cert valid >14d ($(openssl x509 -in "$CRT" -noout -enddate | cut -d= -f2))"
    else
        fail "TLS cert expires within 14 days — check certbot deploy hook"
    fi
fi

# --- 9. Authenticated-path probe (POA&M-055) ---------------------------------
SEC_ID="9"; SEC_NAME="Authenticated-path probe (POA&M-055)"
# WHY: every other check here verifies a service is RUNNING. On 2026-08-04 the
# dashboard returned HTTP 500 to every authenticated request for six minutes
# while all 24 checks reported healthy — httpd was up, the LDAP bind was broken
# (DIWAI-CR-2026-08-10). "Running" and "working" are different questions.
#
# This probe supplies a DELIBERATELY WRONG password. That drives the full path
# — nginx -> Apache -> mod_authnz_ldap -> LDAPS bind to 389-DS — without needing
# a real credential anywhere in this script.
#
#   401 = the directory was reached and rejected the password  -> HEALTHY
#   500 = mod_ldap could not bind (CA unreadable, LDAPS down, directory refusing)
#   000 = no response at all
#
# Do NOT "fix" this by removing the credentials: an unauthenticated request
# returns 401 without ever binding, which is what made the outage invisible.
DASH_URL="https://securemac.[DOMAIN.ORG]/"
DASH_CODE=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 \
            -u "healthcheck:invalid-by-design" "$DASH_URL" 2>/dev/null)
case "$DASH_CODE" in
    401) ok   "dashboard auth path reached the directory (401 on bad password)" ;;
    500) fail "dashboard authenticated requests return 500 — LDAP bind failing, users cannot log in" ;;
    000) fail "dashboard unreachable from the VM ($DASH_URL)" ;;
    *)   fail "dashboard auth path returned unexpected HTTP $DASH_CODE (expected 401)" ;;
esac

# --- 10. Directory password for uid=[USERNAME] (stored by 4 services) ---------
SEC_ID="10"; SEC_NAME="Directory password for uid=[USERNAME] (stored by 4 services)"
# uid=[USERNAME] is also the background bind account for Nextcloud, the portal
# (Apache), webmail (Dovecot) and the Mac's NAS mount (Keychain). 389-DS stores
# only a hash, so a change cannot propagate. ~/diwai/scripts/change-directory-password.sh
# updates all four and records the new fingerprint here. A change by any other
# route is caught here BEFORE stale copies trip the 3-failure lockout, which
# would take down every one of those services and Don's own logins together.
PWFP_FILE=/var/lib/diwai/[USERNAME]-pw.fingerprint
DS_ENTRY=$(ldapsearch -LLL -o ldif-wrap=no -Y EXTERNAL -H 'ldapi://%2frun%2fslapd-diwai.socket' \
    -b 'uid=[USERNAME],ou=people,dc=diwai,dc=org' -s base \
    userPassword accountUnlockTime passwordRetryCount retryCountResetTime 2>/dev/null)
if [ -z "$DS_ENTRY" ]; then
    fail "cannot read uid=[USERNAME] from 389-DS — directory password watch is blind"
else
    pwfp=$(printf '%s\n' "$DS_ENTRY" | grep '^userPassword' | sha256sum | cut -c1-16)
    if [ ! -s "$PWFP_FILE" ]; then
        printf '%s\n' "$pwfp" > "$PWFP_FILE"; chmod 600 "$PWFP_FILE"
        ok "uid=[USERNAME] password fingerprint recorded (first run)"
    elif [ "$pwfp" != "$(cat "$PWFP_FILE")" ]; then
        fail "uid=[USERNAME] directory password CHANGED outside change-directory-password.sh — update the Nextcloud, portal, Dovecot and Mac Keychain copies now or the account will lock"
    else
        ok "uid=[USERNAME] password unchanged since the last recorded change"
    fi
    nowz=$(date -u +%Y%m%d%H%M%SZ)
    unlock=$(printf '%s\n' "$DS_ENTRY" | awk '/^accountUnlockTime:/{print $2}')
    retries=$(printf '%s\n' "$DS_ENTRY" | awk '/^passwordRetryCount:/{print $2}')
    rreset=$(printf '%s\n' "$DS_ENTRY" | awk '/^retryCountResetTime:/{print $2}')
    if [ -n "$unlock" ] && [[ "$unlock" > "$nowz" ]]; then
        fail "uid=[USERNAME] is LOCKED until $unlock UTC — portal, webmail and Nextcloud directory lookups are failing"
    elif [ "${retries:-0}" -ge 2 ] && [ -n "$rreset" ] && [[ "$rreset" > "$nowz" ]]; then
        fail "uid=[USERNAME] has $retries failed logins in the last 10 min — a stored copy may be stale; the account locks at 3"
    else
        ok "uid=[USERNAME] not locked, no run of failed logins"
    fi
fi

# --- 11. Mac audit subsystem warnings reach a person (3.3.4) ---------------
SEC_ID="11"; SEC_NAME="Mac audit subsystem warnings reach a person (3.3.4)"
# /etc/security/audit_warn on the Mac copies each warning to /var/log/diwai-audit-warn.log,
# the Mac agent forwards it, rule 100220 alerts. Wazuh email is off on this manager,
# so THIS check is the delivery path: a warning in the last 30 min fails the run, and
# the run's state-change mail reaches the owner. Clears by itself 30 min later.
AW=$(tail -n 200000 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep '"id":"100220"' | grep '"location":"/var/log/diwai-audit-warn.log"' | grep -vE 'audit warning: (closefile|expired)' | tail -1)
if [ -z "$AW" ]; then
    ok "no Mac audit subsystem warning on record"
else
    aw_ts=$(printf '%s' "$AW" | grep -o '"timestamp":"[^"]*"' | head -1 | cut -d'"' -f4)
    aw_ep=$(date -d "$aw_ts" +%s 2>/dev/null || echo 0)
    aw_age=$(( $(date +%s) - aw_ep ))
    if [ "$aw_ep" -gt 0 ] && [ "$aw_age" -le 1800 ]; then
        fail "Mac audit subsystem warning $(( aw_age / 60 )) min ago: $(printf '%s' "$AW" | grep -o '"full_log":"[^"]*"' | cut -d'"' -f4 | cut -c1-140) - audit logging on the Mac may be failing (3.3.4)"
    else
        ok "no Mac audit subsystem warning in the last 30 min"
    fi
fi

# --- 12. Wazuh API alive, with the OpenSSL workaround it depends on --------
SEC_ID="12"; SEC_NAME="Wazuh API alive, with the OpenSSL workaround it depends on"
# Wazuh 4.14.7 bundles OpenSSL 3.5, which crashes (SIGILL) on this VM unless
# OPENSSL_armcap=0x87d is set - the guest advertises SVE2 without SVE (POA&M-051,
# 2026-09-13). The setting lives ONLY in the systemd drop-in
# /etc/systemd/system/wazuh-manager.service.d/openssl-armcap.conf. Check 1 stays
# green while the API is dead, so check the API process itself. A restart via
# `/var/ossec/bin/wazuh-control` from a shell does not carry the setting.
APIPID=$(pgrep -f wazuh_apid | head -1)
if [ -z "$APIPID" ]; then
    fail "wazuh-apid NOT running - if Wazuh was restarted with wazuh-control instead of systemctl, or the openssl-armcap drop-in is missing, OpenSSL 3.5 crashes on this VM (POA&M-051). Restart with: systemctl restart wazuh-manager"
elif ! tr '\0' '\n' < /proc/$APIPID/environ 2>/dev/null | grep -q '^OPENSSL_armcap='; then
    fail "wazuh-apid running WITHOUT OPENSSL_armcap - it will crash on its next cryptography use (POA&M-051). Restart with: systemctl restart wazuh-manager"
else
    ok "wazuh-apid running with the OpenSSL workaround"
fi

# --- 13. Mac inactivity enforcement (3.5.6) is running and has nothing to report ---
SEC_ID="13"; SEC_NAME="Mac inactivity enforcement (3.5.6) is running and has nothing to report"
# /usr/local/sbin/diwai-inactivity-enforce runs daily on the Mac, disables local accounts
# unused for 90 days (sysadmin exempt) and logs DISABLED / WARNING / RUN lines that the
# agent forwards (rules 100222-100224). Fails on: a disable or warning in the last 26 h,
# or NO heartbeat in the last 26 h (a job that stopped running is a control that stopped).
# alerts.json restarts at midnight, so between 00:00 and the 04:20 run the live file holds no heartbeat. Read
# yesterday's rotated file as well (DIWAI-CR-2026-10-11): without it this check failed every night at ~00:15
# and recovered at 04:30.
PREV_ALERTS="/var/ossec/logs/alerts/$(date -d yesterday +%Y/%b)/ossec-alerts-$(date -d yesterday +%d).json.gz"
IA=$( { [ -r "$PREV_ALERTS" ] && zcat "$PREV_ALERTS" 2>/dev/null | grep '"location":"/var/log/diwai-inactivity.log"'; \
        tail -n 300000 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep '"location":"/var/log/diwai-inactivity.log"'; } )
now_ep=$(date +%s)
last_of(){ printf '%s\n' "$IA" | grep "\"id\":\"$1\"" | tail -1; }
age_of(){ t=$(printf '%s' "$1" | grep -o '"timestamp":"[^"]*"' | head -1 | cut -d'"' -f4); e=$(date -d "$t" +%s 2>/dev/null || echo 0); echo $(( now_ep - e )); }
# Lines tagged test=1 come from the installer's proof test: they prove the rule fires but must not
# hold this check failed for 26 h.
D=$(printf '%s\n' "$IA" | grep '"id":"100222"' | grep -v 'test=1' | tail -1); W=$(printf '%s\n' "$IA" | grep '"id":"100223"' | grep -v 'test=1' | tail -1); R=$(last_of 100224)
if [ -n "$D" ] && [ "$(age_of "$D")" -le 93600 ]; then
    fail "Mac account DISABLED for inactivity: $(printf '%s' "$D" | grep -o '"full_log":"[^"]*"' | cut -d'"' -f4 | sed 's/.*diwai-inactivity: //' | cut -c1-120) (3.5.6) - recover by logging in as sysadmin"
elif [ -n "$W" ] && [ "$(age_of "$W")" -le 93600 ]; then
    fail "Mac account nearing inactivity disable: $(printf '%s' "$W" | grep -o '"full_log":"[^"]*"' | cut -d'"' -f4 | sed 's/.*diwai-inactivity: //' | cut -c1-120) (3.5.6) - log in to reset"
elif [ -z "$R" ] || [ "$(age_of "$R")" -gt 93600 ]; then
    fail "Mac inactivity enforcement job has not reported in 26 h - 3.5.6 enforcement may have stopped (diwai-inactivity-enforce)"
else
    ok "Mac inactivity enforcement ran in the last 26 h, nothing disabled or near disable"
fi

# --- 14. Patch review cadence (3.14.1 / DIWAI-PR-001) ----------------------
SEC_ID="14"; SEC_NAME="Patch review cadence (3.14.1 / DIWAI-PR-001)"
# The cadence moved weekly -> monthly on 2026-09-15 because the weekly one lapsed
# for 5.5 weeks unnoticed: the SCANS kept running, the REVIEW stopped, and nothing
# watched the difference. The CVE checks above watch FINDING age; this watches
# REVIEW age, which is the gap that actually occurred. Sourced from the Mac figures
# key (patch_review_date = newest dated row in CUI_Patch_Review_Log.md).
PR_MAX_DAYS=35          # monthly cadence plus a few days' grace
PRD=$(ssh -i /root/.ssh/id_ecdsa_dashboard_p256 -o IdentitiesOnly=yes -o BatchMode=yes \
        -o ConnectTimeout=10 -o StrictHostKeyChecking=no [USERNAME]@[LAN-IP-REDACTED] figures 2>/dev/null \
      | sed -n 's/^patch_review_date=//p' | head -1)
if [ -z "$PRD" ]; then
    ok "patch review date not sourceable from the Mac (figures key) - not treated as failure"
else
    prd_ep=$(date -d "$PRD" +%s 2>/dev/null || echo 0)
    if [ "$prd_ep" -eq 0 ]; then
        fail "patch review date '$PRD' unparseable - CUI_Patch_Review_Log.md may be malformed"
    else
        pr_age=$(( ( $(date +%s) - prd_ep ) / 86400 ))
        if [ "$pr_age" -gt "$PR_MAX_DAYS" ]; then
            fail "no patch review logged for ${pr_age}d (last $PRD) - monthly cadence has lapsed (DIWAI-PR-001 §3)"
        else
            ok "patch review ${pr_age}d old (last $PRD, monthly cadence)"
        fi
    fi
fi

# --- 15. Mac SSH still demands TOTP (3.5.3 / 3.7.5) ------------------------------
SEC_ID="15"; SEC_NAME="Mac SSH still demands TOTP (3.5.3 / 3.7.5)"
# diwai-mfa-pam-check runs hourly and at boot on the Mac (launchd) and logs OK / FAIL lines that the agent forwards
# (rules 100226 / 100227). A macOS update removed the Mac TOTP line on 2026-09-03 and nothing noticed for 36 days
# (DIWAI-CR-2026-10-11). Fails on a FAIL newer than the last OK, or on no OK for 9000 s (2.5 h). Reads yesterday's
# rotated alerts too, as check 13 does, so the midnight rotation cannot hide a heartbeat.
MP=$( { [ -r "$PREV_ALERTS" ] && zcat "$PREV_ALERTS" 2>/dev/null | grep '"location":"/var/log/diwai-mfa-pam.log"'; \
        tail -n 300000 /var/ossec/logs/alerts/alerts.json 2>/dev/null | grep '"location":"/var/log/diwai-mfa-pam.log"'; } )
MF=$(printf '%s\n' "$MP" | grep '"id":"100227"' | tail -1); MO=$(printf '%s\n' "$MP" | grep '"id":"100226"' | tail -1)
if [ -n "$MF" ] && { [ -z "$MO" ] || [ "$(age_of "$MF")" -le "$(age_of "$MO")" ]; }; then
    fail "Mac SSH no longer demands TOTP: $(printf '%s' "$MF" | grep -o '"full_log":"[^"]*"' | cut -d'"' -f4 | sed 's/.*diwai-mfa-pam: //' | cut -c1-160) (3.5.3 / 3.7.5)"
elif [ -z "$MO" ] || [ "$(age_of "$MO")" -gt 9000 ]; then
    fail "Mac TOTP check has not reported in 2.5 h - the hourly check on the Mac may have stopped (diwai-mfa-pam-check)"
else
    ok "Mac SSH TOTP check passed within the last 2.5 h (TOTP line present)"
fi

# --- report ------------------------------------------------------------------
python3 - "$DIWAI_JSON_LINES" "$DIWAI_JSON_DIR" <<'DIWAI_PY' 2>/dev/null || true
import hashlib, json, os, socket, sys, tempfile, time
lines_file, out_dir = sys.argv[1], sys.argv[2]
checks = []
if lines_file != "/dev/null" and os.path.exists(lines_file):
    for row in open(lines_file, errors="replace"):
        parts = row.rstrip("\n").split("\t", 3)
        if len(parts) == 4:
            status, cid, name, detail = parts
            checks.append({"id": cid, "name": name, "status": status, "detail": detail})
    os.remove(lines_file)
ver = hashlib.sha256(open("/usr/local/sbin/diwai-control-health", "rb").read()).hexdigest()[:12]
doc = {"host": socket.gethostname().split(".")[0], "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
       "monitor_version": ver, "checks": checks}
fd, tmp = tempfile.mkstemp(dir=out_dir, prefix=".latest.")
with os.fdopen(fd, "w") as fh:
    json.dump(doc, fh, indent=1)
os.chmod(tmp, 0o644)
os.replace(tmp, os.path.join(out_dir, "latest.json"))
DIWAI_PY
echo
if [ ${#FAILURES[@]} -eq 0 ]; then
    echo "RESULT: all $CHECKS checks passed"
    logger -t "$TAG" -p daemon.info "control health OK ($CHECKS checks)"

    # Recovery notice (POA&M-067): if the previous run had failures, say so once.
    # Without this, a failure that resolves itself is never reported as resolved,
    # and the reader cannot tell "fixed" from "stopped alerting".
    STATE_FILE=/var/lib/diwai/control-health.state
    if [ -s "$STATE_FILE" ] && grep -qv '^#' "$STATE_FILE" 2>/dev/null; then
        if command -v sendmail >/dev/null 2>&1; then
            {
                echo "Subject: [diwai] CONTROL HEALTH RECOVERED on $(hostname)"
                echo "To: $RECOVERY_MAIL_TO"
                echo
                echo "$(date '+%Y-%m-%d %H:%M:%S %Z')"
                echo
                echo "All $CHECKS control checks now pass. Previously failing:"
                grep -v '^#' "$STATE_FILE" | sed 's/^/  - /'
            } | sendmail -t 2>/dev/null && echo "  (recovery mailed to $RECOVERY_MAIL_TO)"
        fi
        : > "$STATE_FILE"
    fi
    exit 0
fi

echo "RESULT: ${#FAILURES[@]} of $CHECKS checks FAILED"
printf '  - %s\n' "${FAILURES[@]}"

# Dual-path alert: syslog for Wazuh, mail for when Wazuh is the thing that broke.
for f in "${FAILURES[@]}"; do
    logger -t "$TAG" -p daemon.err "CONTROL FAILURE: $f"
done

# --- mail on STATE CHANGE only (POA&M-067, 2026-08-07) ----------------------
#
# This block used to mail on every failing run. The timer fires every 15 minutes,
# so a single unresolved failure produced up to 96 identical mails a day: 81 of
# the 93 alerts sitting unread in the mailbox were one failure (chrony with no
# selected source). Genuine alerts were buried underneath -- an archive stuck in
# staging, the dashboard returning 500, a CRITICAL vulnerability inside its 72h
# window. Delivery was never the problem; attention was.
#
# Mail is now sent when the failure SET CHANGES, when failures CLEAR, or once per
# REMIND_HOURS while something remains broken. syslog above still fires on every
# run, so Wazuh retains the complete record for audit -- de-duplication applies to
# the human channel only.
#
# State file holds one failure string per line, plus a "#last-mail <epoch>" line.

STATE_DIR=/var/lib/diwai
STATE_FILE="${STATE_DIR}/control-health.state"
REMIND_HOURS=24

mkdir -p "$STATE_DIR" 2>/dev/null

PREV_FAILURES=()
PREV_MAIL_EPOCH=0
if [ -r "$STATE_FILE" ]; then
    while IFS= read -r line; do
        case "$line" in
            "#last-mail "*) PREV_MAIL_EPOCH="${line#\#last-mail }" ;;
            "") : ;;
            *) PREV_FAILURES+=("$line") ;;
        esac
    done < "$STATE_FILE"
fi

contains() {  # contains <needle> <haystack...>
    local needle="$1"; shift
    local item
    for item in "$@"; do [ "$item" = "$needle" ] && return 0; done
    return 1
}

NEW_FAILURES=()
for f in "${FAILURES[@]}"; do
    contains "$f" ${PREV_FAILURES[@]+"${PREV_FAILURES[@]}"} || NEW_FAILURES+=("$f")
done

CLEARED=()
for p in ${PREV_FAILURES[@]+"${PREV_FAILURES[@]}"}; do
    contains "$p" "${FAILURES[@]}" || CLEARED+=("$p")
done

NOW_EPOCH=$(date +%s)
REMIND_DUE=0
if [ "$PREV_MAIL_EPOCH" -gt 0 ] 2>/dev/null; then
    [ $(( NOW_EPOCH - PREV_MAIL_EPOCH )) -ge $(( REMIND_HOURS * 3600 )) ] && REMIND_DUE=1
else
    REMIND_DUE=1
fi

SHOULD_MAIL=0
REASON=""
if [ ${#NEW_FAILURES[@]} -gt 0 ]; then
    SHOULD_MAIL=1; REASON="new failure(s)"
elif [ ${#CLEARED[@]} -gt 0 ]; then
    SHOULD_MAIL=1; REASON="failure(s) cleared"
elif [ "$REMIND_DUE" -eq 1 ]; then
    SHOULD_MAIL=1; REASON="${REMIND_HOURS}h reminder, unchanged"
fi

if [ "$SHOULD_MAIL" -eq 1 ] && command -v sendmail >/dev/null 2>&1; then
    {
        echo "Subject: [diwai] CONTROL HEALTH FAILURE on $(hostname) — ${REASON}"
        echo "To: $MAIL_TO"
        echo
        echo "$(date '+%Y-%m-%d %H:%M:%S %Z')"
        echo
        echo "Why this mail was sent: ${REASON}."
        echo "Checks run every 15 min; mail is sent only on change or every ${REMIND_HOURS}h."
        echo
        echo "${#FAILURES[@]} of $CHECKS control checks are failing:"
        printf '  - %s\n' "${FAILURES[@]}"
        if [ ${#NEW_FAILURES[@]} -gt 0 ]; then
            echo
            echo "NEW since the last mail:"
            printf '  + %s\n' "${NEW_FAILURES[@]}"
        fi
        if [ ${#CLEARED[@]} -gt 0 ]; then
            echo
            echo "CLEARED since the last mail:"
            printf '  - (resolved) %s\n' "${CLEARED[@]}"
        fi
        echo
        echo "A failure here means a security control has stopped, not that it"
        echo "reported a problem. Investigate before assuming monitoring is intact."
    } | sendmail -t 2>/dev/null && echo "  (alert mailed to $MAIL_TO — ${REASON})"
    PREV_MAIL_EPOCH="$NOW_EPOCH"
else
    echo "  (no mail — failure set unchanged, next reminder in $(( REMIND_HOURS - (NOW_EPOCH - PREV_MAIL_EPOCH)/3600 ))h)"
fi

{ printf '%s\n' "${FAILURES[@]}"; echo "#last-mail ${PREV_MAIL_EPOCH}"; } > "$STATE_FILE"

exit 1
