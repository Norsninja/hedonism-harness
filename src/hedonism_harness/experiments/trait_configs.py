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


# ---------------------------------------------------------------------------
# v0.6 grid-sweep parametric factory
# ---------------------------------------------------------------------------


def tuned_trait_config(
    *,
    fear_max: float,
    hunger_min: float,
    risk_min: float,
) -> TraitConfig:
    """Parametric ``TraitConfig`` for the v0.6 grid sweep.

    Holds every other axis at the v0.5 ``permissive`` setting so the only
    degrees of freedom are the three load-bearing knobs from the v0.4
    evidence:

      - ``fear_max``     — ceiling on ``fear_sensitivity`` range.
      - ``hunger_min``   — floor on ``hunger_pain_sensitivity`` range.
      - ``risk_min``     — floor on ``risk_tolerance`` range.

    All other ranges (injury ceiling, pleasure floor, pain-tolerance floor,
    plus all SPEC-default axes) match ``permissive_trait_config()``. This
    isolates the three-axis grid from confounding range changes.

    Validates that each parameter stays inside SPEC §8.1; raises
    ``ValueError`` otherwise so a typo like ``fear_max=5.0`` fails loudly.
    """
    # Bounds checks against SPEC §8.1 master ranges.
    spec = TraitConfig()
    if not (spec.fear_sensitivity.min <= fear_max <= spec.fear_sensitivity.max):
        msg = (
            f"fear_max={fear_max} outside SPEC fear_sensitivity range "
            f"[{spec.fear_sensitivity.min}, {spec.fear_sensitivity.max}]"
        )
        raise ValueError(msg)
    if not (spec.hunger_pain_sensitivity.min <= hunger_min <= spec.hunger_pain_sensitivity.max):
        msg = (
            f"hunger_min={hunger_min} outside SPEC hunger_pain_sensitivity range "
            f"[{spec.hunger_pain_sensitivity.min}, {spec.hunger_pain_sensitivity.max}]"
        )
        raise ValueError(msg)
    if not (spec.risk_tolerance.min <= risk_min <= spec.risk_tolerance.max):
        msg = (
            f"risk_min={risk_min} outside SPEC risk_tolerance range "
            f"[{spec.risk_tolerance.min}, {spec.risk_tolerance.max}]"
        )
        raise ValueError(msg)

    return TraitConfig(
        hunger_pain_sensitivity=TraitRange(min=hunger_min, max=2.5),
        injury_pain_sensitivity=TraitRange(min=0.25, max=1.5),
        fear_sensitivity=TraitRange(min=0.0, max=fear_max),
        pleasure_sensitivity=TraitRange(min=1.0, max=2.5),
        pain_tolerance=TraitRange(min=0.4, max=1.0),
        risk_tolerance=TraitRange(min=risk_min, max=1.0),
        # SPEC-default axes (kept explicit so a SPEC change raises a visible diff).
        reproduction_drive=TraitRange(min=0.0, max=3.0),
        novelty_drive=TraitRange(min=0.0, max=2.0),
        uncertainty_aversion=TraitRange(min=0.0, max=2.0),
        memory_strength=TraitRange(min=0.0, max=1.0),
        memory_decay_rate=TraitRange(min=0.0, max=0.1),
        sensor_radius=TraitRange(min=1, max=6),
        metabolic_rate=TraitRange(min=0.5, max=2.0),
    )


def cell_id(*, fear_max: float, hunger_min: float, risk_min: float) -> str:
    """Human-readable filesystem-safe id for a grid cell.

    Format: ``f{fear_max}-h{hunger_min}-r{risk_min}``. Examples:
    ``f1.5-h1.0-r0.4`` is the v0.5 permissive cell.
    """
    return f"f{fear_max:g}-h{hunger_min:g}-r{risk_min:g}"


# ---------------------------------------------------------------------------
# v0.7b motivation-sweep helper
# ---------------------------------------------------------------------------


def motivation_trait_config(*, drive_min: float) -> TraitConfig:
    """v0.7b factory: v0.6 winner trait ranges with a raised
    ``reproduction_drive`` floor.

    Holds the v0.6 winner ``tuned_trait_config(fear_max=1.5,
    hunger_min=1.0, risk_min=0.55)`` fixed and overrides only the
    ``reproduction_drive`` range floor. Used to study whether higher
    reproductive intent converts threshold eligibility into multiple
    births across seeds — separately from the energy-economics axis
    swept in v0.7.

    The ceiling stays at SPEC §8.1 (``3.0``) so a higher floor narrows
    the range upward; ``drive_min=0.0`` is the v0.6 winner identity.
    """
    spec = TraitConfig()
    if not (spec.reproduction_drive.min <= drive_min <= spec.reproduction_drive.max):
        msg = (
            f"drive_min={drive_min} outside SPEC reproduction_drive range "
            f"[{spec.reproduction_drive.min}, {spec.reproduction_drive.max}]"
        )
        raise ValueError(msg)
    base = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    return base.model_copy(
        update={"reproduction_drive": TraitRange(min=drive_min, max=spec.reproduction_drive.max)}
    )


# ---------------------------------------------------------------------------
# v0.8 eligibility-rescue helper
# ---------------------------------------------------------------------------


def eligibility_trait_config(*, sensor_radius_min: int) -> TraitConfig:
    """v0.8 factory: v0.6 winner trait ranges with a raised
    ``sensor_radius`` floor.

    Holds every other axis at the v0.6 winner setting and overrides only
    the ``sensor_radius`` range floor. Used to study whether wider
    perception (and the higher per-tick metabolic cost it carries via
    ``BodyConfig.sensor_radius_metabolic_cost``) raises eligibility
    supply enough to produce reproduction across multiple seeds.

    The ceiling stays at SPEC §8.1 (``6``) so a higher floor narrows the
    range upward; ``sensor_radius_min=1`` is the v0.6 winner identity.
    """
    spec = TraitConfig()
    if not (spec.sensor_radius.min <= sensor_radius_min <= spec.sensor_radius.max):
        msg = (
            f"sensor_radius_min={sensor_radius_min} outside SPEC sensor_radius range "
            f"[{spec.sensor_radius.min}, {spec.sensor_radius.max}]"
        )
        raise ValueError(msg)
    base = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    return base.model_copy(
        update={"sensor_radius": TraitRange(min=sensor_radius_min, max=spec.sensor_radius.max)}
    )


# ---------------------------------------------------------------------------
# v0.9 memory-arm helper
# ---------------------------------------------------------------------------


def memory_trait_config(
    *,
    memory_strength_min: float,
    memory_decay_rate_max: float,
) -> TraitConfig:
    """v0.9 factory: v0.6 winner trait ranges with overridden memory bounds.

    Holds every other axis at the v0.6 winner setting and overrides only the
    two memory ranges:

      - ``memory_strength`` floor raised from SPEC default ``0.0`` to
        ``memory_strength_min`` (ceiling stays at SPEC ``1.0``).
      - ``memory_decay_rate`` ceiling lowered from SPEC default ``0.1`` to
        ``memory_decay_rate_max`` (floor stays at SPEC ``0.0``).

    The cell ``(memory_strength_min=0.0, memory_decay_rate_max=0.1)`` is the
    SPEC-permissive memory identity — same range bounds as the v0.6 winner.
    Higher ``memory_strength_min`` narrows the range upward (slower per-cell
    EMA updates); lower ``memory_decay_rate_max`` narrows the range downward
    (slower per-tick forgetting).
    """
    spec = TraitConfig()
    if not (spec.memory_strength.min <= memory_strength_min <= spec.memory_strength.max):
        msg = (
            f"memory_strength_min={memory_strength_min} outside SPEC memory_strength range "
            f"[{spec.memory_strength.min}, {spec.memory_strength.max}]"
        )
        raise ValueError(msg)
    if not (spec.memory_decay_rate.min <= memory_decay_rate_max <= spec.memory_decay_rate.max):
        msg = (
            f"memory_decay_rate_max={memory_decay_rate_max} outside SPEC memory_decay_rate range "
            f"[{spec.memory_decay_rate.min}, {spec.memory_decay_rate.max}]"
        )
        raise ValueError(msg)
    base = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    return base.model_copy(
        update={
            "memory_strength": TraitRange(min=memory_strength_min, max=spec.memory_strength.max),
            "memory_decay_rate": TraitRange(
                min=spec.memory_decay_rate.min, max=memory_decay_rate_max
            ),
        }
    )


def memory_cell_id(*, memory_strength_min: float, memory_decay_rate_max: float) -> str:
    """Filesystem-safe id for a v0.9 memory grid cell.

    Format: ``ms{strength_min}-md{decay_max}``. ``:g`` formatting trims trailing
    zeros so ``(0.0, 0.1)`` formats as ``ms0-md0.1``.
    """
    return f"ms{memory_strength_min:g}-md{memory_decay_rate_max:g}"
