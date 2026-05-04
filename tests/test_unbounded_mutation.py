"""Tests for v0.2 unbounded-mutation flag in TraitConfig.

The default (``unbounded_mutation=False``) preserves v0.1/v0.7..v0.13
behavior — mutation clamps to the per-trait sampling range. The new
``unbounded_mutation=True`` mode allows lineages to drift outside the
founder distribution range, with only physical floors and ceilings
enforced (no negative sensitivity, sensor_radius >= 1, tolerances in
[0, 1], etc.).
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from hedonism_harness.core.traits import (
    TRAIT_NAMES,
    TraitConfig,
    Traits,
    mutate_traits,
    random_traits,
    validate_traits,
    validate_traits_physical,
)


def _parent(seed: int = 0) -> Traits:
    return random_traits(TraitConfig(), np.random.default_rng(seed))


def test_unbounded_mutation_defaults_to_false() -> None:
    config = TraitConfig()
    assert config.unbounded_mutation is False


def test_bounded_mutation_keeps_values_in_sampling_range() -> None:
    """Default behavior: mutated traits stay in TraitConfig ranges."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=5.0)
    parent = _parent()
    for seed in range(20):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        validate_traits(child, config)


def test_unbounded_mutation_can_drift_outside_sampling_range() -> None:
    """unbounded_mutation=True: mutated traits may exceed TraitConfig.max."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=5.0, unbounded_mutation=True)
    # Start a parent at the high end so a few mutations are likely to push
    # past the sampling range.
    parent = _parent()
    parent = dataclasses.replace(
        parent,
        pleasure_sensitivity=2.5,  # at the sampling-range max.
        fear_sensitivity=3.0,
    )
    drifted = False
    for seed in range(50):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        if (
            child.pleasure_sensitivity > config.pleasure_sensitivity.max
            or child.fear_sensitivity > config.fear_sensitivity.max
        ):
            drifted = True
            break
    assert drifted, "expected at least one mutated trait to exceed sampling-range max"


def test_unbounded_mutation_respects_physical_floors() -> None:
    """Floors enforced even under unbounded mutation."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=10.0, unbounded_mutation=True)
    parent = _parent()
    for seed in range(50):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        validate_traits_physical(child)


def test_unbounded_mutation_respects_tolerance_ceilings() -> None:
    """Tolerance fields are bounded by [0, 1] semantically, even under
    unbounded mutation."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=10.0, unbounded_mutation=True)
    parent = _parent()
    for seed in range(20):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        assert 0.0 <= child.pain_tolerance <= 1.0
        assert 0.0 <= child.risk_tolerance <= 1.0
        assert 0.0 <= child.memory_strength <= 1.0
        assert 0.0 <= child.memory_decay_rate <= 1.0


def test_unbounded_mutation_keeps_sensor_radius_at_least_one() -> None:
    """sensor_radius's physical floor is 1; mutation can push it up freely."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=10.0, unbounded_mutation=True)
    parent = _parent()
    parent = dataclasses.replace(parent, sensor_radius=1)
    for seed in range(30):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        assert child.sensor_radius >= 1
        assert isinstance(child.sensor_radius, int)


def test_validate_traits_physical_rejects_negative_sensitivity() -> None:
    """Documents the validation contract: negative sensitivities fail."""
    parent = _parent()
    bad = dataclasses.replace(parent, pleasure_sensitivity=-0.1)
    with pytest.raises(ValueError, match="pleasure_sensitivity"):
        validate_traits_physical(bad)


def test_validate_traits_physical_rejects_tolerance_above_one() -> None:
    parent = _parent()
    bad = dataclasses.replace(parent, pain_tolerance=1.5)
    with pytest.raises(ValueError, match="pain_tolerance"):
        validate_traits_physical(bad)


def test_validate_traits_physical_accepts_drift_above_sampling_range() -> None:
    """Trait above TraitConfig.max but within physical bounds -> ok."""
    parent = _parent()
    drifted = dataclasses.replace(parent, pleasure_sensitivity=10.0)
    validate_traits_physical(drifted)  # must not raise


def test_all_trait_names_have_physical_bounds_defined() -> None:
    """Coverage check: every trait must be in the physical floor/ceiling
    table (otherwise unbounded mutation would crash at the lookup)."""
    from hedonism_harness.core.traits import _PHYSICAL_CEILINGS, _PHYSICAL_FLOORS

    for name in TRAIT_NAMES:
        assert name in _PHYSICAL_FLOORS
        assert name in _PHYSICAL_CEILINGS
