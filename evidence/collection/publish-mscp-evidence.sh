#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# Publish the weekly mSCP audit result into the CUI evidence store.
#
# WHY THIS EXISTS (DIWAI-VS-002 §5)
#   run-mSCP-scan.sh runs every Sunday 03:00 and writes its result to a plist and
#   a log -- but nothing carried that result into Compliance/Evidence/Scans/. The
#   newest published mSCP report was 2026-08-02 while the scan itself was healthy
#   at 132/136. An assessor reading the evidence folder would conclude scanning
#   had stopped. Unfinished Portal-B work, pending since the 06-12 refactor.
#
# DESIGN NOTES
#   * Runs as [USERNAME], NOT root: the source plist and log are world-readable, so
#     no privilege is needed, and no root process writes into the Nextcloud data
#     directory. `occ` then runs as the account that owns those files.
#   * Publishes MARKDOWN, not HTML/PDF: Nextcloud refuses to render HTML, and the
#     headless-Chrome PDF path is fragile. Same choice already made for OpenSCAP.
#   * IDEMPOTENT and runs DAILY, not weekly: a missed Sunday is caught the next
#     morning. Re-running publishes nothing new.
#   * AUDIT ONLY. It reads results; it never scans and never remediates.
set -u

PLIST=/Library/Preferences/org.diwai_phase1.audit.plist
SCANLOG=/var/log/mscp-scan.log
DEST=/opt/local/nextcloud/data/__groupfolders/1/files/Compliance/Evidence/Scans
NCROOT=/opt/local/nextcloud
LOG="$HOME/Library/Logs/mscp-publish.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

[ -r "$PLIST" ] || { log "ABORT: cannot read $PLIST"; exit 1; }
[ -d "$DEST" ]  || { log "ABORT: evidence folder missing: $DEST"; exit 1; }

# Date the evidence by WHEN THE SCAN RAN, not when we publish.
SCANDATE=$(stat -f '%Sm' -t '%Y-%m-%d' "$PLIST")
MD="$DEST/CUI_mSCP-securemac-${SCANDATE}.md"
PL="$DEST/CUI_mSCP-securemac-${SCANDATE}.plist"

if [ -f "$PL" ] && cmp -s "$PLIST" "$PL"; then
    log "already published for ${SCANDATE} — nothing to do"
    exit 0
fi

SUMMARY=$(/usr/bin/python3 - "$PLIST" <<'PY'
import plistlib, sys, hashlib
p = sys.argv[1]
raw = open(p, 'rb').read()
d = plistlib.loads(raw)
fails = sorted(k for k, v in d.items() if isinstance(v, dict) and v.get('finding'))
total = len(d); failed = len(fails); passed = total - failed
pct = (passed * 100 // total) if total else 0
print(f"{passed}|{failed}|{total}|{pct}|{hashlib.sha256(raw).hexdigest()}|{','.join(fails)}")
PY
) || { log "ABORT: could not parse $PLIST"; exit 1; }

IFS='|' read -r PASSED FAILED TOTAL PCT SHA FAILS <<<"$SUMMARY"
[ -n "${TOTAL:-}" ] && [ "$TOTAL" -gt 0 ] || { log "ABORT: parsed 0 rules"; exit 1; }

{
  echo "**CUI**"; echo
  echo "# mSCP COMPLIANCE SCAN — ${SCANDATE}"
  echo "## [DOMAIN.ORG] SecureMac Reference System — Mac mini host"; echo
  echo "| Field | Value |"
  echo "|-------|-------|"
  echo "| **Scan date** | ${SCANDATE} |"
  echo "| **Host** | securemac.[DOMAIN.ORG] (Mac mini M4 Pro) |"
  echo "| **Baseline** | mSCP diwai phase-1 |"
  echo "| **Result** | **${PASSED} passed / ${FAILED} failed of ${TOTAL} (${PCT}%)** |"
  echo "| **Mode** | Audit only — \`--check\`. This scan never remediates |"
  echo "| **Source** | \`${PLIST}\` |"
  echo "| **SHA-256 (plist)** | \`${SHA}\` |"
  echo "| **Published by** | \`publish-mscp-evidence.sh\` (DIWAI-VS-002 §5) |"
  echo "| **Classification** | Controlled Unclassified Information (CUI) |"
  echo
  if [ "$FAILED" -gt 0 ]; then
    echo "## Failing rules (${FAILED})"; echo
    echo "$FAILS" | tr ',' '\n' | sed 's/^/- `/;s/$/`/'
  else
    echo "## Failing rules"; echo; echo "None — all ${TOTAL} rules passed."
  fi
  echo
  echo "## Provenance"; echo
  echo "Generated from the audit plist written by \`run-mSCP-scan.sh\`"
  echo "(LaunchDaemon \`org.diwai.mSCP-scan\`, Sundays 03:00). The scan log section"
  echo "for this run is reproduced below verbatim."; echo
  echo '```'
  awk -v d="$SCANDATE" '$0 ~ "=== mSCP scan " d {f=1} f' "$SCANLOG" 2>/dev/null | head -30
  echo '```'
} > "$MD"

cp "$PLIST" "$PL"
chmod 644 "$MD" "$PL"
cp "$MD" "$DEST/CUI_mSCP-securemac-latest.md"

log "published ${SCANDATE}: ${PASSED}/${TOTAL} (${PCT}%), ${FAILED} failing"

if (cd "$NCROOT" && php occ groupfolders:scan 1 >/dev/null 2>&1); then
    log "re-indexed groupfolder 1"
else
    log "WARNING: occ groupfolders:scan failed — files are on disk but may not appear in Nextcloud"
fi
