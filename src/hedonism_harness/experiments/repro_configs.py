"""Named ``ReproductionConfig`` factories for the v0.7 reproduction-emergence sweep.

The v0.6 trait-grid sweep validated the v0.5 permissive zone (27/27 cells
qualified, winner ``f1.5-h1-r0.55``) but produced **0 births in any cell**.
The v0.7 hypothesis under test:

> Reproduction does not emerge under SPEC defaults because the energy
> threshold (70) sits above starting energy (60) and the cost (35) is
> punitive relative to the food-event throughput. Lowering the threshold
> and/or cost should unlock first-generation births while preserving the
> v0.6 food/diversity behavior.

Per SPEC §27.11 these factories live in ``experiments/`` — we do not
mutate ``core/config.py`` ``ReproductionConfig`` defaults until v0.7
produces evidence that a shift is warranted.

The trait config is **fixed** at the v0.6 winner
``tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)``;
v0.7 sweeps only ``ReproductionConfig.energy_threshold`` and
``energy_cost``. Other reproduction knobs (min_age, hazard_threshold,
offspring_start_energy) stay at SPEC defaults so the experiment
isolates the energy-economics axis.
"""

from __future__ import annotations

from hedonism_harness.core.config import ReproductionConfig

# SPEC §7/§14 defaults — re-asserted here so a future change to
# ``ReproductionConfig`` raises a visible diff in this file.
SPEC_ENERGY_THRESHOLD: float = 70.0
SPEC_ENERGY_COST: float = 35.0


def tuned_reproduction_config(
    *,
    energy_threshold: float,
    energy_cost: float,
) -> ReproductionConfig:
    """Parametric ``ReproductionConfig`` for the v0.7 grid sweep.

    Holds every other axis (``min_age``, ``hazard_threshold``,
    ``offspring_start_energy``) at SPEC defaults so the only degrees of
    freedom are the two energy-economics knobs:

      - ``energy_threshold`` — minimum parent energy required to reproduce.
      - ``energy_cost``      — energy debited from parent on success.

    Validates that each parameter is non-negative and within sensible
    operational bounds; raises ``ValueError`` so a typo like
    ``energy_threshold=-1`` fails loudly. Bounds are deliberately wider
    than the v0.7 grid itself so the factory remains useful for future
    sweeps without re-editing.
    """
    if not (0.0 <= energy_threshold <= 100.0):
        msg = f"energy_threshold={energy_threshold} outside operational range [0.0, 100.0]"
        raise ValueError(msg)
    if not (0.0 <= energy_cost <= 100.0):
        msg = f"energy_cost={energy_cost} outside operational range [0.0, 100.0]"
        raise ValueError(msg)
    return ReproductionConfig(
        energy_threshold=energy_threshold,
        energy_cost=energy_cost,
        # SPEC defaults — kept explicit so a SPEC change raises a visible diff.
        offspring_start_energy=30.0,
        min_age=10,
        hazard_threshold=0.5,
    )


def repro_cell_id(*, energy_threshold: float, energy_cost: float) -> str:
    """Human-readable filesystem-safe id for a v0.7 grid cell.

    Format: ``et{energy_threshold}-ec{energy_cost}``. Examples:
    ``et70-ec35`` is the SPEC-default cell (and v0.7 baseline).
    """
    return f"et{energy_threshold:g}-ec{energy_cost:g}"
