"""Trait archetypes for the v0.2 positive-control experiment.

The v0.1 pilot showed fear paralysis under the default uniform-random trait
distribution: 40/40 founders died of starvation, 0 hazard entries. The next
question is not "what should defaults be?" but **can the harness express
different behavioral phenotypes at all** when traits are biased toward known
extremes?

This module exports four deterministic ``Traits`` instances whose load-bearing
axes are pinned to SPEC §8.1 extremes; all other traits are at the midpoint of
their configured range. Each archetype is a single fixed instance — every
founder in a positive-control condition shares identical traits, so within-
condition variance comes only from the ``agent_order`` / ``action_noise`` /
``hazard_resolution`` RNG streams.

Per SPEC §27.11 + the v0.1 handoff decision: archetype factories live in
``experiments/``, never in ``core/traits.py``. The global ``TraitConfig``
defaults are not modified.

The archetype semantics:

  - ``FEARFUL``   — should *not* cross. Sanity floor.
  - ``RECKLESS``  — should cross if the harness can express a crosser.
  - ``BALANCED``  — deterministic median agent (every trait at its midpoint).
  - ``EXPLORER``  — novelty-driven; will it cross via curiosity alone?

The success criterion for v0.2 lives in the experiment runner: at minimum,
*some* archetype must produce ≥1 hazard entry across N seeds for the harness
to count as phenotype-capable.
"""

from __future__ import annotations

from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, Traits


def _midpoint(config: TraitConfig, name: str) -> float:
    rng_range = config.range_for(name)
    return (rng_range.min + rng_range.max) / 2.0


def _build(config: TraitConfig, **overrides: float) -> Traits:
    """Build a ``Traits`` with all unspecified fields at the midpoint of their range.

    ``sensor_radius`` is rounded to int (the only integer trait).
    """
    values: dict[str, float | int] = {}
    for name in TRAIT_NAMES:
        if name in overrides:
            values[name] = overrides[name]
        else:
            values[name] = _midpoint(config, name)
    # sensor_radius must be int.
    values["sensor_radius"] = round(values["sensor_radius"])
    return Traits(**values)  # type: ignore[arg-type]


def fearful(config: TraitConfig | None = None) -> Traits:
    """High fear, low hunger drive, low pain tolerance — should never cross."""
    cfg = config or TraitConfig()
    return _build(
        cfg,
        hunger_pain_sensitivity=cfg.hunger_pain_sensitivity.min,
        injury_pain_sensitivity=cfg.injury_pain_sensitivity.max,
        fear_sensitivity=cfg.fear_sensitivity.max,
        pain_tolerance=cfg.pain_tolerance.min,
        risk_tolerance=cfg.risk_tolerance.min,
    )


def reckless(config: TraitConfig | None = None) -> Traits:
    """High hunger, low fear, high pain tolerance — should cross if anyone can."""
    cfg = config or TraitConfig()
    return _build(
        cfg,
        hunger_pain_sensitivity=cfg.hunger_pain_sensitivity.max,
        injury_pain_sensitivity=cfg.injury_pain_sensitivity.min,
        fear_sensitivity=cfg.fear_sensitivity.min,
        pain_tolerance=cfg.pain_tolerance.max,
        risk_tolerance=cfg.risk_tolerance.max,
    )


def balanced(config: TraitConfig | None = None) -> Traits:
    """Every trait at the midpoint of its range — deterministic median agent."""
    cfg = config or TraitConfig()
    return _build(cfg)


def explorer(config: TraitConfig | None = None) -> Traits:
    """High novelty drive, low uncertainty aversion — curiosity-driven crosser?"""
    cfg = config or TraitConfig()
    return _build(
        cfg,
        novelty_drive=cfg.novelty_drive.max,
        uncertainty_aversion=cfg.uncertainty_aversion.min,
    )


# Stable ordering for report tables and CSV columns.
ARCHETYPE_NAMES: tuple[str, ...] = ("fearful", "reckless", "balanced", "explorer")


def archetype_traits(name: str, config: TraitConfig | None = None) -> Traits:
    """Lookup helper — raises ``KeyError`` for unknown archetype names."""
    builders = {
        "fearful": fearful,
        "reckless": reckless,
        "balanced": balanced,
        "explorer": explorer,
    }
    if name not in builders:
        msg = f"Unknown archetype {name!r}; valid names: {sorted(builders)}"
        raise KeyError(msg)
    return builders[name](config)
