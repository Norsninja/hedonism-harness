"""Named ``TraitConfig`` factories for the v0.5 default-tuning sweep.

The v0.4 valence fix made archetype phenotypes work in ``tight_gradient``,
but the ``default`` condition (i.i.d.-uniform sampling from the SPEC §8.1
master ranges) still produced only 1 hazard entry / 0 food events across
40 founder-runs. The hypothesis under test:

> The default ``TraitConfig`` ranges over-weight fear and under-weight
> hunger drive. Shifting the floors/ceilings of trait ranges *within* the
> SPEC §8.1 master bounds should produce mixed-phenotype populations.

Per SPEC §27.11 these factories live in ``experiments/`` — we do not
mutate ``core/traits.py`` global defaults until v0.5 produces evidence
that a shift is warranted.

Each factory returns a ``TraitConfig`` whose ranges are sub-ranges of the
SPEC §8.1 master ranges; ``validate_traits`` against the SPEC config
continues to accept any sample drawn from these tighter ranges.
"""

from __future__ import annotations

from hedonism_harness.core.traits import TraitConfig, TraitRange


def default_trait_config() -> TraitConfig:
    """Identity factory — returns the SPEC §8.1 default ``TraitConfig``."""
    return TraitConfig()


def permissive_trait_config() -> TraitConfig:
    """v0.5 candidate: shifted ranges that lean toward Reckless without pinning to it.

    Direction of shift, per the v0.4 evidence (Reckless succeeded; Balanced
    and Fearful did not):

      - Lower the fear ceiling (less terror at max).
      - Lower the injury-pain ceiling (less catastrophic damage perception).
      - Raise the hunger-pain floor (every agent feels the urgency).
      - Raise the pleasure floor (every agent finds food rewarding).
      - Raise the pain-tolerance floor (no hyper-sensitive agents).
      - Raise the risk-tolerance floor (no fully-cautious agents).

    All shifts stay inside SPEC §8.1 master ranges. Other traits
    (novelty, uncertainty, reproduction, memory, sensor, metabolism)
    remain at SPEC defaults so the experiment isolates the fear/hunger
    axis.
    """
    return TraitConfig(
        hunger_pain_sensitivity=TraitRange(min=1.0, max=2.5),
        injury_pain_sensitivity=TraitRange(min=0.25, max=1.5),
        fear_sensitivity=TraitRange(min=0.0, max=1.5),
        pleasure_sensitivity=TraitRange(min=1.0, max=2.5),
        pain_tolerance=TraitRange(min=0.4, max=1.0),
        risk_tolerance=TraitRange(min=0.4, max=1.0),
        # Defaults below match SPEC §8.1 — kept explicit so a future range
        # change to SPEC raises a visible diff instead of silently shifting.
        reproduction_drive=TraitRange(min=0.0, max=3.0),
        novelty_drive=TraitRange(min=0.0, max=2.0),
        uncertainty_aversion=TraitRange(min=0.0, max=2.0),
        memory_strength=TraitRange(min=0.0, max=1.0),
        memory_decay_rate=TraitRange(min=0.0, max=0.1),
        sensor_radius=TraitRange(min=1, max=6),
        metabolic_rate=TraitRange(min=0.5, max=2.0),
    )


# Stable iteration order for report tables and CSV.
ALL_TRAIT_CONFIGS: dict[str, TraitConfig] = {
    "default": default_trait_config(),
    "permissive": permissive_trait_config(),
}


def trait_config_by_name(name: str) -> TraitConfig:
    """Lookup helper — raises ``KeyError`` for unknown names."""
    if name not in ALL_TRAIT_CONFIGS:
        msg = f"Unknown trait config {name!r}; valid names: {sorted(ALL_TRAIT_CONFIGS)}"
        raise KeyError(msg)
    return ALL_TRAIT_CONFIGS[name]
