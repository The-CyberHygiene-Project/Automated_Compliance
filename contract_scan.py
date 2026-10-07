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
# A Procurement Instrument Identifier (PIID, FAR 4.16; formerly a PIIN under DFARS 204.70) is: funding office (6 characters) -
# fiscal year (2 digits) - type letter - sequence number (4 characters), e.g. FA8650-12-D-1234. Forms often print it without
# the hyphens. The type letter (the D above) says what the document is: FAR 4.1603(a)(3) prescribes the letters, and DoD
# uses M, S and T for its own purposes (DFARS 204.1603, as reported; check against the regulation). Letters not listed
# here are reserved or unknown to this table, and the scan says "unknown" rather than guess.
TYPE_LETTERS = {"A": "agreement", "B": "solicitation", "C": "award", "D": "award", "F": "order", "G": "agreement", "H": "order",
                "J": "order", "P": "purchase_order", "Q": "solicitation", "R": "solicitation",
                "M": "order", "S": "solicitation", "T": "solicitation"}
MARKERS = {
    "CUI": re.compile(r"Controlled Unclassified Information|\bCUI\b", re.I),
    "FCI": re.compile(r"Federal Contract Information|\bFCI\b"),
    "ITAR": re.compile(r"\bITAR\b|International Traffic in Arms", re.I),
    "EAR": re.compile(r"\bEAR\b|Export Administration Regulations"),
    "NDA": re.compile(r"non-?disclosure|\bNDA\b", re.I),
}
# Limited dissemination controls that can follow a CUI marking (CUI//SP-CTI//NOFORN). Reviewable; add as the rules change.
DISSEMINATION = ("NOFORN", "FEDCON", "NOCON", "FED ONLY", "DL ONLY", "REL TO", "DISPLAY ONLY")
# Extra obligations that come with export-controlled information (ITAR, EAR). Export-controlled information is a kind of CUI and
# these items sit on top of NIST SP 800-171; the assessment lists them apart from the 800-171 objectives. Every item is a QUESTION for
# the owner, never a statement of the law. status "owner": named by the owner. status "to_vet": a candidate from a secondary summary
# that the owner has not yet confirmed as a requirement. "applies" lists the regimes: ITAR, EAR, or EXPT (an export-control marking
# whose regime is not stated). Reviewable data: add, correct or remove items as the owner vets them.
_ALL = ("ITAR", "EAR", "EXPT")
ADDITIONAL_REQUIREMENTS = [
    {"id": "dd_form_2345", "status": "owner", "applies": _ALL,
     "text": ("DD Form 2345, the Militarily Critical Technical Data Agreement: the application for Joint Certification Program (US and Canada) "
              "certification, which lets a facility with a CAGE code receive export-controlled unclassified technical data (as reported: valid "
              "for five years, and it names a data custodian)"),
     "ask": "Do you hold a current DD Form 2345 (Joint Certification Program) certification, and when does it expire?"},
    # From the owner's own JCP approval letter and the approved DD Form 2345 (primary documents), so status "owner".
    {"id": "dd_form_2345_updated_on_change", "status": "owner", "applies": _ALL,
     "text": "A revised DD Form 2345 is submitted whenever information on it becomes outdated, for example the company name, a new data custodian or a change of address",
     "ask": "Is the form revised when any of those change?"},
    {"id": "recipients_are_certified", "status": "owner", "applies": _ALL,
     "text": "A certified entity must not provide militarily critical technical data to a non-certified entity (violation may lead to revocation of the certification)",
     "ask": "Do you check that anyone you pass the data to is certified?"},
    {"id": "custodian_is_citizen_or_resident", "status": "owner", "applies": _ALL,
     "text": "The data custodian named on the form is a citizen, or a person lawfully admitted for permanent residence, of the United States or Canada",
     "ask": "Is your named data custodian a citizen or permanent resident?"},
    {"id": "us_persons_only", "status": "to_vet", "applies": _ALL,
     "text": "Access to the export-controlled information is limited to U.S. persons, including administrators and outside IT support",
     "ask": "Is access limited to U.S. persons?"},
    {"id": "storage_location", "status": "to_vet", "applies": _ALL,
     "text": "The information is stored in the United States, or is protected by end-to-end encryption with FIPS-validated cryptography whose keys no foreign person holds",
     "ask": "Is it stored in the U.S. or protected that way?"},
    {"id": "restricted_party_screening", "status": "to_vet", "applies": _ALL,
     "text": "People, visitors and vendors are screened against restricted-party lists (for example the BIS Entity List, OFAC sanctions and the DDTC debarred list)",
     "ask": "Do you screen against those lists?"},
    {"id": "visitor_nationality", "status": "to_vet", "applies": _ALL,
     "text": "A visitor's nationality is checked before they could see export-controlled information (a deemed export)",
     "ask": "Do you check a visitor's nationality first?"},
    {"id": "ddtc_registration", "status": "to_vet", "applies": ("ITAR",),
     "text": "Registration with the State Department's Directorate of Defense Trade Controls, if you manufacture, export or broker defense articles or technical data",
     "ask": "Are you registered, or is registration not required for what you do?"},
    {"id": "technology_control_plan", "status": "to_vet", "applies": _ALL,
     "text": "A Technology Control Plan documents how export-controlled information is isolated, who may access it and how people are trained",
     "ask": "Do you have a Technology Control Plan?"},
    {"id": "classification", "status": "to_vet", "applies": _ALL,
     "text": "You know the USML category (ITAR) or the ECCN (EAR) of the information you hold",
     "ask": "Do you know the category or classification?"},
]
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


_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
# Clause dates are printed as (OCT 2016), as OCT 2016 with no brackets, or as OCT/2016, sometimes followed by a page number.
_DATE = re.compile(r"\(?\s*\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?[ /\-]\s*(\d{4})\b\s*\)?", re.I)
_TITLE_REACH = 180      # a clause title is short: a date farther from the number than this belongs to a sentence, not the title
_DEVIATION = re.compile(r"\(\s*(?:CLASS\s+)?DEVIATION\s+([0-9A-Z][0-9A-Z\-]*)\s*\)", re.I)


def _after_each_clause(text):
    """(clause name, the text between it and the next clause number, limited to a title's length)."""
    ms = list(_CLAUSE.finditer(text))
    for i, m in enumerate(ms):
        end = min(ms[i + 1].start() if i + 1 < len(ms) else len(text), m.end() + 300)
        yield f"{CLAUSE_SOURCES[m.group(1)]} {m.group(1)}.{m.group(2)}-{m.group(3)}", text[m.end():end]


def find_clause_dates(text):
    """{clause: [dates, oldest first]}. A clause's date, e.g. (MAY 2024), sits beside its number in the contract's clause list.
    The date (and any class deviation) is what fixes which version of a clause, and so which rules, apply."""
    out = {}
    for name, window in _after_each_clause(text):
        m = _DATE.search(window)
        span = window[:m.start()] if m else ""
        # between the number and the date there is only a title: no sentence break (a period, then a capitalised word)
        # nor a comma followed by a lowercase word (", the report was issued on"): that is narrative
        if m and len(span) <= _TITLE_REACH and not re.search(r"\.\s+[A-Za-z]|,\s+[a-z]", span):
            d = f"{m.group(1).upper()} {m.group(2)}"
            if d not in out.setdefault(name, []):
                out[name].append(d)
    return {k: sorted(v, key=lambda s: (int(s[-4:]), _MONTHS.index(s[:3]))) for k, v in out.items()}


def find_clause_deviations(text):
    """{clause: [class deviation numbers]} for clauses printed with a deviation, e.g. (DEVIATION 2024-O0013)."""
    out = {}
    for name, window in _after_each_clause(text):
        m = _DEVIATION.search(window)
        if m and m.group(1).upper() not in out.setdefault(name, []):
            out[name].append(m.group(1).upper())
    return {k: v for k, v in out.items() if v}


def additional_requirements(markers, categories=()):
    """The extra items triggered by ITAR or EAR terms, or by an export-control (EXPT) marking when the regime is not stated."""
    regimes = {m for m in markers if m in ("ITAR", "EAR")}
    if not regimes and "EXPT" in categories:
        regimes = {"EXPT"}
    return [r for r in ADDITIONAL_REQUIREMENTS if regimes & set(r["applies"])]


def ambiguous_slash_date(text):
    """True for a date like 11/09/2026 that reads differently as month/day and as day/month. The owner confirms which was meant."""
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text.strip())
    if not m:
        return False
    a, b = int(m.group(1)), int(m.group(2))
    return a != b and a <= 12 and b <= 12


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
            "marking": find_cui_marking(text, name), "klm": has_klm(text),
            "clause_dates": find_clause_dates(text), "clause_deviations": find_clause_deviations(text)}


def _merge_dates(docs, relevant, key):
    out = {}
    for d in docs:
        for clause, vals in d[key].items():
            if clause in relevant:
                for v in vals:
                    if v not in out.setdefault(clause, []):
                        out[clause].append(v)
    if key == "clause_dates":
        out = {c: sorted(v, key=lambda s: (int(s[-4:]), _MONTHS.index(s[:3]))) for c, v in out.items()}
    return out


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
            "additional_requirements": additional_requirements(markers, cats), "information_basis": basis, "clause_dates": _merge_dates(docs, relevant, "clause_dates"),
            "clause_deviations": _merge_dates(docs, relevant, "clause_deviations"), "cui_marked": marked, "categories": cats, "dissemination": diss, "marking_how": how,
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
                      "export_controls": "unknown", "number_kind": "unknown", "fiscal_year": None, "office": "", "cui_marked": False, "information_basis": "", "additional_requirements": [], "clause_dates": {}, "clause_deviations": {},
                      "categories": [], "dissemination": [], "marking_how": [], "information_if_awarded": "", "joined_by_folder": [], "files": [name], "confidence": "low", "needs_a_person": True, "why": why})
    return props


_BASIS_WORDS = {"clauses": "from the clauses", "marking": "the document is marked",
                "award floor": "at least: an executed contract is not public (prices, delivery dates) - award floor, inferred and not stated"}


def _export_section(props):
    """One section for the whole organisation: the extra items triggered by any contract, each a yes / no / unknown question."""
    triggered = [p for p in props if not p["needs_a_person"] and p["additional_requirements"]]
    if not triggered:
        return []
    items = []
    for p in triggered:
        for r in p["additional_requirements"]:
            if r["id"] not in [i["id"] for i in items]:
                items.append(r)
    items.sort(key=lambda r: [x["id"] for x in ADDITIONAL_REQUIREMENTS].index(r["id"]))
    out = ["# ADDITIONAL OBLIGATIONS from export-controlled terms. These are not part of NIST SP 800-171; the assessment lists them apart.",
           "# Each is a question for you: yes | no | unknown. Nothing is assumed.",
           "[export_controls]", f"triggered_by = {', '.join(p['label'] for p in triggered)}"]
    for status, heading in (("owner", None), ("to_vet", "# TO VET: candidates, not yet confirmed as requirements. They are questions, not statements of the law.")):
        group = [r for r in items if r["status"] == status]
        if group and heading:
            out.append(heading)
        for r in group:
            out.append(f"{r['id']} = unknown   ; yes | no | unknown. {r['ask']}")
            if r["id"] == "dd_form_2345":                      # the certification is tied to a facility, runs five years and names a custodian
                out += ["dd_form_2345_expires =   ; the date the certification expires (the approved form states it; valid for five years)",
                        "data_custodian =   ; the person named on the form as responsible for the controlled data"]
    return out + [""]


def _clause_with_date(p, clause):
    dates = p["clause_dates"].get(clause)
    return f"{clause} ({', '.join(dates)})" if dates else clause


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
        if p["additional_requirements"]:
            out.append(f"# EXPORT-CONTROLLED terms or marking found ({p['export_controls']}). Export-controlled information is a kind of CUI, and it "
                       "brings extra obligations on top of 800-171: see [export_controls] below.")
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
                f"dissemination_controls = {', '.join(p['dissemination'])}", f"clauses = {', '.join(_clause_with_date(p, c) for c in p['clauses'])}",
                *([f"clause_deviations = {'; '.join(f'{c}: {', '.join(v)}' for c, v in p['clause_deviations'].items())}"] if p["clause_deviations"] else []),
                f"required_revision = {rev}", f"revision_basis = {'contract_text' if rev != 'unspecified' else 'assumed'}",
                f"export_controls = {p['export_controls']}",
                f"prime_known = {p['prime_known']}", "last_verified =", ""]
    out += _export_section(props)
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
