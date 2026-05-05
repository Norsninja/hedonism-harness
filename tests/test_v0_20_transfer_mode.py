"""Integration tests for v0.20 ChildFundingMode.PARENT_TRANSFER_POOL_GAP.

Covers:
  - Default (ChildFundingMode.POOL_FULL) preserves v0.19 byte-identity:
    no transfer accumulator increments, no v0.20 events emitted, pool
    debit = offspring_start_energy.
  - PARENT_TRANSFER_POOL_GAP cross-config validator: rejects inf-pool.
  - ReproductionConfig cross-field validator: rejects offspring < cost
    under transfer mode; accepts under POOL_FULL (preserves v0.19
    bare-default cost=35, offspring=30).
  - Per-birth pool debit amount: 30 (POOL_FULL) vs 15 (TRANSFER, gap).
  - Per-birth ledger accumulators: reproduction_heat_loss == cost * births
    under POOL_FULL; parent_energy_transferred_to_child == cost * births
    under TRANSFER; H4 invariant
    (parent_transferred + pool_out_child_startup == births * offspring).
  - BirthDeniedParentEnergy emission when parent's energy < energy_cost
    at process time; parent retains energy; pool untouched.
  - End-to-end negative control: closed-3000 PARENT_TRANSFER_POOL_GAP
    matches POOL_FULL on per-agent observables (agent state is mode-
    invariant when neither pool gate fires).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ChildFundingMode,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.events import BirthDeniedParentEnergy, PoolBirthDenied
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.experiments.layouts import food_ladder_layout
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.gradient_policy import GradientPolicy

# ---------------------------------------------------------------------------
# ReproductionConfig + cross-config validators
# ---------------------------------------------------------------------------


def test_default_child_funding_mode_is_pool_full() -> None:
    """v0.20 default preserves v0.19 by construction."""
    cfg = ReproductionConfig()
    assert cfg.child_funding_mode == ChildFundingMode.POOL_FULL


def test_pool_full_accepts_offspring_below_cost() -> None:
    """v0.7..v0.19 bare default has cost=35, offspring=30. The validator
    must allow this under POOL_FULL — it is heat-loss bookkeeping, not a
    pool-gap concern."""
    cfg = ReproductionConfig(
        energy_cost=35.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    )
    assert cfg.energy_cost == 35.0
    assert cfg.offspring_start_energy == 30.0


def test_transfer_mode_rejects_offspring_below_cost() -> None:
    """Negative pool gap is a v0.20 surplus regime not handled; rejected."""
    with pytest.raises(ValueError, match="offspring_start_energy"):
        ReproductionConfig(
            energy_cost=20.0,
            offspring_start_energy=15.0,
            child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        )


def test_transfer_mode_accepts_offspring_equal_to_cost() -> None:
    """Equal is legal — the gap is exactly zero, pool debit per birth is 0."""
    cfg = ReproductionConfig(
        energy_cost=20.0,
        offspring_start_energy=20.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    )
    assert cfg.energy_cost == cfg.offspring_start_energy


def _make_minimal_model(
    *,
    energy_pool_initial: float | None = 1000.0,
    food_respawn_cooldown: int | None = None,
    child_funding_mode: ChildFundingMode = ChildFundingMode.POOL_FULL,
    energy_cost: float = 15.0,
    offspring_start_energy: float = 30.0,
) -> HHModel:
    cfg = WorldConfig(
        seed=42,
        width=6,
        height=4,
        energy_pool_initial=energy_pool_initial,
        food_respawn_cooldown=food_respawn_cooldown,
    )
    founders = [FounderSpec(x=1, y=1, policy_factory=GradientPolicy)]
    return HHModel(
        cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(
            energy_cost=energy_cost,
            offspring_start_energy=offspring_start_energy,
            child_funding_mode=child_funding_mode,
        ),
    )


def test_hhmodel_rejects_transfer_mode_under_inf_pool() -> None:
    """Inf-pool (energy_pool_initial=None) under TRANSFER has no source for
    the gap top-up. Pre-reg pinned this as validator-rejected at chamber-
    driver / HHModel construction time."""
    cfg = WorldConfig(seed=0, width=4, height=4, energy_pool_initial=None)
    founders = [FounderSpec(x=1, y=1, policy_factory=GradientPolicy)]
    with pytest.raises(ValueError, match="PARENT_TRANSFER_POOL_GAP"):
        HHModel(
            cfg,
            founders=founders,
            body_config=BodyConfig(),
            action_config=ActionConfig(),
            reproduction_config=ReproductionConfig(
                energy_cost=15.0,
                offspring_start_energy=30.0,
                child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
            ),
        )


def test_hhmodel_accepts_transfer_mode_with_finite_pool() -> None:
    model = _make_minimal_model(
        energy_pool_initial=500.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    )
    assert model.energy_pool is not None
    assert model.reproduction_config.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP


# ---------------------------------------------------------------------------
# Per-birth pool debit amount + accumulators (the H1-H4 telemetry contract)
# ---------------------------------------------------------------------------


def _force_birth(model: HHModel, *, low_parent_energy: bool = False) -> None:
    """Drive one birth: queue the founder, then process the queue. The
    founder is forced into a state that satisfies all pre-checks; under
    ``low_parent_energy=True`` the parent's energy is below energy_cost
    so the new transfer-mode gate fires."""
    founder = next(iter(model.agents))
    energy = 8.0 if low_parent_energy else 80.0
    founder.body = founder.body.__class__(  # type: ignore[call-arg]
        id=founder.body.id,
        lineage_id=founder.body.lineage_id,
        parent_id=founder.body.parent_id,
        x=founder.body.x,
        y=founder.body.y,
        energy=energy,
        health=100.0,
        age=50,
        traits=founder.body.traits,
        alive=True,
        death_cause=None,
    )
    model.queue_birth(founder)
    model._process_birth_queue()


def test_pool_full_debit_amount_is_offspring_start_energy() -> None:
    """Under POOL_FULL the pool debits the full offspring_start_energy
    per birth (= 30 by v0.20 defaults). reproduction_heat_loss tracks
    the parent's destroyed energy_cost (= 15)."""
    model = _make_minimal_model(
        energy_pool_initial=500.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
        energy_cost=15.0,
        offspring_start_energy=30.0,
    )
    assert model.energy_pool is not None
    pool_before = model.energy_pool.current
    _force_birth(model)
    assert model.energy_pool.out_child_startup == 30.0
    assert model.energy_pool.current == pool_before - 30.0
    assert model.reproduction_heat_loss == 15.0
    assert model.parent_energy_transferred_to_child == 0.0
    assert model.births_blocked_by_parent_energy == 0


def test_transfer_mode_debit_amount_is_gap() -> None:
    """Under PARENT_TRANSFER_POOL_GAP the pool debits only the gap
    (offspring_start_energy - energy_cost = 15). The parent's
    energy_cost is accumulated as parent_energy_transferred_to_child;
    reproduction_heat_loss stays at zero."""
    model = _make_minimal_model(
        energy_pool_initial=500.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        energy_cost=15.0,
        offspring_start_energy=30.0,
    )
    assert model.energy_pool is not None
    pool_before = model.energy_pool.current
    _force_birth(model)
    assert model.energy_pool.out_child_startup == 15.0  # gap, not full
    assert model.energy_pool.current == pool_before - 15.0
    assert model.parent_energy_transferred_to_child == 15.0
    assert model.reproduction_heat_loss == 0.0
    assert model.births_blocked_by_parent_energy == 0


def test_transfer_mode_birth_denied_when_parent_under_cost() -> None:
    """The new transfer-mode gate fires when parent.energy < energy_cost.
    No state changes: parent retains energy, pool untouched, no child.
    Under POOL_FULL the same scenario would proceed (charge_parent floors
    at 0; v0.19 contract preserved)."""
    model = _make_minimal_model(
        energy_pool_initial=500.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        energy_cost=15.0,
        offspring_start_energy=30.0,
    )
    assert model.energy_pool is not None
    pool_before = model.energy_pool.current
    _force_birth(model, low_parent_energy=True)
    # Pool untouched.
    assert model.energy_pool.current == pool_before
    assert model.energy_pool.out_child_startup == 0.0
    # Parent retained energy (no charge_parent fired).
    founder = next(iter(model.agents))
    assert founder.body.energy == 8.0
    # Counter incremented; event emitted.
    assert model.births_blocked_by_parent_energy == 1
    denied = [le.event for le in model.event_log if isinstance(le.event, BirthDeniedParentEnergy)]
    assert len(denied) == 1
    # Accumulators unchanged.
    assert model.parent_energy_transferred_to_child == 0.0
    assert model.reproduction_heat_loss == 0.0


def test_pool_full_does_not_fire_parent_energy_gate() -> None:
    """Under POOL_FULL the parent-energy gate is bypassed entirely —
    charge_parent floors at 0, preserving v0.19 dynamics. A low-energy
    parent's birth still fires (and the parent ends at energy=0)."""
    model = _make_minimal_model(
        energy_pool_initial=500.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
        energy_cost=15.0,
        offspring_start_energy=30.0,
    )
    _force_birth(model, low_parent_energy=True)
    # POOL_FULL gate-bypass: birth fires, no v0.20 event.
    assert model.births_blocked_by_parent_energy == 0
    assert (
        len([le.event for le in model.event_log if isinstance(le.event, BirthDeniedParentEnergy)])
        == 0
    )
    # heat_loss accumulator does increment (one successful birth at cost=15).
    assert model.reproduction_heat_loss == 15.0


def test_transfer_mode_pool_birth_denied_preserves_parent_and_no_transfer() -> None:
    """When pool < gap the existing PoolBirthDenied path fires: parent
    retains energy, pool untouched, accumulators unchanged."""
    model = _make_minimal_model(
        energy_pool_initial=10.0,  # < gap=15
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        energy_cost=15.0,
        offspring_start_energy=30.0,
    )
    assert model.energy_pool is not None
    _force_birth(model)
    assert model.energy_pool.current == 10.0
    assert model.energy_pool.out_child_startup == 0.0
    assert model.energy_pool.blocked_count_child_startup == 1
    assert model.parent_energy_transferred_to_child == 0.0
    assert len([le.event for le in model.event_log if isinstance(le.event, PoolBirthDenied)]) == 1


# ---------------------------------------------------------------------------
# H4 invariant — multiple births
# ---------------------------------------------------------------------------


def test_h4_invariant_holds_under_transfer_multiple_births(tmp_path: Path) -> None:
    """``parent_energy_transferred_to_child + pool_out_child_startup ==
    total_births * offspring_start_energy`` under transfer mode, exactly,
    across a real chamber run with multiple births."""
    layout = food_ladder_layout()
    runs_root = tmp_path / "r"
    runs_root.mkdir()

    repro_cfg = ReproductionConfig(
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    )
    captured: dict[str, object] = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = True
        captured["model"] = model

    result = run_chamber(
        seed=1,
        runs_root=runs_root,
        run_id="seed-1",
        n_founders=5,
        n_ticks=80,
        layout=layout,
        policy_factory=GradientPolicy,
        reproduction_config=repro_cfg,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,  # comfortable, no blocks expected
        ambient_influx_rate=0.0,
        setup_observer=setup,
    )

    expected = result.births * repro_cfg.offspring_start_energy
    actual = result.parent_energy_transferred_to_child + result.pool_out_child_startup
    assert actual == pytest.approx(expected)
    # H1/H2/H3 sub-invariants:
    assert result.reproduction_heat_loss == 0.0
    assert result.parent_energy_transferred_to_child == result.births * repro_cfg.energy_cost
    if result.births > 0:
        gap = repro_cfg.offspring_start_energy - repro_cfg.energy_cost
        assert result.pool_out_child_startup == result.births * gap


def test_pool_full_ledger_under_chamber_run(tmp_path: Path) -> None:
    """Under POOL_FULL, reproduction_heat_loss == energy_cost * births,
    parent_energy_transferred_to_child == 0, pool_out_child_startup ==
    offspring_start_energy * births."""
    layout = food_ladder_layout()
    runs_root = tmp_path / "r"
    runs_root.mkdir()

    repro_cfg = ReproductionConfig(
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    )
    captured: dict[str, object] = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = True
        captured["model"] = model

    result = run_chamber(
        seed=1,
        runs_root=runs_root,
        run_id="seed-1",
        n_founders=5,
        n_ticks=80,
        layout=layout,
        policy_factory=GradientPolicy,
        reproduction_config=repro_cfg,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        setup_observer=setup,
    )

    assert result.parent_energy_transferred_to_child == 0.0
    assert result.reproduction_heat_loss == result.births * repro_cfg.energy_cost
    assert result.pool_out_child_startup == result.births * repro_cfg.offspring_start_energy


# ---------------------------------------------------------------------------
# H10 — POOL_FULL bit-identity vs v0.19 (default-mode no-transfer-fields path)
# ---------------------------------------------------------------------------


def test_pool_full_no_v0_20_fields_emitted(tmp_path: Path) -> None:
    """A v0.20 run with POOL_FULL emits no v0.20-only events, and the
    transfer accumulator stays zero. This is the bit-identity guarantee
    against v0.19 sweeps."""
    layout = food_ladder_layout()
    runs_root = tmp_path / "r"
    runs_root.mkdir()

    captured: dict[str, object] = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = True
        captured["model"] = model

    repro_cfg = ReproductionConfig(
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    )
    result = run_chamber(
        seed=1,
        runs_root=runs_root,
        run_id="seed-1",
        n_founders=5,
        n_ticks=80,
        layout=layout,
        policy_factory=GradientPolicy,
        reproduction_config=repro_cfg,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        setup_observer=setup,
    )

    # Per-tick agent state populated; v0.20 fields untouched.
    assert result.parent_energy_transferred_to_child == 0.0
    assert result.births_blocked_by_parent_energy == 0
    # No BirthDeniedParentEnergy events.
    with (result.output_dir / "events.jsonl").open() as f:
        for line in f:
            row = json.loads(line)
            assert row["type"] != "BirthDeniedParentEnergy"


# ---------------------------------------------------------------------------
# H13 negative control — closed-3000 transfer matches POOL_FULL on agent
# observables when the pool is not binding
# ---------------------------------------------------------------------------


def _agent_observables(events_jsonl: Path) -> tuple[list[dict], int, int, int]:
    """Read agent-observable event rows + counts. Excludes pool-ledger
    events (FoodRespawned is included as an environmental observable;
    PoolRespawnDenied / PoolBirthDenied / BirthDeniedParentEnergy are
    excluded — they fire only under specific gates, but under closed-3000
    the gates do not fire either way, so excluding them is conservative).
    """
    agent_events: list[dict] = []
    births = deaths = food_events = 0
    with events_jsonl.open() as f:
        for line in f:
            row = json.loads(line)
            kind = row["type"]
            if kind in {"PoolRespawnDenied", "PoolBirthDenied", "BirthDeniedParentEnergy"}:
                continue
            agent_events.append(row)
            if kind == "AgentBorn":
                births += 1
            elif kind == "AgentDied":
                deaths += 1
            elif kind == "AteFood":
                food_events += 1
    return agent_events, births, deaths, food_events


def test_h13_negative_control_closed_3000(tmp_path: Path) -> None:
    """At closed-3000 the pool is comfortably above demand and no gates
    fire. Under both modes per-tick agent state must match byte-for-byte
    on all per-agent observables (births, deaths, food events, full
    event sequence). Pool ledger fields legitimately differ between
    modes (see ``v0.20-only field expected non-equivalences`` in the
    pre-reg) and are excluded."""
    layout = food_ladder_layout()
    runs_a = tmp_path / "a"
    runs_b = tmp_path / "b"
    runs_a.mkdir()
    runs_b.mkdir()

    pool_full_cfg = ReproductionConfig(
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    )
    transfer_cfg = ReproductionConfig(
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    )

    def _setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = True

    result_full = run_chamber(
        seed=1,
        runs_root=runs_a,
        run_id="seed-1",
        n_founders=5,
        n_ticks=80,
        layout=layout,
        policy_factory=GradientPolicy,
        reproduction_config=pool_full_cfg,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        setup_observer=_setup,
    )
    result_transfer = run_chamber(
        seed=1,
        runs_root=runs_b,
        run_id="seed-1",
        n_founders=5,
        n_ticks=80,
        layout=layout,
        policy_factory=GradientPolicy,
        reproduction_config=transfer_cfg,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        setup_observer=_setup,
    )

    # Top-line population metrics match.
    assert result_full.births == result_transfer.births
    assert result_full.population_end == result_transfer.population_end
    assert result_full.starvation_deaths == result_transfer.starvation_deaths
    assert result_full.injury_deaths == result_transfer.injury_deaths
    assert result_full.food_events == result_transfer.food_events
    assert result_full.hazard_entries == result_transfer.hazard_entries

    # Pool-ledger fields legitimately differ. v0.20 invariants:
    assert result_full.reproduction_heat_loss == result_full.births * 15.0
    assert result_transfer.reproduction_heat_loss == 0.0
    assert result_full.parent_energy_transferred_to_child == 0.0
    assert result_transfer.parent_energy_transferred_to_child == result_transfer.births * 15.0
    # Pool drained twice as much under POOL_FULL (full vs gap).
    assert result_full.pool_out_child_startup == result_full.births * 30.0
    assert result_transfer.pool_out_child_startup == result_transfer.births * 15.0

    # Per-event agent observables byte-identical.
    rows_full, b_full, d_full, f_full = _agent_observables(result_full.output_dir / "events.jsonl")
    rows_transfer, b_transfer, d_transfer, f_transfer = _agent_observables(
        result_transfer.output_dir / "events.jsonl"
    )
    assert b_full == b_transfer
    assert d_full == d_transfer
    assert f_full == f_transfer
    assert rows_full == rows_transfer


# ---------------------------------------------------------------------------
# Death cause unaffected by mode
# ---------------------------------------------------------------------------


def test_death_residual_credits_pool_under_both_modes() -> None:
    """The v0.19 death-residual recycle is mode-agnostic: under both
    POOL_FULL and PARENT_TRANSFER_POOL_GAP, dying agents' residual body
    energy still credits the pool."""
    for mode in (ChildFundingMode.POOL_FULL, ChildFundingMode.PARENT_TRANSFER_POOL_GAP):
        model = _make_minimal_model(energy_pool_initial=100.0, child_funding_mode=mode)
        assert model.energy_pool is not None
        agent = next(iter(model.agents))
        agent.body = agent.body.__class__(  # type: ignore[call-arg]
            id=agent.body.id,
            lineage_id=agent.body.lineage_id,
            parent_id=agent.body.parent_id,
            x=agent.body.x,
            y=agent.body.y,
            energy=42.0,
            health=0.0,
            age=agent.body.age,
            traits=agent.body.traits,
            alive=True,
            death_cause=None,
        )
        before = model.energy_pool.current
        agent.death_sweep()
        assert model.energy_pool.current == before + 42.0
        assert agent.body.death_cause == DeathCause.INJURY
