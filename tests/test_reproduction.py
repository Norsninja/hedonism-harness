"""Tests for ``core/reproduction.py`` — validity, child construction, processing."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from pydantic import ValidationError

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.body import make_body
from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.reproduction import (
    can_reproduce,
    charge_parent,
    find_adjacent_empty_cell,
    make_child,
    process_reproduction,
)
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, World, build_world


def _empty_world(width: int = 6, height: int = 6) -> World:
    return build_world(
        WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)
    )


def _parent(
    x: int,
    y: int,
    body_config: BodyConfig,
    *,
    energy: float = 80.0,
    age: int = 50,
    body_id: int = 1,
    lineage_id: int = 1,
):
    traits = random_traits(TraitConfig(), np.random.default_rng(0))
    body = make_body(
        body_id=body_id,
        lineage_id=lineage_id,
        parent_id=None,
        x=x,
        y=y,
        traits=traits,
        config=body_config,
    )
    return dataclasses.replace(body, energy=energy, age=age)


# ---------------------------------------------------------------------------
# ReproductionConfig
# ---------------------------------------------------------------------------


def test_reproduction_config_is_frozen() -> None:
    config = ReproductionConfig()
    with pytest.raises(ValidationError):
        config.energy_cost = 99.0  # type: ignore[misc]


def test_reproduction_config_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        ReproductionConfig(energy_cost=-1.0)
    with pytest.raises(ValidationError):
        ReproductionConfig(min_age=-1)


# ---------------------------------------------------------------------------
# find_adjacent_empty_cell
# ---------------------------------------------------------------------------


def test_find_adjacent_empty_cell_returns_north_first() -> None:
    """Order is deterministic (N, S, E, W) — N wins when all four are open."""
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig())
    placement = find_adjacent_empty_cell(world, parent, occupied=None)
    assert placement == (2, 3)


def test_find_adjacent_empty_cell_skips_walls() -> None:
    world = _empty_world()
    world.kind_layer[2, 3] = CellKind.WALL  # block N
    parent = _parent(2, 2, BodyConfig())
    placement = find_adjacent_empty_cell(world, parent, occupied=None)
    assert placement == (2, 1)  # falls through to S


def test_find_adjacent_empty_cell_skips_occupied() -> None:
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig())
    occupied = frozenset({(2, 3), (2, 1)})  # block N and S
    placement = find_adjacent_empty_cell(world, parent, occupied=occupied)
    assert placement == (3, 2)  # falls through to E


def test_find_adjacent_empty_cell_returns_none_when_surrounded() -> None:
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig())
    occupied = frozenset({(2, 3), (2, 1), (3, 2), (1, 2)})  # block all four
    placement = find_adjacent_empty_cell(world, parent, occupied=occupied)
    assert placement is None


def test_find_adjacent_empty_cell_respects_world_edge() -> None:
    world = _empty_world(width=4, height=4)
    parent = _parent(0, 0, BodyConfig())  # SW corner
    placement = find_adjacent_empty_cell(world, parent, occupied=None)
    assert placement == (0, 1)  # only N and E are in-bounds; N first


# ---------------------------------------------------------------------------
# can_reproduce
# ---------------------------------------------------------------------------


def test_can_reproduce_true_under_default_conditions() -> None:
    world = _empty_world()
    config = ReproductionConfig()
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=50)
    assert can_reproduce(world, parent, config) is True


def test_can_reproduce_false_when_energy_below_threshold() -> None:
    world = _empty_world()
    config = ReproductionConfig(energy_threshold=70.0)
    parent = _parent(2, 2, BodyConfig(), energy=50.0, age=50)
    assert can_reproduce(world, parent, config) is False


def test_can_reproduce_false_when_age_too_low() -> None:
    world = _empty_world()
    config = ReproductionConfig(min_age=10)
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=5)
    assert can_reproduce(world, parent, config) is False


def test_can_reproduce_false_when_local_hazard_too_high() -> None:
    world = _empty_world()
    world.kind_layer[2, 3] = CellKind.HAZARD
    world.hazard_damage[2, 3] = 5.0
    config = ReproductionConfig(hazard_threshold=0.5)
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=50)
    assert can_reproduce(world, parent, config) is False


def test_can_reproduce_false_when_no_adjacent_empty_cell() -> None:
    world = _empty_world()
    config = ReproductionConfig()
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=50)
    occupied = frozenset({(2, 3), (2, 1), (3, 2), (1, 2)})
    assert can_reproduce(world, parent, config, occupied) is False


# ---------------------------------------------------------------------------
# make_child
# ---------------------------------------------------------------------------


def test_make_child_inherits_lineage_and_records_parent() -> None:
    body_config = BodyConfig()
    parent = _parent(2, 2, body_config, body_id=42, lineage_id=7)
    child = make_child(
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=ReproductionConfig(),
        child_id=99,
        x=2,
        y=3,
    )
    assert child.id == 99
    assert child.parent_id == 42
    assert child.lineage_id == 7
    assert (child.x, child.y) == (2, 3)


def test_make_child_starts_at_offspring_start_energy() -> None:
    body_config = BodyConfig()
    repro = ReproductionConfig(offspring_start_energy=25.0)
    parent = _parent(2, 2, body_config)
    child = make_child(
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=repro,
        child_id=2,
        x=2,
        y=3,
    )
    assert child.energy == 25.0
    assert child.health == body_config.starting_health
    assert child.age == 0


def test_make_child_traits_are_mutated_form_of_parent() -> None:
    body_config = BodyConfig()
    parent = _parent(2, 2, body_config)
    # mutation_rate=1.0 forces every trait to attempt mutation.
    trait_config = TraitConfig(mutation_rate=1.0, mutation_sigma=0.5)
    child = make_child(
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=trait_config,
        body_config=body_config,
        reproduction_config=ReproductionConfig(),
        child_id=2,
        x=2,
        y=3,
    )
    # At least one continuous trait should differ.
    assert child.traits != parent.traits


def test_make_child_is_deterministic_under_seed() -> None:
    body_config = BodyConfig()
    parent = _parent(2, 2, body_config)
    a = make_child(
        parent,
        parent_rng=np.random.default_rng(7),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=ReproductionConfig(),
        child_id=2,
        x=2,
        y=3,
    )
    b = make_child(
        parent,
        parent_rng=np.random.default_rng(7),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=ReproductionConfig(),
        child_id=2,
        x=2,
        y=3,
    )
    assert a == b


# ---------------------------------------------------------------------------
# charge_parent
# ---------------------------------------------------------------------------


def test_charge_parent_debits_energy() -> None:
    parent = _parent(2, 2, BodyConfig(), energy=80.0)
    after = charge_parent(parent, ReproductionConfig(energy_cost=35.0))
    assert after.energy == pytest.approx(45.0)


def test_charge_parent_floors_at_zero() -> None:
    parent = _parent(2, 2, BodyConfig(), energy=10.0)
    after = charge_parent(parent, ReproductionConfig(energy_cost=50.0))
    assert after.energy == 0.0


# ---------------------------------------------------------------------------
# process_reproduction
# ---------------------------------------------------------------------------


def test_process_reproduction_returns_parent_and_child() -> None:
    body_config = BodyConfig()
    repro = ReproductionConfig(energy_cost=35.0, offspring_start_energy=30.0)
    world = _empty_world()
    parent = _parent(2, 2, body_config, energy=80.0, age=50)
    result = process_reproduction(
        world,
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=repro,
        child_id=99,
        occupied=None,
    )
    assert result is not None
    new_parent, child = result
    assert new_parent.id == parent.id
    assert new_parent.energy == pytest.approx(45.0)
    assert child.parent_id == parent.id
    assert child.energy == 30.0


def test_process_reproduction_returns_none_when_no_space() -> None:
    body_config = BodyConfig()
    world = _empty_world()
    parent = _parent(2, 2, body_config, energy=80.0, age=50)
    occupied = frozenset({(2, 3), (2, 1), (3, 2), (1, 2)})
    result = process_reproduction(
        world,
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=ReproductionConfig(),
        child_id=99,
        occupied=occupied,
    )
    assert result is None


def test_process_reproduction_does_not_charge_parent_on_failure() -> None:
    body_config = BodyConfig()
    world = _empty_world()
    parent = _parent(2, 2, body_config, energy=80.0, age=50)
    occupied = frozenset({(2, 3), (2, 1), (3, 2), (1, 2)})
    # Process_reproduction returns None — parent's energy is not modified
    # (the original parent dataclass is unchanged because everything is frozen).
    process_reproduction(
        world,
        parent,
        parent_rng=np.random.default_rng(0),
        trait_config=TraitConfig(),
        body_config=body_config,
        reproduction_config=ReproductionConfig(energy_cost=35.0),
        child_id=99,
        occupied=occupied,
    )
    assert parent.energy == 80.0


# ---------------------------------------------------------------------------
# Integration with get_valid_actions
# ---------------------------------------------------------------------------


def test_get_valid_actions_includes_reproduce_when_config_provided_and_eligible() -> None:
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=50)
    valid = get_valid_actions(world, parent, reproduction_config=ReproductionConfig())
    assert Action.REPRODUCE in valid


def test_get_valid_actions_excludes_reproduce_when_ineligible() -> None:
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig(), energy=10.0, age=2)  # too young + too tired
    valid = get_valid_actions(world, parent, reproduction_config=ReproductionConfig())
    assert Action.REPRODUCE not in valid


def test_get_valid_actions_excludes_reproduce_when_config_not_provided() -> None:
    """Backward compatibility: no config -> never include REPRODUCE."""
    world = _empty_world()
    parent = _parent(2, 2, BodyConfig(), energy=80.0, age=50)
    valid = get_valid_actions(world, parent)
    assert Action.REPRODUCE not in valid
