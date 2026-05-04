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
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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

    @property
    def has_food_events(self) -> bool:
        return not math.isnan(self.median_food_event_tick)


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

    # ------------------------------------------------------------------
    # Subscriber lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self._connected:
            return
        signal_for(AteFood).connect(self._on_ate, sender=self._model)
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        signal_for(AteFood).disconnect(self._on_ate, sender=self._model)
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
        return MemoryTelemetry(
            agents_with_memory_updates=agents_with_updates,
            total_memory_updates=total_updates,
            repeat_food_visits=repeat_food_visits,
            median_food_event_tick=median_tick,
        )


def empty_telemetry() -> MemoryTelemetry:
    """A neutral telemetry record used when a cell did not run."""
    return MemoryTelemetry(
        agents_with_memory_updates=0,
        total_memory_updates=0,
        repeat_food_visits=0,
        median_food_event_tick=math.nan,
    )


# Convenience field-list for CSV writers.
TELEMETRY_FIELDS: tuple[str, ...] = (
    "agents_with_memory_updates",
    "total_memory_updates",
    "repeat_food_visits",
    "median_food_event_tick",
)
