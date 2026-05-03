"""Pydantic v2 configuration models.

Per SPEC §26.5 and §27, configs are composed (one per subsystem) and frozen to
prevent accidental mutation during a run. Every run writes its resolved config
to ``runs/{run_id}/config.json`` via the ``io/run_writer.py`` layer.

Only ``WorldConfig`` is implemented in this commit — other configs land as
their consuming subsystems are built (TraitConfig with traits.py, HarnessConfig
with valence.py, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

UINT32_MAX = 2**32 - 1


class WorldConfig(BaseModel):
    """Configuration for procedural world generation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    seed: int = Field(ge=0, le=UINT32_MAX, description="Master RNG seed.")
    width: int = Field(ge=2, le=4096, description="Grid width in cells.")
    height: int = Field(ge=2, le=4096, description="Grid height in cells.")

    food_density: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Fraction of cells initialized as FOOD.",
    )
    hazard_density: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Fraction of cells initialized as HAZARD.",
    )
    food_value_default: float = Field(
        default=20.0,
        ge=0.0,
        description="Energy delivered when a FOOD cell is consumed.",
    )
    hazard_damage_default: float = Field(
        default=15.0,
        ge=0.0,
        description="HP lost per tick of HAZARD cell occupancy.",
    )
    safe_value_default: float = Field(
        default=1.0,
        ge=0.0,
        description="Fear-reduction strength of a SAFE cell.",
    )
