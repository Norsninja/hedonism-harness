"""v0.43R intervention audit tests.

Coverage:
  - Locked constants (thresholds, hazards, seeds, arm labels, kinds).
  - Locked phrase regression guards (3 verdicts + auxiliary).
  - H2 halts on synthetic events.jsonl fixtures (H2b/H2c/H2d).
  - Substrate conservation halts (B-not-halved, B-multiset-unchanged-when-
    nondegenerate, C-not-preserved, C-multiset-bug-when-cells-changed).
  - Primary test arithmetic with explicit verdict booleans.
  - Secondary test arithmetic.
  - Verdict mapping (3 verdicts + halt cell).
  - Auxiliary DENSITY_REDUCTION_ABLATES_REPRODUCTION logic.
  - Reduce-one-run computes share correctly over all 5 lineages.
  - assert_sweep_present halts on missing sweep.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_43r_intervention_audit.py"
    spec = importlib.util.spec_from_file_location("v0_43r_intervention_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_43r_intervention_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.PRIMARY_B_REDUCTION_THRESHOLD == 0.15
    assert m.PRIMARY_C_TOLERANCE == 0.10
    assert m.AUXILIARY_DENSITY_REDUCTION_ABLATION_MAX_EXCLUDED == 2
    assert m.B_DENSITY_FACTOR == 0.5
    assert m.TOTAL_FOOD_ABS_TOL == 1e-3
    assert m.TOTAL_FOOD_REL_TOL == 1e-5


def test_locked_hazards_seeds_runs():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 8)
    assert tuple(range(49, 57)) == m.EXPECTED_SEEDS
    assert m.EXPECTED_RUNS_TOTAL == 48
    assert m.EXPECTED_INTERVENTION_TICK == 50
    assert m.EXPECTED_EFFECTIVE_TICK == 51


def test_locked_arm_labels():
    m = _load_audit()
    assert m.ARM_A_NULL == "A_null"
    assert m.ARM_B_REDUCE == "B_reduce_food_density_50pct"
    assert m.ARM_C_PERTURBATION == "C_density_preserving_perturbation"
    assert m.ALL_ARMS == (m.ARM_A_NULL, m.ARM_B_REDUCE, m.ARM_C_PERTURBATION)


def test_locked_kind_labels():
    m = _load_audit()
    assert m.KIND_REDUCE_DENSITY_50PCT == "reduce_food_density_50pct_at_tick50"
    assert m.KIND_DENSITY_PRESERVING_PERTURBATION == "density_preserving_perturbation_at_tick50"


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_density_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_DENSITY_NECESSARY_PHRASE
    assert "Halving the food density" in p
    assert "food density at tick 50 is necessary" in p
    assert "Sufficiency is NOT tested" in p


def test_perturbation_disrupts_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_PERTURBATION_DISRUPTS_PHRASE
    assert "magnitude-matched density-preserving perturbation control" in p
    assert "v0.44 candidate: reduce the C-arm's perturbation magnitude" in p


def test_density_not_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_DENSITY_NOT_NECESSARY_PHRASE
    assert "Food density at tick 50 is" in p
    assert "not necessary" in p
    assert "v0.44 candidate: hazard relocation" in p


def test_auxiliary_phrase_template_has_format_placeholders():
    m = _load_audit()
    p = m.LOCKED_DENSITY_REDUCTION_ABLATES_REPRODUCTION_PHRASE
    assert "{h}" in p
    assert "{n_excluded}" in p


# ---------------------------------------------------------------------------
# Primary / secondary arithmetic on synthesized rows
# ---------------------------------------------------------------------------


def _make_per_arm(m, *, a0, a8, b0, b8, c0, c8) -> list:
    """Synthesize per-arm-per-hazard rows with given mean_share values."""
    return [
        m.PerArmPerHazardRow(
            arm=m.ARM_A_NULL,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=a0,
            median_share=a0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_A_NULL,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=a8,
            median_share=a8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_REDUCE,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b0,
            median_share=b0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_REDUCE,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b8,
            median_share=b8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERTURBATION,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c0,
            median_share=c0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERTURBATION,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c8,
            median_share=c8,
        ),
    ]


def test_primary_food_density_necessary_when_b_drops_c_in_tolerance():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_passes is True
    assert p.food_density_necessary is True
    assert p.substrate_perturbation_disrupts is False
    assert p.food_density_not_necessary is False
    assert p.c_above_a_unmodeled_substrate_artefact is False
    assert p.primary_fires is True


def test_primary_substrate_perturbation_disrupts_when_b_and_c_both_drop():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.5, c8=0.5)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_passes is False
    assert p.c_below_a is True
    assert p.substrate_perturbation_disrupts is True
    assert p.food_density_necessary is False
    assert p.primary_fires is True


def test_primary_food_density_not_necessary_when_b_does_not_drop():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.7, b8=0.7, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is False
    assert p.food_density_not_necessary is True
    assert p.primary_fires is False


def test_primary_food_density_not_necessary_when_b_rises():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.7, b8=0.8, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is False
    assert p.food_density_not_necessary is True


def test_primary_b_passes_at_exact_threshold():
    m = _load_audit()
    # 0.625 - 0.475 = 0.15 exactly (multiples of 1/8 avoid float artifacts).
    per_arm = _make_per_arm(m, a0=0.625, a8=0.625, b0=0.625, b8=0.475, c0=0.625, c8=0.625)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_b_minus_a_h8 == pytest.approx(-0.15, abs=1e-12)
    assert p.b_passes is True


def test_primary_c_passes_at_exact_tolerance():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.7, c8=0.6)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_c_minus_a_h8 == pytest.approx(-0.1)
    assert p.c_passes is True


def test_primary_c_above_a_unmodeled_artefact_flag_set():
    m = _load_audit()
    # B drops 0.20; C rises 0.15 above A.
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.7, c8=0.85)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_above_a is True
    assert p.c_above_a_unmodeled_substrate_artefact is True


def test_secondary_hazard_amplified_when_h8_delta_larger():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.65, b8=0.5, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.delta_b_minus_a_h0 == pytest.approx(-0.05)
    assert s.delta_b_minus_a_h8 == pytest.approx(-0.2)
    assert s.hazard_amplified is True
    assert s.secondary_fires is True


def test_secondary_does_not_fire_when_primary_does_not_fire():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.65, b8=0.65, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.primary_fires is False
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.secondary_fires is False


# ---------------------------------------------------------------------------
# Verdict mapping
# ---------------------------------------------------------------------------


def _make_primary_synth(m, *, b8, c8, a8=0.7):
    delta_b = b8 - a8
    delta_c = c8 - a8
    b_passes = delta_b <= -m.PRIMARY_B_REDUCTION_THRESHOLD
    c_passes = abs(delta_c) <= m.PRIMARY_C_TOLERANCE
    c_below_a = delta_c <= -m.PRIMARY_C_TOLERANCE
    c_above_a = delta_c > m.PRIMARY_C_TOLERANCE
    return m.PrimaryTestRow(
        a_share_h8=a8,
        b_share_h8=b8,
        c_share_h8=c8,
        delta_b_minus_a_h8=delta_b,
        delta_c_minus_a_h8=delta_c,
        b_passes=b_passes,
        c_passes=c_passes,
        c_below_a=c_below_a,
        c_above_a=c_above_a,
        food_density_necessary=b_passes and c_passes,
        substrate_perturbation_disrupts=b_passes and c_below_a,
        food_density_not_necessary=not b_passes,
        c_above_a_unmodeled_substrate_artefact=b_passes and c_above_a,
        primary_fires=(b_passes and c_passes) or (b_passes and c_below_a),
    )


def _make_secondary_synth(m):
    return m.SecondaryTestRow(
        delta_b_minus_a_h0=0.0,
        delta_b_minus_a_h8=0.0,
        abs_delta_h0=0.0,
        abs_delta_h8=0.0,
        hazard_amplified=False,
        secondary_fires=False,
    )


def test_verdict_food_density_necessary():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.5, c8=0.7)  # B drops 0.20; C in tolerance
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_DENSITY_NECESSARY
    assert v.locked_phrase == m.LOCKED_DENSITY_NECESSARY_PHRASE
    assert v.food_density_necessary is True


def test_verdict_substrate_perturbation_disrupts():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.5, c8=0.5)  # B drops 0.20; C drops 0.20
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_PERTURBATION_DISRUPTS
    assert v.locked_phrase == m.LOCKED_PERTURBATION_DISRUPTS_PHRASE
    assert v.substrate_perturbation_disrupts is True


def test_verdict_food_density_not_necessary_when_b_does_not_drop():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.7, c8=0.7)
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_DENSITY_NOT_NECESSARY
    assert v.locked_phrase == m.LOCKED_DENSITY_NOT_NECESSARY_PHRASE
    assert v.food_density_not_necessary is True


def test_verdict_c_above_a_halts_loud():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.5, c8=0.85)  # b_passes AND c_above_a
    s = _make_secondary_synth(m)
    with pytest.raises(m.lr.LineageReplayError, match=r"C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT"):
        m.evaluate_verdict(p, s)


# ---------------------------------------------------------------------------
# Auxiliary findings
# ---------------------------------------------------------------------------


def test_auxiliary_fires_when_b_excluded_exceeds_threshold():
    m = _load_audit()
    per_arm = [
        m.PerArmPerHazardRow(
            arm=m.ARM_A_NULL,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_A_NULL,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=0.5,
            median_share=0.5,
        ),
        # B at h=0 has 5 excluded (>2) -> fires; B at h=8 has 1 excluded (<=2).
        m.PerArmPerHazardRow(
            arm=m.ARM_B_REDUCE,
            hazard=0,
            n_runs=8,
            n_runs_used=3,
            n_excluded_zero_post50=5,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_REDUCE,
            hazard=8,
            n_runs=8,
            n_runs_used=7,
            n_excluded_zero_post50=1,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERTURBATION,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERTURBATION,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=0.5,
            median_share=0.5,
        ),
    ]
    aux = m.evaluate_auxiliary_findings(per_arm)
    aux_by_h = {r.hazard: r for r in aux}
    assert aux_by_h[0].auxiliary_phrase_fires is True
    assert aux_by_h[0].b_n_excluded_zero_post50 == 5
    assert "h=0" in aux_by_h[0].locked_phrase
    assert aux_by_h[8].auxiliary_phrase_fires is False
    assert aux_by_h[8].locked_phrase == ""


# ---------------------------------------------------------------------------
# Synthetic events.jsonl reduction (H2 halts + share arithmetic)
# ---------------------------------------------------------------------------


def _write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")


def _born_event(*, agent_id, lineage_id, tick) -> dict:
    return {
        "tick": tick,
        "type": "AgentBorn",
        "event": {
            "agent_id": agent_id,
            "parent_id": 0,
            "lineage_id": lineage_id,
            "x": 0,
            "y": 0,
            "tick": tick,
        },
    }


def _food_event(
    *,
    intervention_kind,
    n_eligible_cells=24,
    n_cells_changed=24,
    total_food_before=480.0,
    total_food_after=240.0,
    digest_before="aaa",
    digest_after="bbb",
    cells_digest="ccc",
    effective_tick=51,
) -> dict:
    return {
        "tick": effective_tick,
        "type": "FoodRedistributedByIntervention",
        "event": {
            "intervention_kind": intervention_kind,
            "intervention_tick": 50,
            "effective_tick": effective_tick,
            "n_eligible_cells": n_eligible_cells,
            "n_cells_changed": n_cells_changed,
            "total_food_before": total_food_before,
            "total_food_after": total_food_after,
            "eligible_cells_digest": cells_digest,
            "food_multiset_digest_before": digest_before,
            "food_multiset_digest_after": digest_after,
        },
    }


def _set_sweep_root(m, tmp_path):
    return tmp_path / "fear-hunger-v0.43R-tight_gradient" / "arms"


def test_assert_sweep_present_halts_on_missing(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "missing-sweep")
    with pytest.raises(m.lr.LineageReplayError, match=r"sweep incomplete"):
        m.assert_sweep_present()


def test_reduce_one_run_a_null_no_food_event_is_ok(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    p = sweep_root / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-49" / "events.jsonl"
    _write_events(p, [])
    row = m._reduce_one_run(m.ARM_A_NULL, 8, 49)
    assert row.fired is False
    assert row.intervention_kind == m.KIND_NULL
    assert row.total_post_50_births == 0
    assert math.isnan(row.post_intervention_top_lineage_b50_share)
    assert row.excluded_zero_post50 is True


def test_reduce_one_run_a_null_with_food_event_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [_food_event(intervention_kind=m.KIND_REDUCE_DENSITY_50PCT)]
    p = sweep_root / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2b violation: A_null"):
        m._reduce_one_run(m.ARM_A_NULL, 8, 49)


def test_reduce_one_run_b_no_food_event_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, [])
    with pytest.raises(m.lr.LineageReplayError, match=r"H2b violation"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_b_kind_mismatch_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [_food_event(intervention_kind=m.KIND_DENSITY_PRESERVING_PERTURBATION)]
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2b kind mismatch"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_b_effective_tick_drift_halts_h2c(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_REDUCE_DENSITY_50PCT,
            effective_tick=52,
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2c effective_tick"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_b_total_not_halved_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_REDUCE_DENSITY_50PCT,
            total_food_before=480.0,
            total_food_after=480.0,  # not halved
            digest_before="aaa",
            digest_after="bbb",
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2d B-conservation"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_b_multiset_unchanged_when_total_positive_halts(tmp_path, monkeypatch):
    """B halving any total > 0 must shift the multiset; identical digests
    indicate an arithmetic bug in the helper.
    """
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_REDUCE_DENSITY_50PCT,
            total_food_before=480.0,
            total_food_after=240.0,
            digest_before="aaa",
            digest_after="aaa",  # bug: identical digest on non-degenerate halve
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2d B-multiset invariant"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_c_total_not_preserved_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_DENSITY_PRESERVING_PERTURBATION,
            total_food_before=480.0,
            total_food_after=240.0,  # not preserved
            digest_before="aaa",
            digest_after="bbb",
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_C_PERTURBATION][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2d C-conservation"):
        m._reduce_one_run(m.ARM_C_PERTURBATION, 8, 49)


def test_reduce_one_run_c_multiset_unchanged_with_n_changed_positive_halts(tmp_path, monkeypatch):
    """C with digest match AND n_cells_changed > 0 indicates a digest bug."""
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_DENSITY_PRESERVING_PERTURBATION,
            total_food_before=480.0,
            total_food_after=480.0,
            n_cells_changed=24,
            digest_before="aaa",
            digest_after="aaa",  # bug: cells changed but digest matches
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_C_PERTURBATION][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2d C-multiset bug"):
        m._reduce_one_run(m.ARM_C_PERTURBATION, 8, 49)


def test_reduce_one_run_c_multiset_unchanged_with_n_changed_zero_is_legit(tmp_path, monkeypatch):
    """Legitimate degenerate case: C on a 25/75 fixed-point substrate yields
    digest_before == digest_after AND n_cells_changed == 0. Must not halt.
    """
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_DENSITY_PRESERVING_PERTURBATION,
            total_food_before=480.0,
            total_food_after=480.0,
            n_cells_changed=0,
            digest_before="aaa",
            digest_after="aaa",
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_C_PERTURBATION][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_C_PERTURBATION, 8, 49)
    assert row.fired is True
    assert row.n_cells_changed == 0


def test_reduce_one_run_n_cells_changed_exceeds_eligible_halts(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events = [
        _food_event(
            intervention_kind=m.KIND_REDUCE_DENSITY_50PCT,
            n_eligible_cells=24,
            n_cells_changed=25,  # bug
            total_food_before=480.0,
            total_food_after=240.0,
        )
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    with pytest.raises(m.lr.LineageReplayError, match=r"H2d invariant violation"):
        m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)


def test_reduce_one_run_share_arithmetic_over_all_lineages(tmp_path, monkeypatch):
    """v0.43R does not exclude any lineage (no kill). Share is computed
    over all 5 lineages' post-50 births.
    """
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    # Lineage 0=5 births, 1=6 births, 2=3 births, 3=1 birth, 4=0 -> total=15.
    # Top = lineage 1 with 6 -> share = 6/15 = 0.4.
    events: list[dict] = [
        _food_event(intervention_kind=m.KIND_REDUCE_DENSITY_50PCT),
    ]
    aid = 100
    for lid, n in [(0, 5), (1, 6), (2, 3), (3, 1)]:
        for _ in range(n):
            events.append(_born_event(agent_id=aid, lineage_id=lid, tick=60))
            aid += 1
    p = sweep_root / m._ARM_DIRS[m.ARM_B_REDUCE][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_B_REDUCE, 8, 49)
    assert row.total_post_50_births == 15
    assert row.top_lineage_id == 1
    assert row.top_lineage_post50_births == 6
    assert row.post_intervention_top_lineage_b50_share == pytest.approx(6 / 15)


def test_reduce_one_run_share_excludes_pre_50_births(tmp_path, monkeypatch):
    m = _load_audit()
    sweep_root = _set_sweep_root(m, tmp_path)
    monkeypatch.setattr(m, "SWEEP_ROOT", sweep_root)
    events: list[dict] = [
        _born_event(agent_id=200, lineage_id=1, tick=50),  # tick==50, excluded
        _born_event(agent_id=201, lineage_id=1, tick=49),  # excluded
        _born_event(agent_id=202, lineage_id=1, tick=51),  # included
        _born_event(agent_id=203, lineage_id=2, tick=51),  # included
    ]
    p = sweep_root / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-49" / "events.jsonl"
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_A_NULL, 8, 49)
    assert row.total_post_50_births == 2
    assert row.top_lineage_post50_births == 1
    assert row.post_intervention_top_lineage_b50_share == pytest.approx(0.5)
