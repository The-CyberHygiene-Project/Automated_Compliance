import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATH = os.environ.get("TRIAGE_FILE", str(HERE.parent / "triage.py"))
spec = importlib.util.spec_from_file_location("triage_under_test", PATH)
triage_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage_mod)


def obj(i, result, ev=""):
    return {"Objective ID": i, "Result": result, "Evidence reference": ev}


def odp(i, status):
    return {"ODP ID": i, "Status": status}


def test_parameters_that_are_undefined_or_awaiting_review_are_parameter_gaps_and_defined_ones_are_ignored():
    r = triage_mod.triage([], [odp("P1", "Not defined"), odp("P2", "Needs review"), odp("P3", "Defined"), odp("P4", "")])
    assert r["parameter"] == ["P1", "P2"] and r["unsorted"] == []


def test_met_na_and_empty_objectives_are_not_open():
    r = triage_mod.triage([obj("A", "Met", "AI scan (Met, source document): x"), obj("B", "N/A"), obj("C", "")], [])
    assert all(v == [] for v in r.values())


def test_unmet_with_documents_or_no_source_is_a_document_gap():
    r = triage_mod.triage([obj("A", "Not Met", "AI scan (Unmet, source document): no record"),
                           obj("B", "Not Met", "AI scan (Unmet, source none): No value found")], [])
    assert r["document"] == ["A", "B"] and r["configuration"] == []


def test_unmet_with_host_or_both_is_a_configuration_gap():
    r = triage_mod.triage([obj("A", "Not Met", "AI scan (Unmet, source host): setting off"),
                           obj("B", "Not Met", "AI scan (Unmet, source both): file missing")], [])
    assert r["configuration"] == ["A", "B"] and r["document"] == []


def test_not_checkable_is_its_own_class_whatever_the_source():
    r = triage_mod.triage([obj("A", "Not assessed", "AI scan (Not checkable, source none): interview needed"),
                           obj("B", "Not assessed", "AI scan (Not checkable, source host): ps shows")], [])
    assert r["not_checkable"] == ["A", "B"]


def test_an_open_row_without_the_ai_marker_or_with_an_odd_one_is_unsorted_never_guessed():
    r = triage_mod.triage([obj("A", "Not Met", "owner note: will fix"), obj("B", "Not Met", ""),
                           obj("C", "Not Met", "AI scan (Maybe, source document): ?"),
                           obj("D", "Not Met", "AI scan (Unmet, source cloud): ?")], [])
    assert r["unsorted"] == ["A", "B", "C", "D"]


def test_input_order_is_kept_and_every_open_row_lands_in_exactly_one_class():
    rows = [obj("Z", "Not Met", "AI scan (Unmet, source document): a"), obj("A", "Not Met", "AI scan (Unmet, source host): b"),
            obj("M", "Not assessed", "AI scan (Not checkable, source none): c")]
    r = triage_mod.triage(rows, [odp("P", "Not defined")])
    flat = [i for k in ("parameter", "document", "configuration", "not_checkable", "unsorted") for i in r[k]]
    assert sorted(flat) == ["A", "M", "P", "Z"] and list(r) == ["parameter", "document", "configuration", "not_checkable", "unsorted"]


def test_render_has_a_count_line_per_class_in_order_and_a_section_only_for_non_empty_classes():
    text = triage_mod.render({"parameter": ["P1"], "document": ["A", "B"], "configuration": [], "not_checkable": [], "unsorted": []})
    lines = text.splitlines()
    assert lines[0] == "# Remediation triage"
    assert lines[1:6] == ["- parameter: 1", "- document: 2", "- configuration: 0", "- not_checkable: 0", "- unsorted: 0"]
    assert "## document" in text and "- A" in lines and "- B" in lines
    assert "## configuration" not in text and "## unsorted" not in text


def test_main_with_no_argument_prints_usage_and_returns_2(capsys):
    assert triage_mod.main([]) == 2
    assert capsys.readouterr().err.strip() != ""


def test_load_and_main_read_a_real_register_without_changing_it(capsys):
    """Set REGISTER_FOR_TESTS to a filled Rev 3 register to run this; it is skipped otherwise."""
    import pytest
    path = os.environ.get("REGISTER_FOR_TESTS")
    if not path or not Path(path).exists():
        pytest.skip("REGISTER_FOR_TESTS not set")
    reg = Path(path)
    before = reg.read_bytes()
    objectives, odps = triage_mod.load(str(reg))
    assert len(objectives) == 422 and len(odps) == 88
    assert triage_mod.main([str(reg)]) == 0
    out = capsys.readouterr().out
    counts = [int(l.split(": ")[1]) for l in out.splitlines()[1:6]]
    result = triage_mod.triage(objectives, odps)
    assert counts == [len(result[k]) for k in ("parameter", "document", "configuration", "not_checkable", "unsorted")]
    assert reg.read_bytes() == before
