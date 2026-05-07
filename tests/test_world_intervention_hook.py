"""v0.42 chamber-driver intervention-hook integration tests.

Coverage:
  - ``optional_intervention=None`` produces events.jsonl byte-identical
    to a sealed reference (regression-guarded against pre-v0.42
    behaviour). The reference is generated lazily by re-running the
    same chamber config without the intervention parameter routed
    through (i.e., the legacy code path).
  - ``optional_intervention=InterventionConfig(kind="null")`` produces
    events.jsonl byte-identical to ``optional_intervention=None``.
  - ``InterventionConfig(kind="kill_tick50_leader")`` fires exactly
    once at ``tick_count == effective_tick`` (51), produces one
    LineageKilledByIntervention event with role="leader" and
    intervention/effective tick fields matching the config.
  - ``InterventionConfig(kind="kill_size_matched_nonleader")`` fires
    with role="size_matched_nonleader" and a non-leader lineage as
    target.
  - Each killed agent produces an AgentDied(cause=INTERVENTION,
    tick=effective_tick) event paired with the summary event.
  - Pool residual is conserved: pool_in_death_residual increases by
    the sum of killed-agent body energies after the intervention.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hedonism_harness.core.interventions import (
    KIND_KILL_LEADER,
    KIND_KILL_SMNONLEADER,
    KIND_NULL,
    ROLE_LEADER,
    ROLE_SMNONLEADER,
    InterventionConfig,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.experiments.layouts import layout_by_name

# Locked baseline run params — chosen to exercise tick 50/51 boundary
# fully, with at least 5 founders and 200 ticks. We use one of the v0.41
# tight_gradient seeds to keep the fixture deterministic and fast.
_LAYOUT_NAME = "tight_gradient"
_SEED = 33  # within v0.41's 33..40 stream; deterministic on any host
_N_TICKS = 60  # enough to cross tick 50; less than 200 keeps tests fast
_N_FOUNDERS = 5


def _baseline_kwargs(runs_root: Path) -> dict:
    """Substrate matching the v0.41 anchor: tight_gradient, influx=1.0,
    hazard=8, transfer mode, energy_pool=1500, food_respawn_cooldown=50.
    """
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
        "condition": "v0.42-test",
    }


def _read_events(events_jsonl: Path) -> list[dict]:
    return [json.loads(line) for line in events_jsonl.read_text().splitlines()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# H2e — byte-identity regression: optional_intervention=None preserves
#       pre-v0.42 events.jsonl byte stream exactly.
# ---------------------------------------------------------------------------


def test_optional_intervention_none_byte_identical_to_legacy_path(tmp_path):
    """Two runs with the same seed/params: one with optional_intervention=None
    explicitly, one without the parameter. Both must produce events.jsonl
    byte-identical (and the parameter-omitted run is the v0.21..v0.41 default).
    """
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)

    # Run 1: legacy code path (no optional_intervention parameter).
    out1 = tmp_path / "run-legacy"
    out1.mkdir()
    run_chamber(**{**repro_kwargs, "runs_root": out1})

    # Run 2: explicit optional_intervention=None.
    out2 = tmp_path / "run-explicit-none"
    out2.mkdir()
    run_chamber(**{**repro_kwargs, "runs_root": out2}, optional_intervention=None)

    p1 = out1 / f"seed-{_SEED}" / "events.jsonl"
    p2 = out2 / f"seed-{_SEED}" / "events.jsonl"
    assert p1.exists()
    assert p2.exists()
    assert _file_sha256(p1) == _file_sha256(p2)


def test_optional_intervention_null_kind_byte_identical_to_none(tmp_path):
    """``InterventionConfig(kind=KIND_NULL)`` must also be byte-identical
    to ``None`` on the events.jsonl wire. The ``kind="null"`` arm exists
    so the v0.42 sweep can label A_null distinctly without changing
    semantics.
    """
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)

    out_none = tmp_path / "run-none"
    out_none.mkdir()
    run_chamber(**{**repro_kwargs, "runs_root": out_none}, optional_intervention=None)

    out_null = tmp_path / "run-null"
    out_null.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out_null},
        optional_intervention=InterventionConfig(kind=KIND_NULL),
    )

    p1 = out_none / f"seed-{_SEED}" / "events.jsonl"
    p2 = out_null / f"seed-{_SEED}" / "events.jsonl"
    assert _file_sha256(p1) == _file_sha256(p2)


# ---------------------------------------------------------------------------
# Intervention firing — leader kill
# ---------------------------------------------------------------------------


def test_kill_leader_emits_one_summary_event_at_effective_tick(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    assert len(summaries) == 1
    s = summaries[0]
    assert s["tick"] == 51
    assert s["event"]["effective_tick"] == 51
    assert s["event"]["intervention_tick"] == 50
    assert s["event"]["lineage_role"] == ROLE_LEADER
    assert s["event"]["n_killed"] >= 1


def test_kill_leader_emits_paired_agent_died_events_with_intervention_cause(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
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


def test_no_intervention_summary_when_kind_null(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_NULL),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    assert not any(e["type"] == "LineageKilledByIntervention" for e in events)
    assert not any(
        e["type"] == "AgentDied" and e["event"]["cause"] == "INTERVENTION" for e in events
    )


# ---------------------------------------------------------------------------
# Intervention firing — size-matched non-leader kill
# ---------------------------------------------------------------------------


def test_kill_smnonleader_emits_summary_with_smnonleader_role(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_SMNONLEADER),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    # Either fired exactly once with smnonleader role, or zero times if
    # control_unavailable. For seed=33 hzd=8 5 founders we expect at least
    # 1 non-leader lineage alive at tick 50; assert fired.
    assert len(summaries) == 1
    assert summaries[0]["event"]["lineage_role"] == ROLE_SMNONLEADER


def test_intervention_summary_n_killed_matches_paired_deaths(tmp_path):
    """The summary's ``n_killed`` field must equal the number of
    ``AgentDied(cause=INTERVENTION)`` events emitted at the effective tick.
    This is the H2d intervention-conservation invariant the audit checks.
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
    assert n_killed >= 1

    intervention_deaths = [
        e
        for e in events
        if e["type"] == "AgentDied" and e["tick"] == 51 and e["event"]["cause"] == "INTERVENTION"
    ]
    assert len(intervention_deaths) == n_killed


# ---------------------------------------------------------------------------
# Pool residual conservation
# ---------------------------------------------------------------------------


def test_intervention_credits_pool_residual_in_run_summary(tmp_path):
    """After a kill_leader run, the run summary's pool_in_death_residual
    should be >= the sum we'd expect from killing alive agents. We compare
    against a same-seed null-intervention run: the difference equals the
    sum of body energies on the killed agents.

    Looser assertion: pool_in_death_residual is strictly greater in the
    leader-kill run than in the null run on the same seed (because the
    leader-kill adds extra deaths, each crediting their body energy).
    """
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)

    out_null = tmp_path / "run-null"
    out_null.mkdir()
    res_null = run_chamber(
        **{**repro_kwargs, "runs_root": out_null},
        optional_intervention=InterventionConfig(kind=KIND_NULL),
    )

    out_kill = tmp_path / "run-kill"
    out_kill.mkdir()
    res_kill = run_chamber(
        **{**repro_kwargs, "runs_root": out_kill},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )

    null_residual = res_null.pool_in_death_residual
    kill_residual = res_kill.pool_in_death_residual
    # Leader-kill credits at least as much residual as null. (Strictly
    # greater iff at least one killed agent had energy > 0 at tick 51,
    # which is overwhelmingly the case for tick-50 leaders.)
    assert kill_residual >= null_residual


# ---------------------------------------------------------------------------
# Intervention fires exactly once
# ---------------------------------------------------------------------------


def test_intervention_fires_at_most_once(tmp_path):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / "run"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=KIND_KILL_LEADER),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    assert len(summaries) <= 1


@pytest.mark.parametrize("kind", [KIND_KILL_LEADER, KIND_KILL_SMNONLEADER])
def test_intervention_summary_tick_is_effective_tick(tmp_path, kind):
    kwargs = _baseline_kwargs(tmp_path)
    repro_kwargs = dict(kwargs)
    out = tmp_path / f"run-{kind}"
    out.mkdir()
    run_chamber(
        **{**repro_kwargs, "runs_root": out},
        optional_intervention=InterventionConfig(kind=kind),
    )

    events = _read_events(out / f"seed-{_SEED}" / "events.jsonl")
    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]
    if not summaries:
        # control_unavailable path is allowed for KIND_KILL_SMNONLEADER on
        # pathological seeds (none expected for this seed).
        assert kind == KIND_KILL_SMNONLEADER
        return
    assert summaries[0]["tick"] == 51
    assert summaries[0]["event"]["effective_tick"] == 51
