"""Tests for the v0.36 founder-trait heritability reducer
(``scripts/trait_replay.py``).

Synthetic-fixture coverage of the contract committed in
[[docs/experiments/fear_hunger_v0.36.md]]:

  - PRIMARY_TRAITS / EXPECTED_SIGN / SECONDARY_TRAITS locked constants.
  - Cohen's d computation on hand-built fixtures (positive, negative,
    zero-variance, single-sample, empty group).
  - sign_aligned per primary trait based on EXPECTED_SIGN.
  - Monotone non-decreasing predicate on abs_d sequences.
  - Five classification states: aligned-and-strengthening, aligned-flat,
    opposite-sign-strengthening, opposite-sign-flat, below-threshold.
  - Three-way verdict for all three states (H5 fires; H6 fires via
    aligned-flat AND via opposite-sign-only; H7 fires).
  - derive_top_lineage_id matches v0.34's algorithm (lowest lineage_id
    tie-break; None when total_b50 == 0).
  - build_founder_trait_rows halts on founder count != 5 and on
    missing trait row.
  - parse_trait_fingerprints halts on missing file, missing column,
    and empty value.
  - Anchor loaders + cross_check_double_anchor halt on v0.34 / v0.35
    drift.
  - End-to-end on tmp_path synthetic corpus.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

_TR_PATH = Path(__file__).parent.parent / "scripts" / "trait_replay.py"
_spec = importlib.util.spec_from_file_location("trait_replay", _TR_PATH)
assert _spec is not None
assert _spec.loader is not None
tr = importlib.util.module_from_spec(_spec)
sys.modules["trait_replay"] = tr
_spec.loader.exec_module(tr)
lr = tr.lr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent(
    *,
    agent_id: int,
    lineage_id: int,
    parent_id: int | None,
    birth_tick_normalized: int,
    death_tick: int | None = None,
    n_ticks: int = 200,
) -> lr.AgentRow:
    return lr.AgentRow(
        source_version="vX",
        arm_label="arm",
        hazard=8,
        seed=1,
        agent_id=agent_id,
        lineage_id=lineage_id,
        parent_id=parent_id,
        is_founder=parent_id is None,
        birth_tick=None if parent_id is None else birth_tick_normalized,
        birth_tick_normalized=birth_tick_normalized,
        death_tick=death_tick,
        lifespan=(n_ticks if death_tick is None else death_tick) - birth_tick_normalized,
        death_cause="" if death_tick is None else "STARVATION",
        generation_depth=0 if parent_id is None else 1,
        offspring_count=0,
        born_after_tick_50=birth_tick_normalized > 50,
        survived_to_end=death_tick is None,
    )


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_primary_traits_locked() -> None:
    assert tr.PRIMARY_TRAITS == (
        "reproduction_drive",
        "metabolic_rate",
        "sensor_radius",
    )
    assert len(tr.PRIMARY_TRAITS) == 3


def test_expected_signs_locked() -> None:
    assert tr.EXPECTED_SIGN == {
        "reproduction_drive": +1,
        "metabolic_rate": -1,
        "sensor_radius": +1,
    }


def test_secondary_traits_count_locked() -> None:
    assert len(tr.SECONDARY_TRAITS) == 10
    # Every primary trait must NOT be in the secondary set.
    for trait in tr.PRIMARY_TRAITS:
        assert trait not in tr.SECONDARY_TRAITS


def test_all_traits_covers_thirteen_columns() -> None:
    assert len(tr.ALL_TRAITS) == 13
    assert set(tr.ALL_TRAITS) == set(tr.PRIMARY_TRAITS) | set(tr.SECONDARY_TRAITS)


def test_thresholds_locked() -> None:
    assert tr.ABS_D_THRESHOLD == 0.4
    assert tr.STRENGTHENING_SPREAD_THRESHOLD == 0.2


def test_verdict_constants_locked() -> None:
    assert tr.VERDICT_LINKED_STRENGTHENING == "H5_TRAIT_LINKED_AND_STRENGTHENING"
    assert tr.VERDICT_LINKED_FLAT == "H6_TRAIT_LINKED_FLAT"
    assert tr.VERDICT_NEUTRAL == "H7_TRAIT_NEUTRAL"


def test_locked_phrases_present() -> None:
    assert "strengthening monotonically" in tr.LOCKED_H5_PHRASE
    assert "expected sign" in tr.LOCKED_H6_PHRASE
    assert "does not detectably predict" in tr.LOCKED_H7_PHRASE


def test_reassert_b_pool_anchors_passes() -> None:
    tr.reassert_b_pool_anchors()


# ---------------------------------------------------------------------------
# Cohen's d
# ---------------------------------------------------------------------------


def test_cohens_d_positive_signed() -> None:
    winner = [10.0, 11.0, 12.0, 13.0, 14.0]  # mean 12, var 2.5
    nonwinner = [5.0, 6.0, 7.0, 8.0, 9.0]  # mean 7, var 2.5
    mean_w, mean_nw, pooled_std, signed_d, abs_d = tr.compute_cohens_d(winner, nonwinner)
    assert mean_w == 12.0
    assert mean_nw == 7.0
    # pooled_var = (4*2.5 + 4*2.5)/8 = 2.5; pooled_std = sqrt(2.5)
    assert pooled_std == pytest.approx(math.sqrt(2.5))
    assert signed_d == pytest.approx(5.0 / math.sqrt(2.5))
    assert abs_d == pytest.approx(5.0 / math.sqrt(2.5))


def test_cohens_d_negative_signed_when_winner_below() -> None:
    winner = [5.0, 5.0, 5.0]
    nonwinner = [10.0, 10.0, 10.0]
    # Both groups have zero variance -> pooled_std = 0 -> signed_d / abs_d are NaN by design.
    mean_w, mean_nw, pooled_std, signed_d, abs_d = tr.compute_cohens_d(winner, nonwinner)
    assert pooled_std == 0
    assert math.isnan(signed_d)
    assert math.isnan(abs_d)
    assert mean_w == 5.0
    assert mean_nw == 10.0


def test_cohens_d_negative_signed_realistic() -> None:
    winner = [5.0, 6.0, 7.0]  # mean 6, var 1
    nonwinner = [9.0, 10.0, 11.0]  # mean 10, var 1
    mean_w, mean_nw, pooled_std, signed_d, abs_d = tr.compute_cohens_d(winner, nonwinner)
    assert mean_w == 6.0
    assert mean_nw == 10.0
    # pooled_var = (2*1 + 2*1) / 4 = 1
    assert pooled_std == pytest.approx(1.0)
    assert signed_d == pytest.approx(-4.0)
    assert abs_d == pytest.approx(4.0)


def test_cohens_d_empty_group_returns_nans() -> None:
    mean_w, _mean_nw, _pooled_std, signed_d, _abs_d = tr.compute_cohens_d([], [1.0, 2.0])
    assert math.isnan(mean_w)
    assert math.isnan(signed_d)


def test_cohens_d_zero_variance_in_one_group() -> None:
    winner = [5.0, 5.0, 5.0, 5.0]  # var 0
    nonwinner = [3.0, 4.0, 5.0, 6.0]  # var 5/3
    mean_w, mean_nw, pooled_std, signed_d, _abs_d = tr.compute_cohens_d(winner, nonwinner)
    assert mean_w == 5.0
    assert mean_nw == 4.5
    # pooled_var = (3*0 + 3*(5/3)) / 6 = 5/6
    assert pooled_std == pytest.approx(math.sqrt(5 / 6))
    assert signed_d == pytest.approx(0.5 / math.sqrt(5 / 6))


# ---------------------------------------------------------------------------
# is_weak_monotone_non_decreasing
# ---------------------------------------------------------------------------


def test_monotone_non_decreasing_passes_on_strict_increase() -> None:
    assert tr.is_weak_monotone_non_decreasing([0.1, 0.2, 0.3, 0.4]) is True


def test_monotone_non_decreasing_passes_on_ties() -> None:
    assert tr.is_weak_monotone_non_decreasing([0.1, 0.2, 0.2, 0.3]) is True


def test_monotone_non_decreasing_fails_on_dip() -> None:
    assert tr.is_weak_monotone_non_decreasing([0.1, 0.4, 0.3, 0.5]) is False


# ---------------------------------------------------------------------------
# classify_primary
# ---------------------------------------------------------------------------


def test_classify_primary_aligned_and_strengthening() -> None:
    abs_d_by_h = {0: 0.1, 4: 0.2, 8: 0.35, 12: 0.5}
    monotone, spread, crosses, strengthens, sign_aligned, classification = tr.classify_primary(
        abs_d_by_h, signed_d_h12=0.5, expected_sign=+1
    )
    assert monotone is True
    assert spread == pytest.approx(0.4)
    assert crosses is True
    assert strengthens is True
    assert sign_aligned is True
    assert classification == tr.CLASSIFICATION_ALIGNED_STRENGTHENING


def test_classify_primary_aligned_flat() -> None:
    """Crosses threshold but does not strengthen (e.g. flat at 0.45)."""
    abs_d_by_h = {0: 0.45, 4: 0.45, 8: 0.45, 12: 0.45}
    monotone, spread, crosses, strengthens, sign_aligned, classification = tr.classify_primary(
        abs_d_by_h, signed_d_h12=0.45, expected_sign=+1
    )
    assert monotone is True  # ties OK
    assert spread == pytest.approx(0.0)
    assert crosses is True
    assert strengthens is False  # spread < 0.2
    assert sign_aligned is True
    assert classification == tr.CLASSIFICATION_ALIGNED_FLAT


def test_classify_primary_opposite_sign_strengthening() -> None:
    """Crosses threshold and strengthens, but signed direction opposite."""
    abs_d_by_h = {0: 0.1, 4: 0.2, 8: 0.35, 12: 0.5}
    _monotone, _spread, crosses, strengthens, sign_aligned, classification = tr.classify_primary(
        abs_d_by_h,
        signed_d_h12=+0.5,  # positive
        expected_sign=-1,  # but expected negative
    )
    assert crosses is True
    assert strengthens is True
    assert sign_aligned is False
    assert classification == tr.CLASSIFICATION_OPPOSITE_STRENGTHENING


def test_classify_primary_opposite_sign_flat() -> None:
    abs_d_by_h = {0: 0.45, 4: 0.45, 8: 0.45, 12: 0.45}
    _monotone, _spread, crosses, strengthens, sign_aligned, classification = tr.classify_primary(
        abs_d_by_h, signed_d_h12=+0.45, expected_sign=-1
    )
    assert crosses is True
    assert strengthens is False
    assert sign_aligned is False
    assert classification == tr.CLASSIFICATION_OPPOSITE_FLAT


def test_classify_primary_below_threshold() -> None:
    abs_d_by_h = {0: 0.1, 4: 0.2, 8: 0.25, 12: 0.3}
    _monotone, _spread, crosses, _strengthens, _sign_aligned, classification = tr.classify_primary(
        abs_d_by_h, signed_d_h12=0.3, expected_sign=+1
    )
    assert crosses is False
    assert classification == tr.CLASSIFICATION_BELOW_THRESHOLD


def test_classify_primary_below_threshold_when_d_is_nan() -> None:
    abs_d_by_h = {0: float("nan"), 4: 0.5, 8: 0.5, 12: 0.5}
    _, _, crosses, _, _, classification = tr.classify_primary(
        abs_d_by_h, signed_d_h12=0.5, expected_sign=+1
    )
    assert crosses is False
    assert classification == tr.CLASSIFICATION_BELOW_THRESHOLD


# ---------------------------------------------------------------------------
# Three-way verdict
# ---------------------------------------------------------------------------


def _strengthening_row(
    trait: str,
    classification: str,
    *,
    crosses: bool = True,
    expected_sign: int = +1,
) -> tr.PrimaryStrengtheningRow:
    return tr.PrimaryStrengtheningRow(
        trait=trait,
        expected_sign=expected_sign,
        abs_d_h0=0.1,
        abs_d_h4=0.2,
        abs_d_h8=0.3,
        abs_d_h12=0.5 if crosses else 0.3,
        signed_d_h12=0.5,
        monotone_non_decreasing=True,
        spread=0.4,
        crosses_threshold_at_h12=crosses,
        strengthens=True,
        sign_aligned_at_h12=classification.startswith("aligned"),
        classification=classification,
    )


def test_evaluate_verdict_h5_fires_on_aligned_strengthening() -> None:
    rows = [
        _strengthening_row("reproduction_drive", tr.CLASSIFICATION_ALIGNED_STRENGTHENING),
        _strengthening_row("metabolic_rate", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
        _strengthening_row("sensor_radius", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
    ]
    verdict, phrase, firing = tr.evaluate_verdict(rows)
    assert verdict == tr.VERDICT_LINKED_STRENGTHENING
    assert phrase == tr.LOCKED_H5_PHRASE
    assert firing == ["reproduction_drive"]


def test_evaluate_verdict_h6_fires_on_aligned_flat() -> None:
    rows = [
        _strengthening_row("reproduction_drive", tr.CLASSIFICATION_ALIGNED_FLAT),
        _strengthening_row("metabolic_rate", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
        _strengthening_row("sensor_radius", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
    ]
    verdict, phrase, firing = tr.evaluate_verdict(rows)
    assert verdict == tr.VERDICT_LINKED_FLAT
    assert phrase == tr.LOCKED_H6_PHRASE
    assert firing == ["reproduction_drive"]


def test_evaluate_verdict_h6_fires_on_opposite_sign_only() -> None:
    """Opposite-sign-strengthening cannot fire H5 even if it strengthens."""
    rows = [
        _strengthening_row(
            "metabolic_rate",
            tr.CLASSIFICATION_OPPOSITE_STRENGTHENING,
            expected_sign=-1,
        ),
        _strengthening_row("reproduction_drive", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
        _strengthening_row("sensor_radius", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
    ]
    verdict, phrase, firing = tr.evaluate_verdict(rows)
    assert verdict == tr.VERDICT_LINKED_FLAT
    assert phrase == tr.LOCKED_H6_PHRASE
    assert firing == ["metabolic_rate"]


def test_evaluate_verdict_h7_fires_when_no_trait_crosses() -> None:
    rows = [
        _strengthening_row("reproduction_drive", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
        _strengthening_row("metabolic_rate", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
        _strengthening_row("sensor_radius", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
    ]
    verdict, phrase, firing = tr.evaluate_verdict(rows)
    assert verdict == tr.VERDICT_NEUTRAL
    assert phrase == tr.LOCKED_H7_PHRASE
    assert firing == []


def test_evaluate_verdict_h5_takes_priority_over_h6() -> None:
    """If one trait fires aligned-strengthening and another fires
    aligned-flat, H5 wins."""
    rows = [
        _strengthening_row("reproduction_drive", tr.CLASSIFICATION_ALIGNED_FLAT),
        _strengthening_row(
            "metabolic_rate", tr.CLASSIFICATION_ALIGNED_STRENGTHENING, expected_sign=-1
        ),
        _strengthening_row("sensor_radius", tr.CLASSIFICATION_BELOW_THRESHOLD, crosses=False),
    ]
    verdict, _, firing = tr.evaluate_verdict(rows)
    assert verdict == tr.VERDICT_LINKED_STRENGTHENING
    assert "metabolic_rate" in firing


# ---------------------------------------------------------------------------
# derive_top_lineage_id
# ---------------------------------------------------------------------------


def test_derive_top_lineage_id_picks_max_b50() -> None:
    rows = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=2, lineage_id=1, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=10, lineage_id=0, parent_id=1, birth_tick_normalized=100),  # b50
        _agent(agent_id=11, lineage_id=1, parent_id=2, birth_tick_normalized=80),  # b50
        _agent(agent_id=12, lineage_id=1, parent_id=2, birth_tick_normalized=120),  # b50
    ]
    assert tr.derive_top_lineage_id(rows) == 1


def test_derive_top_lineage_id_tie_break_lowest_lineage_id() -> None:
    rows = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=2, lineage_id=1, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=10, lineage_id=0, parent_id=1, birth_tick_normalized=100),
        _agent(agent_id=11, lineage_id=1, parent_id=2, birth_tick_normalized=120),
    ]
    assert tr.derive_top_lineage_id(rows) == 0


def test_derive_top_lineage_id_returns_none_when_no_b50() -> None:
    rows = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=2, lineage_id=1, parent_id=None, birth_tick_normalized=0),
    ]
    assert tr.derive_top_lineage_id(rows) is None


# ---------------------------------------------------------------------------
# build_founder_trait_rows
# ---------------------------------------------------------------------------


def _five_founder_agents() -> list[lr.AgentRow]:
    return [
        _agent(
            agent_id=lineage_id + 1, lineage_id=lineage_id, parent_id=None, birth_tick_normalized=0
        )
        for lineage_id in range(5)
    ]


def _trait_lookup_for(
    agent_ids: list[int], values_by_lineage: dict[int, dict[str, float]] | None = None
) -> dict[int, dict[str, float]]:
    """Build a {agent_id: traits} mapping with default values per agent."""
    out: dict[int, dict[str, float]] = {}
    for idx, aid in enumerate(agent_ids):
        traits = {trait: 1.0 + idx * 0.1 for trait in tr.ALL_TRAITS}
        if values_by_lineage and idx in values_by_lineage:
            traits.update(values_by_lineage[idx])
        out[aid] = traits
    return out


def test_build_founder_trait_rows_marks_winner() -> None:
    rows = _five_founder_agents()
    trait_lookup = _trait_lookup_for([a.agent_id for a in rows])
    founder_rows = tr.build_founder_trait_rows(
        rows,
        trait_lookup,
        top_lineage_id=2,
        source_version="v0.test",
        arm_label="arm",
        hazard=8,
        seed=1,
    )
    assert len(founder_rows) == 5
    winners = [r for r in founder_rows if r.is_winner]
    assert len(winners) == 1
    assert winners[0].lineage_id == 2


def test_build_founder_trait_rows_halts_on_wrong_founder_count() -> None:
    rows = [
        _agent(agent_id=1, lineage_id=0, parent_id=None, birth_tick_normalized=0),
        _agent(agent_id=2, lineage_id=1, parent_id=None, birth_tick_normalized=0),
    ]
    trait_lookup = _trait_lookup_for([1, 2])
    with pytest.raises(lr.LineageReplayError, match="founder-count mismatch"):
        tr.build_founder_trait_rows(
            rows,
            trait_lookup,
            top_lineage_id=0,
            source_version="vX",
            arm_label="arm",
            hazard=8,
            seed=1,
        )


def test_build_founder_trait_rows_halts_on_missing_trait_row() -> None:
    rows = _five_founder_agents()
    trait_lookup = _trait_lookup_for([a.agent_id for a in rows[:-1]])  # missing founder 5
    with pytest.raises(lr.LineageReplayError, match="missing from"):
        tr.build_founder_trait_rows(
            rows,
            trait_lookup,
            top_lineage_id=0,
            source_version="vX",
            arm_label="arm",
            hazard=8,
            seed=1,
        )


# ---------------------------------------------------------------------------
# parse_trait_fingerprints
# ---------------------------------------------------------------------------


def _write_trait_fingerprints(
    path: Path,
    rows: list[dict[str, str]],
    *,
    columns: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = columns or [
        "agent_id",
        "parent_id",
        "lineage_id",
        "birth_tick",
        "spawn_x",
        "spawn_y",
        *tr.ALL_TRAITS,
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _trait_row(
    agent_id: int, parent_id: str = "", lineage_id: int = 0, **overrides: float
) -> dict[str, str]:
    base = {
        "agent_id": str(agent_id),
        "parent_id": parent_id,
        "lineage_id": str(lineage_id),
        "birth_tick": "0",
        "spawn_x": "1",
        "spawn_y": "0",
    }
    for trait in tr.ALL_TRAITS:
        base[trait] = str(overrides.get(trait, 1.0))
    return base


def test_parse_trait_fingerprints_round_trip(tmp_path) -> None:
    run_dir = tmp_path / "run"
    _write_trait_fingerprints(
        run_dir / "trait_fingerprints.csv",
        [
            _trait_row(1, lineage_id=0, reproduction_drive=2.0),
            _trait_row(2, parent_id="1", lineage_id=0, reproduction_drive=2.1),
        ],
    )
    out = tr.parse_trait_fingerprints(run_dir)
    assert out[1]["reproduction_drive"] == 2.0
    assert out[2]["reproduction_drive"] == 2.1
    assert out[1]["sensor_radius"] == 1.0  # default


def test_parse_trait_fingerprints_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match="missing"):
        tr.parse_trait_fingerprints(tmp_path / "nonexistent")


def test_parse_trait_fingerprints_halts_on_missing_column(tmp_path) -> None:
    run_dir = tmp_path / "run"
    cols = ["agent_id", "parent_id", "lineage_id", "birth_tick", "spawn_x", "spawn_y"]
    cols += [t for t in tr.ALL_TRAITS if t != "reproduction_drive"]
    _write_trait_fingerprints(
        run_dir / "trait_fingerprints.csv",
        [{c: "1" for c in cols}],
        columns=cols,
    )
    with pytest.raises(lr.LineageReplayError, match="missing columns"):
        tr.parse_trait_fingerprints(run_dir)


def test_parse_trait_fingerprints_halts_on_empty_value(tmp_path) -> None:
    run_dir = tmp_path / "run"
    row = _trait_row(1)
    row["reproduction_drive"] = ""  # empty
    _write_trait_fingerprints(run_dir / "trait_fingerprints.csv", [row])
    with pytest.raises(lr.LineageReplayError, match="empty value"):
        tr.parse_trait_fingerprints(run_dir)


# ---------------------------------------------------------------------------
# Anchor loaders / cross_check_double_anchor
# ---------------------------------------------------------------------------


def test_load_v0_34_anchors_round_trip(tmp_path) -> None:
    path = tmp_path / "run_summary.csv"
    path.write_text(
        "source_version,arm_label,hazard,seed,total_b50,top_lineage_id,"
        "top_lineage_b50,top_lineage_b50_share,n_lineages_with_b50_ge_1,"
        "n_lineages_alive_at_end\n"
        "v0.test,arm-A,0,1,10,3,10,1.0,1,5\n"
        "v0.test,arm-B,0,2,0,,,,0,5\n"
    )
    out = tr.load_v0_34_top_lineage_anchors(path)
    assert out[("v0.test", "arm-A", 1)] == 3
    assert out[("v0.test", "arm-B", 2)] is None


def test_load_v0_35_anchors_round_trip(tmp_path) -> None:
    path = tmp_path / "pre_post_dominance.csv"
    path.write_text(
        "source_version,arm_label,hazard,seed,leader_lineage_id_at_tick_50,"
        "leader_births_at_tick_50,eventual_top_lineage_id,eventual_top_b50,"
        "winner_already_dominant_at_tick_50,n_lineages_with_post50_birth\n"
        "v0.test,arm-A,0,1,1,2,3,5,False,2\n"
        "v0.test,arm-B,0,2,0,1,,,,0\n"
    )
    out = tr.load_v0_35_eventual_top_anchors(path)
    assert out[("v0.test", "arm-A", 1)] == 3
    assert out[("v0.test", "arm-B", 2)] is None


def test_load_v0_34_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match="missing"):
        tr.load_v0_34_top_lineage_anchors(tmp_path / "nope.csv")


def test_load_v0_35_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match="missing"):
        tr.load_v0_35_eventual_top_anchors(tmp_path / "nope.csv")


def test_cross_check_double_anchor_passes_when_match() -> None:
    derived = {("v0.test", "arm-A", 1): 3}
    v34 = {("v0.test", "arm-A", 1): 3}
    v35 = {("v0.test", "arm-A", 1): 3}
    tr.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_double_anchor_halts_on_v0_34_drift() -> None:
    derived = {("v0.test", "arm-A", 1): 3}
    v34 = {("v0.test", "arm-A", 1): 99}
    v35 = {("v0.test", "arm-A", 1): 3}
    with pytest.raises(lr.LineageReplayError, match=r"v0\.34 re-anchor mismatch"):
        tr.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_double_anchor_halts_on_v0_35_drift() -> None:
    derived = {("v0.test", "arm-A", 1): 3}
    v34 = {("v0.test", "arm-A", 1): 3}
    v35 = {("v0.test", "arm-A", 1): 99}
    with pytest.raises(lr.LineageReplayError, match=r"v0\.35 re-anchor mismatch"):
        tr.cross_check_double_anchor(derived, v34, v35)


# ---------------------------------------------------------------------------
# aggregate_winner_vs_nonwinner sign_aligned correctness
# ---------------------------------------------------------------------------


def _founder_row(
    *,
    hazard: int,
    seed: int,
    lineage_id: int,
    is_winner: bool,
    overrides: dict[str, float] | None = None,
) -> tr.FounderTraitRow:
    base = {trait: 1.0 for trait in tr.ALL_TRAITS}
    if overrides:
        base.update(overrides)
    return tr.FounderTraitRow(
        source_version="v0.test",
        arm_label="arm",
        hazard=hazard,
        seed=seed,
        lineage_id=lineage_id,
        agent_id=seed * 10 + lineage_id,
        is_winner=is_winner,
        **base,
    )


def test_aggregate_winner_vs_nonwinner_sign_aligned_for_primary() -> None:
    """At hazard=12, winners have higher reproduction_drive than non-winners
    (positive signed_d, expected_sign=+1) -> sign_aligned=True."""
    rows = []
    for seed in range(1, 5):
        rows.append(
            _founder_row(
                hazard=12,
                seed=seed,
                lineage_id=0,
                is_winner=True,
                overrides={"reproduction_drive": 2.0 + seed * 0.1},
            )
        )
    for seed in range(1, 5):
        for lineage_id in range(1, 5):
            rows.append(
                _founder_row(
                    hazard=12,
                    seed=seed,
                    lineage_id=lineage_id,
                    is_winner=False,
                    overrides={"reproduction_drive": 1.0 + seed * 0.1},
                )
            )
    # Pad other hazards with empty data — all default values.
    for hazard in (0, 4, 8):
        for seed in range(1, 5):
            for lineage_id in range(5):
                rows.append(
                    _founder_row(
                        hazard=hazard,
                        seed=seed,
                        lineage_id=lineage_id,
                        is_winner=lineage_id == 0,
                    )
                )
    wvn = tr.aggregate_winner_vs_nonwinner(rows)
    rep_drive_h12 = next(r for r in wvn if r.trait == "reproduction_drive" and r.hazard == 12)
    assert rep_drive_h12.is_primary is True
    assert rep_drive_h12.expected_sign == +1
    assert rep_drive_h12.signed_d > 0
    assert rep_drive_h12.sign_aligned is True


def test_aggregate_winner_vs_nonwinner_sign_misaligned_for_primary_negative_sign() -> None:
    """At hazard=12, winners have HIGHER metabolic_rate (positive signed_d),
    but EXPECTED_SIGN[metabolic_rate] = -1 -> sign_aligned=False."""
    rows = []
    for seed in range(1, 5):
        rows.append(
            _founder_row(
                hazard=12,
                seed=seed,
                lineage_id=0,
                is_winner=True,
                overrides={"metabolic_rate": 2.0 + seed * 0.1},
            )
        )
    for seed in range(1, 5):
        for lineage_id in range(1, 5):
            rows.append(
                _founder_row(
                    hazard=12,
                    seed=seed,
                    lineage_id=lineage_id,
                    is_winner=False,
                    overrides={"metabolic_rate": 1.0 + seed * 0.1},
                )
            )
    for hazard in (0, 4, 8):
        for seed in range(1, 5):
            for lineage_id in range(5):
                rows.append(
                    _founder_row(
                        hazard=hazard,
                        seed=seed,
                        lineage_id=lineage_id,
                        is_winner=lineage_id == 0,
                    )
                )
    wvn = tr.aggregate_winner_vs_nonwinner(rows)
    metab_h12 = next(r for r in wvn if r.trait == "metabolic_rate" and r.hazard == 12)
    assert metab_h12.expected_sign == -1
    assert metab_h12.signed_d > 0
    assert metab_h12.sign_aligned is False


def test_aggregate_winner_vs_nonwinner_includes_secondary_traits() -> None:
    rows = [_founder_row(hazard=0, seed=1, lineage_id=lid, is_winner=lid == 0) for lid in range(5)]
    for hazard in (4, 8, 12):
        for lid in range(5):
            rows.append(_founder_row(hazard=hazard, seed=1, lineage_id=lid, is_winner=lid == 0))
    wvn = tr.aggregate_winner_vs_nonwinner(rows)
    secondary_traits_present = {r.trait for r in wvn if not r.is_primary}
    assert secondary_traits_present == set(tr.SECONDARY_TRAITS)
    # Secondary traits never have sign_aligned=True (always False by spec).
    for r in wvn:
        if not r.is_primary:
            assert r.sign_aligned is False


# ---------------------------------------------------------------------------
# End-to-end on tmp_path corpus + v0.34 helper imports
# ---------------------------------------------------------------------------


def _seed_run(
    run_dir: Path,
    *,
    seed: int,
    hazard: int,
    n_ticks: int = 200,
    founder_traits: list[dict[str, float]] | None = None,
    descendant_lineage: int = 2,
    n_post50_descendants: int = 6,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(
        json.dumps({"world": {"seed": seed, "hazard_damage_default": hazard}})
    )
    (run_dir / "manifest.json").write_text(json.dumps({"ticks_completed": n_ticks}))

    # agent_lifetimes.csv: 5 founders + N post-50 descendants of `descendant_lineage`.
    with (run_dir / "agent_lifetimes.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "agent_id",
                "lineage_id",
                "parent_id",
                "birth_tick",
                "death_tick",
                "death_cause",
                "offspring_count",
            ]
        )
        next_id = 1
        for lineage_id in range(5):
            writer.writerow([next_id, lineage_id, "", "", "", "", 0])
            next_id += 1
        descendant_parent_id = descendant_lineage + 1
        for _ in range(n_post50_descendants):
            writer.writerow([next_id, descendant_lineage, descendant_parent_id, 100, "", "", 0])
            next_id += 1

    # trait_fingerprints.csv covering 5 founders + descendants.
    cols = [
        "agent_id",
        "parent_id",
        "lineage_id",
        "birth_tick",
        "spawn_x",
        "spawn_y",
        *tr.ALL_TRAITS,
    ]
    with (run_dir / "trait_fingerprints.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        defaults = founder_traits or [{trait: 1.0 for trait in tr.ALL_TRAITS}] * 5
        next_id = 1
        for lineage_id in range(5):
            base = {
                "agent_id": str(next_id),
                "parent_id": "",
                "lineage_id": str(lineage_id),
                "birth_tick": "0",
                "spawn_x": "1",
                "spawn_y": "0",
            }
            traits = defaults[lineage_id]
            for trait in tr.ALL_TRAITS:
                base[trait] = str(traits.get(trait, 1.0))
            writer.writerow(base)
            next_id += 1
        for _ in range(n_post50_descendants):
            base = {
                "agent_id": str(next_id),
                "parent_id": str(descendant_parent_id),
                "lineage_id": str(descendant_lineage),
                "birth_tick": "100",
                "spawn_x": "1",
                "spawn_y": "0",
            }
            for trait in tr.ALL_TRAITS:
                base[trait] = str(defaults[descendant_lineage].get(trait, 1.0))
            writer.writerow(base)
            next_id += 1


def test_load_run_round_trip_assigns_winner_correctly(tmp_path) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _seed_run(run_dir, seed=1, hazard=0, descendant_lineage=2)
    agent_rows, trait_lookup, derived_top = tr.load_run(
        "v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir
    )
    assert derived_top == 2
    founder_rows = tr.build_founder_trait_rows(
        agent_rows,
        trait_lookup,
        derived_top,
        source_version="v0.test",
        arm_label="transfer-1500-hzd0-influx-1.0",
        hazard=0,
        seed=1,
    )
    winners = [r for r in founder_rows if r.is_winner]
    assert len(winners) == 1
    assert winners[0].lineage_id == 2
