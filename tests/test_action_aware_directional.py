"""Tests for v0.12 action-aware directional memory projection.

Three layers, in order of scope:

  - Pure unit tests on the projection helpers in
    ``policies.hedonism_policy`` — ``_project_memory_for_action`` keeps
    one direction's slot for ``MOVE_<DIR>`` and zeros all 8 fields for
    ``STAY`` / ``EAT`` / ``REPRODUCE``; ``_zero_memory_fields`` wipes
    every slot.
  - Policy-level tests on ``HedonismPolicy.decide`` — the new
    ``swayed_by_memory`` / ``action_without_memory`` fields are
    populated only on the ``DirectionalMemory`` path; cell-exact and
    ``None`` paths leave them at defaults; a hand-loaded directional
    memory whose only nonzero slot pulls toward east must steer the
    argmax to ``MOVE_EAST``.
  - Integration tests on ``MemoryTelemetryCollector`` — ``connect``
    enables the model's policy_decision_log and ``finalize`` reports
    ``directional_decisions`` / ``argmax_changes`` correctly; cell-exact
    runs leave both at zero; the collector survives a finalize-after-
    disconnect call (the order memory_grid uses at run end).
"""

from __future__ import annotations

import dataclasses

import numpy as np

from hedonism_harness.core.actions import Action
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.memory import (
    DirectionalMemory,
    make_directional_memory,
    make_memory,
)
from hedonism_harness.core.sensors import Observation, observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import build_world
from hedonism_harness.experiments.memory_telemetry import MemoryTelemetryCollector
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import DecisionContext, PolicyDecision
from hedonism_harness.policies.hedonism_policy import (
    HedonismPolicy,
    _project_memory_for_action,
    _zero_memory_fields,
)


def _traits():
    return random_traits(TraitConfig(), np.random.default_rng(0))


def _obs_with_all_memory_set(value: float = 1.0) -> Observation:
    """Build an Observation with every directional memory field at ``value``."""
    return Observation(
        energy_ratio=1.0,
        health_ratio=1.0,
        hunger_level=0.0,
        injury_level=0.0,
        age=0,
        food_signal_north=0.0,
        food_signal_south=0.0,
        food_signal_east=0.0,
        food_signal_west=0.0,
        hazard_signal_north=0.0,
        hazard_signal_south=0.0,
        hazard_signal_east=0.0,
        hazard_signal_west=0.0,
        on_food=False,
        on_hazard=False,
        on_safe=False,
        current_food_value=0.0,
        current_hazard_damage=0.0,
        current_safe_value=0.0,
        remembered_good_north=value,
        remembered_good_south=value,
        remembered_good_east=value,
        remembered_good_west=value,
        remembered_bad_north=value,
        remembered_bad_south=value,
        remembered_bad_east=value,
        remembered_bad_west=value,
    )


# ---------------------------------------------------------------------------
# Pure projection helpers
# ---------------------------------------------------------------------------


def test_zero_memory_fields_wipes_all_eight_slots() -> None:
    obs = _obs_with_all_memory_set(value=2.5)
    out = _zero_memory_fields(obs)
    for name in ("north", "south", "east", "west"):
        assert getattr(out, f"remembered_good_{name}") == 0.0
        assert getattr(out, f"remembered_bad_{name}") == 0.0
    # Non-memory fields are unchanged.
    assert out.energy_ratio == obs.energy_ratio
    assert out.on_food == obs.on_food


def test_project_memory_for_move_keeps_only_one_direction_slot() -> None:
    obs = _obs_with_all_memory_set(value=3.0)
    out = _project_memory_for_action(obs, Action.MOVE_EAST)
    assert out.remembered_good_east == 3.0
    assert out.remembered_bad_east == 3.0
    for name in ("north", "south", "west"):
        assert getattr(out, f"remembered_good_{name}") == 0.0
        assert getattr(out, f"remembered_bad_{name}") == 0.0


def test_project_memory_for_each_cardinal_direction() -> None:
    """All four MOVE_<DIR>s map to their own slot only."""
    obs = _obs_with_all_memory_set(value=1.0)
    cases = (
        (Action.MOVE_NORTH, "north"),
        (Action.MOVE_SOUTH, "south"),
        (Action.MOVE_EAST, "east"),
        (Action.MOVE_WEST, "west"),
    )
    for action, kept in cases:
        out = _project_memory_for_action(obs, action)
        for name in ("north", "south", "east", "west"):
            expected = 1.0 if name == kept else 0.0
            assert getattr(out, f"remembered_good_{name}") == expected
            assert getattr(out, f"remembered_bad_{name}") == expected


def test_project_memory_zeros_all_for_non_move_actions() -> None:
    obs = _obs_with_all_memory_set(value=4.0)
    for action in (Action.STAY, Action.EAT, Action.REPRODUCE):
        out = _project_memory_for_action(obs, action)
        for name in ("north", "south", "east", "west"):
            assert getattr(out, f"remembered_good_{name}") == 0.0
            assert getattr(out, f"remembered_bad_{name}") == 0.0


def test_project_memory_returns_new_observation_does_not_mutate() -> None:
    """``_project_memory_for_action`` must use ``dataclasses.replace`` —
    the original Observation is frozen and must not be mutated."""
    obs = _obs_with_all_memory_set(value=1.0)
    out = _project_memory_for_action(obs, Action.MOVE_NORTH)
    # The original observation still has all four directions populated.
    assert obs.remembered_good_east == 1.0
    assert obs.remembered_good_west == 1.0
    # The projected one has only north.
    assert out.remembered_good_north == 1.0
    assert out.remembered_good_east == 0.0


# ---------------------------------------------------------------------------
# HedonismPolicy.decide — directional vs. cell-exact vs. None paths
# ---------------------------------------------------------------------------


def _make_decision_ctx(
    *,
    memory: object | None,
    body_x: int = 3,
    body_y: int = 3,
    seed: int = 0,
) -> DecisionContext:
    world_cfg = WorldConfig(seed=1, width=8, height=8, food_density=0.0, hazard_density=0.0)
    world = build_world(world_cfg)
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=body_x,
        y=body_y,
        traits=_traits(),
        config=BodyConfig(),
    )
    obs = observe(world, body, BodyConfig(), memory=memory)
    return DecisionContext(
        world=world,
        body=body,
        observation=obs,
        rng=np.random.default_rng(seed),
        body_config=BodyConfig(),
        action_config=__import__(
            "hedonism_harness.core.config", fromlist=["ActionConfig"]
        ).ActionConfig(),
        memory=memory,
        reproduction_config=ReproductionConfig(min_age=10),
        occupied=frozenset(),
    )


def test_decide_with_no_memory_leaves_telemetry_fields_at_defaults() -> None:
    policy = HedonismPolicy(exploration_noise=0.0)
    ctx = _make_decision_ctx(memory=None)
    decision = policy.decide(ctx)
    assert decision.swayed_by_memory is False
    assert decision.action_without_memory is None


def test_decide_with_cell_exact_memory_leaves_telemetry_fields_at_defaults() -> None:
    """Cell-exact memory has positional differentiation built into
    ``directional_signals`` (axial scan from predicted body position),
    so it does NOT trigger the v0.12 double-scoring path. Telemetry
    fields stay at defaults — preserves v0.10 bit-identical semantics."""
    policy = HedonismPolicy(exploration_noise=0.0)
    mem = make_memory(width=8, height=8)
    ctx = _make_decision_ctx(memory=mem)
    decision = policy.decide(ctx)
    assert decision.swayed_by_memory is False
    assert decision.action_without_memory is None


def test_decide_with_directional_memory_populates_action_without_memory() -> None:
    """Directional memory triggers the double-scoring path; the policy
    must report what it would have picked with memory zeroed, even when
    the two argmax winners agree."""
    policy = HedonismPolicy(exploration_noise=0.0)
    mem = make_directional_memory()
    ctx = _make_decision_ctx(memory=mem)
    decision = policy.decide(ctx)
    # With a freshly-zeroed DirectionalMemory the projection contributes
    # zero to every candidate's score, so argmax must agree.
    assert decision.action_without_memory is not None
    assert decision.swayed_by_memory is False
    assert decision.action == decision.action_without_memory


def test_directional_memory_loaded_east_steers_argmax_to_move_east() -> None:
    """Hand-load a strong east tendency and trait config that gives the
    memory channel a real say. The agent should pick MOVE_EAST whereas
    with memory zeroed the choice would be different (open featureless
    chamber, ties resolved by valid-action ordering, so first valid
    wins). This is the test that v0.11 could not pass."""
    policy = HedonismPolicy(exploration_noise=0.0)
    mem = make_directional_memory()
    # Strong east pleasure + strong every-other-direction pain so that
    # memory's contribution to MOVE_EAST is positive and MOVE_<other>'s
    # is negative. With memory zeroed, all candidates score equally on
    # the memory channel and the loop's ``> best_score`` strictly-greater
    # tie-break keeps the first valid action — get_valid_actions returns
    # STAY first (see core/actions.py:113), so the no-memory winner is
    # STAY for an idle body in an empty world.
    mem.pleasure_tendency[2] = 50.0  # east slot
    mem.pain_tendency[0] = 50.0  # north
    mem.pain_tendency[1] = 50.0  # south
    mem.pain_tendency[3] = 50.0  # west
    ctx = _make_decision_ctx(memory=mem)
    decision = policy.decide(ctx)
    assert decision.action == Action.MOVE_EAST
    assert decision.action_without_memory is not None
    assert decision.action_without_memory != Action.MOVE_EAST
    assert decision.swayed_by_memory is True


# ---------------------------------------------------------------------------
# Model + collector integration — argmax-changes telemetry plumbing
# ---------------------------------------------------------------------------


def _hedonism_policy_factory():
    return HedonismPolicy(exploration_noise=0.0)


def _build_model(*, memory_type: str = "directional", seed: int = 1) -> HHModel:
    world_cfg = WorldConfig(seed=seed, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(max_energy=200.0, starting_energy=200.0)
    repro_cfg = ReproductionConfig(min_age=10)
    return HHModel(
        world_cfg,
        founders=[
            FounderSpec(
                x=4,
                y=4,
                policy_factory=_hedonism_policy_factory,
                use_memory=True,
                memory_type=memory_type,
            )
        ],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )


def test_model_decision_log_disabled_by_default() -> None:
    model = _build_model(memory_type="directional")
    assert model.policy_decision_log is None
    # And note_policy_decision is a safe no-op when disabled.
    fake = PolicyDecision(
        action=Action.STAY,
        breakdown=None,
        swayed_by_memory=True,
        action_without_memory=Action.MOVE_EAST,
    )
    model.note_policy_decision(fake)  # must not raise.
    assert model.policy_decision_log is None


def test_collector_connect_enables_decision_log() -> None:
    model = _build_model(memory_type="directional")
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    assert model.policy_decision_log == []
    collector.disconnect()
    # Disconnect tears the log down on the model side.
    assert model.policy_decision_log is None


def test_collector_finalize_after_disconnect_uses_snapshot() -> None:
    """memory_grid disconnects in a ``finally`` block then calls
    finalize() — the collector must snapshot the log on disconnect."""
    model = _build_model(memory_type="directional")
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    # Run a tick so the directional founder fills the log.
    model.step()
    log_size_before_disconnect = len(model.policy_decision_log or [])
    assert log_size_before_disconnect >= 1
    collector.disconnect()
    telem = collector.finalize()
    # The snapshot preserves what the live log held.
    assert telem.directional_decisions == log_size_before_disconnect


def test_directional_run_records_decisions_cell_exact_does_not() -> None:
    """The directional path fills the log; cell-exact never does."""
    # Directional.
    model_d = _build_model(memory_type="directional")
    coll_d = MemoryTelemetryCollector(model_d)
    coll_d.connect()
    for _ in range(5):
        model_d.step()
    coll_d.disconnect()
    telem_d = coll_d.finalize()
    assert telem_d.directional_decisions >= 5  # at least one per tick.

    # Cell-exact.
    model_c = _build_model(memory_type="cell_exact")
    coll_c = MemoryTelemetryCollector(model_c)
    coll_c.connect()
    for _ in range(5):
        model_c.step()
    coll_c.disconnect()
    telem_c = coll_c.finalize()
    # HedonismPolicy never fills PolicyDecision.action_without_memory on
    # cell-exact runs, so note_policy_decision early-returns and the log
    # stays empty.
    assert telem_c.directional_decisions == 0
    assert telem_c.argmax_changes == 0


def test_argmax_change_rate_zero_when_no_decisions() -> None:
    """Empty-log finalize must not divide by zero."""
    model = _build_model(memory_type="cell_exact")
    coll = MemoryTelemetryCollector(model)
    coll.connect()
    coll.disconnect()
    telem = coll.finalize()
    assert telem.directional_decisions == 0
    assert telem.argmax_change_rate == 0.0


def test_swayed_decisions_show_up_as_action_transitions() -> None:
    """When memory steers the argmax (as in the loaded-east unit test
    above) the per-tick decision log records the swayed transition; the
    collector aggregates it into ``action_transitions``.

    Post-v0.13 the agent must be hungry for memory to sway anything —
    ``novelty_pleasure`` is gated on ``obs_before.hunger_level``. We
    drain the founder's energy below ``starting_energy`` so the gate
    is open."""
    import dataclasses as _dc

    model = _build_model(memory_type="directional")
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    assert isinstance(agent.memory, DirectionalMemory)
    # Drain energy so hunger_level >= 0.5 — opens the v0.13 hunger-gate.
    agent.body = _dc.replace(agent.body, energy=20.0)
    # Force a directional memory configuration that will sway argmax.
    agent.memory.pleasure_tendency[2] = 50.0  # east
    agent.memory.pain_tendency[0] = 50.0
    agent.memory.pain_tendency[1] = 50.0
    agent.memory.pain_tendency[3] = 50.0

    coll = MemoryTelemetryCollector(model)
    coll.connect()
    model.step()  # one decision recorded.
    coll.disconnect()
    telem = coll.finalize()

    assert telem.directional_decisions >= 1
    assert telem.argmax_changes >= 1
    # Action transitions key on (no_mem_action_int, with_mem_action_int).
    # No-mem winner is the first valid action with the highest tie-broken
    # score; swayed winner is MOVE_EAST. We assert MOVE_EAST appears as
    # the with-memory action in at least one transition (the no-memory
    # action depends on which other channel wins — STAY or MOVE_NORTH
    # depending on the agent's spawn cell — but MOVE_EAST as the "to"
    # is the load-bearing claim).
    assert any(with_mem == int(Action.MOVE_EAST) for (_, with_mem) in telem.action_transitions)


def test_v013_hunger_gate_silences_sated_agent_memory_channel() -> None:
    """Mirror of trace 3 in the v0.13 Phase 1 profile. With the
    hunger-gate, a sated agent cannot be swayed off STAY by a strong
    east-tendency — even though pre-v0.13 it would have been
    (novelty_pleasure ran un-gated)."""
    import dataclasses as _dc

    model = _build_model(memory_type="directional")
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    assert isinstance(agent.memory, DirectionalMemory)
    # Sate the agent: hunger_level = 0.0.
    agent.body = _dc.replace(agent.body, energy=model.body_config.max_energy)
    # Plant the same swaying tendency that did fire in the test above.
    agent.memory.pleasure_tendency[2] = 50.0
    agent.memory.pain_tendency[0] = 50.0
    agent.memory.pain_tendency[1] = 50.0
    agent.memory.pain_tendency[3] = 50.0

    coll = MemoryTelemetryCollector(model)
    coll.connect()
    model.step()
    coll.disconnect()
    telem = coll.finalize()
    # Memory cannot sway a sated agent because novelty_pleasure is gated.
    assert telem.argmax_changes == 0


def test_model_step_calls_note_policy_decision_for_directional_only() -> None:
    """Per-decision sanity: direct inspection of model.policy_decision_log
    after one step shows one entry per living agent on directional
    runs, zero entries on cell-exact runs (because the contributing
    fields stay None)."""
    model_d = _build_model(memory_type="directional")
    model_d.enable_policy_decision_log()
    model_d.step()
    assert len(model_d.policy_decision_log or []) == 1

    model_c = _build_model(memory_type="cell_exact")
    model_c.enable_policy_decision_log()
    model_c.step()
    assert model_c.policy_decision_log == []


def test_policy_decision_dataclass_has_v012_default_fields() -> None:
    """A PolicyDecision built without v0.12 fields keeps its v0.11
    contract — ReflexPolicy / RandomPolicy / tests that build one
    directly continue to work."""
    d = PolicyDecision(action=Action.STAY)
    assert d.swayed_by_memory is False
    assert d.action_without_memory is None
    fields = {f.name for f in dataclasses.fields(PolicyDecision)}
    assert "swayed_by_memory" in fields
    assert "action_without_memory" in fields
