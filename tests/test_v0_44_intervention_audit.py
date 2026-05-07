"""v0.44 intervention audit tests.

Coverage:
  - Locked thresholds, hazards, seeds, arm labels, kind labels.
  - Locked-phrase regression guards (verbatim).
  - Primary test booleans across the truth table.
  - Verdict logic (FLOW_NECESSARY / DISRUPTS / FLOW_NOT_NECESSARY) +
    halt on c_above_a.
  - H2 halts on synthetic events.jsonl fixtures (H2a/H2b/H2c/H2d/H2d-aux).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_44_intervention_audit.py"
    spec = importlib.util.spec_from_file_location("v0_44_intervention_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_44_intervention_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.PRIMARY_B_REDUCTION_THRESHOLD == 0.15
    assert m.PRIMARY_C_TOLERANCE == 0.10
    assert m.AUXILIARY_DELAY_ABLATION_MAX_EXCLUDED == 2
    assert m.B_DELAY_TICKS == 25


def test_locked_hazards_seeds_runs():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 8)
    assert tuple(range(57, 65)) == m.EXPECTED_SEEDS
    assert m.EXPECTED_RUNS_TOTAL == 48
    assert m.EXPECTED_INTERVENTION_TICK == 50
    assert m.EXPECTED_EFFECTIVE_TICK == 51
    assert m.EXPECTED_N_ELIGIBLE_CELLS == 24


def test_locked_arm_labels():
    m = _load_audit()
    assert m.ARM_A_NULL == "A_null"
    assert m.ARM_B_DELAY == "B_delay_respawn_schedule_plus_25"
    assert m.ARM_C_PERMUTE == "C_permute_respawn_schedule_reverse_row_major"
    assert m.ALL_ARMS == (m.ARM_A_NULL, m.ARM_B_DELAY, m.ARM_C_PERMUTE)


def test_locked_kind_labels():
    m = _load_audit()
    assert m.KIND_DELAY_RESPAWN_PLUS_25 == "delay_respawn_schedule_plus_25_at_tick50"
    assert (
        m.KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR
        == "permute_respawn_schedule_reverse_row_major_at_tick50"
    )


def test_locked_verdict_strings():
    m = _load_audit()
    assert m.VERDICT_FLOW_NECESSARY == "RESPAWN_FLOW_NECESSARY"
    assert m.VERDICT_PERTURBATION_DISRUPTS == "SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE"
    assert m.VERDICT_FLOW_NOT_NECESSARY == "RESPAWN_FLOW_NOT_NECESSARY"


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_flow_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_FLOW_NECESSARY_PHRASE
    assert "Delaying the respawn schedule by +25 ticks" in p
    assert "respawn flow at tick 50 is necessary" in p
    assert "Sufficiency is NOT tested" in p


def test_perturbation_disrupts_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_PERTURBATION_DISRUPTS_PHRASE
    assert "multiset-preserving schedule-permutation control" in p
    assert "v0.45 candidate: reduce the C-arm permutation magnitude" in p


def test_flow_not_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_FLOW_NOT_NECESSARY_PHRASE
    assert "Respawn flow at tick 50 is not necessary" in p
    assert "v0.45 candidate" in p


def test_auxiliary_phrase_template_has_format_placeholders():
    m = _load_audit()
    p = m.LOCKED_DELAY_ABLATES_REPRODUCTION_PHRASE
    assert "{h}" in p
    assert "{n_excluded}" in p


# ---------------------------------------------------------------------------
# Primary test arithmetic (synthetic per_arm rows)
# ---------------------------------------------------------------------------


def _make_per_arm(m, *, a0, a8, b0, b8, c0, c8) -> list:
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
            arm=m.ARM_B_DELAY,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b0,
            median_share=b0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_DELAY,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b8,
            median_share=b8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERMUTE,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c0,
            median_share=c0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_PERMUTE,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c8,
            median_share=c8,
        ),
    ]


def test_primary_flow_necessary_when_b_drops_c_in_tolerance():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.60, b8=0.50, c0=0.66, c8=0.72)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_passes is True
    assert p.respawn_flow_necessary is True
    assert p.substrate_perturbation_disrupts is False
    assert p.respawn_flow_not_necessary is False
    assert p.primary_fires is True


def test_primary_substrate_perturbation_disrupts_when_b_and_c_both_drop():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.60, b8=0.45, c0=0.66, c8=0.50)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_below_a is True
    assert p.substrate_perturbation_disrupts is True
    assert p.respawn_flow_necessary is False
    assert p.primary_fires is True


def test_primary_flow_not_necessary_when_b_does_not_drop():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.65, b8=0.65, c0=0.66, c8=0.70)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is False
    assert p.respawn_flow_not_necessary is True
    assert p.primary_fires is False


def test_primary_b_passes_at_exact_threshold():
    m = _load_audit()
    # delta(B-A) = 0.50 - 0.65 = -0.15 (boundary).
    per_arm = _make_per_arm(m, a0=0.65, a8=0.65, b0=0.60, b8=0.50, c0=0.66, c8=0.65)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True


def test_primary_c_passes_at_exact_tolerance():
    m = _load_audit()
    # delta(C-A) = 0.55 - 0.65 = -0.10 (boundary).
    per_arm = _make_per_arm(m, a0=0.65, a8=0.65, b0=0.60, b8=0.50, c0=0.66, c8=0.55)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_passes is True


def test_primary_c_above_a_unmodeled_artefact_flag_set():
    m = _load_audit()
    # delta(C-A) = 0.85 - 0.65 = +0.20 > 0.10.
    per_arm = _make_per_arm(m, a0=0.65, a8=0.65, b0=0.60, b8=0.45, c0=0.66, c8=0.85)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_above_a is True
    assert p.c_above_a_unmodeled_substrate_artefact is True


# ---------------------------------------------------------------------------
# Secondary
# ---------------------------------------------------------------------------


def test_secondary_hazard_amplified_when_h8_delta_larger():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.62, b8=0.50, c0=0.66, c8=0.72)
    p = m.evaluate_primary_test(per_arm)
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.hazard_amplified is True
    assert s.secondary_fires is True


def test_secondary_does_not_fire_when_primary_does_not_fire():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.65, b8=0.65, c0=0.66, c8=0.70)
    p = m.evaluate_primary_test(per_arm)
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.secondary_fires is False


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def _primary_synth(m, *, b8, c8, a8=0.7):
    per_arm = _make_per_arm(m, a0=0.65, a8=a8, b0=0.62, b8=b8, c0=0.66, c8=c8)
    return m.evaluate_primary_test(per_arm)


def _secondary_synth(m):
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.62, b8=0.50, c0=0.66, c8=0.72)
    p = m.evaluate_primary_test(per_arm)
    return m.evaluate_secondary_test(per_arm, p)


def test_verdict_flow_necessary():
    m = _load_audit()
    p = _primary_synth(m, b8=0.50, c8=0.72)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_FLOW_NECESSARY
    assert v.locked_phrase == m.LOCKED_FLOW_NECESSARY_PHRASE


def test_verdict_substrate_perturbation_disrupts():
    m = _load_audit()
    p = _primary_synth(m, b8=0.45, c8=0.50)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_PERTURBATION_DISRUPTS
    assert v.locked_phrase == m.LOCKED_PERTURBATION_DISRUPTS_PHRASE


def test_verdict_flow_not_necessary_when_b_does_not_drop():
    m = _load_audit()
    p = _primary_synth(m, b8=0.65, c8=0.70)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_FLOW_NOT_NECESSARY
    assert v.locked_phrase == m.LOCKED_FLOW_NOT_NECESSARY_PHRASE


def test_verdict_c_above_a_halts_loud():
    m = _load_audit()
    p = _primary_synth(m, b8=0.45, c8=0.85)
    s = _secondary_synth(m)
    with pytest.raises(m.lr.LineageReplayError, match="C_ABOVE_A_UNMODELED"):
        m.evaluate_verdict(p, s)


# ---------------------------------------------------------------------------
# Auxiliary
# ---------------------------------------------------------------------------


def test_auxiliary_fires_when_b_excluded_exceeds_threshold():
    m = _load_audit()
    per_arm = [
        m.PerArmPerHazardRow(
            arm=m.ARM_B_DELAY,
            hazard=0,
            n_runs=8,
            n_runs_used=5,
            n_excluded_zero_post50=3,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_DELAY,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=1,
            mean_share=0.5,
            median_share=0.5,
        ),
    ]
    aux = m.evaluate_auxiliary_findings(per_arm)
    by_hzd = {r.hazard: r for r in aux}
    assert by_hzd[0].auxiliary_phrase_fires is True
    assert "h=0" in by_hzd[0].locked_phrase
    assert "3 of 8" in by_hzd[0].locked_phrase
    assert by_hzd[8].auxiliary_phrase_fires is False
    assert by_hzd[8].locked_phrase == ""


# ---------------------------------------------------------------------------
# Synthetic events.jsonl H2 halts
# ---------------------------------------------------------------------------


def _write_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e, sort_keys=True) for e in events) + "\n")


def _born_event(*, agent_id: int, lineage_id: int, tick: int) -> dict:
    return {
        "tick": tick,
        "type": "AgentBorn",
        "event": {
            "agent_id": agent_id,
            "lineage_id": lineage_id,
            "parent_id": -1,
            "tick": tick,
            "x": 0,
            "y": 0,
        },
    }


def _respawn_event(
    *,
    intervention_kind: str,
    n_eligible: int = 24,
    n_changed: int = 24,
    min_b: int = 54,
    max_b: int = 79,
    sum_b: int = 1500,
    min_a: int | None = None,
    max_a: int | None = None,
    sum_a: int | None = None,
    digest_b: str = "digest_before_aaa",
    digest_a: str = "digest_after_bbb",
    cells_digest: str = "cells_digest_xxx",
    effective_tick: int = 51,
) -> dict:
    if min_a is None:
        min_a = min_b + 25
    if max_a is None:
        max_a = max_b + 25
    if sum_a is None:
        sum_a = sum_b + 25 * n_eligible
    return {
        "tick": effective_tick,
        "type": "RespawnScheduleByIntervention",
        "event": {
            "intervention_kind": intervention_kind,
            "intervention_tick": 50,
            "effective_tick": effective_tick,
            "n_eligible_cells": n_eligible,
            "n_cells_changed": n_changed,
            "min_respawn_tick_before": min_b,
            "max_respawn_tick_before": max_b,
            "min_respawn_tick_after": min_a,
            "max_respawn_tick_after": max_a,
            "sum_respawn_tick_before": sum_b,
            "sum_respawn_tick_after": sum_a,
            "eligible_cells_digest": cells_digest,
            "respawn_multiset_digest_before": digest_b,
            "respawn_multiset_digest_after": digest_a,
        },
    }


def _set_sweep_root(m, tmp_path: Path) -> None:
    m.SWEEP_ROOT = tmp_path


def test_assert_sweep_present_halts_on_missing(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    with pytest.raises(m.lr.LineageReplayError, match="sweep incomplete"):
        m.assert_sweep_present()


def test_reduce_one_run_a_null_no_event_is_ok(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 0, 57)
    _write_events(p, [_born_event(agent_id=1, lineage_id=1, tick=60)])
    row = m._reduce_one_run(m.ARM_A_NULL, 0, 57)
    assert row.fired is False
    assert row.total_post_50_births == 1


def test_reduce_one_run_a_null_with_event_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 0, 57)
    _write_events(p, [_respawn_event(intervention_kind=m.KIND_DELAY_RESPAWN_PLUS_25)])
    with pytest.raises(m.lr.LineageReplayError, match="H2b"):
        m._reduce_one_run(m.ARM_A_NULL, 0, 57)


def test_reduce_one_run_b_no_event_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(p, [_born_event(agent_id=1, lineage_id=1, tick=60)])
    with pytest.raises(m.lr.LineageReplayError, match="H2b"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_b_kind_mismatch_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(
        p,
        [_respawn_event(intervention_kind=m.KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)],
    )
    with pytest.raises(m.lr.LineageReplayError, match="kind mismatch"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_b_effective_tick_drift_halts_h2c(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(
        p,
        [_respawn_event(intervention_kind=m.KIND_DELAY_RESPAWN_PLUS_25, effective_tick=50)],
    )
    with pytest.raises(m.lr.LineageReplayError, match="H2c"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_b_eligible_cells_mismatch_halts_h2d_aux(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(
        p,
        [_respawn_event(intervention_kind=m.KIND_DELAY_RESPAWN_PLUS_25, n_eligible=23)],
    )
    with pytest.raises(m.lr.LineageReplayError, match="H2d-aux"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_b_sum_mismatch_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(
        p,
        [
            _respawn_event(
                intervention_kind=m.KIND_DELAY_RESPAWN_PLUS_25,
                sum_b=1500,
                sum_a=1500 + 25 * 24 + 1,  # off-by-one
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="B-conservation sum"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_b_multiset_unchanged_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_DELAY, 0, 57)
    _write_events(
        p,
        [
            _respawn_event(
                intervention_kind=m.KIND_DELAY_RESPAWN_PLUS_25,
                digest_b="same",
                digest_a="same",
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="B-multiset invariant"):
        m._reduce_one_run(m.ARM_B_DELAY, 0, 57)


def test_reduce_one_run_c_sum_mismatch_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_C_PERMUTE, 0, 57)
    _write_events(
        p,
        [
            _respawn_event(
                intervention_kind=m.KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
                sum_b=1500,
                sum_a=1501,  # not preserved
                min_a=54,
                max_a=79,
                digest_b="same",
                digest_a="same",
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="C-conservation sum"):
        m._reduce_one_run(m.ARM_C_PERMUTE, 0, 57)


def test_reduce_one_run_c_multiset_changed_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_C_PERMUTE, 0, 57)
    _write_events(
        p,
        [
            _respawn_event(
                intervention_kind=m.KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
                sum_b=1500,
                sum_a=1500,
                min_a=54,
                max_a=79,
                digest_b="aaa",
                digest_a="bbb",  # permutation must preserve multiset
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="C-multiset bug"):
        m._reduce_one_run(m.ARM_C_PERMUTE, 0, 57)


def test_reduce_one_run_share_arithmetic(tmp_path, monkeypatch):
    """post_intervention_top_lineage_b50_share over all 5 lineages."""
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 8, 57)
    events = []
    # Lineage 1: 5 post-50 births. Lineage 2: 3. Total 8.
    for i in range(5):
        events.append(_born_event(agent_id=10 + i, lineage_id=1, tick=55 + i))
    for i in range(3):
        events.append(_born_event(agent_id=20 + i, lineage_id=2, tick=70 + i))
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_A_NULL, 8, 57)
    assert row.total_post_50_births == 8
    assert row.top_lineage_id == 1
    assert row.top_lineage_post50_births == 5
    assert abs(row.post_intervention_top_lineage_b50_share - 5 / 8) < 1e-9


def test_reduce_one_run_share_excludes_pre_50_births(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 8, 57)
    events = [
        _born_event(agent_id=1, lineage_id=1, tick=40),  # pre-50; ignored
        _born_event(agent_id=2, lineage_id=1, tick=50),  # tick == 50; ignored
        _born_event(agent_id=3, lineage_id=2, tick=51),  # post-50
    ]
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_A_NULL, 8, 57)
    assert row.total_post_50_births == 1
    assert row.top_lineage_id == 2
