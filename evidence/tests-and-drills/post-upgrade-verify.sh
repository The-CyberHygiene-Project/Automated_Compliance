#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# Post-upgrade verification — macOS 26.6 + VM kernel 687.33.1
# DIWAI-CR-2026-08-08 · DIWAI-PR-001 §4.6 (post-change verification is mandatory)
#
# Run AFTER the Mac restarts and the VM has been unlocked and started.
# Compares against ~/diwai/cve-reports/preflight-2026-08-03.txt
set -uo pipefail
P=0; F=0
ok(){ printf "  [ OK ] %s\n" "$*"; P=$((P+1)); }
bad(){ printf "  [FAIL] %s\n" "$*"; F=$((F+1)); }
# A check that could not RUN is not a check that PASSED, and must not be
# reported as a failed control either — see 2026-08-03, where no passwordless
# sudo made the pf check report the firewall as reverted when it was intact.
inc(){ printf "  [ ?? ] %s\n" "$*"; F=$((F+1)); }

# Prime sudo up front so the pf check below can actually run. This script is
# run interactively by the operator, so prompting here is acceptable; the
# alternative is a check that silently cannot execute.
echo "Priming sudo for the pf ruleset check..."
sudo -v 2>/dev/null || true

echo "=== post-upgrade verification $(date '+%F %T') ==="
echo
echo "--- Mac ---"
v=$(sw_vers -productVersion)
[ "$v" != "26.5.1" ] && ok "macOS now $v (was 26.5.1)" || bad "macOS still $v — update did not apply"
fdesetup status 2>/dev/null | grep -q "FileVault is On" && ok "FileVault On" || bad "FileVault NOT on"
if ! sudo -n true 2>/dev/null; then
  inc "pf en1 blocks NOT VERIFIED — no sudo; run: sudo pfctl -s rules | grep en1"
else
  pfrules=$(sudo -n pfctl -s rules 2>/dev/null)
  if [ -z "$pfrules" ]; then
    inc "pf en1 blocks NOT VERIFIED — pfctl returned nothing (is pf enabled?)"
  elif printf '%s\n' "$pfrules" | grep -q "block drop in quick on en1"; then
    ok "pf en1 blocks survived the update"
  else
    bad "pf en1 block rules MISSING — reload /etc/pf_diwai.conf"
  fi
fi
[ "$(networksetup -getairportpower en1 2>/dev/null | grep -c Off)" -gt 0 ] \
  && ok "Wi-Fi still off" || bad "Wi-Fi came back ON"
for p in nginx php-fpm redis-server; do
  pgrep -q "$p" && ok "$p running" || bad "$p NOT running"
done
c=$(curl -sk -m 10 -o /dev/null -w '%{http_code}' https://localhost 2>/dev/null)
[ "$c" = "302" ] || [ "$c" = "200" ] && ok "Nextcloud HTTP $c" || bad "Nextcloud HTTP ${c:-unreachable}"
c=$(curl -sk -m 15 -o /dev/null -w '%{http_code}' https://cloud.[DOMAIN.ORG]/hosting/discovery 2>/dev/null)
[ "$c" = "200" ] && ok "Collabora HTTP 200" || bad "Collabora HTTP ${c:-unreachable} — run collabora-ensure.sh"
c=$(curl -sf -m 8 -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null)
[ "$c" = "200" ] && ok "Open WebUI HTTP 200" || bad "Open WebUI ${c:-unreachable}"

echo
echo "--- VM ---"
if ssh -i ~/.ssh/diwai_rsa -o BatchMode=yes -o ConnectTimeout=10 [USERNAME]@[LAN-IP-REDACTED] true 2>/dev/null; then
  ok "VM reachable over SSH"
  k=$(ssh -i ~/.ssh/diwai_rsa -o BatchMode=yes [USERNAME]@[LAN-IP-REDACTED] 'uname -r' 2>/dev/null)
  [ "$k" = "5.14.0-687.33.1.el9_8.aarch64" ] && ok "VM running new kernel $k" || bad "VM kernel is $k (expected 687.33.1)"
  n=$(ssh -i ~/.ssh/diwai_rsa -o BatchMode=yes [USERNAME]@[LAN-IP-REDACTED] \
      'n=0; for s in httpd mariadb dirsrv@diwai wazuh-manager suricata fapolicyd auditd chronyd firewalld postfix dovecot; do
         [ "$(systemctl is-active $s 2>/dev/null)" = active ] && n=$((n+1)); done; echo $n' 2>/dev/null)
  [ "$n" = "11" ] && ok "VM services 11/11 active" || bad "VM services $n/11 active"
  h=$(ssh -i ~/.ssh/diwai_rsa -o BatchMode=yes [USERNAME]@[LAN-IP-REDACTED] \
      'sudo /usr/local/sbin/diwai-control-health 2>/dev/null | tail -1' 2>/dev/null)
  echo "$h" | grep -q "all 24 checks passed" && ok "control-health: $h" || bad "control-health: ${h:-no result}"
else
  bad "VM NOT reachable — has it been unlocked and started?"
fi

echo
echo "--- external reachability ---"
c=$(curl -sk -m 15 -o /dev/null -w '%{http_code}' https://webmail.[DOMAIN.ORG] 2>/dev/null)
[ "$c" = "200" ] && ok "webmail reachable from outside path" || bad "webmail HTTP ${c:-unreachable}"

echo
echo "=== $P passed, $F failed ==="
[ "$F" -eq 0 ] && echo "  Clean. Record in the patch review log." || echo "  INVESTIGATE before closing the change."
exit $([ "$F" -eq 0 ] && echo 0 || echo 1)
