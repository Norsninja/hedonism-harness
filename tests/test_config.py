"""Tests for Pydantic v2 configuration models (SPEC §26.5)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hedonism_harness.core.config import WorldConfig


def test_world_config_is_frozen() -> None:
    """Configs must be immutable after construction."""
    config = WorldConfig(seed=1, width=8, height=8)
    with pytest.raises(ValidationError):
        config.seed = 2  # type: ignore[misc]


def test_world_config_rejects_unknown_fields() -> None:
    """``extra='forbid'`` catches typos like ``with`` instead of ``width``."""
    with pytest.raises(ValidationError):
        WorldConfig(seed=1, width=8, height=8, with_typo=True)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seed", -1),
        ("seed", 2**32),
        ("width", 1),
        ("height", 1),
        ("food_density", -0.1),
        ("food_density", 1.1),
        ("hazard_density", -0.1),
        ("hazard_density", 1.1),
        ("food_value_default", -1.0),
        ("hazard_damage_default", -1.0),
        ("safe_value_default", -1.0),
    ],
)
def test_world_config_rejects_out_of_range_values(field: str, value: float) -> None:
    """Range constraints are enforced for every numeric field."""
    base = {"seed": 1, "width": 8, "height": 8}
    base[field] = value
    with pytest.raises(ValidationError):
        WorldConfig(**base)


def test_world_config_round_trips_through_json() -> None:
    """Configs serialize to JSON and back without loss (used for runs/{run_id}/config.json)."""
    original = WorldConfig(seed=42, width=32, height=64, food_density=0.1)
    restored = WorldConfig.model_validate_json(original.model_dump_json())
    assert restored == original
