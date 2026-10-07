"""Organization profile: loads profile.ini, checks it in plain words, and builds the short context the AI may see.

The profile holds the owner's own statements of fact. Nothing here decides what applies to a company: it only reads what
the owner wrote, says what looks wrong, and works out derived facts (size band, revision per contract) openly.
Blank always means unknown, and unknown stays unknown. Runs on the Python 3.9 that ships with macOS.
"""
import configparser
import datetime
import json
import sys
from pathlib import Path


YES_NO = ("yes", "no")
CHOICES = {
    ("organization", "owner_is_it_admin"): YES_NO,
    ("organization", "independent_reviewer"): YES_NO,
    ("organization", "outside_it_provider"): YES_NO,
    ("organization", "other_personnel"): YES_NO,
    ("organization", "security_lead"): ("owner", "employee", "outside_provider"),
    ("business", "facility_type"): ("home_office", "shared_office", "commercial_space", "other"),
    ("contract", "agency_group"): ("DoW", "GSA", "other_civilian"),
    ("contract", "vehicle"): ("prime", "subcontract"),
    ("contract", "information"): ("FCI", "CUI", "both", "unknown"),
    ("contract", "required_revision"): ("2", "3", "unspecified"),
    ("contract", "revision_basis"): ("contract_text", "agency_notice", "assumed"),
    ("provider", "access"): ("remote", "on_site", "both"),
    ("system", "kind"): ("server", "workstation", "laptop", "mobile", "network_device", "cloud_service", "managed_service"),
    ("system", "in_boundary"): YES_NO,
    ("system", "administered_by"): ("owner", "employee", "outside_provider", "cloud_provider"),
    ("assessment", "not_applicable_needs_reason"): YES_NO,
}
AGENCY_DEFAULT_REVISION = {"DoW": 2, "GSA": 3, "other_civilian": 3}      # the owner's dated working assumptions
LEVEL_ORDER = {"unknown": 0, "FCI": 1, "CUI": 2}
STALE_DAYS = 90
WARN_DAYS = (90, 30)


class ProfileError(Exception):
    pass


class Profile:
    def __init__(self, parser):
        self.parser = parser

    def get(self, section, key, default=""):
        return self.parser.get(section, key, fallback=default).strip() if self.parser.has_section(section) else default

    def sections(self, kind):
        """The numbered or named sections of one kind, for example contract.1 and contract.2: (name, {key: value})."""
        return [(s.split(".", 1)[1], {k: v.strip() for k, v in self.parser.items(s)})
                for s in self.parser.sections() if s.startswith(kind + ".")]


def _parser():
    return configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",), strict=False)


def load_text(text):
    p = _parser()
    try:
        p.read_string(text)
    except configparser.Error as e:
        raise ProfileError(f"The profile could not be read: {str(e).splitlines()[0]}. "
                           "Each line should be 'key = value', under a [section] heading.")
    return Profile(p)


def load_path(path):
    path = Path(path)
    if not path.is_file():
        raise ProfileError(f"No profile found at {path}. Copy profile.example.ini to profile.ini and fill it in.")
    return load_text(path.read_text())


def _int(text):
    try:
        return int(text.strip())
    except ValueError:
        return None


def band(employees):
    """The size categories of the cited article. Twenty or more is outside this tool's scope (None)."""
    if employees < 5:
        return "nano"
    if employees < 10:
        return "micro"
    if employees < 20:
        return "mini"
    return None


def band_of(profile):
    n = _int(profile.get("organization", "employees"))
    return band(n) if n is not None and n >= 1 else None


def other_personnel(profile):
    """Anyone besides the owner with access? The owner's statement wins; otherwise one person means no; blank means unknown."""
    stated = profile.get("organization", "other_personnel").lower()
    if stated in YES_NO:
        return stated
    n = _int(profile.get("organization", "people"))
    if n is None or n < 1:
        return "unknown"
    return "no" if n == 1 else "yes"


def required_revisions(profile):
    out = []
    for name, c in profile.sections("contract"):
        stated = c.get("required_revision", "").lower()
        rev = int(stated) if stated in ("2", "3") else AGENCY_DEFAULT_REVISION.get(c.get("agency_group", ""), 3)
        assumed = stated not in ("2", "3") or c.get("revision_basis", "").lower() == "assumed"
        out.append({"contract": name, "label": c.get("label", name), "revision": rev, "assumed": assumed})
    return out


def kits_needed(profile):
    return sorted({r["revision"] for r in required_revisions(profile)})


def organization_level(profile):
    level = "unknown"
    for _, c in profile.sections("contract"):
        info = c.get("information", "unknown")
        info = "CUI" if info.lower() == "both" else ("FCI" if info.lower() == "fci" else ("CUI" if info.lower() == "cui" else "unknown"))
        if LEVEL_ORDER[info] > LEVEL_ORDER[level]:
            level = info
    return level


def scan_targets(profile):
    """Systems the assessor may log in to: the listed targets (or every system) that have an SSH alias."""
    systems = dict(profile.sections("system"))
    listed = [t.strip() for t in profile.get("assessment", "targets").split(",") if t.strip()] or list(systems)
    return [t for t in listed if systems.get(t, {}).get("ssh_alias", "").strip()]


def _date(text):
    try:
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        return None


def _list_text(choices):
    return ", ".join(choices[:-1]) + " or " + choices[-1]


def _finding(level, message):
    return {"level": level, "message": message}


def _check_choices(profile, out):
    for (kind, key), choices in CHOICES.items():
        blocks = [(kind, {key: profile.get(kind, key)})] if kind in ("organization", "business", "assessment") else \
            [(f"{kind}.{n}", c) for n, c in profile.sections(kind)]
        for where, values in blocks:
            v = values.get(key, "")
            if v and v.lower() not in [c.lower() for c in choices]:
                out.append(_finding("error", f"[{where}] {key} must be {_list_text(list(choices))}, not '{v}'."))


def _check_size(profile, out):
    emp = profile.get("organization", "employees")
    n = _int(emp) if emp else None
    if emp and (n is None or n < 1):
        out.append(_finding("error", f"[organization] employees must be a whole number of 1 or more, not '{emp}'."))
        return
    if n is not None and n >= 20:
        out.append(_finding("warning", "This tool is built for very small businesses (fewer than 20 employees). "
                                       "The results may not fit a company this size."))
    ppl = profile.get("organization", "people")
    m = _int(ppl) if ppl else None
    if ppl and (m is None or m < 1):
        out.append(_finding("error", f"[organization] people must be a whole number of 1 or more, not '{ppl}'."))
    elif n is not None and m is not None and m < n:
        out.append(_finding("warning", "[organization] people is smaller than employees, but 'people' counts everyone who uses the "
                                       "systems, employees included. Check both numbers."))


def _check_contracts(profile, today, out):
    for name, c in profile.sections("contract"):
        text = c.get("last_verified", "")
        where = f"[contract.{name}]"
        if not text:
            out.append(_finding("warning", f"{where} last_verified is blank: write the date (YYYY-MM-DD) you last checked which "
                                           "revision this contract requires."))
            continue
        d = _date(text)
        if d is None:
            out.append(_finding("error", f"{where} last_verified must be written YYYY-MM-DD (for example 2026-10-06), not '{text}'."))
        elif (today - d).days > STALE_DAYS:
            out.append(_finding("warning", f"{where} was last checked {(today - d).days} days ago, more than {STALE_DAYS} days: "
                                           "re-check which revision it requires."))


def _check_dd2345(profile, today, out):
    holds = profile.get("export_controls", "dd_form_2345").lower()
    text = profile.get("export_controls", "dd_form_2345_expires")
    if not text:
        if holds == "yes":
            out.append(_finding("warning", "[export_controls] dd_form_2345_expires is blank: write the expiry date from Block 7c "
                                           "of the approved form (YYYY-MM-DD) so the tool can warn before it lapses."))
        return
    d = _date(text)
    if d is None:
        out.append(_finding("error", f"[export_controls] dd_form_2345_expires must be written YYYY-MM-DD, not '{text}'. A date like "
                                     "11/09/2026 can be read month-first or day-first (two months apart); check the form and write it out in full."))
        return
    days = (d - today).days
    if days < 0:
        out.append(_finding("error", f"The DD Form 2345 certification expired {-days} days ago ({d.isoformat()})."))
    elif days <= WARN_DAYS[1]:
        out.append(_finding("warning", f"The DD Form 2345 certification expires in {days} days ({d.isoformat()}): renewal is due now."))
    elif days <= WARN_DAYS[0]:
        out.append(_finding("warning", f"The DD Form 2345 certification expires in {days} days ({d.isoformat()}): start the renewal."))


def _check_targets(profile, out):
    systems = dict(profile.sections("system"))
    for t in [t.strip() for t in profile.get("assessment", "targets").split(",") if t.strip()]:
        if t not in systems:
            out.append(_finding("error", f"[assessment] targets names '{t}', but there is no [system.{t}] section."))
        elif not systems[t].get("ssh_alias", "").strip():
            out.append(_finding("warning", f"[system.{t}] is a scan target but has no ssh_alias, so it is documented, not scanned."))


def check(profile, today=None):
    """Every problem found, as {'level': 'error' | 'warning', 'message': plain words}. Errors first."""
    today = today or datetime.date.today()
    out = []
    _check_choices(profile, out)
    _check_size(profile, out)
    _check_contracts(profile, today, out)
    _check_dd2345(profile, today, out)
    _check_targets(profile, out)
    return sorted(out, key=lambda f: f["level"] != "error")


def assessment_context(profile, today=None):
    """The only facts about the company the AI may see. No names, numbers, clauses, hosts or counts."""
    today = today or datetime.date.today()
    stale = any(f["level"] == "warning" for f in _contract_findings(profile, today))     # a late or missing check
    return {
        "size_band": band_of(profile),
        "other_personnel": other_personnel(profile),
        "owner_is_it_admin": profile.get("organization", "owner_is_it_admin") or "unknown",
        "security_lead": profile.get("organization", "security_lead") or "unknown",
        "independent_reviewer": profile.get("organization", "independent_reviewer") or "unknown",
        "outside_it_provider": profile.get("organization", "outside_it_provider") or "unknown",
        "organization_level": organization_level(profile),
        "kits": kits_needed(profile),
        "revisions": sorted({(r["revision"], r["assumed"]) for r in required_revisions(profile)}),
        "contract_checks_current": not stale,
        "systems": [{"kind": s.get("kind", "unknown"), "administered_by": s.get("administered_by", "unknown")}
                    for _, s in profile.sections("system") if s.get("in_boundary", "").lower() != "no"],
    }


def _contract_findings(profile, today):
    out = []
    _check_contracts(profile, today, out)
    return out


def main(argv=None, today=None):
    argv = sys.argv[1:] if argv is None else argv
    as_context = "--context" in argv
    argv = [a for a in argv if a != "--context"]
    path = argv[0] if argv else "profile.ini"
    out = sys.stderr if as_context else sys.stdout       # with --context, stdout carries only the JSON
    try:
        profile = load_path(path)
    except ProfileError as e:
        print(f"ERROR: {e}", file=out)
        return 1
    findings = check(profile, today)
    if as_context:
        for f in findings:
            print(("ERROR: " if f["level"] == "error" else "warning: ") + f["message"], file=out)
        if any(f["level"] == "error" for f in findings):
            return 1
        print(json.dumps(assessment_context(profile, today), indent=1))
        return 0
    for f in findings:
        print(("ERROR: " if f["level"] == "error" else "warning: ") + f["message"])
    errors = sum(f["level"] == "error" for f in findings)
    print(f"{path}: {errors} error(s), {len(findings) - errors} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
