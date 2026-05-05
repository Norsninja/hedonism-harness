"""Pydantic v2 configuration models.

Per SPEC §26.5 and §27, configs are composed (one per subsystem) and frozen to
prevent accidental mutation during a run. Every run writes its resolved config
to ``runs/{run_id}/config.json`` via the ``io/run_writer.py`` layer.

Only ``WorldConfig`` is implemented in this commit — other configs land as
their consuming subsystems are built (TraitConfig with traits.py, HarnessConfig
with valence.py, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    food_respawn_cooldown: int | None = Field(
        default=None,
        ge=1,
        description=(
            "v0.18: per-tile cooldown (in ticks) before a consumed FOOD cell "
            "refills back to FOOD with food_value_default. None disables "
            "respawn — the v0.7..v0.17 default. K must be >= 1; K=0 would "
            "clash with the unscheduled sentinel (respawn_at_tick == 0). "
            "Determinism: cooldown is fully scheduled (no RNG draws); "
            "K=None preserves v0.7..v0.17 bit-identity by construction."
        ),
    )
    energy_pool_initial: float | None = Field(
        default=None,
        ge=0.0,
        description=(
            "v0.19: initial size of the ambient energy pool that funds food "
            "respawn refills and child startup energy under strict mass-"
            "energy conservation. None disables the pool entirely — the "
            "v0.7..v0.18 default; respawn and child startup are unfunded "
            "and the death-residual recycle is not registered. Finite "
            "values enable closed-pool / open-ecology arms; respawn "
            "fails-soft and births are denied atomically when the pool "
            "cannot fund the required draw. See "
            "docs/experiments/fear_hunger_v0.19.md."
        ),
    )
    ambient_influx_rate: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "v0.19: deterministic per-tick energy credited to the ambient "
            "pool at phase 0 of each step (open-ecology arms). 0.0 (the "
            "default) preserves v0.7..v0.18 bit-identity and the closed-"
            "pool semantics. Only consulted when energy_pool_initial is "
            "not None; setting a positive rate without a pool raises "
            "during config construction."
        ),
    )

    @model_validator(mode="after")
    def _check_influx_requires_pool(self) -> WorldConfig:
        if self.ambient_influx_rate > 0.0 and self.energy_pool_initial is None:
            msg = (
                f"ambient_influx_rate ({self.ambient_influx_rate}) > 0 requires "
                "energy_pool_initial to be set; influx with no pool would create "
                "energy from nowhere outside the v0.19 conservation framing."
            )
            raise ValueError(msg)
        return self


class BodyConfig(BaseModel):
    """Per-agent body capacities, costs, and starting state (SPEC §7)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_energy: float = Field(default=100.0, gt=0.0)
    starting_energy: float = Field(default=60.0, ge=0.0)
    max_health: float = Field(default=100.0, gt=0.0)
    starting_health: float = Field(default=100.0, ge=0.0)
    base_metabolic_cost: float = Field(
        default=0.25,
        ge=0.0,
        description="Energy lost per tick before trait modifiers.",
    )
    sensor_radius_metabolic_cost: float = Field(
        default=0.05,
        ge=0.0,
        description=(
            "Additional energy cost per unit of sensor_radius per tick "
            "(SPEC §22 recommendation: high sensor radius costs more)."
        ),
    )

    @model_validator(mode="after")
    def _check_starting_within_max(self) -> BodyConfig:
        if self.starting_energy > self.max_energy:
            msg = f"starting_energy ({self.starting_energy}) > max_energy ({self.max_energy})"
            raise ValueError(msg)
        if self.starting_health > self.max_health:
            msg = f"starting_health ({self.starting_health}) > max_health ({self.max_health})"
            raise ValueError(msg)
        return self


class ActionConfig(BaseModel):
    """Per-action energy costs (SPEC §7)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    move_cost: float = Field(default=1.0, ge=0.0)
    stay_cost: float = Field(default=0.1, ge=0.0)
    eat_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Energy cost of the EAT action (food gain is separate).",
    )


class ReproductionConfig(BaseModel):
    """Validity thresholds + costs for asexual reproduction (SPEC §7, §14)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    energy_threshold: float = Field(
        default=70.0,
        ge=0.0,
        description="Parent must have at least this much energy to reproduce.",
    )
    energy_cost: float = Field(
        default=35.0,
        ge=0.0,
        description="Energy debited from parent on successful reproduction.",
    )
    offspring_start_energy: float = Field(
        default=30.0,
        ge=0.0,
        description="Starting energy of the newborn child.",
    )
    min_age: int = Field(
        default=10,
        ge=0,
        description="Minimum parent age (in ticks) required to reproduce.",
    )
    hazard_threshold: float = Field(
        default=0.5,
        ge=0.0,
        description=(
            "Maximum local hazard signal under which reproduction is allowed. "
            "Hazard signal here is the same axial sum used by sensors."
        ),
    )
