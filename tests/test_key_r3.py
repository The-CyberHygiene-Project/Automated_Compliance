"""Rev 3 provisional answer key (derived from the owner's Rev 2 determinations through NIST's mapping)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import key_r3 as k  # noqa: E402


def test_requirement_status_aggregates_the_objectives_the_key_assessed():
    agg = k.r2_by_requirement({
        "3.1.1[a]": "SATISFIED", "3.1.1[b]": "SATISFIED",
        "3.1.2[a]": "SATISFIED", "3.1.2[b]": "PARTIALLY SATISFIED",
        "3.1.3[a]": "OTHER THAN SATISFIED", "3.1.3[b]": "OTHER THAN SATISFIED",
        "3.1.4": "UNVERIFIED", "3.1.5[a]": "NOT APPLICABLE",
        "3.1.6[a]": "SATISFIED", "3.1.6[b]": "OTHER THAN SATISFIED"})
    assert agg["3.1.1"] == "SATISFIED" and agg["3.1.2"] == "PARTIALLY SATISFIED"
    assert agg["3.1.3"] == "OTHER THAN SATISFIED" and agg["3.1.6"] == "PARTIALLY SATISFIED"
    assert agg["3.1.4"] == "UNVERIFIED" and agg["3.1.5"] == "NOT APPLICABLE"


MAPPING = [  # (R2 id, R3 id, change type)
    ("3.1.1", "03.01.01", "Significant Change"), ("3.1.2", "03.01.02", "No Significant Change"),
    ("3.1.14", "03.01.14", "Withdrawn"), ("", "03.06.04", "New Requirement"),
    ("3.1.7", "03.01.07", "Minor Change"), ("3.1.8", "03.01.08", "New ODP")]
INCORPORATED = {"03.01.14": "03.01.12"}
R2 = {"3.1.1": "SATISFIED", "3.1.2": "SATISFIED", "3.1.7": "OTHER THAN SATISFIED", "3.1.8": "SATISFIED",
      "3.1.14": "OTHER THAN SATISFIED", "3.1.12": "SATISFIED"}
MAPPING.append(("3.1.12", "03.01.12", "No Significant Change"))


def build():
    return {r["r3"]: r for r in k.build(MAPPING, INCORPORATED, R2, in_force=["03.01.01", "03.01.02", "03.01.07",
            "03.01.08", "03.01.12", "03.06.04"])}


def test_basis_carried_ceiling_or_new_by_the_kind_of_change():
    b = build()
    assert b["03.01.02"]["basis"] == "carried" and b["03.01.07"]["basis"] == "carried"
    assert b["03.01.01"]["basis"] == "ceiling" and b["03.01.08"]["basis"] == "ceiling"      # significant / new ODP
    assert b["03.06.04"]["basis"] == "new" and b["03.06.04"]["status"] is None             # no Rev 2 counterpart


def test_a_withdrawn_requirement_folds_into_the_one_that_absorbed_it():
    b = build()
    assert set(b["03.01.12"]["r2_sources"]) == {"3.1.12", "3.1.14"}
    assert b["03.01.12"]["status"] == "PARTIALLY SATISFIED"      # satisfied + other-than-satisfied
    assert "03.01.14" not in b                                   # withdrawn items are not requirements


def test_every_row_says_where_it_came_from_and_nothing_is_called_independent():
    for r in build().values():
        assert r["provenance"].startswith("derived") and "ISSO" in r["provenance"]
