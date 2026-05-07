"""v0.43R sweep driver tests.

Validates V0_43R_INTERVENTION_ARMS shape, locked constants, intervention_kind
plumbing, substrate-byte-identity to V0_25 anchors, and disjoint-seeds
discipline relative to all prior streams (v0.25 / v0.32 / v0.33 / v0.39 /
v0.41 / v0.42 / v0.43-halted).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from hedonism_harness.core.interventions import (
    KIND_DENSITY_PRESERVING_PERTURBATION,
    KIND_NULL,
    KIND_REDUCE_DENSITY_50PCT,
)
from hedonism_harness.experiments.comparison_grid import (
    V0_25_ARMS,
    V0_43R_INTERVENTION_ARMS,
)


def _load_sweep_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "v0.43r_sweep.py"
    spec = importlib.util.spec_from_file_location("v0_43r_sweep", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["v0_43r_sweep"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_v0_43r_arms_count_and_kinds():
    """6 arms total: 2 hazards x 3 intervention kinds."""
    assert len(V0_43R_INTERVENTION_ARMS) == 6
    kinds = {a.intervention_kind for a in V0_43R_INTERVENTION_ARMS}
    assert kinds == {KIND_NULL, KIND_REDUCE_DENSITY_50PCT, KIND_DENSITY_PRESERVING_PERTURBATION}


def test_v0_43r_arms_two_hazards_only():
    hazards = sorted({a.hazard_damage for a in V0_43R_INTERVENTION_ARMS})
    assert hazards == [0.0, 8.0]


def test_v0_43r_arms_each_kind_has_both_hazards():
    by_kind: dict[str, set[float]] = {}
    for a in V0_43R_INTERVENTION_ARMS:
        by_kind.setdefault(a.intervention_kind, set()).add(a.hazard_damage)
    for kind, hazards in by_kind.items():
        assert hazards == {0.0, 8.0}, kind


def test_v0_43r_arms_labels_unique():
    labels = [a.label for a in V0_43R_INTERVENTION_ARMS]
    assert len(set(labels)) == len(labels)


def test_v0_43r_arms_labels_have_v043r_prefix():
    for a in V0_43R_INTERVENTION_ARMS:
        assert a.label.startswith("v043R-")


def test_v0_43r_arms_substrate_matches_v0_25_anchors():
    """Substrate fields must match the V0_25 hzd0/hzd8 influx=1.0 anchors.
    Only ``label`` and ``intervention_kind`` differ.
    """
    v25_by_hzd = {
        a.hazard_damage: a
        for a in V0_25_ARMS
        if a.label.endswith("-influx-1.0") and a.hazard_damage in (0.0, 8.0)
    }
    for arm in V0_43R_INTERVENTION_ARMS:
        anchor = v25_by_hzd[arm.hazard_damage]
        assert arm.policy_factory == anchor.policy_factory
        assert arm.auto_reproduction == anchor.auto_reproduction
        assert arm.memory_type == anchor.memory_type
        assert arm.energy_cost == anchor.energy_cost
        assert arm.energy_threshold == anchor.energy_threshold
        assert arm.offspring_start_energy == anchor.offspring_start_energy
        assert arm.food_respawn_cooldown == anchor.food_respawn_cooldown
        assert arm.energy_pool_initial == anchor.energy_pool_initial
        assert arm.ambient_influx_rate == anchor.ambient_influx_rate
        assert arm.child_funding_mode == anchor.child_funding_mode
        assert arm.hazard_damage == anchor.hazard_damage
        assert arm.hazard_avoidance_weight == anchor.hazard_avoidance_weight


def test_v0_43r_arms_intervention_kind_set_explicitly():
    for arm in V0_43R_INTERVENTION_ARMS:
        assert arm.intervention_kind is not None


def test_sweep_locked_constants():
    mod = _load_sweep_module()
    assert mod.CHAMBER == "tight_gradient"
    assert tuple(range(49, 57)) == mod.SEEDS
    assert mod.N_TICKS == 200
    assert mod.N_FOUNDERS == 5
    assert mod.BATCH_ID == "fear-hunger-v0.43R-tight_gradient"


def test_sweep_seeds_disjoint_from_prior_streams():
    """Seeds 49..56 must not overlap any prior stream (v0.25 1..8, v0.32
    9..16, v0.33 17..24, v0.39 25..32, v0.41 33..40, v0.42 41..48).
    """
    mod = _load_sweep_module()
    fresh = set(mod.SEEDS)
    for prior in (
        range(1, 9),
        range(9, 17),
        range(17, 25),
        range(25, 33),
        range(33, 41),
        range(41, 49),
    ):
        assert fresh.isdisjoint(set(prior))


def test_sweep_seed_count():
    mod = _load_sweep_module()
    assert len(mod.SEEDS) == 8


def test_sweep_arms_constant_matches_module_export():
    mod = _load_sweep_module()
    assert mod.V0_43R_INTERVENTION_ARMS is V0_43R_INTERVENTION_ARMS
