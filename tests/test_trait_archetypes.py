"""Tests for ``experiments.trait_archetypes``.

The archetypes are positive-control fixtures, so the contracts we care about
are: (1) every archetype produces a valid ``Traits`` (within SPEC §8.1
ranges), (2) the load-bearing axes are pinned to the documented extremes, and
(3) ``archetype_traits(name)`` is a stable lookup.
"""

from __future__ import annotations

import pytest

from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, validate_traits
from hedonism_harness.experiments.trait_archetypes import (
    ARCHETYPE_NAMES,
    archetype_traits,
    balanced,
    explorer,
    fearful,
    reckless,
)


def test_all_archetypes_validate_against_default_config() -> None:
    cfg = TraitConfig()
    for name in ARCHETYPE_NAMES:
        traits = archetype_traits(name, cfg)
        validate_traits(traits, cfg)  # raises if any field is out of range


def test_fearful_pins_fear_axes_to_extremes() -> None:
    cfg = TraitConfig()
    t = fearful(cfg)
    assert t.fear_sensitivity == cfg.fear_sensitivity.max
    assert t.hunger_pain_sensitivity == cfg.hunger_pain_sensitivity.min
    assert t.injury_pain_sensitivity == cfg.injury_pain_sensitivity.max
    assert t.pain_tolerance == cfg.pain_tolerance.min
    assert t.risk_tolerance == cfg.risk_tolerance.min


def test_reckless_pins_hunger_axes_to_extremes() -> None:
    cfg = TraitConfig()
    t = reckless(cfg)
    assert t.fear_sensitivity == cfg.fear_sensitivity.min
    assert t.hunger_pain_sensitivity == cfg.hunger_pain_sensitivity.max
    assert t.injury_pain_sensitivity == cfg.injury_pain_sensitivity.min
    assert t.pain_tolerance == cfg.pain_tolerance.max
    assert t.risk_tolerance == cfg.risk_tolerance.max


def test_balanced_uses_midpoints_for_every_trait() -> None:
    cfg = TraitConfig()
    t = balanced(cfg)
    for name in TRAIT_NAMES:
        rng = cfg.range_for(name)
        midpoint = (rng.min + rng.max) / 2.0
        actual = getattr(t, name)
        if name == "sensor_radius":
            # Integer trait — rounded midpoint.
            assert actual == round(midpoint)
        else:
            assert actual == midpoint, f"{name}: expected midpoint {midpoint}, got {actual}"


def test_explorer_pins_novelty_axes() -> None:
    cfg = TraitConfig()
    t = explorer(cfg)
    assert t.novelty_drive == cfg.novelty_drive.max
    assert t.uncertainty_aversion == cfg.uncertainty_aversion.min
    # Hunger / fear axes should NOT be pinned — they stay at midpoints.
    expected_hunger = (cfg.hunger_pain_sensitivity.min + cfg.hunger_pain_sensitivity.max) / 2.0
    expected_fear = (cfg.fear_sensitivity.min + cfg.fear_sensitivity.max) / 2.0
    assert t.hunger_pain_sensitivity == expected_hunger
    assert t.fear_sensitivity == expected_fear


def test_archetype_traits_are_deterministic_across_calls() -> None:
    """Same archetype name must yield the same Traits — no hidden RNG."""
    a = archetype_traits("reckless")
    b = archetype_traits("reckless")
    assert a == b


def test_archetype_traits_unknown_name_raises() -> None:
    with pytest.raises(KeyError):
        archetype_traits("super-saiyan")


def test_archetype_names_tuple_is_complete() -> None:
    """ARCHETYPE_NAMES must include every archetype reachable via lookup."""
    for name in ARCHETYPE_NAMES:
        archetype_traits(name)  # must not raise
    assert set(ARCHETYPE_NAMES) == {"fearful", "reckless", "balanced", "explorer"}
