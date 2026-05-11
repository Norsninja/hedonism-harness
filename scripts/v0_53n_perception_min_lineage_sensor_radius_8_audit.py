"""v0.53n per-lineage perception heterogeneity probe — 5-arm
alignment-control / negative-control reducer with in-slice predecessor
anchors on C (v0.53l) and E (v0.53k).

Pre-reg: [[docs/experiments/fear_hunger_v0.53n.md]]. Question: Does
assigning r=8 perception access to the lowest-sensor founder lineage
rescue reachability without rescuing the original max-sensor Label A
bridge, under FOOD_NEAR1 x combined-budget x n_ticks=400?

v0.53n disentangles COVERAGE from ALIGNMENT: it holds coverage fixed at
1/5 (matching v0.53l) while inverting alignment — the override is
assigned to the **min-sensor** lineage (``argmin(sensor_radius)``,
``min(lineage_id)`` tiebreak) per run. The v0.48
``is_high_sensor_radius_lineage`` selector still picks the MAX-sensor
lineage for Label A indexing — that lineage receives NO override on D.
This is the alignment-control mechanism.

Corpus (locked, identical shape to v0.53m): A_null arm only across
v0.42 / v0.43R / v0.44 / v0.45, hazards {0, 8}, seeds 41..72. 64 runs
per arm; 5 arms; 320 runs total.

Arms (locked, 5):
  A_null_V0_25:                                  tight_gradient   + body_config=None  + n_ticks=200
  B_widened_V0_25:                               widened_gradient + body_config=None  + n_ticks=200
  C_widened_food_near1_combined_max_lineage_sr8_N400:
      FOOD_NEAR1_LAYOUT +
      body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10) +
      per_founder_traits_overrides[top1_lid] = Traits(..., effective_sensor_radius_override=8)
      n_ticks=400  (IN-SLICE PREDECESSOR ANCHOR vs v0.53l C)
  D_widened_food_near1_combined_min_lineage_sr8_N400:
      FOOD_NEAR1_LAYOUT +
      body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10) +
      per_founder_traits_overrides[bottom1_lid] = Traits(..., effective_sensor_radius_override=8)
      n_ticks=400  (PRIMARY VERDICT-GATING — alignment-control intervention)
  E_widened_food_near1_combined_modelwide_sr8_N400:
      FOOD_NEAR1_LAYOUT +
      body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10,
                             effective_sensor_radius_override=8) +
      per_founder_traits_overrides=None +
      n_ticks=400  (IN-SLICE PREDECESSOR ANCHOR vs v0.53k C)

Anchor stack (locked, priority 2 — eight sub-conditions a-h):
  (a) Tier-1 A_null_V0_25 tick-50 paired_d drift > 1e-3.
  (b) A_null_V0_25 tick-50 sub-verdict != PRESENT.
  (c) C tick-400 reachability != 61/64 exact.
  (d) C tick-400 sub-verdict != C_..._MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT.
  (e) C tick-400 six paired_d cells drift > 1e-3 vs v0.53l published.
  (f) E tick-400 reachability != 64/64 exact.
  (g) E tick-400 sub-verdict suffix != _TICK400_BRIDGE_PARTIAL.
  (h) E tick-400 six paired_d cells drift > 1e-3 vs v0.53k published.

Slice rollup (locked, 7 outcomes, priority-ordered — PRIORITY 3 IS
REACHABILITY-GATED + LABEL-B-SPECIFIC on D tick-400; the central design
correction is the asymmetric halt rule):
  1. CORPUS_REDERIVE_DRIFT_HALT
  2. ANCHOR_REPLICATION_HALT  (eight sub-conditions a-h)
  3. MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT
  4. MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A
  5. MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE
  6. MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED
  7. MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD

Conservation framing: zero ``src/`` modifications. v0.53l-tip seams cover
all three intervention arms (C max-only / D min-only / E model-wide).
The new bottom-K helper ``_select_bottom_k_sensor_radius_lineages`` and
pre-sampling helper ``build_bottom_k_per_founder_overrides`` mirror
v0.53m's top-K helpers (which are reused for the C arm via cross-script
import). ``tests/sha_pins.py`` carries forward unchanged.

Usage:
    uv run python scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py
    uv run python scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py \\
        --out-dir runs/v0.53n-perception-min-lineage-sensor-radius-8
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import statistics
import sys
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np

from hedonism_harness.core.config import BodyConfig
from hedonism_harness.core.events import (
    AgentBorn,
    AteFood,
    HazardDamageApplied,
    signal_for,
)
from hedonism_harness.core.interventions import KIND_NULL, InterventionConfig
from hedonism_harness.core.rng import make_streams
from hedonism_harness.core.traits import TraitConfig, Traits, random_traits
from hedonism_harness.experiments.comparison_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
    V0_42_INTERVENTION_ARMS,
    V0_43R_INTERVENTION_ARMS,
    V0_44_INTERVENTION_ARMS,
    V0_45_INTERVENTION_ARMS,
    Arm,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.fear_hunger_chamber import ChamberLayout, run_chamber
from hedonism_harness.experiments.layouts import (
    tight_gradient_layout,
    widened_gradient_layout,
)
from hedonism_harness.model import HHModel

# ---------------------------------------------------------------------------
# Cross-script imports: reuse v0.53k's ``_select_sensor_radius_label`` AND
# v0.53m's ``_select_top_k_sensor_radius_lineages`` + ``build_top_k_per_founder_overrides``
# (the C arm path is byte-identical to v0.53m's C arm). v0.53n introduces
# the new sibling ``_select_bottom_k_sensor_radius_lineages`` AND
# ``build_bottom_k_per_founder_overrides`` for the D arm (argmin instead of
# argmax). Per CLAUDE.md "Cross-script imports" — established importlib.util
# pattern. Predecessor names (v0.53m, v0.53k) in cross-script imports are
# PRESERVED VERBATIM — do not rename to v0.53n.
# ---------------------------------------------------------------------------
_V053K_PATH = Path(__file__).parent / "v0_53k_perception_sensor_radius_8_audit.py"
_v053k_spec = importlib.util.spec_from_file_location("v0_53k_audit", _V053K_PATH)
assert _v053k_spec is not None
assert _v053k_spec.loader is not None
v0_53k_audit = importlib.util.module_from_spec(_v053k_spec)
sys.modules.setdefault("v0_53k_audit", v0_53k_audit)
_v053k_spec.loader.exec_module(v0_53k_audit)

_V053M_PATH = Path(__file__).parent / "v0_53m_perception_top2_lineage_sensor_radius_8_audit.py"
_v053m_spec = importlib.util.spec_from_file_location("v0_53m_audit", _V053M_PATH)
assert _v053m_spec is not None
assert _v053m_spec.loader is not None
v0_53m_audit = importlib.util.module_from_spec(_v053m_spec)
sys.modules.setdefault("v0_53m_audit", v0_53m_audit)
_v053m_spec.loader.exec_module(v0_53m_audit)

# ---------------------------------------------------------------------------
# Locked configuration (pre-reg)
# ---------------------------------------------------------------------------

SEEDS_BY_VERSION: dict[str, tuple[int, ...]] = {
    "v0.42": tuple(range(41, 49)),
    "v0.43R": tuple(range(49, 57)),
    "v0.44": tuple(range(57, 65)),
    "v0.45": tuple(range(65, 73)),
}

HAZARDS: tuple[int, ...] = (0, 8)
N_TICKS_AB: int = 200
N_TICKS_CDE: int = 400
N_FOUNDERS: int = 5
TICK_50: int = 50
TICK_100: int = 100
TICK_200: int = 200
TICK_400: int = 400

WINDOWS_AB: tuple[int, ...] = (TICK_50, TICK_100, TICK_200)
WINDOWS_CDE: tuple[int, ...] = (TICK_50, TICK_100, TICK_200, TICK_400)
WINDOWS_ALL: tuple[int, ...] = (TICK_50, TICK_100, TICK_200, TICK_400)

ARM_A_NULL_V025: str = "A_null_V0_25"
ARM_B_WIDENED_V025: str = "B_widened_V0_25"
ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: str = (
    "C_widened_food_near1_combined_max_lineage_sr8_N400"
)
ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: str = (
    "D_widened_food_near1_combined_min_lineage_sr8_N400"
)
ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: str = (
    "E_widened_food_near1_combined_modelwide_sr8_N400"
)
ARMS: tuple[str, ...] = (
    ARM_A_NULL_V025,
    ARM_B_WIDENED_V025,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
)

FOOD_NEAR1_LAYOUT: ChamberLayout = ChamberLayout(
    safe_x_min=0,
    safe_x_max=4,
    hazard_x_min=5,
    hazard_x_max=7,
    food_x_min=9,
    food_x_max=13,
    height=6,
    spawn_x=1,
)

LAYOUT_NAME_BY_ARM: dict[str, str] = {
    ARM_A_NULL_V025: "tight_gradient",
    ARM_B_WIDENED_V025: "widened_gradient",
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: "widened_food_near1",
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: "widened_food_near1",
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: "widened_food_near1",
}

_select_sensor_radius_label = v0_53k_audit._select_sensor_radius_label
_select_top_k_sensor_radius_lineages = v0_53m_audit._select_top_k_sensor_radius_lineages
build_top_k_per_founder_overrides = v0_53m_audit.build_top_k_per_founder_overrides

N_TICKS_BY_ARM: dict[str, int] = {
    ARM_A_NULL_V025: N_TICKS_AB,
    ARM_B_WIDENED_V025: N_TICKS_AB,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: N_TICKS_CDE,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: N_TICKS_CDE,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: N_TICKS_CDE,
}

WINDOWS_BY_ARM: dict[str, tuple[int, ...]] = {
    ARM_A_NULL_V025: WINDOWS_AB,
    ARM_B_WIDENED_V025: WINDOWS_AB,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: WINDOWS_CDE,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: WINDOWS_CDE,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: WINDOWS_CDE,
}

V0_25_ENERGY_POOL_INITIAL: float = 1500.0
V0_25_FOOD_RESPAWN_COOLDOWN: int = 50
V0_25_AMBIENT_INFLUX_RATE: float = 1.0
V0_25_BODY_STARTING_ENERGY: float = 60.0
V0_25_BODY_BASE_METABOLIC_COST: float = 0.25
STARTING_ENERGY_100_DOSE: float = 100.0
BASE_METABOLIC_COST_010_DOSE: float = 0.10
EFFECTIVE_SENSOR_RADIUS_OVERRIDE_8_DOSE: int = 8

BODY_STARTING_ENERGY_BY_ARM: dict[str, float] = {
    ARM_A_NULL_V025: V0_25_BODY_STARTING_ENERGY,
    ARM_B_WIDENED_V025: V0_25_BODY_STARTING_ENERGY,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: STARTING_ENERGY_100_DOSE,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: STARTING_ENERGY_100_DOSE,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: STARTING_ENERGY_100_DOSE,
}

BODY_BASE_METABOLIC_COST_BY_ARM: dict[str, float] = {
    ARM_A_NULL_V025: V0_25_BODY_BASE_METABOLIC_COST,
    ARM_B_WIDENED_V025: V0_25_BODY_BASE_METABOLIC_COST,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: BASE_METABOLIC_COST_010_DOSE,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: BASE_METABOLIC_COST_010_DOSE,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: BASE_METABOLIC_COST_010_DOSE,
}

BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM: dict[str, int | None] = {
    ARM_A_NULL_V025: None,
    ARM_B_WIDENED_V025: None,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: None,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: None,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: EFFECTIVE_SENSOR_RADIUS_OVERRIDE_8_DOSE,
}

# Per-arm override scheme: C uses top-K (k=1), D uses bottom-K (k=1), E
# uses model-wide body_config. The value indicates k for C/D (None for
# A/B/E).
ARM_OVERRIDE_K: dict[str, int | None] = {
    ARM_A_NULL_V025: None,
    ARM_B_WIDENED_V025: None,
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: 1,
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: 1,
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: None,
}


def _layout_for_arm(arm: str) -> ChamberLayout:
    if arm == ARM_A_NULL_V025:
        return tight_gradient_layout()
    if arm == ARM_B_WIDENED_V025:
        return widened_gradient_layout()
    if arm in (
        ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
        ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
        ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
    ):
        return FOOD_NEAR1_LAYOUT
    msg = f"v0.53n: unknown arm {arm!r}"
    raise V053nReducerError(msg)


def _body_config_for_arm(arm: str) -> BodyConfig | None:
    if arm in (ARM_A_NULL_V025, ARM_B_WIDENED_V025):
        return None
    if arm in (
        ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
        ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
    ):
        return BodyConfig(
            starting_energy=STARTING_ENERGY_100_DOSE,
            base_metabolic_cost=BASE_METABOLIC_COST_010_DOSE,
        )
    if arm == ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400:
        return BodyConfig(
            starting_energy=STARTING_ENERGY_100_DOSE,
            base_metabolic_cost=BASE_METABOLIC_COST_010_DOSE,
            effective_sensor_radius_override=EFFECTIVE_SENSOR_RADIUS_OVERRIDE_8_DOSE,
        )
    msg = f"v0.53n: unknown arm {arm!r}"
    raise V053nReducerError(msg)


def _select_bottom_k_sensor_radius_lineages(
    sensor_radius_by_lineage: dict[int, int],
    k: int,
) -> list[int]:
    """Return the bottom-K lineage_ids by sensor_radius (ascending),
    tiebreak ``min(lineage_id)``.

    Sibling of ``_select_top_k_sensor_radius_lineages``: sort ascending
    by sensor_radius (instead of descending), then ascending by
    lineage_id on ties (``min(lineage_id)`` wins, same direction as the
    top-K tiebreak).

    Tiebreak example (k=1): ``{0: 3, 1: 3, 2: 5, 3: 6, 4: 4}`` returns
    ``[0]`` — both 0 and 1 have sensor_radius=3, but ``min(lineage_id)``
    picks 0.

    Asymmetry-vs-top example: ``{0: 7, 1: 3, 2: 5, 3: 6, 4: 4}`` —
    bottom-K with k=1 returns ``[1]``; top-K with k=1 returns ``[0]``.
    """
    if not sensor_radius_by_lineage:
        return []
    if k <= 0:
        return []
    sorted_lids = sorted(
        sensor_radius_by_lineage.keys(),
        key=lambda lid: (float(sensor_radius_by_lineage[lid]), lid),
    )
    return sorted_lids[: min(k, len(sorted_lids))]


def build_bottom_k_per_founder_overrides(
    *,
    seed: int,
    trait_config: TraitConfig,
    n_founders: int = 5,
    k: int,
) -> tuple[list[Traits | None], list[int]]:
    """Pre-sample ``n_founders`` Traits using the same RNG state the
    chamber will use, identify the bottom-K sensor_radius lineages, and
    build the per-founder override list.

    Mirrors ``build_top_k_per_founder_overrides`` shape. Returns
    ``(overrides, bottom_lineage_ids)``. ``overrides`` is a length-
    ``n_founders`` list where exactly the elements at each index in
    ``bottom_lineage_ids[:k]`` are ``Traits`` instances carrying
    ``effective_sensor_radius_override = 8``; all other entries are
    ``None``.
    """
    streams = make_streams(seed)
    sampled = [random_traits(trait_config, streams.mutation) for _ in range(n_founders)]
    sensor_radius_by_lineage = {lid: int(sampled[lid].sensor_radius) for lid in range(n_founders)}
    bottom_lineage_ids = _select_bottom_k_sensor_radius_lineages(sensor_radius_by_lineage, k)
    overrides: list[Traits | None] = [None] * n_founders
    for lid in bottom_lineage_ids:
        overrides[lid] = replace(
            sampled[lid],
            effective_sensor_radius_override=EFFECTIVE_SENSOR_RADIUS_OVERRIDE_8_DOSE,
        )
    return overrides, bottom_lineage_ids


PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5
B_REACHABILITY_THRESHOLD: float = 0.25

C_INSLICE_REACHABILITY_LOCKED: float = 61.0 / 64.0
E_INSLICE_REACHABILITY_LOCKED: float = 64.0 / 64.0
INSLICE_PAIRED_D_TOLERANCE: float = 1e-3
E_INSLICE_SUBVERDICT_SUFFIX: str = "_TICK400_BRIDGE_PARTIAL"

EXPECTED_FOUNDERS: int = 5

PRIMARY_OBSERVABLES_TICK50: tuple[tuple[str, int], ...] = (
    ("pre50_food_events_count", +1),
    ("pre50_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell_tick50", -1),
)
PRIMARY_OBSERVABLES_TICK100: tuple[tuple[str, int], ...] = (
    ("pre100_food_events_count", +1),
    ("pre100_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell_tick100", -1),
)
PRIMARY_OBSERVABLES_TICK200: tuple[tuple[str, int], ...] = (
    ("pre200_food_events_count", +1),
    ("pre200_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell_tick200", -1),
)
PRIMARY_OBSERVABLES_TICK400: tuple[tuple[str, int], ...] = (
    ("pre400_food_events_count", +1),
    ("pre400_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell_tick400", -1),
)

LABEL_A_FIELD = "is_high_sensor_radius_lineage"
LABEL_B_TICK50_FIELD = "is_high_tick50_readiness_fraction_lineage"
LABEL_B_TICK100_FIELD = "is_high_tick100_readiness_fraction_lineage"
LABEL_B_TICK200_FIELD = "is_high_tick200_readiness_fraction_lineage"
LABEL_B_TICK400_FIELD = "is_high_tick400_readiness_fraction_lineage"
LABEL_A_NAME = "label_a_sensor_radius"
LABEL_B_TICK50_NAME = "label_b_readiness_fraction_tick50"
LABEL_B_TICK100_NAME = "label_b_readiness_fraction_tick100"
LABEL_B_TICK200_NAME = "label_b_readiness_fraction_tick200"
LABEL_B_TICK400_NAME = "label_b_readiness_fraction_tick400"

V048_PUBLISHED_SIGNED_D: dict[tuple[str, str], float] = {
    (LABEL_A_NAME, "pre50_food_events_count"): +1.066,
    (LABEL_A_NAME, "pre50_food_energy_acquired"): +1.066,
    (LABEL_A_NAME, "mean_distance_to_nearest_food_cell_tick50"): +1.916,
    (LABEL_B_TICK50_NAME, "pre50_food_events_count"): +0.916,
    (LABEL_B_TICK50_NAME, "pre50_food_energy_acquired"): +0.916,
    (LABEL_B_TICK50_NAME, "mean_distance_to_nearest_food_cell_tick50"): +1.179,
}

V053L_C_TIER3_ANCHOR_PUBLISHED: dict[tuple[str, str], float] = {
    (LABEL_A_NAME, "pre400_food_events_count"): +4.407500095034808,
    (LABEL_A_NAME, "pre400_food_energy_acquired"): +4.407500095034808,
    (LABEL_A_NAME, "mean_distance_to_nearest_food_cell_tick400"): +3.8177086030179344,
    (LABEL_B_TICK400_NAME, "pre400_food_events_count"): +44.79447381457056,
    (LABEL_B_TICK400_NAME, "pre400_food_energy_acquired"): +44.79447381457056,
    (LABEL_B_TICK400_NAME, "mean_distance_to_nearest_food_cell_tick400"): +7.203121884647769,
}

V053K_C_TIER3_ANCHOR_PUBLISHED: dict[tuple[str, str], float] = {
    (LABEL_A_NAME, "pre400_food_events_count"): -0.019198889380801876,
    (LABEL_A_NAME, "pre400_food_energy_acquired"): -0.019198889380801876,
    (LABEL_A_NAME, "mean_distance_to_nearest_food_cell_tick400"): -0.002295569212554338,
    (LABEL_B_TICK400_NAME, "pre400_food_events_count"): +0.6978345195653476,
    (LABEL_B_TICK400_NAME, "pre400_food_energy_acquired"): +0.6978345195653476,
    (LABEL_B_TICK400_NAME, "mean_distance_to_nearest_food_cell_tick400"): +0.5878534807527567,
}

SUBVERDICT_A_NULL_V025_TICK50_PRESENT = "A_NULL_V025_TICK50_BRIDGE_PRESENT"
SUBVERDICT_A_NULL_V025_TICK50_PARTIAL = "A_NULL_V025_TICK50_BRIDGE_PARTIAL"
SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND = "A_NULL_V025_TICK50_BRIDGE_NOT_FOUND"
SUBVERDICT_A_NULL_V025_TICK50_OPPOSITE = "A_NULL_V025_TICK50_OPPOSITE_SIGN_HALT"

SUBVERDICT_A_NULL_V025_TICK100_PRESENT = "A_NULL_V025_TICK100_BRIDGE_PRESENT"
SUBVERDICT_A_NULL_V025_TICK100_PARTIAL = "A_NULL_V025_TICK100_BRIDGE_PARTIAL"
SUBVERDICT_A_NULL_V025_TICK100_NOT_FOUND = "A_NULL_V025_TICK100_BRIDGE_NOT_FOUND"
SUBVERDICT_A_NULL_V025_TICK100_OPPOSITE = "A_NULL_V025_TICK100_OPPOSITE_SIGN_HALT"

SUBVERDICT_A_NULL_V025_TICK200_PRESENT = "A_NULL_V025_TICK200_BRIDGE_PRESENT"
SUBVERDICT_A_NULL_V025_TICK200_PARTIAL = "A_NULL_V025_TICK200_BRIDGE_PARTIAL"
SUBVERDICT_A_NULL_V025_TICK200_NOT_FOUND = "A_NULL_V025_TICK200_BRIDGE_NOT_FOUND"
SUBVERDICT_A_NULL_V025_TICK200_OPPOSITE = "A_NULL_V025_TICK200_OPPOSITE_SIGN_HALT"

SUBVERDICT_B_WIDENED_V025_TICK50_PRESENT = "B_WIDENED_V025_TICK50_BRIDGE_PRESENT"
SUBVERDICT_B_WIDENED_V025_TICK50_PARTIAL = "B_WIDENED_V025_TICK50_BRIDGE_PARTIAL"
SUBVERDICT_B_WIDENED_V025_TICK50_NOT_FOUND = "B_WIDENED_V025_TICK50_BRIDGE_NOT_FOUND"
SUBVERDICT_B_WIDENED_V025_TICK50_OPPOSITE = "B_WIDENED_V025_TICK50_OPPOSITE_SIGN_HALT"

SUBVERDICT_B_WIDENED_V025_TICK100_PRESENT = "B_WIDENED_V025_TICK100_BRIDGE_PRESENT"
SUBVERDICT_B_WIDENED_V025_TICK100_PARTIAL = "B_WIDENED_V025_TICK100_BRIDGE_PARTIAL"
SUBVERDICT_B_WIDENED_V025_TICK100_NOT_FOUND = "B_WIDENED_V025_TICK100_BRIDGE_NOT_FOUND"
SUBVERDICT_B_WIDENED_V025_TICK100_OPPOSITE = "B_WIDENED_V025_TICK100_OPPOSITE_SIGN_HALT"

SUBVERDICT_B_WIDENED_V025_TICK200_PRESENT = "B_WIDENED_V025_TICK200_BRIDGE_PRESENT"
SUBVERDICT_B_WIDENED_V025_TICK200_PARTIAL = "B_WIDENED_V025_TICK200_BRIDGE_PARTIAL"
SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND = "B_WIDENED_V025_TICK200_BRIDGE_NOT_FOUND"
SUBVERDICT_B_WIDENED_V025_TICK200_OPPOSITE = "B_WIDENED_V025_TICK200_OPPOSITE_SIGN_HALT"

SUBVERDICT_C_FOOD_NEAR1_TICK50_PRESENT = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK50_BRIDGE_PRESENT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK50_PARTIAL = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK50_BRIDGE_PARTIAL"
)
SUBVERDICT_C_FOOD_NEAR1_TICK50_NOT_FOUND = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK50_BRIDGE_NOT_FOUND"
)
SUBVERDICT_C_FOOD_NEAR1_TICK50_OPPOSITE = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK50_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK100_PRESENT = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK100_BRIDGE_PRESENT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK100_PARTIAL = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK100_BRIDGE_PARTIAL"
)
SUBVERDICT_C_FOOD_NEAR1_TICK100_NOT_FOUND = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK100_BRIDGE_NOT_FOUND"
)
SUBVERDICT_C_FOOD_NEAR1_TICK100_OPPOSITE = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK100_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK200_PRESENT = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK200_BRIDGE_PRESENT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK200_PARTIAL = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK200_BRIDGE_PARTIAL"
)
SUBVERDICT_C_FOOD_NEAR1_TICK200_NOT_FOUND = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK200_BRIDGE_NOT_FOUND"
)
SUBVERDICT_C_FOOD_NEAR1_TICK200_OPPOSITE = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK200_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PRESENT"
)
SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_PARTIAL"
)
SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_BRIDGE_NOT_FOUND"
)
SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE = (
    "C_WIDENED_FOOD_NEAR1_MAX_LINEAGE_SR8_TICK400_OPPOSITE_SIGN_HALT"
)

# D arm sub-verdicts (NEW v0.53n — min-only).
SUBVERDICT_D_FOOD_NEAR1_TICK50_PRESENT = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK50_BRIDGE_PRESENT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK50_PARTIAL = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK50_BRIDGE_PARTIAL"
)
SUBVERDICT_D_FOOD_NEAR1_TICK50_NOT_FOUND = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK50_BRIDGE_NOT_FOUND"
)
SUBVERDICT_D_FOOD_NEAR1_TICK50_OPPOSITE = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK50_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK100_PRESENT = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK100_BRIDGE_PRESENT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK100_PARTIAL = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK100_BRIDGE_PARTIAL"
)
SUBVERDICT_D_FOOD_NEAR1_TICK100_NOT_FOUND = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK100_BRIDGE_NOT_FOUND"
)
SUBVERDICT_D_FOOD_NEAR1_TICK100_OPPOSITE = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK100_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK200_PRESENT = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK200_BRIDGE_PRESENT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK200_PARTIAL = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK200_BRIDGE_PARTIAL"
)
SUBVERDICT_D_FOOD_NEAR1_TICK200_NOT_FOUND = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK200_BRIDGE_NOT_FOUND"
)
SUBVERDICT_D_FOOD_NEAR1_TICK200_OPPOSITE = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK200_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK400_PRESENT = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK400_BRIDGE_PRESENT"
)
SUBVERDICT_D_FOOD_NEAR1_TICK400_PARTIAL = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK400_BRIDGE_PARTIAL"
)
SUBVERDICT_D_FOOD_NEAR1_TICK400_NOT_FOUND = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK400_BRIDGE_NOT_FOUND"
)
SUBVERDICT_D_FOOD_NEAR1_TICK400_OPPOSITE = (
    "D_WIDENED_FOOD_NEAR1_MIN_LINEAGE_SR8_TICK400_OPPOSITE_SIGN_HALT"
)

SUBVERDICT_E_FOOD_NEAR1_TICK50_PRESENT = "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK50_BRIDGE_PRESENT"
SUBVERDICT_E_FOOD_NEAR1_TICK50_PARTIAL = "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK50_BRIDGE_PARTIAL"
SUBVERDICT_E_FOOD_NEAR1_TICK50_NOT_FOUND = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK50_BRIDGE_NOT_FOUND"
)
SUBVERDICT_E_FOOD_NEAR1_TICK50_OPPOSITE = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK50_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK100_PRESENT = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK100_BRIDGE_PRESENT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK100_PARTIAL = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK100_BRIDGE_PARTIAL"
)
SUBVERDICT_E_FOOD_NEAR1_TICK100_NOT_FOUND = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK100_BRIDGE_NOT_FOUND"
)
SUBVERDICT_E_FOOD_NEAR1_TICK100_OPPOSITE = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK100_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK200_PRESENT = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK200_BRIDGE_PRESENT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK200_PARTIAL = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK200_BRIDGE_PARTIAL"
)
SUBVERDICT_E_FOOD_NEAR1_TICK200_NOT_FOUND = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK200_BRIDGE_NOT_FOUND"
)
SUBVERDICT_E_FOOD_NEAR1_TICK200_OPPOSITE = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK200_OPPOSITE_SIGN_HALT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK400_PRESENT = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_BRIDGE_PRESENT"
)
SUBVERDICT_E_FOOD_NEAR1_TICK400_PARTIAL = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_BRIDGE_PARTIAL"
)
SUBVERDICT_E_FOOD_NEAR1_TICK400_NOT_FOUND = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_BRIDGE_NOT_FOUND"
)
SUBVERDICT_E_FOOD_NEAR1_TICK400_OPPOSITE = (
    "E_WIDENED_FOOD_NEAR1_MODELWIDE_SR8_TICK400_OPPOSITE_SIGN_HALT"
)

# Slice rollup verdicts (locked, 7 outcomes, priority-ordered).
ROLLUP_CORPUS_DRIFT_HALT = "CORPUS_REDERIVE_DRIFT_HALT"
ROLLUP_ANCHOR_REPLICATION_HALT = "ANCHOR_REPLICATION_HALT"
ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT = "MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT"
ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A = (
    "MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A"
)
ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE = "MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE"
ROLLUP_MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED = "MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED"
ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD = (
    "MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD"
)

# Locked phrases (verbatim per pre-reg, v0.53n). Predecessor stack
# ELEVEN long: v0.53c..v0.53m. These predecessor refs are preserved
# VERBATIM; only the slice's own self-reference (v0.53n) is new.
LOCKED_PHRASES: dict[str, str] = {
    ROLLUP_CORPUS_DRIFT_HALT: (
        "Halt: A_null_V0_25 re-anchor drifted from the published Results value for "
        "{version}; v0.53n's deterministic re-execution of the V0_25 corpus does not "
        "reproduce the published metric within 1e-3."
    ),
    ROLLUP_ANCHOR_REPLICATION_HALT: (
        "Halt: v0.53n's A_null_V0_25 arm does not reproduce v0.48–v0.53m's "  # noqa: RUF001
        "tick-50 spatial bridge, OR v0.53n's B_widened_V0_25 arm does not "
        "reproduce v0.53c–v0.53m's `0/64` reachability lock at tick-200, OR "  # noqa: RUF001
        "v0.53n's C_widened_food_near1_combined_max_lineage_sr8_N400 arm does "
        "not reproduce v0.53l's tick-400 anchor (categorical reachability "
        "`61/64` AND sub-verdict `BRIDGE_PRESENT` AND six published paired_d "
        "cells within 1e-3), OR v0.53n's "
        "E_widened_food_near1_combined_modelwide_sr8_N400 arm does not "
        "reproduce v0.53k's tick-400 anchor (categorical reachability `64/64` "
        "AND categorical resolution `PARTIAL` AND six published paired_d cells "
        "within 1e-3). v0.53n cannot interpret the "
        "D_widened_food_near1_combined_min_lineage_sr8_N400 cells without "
        "reproducing both the V0_25 baseline anchors AND both "
        "heterogeneity-alignment anchors that bracket the min-only "
        "measurement on the same FOOD_NEAR1 × combined-budget × n_ticks=400 "  # noqa: RUF001
        "mechanism axis. Anchor wrong-sign on C or E is captured here; D "
        "Label A wrong-sign is NOT a halt under v0.53n's alignment-control "
        "framing."
    ),
    ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT: (
        "Halt: a v0.53n D_widened_food_near1_combined_min_lineage_sr8_N400 "
        "tick-400 **Label B** spatial / foraging primary fires in the WRONG "
        "direction, AND D reachability at tick-400 clears the locked 25% "
        "threshold. Under v0.53n's alignment-control framing, Label B is "
        "expected to track outcome / readiness on the boosted lineage (the "
        "min-sensor founder receiving the perception override); a Label B "
        "reversal indicates the min-sensor boost actively reduced food "
        "acquisition on the boosted lineage relative to the non-label pool "
        "— a result that demands investigation before priority-4/5/6 "
        "interpretation. D Label A wrong-sign or deadband is NOT a halt; "
        "under the alignment-control framing it is substantive decoupling "
        "evidence (routed to priority 4). The reachability-gated trigger "
        "preserves v0.53e's locked sign discipline while excluding the "
        "v0.53e-style measurement-edge case (wrong-sign at reachability=0)."
    ),
    ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A: (
        "On the modern A_null corpus with the V0_25 substrate held constant "
        "except for the combined founder-facing budget relaxation "
        "`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND "
        "the simulation horizon doubled to `n_ticks=400` AND the "
        "`widened_food_near1` layout AND the **min-sensor-lineage** "
        "per-lineage perception intervention "
        "`per_founder_traits_overrides[bottom_lineage_ids[0]] = "
        "Traits(effective_sensor_radius_override=8)` (the override applies "
        "ONLY to the single min-`sensor_radius` founder per run, with "
        "`argmin(sensor_radius)` selection and `min(lineage_id)` tiebreak; "
        "the v0.48 `is_high_sensor_radius_lineage` selector still picks the "
        "MAX-sensor lineage for Label A indexing — that lineage receives "
        "NO override; metabolic cost UNAFFECTED per the override's "
        "information-channel-only contract; override propagates to all "
        "descendants via `dataclasses.replace`'s preservation), D "
        "reachability at tick-400 clears the locked 25% threshold and D "
        "Label B fires PRESENT under the locked +0.5 paired_d threshold, "
        "while D Label A does NOT fire PRESENT (NOT_FOUND, PARTIAL <2/3, "
        "deadband, wrong-sign, or NaN-nonfiring). "
        "C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces "
        "v0.53l's `61/64` anchor at tick-400 (max-only / trait-aligned "
        "lock holds), E_widened_food_near1_combined_modelwide_sr8_N400 "
        "reproduces v0.53k's `64/64` anchor at tick-400 (model-wide / "
        "homogenized lock holds). The geometry/substrate cell that v0.53c "
        "locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, "
        "v0.53d locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, "
        "v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, "
        "v0.53g locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, "
        "v0.53h locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, "
        "v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j "
        "locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, "
        "v0.53k locked as "
        "`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`, v0.53l "
        "locked as `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`, "
        "and v0.53m locked as "
        "`WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` admits "
        "an alignment-decoupled outcome at the min-sensor-lineage "
        "adversarial control point: D reachability clears the 25% "
        "threshold, D Label B fires PRESENT, and D Label A does NOT fire "
        "PRESENT. **The result is consistent with the v0.53l/m Label A "
        "rescue depending on alignment between the boosted perception "
        "channel and the max-sensor lineage label, while reachability "
        "itself can be rescued by perception access assigned to a non-max "
        "lineage.** This is strong evidence but NOT exclusive causality "
        "and NOT a claim that the v0.48 bridge is purely access-mediated "
        "— the min-sensor boost may also produce Label A decoupling "
        "through secondary channels (asymmetric early survival of the "
        "boosted lineage, reproduction-rate differential, pleiotropy with "
        "other heritable traits, structural-concentration effects on "
        "Label B that obscure the trait signal). This does NOT prove "
        "`the v0.48 bridge is purely access-mediated`; NOT `the v0.53l/m "
        "Label A rescue was purely access-mediated` (max-only's "
        "trait-aligned access is consistent with both readings; v0.53n's "
        "adversarial control localizes the alignment requirement to the "
        "boosted-lineage channel): "
        "`MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A`."
    ),
    ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE: (
        "On the modern A_null corpus with the V0_25 substrate held constant "
        "except for the combined founder-facing budget relaxation AND the "
        "simulation horizon doubled to `n_ticks=400` AND the "
        "`widened_food_near1` layout AND the min-sensor-lineage per-lineage "
        "perception intervention "
        "`per_founder_traits_overrides[bottom_lineage_ids[0]] = "
        "Traits(effective_sensor_radius_override=8)`, D reachability clears "
        "the 25% threshold AND both Label A AND Label B fire PRESENT at "
        "tick-400. **This is the surprising and high-information outcome.** "
        "Under v0.53n's alignment-control design, Label A indexes the "
        "MAX-sensor lineage — which receives NO override on D. For Label A "
        "to fire PRESENT despite not receiving the override implies one of: "
        "(i) the max-sensor lineage dominates food acquisition on D anyway "
        "via trait-level expression (e.g., reproduction-rate / "
        "metabolic-rate / hazard-tolerance pleiotropy with sensor_radius "
        "gives the max-sensor lineage an outcome edge once any access is "
        "rescued); (ii) the lineage labels / override targeting / "
        "measurement wiring need audit (verify `bottom_lineage_ids[0]` "
        "actually received the override; verify Label A picks "
        "`top_lineage_ids[0]`; verify the override propagated to "
        "descendants); (iii) some non-perception channel of the v0.48 "
        "bridge is dominant. The geometry/substrate cell that v0.53c "
        "through v0.53m locked admits a full-bridge rescue under "
        "min-lineage adversarial alignment: "
        "`MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE` — flagged for audit and "
        "follow-up. Results must include explicit checks of override "
        "targeting, descendant propagation, lineage-label resolution, and "
        "per-lineage population dynamics before assigning mechanistic "
        "interpretation. v0.53l/m's trait-aligned interpretation is NOT "
        "falsified by this outcome but requires additional non-perception "
        "mechanism to be operating in concert. v0.53o candidate: "
        "per-lineage population-dynamics audit + dose-response on `r=8` "
        "magnitude under min-lineage scope."
    ),
    ROLLUP_MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED: (
        "On the modern A_null corpus with the V0_25 substrate held constant "
        "except for the combined founder-facing budget relaxation AND the "
        "min-sensor-lineage per-lineage perception intervention on "
        "FOOD_NEAR1 at `n_ticks=400`, D's reachability clears the locked "
        "25% threshold but neither the clean DECOUPLES outcome (Label B "
        "PRESENT + Label A NOT PRESENT) nor the FULL_BRIDGE outcome (both "
        "labels PRESENT) holds, and D Label B has no wrong-sign cells "
        "(else priority 3 would have fired). "
        "C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces "
        "v0.53l's `61/64` anchor at tick-400 in-slice; "
        "E_widened_food_near1_combined_modelwide_sr8_N400 reproduces "
        "v0.53k's `64/64` anchor at tick-400 in-slice. The "
        "min-sensor-lineage adversarial intervention admits measurable "
        "food access on the boosted lineage but produces a mixed or "
        "partial bridge signal that does not cleanly localize the "
        "alignment requirement. Layout-specific partial-or-mixed "
        "alignment-control outcome logged in Results: "
        "`MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED`. Results section should "
        "describe which label fires under which cells, and whether the "
        "per-cell pattern hints at population-dynamics interference (e.g., "
        "the min-sensor boosted lineage having low reproductive fitness "
        "despite gaining access)."
    ),
    ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD: (
        "On the modern A_null corpus with the V0_25 substrate held constant "
        "except for the combined founder-facing budget relaxation AND the "
        "simulation horizon doubled to `n_ticks=400` AND the "
        "`widened_food_near1` layout AND the min-sensor-lineage per-lineage "
        "perception intervention, fewer than 25% of D runs have any "
        "founder lineage with pre400 food events. "
        "C_widened_food_near1_combined_max_lineage_sr8_N400 reproduces "
        "v0.53l's `61/64` anchor at tick-400 in-slice; "
        "E_widened_food_near1_combined_modelwide_sr8_N400 reproduces "
        "v0.53k's `64/64` anchor at tick-400 in-slice. **Min-lineage "
        "override is NOT symmetric with max-lineage override under this "
        "corpus and implementation.** The geometry/substrate cell that "
        "v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, "
        "v0.53d locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, "
        "v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, "
        "v0.53g locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, "
        "v0.53h locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, "
        "v0.53i locked as `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, v0.53j "
        "locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, "
        "v0.53k locked as "
        "`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`, v0.53l "
        "locked as `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`, "
        "and v0.53m locked as "
        "`WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` is not "
        "rescued at tick-400 when the same intervention magnitude (`r=8`) "
        "and same coverage (1/5) are assigned to the lowest-sensor "
        "lineage instead of the highest-sensor lineage. This implies that "
        "starting position, early survival, trait package interactions "
        "(the min-sensor founder may also carry low-fitness values on "
        "other traits via correlated sampling within the V0_25 "
        "TraitConfig), or reproduction-rate differential matter beyond "
        "raw perception radius — the boosted access does NOT translate "
        "into measurable food acquisition for the min-sensor lineage "
        "under the tested envelope. This does NOT prove `non-max lineages "
        "cannot use perception access` — only that this specific "
        "min-sensor adversarial scheme does not clear the threshold "
        "under the tested envelope. v0.53o candidate: per-lineage "
        "survival / reproduction diagnostics on D + dose-response on "
        "`r=8` magnitude under min-lineage scope: "
        "`MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD`."
    ),
}


class V053nReducerError(Exception):
    """Halt condition raised when a v0.53n invariant is violated."""


# ---------------------------------------------------------------------------
# Per-run capture (per-arm)
# ---------------------------------------------------------------------------


@dataclass
class _TickRecord:
    tick: int
    agents: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    food_cells: tuple[tuple[int, int], ...] = ()
    hazard_cells: tuple[tuple[int, int], ...] = ()


@dataclass
class _ReadinessSnapshot:
    agent_id: int
    lineage_id: int
    energy: float
    age: int


@dataclass
class _FounderRecord:
    """Per-founder snapshot for the v0.53n audit (read-only)."""

    lineage_id: int
    founder_index: int
    founder_sensor_radius: int
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    founder_body_energy_tick0: float
    founder_body_starting_energy_tick0: float
    founder_body_base_metabolic_cost_tick0: float
    founder_body_effective_sensor_radius_override_tick0: int | None
    founder_traits_effective_sensor_radius_override_tick0: int | None = None


@dataclass
class _RunCapture:
    arm: str
    layout_name: str
    safe_x_min: int
    safe_x_max: int
    hazard_x_min: int
    hazard_x_max: int
    food_x_min: int
    food_x_max: int
    world_width: int
    spawn_x: int
    height: int
    body_starting_energy: float
    body_base_metabolic_cost: float
    body_effective_sensor_radius_override: int | None
    n_ticks: int
    version: str
    seed: int
    hazard: int
    # v0.53n: C arm captures top1; D arm captures bottom1. top1 also recorded
    # on D for cross-arm Label A indexing diagnostics (Label A picks
    # top_lineage_ids[0] even on D — the alignment-control mechanism).
    top1_lineage_id_in_run: int | None = None
    bottom1_lineage_id_in_run: int | None = None
    top1_sensor_radius_in_run: int | None = None
    bottom1_sensor_radius_in_run: int | None = None
    tick_records: dict[int, _TickRecord] = field(default_factory=dict)
    tick50_readiness: list[_ReadinessSnapshot] = field(default_factory=list)
    tick100_readiness: list[_ReadinessSnapshot] = field(default_factory=list)
    tick200_readiness: list[_ReadinessSnapshot] = field(default_factory=list)
    tick400_readiness: list[_ReadinessSnapshot] = field(default_factory=list)
    birth_tick_by_agent: dict[int, int] = field(default_factory=dict)
    lineage_by_agent: dict[int, int] = field(default_factory=dict)
    founder_records: list[_FounderRecord] = field(default_factory=list)
    pre50_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre50_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre50_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre100_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre100_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre100_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre200_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre200_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre200_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre400_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre400_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre400_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    n_observer_fires: int = 0
    energy_threshold: float = 0.0
    min_age: int = 0
    living_population_by_window: dict[int, bool] = field(default_factory=dict)
    final_tick_count: int = 0


def _select_a_null_arm(version: str, hazard: int) -> Arm:
    armset = {
        "v0.42": V0_42_INTERVENTION_ARMS,
        "v0.43R": V0_43R_INTERVENTION_ARMS,
        "v0.44": V0_44_INTERVENTION_ARMS,
        "v0.45": V0_45_INTERVENTION_ARMS,
    }[version]
    candidates = [a for a in armset if "A_null" in a.label and a.hazard_damage == hazard]
    if len(candidates) != 1:
        msg = (
            f"v0.53n: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V053nReducerError(msg)
    return candidates[0]


# ---------------------------------------------------------------------------
# Founder audit (read-only — no patch)
# ---------------------------------------------------------------------------


def _capture_founder_audit(model: HHModel, capture: _RunCapture) -> None:
    founders = sorted(model.agents, key=lambda a: int(a.body.lineage_id))
    if len(founders) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.53n invariant: expected exactly {EXPECTED_FOUNDERS} founders "
            f"at setup_observer time; got {len(founders)}"
        )
        raise V053nReducerError(msg)
    body_starting_energy = float(model.body_config.starting_energy)
    body_base_metabolic_cost = float(model.body_config.base_metabolic_cost)
    raw_override = model.body_config.effective_sensor_radius_override
    body_effective_sensor_radius_override: int | None = (
        int(raw_override) if raw_override is not None else None
    )
    for i, agent in enumerate(founders):
        traits = agent.body.traits
        raw_traits_override = traits.effective_sensor_radius_override
        traits_override_value: int | None = (
            int(raw_traits_override) if raw_traits_override is not None else None
        )
        capture.founder_records.append(
            _FounderRecord(
                lineage_id=int(agent.body.lineage_id),
                founder_index=i,
                founder_sensor_radius=int(traits.sensor_radius),
                founder_reproduction_drive=float(traits.reproduction_drive),
                founder_metabolic_rate=float(traits.metabolic_rate),
                founder_body_energy_tick0=float(agent.body.energy),
                founder_body_starting_energy_tick0=body_starting_energy,
                founder_body_base_metabolic_cost_tick0=body_base_metabolic_cost,
                founder_body_effective_sensor_radius_override_tick0=(
                    body_effective_sensor_radius_override
                ),
                founder_traits_effective_sensor_radius_override_tick0=traits_override_value,
            )
        )


def _assert_layout_invariant(model: HHModel, arm: str) -> None:
    expected = _layout_for_arm(arm)
    actual_width = int(model.world.width)
    actual_height = int(model.world.height)
    if actual_width != expected.width or actual_height != expected.height:
        msg = (
            f"v0.53n layout invariant violated for arm {arm!r}: "
            f"expected (width={expected.width}, height={expected.height}); "
            f"got (width={actual_width}, height={actual_height})"
        )
        raise V053nReducerError(msg)


# ---------------------------------------------------------------------------
# Per-tick capture (read-only)
# ---------------------------------------------------------------------------


def _capture_tick_record(model: HHModel, tick_label: int, capture: _RunCapture) -> None:
    if tick_label in capture.tick_records:
        return
    capture.n_observer_fires += 1
    record = _TickRecord(tick=tick_label)
    for agent in model.agents:
        body = getattr(agent, "body", None)
        if body is None or not getattr(body, "alive", False):
            continue
        traits = body.traits
        record.agents.append(
            (
                int(body.id),
                int(body.lineage_id),
                int(body.x),
                int(body.y),
                int(traits.sensor_radius),
            )
        )
    food_mask = np.asarray(model.world.food_value) > 0
    food_xs, food_ys = np.where(food_mask)
    record.food_cells = tuple(zip(food_xs.tolist(), food_ys.tolist(), strict=True))
    hazard_mask = np.asarray(model.world.hazard_damage) > 0
    hazard_xs, hazard_ys = np.where(hazard_mask)
    record.hazard_cells = tuple(zip(hazard_xs.tolist(), hazard_ys.tolist(), strict=True))
    capture.tick_records[tick_label] = record


def _make_setup_observer(  # noqa: PLR0915
    arm: str,
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    arm_horizon = N_TICKS_BY_ARM[arm]

    def setup(model: HHModel) -> None:
        _capture_founder_audit(model, capture)

        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None:
                continue
            lineage_id = int(body.lineage_id)
            capture.lineage_by_agent[int(body.id)] = lineage_id
            capture.birth_tick_by_agent[int(body.id)] = 0

        def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
            aid = int(event.agent_id)
            capture.birth_tick_by_agent[aid] = int(event.tick)
            capture.lineage_by_agent[aid] = int(event.lineage_id)

        signal_for(AgentBorn).connect(_on_agent_born, sender=model, weak=False)
        disconnect_callbacks.append(
            lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
        )

        def _on_ate_food(_sender: object, *, event: AteFood) -> None:
            tick_now = int(model.tick_count)
            if tick_now > arm_horizon:
                return
            aid = int(event.agent_id)
            food_gained = float(event.food_gained)
            if tick_now <= TICK_50:
                capture.pre50_food_events_by_agent[aid] = (
                    capture.pre50_food_events_by_agent.get(aid, 0) + 1
                )
                capture.pre50_food_energy_by_agent[aid] = (
                    capture.pre50_food_energy_by_agent.get(aid, 0.0) + food_gained
                )
            if tick_now <= TICK_100:
                capture.pre100_food_events_by_agent[aid] = (
                    capture.pre100_food_events_by_agent.get(aid, 0) + 1
                )
                capture.pre100_food_energy_by_agent[aid] = (
                    capture.pre100_food_energy_by_agent.get(aid, 0.0) + food_gained
                )
            if tick_now <= TICK_200:
                capture.pre200_food_events_by_agent[aid] = (
                    capture.pre200_food_events_by_agent.get(aid, 0) + 1
                )
                capture.pre200_food_energy_by_agent[aid] = (
                    capture.pre200_food_energy_by_agent.get(aid, 0.0) + food_gained
                )
            if arm_horizon >= TICK_400 and tick_now <= TICK_400:
                capture.pre400_food_events_by_agent[aid] = (
                    capture.pre400_food_events_by_agent.get(aid, 0) + 1
                )
                capture.pre400_food_energy_by_agent[aid] = (
                    capture.pre400_food_energy_by_agent.get(aid, 0.0) + food_gained
                )

        def _on_hazard_damage(_sender: object, *, event: HazardDamageApplied) -> None:
            tick_now = int(model.tick_count)
            if tick_now > arm_horizon:
                return
            aid = int(event.agent_id)
            if tick_now <= TICK_50:
                capture.pre50_hazard_damage_events_by_agent[aid] = (
                    capture.pre50_hazard_damage_events_by_agent.get(aid, 0) + 1
                )
            if tick_now <= TICK_100:
                capture.pre100_hazard_damage_events_by_agent[aid] = (
                    capture.pre100_hazard_damage_events_by_agent.get(aid, 0) + 1
                )
            if tick_now <= TICK_200:
                capture.pre200_hazard_damage_events_by_agent[aid] = (
                    capture.pre200_hazard_damage_events_by_agent.get(aid, 0) + 1
                )
            if arm_horizon >= TICK_400 and tick_now <= TICK_400:
                capture.pre400_hazard_damage_events_by_agent[aid] = (
                    capture.pre400_hazard_damage_events_by_agent.get(aid, 0) + 1
                )

        signal_for(AteFood).connect(_on_ate_food, sender=model)
        signal_for(HazardDamageApplied).connect(_on_hazard_damage, sender=model)
        disconnect_callbacks.append(
            lambda: signal_for(AteFood).disconnect(_on_ate_food, sender=model)
        )
        disconnect_callbacks.append(
            lambda: signal_for(HazardDamageApplied).disconnect(_on_hazard_damage, sender=model)
        )

        capture.energy_threshold = float(model.reproduction_config.energy_threshold)
        capture.min_age = int(model.reproduction_config.min_age)

        _assert_layout_invariant(model, arm)
        _capture_tick_record(model, tick_label=0, capture=capture)

    return setup


def _make_per_tick_observer(arm: str, capture: _RunCapture) -> Callable[[HHModel], None]:
    arm_horizon = N_TICKS_BY_ARM[arm]

    def observer(model: HHModel) -> None:  # noqa: PLR0912
        tick = int(model.tick_count)
        if tick == 0 or tick > arm_horizon:
            return
        capture.final_tick_count = tick
        _capture_tick_record(model, tick_label=tick, capture=capture)
        if tick == TICK_50:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick50_readiness.append(
                    _ReadinessSnapshot(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )
        if tick == TICK_100:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick100_readiness.append(
                    _ReadinessSnapshot(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )
        if tick == TICK_200:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick200_readiness.append(
                    _ReadinessSnapshot(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )
        if tick == TICK_400 and arm_horizon >= TICK_400:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick400_readiness.append(
                    _ReadinessSnapshot(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )

    return observer


def _run_one_arm(  # noqa: PLR0912, PLR0915
    arm: str, version: str, seed: int, hazard: int, runs_root: Path
) -> _RunCapture:
    """Execute one (arm, version, seed, hazard) run, returning its capture."""
    if arm not in ARMS:
        msg = f"v0.53n: unknown arm {arm!r}"
        raise V053nReducerError(msg)
    base_arm = _select_a_null_arm(version, hazard)
    layout = _layout_for_arm(arm)
    layout_name = LAYOUT_NAME_BY_ARM[arm]
    arm_body_config = _body_config_for_arm(arm)
    arm_starting_energy = BODY_STARTING_ENERGY_BY_ARM[arm]
    arm_base_metabolic_cost = BODY_BASE_METABOLIC_COST_BY_ARM[arm]
    arm_effective_sensor_radius_override = BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM[arm]
    arm_n_ticks = N_TICKS_BY_ARM[arm]

    repro_kwargs: dict[str, float] = {
        "energy_threshold": (
            base_arm.energy_threshold
            if base_arm.energy_threshold is not None
            else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": (
            base_arm.energy_cost if base_arm.energy_cost is not None else FIXED_ENERGY_COST
        ),
    }
    if base_arm.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = base_arm.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
    trait_cfg = TraitConfig(unbounded_mutation=True)

    capture = _RunCapture(
        arm=arm,
        layout_name=layout_name,
        safe_x_min=int(layout.safe_x_min),
        safe_x_max=int(layout.safe_x_max),
        hazard_x_min=int(layout.hazard_x_min),
        hazard_x_max=int(layout.hazard_x_max),
        food_x_min=int(layout.food_x_min),
        food_x_max=int(layout.food_x_max),
        world_width=int(layout.width),
        spawn_x=int(layout.resolved_spawn_x),
        height=int(layout.height),
        body_starting_energy=arm_starting_energy,
        body_base_metabolic_cost=arm_base_metabolic_cost,
        body_effective_sensor_radius_override=arm_effective_sensor_radius_override,
        n_ticks=arm_n_ticks,
        version=version,
        seed=seed,
        hazard=hazard,
    )
    disconnects: list[Callable[[], None]] = []
    base_setup = _make_setup_observer(arm, capture, disconnects)

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = base_arm.auto_reproduction
        base_setup(model)

    use_memory = base_arm.memory_type is not None
    memory_type = base_arm.memory_type or "cell_exact"

    optional_intervention: InterventionConfig | None = None
    if base_arm.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=base_arm.intervention_kind)
    if optional_intervention is not None and optional_intervention.kind != KIND_NULL:
        msg = (
            f"v0.53n: base arm must be A_null only; got "
            f"intervention_kind={base_arm.intervention_kind!r}"
        )
        raise V053nReducerError(msg)

    # v0.53n: C arm uses top-K (k=1); D arm uses bottom-K (k=1); E uses
    # model-wide body_config; A/B pass no override.
    per_founder_overrides: list[Traits | None] | None = None
    arm_k = ARM_OVERRIDE_K[arm]
    if arm_k is not None:
        if arm == ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400:
            per_founder_overrides, top_lineage_ids = build_top_k_per_founder_overrides(
                seed=seed,
                trait_config=trait_cfg,
                n_founders=N_FOUNDERS,
                k=arm_k,
            )
            if len(top_lineage_ids) >= 1:
                capture.top1_lineage_id_in_run = int(top_lineage_ids[0])
                t1 = per_founder_overrides[top_lineage_ids[0]]
                if t1 is not None:
                    capture.top1_sensor_radius_in_run = int(t1.sensor_radius)
        elif arm == ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400:
            per_founder_overrides, bottom_lineage_ids = build_bottom_k_per_founder_overrides(
                seed=seed,
                trait_config=trait_cfg,
                n_founders=N_FOUNDERS,
                k=arm_k,
            )
            if len(bottom_lineage_ids) >= 1:
                capture.bottom1_lineage_id_in_run = int(bottom_lineage_ids[0])
                b1 = per_founder_overrides[bottom_lineage_ids[0]]
                if b1 is not None:
                    capture.bottom1_sensor_radius_in_run = int(b1.sensor_radius)
            # Also record top1 lineage_id on D for cross-arm diagnostics
            # (Label A picks top1 on D — the alignment-control mechanism).
            _, top_one = build_top_k_per_founder_overrides(
                seed=seed,
                trait_config=trait_cfg,
                n_founders=N_FOUNDERS,
                k=1,
            )
            if len(top_one) >= 1:
                capture.top1_lineage_id_in_run = int(top_one[0])
                streams_rs = make_streams(seed)
                sampled_rs = [
                    random_traits(trait_cfg, streams_rs.mutation) for _ in range(N_FOUNDERS)
                ]
                capture.top1_sensor_radius_in_run = int(sampled_rs[top_one[0]].sensor_radius)

    run_id = f"{arm}-{version}-A_null-hzd{hazard}-seed-{seed}"
    try:
        run_chamber(
            seed=seed,
            runs_root=runs_root,
            run_id=run_id,
            n_founders=N_FOUNDERS,
            n_ticks=arm_n_ticks,
            layout=layout,
            policy_factory=base_arm.policy_factory,
            trait_config=trait_cfg,
            reproduction_config=repro_cfg,
            body_config=arm_body_config,
            per_founder_traits_overrides=per_founder_overrides,
            use_memory=use_memory,
            memory_type=memory_type,
            food_respawn_cooldown=base_arm.food_respawn_cooldown,
            energy_pool_initial=base_arm.energy_pool_initial,
            ambient_influx_rate=base_arm.ambient_influx_rate,
            child_funding_mode=base_arm.child_funding_mode,
            hazard_damage=base_arm.hazard_damage,
            hazard_avoidance_weight=base_arm.hazard_avoidance_weight,
            condition=f"v0.53n-{arm}-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_per_tick_observer(arm, capture),
            optional_intervention=optional_intervention,
        )
    finally:
        for disconnect in disconnects:
            disconnect()

    max_expected_ticks = arm_n_ticks + 1
    if len(capture.tick_records) < 1 or len(capture.tick_records) > max_expected_ticks:
        msg = (
            f"v0.53n invariant: per-tick observer must capture between 1 and "
            f"{max_expected_ticks} ticks for {run_id}; got {len(capture.tick_records)}"
        )
        raise V053nReducerError(msg)
    if 0 not in capture.tick_records:
        msg = f"v0.53n invariant: missing tick-0 record for {run_id}"
        raise V053nReducerError(msg)
    captured_ticks = sorted(capture.tick_records.keys())
    if captured_ticks != list(range(captured_ticks[0], captured_ticks[-1] + 1)):
        msg = (
            f"v0.53n invariant: tick records must be a contiguous prefix for "
            f"{run_id}; got non-contiguous ticks {captured_ticks}"
        )
        raise V053nReducerError(msg)
    if len(capture.founder_records) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.53n invariant: expected exactly {EXPECTED_FOUNDERS} founder records for "
            f"{run_id}; got {len(capture.founder_records)}"
        )
        raise V053nReducerError(msg)

    arm_windows = WINDOWS_BY_ARM[arm]
    for window in arm_windows:
        record = capture.tick_records.get(window)
        capture.living_population_by_window[window] = record is not None and len(record.agents) > 0
    return capture


# ---------------------------------------------------------------------------
# Per-lineage row + label assignment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerLineageRow:
    arm: str
    layout_name: str
    safe_x_min: int
    safe_x_max: int
    hazard_x_min: int
    hazard_x_max: int
    food_x_min: int
    food_x_max: int
    world_width: int
    spawn_x: int
    height: int
    body_starting_energy: float
    body_base_metabolic_cost: float
    body_effective_sensor_radius_override: object
    founder_effective_sensor_radius_override: object
    is_max_sensor_lineage_in_run: bool
    # v0.53n NEW: min-sensor lineage column.
    is_min_sensor_lineage_in_run: bool
    top1_lineage_id_in_run: object
    bottom1_lineage_id_in_run: object
    top1_sensor_radius_in_run: object
    bottom1_sensor_radius_in_run: object
    n_ticks: int
    version: str
    seed: int
    hazard: int
    run_id: str
    lineage_id: int
    founder_sensor_radius: int
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    pre50_food_events_count: int
    pre50_food_energy_acquired: float
    pre100_food_events_count: int
    pre100_food_energy_acquired: float
    pre200_food_events_count: int
    pre200_food_energy_acquired: float
    pre400_food_events_count: float
    pre400_food_energy_acquired: float
    mean_distance_to_nearest_food_cell_tick50: float
    mean_distance_to_nearest_food_cell_tick100: float
    mean_distance_to_nearest_food_cell_tick200: float
    mean_distance_to_nearest_food_cell_tick400: float
    tick50_living_count: int
    tick50_above_threshold_count: int
    tick50_above_threshold_fraction: float
    tick100_living_count: int
    tick100_above_threshold_count: int
    tick100_above_threshold_fraction: float
    tick200_living_count: int
    tick200_above_threshold_count: int
    tick200_above_threshold_fraction: float
    tick400_living_count: float
    tick400_above_threshold_count: float
    tick400_above_threshold_fraction: float
    b50_count: int
    is_eventual_top_b50_label: bool
    is_high_sensor_radius_lineage: bool
    is_high_tick50_readiness_fraction_lineage: bool
    is_high_tick100_readiness_fraction_lineage: bool
    is_high_tick200_readiness_fraction_lineage: bool
    is_high_tick400_readiness_fraction_lineage: object


PER_LINEAGE_FIELDNAMES: list[str] = [
    "arm",
    "layout_name",
    "safe_x_min",
    "safe_x_max",
    "hazard_x_min",
    "hazard_x_max",
    "food_x_min",
    "food_x_max",
    "world_width",
    "spawn_x",
    "height",
    "body_starting_energy",
    "body_base_metabolic_cost",
    "body_effective_sensor_radius_override",
    "founder_effective_sensor_radius_override",
    "is_max_sensor_lineage_in_run",
    "is_min_sensor_lineage_in_run",
    "top1_lineage_id_in_run",
    "bottom1_lineage_id_in_run",
    "top1_sensor_radius_in_run",
    "bottom1_sensor_radius_in_run",
    "n_ticks",
    "version",
    "seed",
    "hazard",
    "run_id",
    "lineage_id",
    "founder_sensor_radius",
    "founder_reproduction_drive",
    "founder_metabolic_rate",
    "pre50_food_events_count",
    "pre50_food_energy_acquired",
    "pre100_food_events_count",
    "pre100_food_energy_acquired",
    "pre200_food_events_count",
    "pre200_food_energy_acquired",
    "pre400_food_events_count",
    "pre400_food_energy_acquired",
    "mean_distance_to_nearest_food_cell_tick50",
    "mean_distance_to_nearest_food_cell_tick100",
    "mean_distance_to_nearest_food_cell_tick200",
    "mean_distance_to_nearest_food_cell_tick400",
    "tick50_living_count",
    "tick50_above_threshold_count",
    "tick50_above_threshold_fraction",
    "tick100_living_count",
    "tick100_above_threshold_count",
    "tick100_above_threshold_fraction",
    "tick200_living_count",
    "tick200_above_threshold_count",
    "tick200_above_threshold_fraction",
    "tick400_living_count",
    "tick400_above_threshold_count",
    "tick400_above_threshold_fraction",
    "b50_count",
    "is_eventual_top_b50_label",
    "is_high_sensor_radius_lineage",
    "is_high_tick50_readiness_fraction_lineage",
    "is_high_tick100_readiness_fraction_lineage",
    "is_high_tick200_readiness_fraction_lineage",
    "is_high_tick400_readiness_fraction_lineage",
]


def _manhattan_distance_to_nearest(
    x: int, y: int, cells: tuple[tuple[int, int], ...]
) -> float | None:
    if not cells:
        return None
    return float(min(abs(cx - x) + abs(cy - y) for (cx, cy) in cells))


def _per_tick_lineage_distance_means(capture: _RunCapture, last_tick: int) -> dict[int, float]:
    all_lineages = sorted(set(capture.lineage_by_agent.values()))
    sums: dict[int, float] = dict.fromkeys(all_lineages, 0.0)
    counts: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for tick in range(last_tick + 1):
        record = capture.tick_records.get(tick)
        if record is None:
            continue
        living_by_lineage: dict[int, list[tuple[int, int, int, int, int]]] = {}
        for row in record.agents:
            living_by_lineage.setdefault(row[1], []).append(row)
        for lid, agents in living_by_lineage.items():
            agent_distances: list[float] = []
            for _aid, _lid, ax, ay, _r in agents:
                d = _manhattan_distance_to_nearest(ax, ay, record.food_cells)
                if d is not None:
                    agent_distances.append(d)
            if agent_distances:
                sums[lid] = sums.get(lid, 0.0) + statistics.mean(agent_distances)
                counts[lid] = counts.get(lid, 0) + 1
    out: dict[int, float] = {}
    for lid in all_lineages:
        out[lid] = sums[lid] / counts[lid] if counts.get(lid, 0) > 0 else float("nan")
    return out


def _select_fraction_label(candidates: list[tuple[int, float, int]]) -> int | None:
    """v0.47-style 3-tier tiebreak: fraction -> count -> min(lineage_id)."""
    if not candidates:
        return None
    best = candidates[0]
    for cand in candidates[1:]:
        if (
            cand[1] > best[1]
            or (cand[1] == best[1] and cand[2] > best[2])
            or (cand[1] == best[1] and cand[2] == best[2] and cand[0] < best[0])
        ):
            best = cand
    return best[0]


def _readiness_label_at_tick(
    all_lineages: list[int],
    readiness_snaps: list[_ReadinessSnapshot],
    energy_threshold: float,
    min_age: int,
) -> tuple[int | None, dict[int, int], dict[int, int], dict[int, float]]:
    living_by_lineage: dict[int, list[_ReadinessSnapshot]] = {lid: [] for lid in all_lineages}
    for snap in readiness_snaps:
        living_by_lineage.setdefault(snap.lineage_id, []).append(snap)

    fraction_by_lineage: dict[int, float] = {}
    count_by_lineage: dict[int, int] = {}
    living_count_by_lineage: dict[int, int] = {}
    for lid in all_lineages:
        living = living_by_lineage.get(lid, [])
        n_living = len(living)
        living_count_by_lineage[lid] = n_living
        n_above = sum(1 for s in living if s.energy >= energy_threshold and s.age >= min_age)
        count_by_lineage[lid] = n_above
        fraction_by_lineage[lid] = (n_above / n_living) if n_living > 0 else float("nan")

    candidates = [
        (lid, fraction_by_lineage[lid], count_by_lineage[lid])
        for lid in all_lineages
        if not math.isnan(fraction_by_lineage[lid])
    ]
    selected = _select_fraction_label(candidates)
    return selected, living_count_by_lineage, count_by_lineage, fraction_by_lineage


def _aggregate_per_lineage(  # noqa: PLR0912, PLR0915
    capture: _RunCapture,
) -> list[PerLineageRow]:
    all_lineages = sorted(set(capture.lineage_by_agent.values()))
    is_cde_arm = capture.arm in (
        ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
        ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
        ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
    )

    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.53n: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V053nReducerError(msg)
            b50_by_lineage[lid] = b50_by_lineage.get(lid, 0) + 1
    total_b50 = sum(b50_by_lineage.values())

    eventual_top: int | None
    if total_b50 == 0:
        eventual_top = None
    else:
        best_id = -1
        best_count = -1
        for lid in sorted(all_lineages):
            count = b50_by_lineage.get(lid, 0)
            if count > best_count:
                best_id = lid
                best_count = count
        eventual_top = best_id

    (
        fraction_label_tick50,
        living_count_tick50,
        above_count_tick50,
        fraction_tick50,
    ) = _readiness_label_at_tick(
        all_lineages,
        capture.tick50_readiness,
        capture.energy_threshold,
        capture.min_age,
    )
    (
        fraction_label_tick100,
        living_count_tick100,
        above_count_tick100,
        fraction_tick100,
    ) = _readiness_label_at_tick(
        all_lineages,
        capture.tick100_readiness,
        capture.energy_threshold,
        capture.min_age,
    )
    (
        fraction_label_tick200,
        living_count_tick200,
        above_count_tick200,
        fraction_tick200,
    ) = _readiness_label_at_tick(
        all_lineages,
        capture.tick200_readiness,
        capture.energy_threshold,
        capture.min_age,
    )
    if is_cde_arm:
        (
            fraction_label_tick400,
            living_count_tick400,
            above_count_tick400,
            fraction_tick400,
        ) = _readiness_label_at_tick(
            all_lineages,
            capture.tick400_readiness,
            capture.energy_threshold,
            capture.min_age,
        )
    else:
        fraction_label_tick400 = None
        living_count_tick400 = {}
        above_count_tick400 = {}
        fraction_tick400 = {}

    founder_by_lineage: dict[int, _FounderRecord] = {
        rec.lineage_id: rec for rec in capture.founder_records
    }
    sensor_radius_by_lineage: dict[int, int] = {
        lid: founder_by_lineage[lid].founder_sensor_radius for lid in all_lineages
    }
    # Label A picks the MAX-sensor lineage; this is the alignment-control
    # mechanism on D (Label A indexes max-sensor regardless of which
    # lineage actually received the override).
    sensor_label = _select_sensor_radius_label(sensor_radius_by_lineage)
    # min-sensor lineage (D arm's boosted lineage).
    min_sensor_lid: int | None = None
    bottom_one = _select_bottom_k_sensor_radius_lineages(sensor_radius_by_lineage, 1)
    if bottom_one:
        min_sensor_lid = bottom_one[0]

    distance_by_lineage_tick50 = _per_tick_lineage_distance_means(capture, TICK_50)
    distance_by_lineage_tick100 = _per_tick_lineage_distance_means(capture, TICK_100)
    distance_by_lineage_tick200 = _per_tick_lineage_distance_means(capture, TICK_200)
    if is_cde_arm:
        distance_by_lineage_tick400 = _per_tick_lineage_distance_means(capture, TICK_400)
    else:
        distance_by_lineage_tick400 = {lid: float("nan") for lid in all_lineages}

    pre50_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre50_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    pre100_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre100_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    pre200_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre200_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    pre400_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre400_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    for aid, lid in capture.lineage_by_agent.items():
        pre50_food_events_by_lineage[lid] = pre50_food_events_by_lineage.get(
            lid, 0
        ) + capture.pre50_food_events_by_agent.get(aid, 0)
        pre50_food_energy_by_lineage[lid] = pre50_food_energy_by_lineage.get(
            lid, 0.0
        ) + capture.pre50_food_energy_by_agent.get(aid, 0.0)
        pre100_food_events_by_lineage[lid] = pre100_food_events_by_lineage.get(
            lid, 0
        ) + capture.pre100_food_events_by_agent.get(aid, 0)
        pre100_food_energy_by_lineage[lid] = pre100_food_energy_by_lineage.get(
            lid, 0.0
        ) + capture.pre100_food_energy_by_agent.get(aid, 0.0)
        pre200_food_events_by_lineage[lid] = pre200_food_events_by_lineage.get(
            lid, 0
        ) + capture.pre200_food_events_by_agent.get(aid, 0)
        pre200_food_energy_by_lineage[lid] = pre200_food_energy_by_lineage.get(
            lid, 0.0
        ) + capture.pre200_food_energy_by_agent.get(aid, 0.0)
        if is_cde_arm:
            pre400_food_events_by_lineage[lid] = pre400_food_events_by_lineage.get(
                lid, 0
            ) + capture.pre400_food_events_by_agent.get(aid, 0)
            pre400_food_energy_by_lineage[lid] = pre400_food_energy_by_lineage.get(
                lid, 0.0
            ) + capture.pre400_food_energy_by_agent.get(aid, 0.0)

    rows: list[PerLineageRow] = []
    run_id = f"{capture.arm}-{capture.version}-A_null-hzd{capture.hazard}-seed-{capture.seed}"
    for lid in all_lineages:
        founder = founder_by_lineage[lid]
        if is_cde_arm:
            pre400_count_val: float = float(pre400_food_events_by_lineage.get(lid, 0))
            pre400_energy_val: float = pre400_food_energy_by_lineage.get(lid, 0.0)
            tick400_living_val: float = float(living_count_tick400[lid])
            tick400_above_count_val: float = float(above_count_tick400[lid])
            tick400_above_frac_val: float = fraction_tick400[lid]
            high_tick400_label_val: object = (
                fraction_label_tick400 is not None and lid == fraction_label_tick400
            )
        else:
            pre400_count_val = float("nan")
            pre400_energy_val = float("nan")
            tick400_living_val = float("nan")
            tick400_above_count_val = float("nan")
            tick400_above_frac_val = float("nan")
            high_tick400_label_val = float("nan")
        rows.append(
            PerLineageRow(
                arm=capture.arm,
                layout_name=capture.layout_name,
                safe_x_min=capture.safe_x_min,
                safe_x_max=capture.safe_x_max,
                hazard_x_min=capture.hazard_x_min,
                hazard_x_max=capture.hazard_x_max,
                food_x_min=capture.food_x_min,
                food_x_max=capture.food_x_max,
                world_width=capture.world_width,
                spawn_x=capture.spawn_x,
                height=capture.height,
                body_starting_energy=capture.body_starting_energy,
                body_base_metabolic_cost=capture.body_base_metabolic_cost,
                body_effective_sensor_radius_override=(
                    capture.body_effective_sensor_radius_override
                ),
                founder_effective_sensor_radius_override=(
                    founder.founder_traits_effective_sensor_radius_override_tick0
                ),
                is_max_sensor_lineage_in_run=(sensor_label is not None and lid == sensor_label),
                is_min_sensor_lineage_in_run=(min_sensor_lid is not None and lid == min_sensor_lid),
                top1_lineage_id_in_run=capture.top1_lineage_id_in_run,
                bottom1_lineage_id_in_run=capture.bottom1_lineage_id_in_run,
                top1_sensor_radius_in_run=capture.top1_sensor_radius_in_run,
                bottom1_sensor_radius_in_run=capture.bottom1_sensor_radius_in_run,
                n_ticks=capture.n_ticks,
                version=capture.version,
                seed=capture.seed,
                hazard=capture.hazard,
                run_id=run_id,
                lineage_id=lid,
                founder_sensor_radius=founder.founder_sensor_radius,
                founder_reproduction_drive=float(founder.founder_reproduction_drive),
                founder_metabolic_rate=float(founder.founder_metabolic_rate),
                pre50_food_events_count=pre50_food_events_by_lineage.get(lid, 0),
                pre50_food_energy_acquired=pre50_food_energy_by_lineage.get(lid, 0.0),
                pre100_food_events_count=pre100_food_events_by_lineage.get(lid, 0),
                pre100_food_energy_acquired=pre100_food_energy_by_lineage.get(lid, 0.0),
                pre200_food_events_count=pre200_food_events_by_lineage.get(lid, 0),
                pre200_food_energy_acquired=pre200_food_energy_by_lineage.get(lid, 0.0),
                pre400_food_events_count=pre400_count_val,
                pre400_food_energy_acquired=pre400_energy_val,
                mean_distance_to_nearest_food_cell_tick50=distance_by_lineage_tick50.get(
                    lid, float("nan")
                ),
                mean_distance_to_nearest_food_cell_tick100=distance_by_lineage_tick100.get(
                    lid, float("nan")
                ),
                mean_distance_to_nearest_food_cell_tick200=distance_by_lineage_tick200.get(
                    lid, float("nan")
                ),
                mean_distance_to_nearest_food_cell_tick400=distance_by_lineage_tick400.get(
                    lid, float("nan")
                ),
                tick50_living_count=living_count_tick50[lid],
                tick50_above_threshold_count=above_count_tick50[lid],
                tick50_above_threshold_fraction=fraction_tick50[lid],
                tick100_living_count=living_count_tick100[lid],
                tick100_above_threshold_count=above_count_tick100[lid],
                tick100_above_threshold_fraction=fraction_tick100[lid],
                tick200_living_count=living_count_tick200[lid],
                tick200_above_threshold_count=above_count_tick200[lid],
                tick200_above_threshold_fraction=fraction_tick200[lid],
                tick400_living_count=tick400_living_val,
                tick400_above_threshold_count=tick400_above_count_val,
                tick400_above_threshold_fraction=tick400_above_frac_val,
                b50_count=b50_by_lineage.get(lid, 0),
                is_eventual_top_b50_label=(eventual_top is not None and lid == eventual_top),
                is_high_sensor_radius_lineage=(sensor_label is not None and lid == sensor_label),
                is_high_tick50_readiness_fraction_lineage=(
                    fraction_label_tick50 is not None and lid == fraction_label_tick50
                ),
                is_high_tick100_readiness_fraction_lineage=(
                    fraction_label_tick100 is not None and lid == fraction_label_tick100
                ),
                is_high_tick200_readiness_fraction_lineage=(
                    fraction_label_tick200 is not None and lid == fraction_label_tick200
                ),
                is_high_tick400_readiness_fraction_lineage=high_tick400_label_val,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Effect-size + per-arm sub-verdicts
# ---------------------------------------------------------------------------


def _per_run_paired_delta(
    rows_in_run: list[PerLineageRow], observable_field: str, label_field: str
) -> float | None:
    label_rows: list[PerLineageRow] = []
    for r in rows_in_run:
        v = getattr(r, label_field)
        if isinstance(v, float) and math.isnan(v):
            continue
        if v:
            label_rows.append(r)
    if len(label_rows) != 1:
        return None
    label_value = getattr(label_rows[0], observable_field)
    if isinstance(label_value, float) and math.isnan(label_value):
        return None
    non_label: list[PerLineageRow] = []
    for r in rows_in_run:
        v = getattr(r, label_field)
        if isinstance(v, float) and math.isnan(v):
            non_label.append(r)
            continue
        if not v:
            non_label.append(r)
    non_label_values = [
        getattr(r, observable_field)
        for r in non_label
        if not (
            isinstance(getattr(r, observable_field), float)
            and math.isnan(getattr(r, observable_field))
        )
    ]
    if not non_label_values:
        return None
    return float(label_value) - statistics.mean(non_label_values)


def _paired_cohens_d(deltas: list[float]) -> float:
    if len(deltas) < 2:
        return float("nan")
    mean = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    if sd == 0:
        return float("nan")
    return mean / sd


@dataclass(frozen=True)
class ObservableSummary:
    arm: str
    observable: str
    label: str
    sign: int
    n_runs_contributing: int
    paired_d: float
    signed_d: float
    delta_mean: float
    delta_stdev: float
    delta_min: float
    delta_max: float
    fires_expected: bool
    fires_wrong: bool


def _index_rows_by_arm_run(
    rows: list[PerLineageRow],
) -> dict[tuple[str, str, int, int], list[PerLineageRow]]:
    out: dict[tuple[str, str, int, int], list[PerLineageRow]] = {}
    for r in rows:
        out.setdefault((r.arm, r.version, r.seed, r.hazard), []).append(r)
    return out


def _summarise_observable_for_arm(
    *,
    arm: str,
    observable: str,
    sign: int,
    label: str,
    label_field: str,
    all_rows: list[PerLineageRow],
    runs: list[tuple[str, int, int]],
) -> ObservableSummary:
    deltas: list[float] = []
    by_arm_run = _index_rows_by_arm_run(all_rows)
    for run_key in runs:
        run_rows = by_arm_run.get((arm, run_key[0], run_key[1], run_key[2]), [])
        delta = _per_run_paired_delta(run_rows, observable, label_field)
        if delta is not None:
            deltas.append(delta)
    d = _paired_cohens_d(deltas)
    if not deltas:
        delta_mean = float("nan")
        delta_min = float("nan")
        delta_max = float("nan")
    else:
        delta_mean = statistics.mean(deltas)
        delta_min = min(deltas)
        delta_max = max(deltas)
    delta_stdev = statistics.stdev(deltas) if len(deltas) >= 2 else float("nan")
    signed_d = d * sign if not math.isnan(d) else d
    fires_expected = (not math.isnan(signed_d)) and signed_d >= COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed_d)) and signed_d <= -COHENS_D_THRESHOLD
    return ObservableSummary(
        arm=arm,
        observable=observable,
        label=label,
        sign=sign,
        n_runs_contributing=len(deltas),
        paired_d=d,
        signed_d=signed_d,
        delta_mean=delta_mean,
        delta_stdev=delta_stdev,
        delta_min=delta_min,
        delta_max=delta_max,
        fires_expected=fires_expected,
        fires_wrong=fires_wrong,
    )


_SUBVERDICT_TICK50_TABLE: dict[str, tuple[str, str, str, str]] = {
    ARM_A_NULL_V025: (
        SUBVERDICT_A_NULL_V025_TICK50_PRESENT,
        SUBVERDICT_A_NULL_V025_TICK50_PARTIAL,
        SUBVERDICT_A_NULL_V025_TICK50_NOT_FOUND,
        SUBVERDICT_A_NULL_V025_TICK50_OPPOSITE,
    ),
    ARM_B_WIDENED_V025: (
        SUBVERDICT_B_WIDENED_V025_TICK50_PRESENT,
        SUBVERDICT_B_WIDENED_V025_TICK50_PARTIAL,
        SUBVERDICT_B_WIDENED_V025_TICK50_NOT_FOUND,
        SUBVERDICT_B_WIDENED_V025_TICK50_OPPOSITE,
    ),
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: (
        SUBVERDICT_C_FOOD_NEAR1_TICK50_PRESENT,
        SUBVERDICT_C_FOOD_NEAR1_TICK50_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR1_TICK50_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR1_TICK50_OPPOSITE,
    ),
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: (
        SUBVERDICT_D_FOOD_NEAR1_TICK50_PRESENT,
        SUBVERDICT_D_FOOD_NEAR1_TICK50_PARTIAL,
        SUBVERDICT_D_FOOD_NEAR1_TICK50_NOT_FOUND,
        SUBVERDICT_D_FOOD_NEAR1_TICK50_OPPOSITE,
    ),
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: (
        SUBVERDICT_E_FOOD_NEAR1_TICK50_PRESENT,
        SUBVERDICT_E_FOOD_NEAR1_TICK50_PARTIAL,
        SUBVERDICT_E_FOOD_NEAR1_TICK50_NOT_FOUND,
        SUBVERDICT_E_FOOD_NEAR1_TICK50_OPPOSITE,
    ),
}

_SUBVERDICT_TICK100_TABLE: dict[str, tuple[str, str, str, str]] = {
    ARM_A_NULL_V025: (
        SUBVERDICT_A_NULL_V025_TICK100_PRESENT,
        SUBVERDICT_A_NULL_V025_TICK100_PARTIAL,
        SUBVERDICT_A_NULL_V025_TICK100_NOT_FOUND,
        SUBVERDICT_A_NULL_V025_TICK100_OPPOSITE,
    ),
    ARM_B_WIDENED_V025: (
        SUBVERDICT_B_WIDENED_V025_TICK100_PRESENT,
        SUBVERDICT_B_WIDENED_V025_TICK100_PARTIAL,
        SUBVERDICT_B_WIDENED_V025_TICK100_NOT_FOUND,
        SUBVERDICT_B_WIDENED_V025_TICK100_OPPOSITE,
    ),
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: (
        SUBVERDICT_C_FOOD_NEAR1_TICK100_PRESENT,
        SUBVERDICT_C_FOOD_NEAR1_TICK100_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR1_TICK100_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR1_TICK100_OPPOSITE,
    ),
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: (
        SUBVERDICT_D_FOOD_NEAR1_TICK100_PRESENT,
        SUBVERDICT_D_FOOD_NEAR1_TICK100_PARTIAL,
        SUBVERDICT_D_FOOD_NEAR1_TICK100_NOT_FOUND,
        SUBVERDICT_D_FOOD_NEAR1_TICK100_OPPOSITE,
    ),
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: (
        SUBVERDICT_E_FOOD_NEAR1_TICK100_PRESENT,
        SUBVERDICT_E_FOOD_NEAR1_TICK100_PARTIAL,
        SUBVERDICT_E_FOOD_NEAR1_TICK100_NOT_FOUND,
        SUBVERDICT_E_FOOD_NEAR1_TICK100_OPPOSITE,
    ),
}

_SUBVERDICT_TICK200_TABLE: dict[str, tuple[str, str, str, str]] = {
    ARM_A_NULL_V025: (
        SUBVERDICT_A_NULL_V025_TICK200_PRESENT,
        SUBVERDICT_A_NULL_V025_TICK200_PARTIAL,
        SUBVERDICT_A_NULL_V025_TICK200_NOT_FOUND,
        SUBVERDICT_A_NULL_V025_TICK200_OPPOSITE,
    ),
    ARM_B_WIDENED_V025: (
        SUBVERDICT_B_WIDENED_V025_TICK200_PRESENT,
        SUBVERDICT_B_WIDENED_V025_TICK200_PARTIAL,
        SUBVERDICT_B_WIDENED_V025_TICK200_NOT_FOUND,
        SUBVERDICT_B_WIDENED_V025_TICK200_OPPOSITE,
    ),
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: (
        SUBVERDICT_C_FOOD_NEAR1_TICK200_PRESENT,
        SUBVERDICT_C_FOOD_NEAR1_TICK200_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR1_TICK200_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR1_TICK200_OPPOSITE,
    ),
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: (
        SUBVERDICT_D_FOOD_NEAR1_TICK200_PRESENT,
        SUBVERDICT_D_FOOD_NEAR1_TICK200_PARTIAL,
        SUBVERDICT_D_FOOD_NEAR1_TICK200_NOT_FOUND,
        SUBVERDICT_D_FOOD_NEAR1_TICK200_OPPOSITE,
    ),
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: (
        SUBVERDICT_E_FOOD_NEAR1_TICK200_PRESENT,
        SUBVERDICT_E_FOOD_NEAR1_TICK200_PARTIAL,
        SUBVERDICT_E_FOOD_NEAR1_TICK200_NOT_FOUND,
        SUBVERDICT_E_FOOD_NEAR1_TICK200_OPPOSITE,
    ),
}

_SUBVERDICT_TICK400_TABLE: dict[str, tuple[str, str, str, str]] = {
    ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400: (
        SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT,
        SUBVERDICT_C_FOOD_NEAR1_TICK400_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR1_TICK400_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR1_TICK400_OPPOSITE,
    ),
    ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400: (
        SUBVERDICT_D_FOOD_NEAR1_TICK400_PRESENT,
        SUBVERDICT_D_FOOD_NEAR1_TICK400_PARTIAL,
        SUBVERDICT_D_FOOD_NEAR1_TICK400_NOT_FOUND,
        SUBVERDICT_D_FOOD_NEAR1_TICK400_OPPOSITE,
    ),
    ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400: (
        SUBVERDICT_E_FOOD_NEAR1_TICK400_PRESENT,
        SUBVERDICT_E_FOOD_NEAR1_TICK400_PARTIAL,
        SUBVERDICT_E_FOOD_NEAR1_TICK400_NOT_FOUND,
        SUBVERDICT_E_FOOD_NEAR1_TICK400_OPPOSITE,
    ),
}


def _classify_subverdict(
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
    sub_table: tuple[str, str, str, str],
) -> str:
    """Per-arm 4-way sub-verdict from two label triples."""
    present, partial, not_found, opposite = sub_table
    n_wrong = sum(1 for s in summaries_a + summaries_b if s.fires_wrong)
    if n_wrong > 0:
        return opposite
    n_fire_a = sum(1 for s in summaries_a if s.fires_expected)
    n_fire_b = sum(1 for s in summaries_b if s.fires_expected)
    a_clears = n_fire_a >= 2
    b_clears = n_fire_b >= 2
    if a_clears and b_clears:
        return present
    if a_clears != b_clears:
        return partial
    return not_found


def _arm_subverdict_at_window(
    arm: str,
    window: int,
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
) -> str:
    if window == TICK_50:
        table = _SUBVERDICT_TICK50_TABLE[arm]
    elif window == TICK_100:
        table = _SUBVERDICT_TICK100_TABLE[arm]
    elif window == TICK_200:
        table = _SUBVERDICT_TICK200_TABLE[arm]
    elif window == TICK_400:
        if arm not in _SUBVERDICT_TICK400_TABLE:
            msg = f"v0.53n: tick-400 sub-verdict only defined on C/D/E; got arm {arm!r}"
            raise V053nReducerError(msg)
        table = _SUBVERDICT_TICK400_TABLE[arm]
    else:
        msg = f"v0.53n: unknown window {window!r}"
        raise V053nReducerError(msg)
    return _classify_subverdict(summaries_a, summaries_b, table)


# Per-arm Label A / Label B firing helpers for D-specific rollup logic.
# These return ("PRESENT" | "NOT_PRESENT", n_wrong) tuples per label
# triple. Used in the asymmetric halt rule on D.
def _label_firing_status(
    summaries: list[ObservableSummary],
) -> tuple[str, int]:
    """Classify a single label triple into ('PRESENT' | 'NOT_PRESENT', n_wrong).

    PRESENT iff 2/3 fires_expected AND 0 fires_wrong.
    NOT_PRESENT otherwise (covers NOT_FOUND, PARTIAL <2/3, wrong-sign,
    NaN-nonfiring).
    """
    n_fire = sum(1 for s in summaries if s.fires_expected)
    n_wrong = sum(1 for s in summaries if s.fires_wrong)
    if n_fire >= 2 and n_wrong == 0:
        return "PRESENT", n_wrong
    return "NOT_PRESENT", n_wrong


# ---------------------------------------------------------------------------
# Re-anchor (corpus + Tier-1 bridge + C/E in-slice anchors)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReAnchorRow:
    arm: str
    version: str
    hazard: int
    n_runs_contributing: int
    a_share_h8_derived: float
    a_share_h8_published: float | None
    drift_abs: float | None
    halts: bool


def _compute_a_share_h8(all_rows: list[PerLineageRow], arm: str, version: str) -> tuple[float, int]:
    by_arm_run = _index_rows_by_arm_run(all_rows)
    shares: list[float] = []
    for (a, ver, _seed, haz), rows_in_run in by_arm_run.items():
        if a != arm or ver != version or haz != 8:
            continue
        total_b50 = sum(r.b50_count for r in rows_in_run)
        if total_b50 == 0:
            continue
        max_b50 = max(r.b50_count for r in rows_in_run)
        shares.append(max_b50 / total_b50)
    if not shares:
        return float("nan"), 0
    return statistics.mean(shares), len(shares)


def _check_corpus_re_anchor(all_rows: list[PerLineageRow]) -> list[ReAnchorRow]:
    out: list[ReAnchorRow] = []
    for arm in ARMS:
        for version in ("v0.42", "v0.43R", "v0.44", "v0.45"):
            derived, n_runs = _compute_a_share_h8(all_rows, arm, version)
            published = PUBLISHED_A_SHARE_H8[version] if arm == ARM_A_NULL_V025 else None
            if published is None or math.isnan(derived):
                drift_abs: float | None = None
                halts = False
            else:
                drift_abs = abs(derived - published)
                halts = drift_abs > RE_ANCHOR_DRIFT_TOLERANCE
            out.append(
                ReAnchorRow(
                    arm=arm,
                    version=version,
                    hazard=8,
                    n_runs_contributing=n_runs,
                    a_share_h8_derived=derived,
                    a_share_h8_published=published,
                    drift_abs=drift_abs,
                    halts=halts,
                )
            )
    return out


@dataclass(frozen=True)
class BridgeReAnchorRow:
    label: str
    observable: str
    published_signed_d: float
    derived_signed_d: float
    drift_abs: float
    halts: bool


def _check_bridge_re_anchor_tick50(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
) -> list[BridgeReAnchorRow]:
    out: list[BridgeReAnchorRow] = []
    for (label, observable), published in V048_PUBLISHED_SIGNED_D.items():
        derived = _lookup_signed_d(summaries_by_arm_label, ARM_A_NULL_V025, label, observable)
        if math.isnan(derived):
            drift_abs = float("inf")
            halts = True
        else:
            drift_abs = abs(derived - published)
            halts = drift_abs > RE_ANCHOR_DRIFT_TOLERANCE
        out.append(
            BridgeReAnchorRow(
                label=label,
                observable=observable,
                published_signed_d=published,
                derived_signed_d=derived,
                drift_abs=drift_abs,
                halts=halts,
            )
        )
    return out


@dataclass(frozen=True)
class InSliceAnchorRow:
    anchor_arm: str
    label: str
    observable: str
    published_signed_d: float
    derived_signed_d: float
    drift_abs: float
    halts: bool


def _check_c_inslice_paired_d_anchor(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
    c_published: dict[tuple[str, str], float] | None = None,
) -> list[InSliceAnchorRow]:
    if c_published is None:
        c_published = V053L_C_TIER3_ANCHOR_PUBLISHED
    out: list[InSliceAnchorRow] = []
    for (label, observable), published in c_published.items():
        derived = _lookup_signed_d(
            summaries_by_arm_label,
            ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
            label,
            observable,
        )
        if math.isnan(derived):
            drift_abs = float("inf")
            halts = True
        else:
            drift_abs = abs(derived - published)
            halts = drift_abs > INSLICE_PAIRED_D_TOLERANCE
        out.append(
            InSliceAnchorRow(
                anchor_arm="C_vs_v053l",
                label=label,
                observable=observable,
                published_signed_d=published,
                derived_signed_d=derived,
                drift_abs=drift_abs,
                halts=halts,
            )
        )
    return out


def _check_e_inslice_paired_d_anchor(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
    e_published: dict[tuple[str, str], float] | None = None,
) -> list[InSliceAnchorRow]:
    if e_published is None:
        e_published = V053K_C_TIER3_ANCHOR_PUBLISHED
    out: list[InSliceAnchorRow] = []
    for (label, observable), published in e_published.items():
        derived = _lookup_signed_d(
            summaries_by_arm_label,
            ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
            label,
            observable,
        )
        if math.isnan(derived):
            drift_abs = float("inf")
            halts = True
        else:
            drift_abs = abs(derived - published)
            halts = drift_abs > INSLICE_PAIRED_D_TOLERANCE
        out.append(
            InSliceAnchorRow(
                anchor_arm="E_vs_v053k",
                label=label,
                observable=observable,
                published_signed_d=published,
                derived_signed_d=derived,
                drift_abs=drift_abs,
                halts=halts,
            )
        )
    return out


def _lookup_signed_d(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
    arm: str,
    label: str,
    observable: str,
) -> float:
    for s in summaries_by_arm_label.get((arm, label), []):
        if s.observable == observable:
            return s.signed_d
    return float("nan")


# ---------------------------------------------------------------------------
# Per-arm reachability + population-stability metrics
# ---------------------------------------------------------------------------


def _compute_arm_reachability_run_share(
    all_rows: list[PerLineageRow], arm: str, events_field: str
) -> tuple[float, int]:
    by_arm_run = _index_rows_by_arm_run(all_rows)
    n_runs_total = 0
    n_runs_with_food = 0
    for (a, _ver, _seed, _haz), rows_in_run in by_arm_run.items():
        if a != arm:
            continue
        n_runs_total += 1
        any_food = False
        for r in rows_in_run:
            v = getattr(r, events_field)
            if isinstance(v, float) and math.isnan(v):
                continue
            if v > 0:
                any_food = True
                break
        if any_food:
            n_runs_with_food += 1
    if n_runs_total == 0:
        return float("nan"), 0
    return n_runs_with_food / n_runs_total, n_runs_total


@dataclass(frozen=True)
class PopulationStabilityRow:
    arm: str
    window: int
    n_runs_total: int
    living_population_run_share: float
    label_a_n_runs: int
    label_b_n_runs: int


def _compute_population_stability(
    all_rows: list[PerLineageRow],
    captures: list[_RunCapture],
) -> list[PopulationStabilityRow]:
    by_arm_run = _index_rows_by_arm_run(all_rows)
    captures_by_key: dict[tuple[str, str, int, int], _RunCapture] = {}
    for cap in captures:
        captures_by_key[(cap.arm, cap.version, cap.seed, cap.hazard)] = cap

    label_b_field_by_window: dict[int, str] = {
        TICK_50: LABEL_B_TICK50_FIELD,
        TICK_100: LABEL_B_TICK100_FIELD,
        TICK_200: LABEL_B_TICK200_FIELD,
        TICK_400: LABEL_B_TICK400_FIELD,
    }

    out: list[PopulationStabilityRow] = []
    for arm in ARMS:
        run_keys = [k for k in by_arm_run if k[0] == arm]
        n_runs_total = len(run_keys)
        for window in WINDOWS_BY_ARM[arm]:
            n_living = 0
            n_label_a = 0
            n_label_b = 0
            for k in run_keys:
                cap = captures_by_key.get(k)
                if cap is not None and cap.living_population_by_window.get(window, False):
                    n_living += 1
                rows_in_run = by_arm_run[k]
                if any(getattr(r, LABEL_A_FIELD) for r in rows_in_run):
                    n_label_a += 1
                label_b_field = label_b_field_by_window[window]
                if any(
                    not (
                        isinstance(getattr(r, label_b_field), float)
                        and math.isnan(getattr(r, label_b_field))
                    )
                    and getattr(r, label_b_field)
                    for r in rows_in_run
                ):
                    n_label_b += 1
            living_share = (n_living / n_runs_total) if n_runs_total > 0 else float("nan")
            out.append(
                PopulationStabilityRow(
                    arm=arm,
                    window=window,
                    n_runs_total=n_runs_total,
                    living_population_run_share=living_share,
                    label_a_n_runs=n_label_a,
                    label_b_n_runs=n_label_b,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Wrong-sign cell collection (D arm, tick-400)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WrongSignCellRow:
    arm: str
    label: str
    observable: str
    paired_d: float
    signed_d: float
    n: int


def _collect_d_tick400_wrong_sign_cells(
    summaries_tick400: list[ObservableSummary],
) -> list[WrongSignCellRow]:
    rows: list[WrongSignCellRow] = []
    for s in summaries_tick400:
        if s.arm != ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400:
            continue
        if not s.fires_wrong:
            continue
        rows.append(
            WrongSignCellRow(
                arm=s.arm,
                label=s.label,
                observable=s.observable,
                paired_d=s.paired_d,
                signed_d=s.signed_d,
                n=s.n_runs_contributing,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Slice rollup (priority-ordered, 7 outcomes)
# ---------------------------------------------------------------------------


def _evaluate_rollup(  # noqa: PLR0911, PLR0912
    *,
    a_null_tick50_subverdict: str,
    d_tick400_label_a_summaries: list[ObservableSummary],
    d_tick400_label_b_summaries: list[ObservableSummary],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    b_widened_v025_reachability_tick200: float,
    c_reachability_tick400: float,
    c_tick400_subverdict: str,
    c_tick400_signed_d: dict[tuple[str, str], float],
    e_reachability_tick400: float,
    e_tick400_subverdict: str,
    e_tick400_signed_d: dict[tuple[str, str], float],
    d_reachability_tick400: float,
) -> tuple[str, str]:
    """7-outcome priority-ordered rollup with asymmetric halt rule.

    Priority 3 (`MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT`) triggers ONLY
    on D Label B wrong-sign cells (signed_d <= -0.5) AND D reachability
    >= 0.25. D Label A wrong-sign cells alone do NOT trigger priority 3
    — they route to priority 4 (DECOUPLES) since "Label A wrong-sign"
    ⊂ "Label A NOT PRESENT" in priority 4's trigger.

    Priority 4 trigger: ``d_reach >= 0.25`` AND D Label B PRESENT AND D
    Label A NOT PRESENT.
    Priority 5 trigger: ``d_reach >= 0.25`` AND Label A PRESENT AND
    Label B PRESENT.
    Priority 6 trigger: ``d_reach >= 0.25`` AND none of 3/4/5 (catch-all).
    Priority 7 trigger: ``d_reach < 0.25`` (regardless of label firing).
    """
    # Priority 1.
    drift_halt = next(
        (r for r in corpus_re_anchor if r.halts and r.arm == ARM_A_NULL_V025),
        None,
    )
    if drift_halt is not None:
        return ROLLUP_CORPUS_DRIFT_HALT, LOCKED_PHRASES[ROLLUP_CORPUS_DRIFT_HALT].format(
            version=drift_halt.version
        )

    # Priority 2 sub-conditions a-h.
    if any(r.halts for r in bridge_re_anchor):
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    if a_null_tick50_subverdict != SUBVERDICT_A_NULL_V025_TICK50_PRESENT:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    if b_widened_v025_reachability_tick200 != 0.0:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    if c_reachability_tick400 != C_INSLICE_REACHABILITY_LOCKED:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    if c_tick400_subverdict != SUBVERDICT_C_FOOD_NEAR1_TICK400_PRESENT:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    for key, published in V053L_C_TIER3_ANCHOR_PUBLISHED.items():
        derived = c_tick400_signed_d.get(key)
        if derived is None or math.isnan(derived):
            return (
                ROLLUP_ANCHOR_REPLICATION_HALT,
                LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
            )
        if abs(derived - published) > INSLICE_PAIRED_D_TOLERANCE:
            return (
                ROLLUP_ANCHOR_REPLICATION_HALT,
                LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
            )
    if e_reachability_tick400 != E_INSLICE_REACHABILITY_LOCKED:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    if not e_tick400_subverdict.endswith(E_INSLICE_SUBVERDICT_SUFFIX):
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    for key, published in V053K_C_TIER3_ANCHOR_PUBLISHED.items():
        derived = e_tick400_signed_d.get(key)
        if derived is None or math.isnan(derived):
            return (
                ROLLUP_ANCHOR_REPLICATION_HALT,
                LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
            )
        if abs(derived - published) > INSLICE_PAIRED_D_TOLERANCE:
            return (
                ROLLUP_ANCHOR_REPLICATION_HALT,
                LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
            )

    # Compute D Label A / Label B firing statuses.
    label_a_status, _label_a_wrong = _label_firing_status(d_tick400_label_a_summaries)
    label_b_status, label_b_wrong = _label_firing_status(d_tick400_label_b_summaries)

    # Priority 3: ASYMMETRIC halt — reachability-gated, Label B SPECIFICALLY.
    # D Label A wrong-sign alone does NOT route here.
    if d_reachability_tick400 >= B_REACHABILITY_THRESHOLD and label_b_wrong > 0:
        return (
            ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT,
            LOCKED_PHRASES[ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT],
        )

    # Priority 7: below reachability threshold.
    if d_reachability_tick400 < B_REACHABILITY_THRESHOLD:
        return (
            ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD,
            LOCKED_PHRASES[ROLLUP_MIN_LINEAGE_ACCESS_BELOW_REACHABILITY_THRESHOLD],
        )

    # At this point: d_reach >= 0.25 AND no Label B wrong-sign cells.
    # Priority 5: both labels PRESENT.
    if label_a_status == "PRESENT" and label_b_status == "PRESENT":
        return (
            ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE,
            LOCKED_PHRASES[ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_FULL_BRIDGE],
        )

    # Priority 4: Label B PRESENT AND Label A NOT PRESENT.
    if label_b_status == "PRESENT" and label_a_status == "NOT_PRESENT":
        return (
            ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A,
            LOCKED_PHRASES[ROLLUP_MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A],
        )

    # Priority 6: catch-all (mixed / partial).
    return (
        ROLLUP_MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED,
        LOCKED_PHRASES[ROLLUP_MIN_LINEAGE_ACCESS_PARTIAL_OR_MIXED],
    )


def compute_slice_rollup_verdict(
    *,
    a_null_tick50_subverdict: str,
    d_tick400_label_a_summaries: list[ObservableSummary],
    d_tick400_label_b_summaries: list[ObservableSummary],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    b_widened_v025_reachability_tick200: float,
    c_reachability_tick400: float,
    c_tick400_subverdict: str,
    c_tick400_signed_d: dict[tuple[str, str], float],
    e_reachability_tick400: float,
    e_tick400_subverdict: str,
    e_tick400_signed_d: dict[tuple[str, str], float],
    d_reachability_tick400: float,
) -> tuple[str, str]:
    """Public wrapper around the priority-ordered rollup evaluation."""
    return _evaluate_rollup(
        a_null_tick50_subverdict=a_null_tick50_subverdict,
        d_tick400_label_a_summaries=d_tick400_label_a_summaries,
        d_tick400_label_b_summaries=d_tick400_label_b_summaries,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor,
        b_widened_v025_reachability_tick200=b_widened_v025_reachability_tick200,
        c_reachability_tick400=c_reachability_tick400,
        c_tick400_subverdict=c_tick400_subverdict,
        c_tick400_signed_d=c_tick400_signed_d,
        e_reachability_tick400=e_reachability_tick400,
        e_tick400_subverdict=e_tick400_subverdict,
        e_tick400_signed_d=e_tick400_signed_d,
        d_reachability_tick400=d_reachability_tick400,
    )


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return repr(value)
    return str(value)


def _write_per_lineage_csv(rows: list[PerLineageRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PER_LINEAGE_FIELDNAMES)
        for row in rows:
            d = asdict(row)
            writer.writerow([_format_value(d[name]) for name in PER_LINEAGE_FIELDNAMES])


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0912, PLR0915
    out_dir.mkdir(parents=True, exist_ok=True)

    print(
        "=== v0.53n perception min-lineage sensor_radius_8 audit (5-arm; n_ticks=400 on C/D/E) ==="
    )
    print(f"Arms: {list(ARMS)}")
    print(f"Per-arm n_ticks: {N_TICKS_BY_ARM}")
    print(f"Per-arm body_starting_energy: {BODY_STARTING_ENERGY_BY_ARM}")
    print(f"Per-arm body_base_metabolic_cost: {BODY_BASE_METABOLIC_COST_BY_ARM}")
    print(
        f"Per-arm effective_sensor_radius_override: {BODY_EFFECTIVE_SENSOR_RADIUS_OVERRIDE_BY_ARM}"
    )
    print(f"Per-arm override k: {ARM_OVERRIDE_K}")
    print(
        f"FOOD_NEAR1 layout: "
        f"safe_x=[{FOOD_NEAR1_LAYOUT.safe_x_min},{FOOD_NEAR1_LAYOUT.safe_x_max}], "
        f"hazard_x=[{FOOD_NEAR1_LAYOUT.hazard_x_min},{FOOD_NEAR1_LAYOUT.hazard_x_max}], "
        f"food_x=[{FOOD_NEAR1_LAYOUT.food_x_min},{FOOD_NEAR1_LAYOUT.food_x_max}], "
        f"width={FOOD_NEAR1_LAYOUT.width}"
    )
    print(f"Corpus per arm: A_null over {list(SEEDS_BY_VERSION)}; hazards={HAZARDS}")
    print(
        f"Total runs: {len(ARMS) * sum(len(s) for s in SEEDS_BY_VERSION.values()) * len(HAZARDS)}"
    )
    print()

    captures: list[_RunCapture] = []
    all_rows: list[PerLineageRow] = []
    runs_meta: list[tuple[str, int, int]] = []

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        for arm in ARMS:
            for version, seeds in SEEDS_BY_VERSION.items():
                for hazard in HAZARDS:
                    for seed in seeds:
                        capture = _run_one_arm(arm, version, seed, hazard, runs_root)
                        rows = _aggregate_per_lineage(capture)
                        captures.append(capture)
                        all_rows.extend(rows)
                        if arm == ARM_A_NULL_V025:
                            runs_meta.append((version, seed, hazard))
                        a_lid = next(
                            (r.lineage_id for r in rows if r.is_high_sensor_radius_lineage),
                            None,
                        )
                        print(
                            f"  {arm:<58} {version} h={hazard:>2} seed={seed:>2}  "
                            f"a_top={a_lid}  top1={capture.top1_lineage_id_in_run}  "
                            f"bot1={capture.bottom1_lineage_id_in_run}"
                        )

    print()

    label_pairs_by_window: dict[int, tuple[tuple[str, str], ...]] = {
        TICK_50: (
            (LABEL_A_NAME, LABEL_A_FIELD),
            (LABEL_B_TICK50_NAME, LABEL_B_TICK50_FIELD),
        ),
        TICK_100: (
            (LABEL_A_NAME, LABEL_A_FIELD),
            (LABEL_B_TICK100_NAME, LABEL_B_TICK100_FIELD),
        ),
        TICK_200: (
            (LABEL_A_NAME, LABEL_A_FIELD),
            (LABEL_B_TICK200_NAME, LABEL_B_TICK200_FIELD),
        ),
        TICK_400: (
            (LABEL_A_NAME, LABEL_A_FIELD),
            (LABEL_B_TICK400_NAME, LABEL_B_TICK400_FIELD),
        ),
    }
    primary_observables_by_window: dict[int, tuple[tuple[str, int], ...]] = {
        TICK_50: PRIMARY_OBSERVABLES_TICK50,
        TICK_100: PRIMARY_OBSERVABLES_TICK100,
        TICK_200: PRIMARY_OBSERVABLES_TICK200,
        TICK_400: PRIMARY_OBSERVABLES_TICK400,
    }

    summaries_by_window: dict[int, list[ObservableSummary]] = {w: [] for w in WINDOWS_ALL}
    for window in WINDOWS_ALL:
        arms_for_window = [arm for arm in ARMS if window in WINDOWS_BY_ARM[arm]]
        for arm in arms_for_window:
            for label_name, label_field in label_pairs_by_window[window]:
                for name, sign in primary_observables_by_window[window]:
                    summaries_by_window[window].append(
                        _summarise_observable_for_arm(
                            arm=arm,
                            observable=name,
                            sign=sign,
                            label=label_name,
                            label_field=label_field,
                            all_rows=all_rows,
                            runs=runs_meta,
                        )
                    )

    summaries_by_arm_label: dict[int, dict[tuple[str, str], list[ObservableSummary]]] = {}
    for window, summaries in summaries_by_window.items():
        idx: dict[tuple[str, str], list[ObservableSummary]] = {}
        for s in summaries:
            idx.setdefault((s.arm, s.label), []).append(s)
        summaries_by_arm_label[window] = idx

    a_null_tick50_subverdict = _arm_subverdict_at_window(
        ARM_A_NULL_V025,
        TICK_50,
        summaries_by_arm_label[TICK_50].get((ARM_A_NULL_V025, LABEL_A_NAME), []),
        summaries_by_arm_label[TICK_50].get((ARM_A_NULL_V025, LABEL_B_TICK50_NAME), []),
    )
    descriptive_subverdicts: dict[tuple[str, int], str] = {}
    for arm in ARMS:
        for window in WINDOWS_BY_ARM[arm]:
            if window == TICK_50 and arm == ARM_A_NULL_V025:
                continue
            if window == TICK_400:
                continue
            label_a_summaries = summaries_by_arm_label[window].get((arm, LABEL_A_NAME), [])
            label_b_field_name = label_pairs_by_window[window][1][0]
            label_b_summaries = summaries_by_arm_label[window].get((arm, label_b_field_name), [])
            descriptive_subverdicts[(arm, window)] = _arm_subverdict_at_window(
                arm, window, label_a_summaries, label_b_summaries
            )

    c_tick400_subverdict = _arm_subverdict_at_window(
        ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
        TICK_400,
        summaries_by_arm_label[TICK_400].get(
            (ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400, LABEL_A_NAME), []
        ),
        summaries_by_arm_label[TICK_400].get(
            (ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400, LABEL_B_TICK400_NAME), []
        ),
    )
    d_tick400_label_a = summaries_by_arm_label[TICK_400].get(
        (ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400, LABEL_A_NAME), []
    )
    d_tick400_label_b = summaries_by_arm_label[TICK_400].get(
        (ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400, LABEL_B_TICK400_NAME), []
    )
    d_tick400_subverdict = _arm_subverdict_at_window(
        ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
        TICK_400,
        d_tick400_label_a,
        d_tick400_label_b,
    )
    e_tick400_subverdict = _arm_subverdict_at_window(
        ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
        TICK_400,
        summaries_by_arm_label[TICK_400].get(
            (ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400, LABEL_A_NAME), []
        ),
        summaries_by_arm_label[TICK_400].get(
            (ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400, LABEL_B_TICK400_NAME), []
        ),
    )

    corpus_re_anchor = _check_corpus_re_anchor(all_rows)
    bridge_re_anchor_tick50 = _check_bridge_re_anchor_tick50(summaries_by_arm_label[TICK_50])
    c_inslice_anchor_rows = _check_c_inslice_paired_d_anchor(summaries_by_arm_label[TICK_400])
    e_inslice_anchor_rows = _check_e_inslice_paired_d_anchor(summaries_by_arm_label[TICK_400])

    reachability_by_window: dict[int, dict[str, tuple[float, int]]] = {}
    events_field_by_window: dict[int, str] = {
        TICK_50: "pre50_food_events_count",
        TICK_100: "pre100_food_events_count",
        TICK_200: "pre200_food_events_count",
        TICK_400: "pre400_food_events_count",
    }
    for window in WINDOWS_ALL:
        events_field = events_field_by_window[window]
        reachability_by_window[window] = {}
        for arm in ARMS:
            if window not in WINDOWS_BY_ARM[arm]:
                continue
            reachability_by_window[window][arm] = _compute_arm_reachability_run_share(
                all_rows, arm, events_field
            )

    population_stability = _compute_population_stability(all_rows, captures)
    wrong_sign_cells = _collect_d_tick400_wrong_sign_cells(summaries_by_window[TICK_400])
    c_reach_t400 = reachability_by_window[TICK_400][
        ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400
    ][0]
    d_reach_t400 = reachability_by_window[TICK_400][
        ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400
    ][0]
    e_reach_t400 = reachability_by_window[TICK_400][
        ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400
    ][0]

    c_tick400_signed_d: dict[tuple[str, str], float] = {}
    for key in V053L_C_TIER3_ANCHOR_PUBLISHED:
        label, observable = key
        c_tick400_signed_d[key] = _lookup_signed_d(
            summaries_by_arm_label[TICK_400],
            ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
            label,
            observable,
        )
    e_tick400_signed_d: dict[tuple[str, str], float] = {}
    for key in V053K_C_TIER3_ANCHOR_PUBLISHED:
        label, observable = key
        e_tick400_signed_d[key] = _lookup_signed_d(
            summaries_by_arm_label[TICK_400],
            ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
            label,
            observable,
        )

    rollup_verdict, rollup_phrase = _evaluate_rollup(
        a_null_tick50_subverdict=a_null_tick50_subverdict,
        d_tick400_label_a_summaries=d_tick400_label_a,
        d_tick400_label_b_summaries=d_tick400_label_b,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor_tick50,
        b_widened_v025_reachability_tick200=reachability_by_window[TICK_200][ARM_B_WIDENED_V025][0],
        c_reachability_tick400=c_reach_t400,
        c_tick400_subverdict=c_tick400_subverdict,
        c_tick400_signed_d=c_tick400_signed_d,
        e_reachability_tick400=e_reach_t400,
        e_tick400_subverdict=e_tick400_subverdict,
        e_tick400_signed_d=e_tick400_signed_d,
        d_reachability_tick400=d_reach_t400,
    )

    per_lineage_path = out_dir / "per_run_per_lineage_v053n.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)

    # Audit summary CSV.
    with audit_summary_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "key", "value"])
        for r in corpus_re_anchor:
            for field_name, value in (
                ("derived", r.a_share_h8_derived),
                ("published", r.a_share_h8_published),
                ("drift_abs", r.drift_abs),
                ("n_runs", r.n_runs_contributing),
                ("halts", r.halts),
            ):
                writer.writerow(
                    [
                        "reanchor_a_share_h8",
                        f"{r.arm}/{r.version}/h{r.hazard}/{field_name}",
                        _format_value(value),
                    ]
                )
        for br in bridge_re_anchor_tick50:
            for field_name, value in (
                ("published_signed_d", br.published_signed_d),
                ("derived_signed_d", br.derived_signed_d),
                ("drift_abs", br.drift_abs),
                ("halts", br.halts),
            ):
                writer.writerow(
                    [
                        "bridge_reanchor_tick50",
                        f"{br.label}/{br.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        for cell in c_inslice_anchor_rows:
            for field_name, value in (
                ("published_signed_d", cell.published_signed_d),
                ("derived_signed_d", cell.derived_signed_d),
                ("drift_abs", cell.drift_abs),
                ("halts", cell.halts),
            ):
                writer.writerow(
                    [
                        "inslice_c_anchor_vs_v053l",
                        f"{cell.label}/{cell.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        for cell in e_inslice_anchor_rows:
            for field_name, value in (
                ("published_signed_d", cell.published_signed_d),
                ("derived_signed_d", cell.derived_signed_d),
                ("drift_abs", cell.drift_abs),
                ("halts", cell.halts),
            ):
                writer.writerow(
                    [
                        "inslice_e_anchor_vs_v053k",
                        f"{cell.label}/{cell.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        for window in WINDOWS_ALL:
            section = f"paired_d_tick{window}"
            for s in summaries_by_window.get(window, []):
                for field_name, value in (
                    ("paired_d", s.paired_d),
                    ("signed_d", s.signed_d),
                    ("n_runs", s.n_runs_contributing),
                    ("fires_expected", s.fires_expected),
                    ("fires_wrong", s.fires_wrong),
                ):
                    writer.writerow(
                        [
                            section,
                            f"{s.arm}/{s.label}/{s.observable}/{field_name}",
                            _format_value(value),
                        ]
                    )
        for window in WINDOWS_ALL:
            section = f"reachability_tick{window}"
            for arm, (reach, n) in reachability_by_window.get(window, {}).items():
                writer.writerow([section, f"{arm}/value", _format_value(reach)])
                writer.writerow([section, f"{arm}/n_runs", _format_value(n)])
        for ps in population_stability:
            for field_name, value in (
                ("n_runs_total", ps.n_runs_total),
                ("living_population_run_share", ps.living_population_run_share),
                ("label_a_n_runs", ps.label_a_n_runs),
                ("label_b_n_runs", ps.label_b_n_runs),
            ):
                writer.writerow(
                    [
                        "population_stability",
                        f"{ps.arm}/tick{ps.window}/{field_name}",
                        _format_value(value),
                    ]
                )
        for wsc in wrong_sign_cells:
            for field_name, value in (
                ("paired_d", wsc.paired_d),
                ("signed_d", wsc.signed_d),
                ("n", wsc.n),
            ):
                writer.writerow(
                    [
                        "d_tick400_wrong_sign_cells",
                        f"{wsc.arm}/{wsc.label}/{wsc.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        writer.writerow(["sub_verdicts_tick50", ARM_A_NULL_V025, a_null_tick50_subverdict])
        for (arm, window), sv in sorted(descriptive_subverdicts.items()):
            writer.writerow([f"sub_verdicts_tick{window}", arm, sv])
        writer.writerow(
            [
                "sub_verdicts_tick400",
                ARM_C_WIDENED_FOOD_NEAR1_COMBINED_MAX_LINEAGE_SR8_N400,
                c_tick400_subverdict,
            ]
        )
        writer.writerow(
            [
                "sub_verdicts_tick400",
                ARM_D_WIDENED_FOOD_NEAR1_COMBINED_MIN_LINEAGE_SR8_N400,
                d_tick400_subverdict,
            ]
        )
        writer.writerow(
            [
                "sub_verdicts_tick400",
                ARM_E_WIDENED_FOOD_NEAR1_COMBINED_MODELWIDE_SR8_N400,
                e_tick400_subverdict,
            ]
        )
        writer.writerow(["rollup_verdict", "verdict", rollup_verdict])
        writer.writerow(["rollup_verdict", "locked_phrase", rollup_phrase])

    # Audit log txt.
    lines: list[str] = []
    lines.append(
        "=== v0.53n perception min-lineage sensor_radius_8 audit "
        "(5-arm; n_ticks=400 on C/D/E) ===\n"
    )
    lines.append(f"\nA_null_V0_25 tick-50 sub-verdict (anchor): {a_null_tick50_subverdict}\n")
    lines.append(f"C tick-400 sub-verdict (in-slice anchor): {c_tick400_subverdict}\n")
    lines.append(f"D tick-400 sub-verdict (verdict-gating): {d_tick400_subverdict}\n")
    lines.append(f"E tick-400 sub-verdict (in-slice anchor): {e_tick400_subverdict}\n")
    lines.append(f"\nD reachability tick-400: {d_reach_t400}\n")
    lines.append(f"C reachability tick-400: {c_reach_t400}\n")
    lines.append(f"E reachability tick-400: {e_reach_t400}\n")
    lines.append(f"\nRollup verdict: {rollup_verdict}\n")
    lines.append(f'Locked phrase fired: "{rollup_phrase}"\n')
    audit_log_path.write_text("".join(lines))

    print(f"\nA_null_V0_25 tick-50 sub-verdict (anchor): {a_null_tick50_subverdict}")
    print(f"C tick-400 sub-verdict (in-slice anchor): {c_tick400_subverdict}")
    print(f"D tick-400 sub-verdict (verdict-gating): {d_tick400_subverdict}")
    print(f"E tick-400 sub-verdict (in-slice anchor): {e_tick400_subverdict}")
    print(f"\nRollup verdict: {rollup_verdict}")
    print(f'Locked phrase: "{rollup_phrase}"')
    print()
    print(f"Wrote {per_lineage_path}")
    print(f"Wrote {audit_summary_path}")
    print(f"Wrote {audit_log_path}")

    if rollup_verdict in {
        ROLLUP_CORPUS_DRIFT_HALT,
        ROLLUP_ANCHOR_REPLICATION_HALT,
        ROLLUP_MIN_LINEAGE_LABEL_B_OPPOSITE_SIGN_HALT,
    }:
        raise V053nReducerError(rollup_phrase)
    return rollup_verdict, rollup_phrase


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "v0.53n perception min-lineage sensor_radius_8 audit (5-arm; n_ticks=400 on C/D/E)"
        )
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.53n-perception-min-lineage-sensor-radius-8"),
        help=(
            "Directory for v0.53n outputs "
            "(default: runs/v0.53n-perception-min-lineage-sensor-radius-8)."
        ),
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
