"""v0.8 eligibility telemetry — per-run instrumentation.

The v0.7 + v0.7b sweeps showed that lowering ``energy_threshold`` to 50
unlocks one birth in one seed, and that ``energy_cost`` and
``reproduction_drive_min`` are dormant at this throughput. The
bottleneck is upstream of the reproduction subsystem: agents must
*survive long enough* to clear ``energy_threshold`` past
``ReproductionConfig.min_age``. v0.8 instruments this question with
seven new fields:

  - ``eligible_agent_ticks``           — total agent-ticks where
                                          ``can_reproduce(...) is True``
  - ``seeds_with_reproduction_eligibility`` — derived at aggregate
                                          time from per-run
                                          ``had_any_eligibility``
  - ``first_eligibility_tick``         — earliest tick any agent in the
                                          run was eligible (or ``None``)
  - ``max_energy_after_min_age``       — peak energy any agent reached
                                          *after* clearing min_age
  - ``food_events_after_min_age``      — AteFood events fired by agents
                                          whose age at event time was
                                          >= min_age
  - ``deaths_before_min_age``          — AgentDied events for agents
                                          younger than min_age
  - ``median_death_age``               — median age across all observed
                                          deaths (NaN if no deaths)

Implementation: a lightweight collector subscribes to ``AgentBorn`` /
``AteFood`` / ``AgentDied`` for the time-correlated metrics and is
polled per-tick by ``run_chamber`` (via the ``tick_observer`` hook)
for the state-snapshot metrics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hedonism_harness.core.events import AgentBorn, AgentDied, AteFood, signal_for
from hedonism_harness.core.reproduction import can_reproduce
from hedonism_harness.mesa_agents import HHAgent

if TYPE_CHECKING:
    from hedonism_harness.core.config import ReproductionConfig
    from hedonism_harness.model import HHModel


@dataclass(frozen=True)
class EligibilityTelemetry:
    """Per-run snapshot of the v0.8 eligibility instrumentation."""

    eligible_agent_ticks: int
    had_any_eligibility: bool
    first_eligibility_tick: int | None
    max_energy_after_min_age: float
    food_events_after_min_age: int
    deaths_before_min_age: int
    median_death_age: float  # math.nan when no deaths observed

    @property
    def has_deaths(self) -> bool:
        return not math.isnan(self.median_death_age)


class EligibilityTelemetryCollector:
    """Mutable per-run telemetry accumulator.

    Connect at the start of a run; call ``observe_tick`` after each
    ``model.step()``; call ``finalize`` at run end to produce the
    immutable ``EligibilityTelemetry`` snapshot.
    """

    def __init__(self, model: HHModel, repro_cfg: ReproductionConfig) -> None:
        self._model = model
        self._repro_cfg = repro_cfg
        # Per-agent birth tick. Founders have birth_tick = 0 (constructed
        # at model init, before any ticks have run). Children's birth
        # ticks come from AgentBorn events.
        self._birth_ticks: dict[int, int] = {}
        for agent in model.agents:
            if isinstance(agent, HHAgent):
                self._birth_ticks[agent.body.id] = 0

        self.eligible_agent_ticks: int = 0
        self.first_eligibility_tick: int | None = None
        self.max_energy_after_min_age: float = 0.0
        self.food_events_after_min_age: int = 0
        self.deaths_before_min_age: int = 0
        self._death_ages: list[int] = []

        self._connected = False
        self._handlers = (
            (AgentBorn, self._on_born),
            (AteFood, self._on_ate),
            (AgentDied, self._on_died),
        )

    # ------------------------------------------------------------------
    # Subscriber lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        if self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            sig.connect(handler, sender=self._model)
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        for event_type, handler in self._handlers:
            sig = signal_for(event_type)
            sig.disconnect(handler, sender=self._model)
        self._connected = False

    # ------------------------------------------------------------------
    # Per-tick polling (called by run_chamber after each step)
    # ------------------------------------------------------------------

    def observe_tick(self) -> None:
        """Walk living agents and update eligibility / peak-energy counters."""
        living: list[HHAgent] = [
            a for a in self._model.agents if isinstance(a, HHAgent) and a.body.alive
        ]
        occupied: frozenset[tuple[int, int]] = frozenset((a.body.x, a.body.y) for a in living)
        tick = self._model.tick_count
        min_age = self._repro_cfg.min_age
        for agent in living:
            body = agent.body
            if body.age >= min_age:
                self.max_energy_after_min_age = max(self.max_energy_after_min_age, body.energy)
            if can_reproduce(self._model.world, body, self._repro_cfg, occupied):
                self.eligible_agent_ticks += 1
                if self.first_eligibility_tick is None:
                    self.first_eligibility_tick = tick

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_born(self, sender: object, event: AgentBorn) -> None:
        # Children's birth tick comes from the AgentBorn event.
        self._birth_ticks[event.agent_id] = event.tick

    def _on_ate(self, sender: object, event: AteFood) -> None:
        # ``AteFood`` events do not carry their own ``tick`` field; read it
        # from the model (which is the signal sender, but we keep the
        # explicit reference so the handler is robust to sender filtering).
        birth_tick = self._birth_ticks.get(event.agent_id, 0)
        age_at_event = self._model.tick_count - birth_tick
        if age_at_event >= self._repro_cfg.min_age:
            self.food_events_after_min_age += 1

    def _on_died(self, sender: object, event: AgentDied) -> None:
        birth_tick = self._birth_ticks.get(event.agent_id, 0)
        age_at_death = event.tick - birth_tick
        self._death_ages.append(age_at_death)
        if age_at_death < self._repro_cfg.min_age:
            self.deaths_before_min_age += 1

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------

    def finalize(self) -> EligibilityTelemetry:
        if self._death_ages:
            sorted_ages = sorted(self._death_ages)
            mid = len(sorted_ages) // 2
            if len(sorted_ages) % 2 == 1:
                median = float(sorted_ages[mid])
            else:
                median = (sorted_ages[mid - 1] + sorted_ages[mid]) / 2.0
        else:
            median = math.nan
        return EligibilityTelemetry(
            eligible_agent_ticks=self.eligible_agent_ticks,
            had_any_eligibility=self.eligible_agent_ticks > 0,
            first_eligibility_tick=self.first_eligibility_tick,
            max_energy_after_min_age=self.max_energy_after_min_age,
            food_events_after_min_age=self.food_events_after_min_age,
            deaths_before_min_age=self.deaths_before_min_age,
            median_death_age=median,
        )


def empty_telemetry() -> EligibilityTelemetry:
    """A neutral telemetry record used when a cell did not run."""
    return EligibilityTelemetry(
        eligible_agent_ticks=0,
        had_any_eligibility=False,
        first_eligibility_tick=None,
        max_energy_after_min_age=0.0,
        food_events_after_min_age=0,
        deaths_before_min_age=0,
        median_death_age=math.nan,
    )


# Convenience field-list for CSV writers.
TELEMETRY_FIELDS: tuple[str, ...] = (
    "eligible_agent_ticks",
    "had_any_eligibility",
    "first_eligibility_tick",
    "max_energy_after_min_age",
    "food_events_after_min_age",
    "deaths_before_min_age",
    "median_death_age",
)
