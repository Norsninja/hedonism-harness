"""v0.41 sweep driver tests.

Validates the V0_41_TIGHT_H_ARMS arm tuple shape, the SEEDS / N_TICKS /
N_FOUNDERS locked constants, and substrate-byte-identity to the
v0.32 / v0.33 / v0.39 hazard-axis arm tuples.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from hedonism_harness.experiments.comparison_grid import (
    V0_25_ARMS,
    V0_32_TIGHT_H_ARMS,
    V0_33_TIGHT_H_ARMS,
    V0_39_TIGHT_H_ARMS,
    V0_41_TIGHT_H_ARMS,
)


def _load_sweep_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0.41_sweep.py"
    spec = importlib.util.spec_from_file_location("v0_41_sweep", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_41_sweep"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_v0_41_tight_h_arms_has_four_hazards():
    assert len(V0_41_TIGHT_H_ARMS) == 4
    hazards = sorted(arm.hazard_damage for arm in V0_41_TIGHT_H_ARMS)
    assert hazards == [0.0, 4.0, 8.0, 12.0]


def test_v0_41_tight_h_arms_all_influx_1_0():
    for arm in V0_41_TIGHT_H_ARMS:
        assert arm.label.endswith("-influx-1.0")
        assert arm.ambient_influx_rate == 1.0


def test_v0_41_tight_h_arms_element_wise_identical_to_v0_32():
    """Substrate-byte-identity to V0_32_TIGHT_H_ARMS by construction."""
    assert V0_41_TIGHT_H_ARMS == V0_32_TIGHT_H_ARMS


def test_v0_41_tight_h_arms_element_wise_identical_to_v0_33():
    assert V0_41_TIGHT_H_ARMS == V0_33_TIGHT_H_ARMS


def test_v0_41_tight_h_arms_element_wise_identical_to_v0_39():
    assert V0_41_TIGHT_H_ARMS == V0_39_TIGHT_H_ARMS


def test_v0_41_tight_h_arms_literal_slice_of_v0_25():
    """Literal slice of V0_25_ARMS at influx=1.0 across hazards {0,4,8,12}."""
    expected = tuple(arm for arm in V0_25_ARMS if arm.label.endswith("-influx-1.0"))
    assert expected == V0_41_TIGHT_H_ARMS


def test_v0_41_tight_h_arms_arm_object_identity_with_v0_25():
    """v0.41 arms are the SAME Arm objects as in V0_25_ARMS (no copies)."""
    expected = tuple(arm for arm in V0_25_ARMS if arm.label.endswith("-influx-1.0"))
    for v041_arm, v025_arm in zip(V0_41_TIGHT_H_ARMS, expected, strict=True):
        assert v041_arm is v025_arm


def test_sweep_locked_constants():
    mod = _load_sweep_module()
    assert mod.CHAMBER == "tight_gradient"
    assert tuple(range(33, 41)) == mod.SEEDS
    assert mod.N_TICKS == 200
    assert mod.N_FOUNDERS == 5
    assert mod.BATCH_ID == "fear-hunger-v0.41-tight_gradient"


def test_sweep_seeds_disjoint_from_prior_streams():
    """Fresh seeds 33..40 must not overlap with prior streams."""
    mod = _load_sweep_module()
    fresh = set(mod.SEEDS)
    v0_25_seeds = set(range(1, 9))
    v0_32_seeds = set(range(9, 17))
    v0_33_seeds = set(range(17, 25))
    v0_39_seeds = set(range(25, 33))
    assert fresh.isdisjoint(v0_25_seeds)
    assert fresh.isdisjoint(v0_32_seeds)
    assert fresh.isdisjoint(v0_33_seeds)
    assert fresh.isdisjoint(v0_39_seeds)


def test_sweep_seed_count():
    mod = _load_sweep_module()
    assert len(mod.SEEDS) == 8
