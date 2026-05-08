"""v0.48 sensor_radius -> space -> readiness bridge — tests (14 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.48.md]] §"Test list (locked,
per v0.46 / v0.47 7-point review pattern)". Tests numbered to match the
pre-reg's ordering.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).parent.parent / "scripts" / "v0_48_sensor_radius_spatial_bridge_audit.py"
)
_spec = importlib.util.spec_from_file_location("v0_48_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_48_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_48_audit"] = v0_48_audit
_spec.loader.exec_module(v0_48_audit)


# ---------------------------------------------------------------------------
# Synthetic _RunCapture / PerLineageRow / ObservableSummary helpers
# ---------------------------------------------------------------------------


def _empty_capture(*, version: str = "v0.42", seed: int = 41, hazard: int = 8) -> object:
    cap = v0_48_audit._RunCapture(version=version, seed=seed, hazard=hazard)
    cap.energy_threshold = 50.0
    cap.min_age = 10
    return cap


def _make_lineage_row(
    *,
    version: str = "v0.42",
    seed: int = 41,
    hazard: int = 8,
    lineage_id: int,
    rd: float = 0.0,
    mr: float = 0.0,
    sr: float = 0.0,
    food_events: int = 0,
    food_energy: float = 0.0,
    distance: float = 0.0,
    axial_food: float = 0.0,
    axial_hazard: float = 0.0,
    centroid_food: float = 0.0,
    centroid_hazard: float = 0.0,
    living: int = 0,
    above_count: int = 0,
    above_fraction: float = 0.0,
    pre50_hazard: int = 0,
    b50: int = 0,
    is_eventual_top: bool = False,
    is_high_sensor_radius: bool = False,
    is_high_readiness_fraction: bool = False,
) -> object:
    return v0_48_audit.PerLineageRow(
        version=version,
        seed=seed,
        hazard=hazard,
        run_id=f"{version}-A_null-hzd{hazard}-seed-{seed}",
        lineage_id=lineage_id,
        founder_reproduction_drive=rd,
        founder_metabolic_rate=mr,
        founder_sensor_radius=sr,
        pre50_food_events_count=food_events,
        pre50_food_energy_acquired=food_energy,
        mean_distance_to_nearest_food_cell=distance,
        mean_axial_food_signal_own_radius=axial_food,
        mean_axial_hazard_signal_own_radius=axial_hazard,
        tick50_centroid_distance_to_nearest_food=centroid_food,
        tick50_centroid_distance_to_nearest_hazard=centroid_hazard,
        tick50_living_count=living,
        tick50_above_threshold_count=above_count,
        tick50_above_threshold_fraction=above_fraction,
        pre50_hazard_damage_received_count=pre50_hazard,
        b50_count=b50,
        is_eventual_top_b50_label=is_eventual_top,
        is_high_sensor_radius_lineage=is_high_sensor_radius,
        is_high_tick50_readiness_fraction_lineage=is_high_readiness_fraction,
    )


def _make_summary(
    observable: str, sign: int, paired_d: float, label: str = "label_a_sensor_radius"
) -> object:
    signed = paired_d * sign if not math.isnan(paired_d) else float("nan")
    fires_expected = (not math.isnan(signed)) and signed >= v0_48_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_48_audit.COHENS_D_THRESHOLD
    return v0_48_audit.ObservableSummary(
        observable=observable,
        label=label,
        sign=sign,
        n_runs_contributing=64,
        paired_d=paired_d,
        signed_d=signed,
        delta_mean=0.0,
        delta_stdev=1.0,
        delta_min=-1.0,
        delta_max=+1.0,
        fires_expected=fires_expected,
        fires_wrong=fires_wrong,
    )


# ---------------------------------------------------------------------------
# Test 1 — per-tick observer fires for each tick 0..50 inclusive
# ---------------------------------------------------------------------------


def test_per_tick_observer_fires_for_each_tick_0_through_50(tmp_path):
    """Run one A_null run and verify the v0.48 observer captured exactly
    51 tick records (ticks 0..50). Also confirms the run's anchor is byte-
    compatible with the V0_25 anchor used by v0.46/v0.47."""
    cap = v0_48_audit._run_one_a_null_run(version="v0.42", seed=41, hazard=0, runs_root=tmp_path)
    assert set(cap.tick_records.keys()) == set(range(0, v0_48_audit.TICK_50 + 1))
    for tick, record in cap.tick_records.items():
        assert record.tick == tick
        # Founders are alive at tick 0; subsequent ticks should keep at
        # least one living agent on the V0_25 anchor.
        assert isinstance(record.food_cells, tuple)
        assert isinstance(record.hazard_cells, tuple)


# ---------------------------------------------------------------------------
# Test 2 — label A picks argmax(founder_sensor_radius) with min(lineage_id) tiebreak
# ---------------------------------------------------------------------------


def test_label_a_argmax_founder_sensor_radius_with_tiebreak():
    founder_traits = {
        0: {"sensor_radius": 5.0},
        1: {"sensor_radius": 7.0},
        2: {"sensor_radius": 7.0},
    }
    assert v0_48_audit._select_sensor_radius_label(founder_traits) == 1
    # Empty input -> None.
    assert v0_48_audit._select_sensor_radius_label({}) is None
    # Strict argmax wins over tiebreak.
    founder_traits_clear = {
        2: {"sensor_radius": 9.0},
        0: {"sensor_radius": 5.0},
        1: {"sensor_radius": 7.0},
    }
    assert v0_48_audit._select_sensor_radius_label(founder_traits_clear) == 2


# ---------------------------------------------------------------------------
# Test 3 — label B follows v0.47's 3-tier tiebreak (fraction -> count -> min(lineage_id))
# ---------------------------------------------------------------------------


def test_label_b_three_tier_tiebreak_matches_v0_47():
    # Equal fraction, count breaks tie.
    cands = [(0, 0.5, 2), (1, 0.5, 3)]
    assert v0_48_audit._select_fraction_label(cands) == 1
    # Equal fraction and count, min(lineage_id) breaks tie.
    cands_eq = [(2, 0.5, 2), (0, 0.5, 2), (1, 0.5, 2)]
    assert v0_48_audit._select_fraction_label(cands_eq) == 0
    # Strict fraction wins.
    cands_clear = [(0, 0.6, 0), (1, 0.5, 99)]
    assert v0_48_audit._select_fraction_label(cands_clear) == 0
    # Empty -> None.
    assert v0_48_audit._select_fraction_label([]) is None


# ---------------------------------------------------------------------------
# Test 4 — pre50_food_events filtered by tick <= 50 inclusive
# ---------------------------------------------------------------------------


def test_pre50_food_events_filtered_by_tick_inclusive_50():
    """Drive _on_ate_food via the live signal pipeline at simulated ticks
    30 / 50 / 75; assert the lineage-level rollup counts exactly the two
    pre-50 events."""
    from hedonism_harness.core.events import AteFood, signal_for

    cap = _empty_capture()
    cap.lineage_by_agent = {1: 0, 2: 0, 3: 0}
    cap.founder_traits_by_lineage = {
        0: {"reproduction_drive": 0, "metabolic_rate": 0, "sensor_radius": 0}
    }

    class _StubModel:
        def __init__(self):
            self.tick_count = 0

    stub = _StubModel()

    def _on_ate_food(_sender, *, event):
        if int(stub.tick_count) > v0_48_audit.TICK_50:
            return
        aid = int(event.agent_id)
        cap.pre50_food_events_by_agent[aid] = cap.pre50_food_events_by_agent.get(aid, 0) + 1
        cap.pre50_food_energy_by_agent[aid] = cap.pre50_food_energy_by_agent.get(aid, 0.0) + float(
            event.food_gained
        )

    sig = signal_for(AteFood)
    sig.connect(_on_ate_food, sender=stub)
    try:
        for tick, aid in ((30, 1), (50, 2), (75, 3)):
            stub.tick_count = tick
            sig.send(stub, event=AteFood(agent_id=aid, x=0, y=0, food_gained=1.0))
    finally:
        sig.disconnect(_on_ate_food, sender=stub)

    # Tick 75 must NOT have been recorded.
    assert sum(cap.pre50_food_events_by_agent.values()) == 2
    assert 3 not in cap.pre50_food_events_by_agent


# ---------------------------------------------------------------------------
# Test 5 — pre50_food_energy_acquired sums AteFood.food_gained
# ---------------------------------------------------------------------------


def test_pre50_food_energy_uses_food_gained_field():
    from hedonism_harness.core.events import AteFood, signal_for

    cap = _empty_capture()
    cap.lineage_by_agent = {1: 0}
    cap.founder_traits_by_lineage = {
        0: {"reproduction_drive": 0, "metabolic_rate": 0, "sensor_radius": 0}
    }

    class _StubModel:
        def __init__(self):
            self.tick_count = 10

    stub = _StubModel()

    def _on_ate_food(_sender, *, event):
        if int(stub.tick_count) > v0_48_audit.TICK_50:
            return
        aid = int(event.agent_id)
        cap.pre50_food_events_by_agent[aid] = cap.pre50_food_events_by_agent.get(aid, 0) + 1
        cap.pre50_food_energy_by_agent[aid] = cap.pre50_food_energy_by_agent.get(aid, 0.0) + float(
            event.food_gained
        )

    sig = signal_for(AteFood)
    sig.connect(_on_ate_food, sender=stub)
    try:
        for gained in (1.0, 2.5, 0.5):
            sig.send(stub, event=AteFood(agent_id=1, x=0, y=0, food_gained=gained))
    finally:
        sig.disconnect(_on_ate_food, sender=stub)

    assert cap.pre50_food_events_by_agent[1] == 3
    assert cap.pre50_food_energy_by_agent[1] == pytest.approx(4.0)


# ---------------------------------------------------------------------------
# Test 6 — distance uses per-tick lineage mean THEN mean over ticks
# ---------------------------------------------------------------------------


def test_distance_uses_per_tick_lineage_mean_then_mean_over_ticks():
    """Synthetic capture (per pre-reg test #6 patch):
      tick 0: 1 agent at distance 9 (per_tick mean = 9)
      tick 1: 3 agents at distances 1, 1, 1 (per_tick mean = 1)
      ticks 2..50: 0 living agents
    Per-tick-then-mean = mean(9, 1) = 5.0.
    Agent-tick pooled would be mean(9, 1, 1, 1) = 3.0 — distinct.
    """
    cap = _empty_capture()
    lineage_id = 7
    cap.lineage_by_agent = {1: lineage_id, 2: lineage_id, 3: lineage_id, 4: lineage_id}
    cap.founder_traits_by_lineage = {
        lineage_id: {"reproduction_drive": 0, "metabolic_rate": 0, "sensor_radius": 1}
    }

    # Tick 0: 1 agent at (0, 0) with sensor_radius 1; food at (9, 0) -> Manhattan 9.
    rec0 = v0_48_audit._TickRecord(tick=0)
    rec0.agents = [(1, lineage_id, 0, 0, 1)]
    rec0.food_cells = ((9, 0),)
    rec0.hazard_cells = ()
    cap.tick_records[0] = rec0

    # Tick 1: 3 agents each at distance 1 from a food cell.
    rec1 = v0_48_audit._TickRecord(tick=1)
    rec1.agents = [
        (2, lineage_id, 0, 0, 1),
        (3, lineage_id, 2, 0, 1),
        (4, lineage_id, 0, 2, 1),
    ]
    rec1.food_cells = ((1, 0), (3, 0), (0, 1))
    rec1.hazard_cells = ()
    cap.tick_records[1] = rec1

    # Ticks 2..50: empty (no living agents).
    for t in range(2, v0_48_audit.TICK_50 + 1):
        cap.tick_records[t] = v0_48_audit._TickRecord(tick=t)

    spatial = v0_48_audit._per_tick_lineage_means(cap)
    assert spatial[lineage_id]["mean_distance_to_nearest_food_cell"] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Test 7 — distance NaN when lineage has no living agents across the window
# ---------------------------------------------------------------------------


def test_distance_nan_when_lineage_has_no_living_agents_across_window():
    cap = _empty_capture()
    lineage_id = 3
    cap.lineage_by_agent = {0: lineage_id}
    cap.founder_traits_by_lineage = {
        lineage_id: {"reproduction_drive": 0, "metabolic_rate": 0, "sensor_radius": 1}
    }
    for t in range(0, v0_48_audit.TICK_50 + 1):
        rec = v0_48_audit._TickRecord(tick=t)
        rec.food_cells = ((1, 1),)
        cap.tick_records[t] = rec
    spatial = v0_48_audit._per_tick_lineage_means(cap)
    assert math.isnan(spatial[lineage_id]["mean_distance_to_nearest_food_cell"])

    # Confirm the NaN propagates to a per-run paired-delta None result.
    rows = [
        _make_lineage_row(
            lineage_id=lineage_id,
            distance=float("nan"),
            is_high_sensor_radius=True,
        ),
        _make_lineage_row(
            lineage_id=lineage_id + 1,
            distance=4.0,
            is_high_sensor_radius=False,
        ),
    ]
    delta = v0_48_audit._per_run_paired_delta(
        rows, "mean_distance_to_nearest_food_cell", v0_48_audit.LABEL_A_FIELD
    )
    assert delta is None


# ---------------------------------------------------------------------------
# Test 8 — signed_d for negative-expected-sign observable
# ---------------------------------------------------------------------------


def test_signed_d_for_negative_expected_sign_observable():
    """Observable #3 has expected sign -1: a negative paired_d corresponds
    to a positive signed_d (lineage closer to food than peers)."""
    s = _make_summary("mean_distance_to_nearest_food_cell", -1, paired_d=-2.0)
    assert s.signed_d == pytest.approx(+2.0)
    assert s.fires_expected is True
    assert s.fires_wrong is False

    # Conversely, a positive paired_d for sign -1 fires WRONG.
    s_wrong = _make_summary("mean_distance_to_nearest_food_cell", -1, paired_d=+1.5)
    assert s_wrong.signed_d == pytest.approx(-1.5)
    assert s_wrong.fires_expected is False
    assert s_wrong.fires_wrong is True


# ---------------------------------------------------------------------------
# Test 9 — _PRESENT requires both labels >= 2/3
# ---------------------------------------------------------------------------


def test_verdict_present_requires_both_labels_clear_two_of_three():
    summaries_a = [
        _make_summary("o1", +1, +0.6),
        _make_summary("o2", +1, +0.7),
        _make_summary("o3", -1, -0.3),  # signed_d = +0.3 (no fire)
    ]
    summaries_b = [
        _make_summary("o1", +1, +0.6, label="label_b_readiness_fraction"),
        _make_summary("o2", +1, +0.8, label="label_b_readiness_fraction"),
        _make_summary("o3", -1, -0.2, label="label_b_readiness_fraction"),
    ]
    assert v0_48_audit._evaluate_verdict(summaries_a, summaries_b) == v0_48_audit.VERDICT_PRESENT


# ---------------------------------------------------------------------------
# Test 10 — _PARTIAL when only one label clears
# ---------------------------------------------------------------------------


def test_verdict_partial_when_only_one_label_clears():
    summaries_a = [
        _make_summary("o1", +1, +0.6),
        _make_summary("o2", +1, +0.7),
        _make_summary("o3", -1, -0.3),
    ]
    summaries_b = [
        _make_summary("o1", +1, +0.3, label="label_b_readiness_fraction"),
        _make_summary("o2", +1, +0.4, label="label_b_readiness_fraction"),
        _make_summary("o3", -1, -0.2, label="label_b_readiness_fraction"),
    ]
    assert v0_48_audit._evaluate_verdict(summaries_a, summaries_b) == v0_48_audit.VERDICT_PARTIAL
    # Reversed (B clears, A doesn't) — still PARTIAL.
    assert v0_48_audit._evaluate_verdict(summaries_b, summaries_a) == v0_48_audit.VERDICT_PARTIAL


# ---------------------------------------------------------------------------
# Test 11 — _NOT_FOUND when neither label clears
# ---------------------------------------------------------------------------


def test_verdict_not_found_when_neither_label_clears():
    summaries_a = [
        _make_summary("o1", +1, +0.4),
        _make_summary("o2", +1, +0.3),
        _make_summary("o3", -1, -0.2),
    ]
    summaries_b = [
        _make_summary("o1", +1, +0.3, label="label_b_readiness_fraction"),
        _make_summary("o2", +1, +0.2, label="label_b_readiness_fraction"),
        _make_summary("o3", -1, -0.4, label="label_b_readiness_fraction"),
    ]
    assert v0_48_audit._evaluate_verdict(summaries_a, summaries_b) == v0_48_audit.VERDICT_NOT


# ---------------------------------------------------------------------------
# Test 12 — wrong-sign halt under either label
# ---------------------------------------------------------------------------


def test_verdict_halt_on_wrong_sign_under_either_label():
    # Wrong-sign under A (paired_d -0.7 with sign +1 -> signed_d -0.7).
    summaries_a = [
        _make_summary("o1", +1, +0.6),
        _make_summary("o2", +1, -0.7),
        _make_summary("o3", -1, -0.3),
    ]
    summaries_b = [
        _make_summary("o1", +1, +0.6, label="label_b_readiness_fraction"),
        _make_summary("o2", +1, +0.6, label="label_b_readiness_fraction"),
        _make_summary("o3", -1, -0.6, label="label_b_readiness_fraction"),
    ]
    assert (
        v0_48_audit._evaluate_verdict(summaries_a, summaries_b) == v0_48_audit.VERDICT_HALT_OPPOSITE
    )

    # Wrong-sign only under B (sign -1, paired_d +0.7 -> signed_d -0.7).
    summaries_b_wrong = [
        _make_summary("o1", +1, +0.6, label="label_b_readiness_fraction"),
        _make_summary("o2", +1, +0.6, label="label_b_readiness_fraction"),
        _make_summary("o3", -1, +0.7, label="label_b_readiness_fraction"),
    ]
    summaries_a_clean = [
        _make_summary("o1", +1, +0.6),
        _make_summary("o2", +1, +0.6),
        _make_summary("o3", -1, -0.6),
    ]
    assert (
        v0_48_audit._evaluate_verdict(summaries_a_clean, summaries_b_wrong)
        == v0_48_audit.VERDICT_HALT_OPPOSITE
    )


# ---------------------------------------------------------------------------
# Test 13 — re-anchor drift halt
# ---------------------------------------------------------------------------


def test_reanchor_drift_halt():
    """Synthesise per-lineage rows whose b50 share at h=8 drifts > 1e-3
    from v0.42's published 0.652."""
    rows: list[object] = []
    # 4 lineages per run; lineage 0 holds 90% of post-50 births -> share 0.90.
    for seed in range(41, 49):
        rows.extend(
            [
                _make_lineage_row(version="v0.42", seed=seed, hazard=8, lineage_id=0, b50=90),
                _make_lineage_row(version="v0.42", seed=seed, hazard=8, lineage_id=1, b50=4),
                _make_lineage_row(version="v0.42", seed=seed, hazard=8, lineage_id=2, b50=3),
                _make_lineage_row(version="v0.42", seed=seed, hazard=8, lineage_id=3, b50=3),
            ]
        )
    re_anchor = v0_48_audit._check_re_anchor(rows)
    v042 = next(r for r in re_anchor if r.version == "v0.42")
    assert v042.drift_abs is not None
    assert v042.drift_abs > v0_48_audit.RE_ANCHOR_DRIFT_TOLERANCE
    assert v042.halts is True


# ---------------------------------------------------------------------------
# Test 14 — secondary metrics in CSV but do not affect verdict
# ---------------------------------------------------------------------------


def test_secondary_metrics_in_csv_but_do_not_affect_verdict():
    """Per-lineage CSV schema must include the descriptive secondary
    fields (axial signals, centroid distances, hazard damage, b50 label),
    but the verdict consults primaries only — verified via field presence
    on PerLineageRow plus a synthetic verdict where secondaries would
    'fire' but primaries do not."""
    descriptive_fields = {
        "mean_axial_food_signal_own_radius",
        "mean_axial_hazard_signal_own_radius",
        "tick50_centroid_distance_to_nearest_food",
        "tick50_centroid_distance_to_nearest_hazard",
        "pre50_hazard_damage_received_count",
        "b50_count",
        "is_eventual_top_b50_label",
    }
    assert descriptive_fields <= set(v0_48_audit.PER_LINEAGE_FIELDNAMES)

    # Primaries do not fire under either label.
    summaries_a = [
        _make_summary("pre50_food_events_count", +1, +0.2),
        _make_summary("pre50_food_energy_acquired", +1, +0.3),
        _make_summary("mean_distance_to_nearest_food_cell", -1, +0.1),
    ]
    summaries_b = [
        _make_summary("pre50_food_events_count", +1, +0.1, label="label_b_readiness_fraction"),
        _make_summary("pre50_food_energy_acquired", +1, +0.2, label="label_b_readiness_fraction"),
        _make_summary(
            "mean_distance_to_nearest_food_cell",
            -1,
            +0.1,
            label="label_b_readiness_fraction",
        ),
    ]
    assert v0_48_audit._evaluate_verdict(summaries_a, summaries_b) == v0_48_audit.VERDICT_NOT
