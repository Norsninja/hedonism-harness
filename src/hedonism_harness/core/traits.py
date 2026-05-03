"""Inherited trait genome (SPEC §8).

Per SPEC §27.11, this module imports stdlib + numpy + pydantic only — no Mesa,
no IO. Generation and mutation both use a passed-in NumPy ``Generator`` so
behavior stays reproducible per the v0.1 determinism north star.

Design notes:
  - ``Traits`` is a frozen dataclass (not Pydantic) because it is constructed
    on every reproduction and accessed many times per tick during valence
    scoring. The Pydantic validation overhead is paid once on ``TraitConfig``
    construction and never per-agent.
  - Bounds and mutation parameters live in ``TraitConfig`` so an experiment
    can sweep them without touching code.
  - A single ``mutation_sigma`` is applied uniformly across traits per
    SPEC §8.2. Traits with very different scales (e.g. ``sensor_radius``)
    therefore mutate more conservatively in absolute terms — a deliberate
    consequence of the spec's formulation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator


@dataclass(frozen=True)
class Traits:
    """Inherited parameters that transform world states into felt valence."""

    hunger_pain_sensitivity: float
    injury_pain_sensitivity: float
    fear_sensitivity: float
    pleasure_sensitivity: float
    reproduction_drive: float
    novelty_drive: float
    uncertainty_aversion: float
    pain_tolerance: float
    risk_tolerance: float
    memory_strength: float
    memory_decay_rate: float
    sensor_radius: int
    metabolic_rate: float


TRAIT_NAMES: tuple[str, ...] = tuple(f.name for f in fields(Traits))
INTEGER_TRAITS: frozenset[str] = frozenset({"sensor_radius"})


class TraitRange(BaseModel):
    """Inclusive [min, max] bounds for a single trait."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    min: float
    max: float

    @model_validator(mode="after")
    def _check_min_le_max(self) -> TraitRange:
        if self.min > self.max:
            msg = f"TraitRange min ({self.min}) must be <= max ({self.max})"
            raise ValueError(msg)
        return self

    def clamp(self, x: float) -> float:
        return max(self.min, min(self.max, x))


class TraitConfig(BaseModel):
    """Per-trait bounds + mutation parameters (SPEC §8.1, §8.2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hunger_pain_sensitivity: TraitRange = TraitRange(min=0.25, max=2.5)
    injury_pain_sensitivity: TraitRange = TraitRange(min=0.25, max=2.5)
    fear_sensitivity: TraitRange = TraitRange(min=0.0, max=3.0)
    pleasure_sensitivity: TraitRange = TraitRange(min=0.25, max=2.5)
    reproduction_drive: TraitRange = TraitRange(min=0.0, max=3.0)
    novelty_drive: TraitRange = TraitRange(min=0.0, max=2.0)
    uncertainty_aversion: TraitRange = TraitRange(min=0.0, max=2.0)
    pain_tolerance: TraitRange = TraitRange(min=0.0, max=1.0)
    risk_tolerance: TraitRange = TraitRange(min=0.0, max=1.0)
    memory_strength: TraitRange = TraitRange(min=0.0, max=1.0)
    memory_decay_rate: TraitRange = TraitRange(min=0.0, max=0.1)
    sensor_radius: TraitRange = TraitRange(min=1, max=6)
    metabolic_rate: TraitRange = TraitRange(min=0.5, max=2.0)

    mutation_rate: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Per-trait probability of mutating during reproduction.",
    )
    mutation_sigma: float = Field(
        default=0.08,
        ge=0.0,
        description="Standard deviation of the Gaussian mutation kernel.",
    )

    def range_for(self, name: str) -> TraitRange:
        return getattr(self, name)


def random_traits(config: TraitConfig, rng: np.random.Generator) -> Traits:
    """Sample a ``Traits`` instance with each value drawn uniformly from its range."""
    values: dict[str, float | int] = {}
    for name in TRAIT_NAMES:
        rng_range = config.range_for(name)
        if name in INTEGER_TRAITS:
            values[name] = int(rng.integers(int(rng_range.min), int(rng_range.max) + 1))
        else:
            values[name] = float(rng.uniform(rng_range.min, rng_range.max))
    return Traits(**values)  # type: ignore[arg-type]


def mutate_traits(parent: Traits, config: TraitConfig, rng: np.random.Generator) -> Traits:
    """Return a child ``Traits`` derived from ``parent`` with per-trait Gaussian mutation.

    Each trait independently mutates with probability ``config.mutation_rate``.
    Mutated values get a Gaussian delta with std ``config.mutation_sigma`` and
    are clamped to the trait's configured range. Integer traits are rounded.
    """
    values: dict[str, float | int] = {}
    for name in TRAIT_NAMES:
        parent_value = getattr(parent, name)
        rng_range = config.range_for(name)

        if rng.random() < config.mutation_rate:
            new_value = parent_value + rng.normal(0.0, config.mutation_sigma)
        else:
            new_value = parent_value

        clamped = rng_range.clamp(float(new_value))
        if name in INTEGER_TRAITS:
            rounded = round(clamped)
            values[name] = max(int(rng_range.min), min(int(rng_range.max), rounded))
        else:
            values[name] = clamped
    return Traits(**values)  # type: ignore[arg-type]


def validate_traits(traits: Traits, config: TraitConfig) -> None:
    """Raise ``ValueError`` if any trait is outside its configured range.

    Used by tests and debug logging. Not called in the hot path; the normal
    construction path (random/mutate) guarantees in-range values.
    """
    for name in TRAIT_NAMES:
        value = getattr(traits, name)
        rng_range = config.range_for(name)
        if not (rng_range.min <= value <= rng_range.max):
            msg = f"Trait {name}={value} outside range [{rng_range.min}, {rng_range.max}]"
            raise ValueError(msg)
