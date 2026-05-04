"""Mesa agent adapter — orchestration only (SPEC §27.9, CORE_ARCHITECTURE §4).

This module's single responsibility is to glue the pure ``core/`` + ``policies/``
layers to Mesa's agent lifecycle. ``HHAgent.step`` does:

    build occupied set -> observe -> policy.decide -> apply_action ->
    commit_delta -> update memory -> sync grid position -> emit events ->
    queue births

No new behavior logic lives here. If a change to ``step()`` would touch
valence, trait, sensor, action, or reproduction *math*, the right home is one
of the ``core/`` modules (see CORE_ARCHITECTURE §4 — the adapter rule).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from mesa.discrete_space import CellAgent

from hedonism_harness.core.actions import apply_action, commit_delta, get_valid_actions
from hedonism_harness.core.body import (
    AgentBody,
    apply_damage,
    apply_metabolism,
    infer_death_cause,
    is_dead,
    mark_dead,
)
from hedonism_harness.core.events import HazardDamageApplied, ReproductionRequested
from hedonism_harness.core.memory import (
    DirectionalMemory,
    ValenceMemory,
    update_at,
    update_directional,
)
from hedonism_harness.core.memory import decay_all as _decay_memory_all
from hedonism_harness.core.memory import (
    decay_directional as _decay_memory_directional,
)
from hedonism_harness.core.reproduction import can_reproduce
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.world import CellKind
from hedonism_harness.policies.base import DecisionContext

if TYPE_CHECKING:
    from hedonism_harness.core.events import AnyEvent
    from hedonism_harness.model import HHModel
    from hedonism_harness.policies.base import Policy


class HHAgent(CellAgent):
    """Hedonism Harness Mesa agent — wraps a body + policy + memory + RNG.

    Position is owned by Mesa's ``self.cell``; ``self.body.x/y`` are kept in
    sync after every action so the pure ``core/`` view matches the Mesa view.
    """

    def __init__(
        self,
        model: HHModel,
        body: AgentBody,
        policy: Policy,
        memory: ValenceMemory | DirectionalMemory | None,
        agent_rng: np.random.Generator,
        policy_factory: Callable[[], Policy] | None = None,
    ) -> None:
        super().__init__(model)
        self.body = body
        self.policy = policy
        self.memory = memory
        self.agent_rng = agent_rng
        # Children copy the parent's policy_factory so they reuse the parent's
        # configured policy (e.g. HedonismPolicy(exploration_noise=...)) rather
        # than getting a default-constructed clone.
        self.policy_factory = policy_factory
        self.cell = model.cell_at(body.x, body.y)

    def step(self) -> None:
        """One tick of decision + action. See SPEC §27.4 for tick order."""
        if not self.body.alive:
            return

        model = self.model  # type: HHModel  # narrow for the type checker

        occupied = model.occupied_cells_excluding(self)

        observation = observe(model.world, self.body, model.body_config, memory=self.memory)

        ctx = DecisionContext(
            world=model.world,
            body=self.body,
            observation=observation,
            rng=self.agent_rng,
            body_config=model.body_config,
            action_config=model.action_config,
            memory=self.memory,
            reproduction_config=model.reproduction_config,
            occupied=occupied,
        )
        decision = self.policy.decide(ctx)

        # v0.12 action-aware directional memory introspection. The model
        # holds a per-tick log only when MemoryTelemetryCollector enabled
        # it; this call is a no-op (one None-check) on every other path.
        model.note_policy_decision(decision)

        # Defensive: every policy must select from get_valid_actions(...).
        # A bug in a custom policy that returns an out-of-set action would
        # otherwise silently pass through apply_action with broken semantics
        # (e.g. picking REPRODUCE when not eligible would emit a request that
        # the birth queue can't satisfy). The same `occupied` view is used
        # here as in policy.decide so the two cannot disagree.
        valid = get_valid_actions(model.world, self.body, model.reproduction_config, occupied)
        if decision.action not in valid:
            msg = (
                f"Policy {type(self.policy).__name__} returned {decision.action.name}, "
                f"which is not in get_valid_actions(...) = {[a.name for a in valid]}"
            )
            raise AssertionError(msg)

        result = apply_action(
            model.world,
            self.body,
            decision.action,
            model.body_config,
            model.action_config,
            self.agent_rng,
        )
        commit_delta(model.world, result.delta)

        if self.memory is not None:
            pleasure = decision.breakdown.pleasure if decision.breakdown else 0.0
            pain = decision.breakdown.pain if decision.breakdown else 0.0
            if isinstance(self.memory, ValenceMemory):
                # Cell-exact: associate (pleasure, pain) with the cell the
                # agent landed on this tick.
                update_at(
                    self.memory,
                    result.body.x,
                    result.body.y,
                    pleasure=pleasure,
                    pain=pain,
                    traits=self.body.traits,
                    tick=model.tick_count,
                )
            elif isinstance(self.memory, DirectionalMemory):
                # Chemotaxis-style: associate (pleasure, pain) with the
                # direction of this tick's move. STAY / EAT / REPRODUCE
                # leave (dx, dy) at (0, 0); update_directional skips those.
                dx = result.body.x - self.body.x
                dy = result.body.y - self.body.y
                update_directional(
                    self.memory,
                    dx=dx,
                    dy=dy,
                    pleasure=pleasure,
                    pain=pain,
                    traits=self.body.traits,
                )

        self.body = result.body
        # Sync Mesa cell position with body position.
        if (self.cell.coordinate[0], self.cell.coordinate[1]) != (self.body.x, self.body.y):
            self.cell = model.cell_at(self.body.x, self.body.y)

        # Emit collected events to the model for tally / persistence.
        events: list[AnyEvent] = list(result.events)
        # Reproduction requests go BOTH to the birth queue (so the model
        # processes them in step 7) AND through record_event so the metrics
        # layer's ReproductionRequested handler observes the intent. Per
        # SPEC §14 the request (intent) is distinct from the birth
        # (acceptance); the EpisodeAggregator counts them as separate
        # channels and ``births <= reproduction_requests`` is invariant.
        for event in events:
            if isinstance(event, ReproductionRequested):
                model.record_event(event)
                model.queue_birth(self)
            else:
                model.record_event(event)

    def apply_residency_damage(self) -> None:
        """Apply hazard residency damage if the body is on a HAZARD cell.

        Emits a ``HazardDamageApplied`` event to the model's event log so
        injury metrics (in ``metrics/aggregators.py``) can tally per-agent
        and per-tick damage taken.
        """
        if not self.body.alive:
            return
        kind = CellKind(int(self.model.world.kind_layer[self.body.x, self.body.y]))
        if kind == CellKind.HAZARD:
            damage = float(self.model.world.hazard_damage[self.body.x, self.body.y])
            if damage > 0.0:
                self.body = apply_damage(self.body, damage)
                self.model.record_event(
                    HazardDamageApplied(
                        agent_id=self.body.id,
                        x=self.body.x,
                        y=self.body.y,
                        damage=damage,
                    )
                )

    def apply_metabolism_step(self) -> None:
        """Apply baseline metabolism for the tick."""
        if not self.body.alive:
            return
        self.body = apply_metabolism(self.body, self.model.body_config)

    def apply_memory_decay(self) -> None:
        """Apply per-tick exponential decay to the agent's valence memory.

        Per SPEC §13.3 the EMA layers / tendency vectors decay by a
        factor of ``(1 - traits.memory_decay_rate)`` each tick so stale
        associations fade as the world changes (food consumed, hazards
        re-located). No-op when the agent has no memory or is dead.
        Dispatches on memory type — both decay functions early-return
        when ``decay_rate <= 0``.
        """
        if not self.body.alive or self.memory is None:
            return
        decay_rate = float(self.body.traits.memory_decay_rate)
        if isinstance(self.memory, ValenceMemory):
            _decay_memory_all(self.memory, decay_rate)
        elif isinstance(self.memory, DirectionalMemory):
            _decay_memory_directional(self.memory, decay_rate)

    def apply_auto_reproduction(self) -> None:
        """v0.2 substrate phase: trigger reproduction without policy intent.

        Per v0.2 reflex-cell spec, reproduction is a substrate consequence
        of body state, not a behavior. When the agent is alive, eligible
        (energy >= threshold, age >= min_age, not on a hazard cell, has
        an open neighbor), and the model has auto-reproduction enabled,
        this phase emits a ``ReproductionRequested`` event and queues a
        birth via the existing ``_birth_queue`` infrastructure. The
        per-tick birth-queue processing in ``model.step()`` then handles
        the actual reproduction (energy debit, child construction).

        No-op when:
          - the agent is dead;
          - ``model.auto_reproduction_enabled`` is False (the v0.7..v0.13
            default; preserves bit-identity for the deliberative-voluntary
            comparison branch);
          - the agent fails ``can_reproduce`` (e.g., insufficient energy,
            no open neighbor, on a hazard cell).
        """
        if not self.body.alive:
            return
        model = self.model  # type: HHModel
        if not getattr(model, "auto_reproduction_enabled", False):
            return
        if model.reproduction_config is None:
            return
        # Build the same occupancy view the deliberative policy uses, so
        # auto and voluntary triggers see identical eligibility state.
        occupied = model.occupied_cells_excluding(self)
        if not can_reproduce(model.world, self.body, model.reproduction_config, occupied):
            return
        # Emit ReproductionRequested so existing aggregators that count
        # requests still see the intent (mirror of voluntary REPRODUCE
        # apply_action emission).
        request = ReproductionRequested(agent_id=self.body.id, x=self.body.x, y=self.body.y)
        model.record_event(request)
        model.queue_birth(self)

    def death_sweep(self) -> bool:
        """Mark the body dead (and remove from the grid + AgentSet) if vitals zeroed.

        Returns True iff the agent was just marked dead this call.
        """
        if not self.body.alive:
            return False
        if is_dead(self.body):
            cause = infer_death_cause(self.body)
            if cause is not None:
                self.body = mark_dead(self.body, cause)
                self.model.record_death(self)
                # ``CellAgent.remove`` clears ``self.cell`` and unregisters the
                # agent from ``model.agents``.
                self.remove()
                return True
        return False
