"""Tests for ``experiments.trait_configs``.

The v0.5 trait-tuning experiment depends on the permissive config being
strictly inside SPEC §8.1 master ranges and shifted in the documented
direction. These tests pin both contracts so a future range tweak that
silently broadens beyond SPEC trips immediately.
"""

from __future__ import annotations

import numpy as np
import pytest

from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, random_traits, validate_traits
from hedonism_harness.experiments.trait_configs import (
    ALL_TRAIT_CONFIGS,
    default_trait_config,
    permissive_trait_config,
    trait_config_by_name,
)

SPEC_MASTER = TraitConfig()


def test_all_keys_match_factory_set() -> None:
    assert set(ALL_TRAIT_CONFIGS.keys()) == {"default", "permissive"}


def test_default_factory_returns_spec_default() -> None:
    """Identity factory: the default ``TraitConfig`` must match SPEC §8.1."""
    cfg = default_trait_config()
    for name in TRAIT_NAMES:
        assert cfg.range_for(name) == SPEC_MASTER.range_for(name)


def test_permissive_ranges_are_subranges_of_spec_master() -> None:
    """Every permissive trait range must lie inside the SPEC §8.1 master.

    If a future tweak widens beyond SPEC, this test flags the change so we
    can decide whether to update SPEC or revert.
    """
    perm = permissive_trait_config()
    for name in TRAIT_NAMES:
        spec_rng = SPEC_MASTER.range_for(name)
        perm_rng = perm.range_for(name)
        assert perm_rng.min >= spec_rng.min, (
            f"{name}: permissive min {perm_rng.min} below SPEC min {spec_rng.min}"
        )
        assert perm_rng.max <= spec_rng.max, (
            f"{name}: permissive max {perm_rng.max} above SPEC max {spec_rng.max}"
        )


def test_permissive_shifts_are_in_documented_direction() -> None:
    """Pin the v0.5 hypothesis: permissive should lean toward Reckless.

    Each assertion below corresponds to one row of the v0.5 design table.
    """
    perm = permissive_trait_config()
    # Raise hunger floor (every agent feels urgency).
    assert perm.hunger_pain_sensitivity.min > SPEC_MASTER.hunger_pain_sensitivity.min
    # Lower injury ceiling (less catastrophic damage).
    assert perm.injury_pain_sensitivity.max < SPEC_MASTER.injury_pain_sensitivity.max
    # Lower fear ceiling (no agent terrified).
    assert perm.fear_sensitivity.max < SPEC_MASTER.fear_sensitivity.max
    # Raise pleasure floor (food matters to everyone).
    assert perm.pleasure_sensitivity.min > SPEC_MASTER.pleasure_sensitivity.min
    # Raise pain-tolerance floor.
    assert perm.pain_tolerance.min > SPEC_MASTER.pain_tolerance.min
    # Raise risk-tolerance floor.
    assert perm.risk_tolerance.min > SPEC_MASTER.risk_tolerance.min


def test_random_traits_under_permissive_validates_against_spec_master() -> None:
    """Sanity: any sample drawn from permissive must still be a SPEC §8.1
    legal ``Traits`` -- otherwise downstream code that validates against
    the SPEC config would reject permissive samples."""
    perm = permissive_trait_config()
    rng = np.random.default_rng(0)
    for _ in range(64):
        traits = random_traits(perm, rng)
        validate_traits(traits, SPEC_MASTER)


def test_trait_config_by_name_lookup_and_unknown_raises() -> None:
    cfg = trait_config_by_name("permissive")
    assert cfg.fear_sensitivity.max == 1.5
    with pytest.raises(KeyError):
        trait_config_by_name("ultra-reckless")
