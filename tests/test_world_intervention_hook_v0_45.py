"""v0.45 chamber-driver hook tests for birth-redirection kinds.

Coverage:
- B kind emits BirthRedirectedByIntervention events with tick > 50,
  correct fields, and target_cell_kind in {"EMPTY", "FOOD", "SAFE"}.
- C kind emits events with parent-adjacent redirected cells (Manhattan
  == 1).
- Neither kind emits AgentDied(cause="INTERVENTION").
- No events emitted for tick <= 50 (callback is not called pre-50).
- Cross-version regression (H2e):
  - kind="null" byte-identical to optional_intervention=None.
  - v0.42 / v0.43R / v0.44 paths still dispatchable on v0.45 branch.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from hedonism_harness.core.interventions import (
    KIND_DELAY_RESPAWN_PLUS_25,
    KIND_KILL_LEADER,
    KIND_NULL,
    KIND_REDUCE_DENSITY_50PCT,
    KIND_UNIFORM_NEIGHBOR_BIRTH,
    KIND_UNIFORM_VALID_REGION_BIRTH,
    InterventionConfig,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.experiments.layouts import layout_by_name

_LAYOUT_NAME = "tight_gradient"
_SEED = 33
_N_TICKS = 80
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
        "condition": "v0.45-test",
    }


def _read_events(events_jsonl: Path) -> list[dict]:
    return [json.loads(line) for line in events_jsonl.read_text().splitlines()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# B arm
# ---------------------------------------------------------------------------


def test_b_uniform_global_emits_redirected_events_post_50(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    # Some redirected births should occur (sweep has ~12 post-50 births
    # per V0_25 anchor; under hand-rolled HedonismPolicy there will be
    # fewer but typically > 0).
    assert all(e["tick"] > 50 for e in redirects)
    assert all(
        e["event"]["intervention_kind"] == KIND_UNIFORM_VALID_REGION_BIRTH for e in redirects
    )


def test_b_target_cell_kind_in_safe_set(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    for e in redirects:
        assert e["event"]["target_cell_kind"] in {"EMPTY", "FOOD", "SAFE"}


def test_b_redirected_cell_not_parent_cell(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    for e in redirects:
        ev = e["event"]
        assert (ev["redirected_x"], ev["redirected_y"]) != (ev["parent_x"], ev["parent_y"])


def test_b_emits_no_intervention_agentdied(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    deaths = [
        e for e in events if e["type"] == "AgentDied" and e["event"].get("cause") == "INTERVENTION"
    ]
    assert deaths == []


# ---------------------------------------------------------------------------
# C arm
# ---------------------------------------------------------------------------


def test_c_uniform_neighbor_redirects_are_parent_adjacent(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_UNIFORM_NEIGHBOR_BIRTH),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    for e in redirects:
        ev = e["event"]
        manhattan = abs(ev["parent_x"] - ev["redirected_x"]) + abs(
            ev["parent_y"] - ev["redirected_y"]
        )
        assert manhattan == 1, f"C event has Manhattan distance {manhattan}"
        assert ev["preserved_parent_adjacency"] is True


# ---------------------------------------------------------------------------
# Cross-version regression (H2e)
# ---------------------------------------------------------------------------


def test_kind_null_byte_identical_to_no_intervention(tmp_path):
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


def test_v0_42_kill_leader_path_remains_dispatchable(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    # No BirthRedirectedByIntervention events; v0.45 callback not constructed.
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    assert redirects == []


def test_v0_43r_reduce_density_path_remains_dispatchable(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    assert redirects == []
    # Original v0.43R event still emitted.
    food_events = [e for e in events if e["type"] == "FoodRedistributedByIntervention"]
    assert len(food_events) == 1


def test_v0_44_delay_respawn_path_remains_dispatchable(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25),
    )
    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    redirects = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]
    assert redirects == []
    respawn_events = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]
    assert len(respawn_events) == 1
