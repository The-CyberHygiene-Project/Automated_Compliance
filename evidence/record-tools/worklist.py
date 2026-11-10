#!/usr/bin/env python3
# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""worklist — render DIWAI-ORW-001 as an HTML to-do list, and close items.

WHY THIS EXISTS
---------------
The objective-recovery worklist is a to-do list that has to stay in front of the
owner, and shrink as items are done. A Markdown document does neither: it is not
on the dashboard, and closing an item means hand-editing prose.

So the worklist is DATA (etc/worklist-orw-001.json) plus this renderer. Closing an
item is one command; the item then drops off the to-do list and moves to a
completed tail, and the counts move by themselves.

USAGE
    worklist.py render                    # write the HTML fragment + full page
    worklist.py close 3.1.16 "note"       # mark done; drops off the to-do list
    worklist.py reopen 3.1.16             # undo
    worklist.py status                    # one-line summary, and key=value for the dashboard

OUTPUT
    ~/diwai/securemac-site/worklist.html            standalone page
    ~/diwai/securemac-site/worklist-fragment.html   for inclusion in compliance.html
    stdout (status): worklist_open=N worklist_done=N worklist_total=N

The figure the dashboard reports (reqs_met) still comes from the SSP Control
Family Status table via diwai-dashboard-figures. This file tracks the WORK, not
the score: closing an item here is a reminder to re-determine the requirement in
the assessment, which is what actually moves the number.
"""
import json
import os
import sys
import datetime
import html

DATA = os.path.expanduser("~/diwai/etc/worklist-orw-001.json")
OUT_DIR = os.path.expanduser("~/diwai/securemac-site")
PAGE = os.path.join(OUT_DIR, "worklist.html")
FRAGMENT = os.path.join(OUT_DIR, "worklist-fragment.html")

TIER_LABEL = {
    "A": ("Tier A — evidence exists, re-walk only", "Fastest points. Verify the citation, then re-determine."),
    "B": ("Tier B — define it in writing", "A number or a list that has never been written down."),
    "C": ("Tier C — needs a decision or an artifact", "Small piece of work, not just a paragraph."),
}


def load():
    with open(DATA) as fh:
        return json.load(fh)


def save(d):
    tmp = DATA + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(d, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, DATA)


def counts(d):
    items = d["items"]
    done = [i for i in items if i["status"] == "closed"]
    return len(items) - len(done), len(done), len(items)


def esc(s):
    return html.escape(str(s))


def render_fragment(d):
    open_n, done_n, total = counts(d)
    pct = int(round(100 * done_n / total)) if total else 0
    projected = d["baseline_met"] + done_n

    out = []
    out.append('<section class="orw">')
    out.append('<h2>Objective recovery to-do &mdash; <code>DIWAI-ORW-001</code></h2>')
    out.append(
        f'<p class="orw-sub"><strong>{open_n}</strong> open &middot; '
        f'<strong>{done_n}</strong> done of {total} &middot; '
        f'currently <strong>{projected}/{d["total_requirements"]}</strong> objectives met, '
        f'target <strong>{d["target_met"]}/{d["total_requirements"]}</strong></p>'
    )
    out.append(
        f'<div class="orw-bar"><div class="orw-fill" style="width:{pct}%"></div></div>'
    )

    for tier in ("A", "B", "C"):
        todo = [i for i in d["items"] if i["tier"] == tier and i["status"] == "open"]
        if not todo:
            continue
        label, hint = TIER_LABEL[tier]
        out.append(f'<h3>{esc(label)} <span class="orw-count">{len(todo)}</span></h3>')
        out.append(f'<p class="orw-hint">{esc(hint)}</p>')
        out.append('<table class="orw-table"><thead><tr>'
                   '<th>Req</th><th>What it needs</th><th>POA&amp;M</th></tr></thead><tbody>')
        for i in todo:
            blocked = ' <span class="orw-blocked">BLOCKED</span>' if i.get("blocked") else ""
            poam = ", ".join(i["poam"]) if i["poam"] else '<span class="orw-none">none</span>'
            out.append(
                f'<tr><td class="orw-req"><strong>{esc(i["req"])}</strong>{blocked}<br>'
                f'<span class="orw-title">{esc(i["title"])}</span></td>'
                f'<td>{esc(i["action"])}</td><td>{poam}</td></tr>'
            )
        out.append("</tbody></table>")

    done = [i for i in d["items"] if i["status"] == "closed"]
    if done:
        out.append(f'<h3>Completed <span class="orw-count">{len(done)}</span></h3>')
        out.append('<ul class="orw-done">')
        for i in sorted(done, key=lambda x: x.get("closed", "")):
            note = f' &mdash; {esc(i["closed_note"])}' if i.get("closed_note") else ""
            out.append(f'<li><strong>{esc(i["req"])}</strong> {esc(i["title"])} '
                       f'<span class="orw-date">{esc(i.get("closed", ""))}</span>{note}</li>')
        out.append("</ul>")

    out.append(f'<p class="orw-foot">Basis: {esc(d["basis"])}. '
               'Closing an item here is the reminder to re-determine that requirement in the '
               'assessment &mdash; that is what moves the published figure.</p>')
    out.append("</section>")
    return "\n".join(out)


CSS = """
.orw{font:14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#1a1a1a;max-width:1100px}
.orw h2{margin:0 0 4px;font-size:20px}
.orw-sub{margin:0 0 10px;color:#444}
.orw-bar{height:10px;background:#e6e6e6;border-radius:5px;overflow:hidden;margin-bottom:18px}
.orw-fill{height:100%;background:#1a7f37}
.orw h3{margin:18px 0 2px;font-size:15px}
.orw-count{background:#0b5ed7;color:#fff;border-radius:10px;padding:1px 8px;font-size:12px;margin-left:6px}
.orw-hint{margin:0 0 8px;color:#666;font-size:13px}
.orw-table{border-collapse:collapse;width:100%;margin-bottom:8px}
.orw-table th{text-align:left;background:#f2f4f7;padding:6px 8px;border-bottom:2px solid #d0d5dd;font-size:13px}
.orw-table td{padding:6px 8px;border-bottom:1px solid #e4e7ec;vertical-align:top}
.orw-req{white-space:nowrap}
.orw-title{color:#667085;font-size:12px}
.orw-blocked{background:#b42318;color:#fff;border-radius:3px;padding:0 5px;font-size:11px}
.orw-none{color:#98a2b3}
.orw-done li{margin:2px 0}
.orw-date{color:#667085;font-size:12px}
.orw-foot{margin-top:14px;color:#667085;font-size:12px}
"""


def cmd_render():
    d = load()
    frag = render_fragment(d)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(FRAGMENT, "w") as fh:
        fh.write(frag + "\n")
    page = (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
        "<title>Objective Recovery To-Do — DIWAI-ORW-001</title>\n"
        f"<style>{CSS}</style></head><body>\n{frag}\n</body></html>\n"
    )
    with open(PAGE, "w") as fh:
        fh.write(page)
    o, dn, t = counts(d)
    print(f"rendered: {PAGE}")
    print(f"rendered: {FRAGMENT}")
    print(f"{o} open, {dn} done, {t} total")
    return 0


def cmd_close(req, note=None):
    d = load()
    for i in d["items"]:
        if i["req"] == req:
            if i["status"] == "closed":
                print(f"{req} already closed ({i.get('closed')})")
                return 0
            i["status"] = "closed"
            i["closed"] = datetime.date.today().isoformat()
            if note:
                i["closed_note"] = note
            save(d)
            o, dn, t = counts(d)
            print(f"closed {req}. {o} open, {dn} done.")
            print("REMINDER: re-determine this requirement in "
                  "CUI_800-171A_Self_Assessment_2026-08.md and publish, or the figure will not move.")
            return cmd_render()
    sys.exit(f"not in the worklist: {req}")


def cmd_reopen(req):
    d = load()
    for i in d["items"]:
        if i["req"] == req:
            i["status"] = "open"
            i.pop("closed", None)
            i.pop("closed_note", None)
            save(d)
            print(f"reopened {req}")
            return cmd_render()
    sys.exit(f"not in the worklist: {req}")


def cmd_status():
    d = load()
    o, dn, t = counts(d)
    print(f"worklist_open={o}")
    print(f"worklist_done={dn}")
    print(f"worklist_total={t}")
    print(f"worklist_projected={d['baseline_met'] + dn}/{d['total_requirements']}")
    return 0


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "render":
        return cmd_render()
    if cmd == "close":
        if len(sys.argv) < 3:
            sys.exit("close needs a requirement id, e.g. worklist.py close 3.1.16")
        return cmd_close(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    if cmd == "reopen":
        if len(sys.argv) < 3:
            sys.exit("reopen needs a requirement id")
        return cmd_reopen(sys.argv[2])
    if cmd == "status":
        return cmd_status()
    sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    sys.exit(main())
