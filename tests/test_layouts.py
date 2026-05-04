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
    layout_by_name,
    near_hazard_layout,
    tight_gradient_layout,
)


def test_all_layouts_keys_match_factory_set() -> None:
    assert set(ALL_LAYOUTS.keys()) == {"default", "tight_gradient", "near_hazard"}


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
