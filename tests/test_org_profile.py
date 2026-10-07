"""Organization profile loader and checker. Every profile here is invented."""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import org_profile as op  # noqa: E402

TODAY = datetime.date(2026, 10, 7)

BASE = """
[organization]
employees = 3
people = 3
owner_is_it_admin = yes
security_lead = owner
independent_reviewer = no
outside_it_provider = no

[roles]
system_owner = owner

[contract.1]
label = Secret Name Prime Contract
agency_group = DoW
vehicle = prime
information = CUI
clauses = DFARS 252.204-7012
required_revision = 2
revision_basis = contract_text
last_verified = 2026-09-20

[system.server1]
kind = server
in_boundary = yes
administered_by = owner
ssh_alias = secret-host
"""


def load(extra="", base=BASE):
    return op.load_text(base + extra)


def msgs(findings, level=None):
    return [f["message"] for f in findings if level is None or f["level"] == level]


def test_the_band_comes_from_the_employee_count_using_the_articles_categories():
    assert [op.band(n) for n in (1, 4, 5, 9, 10, 19)] == ["nano", "nano", "micro", "micro", "mini", "mini"]
    assert op.band(20) is None and op.band(200) is None


def test_a_clean_profile_has_no_errors_and_no_warnings():
    assert op.check(load(), TODAY) == []


def test_twenty_or_more_employees_is_a_warning_that_the_tool_is_not_built_for_that_size():
    p = load(base=BASE.replace("employees = 3", "employees = 25"))
    w = msgs(op.check(p, TODAY), "warning")
    assert any("20" in m and "very small" in m.lower() for m in w)


def test_a_bad_employee_count_is_an_error_in_plain_words():
    p = load(base=BASE.replace("employees = 3", "employees = three"))
    e = msgs(op.check(p, TODAY), "error")
    assert any("employees" in m and "whole number" in m for m in e)


def test_a_value_outside_its_allowed_list_names_the_key_and_the_choices():
    p = load(base=BASE.replace("required_revision = 2", "required_revision = 4"))
    e = msgs(op.check(p, TODAY), "error")
    assert any("required_revision" in m and "2, 3 or unspecified" in m for m in e)


def test_a_contract_check_older_than_ninety_days_warns_and_a_missing_date_warns():
    old = load(base=BASE.replace("2026-09-20", "2026-05-01"))
    assert any("90 days" in m for m in msgs(op.check(old, TODAY), "warning"))
    blank = load(base=BASE.replace("last_verified = 2026-09-20", "last_verified ="))
    assert any("last_verified" in m for m in msgs(op.check(blank, TODAY), "warning"))


def test_an_unreadable_verification_date_is_an_error():
    p = load(base=BASE.replace("2026-09-20", "20/09/2026"))
    assert any("last_verified" in m and "YYYY-MM-DD" in m for m in msgs(op.check(p, TODAY), "error"))


def test_revision_comes_from_the_contract_else_from_the_agency_group_and_is_marked_assumed():
    p = load("""
[contract.2]
label = GSA order
agency_group = GSA
required_revision = unspecified
last_verified = 2026-09-20
[contract.3]
label = Other agency
agency_group = other_civilian
required_revision = unspecified
revision_basis = assumed
last_verified = 2026-09-20
""")
    rv = {r["label"]: r for r in op.required_revisions(p)}
    assert rv["Secret Name Prime Contract"]["revision"] == 2 and rv["Secret Name Prime Contract"]["assumed"] is False
    assert rv["GSA order"]["revision"] == 3 and rv["GSA order"]["assumed"] is True
    assert rv["Other agency"]["revision"] == 3 and rv["Other agency"]["assumed"] is True
    assert op.kits_needed(p) == [2, 3]


def test_the_organisation_level_is_the_highest_among_the_contracts_listed():
    assert op.organization_level(load()) == "CUI"
    fci = load(base=BASE.replace("information = CUI", "information = FCI"))
    assert op.organization_level(fci) == "FCI"
    assert op.organization_level(op.load_text("[organization]\nemployees = 1\n")) == "unknown"


def test_other_personnel_is_derived_from_people_unless_the_owner_states_it():
    one = load(base=BASE.replace("people = 3", "people = 1"))
    assert op.other_personnel(one) == "no"
    assert op.other_personnel(load()) == "yes"
    stated = load(base=BASE.replace("people = 3", "people = 1").replace("employees = 3", "employees = 3\nother_personnel = yes"))
    assert op.other_personnel(stated) == "yes"                       # the owner's statement wins
    assert op.other_personnel(op.load_text("[organization]\nemployees = 1\n")) == "unknown"


def test_people_fewer_than_employees_is_flagged_as_inconsistent():
    p = load(base=BASE.replace("people = 3", "people = 1"))
    assert any("people" in m and "employees" in m for m in msgs(op.check(p, TODAY), "warning"))


def test_the_dd_form_2345_expiry_warns_at_ninety_and_thirty_days_and_errors_when_past():
    def at(date):
        return load(f"[export_controls]\ndd_form_2345 = yes\ndd_form_2345_expires = {date}\n")
    assert not any("DD Form 2345" in m for m in msgs(op.check(at("2027-06-01"), TODAY)))          # far away
    assert any("expires in" in m for m in msgs(op.check(at("2026-12-20"), TODAY), "warning"))      # 74 days
    soon = op.check(at("2026-11-09"), TODAY)                                                         # 33 days
    assert any("33 days" in m for m in msgs(soon, "warning"))
    assert any("expired" in m for m in msgs(op.check(at("2026-10-01"), TODAY), "error"))


def test_a_certificate_marked_yes_with_no_expiry_date_warns_and_a_slash_date_is_refused_as_ambiguous():
    blank = load("[export_controls]\ndd_form_2345 = yes\ndd_form_2345_expires =\n")
    assert any("dd_form_2345_expires" in m for m in msgs(op.check(blank, TODAY), "warning"))
    slash = load("[export_controls]\ndd_form_2345 = yes\ndd_form_2345_expires = 11/09/2026\n")
    e = msgs(op.check(slash, TODAY), "error")
    assert any("11/09/2026" in m and "YYYY-MM-DD" in m and "month" in m for m in e)


def test_not_applicable_style_unknowns_stay_unknown_and_blank_never_becomes_a_guess():
    p = op.load_text("[organization]\nemployees =\npeople =\n")
    assert op.band_of(p) is None and op.other_personnel(p) == "unknown"
    assert not any(f["level"] == "error" for f in op.check(p, TODAY))


def test_the_assessment_context_for_the_ai_carries_no_names_numbers_or_hosts():
    ctx = op.assessment_context(load(), TODAY)
    blob = repr(ctx)
    for secret in ("Secret Name", "secret-host", "252.204-7012", "employees", "people", "3"):
        if secret != "3":
            assert secret not in blob
    assert ctx["size_band"] == "nano" and ctx["other_personnel"] == "yes" and ctx["kits"] == [2]
    assert ctx["owner_is_it_admin"] == "yes" and ctx["systems"] == [{"kind": "server", "administered_by": "owner"}]
    assert ctx["organization_level"] == "CUI"


def test_a_system_with_no_ssh_alias_is_documented_but_not_a_scan_target():
    p = load("[system.laptop]\nkind = laptop\nin_boundary = yes\nadministered_by = owner\n")
    assert op.scan_targets(p) == ["server1"]


def test_a_target_naming_an_unknown_system_is_an_error():
    p = load("[assessment]\ntargets = server1, nowhere\n")
    assert any("nowhere" in m for m in msgs(op.check(p, TODAY), "error"))


def test_the_example_profile_loads_and_has_no_errors():
    p = op.load_path(Path(__file__).resolve().parents[1] / "profile.example.ini")
    assert [f for f in op.check(p, TODAY) if f["level"] == "error"] == []


def test_the_command_line_reports_problems_and_exits_nonzero_only_on_errors(tmp_path, capsys):
    good = tmp_path / "good.ini"; good.write_text(BASE)
    bad = tmp_path / "bad.ini"; bad.write_text(BASE.replace("employees = 3", "employees = x"))
    assert op.main([str(good)], today=TODAY) == 0
    assert op.main([str(bad)], today=TODAY) == 1
    assert "whole number" in capsys.readouterr().out


def test_the_context_option_prints_only_the_ai_safe_facts_as_json_and_refuses_a_profile_with_errors(tmp_path, capsys):
    import json
    good = tmp_path / "good.ini"; good.write_text(BASE)
    assert op.main(["--context", str(good)], today=TODAY) == 0
    out = capsys.readouterr().out
    ctx = json.loads(out)
    assert ctx["size_band"] == "nano" and ctx["other_personnel"] == "yes"
    assert "Secret Name" not in out and "secret-host" not in out
    bad = tmp_path / "bad.ini"; bad.write_text(BASE.replace("employees = 3", "employees = x"))
    assert op.main(["--context", str(bad)], today=TODAY) == 1
    captured = capsys.readouterr()
    assert captured.out.strip() == "" and "whole number" in captured.err       # nothing on stdout for the shell to pick up


def test_the_private_profile_and_the_generated_context_are_never_published():
    ignored = (Path(__file__).resolve().parents[1] / ".gitignore").read_text().split()
    assert "profile.ini" in ignored and ".context.json" in ignored
