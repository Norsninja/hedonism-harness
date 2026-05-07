"""v0.43R chamber-driver hook tests for density-reduction +
density-preserving perturbation kinds.

Coverage:
- ``InterventionConfig(kind="reduce_food_density_50pct_at_tick50")``
  fires once at tick 51, emits one ``FoodRedistributedByIntervention``
  event with correct fields; total food halves.
- ``InterventionConfig(kind="density_preserving_perturbation_at_tick50")``
  fires once at tick 51, total food preserved exactly.
- Neither kind emits ``AgentDied(cause="INTERVENTION")``.
- Cross-version regression (H2e):
  - ``kind="null"`` byte-identical to ``optional_intervention=None``.
  - ``kind="kill_tick50_leader"`` produces v0.42-shaped events.jsonl
    (single LineageKilledByIntervention summary at tick 51, paired
    AgentDied count == n_killed).
- Idempotency: each new kind fires at most once per run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hedonism_harness.core.interventions import (
    KIND_DENSITY_PRESERVING_PERTURBATION,
    KIND_KILL_LEADER,
    KIND_NULL,
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
        "condition": "v0.43R-test",
    }


def _read_events(events_jsonl: Path) -> list[dict]:
    return [json.loads(line) for line in events_jsonl.read_text().splitlines()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Reduce-density arm
# ---------------------------------------------------------------------------


def test_reduce_density_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["effective_tick"] == 51
    assert s["event"]["intervention_tick"] == 50
    assert s["event"]["intervention_kind"] == KIND_REDUCE_DENSITY_50PCT


def test_reduce_density_halves_total_food(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    before = float(e["event"]["total_food_before"])
    after = float(e["event"]["total_food_after"])
    expected_after = 0.5 * before
    tol = max(1e-3, 1e-5 * before)
    assert abs(after - expected_after) <= tol


def test_reduce_density_changes_multiset_at_h8_substrate(tmp_path):
    """At h=8 tick 50 the substrate is saturated (every cell at 20).
    Halving sets every cell to 10 — multiset transitions from {20x24} to
    {10x24}. Digest must change.
    """
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    assert e["event"]["food_multiset_digest_before"] != e["event"]["food_multiset_digest_after"]


def test_reduce_density_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"]["cause"] == "INTERVENTION"
    ]
    assert intervention_deaths == []


def test_reduce_density_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) <= 1


# ---------------------------------------------------------------------------
# Density-preserving perturbation arm
# ---------------------------------------------------------------------------


def test_perturbation_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["intervention_kind"] == KIND_DENSITY_PRESERVING_PERTURBATION


def test_perturbation_preserves_total_food_within_tolerance(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    before = float(e["event"]["total_food_before"])
    after = float(e["event"]["total_food_after"])
    tol = max(1e-3, 1e-5 * before)
    assert abs(after - before) <= tol


def test_perturbation_changes_multiset_at_h8_substrate(tmp_path):
    """At h=8 the substrate is uniform (24 x 20). Pair (20, 20) -> (10, 30).
    Multiset transitions from {20x24} to {10x12, 30x12}. Digest changes.
    """
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    assert e["event"]["food_multiset_digest_before"] != e["event"]["food_multiset_digest_after"]


def test_perturbation_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"]["cause"] == "INTERVENTION"
    ]
    assert intervention_deaths == []


def test_perturbation_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) <= 1


# ---------------------------------------------------------------------------
# Cross-version regression (H2e) — v0.42 paths byte-identical on v0.43R branch
# ---------------------------------------------------------------------------


def test_h2e_kind_null_byte_identical_to_none_on_v0_43r_branch(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out_none = tmp_path / "run-none"
    out_none.mkdir()
    run_chamber(**{**kwargs, "runs_root": out_none}, optional_intervention=None)

    out_null = tmp_path / "run-null"
    out_null.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out_null},
        optional_intervention=InterventionConfig(kind=KIND_NULL),
    )

    p1 = out_none / f"seed-{_SEED}" / "events.jsonl"
    p2 = out_null / f"seed-{_SEED}" / "events.jsonl"
    assert _file_sha256(p1) == _file_sha256(p2)


def test_h2e_kill_leader_path_unchanged_on_v0_43r_branch(tmp_path):
    """The v0.42 leader-kill code path must produce v0.42-shaped events on
    v0.43R: exactly one LineageKilledByIntervention at tick 51, paired
    with AgentDied(INTERVENTION) count equal to n_killed. No
    FoodRedistributedByIntervention events on the kill path.
    """
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    assert len(summaries) == 1
    n_killed = summaries[0]["event"]["n_killed"]
    intervention_deaths = [
        e
        for e in events
        if e["type"] == "AgentDied" and e["tick"] == 51 and e["event"]["cause"] == "INTERVENTION"
    ]
    assert len(intervention_deaths) == n_killed
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert food_events == []
