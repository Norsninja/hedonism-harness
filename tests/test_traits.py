"""Tests for ``core/traits.py`` — generation, mutation, range enforcement."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from hedonism_harness.core.traits import (
    INTEGER_TRAITS,
    TRAIT_NAMES,
    TraitConfig,
    TraitRange,
    Traits,
    mutate_traits,
    random_traits,
    validate_traits,
)

# ---------------------------------------------------------------------------
# TraitRange + TraitConfig
# ---------------------------------------------------------------------------


def test_trait_range_clamps_values() -> None:
    r = TraitRange(min=0.0, max=1.0)
    assert r.clamp(-0.5) == 0.0
    assert r.clamp(0.3) == 0.3
    assert r.clamp(1.5) == 1.0


def test_trait_range_rejects_inverted_bounds() -> None:
    with pytest.raises(ValidationError):
        TraitRange(min=1.0, max=0.0)


def test_trait_config_is_frozen() -> None:
    config = TraitConfig()
    with pytest.raises(ValidationError):
        config.mutation_rate = 0.5  # type: ignore[misc]


def test_trait_config_default_ranges_match_spec() -> None:
    """Spot-check a few defaults against SPEC §8.1."""
    config = TraitConfig()
    assert (config.fear_sensitivity.min, config.fear_sensitivity.max) == (0.0, 3.0)
    assert (config.pain_tolerance.min, config.pain_tolerance.max) == (0.0, 1.0)
    assert (config.sensor_radius.min, config.sensor_radius.max) == (1.0, 6.0)


def test_trait_names_cover_all_dataclass_fields() -> None:
    """Sanity: TRAIT_NAMES should match the Traits dataclass exactly."""
    assert len(TRAIT_NAMES) == 13
    assert "sensor_radius" in INTEGER_TRAITS


# ---------------------------------------------------------------------------
# random_traits
# ---------------------------------------------------------------------------


def test_random_traits_respects_all_ranges() -> None:
    config = TraitConfig()
    rng = np.random.default_rng(0)
    for _ in range(50):
        traits = random_traits(config, rng)
        validate_traits(traits, config)
        assert isinstance(traits.sensor_radius, int)


def test_random_traits_is_deterministic_under_seed() -> None:
    config = TraitConfig()
    a = random_traits(config, np.random.default_rng(42))
    b = random_traits(config, np.random.default_rng(42))
    assert a == b


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_random_traits_property_in_range(seed: int) -> None:
    """Property: any seed produces in-range traits."""
    config = TraitConfig()
    traits = random_traits(config, np.random.default_rng(seed))
    validate_traits(traits, config)


# ---------------------------------------------------------------------------
# mutate_traits
# ---------------------------------------------------------------------------


def _make_parent(config: TraitConfig) -> Traits:
    return random_traits(config, np.random.default_rng(123))


def test_mutate_traits_is_deterministic_under_seed() -> None:
    config = TraitConfig()
    parent = _make_parent(config)
    a = mutate_traits(parent, config, np.random.default_rng(7))
    b = mutate_traits(parent, config, np.random.default_rng(7))
    assert a == b


def test_mutate_traits_with_zero_rate_returns_clone() -> None:
    config = TraitConfig(mutation_rate=0.0)
    parent = _make_parent(config)
    child = mutate_traits(parent, config, np.random.default_rng(0))
    assert child == parent


def test_mutate_traits_with_unit_rate_changes_at_least_one_trait() -> None:
    """With mutation_rate=1.0 and non-zero sigma, at least one continuous trait should differ."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=0.5)
    parent = _make_parent(config)
    child = mutate_traits(parent, config, np.random.default_rng(0))
    # sensor_radius may or may not flip; check continuous traits as a group.
    differences = [
        getattr(child, name) != getattr(parent, name)
        for name in TRAIT_NAMES
        if name not in INTEGER_TRAITS
    ]
    assert any(differences)


def test_mutate_traits_keeps_integer_traits_integer() -> None:
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=2.0)
    parent = _make_parent(config)
    for seed in range(10):
        child = mutate_traits(parent, config, np.random.default_rng(seed))
        assert isinstance(child.sensor_radius, int)


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_mutate_traits_property_stays_in_range(seed: int) -> None:
    """Property: regardless of seed, mutated traits stay in configured ranges."""
    config = TraitConfig(mutation_rate=1.0, mutation_sigma=5.0)
    rng = np.random.default_rng(seed)
    parent = random_traits(config, rng)
    child = mutate_traits(parent, config, rng)
    validate_traits(child, config)


# ---------------------------------------------------------------------------
# validate_traits
# ---------------------------------------------------------------------------


def test_validate_traits_raises_when_out_of_range() -> None:
    config = TraitConfig()
    parent = _make_parent(config)
    # Force an out-of-range value via dataclass replace.
    bad = Traits(
        **{
            **{name: getattr(parent, name) for name in TRAIT_NAMES},
            "fear_sensitivity": 999.0,
        }
    )
    with pytest.raises(ValueError, match="fear_sensitivity"):
        validate_traits(bad, config)
