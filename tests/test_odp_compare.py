import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import odp_compare  # noqa: E402

ODPS = [
    {"ODP ID": "A.03.01.01.ODP[02]", "Req ID": "03.01.01", "Requirement title": "Account Management",
     "What must be defined (NIST)": "the time period to notify when accounts are no longer required", "Status": "Not defined",
     "Basis for the value": "AI scan 2026-10-08 (Local AI (m), unreviewed): No value found in organizational documents. (a proposal: the ISSO decides the value)"},
    {"ODP ID": "A.03.01.01.ODP[01]", "Req ID": "03.01.01", "Requirement title": "Account Management",
     "What must be defined (NIST)": "the time period of inactivity", "Status": "Needs review",
     "Basis for the value": "AI scan 2026-10-08 (Local AI (m), unreviewed): SSP says accounts disabled after 90 days. (a proposal: the ISSO decides the value)"},
    {"ODP ID": "A.03.99.99.ODP[01]", "Req ID": "03.99.99", "Requirement title": "Other",
     "What must be defined (NIST)": "something", "Status": "Not defined", "Basis for the value": ""},
]
DOD = {"03.01.01.g.01": "24 hours", "03.01.01.f.02": "at most 90 days"}
MAP = {"A.03.01.01.ODP.02": ["03.01.01.g.01"], "A.03.01.01.ODP.01": ["03.01.01.f.02"]}


def test_a_register_odp_id_is_matched_to_the_kit_form():
    assert odp_compare.kit_id("A.03.01.01.ODP[02]") == "A.03.01.01.ODP.02"


def test_each_odp_gets_the_dod_value_what_the_documents_say_and_what_to_do():
    rows = {r["odp"]: r for r in odp_compare.compare(ODPS, DOD, MAP)}
    a = rows["A.03.01.01.ODP[02]"]
    assert a["dod"] == "24 hours" and a["action"] == "adopt" and "No value found" in a["found"]
    b = rows["A.03.01.01.ODP[01]"]
    assert b["dod"] == "at most 90 days" and b["action"] == "compare" and "90 days" in b["found"]
    assert "(a proposal" not in b["found"] and "AI scan" not in b["found"]


def test_an_odp_the_memo_does_not_cover_is_marked_so_not_guessed():
    c = {r["odp"]: r for r in odp_compare.compare(ODPS, DOD, MAP)}["A.03.99.99.ODP[01]"]
    assert c["dod"] == "" and c["action"] == "no DoD value"


def test_the_report_has_counts_and_one_row_per_odp():
    text = odp_compare.render(odp_compare.compare(ODPS, DOD, MAP))
    assert "- adopt: 1" in text and "- compare: 1" in text and "- no DoD value: 1" in text
    assert text.count("| A.03.") == 3
