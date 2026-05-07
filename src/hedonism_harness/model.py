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
    ChildFundingMode,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.energy_pool import EnergyPool
from hedonism_harness.core.events import (
    AgentBorn,
    AgentDied,
    AteFood,
    BirthDeniedParentEnergy,
    FoodRespawned,
    LoggedEvent,
    PoolBirthDenied,
    PoolRespawnDenied,
    emit,
    signal_for,
)
from hedonism_harness.core.memory import (
    DirectionalMemory,
    ScalarMemory,
    ValenceMemory,
    make_directional_memory,
    make_memory,
    make_scalar_memory,
)
from hedonism_harness.core.reproduction import find_adjacent_empty_cell, process_reproduction
from hedonism_harness.core.rng import RngStreams, make_streams, spawn_agent_rng
from hedonism_harness.core.traits import TraitConfig, Traits, random_traits
from hedonism_harness.core.world import CellKind, World, build_world
from hedonism_harness.mesa_agents import HHAgent

if TYPE_CHECKING:
    from hedonism_harness.core.events import AnyEvent
    from hedonism_harness.policies.base import Policy, PolicyDecision


# A founder spec lets the caller declare population without exposing the
# Memory/RNG/lineage plumbing — those are owned by the model.
PolicyFactory = Callable[[], "Policy"]


MEMORY_TYPE_CELL_EXACT: str = "cell_exact"
MEMORY_TYPE_DIRECTIONAL: str = "directional"
MEMORY_TYPE_SCALAR: str = "scalar"
_VALID_MEMORY_TYPES: frozenset[str] = frozenset(
    {MEMORY_TYPE_CELL_EXACT, MEMORY_TYPE_DIRECTIONAL, MEMORY_TYPE_SCALAR}
)


def _make_memory_for_spec(
    *, use_memory: bool, memory_type: str, width: int, height: int
) -> ValenceMemory | DirectionalMemory | ScalarMemory | None:
    """Build a fresh per-agent memory matching ``memory_type``.

    Returns ``None`` when ``use_memory=False`` (the default — keeps v0.1
    behavior bit-identical for callers that never asked for memory).
    """
    if not use_memory:
        return None
    if memory_type == MEMORY_TYPE_CELL_EXACT:
        return make_memory(width, height)
    if memory_type == MEMORY_TYPE_DIRECTIONAL:
        return make_directional_memory()
    if memory_type == MEMORY_TYPE_SCALAR:
        return make_scalar_memory()
    msg = f"Unknown memory_type {memory_type!r}; valid: {sorted(_VALID_MEMORY_TYPES)}"
    raise ValueError(msg)


class FounderSpec:
    """Declarative founder agent description.

    The model assigns ``lineage_id`` (sequential, 0..N-1) and per-agent RNG.

    ``traits_override``: when provided, the founder is built with exactly those
    traits and ``random_traits`` is not consulted. This is the seam used by the
    v0.2 positive-control experiment to inject deterministic archetype Traits.
    Leave ``None`` (default) to keep the v0.1 behavior of sampling each founder
    from the configured ``TraitConfig`` ranges.

    ``memory_type``: the v0.11 / v0.15 memory-representation seam. Only
    consulted when ``use_memory=True``. ``"cell_exact"`` (the v0.1 default)
    keeps callers bit-identical to v0.9/v0.10 behavior; ``"directional"``
    uses the multi-cell-tier 4-vector ``DirectionalMemory``;
    ``"scalar"`` (v0.15) uses the prokaryotic-chemotaxis-tier
    ``ScalarMemory`` (one float + last move direction).
    """

    __slots__ = (
        "memory_type",
        "policy_factory",
        "traits_override",
        "use_memory",
        "x",
        "y",
    )

    def __init__(
        self,
        x: int,
        y: int,
        policy_factory: PolicyFactory,
        use_memory: bool = False,
        traits_override: Traits | None = None,
        memory_type: str = MEMORY_TYPE_CELL_EXACT,
    ) -> None:
        if memory_type not in _VALID_MEMORY_TYPES:
            msg = f"Unknown memory_type {memory_type!r}; valid: {sorted(_VALID_MEMORY_TYPES)}"
            raise ValueError(msg)
        self.x = x
        self.y = y
        self.policy_factory = policy_factory
        self.use_memory = use_memory
        self.traits_override = traits_override
        self.memory_type = memory_type


class HHModel(mesa.Model):
    """Hedonism Harness Mesa model — adapter over ``core/`` + ``policies/``.

    Tick order (SPEC §27.4):
        1. snapshot living agents for this tick
        2. shuffle deterministically via ``RngStreams.agent_order``
        3. each agent steps once (observe / decide / apply_action / commit /
           memory update / grid sync)
        4. baseline metabolism + per-agent memory decay (SPEC §13.3)
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

        # v0.20 cross-config validator: PARENT_TRANSFER_POOL_GAP requires a
        # finite or open energy pool. Inf-pool under transfer mode has no
        # source for the gap top-up, so this configuration is rejected at
        # construction time rather than silently degraded.
        if (
            self.reproduction_config.child_funding_mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
            and world_config.energy_pool_initial is None
        ):
            msg = (
                "ChildFundingMode.PARENT_TRANSFER_POOL_GAP requires "
                "WorldConfig.energy_pool_initial to be set; inf-pool under "
                "transfer mode has no pool to fund the offspring_start_energy "
                "gap. See docs/experiments/fear_hunger_v0.20.md."
            )
            raise ValueError(msg)

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
        # Every entry is a ``LoggedEvent`` carrying the emission tick. The
        # JSONL writer reads ``.tick`` and ``.event``; aggregators read the
        # raw event off the signal (which is sender + event-only — no
        # envelope on the wire).
        self.event_log: list[LoggedEvent] = []
        self._birth_queue: list[HHAgent] = []
        self._next_body_id: int = 1
        self._next_lineage_id: int = 0

        # v0.12 action-aware-directional-memory introspection log.
        # ``None`` by default — opt-in via ``enable_policy_decision_log``,
        # which is what ``MemoryTelemetryCollector.connect()`` does on
        # directional sweeps. Each entry is a tuple
        # ``(swayed_by_memory: bool, action_int: int,
        #    action_without_memory_int: int)``. Only HedonismPolicy on a
        # ``DirectionalMemory`` fills the contributing ``PolicyDecision``
        # fields, so other (policy, memory_type) combinations leave the
        # log empty even when enabled.
        self._policy_decision_log: list[tuple[bool, int, int]] | None = None

        # v0.2 reflex-cell substrate — automatic reproduction trigger.
        # When ``auto_reproduction_enabled`` is True, ``HHAgent.apply_auto_reproduction``
        # fires each tick (model.step() phase 4.5) and queues a birth for
        # any agent whose body state satisfies ``can_reproduce``. Default
        # False preserves v0.7..v0.13 voluntary-REPRODUCE behavior; the
        # v0.14 comparison driver flips it to True for arms B and C.
        self.auto_reproduction_enabled: bool = False

        # v0.14 per-lineage trait fingerprint log. One entry per agent
        # spawned (founders + births). Used by the speciation analysis
        # pipeline. Always populated; cheap (one dict copy per spawn).
        self.trait_fingerprints: list[dict[str, object]] = []

        # ---- v0.18 food respawn subscription ----------------------------
        # When cooldown is configured, every AteFood event schedules the
        # consumed cell to refill ``cooldown`` ticks later. Sender-scoped
        # (sender=self) so concurrent batch runs do not cross-talk. The
        # handler is stored on the instance so it stays alive against
        # blinker's weak-reference behaviour.
        self._ate_food_handler: Callable[..., None] | None = None
        if world_config.food_respawn_cooldown is not None:
            cooldown = int(world_config.food_respawn_cooldown)

            def _on_ate_food(_sender: object, *, event: AteFood) -> None:
                self.world.respawn_at_tick[event.x, event.y] = self.tick_count + cooldown

            self._ate_food_handler = _on_ate_food
            signal_for(AteFood).connect(_on_ate_food, sender=self)

        # ---- v0.20 mode-specific reproduction accumulators -------------
        # These track conservation-ledger semantics that the EnergyPool
        # primitive cannot express on its own. Under POOL_FULL the
        # parent's energy_cost is destroyed at each successful birth,
        # accumulated as ``reproduction_heat_loss``; under
        # PARENT_TRANSFER_POOL_GAP the same energy is conceptually
        # routed into the child and accumulated as
        # ``parent_energy_transferred_to_child`` (with
        # ``reproduction_heat_loss`` staying at zero). The
        # ``births_blocked_by_parent_energy`` counter captures the new
        # transfer-mode-only failure path where the parent's energy
        # dropped below energy_cost between queue and process time.
        self.reproduction_heat_loss: float = 0.0
        self.parent_energy_transferred_to_child: float = 0.0
        self.births_blocked_by_parent_energy: int = 0

        # ---- v0.19 ambient energy pool ----------------------------------
        # Constructed only when ``energy_pool_initial`` is finite. Under
        # ``None`` (the v0.7..v0.18 default) the pool path is fully
        # bypassed: respawn refills are not gated, child startup is not
        # debited, the death-residual recycle is not applied, and ambient
        # influx is not credited. This preserves bit-identity for every
        # arm prior to v0.19 by construction.
        self.energy_pool: EnergyPool | None = None
        if world_config.energy_pool_initial is not None:
            self.energy_pool = EnergyPool(current=float(world_config.energy_pool_initial))

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
        # v0.18: per-tile cooldown schedule for food respawn. 0 = not
        # scheduled. Allocated regardless of config; never written when
        # food_respawn_cooldown is None (preserves v0.7..v0.17 bit-identity).
        respawn_pl = PropertyLayer(
            "respawn_at_tick", dims, default_value=np.int32(0), dtype=np.int32
        )

        # Copy initial terrain into PL storage, then point World at it.
        kind_pl.data[:] = self.world.kind_layer
        food_pl.data[:] = self.world.food_value
        hazard_pl.data[:] = self.world.hazard_damage
        safe_pl.data[:] = self.world.safe_value
        respawn_pl.data[:] = self.world.respawn_at_tick

        self.world.kind_layer = kind_pl.data
        self.world.food_value = food_pl.data
        self.world.hazard_damage = hazard_pl.data
        self.world.safe_value = safe_pl.data
        self.world.respawn_at_tick = respawn_pl.data

        self._property_layers: dict[str, PropertyLayer] = {
            "kind": kind_pl,
            "food_value": food_pl,
            "hazard_damage": hazard_pl,
            "safe_value": safe_pl,
            "respawn_at_tick": respawn_pl,
        }

    # ------------------------------------------------------------------
    # Population helpers
    # ------------------------------------------------------------------

    def _spawn_founder(self, spec: FounderSpec) -> HHAgent:
        lineage_id = self._next_lineage_id
        self._next_lineage_id += 1

        traits = (
            spec.traits_override
            if spec.traits_override is not None
            else random_traits(self.trait_config, self.streams.mutation)
        )
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

        memory = _make_memory_for_spec(
            use_memory=spec.use_memory,
            memory_type=spec.memory_type,
            width=self.world_config.width,
            height=self.world_config.height,
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
        self._record_trait_fingerprint(agent.body, birth_tick=0)
        return agent

    def _record_trait_fingerprint(self, body: object, *, birth_tick: int) -> None:
        """Append one entry to ``self.trait_fingerprints`` for a spawned agent.

        Called at founder spawn (birth_tick=0) and at each child birth in
        ``_process_birth_queue`` (birth_tick = tick the child was queued
        and processed). The entry includes lineage_id, parent_id (None
        for founders), the agent_id, and the full trait vector at spawn
        time. Lineage-ancestry analysis stitches entries by parent_id.
        """
        traits = body.traits  # type: ignore[attr-defined]
        entry: dict[str, object] = {
            "agent_id": int(body.id),  # type: ignore[attr-defined]
            "parent_id": (
                None if body.parent_id is None else int(body.parent_id)  # type: ignore[attr-defined]
            ),
            "lineage_id": int(body.lineage_id),  # type: ignore[attr-defined]
            "birth_tick": int(birth_tick),
            "spawn_x": int(body.x),  # type: ignore[attr-defined]
            "spawn_y": int(body.y),  # type: ignore[attr-defined]
        }
        for trait_name in (
            "hunger_pain_sensitivity",
            "injury_pain_sensitivity",
            "fear_sensitivity",
            "pleasure_sensitivity",
            "reproduction_drive",
            "novelty_drive",
            "uncertainty_aversion",
            "pain_tolerance",
            "risk_tolerance",
            "memory_strength",
            "memory_decay_rate",
            "sensor_radius",
            "metabolic_rate",
        ):
            entry[trait_name] = getattr(traits, trait_name)
        self.trait_fingerprints.append(entry)

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

    def cell_at(self, x: int, y: int) -> object:
        """Return the Mesa cell at ``(x, y)``.

        Public seam over Mesa's per-version private cell-lookup API
        (currently ``OrthogonalVonNeumannGrid._cells``). Call sites in
        ``mesa_agents.py`` use this wrapper so a Mesa upgrade that
        renames the private mapping changes one method here instead of
        every caller.
        """
        return self.grid._cells[(x, y)]

    # ------------------------------------------------------------------
    # v0.12 policy-decision introspection log
    # ------------------------------------------------------------------

    def enable_policy_decision_log(self) -> None:
        """Begin recording per-decision argmax-with/without-memory outcomes.

        ``MemoryTelemetryCollector`` calls this from ``connect()`` so the
        log is live before the first ``model.step()``. Idempotent.
        """
        if self._policy_decision_log is None:
            self._policy_decision_log = []

    def disable_policy_decision_log(self) -> None:
        """Stop recording and clear the policy-decision log."""
        self._policy_decision_log = None

    @property
    def policy_decision_log(self) -> list[tuple[bool, int, int]] | None:
        """Read-only view of the recorded log, or ``None`` when disabled."""
        return self._policy_decision_log

    def note_policy_decision(self, decision: PolicyDecision) -> None:
        """Append one entry to the policy-decision log if recording is on.

        No-op when the log is disabled, when ``decision.action_without_memory``
        is ``None`` (every non-directional code path), or when the agent
        is dead. Called from ``HHAgent.step()`` immediately after
        ``policy.decide(ctx)``.
        """
        if self._policy_decision_log is None:
            return
        if decision.action_without_memory is None:
            return
        self._policy_decision_log.append(
            (
                decision.swayed_by_memory,
                int(decision.action),
                int(decision.action_without_memory),
            )
        )

    def record_event(self, event: AnyEvent) -> None:
        """Append a tick-stamped envelope AND emit on the event's named signal.

        Subscribers (``metrics/aggregators.py``) connect to the signals and
        receive the raw event; the log carries the tick alongside for IO
        writers and per-tick analyses.
        """
        self.event_log.append(LoggedEvent(tick=self.tick_count, event=event))
        emit(self, event)

    def record_death(self, agent: HHAgent) -> None:
        cause = agent.body.death_cause
        assert cause is not None  # death_sweep only records after mark_dead.
        # v0.19 strict-conservation: credit residual body energy to the
        # ambient pool synchronously. Starvation deaths credit 0 by
        # construction (energy <= 0 was the death trigger); injury /
        # hazard deaths credit whatever the body still held. No-op when
        # no pool is configured (preserves v0.7..v0.18 bit-identity).
        if self.energy_pool is not None:
            self.energy_pool.credit_death_residual(float(agent.body.energy))
        died = AgentDied(agent_id=agent.body.id, cause=cause, tick=self.tick_count)
        self.event_log.append(LoggedEvent(tick=self.tick_count, event=died))
        emit(self, died)

    # ------------------------------------------------------------------
    # Tick loop (SPEC §27.4)
    # ------------------------------------------------------------------

    def _apply_ambient_influx(self) -> None:
        """v0.19 phase-0a: credit the deterministic per-tick influx to pool.

        No-op when no pool is configured or rate is 0.0. Sub-phase of
        phase 0 — runs before respawn so a sufficiently large influx
        can fund refills scheduled for this tick.
        """
        if self.energy_pool is None:
            return
        rate = float(self.world_config.ambient_influx_rate)
        if rate <= 0.0:
            return
        self.energy_pool.credit_ambient_influx(rate)

    def _apply_food_respawn(self) -> None:
        """Phase 0 of ``step()``: refill scheduled FOOD cells (v0.18).

        No-op when no cooldown is configured (the subscription never
        registered, so ``respawn_at_tick`` stays all-zero and the
        predicate is false everywhere). When configured, scans for cells
        where ``kind == EMPTY AND respawn_at_tick > 0 AND
        tick_count >= respawn_at_tick``. For each such cell, flip
        ``kind`` to FOOD with ``food_value_default``, reset
        ``respawn_at_tick`` to 0, and emit one ``FoodRespawned`` event.

        Refill happens regardless of cell occupancy. An agent standing
        on a cell that refills sees the food via its sensor next tick
        and (under the v0.14 reflex) eats it. This preserves symmetry
        between occupied and unoccupied cells and avoids the
        stationary-agent-blocks-respawn fairness asymmetry.

        v0.19 strict-conservation: when an energy pool is configured,
        each refill must be funded by a successful pool debit of
        ``food_value_default``. On debit failure, the cell's schedule
        is cleared (sentinel reset to 0; cell stays EMPTY) and a
        ``PoolRespawnDenied`` event is emitted in place of
        ``FoodRespawned``. Pre-reg §"Respawn failure semantics" pins
        this as option (i) — clear-the-schedule rather than defer.
        """
        if self._ate_food_handler is None:
            return  # No cooldown configured; nothing scheduled, ever.
        # Vectorized predicate; cheap on chamber-sized layers.
        ready = (
            (self.world.kind_layer == CellKind.EMPTY)
            & (self.world.respawn_at_tick > 0)
            & (self.world.respawn_at_tick <= self.tick_count)
        )
        if not ready.any():
            return
        food_value_default = float(self.world_config.food_value_default)
        # np.argwhere returns ((x, y), ...) in lexicographic order — stable
        # across runs given identical world state, so determinism is
        # preserved without extra sorting.
        for x, y in np.argwhere(ready):
            x_i, y_i = int(x), int(y)
            if self.energy_pool is not None and not self.energy_pool.try_debit_respawn(
                food_value_default
            ):
                # Pool can't fund the refill. Cell stays EMPTY; clear schedule
                # so the cooldown does not loop on this empty pool every tick.
                self.world.respawn_at_tick[x_i, y_i] = 0
                self.record_event(PoolRespawnDenied(x=x_i, y=y_i, tick=self.tick_count))
                continue
            self.world.kind_layer[x_i, y_i] = CellKind.FOOD
            self.world.food_value[x_i, y_i] = food_value_default
            self.world.respawn_at_tick[x_i, y_i] = 0
            self.record_event(FoodRespawned(x=x_i, y=y_i, tick=self.tick_count))

    def step(self) -> None:
        # 0a. v0.19 ambient influx (phase 0a). No-op when no pool is
        #     configured or influx_rate == 0. Runs before respawn so an
        #     influx-rich open-ecology arm can fund this tick's refills.
        self._apply_ambient_influx()

        # 0b. v0.18 food respawn (phase 0). No-op when cooldown is not
        #     configured (subscription never fired, all schedules are 0).
        #     Refilled cells are visible to the foraging policy this tick —
        #     placement before the snapshot avoids the off-by-one that
        #     would arise if respawn ran after agent decisions. Under
        #     v0.19 with a finite pool, each refill must be pool-funded.
        self._apply_food_respawn()

        # 1. Snapshot active agents.
        active: list[HHAgent] = [a for a in self.agents if isinstance(a, HHAgent) and a.body.alive]
        # 2. Deterministic shuffle via NumPy agent_order stream.
        order = self.streams.agent_order.permutation(len(active))
        ordered = [active[i] for i in order]

        # 3. Each agent steps once.
        for agent in ordered:
            agent.step()

        # 4. Baseline metabolism + per-agent memory decay (SPEC §13.3).
        for agent in self.agents:
            if isinstance(agent, HHAgent):
                agent.apply_metabolism_step()
                agent.apply_memory_decay()

        # 4.5 v0.2 reflex-cell substrate: automatic reproduction trigger.
        # No-op for the v0.7..v0.13 deliberative-voluntary path
        # (auto_reproduction_enabled defaults to False).
        if self.auto_reproduction_enabled:
            for agent in self.agents:
                if isinstance(agent, HHAgent):
                    agent.apply_auto_reproduction()

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

    def _process_birth_queue(self) -> None:  # noqa: PLR0912, PLR0915 — birth path is cohesive (gates + reproduction + child wiring + accumulators); extracting would obscure the lifecycle.
        if not self._birth_queue:
            return
        # Snapshot + clear so reproductions during processing don't recurse.
        parents = self._birth_queue
        self._birth_queue = []
        # v0.20: per-mode debit amount + parent-energy gate guard. Resolved
        # once per call rather than per-parent.
        mode = self.reproduction_config.child_funding_mode
        offspring_start_energy = float(self.reproduction_config.offspring_start_energy)
        energy_cost = float(self.reproduction_config.energy_cost)
        if mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP:
            pool_debit_amount = offspring_start_energy - energy_cost
        else:
            pool_debit_amount = offspring_start_energy
        for parent in parents:
            if not parent.body.alive:
                continue
            occupied = self.occupied_cells_excluding(parent)
            # v0.19/v0.20 strict-conservation: when an ambient pool is
            # configured, gates fire in (placement, parent-energy under
            # transfer mode only, pool) order. All checks happen before any
            # state mutation; on any failure no debits or events of birth
            # fire (parent stays alive and re-eligible next tick). Under
            # POOL_FULL the pool debit is offspring_start_energy (v0.19
            # semantics, preserved). Under PARENT_TRANSFER_POOL_GAP it is
            # the gap (offspring_start_energy - energy_cost); the parent
            # debit happens inside process_reproduction unchanged.
            if self.energy_pool is not None:
                if find_adjacent_empty_cell(self.world, parent.body, occupied) is None:
                    # No placement available — same outcome as v0.7..v0.18
                    # (no energy lost). Skip without touching the pool.
                    continue
                # v0.20 transfer-mode parent-energy gate. Under POOL_FULL the
                # parent's energy_cost is destroyed unconditionally
                # (charge_parent floors at 0), preserving v0.19 dynamics
                # exactly; this gate fires only when the parent's transfer
                # would underfund the child's body energy.
                if (
                    mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP
                    and parent.body.energy < energy_cost
                ):
                    self.record_event(
                        BirthDeniedParentEnergy(
                            parent_id=parent.body.id,
                            x=parent.body.x,
                            y=parent.body.y,
                            tick=self.tick_count,
                        )
                    )
                    self.births_blocked_by_parent_energy += 1
                    continue
                if not self.energy_pool.try_debit_child_startup(pool_debit_amount):
                    self.record_event(
                        PoolBirthDenied(
                            parent_id=parent.body.id,
                            x=parent.body.x,
                            y=parent.body.y,
                            tick=self.tick_count,
                        )
                    )
                    continue
            # v0.45 (additive): the chamber driver may install a
            # birth_redirect_callback on the model when the intervention
            # kind is one of v0.45's two. The callback is gated to
            # ``tick > 50`` HERE at the call site so process_reproduction
            # never sees the callback for pre-50 reproduction. Default
            # path (no callback installed, or tick <= 50) is byte-
            # identical to v0.21..v0.44.
            v045_callback = getattr(self, "v045_birth_redirect_callback", None)
            active_callback = (
                v045_callback if (v045_callback is not None and self.tick_count > 50) else None
            )
            outcome = process_reproduction(
                self.world,
                parent.body,
                parent_rng=parent.agent_rng,
                trait_config=self.trait_config,
                body_config=self.body_config,
                reproduction_config=self.reproduction_config,
                child_id=self._next_body_id,
                occupied=occupied,
                birth_redirect_callback=active_callback,
            )
            if outcome is None:
                # Defensive: under v0.19 we pre-checked placement so this
                # branch should not fire when a pool is configured. Under
                # v0.7..v0.18 (no pool) this is the existing
                # placement-rejected path.
                continue
            updated_parent_body, child_body = outcome
            parent.body = updated_parent_body
            self._next_body_id += 1

            # SPEC §13.4: children get fresh memory of the parent's
            # representation type, never inherit parent's accumulated state.
            if parent.memory is None:
                child_memory: ValenceMemory | DirectionalMemory | ScalarMemory | None = None
            elif isinstance(parent.memory, ValenceMemory):
                child_memory = make_memory(self.world_config.width, self.world_config.height)
            elif isinstance(parent.memory, DirectionalMemory):
                child_memory = make_directional_memory()
            elif isinstance(parent.memory, ScalarMemory):
                child_memory = make_scalar_memory()
            else:
                msg = f"Unknown parent memory type {type(parent.memory)!r}"
                raise TypeError(msg)
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
            self._record_trait_fingerprint(child_body, birth_tick=self.tick_count)
            born = AgentBorn(
                agent_id=child_body.id,
                parent_id=child_body.parent_id,
                lineage_id=child_body.lineage_id,
                x=child_body.x,
                y=child_body.y,
                tick=self.tick_count,
            )
            self.event_log.append(LoggedEvent(tick=self.tick_count, event=born))
            emit(self, born)
            # v0.20 conservation accumulators. Increment at successful birth
            # only — failed births (placement / parent-energy / pool gates)
            # already returned without touching parent or pool state, so no
            # ledger entry should fire.
            if mode == ChildFundingMode.PARENT_TRANSFER_POOL_GAP:
                self.parent_energy_transferred_to_child += energy_cost
            else:
                self.reproduction_heat_loss += energy_cost
            # ``child_agent`` is intentionally referenced via model.agents only.
            del child_agent
