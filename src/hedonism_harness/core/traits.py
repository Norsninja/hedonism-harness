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

v0.2 / v0.14 addition — unbounded mutation:
  ``TraitConfig.unbounded_mutation`` (default ``False``) controls whether
  ``mutate_traits`` clamps to the per-trait sampling range (``False``,
  preserves v0.1 / v0.7..v0.13 bit-identity) or to module-level physical
  floors and ceilings (``True``, the v0.2 reflex-cell substrate where
  lineages are allowed to drift outside the founder distribution range).
  Physical bounds are at ``_PHYSICAL_FLOORS`` and ``_PHYSICAL_CEILINGS``.
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


# v0.2 spec §"Traits": physical floors / ceilings used by unbounded
# mutation. Floors enforce values that would crash the harness or sensors
# (negative sensitivities, sensor_radius < 1). Ceilings exist only for
# traits that are bounded by their own semantics (tolerances are in
# [0, 1] by construction; memory_strength and memory_decay_rate likewise).
# All other traits have ``None`` ceilings — lineages may drift upward
# without artificial cap.
_PHYSICAL_FLOORS: dict[str, float] = {
    "hunger_pain_sensitivity": 0.0,
    "injury_pain_sensitivity": 0.0,
    "fear_sensitivity": 0.0,
    "pleasure_sensitivity": 0.0,
    "reproduction_drive": 0.0,
    "novelty_drive": 0.0,
    "uncertainty_aversion": 0.0,
    "pain_tolerance": 0.0,
    "risk_tolerance": 0.0,
    "memory_strength": 0.0,
    "memory_decay_rate": 0.0,
    "sensor_radius": 1,
    "metabolic_rate": 0.0,
}
_PHYSICAL_CEILINGS: dict[str, float | None] = {
    "hunger_pain_sensitivity": None,
    "injury_pain_sensitivity": None,
    "fear_sensitivity": None,
    "pleasure_sensitivity": None,
    "reproduction_drive": None,
    "novelty_drive": None,
    "uncertainty_aversion": None,
    "pain_tolerance": 1.0,
    "risk_tolerance": 1.0,
    "memory_strength": 1.0,
    "memory_decay_rate": 1.0,
    "sensor_radius": None,
    "metabolic_rate": None,
}


def _physical_clamp(name: str, value: float) -> float:
    """Clamp ``value`` to the trait's physical floor / ceiling.

    Floors prevent values that would crash sensors or the harness (negative
    sensitivities, sensor_radius below 1). Ceilings only apply to traits
    bounded by definition (tolerances in [0, 1], memory_strength /
    memory_decay_rate in [0, 1]). All other traits drift freely upward
    under unbounded mutation.
    """
    floor = _PHYSICAL_FLOORS[name]
    value = max(value, floor)
    ceiling = _PHYSICAL_CEILINGS[name]
    if ceiling is not None and value > ceiling:
        value = ceiling
    return value


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
    unbounded_mutation: bool = Field(
        default=False,
        description=(
            "When False (v0.1 / v0.7..v0.13 default), mutation clamps to the "
            "per-trait sampling range. When True (v0.2 reflex-cell substrate "
            "default), mutation clamps only to physical floors and ceilings, "
            "allowing lineages to drift outside the founder distribution."
        ),
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
    Mutated values get a Gaussian delta with std ``config.mutation_sigma``.

    Bound enforcement depends on ``config.unbounded_mutation``:
      - ``False`` (default): values clamp to the per-trait sampling range
        ``config.range_for(name)``. Lineages stay inside the founder
        distribution. v0.1 / v0.7..v0.13 behavior.
      - ``True`` (v0.2 reflex-cell substrate): values clamp only to
        physical floors (``_PHYSICAL_FLOORS``) and ceilings
        (``_PHYSICAL_CEILINGS``). Lineages may drift outside the founder
        distribution upward. Floors prevent crashes; ceilings only apply
        to semantically-bounded traits (tolerances, memory_*).

    Integer traits are rounded after clamping.
    """
    values: dict[str, float | int] = {}
    for name in TRAIT_NAMES:
        parent_value = getattr(parent, name)
        rng_range = config.range_for(name)

        if rng.random() < config.mutation_rate:
            new_value = parent_value + rng.normal(0.0, config.mutation_sigma)
        else:
            new_value = parent_value

        if config.unbounded_mutation:
            clamped = _physical_clamp(name, float(new_value))
        else:
            clamped = rng_range.clamp(float(new_value))

        if name in INTEGER_TRAITS:
            rounded = round(clamped)
            if config.unbounded_mutation:
                floor = int(_PHYSICAL_FLOORS[name])
                ceiling = _PHYSICAL_CEILINGS[name]
                rounded = max(floor, rounded)
                if ceiling is not None:
                    rounded = min(int(ceiling), rounded)
                values[name] = rounded
            else:
                values[name] = max(int(rng_range.min), min(int(rng_range.max), rounded))
        else:
            values[name] = clamped
    return Traits(**values)  # type: ignore[arg-type]


def validate_traits(traits: Traits, config: TraitConfig) -> None:
    """Raise ``ValueError`` if any trait is outside its configured range.

    Used by tests and debug logging. Not called in the hot path.

    Validation is against the configured sampling range for the bounded-
    mutation default; under unbounded mutation, mutated traits are not
    expected to satisfy the sampling range bound (only the physical
    floors/ceilings). Use ``validate_traits_physical`` for the unbounded
    case.
    """
    for name in TRAIT_NAMES:
        value = getattr(traits, name)
        rng_range = config.range_for(name)
        if not (rng_range.min <= value <= rng_range.max):
            msg = f"Trait {name}={value} outside range [{rng_range.min}, {rng_range.max}]"
            raise ValueError(msg)


def validate_traits_physical(traits: Traits) -> None:
    """Raise ``ValueError`` if any trait is below its physical floor or
    above its physical ceiling.

    The v0.2 unbounded-mutation counterpart to ``validate_traits``.
    Lineages may drift outside the founder sampling range under
    ``TraitConfig.unbounded_mutation=True``, but they must still satisfy
    physical constraints (no negative sensitivities, no sensor_radius
    below 1, tolerances in [0, 1], etc.).
    """
    for name in TRAIT_NAMES:
        value = getattr(traits, name)
        floor = _PHYSICAL_FLOORS[name]
        if value < floor:
            msg = f"Trait {name}={value} below physical floor {floor}"
            raise ValueError(msg)
        ceiling = _PHYSICAL_CEILINGS[name]
        if ceiling is not None and value > ceiling:
            msg = f"Trait {name}={value} above physical ceiling {ceiling}"
            raise ValueError(msg)
