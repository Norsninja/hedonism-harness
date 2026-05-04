"""Geometry tests for ``experiments.layouts``.

The layouts encode pre-registered v0.3 hypotheses about sensor visibility.
If the chamber dimensions change without intent, the experiments lose their
diagnostic value — these tests pin the geometry that the v0.3 report relies
on.
"""

from __future__ import annotations

import pytest

from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.experiments.layouts import (
    ALL_LAYOUTS,
    default_layout,
    food_ladder_layout,
    layout_by_name,
    near_hazard_layout,
    tight_gradient_layout,
    widened_gradient_layout,
)


def test_all_layouts_keys_match_factory_set() -> None:
    assert set(ALL_LAYOUTS.keys()) == {
        "default",
        "tight_gradient",
        "near_hazard",
        "widened_gradient",
        "food_ladder",
    }


def test_default_layout_replicates_v01_chamber() -> None:
    layout = default_layout()
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 5
    assert layout.hazard_x_min == 8
    assert layout.hazard_x_max == 11
    assert layout.food_x_min == 14
    assert layout.food_x_max == 19
    assert layout.height == 6
    assert layout.width == 20
    assert layout.resolved_spawn_x == 1  # safe_x_min + 1, since spawn_x is None


def test_tight_gradient_puts_hazard_and_food_in_sensor_range() -> None:
    """With sensor_radius=4 (SPEC §8.1 midpoint) the east axial ray from the
    spawn must reach at least the first hazard column AND the first food
    column. This is the geometry the v0.3 positive-control hypothesis depends
    on — if it changes, the report's diagnosis is invalid.
    """
    layout = tight_gradient_layout()
    midpoint_radius = 4  # (1 + 6) // 2 + 0 = midpoint of [1, 6] rounded up
    spawn = layout.resolved_spawn_x
    east_visible_max = spawn + midpoint_radius

    # Sanity: the first hazard column is reachable.
    assert layout.hazard_x_min <= east_visible_max, (
        f"hazard_x_min={layout.hazard_x_min} not visible from spawn={spawn} "
        f"with radius={midpoint_radius} (max east visible x={east_visible_max})"
    )
    # And the first food column is reachable.
    assert layout.food_x_min <= east_visible_max, (
        f"food_x_min={layout.food_x_min} not visible from spawn={spawn} "
        f"with radius={midpoint_radius} (max east visible x={east_visible_max})"
    )


def test_near_hazard_keeps_food_out_of_sensor_range() -> None:
    """Pure avoidance test: hazard visible, food not. Maximum sensor radius
    is 6 (SPEC §8.1). Even at that ceiling, food must remain invisible from
    the spawn — otherwise the layout's purpose collapses to ``tight_gradient``.
    """
    layout = near_hazard_layout()
    max_radius = 6
    spawn = layout.resolved_spawn_x
    east_visible_max = spawn + max_radius

    # First hazard column is reachable from spawn.
    midpoint_radius = 4
    assert layout.hazard_x_min <= spawn + midpoint_radius, "hazard must be in midpoint sensor range"
    # Food remains out of range even at sensor_radius_max.
    assert layout.food_x_min > east_visible_max, (
        f"food_x_min={layout.food_x_min} reachable at max radius from spawn={spawn} "
        f"(east_visible_max={east_visible_max}); near_hazard would not be food-blind"
    )


def test_sensor_radius_max_matches_spec() -> None:
    """Sanity-check the assumption used in test_near_hazard_keeps_food_out: we
    pin to SPEC §8.1's max sensor_radius (6). If the spec changes, this test
    flags it so we revisit ``near_hazard_layout``."""
    cfg = TraitConfig()
    assert cfg.sensor_radius.max == 6, (
        "near_hazard_layout depends on sensor_radius.max=6; spec changed."
    )


def test_layout_by_name_lookup_and_unknown_raises() -> None:
    layout = layout_by_name("default")
    assert layout.width == 20
    with pytest.raises(KeyError):
        layout_by_name("does-not-exist")


def test_layouts_are_frozen_dataclasses() -> None:
    """A mutated layout would silently invalidate the diagnostic table."""
    layout = default_layout()
    with pytest.raises((AttributeError, TypeError)):
        layout.spawn_x = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# v0.8 layouts
# ---------------------------------------------------------------------------


def test_widened_gradient_geometry() -> None:
    """v0.8 widened_gradient: width=15, safe[0..4], hazard[5..7], food[10..14]."""
    layout = widened_gradient_layout()
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 4
    assert layout.hazard_x_min == 5
    assert layout.hazard_x_max == 7
    assert layout.food_x_min == 10
    assert layout.food_x_max == 14
    assert layout.height == 6
    assert layout.width == 15
    assert layout.resolved_spawn_x == 1
    assert not layout.has_pre_food
    # Corridor between hazard and food (x=8, x=9) is 2 cells wide.
    assert layout.food_x_min - layout.hazard_x_max - 1 == 2


def test_food_ladder_has_pre_food_band() -> None:
    """v0.8 food_ladder: pre-food at x=4, hazard[6..8], food[9..11]."""
    layout = food_ladder_layout()
    assert layout.safe_x_min == 0
    assert layout.safe_x_max == 2
    assert layout.hazard_x_min == 6
    assert layout.hazard_x_max == 8
    assert layout.food_x_min == 9
    assert layout.food_x_max == 11
    assert layout.height == 6
    assert layout.width == 12
    assert layout.resolved_spawn_x == 1
    assert layout.has_pre_food
    assert layout.pre_food_x_min == 4
    assert layout.pre_food_x_max == 4


# ---------------------------------------------------------------------------
# ChamberLayout.__post_init__ pre-food validation (v0.8 hygiene-2)
# ---------------------------------------------------------------------------


def test_chamber_layout_rejects_half_set_pre_food_min_only() -> None:
    """Setting one of (pre_food_x_min, pre_food_x_max) without the other
    is a typo that would silently disable the band — must raise."""
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    with pytest.raises(ValueError, match="set together"):
        ChamberLayout(pre_food_x_min=4)


def test_chamber_layout_rejects_half_set_pre_food_max_only() -> None:
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    with pytest.raises(ValueError, match="set together"):
        ChamberLayout(pre_food_x_max=4)


def test_chamber_layout_rejects_inverted_pre_food_range() -> None:
    """``pre_food_x_min > pre_food_x_max`` paints zero columns silently."""
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    with pytest.raises(ValueError, match="inverted"):
        ChamberLayout(pre_food_x_min=5, pre_food_x_max=4)


def test_chamber_layout_rejects_pre_food_overlapping_safe_band() -> None:
    """A pre-food column that overlaps the safe band would get stamped
    twice with conflicting CellKind values; last write wins silently."""
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    # default safe is [0..5]; pre_food at x=2 overlaps.
    with pytest.raises(ValueError, match="overlaps safe band"):
        ChamberLayout(pre_food_x_min=2, pre_food_x_max=2)


def test_chamber_layout_rejects_pre_food_overlapping_hazard_band() -> None:
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    # default hazard is [8..11]; pre_food at x=9 overlaps.
    with pytest.raises(ValueError, match="overlaps hazard band"):
        ChamberLayout(pre_food_x_min=9, pre_food_x_max=10)


def test_chamber_layout_rejects_pre_food_overlapping_terminal_food_band() -> None:
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    # default food is [14..19]; pre_food at x=15 overlaps.
    with pytest.raises(ValueError, match="overlaps food band"):
        ChamberLayout(pre_food_x_min=15, pre_food_x_max=15)


def test_chamber_layout_accepts_valid_pre_food() -> None:
    """The food_ladder configuration must continue to construct cleanly:
    pre_food=[4,4] sits between safe=[0..2] and hazard=[6..8]."""
    layout = food_ladder_layout()
    assert layout.has_pre_food
    assert layout.pre_food_x_min == 4
    assert layout.pre_food_x_max == 4


def test_chamber_layout_accepts_no_pre_food() -> None:
    """Default layouts (no pre-food) must continue to construct."""
    from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout

    layout = ChamberLayout()
    assert not layout.has_pre_food


def test_food_ladder_pre_food_is_painted_as_food_band() -> None:
    """End-to-end: paint_chamber must stamp the pre-food column as FOOD
    cells with the standard food_value, in every row."""
    from hedonism_harness.core.config import BodyConfig, ReproductionConfig
    from hedonism_harness.core.world import CellKind
    from hedonism_harness.experiments.fear_hunger_chamber import (
        build_chamber_layout,
        paint_chamber,
    )
    from hedonism_harness.model import FounderSpec, HHModel
    from hedonism_harness.policies.hedonism_policy import HedonismPolicy

    layout = food_ladder_layout()
    world_cfg = build_chamber_layout(layout).model_copy(update={"seed": 42})
    model = HHModel(
        world_cfg,
        founders=[
            FounderSpec(
                x=layout.resolved_spawn_x,
                y=0,
                policy_factory=lambda: HedonismPolicy(exploration_noise=0.0),
            )
        ],
        body_config=BodyConfig(),
        reproduction_config=ReproductionConfig(),
    )
    paint_chamber(model, layout)

    pre_food_x = layout.pre_food_x_min
    assert pre_food_x is not None
    for y in range(layout.height):
        kind = CellKind(int(model.world.kind_layer[pre_food_x, y]))
        assert kind == CellKind.FOOD, f"pre-food column x={pre_food_x} y={y} should be FOOD"
        assert float(model.world.food_value[pre_food_x, y]) == world_cfg.food_value_default

    # Sanity: corridor cells x=3 and x=5 are NOT painted (default empty).
    for empty_x in (3, 5):
        kind = CellKind(int(model.world.kind_layer[empty_x, 0]))
        assert kind != CellKind.FOOD, f"corridor x={empty_x} should not be FOOD"
        assert kind != CellKind.HAZARD, f"corridor x={empty_x} should not be HAZARD"
        assert kind != CellKind.SAFE, f"corridor x={empty_x} should not be SAFE"
