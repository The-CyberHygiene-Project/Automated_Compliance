# REDACTED PUBLIC COPY (2026-11-10). Site identifiers are replaced with placeholders, so this is a
# reference copy, not drop-in. What it does, reads, writes and changes, and its limits, are in
# evidence/README.md. It was not run while this copy was prepared.
"""Compute per-requirement 'fully met' from DIWAI-ASMT-2026-08 (all table layouts). Met = every objective SATISFIED or NOT APPLICABLE."""
import re,sys,collections
def parse(path):
    t=open(path).read()
    heads=[(m.start(),m.group(1)) for m in re.finditer(r"^## (3\.\d+\.\d+(?: / 3\.\d+\.\d+)*(?: / \d+\.\d+\.\d+)*)",t,re.M)]
    res={}
    for i,(pos,h) in enumerate(heads):
        end=heads[i+1][0] if i+1<len(heads) else len(t)
        s=t[pos:end]; s=re.split(r"\n# 3\.|\n---\n\n# |\n## Interim findings",s)[0]
        reqs=re.findall(r"3\.\d+\.\d+",h)
        if h.startswith("3.2.1 / 3.2.2"): reqs=["3.2.1","3.2.2","3.2.3"]
        # allow 'x.y.z' shorthand after slash
        m=re.match(r"(3\.\d+)\.(\d+)((?: / \d+)+)?",h)
        rows=[]
        for l in s.split("\n"):
            if not l.startswith("|"): continue
            cells=[c.strip() for c in l.strip().strip("|").split("|")]
            st=re.sub(r"\*","",cells[-1]).strip()
            if st not in ("SATISFIED","PARTIALLY SATISFIED","OTHER THAN SATISFIED","UNVERIFIED","NOT APPLICABLE"): continue
            rid=None
            for c in cells[:2]:
                mm=re.match(r"^(3\.\d+\.\d+)$",c)
                if mm: rid=mm.group(1)
            rows.append((rid,st))
        if len(reqs)==1:
            res[reqs[0]]=[st for _,st in rows]
        else:
            for r in reqs:
                res[r]=[st for rid,st in rows if rid==r]
    return res
def fam_counts(res):
    fam=collections.OrderedDict()
    for r,sts in res.items():
        f=int(r.split(".")[1]); d=fam.setdefault(f,[0,0])
        d[0]+=1
        if sts and all(s in("SATISFIED","NOT APPLICABLE") for s in sts): d[1]+=1
    return fam
if __name__=="__main__":
    res=parse(sys.argv[1]); fam=fam_counts(res)
    tot=sum(v[0] for v in fam.values()); met=sum(v[1] for v in fam.values())
    print("requirements:",tot,"fully met:",met)
    print({f:tuple(v) for f,v in sorted(fam.items())})
    empty=[r for r,s in res.items() if not s]; print("requirements with no parsed rows:",empty)
