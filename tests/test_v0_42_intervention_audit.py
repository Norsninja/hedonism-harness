"""v0.42 intervention audit tests.

Coverage:
  - Locked constants (thresholds, hazards, seeds, arm labels, kinds, roles).
  - Locked phrase regression guards (3 verdicts).
  - H2 halts on synthetic events.jsonl fixtures:
    * A_null arm with intervention summary present -> H2b violation halt.
    * B_kill_leader arm with no summary -> H2b violation halt.
    * Lineage role mismatch -> H2b violation halt.
    * effective_tick != 51 -> H2c violation halt.
    * AgentDied count != n_killed -> H2d violation halt.
  - Primary test arithmetic (b_passes / c_passes) on synthesized per-arm
    summaries.
  - Secondary test arithmetic.
  - Verdict three-way mapping.
  - C-rises-above-A guard halts loud.
  - Reduce-one-run computes share correctly on a synthetic events stream.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_audit():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0_42_intervention_audit.py"
    spec = importlib.util.spec_from_file_location("v0_42_intervention_audit", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_42_intervention_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_thresholds():
    m = _load_audit()
    assert m.PRIMARY_B_REDUCTION_THRESHOLD == 0.15
    assert m.PRIMARY_C_TOLERANCE == 0.10


def test_locked_hazards_seeds_runs():
    m = _load_audit()
    assert m.EXPECTED_HAZARDS == (0, 8)
    assert tuple(range(41, 49)) == m.EXPECTED_SEEDS
    assert m.EXPECTED_RUNS_TOTAL == 48
    assert m.EXPECTED_INTERVENTION_TICK == 50
    assert m.EXPECTED_EFFECTIVE_TICK == 51


def test_locked_arm_labels():
    m = _load_audit()
    assert m.ARM_A_NULL == "A_null"
    assert m.ARM_B_KILL_LEADER == "B_kill_leader"
    assert m.ARM_C_KILL_SMNONLEADER == "C_kill_smnonleader"
    assert m.ALL_ARMS == (m.ARM_A_NULL, m.ARM_B_KILL_LEADER, m.ARM_C_KILL_SMNONLEADER)


# ---------------------------------------------------------------------------
# Locked phrase regression guards
# ---------------------------------------------------------------------------


def test_necessity_phrase_verbatim():
    m = _load_audit()
    assert m.LOCKED_NECESSITY_PHRASE.startswith("Hard-killing the tick-50 leader lineage")
    assert "necessary for the v0.34..v0.41 dominance pattern" in m.LOCKED_NECESSITY_PHRASE
    assert "Sufficiency is NOT tested." in m.LOCKED_NECESSITY_PHRASE


def test_disruption_phrase_verbatim():
    m = _load_audit()
    assert "size-shock-sensitive" in m.LOCKED_DISRUPTION_PHRASE
    assert "v0.43 candidate: finer-grained control sweep" in m.LOCKED_DISRUPTION_PHRASE


def test_not_necessary_phrase_verbatim():
    m = _load_audit()
    phrase = m.LOCKED_NOT_NECESSARY_PHRASE
    assert "not necessary" in phrase
    assert "v0.43 candidate: pivot to substrate-level interventions" in phrase


# ---------------------------------------------------------------------------
# Primary / secondary test arithmetic on synthesized PerArmPerHazard rows
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
            n_control_unavailable=0,
            mean_share=a0,
            median_share=a0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_A_NULL,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            n_control_unavailable=0,
            mean_share=a8,
            median_share=a8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_KILL_LEADER,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            n_control_unavailable=0,
            mean_share=b0,
            median_share=b0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_B_KILL_LEADER,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            n_control_unavailable=0,
            mean_share=b8,
            median_share=b8,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_KILL_SMNONLEADER,
            hazard=0,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            n_control_unavailable=0,
            mean_share=c0,
            median_share=c0,
        ),
        m.PerArmPerHazardRow(
            arm=m.ARM_C_KILL_SMNONLEADER,
            hazard=8,
            n_runs=8,
            n_runs_used=8,
            n_excluded_zero_post50=0,
            n_control_unavailable=0,
            mean_share=c8,
            median_share=c8,
        ),
    ]


def test_primary_b_passes_when_b_drops_by_at_least_threshold():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_b_minus_a_h8 == pytest.approx(-0.2)
    assert p.b_passes is True
    assert p.c_passes is True
    assert p.primary_fires is True


def test_primary_b_fails_when_b_drops_just_under_threshold():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.7, b8=0.56, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    # delta = -0.14, just above threshold (-0.15)
    assert p.delta_b_minus_a_h8 == pytest.approx(-0.14, abs=1e-9)
    assert p.b_passes is False
    assert p.primary_fires is False


def test_primary_b_passes_at_exact_threshold():
    m = _load_audit()
    # Pick values where the float subtraction is exact (multiples of 1/8).
    per_arm = _make_per_arm(m, a0=0.625, a8=0.625, b0=0.625, b8=0.475, c0=0.625, c8=0.625)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_b_minus_a_h8 == pytest.approx(-0.15, abs=1e-12)
    assert p.b_passes is True


def test_primary_c_fails_when_c_drops_too_far():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.5, c8=0.5)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_c_minus_a_h8 == pytest.approx(-0.2)
    assert p.c_passes is False  # |-0.2| > 0.10
    assert p.primary_fires is False


def test_primary_c_passes_at_exact_tolerance():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.5, b8=0.5, c0=0.7, c8=0.6)
    p = m.evaluate_primary_test(per_arm)
    assert p.delta_c_minus_a_h8 == pytest.approx(-0.1)
    assert p.c_passes is True  # |-0.1| <= 0.10 exactly


def test_secondary_hazard_amplified_when_h8_delta_larger():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.65, b8=0.5, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.delta_b_minus_a_h0 == pytest.approx(-0.05)
    assert s.delta_b_minus_a_h8 == pytest.approx(-0.2)
    assert s.hazard_amplified is True
    assert s.secondary_fires is True  # primary fires AND hazard amplified


def test_secondary_does_not_fire_when_primary_does_not_fire():
    m = _load_audit()
    per_arm = _make_per_arm(m, a0=0.7, a8=0.7, b0=0.65, b8=0.65, c0=0.7, c8=0.7)
    p = m.evaluate_primary_test(per_arm)
    assert p.primary_fires is False
    s = m.evaluate_secondary_test(per_arm, p)
    assert s.secondary_fires is False  # primary did not fire -> secondary off


# ---------------------------------------------------------------------------
# Verdict three-way mapping
# ---------------------------------------------------------------------------


def _make_primary_synth(m, *, b8, c8, a8=0.7) -> object:
    """Build a PrimaryTestRow with given B and C shares at h=8."""
    delta_b = b8 - a8
    delta_c = c8 - a8
    return m.PrimaryTestRow(
        a_share_h8=a8,
        b_share_h8=b8,
        c_share_h8=c8,
        delta_b_minus_a_h8=delta_b,
        delta_c_minus_a_h8=delta_c,
        b_passes=delta_b <= -m.PRIMARY_B_REDUCTION_THRESHOLD,
        c_passes=abs(delta_c) <= m.PRIMARY_C_TOLERANCE,
        primary_fires=(delta_b <= -m.PRIMARY_B_REDUCTION_THRESHOLD)
        and abs(delta_c) <= m.PRIMARY_C_TOLERANCE,
    )


def _make_secondary_synth(m) -> object:
    """Stub secondary for verdict tests; secondary_fires false."""
    return m.SecondaryTestRow(
        delta_b_minus_a_h0=0.0,
        delta_b_minus_a_h8=0.0,
        abs_delta_h0=0.0,
        abs_delta_h8=0.0,
        hazard_amplified=False,
        secondary_fires=False,
    )


def test_verdict_necessity_supported():
    m = _load_audit()
    # B drops by 0.20, C stays within tolerance.
    p = _make_primary_synth(m, b8=0.5, c8=0.7)
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_NECESSITY
    assert v.locked_phrase == m.LOCKED_NECESSITY_PHRASE


def test_verdict_general_disruption():
    m = _load_audit()
    # B drops by 0.20, C also drops by 0.20.
    p = _make_primary_synth(m, b8=0.5, c8=0.5)
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_DISRUPTION
    assert v.locked_phrase == m.LOCKED_DISRUPTION_PHRASE


def test_verdict_not_necessary_when_b_does_not_drop():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.7, c8=0.7)  # no drop
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_NOT_NECESSARY
    assert v.locked_phrase == m.LOCKED_NOT_NECESSARY_PHRASE


def test_verdict_not_necessary_when_b_rises():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.8, c8=0.7)  # B rises above A
    s = _make_secondary_synth(m)
    v = m.evaluate_verdict(p, s)
    assert v.verdict == m.VERDICT_NOT_NECESSARY


def test_verdict_c_rises_above_a_guard_halts_loud():
    m = _load_audit()
    p = _make_primary_synth(m, b8=0.5, c8=0.85)  # C +0.15 above A
    s = _make_secondary_synth(m)
    with pytest.raises(m.lr.LineageReplayError, match=r"C-rises-above-A guard"):
        m.evaluate_verdict(p, s)


# ---------------------------------------------------------------------------
# Synthetic events.jsonl reduction
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


def _died_event(*, agent_id, cause, tick) -> dict:
    return {
        "tick": tick,
        "type": "AgentDied",
        "event": {"agent_id": agent_id, "cause": cause, "tick": tick},
    }


def _summary_event(*, lineage_id, n_killed, role, effective_tick=51) -> dict:
    return {
        "tick": effective_tick,
        "type": "LineageKilledByIntervention",
        "event": {
            "lineage_id": lineage_id,
            "n_killed": n_killed,
            "lineage_role": role,
            "intervention_tick": 50,
            "effective_tick": effective_tick,
        },
    }


def _build_run(tmp_path, m, arm: str, hazard: int, seed: int, events: list[dict]) -> Path:
    p = m.SWEEP_ROOT / m._ARM_DIRS[arm][hazard] / f"seed-{seed}" / "events.jsonl"
    actual_path = tmp_path / p.relative_to("runs")
    _write_events(actual_path, events)
    return actual_path


def test_reduce_one_run_a_null_zero_intervention_no_post50_births(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-41" / "events.jsonl"
    _write_events(p, [])  # empty events stream

    row = m._reduce_one_run(m.ARM_A_NULL, 8, 41)
    assert row.fired is False
    assert row.lineage_id is None
    assert row.n_killed == 0
    assert row.total_post_50_births_among_survivors == 0
    # 0 post-50 births -> NaN share
    import math

    assert math.isnan(row.post_intervention_top_lineage_b50_share)


def test_reduce_one_run_a_null_with_summary_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    events = [_summary_event(lineage_id=0, n_killed=2, role=m.ROLE_LEADER)]
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    with pytest.raises(m.lr.LineageReplayError, match=r"H2b.*A_null"):
        m._reduce_one_run(m.ARM_A_NULL, 8, 41)


def test_reduce_one_run_b_no_summary_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_B_KILL_LEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, [])

    with pytest.raises(m.lr.LineageReplayError, match=r"H2b.*B_kill_leader"):
        m._reduce_one_run(m.ARM_B_KILL_LEADER, 8, 41)


def test_reduce_one_run_b_role_mismatch_halts_h2b(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    events = [
        _summary_event(lineage_id=0, n_killed=1, role=m.ROLE_SMNONLEADER),  # wrong role
        _died_event(agent_id=10, cause="INTERVENTION", tick=51),
    ]
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_B_KILL_LEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    with pytest.raises(m.lr.LineageReplayError, match=r"H2b role mismatch"):
        m._reduce_one_run(m.ARM_B_KILL_LEADER, 8, 41)


def test_reduce_one_run_b_effective_tick_drift_halts_h2c(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    events = [
        _summary_event(lineage_id=0, n_killed=1, role=m.ROLE_LEADER, effective_tick=52),
    ]
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_B_KILL_LEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    with pytest.raises(m.lr.LineageReplayError, match=r"H2c effective_tick"):
        m._reduce_one_run(m.ARM_B_KILL_LEADER, 8, 41)


def test_reduce_one_run_b_n_killed_mismatch_halts_h2d(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    # summary says n_killed=2 but only one AgentDied(INTERVENTION) at tick 51
    events = [
        _summary_event(lineage_id=0, n_killed=2, role=m.ROLE_LEADER),
        _died_event(agent_id=10, cause="INTERVENTION", tick=51),
    ]
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_B_KILL_LEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    with pytest.raises(m.lr.LineageReplayError, match=r"H2d conservation mismatch"):
        m._reduce_one_run(m.ARM_B_KILL_LEADER, 8, 41)


def test_reduce_one_run_c_no_summary_records_control_unavailable(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_C_KILL_SMNONLEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, [])  # no summary => control_unavailable

    row = m._reduce_one_run(m.ARM_C_KILL_SMNONLEADER, 8, 41)
    assert row.fired is False
    assert row.control_unavailable is True


def test_reduce_one_run_share_arithmetic_excludes_killed_lineage(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    # Killed lineage 0; surviving lineages 1, 2, 3, 4.
    # Post-50 births: lineage 1 has 6, lineage 2 has 3, lineage 3 has 1, lineage 4 has 0,
    # lineage 0 (killed) has 5 births that would have happened (we exclude them).
    # Top surviving = lineage 1 with 6; total surviving = 10; share = 0.6.
    events: list[dict] = [
        _summary_event(lineage_id=0, n_killed=2, role=m.ROLE_LEADER),
        _died_event(agent_id=100, cause="INTERVENTION", tick=51),
        _died_event(agent_id=101, cause="INTERVENTION", tick=51),
    ]
    aid = 200
    for lid, n in [(0, 5), (1, 6), (2, 3), (3, 1)]:
        for _ in range(n):
            events.append(_born_event(agent_id=aid, lineage_id=lid, tick=60))
            aid += 1
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_B_KILL_LEADER][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    row = m._reduce_one_run(m.ARM_B_KILL_LEADER, 8, 41)
    # Post-50 births among survivors: lineage 1=6, 2=3, 3=1 -> total 10.
    # Top = lineage 1 with 6 -> share = 0.6.
    assert row.total_post_50_births_among_survivors == 10
    assert row.top_lineage_post50_births == 6
    assert row.post_intervention_top_lineage_b50_share == pytest.approx(0.6)


def test_reduce_one_run_share_excludes_pre_50_births(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "fear-hunger-v0.42-tight_gradient" / "arms")
    # Pre-50 births should NOT count.
    events: list[dict] = [
        _born_event(agent_id=200, lineage_id=1, tick=50),  # tick==50, not > 50; excluded
        _born_event(agent_id=201, lineage_id=1, tick=49),  # excluded
        _born_event(agent_id=202, lineage_id=1, tick=51),  # included
        _born_event(agent_id=203, lineage_id=2, tick=51),  # included
    ]
    p = m.SWEEP_ROOT / m._ARM_DIRS[m.ARM_A_NULL][8] / "seed-41" / "events.jsonl"
    _write_events(p, events)

    row = m._reduce_one_run(m.ARM_A_NULL, 8, 41)
    assert row.total_post_50_births_among_survivors == 2
    assert row.top_lineage_post50_births == 1
    assert row.post_intervention_top_lineage_b50_share == pytest.approx(0.5)


def test_assert_sweep_present_halts_on_missing(tmp_path, monkeypatch):
    m = _load_audit()
    monkeypatch.setattr(m, "SWEEP_ROOT", tmp_path / "missing-sweep")
    with pytest.raises(m.lr.LineageReplayError, match=r"sweep incomplete"):
        m.assert_sweep_present()
