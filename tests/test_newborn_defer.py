"""Newborns added during tick T must NOT step until tick T+1 (SPEC §27.4).

This invariant is currently enforced structurally — ``HHModel.step`` snapshots
the living agents at the top of each tick and only iterates that snapshot,
even though birth-queue processing later adds new agents. The test below is
a regression guard: any future refactor that iterates ``self.agents``
in-place during a tick risks giving newborns a "free first step."
"""

from __future__ import annotations

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.base import DecisionContext, PolicyDecision


class _AlwaysReproducePolicy:
    """Picks REPRODUCE if valid; STAY otherwise. Test-only fixture."""

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        valid = get_valid_actions(ctx.world, ctx.body, ctx.reproduction_config, ctx.occupied)
        if Action.REPRODUCE in valid:
            return PolicyDecision(action=Action.REPRODUCE, breakdown=None)
        return PolicyDecision(action=Action.STAY, breakdown=None)


def _build_repro_ready_model() -> HHModel:
    """Founder is immediately eligible to reproduce (high starting energy, no age gate)."""
    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)  # >= ReproductionConfig.energy_threshold
    repro_cfg = ReproductionConfig(min_age=0, hazard_threshold=10.0)
    return HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysReproducePolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )


def _hh_agents(model: HHModel) -> list[HHAgent]:
    return [a for a in model.agents if isinstance(a, HHAgent)]


def test_newborn_does_not_step_on_reproduction_tick() -> None:
    model = _build_repro_ready_model()
    assert len(_hh_agents(model)) == 1

    # Tick 0: parent reproduces; child must be created and added to model.agents,
    # but must NOT have stepped (age is incremented by metabolism, not by step
    # itself — we assert age == 0 to prove the newborn's metabolism phase did
    # not run on this tick).
    model.step()
    agents = _hh_agents(model)
    assert len(agents) == 2, "child should have been added"

    parent = next(a for a in agents if a.body.parent_id is None)
    child = next(a for a in agents if a.body.parent_id is not None)

    assert child.body.parent_id == parent.body.id
    assert child.body.lineage_id == parent.body.lineage_id
    assert child.body.age == 0, (
        "child age must be 0 on the reproduction tick — metabolism did not run for the newborn"
    )
    # Parent age advanced from 0 -> 1 (its own metabolism ran).
    assert parent.body.age == 1


def test_newborn_steps_on_the_following_tick() -> None:
    model = _build_repro_ready_model()
    model.step()  # tick 0: child born
    child_before = next(a for a in _hh_agents(model) if a.body.parent_id is not None).body
    assert child_before.age == 0

    model.step()  # tick 1: child should now step
    child_after = next(a for a in _hh_agents(model) if a.body.id == child_before.id).body
    assert child_after.age == 1, "child age must advance to 1 after its first metabolism tick (T+1)"


def test_reproduction_request_is_observable_through_signal_and_birth_follows() -> None:
    """Pinning regression: ``ReproductionRequested`` must flow through the
    signal bus so ``EpisodeAggregator`` can tally it; the birth queue must
    still produce an ``AgentBorn`` event when placement succeeds; and
    ``births <= reproduction_requests`` must hold as a tally invariant
    (intent is logged before, or simultaneously with, acceptance).

    Pre-fix bug: ``mesa_agents`` queued the birth without emitting through
    ``record_event``, so ``tally.reproduction_requests`` silently stayed 0
    while ``tally.births`` advanced.
    """
    from hedonism_harness.metrics.aggregators import EpisodeAggregator

    model = _build_repro_ready_model()
    aggregator = EpisodeAggregator(model=model)
    aggregator.connect()
    try:
        model.step()  # tick 0: parent emits REPRODUCE; child born
    finally:
        aggregator.disconnect()

    assert aggregator.tally.reproduction_requests == 1, (
        "ReproductionRequested must reach the EpisodeAggregator handler"
    )
    assert aggregator.tally.births == 1, "AgentBorn must still fire from the birth queue"
    assert aggregator.tally.births <= aggregator.tally.reproduction_requests, (
        "tally invariant: births cannot exceed requests"
    )


def test_reproduction_request_is_persisted_to_event_log() -> None:
    """Pinning: the request event must also be recorded in ``model.event_log``
    so JSONL writers and per-tick analyses can see request-vs-birth ordering.
    """
    from hedonism_harness.core.events import AgentBorn, ReproductionRequested

    model = _build_repro_ready_model()
    model.step()

    request_entries = [e for e in model.event_log if isinstance(e.event, ReproductionRequested)]
    birth_entries = [e for e in model.event_log if isinstance(e.event, AgentBorn)]
    assert len(request_entries) == 1
    assert len(birth_entries) == 1
    # Both occur on tick 0 (request from parent action, birth from queue
    # processing later in the same tick).
    assert request_entries[0].tick == 0
    assert birth_entries[0].tick == 0
