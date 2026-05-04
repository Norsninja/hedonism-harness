"""Mesa Model adapter — orchestration only (CORE_ARCHITECTURE §4).

Builds the runtime context the pure ``core/`` + ``policies/`` layers need:
``World`` (sharing storage with Mesa ``PropertyLayer``s), an
``OrthogonalVonNeumannGrid`` with ``capacity=1``, founder agents with
sequential ``lineage_id``, a deterministic per-tick order per SPEC §27.4, and
the birth queue / event log.

This file does not contain new behavior. All math lives in ``core/`` and all
strategy lives in ``policies/`` — see CORE_ARCHITECTURE §4 for the adapter rule.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import mesa
import numpy as np
from mesa.discrete_space import OrthogonalVonNeumannGrid, PropertyLayer

from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.events import AgentBorn, AgentDied
from hedonism_harness.core.memory import make_memory
from hedonism_harness.core.reproduction import process_reproduction
from hedonism_harness.core.rng import RngStreams, make_streams, spawn_agent_rng
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import World, build_world
from hedonism_harness.mesa_agents import HHAgent

if TYPE_CHECKING:
    from hedonism_harness.core.events import AnyEvent
    from hedonism_harness.policies.base import Policy


# A founder spec lets the caller declare population without exposing the
# Memory/RNG/lineage plumbing — those are owned by the model.
PolicyFactory = Callable[[], "Policy"]


class FounderSpec:
    """Declarative founder agent description.

    The model assigns ``lineage_id`` (sequential, 0..N-1) and per-agent RNG.
    """

    __slots__ = ("policy_factory", "use_memory", "x", "y")

    def __init__(
        self,
        x: int,
        y: int,
        policy_factory: PolicyFactory,
        use_memory: bool = False,
    ) -> None:
        self.x = x
        self.y = y
        self.policy_factory = policy_factory
        self.use_memory = use_memory


class HHModel(mesa.Model):
    """Hedonism Harness Mesa model — adapter over ``core/`` + ``policies/``.

    Tick order (SPEC §27.4):
        1. snapshot living agents for this tick
        2. shuffle deterministically via ``RngStreams.agent_order``
        3. each agent steps once (observe / decide / apply_action / commit /
           memory update / grid sync)
        4. baseline metabolism
        5. hazard residency damage
        6. death sweep
        7. process queued births (newborns DO NOT act this tick)
        8. tick_count += 1
    """

    def __init__(
        self,
        world_config: WorldConfig,
        founders: Sequence[FounderSpec],
        body_config: BodyConfig | None = None,
        action_config: ActionConfig | None = None,
        reproduction_config: ReproductionConfig | None = None,
        trait_config: TraitConfig | None = None,
    ) -> None:
        # Mesa's Model uses Python ``random.Random`` internally (e.g. for
        # default agent ID assignment). Per SPEC §27.3 we never read
        # ``self.random`` from policies / scheduling; we shuffle agents via
        # our own NumPy ``agent_order`` stream. The seed passed up to Mesa is
        # only used for that internal Mesa state.
        super().__init__(seed=world_config.seed)

        self.world_config = world_config
        self.body_config = body_config or BodyConfig()
        self.action_config = action_config or ActionConfig()
        self.reproduction_config = reproduction_config or ReproductionConfig()
        self.trait_config = trait_config or TraitConfig()

        self.streams: RngStreams = make_streams(world_config.seed)

        # ---- Build the world and PropertyLayers with SHARED storage ----
        # ``build_world`` produces freshly-allocated NumPy arrays. We then
        # build PropertyLayers with matching shape/dtype, copy values in,
        # and re-point ``World``'s array fields at the PL storage. After
        # this, ``world.kind_layer is kind_pl.data`` (verified by test).
        self.world: World = build_world(world_config)
        self._attach_shared_property_layers()

        # ---- Grid with capacity=1 (single agent per cell) --------------
        self.grid = OrthogonalVonNeumannGrid(
            (world_config.width, world_config.height),
            torus=False,
            capacity=1,
            random=self.random,
        )
        for pl in self._property_layers.values():
            self.grid.add_property_layer(pl)

        # ---- Tick / event bookkeeping ----------------------------------
        self.tick_count: int = 0
        self.event_log: list[AnyEvent] = []
        self._birth_queue: list[HHAgent] = []
        self._next_body_id: int = 1
        self._next_lineage_id: int = 0

        # ---- Place founders --------------------------------------------
        for spec in founders:
            self._spawn_founder(spec)

    # ------------------------------------------------------------------
    # Property-layer wiring
    # ------------------------------------------------------------------

    def _attach_shared_property_layers(self) -> None:
        """Build PropertyLayers and re-point ``World`` fields at PL storage.

        After this method, mutating ``self.world.kind_layer`` (etc.) is
        equivalent to mutating the PropertyLayer's NumPy buffer. This is what
        keeps ``apply_action`` / ``commit_delta`` Mesa-free while still giving
        Mesa-side consumers (visualization, batch_run) a live view.
        """
        dims = (self.world_config.width, self.world_config.height)
        # Match dtype precisely with the default_value to silence Mesa's
        # "default value might not be best suitable" warning.
        kind_pl = PropertyLayer("kind", dims, default_value=np.uint8(0), dtype=np.uint8)
        food_pl = PropertyLayer("food_value", dims, default_value=np.float32(0.0), dtype=np.float32)
        hazard_pl = PropertyLayer(
            "hazard_damage", dims, default_value=np.float32(0.0), dtype=np.float32
        )
        safe_pl = PropertyLayer("safe_value", dims, default_value=np.float32(0.0), dtype=np.float32)

        # Copy initial terrain into PL storage, then point World at it.
        kind_pl.data[:] = self.world.kind_layer
        food_pl.data[:] = self.world.food_value
        hazard_pl.data[:] = self.world.hazard_damage
        safe_pl.data[:] = self.world.safe_value

        self.world.kind_layer = kind_pl.data
        self.world.food_value = food_pl.data
        self.world.hazard_damage = hazard_pl.data
        self.world.safe_value = safe_pl.data

        self._property_layers: dict[str, PropertyLayer] = {
            "kind": kind_pl,
            "food_value": food_pl,
            "hazard_damage": hazard_pl,
            "safe_value": safe_pl,
        }

    # ------------------------------------------------------------------
    # Population helpers
    # ------------------------------------------------------------------

    def _spawn_founder(self, spec: FounderSpec) -> HHAgent:
        lineage_id = self._next_lineage_id
        self._next_lineage_id += 1

        traits = random_traits(self.trait_config, self.streams.mutation)
        body = make_body(
            body_id=self._next_body_id,
            lineage_id=lineage_id,
            parent_id=None,
            x=spec.x,
            y=spec.y,
            traits=traits,
            config=self.body_config,
        )
        self._next_body_id += 1

        memory = (
            make_memory(self.world_config.width, self.world_config.height)
            if spec.use_memory
            else None
        )
        agent_rng = spawn_agent_rng(self.streams.mutation)
        agent = HHAgent(
            self,
            body=body,
            policy=spec.policy_factory(),
            memory=memory,
            agent_rng=agent_rng,
            policy_factory=spec.policy_factory,
        )
        return agent

    # ------------------------------------------------------------------
    # Wrapper-side queries (read by HHAgent.step)
    # ------------------------------------------------------------------

    def occupied_cells_excluding(self, exclude: HHAgent) -> frozenset[tuple[int, int]]:
        """Return the set of cells occupied by living agents other than ``exclude``."""
        return frozenset(
            (a.body.x, a.body.y)
            for a in self.agents
            if isinstance(a, HHAgent) and a is not exclude and a.body.alive
        )

    def queue_birth(self, parent: HHAgent) -> None:
        self._birth_queue.append(parent)

    def record_event(self, event: AnyEvent) -> None:
        self.event_log.append(event)

    def record_death(self, agent: HHAgent) -> None:
        cause = agent.body.death_cause
        assert cause is not None  # death_sweep only records after mark_dead.
        self.event_log.append(AgentDied(agent_id=agent.body.id, cause=cause, tick=self.tick_count))

    # ------------------------------------------------------------------
    # Tick loop (SPEC §27.4)
    # ------------------------------------------------------------------

    def step(self) -> None:
        # 1. Snapshot active agents.
        active: list[HHAgent] = [a for a in self.agents if isinstance(a, HHAgent) and a.body.alive]
        # 2. Deterministic shuffle via NumPy agent_order stream.
        order = self.streams.agent_order.permutation(len(active))
        ordered = [active[i] for i in order]

        # 3. Each agent steps once.
        for agent in ordered:
            agent.step()

        # 4. Baseline metabolism.
        for agent in self.agents:
            if isinstance(agent, HHAgent):
                agent.apply_metabolism_step()

        # 5. Hazard residency damage.
        for agent in self.agents:
            if isinstance(agent, HHAgent):
                agent.apply_residency_damage()

        # 6. Death sweep.
        # Iterate over a list copy because death_sweep may remove from
        # ``self.agents`` (via ``CellAgent.remove``).
        for agent in list(self.agents):
            if isinstance(agent, HHAgent):
                agent.death_sweep()

        # 7. Process queued births. Newborns added now do NOT step this tick
        #    (the snapshot above is already iterated).
        self._process_birth_queue()

        # 8. Increment tick count.
        self.tick_count += 1

    def _process_birth_queue(self) -> None:
        if not self._birth_queue:
            return
        # Snapshot + clear so reproductions during processing don't recurse.
        parents = self._birth_queue
        self._birth_queue = []
        for parent in parents:
            if not parent.body.alive:
                continue
            occupied = self.occupied_cells_excluding(parent)
            outcome = process_reproduction(
                self.world,
                parent.body,
                parent_rng=parent.agent_rng,
                trait_config=self.trait_config,
                body_config=self.body_config,
                reproduction_config=self.reproduction_config,
                child_id=self._next_body_id,
                occupied=occupied,
            )
            if outcome is None:
                continue
            updated_parent_body, child_body = outcome
            parent.body = updated_parent_body
            self._next_body_id += 1

            child_memory = (
                make_memory(self.world_config.width, self.world_config.height)
                if parent.memory is not None
                else None
            )
            child_rng = spawn_agent_rng(self.streams.mutation)
            # Reuse the parent's policy factory so the child gets a policy with
            # the same configuration (e.g. HedonismPolicy.exploration_noise).
            policy_factory = parent.policy_factory or type(parent.policy)
            child_agent = HHAgent(
                self,
                body=child_body,
                policy=policy_factory(),
                memory=child_memory,
                agent_rng=child_rng,
                policy_factory=policy_factory,
            )
            assert child_body.parent_id is not None  # children always have a parent_id.
            self.event_log.append(
                AgentBorn(
                    agent_id=child_body.id,
                    parent_id=child_body.parent_id,
                    lineage_id=child_body.lineage_id,
                    x=child_body.x,
                    y=child_body.y,
                    tick=self.tick_count,
                )
            )
            # ``child_agent`` is intentionally referenced via model.agents only.
            del child_agent
