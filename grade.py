#!/usr/bin/env python3
"""Grade a local AI's 800-171A assessment against the owner's self-assessment (the answer key).

    python3 grade.py assessment.md [MODEL-NAME] > grade-<run>.md

Runs OUTSIDE the sandbox: the answer key is unreadable to the AI. Nothing is dropped silently: every row it
cannot read, every duplicate, every objective with no answer and every objective the key never assessed is
listed in the report.
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY_PATH = Path(os.environ.get("R2_ANSWER_KEY", str(Path.home() / "compliance-private" / "rev2-self-assessment.md")))
KEY_STATUSES = ("OTHER THAN SATISFIED", "PARTIALLY SATISFIED", "SATISFIED", "NOT APPLICABLE", "UNVERIFIED")
AI_STATUSES = {"met": "Met", "unmet": "Unmet", "n/a": "N/A", "na": "N/A", "not applicable": "N/A",
               "not checkable": "Not checkable"}
SOURCES = {"host", "document", "library", "both", "none"}
OBJ = r"3\.\d+\.\d+(?:\[[a-z]+\])?"


def kit_ids(text):
    """Objective ids in kit order: lettered (3.1.1[a]) and single (3.13.4)."""
    return re.findall(r"^- (" + OBJ + r") ", text, re.M)


def _letters(cell):
    """'[a]' -> [a]; '[a]–[c]' -> a,b,c; '[a]/[b]' -> a,b."""
    found = re.findall(r"\[([a-z])\]", cell)
    if len(found) == 2 and re.search(r"\]\s*[–-]\s*\[", cell):
        return [chr(c) for c in range(ord(found[0]), ord(found[1]) + 1)]
    return found


def _key_status(cell):
    s = cell.replace("*", "").strip().upper()
    return next((k for k in KEY_STATUSES if s.startswith(k)), None)


def parse_key(text, kit):
    """{objective: key status} and notes (re-determinations applied, unreadable cells)."""
    kitset, key, notes, reqs = set(kit), {}, [], []
    for line in text.splitlines():
        h = re.match(r"^## (3\.\d+\.\d+(?:\s*/\s*3\.\d+\.\d+)*)", line)
        if h:
            reqs = re.findall(r"3\.\d+\.\d+", h.group(1))
            continue
        if not line.startswith("|") or not reqs:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        req = reqs[0]
        if re.fullmatch(r"3\.\d+\.\d+", cols[0]):          # tables with a Req column
            req, cols = cols[0], cols[1:]
        if not cols:
            continue
        lettered = bool(re.match(r"\[[a-z]\]", cols[0]))
        if not lettered and not re.fullmatch(r"3\.\d+\.\d+", line.strip().strip("|").split("|")[0].strip()):
            continue                                          # header / separator / other tables
        status = _key_status(cols[-1])
        if status is None:
            notes.append(f"key row not read (status cell {cols[-1]!r}): {req} {cols[0]}")
            continue
        if not lettered:                                      # one status for the whole requirement
            hit = [o for o in kit if o == req or o.startswith(req + "[")]
            for o in hit:
                key[o] = status
            notes.append(f"requirement-level determination: {req} -> {status} (applied to {len(hit)} objectives)")
            continue
        for letter in _letters(cols[0]):
            oid = f"{req}[{letter}]"
            if oid not in kitset and req in kitset:          # the key writes a single objective as [a]
                oid = req
            key[oid] = status
    # Re-determinations: the table above each one already shows the CURRENT determination; the note keeps the
    # superseded August values for history. So nothing is overridden; the reader is told where they are.
    sec = None
    for line in text.splitlines():
        h = re.match(r"^## (3\.\d+\.\d+(?:\s*/\s*3\.\d+\.\d+)*)", line)
        if h:
            sec = h.group(1)
        if "RE-DETERMINED" in line and sec:
            notes.append(f"re-determined 2026-09-15 (table shows the current value): {sec}")
    return key, notes


def _ai_status(cell):
    s = cell.replace("*", "").strip().lower()
    for k in sorted(AI_STATUSES, key=len, reverse=True):
        if s == k or s.startswith(k + " ") or s.startswith(k + ":"):
            return AI_STATUSES[k]
    return None


def parse_ai(text, kit):
    """{objective: (status, source)} and problems (duplicates, unreadable rows, unknown ids)."""
    kitset, rows, problems, req = set(kit), {}, [], None
    for line in text.splitlines():
        h = re.match(r"^#{2,4}\s+(?:Requirement\s+)?(3\.\d+\.\d+)\b", line)
        if h:
            req = h.group(1)
            continue
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        first = cols[0].replace("*", "").replace("`", "").strip()
        m = re.fullmatch(OBJ, first)
        if m:
            oid = first
        elif re.fullmatch(r"\[[a-z]+\]", first) and req:
            oid = req + first
        else:
            continue
        if oid not in kitset:
            problems.append(f"not an objective in the kit: {oid}")
            continue
        status = _ai_status(cols[1]) if len(cols) > 1 else None
        if status is None:
            problems.append(f"unreadable status for {oid}: {cols[1] if len(cols) > 1 else ''!r}")
            continue
        source = cols[2].replace("*", "").strip().lower() if len(cols) > 2 else ""
        if oid in rows:
            problems.append(f"duplicate answer for {oid} (first kept)")
            continue
        rows[oid] = (status, source if source in SOURCES else f"? {source}")
    return rows, problems


def compare(kit, key, rows):
    r = {"total": len(kit), "answered": len(rows), "missing": [o for o in kit if o not in rows],
         "agree": [], "lenient": [], "stricter": [], "abstained": [], "na_differs": [], "no_key": [],
         "key_unverified": []}
    for o in kit:
        if o not in rows:
            continue
        ai, k = rows[o][0], key.get(o)
        if k is None:
            r["no_key"].append((o, ai))
        elif k == "UNVERIFIED":
            r["key_unverified"].append((o, ai, k))
        elif ai == "Not checkable":
            r["abstained"].append((o, ai, k))
        elif (ai, k) in {("Met", "SATISFIED"), ("Unmet", "OTHER THAN SATISFIED"),
                         ("Unmet", "PARTIALLY SATISFIED"), ("N/A", "NOT APPLICABLE")}:
            r["agree"].append((o, ai, k))
        elif ai == "Met":
            r["lenient"].append((o, ai, k))
        elif ai == "Unmet" and k == "SATISFIED":
            r["stricter"].append((o, ai, k))
        else:
            r["na_differs"].append((o, ai, k))
    r["sources"] = {}
    for st, src in rows.values():
        r["sources"][src] = r["sources"].get(src, 0) + 1
    r["statuses"] = {}
    for st, _ in rows.values():
        r["statuses"][st] = r["statuses"].get(st, 0) + 1
    return r


def _list(items):
    return "\n".join(f"| {' | '.join(i)} |" for i in items) or "| (none) | | |"


def report(r, problems, notes, model):
    judged = len(r["agree"]) + len(r["lenient"]) + len(r["stricter"]) + len(r["na_differs"])
    pct = f"{100 * len(r['agree']) / judged:.0f}%" if judged else "n/a"
    out = [f"# 800-171A local-AI test: grade ({model})", "",
           f"**Answered {r['answered']} of {r['total']} objectives.** Where both the AI and the answer key gave a "
           f"determination, they agreed on {len(r['agree'])} of {judged} ({pct}). The AI was **more lenient** than "
           f"the key {len(r['lenient'])} times (it said Met; the key did not), and stricter {len(r['stricter'])} times.",
           "", "Answer key: the owner's August 2026 self-assessment with its later re-determinations. The system has "
           "changed since August, so a disagreement is a question for the ISSO, not automatically an AI error.", "",
           "| Measure | Count |", "| --- | --- |"]
    for k, v in sorted(r["statuses"].items()):
        out.append(f"| AI status: {k} | {v} |")
    for k, v in sorted(r["sources"].items()):
        out.append(f"| Evidence source: {k} | {v} |")
    out += [f"| Agree | {len(r['agree'])} |", f"| AI more lenient (Met vs key not satisfied) | {len(r['lenient'])} |",
            f"| AI stricter (Unmet vs key satisfied) | {len(r['stricter'])} |",
            f"| N/A differs | {len(r['na_differs'])} |", f"| AI said Not checkable | {len(r['abstained'])} |",
            f"| Key says UNVERIFIED (not graded) | {len(r['key_unverified'])} |",
            f"| Key never assessed this objective | {len(r['no_key'])} |", f"| No answer from the AI | {len(r['missing'])} |",
            "", "## AI more lenient than the key (review first)", "", "| Objective | AI | Key |", "| --- | --- | --- |",
            _list(r["lenient"]), "", "## AI stricter than the key", "", "| Objective | AI | Key |", "| --- | --- | --- |",
            _list(r["stricter"]), "", "## N/A differs", "", "| Objective | AI | Key |", "| --- | --- | --- |",
            _list(r["na_differs"]), "", "## Problems reading the AI's file", ""]
    out += [f"- {p}" for p in problems] or ["- none"]
    out += ["", "## Notes on the answer key", ""] + ([f"- {n}" for n in notes] or ["- none"])
    out += ["", "## No answer from the AI", "", ", ".join(r["missing"]) or "none", ""]
    return "\n".join(out)


def main(argv):
    ai_path = Path(argv[1]) if len(argv) > 1 else HERE / "assessment.md"
    model = argv[2] if len(argv) > 2 else "model not named"
    kit = kit_ids((HERE / "objectives.md").read_text())
    key, notes = parse_key(KEY_PATH.read_text(), kit)
    rows, problems = parse_ai(ai_path.read_text(), kit)
    print(report(compare(kit, key, rows), problems, notes, model))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
