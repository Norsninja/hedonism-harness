"""v0.53i geometry calibration probe — post-hazard food distance reduced by
two columns (``FOOD_NEAR2``) on ``widened_gradient`` x V0_25 x combined
founder-budget envelope at ``n_ticks=400``.

Pre-reg: [[docs/experiments/fear_hunger_v0.53i.md]]. Question: with the
combined-budget envelope (``BodyConfig(starting_energy=100.0,
base_metabolic_cost=0.10)``) AND ``n_ticks=400`` held identical to v0.53h C,
and the food band slid two columns left (from ``x in [10,14]`` under
``widened_gradient`` to ``x in [8,12]`` under a script-local
``widened_food_near2`` layout -- corridor removed; hazard band, food width,
spawn position, safe band, height all preserved), does C reachability cross
0.25 at tick-400?

Corpus (locked, identical shape to v0.53..v0.53h): A_null arm only across
v0.42 / v0.43R / v0.44 / v0.45, hazards {0, 8}, seeds 41..72. 64 runs per arm;
3 arms (asymmetric layout AND BodyConfig AND ``n_ticks``); 192 runs total.

Arms (locked, 3 -- asymmetric layout AND BodyConfig AND ``n_ticks``):
  A_null_V0_25:                          tight_gradient   + body_config=None  + n_ticks=200
  B_widened_V0_25:                       widened_gradient + body_config=None  + n_ticks=200
  C_widened_food_near2_combined_N400:    <script-local widened_food_near2> +
      body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10) +
      n_ticks=400

The C layout is constructed script-local (NOT in ``layouts.py``) at module
load:
  WIDENED_FOOD_NEAR2_LAYOUT = ChamberLayout(
      safe_x_min=0, safe_x_max=4,
      hazard_x_min=5, hazard_x_max=7,
      food_x_min=8, food_x_max=12,
      height=6, spawn_x=1,
  )

Primary observables (locked, 3, computed at four windows on C, three on A/B):
  pre{50,100,200}_food_events_count                      (+) on A/B/C
  pre400_food_events_count                               (+) on C only
  pre{50,100,200}_food_energy_acquired                   (+) on A/B/C
  pre400_food_energy_acquired                            (+) on C only
  mean_distance_to_nearest_food_cell_tick{50,100,200}    (-) on A/B/C
  mean_distance_to_nearest_food_cell_tick400             (-) on C only

Tick-50 cells anchor v0.48..v0.53h (Tier-1 priority 2.a). Tick-100 / tick-200
cells are descriptive on A/B and descriptive cross-slice anchors on C. The
tick-400 panel on C is verdict-gating.

Labels:
  Label A:           high_sensor_radius_lineage. Trait-resolved (identical to v0.48..v0.53h).
  Label B (tick-50): high_tick50_readiness_fraction_lineage  — Tier-1 anchor only.
  Label B (tick-100): high_tick100_readiness_fraction_lineage — descriptive.
  Label B (tick-200): high_tick200_readiness_fraction_lineage — descriptive.
  Label B (tick-400): high_tick400_readiness_fraction_lineage — verdict-gating; C only,
                                                                 NaN-broadcast on A/B.

Effect-size rule (locked, sign-aware, identical to v0.48..v0.53h):
  signed_d = paired_d * expected_sign
  fires_expected iff signed_d >= +0.5
  fires_wrong    iff signed_d <= -0.5

Anchor stack (locked, 3-tier — NO Tier-3 in v0.53i):
  Tier-1 (priority 2.a): A_null_V0_25 tick-50 six v0.48 cells drift <= 1e-3.
  Priority 2.b:          A_null_V0_25 tick-50 sub-verdict == PRESENT.
  Tier-2 (priority 2.c): b_widened_v025_reachability_run_share_tick_200 == 0.0 exactly.

Verdict-gating reachability (locked, pre-data):
  c_widened_food_near2_combined_N400_reachability_run_share_tick_400  vs threshold 0.25.

Per-arm tick-400 sub-verdicts on C (locked, 4-way — verdict-gating):
  C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_{PRESENT, PARTIAL, NOT_FOUND, OPPOSITE_SIGN_HALT}
A/B tick-{50,100,200} and C tick-{50,100,200} sub-verdicts are computed
descriptively (priority-2.b / cross-slice anchors); only C tick-400 gates the
verdict.

Slice rollup (locked, 6 outcomes, priority-ordered — PRIORITY 3 IS
REACHABILITY-GATED on C tick-400):
  1. CORPUS_REDERIVE_DRIFT_HALT
  2. ANCHOR_REPLICATION_HALT  (Tier-1 + 2.b + Tier-2 — NO Tier-3 in v0.53i)
  3. GEOMETRY_OPPOSITE_SIGN_HALT  (gates on C tick-400 sub-verdict + reach >= 0.25)
  4. WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2
        (C tick-400 reach >= 0.25 AND C tick-400 sub-verdict = PRESENT)
  5. WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2
        (C tick-400 reach < 0.25)
  6. WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2
        (C tick-400 reach >= 0.25 AND C tick-400 sub-verdict in {PARTIAL, NOT_FOUND})

When C tick-400 sub-verdict = OPPOSITE_SIGN_HALT AND C tick-400 reach < 0.25:
priority 3 SKIPS; rollup falls through to priority 5; the wrong-sign cell(s)
are logged descriptively in audit_summary.csv under
``wrong_sign_cells_under_reachability_below_threshold``.

Conservation framing: zero ``src/`` modifications. ``ChamberLayout`` is
constructed script-local (NOT added to ``layouts.py``). ``n_ticks`` is
already a ``run_chamber()`` parameter (default 200); v0.53e's
``body_config: BodyConfig | None = None`` seam carries forward; the existing
``layout: ChamberLayout | None = None`` parameter accepts the script-local
instance directly.

Usage:
    uv run python scripts/v0_53i_geometry_food_near2_audit.py
    uv run python scripts/v0_53i_geometry_food_near2_audit.py \
        --out-dir runs/v0.53i-geometry-food-near2
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
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
from hedonism_harness.core.traits import TraitConfig
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
# Locked configuration (pre-reg)
# ---------------------------------------------------------------------------

SEEDS_BY_VERSION: dict[str, tuple[int, ...]] = {
    "v0.42": tuple(range(41, 49)),
    "v0.43R": tuple(range(49, 57)),
    "v0.44": tuple(range(57, 65)),
    "v0.45": tuple(range(65, 73)),
}

HAZARDS: tuple[int, ...] = (0, 8)
N_TICKS_AB: int = 200  # A and B horizon (V0_25 baseline)
N_TICKS_C: int = 400  # C horizon (carried forward from v0.53h)
N_FOUNDERS: int = 5
TICK_50: int = 50
TICK_100: int = 100
TICK_200: int = 200
TICK_400: int = 400

# Windows (locked, ordered).
WINDOWS_AB: tuple[int, ...] = (TICK_50, TICK_100, TICK_200)
WINDOWS_C: tuple[int, ...] = (TICK_50, TICK_100, TICK_200, TICK_400)
WINDOWS_ALL: tuple[int, ...] = (TICK_50, TICK_100, TICK_200, TICK_400)

# Arms (locked, 3 — asymmetric layout AND BodyConfig AND n_ticks).
ARM_A_NULL_V025: str = "A_null_V0_25"
ARM_B_WIDENED_V025: str = "B_widened_V0_25"
ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: str = "C_widened_food_near2_combined_N400"
ARMS: tuple[str, ...] = (
    ARM_A_NULL_V025,
    ARM_B_WIDENED_V025,
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400,
)

# ---------------------------------------------------------------------------
# Script-local layout for the C arm (NOT added to layouts.py per pre-reg
# Conservation framing — preserves v0.52b-tip layouts.py byte-identity).
# ---------------------------------------------------------------------------
WIDENED_FOOD_NEAR2_LAYOUT: ChamberLayout = ChamberLayout(
    safe_x_min=0,
    safe_x_max=4,
    hazard_x_min=5,
    hazard_x_max=7,
    food_x_min=8,
    food_x_max=12,
    height=6,
    spawn_x=1,
)

LAYOUT_NAME_BY_ARM: dict[str, str] = {
    ARM_A_NULL_V025: "tight_gradient",
    ARM_B_WIDENED_V025: "widened_gradient",
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: "widened_food_near2",
}

# Per-arm n_ticks (locked).
N_TICKS_BY_ARM: dict[str, int] = {
    ARM_A_NULL_V025: N_TICKS_AB,
    ARM_B_WIDENED_V025: N_TICKS_AB,
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: N_TICKS_C,
}

# Per-arm windows (locked).
WINDOWS_BY_ARM: dict[str, tuple[int, ...]] = {
    ARM_A_NULL_V025: WINDOWS_AB,
    ARM_B_WIDENED_V025: WINDOWS_AB,
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: WINDOWS_C,
}

# V0_25 baseline substrate constants (preserved on all three arms).
V0_25_ENERGY_POOL_INITIAL: float = 1500.0
V0_25_FOOD_RESPAWN_COOLDOWN: int = 50
V0_25_AMBIENT_INFLUX_RATE: float = 1.0  # baseline (preserved on ALL arms in v0.53i).
V0_25_BODY_STARTING_ENERGY: float = 60.0  # default BodyConfig().starting_energy
V0_25_BODY_BASE_METABOLIC_COST: float = 0.25  # default BodyConfig().base_metabolic_cost
STARTING_ENERGY_100_DOSE: float = 100.0  # v0.53e/g/h test dose (carried forward into v0.53i C)
BASE_METABOLIC_COST_010_DOSE: float = 0.10  # v0.53f/g/h test dose (carried forward into v0.53i C)

# Per-arm body_starting_energy override (locked).
BODY_STARTING_ENERGY_BY_ARM: dict[str, float] = {
    ARM_A_NULL_V025: V0_25_BODY_STARTING_ENERGY,
    ARM_B_WIDENED_V025: V0_25_BODY_STARTING_ENERGY,
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: STARTING_ENERGY_100_DOSE,
}

# Per-arm body_base_metabolic_cost override (locked).
BODY_BASE_METABOLIC_COST_BY_ARM: dict[str, float] = {
    ARM_A_NULL_V025: V0_25_BODY_BASE_METABOLIC_COST,
    ARM_B_WIDENED_V025: V0_25_BODY_BASE_METABOLIC_COST,
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: BASE_METABOLIC_COST_010_DOSE,
}


def _layout_for_arm(arm: str) -> ChamberLayout:
    if arm == ARM_A_NULL_V025:
        return tight_gradient_layout()
    if arm == ARM_B_WIDENED_V025:
        return widened_gradient_layout()
    if arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
        return WIDENED_FOOD_NEAR2_LAYOUT
    msg = f"v0.53i: unknown arm {arm!r}"
    raise V053iReducerError(msg)


def _body_config_for_arm(arm: str) -> BodyConfig | None:
    """Per-arm BodyConfig override.

    A and B return ``None`` (default ``BodyConfig()`` fallback in run_chamber,
    base_metabolic_cost=0.25, starting_energy=60.0). C returns
    ``BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)`` — identical
    to v0.53g/h C; v0.53i's only delta from v0.53h is the ``layout`` (script-
    local ``widened_food_near2``). All other BodyConfig fields preserved at
    default (max_energy=100.0, starting_health=100.0, max_health=100.0,
    sensor_radius_metabolic_cost=0.05, effective_sensor_radius_override=None).
    """
    if arm in (ARM_A_NULL_V025, ARM_B_WIDENED_V025):
        return None
    if arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
        return BodyConfig(
            starting_energy=STARTING_ENERGY_100_DOSE,
            base_metabolic_cost=BASE_METABOLIC_COST_010_DOSE,
        )
    msg = f"v0.53i: unknown arm {arm!r}"
    raise V053iReducerError(msg)


# Hardcoded re-anchor reference values (A_null_V0_25 arm only; corpus Tier-1).
PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,  # informational only
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5
B_REACHABILITY_THRESHOLD: float = 0.25

EXPECTED_FOUNDERS: int = 5

# Primary observables — four windows, three observable types each.
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

# Label fields and names.
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

# v0.48..v0.53h published bridge cells (label, observable) -> signed_d.
# Tier-1 anchor at tick-50 only.
V048_PUBLISHED_SIGNED_D: dict[tuple[str, str], float] = {
    (LABEL_A_NAME, "pre50_food_events_count"): +1.066,
    (LABEL_A_NAME, "pre50_food_energy_acquired"): +1.066,
    (LABEL_A_NAME, "mean_distance_to_nearest_food_cell_tick50"): +1.916,
    (LABEL_B_TICK50_NAME, "pre50_food_events_count"): +0.916,
    (LABEL_B_TICK50_NAME, "pre50_food_energy_acquired"): +0.916,
    (LABEL_B_TICK50_NAME, "mean_distance_to_nearest_food_cell_tick50"): +1.179,
}

# Per-arm sub-verdicts (locked) for tick-{50,100,200} on A/B/C plus tick-400 on C.
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

SUBVERDICT_C_FOOD_NEAR2_TICK50_PRESENT = "C_WIDENED_FOOD_NEAR2_TICK50_BRIDGE_PRESENT"
SUBVERDICT_C_FOOD_NEAR2_TICK50_PARTIAL = "C_WIDENED_FOOD_NEAR2_TICK50_BRIDGE_PARTIAL"
SUBVERDICT_C_FOOD_NEAR2_TICK50_NOT_FOUND = "C_WIDENED_FOOD_NEAR2_TICK50_BRIDGE_NOT_FOUND"
SUBVERDICT_C_FOOD_NEAR2_TICK50_OPPOSITE = "C_WIDENED_FOOD_NEAR2_TICK50_OPPOSITE_SIGN_HALT"

SUBVERDICT_C_FOOD_NEAR2_TICK100_PRESENT = "C_WIDENED_FOOD_NEAR2_TICK100_BRIDGE_PRESENT"
SUBVERDICT_C_FOOD_NEAR2_TICK100_PARTIAL = "C_WIDENED_FOOD_NEAR2_TICK100_BRIDGE_PARTIAL"
SUBVERDICT_C_FOOD_NEAR2_TICK100_NOT_FOUND = "C_WIDENED_FOOD_NEAR2_TICK100_BRIDGE_NOT_FOUND"
SUBVERDICT_C_FOOD_NEAR2_TICK100_OPPOSITE = "C_WIDENED_FOOD_NEAR2_TICK100_OPPOSITE_SIGN_HALT"

SUBVERDICT_C_FOOD_NEAR2_TICK200_PRESENT = "C_WIDENED_FOOD_NEAR2_TICK200_BRIDGE_PRESENT"
SUBVERDICT_C_FOOD_NEAR2_TICK200_PARTIAL = "C_WIDENED_FOOD_NEAR2_TICK200_BRIDGE_PARTIAL"
SUBVERDICT_C_FOOD_NEAR2_TICK200_NOT_FOUND = "C_WIDENED_FOOD_NEAR2_TICK200_BRIDGE_NOT_FOUND"
SUBVERDICT_C_FOOD_NEAR2_TICK200_OPPOSITE = "C_WIDENED_FOOD_NEAR2_TICK200_OPPOSITE_SIGN_HALT"

SUBVERDICT_C_FOOD_NEAR2_TICK400_PRESENT = "C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PRESENT"
SUBVERDICT_C_FOOD_NEAR2_TICK400_PARTIAL = "C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_PARTIAL"
SUBVERDICT_C_FOOD_NEAR2_TICK400_NOT_FOUND = "C_WIDENED_FOOD_NEAR2_TICK400_BRIDGE_NOT_FOUND"
SUBVERDICT_C_FOOD_NEAR2_TICK400_OPPOSITE = "C_WIDENED_FOOD_NEAR2_TICK400_OPPOSITE_SIGN_HALT"

# Slice rollup verdicts (locked, priority-ordered).
ROLLUP_CORPUS_DRIFT_HALT = "CORPUS_REDERIVE_DRIFT_HALT"
ROLLUP_ANCHOR_REPLICATION_HALT = "ANCHOR_REPLICATION_HALT"
ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT = "GEOMETRY_OPPOSITE_SIGN_HALT"
ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2 = "WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2"
ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2 = (
    "WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2"
)
ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2 = (
    "WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2"
)

# Locked phrases (verbatim per pre-reg).
LOCKED_PHRASES: dict[str, str] = {
    ROLLUP_CORPUS_DRIFT_HALT: (
        "Halt: A_null_V0_25 re-anchor drifted from the published Results value for "
        "{version}; v0.53i's deterministic re-execution of the V0_25 corpus does not "
        "reproduce the published metric within 1e-3."
    ),
    ROLLUP_ANCHOR_REPLICATION_HALT: (
        "Halt: v0.53i's A_null_V0_25 arm does not reproduce v0.48–v0.53h's "  # noqa: RUF001
        "tick-50 spatial bridge, OR v0.53i's B_widened_V0_25 arm does not "
        "reproduce v0.53c–v0.53h's `0/64` reachability lock at tick-200. "  # noqa: RUF001
        "v0.53i cannot interpret the C_widened_food_near2_combined_N400 cells "
        "without an established baseline on the V0_25 substrate."
    ),
    ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT: (
        "Halt: a v0.53i C_widened_food_near2_combined_N400 tick-400 spatial / "
        "foraging primary fires in the WRONG direction under a gating label, AND "
        "C reachability at tick-400 clears the locked 25% threshold (so the bridge "
        "framework is meaningful at this measurement). The geometric intervention "
        "(post-hazard food distance reduced by two columns; food band moved from "
        "`x∈[10,14]` to `x∈[8,12]`) under the v0.53g/h combined founder-facing "
        "budget envelope (`BodyConfig.starting_energy = 100.0` AND "
        "`BodyConfig.base_metabolic_cost = 0.10`) at `n_ticks = 400` surfaces a "
        "regime where the locked expected signs do not hold under measurable food "
        "access. The reachability-gated trigger preserves v0.53e's locked sign "
        "discipline while excluding the v0.53e-style measurement-edge case "
        "(wrong-sign at reachability=0)."
    ),
    ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2: (
        "On the modern A_null corpus with the V0_25 substrate held constant except "
        "for the combined founder-facing budget relaxation "
        "`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the "
        "simulation horizon doubled to `n_ticks=400` AND the post-hazard food "
        "distance reduced by two columns (food band moved from `x∈[10,14]` under "
        "`widened_gradient` to `x∈[8,12]` under the script-local "
        "`widened_food_near2` layout; corridor removed; hazard band, food width, "
        "spawn position, safe band, and chamber height preserved), the v0.48 "
        "sensor_radius spatial / foraging bridge fires PRESENT under the locked "
        "+0.5 paired_d threshold at tick-400. The geometry/substrate cell that "
        "v0.53c locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, "
        "v0.53d locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, "
        "v0.53e locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, "
        "v0.53g locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and "
        "v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` "
        "admits a measurable bridge under the geometric intervention: "
        "B_widened_V0_25 reachability remains `0/64` at tick-200 (predecessor "
        "lock holds), C reachability at tick-400 clears the locked 25% threshold, "
        "and ≥ 2/3 spatial / foraging primaries fire PRESENT under both gating "
        "labels at the tick-400 panel. Reducing post-hazard food distance by two "
        "columns is sufficient to restore measurable reachability and bridge "
        "expression under the combined-budget envelope at `n_ticks=400` on the "
        "V0_25 substrate. The v0.53c–v0.53h reachability ceiling is lifted by "  # noqa: RUF001
        "reducing post-hazard food distance under the tested envelope; this "
        "does NOT prove `geometry solved` — only that this specific 2-column "
        "reduction is sufficient under the tested envelope: "
        "`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`."
    ),
    ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2: (
        "On the modern A_null corpus with the V0_25 substrate held constant except "
        "for the combined founder-facing budget relaxation "
        "`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the "
        "simulation horizon doubled to `n_ticks=400` AND the post-hazard food "
        "distance reduced by two columns (food band moved from `x∈[10,14]` under "
        "`widened_gradient` to `x∈[8,12]` under the script-local "
        "`widened_food_near2` layout; corridor removed; hazard band, food width, "
        "spawn position, safe band, and chamber height preserved), fewer than "
        "25% of C runs have any founder lineage with pre400 food events. C's "
        "reachability is below the locked 25% threshold at tick-400; the "
        "geometry/substrate cell that v0.53c locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e "
        "locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, "
        "v0.53g locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and "
        "v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` "
        "remains below the reachability threshold under the geometric "
        "intervention. The bridge is not rescued by reducing post-hazard food "
        "distance by two columns under V0_25 × `widened_gradient`-shape × "  # noqa: RUF001
        "combined-budget envelope × `n_ticks=400`; the tested 2-column "  # noqa: RUF001
        "reduction does NOT prove `geometry irrelevant` or `corridor removal "
        "proves distance was not the problem` — only that this specific "
        "intervention does not lift reachability under the tested envelope. "
        "v0.53j (or later) candidates shift toward policy / hazard-avoidance "
        "dynamics, hazard-band traversal mechanics, or larger geometric "
        "perturbations (e.g., further food-near, reduced hazard thickness, or "
        "alternative spawn position): "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2`."
    ),
    ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2: (
        "On the modern A_null corpus with the V0_25 substrate held constant except "
        "for the combined founder-facing budget relaxation "
        "`BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` AND the "
        "simulation horizon doubled to `n_ticks=400` AND the post-hazard food "
        "distance reduced by two columns (food band moved from `x∈[10,14]` under "
        "`widened_gradient` to `x∈[8,12]` under the script-local "
        "`widened_food_near2` layout), C's reachability clears the locked 25% "
        "threshold at tick-400 but the v0.48 sensor_radius spatial / foraging "
        "bridge does not fully fire PRESENT — fewer than 2/3 primaries fire "
        "across both gating labels at tick-400 under the strict NaN rule. The "
        "geometry/substrate cell that v0.53c locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`, v0.53d locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`, v0.53e "
        "locked as `RELAXED_OPPOSITE_SIGN_HALT`, v0.53f locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`, "
        "v0.53g locked as "
        "`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`, and "
        "v0.53h locked as `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` "
        "is partially rescued under the geometric intervention: reachability "
        "becomes measurable but the bridge does not fully replicate. "
        "Layout-specific partial-rescue logged in Results: "
        "`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2`."
    ),
}


class V053iReducerError(Exception):
    """Halt condition raised when a v0.53i invariant is violated."""


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
    """Per-founder snapshot for the v0.53i audit (read-only).

    Captures founder ``body.energy`` AND the model-level
    ``body_config.starting_energy`` AND ``body_config.base_metabolic_cost``
    at setup_observer time (read-only). Used by Test #5 to verify BOTH knobs
    of the ``body_config`` seam took effect at config-time founder
    construction.
    """

    lineage_id: int
    founder_index: int
    founder_sensor_radius: int
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    founder_body_energy_tick0: float
    founder_body_starting_energy_tick0: float
    founder_body_base_metabolic_cost_tick0: float


@dataclass
class _RunCapture:
    arm: str
    layout_name: str
    # Layout geometry captured per-arm from the actual ChamberLayout instance
    # used in run_chamber. Populated in _run_one_arm; written per-row in CSV.
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
    n_ticks: int
    version: str
    seed: int
    hazard: int
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
    # pre400 buckets are only accumulated on the C arm (n_ticks=400 horizon).
    pre400_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre400_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre400_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    n_observer_fires: int = 0
    energy_threshold: float = 0.0
    min_age: int = 0
    # Population stability (set during aggregate_per_lineage from tick_records).
    living_population_by_window: dict[int, bool] = field(default_factory=dict)
    # Final tick reached (read after run_chamber returns via tick observer).
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
            f"v0.53i: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V053iReducerError(msg)
    return candidates[0]


# ---------------------------------------------------------------------------
# Founder audit (read-only — no patch)
# ---------------------------------------------------------------------------


def _capture_founder_audit(model: HHModel, capture: _RunCapture) -> None:
    """Capture per-founder traits read-only at setup_observer time. No patch."""
    founders = sorted(model.agents, key=lambda a: int(a.body.lineage_id))
    if len(founders) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.53i invariant: expected exactly {EXPECTED_FOUNDERS} founders "
            f"at setup_observer time; got {len(founders)}"
        )
        raise V053iReducerError(msg)
    body_starting_energy = float(model.body_config.starting_energy)
    body_base_metabolic_cost = float(model.body_config.base_metabolic_cost)
    for i, agent in enumerate(founders):
        traits = agent.body.traits
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
            )
        )


def _assert_layout_invariant(model: HHModel, arm: str) -> None:
    """Assert the constructed model's world dimensions match the arm's layout."""
    expected = _layout_for_arm(arm)
    actual_width = int(model.world.width)
    actual_height = int(model.world.height)
    if actual_width != expected.width or actual_height != expected.height:
        msg = (
            f"v0.53i layout invariant violated for arm {arm!r}: "
            f"expected (width={expected.width}, height={expected.height}); "
            f"got (width={actual_width}, height={actual_height})"
        )
        raise V053iReducerError(msg)


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


def _make_setup_observer(  # noqa: PLR0915 — pre400 listeners for asymmetric horizon
    arm: str,
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    """setup_observer factory: read-only founder audit, listeners, layout
    invariant, tick 0 capture.

    On A and B, the AteFood / HazardDamageApplied listeners accumulate pre50 /
    pre100 / pre200 rollups (through tick-200, the arm's horizon). On C they
    additionally accumulate pre400 rollups (through tick-400, C's doubled
    horizon). The pre400 buckets remain empty on A and B by construction
    (their loops terminate at tick-200; downstream NaN-broadcast on output).
    """
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

        # AgentBorn listener: lineage tracking only.
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
            # pre400 only accumulates on the C arm (arm_horizon == 400).
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

        # Layout invariant: read back world dimensions and assert match.
        _assert_layout_invariant(model, arm)

        _capture_tick_record(model, tick_label=0, capture=capture)

    return setup


def _make_per_tick_observer(arm: str, capture: _RunCapture) -> Callable[[HHModel], None]:
    """Per-tick observer: tick records + readiness snapshots at window ticks.

    Window ticks for A/B: 50/100/200. For C: 50/100/200/400. Also records the
    last observed model.tick_count into capture.final_tick_count so test #5
    can assert horizon propagation after run_chamber returns (model is local
    to run_chamber and not exposed otherwise).
    """
    arm_horizon = N_TICKS_BY_ARM[arm]

    def observer(model: HHModel) -> None:  # noqa: PLR0912 — adds tick-400 readiness branch
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


def _run_one_arm(  # noqa: PLR0915 — script-local layout AND asymmetric n_ticks vs v0.53h
    arm: str, version: str, seed: int, hazard: int, runs_root: Path
) -> _RunCapture:
    """Execute one (arm, version, seed, hazard) run, returning its capture.

    A and B run to ``n_ticks=200`` with default ``BodyConfig()`` and library
    layouts. C runs to ``n_ticks=400`` with
    ``body_config=BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)``
    AND the script-local ``WIDENED_FOOD_NEAR2_LAYOUT`` (food band slid 2
    columns left vs widened_gradient).
    """
    if arm not in ARMS:
        msg = f"v0.53i: unknown arm {arm!r}"
        raise V053iReducerError(msg)
    base_arm = _select_a_null_arm(version, hazard)
    layout = _layout_for_arm(arm)
    layout_name = LAYOUT_NAME_BY_ARM[arm]
    arm_body_config = _body_config_for_arm(arm)
    arm_starting_energy = BODY_STARTING_ENERGY_BY_ARM[arm]
    arm_base_metabolic_cost = BODY_BASE_METABOLIC_COST_BY_ARM[arm]
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
        # Layout geometry read directly from the actual ChamberLayout instance
        # passed to run_chamber (not hardcoded — matches the per-arm contract).
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
            f"v0.53i: base arm must be A_null only; got "
            f"intervention_kind={base_arm.intervention_kind!r}"
        )
        raise V053iReducerError(msg)

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
            use_memory=use_memory,
            memory_type=memory_type,
            food_respawn_cooldown=base_arm.food_respawn_cooldown,
            energy_pool_initial=base_arm.energy_pool_initial,
            ambient_influx_rate=base_arm.ambient_influx_rate,
            child_funding_mode=base_arm.child_funding_mode,
            hazard_damage=base_arm.hazard_damage,
            hazard_avoidance_weight=base_arm.hazard_avoidance_weight,
            condition=f"v0.53i-{arm}-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_per_tick_observer(arm, capture),
            optional_intervention=optional_intervention,
        )
    finally:
        for disconnect in disconnects:
            disconnect()

    # Tick records cover a contiguous prefix [0, last_tick] with last_tick <=
    # arm_n_ticks; tick-0 always exists. Readiness lists may be empty if
    # extinction occurred before the snapshot tick.
    max_expected_ticks = arm_n_ticks + 1
    if len(capture.tick_records) < 1 or len(capture.tick_records) > max_expected_ticks:
        msg = (
            f"v0.53i invariant: per-tick observer must capture between 1 and "
            f"{max_expected_ticks} ticks for {run_id}; got {len(capture.tick_records)}"
        )
        raise V053iReducerError(msg)
    if 0 not in capture.tick_records:
        msg = f"v0.53i invariant: missing tick-0 record for {run_id}"
        raise V053iReducerError(msg)
    captured_ticks = sorted(capture.tick_records.keys())
    if captured_ticks != list(range(captured_ticks[0], captured_ticks[-1] + 1)):
        msg = (
            f"v0.53i invariant: tick records must be a contiguous prefix for "
            f"{run_id}; got non-contiguous ticks {captured_ticks}"
        )
        raise V053iReducerError(msg)
    if len(capture.founder_records) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.53i invariant: expected exactly {EXPECTED_FOUNDERS} founder records for "
            f"{run_id}; got {len(capture.founder_records)}"
        )
        raise V053iReducerError(msg)

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
    # pre400 cells: int on C, NaN-broadcast on A/B (stored as float for unified column).
    pre400_food_events_count: float
    pre400_food_energy_acquired: float
    mean_distance_to_nearest_food_cell_tick50: float
    mean_distance_to_nearest_food_cell_tick100: float
    mean_distance_to_nearest_food_cell_tick200: float
    mean_distance_to_nearest_food_cell_tick400: float  # NaN on A/B
    tick50_living_count: int
    tick50_above_threshold_count: int
    tick50_above_threshold_fraction: float
    tick100_living_count: int
    tick100_above_threshold_count: int
    tick100_above_threshold_fraction: float
    tick200_living_count: int
    tick200_above_threshold_count: int
    tick200_above_threshold_fraction: float
    # tick-400 cells: int on C, NaN-broadcast on A/B (float column for unified output).
    tick400_living_count: float
    tick400_above_threshold_count: float
    tick400_above_threshold_fraction: float
    b50_count: int
    is_eventual_top_b50_label: bool
    is_high_sensor_radius_lineage: bool
    is_high_tick50_readiness_fraction_lineage: bool
    is_high_tick100_readiness_fraction_lineage: bool
    is_high_tick200_readiness_fraction_lineage: bool
    # Computed only on C arm; NaN-broadcast on A/B (Optional[bool]).
    is_high_tick400_readiness_fraction_lineage: object  # bool | float (NaN on A/B)


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
    """Per-lineage mean distance to nearest food cell, averaged over the
    living-agent means from tick 0 through ``last_tick`` (inclusive)."""
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


def _select_sensor_radius_label(
    sensor_radius_by_lineage: dict[int, int],
) -> int | None:
    """argmax(sensor_radius), tiebreak min(lineage_id)."""
    if not sensor_radius_by_lineage:
        return None
    best_lid: int | None = None
    best_value = float("-inf")
    for lid in sorted(sensor_radius_by_lineage):
        v = float(sensor_radius_by_lineage[lid])
        if v > best_value:
            best_value = v
            best_lid = lid
    return best_lid


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
    """Compute Label B candidate at a given tick. Returns
    (selected_lineage_id, living_count_by_lineage, above_count_by_lineage,
    fraction_by_lineage)."""
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


def _aggregate_per_lineage(  # noqa: PLR0912, PLR0915 — pre400 / tick-400 aggregation on C
    capture: _RunCapture,
) -> list[PerLineageRow]:
    all_lineages = sorted(set(capture.lineage_by_agent.values()))
    is_c_arm = capture.arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400

    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.53i: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V053iReducerError(msg)
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
    # tick-400 readiness label only computed on C; NaN-broadcast on A/B.
    if is_c_arm:
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
    sensor_label = _select_sensor_radius_label(sensor_radius_by_lineage)

    distance_by_lineage_tick50 = _per_tick_lineage_distance_means(capture, TICK_50)
    distance_by_lineage_tick100 = _per_tick_lineage_distance_means(capture, TICK_100)
    distance_by_lineage_tick200 = _per_tick_lineage_distance_means(capture, TICK_200)
    if is_c_arm:
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
        if is_c_arm:
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
        # pre400 cells: int values on C, NaN-broadcast on A/B.
        if is_c_arm:
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
            high_tick400_label_val = float("nan")  # NaN-broadcast on A/B
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
    # The C-only Label B tick-400 column carries NaN on A/B rows. Treat any
    # NaN flag as "this row is not the label" (skipped).
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


# Per-arm tick-50 sub-verdict tables (descriptive on B/C; priority-2.b on A).
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
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: (
        SUBVERDICT_C_FOOD_NEAR2_TICK50_PRESENT,
        SUBVERDICT_C_FOOD_NEAR2_TICK50_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR2_TICK50_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR2_TICK50_OPPOSITE,
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
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: (
        SUBVERDICT_C_FOOD_NEAR2_TICK100_PRESENT,
        SUBVERDICT_C_FOOD_NEAR2_TICK100_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR2_TICK100_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR2_TICK100_OPPOSITE,
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
    ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400: (
        SUBVERDICT_C_FOOD_NEAR2_TICK200_PRESENT,
        SUBVERDICT_C_FOOD_NEAR2_TICK200_PARTIAL,
        SUBVERDICT_C_FOOD_NEAR2_TICK200_NOT_FOUND,
        SUBVERDICT_C_FOOD_NEAR2_TICK200_OPPOSITE,
    ),
}

# C tick-400 sub-verdict (verdict-gating window; C only).
_SUBVERDICT_TICK400_C: tuple[str, str, str, str] = (
    SUBVERDICT_C_FOOD_NEAR2_TICK400_PRESENT,
    SUBVERDICT_C_FOOD_NEAR2_TICK400_PARTIAL,
    SUBVERDICT_C_FOOD_NEAR2_TICK400_NOT_FOUND,
    SUBVERDICT_C_FOOD_NEAR2_TICK400_OPPOSITE,
)


def _classify_subverdict(
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
    sub_table: tuple[str, str, str, str],
) -> str:
    """Per-arm 4-way sub-verdict from two label triples.

    Strict NaN-counts-toward-denominator rule: each label has 3 cells; a label
    is considered "clearing" iff fires_expected count >= 2. NaN cells (paired_d
    is nan) have fires_expected=False, so they count toward the denominator
    but not the numerator.
    """
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
    """Per-arm 4-way sub-verdict at a window; both labels gate."""
    if window == TICK_50:
        table = _SUBVERDICT_TICK50_TABLE[arm]
    elif window == TICK_100:
        table = _SUBVERDICT_TICK100_TABLE[arm]
    elif window == TICK_200:
        table = _SUBVERDICT_TICK200_TABLE[arm]
    elif window == TICK_400:
        if arm != ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
            msg = f"v0.53i: tick-400 sub-verdict only defined on C; got arm {arm!r}"
            raise V053iReducerError(msg)
        table = _SUBVERDICT_TICK400_C
    else:
        msg = f"v0.53i: unknown window {window!r}"
        raise V053iReducerError(msg)
    return _classify_subverdict(summaries_a, summaries_b, table)


# ---------------------------------------------------------------------------
# Re-anchor (corpus + Tier-1 bridge + Tier-2 categorical — NO Tier-3 in v0.53i)
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
    """Tier-1 anchor: A_null_V0_25 tick-50 cells against
    v0.48 / v0.53 / .../v0.53h."""
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
    """Fraction of ``arm`` runs where >= 1 founder lineage has
    ``events_field`` > 0. Returns (fraction, n_runs).

    NaN-broadcast values (e.g., pre400 on A/B) are treated as 0 — they
    cannot contribute reachability.
    """
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
    """Per (arm, window) descriptive metrics. Windows: tick-{50,100,200} on
    A/B/C plus tick-400 on C only."""
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
                # Label B: NaN-broadcast values count as False.
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
# Wrong-sign cell collection (always logged; rollup gating uses a separate path)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WrongSignCellRow:
    """Descriptive log row for a tick-400 wrong-sign cell on the C arm."""

    arm: str
    label: str
    observable: str
    paired_d: float
    signed_d: float
    n: int


def _collect_c_tick400_wrong_sign_cells(
    summaries_tick400: list[ObservableSummary],
) -> list[WrongSignCellRow]:
    """Collect every C tick-400 cell with signed_d <= -0.5 (descriptive log)."""
    rows: list[WrongSignCellRow] = []
    for s in summaries_tick400:
        if s.arm != ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
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
# Slice rollup (priority-ordered — PRIORITY 3 IS REACHABILITY-GATED on C tick-400)
# ---------------------------------------------------------------------------


def _evaluate_rollup(  # noqa: PLR0911 — 6-way priority match is the explicit verdict structure.
    *,
    a_null_tick50_subverdict: str,
    c_tick400_subverdict: str,
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    b_widened_v025_reachability_tick200: float,
    c_reachability_tick400: float,
) -> tuple[str, str]:
    """6-outcome priority-ordered rollup. Returns (verdict, locked_phrase).

    Priority 2 fires on (a) Tier-1 A_null_V0_25 tick-50 drift, (b) A_null
    tick-50 sub-verdict != PRESENT, OR (c) B_widened_V0_25 categorical
    reachability anchor != 0.0 exactly. NO Tier-3 in v0.53i (v0.53h's C
    tick-200 predecessor-sanity anchor is removed; v0.53h's `0/64` C result
    is referenced as a logical predecessor in locked phrases only).

    Priority 3 (GEOMETRY_OPPOSITE_SIGN_HALT) is REACHABILITY-GATED — fires iff
    BOTH:
      - C tick-400 sub-verdict == OPPOSITE_SIGN_HALT, AND
      - c_reachability_tick400 >= 0.25.
    If C sub-verdict == OPPOSITE_SIGN_HALT AND C reach < 0.25, priority 3
    SKIPS; rollup falls through to priority 5.

    Priorities 4/5/6 gate on C tick-400 reachability + tick-400 sub-verdict only.
    """
    # Priority 1: corpus drift halt (A_null_V0_25 only).
    drift_halt = next(
        (r for r in corpus_re_anchor if r.halts and r.arm == ARM_A_NULL_V025),
        None,
    )
    if drift_halt is not None:
        return ROLLUP_CORPUS_DRIFT_HALT, LOCKED_PHRASES[ROLLUP_CORPUS_DRIFT_HALT].format(
            version=drift_halt.version
        )

    # Priority 2: ANCHOR_REPLICATION_HALT — three legs (a/b/c). NO Tier-3.
    # (a) Tier-1 A_null_V0_25 tick-50 drift > 1e-3 against published values.
    if any(r.halts for r in bridge_re_anchor):
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    # (b) A_null_V0_25 tick-50 sub-verdict != PRESENT.
    if a_null_tick50_subverdict != SUBVERDICT_A_NULL_V025_TICK50_PRESENT:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )
    # (c) Tier-2 categorical: B_widened_V0_25 reachability tick-200 must == 0.0
    # exactly. Any non-zero value halts loud (categorical, not float-tolerance).
    if b_widened_v025_reachability_tick200 != 0.0:
        return (
            ROLLUP_ANCHOR_REPLICATION_HALT,
            LOCKED_PHRASES[ROLLUP_ANCHOR_REPLICATION_HALT],
        )

    # Priority 3: GEOMETRY_OPPOSITE_SIGN_HALT — REACHABILITY-GATED on C tick-400.
    if (
        c_tick400_subverdict == SUBVERDICT_C_FOOD_NEAR2_TICK400_OPPOSITE
        and c_reachability_tick400 >= B_REACHABILITY_THRESHOLD
    ):
        return (
            ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT,
            LOCKED_PHRASES[ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT],
        )

    # Priorities 4 / 5 / 6: gate on C tick-400 reachability + sub-verdict only.
    if c_reachability_tick400 < B_REACHABILITY_THRESHOLD:
        # Priority 5: below threshold, regardless of C sub-verdict (including
        # OPPOSITE_SIGN_HALT — the reachability-gated priority-3 trigger
        # collapses these wrong-sign cells into priority 5).
        return (
            ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2,
            LOCKED_PHRASES[ROLLUP_WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR2],
        )
    if c_tick400_subverdict == SUBVERDICT_C_FOOD_NEAR2_TICK400_PRESENT:
        # Priority 4: rescued.
        return (
            ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2,
            LOCKED_PHRASES[ROLLUP_WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2],
        )
    # Priority 6: partially rescued (C tick-400 sub-verdict in {PARTIAL, NOT_FOUND}).
    return (
        ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2,
        LOCKED_PHRASES[ROLLUP_WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_FOOD_NEAR2],
    )


# Public alias for parent-script convenience (per task spec — confirms importability).
def compute_slice_rollup_verdict(
    *,
    a_null_tick50_subverdict: str,
    c_tick400_subverdict: str,
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    b_widened_v025_reachability_tick200: float,
    c_reachability_tick400: float,
) -> tuple[str, str]:
    """Public wrapper around the priority-ordered rollup evaluation.

    NOTE: v0.53i deliberately does NOT accept a ``c_reachability_tick200``
    parameter. v0.53h's Tier-3 predecessor-sanity anchor is removed in v0.53i;
    test #14 enforces this absence via inspect.signature as a regression guard.
    """
    return _evaluate_rollup(
        a_null_tick50_subverdict=a_null_tick50_subverdict,
        c_tick400_subverdict=c_tick400_subverdict,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor,
        b_widened_v025_reachability_tick200=b_widened_v025_reachability_tick200,
        c_reachability_tick400=c_reachability_tick400,
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


def _write_paired_d_section(
    writer: csv.writer,
    section: str,
    summaries: list[ObservableSummary],
) -> None:
    for s in summaries:
        for field_name, value in (
            ("paired_d", s.paired_d),
            ("signed_d", s.signed_d),
            ("n_runs", s.n_runs_contributing),
            ("fires_expected", s.fires_expected),
            ("fires_wrong", s.fires_wrong),
            ("delta_mean", s.delta_mean),
            ("delta_stdev", s.delta_stdev),
            ("delta_min", s.delta_min),
            ("delta_max", s.delta_max),
        ):
            writer.writerow(
                [
                    section,
                    f"{s.arm}/{s.label}/{s.observable}/{field_name}",
                    _format_value(value),
                ]
            )


def _write_arm_reachability_section(
    writer: csv.writer,
    section: str,
    arm_reach: dict[str, tuple[float, int]],
    *,
    is_gating: bool,
    tier2_arm: str | None = None,
) -> None:
    for arm, (reach, n) in arm_reach.items():
        writer.writerow([section, f"{arm}/value", _format_value(reach)])
        writer.writerow([section, f"{arm}/n_runs", _format_value(n)])
        writer.writerow([section, f"{arm}/threshold", _format_value(B_REACHABILITY_THRESHOLD)])
        passes = (not math.isnan(reach)) and reach >= B_REACHABILITY_THRESHOLD
        writer.writerow([section, f"{arm}/passes_threshold", _format_value(passes)])
        is_arm_tier2 = tier2_arm is not None and arm == tier2_arm
        writer.writerow([section, f"{arm}/tier2_categorical_anchor", _format_value(is_arm_tier2)])
        writer.writerow(
            [
                section,
                f"{arm}/is_verdict_gating",
                _format_value(is_gating and arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400),
            ]
        )


def _write_audit_summary_csv(
    summaries_by_window: dict[int, list[ObservableSummary]],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor_tick50: list[BridgeReAnchorRow],
    a_null_tick50_subverdict: str,
    descriptive_subverdicts: dict[tuple[str, int], str],
    c_tick400_subverdict: str,
    reachability_by_window: dict[int, dict[str, tuple[float, int]]],
    population_stability: list[PopulationStabilityRow],
    wrong_sign_cells: list[WrongSignCellRow],
    *,
    priority3_skipped_under_reachability: bool,
    rollup_verdict: str,
    rollup_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
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
        for window, section in (
            (TICK_50, "paired_d_tick50"),
            (TICK_100, "paired_d_tick100"),
            (TICK_200, "paired_d_tick200"),
            (TICK_400, "paired_d_tick400"),
        ):
            _write_paired_d_section(writer, section, summaries_by_window.get(window, []))
        for window, section in (
            (TICK_50, "reachability_tick50"),
            (TICK_100, "reachability_tick100"),
            (TICK_200, "reachability_tick200"),
            (TICK_400, "reachability_tick400"),
        ):
            tier2_arm = ARM_B_WIDENED_V025 if window == TICK_200 else None
            _write_arm_reachability_section(
                writer,
                section,
                reachability_by_window.get(window, {}),
                is_gating=(window == TICK_400),
                tier2_arm=tier2_arm,
            )
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
        # Wrong-sign cells under C tick-400 reachability < 0.25 (carries
        # forward from v0.53f/g/h; gating window is tick-400).
        writer.writerow(
            [
                "wrong_sign_cells_under_reachability_below_threshold",
                "priority3_skipped_under_reachability_below_threshold",
                _format_value(priority3_skipped_under_reachability),
            ]
        )
        writer.writerow(
            [
                "wrong_sign_cells_under_reachability_below_threshold",
                "n_wrong_sign_cells_logged",
                _format_value(len(wrong_sign_cells)),
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
                        "wrong_sign_cells_under_reachability_below_threshold",
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
                ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400,
                c_tick400_subverdict,
            ]
        )
        writer.writerow(["rollup_verdict", "verdict", rollup_verdict])
        writer.writerow(["rollup_verdict", "locked_phrase", rollup_phrase])


def _observable_line(s: ObservableSummary) -> str:
    d_str = "nan" if math.isnan(s.paired_d) else f"{s.paired_d:+.3f}"
    signed_str = "nan" if math.isnan(s.signed_d) else f"{s.signed_d:+.3f}"
    flag = ""
    if s.fires_expected:
        flag = " FIRES"
    if s.fires_wrong:
        flag = " WRONG-SIGN"
    sign_label = "+" if s.sign > 0 else "-"
    mean_str = "nan" if math.isnan(s.delta_mean) else f"{s.delta_mean:+.4f}"
    sd_str = "nan" if math.isnan(s.delta_stdev) else f"{s.delta_stdev:.4f}"
    min_str = "nan" if math.isnan(s.delta_min) else f"{s.delta_min:+.4f}"
    max_str = "nan" if math.isnan(s.delta_max) else f"{s.delta_max:+.4f}"
    return (
        f"  {s.observable:<46} sign={sign_label}  d={d_str}  signed_d={signed_str}  "
        f"n={s.n_runs_contributing:>2}  "
        f"delta_mean={mean_str}  sd={sd_str}  min={min_str}  max={max_str}{flag}\n"
    )


def _write_audit_log(  # noqa: PLR0912
    summaries_by_window: dict[int, list[ObservableSummary]],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor_tick50: list[BridgeReAnchorRow],
    a_null_tick50_subverdict: str,
    descriptive_subverdicts: dict[tuple[str, int], str],
    c_tick400_subverdict: str,
    reachability_by_window: dict[int, dict[str, tuple[float, int]]],
    population_stability: list[PopulationStabilityRow],
    wrong_sign_cells: list[WrongSignCellRow],
    *,
    priority3_skipped_under_reachability: bool,
    rollup_verdict: str,
    rollup_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=== v0.53i geometry food-near2 audit (n_ticks=400 on C arm) ===\n")
    lines.append("\nCorpus re-anchor (per (arm, version, h=8)):\n")
    for r in corpus_re_anchor:
        published_str = "—" if r.a_share_h8_published is None else f"{r.a_share_h8_published:.3f}"
        derived_str = "nan" if math.isnan(r.a_share_h8_derived) else f"{r.a_share_h8_derived:.3f}"
        drift_str = "—" if r.drift_abs is None else f"{r.drift_abs:.4f}"
        halt_str = " HALT" if r.halts else ""
        lines.append(
            f"  {r.arm:<40} {r.version} h={r.hazard}  n={r.n_runs_contributing:>2}  "
            f"derived={derived_str}  published={published_str}  drift={drift_str}{halt_str}\n"
        )
    lines.append(
        "\nTier-1 bridge re-anchor (A_null_V0_25 tick-50 vs v0.48–v0.53h published):\n"  # noqa: RUF001
    )
    for br in bridge_re_anchor_tick50:
        drift_str = "inf" if math.isinf(br.drift_abs) else f"{br.drift_abs:.4f}"
        halt_str = " HALT" if br.halts else ""
        lines.append(
            f"  {br.label}/{br.observable:<46} "
            f"published={br.published_signed_d:+.3f}  derived={br.derived_signed_d:+.3f}  "
            f"drift={drift_str}{halt_str}\n"
        )
    b_v025_reach_t200, b_v025_n_t200 = reachability_by_window[TICK_200][ARM_B_WIDENED_V025]
    tier2_halt_str = " HALT" if b_v025_reach_t200 != 0.0 else ""
    lines.append(
        "\nTier-2 categorical anchor "
        "(B_widened_V0_25 reachability_run_share at tick-200 must == 0.0 exactly):\n"
    )
    lines.append(
        f"  {ARM_B_WIDENED_V025:<40} tick-200  n={b_v025_n_t200:>2}  "
        f"derived={b_v025_reach_t200:.4f}  expected=0.0000{tier2_halt_str}\n"
    )

    for window in WINDOWS_ALL:
        for arm in ARMS:
            if window == TICK_400 and arm != ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
                continue
            lines.append(
                f"\nArm {arm} — TICK-{window} paired_d per (gating-label, primary observable):\n"
            )
            for s in summaries_by_window.get(window, []):
                if s.arm != arm:
                    continue
                lines.append(f"  [{s.label}] {_observable_line(s)}")

    lines.append("\nPer-arm reachability_run_share by window:\n")
    for window in WINDOWS_ALL:
        for arm in ARMS:
            if arm not in reachability_by_window.get(window, {}):
                continue
            reach, n = reachability_by_window[window][arm]
            tag = ""
            if window == TICK_200 and arm == ARM_B_WIDENED_V025:
                tag = " (Tier-2 categorical anchor)"
            elif window == TICK_400 and arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
                tag = " (verdict-gating)"
            else:
                tag = " (descriptive)"
            passes = (not math.isnan(reach)) and reach >= B_REACHABILITY_THRESHOLD
            reach_str = "nan" if math.isnan(reach) else f"{reach:.4f}"
            lines.append(
                f"  tick-{window:>3} {arm:<40}: {reach_str} (n={n}, "
                f"threshold={B_REACHABILITY_THRESHOLD:.2f}, passes={passes}){tag}\n"
            )
    lines.append("\nPopulation-stability per (arm, window) (descriptive):\n")
    for ps in population_stability:
        lines.append(
            f"  {ps.arm:<40} tick-{ps.window:>3}  n_runs={ps.n_runs_total:>2}  "
            f"living_share={ps.living_population_run_share:.4f}  "
            f"label_a_n={ps.label_a_n_runs:>2}  label_b_n={ps.label_b_n_runs:>2}\n"
        )

    if wrong_sign_cells:
        lines.append(
            "\nWrong-sign cells under C tick-400 (reachability-gated priority-3 trigger; "
            f"priority-3 SKIPPED={priority3_skipped_under_reachability}):\n"
        )
        for wsc in wrong_sign_cells:
            lines.append(
                f"  [{wsc.label}] {wsc.observable:<46} paired_d={wsc.paired_d:+.3f}  "
                f"signed_d={wsc.signed_d:+.3f}  n={wsc.n:>2}\n"
            )

    lines.append(f"\nA_null_V0_25 tick-50 sub-verdict (anchor): {a_null_tick50_subverdict}\n")
    lines.append("\nDescriptive sub-verdicts (cross-slice anchors; not verdict-gating):\n")
    for (arm, window), sv in sorted(descriptive_subverdicts.items()):
        lines.append(f"  {arm:<40} tick-{window:>3}  {sv}\n")
    lines.append(f"\nC tick-400 sub-verdict (verdict-gating): {c_tick400_subverdict}\n")
    lines.append(f"\nRollup verdict: {rollup_verdict}\n")
    lines.append(f'Locked phrase fired: "{rollup_phrase}"\n')
    path.write_text("".join(lines))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0912, PLR0915
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== v0.53i geometry food-near2 audit (n_ticks=400 on C arm) ===")
    print(f"Arms: {list(ARMS)}")
    print(f"Per-arm n_ticks: {N_TICKS_BY_ARM}")
    print(f"Per-arm body_starting_energy: {BODY_STARTING_ENERGY_BY_ARM}")
    print(f"Per-arm body_base_metabolic_cost: {BODY_BASE_METABOLIC_COST_BY_ARM}")
    print(
        f"C layout (script-local): "
        f"safe_x=[{WIDENED_FOOD_NEAR2_LAYOUT.safe_x_min},"
        f"{WIDENED_FOOD_NEAR2_LAYOUT.safe_x_max}], "
        f"hazard_x=[{WIDENED_FOOD_NEAR2_LAYOUT.hazard_x_min},"
        f"{WIDENED_FOOD_NEAR2_LAYOUT.hazard_x_max}], "
        f"food_x=[{WIDENED_FOOD_NEAR2_LAYOUT.food_x_min},"
        f"{WIDENED_FOOD_NEAR2_LAYOUT.food_x_max}], "
        f"width={WIDENED_FOOD_NEAR2_LAYOUT.width}"
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
                        b50_lid = next(
                            (
                                r.lineage_id
                                for r in rows
                                if r.is_high_tick50_readiness_fraction_lineage
                            ),
                            None,
                        )
                        b400_val = "—"
                        if arm == ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400:
                            b400_lid = next(
                                (
                                    r.lineage_id
                                    for r in rows
                                    if isinstance(
                                        r.is_high_tick400_readiness_fraction_lineage, bool
                                    )
                                    and r.is_high_tick400_readiness_fraction_lineage
                                ),
                                None,
                            )
                            b400_val = str(b400_lid)
                        print(
                            f"  {arm:<40} {version} h={hazard:>2} seed={seed:>2}  "
                            f"a_top={a_lid}  b50_top={b50_lid}  b400_top={b400_val}"
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

    # A_null tick-50 sub-verdict (priority-2.b trigger).
    a_null_tick50_subverdict = _arm_subverdict_at_window(
        ARM_A_NULL_V025,
        TICK_50,
        summaries_by_arm_label[TICK_50].get((ARM_A_NULL_V025, LABEL_A_NAME), []),
        summaries_by_arm_label[TICK_50].get((ARM_A_NULL_V025, LABEL_B_TICK50_NAME), []),
    )
    # Descriptive sub-verdicts (B/C tick-50, A/B/C tick-100/200, C tick-50/100/200).
    descriptive_subverdicts: dict[tuple[str, int], str] = {}
    for arm in ARMS:
        for window in WINDOWS_BY_ARM[arm]:
            if window == TICK_50 and arm == ARM_A_NULL_V025:
                continue  # priority-2.b consumed above (kept separate in writers).
            if window == TICK_400:
                continue  # tick-400 is verdict-gating; recorded below.
            label_a_summaries = summaries_by_arm_label[window].get((arm, LABEL_A_NAME), [])
            label_b_field_name = label_pairs_by_window[window][1][0]
            label_b_summaries = summaries_by_arm_label[window].get((arm, label_b_field_name), [])
            descriptive_subverdicts[(arm, window)] = _arm_subverdict_at_window(
                arm, window, label_a_summaries, label_b_summaries
            )

    # C tick-400 sub-verdict — verdict-gating window.
    c_tick400_subverdict = _arm_subverdict_at_window(
        ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400,
        TICK_400,
        summaries_by_arm_label[TICK_400].get(
            (ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400, LABEL_A_NAME), []
        ),
        summaries_by_arm_label[TICK_400].get(
            (ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400, LABEL_B_TICK400_NAME), []
        ),
    )

    corpus_re_anchor = _check_corpus_re_anchor(all_rows)
    bridge_re_anchor_tick50 = _check_bridge_re_anchor_tick50(summaries_by_arm_label[TICK_50])

    # Per-arm reachability at every window the arm reaches.
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

    # Always collect C tick-400 wrong-sign cells (descriptive log; relevant
    # whether or not priority 3 fires).
    wrong_sign_cells = _collect_c_tick400_wrong_sign_cells(summaries_by_window[TICK_400])
    c_reach_t400 = reachability_by_window[TICK_400][ARM_C_WIDENED_FOOD_NEAR2_COMBINED_N400][0]
    priority3_skipped_under_reachability = (
        c_tick400_subverdict == SUBVERDICT_C_FOOD_NEAR2_TICK400_OPPOSITE
        and c_reach_t400 < B_REACHABILITY_THRESHOLD
    )

    rollup_verdict, rollup_phrase = _evaluate_rollup(
        a_null_tick50_subverdict=a_null_tick50_subverdict,
        c_tick400_subverdict=c_tick400_subverdict,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor_tick50,
        b_widened_v025_reachability_tick200=reachability_by_window[TICK_200][ARM_B_WIDENED_V025][0],
        c_reachability_tick400=c_reach_t400,
    )

    per_lineage_path = out_dir / "per_run_per_lineage_v053i.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)
    _write_audit_summary_csv(
        summaries_by_window,
        corpus_re_anchor,
        bridge_re_anchor_tick50,
        a_null_tick50_subverdict,
        descriptive_subverdicts,
        c_tick400_subverdict,
        reachability_by_window,
        population_stability,
        wrong_sign_cells,
        priority3_skipped_under_reachability=priority3_skipped_under_reachability,
        rollup_verdict=rollup_verdict,
        rollup_phrase=rollup_phrase,
        path=audit_summary_path,
    )
    _write_audit_log(
        summaries_by_window,
        corpus_re_anchor,
        bridge_re_anchor_tick50,
        a_null_tick50_subverdict,
        descriptive_subverdicts,
        c_tick400_subverdict,
        reachability_by_window,
        population_stability,
        wrong_sign_cells,
        priority3_skipped_under_reachability=priority3_skipped_under_reachability,
        rollup_verdict=rollup_verdict,
        rollup_phrase=rollup_phrase,
        path=audit_log_path,
    )

    print(f"\nA_null_V0_25 tick-50 sub-verdict (anchor): {a_null_tick50_subverdict}")
    for (arm, window), sv in sorted(descriptive_subverdicts.items()):
        print(f"Descriptive sub-verdict {arm} tick-{window}: {sv}")
    print(f"C tick-400 sub-verdict (verdict-gating): {c_tick400_subverdict}")
    print(f"\nRollup verdict: {rollup_verdict}")
    print(f'Locked phrase: "{rollup_phrase}"')
    print()
    print(f"Wrote {per_lineage_path}")
    print(f"Wrote {audit_summary_path}")
    print(f"Wrote {audit_log_path}")

    if rollup_verdict in {
        ROLLUP_CORPUS_DRIFT_HALT,
        ROLLUP_ANCHOR_REPLICATION_HALT,
        ROLLUP_GEOMETRY_OPPOSITE_SIGN_HALT,
    }:
        raise V053iReducerError(rollup_phrase)
    return rollup_verdict, rollup_phrase


def main() -> None:
    parser = argparse.ArgumentParser(
        description="v0.53i geometry food-near2 audit (n_ticks=400 on C arm)"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.53i-geometry-food-near2"),
        help=("Directory for v0.53i outputs (default: runs/v0.53i-geometry-food-near2)."),
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
