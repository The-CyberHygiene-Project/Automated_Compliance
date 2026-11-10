#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# Phase 2 technical scrub — Mac host evidence collection.
# Part of DIWAI-ASMT-2026-08. Read-only: inspects and scans, changes nothing.
#
# Run as:  sudo /Users/[USERNAME]/diwai/assessment-2026-08/collect-mac-evidence.sh
#
# Writes everything to a single file for Claude to read back. The mSCP scan is
# the slow part (several minutes) — let it finish.

set -u

OUT=/Users/[USERNAME]/diwai/assessment-2026-08/evidence/mac-scrub-raw-$(date +%Y%m%d-%H%M%S).txt
MSCP=/usr/local/bin/run-mSCP-scan.sh
MSCP_REAL="/Users/[USERNAME]/Documents/SecureMac Project Docs/USB Reference/mSCP_diwai_phase1_compliance.sh"

if [ "$(id -u)" -ne 0 ]; then
    echo "This needs root. Run:  sudo $0"
    exit 1
fi

exec > >(tee "$OUT") 2>&1

sec() { echo; echo "================ $* ================"; }

echo "[DOMAIN.ORG] Mac host evidence — $(date)"
echo "host: $(hostname)  macOS: $(sw_vers -productVersion)  build: $(sw_vers -buildVersion)"

sec "FileVault (3.13.16 at rest)"
fdesetup status

sec "System Integrity Protection (3.4.2)"
csrutil status

sec "Gatekeeper / code signing (3.4.8, 3.14.2)"
spctl --status 2>&1
echo "--- assessments:"; spctl --assess --verbose /Applications/Safari.app 2>&1 | head -2

sec "pf firewall (3.13.1)"
pfctl -s info 2>&1 | head -6
echo "--- anchors:"; pfctl -s Anchors 2>&1 | head -10
echo "--- rules:"; pfctl -s rules 2>&1 | head -25

sec "Application firewall"
/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>&1
/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode 2>&1

sec "USBGuard / removable media (3.8.7, 3.8.8)"
launchctl print system/org.diwai.usb-guard 2>&1 | grep -E "state|program|path" | head -5
ls -la /Library/LaunchDaemons/org.diwai.usb-guard.plist 2>&1

sec "Wazuh agent (3.3.1, 3.14.6)"
if [ -x /Library/Ossec/bin/wazuh-control ]; then
    /Library/Ossec/bin/wazuh-control status 2>&1
    echo "--- agent id/server:"
    grep -E "<address>|<enrollment>|agent_name" /Library/Ossec/etc/ossec.conf 2>/dev/null | head -5
    echo "--- last log lines:"; tail -5 /Library/Ossec/logs/ossec.log 2>/dev/null
else
    echo "wazuh-control not found at /Library/Ossec/bin"
fi

sec "Software updates pending (3.14.1)"
softwareupdate --list 2>&1 | head -15

sec "Listening network services (3.13.1)"
netstat -an -p tcp | grep LISTEN | awk '{print $4}' | sort -u | head -30

sec "Local accounts (3.1.1, 3.5.x)"
dscl . -list /Users | grep -vE "^_" | head -20
echo "--- admin group:"; dscl . -read /Groups/admin GroupMembership 2>&1

sec "Login/auth policy (3.5.7-3.5.11)"
pwpolicy -getaccountpolicies 2>&1 | head -20

sec "Screen lock (3.1.10)"
sudo -u [USERNAME] defaults -currentHost read com.apple.screensaver askForPassword 2>&1
sudo -u [USERNAME] defaults -currentHost read com.apple.screensaver askForPasswordDelay 2>&1

sec "Audit / logging (3.3.1)"
ls -la /var/audit 2>/dev/null | tail -5
echo "--- audit config:"; grep -vE "^#|^$" /etc/security/audit_control 2>/dev/null

sec "TLS certificate in service (3.13.11)"
openssl x509 -in /etc/ssl/diwai/[DOMAIN.ORG].crt -noout -subject -issuer -dates 2>&1

sec "Nextcloud / CUI repository (3.1.1, 3.5.3)"
sudo -u [USERNAME] /opt/homebrew/bin/php /opt/local/nextcloud/occ status 2>&1 | head -8
echo "--- 2FA enforcement:"
sudo -u [USERNAME] /opt/homebrew/bin/php /opt/local/nextcloud/occ config:app:get twofactor_totp enabled 2>&1
echo "--- app list (security-relevant):"
sudo -u [USERNAME] /opt/homebrew/bin/php /opt/local/nextcloud/occ app:list 2>&1 | grep -iE "twofactor|accesscontrol|automatedtagging|admin_audit|files_antivirus" | head -8

sec "FINDING CHECK — the installed weekly scan wrapper"
# 2026-08-01: /usr/local/bin/run-mSCP-scan.sh was found to be a ZERO-BYTE file.
# The weekly org.diwai.mSCP-scan LaunchDaemon has therefore been executing an
# empty script, and no mSCP results have been produced since 2026-04-24.
ls -la "$MSCP" 2>&1
echo "byte count: $(wc -c < "$MSCP" 2>/dev/null)  (0 = the finding is confirmed)"
ls -la /var/log/mscp-scan.log 2>&1

sec "mSCP configuration profile installed? (the audit needs it)"
profiles list -all 2>&1 | head -15
profiles show -type configuration 2>&1 | head -15

sec "mSCP compliance audit (3.4.1) — SLOW, several minutes"
# Uses the real generated audit script. --check is AUDIT ONLY (run_scan).
# --fix is deliberately never passed. With no arguments the script drops into
# an interactive menu, which would hang an unattended run.
if [ -x "$MSCP_REAL" ]; then
    echo "running: $MSCP_REAL --check"
    /bin/zsh "$MSCP_REAL" --check 2>&1 | tail -60
    echo
    echo "--- statistics ---"
    /bin/zsh "$MSCP_REAL" --stats 2>&1 | tail -15
    echo "--- counts ---"
    /bin/zsh "$MSCP_REAL" --compliant 2>&1 | tail -3
    /bin/zsh "$MSCP_REAL" --non_compliant 2>&1 | tail -3
else
    echo "real mSCP audit script not found at: $MSCP_REAL"
fi

sec "mSCP results location"
ls -lat /Users/[USERNAME]/*mscp* /Library/Logs/*mscp* /var/log/*mscp* 2>/dev/null | head -8
ls -la /Library/Preferences/org.mscp.* 2>/dev/null | head -5

echo
echo "================ COLLECTION COMPLETE ================"
echo "Written to: $OUT"
echo "Tell Claude the collection is done."
