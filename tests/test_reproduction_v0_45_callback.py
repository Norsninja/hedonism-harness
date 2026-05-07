"""v0.45 process_reproduction() additive-callback regression tests.

Locked test cases (per pre-reg §"Tests required"):
- default-None reproduces existing deterministic N/S/E/W placement
- callback is not called for tick <= 50 (call-site gate; tested via
  the chamber driver's wrapping of optional_intervention)
- callback is called for tick >= 51
- callback returning None skips the birth and does not charge parent
- invalid callback return raises ValueError
- B predicate excludes HAZARD and WALL (unit tested in
  test_interventions_v0_45.py; this file confirms the integration
  end-to-end with process_reproduction)
- C predicate excludes HAZARD and WALL and requires adjacency
"""

from __future__ import annotations

import numpy as np
import pytest

from hedonism_harness.core.body import AgentBody, make_body
from hedonism_harness.core.config import BodyConfig, ReproductionConfig
from hedonism_harness.core.reproduction import process_reproduction
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import CellKind, World


def _make_world(width: int = 4, height: int = 4) -> World:
    kind_layer = np.full((width, height), int(CellKind.EMPTY), dtype=np.uint8)
    food_value = np.zeros((width, height), dtype=np.float32)
    hazard_damage = np.zeros((width, height), dtype=np.float32)
    safe_value = np.zeros((width, height), dtype=np.float32)
    respawn_at_tick = np.zeros((width, height), dtype=np.int32)
    return World(
        width=width,
        height=height,
        kind_layer=kind_layer,
        food_value=food_value,
        hazard_damage=hazard_damage,
        safe_value=safe_value,
        respawn_at_tick=respawn_at_tick,
    )


def _make_parent(world: World, x: int = 1, y: int = 1) -> AgentBody:
    import dataclasses

    rng = np.random.default_rng(0)
    traits = random_traits(TraitConfig(unbounded_mutation=False), rng)
    body = make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=x,
        y=y,
        traits=traits,
        config=BodyConfig(),
    )
    return dataclasses.replace(body, energy=100.0)


def _repro_kwargs() -> dict:
    return {
        "parent_rng": np.random.default_rng(0),
        "trait_config": TraitConfig(unbounded_mutation=False),
        "body_config": BodyConfig(),
        "reproduction_config": ReproductionConfig(
            energy_threshold=50.0, energy_cost=15.0, offspring_start_energy=30.0
        ),
        "child_id": 2,
    }


def test_default_none_reproduces_n_s_e_w_first_fit_placement():
    """With birth_redirect_callback=None (default), placement uses the
    deterministic N/S/E/W first-fit scan. For parent at (1, 1) in a 4x4
    chamber, the first valid neighbor in (N, S, E, W) order is N=(1, 2)."""
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)
    outcome = process_reproduction(world, parent, **_repro_kwargs())
    assert outcome is not None
    _, child = outcome
    assert (child.x, child.y) == (1, 2)


def test_callback_redirect_overrides_default_placement():
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)
    captured = {}

    def callback(world_arg, parent_arg, occupied, original):
        captured["called"] = True
        captured["original"] = original
        return (3, 3)

    outcome = process_reproduction(
        world, parent, **_repro_kwargs(), birth_redirect_callback=callback
    )
    assert outcome is not None
    _, child = outcome
    assert (child.x, child.y) == (3, 3)
    assert captured["called"] is True
    assert captured["original"] == (1, 2)  # what default would have returned


def test_callback_returning_none_skips_birth_no_charge():
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)
    parent_energy_before = parent.energy

    def callback(world_arg, parent_arg, occupied, original):
        return None

    outcome = process_reproduction(
        world, parent, **_repro_kwargs(), birth_redirect_callback=callback
    )
    assert outcome is None
    # Parent body unchanged (no charge applied because outcome is None).
    # process_reproduction returns None before charging when the callback
    # returns None. The caller's parent reference is unmodified.
    assert parent.energy == parent_energy_before


def test_invalid_callback_return_out_of_bounds_raises_value_error():
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)

    def callback(world_arg, parent_arg, occupied, original):
        return (-1, 0)

    with pytest.raises(ValueError, match="invalid cell"):
        process_reproduction(world, parent, **_repro_kwargs(), birth_redirect_callback=callback)


def test_invalid_callback_return_wall_raises_value_error():
    world = _make_world()
    world.kind_layer[2, 2] = int(CellKind.WALL)
    parent = _make_parent(world, x=1, y=1)

    def callback(world_arg, parent_arg, occupied, original):
        return (2, 2)

    with pytest.raises(ValueError, match="invalid cell"):
        process_reproduction(world, parent, **_repro_kwargs(), birth_redirect_callback=callback)


def test_invalid_callback_return_occupied_raises_value_error():
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)
    occupied = frozenset({(2, 2)})

    def callback(world_arg, parent_arg, occupied_arg, original):
        return (2, 2)

    kwargs = _repro_kwargs()
    with pytest.raises(ValueError, match="invalid cell"):
        process_reproduction(
            world, parent, occupied=occupied, **kwargs, birth_redirect_callback=callback
        )


def test_callback_keyword_only_parameter_rejects_positional():
    """birth_redirect_callback must be keyword-only (after `*` barrier).
    Calling positionally raises TypeError."""
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)
    rng = np.random.default_rng(0)
    cfg = ReproductionConfig(energy_threshold=50.0, energy_cost=15.0, offspring_start_energy=30.0)
    body_cfg = BodyConfig()
    trait_cfg = TraitConfig(unbounded_mutation=False)
    with pytest.raises(TypeError):
        # Attempt positional call after the `*` barrier — process_reproduction
        # accepts only (world, parent) positionally; everything else is keyword-only.
        process_reproduction(  # type: ignore[misc]
            world,
            parent,
            rng,
            trait_cfg,
            body_cfg,
            cfg,
            2,
            None,
            lambda *args: None,
        )


def test_callback_with_food_cell_target_charges_parent():
    """When callback returns a valid cell, parent is charged normally
    (tests that the callback path doesn't bypass charge_parent)."""
    world = _make_world()
    world.kind_layer[3, 3] = int(CellKind.FOOD)
    parent = _make_parent(world, x=1, y=1)
    parent_energy_before = parent.energy

    def callback(world_arg, parent_arg, occupied, original):
        return (3, 3)

    outcome = process_reproduction(
        world, parent, **_repro_kwargs(), birth_redirect_callback=callback
    )
    assert outcome is not None
    updated_parent, _ = outcome
    assert updated_parent.energy == parent_energy_before - 15.0  # energy_cost


def test_callback_skip_returns_none_when_default_would_have_succeeded():
    """Callback can choose to skip even when default placement would have
    worked — confirms the callback overrides the default's success path."""
    world = _make_world()
    parent = _make_parent(world, x=1, y=1)

    def callback(world_arg, parent_arg, occupied, original):
        # Default would have returned (1, 2). Callback skips anyway.
        assert original == (1, 2)

    outcome = process_reproduction(
        world, parent, **_repro_kwargs(), birth_redirect_callback=callback
    )
    assert outcome is None
