import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import poam  # noqa: E402
import triage  # noqa: E402

OBJ_KEY = "What is measured (SP 800-171A Rev 3 objective)"


def obj(i, result, ev, req="03.01.01", method="Examine", date="2026-10-08", text="something is defined"):
    return {"Objective ID": i, "Req ID": req, OBJ_KEY: text, "Result": result, "Method used": method,
            "Evidence reference": ev, "Assessor": "Local AI (model), unreviewed", "Date assessed": date, "Notes": ""}


def odp(i, status, req="03.01.01", basis="AI scan 2026-10-08 (Local AI): No value found."):
    return {"ODP ID": i, "Req ID": req, "What must be defined (NIST)": "the time period", "Value defined": "",
            "Status": status, "Basis for the value": basis}


ROWS = [obj("A.03.01.01.a", "Not Met", "AI scan (Unmet, source document): no record found"),
        obj("A.03.07.06.b", "Not Met", "AI scan (Unmet, source both): file missing on host", req="03.07.06", method="Test"),
        obj("A.03.09.01.a", "Not assessed", "AI scan (Not checkable, source none): needs interview", req="03.09.01", method="Interview"),
        obj("A.03.01.02", "Not Met", "owner note: will fix", req="03.01.02"),
        obj("A.03.01.03", "Met", "AI scan (Met, source document): fine", req="03.01.03")]
ODPS = [odp("A.03.01.01.ODP[01]", "Not defined"), odp("A.03.01.01.ODP[02]", "Needs review"), odp("A.03.01.01.ODP[03]", "Defined")]


def build():
    result = triage.triage(ROWS, ODPS)
    return poam.build(ROWS, ODPS, result, when="2026-10-09T12:00:00Z")


def body(doc):
    return doc["plan-of-action-and-milestones"]


def item_for(doc, oid):
    return next(i for i in body(doc)["poam-items"] if f"[{oid}]" in i["title"])


def props(item):
    return {p["name"]: p["value"] for p in item["props"]}


def test_one_item_per_open_row_and_none_for_met_or_defined():
    items = body(build())["poam-items"]
    titles = " ".join(i["title"] for i in items)
    assert len(items) == 6
    assert "[A.03.01.03]" not in titles and "ODP[03]" not in titles


def test_each_item_says_its_class_its_control_and_that_it_is_a_draft():
    d = build()
    p = props(item_for(d, "A.03.01.01.a"))
    assert p["triage-class"] == "document" and p["control-id"] == "03.01.01" and p["status"] == "draft"
    assert props(item_for(d, "A.03.07.06.b"))["triage-class"] == "configuration"
    assert props(item_for(d, "A.03.09.01.a"))["triage-class"] == "not_checkable"
    assert props(item_for(d, "A.03.01.01.ODP[01]"))["triage-class"] == "parameter"


def test_ai_written_rows_are_marked_unreviewed_and_owner_edited_rows_are_not():
    d = build()
    assert props(item_for(d, "A.03.01.01.a"))["source"] == "local-ai-unreviewed"
    assert props(item_for(d, "A.03.01.02"))["source"] == "owner-edited"
    assert props(item_for(d, "A.03.01.02"))["triage-class"] == "unsorted"


def test_the_weakness_is_in_plain_words_and_the_evidence_is_an_observation_the_item_points_to():
    d = build()
    item = item_for(d, "A.03.01.01.a")
    assert "something is defined" in item["description"]
    obs = {o["uuid"]: o for o in body(d)["observations"]}
    linked = [obs[r["observation-uuid"]] for r in item["related-observations"]]
    assert len(linked) == 1 and "no record found" in linked[0]["description"]
    assert linked[0]["methods"] == ["EXAMINE"] and linked[0]["collected"] == "2026-10-08T00:00:00Z"
    assert obs[item_for(d, "A.03.07.06.b")["related-observations"][0]["observation-uuid"]]["methods"] == ["TEST"]


def test_a_proposed_parameter_value_is_described_as_awaiting_the_owner():
    d = build()
    assert "awaiting" in item_for(d, "A.03.01.01.ODP[02]")["description"].lower()
    assert "no value" in item_for(d, "A.03.01.01.ODP[01]")["description"].lower()


def test_ids_are_stable_between_builds_and_unique_within_one():
    a, b = build(), build()
    assert a == b
    ids = [i["uuid"] for i in body(a)["poam-items"]] + [o["uuid"] for o in body(a)["observations"]] + [body(a)["uuid"]]
    assert len(ids) == len(set(ids))


def test_the_document_names_no_organization_or_person_and_says_it_is_draft_ai_assisted():
    text = json.dumps(build())
    meta = body(build())["metadata"]
    assert "draft" in meta["title"].lower() and "AI" in meta["title"]
    assert meta["oscal-version"] == "1.1.2" and meta["last-modified"] == "2026-10-09T12:00:00Z"
    assert "party" not in text and "Shannon" not in text


def test_the_output_validates_against_nists_oscal_schema():
    jsonschema = pytest.importorskip("jsonschema")
    raw = (HERE / "reference" / "oscal_complete_schema_1.1.2.json").read_text()
    # NIST's patterns use ECMA \\p{L} / \\p{N}, which Python's re does not know: use plain letter and digit classes
    schema = json.loads(raw.replace("\\\\p{L}", "[a-zA-Z]").replace("\\\\p{N}", "[0-9]"))
    jsonschema.validate(build(), schema)


def test_the_command_writes_a_file_and_leaves_the_register_alone(tmp_path, monkeypatch):
    monkeypatch.setattr(poam, "_load", lambda path: (ROWS, ODPS))
    reg = tmp_path / "reg.xlsx"
    reg.write_bytes(b"not read by the stub")
    out = tmp_path / "poam.json"
    assert poam.main([str(reg), "--out", str(out), "--when", "2026-10-09T12:00:00Z"]) == 0
    assert json.loads(out.read_text()) == build() and reg.read_bytes() == b"not read by the stub"
    assert poam.main([]) == 2
    assert poam.main([str(reg), "--out", str(out), "--when", "2026-10-09T12:00:00Z"]) == 1   # never overwrites
