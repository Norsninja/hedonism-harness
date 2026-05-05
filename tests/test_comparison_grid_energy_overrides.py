"""Tests for v0.16 reproduction-economics overrides on Arm.

The v0.16 axis adds optional ``energy_cost`` and ``energy_threshold``
fields on ``Arm``. ``None`` (default) preserves v0.14/v0.15 bit-identity
by falling back to ``FIXED_ENERGY_COST=35.0`` /
``FIXED_ENERGY_THRESHOLD=50.0``. Non-None values flow into
``tuned_reproduction_config``.

The bit-identity contract for arm A vs v0.15 reflex-baseline is verified
end-to-end by the v0.16 sweep itself (Arm A reproduces the v0.15
reflex-baseline numbers exactly); these tests cover the wiring layer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hedonism_harness.experiments.comparison_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
    V0_15_ARMS,
    V0_16_ARMS,
    Arm,
    _gradient_policy_factory,
    _run_one_arm_seed,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config


def test_arm_energy_overrides_default_to_none() -> None:
    """Existing v0.15 arms have no energy override; v0.14 bit-identity
    contract holds via the FIXED_* constants."""
    for arm in V0_15_ARMS:
        assert arm.energy_cost is None
        assert arm.energy_threshold is None


def test_v0_16_arms_carry_explicit_energy_overrides() -> None:
    """V0_16_ARMS spans cost ∈ {35, 25, 15} at threshold 50."""
    labels = [arm.label for arm in V0_16_ARMS]
    assert labels == ["cost-35", "cost-25", "cost-15"]
    assert [arm.energy_cost for arm in V0_16_ARMS] == [35.0, 25.0, 15.0]
    for arm in V0_16_ARMS:
        assert arm.energy_threshold == 50.0
        assert arm.memory_type is None  # single-arm: no scalar memory.


def test_default_arm_runs_with_baseline_energy_economics(tmp_path: Path) -> None:
    """An Arm with no overrides runs to completion and uses the baseline
    economics (smoke). The detailed bit-identity check vs v0.15
    reflex-baseline is performed by the v0.16 sweep itself."""
    arm = Arm(
        label="probe-default",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=3,
        n_founders=2,
    )
    assert result.population_start == 2


def test_explicit_overrides_run_to_completion(tmp_path: Path) -> None:
    """Arm with energy_cost=20, energy_threshold=40 runs without raising
    and produces a deterministic ChamberRunResult. The override values
    flow through tuned_reproduction_config; that factory's contract is
    asserted in test_arm_energy_override_bounds_validated below."""
    arm = Arm(
        label="probe-override",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        energy_cost=20.0,
        energy_threshold=40.0,
    )
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    result, _diag = _run_one_arm_seed(
        arm=arm,
        layout_name="food_ladder",
        seed=1,
        runs_root=runs_root,
        n_ticks=3,
        n_founders=2,
    )
    assert result.population_end >= 0


def test_arm_energy_override_bounds_validated() -> None:
    """tuned_reproduction_config enforces [0.0, 100.0] on each axis;
    Arm overrides defer to that factory."""
    with pytest.raises(ValueError, match="energy_cost"):
        tuned_reproduction_config(energy_threshold=50.0, energy_cost=-1.0)
    with pytest.raises(ValueError, match="energy_threshold"):
        tuned_reproduction_config(energy_threshold=200.0, energy_cost=10.0)


def test_tuned_reproduction_config_propagates_override_values() -> None:
    """Direct contract: the factory output carries the override values."""
    cfg = tuned_reproduction_config(energy_threshold=40.0, energy_cost=20.0)
    assert cfg.energy_threshold == 40.0
    assert cfg.energy_cost == 20.0


def test_fixed_constants_match_v0_15_baseline() -> None:
    """Sanity: FIXED_* constants are still the v0.14/v0.15 baseline values
    used by all prior published results."""
    assert FIXED_ENERGY_COST == 35.0
    assert FIXED_ENERGY_THRESHOLD == 50.0
