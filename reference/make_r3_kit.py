#!/usr/bin/env python3
"""Build the Rev 3 AI-test kit from NIST's OSCAL catalog, mechanically (no wording of ours).
Writes kit-r3/objectives.md and kit-r3/methods.md. Parameters inside prose become [<parameter id>: <label>], so each objective names the parameter it depends on."""
import json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
cat = json.load(open(HERE / "NIST_SP800-171_rev3_catalog.json"))["catalog"]
labels = {}
def collect(c):
    for p in c.get("params", []):
        labels[p["id"]] = p.get("label", "value")
    for s in c.get("controls", []): collect(s)
for g in cat["groups"]:
    for c in g.get("controls", []): collect(c)
def prose(t):
    t = re.sub(r"\{\{\s*insert:\s*param,\s*([^}\s]+)\s*\}\}", lambda m: f"[{m.group(1)}: {labels.get(m.group(1), 'value')}]", t or "")
    return " ".join(t.split())
def odp_text(q):
    """The parameter's determination statement. Value parameters carry one; selection parameters carry a list of
    choices instead, which becomes 'one or more of the following is selected: ...' (how-many from the catalog)."""
    if q.get("guidelines"):
        return prose(q["guidelines"][0]["prose"])
    sel = q.get("select", {})
    how = {"one-or-more": "one or more of", "one": "one of"}.get(sel.get("how-many", ""), "")
    return f"the following parameter values are selected ({how} the choices): " + "; ".join(prose(c) for c in sel.get("choice", []))


def items(parts, depth=0):
    out = []
    for p in parts or []:
        lab = next((x["value"] for x in p.get("props", []) if x["name"] == "label"), "")
        if p.get("prose"): out.append("  " * depth + f"{lab.replace('SR-', '')} {prose(p['prose'])}".strip())
        out += items(p.get("parts"), depth + 1)
    return out
def objectives(parts):
    out = []
    for p in parts or []:
        if p["name"] != "assessment-objective": continue
        kids = [q for q in p.get("parts") or [] if q["name"] == "assessment-objective"]
        if kids: out += objectives(kids)
        else: out.append((p["id"].replace("assessment-objective_DS-", "").replace("assessment-objective_", ""), prose(p.get("prose"))))
    return out
obj_md = ["# NIST SP 800-171A Rev 3 assessment objectives", "",
          f"Source: NIST OSCAL catalog \"{cat['metadata']['title']}\", version {cat['metadata'].get('version')}, "
          f"modified {cat['metadata'].get('last-modified')}. Generated mechanically; withdrawn requirements left out. Includes the 88 organization-defined-parameter objectives (A.xx.xx.xx.ODP.nn).", ""]
meth_md = ["# NIST SP 800-171A Rev 3 potential assessment methods and objects", ""]
n_req = n_obj = 0
for g in cat["groups"]:
    fam = [c for c in g.get("controls", []) if not any(p["name"] == "status" and p["value"] == "withdrawn" for p in c.get("props", []))]
    if not fam: continue
    obj_md += [f"## {g['title']}", ""]
    for c in fam:
        rid = c["id"].replace("SP_800_171_", "")
        st = next((p for p in c.get("parts", []) if p["name"] == "statement"), {})
        obj_md += [f"### {rid} {c['title']}", ""] + [f"> {line}" for line in items(st.get("parts")) or [prose(st.get("prose"))]] + [""]
        odps = [(q["id"], odp_text(q)) for q in c.get("params", [])]
        objs = odps + objectives(c.get("parts"))      # the parameter objectives ("... is defined") come first
        obj_md += [f"- {i} {t}" for i, t in objs] + [""]
        n_req += 1; n_obj += len(objs)
        meth_md += [f"## {rid} {c['title']}", ""]
        for m in [p for p in c.get("parts", []) if p["name"] == "assessment-method"]:
            meth = next((x["value"] for x in m.get("props", []) if x["name"] == "method"), "")
            objs_txt = "; ".join(" ".join(s.split()) for q in m.get("parts", []) for s in (q.get("prose") or "").split("\n\n") if s.strip())
            meth_md += [f"- **{meth.title()}:** {objs_txt}"]
        meth_md += [""]
obj_md[0] += f" ({n_obj})"
(HERE.parent / "kit-r3" / "objectives.md").write_text("\n".join(obj_md) + "\n")
(HERE.parent / "kit-r3" / "methods.md").write_text("\n".join(meth_md) + "\n")
print(n_req, "requirements,", n_obj, "objectives")
