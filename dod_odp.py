#!/usr/bin/env python3
"""Read the DoD organization-defined parameter (ODP) values for NIST SP 800-171 Rev 3.

The values come from the DoD memo "Department of Defense Organization-Defined Parameters for NIST SP 800-171
Revision 3" (Attachment A, public). Give this module the text of that PDF (extract it with any PDF tool); it returns
{part id: value}, for example {"03.01.01.g.01": "24 hours"}. The memo names a requirement part (03.01.01.g.01);
the kit names an objective (A.03.01.01.g.01), so `part_of` matches an objective to its part by prefix.
Standard library only. See odp_compare.py for the comparison against a measurement register.
"""
import re

ID = re.compile(r"^(0\d\.\d\d\.\d\d(?:\.[a-z](?:\.\d\d)?)?)\b\s*(.*)$")
FAMILIES = ("Access Control", "Awareness and Training", "Audit and Accountability", "Configuration Management",
            "Identification and Authentication", "Incident Response", "Maintenance", "Media Protection",
            "Personnel Security", "Physical Protection", "Risk Assessment", "Security Assessment and Monitoring",
            "System and Communications Protection", "System and Information Integrity", "Planning",
            "System and Services Acquisition", "Supply Chain Risk Management")
STOP = re.compile(r"^(Related Controls|ODP Values|ODP$|Identifier ODP|Attachment|" + "|".join(FAMILIES) + r"$|3\.\d+\.\d+ )")


def _clean(text):
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if line and not re.fullmatch(r"\d{1,3}", line):          # blank lines and bare page numbers
            lines.append(line)
    return lines


def _value(chunk):
    """Drop the '[Assignment: ...]' / '[Selection: ...]' label that opens an entry, keep the value after it."""
    s = " ".join(chunk)
    m = re.match(r"\[(?:Assignment|Selection)[^\]]*\]\s*", s)
    return (s[m.end():] if m else s).strip()


def parse_values(text):
    out, current, chunk = {}, None, []

    def flush():
        if current is not None and chunk:
            v = _value(chunk)
            if v:
                out[current] = v

    for line in _clean(text):
        m = ID.match(line)
        if m and (m.group(2).startswith("[") or not m.group(2)):
            flush()
            current, chunk = m.group(1), ([m.group(2)] if m.group(2) else [])
        elif STOP.match(line):
            flush()
            current, chunk = None, []
        elif current is not None:
            chunk.append(line)
    flush()
    return out


def part_of(objective_id, parts):
    """The DoD part an objective belongs to: the longest part id that is a prefix of the objective id."""
    oid = objective_id[2:] if objective_id.startswith("A.") else objective_id
    best = None
    for p in parts:
        if (oid == p or oid.startswith(p + ".")) and (best is None or len(p) > len(best)):
            best = p
    return best


def odp_parts(kit_text, parts):
    """{ODP id: [DoD part ids]} from the kit's objective lines. The objective that uses a parameter names it as
    [A.03.xx.xx.ODP.nn: kind]. The line that merely defines a parameter (its own id contains .ODP.) is skipped.
    Where the memo splits an objective into child parts (h -> h.01, h.02) and the objective holds the same number
    of parameters, they pair off in order; otherwise the parameter maps to every child part."""
    out = {}
    for line in kit_text.splitlines():
        m = re.match(r"- (A\.\S+) ", line)
        if not m or ".ODP." in m.group(1):
            continue
        oid = m.group(1)
        used = re.findall(r"\[(A\.\d\d\.\d\d\.\d\d\.ODP\.\d\d)", line)
        if not used:
            continue
        own = part_of(oid, parts)
        if own:
            for u in used:
                out.setdefault(u, [])
                if own not in out[u]:
                    out[u].append(own)
            continue
        bare = oid[2:]
        kids = sorted(p for p in parts if p.startswith(bare + "."))
        if not kids:
            continue
        for i, u in enumerate(used):
            chosen = [kids[i]] if len(kids) == len(used) else kids
            out.setdefault(u, [])
            out[u] += [c for c in chosen if c not in out[u]]
    return out
