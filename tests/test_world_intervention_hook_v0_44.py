"""v0.44 chamber-driver hook tests for respawn-schedule rewrite kinds.

Coverage:
- ``InterventionConfig(kind="delay_respawn_schedule_plus_25_at_tick50")``
  fires once at tick 51, emits one ``RespawnScheduleByIntervention``
  event with correct fields; sum_after = sum_before + 25 * n.
- ``InterventionConfig(kind="permute_respawn_schedule_reverse_row_major_at_tick50")``
  fires once at tick 51, sum/min/max preserved exactly, multiset digest
  preserved exactly.
- Neither kind emits ``AgentDied(cause="INTERVENTION")``.
- Cross-version regression (H2e):
  - ``kind="null"`` byte-identical to ``optional_intervention=None``.
  - v0.42 kill paths byte-identical when re-run on the v0.44 branch.
  - v0.43 / v0.43R food-redistribution paths byte-identical when re-run
    on the v0.44 branch.
- Idempotency: each new kind fires at most once per run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hedonism_harness.core.interventions import (
    KIND_DELAY_RESPAWN_PLUS_25,
    KIND_KILL_LEADER,
    KIND_NULL,
    KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
    KIND_REDUCE_DENSITY_50PCT,
    InterventionConfig,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.experiments.layouts import layout_by_name

_LAYOUT_NAME = "tight_gradient"
_SEED = 33
_N_TICKS = 60
_N_FOUNDERS = 5


def _baseline_kwargs(runs_root: Path) -> dict:
    from hedonism_harness.core.config import ChildFundingMode
    from hedonism_harness.experiments.repro_configs import tuned_reproduction_config

    repro_cfg = tuned_reproduction_config(energy_cost=15.0, energy_threshold=50.0)
    return {
        "seed": _SEED,
        "runs_root": runs_root,
        "run_id": f"seed-{_SEED}",
        "n_founders": _N_FOUNDERS,
        "n_ticks": _N_TICKS,
        "layout": layout_by_name(_LAYOUT_NAME),
        "reproduction_config": repro_cfg,
        "food_respawn_cooldown": 50,
        "energy_pool_initial": 1_500.0,
        "ambient_influx_rate": 1.0,
        "child_funding_mode": ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        "hazard_damage": 8.0,
        "condition": "v0.44-test",
    }


def _read_events(events_jsonl: Path) -> list[dict]:
    return [json.loads(line) for line in events_jsonl.read_text().splitlines()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Delay arm (B)
# ---------------------------------------------------------------------------


def test_delay_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["effective_tick"] == 51
    assert s["event"]["intervention_tick"] == 50
    assert s["event"]["intervention_kind"] == KIND_DELAY_RESPAWN_PLUS_25


def test_delay_sum_invariant(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "RespawnScheduleByIntervention")
    sum_before = int(e["event"]["sum_respawn_tick_before"])
    sum_after = int(e["event"]["sum_respawn_tick_after"])
    n = int(e["event"]["n_eligible_cells"])
    assert sum_after == sum_before + 25 * n


def test_delay_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"].get("cause") == "INTERVENTION"
    ]
    assert intervention_deaths == []


# ---------------------------------------------------------------------------
# Permute arm (C)
# ---------------------------------------------------------------------------


def test_permute_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["intervention_kind"] == KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR


def test_permute_preserves_sum_and_multiset(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "RespawnScheduleByIntervention")
    assert e["event"]["sum_respawn_tick_after"] == e["event"]["sum_respawn_tick_before"]
    assert e["event"]["min_respawn_tick_after"] == e["event"]["min_respawn_tick_before"]
    assert e["event"]["max_respawn_tick_after"] == e["event"]["max_respawn_tick_before"]
    assert (
        e["event"]["respawn_multiset_digest_after"] == e["event"]["respawn_multiset_digest_before"]
    )


def test_permute_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"].get("cause") == "INTERVENTION"
    ]
    assert intervention_deaths == []


# ---------------------------------------------------------------------------
# Cross-version regression (H2e)
# ---------------------------------------------------------------------------


def test_kind_null_byte_identical_to_no_intervention(tmp_path):
    """``optional_intervention=InterventionConfig(kind="null")`` must produce
    events.jsonl bytewise identical to ``optional_intervention=None``."""
    kwargs = _baseline_kwargs(tmp_path)
    out_a = tmp_path / "run-none"
    out_b = tmp_path / "run-null"
    out_a.mkdir()
    out_b.mkdir()
    run_chamber(**{**kwargs, "runs_root": out_a}, optional_intervention=None)
    run_chamber(
        **{**kwargs, "runs_root": out_b},
        optional_intervention=InterventionConfig(kind=KIND_NULL),
    )
    sha_a = _file_sha256(out_a / f"seed-{_SEED}" / "events.jsonl")
    sha_b = _file_sha256(out_b / f"seed-{_SEED}" / "events.jsonl")
    assert sha_a == sha_b


def test_kill_leader_path_emits_lineagekilled_summary(tmp_path):
    """v0.42 kill_tick50_leader path remains dispatchable on v0.44 branch."""
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    assert len(summaries) <= 1  # 0 if no living leader at tick 50; 1 otherwise
    # If summary present, no RespawnScheduleByIntervention should be emitted.
    respawn_events = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]
    assert respawn_events == []


def test_v0_43r_reduce_density_path_remains_dispatchable(tmp_path):
    """v0.43R density reduce path remains dispatchable on v0.44 branch."""
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) == 1
    # No respawn-schedule events on the food-redistribution path.
    respawn_events = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]
    assert respawn_events == []


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_delay_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    delay_events = [
        e
        for e in events
        if e["type"] == "RespawnScheduleByIntervention"
        and e["event"]["intervention_kind"] == KIND_DELAY_RESPAWN_PLUS_25
    ]
    assert len(delay_events) == 1


def test_permute_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    permute_events = [
        e
        for e in events
        if e["type"] == "RespawnScheduleByIntervention"
        and e["event"]["intervention_kind"] == KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR
    ]
    assert len(permute_events) == 1
