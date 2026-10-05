import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grade_r3 as g  # noqa: E402

AI = """## 03.01.01 Account Management

| Objective | Status | Source | Evidence or reason |
|---|---|---|---|
| A.03.01.01.ODP.01 | Unmet | document | no value found |
| A.03.01.01.a.01 | Met | both | getent shows accounts |
| A.03.01.01.a.02 | Met | document | SSP lists them |
| A.03.01.02.a.01 | Unmet | host | not enforced |
| A.03.01.02.a.02 | Met | host | ok |
| A.03.06.04.a.01 | Met | document | training record |
"""
KEY = [
    {"r3": "03.01.01", "title": "Account Management", "basis": "ceiling", "status": "PARTIALLY SATISFIED", "r2_sources": ["3.1.1"]},
    {"r3": "03.01.02", "title": "Access Enforcement", "basis": "carried", "status": "SATISFIED", "r2_sources": ["3.1.2"]},
    {"r3": "03.06.04", "title": "IR Training", "basis": "new", "status": None, "r2_sources": []},
    {"r3": "03.01.03", "title": "Flow", "basis": "carried", "status": "OTHER THAN SATISFIED", "r2_sources": ["3.1.3"]},
]


def test_requirement_and_parameter_rows_are_separated():
    rows, problems = g.parse_ai(AI)
    assert rows["A.03.01.01.a.01"][:2] == ("Met", "both") and problems == []
    req, odp = g.split(rows)
    assert set(odp) == {"A.03.01.01.ODP.01"} and "A.03.01.01.ODP.01" not in g.requirement_status(req)


def test_requirement_status_from_its_objectives():
    rows, _ = g.parse_ai(AI)
    req, _ = g.split(rows)
    s = g.requirement_status(req)
    assert s["03.01.01"] == "Met" and s["03.01.02"] == "Partial" and s["03.06.04"] == "Met"


def test_compare_against_the_derived_key():
    rows, _ = g.parse_ai(AI)
    r = g.compare(rows, KEY)
    assert ("03.01.01", "Met", "PARTIALLY SATISFIED", "ceiling") in r["lenient"]      # AI above the Rev 2 best case
    assert ("03.01.02", "Partial", "SATISFIED", "carried") in r["stricter"]
    assert [x[0] for x in r["new"]] == ["03.06.04"]                                  # no key: listed, not graded
    assert r["no_answer"] == ["03.01.03"]
    assert r["agree"] == []


def test_report_lists_the_parameters_the_ai_could_not_find_a_value_for():
    rows, problems = g.parse_ai(AI)
    md = g.report(g.compare(rows, KEY), rows, problems, "test-model")
    assert "A.03.01.01.ODP.01" in md and "no value found" in md and "test-model" in md
    assert "provisional" in md.lower()
