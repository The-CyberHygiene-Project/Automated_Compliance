#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Generate a human-readable mSCP compliance report from the audit plist.

Why this exists: the Mac is scanned on a timer and the results land in
/Library/Preferences/org.diwai_phase1.audit.plist, but nothing turned that into
a readable report. The Admin Portal's "View Report" button for the Mac pointed at
a folder whose newest macOS report was CUI_mSCP-securemac-latest.pdf dated
2026-06-21 — six weeks stale — while the scan itself was current.

Counting note: the plist contains one non-rule key, `lastComplianceCheck`, which
holds a timestamp. dashboard-refresh computed its score as len(plist) - failures,
which counted that key as both a rule and a pass, reporting 134/136 where the
truth is 133/135. This script counts only keys whose value is a dict with a
boolean `finding`.

Usage:  mscp-report.py [--out DIR]
Default output: the canonical Nextcloud scan-evidence folder.
"""

import argparse
import datetime
import html
import os
import plistlib
import sys

PLIST = "/Library/Preferences/org.diwai_phase1.audit.plist"
CANON = ("/opt/local/nextcloud/data/__groupfolders/1/files/"
         "Compliance/Evidence/Scans")


def load(path):
    with open(path, "rb") as fh:
        return plistlib.load(fh)


def classify(data):
    """Split plist keys into rules and metadata. See module docstring."""
    rules, meta = {}, {}
    for key, val in data.items():
        if isinstance(val, dict) and isinstance(val.get("finding"), bool):
            rules[key] = val["finding"]        # True == finding == FAIL
        else:
            meta[key] = val
    return rules, meta


def render(rules, meta, scan_dt):
    failing = sorted(k for k, bad in rules.items() if bad)
    passing = sorted(k for k, bad in rules.items() if not bad)
    total, npass = len(rules), len(passing)
    pct = round(100 * npass / total) if total else 0
    colour = "#1a7f37" if not failing else "#9a6700"
    gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()

    rows = "\n".join(
        f'<tr class="fail"><td>{html.escape(r)}</td><td>FAIL</td></tr>'
        for r in failing)
    rows += "\n" + "\n".join(
        f'<tr><td>{html.escape(r)}</td><td>pass</td></tr>' for r in passing)

    return f"""<!doctype html>
<meta charset="utf-8">
<title>mSCP Compliance Report — securemac.[DOMAIN.ORG]</title>
<style>
 body{{font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      margin:2rem auto;max-width:60rem;padding:0 1rem;color:#1f2328}}
 h1{{font-size:1.4rem;margin-bottom:.25rem}}
 .sub{{color:#656d76;margin-top:0}}
 .score{{font-size:2rem;font-weight:700;color:{colour}}}
 table{{border-collapse:collapse;width:100%;margin-top:1rem}}
 th,td{{text-align:left;padding:.4rem .6rem;border-bottom:1px solid #d0d7de}}
 th{{background:#f6f8fa}}
 tr.fail td{{background:#fff8c5;font-weight:600}}
 .cui{{font-weight:700;letter-spacing:.08em}}
 code{{background:#f6f8fa;padding:.1rem .3rem;border-radius:3px}}
</style>
<p class="cui">CUI</p>
<h1>mSCP Compliance Report — securemac.[DOMAIN.ORG]</h1>
<p class="sub">macOS baseline <code>diwai_phase1</code> &middot;
 scan {html.escape(str(scan_dt))} &middot; report generated {html.escape(gen)}</p>

<p class="score">{npass}/{total} <span style="font-size:1rem;font-weight:400">
 ({pct}% of rules passing)</span></p>

<p><strong>Counting:</strong> {total} rules evaluated. The plist also carries a
 <code>lastComplianceCheck</code> timestamp, which is metadata and is
 <em>not</em> counted as a rule — earlier dashboard figures of
 {total + 1} included it.</p>

<h2>Failing rules ({len(failing)})</h2>
{"<p>None — all evaluated rules pass.</p>" if not failing else ""}
<table><thead><tr><th>Rule</th><th>Result</th></tr></thead>
<tbody>
{rows}
</tbody></table>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plist", default=PLIST)
    ap.add_argument("--out", default=CANON)
    args = ap.parse_args()

    if not os.path.exists(args.plist):
        sys.exit(f"audit plist not found: {args.plist}")

    data = load(args.plist)
    rules, meta = classify(data)
    if not rules:
        sys.exit("no rules with a boolean 'finding' — plist shape unexpected")

    scan_dt = meta.get("lastComplianceCheck", "unknown")
    stamp = str(scan_dt)[:10] if str(scan_dt)[:4].isdigit() else \
        datetime.date.today().isoformat()

    if not os.path.isdir(args.out):
        sys.exit(f"output directory does not exist: {args.out}")

    body = render(rules, meta, scan_dt)
    dated = os.path.join(args.out, f"CUI_mSCP-securemac-{stamp}.html")
    latest = os.path.join(args.out, "CUI_mSCP-securemac-latest.html")
    for path in (dated, latest):
        with open(path, "w") as fh:
            fh.write(body)
        os.chmod(path, 0o644)

    npass = sum(1 for bad in rules.values() if not bad)
    print(f"  scan date : {scan_dt}")
    print(f"  score     : {npass}/{len(rules)}")
    print(f"  failing   : "
          f"{', '.join(sorted(k for k, b in rules.items() if b)) or 'none'}")
    print(f"  written   : {dated}")
    print(f"              {latest}")


if __name__ == "__main__":
    main()
