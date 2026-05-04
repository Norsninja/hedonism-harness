"""v0.9 memory-arm telemetry — per-run instrumentation.

The v0.9 question is whether per-agent valence memory improves repeat
foraging in the hard ``tight_gradient`` chamber, which would in turn
raise the supply of reproductive eligibility. The v0.7b 6-criterion
rule still gates qualification; this telemetry surfaces the *behavioral*
question (do agents return to known food?) so that "memory state exists"
is not misread as "memory rescued the chamber".

Four diagnostic fields per run (the minimum-viable set agreed pre-run):

  - ``agents_with_memory_updates`` — count of distinct agent_ids whose
    memory was updated at least once. With ``use_memory=False`` this is
    structurally 0; with ``use_memory=True`` it should equal the
    population total (every step writes one EMA update).
  - ``total_memory_updates`` — sum of per-agent ``memory.visits.sum()``
    across all agents observed during the run. Approximates total
    agent-ticks of memory activity.
  - ``repeat_food_visits`` — sum of ``max(0, count - 1)`` over per-agent
    ``AteFood`` counts. The headline behavioral metric: if memory helps,
    surviving agents return to known food, raising this count.
  - ``median_food_event_tick`` — median tick across all observed
    ``AteFood`` events. Without memory, the lone food event clusters
    early (one trip across hazard); with memory, repeat visits should
    pull the median later.

Implementation: a lightweight collector subscribes to ``AteFood`` for
the per-agent count + tick history, and is polled per-tick by
``run_chamber`` (via the ``tick_observer`` hook) for the
``memory.visits`` snapshot. The collector tracks
``max(memory.visits.sum())`` per agent so dead-and-removed agents'
peaks are preserved.

v0.12 additions — argmax-changes + action transitions
-----------------------------------------------------
``directional_decisions`` and ``argmax_changes`` count how often the
two scoring passes inside ``HedonismPolicy`` (with vs. without the
projected directional memory) produced different argmax winners — a
cheap, leak-proof check that the action-aware-projection is causally
influencing decisions. ``action_transitions`` is a Counter keyed by
``(action_without_memory_int, action_with_memory_int)`` over only the
swayed decisions, so we can read the directional shift (e.g., did
memory mostly steer EAT↔MOVE, or only MOVE↔MOVE?). All three fields
are populated only when the model's ``policy_decision_log`` is
enabled (``connect()`` enables it on directional sweeps; cell-exact
runs leave them at zero / empty).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hedonism_harness.core.events import AteFood, signal_for
from hedonism_harness.core.memory import DirectionalMemory, ValenceMemory
from hedonism_harness.mesa_agents import HHAgent

if TYPE_CHECKING:
    from hedonism_harness.model import HHModel


@dataclass(frozen=True)
class MemoryTelemetry:
    """Per-run snapshot of v0.9 memory-arm instrumentation."""

    agents_with_memory_updates: int
    total_memory_updates: int
    repeat_food_visits: int
    median_food_event_tick: float  # math.nan when no AteFood events observed
    # v0.12: directional-projection introspection. Zero / empty on
    # cell-exact and mem-off runs.
    directional_decisions: int = 0
    argmax_changes: int = 0
    action_transitions: Counter[tuple[int, int]] = field(default_factory=Counter)

    @property
    def has_food_events(self) -> bool:
        return not math.isnan(self.median_food_event_tick)

    @property
    def argmax_change_rate(self) -> float:
        """Fraction of recorded directional decisions where memory swayed
        the argmax (0.0 when no decisions were recorded)."""
        if self.directional_decisions == 0:
            return 0.0
        return self.argmax_changes / self.directional_decisions


class MemoryTelemetryCollector:
    """Mutable per-run memory-arm telemetry accumulator.

    Connect at the start of a run (before the first ``model.step()``);
    call ``observe_tick`` after each ``model.step()``; call ``finalize``
    at run end to produce the immutable ``MemoryTelemetry`` snapshot.
    """

    def __init__(self, model: HHModel) -> None:
        self._model = model
        # Per-agent maximum observed ``memory.visits.sum()``. Tracked as
        # max-ever so that an agent's contribution is preserved after it
        # dies and is removed from ``model.agents``.
        self._max_visits_per_agent: dict[int, int] = {}
        self._food_events_per_agent: dict[int, int] = {}
        self._food_event_ticks: list[int] = []
        self._connected = False
        # v0.12: snapshot the model's policy_decision_log on disconnect so
        # ``finalize()`` can be called after the run ends without losing
        # the per-decision history. ``None`` means "not yet snapshotted".
        self._decision_log_snapshot: list[tuple[bool, int, int]] | None = None

    # ------------------------------------------------------------------
    # Subscriber lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self._connected:
            return
        signal_for(AteFood).connect(self._on_ate, sender=self._model)
        # v0.12: enable the model's per-decision argmax-with/without-memory
        # log so finalize() can report directional decisions + sway counts.
        # No-op for cell-exact runs (HedonismPolicy never fills the
        # contributing PolicyDecision fields, so the log stays empty).
        self._model.enable_policy_decision_log()
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        signal_for(AteFood).disconnect(self._on_ate, sender=self._model)
        # Snapshot the policy-decision log before clearing it on the
        # model — finalize() may run after disconnect() (see
        # _run_one_cell_seed in memory_grid.py).
        log = self._model.policy_decision_log
        self._decision_log_snapshot = list(log) if log is not None else []
        self._model.disable_policy_decision_log()
        self._connected = False

    # ------------------------------------------------------------------
    # Per-tick polling
    # ------------------------------------------------------------------

    def observe_tick(self) -> None:
        """Snapshot a per-tick "memory activity" count for every living agent.

        Dispatches on memory type:

          - ``ValenceMemory``: uses ``visits.sum()`` (total ``update_at``
            calls, equals ticks the agent has stepped while alive).
          - ``DirectionalMemory``: uses the count of nonzero tendency
            slots (max 8: 4 pleasure + 4 pain). This is a different unit
            from the cell-exact case (saturating, not monotone-with-time);
            interpret per-cell, not across memory types.
        """
        for agent in self._model.agents:
            if not isinstance(agent, HHAgent) or not agent.body.alive:
                continue
            if agent.memory is None:
                continue
            if isinstance(agent.memory, ValenceMemory):
                activity = int(agent.memory.visits.sum())
            elif isinstance(agent.memory, DirectionalMemory):
                # Count direction slots that have any nonzero tendency.
                pleasure_slots = int((agent.memory.pleasure_tendency != 0).sum())
                pain_slots = int((agent.memory.pain_tendency != 0).sum())
                activity = pleasure_slots + pain_slots
            else:
                continue
            aid = agent.body.id
            prior = self._max_visits_per_agent.get(aid, 0)
            if activity > prior:
                self._max_visits_per_agent[aid] = activity

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_ate(self, sender: object, event: AteFood) -> None:
        self._food_events_per_agent[event.agent_id] = (
            self._food_events_per_agent.get(event.agent_id, 0) + 1
        )
        self._food_event_ticks.append(self._model.tick_count)

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self) -> MemoryTelemetry:
        agents_with_updates = sum(1 for v in self._max_visits_per_agent.values() if v > 0)
        total_updates = sum(self._max_visits_per_agent.values())
        repeat_food_visits = sum(max(0, c - 1) for c in self._food_events_per_agent.values())
        if self._food_event_ticks:
            sorted_ticks = sorted(self._food_event_ticks)
            mid = len(sorted_ticks) // 2
            if len(sorted_ticks) % 2 == 1:
                median_tick = float(sorted_ticks[mid])
            else:
                median_tick = (sorted_ticks[mid - 1] + sorted_ticks[mid]) / 2.0
        else:
            median_tick = math.nan

        # v0.12 directional-projection introspection. Use the snapshot
        # captured at disconnect() if available, else read the live log.
        if self._decision_log_snapshot is not None:
            decisions = self._decision_log_snapshot
        elif self._model.policy_decision_log is not None:
            decisions = list(self._model.policy_decision_log)
        else:
            decisions = []
        argmax_changes = sum(1 for swayed, _, _ in decisions if swayed)
        action_transitions: Counter[tuple[int, int]] = Counter(
            (no_mem_action, with_mem_action)
            for swayed, with_mem_action, no_mem_action in decisions
            if swayed
        )

        return MemoryTelemetry(
            agents_with_memory_updates=agents_with_updates,
            total_memory_updates=total_updates,
            repeat_food_visits=repeat_food_visits,
            median_food_event_tick=median_tick,
            directional_decisions=len(decisions),
            argmax_changes=argmax_changes,
            action_transitions=action_transitions,
        )


def empty_telemetry() -> MemoryTelemetry:
    """A neutral telemetry record used when a cell did not run."""
    return MemoryTelemetry(
        agents_with_memory_updates=0,
        total_memory_updates=0,
        repeat_food_visits=0,
        median_food_event_tick=math.nan,
        directional_decisions=0,
        argmax_changes=0,
        action_transitions=Counter(),
    )


# Convenience field-list for CSV writers.
TELEMETRY_FIELDS: tuple[str, ...] = (
    "agents_with_memory_updates",
    "total_memory_updates",
    "repeat_food_visits",
    "median_food_event_tick",
    "directional_decisions",
    "argmax_changes",
)
