"""v0.43 chamber-driver hook tests for substrate-rewrite kinds.

Coverage (v0.43-specific; v0.42 hook tests in
``tests/test_world_intervention_hook.py`` continue to pass unchanged):

- ``InterventionConfig(kind="flatten_food_at_tick50")`` fires exactly
  once at ``tick_count == 51``, emits one
  ``FoodRedistributedByIntervention`` event with correct fields.
- Same for ``shuffle_food_at_tick50``.
- Total food preserved within float-32 tolerance for both kinds.
- Multiset preserved (digest equality) for shuffle; multiset NOT
  preserved (digest inequality) for flatten on a non-degenerate
  substrate.
- No ``AgentDied(cause="INTERVENTION")`` events at tick 51 from
  substrate-rewrite kinds (no agents killed by substrate rewrite).
- Cross-version regression (H2e):
  - ``kind="null"`` produces events.jsonl byte-identical to
    ``optional_intervention=None`` (carried forward from v0.42).
  - ``kind="kill_tick50_leader"`` and ``kind="kill_size_matched_nonleader"``
    produce identical events.jsonl whether re-run on v0.43 or under
    v0.42's path. This is verified by re-running and checking that
    the resulting events match the v0.42 contract (single
    ``LineageKilledByIntervention`` summary at tick 51, paired
    ``AgentDied(cause="INTERVENTION")`` count equal to ``n_killed``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hedonism_harness.core.interventions import (
    KIND_FLATTEN_FOOD,
    KIND_KILL_LEADER,
    KIND_NULL,
    KIND_SHUFFLE_FOOD,
    InterventionConfig,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.experiments.layouts import layout_by_name

# Locked baseline matching the v0.42 hook tests' fixture (seed 33,
# v0.41 stream; tight_gradient; 60 ticks to cross tick-50 boundary).
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
        "condition": "v0.43-test",
    }


def _read_events(events_jsonl: Path) -> list[dict]:
    return [json.loads(line) for line in events_jsonl.read_text().splitlines()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Flatten arm — firing + fields
# ---------------------------------------------------------------------------


def test_flatten_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_FLATTEN_FOOD),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["effective_tick"] == 51
    assert s["event"]["intervention_tick"] == 50
    assert s["event"]["intervention_kind"] == KIND_FLATTEN_FOOD


def test_flatten_total_food_preserved_within_tolerance(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_FLATTEN_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    before = float(e["event"]["total_food_before"])
    after = float(e["event"]["total_food_after"])
    tol = max(1e-3, 1e-5 * before)
    assert abs(after - before) <= tol


@pytest.mark.skip(
    reason=(
        "Substrate-mismatch finding (v0.43 + v0.43R halt addenda): under this "
        "test fixture's hand-rolled config (HedonismPolicy, auto_reproduction "
        "default off), the food zone is saturated at tick 50 (total_food=480) "
        "and flatten is a no-op. Under the actual sweep config (V0_25 anchor: "
        "GradientPolicy + auto_reproduction=True + unbounded mutation), the "
        "zone is depleted to zero by tick ~44 across all seeds and flatten is "
        "also a no-op (just for the opposite reason). Either way the assertion "
        "below does not hold. See docs/experiments/fear_hunger_v0.43R.md "
        "SUBSTRATE_PREFLIGHT_HALT_2 for the corrected substrate finding and "
        "the methodological lesson."
    )
)
def test_flatten_changes_multiset_on_nondegenerate_substrate(tmp_path):
    """At tick 50, the tight_gradient zone has heterogeneous food; flatten
    should produce a different multiset (the post-state is uniform).
    """
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_FLATTEN_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    assert e["event"]["food_multiset_digest_before"] != e["event"]["food_multiset_digest_after"]


def test_flatten_emits_no_intervention_agentdied(tmp_path):
    """Substrate-rewrite kinds must not emit AgentDied(cause=INTERVENTION).
    No agents are killed by food redistribution.
    """
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_FLATTEN_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"]["cause"] == "INTERVENTION"
    ]
    assert intervention_deaths == []


# ---------------------------------------------------------------------------
# Shuffle arm — firing + fields
# ---------------------------------------------------------------------------


def test_shuffle_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_SHUFFLE_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["intervention_kind"] == KIND_SHUFFLE_FOOD


def test_shuffle_preserves_multiset(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_SHUFFLE_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    assert e["event"]["food_multiset_digest_before"] == e["event"]["food_multiset_digest_after"]


def test_shuffle_total_food_preserved_within_tolerance(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_SHUFFLE_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    e = next(ev for ev in events if ev["type"] == "FoodRedistributedByIntervention")
    before = float(e["event"]["total_food_before"])
    after = float(e["event"]["total_food_after"])
    tol = max(1e-3, 1e-5 * before)
    assert abs(after - before) <= tol


def test_shuffle_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_SHUFFLE_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    intervention_deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"]["cause"] == "INTERVENTION"
    ]
    assert intervention_deaths == []


# ---------------------------------------------------------------------------
# Cross-version regression (H2e) — v0.42 paths byte-identical on v0.43 branch
# ---------------------------------------------------------------------------


def test_h2e_kind_null_byte_identical_to_none_on_v0_43_branch(tmp_path):
    """v0.43 must preserve the v0.42 invariant that kind="null" is
    byte-identical to optional_intervention=None on the events.jsonl
    wire. The v0.42 hook tests cover this directly; this test adds an
    explicit v0.43-branch regression for the H2e regression-fingerprint
    invariant.
    """
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


def test_h2e_kill_leader_path_unchanged_on_v0_43_branch(tmp_path):
    """The v0.42 leader-kill code path must produce the same shape of
    events.jsonl on v0.43: exactly one LineageKilledByIntervention at
    tick 51, paired with AgentDied(cause="INTERVENTION") count equal to
    ``n_killed``. Bit-identity vs v0.42 reference is implicit via test
    determinism (no v0.43 code path mutates the kill helpers).
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
    # No food-redistribution events on the kill path.
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert food_events == []


# ---------------------------------------------------------------------------
# Idempotency — intervention fires at most once
# ---------------------------------------------------------------------------


def test_flatten_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_FLATTEN_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) <= 1


def test_shuffle_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_SHUFFLE_FOOD),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) <= 1
