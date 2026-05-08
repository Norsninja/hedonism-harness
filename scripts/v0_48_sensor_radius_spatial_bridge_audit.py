"""v0.48 sensor_radius -> space -> readiness bridge (post-hoc reducer).

Pre-reg: [[docs/experiments/fear_hunger_v0.48.md]]. Question: is the
founder-level sensor_radius advantage observed by v0.47 mediated by a
measurable pre-50 spatial / foraging advantage that - under the same
effect-size discipline - also tracks the v0.47 readiness-fraction label?

Corpus (locked, same as v0.46 / v0.47): A_null arm only across v0.42 /
v0.43R / v0.44 / v0.45, hazards {0, 8}, seeds 41..72 (8 per version,
disjoint). 64 runs total.

Primary observables (locked, with expected signs):
  1. pre50_food_events_count           (+)
  2. pre50_food_energy_acquired        (+)
  3. mean_distance_to_nearest_food_cell(-)

Primary labels (verdict-firing, both consulted independently):
  A. high_sensor_radius_lineage =
       argmax_lineage(founder_sensor_radius), tiebreak min(lineage_id)
  B. high_tick50_readiness_fraction_lineage =
       argmax_lineage(tick50_above_threshold_fraction)
       3-tier: fraction -> count -> min(lineage_id) (NaN-loses)
       (identical to v0.47's primary label)

Effect-size rule (locked, sign-aware):
  per_run_delta_O = label_lineage_value_O - mean(non_label_values_O)
  paired_d_O      = mean(per_run_delta_O) / stdev(per_run_delta_O, ddof=1)
  signed_d_O      = paired_d_O * expected_sign
  fires_expected  iff signed_d_O >= +0.5
  fires_wrong     iff signed_d_O <= -0.5

Verdicts (locked, AND-gated for PRESENT):
  any wrong-sign under either label  -> SPATIAL_BRIDGE_OPPOSITE_SIGN_HALT
  both labels >= 2/3 fire (no wrong) -> SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT
  exactly one label >= 2/3 fires     -> SENSOR_RADIUS_SPATIAL_BRIDGE_PARTIAL
  neither label >= 2/3 fires         -> SENSOR_RADIUS_SPATIAL_BRIDGE_NOT_FOUND
  re-anchor drift > 1e-3 (v0.42 / v0.44 / v0.45 only) -> CORPUS_REDERIVE_DRIFT_HALT

Conservation framing (unchanged from v0.46 / v0.47): no ``src/``
modifications, no new sweep arms, no modifications to prior reducer or
audit scripts.

Usage:
    uv run python scripts/v0_48_sensor_radius_spatial_bridge_audit.py
    uv run python scripts/v0_48_sensor_radius_spatial_bridge_audit.py \
        --out-dir runs/v0.48-spatial-bridge
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
    _resolve_layout,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
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
N_TICKS: int = 200
N_FOUNDERS: int = 5
TICK_50: int = 50
LAYOUT_NAME: str = "tight_gradient"

PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5

EXPECTED_FOUNDERS: int = 5

# Primary observables with locked expected signs.
PRIMARY_OBSERVABLES: tuple[tuple[str, int], ...] = (
    ("pre50_food_events_count", +1),
    ("pre50_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell", -1),
)

# Primary labels (verdict-firing).
LABEL_A_FIELD = "is_high_sensor_radius_lineage"
LABEL_B_FIELD = "is_high_tick50_readiness_fraction_lineage"
LABEL_A_NAME = "label_a_sensor_radius"
LABEL_B_NAME = "label_b_readiness_fraction"

# Verdicts (locked).
VERDICT_PRESENT = "SENSOR_RADIUS_SPATIAL_BRIDGE_PRESENT"
VERDICT_PARTIAL = "SENSOR_RADIUS_SPATIAL_BRIDGE_PARTIAL"
VERDICT_NOT = "SENSOR_RADIUS_SPATIAL_BRIDGE_NOT_FOUND"
VERDICT_HALT_OPPOSITE = "SPATIAL_BRIDGE_OPPOSITE_SIGN_HALT"
VERDICT_HALT_DRIFT = "CORPUS_REDERIVE_DRIFT_HALT"

# Locked phrases (verbatim per pre-reg).
LOCKED_PHRASES: dict[str, str] = {
    VERDICT_PRESENT: (
        "Founder `sensor_radius` advantage co-occurs with a pre-50 spatial / foraging "
        "advantage that also tracks tick-50 readiness fraction on the modern A_null corpus."
    ),
    VERDICT_PARTIAL: (
        "A pre-50 spatial / foraging advantage tracks one of (founder `sensor_radius`, "
        "tick-50 readiness fraction) but not the other on the modern A_null corpus; "
        "the bridge is partial."
    ),
    VERDICT_NOT: (
        "No pre-50 spatial / foraging advantage tracks either label on the modern A_null "
        "corpus; the trait->space->readiness bridge does not fire under the locked "
        "observables and threshold."
    ),
    VERDICT_HALT_OPPOSITE: (
        "Halt: a v0.48 spatial / foraging primary fires in the WRONG direction under at "
        "least one of the two labels; the trait->space->readiness bridge hypothesis is "
        "incompatible with the locked expected signs."
    ),
    VERDICT_HALT_DRIFT: (
        "Halt: A_null re-anchor drifted from the published Results value for {version}; "
        "v0.48's deterministic re-execution does not reproduce the published metric within 1e-3."
    ),
}

# Founder-trait names mirrored from v0.47 schema for cross-readability.
FOUNDER_TRAIT_NAMES: tuple[str, ...] = (
    "reproduction_drive",
    "metabolic_rate",
    "sensor_radius",
)


class V048ReducerError(Exception):
    """Halt condition raised when a v0.48 invariant is violated."""


# ---------------------------------------------------------------------------
# Per-run capture
# ---------------------------------------------------------------------------


@dataclass
class _TickRecord:
    """Per-tick snapshot of living-agent positions + food/hazard cells.

    ``agents`` rows: (agent_id, lineage_id, x, y, sensor_radius).
    ``food_cells`` / ``hazard_cells``: tuples of (x, y).
    """

    tick: int
    agents: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    food_cells: tuple[tuple[int, int], ...] = ()
    hazard_cells: tuple[tuple[int, int], ...] = ()


@dataclass
class _Tick50Readiness:
    """Tick-50 readiness-predicate snapshot per living agent."""

    agent_id: int
    lineage_id: int
    energy: float
    age: int


@dataclass
class _RunCapture:
    """Everything captured during one A_null run."""

    version: str
    seed: int
    hazard: int
    # Per-tick records keyed by tick (0..50 inclusive). 51 entries expected.
    tick_records: dict[int, _TickRecord] = field(default_factory=dict)
    # Tick-50 readiness predicate snapshot (label B input).
    tick50_readiness: list[_Tick50Readiness] = field(default_factory=list)
    # birth_tick by agent_id; founders normalised to 0 by convention.
    birth_tick_by_agent: dict[int, int] = field(default_factory=dict)
    # lineage_id by agent_id.
    lineage_by_agent: dict[int, int] = field(default_factory=dict)
    # Founder traits keyed by lineage_id (locked unmutated initial draws).
    founder_traits_by_lineage: dict[int, dict[str, float]] = field(default_factory=dict)
    # AteFood event accumulators by agent_id, filtered to tick <= 50.
    pre50_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre50_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre50_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    # Sanity counters.
    n_observer_fires: int = 0
    energy_threshold: float = 0.0
    min_age: int = 0


def _select_a_null_arm(version: str, hazard: int) -> Arm:
    """Pull the A_null arm for ``hazard`` from the version's INTERVENTION_ARMS tuple."""
    armset = {
        "v0.42": V0_42_INTERVENTION_ARMS,
        "v0.43R": V0_43R_INTERVENTION_ARMS,
        "v0.44": V0_44_INTERVENTION_ARMS,
        "v0.45": V0_45_INTERVENTION_ARMS,
    }[version]
    candidates = [a for a in armset if "A_null" in a.label and a.hazard_damage == hazard]
    if len(candidates) != 1:
        msg = (
            f"v0.48: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V048ReducerError(msg)
    return candidates[0]


def _capture_tick_record(model: HHModel, tick_label: int, capture: _RunCapture) -> None:
    """Read-only snapshot of living-agent positions + food/hazard cells.

    Stored at ``capture.tick_records[tick_label]``. Idempotent: a second call
    for an already-captured tick is a no-op (guards against duplicate
    observer fires)."""
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


def _make_setup_observer(
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    """Build a setup_observer that captures founder traits + wires signal listeners.

    Per pre-reg "Pre-implementation correction (2026-05-08)": the per-tick
    observer fires AFTER ``model.step()`` increments ``tick_count``, so it
    cannot directly observe the pre-step initial state. The setup_observer
    captures the initial state as ``tick = 0`` to honour the locked window
    of ticks 0..50 inclusive (51 snapshots total)."""

    def setup(model: HHModel) -> None:
        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None:
                continue
            lineage_id = int(body.lineage_id)
            capture.lineage_by_agent[int(body.id)] = lineage_id
            capture.birth_tick_by_agent[int(body.id)] = 0
            traits = body.traits
            capture.founder_traits_by_lineage[lineage_id] = {
                name: float(getattr(traits, name)) for name in FOUNDER_TRAIT_NAMES
            }

        # Capture initial state as tick 0 (pre-step, before any model.step()).
        _capture_tick_record(model, tick_label=0, capture=capture)

        def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
            capture.birth_tick_by_agent[int(event.agent_id)] = int(event.tick)
            capture.lineage_by_agent[int(event.agent_id)] = int(event.lineage_id)

        signal_for(AgentBorn).connect(_on_agent_born, sender=model)
        disconnect_callbacks.append(
            lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
        )

        def _on_ate_food(_sender: object, *, event: AteFood) -> None:
            if int(model.tick_count) > TICK_50:
                return
            aid = int(event.agent_id)
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = capture.pre50_food_energy_by_agent.get(
                aid, 0.0
            ) + float(event.food_gained)

        def _on_hazard_damage(_sender: object, *, event: HazardDamageApplied) -> None:
            if int(model.tick_count) > TICK_50:
                return
            aid = int(event.agent_id)
            capture.pre50_hazard_damage_events_by_agent[aid] = (
                capture.pre50_hazard_damage_events_by_agent.get(aid, 0) + 1
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

    return setup


def _make_per_tick_observer(capture: _RunCapture) -> Callable[[HHModel], None]:
    """Build a per-tick read-only observer for ticks 1..50 (post-step).

    Tick 0 is captured by the setup_observer (per pre-reg "Pre-implementation
    correction"). At each fire this observer snapshots every living agent's
    (id, lineage, x, y, sensor_radius) plus the live food / hazard cell
    positions. At tick 50 it additionally snapshots (energy, age) per
    living agent for the label B readiness predicate.
    """

    def observer(model: HHModel) -> None:
        tick = int(model.tick_count)
        if tick == 0 or tick > TICK_50:
            return
        _capture_tick_record(model, tick_label=tick, capture=capture)

        if tick == TICK_50:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick50_readiness.append(
                    _Tick50Readiness(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )

    return observer


def _run_one_a_null_run(version: str, seed: int, hazard: int, runs_root: Path) -> _RunCapture:
    """Execute one A_null (version, seed, hazard) run, returning its capture."""
    arm = _select_a_null_arm(version, hazard)
    layout = _resolve_layout(LAYOUT_NAME)
    repro_kwargs: dict[str, float] = {
        "energy_threshold": (
            arm.energy_threshold if arm.energy_threshold is not None else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": (arm.energy_cost if arm.energy_cost is not None else FIXED_ENERGY_COST),
    }
    if arm.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = arm.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
    trait_cfg = TraitConfig(unbounded_mutation=True)

    capture = _RunCapture(version=version, seed=seed, hazard=hazard)
    disconnects: list[Callable[[], None]] = []
    base_setup = _make_setup_observer(capture, disconnects)

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = arm.auto_reproduction
        base_setup(model)

    use_memory = arm.memory_type is not None
    memory_type = arm.memory_type or "cell_exact"

    optional_intervention: InterventionConfig | None = None
    if arm.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=arm.intervention_kind)
    if optional_intervention is not None and optional_intervention.kind != KIND_NULL:
        msg = (
            f"v0.48 corpus must be A_null only; arm {arm.label} has "
            f"intervention_kind={arm.intervention_kind!r}"
        )
        raise V048ReducerError(msg)

    run_id = f"{version}-A_null-hzd{hazard}-seed-{seed}"
    try:
        run_chamber(
            seed=seed,
            runs_root=runs_root,
            run_id=run_id,
            n_founders=N_FOUNDERS,
            n_ticks=N_TICKS,
            layout=layout,
            policy_factory=arm.policy_factory,
            trait_config=trait_cfg,
            reproduction_config=repro_cfg,
            use_memory=use_memory,
            memory_type=memory_type,
            food_respawn_cooldown=arm.food_respawn_cooldown,
            energy_pool_initial=arm.energy_pool_initial,
            ambient_influx_rate=arm.ambient_influx_rate,
            child_funding_mode=arm.child_funding_mode,
            hazard_damage=arm.hazard_damage,
            hazard_avoidance_weight=arm.hazard_avoidance_weight,
            condition=f"v0.48-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_per_tick_observer(capture),
            optional_intervention=optional_intervention,
        )
    finally:
        for disconnect in disconnects:
            disconnect()

    expected_ticks = TICK_50 + 1  # 0..50 inclusive
    if len(capture.tick_records) != expected_ticks:
        msg = (
            f"v0.48 invariant: per-tick observer must capture {expected_ticks} ticks for "
            f"{run_id}; got {len(capture.tick_records)}"
        )
        raise V048ReducerError(msg)
    if len(capture.founder_traits_by_lineage) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.48 invariant: expected exactly {EXPECTED_FOUNDERS} founders for "
            f"{run_id}; captured traits for {len(capture.founder_traits_by_lineage)}"
        )
        raise V048ReducerError(msg)
    return capture


# ---------------------------------------------------------------------------
# Per-lineage row + label assignment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerLineageRow:
    version: str
    seed: int
    hazard: int
    run_id: str
    lineage_id: int
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    founder_sensor_radius: float
    pre50_food_events_count: int
    pre50_food_energy_acquired: float
    mean_distance_to_nearest_food_cell: float  # NaN if lineage has 0 living over 0..50.
    mean_axial_food_signal_own_radius: float  # NaN if lineage has 0 living over 0..50.
    mean_axial_hazard_signal_own_radius: float  # NaN if lineage has 0 living over 0..50.
    tick50_centroid_distance_to_nearest_food: float  # NaN if 0 living at tick 50.
    tick50_centroid_distance_to_nearest_hazard: float  # NaN if 0 living at tick 50.
    tick50_living_count: int
    tick50_above_threshold_count: int
    tick50_above_threshold_fraction: float  # NaN if 0 living at tick 50.
    pre50_hazard_damage_received_count: int
    b50_count: int
    is_eventual_top_b50_label: bool
    is_high_sensor_radius_lineage: bool
    is_high_tick50_readiness_fraction_lineage: bool


PER_LINEAGE_FIELDNAMES: list[str] = [
    "version",
    "seed",
    "hazard",
    "run_id",
    "lineage_id",
    "founder_reproduction_drive",
    "founder_metabolic_rate",
    "founder_sensor_radius",
    "pre50_food_events_count",
    "pre50_food_energy_acquired",
    "mean_distance_to_nearest_food_cell",
    "mean_axial_food_signal_own_radius",
    "mean_axial_hazard_signal_own_radius",
    "tick50_centroid_distance_to_nearest_food",
    "tick50_centroid_distance_to_nearest_hazard",
    "tick50_living_count",
    "tick50_above_threshold_count",
    "tick50_above_threshold_fraction",
    "pre50_hazard_damage_received_count",
    "b50_count",
    "is_eventual_top_b50_label",
    "is_high_sensor_radius_lineage",
    "is_high_tick50_readiness_fraction_lineage",
]


def _manhattan_distance_to_nearest(
    x: int, y: int, cells: tuple[tuple[int, int], ...]
) -> float | None:
    """Min Manhattan distance from (x, y) to any cell in ``cells``; None if empty."""
    if not cells:
        return None
    return float(min(abs(cx - x) + abs(cy - y) for (cx, cy) in cells))


def _manhattan_distance_real_to_nearest(
    fx: float, fy: float, cells: tuple[tuple[int, int], ...]
) -> float | None:
    """Min Manhattan distance from real-valued (fx, fy) to any cell in ``cells``."""
    if not cells:
        return None
    return float(min(abs(cx - fx) + abs(cy - fy) for (cx, cy) in cells))


def _axial_signal_count(x: int, y: int, radius: int, cells_set: frozenset[tuple[int, int]]) -> int:
    """Count cells in ``cells_set`` along the four axial rays from (x, y) at
    distances 1..radius (4 * radius cells max). Out-of-bounds cells simply
    are not in the set so they don't contribute - the 12x12 layout makes
    this safe without bounds clamping."""
    count = 0
    for k in range(1, radius + 1):
        for dx, dy in ((0, k), (0, -k), (k, 0), (-k, 0)):
            if (x + dx, y + dy) in cells_set:
                count += 1
    return count


def _per_tick_lineage_means(
    capture: _RunCapture,
) -> dict[int, dict[str, float]]:
    """Compute per-lineage spatial observables aggregated over ticks 0..50.

    Returns ``{lineage_id: {observable_name: value or NaN}}`` for the
    primary distance metric and the two descriptive axial signals. The
    aggregation rule (per pre-reg) is per-tick lineage mean then mean
    across ticks where the lineage had >= 1 living agent. NaN if zero
    living agents across the whole window OR if every contributing tick
    had no food cells (distance metric only)."""
    all_lineages = sorted(set(capture.lineage_by_agent.values()))
    sums: dict[int, dict[str, float]] = {
        lid: {"distance": 0.0, "axial_food": 0.0, "axial_hazard": 0.0} for lid in all_lineages
    }
    counts: dict[int, dict[str, int]] = {
        lid: {"distance": 0, "axial_food": 0, "axial_hazard": 0} for lid in all_lineages
    }

    for tick in range(TICK_50 + 1):
        record = capture.tick_records.get(tick)
        if record is None:
            continue
        food_set = frozenset(record.food_cells)
        hazard_set = frozenset(record.hazard_cells)
        # Group living agents by lineage.
        living_by_lineage: dict[int, list[tuple[int, int, int, int, int]]] = {}
        for row in record.agents:
            living_by_lineage.setdefault(row[1], []).append(row)
        for lid, agents in living_by_lineage.items():
            # Distance: mean over agents of min Manhattan to nearest food cell.
            agent_distances: list[float] = []
            for _aid, _lid, ax, ay, _r in agents:
                d = _manhattan_distance_to_nearest(ax, ay, record.food_cells)
                if d is not None:
                    agent_distances.append(d)
            if agent_distances:
                sums[lid]["distance"] += statistics.mean(agent_distances)
                counts[lid]["distance"] += 1
            # Axial food / hazard signals (own radius).
            food_signal_per_agent = [
                _axial_signal_count(ax, ay, r, food_set) for (_aid, _lid, ax, ay, r) in agents
            ]
            hazard_signal_per_agent = [
                _axial_signal_count(ax, ay, r, hazard_set) for (_aid, _lid, ax, ay, r) in agents
            ]
            if food_signal_per_agent:
                sums[lid]["axial_food"] += statistics.mean(food_signal_per_agent)
                counts[lid]["axial_food"] += 1
            if hazard_signal_per_agent:
                sums[lid]["axial_hazard"] += statistics.mean(hazard_signal_per_agent)
                counts[lid]["axial_hazard"] += 1

    out: dict[int, dict[str, float]] = {}
    for lid in all_lineages:
        out[lid] = {
            "mean_distance_to_nearest_food_cell": (
                sums[lid]["distance"] / counts[lid]["distance"]
                if counts[lid]["distance"] > 0
                else float("nan")
            ),
            "mean_axial_food_signal_own_radius": (
                sums[lid]["axial_food"] / counts[lid]["axial_food"]
                if counts[lid]["axial_food"] > 0
                else float("nan")
            ),
            "mean_axial_hazard_signal_own_radius": (
                sums[lid]["axial_hazard"] / counts[lid]["axial_hazard"]
                if counts[lid]["axial_hazard"] > 0
                else float("nan")
            ),
        }
    return out


def _select_sensor_radius_label(
    founder_traits_by_lineage: dict[int, dict[str, float]],
) -> int | None:
    """argmax(founder_sensor_radius), tiebreak min(lineage_id)."""
    if not founder_traits_by_lineage:
        return None
    best_lid: int | None = None
    best_value = float("-inf")
    for lid in sorted(founder_traits_by_lineage):
        v = float(founder_traits_by_lineage[lid].get("sensor_radius", float("-inf")))
        # Strict ">" preserves min(lineage_id) tiebreak via sorted iteration.
        if v > best_value:
            best_value = v
            best_lid = lid
    return best_lid


def _select_fraction_label(
    candidates: list[tuple[int, float, int]],
) -> int | None:
    """``candidates``: ``[(lineage_id, fraction, count), ...]`` over lineages
    with non-NaN fraction. Tiebreak: fraction -> count -> min(lineage_id).

    Identical semantics to v0.47's ``_select_fraction_label``; copy-local
    to keep the prior reducer byte-identical."""
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


def _aggregate_per_lineage(capture: _RunCapture) -> list[PerLineageRow]:  # noqa: PLR0912, PLR0915 — per-lineage aggregation is cohesive (b50 / pre50 / spatial / centroid / readiness all consume the same capture; splitting would obscure the row construction).
    """Roll up per-tick + per-event capture into per-lineage rows."""
    all_lineages = sorted(set(capture.lineage_by_agent.values()))

    # b50_count per lineage.
    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.48: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V048ReducerError(msg)
            b50_by_lineage[lid] = b50_by_lineage.get(lid, 0) + 1
    total_b50 = sum(b50_by_lineage.values())

    # Eventual top by v0.46/v0.47 b50-label semantics (descriptive only here).
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

    # Tick-50 readiness predicate per lineage.
    living_at_50_by_lineage: dict[int, list[_Tick50Readiness]] = {lid: [] for lid in all_lineages}
    for snap in capture.tick50_readiness:
        living_at_50_by_lineage.setdefault(snap.lineage_id, []).append(snap)

    fraction_by_lineage: dict[int, float] = {}
    count_by_lineage: dict[int, int] = {}
    living_count_by_lineage: dict[int, int] = {}
    for lid in all_lineages:
        living = living_at_50_by_lineage.get(lid, [])
        n_living = len(living)
        living_count_by_lineage[lid] = n_living
        n_above = sum(
            1 for s in living if s.energy >= capture.energy_threshold and s.age >= capture.min_age
        )
        count_by_lineage[lid] = n_above
        fraction_by_lineage[lid] = (n_above / n_living) if n_living > 0 else float("nan")

    fraction_candidates = [
        (lid, fraction_by_lineage[lid], count_by_lineage[lid])
        for lid in all_lineages
        if not math.isnan(fraction_by_lineage[lid])
    ]
    fraction_label = _select_fraction_label(fraction_candidates)
    sensor_label = _select_sensor_radius_label(capture.founder_traits_by_lineage)

    # Spatial aggregations.
    spatial = _per_tick_lineage_means(capture)

    # Tick-50 centroid distances (descriptive).
    tick50_record = capture.tick_records.get(TICK_50)
    food_cells_t50: tuple[tuple[int, int], ...] = (
        tick50_record.food_cells if tick50_record is not None else ()
    )
    hazard_cells_t50: tuple[tuple[int, int], ...] = (
        tick50_record.hazard_cells if tick50_record is not None else ()
    )
    centroid_food_by_lineage: dict[int, float] = {}
    centroid_hazard_by_lineage: dict[int, float] = {}
    if tick50_record is not None:
        agents_t50_by_lineage: dict[int, list[tuple[int, int, int, int, int]]] = {}
        for row in tick50_record.agents:
            agents_t50_by_lineage.setdefault(row[1], []).append(row)
        for lid in all_lineages:
            agents = agents_t50_by_lineage.get(lid, [])
            if not agents:
                centroid_food_by_lineage[lid] = float("nan")
                centroid_hazard_by_lineage[lid] = float("nan")
                continue
            mean_x = statistics.mean(a[2] for a in agents)
            mean_y = statistics.mean(a[3] for a in agents)
            food_d = _manhattan_distance_real_to_nearest(mean_x, mean_y, food_cells_t50)
            haz_d = _manhattan_distance_real_to_nearest(mean_x, mean_y, hazard_cells_t50)
            centroid_food_by_lineage[lid] = float("nan") if food_d is None else float(food_d)
            centroid_hazard_by_lineage[lid] = float("nan") if haz_d is None else float(haz_d)
    else:
        for lid in all_lineages:
            centroid_food_by_lineage[lid] = float("nan")
            centroid_hazard_by_lineage[lid] = float("nan")

    # Pre-50 event counts per lineage.
    pre50_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre50_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    pre50_hazard_damage_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, lid in capture.lineage_by_agent.items():
        pre50_food_events_by_lineage[lid] = pre50_food_events_by_lineage.get(
            lid, 0
        ) + capture.pre50_food_events_by_agent.get(aid, 0)
        pre50_food_energy_by_lineage[lid] = pre50_food_energy_by_lineage.get(
            lid, 0.0
        ) + capture.pre50_food_energy_by_agent.get(aid, 0.0)
        pre50_hazard_damage_by_lineage[lid] = pre50_hazard_damage_by_lineage.get(
            lid, 0
        ) + capture.pre50_hazard_damage_events_by_agent.get(aid, 0)

    rows: list[PerLineageRow] = []
    run_id = f"{capture.version}-A_null-hzd{capture.hazard}-seed-{capture.seed}"
    for lid in all_lineages:
        founder = capture.founder_traits_by_lineage.get(lid, {})
        spatial_lid = spatial.get(
            lid,
            {
                "mean_distance_to_nearest_food_cell": float("nan"),
                "mean_axial_food_signal_own_radius": float("nan"),
                "mean_axial_hazard_signal_own_radius": float("nan"),
            },
        )
        rows.append(
            PerLineageRow(
                version=capture.version,
                seed=capture.seed,
                hazard=capture.hazard,
                run_id=run_id,
                lineage_id=lid,
                founder_reproduction_drive=float(founder.get("reproduction_drive", float("nan"))),
                founder_metabolic_rate=float(founder.get("metabolic_rate", float("nan"))),
                founder_sensor_radius=float(founder.get("sensor_radius", float("nan"))),
                pre50_food_events_count=pre50_food_events_by_lineage.get(lid, 0),
                pre50_food_energy_acquired=pre50_food_energy_by_lineage.get(lid, 0.0),
                mean_distance_to_nearest_food_cell=spatial_lid[
                    "mean_distance_to_nearest_food_cell"
                ],
                mean_axial_food_signal_own_radius=spatial_lid["mean_axial_food_signal_own_radius"],
                mean_axial_hazard_signal_own_radius=spatial_lid[
                    "mean_axial_hazard_signal_own_radius"
                ],
                tick50_centroid_distance_to_nearest_food=centroid_food_by_lineage[lid],
                tick50_centroid_distance_to_nearest_hazard=centroid_hazard_by_lineage[lid],
                tick50_living_count=living_count_by_lineage[lid],
                tick50_above_threshold_count=count_by_lineage[lid],
                tick50_above_threshold_fraction=fraction_by_lineage[lid],
                pre50_hazard_damage_received_count=pre50_hazard_damage_by_lineage.get(lid, 0),
                b50_count=b50_by_lineage.get(lid, 0),
                is_eventual_top_b50_label=(eventual_top is not None and lid == eventual_top),
                is_high_sensor_radius_lineage=(sensor_label is not None and lid == sensor_label),
                is_high_tick50_readiness_fraction_lineage=(
                    fraction_label is not None and lid == fraction_label
                ),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Effect-size + verdict
# ---------------------------------------------------------------------------


def _per_run_paired_delta(
    rows_in_run: list[PerLineageRow], observable_field: str, label_field: str
) -> float | None:
    """``label_value - mean(non_label_values)`` for one run. None if can't contribute."""
    label_rows = [r for r in rows_in_run if getattr(r, label_field)]
    if len(label_rows) != 1:
        return None
    label_value = getattr(label_rows[0], observable_field)
    if isinstance(label_value, float) and math.isnan(label_value):
        return None
    non_label = [r for r in rows_in_run if not getattr(r, label_field)]
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
    observable: str
    label: str  # LABEL_A_NAME or LABEL_B_NAME
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


def _summarise_observable(
    *,
    observable: str,
    sign: int,
    label: str,
    label_field: str,
    all_rows: list[PerLineageRow],
    runs: list[tuple[str, int, int]],
) -> ObservableSummary:
    deltas: list[float] = []
    by_run = _index_rows_by_run(all_rows)
    for run_key in runs:
        run_rows = by_run.get(run_key, [])
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


def _index_rows_by_run(
    rows: list[PerLineageRow],
) -> dict[tuple[str, int, int], list[PerLineageRow]]:
    out: dict[tuple[str, int, int], list[PerLineageRow]] = {}
    for r in rows:
        out.setdefault((r.version, r.seed, r.hazard), []).append(r)
    return out


def _evaluate_verdict(
    summaries_a: list[ObservableSummary], summaries_b: list[ObservableSummary]
) -> str:
    """AND-gated verdict consulting both label sets."""
    n_wrong_a = sum(1 for s in summaries_a if s.fires_wrong)
    n_wrong_b = sum(1 for s in summaries_b if s.fires_wrong)
    if n_wrong_a > 0 or n_wrong_b > 0:
        return VERDICT_HALT_OPPOSITE
    n_fire_a = sum(1 for s in summaries_a if s.fires_expected)
    n_fire_b = sum(1 for s in summaries_b if s.fires_expected)
    a_clears = n_fire_a >= 2
    b_clears = n_fire_b >= 2
    if a_clears and b_clears:
        return VERDICT_PRESENT
    if a_clears != b_clears:
        return VERDICT_PARTIAL
    return VERDICT_NOT


# ---------------------------------------------------------------------------
# Label-A / label-B agreement (descriptive)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgreementSummary:
    n_runs_well_defined: int
    n_runs_match: int
    agreement_rate: float


def _compute_agreement(all_rows: list[PerLineageRow]) -> AgreementSummary:
    by_run = _index_rows_by_run(all_rows)
    well_defined = 0
    match = 0
    for rows_in_run in by_run.values():
        a_label = next((r.lineage_id for r in rows_in_run if r.is_high_sensor_radius_lineage), None)
        b_label = next(
            (r.lineage_id for r in rows_in_run if r.is_high_tick50_readiness_fraction_lineage),
            None,
        )
        if a_label is None or b_label is None:
            continue
        well_defined += 1
        if a_label == b_label:
            match += 1
    rate = (match / well_defined) if well_defined > 0 else float("nan")
    return AgreementSummary(
        n_runs_well_defined=well_defined, n_runs_match=match, agreement_rate=rate
    )


# ---------------------------------------------------------------------------
# Re-anchor (cross-version, identical to v0.46/v0.47)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReAnchorRow:
    version: str
    hazard: int
    n_runs_contributing: int
    a_share_h8_derived: float
    a_share_h8_published: float | None
    drift_abs: float | None
    halts: bool


def _compute_a_share_h8(all_rows: list[PerLineageRow], version: str) -> tuple[float, int]:
    by_run = _index_rows_by_run(all_rows)
    shares: list[float] = []
    for (ver, _seed, haz), rows_in_run in by_run.items():
        if ver != version or haz != 8:
            continue
        total_b50 = sum(r.b50_count for r in rows_in_run)
        if total_b50 == 0:
            continue
        max_b50 = max(r.b50_count for r in rows_in_run)
        shares.append(max_b50 / total_b50)
    if not shares:
        return float("nan"), 0
    return statistics.mean(shares), len(shares)


def _check_re_anchor(all_rows: list[PerLineageRow]) -> list[ReAnchorRow]:
    out: list[ReAnchorRow] = []
    for version in ("v0.42", "v0.43R", "v0.44", "v0.45"):
        derived, n_runs = _compute_a_share_h8(all_rows, version)
        published = PUBLISHED_A_SHARE_H8[version]
        if published is None or math.isnan(derived):
            drift_abs: float | None = None
            halts = False
        else:
            drift_abs = abs(derived - published)
            halts = drift_abs > RE_ANCHOR_DRIFT_TOLERANCE
        out.append(
            ReAnchorRow(
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


def _write_audit_summary_csv(
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
    agreement: AgreementSummary,
    re_anchor: list[ReAnchorRow],
    verdict: str,
    locked_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "key", "value"])
        for r in re_anchor:
            for field_name, value in (
                ("derived", r.a_share_h8_derived),
                ("published", r.a_share_h8_published),
                ("drift_abs", r.drift_abs),
                ("n_runs", r.n_runs_contributing),
                ("halts", r.halts),
            ):
                writer.writerow(
                    ["reanchor", f"{r.version}/h{r.hazard}/{field_name}", _format_value(value)]
                )
        for s in summaries_a + summaries_b:
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
                    ["paired_d", f"{s.label}/{s.observable}/{field_name}", _format_value(value)]
                )
        writer.writerow(["agreement", "rate", _format_value(agreement.agreement_rate)])
        writer.writerow(["agreement", "n_runs_well_defined", str(agreement.n_runs_well_defined)])
        writer.writerow(["agreement", "n_runs_match", str(agreement.n_runs_match)])
        writer.writerow(["verdict", "verdict", verdict])
        writer.writerow(["verdict", "locked_phrase", locked_phrase])


def _write_audit_log(
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
    agreement: AgreementSummary,
    re_anchor: list[ReAnchorRow],
    verdict: str,
    locked_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=== v0.48 sensor_radius -> space -> readiness bridge ===\n")
    lines.append("Re-anchor (per (version, h=8)):\n")
    for r in re_anchor:
        published_str = "—" if r.a_share_h8_published is None else f"{r.a_share_h8_published:.3f}"
        derived_str = "nan" if math.isnan(r.a_share_h8_derived) else f"{r.a_share_h8_derived:.3f}"
        drift_str = "—" if r.drift_abs is None else f"{r.drift_abs:.4f}"
        halt_str = " HALT" if r.halts else ""
        lines.append(
            f"  {r.version} h={r.hazard}  n={r.n_runs_contributing:>2}  "
            f"derived={derived_str}  published={published_str}  drift={drift_str}{halt_str}\n"
        )
    lines.append("\nLabel A (high_sensor_radius_lineage) — paired_d per primary observable:\n")
    for s in summaries_a:
        lines.append(_observable_line(s))
    lines.append(
        "\nLabel B (high_tick50_readiness_fraction_lineage) — paired_d per primary observable:\n"
    )
    for s in summaries_b:
        lines.append(_observable_line(s))
    rate_str = "nan" if math.isnan(agreement.agreement_rate) else f"{agreement.agreement_rate:.3f}"
    lines.append(
        f"\nLabel A / Label B agreement: "
        f"{agreement.n_runs_match}/{agreement.n_runs_well_defined} "
        f"(rate={rate_str})\n"
    )
    lines.append(f"\nVerdict: {verdict}\n")
    lines.append(f'Locked phrase fired: "{locked_phrase}"\n')
    path.write_text("".join(lines))


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
        f"  {s.observable:<38} sign={sign_label}  d={d_str}  signed_d={signed_str}  "
        f"n={s.n_runs_contributing:>2}  "
        f"delta_mean={mean_str}  sd={sd_str}  min={min_str}  max={max_str}{flag}\n"
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0915 — orchestrator threads sweep + aggregation + paired_d (x2 labels x3 observables) + agreement + re-anchor + verdict + I/O.
    """Run the full v0.48 audit, writing outputs under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== v0.48 sensor_radius -> space -> readiness bridge ===")
    print(f"Corpus: A_null only across {list(SEEDS_BY_VERSION)}; hazards={HAZARDS}")
    print(f"Total runs: {sum(len(s) for s in SEEDS_BY_VERSION.values()) * len(HAZARDS)}")
    print(
        "Primary observables: "
        + ", ".join(f"{n} ({'+' if s > 0 else '-'})" for n, s in PRIMARY_OBSERVABLES)
    )
    print()

    all_rows: list[PerLineageRow] = []
    runs_meta: list[tuple[str, int, int]] = []

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        for version, seeds in SEEDS_BY_VERSION.items():
            for hazard in HAZARDS:
                for seed in seeds:
                    capture = _run_one_a_null_run(version, seed, hazard, runs_root)
                    rows = _aggregate_per_lineage(capture)
                    all_rows.extend(rows)
                    runs_meta.append((version, seed, hazard))
                    a_top = next(
                        (r.lineage_id for r in rows if r.is_high_sensor_radius_lineage),
                        None,
                    )
                    b_top = next(
                        (r.lineage_id for r in rows if r.is_high_tick50_readiness_fraction_lineage),
                        None,
                    )
                    print(f"  {version} h={hazard:>2} seed={seed:>2}  a_top={a_top}  b_top={b_top}")

    print()
    summaries_a = [
        _summarise_observable(
            observable=name,
            sign=sign,
            label=LABEL_A_NAME,
            label_field=LABEL_A_FIELD,
            all_rows=all_rows,
            runs=runs_meta,
        )
        for (name, sign) in PRIMARY_OBSERVABLES
    ]
    summaries_b = [
        _summarise_observable(
            observable=name,
            sign=sign,
            label=LABEL_B_NAME,
            label_field=LABEL_B_FIELD,
            all_rows=all_rows,
            runs=runs_meta,
        )
        for (name, sign) in PRIMARY_OBSERVABLES
    ]
    agreement = _compute_agreement(all_rows)
    re_anchor = _check_re_anchor(all_rows)

    drift_halt_version: str | None = next((r.version for r in re_anchor if r.halts), None)
    if drift_halt_version is not None:
        verdict = VERDICT_HALT_DRIFT
        locked_phrase = LOCKED_PHRASES[VERDICT_HALT_DRIFT].format(version=drift_halt_version)
    else:
        verdict = _evaluate_verdict(summaries_a, summaries_b)
        locked_phrase = LOCKED_PHRASES[verdict]

    per_lineage_path = out_dir / "per_run_per_lineage_spatial.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)
    _write_audit_summary_csv(
        summaries_a,
        summaries_b,
        agreement,
        re_anchor,
        verdict,
        locked_phrase,
        audit_summary_path,
    )
    _write_audit_log(
        summaries_a,
        summaries_b,
        agreement,
        re_anchor,
        verdict,
        locked_phrase,
        audit_log_path,
    )

    print("Re-anchor (per version, h=8):")
    for r in re_anchor:
        published_str = "—" if r.a_share_h8_published is None else f"{r.a_share_h8_published:.3f}"
        derived_str = "nan" if math.isnan(r.a_share_h8_derived) else f"{r.a_share_h8_derived:.3f}"
        drift_str = "—" if r.drift_abs is None else f"{r.drift_abs:.4f}"
        halt_str = " HALT" if r.halts else ""
        print(
            f"  {r.version:<7} n={r.n_runs_contributing:>2}  "
            f"derived={derived_str}  published={published_str}  drift={drift_str}{halt_str}"
        )

    print()
    print("Label A (high_sensor_radius_lineage) — paired_d per primary observable:")
    for s in summaries_a:
        print(_observable_line(s).rstrip("\n"))
    print()
    print("Label B (high_tick50_readiness_fraction_lineage) — paired_d per primary observable:")
    for s in summaries_b:
        print(_observable_line(s).rstrip("\n"))

    rate_str = "nan" if math.isnan(agreement.agreement_rate) else f"{agreement.agreement_rate:.3f}"
    print(
        f"\nLabel A / Label B agreement: "
        f"{agreement.n_runs_match}/{agreement.n_runs_well_defined} "
        f"(rate={rate_str})"
    )

    print()
    print(f"Verdict: {verdict}")
    print(f'Locked phrase: "{locked_phrase}"')
    print()
    print(f"Wrote {per_lineage_path}")
    print(f"Wrote {audit_summary_path}")
    print(f"Wrote {audit_log_path}")

    if verdict in {VERDICT_HALT_OPPOSITE, VERDICT_HALT_DRIFT}:
        raise V048ReducerError(locked_phrase)
    return verdict, locked_phrase


def main() -> None:
    parser = argparse.ArgumentParser(description="v0.48 sensor_radius spatial bridge audit")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.48-spatial-bridge"),
        help="Directory for v0.48 outputs (default: runs/v0.48-spatial-bridge).",
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
