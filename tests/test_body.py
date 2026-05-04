"""Tests for ``core/body.py`` — AgentBody dataclass + lifecycle helpers."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from hedonism_harness.core.body import (
    AgentBody,
    DeathCause,
    apply_damage,
    apply_energy_delta,
    apply_metabolism,
    infer_death_cause,
    is_dead,
    make_body,
    mark_dead,
)
from hedonism_harness.core.config import BodyConfig
from hedonism_harness.core.traits import TraitConfig, random_traits


def _fresh_body(seed: int = 0, **overrides: object) -> AgentBody:
    config = BodyConfig()
    traits = random_traits(TraitConfig(), np.random.default_rng(seed))
    body = make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=0,
        y=0,
        traits=traits,
        config=config,
    )
    if overrides:
        body = dataclasses.replace(body, **overrides)
    return body


# ---------------------------------------------------------------------------
# BodyConfig
# ---------------------------------------------------------------------------


def test_body_config_is_frozen() -> None:
    config = BodyConfig()
    with pytest.raises(ValidationError):
        config.max_energy = 10.0  # type: ignore[misc]


def test_body_config_rejects_starting_above_max() -> None:
    with pytest.raises(ValidationError):
        BodyConfig(starting_energy=200.0, max_energy=100.0)
    with pytest.raises(ValidationError):
        BodyConfig(starting_health=200.0, max_health=100.0)


# ---------------------------------------------------------------------------
# make_body
# ---------------------------------------------------------------------------


def test_make_body_starts_at_configured_vitals() -> None:
    config = BodyConfig()
    body = _fresh_body()
    assert body.energy == config.starting_energy
    assert body.health == config.starting_health
    assert body.age == 0
    assert body.alive is True
    assert body.death_cause is None


def test_agent_body_is_frozen() -> None:
    body = _fresh_body()
    with pytest.raises(dataclasses.FrozenInstanceError):
        body.energy = 0.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# apply_metabolism
# ---------------------------------------------------------------------------


def test_apply_metabolism_decreases_energy_and_increments_age() -> None:
    config = BodyConfig()
    body = _fresh_body()
    after = apply_metabolism(body, config)
    assert after.energy < body.energy
    assert after.age == body.age + 1


def test_apply_metabolism_floors_energy_at_zero() -> None:
    config = BodyConfig(base_metabolic_cost=1000.0)
    body = _fresh_body(energy=0.5)
    after = apply_metabolism(body, config)
    assert after.energy == 0.0


def test_apply_metabolism_scales_with_metabolic_rate_trait() -> None:
    """Higher metabolic_rate should burn more energy per tick."""
    config = BodyConfig(base_metabolic_cost=1.0, sensor_radius_metabolic_cost=0.0)
    rng = np.random.default_rng(0)
    fast_traits = dataclasses.replace(
        random_traits(TraitConfig(), rng), metabolic_rate=2.0, sensor_radius=1
    )
    slow_traits = dataclasses.replace(fast_traits, metabolic_rate=0.5)
    fast = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=0, y=0, traits=fast_traits, config=config
    )
    slow = make_body(
        body_id=2, lineage_id=2, parent_id=None, x=0, y=0, traits=slow_traits, config=config
    )
    fast_after = apply_metabolism(fast, config)
    slow_after = apply_metabolism(slow, config)
    assert (fast.energy - fast_after.energy) > (slow.energy - slow_after.energy)


def test_apply_metabolism_scales_with_sensor_radius() -> None:
    config = BodyConfig(base_metabolic_cost=0.0, sensor_radius_metabolic_cost=1.0)
    rng = np.random.default_rng(0)
    big_eyes = dataclasses.replace(
        random_traits(TraitConfig(), rng), sensor_radius=6, metabolic_rate=1.0
    )
    small_eyes = dataclasses.replace(big_eyes, sensor_radius=1)
    big = make_body(
        body_id=1, lineage_id=1, parent_id=None, x=0, y=0, traits=big_eyes, config=config
    )
    small = make_body(
        body_id=2, lineage_id=2, parent_id=None, x=0, y=0, traits=small_eyes, config=config
    )
    big_after = apply_metabolism(big, config)
    small_after = apply_metabolism(small, config)
    assert (big.energy - big_after.energy) == pytest.approx(6 * (small.energy - small_after.energy))


# ---------------------------------------------------------------------------
# apply_damage / apply_energy_delta
# ---------------------------------------------------------------------------


def test_apply_damage_reduces_health() -> None:
    body = _fresh_body(health=80.0)
    after = apply_damage(body, 25.0)
    assert after.health == 55.0


def test_apply_damage_floors_health_at_zero() -> None:
    body = _fresh_body(health=10.0)
    after = apply_damage(body, 50.0)
    assert after.health == 0.0


def test_apply_damage_rejects_negative_amount() -> None:
    body = _fresh_body()
    with pytest.raises(ValueError, match="non-negative"):
        apply_damage(body, -1.0)


def test_apply_energy_delta_clamps_to_max() -> None:
    config = BodyConfig(max_energy=100.0, starting_energy=80.0)
    body = _fresh_body()
    body = make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=0,
        y=0,
        traits=body.traits,
        config=config,
    )
    after = apply_energy_delta(body, 50.0, config)
    assert after.energy == config.max_energy


def test_apply_energy_delta_floors_at_zero() -> None:
    config = BodyConfig()
    body = _fresh_body(energy=5.0)
    after = apply_energy_delta(body, -100.0, config)
    assert after.energy == 0.0


# ---------------------------------------------------------------------------
# is_dead / infer_death_cause / mark_dead
# ---------------------------------------------------------------------------


def test_is_dead_true_when_energy_zero() -> None:
    body = _fresh_body(energy=0.0)
    assert is_dead(body)


def test_is_dead_true_when_health_zero() -> None:
    body = _fresh_body(health=0.0)
    assert is_dead(body)


def test_is_dead_false_when_both_positive() -> None:
    body = _fresh_body()
    assert not is_dead(body)


def test_infer_death_cause_returns_none_for_alive_body() -> None:
    assert infer_death_cause(_fresh_body()) is None


def test_infer_death_cause_starvation_when_only_energy_zero() -> None:
    body = _fresh_body(energy=0.0)
    assert infer_death_cause(body) == DeathCause.STARVATION


def test_infer_death_cause_injury_when_health_zero() -> None:
    body = _fresh_body(health=0.0)
    assert infer_death_cause(body) == DeathCause.INJURY


def test_infer_death_cause_injury_wins_when_both_zero() -> None:
    body = _fresh_body(energy=0.0, health=0.0)
    assert infer_death_cause(body) == DeathCause.INJURY


def test_mark_dead_flips_flags() -> None:
    body = _fresh_body()
    dead = mark_dead(body, DeathCause.STARVATION)
    assert dead.alive is False
    assert dead.death_cause == DeathCause.STARVATION


# ---------------------------------------------------------------------------
# Property tests
# ---------------------------------------------------------------------------


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_apply_metabolism_never_increases_energy(seed: int) -> None:
    config = BodyConfig()
    body = _fresh_body(seed=seed)
    after = apply_metabolism(body, config)
    assert after.energy <= body.energy


@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    delta=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
)
def test_apply_energy_delta_stays_in_bounds(seed: int, delta: float) -> None:
    config = BodyConfig()
    body = _fresh_body(seed=seed)
    body = make_body(
        body_id=1,
        lineage_id=1,
        parent_id=None,
        x=0,
        y=0,
        traits=body.traits,
        config=config,
    )
    after = apply_energy_delta(body, delta, config)
    assert 0.0 <= after.energy <= config.max_energy
