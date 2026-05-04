"""Event-stream subscribers maintaining running tallies (SPEC §17, §27.8).

Aggregators connect to the named blinker signals defined in
``core/events.py``. Each aggregator:

  - owns a small dataclass of running tallies,
  - exposes ``connect()`` / ``disconnect()`` symmetric methods so tests and
    experiments can opt in/out cleanly,
  - optionally scopes to a single ``model`` sender so concurrent batch runs
    do not cross-contaminate (per blinker's per-sender connection model),
  - never writes to disk (that's ``io/``'s job).

Sender filtering: pass ``model=<HHModel instance>`` to the constructor and
the aggregator will only react to signals emitted with that exact sender.
Multiple aggregators in the same process — one per model — stay isolated.
Without ``model`` the aggregator listens to every model in the process,
which is the right default for single-run scripts and tests.

The two aggregators here cover the SPEC §17 metric set:

  - ``EpisodeAggregator``: model-level totals (births, deaths by cause,
    food events, hazard entries, hazard damage delivered, paralysis ticks,
    reproduction requests).
  - ``LifetimeAggregator``: per-agent lifetime tallies, keyed by agent_id —
    the source of ``agent_lifetimes.csv``.

Per SPEC §27.11 ``metrics/`` may import ``core/events`` only (no ``io/``,
no Mesa). The aggregators read events; they do not look at model state.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.events import (
    AgentBorn,
    AgentDied,
    AgentMoved,
    AgentStayed,
    AteFood,
    HazardDamageApplied,
    HazardEntered,
    ReproductionRequested,
    signal_for,
)

# ---------------------------------------------------------------------------
# Episode-level tally
# ---------------------------------------------------------------------------


@dataclass
class EpisodeTally:
    """Running counts for a single simulation run (SPEC §17.1)."""

    births: int = 0
    deaths: int = 0
    starvation_deaths: int = 0
    injury_deaths: int = 0
    food_events: int = 0
    hazard_entries: int = 0
    hazard_damage_total: float = 0.0
    reproduction_requests: int = 0
    moves: int = 0
    stays: int = 0


class EpisodeAggregator:
    """Subscribes to blinker signals; updates an ``EpisodeTally`` in place.

    Usage::

        agg = EpisodeAggregator()
        agg.connect()
        ... run model ...
        agg.disconnect()
        print(agg.tally.births, agg.tally.deaths_by_cause)

    Connection is symmetrical: every ``connect()`` must be matched by a
    ``disconnect()`` to avoid stale handlers across test runs.
    """

    def __init__(self, model: object | None = None) -> None:
        self.tally = EpisodeTally()
        self._model = model
        self._connected = False
        self._handlers = (
            (AgentBorn, self._on_born),
            (AgentDied, self._on_died),
            (AteFood, self._on_ate),
            (HazardEntered, self._on_hazard_entered),
            (HazardDamageApplied, self._on_hazard_damage),
            (ReproductionRequested, self._on_repro_request),
            (AgentMoved, self._on_moved),
            (AgentStayed, self._on_stayed),
        )

    def connect(self) -> None:
        if self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            if self._model is not None:
                sig.connect(handler, sender=self._model)
            else:
                sig.connect(handler)
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            if self._model is not None:
                sig.disconnect(handler, sender=self._model)
            else:
                sig.disconnect(handler)
        self._connected = False

    # Handlers — blinker calls them as (sender, **kwargs). The kwarg name
    # ``event`` is the contract from ``core.events.emit``.

    def _on_born(self, sender: object, event: AgentBorn) -> None:
        self.tally.births += 1

    def _on_died(self, sender: object, event: AgentDied) -> None:
        self.tally.deaths += 1
        if event.cause == DeathCause.STARVATION:
            self.tally.starvation_deaths += 1
        elif event.cause == DeathCause.INJURY:
            self.tally.injury_deaths += 1

    def _on_ate(self, sender: object, event: AteFood) -> None:
        self.tally.food_events += 1

    def _on_hazard_entered(self, sender: object, event: HazardEntered) -> None:
        self.tally.hazard_entries += 1

    def _on_hazard_damage(self, sender: object, event: HazardDamageApplied) -> None:
        self.tally.hazard_damage_total += event.damage

    def _on_repro_request(self, sender: object, event: ReproductionRequested) -> None:
        self.tally.reproduction_requests += 1

    def _on_moved(self, sender: object, event: AgentMoved) -> None:
        self.tally.moves += 1

    def _on_stayed(self, sender: object, event: AgentStayed) -> None:
        self.tally.stays += 1


# ---------------------------------------------------------------------------
# Per-agent lifetime tally
# ---------------------------------------------------------------------------


@dataclass
class LifetimeRecord:
    """Per-agent lifetime tallies (SPEC §17.2)."""

    agent_id: int
    parent_id: int | None = None
    lineage_id: int | None = None
    birth_tick: int | None = None
    death_tick: int | None = None
    death_cause: DeathCause | None = None
    offspring_count: int = 0
    food_events: int = 0
    hazard_entries: int = 0
    hazard_damage_total: float = 0.0
    moves: int = 0
    stays: int = 0
    unique_cells_visited: set[tuple[int, int]] = field(default_factory=set)


class LifetimeAggregator:
    """One ``LifetimeRecord`` per agent, populated incrementally from events.

    Founders never emit ``AgentBorn`` (they are constructed at ``HHModel``
    init), so a record is created lazily on the first event mentioning a
    given ``agent_id``. Founders' ``parent_id`` / ``lineage_id`` /
    ``birth_tick`` will be ``None`` in the record unless populated externally
    (the IO layer does this from ``model.agents`` at run-end).
    """

    def __init__(self, model: object | None = None) -> None:
        self.records: dict[int, LifetimeRecord] = defaultdict(lambda: LifetimeRecord(agent_id=-1))
        self._model = model
        self._connected = False
        self._handlers = (
            (AgentBorn, self._on_born),
            (AgentDied, self._on_died),
            (AteFood, self._on_ate),
            (HazardEntered, self._on_hazard_entered),
            (HazardDamageApplied, self._on_hazard_damage),
            (AgentMoved, self._on_moved),
            (AgentStayed, self._on_stayed),
        )

    def _record(self, agent_id: int) -> LifetimeRecord:
        rec = self.records[agent_id]
        if rec.agent_id == -1:
            rec.agent_id = agent_id
        return rec

    def connect(self) -> None:
        if self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            if self._model is not None:
                sig.connect(handler, sender=self._model)
            else:
                sig.connect(handler)
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            if self._model is not None:
                sig.disconnect(handler, sender=self._model)
            else:
                sig.disconnect(handler)
        self._connected = False

    # Handlers ----------------------------------------------------------

    def _on_born(self, sender: object, event: AgentBorn) -> None:
        rec = self._record(event.agent_id)
        rec.parent_id = event.parent_id
        rec.lineage_id = event.lineage_id
        rec.birth_tick = event.tick
        rec.unique_cells_visited.add((event.x, event.y))
        # Increment parent's offspring count when known.
        parent = self._record(event.parent_id)
        parent.offspring_count += 1

    def _on_died(self, sender: object, event: AgentDied) -> None:
        rec = self._record(event.agent_id)
        rec.death_tick = event.tick
        rec.death_cause = event.cause

    def _on_ate(self, sender: object, event: AteFood) -> None:
        rec = self._record(event.agent_id)
        rec.food_events += 1
        rec.unique_cells_visited.add((event.x, event.y))

    def _on_hazard_entered(self, sender: object, event: HazardEntered) -> None:
        rec = self._record(event.agent_id)
        rec.hazard_entries += 1

    def _on_hazard_damage(self, sender: object, event: HazardDamageApplied) -> None:
        rec = self._record(event.agent_id)
        rec.hazard_damage_total += event.damage

    def _on_moved(self, sender: object, event: AgentMoved) -> None:
        rec = self._record(event.agent_id)
        rec.moves += 1
        rec.unique_cells_visited.add((event.to_x, event.to_y))

    def _on_stayed(self, sender: object, event: AgentStayed) -> None:
        rec = self._record(event.agent_id)
        rec.stays += 1
        rec.unique_cells_visited.add((event.x, event.y))
