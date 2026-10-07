#!/usr/bin/env python3
"""Scan a folder of contract documents and PROPOSE contract entries for the organization profile.

    python3 contract_scan.py <folder> [--out proposals.ini]

Everything runs on this machine with plain pattern matching (standard library only). Nothing is sent anywhere, no AI is
involved, and only extracted facts (numbers, clause references, markers, file names) are written out, never document text.
Every result is a PROPOSAL for the owner to confirm; anything it cannot read is listed for a person.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

# ----------------------------------------------------------------------------- reviewable data (not code)
# Clauses that bear on what must be protected. The owner reviews this table; add or remove entries as the rules change.
# 'information' is the level the clause points to: FCI (federal contract information) or CUI.
RELEVANT = {
    "FAR 52.204-21": {"information": "FCI"},
    "DFARS 252.204-7008": {"information": "CUI"},
    "DFARS 252.204-7012": {"information": "CUI"},
    "DFARS 252.204-7019": {"information": "CUI"},
    "DFARS 252.204-7020": {"information": "CUI"},
    "DFARS 252.204-7021": {"information": "CUI"},
    # an agency's own security clause is a duty, but it does not itself say CUI or FCI
    "NFS 1852.204-76": {"information": None},
}
# What the number in front of a clause means: FAR 52.x, DFARS 252.x and the agency supplements.
CLAUSE_SOURCES = {"52": "FAR", "252": "DFARS", "1852": "NFS", "552": "GSAR", "3052": "HSAR", "5352": "AFFARS", "5152": "AFARS", "5252": "NMCARS"}
# Agency group from the start of a contract number. Only well-known prefixes; anything else stays "unknown".
AGENCY_PREFIXES = [("FA", "DoW"), ("SP", "DoW"), ("HQ", "DoW"), ("HC", "DoW"), ("W", "DoW"), ("N", "DoW"), ("47", "GSA"), ("GS-", "GSA"),
                   ("70", "other_civilian"), ("75", "other_civilian"), ("80", "other_civilian"), ("89", "other_civilian"),
                   ("36", "other_civilian"), ("69", "other_civilian")]
# A Procurement Instrument Identification Number (PIIN, DFARS 204.70) is: funding office (6 characters) - fiscal year (2 digits)
# - type letter - sequence number (4 characters), e.g. FA8650-12-D-1234. Forms often print it without the hyphens.
# The type letter (the D above) says what the document is.
TYPE_LETTERS = {"A": "agreement", "B": "solicitation", "C": "award", "D": "award", "F": "order", "G": "agreement", "H": "order",
                "J": "order", "P": "purchase_order", "Q": "solicitation", "R": "solicitation"}
MARKERS = {
    "CUI": re.compile(r"Controlled Unclassified Information|\bCUI\b", re.I),
    "FCI": re.compile(r"Federal Contract Information|\bFCI\b"),
    "ITAR": re.compile(r"\bITAR\b|International Traffic in Arms", re.I),
    "EAR": re.compile(r"\bEAR\b|Export Administration Regulations"),
    "NDA": re.compile(r"non-?disclosure|\bNDA\b", re.I),
}
# Limited dissemination controls that can follow a CUI marking (CUI//SP-CTI//NOFORN). Reviewable; add as the rules change.
DISSEMINATION = ("NOFORN", "FEDCON", "NOCON", "FED ONLY", "DL ONLY", "REL TO", "DISPLAY ONLY")
READABLE = {".docx", ".md", ".txt", ".csv", ".pdf"}

_PIIN = re.compile(r"\b([A-Z0-9]{6})-?(\d{2})-?([A-Z])-?([A-Z0-9]{4})(?:-?([A-Z0-9]{4}))?\b")
_GS = re.compile(r"\bGS-\d{2}[A-Z]-[A-Z0-9]{4,6}\b")
_CLAUSE = re.compile(r"\b(?:(?:FAR|DFARS|NFS|GSAR|HSAR|AFFARS|AFARS|NMCARS)\s*)?(1852|5352|5152|5252|3052|552|252|52)\.(\d{3})-(\d{1,4})\b")
_REV = re.compile(r"\bRev(?:ision)?\.?\s*([23])\b", re.I)


# ----------------------------------------------------------------------------- finding things in text
def find_contract_numbers(text):
    """PIINs normalised as XXXXXX-YY-T-NNNN, with or without hyphens as written. An order under a contract is reported as its base."""
    found = []
    for m in _PIIN.finditer(text):
        n = f"{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"
        if n not in found:
            found.append(n)
    for m in _GS.finditer(text):
        if m.group(0) not in found:
            found.append(m.group(0))
    return found


def base_number(number):
    """Strip an order suffix: FA8650-12-D-1234-0005 -> FA8650-12-D-1234."""
    m = re.fullmatch(r"([A-Z0-9]{6}-\d{2}-[A-Z]-[A-Z0-9]{4})-[A-Z0-9]{4}", number)
    return m.group(1) if m else number


def find_clauses(text):
    out = []
    for m in _CLAUSE.finditer(text):
        name = f"{CLAUSE_SOURCES[m.group(1)]} {m.group(1)}.{m.group(2)}-{m.group(3)}"
        if name not in out:
            out.append(name)
    return out


def find_markers(text):
    return {k for k, rx in MARKERS.items() if rx.search(text)}


def find_revision_hints(text):
    """Revision numbers mentioned in a document that talks about 800-171 (a hint, not a statement of the requirement)."""
    return set(_REV.findall(text)) if "800-171" in text else set()


def find_cui_marking(text, filename=""):
    """Is the DOCUMENT marked as CUI? That is different from a clause that merely mentions CUI. Looks for a banner line
    (CUI or CUI//SP-CTI//NOFORN), a portion marking (CUI), a designation indicator (Controlled by / CUI Category), and a
    file name that starts with CUI. Categories and limited dissemination controls are read from the marking."""
    how, cats, diss = [], set(), set()
    banners = re.findall(r"(?m)^[ \t]*(CUI(?://[A-Z0-9\- /,]+)?)[ \t]*$", text)
    # "Controlled Unclassified Information (CUI)" defines the abbreviation; it is not a marking. Real markings repeat
    # (a banner top and bottom, a mark on each paragraph), so a single stray one is ignored.
    portions = re.findall(r"(?<![Ii]nformation )(?<![Ii]nformation)\((CUI(?://[A-Z0-9\- /,]+)?)\)", text)
    if len(banners) >= 2:
        how.append("banner")
    else:
        banners = []
    if len(portions) >= 2:
        how.append("portion marking")
    else:
        portions = []
    if "Controlled by:" in text and "CUI Category:" in text:
        how.append("designation indicator")
    if re.match(r"(?i)\s*CUI[ _\-]", Path(filename).name):
        how.append("file name")
    for marking in banners + portions + re.findall(r"CUI//[A-Z0-9\- /,]+", text):
        for seg in marking.split("//")[1:]:
            seg = seg.strip()
            if seg.startswith("SP-"):
                cats.update(c.strip(" ,") for c in re.split(r"[/,]", seg[3:]) if c.strip(" ,"))
            else:
                diss.update(d for d in DISSEMINATION if seg.upper().startswith(d))
    for m in re.finditer(r"CUI Category:[ \t]*([A-Z][A-Z, /\-]*)", text):
        cats.update(c for c in re.split(r"[,/ ]+", m.group(1)) if 2 <= len(c) <= 8 and c.isupper())
    for m in re.finditer(r"Dissemination Control[s]?:[ \t]*([A-Z][A-Z, /\-]*)", text):
        diss.update(d for d in DISSEMINATION if d in m.group(1).upper())
    return {"marked": bool(how), "categories": sorted(cats), "dissemination": sorted(diss), "how": how}


def has_klm(text):
    """Sections K, L and M of the uniform contract format are removed at award; their presence marks a solicitation."""
    return len(set(re.findall(r"\bSECTION\s+([KLM])\b", text))) >= 2


def information_type(markers, clauses):
    """The highest level the evidence points to: CUI, else FCI, else unknown."""
    if "CUI" in markers or any(RELEVANT.get(c, {}).get("information") == "CUI" for c in clauses):
        return "CUI"
    if "FCI" in markers or any(RELEVANT.get(c, {}).get("information") == "FCI" for c in clauses):
        return "FCI"
    return "unknown"


def number_kind(number):
    """award | order | agreement | solicitation | purchase_order | unknown, from the type letter in the number."""
    if number.startswith("GS-"):
        return "award"
    parts = number.split("-")
    return TYPE_LETTERS.get(parts[2], "unknown") if len(parts) == 4 else "unknown"


def decode_piin(number):
    """The parts of a PIIN written as XXXXXX-YY-T-NNNN, or None for a number with another structure (a schedule number)."""
    m = re.fullmatch(r"([A-Z0-9]{6})-(\d{2})-([A-Z])-([A-Z0-9]{4})", number)
    if not m:
        return None
    yy = int(m.group(2))
    return {"office": m.group(1), "fiscal_year": (2000 if yy < 50 else 1900) + yy, "type_letter": m.group(3),
            "kind": TYPE_LETTERS.get(m.group(3), "unknown"), "sequence": m.group(4)}


def agency_guess(number):
    for prefix, group in AGENCY_PREFIXES:
        if number.startswith(prefix):
            return group
    return "unknown"


def instrument_guess(text):
    """What kind of document this is, from its heading. Government award forms come first: they print 'Purchase Order'
    as a number label, but they are the Government's own contract."""
    head = text[:1500].lower()
    if "modification of contract" in head or "standard form 30" in head:
        return "modification"
    if any(w in head for w in ("standard form 1449", "solicitation/contract/order", "award/contract", "standard form 26",
                               "order for supplies or services")):
        return "prime"
    for kind, words in (("nda", ("non-disclosure", "nondisclosure")), ("purchase_order", ("purchase order",)),
                        ("subcontract", ("subcontract",)), ("consulting", ("consulting agreement", "consulting services")),
                        ("order", ("delivery order", "task order")), ("prime", ("prime contract", "contract no", "contract number"))):
        if any(w in head for w in words):
            return kind
    return "other"


# ----------------------------------------------------------------------------- reading files
def read_text(path):
    """(text, None) or (None, why it needs a person). Word, Markdown and text first; PDF only if a reader is installed."""
    path = Path(path)
    ext = path.suffix.lower()
    try:
        if ext in (".md", ".txt", ".csv"):
            return path.read_text(errors="ignore"), None
        if ext == ".docx":
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode(errors="ignore")
            xml = re.sub(r"</w:p>", "\n", xml)                          # a paragraph ends the line
            text = re.sub(r"<[^>]+>", "", xml)                            # drop the markup, keep the words
            return text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&apos;", "'").replace("&quot;", '"'), None
        if ext == ".pdf":
            try:
                import logging
                logging.getLogger("pypdf").setLevel(logging.CRITICAL)           # damaged-but-readable files are common
                from pypdf import PdfReader
            except ImportError:
                return None, "a PDF reader (pypdf) is not installed"
            text = "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
            return (text, None) if text.strip() else (None, "a PDF with no readable text (probably a scan)")
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        return None, f"could not be opened ({type(exc).__name__})"
    return None, "not a document type this scan reads"


# ----------------------------------------------------------------------------- the scan
def _analyse(text, name):
    nums = [base_number(n) for n in find_contract_numbers(text)]
    clauses = find_clauses(text)
    return {"file": name, "folder": str(Path(name).parent), "numbers": list(dict.fromkeys(nums)), "clauses": clauses,
            "markers": find_markers(text), "revisions": find_revision_hints(text), "instrument": instrument_guess(text),
            "marking": find_cui_marking(text, name), "klm": has_klm(text)}


def _proposal(docs, reference):
    clauses = list(dict.fromkeys(c for d in docs for c in d["clauses"]))
    markers = set().union(*(d["markers"] for d in docs))
    kinds = [d["instrument"] for d in docs]
    instrument = next((k for k in ("prime", "subcontract", "purchase_order", "consulting", "nda", "order", "modification", "other") if k in kinds), "other")
    if instrument in ("order", "modification"):
        instrument = "prime"                       # an order or modification belongs to the contract it was issued under
    kind = number_kind(reference) if reference else "unknown"
    if kind == "solicitation" and instrument in ("prime", "other"):
        instrument = "solicitation"                # a request for proposals or quotations is not an award
    elif instrument == "other" and kind in ("award", "order", "agreement"):
        instrument = "prime"
    if instrument in ("prime", "other") and any(d["klm"] for d in docs):
        instrument = "solicitation"                # sections K, L and M are removed at award: this is still a solicitation
    relevant = [c for c in clauses if c in RELEVANT]
    marked = any(d["marking"]["marked"] for d in docs)
    cats = sorted(set().union(*(d["marking"]["categories"] for d in docs)))
    diss = sorted(set().union(*(d["marking"]["dissemination"] for d in docs)))
    how = sorted(set().union(*(set(d["marking"]["how"]) for d in docs)))
    info = information_type(markers | ({"CUI"} if marked else set()), clauses)
    basis = ("marking" if marked else "clauses") if info != "unknown" else ""
    # An executed contract is not public (Section B prices, delivery dates), so an award carries at least FCI even when no
    # clause says so. A solicitation is normally posted publicly, so the floor applies to the award it previews, not to it.
    if instrument == "prime" and info == "unknown":
        info, basis = "FCI", "award floor"
    # A solicitation previews its award: the duty shown is "if awarded". The solicitation itself holds CUI only if it is marked.
    information_if_awarded = (info if info != "unknown" else "FCI") if instrument == "solicitation" else ""
    if instrument == "solicitation":
        info, basis = ("CUI", "marking") if marked else ("unknown", "")
    duty = "clauses" if relevant else ("nda" if instrument == "nda" or ("NDA" in markers and info == "unknown") else
                                       ("markers" if info != "unknown" else ""))
    prime_known = ""
    if instrument in ("subcontract", "purchase_order", "consulting"):
        prime_known = "yes" if any(d["numbers"] for d in docs) else "no"
    confidence = "high" if reference and relevant and basis in ("clauses", "marking") else ("medium" if (reference or relevant or info != "unknown") else "low")
    return {"label": reference or Path(docs[0]["file"]).stem, "reference": reference, "instrument": instrument,
            "number_kind": kind, "fiscal_year": (decode_piin(reference) or {}).get("fiscal_year"),
            "office": (decode_piin(reference) or {}).get("office", ""), "agency_group": agency_guess(reference) if reference else "unknown", "information": info,
            "clauses": relevant, "other_clauses": len(clauses) - len(relevant), "markers": sorted(markers),
            "revision_hint": sorted(set().union(*(d["revisions"] for d in docs))), "prime_known": prime_known, "duty_from": duty,
            "export_controls": ", ".join(m for m in ("ITAR", "EAR") if m in markers) or "unknown",
            "information_basis": basis, "cui_marked": marked, "categories": cats, "dissemination": diss, "marking_how": how,
            "information_if_awarded": information_if_awarded, "joined_by_folder": [d["file"] for d in docs if d.get("joined")],
            "files": [d["file"] for d in docs], "confidence": confidence, "needs_a_person": False}


def scan_folder(folder):
    folder = Path(folder)
    groups, loose, unreadable = {}, [], []
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".")):
        name = str(path.relative_to(folder))
        if path.suffix.lower() not in READABLE:
            if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".heic", ".gif"):
                unreadable.append((name, "an image (a scan or photo)"))
            continue
        text, why = read_text(path)
        if text is None:
            unreadable.append((name, why))
            continue
        d = _analyse(text, name)
        if d["numbers"]:
            groups.setdefault(d["numbers"][0], []).append(d)              # grouped under the first contract number found
        else:
            loose.append([d])                                             # no number: an entry of its own
    still_loose = []
    for docs in loose:
        d = docs[0]
        near = [ref for ref, ds in groups.items() if any(x["folder"] == d["folder"] for x in ds)]
        if d["folder"] != "." and d["instrument"] == "other" and len(near) == 1:
            groups[near[0]].append(dict(d, joined=True))      # kept in the contract's own subfolder: an attachment, to confirm
        else:
            still_loose.append(docs)
    props = [_proposal(docs, ref) for ref, docs in groups.items()] + [_proposal(docs, "") for docs in still_loose]
    for name, why in unreadable:
        props.append({"label": Path(name).stem, "reference": "", "instrument": "other", "agency_group": "unknown", "information": "unknown",
                      "clauses": [], "other_clauses": 0, "markers": [], "revision_hint": [], "prime_known": "", "duty_from": "",
                      "export_controls": "unknown", "number_kind": "unknown", "fiscal_year": None, "office": "", "cui_marked": False, "information_basis": "",
                      "categories": [], "dissemination": [], "marking_how": [], "information_if_awarded": "", "joined_by_folder": [], "files": [name], "confidence": "low", "needs_a_person": True, "why": why})
    return props


_BASIS_WORDS = {"clauses": "from the clauses", "marking": "the document is marked",
                "award floor": "at least: an executed contract is not public (prices, delivery dates) - award floor, inferred and not stated"}


def organization_level(props):
    """The level for the whole organization: the highest among contracts HELD. Solicitations are bids, not contracts held."""
    order = {"unknown": 0, "FCI": 1, "CUI": 2}
    held = [p for p in props if not p["needs_a_person"] and p["instrument"] != "solicitation"]
    bids = [p for p in props if not p["needs_a_person"] and p["instrument"] == "solicitation"]
    level = max((p["information"] for p in held), key=order.get, default="unknown")
    awarded = max((p["information_if_awarded"] for p in bids), key=order.get, default="unknown")
    return {"level": level, "held": len(held), "bids": len(bids), "if_all_awarded": max([level, awarded], key=order.get)}


def proposals_to_ini(props):
    """Proposals as profile entries. Only extracted facts and file names, never document text."""
    out = ["# PROPOSED contract entries from a folder scan.",
           "# Nothing here is confirmed. Check every line against the document, then copy what is right into profile.ini.",
           "# Blank means the scan could not tell. Anything it missed can be typed in by hand.", ""]
    n, people = 0, []
    for p in props:
        if p["needs_a_person"]:
            people.append(f"{p['files'][0]} ({p.get('why', '')})")
            continue
        n += 1
        vehicle = {"prime": "prime", "subcontract": "subcontract", "purchase_order": "subcontract"}.get(p["instrument"], "")
        agency = "" if p["agency_group"] == "unknown" else p["agency_group"]
        rev = p["revision_hint"][0] if len(p["revision_hint"]) == 1 else "unspecified"
        if p["instrument"] == "solicitation":
            out.append("# SOLICITATION, not an award: it previews the contract. The clauses shown apply to an award ('information_if_awarded'),")
            out.append("# not necessarily to this document, which holds CUI only if it is marked (cui_marked).")
        if p["joined_by_folder"]:
            out.append(f"# JOINED BY FOLDER (confirm): {', '.join(p['joined_by_folder'][:5])}")
        out += [f"# PROPOSED from: {', '.join(p['files'][:5])}{' ...' if len(p['files']) > 5 else ''}   (confidence: {p['confidence']}; "
                f"found: {p['instrument']}, {p['duty_from'] or 'no duty found'}"
                f"{', FY' + str(p['fiscal_year']) if p['fiscal_year'] else ''}; other clauses mentioned: {p['other_clauses']})",
                f"[contract.{n}]", f"label = {p['label']}", f"reference = {p['reference']}", f"agency_group = {agency}",
                f"vehicle = {vehicle}",
                f"information = {p['information']}" + (f"   ; {_BASIS_WORDS[p['information_basis']]}" if p["information_basis"] else ""),
                *([f"information_if_awarded = {p['information_if_awarded']}"] if p["instrument"] == "solicitation" else []),
                f"cui_marked = {'yes' if p['cui_marked'] else 'no'}", f"cui_categories = {', '.join(p['categories'])}",
                f"dissemination_controls = {', '.join(p['dissemination'])}", f"clauses = {', '.join(p['clauses'])}",
                f"required_revision = {rev}", f"revision_basis = {'contract_text' if rev != 'unspecified' else 'assumed'}",
                f"export_controls = {p['export_controls']}", f"prime_known = {p['prime_known']}", "last_verified =", ""]
    if people:
        out += ["# NEEDS A PERSON (could not be read): " + "; ".join(people), ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None, help="default: PROPOSED-contracts.ini inside the folder scanned")
    a = ap.parse_args(argv)
    props = scan_folder(a.folder)
    out = Path(a.out) if a.out else Path(a.folder) / "PROPOSED-contracts.ini"
    out.write_text(proposals_to_ini(props))
    ok = [p for p in props if not p["needs_a_person"]]
    print(f"{len(ok)} proposed entries, {len(props) - len(ok)} files need a person. Wrote {out}")
    lv = organization_level(props)
    print(f"Highest level among contracts held ({lv['held']}): {lv['level']}. Solicitations ({lv['bids']}) are not counted; "
          f"if all were awarded: {lv['if_all_awarded']}.")
    for p in ok:
        print(f"  {p['label']:<24} {p['instrument']:<14} {p['information']:<8} {p['agency_group']:<8} confidence {p['confidence']}  ({len(p['files'])} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
