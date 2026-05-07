"""v0.45 intervention audit tests.

Coverage:
  - Locked thresholds, hazards, seeds, arm labels, kind labels,
    verdict labels.
  - Locked-phrase regression guards (verbatim).
  - Primary test booleans across the truth table (3-way + 2 halt cells).
  - Verdict logic (BIRTH_LOCALITY_NECESSARY / LOCAL_CONTROL_DISRUPTS /
    BIRTH_LOCALITY_NOT_NECESSARY) + 2 halt cells.
  - H2 halts on synthetic events.jsonl fixtures.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_45_intervention_audit.py"
    spec = importlib.util.spec_from_file_location("v0_45_intervention_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_45_intervention_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.PRIMARY_B_REDUCTION_THRESHOLD == 0.15
    assert m.PRIMARY_C_TOLERANCE == 0.10
    assert m.AUXILIARY_GLOBAL_REDIRECT_ABLATION_MAX_EXCLUDED == 2


def test_locked_hazards_seeds_runs():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 8)
    assert tuple(range(65, 73)) == m.EXPECTED_SEEDS
    assert m.EXPECTED_RUNS_TOTAL == 48
    assert m.EXPECTED_TICK_THRESHOLD == 50


def test_locked_arm_labels():
    m = _load_audit()
    assert m.ARM_A_NULL == "A_null"
    assert m.ARM_B_UNIFORM_GLOBAL == "B_uniform_valid_region"
    assert m.ARM_C_UNIFORM_NEIGHBOR == "C_uniform_neighbor"


def test_locked_kind_labels():
    m = _load_audit()
    assert m.KIND_UNIFORM_VALID_REGION_BIRTH == "uniform_valid_region_birth_position_after_tick50"
    assert m.KIND_UNIFORM_NEIGHBOR_BIRTH == "uniform_neighbor_birth_position_after_tick50"
    assert m.RNG_STREAM_LABEL == "v0_45_birth_position_intervention"


def test_locked_verdict_strings():
    m = _load_audit()
    assert m.VERDICT_BIRTH_LOCALITY_NECESSARY == "BIRTH_LOCALITY_NECESSARY"
    assert m.VERDICT_LOCAL_CONTROL_DISRUPTS == "LOCAL_CONTROL_DISRUPTS_DOMINANCE"
    assert m.VERDICT_BIRTH_LOCALITY_NOT_NECESSARY == "BIRTH_LOCALITY_NOT_NECESSARY"


def test_valid_target_kinds():
    m = _load_audit()
    assert frozenset({"EMPTY", "FOOD", "SAFE"}) == m.VALID_TARGET_KINDS


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_birth_locality_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_BIRTH_LOCALITY_NECESSARY_PHRASE
    assert "Redirecting every post-50 offspring birth" in p
    assert "parent-local birth placement is necessary" in p
    assert "Sufficiency is NOT tested" in p


def test_local_control_disrupts_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_LOCAL_CONTROL_DISRUPTS_PHRASE
    assert "any per-birth randomization" in p
    assert "v0.46 candidate: weaker C-arm randomization" in p


def test_birth_locality_not_necessary_phrase_verbatim():
    m = _load_audit()
    p = m.LOCKED_BIRTH_LOCALITY_NOT_NECESSARY_PHRASE
    assert "Parent-local birth placement is not necessary" in p
    assert "v0.46 candidate" in p


def test_auxiliary_phrase_template_has_format_placeholders():
    m = _load_audit()
    p = m.LOCKED_GLOBAL_REDIRECT_ABLATES_REPRODUCTION_PHRASE
    assert "{h}" in p
    assert "{n_excluded}" in p


# ---------------------------------------------------------------------------
# Primary test arithmetic
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
            arm=m.ARM_B_UNIFORM_GLOBAL,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b0,
            median_share=b0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_UNIFORM_GLOBAL,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=b8,
            median_share=b8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_UNIFORM_NEIGHBOR,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c0,
            median_share=c0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_UNIFORM_NEIGHBOR,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            mean_share=c8,
            median_share=c8,
        ),
    ]


def test_primary_birth_locality_necessary():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.60, b8=0.50, c0=0.66, c8=0.72)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_passes is True
    assert p.birth_locality_necessary is True
    assert p.local_control_disrupts is False
    assert p.birth_locality_not_necessary is False
    assert p.primary_fires is True


def test_primary_local_control_disrupts():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.60, b8=0.45, c0=0.66, c8=0.50)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is True
    assert p.c_below_a is True
    assert p.local_control_disrupts is True
    assert p.birth_locality_necessary is False
    assert p.primary_fires is True


def test_primary_birth_locality_not_necessary():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.70, b0=0.65, b8=0.65, c0=0.66, c8=0.70)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is False
    assert p.birth_locality_not_necessary is True
    assert p.primary_fires is False


def test_primary_c_above_a_unmodeled_artefact():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.65, b0=0.60, b8=0.45, c0=0.66, c8=0.85)
    p = m.evaluate_primary_test(per_arm)
    assert p.c_above_a_unmodeled_substrate_artefact is True


def test_primary_c_disrupts_without_b():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.65, a8=0.65, b0=0.60, b8=0.65, c0=0.66, c8=0.45)
    p = m.evaluate_primary_test(per_arm)
    assert p.b_passes is False
    assert p.c_disrupts_without_b is True


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


def test_verdict_birth_locality_necessary():
    m = _load_audit()
    p = _primary_synth(m, b8=0.50, c8=0.72)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_BIRTH_LOCALITY_NECESSARY


def test_verdict_local_control_disrupts():
    m = _load_audit()
    p = _primary_synth(m, b8=0.45, c8=0.50)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_LOCAL_CONTROL_DISRUPTS


def test_verdict_birth_locality_not_necessary():
    m = _load_audit()
    p = _primary_synth(m, b8=0.65, c8=0.70)
    s = _secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_BIRTH_LOCALITY_NOT_NECESSARY


def test_verdict_c_above_a_halts_loud():
    m = _load_audit()
    p = _primary_synth(m, b8=0.45, c8=0.85)
    s = _secondary_synth(m)
    with pytest.raises(m.lr.LineageReplayError, match="C_ABOVE_A_UNMODELED"):
        m.evaluate_verdict(p, s)


def test_verdict_c_disrupts_without_b_halts_loud():
    m = _load_audit()
    p = _primary_synth(m, b8=0.65, c8=0.45)
    s = _secondary_synth(m)
    with pytest.raises(m.lr.LineageReplayError, match="C_DISRUPTS_WITHOUT_B"):
        m.evaluate_verdict(p, s)


# ---------------------------------------------------------------------------
# Auxiliary
# ---------------------------------------------------------------------------


def test_auxiliary_fires_when_b_excluded_exceeds_threshold():
    m = _load_audit()
    per_arm = [
        m.PerArmPerHazardRow(
            arm=m.ARM_B_UNIFORM_GLOBAL,
            hazard=0,
            n_runs=8,
            n_runs_used=5,
            n_excluded_zero_post50=3,
            mean_share=0.5,
            median_share=0.5,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_UNIFORM_GLOBAL,
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


def _redirect_event(
    *,
    intervention_kind: str,
    tick: int = 60,
    parent_x: int = 1,
    parent_y: int = 1,
    redirected_x: int = 3,
    redirected_y: int = 3,
    target_kind: str = "EMPTY",
    n_valid: int = 5,
    rng_label: str = "v0_45_birth_position_intervention",
) -> dict:
    manhattan = abs(parent_x - redirected_x) + abs(parent_y - redirected_y)
    return {
        "tick": tick,
        "type": "BirthRedirectedByIntervention",
        "event": {
            "intervention_kind": intervention_kind,
            "tick": tick,
            "parent_id": 1,
            "parent_lineage_id": 1,
            "parent_x": parent_x,
            "parent_y": parent_y,
            "original_x": parent_x + 1,
            "original_y": parent_y,
            "redirected_x": redirected_x,
            "redirected_y": redirected_y,
            "n_valid_cells": n_valid,
            "target_cell_kind": target_kind,
            "preserved_parent_adjacency": manhattan == 1,
            "rng_stream_label": rng_label,
        },
    }


def test_assert_sweep_present_halts_on_missing(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    with pytest.raises(m.lr.LineageReplayError, match="sweep incomplete"):
        m.assert_sweep_present()


def test_a_null_with_redirect_event_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 0, 65)
    _write_events(p, [_redirect_event(intervention_kind=m.KIND_UNIFORM_VALID_REGION_BIRTH)])
    with pytest.raises(m.lr.LineageReplayError, match="A_null"):
        m._reduce_one_run(m.ARM_A_NULL, 0, 65)


def test_b_kind_mismatch_halts(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_UNIFORM_GLOBAL, 0, 65)
    _write_events(p, [_redirect_event(intervention_kind=m.KIND_UNIFORM_NEIGHBOR_BIRTH)])
    with pytest.raises(m.lr.LineageReplayError, match="kind mismatch"):
        m._reduce_one_run(m.ARM_B_UNIFORM_GLOBAL, 0, 65)


def test_event_pre_50_tick_halts_h2c(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_UNIFORM_GLOBAL, 0, 65)
    _write_events(
        p, [_redirect_event(intervention_kind=m.KIND_UNIFORM_VALID_REGION_BIRTH, tick=49)]
    )
    with pytest.raises(m.lr.LineageReplayError, match="H2c"):
        m._reduce_one_run(m.ARM_B_UNIFORM_GLOBAL, 0, 65)


def test_invalid_target_cell_kind_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_UNIFORM_GLOBAL, 0, 65)
    _write_events(
        p,
        [
            _redirect_event(
                intervention_kind=m.KIND_UNIFORM_VALID_REGION_BIRTH,
                target_kind="HAZARD",  # forbidden
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="target_cell_kind"):
        m._reduce_one_run(m.ARM_B_UNIFORM_GLOBAL, 0, 65)


def test_redirected_equals_parent_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_UNIFORM_GLOBAL, 0, 65)
    _write_events(
        p,
        [
            _redirect_event(
                intervention_kind=m.KIND_UNIFORM_VALID_REGION_BIRTH,
                parent_x=1,
                parent_y=1,
                redirected_x=1,
                redirected_y=1,
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="redirected cell == parent"):
        m._reduce_one_run(m.ARM_B_UNIFORM_GLOBAL, 0, 65)


def test_c_arm_non_adjacent_redirect_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_C_UNIFORM_NEIGHBOR, 0, 65)
    _write_events(
        p,
        [
            _redirect_event(
                intervention_kind=m.KIND_UNIFORM_NEIGHBOR_BIRTH,
                parent_x=1,
                parent_y=1,
                redirected_x=3,
                redirected_y=3,  # Manhattan = 4, should be 1 for C
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="adjacency"):
        m._reduce_one_run(m.ARM_C_UNIFORM_NEIGHBOR, 0, 65)


def test_rng_stream_label_drift_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_B_UNIFORM_GLOBAL, 0, 65)
    _write_events(
        p,
        [
            _redirect_event(
                intervention_kind=m.KIND_UNIFORM_VALID_REGION_BIRTH,
                rng_label="some_other_stream",
            )
        ],
    )
    with pytest.raises(m.lr.LineageReplayError, match="rng_stream_label"):
        m._reduce_one_run(m.ARM_B_UNIFORM_GLOBAL, 0, 65)


def test_a_null_share_arithmetic(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path)
    p = m._events_path(m.ARM_A_NULL, 8, 65)
    events = []
    for i in range(5):
        events.append(_born_event(agent_id=10 + i, lineage_id=1, tick=55 + i))
    for i in range(3):
        events.append(_born_event(agent_id=20 + i, lineage_id=2, tick=70 + i))
    _write_events(p, events)
    row = m._reduce_one_run(m.ARM_A_NULL, 8, 65)
    assert row.total_post_50_births == 8
    assert row.top_lineage_id == 1
    assert abs(row.post_intervention_top_lineage_b50_share - 5 / 8) < 1e-9
