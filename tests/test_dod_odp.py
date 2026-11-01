import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import dod_odp  # noqa: E402

SAMPLE = """Access Control
3.1.1 System Account Management
g. Notify account managers.
ODP Values
ODP
Identifier ODP Assignment Text ODP Value
03.01.01.f.02 [Assignment: organization-defined
time period] at most 90 days
03.01.01.g.01 [Assignment: organization-defined
time period] 24 hours
03.01.01.h.02 [Assignment: organization-defined
circumstances]
the work period ends, for privileged
users at a minimum
4
Access Control
3.1.5 System Access Authorization
ODP Values
03.01.05.c
[Assignment: organization-
defined frequency] at least every 12 months, or after
a significant1 change
13
ODP
Identifier ODP Assignment Text ODP Value
03.03.01.a [Assignment:
organization-defined event types]
at a minimum and where applicable:
1) Authentication events:
a) Logons (Success/Failure)
Related Controls: AU-02
"""


def test_values_are_read_with_the_assignment_text_removed_and_lines_joined():
    v = dod_odp.parse_values(SAMPLE)
    assert v["03.01.01.f.02"] == "at most 90 days"
    assert v["03.01.01.g.01"] == "24 hours"
    assert v["03.01.01.h.02"] == "the work period ends, for privileged users at a minimum"


def test_an_identifier_on_its_own_line_and_a_footnote_digit_are_handled_and_page_numbers_dropped():
    v = dod_odp.parse_values(SAMPLE)
    assert v["03.01.05.c"] == "at least every 12 months, or after a significant1 change"


def test_a_long_value_stops_at_related_controls_and_keeps_its_list():
    v = dod_odp.parse_values(SAMPLE)
    assert v["03.03.01.a"].startswith("at a minimum and where applicable:") and "Logons" in v["03.03.01.a"]
    assert "Related Controls" not in v["03.03.01.a"]


def test_no_text_means_no_values():
    assert dod_odp.parse_values("") == {}


def test_a_requirement_part_covers_the_odps_used_in_its_objectives():
    # DoD names the part (03.03.01.b); the kit names the objective (A.03.03.01.b.02). The part is the prefix.
    assert dod_odp.part_of("A.03.03.01.b.02", ["03.03.01.a", "03.03.01.b"]) == "03.03.01.b"
    assert dod_odp.part_of("A.03.01.01.g.01", ["03.01.01.g.01", "03.01.01.g"]) == "03.01.01.g.01"
    assert dod_odp.part_of("A.03.09.01.a", ["03.01.01.g.01"]) is None


KIT = """### 03.01.01 Account Management
- A.03.01.01.g.01 notified within [A.03.01.01.ODP.02: time period] when accounts are no longer required.
- A.03.01.01.h require logout after [A.03.01.01.ODP.05: time period] or when [A.03.01.01.ODP.06: circumstances].
- A.03.01.01.ODP.05 the time period is defined.
- A.03.03.01.b.02 the event types are updated [A.03.03.01.ODP.02: frequency].
"""
PARTS = ["03.01.01.g.01", "03.01.01.h.01", "03.01.01.h.02", "03.03.01.b"]


def test_an_odp_is_matched_to_the_part_of_the_objective_that_uses_it():
    m = dod_odp.odp_parts(KIT, PARTS)
    assert m["A.03.01.01.ODP.02"] == ["03.01.01.g.01"] and m["A.03.03.01.ODP.02"] == ["03.03.01.b"]


def test_when_the_memo_splits_an_objective_into_parts_the_odps_pair_off_in_order():
    m = dod_odp.odp_parts(KIT, PARTS)
    assert m["A.03.01.01.ODP.05"] == ["03.01.01.h.01"] and m["A.03.01.01.ODP.06"] == ["03.01.01.h.02"]


def test_an_odp_with_no_part_in_the_memo_is_left_out_rather_than_guessed():
    assert "A.03.09.99.ODP.01" not in dod_odp.odp_parts(KIT + "- A.03.09.99.a x [A.03.09.99.ODP.01: y]\n", PARTS)
