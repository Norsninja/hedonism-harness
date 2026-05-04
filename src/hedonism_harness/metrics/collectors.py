"""Mesa ``DataCollector`` wiring for snapshot-style metrics (SPEC §17.1).

Snapshot metrics are sampled once per tick from live model state. They answer
"how is the population doing right now?" — population, average energy, average
trait values, etc.

Event-style metrics (births, deaths, food events, hazard entries) live in
``aggregators.py`` and subscribe to blinker signals. The two layers are
complementary: ``DataCollector`` for time series, aggregators for tallies.

Per SPEC §27.11, ``metrics/`` may import ``core/events``, ``mesa``, and the
model layer (only as the consumed type) — but not ``io/``. IO writers
consume what we produce here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mesa import DataCollector

from hedonism_harness.mesa_agents import HHAgent

if TYPE_CHECKING:
    from hedonism_harness.model import HHModel


def _alive_hh_agents(model: HHModel) -> list[HHAgent]:
    return [a for a in model.agents if isinstance(a, HHAgent) and a.body.alive]


def _population(model: HHModel) -> int:
    return len(_alive_hh_agents(model))


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _avg_energy(model: HHModel) -> float:
    return _avg([a.body.energy for a in _alive_hh_agents(model)])


def _avg_health(model: HHModel) -> float:
    return _avg([a.body.health for a in _alive_hh_agents(model)])


def _avg_age(model: HHModel) -> float:
    return _avg([float(a.body.age) for a in _alive_hh_agents(model)])


def _avg_trait(name: str):
    """Build a model reporter for a trait field's population mean."""

    def reporter(model: HHModel) -> float:
        return _avg([float(getattr(a.body.traits, name)) for a in _alive_hh_agents(model)])

    reporter.__name__ = f"avg_trait_{name}"
    return reporter


# Trait names whose population means we track per tick. Keep this list short —
# anything specialty can be derived from agent_lifetimes.csv post-run.
SNAPSHOT_TRAIT_NAMES: tuple[str, ...] = (
    "hunger_pain_sensitivity",
    "fear_sensitivity",
    "pleasure_sensitivity",
    "reproduction_drive",
    "risk_tolerance",
    "metabolic_rate",
)


def build_default_collector() -> DataCollector:
    """Return a ``DataCollector`` populated with the v0.1 snapshot reporters.

    The collector is meant to be attached to ``HHModel`` via
    ``model.datacollector = build_default_collector()`` and ticked by the
    caller's experiment driver (``model.datacollector.collect(model)``).
    Construction is decoupled from ``HHModel.__init__`` so experiments can
    customize the reporter set without subclassing the model.
    """
    model_reporters: dict[str, object] = {
        "population": _population,
        "avg_energy": _avg_energy,
        "avg_health": _avg_health,
        "avg_age": _avg_age,
    }
    for trait_name in SNAPSHOT_TRAIT_NAMES:
        model_reporters[f"avg_trait_{trait_name}"] = _avg_trait(trait_name)

    return DataCollector(model_reporters=model_reporters)
