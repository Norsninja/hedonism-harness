"""Named ``ChamberLayout`` factories for the v0.3 geometry-tightening sweep.

The v0.2 positive-control experiment ruled out "extreme traits alone produce
crossing." It also revealed why: with the default chamber's spawn at x=1 and
SPEC §8.1 midpoint ``sensor_radius=4``, the east axial sensor ray scans cells
``x ∈ [2..5]`` — pure SAFE. The agent has no spatial information that would
make eastward movement feel better than staying still. Trait differences
scale a zero gradient.

v0.3 isolates that hypothesis by varying chamber geometry and spawn position,
holding traits / policies / hyperparameters constant. Three layouts
(see ``ALL_LAYOUTS``):

  - ``default_layout``    — null baseline (replicates v0.1/v0.2 chamber).
  - ``tight_gradient_layout`` — both hazard AND food enter sensor range from
    spawn. Full positive-gradient test.
  - ``near_hazard_layout`` — default chamber but spawn one column east of the
    safe zone, so the hazard ray fires but food remains invisible. Pure
    avoidance test (does fear gradient alone produce differentiation?).

Per SPEC §27.11 these factories live in ``experiments/`` — no changes to
``core/`` defaults. The layouts are deliberately small and named; do not
parameterize them by adding kwargs. New variants get new factories.

Sensor model reminder (``core/sensors._scan_axial``): radius scans go along
the four cardinal rays only, NOT a square box. So "visible eastward from
``spawn_x``" means cells at ``y == spawn_y`` in ``[spawn_x+1 .. spawn_x+r]``.
The y-coordinate doesn't matter for east/west reach.
"""

from __future__ import annotations

from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout


def default_layout() -> ChamberLayout:
    """v0.1/v0.2 chamber. Spawn x=1, hazard 8-11, food 14-19; nothing visible."""
    return ChamberLayout()


def tight_gradient_layout() -> ChamberLayout:
    """Compressed chamber — both hazard and food visible from spawn.

    Width=9, safe x=[0,2], hazard x=[3,4], food x=[5,8]. With spawn at x=1
    and ``sensor_radius=4`` (midpoint), the east ray scans x∈[2..5]: 1 SAFE,
    2 HAZARD, 1 FOOD. Both opposing gradients enter sensor range; the
    archetypes' diverging valence weights now multiply non-zero signals.
    """
    return ChamberLayout(
        safe_x_min=0,
        safe_x_max=2,
        hazard_x_min=3,
        hazard_x_max=4,
        food_x_min=5,
        food_x_max=8,
        height=6,
        spawn_x=1,
    )


def near_hazard_layout() -> ChamberLayout:
    """Default chamber, spawn moved east so hazard is visible but food is not.

    Same proportions as ``default_layout`` (width 20, hazard x∈[8,11], food
    x∈[14,19]). Founders spawn at x=6 instead of x=1. The east ray with
    ``sensor_radius=4`` scans x∈[7..10]: 3 of 4 hazard columns visible, food
    still invisible. Tests whether a fear-only gradient is sufficient to
    produce trait differentiation in the absence of opposing food signal.
    """
    return ChamberLayout(spawn_x=6)


def widened_gradient_layout() -> ChamberLayout:
    """v0.8 — tight_gradient's proportions with a longer corridor.

    Width=15, safe x=[0,4], hazard x=[5,7], corridor x=[8,9],
    food x=[10,14]. Spawn at x=1. Two columns of empty corridor between
    the 3-wide hazard band and the 5-wide food zone widen the structural
    gap; hazard band thickness matches tight_gradient (3 columns),
    while the food zone is one column wider. Tests whether more
    breathing room (and a marginally larger food target) raises
    survival x foraging throughput enough to unlock recurring
    eligibility.
    """
    return ChamberLayout(
        safe_x_min=0,
        safe_x_max=4,
        hazard_x_min=5,
        hazard_x_max=7,
        food_x_min=10,
        food_x_max=14,
        height=6,
        spawn_x=1,
    )


def food_ladder_layout() -> ChamberLayout:
    """v0.8 — sparse pre-food before the hazard barrier.

    Width=12, safe x=[0,2], corridor x=3, **pre-food x=4** (1-column
    food band, all rows), corridor x=5, hazard x=[6,8], food x=[9,11].
    Spawn at x=1. The pre-food column gives founders a chance to top
    up their energy before facing the hazard band, separating
    "perceptual reach" (sensor question) from "barrier traversal"
    (layout question). Tests whether an early, low-cost food source
    raises the rate at which agents reach reproductive eligibility.
    """
    return ChamberLayout(
        safe_x_min=0,
        safe_x_max=2,
        hazard_x_min=6,
        hazard_x_max=8,
        food_x_min=9,
        food_x_max=11,
        height=6,
        spawn_x=1,
        pre_food_x_min=4,
        pre_food_x_max=4,
    )


# Public dictionary form. Stable iteration order for report tables and CSV.
ALL_LAYOUTS: dict[str, ChamberLayout] = {
    "default": default_layout(),
    "tight_gradient": tight_gradient_layout(),
    "near_hazard": near_hazard_layout(),
    "widened_gradient": widened_gradient_layout(),
    "food_ladder": food_ladder_layout(),
}


def layout_by_name(name: str) -> ChamberLayout:
    """Lookup helper — raises ``KeyError`` for unknown layout names."""
    if name not in ALL_LAYOUTS:
        msg = f"Unknown layout {name!r}; valid names: {sorted(ALL_LAYOUTS)}"
        raise KeyError(msg)
    return ALL_LAYOUTS[name]
