import json
import os
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "reference"))
import fill_register as fr  # noqa: E402
import read_xlsx  # noqa: E402

REGISTER = Path(os.environ.get("R3_REGISTER", str(Path(__file__).resolve().parents[1] / "templates" / "NIST_800-171r3_Measurement_Register.xlsx")))


def test_set_cell_fills_empty_typed_and_missing_cells_and_escapes():
    xml = '<row r="3"><c r="H3" s="23"/><c r="J3" s="23" t="s"><v>5</v></c></row>'
    out = fr.set_cell(xml, "H3", "3.1.1 & <x>")
    assert '<c r="H3" s="23" t="inlineStr"><is><t xml:space="preserve">3.1.1 &amp; &lt;x&gt;</t></is></c>' in out
    out = fr.set_cell(out, "J3", "Implemented")
    assert "<v>5</v>" not in out and "Implemented" in out and 's="23"' in out
    with pytest.raises(KeyError):
        fr.set_cell(xml, "Z9", "x")


def test_ai_results_map_to_the_registers_own_dropdown_words():
    assert fr.result_word("Met") == "Met" and fr.result_word("Unmet") == "Not Met"
    assert fr.result_word("N/A") == "N/A" and fr.result_word("Not checkable") == "Not assessed"
    assert fr.method_word("host") == "Test" and fr.method_word("document") == "Examine"
    assert fr.method_word("both") == "Combination" and fr.method_word("none") == ""


def test_parameter_values_found_by_the_ai_are_needs_review_never_defined():
    assert fr.odp_status("Met") == "Needs review" and fr.odp_status("Unmet") == "Not defined"
    assert fr.odp_status("Not checkable") == "Not defined"


def test_rev2_status_only_where_rev3_barely_changed():
    k = lambda basis, status: {"basis": basis, "status": status}  # noqa: E731
    assert fr.implementation_status(k("carried", "SATISFIED")) == "Implemented"
    assert fr.implementation_status(k("carried", "PARTIALLY SATISFIED")) == "Partially implemented"
    assert fr.implementation_status(k("ceiling", "SATISFIED")) == ""           # Rev 3 asks for more: leave it
    assert fr.implementation_status(k("new", None)) == ""
    assert fr.implementation_status(k("carried", "OTHER THAN SATISFIED")) == ""   # not claiming "Not started"


@pytest.mark.skipif(not REGISTER.exists(), reason="set R3_REGISTER to a Rev 3 measurement register to run this")
def test_round_trip_on_the_real_register(tmp_path):
    res = tmp_path / "res"
    res.mkdir()
    (res / "03.01.01.json").write_text(json.dumps({"requirement": "03.01.01", "model": "m", "results": [
        {"objective": "A.03.01.01.a.01", "status": "Met", "source": "both", "evidence": "SSP lists types"},
        {"objective": "A.03.01.01.ODP.01", "status": "Met", "source": "document", "evidence": "SSP states 90 days"},
        {"objective": "A.03.01.01.ODP.02", "status": "Unmet", "source": "none", "evidence": "no value found"}]}))
    key = [{"r3": "03.01.01", "title": "Account Management", "basis": "ceiling", "status": "PARTIALLY SATISFIED",
            "r2_sources": ["3.1.1"], "note": "n"},
           {"r3": "03.01.02", "title": "Access Enforcement", "basis": "carried", "status": "SATISFIED",
            "r2_sources": ["3.1.2"], "note": "n"}]
    out = tmp_path / "filled.xlsx"
    fr.fill(REGISTER, out, key, res, "2026-10-05")
    wb = read_xlsx.read(out)
    req = {r[1]: r for r in wb["Requirements"][1:]}
    assert req["03.01.01"][7] == "3.1.1" and "PARTIALLY SATISFIED" in req["03.01.01"][11] and req["03.01.01"][9] == "Not started"
    assert req["03.01.02"][9] == "Implemented"
    obj = {r[0]: r for r in wb["Objectives"][1:]}
    row = obj["A.03.01.01.a.01"]
    assert row[7] == "Met" and row[8] == "Combination" and "SSP lists types" in row[9] and "unreviewed" in row[10]
    assert obj["A.03.01.01.a.02"][7] == "Not assessed"                      # not in the results: untouched
    odp = {r[0]: r for r in wb["ODPs"][1:]}
    assert odp["A.03.01.01.ODP[01]"][12] == "Needs review" and "90 days" in odp["A.03.01.01.ODP[01]"][11]
    assert odp["A.03.01.01.ODP[02]"][12] == "Not defined" and odp["A.03.01.01.ODP[01]"][8] == ""
    assert zipfile.ZipFile(out).testzip() is None


def test_an_existing_output_is_never_overwritten_without_force(tmp_path):
    out = tmp_path / "filled.xlsx"
    out.write_text("the owner's edits")
    with pytest.raises(FileExistsError):
        fr.fill(tmp_path / "no-register-needed.xlsx", out, [], tmp_path, "2026-10-06")
    assert out.read_text() == "the owner's edits"


def test_the_default_output_name_carries_the_date_so_runs_never_collide():
    assert fr.default_out("2026-10-06").name == "NIST_800-171r3_Measurement_Register_filled_2026-10-06.xlsx"
    assert fr.default_out("2026-10-07") != fr.default_out("2026-10-06")


def test_a_missing_rev2_key_skips_the_prefill_instead_of_failing(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "KEY_PATH", tmp_path / "absent.json")
    assert fr.load_key() == []


# ------------------------------------------------------------------ merge: new scan results into a working register
def _results(dirpath, rows, model="m"):
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "03.01.01.json").write_text(json.dumps({"requirement": "03.01.01", "model": model, "results": rows}))
    return dirpath


def _row(oid, status, source="both", evidence="evidence text"):
    return {"objective": oid, "status": status, "source": source, "evidence": evidence}


def _edit(path, sheet, ref, text):
    """Simulate the owner typing into a cell (rewrites the workbook, leaves the AI record file alone)."""
    z = zipfile.ZipFile(path)
    names = fr._sheets(z)
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    items = list(z.infolist())
    z.close()
    parts[names[sheet]] = fr.set_cell(parts[names[sheet]].decode(), ref, text).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for i in items:
            out.writestr(i, parts[i.filename])


def _cell(path, sheet, id_col, oid, col):
    rows = read_xlsx.read(path)[sheet]
    return next((r[col] if len(r) > col else "" for r in rows[1:] if r and r[id_col] == oid), None)


@pytest.mark.skipif(not REGISTER.exists(), reason="set R3_REGISTER to a Rev 3 measurement register to run this")
class TestMerge:
    KEY = [{"r3": "03.01.01", "title": "t", "basis": "ceiling", "status": "PARTIALLY SATISFIED", "r2_sources": ["3.1.1"], "note": "n"}]

    def _first(self, tmp_path):
        res = _results(tmp_path / "r1", [_row("A.03.01.01.a.01", "Met"), _row("A.03.01.01.ODP.01", "Met", "document", "SSP states 90 days"),
                                         _row("A.03.01.01.ODP.02", "Unmet", "none", "no value found")])
        first = tmp_path / "first.xlsx"
        fr.fill(REGISTER, first, self.KEY, res, "2026-10-05")
        return first

    def test_fill_writes_a_record_of_what_the_ai_wrote(self, tmp_path):
        first = self._first(tmp_path)
        rec = json.loads(Path(str(first) + ".aimeta.json").read_text())
        assert rec["Objectives!H" + str(fr._rowof(first, "Objectives", 0, "A.03.01.01.a.01"))] == "Met"
        assert any(k.startswith("ODPs!M") and v == "Needs review" for k, v in rec.items())

    def test_merge_keeps_the_owners_edits_and_refreshes_the_rest(self, tmp_path):
        first = self._first(tmp_path)
        oh = fr._rowof(first, "Objectives", 0, "A.03.01.01.a.01")
        om = fr._rowof(first, "ODPs", 0, "A.03.01.01.ODP[01]")
        _edit(first, "Objectives", f"H{oh}", "Not Met")                    # the owner overrode the AI's Met
        _edit(first, "ODPs", f"M{om}", "Defined")                          # the owner decided a parameter
        _edit(first, "ODPs", f"I{om}", "90 days")
        res2 = _results(tmp_path / "r2", [_row("A.03.01.01.a.01", "Unmet", evidence="new evidence"), _row("A.03.01.01.a.02", "Met"),
                                          _row("A.03.01.01.ODP.01", "Unmet", "none", "no value now"),
                                          _row("A.03.01.01.ODP.02", "Met", "document", "now stated: 30 days")])
        second = tmp_path / "second.xlsx"
        report = fr.merge(first, second, self.KEY, res2, "2026-10-06")
        assert _cell(second, "Objectives", 0, "A.03.01.01.a.01", 7) == "Not Met"                  # owner's edit kept
        assert _cell(second, "ODPs", 0, "A.03.01.01.ODP[01]", 12) == "Defined"
        assert _cell(second, "ODPs", 0, "A.03.01.01.ODP[01]", 8) == "90 days"
        assert _cell(second, "Objectives", 0, "A.03.01.01.a.02", 7) == "Met"                      # new row written
        assert _cell(second, "ODPs", 0, "A.03.01.01.ODP[02]", 12) == "Needs review"               # untouched AI cell refreshed
        assert "30 days" in _cell(second, "ODPs", 0, "A.03.01.01.ODP[02]", 11)
        assert _cell(first, "Objectives", 0, "A.03.01.01.a.01", 7) == "Not Met"                   # the old file is unchanged
        assert any("A.03.01.01.a.01" in c["what"] for c in report["kept"]) and report["written"] > 0
        assert Path(str(second) + ".aimeta.json").exists()

    def test_merge_refuses_a_file_it_has_no_record_for(self, tmp_path):
        first = self._first(tmp_path)
        Path(str(first) + ".aimeta.json").unlink()
        with pytest.raises(fr.NoRecord):
            fr.merge(first, tmp_path / "x.xlsx", self.KEY, tmp_path / "r1", "2026-10-06")

    def test_adopt_rebuilds_the_record_for_a_file_made_before_records_existed(self, tmp_path):
        first = self._first(tmp_path)
        rec_path = Path(str(first) + ".aimeta.json")
        original = rec_path.read_text()
        rec_path.unlink()
        n = fr.adopt(first, self.KEY, tmp_path / "r1", "2026-10-05")
        assert n > 0 and json.loads(rec_path.read_text()) == json.loads(original)

    def test_evidence_with_line_breaks_is_not_mistaken_for_an_owner_edit(self, tmp_path):
        res = _results(tmp_path / "r", [_row("A.03.01.01.a.01", "Met", evidence="line one\nline  two\n\nline three")])
        first = tmp_path / "first.xlsx"
        fr.fill(REGISTER, first, self.KEY, res, "2026-10-05")
        report = fr.merge(first, tmp_path / "second.xlsx", self.KEY, res, "2026-10-06")
        assert report["kept"] == []

    def test_adopt_records_cells_whose_text_has_odd_whitespace(self, tmp_path):
        res = _results(tmp_path / "r", [_row("A.03.01.01.a.01", "Met", evidence="a\nb  c")])
        first = tmp_path / "first.xlsx"
        fr.fill(REGISTER, first, self.KEY, res, "2026-10-05")
        rec = _record = Path(str(first) + ".aimeta.json")
        full = json.loads(rec.read_text())
        rec.unlink()
        assert fr.adopt(first, self.KEY, res, "2026-10-05") == len(full)
