"""Grader for the 800-171A local-AI test. Run: python3 -m pytest -q tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grade  # noqa: E402

KIT = """### 3.1.1 Limit access.

- 3.1.1[a] users identified.
- 3.1.1[b] processes identified.
- 3.1.1[c] devices identified.

### 3.13.4 Prevent transfer.

- 3.13.4 transfer is prevented.

### 3.2.1 Awareness.

- 3.2.1[a] x.
- 3.2.1[b] y.
- 3.2.1[c] z.

### 3.10.4 Physical logs.

- 3.10.4 audit logs of physical access are maintained.
"""

KEY = """## 3.1.1 — Limit access

| Obj | Determination | Method | Status |
|:---|:---|:---:|:---|
| [a]–[b] | users and processes | E | **SATISFIED** |
| [c] | devices | E | **PARTIALLY SATISFIED** |

## 3.13.4 — Prevent transfer

| Obj | Determination | Status |
|:---|:---|:---|
| [a] | transfer prevented | **OTHER THAN SATISFIED** |

## 3.2.1 / 3.2.2
| Req | Obj | Determination | Status |
|:---|:---|:---|:---|
| 3.2.1 | [a]/[b] | aware | **SATISFIED** |

> **RE-DETERMINED 2026-09-15** — superseding the August determinations, retained
> here: **3.2.1 PARTIALLY SATISFIED**.

## 3.10.4 / 3.10.5
| Req | Determination | Status |
|:---|:---|:---|
| 3.10.4 | Audit logs of physical access are maintained | **OTHER THAN SATISFIED** |
"""

AI = """## 3.1.1 Limit access

| Objective | Status | Source | Evidence or reason |
|---|---|---|---|
| 3.1.1[a] | Met | host | getent passwd |
| [b] | **Unmet** | document | SSP says so |
| 3.1.1[c] | Not checkable on the VM | none | needs inventory |

### 3.13.4 Prevent transfer

| Objective | Status | Source | Evidence or reason |
|---|---|---|---|
| 3.13.4 | Met | host | ok |
| 3.13.4 | Unmet | host | duplicate row |
| 3.2.1[a] | Maybe | host | odd status |
"""


def test_kit_lists_lettered_and_single_objectives():
    assert grade.kit_ids(KIT) == ["3.1.1[a]", "3.1.1[b]", "3.1.1[c]", "3.13.4", "3.2.1[a]", "3.2.1[b]", "3.2.1[c]",
                                  "3.10.4"]


def test_key_expands_ranges_maps_single_a_and_applies_redeterminations():
    key, notes = grade.parse_key(KEY, grade.kit_ids(KIT))
    assert key["3.1.1[a]"] == key["3.1.1[b]"] == "SATISFIED"
    assert key["3.1.1[c]"] == "PARTIALLY SATISFIED"
    assert key["3.13.4"] == "OTHER THAN SATISFIED"            # the key's [a] is NIST's single objective
    # the TABLE carries the current determination; the note keeps the superseded August value for history
    assert key["3.2.1[a]"] == key["3.2.1[b]"] == "SATISFIED"
    assert "3.2.1[c]" not in key                              # the key never assessed it
    assert any("re-determined" in n and "3.2.1" in n for n in notes)
    assert key["3.10.4"] == "OTHER THAN SATISFIED"            # requirement-level row, no objective letter


def test_ai_rows_read_with_heading_context_and_problems_reported():
    rows, problems = grade.parse_ai(AI, grade.kit_ids(KIT))
    assert rows["3.1.1[a]"] == ("Met", "host")
    assert rows["3.1.1[b]"] == ("Unmet", "document")
    assert rows["3.1.1[c]"] == ("Not checkable", "none")
    assert rows["3.13.4"] == ("Met", "host")                  # first answer kept
    assert any("duplicate" in p and "3.13.4" in p for p in problems)
    assert any("unreadable status" in p and "3.2.1[a]" in p for p in problems)


def test_compare_counts_agreement_and_names_lenient_disagreements():
    kit = grade.kit_ids(KIT)
    key, _ = grade.parse_key(KEY, kit)
    rows, _ = grade.parse_ai(AI, kit)
    r = grade.compare(kit, key, rows)
    assert r["answered"] == 4 and r["missing"] == ["3.2.1[a]", "3.2.1[b]", "3.2.1[c]", "3.10.4"]
    assert ("3.1.1[a]", "Met", "SATISFIED") in r["agree"]
    assert ("3.1.1[b]", "Unmet", "SATISFIED") in r["stricter"]          # AI says unmet, key says satisfied
    assert ("3.13.4", "Met", "OTHER THAN SATISFIED") in r["lenient"]    # AI says met, key says not
    assert ("3.1.1[c]", "Not checkable", "PARTIALLY SATISFIED") in r["abstained"]


def test_report_is_markdown_with_the_headline_numbers():
    kit = grade.kit_ids(KIT)
    key, notes = grade.parse_key(KEY, kit)
    rows, problems = grade.parse_ai(AI, kit)
    md = grade.report(grade.compare(kit, key, rows), problems, notes, "test-model")
    assert "4 of 8" in md and "test-model" in md and "3.13.4" in md
