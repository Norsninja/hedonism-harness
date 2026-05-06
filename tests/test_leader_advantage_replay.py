"""Tests for the v0.38 leader post-50 reproductive advantage reducer
(``scripts/leader_advantage_replay.py``).

Synthetic-fixture coverage of the contract committed in
[[docs/experiments/fear_hunger_v0.38.md]]:

  - Per-lineage b50: founder-only run; founder + post-50 descendants;
    founder + pre-50-only descendants (b50 = 0).
  - leader_advantage: wad=True; wad=False; leader has b50=0 (negative
    advantage); all-equal b50 (advantage = 0).
  - winner_overtake: wad=True returns 0; wad=False positive; winner
    is None returns 0.
  - Indicator rules: monotone-up + spread-up;
    monotone-up + spread-fail; monotone-down + reverse-spread;
    non-monotone; all-equal (neither direction fires).
  - Three-way verdict: H5 / H6 / H7 fire under their pre-committed
    indicator states.
  - Re-anchor halt: v0.34 mismatch, v0.35 leader-column mismatch,
    v0.35 winner-column mismatch, missing anchor.
  - Anchor loader round-trip + halt-on-missing-file.
  - Substrate-immutability: byte-identity of imported v0.34 / v0.35
    constants and helpers; B_POOL_ANCHORS + EXPECTED_FOUNDERS
    re-assertion.
  - End-to-end on a tmp_path 1-run synthetic corpus.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_LAR_PATH = Path(__file__).parent.parent / "scripts" / "leader_advantage_replay.py"
_spec = importlib.util.spec_from_file_location("leader_advantage_replay", _LAR_PATH)
assert _spec is not None
assert _spec.loader is not None
lar = importlib.util.module_from_spec(_spec)
sys.modules["leader_advantage_replay"] = lar
_spec.loader.exec_module(lar)
lr = lar.lr
ls = lar.ls


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent(
    *,
    agent_id: int,
    lineage_id: int,
    parent_id: int | None,
    birth_tick_normalized: int,
    death_tick: int | None,
    born_after_tick_50: bool | None = None,
    survived_to_end: bool | None = None,
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
        born_after_tick_50=(
            (birth_tick_normalized > 50) if born_after_tick_50 is None else born_after_tick_50
        ),
        survived_to_end=((death_tick is None) if survived_to_end is None else survived_to_end),
    )


def _five_founders() -> list[lr.AgentRow]:
    return [
        _agent(
            agent_id=lineage_id + 1,
            lineage_id=lineage_id,
            parent_id=None,
            birth_tick_normalized=0,
            death_tick=None,
        )
        for lineage_id in range(5)
    ]


# ---------------------------------------------------------------------------
# Substrate immutability / locked constants
# ---------------------------------------------------------------------------


def test_v0_34_constants_match() -> None:
    assert lr.EXPECTED_FOUNDERS == 5
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}
    assert lr.HAZARDS == (0, 4, 8, 12)


def test_v0_35_helpers_imported() -> None:
    assert hasattr(ls, "compute_leader_at_tick_50")
    assert hasattr(ls, "compute_eventual_top_lineage")
    assert hasattr(ls, "is_weak_monotone_non_increasing")
    assert hasattr(ls, "is_weak_monotone_non_decreasing")
    assert hasattr(ls, "load_run_agents")


def test_reassert_b_pool_anchors_passes_on_unmodified_v0_34() -> None:
    lar.reassert_b_pool_anchors()


def test_v0_38_locked_thresholds_and_phrases() -> None:
    assert lar.LEADER_TICK == 50
    assert lar.O1_SPREAD_THRESHOLD == 1.5
    assert lar.N_NON_LEADERS == 4
    assert lar.EXPECTED_N_TICKS == 200
    assert "rises with hazard" in lar.LOCKED_H5_PHRASE
    assert "does not strengthen with hazard" in lar.LOCKED_H6_PHRASE
    assert "decreases with hazard" in lar.LOCKED_H7_PHRASE


# ---------------------------------------------------------------------------
# per_lineage_b50
# ---------------------------------------------------------------------------


def test_per_lineage_b50_founder_only_run_yields_zeros() -> None:
    rows = _five_founders()
    b50 = lar.per_lineage_b50(rows)
    assert b50 == {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}


def test_per_lineage_b50_counts_post_50_descendants_only() -> None:
    rows = _five_founders()
    rows.append(
        _agent(
            agent_id=10,
            lineage_id=2,
            parent_id=3,
            birth_tick_normalized=60,
            death_tick=None,
            born_after_tick_50=True,
        )
    )
    rows.append(
        _agent(
            agent_id=11,
            lineage_id=2,
            parent_id=3,
            birth_tick_normalized=70,
            death_tick=None,
            born_after_tick_50=True,
        )
    )
    rows.append(
        _agent(
            agent_id=12,
            lineage_id=2,
            parent_id=3,
            birth_tick_normalized=30,
            death_tick=None,
            born_after_tick_50=False,
        )
    )
    b50 = lar.per_lineage_b50(rows)
    assert b50[2] == 2  # only the two post-50 descendants count
    assert b50[0] == 0
    assert b50[1] == 0
    assert b50[3] == 0
    assert b50[4] == 0


def test_per_lineage_b50_pre_50_descendants_do_not_count() -> None:
    rows = _five_founders()
    for tick in (10, 20, 30, 40, 50):
        rows.append(
            _agent(
                agent_id=20 + tick,
                lineage_id=1,
                parent_id=2,
                birth_tick_normalized=tick,
                death_tick=None,
                born_after_tick_50=False,
            )
        )
    b50 = lar.per_lineage_b50(rows)
    assert b50[1] == 0


# ---------------------------------------------------------------------------
# compute_leader_advantage
# ---------------------------------------------------------------------------


def test_compute_leader_advantage_clean_case() -> None:
    b50 = {0: 0, 1: 1, 2: 5, 3: 0, 4: 2}
    leader_b50, non_leader_mean, adv = lar.compute_leader_advantage(b50, leader_id=2)
    assert leader_b50 == 5
    assert non_leader_mean == pytest.approx((0 + 1 + 0 + 2) / 4)
    assert adv == pytest.approx(5 - 0.75)


def test_compute_leader_advantage_negative_when_leader_underperforms() -> None:
    """Leader has b50=0 but non-leaders average 2.5 -> negative advantage."""
    b50 = {0: 0, 1: 4, 2: 3, 3: 2, 4: 1}
    leader_b50, non_leader_mean, adv = lar.compute_leader_advantage(b50, leader_id=0)
    assert leader_b50 == 0
    assert non_leader_mean == pytest.approx(2.5)
    assert adv == pytest.approx(-2.5)


def test_compute_leader_advantage_zero_when_all_equal() -> None:
    b50 = {0: 3, 1: 3, 2: 3, 3: 3, 4: 3}
    _, _, adv = lar.compute_leader_advantage(b50, leader_id=0)
    assert adv == pytest.approx(0.0)


def test_compute_leader_advantage_halts_with_single_lineage() -> None:
    b50 = {0: 5}
    with pytest.raises(lr.LineageReplayError, match="no non-leader lineages"):
        lar.compute_leader_advantage(b50, leader_id=0)


# ---------------------------------------------------------------------------
# compute_winner_overtake
# ---------------------------------------------------------------------------


def test_winner_overtake_zero_when_wad_true() -> None:
    b50 = {0: 1, 1: 0, 2: 5, 3: 0, 4: 0}
    w_b50, overtake = lar.compute_winner_overtake(b50, leader_id=2, winner_id=2, wad=True)
    assert w_b50 == 5
    assert overtake == 0


def test_winner_overtake_positive_when_wad_false() -> None:
    """Leader=2 has b50=4; winner=4 has b50=7 -> overtake = +3."""
    b50 = {0: 0, 1: 0, 2: 4, 3: 0, 4: 7}
    w_b50, overtake = lar.compute_winner_overtake(b50, leader_id=2, winner_id=4, wad=False)
    assert w_b50 == 7
    assert overtake == 3


def test_winner_overtake_zero_when_no_winner() -> None:
    b50 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    w_b50, overtake = lar.compute_winner_overtake(b50, leader_id=0, winner_id=None, wad=False)
    assert w_b50 == 0
    assert overtake == 0


# ---------------------------------------------------------------------------
# Indicator rules
# ---------------------------------------------------------------------------


def _per_hazard(o1_means: tuple[float, float, float, float]) -> list[lar.PerHazardRow]:
    return [
        lar.PerHazardRow(
            hazard=h,
            n_runs=24,
            n_wad_true=12,
            n_wad_false=12,
            n_no_winner=0,
            mean_o1=o1_means[i],
            mean_o1_wad_true=o1_means[i],
            mean_o1_wad_false=0.0,
            mean_winner_overtake_wad_false=0.0,
        )
        for i, h in enumerate((0, 4, 8, 12))
    ]


def test_indicator_passes_up_when_monotone_increasing_and_spread_meets_threshold() -> None:
    indicator = lar.evaluate_indicator(_per_hazard((1.0, 1.5, 2.0, 3.0)))
    assert indicator.monotone_pass_up is True
    assert indicator.threshold_passes_up is True
    assert indicator.indicator_passes is True
    assert indicator.verdict_direction == "up"


def test_indicator_fails_up_when_spread_under_threshold() -> None:
    """Monotone increasing but spread = 1.0 < 1.5."""
    indicator = lar.evaluate_indicator(_per_hazard((1.0, 1.3, 1.7, 2.0)))
    assert indicator.monotone_pass_up is True
    assert indicator.threshold_passes_up is False
    assert indicator.indicator_passes is False
    assert indicator.verdict_direction == "none"


def test_indicator_passes_down_when_monotone_decreasing_and_reverse_spread_meets_threshold() -> (
    None
):
    indicator = lar.evaluate_indicator(_per_hazard((5.0, 4.0, 3.5, 2.0)))
    assert indicator.monotone_pass_down is True
    assert indicator.threshold_passes_down is True
    assert indicator.indicator_passes is True
    assert indicator.verdict_direction == "down"


def test_indicator_fails_when_non_monotone() -> None:
    """h=4 mean drops below h=0; h=8 rises above h=4 -> non-monotone in either direction."""
    indicator = lar.evaluate_indicator(_per_hazard((3.0, 1.0, 5.0, 2.0)))
    assert indicator.monotone_pass_up is False
    assert indicator.monotone_pass_down is False
    assert indicator.indicator_passes is False
    assert indicator.verdict_direction == "none"


def test_indicator_fails_when_all_equal() -> None:
    """All-equal sequence is technically both monotone-up and monotone-down,
    but spread = 0 fails both threshold rules."""
    indicator = lar.evaluate_indicator(_per_hazard((4.0, 4.0, 4.0, 4.0)))
    assert indicator.monotone_pass_up is True
    assert indicator.monotone_pass_down is True
    assert indicator.threshold_passes_up is False
    assert indicator.threshold_passes_down is False
    assert indicator.indicator_passes is False
    assert indicator.verdict_direction == "none"


# ---------------------------------------------------------------------------
# Three-way verdict
# ---------------------------------------------------------------------------


def _indicator(direction: str) -> lar.IndicatorSummaryRow:
    return lar.IndicatorSummaryRow(
        observable="O1",
        verdict_role="driver",
        monotone_pass_up=(direction == "up"),
        monotone_pass_down=(direction == "down"),
        spread_value=2.0 if direction == "up" else (-2.0 if direction == "down" else 0.0),
        spread_threshold=lar.O1_SPREAD_THRESHOLD,
        threshold_passes_up=(direction == "up"),
        threshold_passes_down=(direction == "down"),
        indicator_passes=(direction in ("up", "down")),
        verdict_direction=direction,
    )


def test_verdict_h5_amplified_when_indicator_up() -> None:
    verdict, phrase, firing = lar.evaluate_verdict(_indicator("up"))
    assert verdict == lar.VERDICT_AMPLIFIED
    assert phrase == lar.LOCKED_H5_PHRASE
    assert firing == "O1_up"


def test_verdict_h6_flat_when_indicator_none() -> None:
    verdict, phrase, firing = lar.evaluate_verdict(_indicator("none"))
    assert verdict == lar.VERDICT_FLAT
    assert phrase == lar.LOCKED_H6_PHRASE
    assert firing == ""


def test_verdict_h7_inverted_when_indicator_down() -> None:
    verdict, phrase, firing = lar.evaluate_verdict(_indicator("down"))
    assert verdict == lar.VERDICT_INVERTED
    assert phrase == lar.LOCKED_H7_PHRASE
    assert firing == "O1_down"


# ---------------------------------------------------------------------------
# Re-anchor halt
# ---------------------------------------------------------------------------


def test_cross_check_passes_on_match() -> None:
    derived = {("vX", "arm-0", 1): (2, 4)}
    v34 = {("vX", "arm-0", 1): 4}
    v35 = {("vX", "arm-0", 1): (2, 4)}
    lar.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_v0_34_top_mismatch() -> None:
    derived = {("vX", "arm-0", 1): (2, 4)}
    v34 = {("vX", "arm-0", 1): 3}  # winner mismatch
    v35 = {("vX", "arm-0", 1): (2, 4)}
    with pytest.raises(lr.LineageReplayError, match=r"H2a v0\.34 re-anchor mismatch"):
        lar.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_v0_35_leader_mismatch() -> None:
    derived = {("vX", "arm-0", 1): (2, 4)}
    v34 = {("vX", "arm-0", 1): 4}
    v35 = {("vX", "arm-0", 1): (3, 4)}  # leader mismatch
    with pytest.raises(lr.LineageReplayError, match=r"H2b v0\.35 leader re-anchor mismatch"):
        lar.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_v0_35_winner_mismatch() -> None:
    derived = {("vX", "arm-0", 1): (2, 4)}
    v34 = {("vX", "arm-0", 1): 4}
    v35 = {("vX", "arm-0", 1): (2, 1)}  # winner mismatch
    with pytest.raises(lr.LineageReplayError, match=r"H2b v0\.35 winner re-anchor mismatch"):
        lar.cross_check_double_anchor(derived, v34, v35)


def test_cross_check_halts_on_missing_v0_34_anchor() -> None:
    derived = {("vX", "arm-0", 1): (2, 4)}
    v34: dict[tuple[str, str, int], int | None] = {}  # missing
    v35 = {("vX", "arm-0", 1): (2, 4)}
    with pytest.raises(lr.LineageReplayError, match=r"v0\.34 anchor missing"):
        lar.cross_check_double_anchor(derived, v34, v35)


def test_load_v0_35_anchors_round_trip(tmp_path) -> None:
    path = tmp_path / "pre_post_dominance.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "source_version",
                "arm_label",
                "hazard",
                "seed",
                "leader_lineage_id_at_tick_50",
                "leader_births_at_tick_50",
                "eventual_top_lineage_id",
                "eventual_top_b50",
                "winner_already_dominant_at_tick_50",
                "n_lineages_with_post50_birth",
            ]
        )
        writer.writerow(["vX", "arm-0", 0, 1, 2, 1, 4, 7, "False", 2])
        writer.writerow(["vX", "arm-0", 0, 2, 0, 1, "", "", "", 0])
    anchors = lar.load_v0_35_anchors(path)
    assert anchors[("vX", "arm-0", 1)] == (2, 4)
    assert anchors[("vX", "arm-0", 2)] == (0, None)


def test_load_v0_34_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match=r"v0\.34 run_summary\.csv missing"):
        lar.load_v0_34_anchors(tmp_path / "does-not-exist.csv")


def test_load_v0_35_anchors_halts_on_missing_file(tmp_path) -> None:
    with pytest.raises(lr.LineageReplayError, match=r"v0\.35 pre_post_dominance\.csv missing"):
        lar.load_v0_35_anchors(tmp_path / "does-not-exist.csv")


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def test_aggregate_per_hazard_means_match_synthetic_corpus() -> None:
    """Build a small per-run list and check aggregations are arithmetic means."""
    per_run: list[lar.PerRunRow] = []
    for hazard in (0, 4, 8, 12):
        for seed in (1, 2):
            wad = seed == 1
            per_run.append(
                lar.PerRunRow(
                    source_version="vX",
                    arm_label=f"arm-{hazard}",
                    hazard=hazard,
                    seed=seed,
                    n_ticks=200,
                    leader_lineage_id=2,
                    eventual_top_lineage_id=2 if wad else 4,
                    wad_flag=wad,
                    b50_lineage_0=0,
                    b50_lineage_1=0,
                    b50_lineage_2=4,
                    b50_lineage_3=0,
                    b50_lineage_4=0 if wad else 6,
                    leader_b50=4,
                    non_leader_mean_b50=0.0 if wad else 1.5,
                    leader_advantage=4.0 if wad else 2.5,
                    winner_b50=4 if wad else 6,
                    winner_overtake=0 if wad else 2,
                )
            )
    summary = lar.aggregate_per_hazard(per_run)
    by_hazard = {row.hazard: row for row in summary}
    for hazard in (0, 4, 8, 12):
        row = by_hazard[hazard]
        assert row.n_runs == 2
        assert row.n_wad_true == 1
        assert row.n_wad_false == 1
        assert row.mean_o1 == pytest.approx((4.0 + 2.5) / 2)
        assert row.mean_o1_wad_true == pytest.approx(4.0)
        assert row.mean_o1_wad_false == pytest.approx(2.5)
        assert row.mean_winner_overtake_wad_false == pytest.approx(2.0)


def test_aggregate_per_hazard_handles_empty_wad_subsets() -> None:
    """If a hazard has no wad=False runs, mean_o1_wad_false is nan."""
    import math

    per_run = [
        lar.PerRunRow(
            source_version="vX",
            arm_label="arm-0",
            hazard=0,
            seed=1,
            n_ticks=200,
            leader_lineage_id=2,
            eventual_top_lineage_id=2,
            wad_flag=True,
            b50_lineage_0=0,
            b50_lineage_1=0,
            b50_lineage_2=4,
            b50_lineage_3=0,
            b50_lineage_4=0,
            leader_b50=4,
            non_leader_mean_b50=0.0,
            leader_advantage=4.0,
            winner_b50=4,
            winner_overtake=0,
        ),
    ]
    summary = lar.aggregate_per_hazard(per_run)
    by_hazard = {row.hazard: row for row in summary}
    assert by_hazard[0].n_wad_false == 0
    assert math.isnan(by_hazard[0].mean_o1_wad_false)
    assert math.isnan(by_hazard[0].mean_winner_overtake_wad_false)


# ---------------------------------------------------------------------------
# End-to-end on tmp_path synthetic corpus
# ---------------------------------------------------------------------------


def _write_synthetic_run(
    run_dir: Path,
    *,
    seed: int,
    hazard: int,
    n_ticks: int,
    agents: list[dict],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(
        json.dumps({"world": {"seed": seed, "hazard_damage_default": hazard}})
    )
    (run_dir / "manifest.json").write_text(json.dumps({"ticks_completed": n_ticks}))
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
        for a in agents:
            writer.writerow(
                [
                    a["agent_id"],
                    a.get("lineage_id", ""),
                    a.get("parent_id", "") if a.get("parent_id") is not None else "",
                    a.get("birth_tick", "") if a.get("birth_tick") is not None else "",
                    a.get("death_tick", "") if a.get("death_tick") is not None else "",
                    a.get("death_cause", ""),
                    a.get("offspring_count", 0),
                ]
            )


def _five_founder_run_records(*, dominant_lineage: int) -> list[dict]:
    """5 founders + 6 post-50 descendants of `dominant_lineage`. The dominant
    lineage is BOTH the tick-50 leader (because its descendants are born at
    tick 100, after tick 50, so at tick 50 all founders are tied at 1 and
    the lowest lineage_id wins tie-break) AND the eventual winner."""
    records: list[dict] = []
    next_id = 1
    for lineage_id in range(5):
        records.append(
            {
                "agent_id": next_id,
                "lineage_id": lineage_id,
                "parent_id": None,
                "birth_tick": None,
                "death_tick": None,
                "death_cause": "",
                "offspring_count": 6 if lineage_id == dominant_lineage else 0,
            }
        )
        next_id += 1
    for _ in range(6):
        records.append(
            {
                "agent_id": next_id,
                "lineage_id": dominant_lineage,
                "parent_id": dominant_lineage + 1,
                "birth_tick": 100,
                "death_tick": None,
                "death_cause": "",
                "offspring_count": 0,
            }
        )
        next_id += 1
    return records


def test_summarise_run_end_to_end_dominant_lineage_zero(tmp_path) -> None:
    """When dominant_lineage = 0, leader = winner = 0 (wad=True). Lineage 0
    has 6 post-50 descendants; non-leaders mean is 0; advantage = 6.0."""
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir,
        seed=1,
        hazard=0,
        n_ticks=200,
        agents=_five_founder_run_records(dominant_lineage=0),
    )
    row = lar.summarise_run("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)
    assert row.leader_lineage_id == 0
    assert row.eventual_top_lineage_id == 0
    assert row.wad_flag is True
    assert row.b50_lineage_0 == 6
    assert row.leader_b50 == 6
    assert row.non_leader_mean_b50 == pytest.approx(0.0)
    assert row.leader_advantage == pytest.approx(6.0)
    assert row.winner_overtake == 0


def test_summarise_run_halts_on_n_ticks_drift(tmp_path) -> None:
    run_dir = tmp_path / "v0.test" / "transfer-1500-hzd0-influx-1.0" / "seed-1"
    _write_synthetic_run(
        run_dir,
        seed=1,
        hazard=0,
        n_ticks=150,  # not 200
        agents=_five_founder_run_records(dominant_lineage=2),
    )
    with pytest.raises(lr.LineageReplayError, match=r"H2d n_ticks drift"):
        lar.summarise_run("v0.test", "transfer-1500-hzd0-influx-1.0", 0, 1, run_dir)
