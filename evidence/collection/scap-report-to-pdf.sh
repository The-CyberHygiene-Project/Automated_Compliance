#!/bin/bash
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
# Convert OpenSCAP HTML reports to PDF and file them in the Nextcloud CUI store.
#
# Created 2026-08-02 (DIWAI-ASMT-2026-08). Runs on the Mac because the PDF
# engine lives here: Chrome headless (Skia/PDF) is what produced the existing
# mSCP PDFs, and there is no PDF tooling on the VM. macOS `cupsfilter` cannot
# do HTML->PDF on this release.
#
# THE IMPORTANT BIT — why the CSS injection exists:
#   The OpenSCAP report hides #result-details behind a "Show all result details"
#   button; jQuery sets an inline display:none on load. Chrome runs that JS, so
#   a naive conversion silently produces a FIVE PAGE SUMMARY with no rule
#   results at all -- an evidence artifact missing the evidence. A stylesheet
#   rule with !important overrides the inline style, giving the full ~416-page
#   report. Do not remove the injection without re-checking the page count.
#
# Direction of travel: the VM pushes reports here (VM->Mac SSH works; the
# reverse does not).

set -uo pipefail

STAGING="${HOME}/scap-staging"
NC_SCANS="/opt/local/nextcloud/data/__groupfolders/1/files/Compliance/Evidence/Scans"
OCC="/opt/homebrew/bin/php /opt/local/nextcloud/occ"
NC_USER="[USERNAME]"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LOG="${HOME}/Library/Logs/scap-report-to-pdf.log"
MIN_PAGES=50          # a correct report is hundreds of pages; 5 means the
                      # injection failed and only the summary rendered

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

mkdir -p "$STAGING"

shopt -s nullglob
FILES=("$STAGING"/*.html)
shopt -u nullglob
[ ${#FILES[@]} -eq 0 ] && exit 0

[ -x "$CHROME" ] || { log "ERROR: Chrome not found at $CHROME"; exit 1; }

log "=== run: ${#FILES[@]} report(s) ==="
CONVERTED=0
FAILED=0

for src in "${FILES[@]}"; do
    base=$(basename "$src" .html)
    log "converting ${base}"

    tmp=$(mktemp -d /tmp/scappdf.XXXXXX)
    expanded="${tmp}/expanded.html"
    pdf="${tmp}/${base}.pdf"

    # Force the result-details section visible; !important beats the inline
    # display:none that jQuery applies at load.
    /usr/bin/python3 - "$src" "$expanded" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
css = ("<style>#result-details{display:block !important;visibility:visible !important}"
       "@media print{#result-details{display:block !important}"
       ".rule-detail{page-break-inside:avoid}"
       ".noprint,.hidden-print,.js-only{display:none !important}}</style>")
t = open(src, errors="ignore").read()
open(dst, "w").write(t.replace("</head>", css + "</head>", 1) if "</head>" in t else css + t)
PY

    "$CHROME" --headless --disable-gpu --no-sandbox \
        --virtual-time-budget=60000 --no-pdf-header-footer \
        --print-to-pdf="$pdf" "file://${expanded}" >/dev/null 2>&1

    if [ ! -s "$pdf" ]; then
        log "  ERROR: no PDF produced for ${base} — leaving source in staging"
        FAILED=$((FAILED + 1)); rm -rf "$tmp"; continue
    fi

    # Verify completeness by page count, not by the file merely existing.
    pages=$(/usr/bin/python3 -c "
import re,sys
d=open(sys.argv[1],'rb').read()
print(len(re.findall(rb'/Type\s*/Page[^s]', d)))" "$pdf" 2>/dev/null)
    pages=${pages:-0}

    if [ "$pages" -lt "$MIN_PAGES" ]; then
        log "  ERROR: only ${pages} pages — the result-details injection likely failed."
        log "         A summary-only PDF is not acceptable evidence. Source kept."
        FAILED=$((FAILED + 1)); rm -rf "$tmp"; continue
    fi

    dest="${NC_SCANS}/CUI_${base}.pdf"
    if cp "$pdf" "$dest"; then
        chmod 644 "$dest"
        # keep a stable "latest" alongside the dated copy
        case "$base" in
            *services*) cp "$pdf" "${NC_SCANS}/CUI_oscap-services-latest.pdf" ;;
        esac
        sz=$(/usr/bin/stat -f%z "$dest")
        log "  OK ${pages} pages, $((sz / 1048576)) MB -> $(basename "$dest")"
        rm -f "$src"
        CONVERTED=$((CONVERTED + 1))
    else
        log "  ERROR: could not write ${dest}"
        FAILED=$((FAILED + 1))
    fi
    rm -rf "$tmp"
done

if [ "$CONVERTED" -gt 0 ]; then
    $OCC files:scan --path="/${NC_USER}/files/CUI/Compliance/Evidence/Scans" >/dev/null 2>&1 \
        && log "  Nextcloud re-indexed" || log "  WARNING: occ files:scan failed"
fi

log "converted ${CONVERTED}, failed ${FAILED}"
[ "$FAILED" -eq 0 ] || exit 1
