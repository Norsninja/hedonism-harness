"""v0.46 tick-50 readiness decomposition (post-hoc reducer).

Pre-reg: [[docs/experiments/fear_hunger_v0.46.md]]. Question: is the
eventual post-50 dominant lineage already advantaged at tick 50 by
reproduction readiness, energy state, or pre-50 reproductive momentum?

Corpus (locked): A_null arm only across v0.42 / v0.43R / v0.44 / v0.45,
hazards {0, 8}, seeds 41..72 (8 per version, disjoint). 64 runs total.

Decomposition (locked):
  1. pre50_reproductive_momentum_count  (expected sign +)
  2. tick50_above_threshold_fraction    (expected sign +)
  3. tick50_mean_energy                 (expected sign +)

Effect-size rule (locked):
  per_run_delta = top_lineage_value - mean(non_top_lineage_values)
  paired_d      = mean(per_run_delta) / stdev(per_run_delta, ddof=1)
  fires         iff paired_d >= +0.5
  halts         iff paired_d <= -0.5

Verdicts (locked):
  >= 2/3 fire AND 0/3 halt   → READINESS_PREDICTS_DOMINANCE
  exactly 1/3 fires AND 0/3 halt → READINESS_PARTIALLY_PREDICTIVE
  0/3 fire AND 0/3 halt      → READINESS_NOT_PREDICTIVE
  any halts                  → READINESS_OPPOSITE_SIGN_HALT
  re-anchor drift > 1e-3 (v0.42 / v0.44 / v0.45 only) → CORPUS_REDERIVE_DRIFT_HALT

Tick-50 state-capture path (locked, post-correction): in-simulation
``tick_observer`` snapshot during deterministic re-execution of each
A_null (version, seed, hazard) tuple under that version's locked V0_25
anchor + A_null arm config. Exact by construction; no events.jsonl
arithmetic.

Conservation framing (unchanged from v0.45): no ``src/`` modifications,
no new sweep arms, no modifications to prior reducer or audit scripts.

Usage:
    uv run python scripts/v0_46_tick50_readiness_audit.py
    uv run python scripts/v0_46_tick50_readiness_audit.py --out-dir runs/v0.46-readiness
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

from hedonism_harness.core.events import AgentBorn, AteFood, HazardDamageApplied, signal_for
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

# Each version's seed band — disjoint across versions per pre-reg.
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

# Hardcoded re-anchor reference values (extracted from each version's
# merged Results pre-reg-time). v0.43R has no published value (Results
# halted as non-citable per SUBSTRATE_PREFLIGHT_HALT_2); excluded from
# the halt protocol but its derived value is logged.
PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5

EXPECTED_FOUNDERS: int = 5

# Verdicts (locked).
VERDICT_PREDICTS = "READINESS_PREDICTS_DOMINANCE"
VERDICT_PARTIAL = "READINESS_PARTIALLY_PREDICTIVE"
VERDICT_NOT = "READINESS_NOT_PREDICTIVE"
VERDICT_HALT_OPPOSITE = "READINESS_OPPOSITE_SIGN_HALT"
VERDICT_HALT_DRIFT = "CORPUS_REDERIVE_DRIFT_HALT"

# Locked phrases (verbatim per pre-reg).
LOCKED_PHRASES: dict[str, str] = {
    VERDICT_PREDICTS: ("Tick-50 readiness predicts post-50 dominance on the modern A_null corpus."),
    VERDICT_PARTIAL: (
        "Tick-50 readiness is partially predictive of post-50 dominance on the modern "
        "A_null corpus; only one of three primary observables clears the locked threshold."
    ),
    VERDICT_NOT: (
        "Tick-50 readiness does not predict post-50 dominance on the modern A_null corpus; "
        "none of the three primary observables clear the locked threshold."
    ),
    VERDICT_HALT_OPPOSITE: (
        "Halt: tick-50 readiness shows a wrong-direction signal on the modern A_null "
        "corpus; the substrate-causal arc's readiness candidate is incompatible with "
        "the locked expected signs."
    ),
    VERDICT_HALT_DRIFT: (
        "Halt: A_null re-anchor drifted from the published Results value for {version}; "
        "v0.46's deterministic re-execution does not reproduce the published metric within 1e-3."
    ),
}

# Primary observable identifiers (locked order — verdict counts fires by
# index 0..2). Each observable carries an expected sign (+ for all three
# per pre-reg).
PRIMARY_OBSERVABLES: tuple[str, ...] = (
    "pre50_reproductive_momentum_count",
    "tick50_above_threshold_fraction",
    "tick50_mean_energy",
)


class V046ReducerError(Exception):
    """Halt condition raised when a v0.46 invariant is violated."""


# ---------------------------------------------------------------------------
# Per-run capture
# ---------------------------------------------------------------------------


@dataclass
class _AgentSnapshot:
    """Living agent state snapshot at tick 50."""

    agent_id: int
    lineage_id: int
    parent_id: int | None
    x: int
    y: int
    energy: float
    age: int


@dataclass
class _RunCapture:
    """Everything captured during one A_null run."""

    version: str
    seed: int
    hazard: int
    tick50_snapshot: list[_AgentSnapshot] = field(default_factory=list)
    # birth_tick by agent_id (None => founder, mapped to 0 at use-site).
    birth_tick_by_agent: dict[int, int] = field(default_factory=dict)
    # lineage_id by agent_id, including founders.
    lineage_by_agent: dict[int, int] = field(default_factory=dict)
    # tick_observer-fire count (sanity).
    n_tick50_observer_fires: int = 0
    # End-of-run living count by lineage (informational).
    end_of_run_living_by_lineage: dict[int, int] = field(default_factory=dict)
    # Reproduction-readiness predicate inputs at tick 50.
    energy_threshold: float = 0.0
    min_age: int = 0
    # Pre-50 secondary diagnostics (counts of AteFood / HazardDamageApplied
    # events with tick <= 50, by agent_id). Populated via signal listeners
    # registered at setup_observer time. Aggregated to lineage at tick 50.
    pre50_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre50_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)


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
            f"v0.46: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V046ReducerError(msg)
    return candidates[0]


def _make_setup_observer(
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    """Build a setup_observer that wires AgentBorn listener + records founders."""

    def setup(model: HHModel) -> None:
        # Enable auto_reproduction via the arm's setting (matches
        # _run_one_arm_seed semantics); the caller wires this through
        # arm.auto_reproduction in _run_one_a_null_run.
        # (We don't override here; the caller's surrounding setup is
        # already applied because run_chamber consumes the policy_factory
        # and the V0_25 anchor wires auto_reproduction via its own setup.)
        # Founder registration: model.agents already populated at this point.
        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None:
                continue
            capture.lineage_by_agent[int(body.id)] = int(body.lineage_id)
            # Founders have parent_id None and are not the subject of an
            # AgentBorn event; treat their birth_tick as 0 by convention.
            capture.birth_tick_by_agent[int(body.id)] = 0

        # Listener for non-founder births: records (agent_id -> birth_tick)
        # and (agent_id -> lineage_id). Filtered by sender=model so multiple
        # concurrent runs don't cross-pollinate.
        def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
            capture.birth_tick_by_agent[int(event.agent_id)] = int(event.tick)
            capture.lineage_by_agent[int(event.agent_id)] = int(event.lineage_id)

        signal_for(AgentBorn).connect(_on_agent_born, sender=model)
        disconnect_callbacks.append(
            lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
        )

        # Capture readiness-predicate constants from the model's config.
        capture.energy_threshold = float(model.reproduction_config.energy_threshold)
        capture.min_age = int(model.reproduction_config.min_age)

        # AteFood listener (secondary diagnostic; pre-50 food event count).
        def _on_ate_food(_sender: object, *, event: AteFood) -> None:
            if int(_sender_tick(model)) > TICK_50:
                return
            capture.pre50_food_events_by_agent[int(event.agent_id)] = (
                capture.pre50_food_events_by_agent.get(int(event.agent_id), 0) + 1
            )

        def _on_hazard_damage(_sender: object, *, event: HazardDamageApplied) -> None:
            if int(_sender_tick(model)) > TICK_50:
                return
            capture.pre50_hazard_damage_events_by_agent[int(event.agent_id)] = (
                capture.pre50_hazard_damage_events_by_agent.get(int(event.agent_id), 0) + 1
            )

        signal_for(AteFood).connect(_on_ate_food, sender=model)
        signal_for(HazardDamageApplied).connect(_on_hazard_damage, sender=model)
        disconnect_callbacks.append(
            lambda: signal_for(AteFood).disconnect(_on_ate_food, sender=model)
        )
        disconnect_callbacks.append(
            lambda: signal_for(HazardDamageApplied).disconnect(_on_hazard_damage, sender=model)
        )

    return setup


def _sender_tick(model: HHModel) -> int:
    """Return the model's current tick. Helper to keep the lambdas above tidy."""
    return int(model.tick_count)


def _make_tick50_observer(capture: _RunCapture) -> Callable[[HHModel], None]:
    """Build a tick_observer that snapshots living-agent state when tick_count == 50."""

    def observer(model: HHModel) -> None:
        if model.tick_count != TICK_50:
            return
        # Idempotent — snapshot only once even if the observer fires more
        # than once at tick 50 (it shouldn't, but guard anyway).
        if capture.n_tick50_observer_fires > 0:
            return
        capture.n_tick50_observer_fires += 1
        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None or not getattr(body, "alive", False):
                continue
            capture.tick50_snapshot.append(
                _AgentSnapshot(
                    agent_id=int(body.id),
                    lineage_id=int(body.lineage_id),
                    parent_id=(None if body.parent_id is None else int(body.parent_id)),
                    x=int(body.x),
                    y=int(body.y),
                    energy=float(body.energy),
                    age=int(body.age),
                )
            )

    return observer


def _capture_end_of_run(model: HHModel, capture: _RunCapture) -> None:
    """After the last step, record end-of-run living count by lineage."""
    for agent in model.agents:
        body = getattr(agent, "body", None)
        if body is None or not getattr(body, "alive", False):
            continue
        lid = int(body.lineage_id)
        capture.end_of_run_living_by_lineage[lid] = (
            capture.end_of_run_living_by_lineage.get(lid, 0) + 1
        )


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
    captured_model: dict[str, HHModel] = {}

    base_setup = _make_setup_observer(capture, disconnects)

    def setup(model: HHModel) -> None:
        # auto_reproduction wired here per _run_one_arm_seed semantics; the
        # arm's value is the source of truth.
        model.auto_reproduction_enabled = arm.auto_reproduction
        captured_model["model"] = model
        base_setup(model)

    use_memory = arm.memory_type is not None
    memory_type = arm.memory_type or "cell_exact"

    optional_intervention: InterventionConfig | None = None
    if arm.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=arm.intervention_kind)
    if optional_intervention is not None and optional_intervention.kind != KIND_NULL:
        msg = (
            f"v0.46 corpus must be A_null only; arm {arm.label} has "
            f"intervention_kind={arm.intervention_kind!r}"
        )
        raise V046ReducerError(msg)

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
            condition=f"v0.46-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_tick50_observer(capture),
            optional_intervention=optional_intervention,
        )
        if "model" in captured_model:
            _capture_end_of_run(captured_model["model"], capture)
    finally:
        for disconnect in disconnects:
            disconnect()

    if capture.n_tick50_observer_fires != 1:
        msg = (
            f"v0.46 invariant: tick_50 observer must fire exactly once for "
            f"{run_id}; got {capture.n_tick50_observer_fires}"
        )
        raise V046ReducerError(msg)
    if not capture.tick50_snapshot:
        msg = (
            f"v0.46 invariant: tick_50 snapshot was empty (no living agents) for "
            f"{run_id}; this should not happen on the V0_25 anchor"
        )
        raise V046ReducerError(msg)
    n_founders_recorded = sum(1 for aid, btick in capture.birth_tick_by_agent.items() if btick == 0)
    if n_founders_recorded < EXPECTED_FOUNDERS:
        msg = (
            f"v0.46 invariant: expected at least {EXPECTED_FOUNDERS} founders recorded "
            f"with birth_tick=0 for {run_id}; got {n_founders_recorded}"
        )
        raise V046ReducerError(msg)
    return capture


# ---------------------------------------------------------------------------
# Lineage-level aggregation per pre-reg
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerLineageRow:
    version: str
    seed: int
    hazard: int
    run_id: str
    lineage_id: int
    # Primary (verdict-firing).
    pre50_reproductive_momentum_count: int
    tick50_above_threshold_fraction: float  # NaN if no living agents.
    tick50_mean_energy: float  # NaN if no living agents.
    # Secondary (descriptive only).
    tick50_living_count: int
    tick50_total_energy: float
    tick50_mean_age: float  # NaN if no living agents.
    tick50_above_threshold_count: int
    tick50_neighbor_unoccupied_coarse_count: int
    pre50_food_acquired_count: int
    pre50_hazard_damage_received_count: int
    end_of_run_living: int
    # Eventual-dominance label.
    b50_count: int
    is_eventual_top: bool


PER_LINEAGE_FIELDNAMES: list[str] = [
    "version",
    "seed",
    "hazard",
    "run_id",
    "lineage_id",
    "pre50_reproductive_momentum_count",
    "tick50_above_threshold_fraction",
    "tick50_mean_energy",
    "tick50_living_count",
    "tick50_total_energy",
    "tick50_mean_age",
    "tick50_above_threshold_count",
    "tick50_neighbor_unoccupied_coarse_count",
    "pre50_food_acquired_count",
    "pre50_hazard_damage_received_count",
    "end_of_run_living",
    "b50_count",
    "is_eventual_top",
]


def _aggregate_per_lineage(capture: _RunCapture) -> tuple[list[PerLineageRow], int | None, int]:  # noqa: PLR0912, PLR0915 — per-lineage aggregation is cohesive (b50 / pre50 / living / secondary all consume the same capture; splitting would obscure the row construction).
    """Roll up per-agent tick-50 + birth-tick capture into per-lineage rows.

    Returns ``(rows, eventual_top_lineage_id_or_None, total_b50)``. If
    ``total_b50 == 0`` the run has no post-50 births and the eventual
    top lineage is None (per pre-reg NaN handling).
    """
    # Determine all lineage_ids present. Founders are guaranteed to be
    # present in lineage_by_agent (registered at setup_observer time).
    all_lineages = sorted({lid for lid in capture.lineage_by_agent.values()})

    # b50_count per lineage = #agents with birth_tick > 50 in this lineage.
    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.46: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V046ReducerError(msg)
            b50_by_lineage[lid] = b50_by_lineage.get(lid, 0) + 1
    total_b50 = sum(b50_by_lineage.values())

    # eventual_top: argmax(b50_count); tiebreak min(lineage_id). None if total_b50 == 0.
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

    # Pre-50 reproductive momentum = number of agents in lineage with
    # birth_tick <= 50 AND birth_tick > 0 (i.e., true births during pre-50
    # window, excluding founders whose birth_tick is the convention-0).
    # Founders always exist; the "momentum" is descendants.
    pre50_momentum_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if 0 < btick <= TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.46: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V046ReducerError(msg)
            pre50_momentum_by_lineage[lid] = pre50_momentum_by_lineage.get(lid, 0) + 1

    # Living-at-tick-50 by lineage.
    living_by_lineage: dict[int, list[_AgentSnapshot]] = {lid: [] for lid in all_lineages}
    for snap in capture.tick50_snapshot:
        living_by_lineage.setdefault(snap.lineage_id, []).append(snap)

    rows: list[PerLineageRow] = []
    run_id = f"{capture.version}-A_null-hzd{capture.hazard}-seed-{capture.seed}"
    for lid in all_lineages:
        living = living_by_lineage.get(lid, [])
        n_living = len(living)
        if n_living == 0:
            mean_energy = float("nan")
            mean_age = float("nan")
            total_energy = 0.0
            n_above = 0
            above_fraction = float("nan")
            valid_adj = 0
        else:
            energies = [s.energy for s in living]
            ages = [s.age for s in living]
            mean_energy = statistics.mean(energies)
            mean_age = statistics.mean(ages)
            total_energy = sum(energies)
            n_above = sum(
                1
                for s in living
                if s.energy >= capture.energy_threshold and s.age >= capture.min_age
            )
            above_fraction = n_above / n_living
            valid_adj = sum(
                _count_neighbor_unoccupied_coarse(s, capture.tick50_snapshot) for s in living
            )

        # Pre-50 food / hazard counts (sum of agent-level counts; agents not
        # in dict contribute 0).
        food_count = 0
        hazard_count = 0
        for aid, alid in capture.lineage_by_agent.items():
            if alid != lid:
                continue
            food_count += capture.pre50_food_events_by_agent.get(aid, 0)
            hazard_count += capture.pre50_hazard_damage_events_by_agent.get(aid, 0)

        rows.append(
            PerLineageRow(
                version=capture.version,
                seed=capture.seed,
                hazard=capture.hazard,
                run_id=run_id,
                lineage_id=lid,
                pre50_reproductive_momentum_count=pre50_momentum_by_lineage.get(lid, 0),
                tick50_above_threshold_fraction=above_fraction,
                tick50_mean_energy=mean_energy,
                tick50_living_count=n_living,
                tick50_total_energy=total_energy,
                tick50_mean_age=mean_age,
                tick50_above_threshold_count=n_above,
                tick50_neighbor_unoccupied_coarse_count=valid_adj,
                pre50_food_acquired_count=food_count,
                pre50_hazard_damage_received_count=hazard_count,
                end_of_run_living=capture.end_of_run_living_by_lineage.get(lid, 0),
                b50_count=b50_by_lineage.get(lid, 0),
                is_eventual_top=(eventual_top is not None and lid == eventual_top),
            )
        )
    return rows, eventual_top, total_b50


def _count_neighbor_unoccupied_coarse(
    agent: _AgentSnapshot, all_living: list[_AgentSnapshot]
) -> int:
    """Coarse occupancy-only count: N/S/E/W cells around ``agent`` not held by
    another living agent at tick 50. **Does NOT** exclude WALL cells or
    out-of-bounds positions because the snapshot does not carry world
    geometry. The count therefore overestimates true reproduction-eligible
    adjacency (an "unoccupied" neighbour can be a WALL or off-grid). This is
    a secondary descriptive metric per the pre-reg; not a verdict-firing
    observable. The name "coarse" is part of the field name to flag this."""
    occupied = {(s.x, s.y) for s in all_living}
    count = 0
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = (agent.x + dx, agent.y + dy)
        if nb not in occupied:
            count += 1
    return count


# ---------------------------------------------------------------------------
# Effect-size + verdict
# ---------------------------------------------------------------------------


def _per_run_paired_delta(rows_in_run: list[PerLineageRow], observable: str) -> float | None:
    """Return ``top_lineage_value - mean(non_top_values)`` for one run, or
    None if the run cannot contribute (no eventual top, or NaN at the top
    lineage, or all non-top NaN, or only one lineage)."""
    top_rows = [r for r in rows_in_run if r.is_eventual_top]
    if len(top_rows) != 1:
        return None
    top_value = getattr(top_rows[0], observable)
    if isinstance(top_value, float) and math.isnan(top_value):
        return None
    non_top = [r for r in rows_in_run if not r.is_eventual_top]
    non_top_values = [
        getattr(r, observable)
        for r in non_top
        if not (isinstance(getattr(r, observable), float) and math.isnan(getattr(r, observable)))
    ]
    if not non_top_values:
        return None
    return float(top_value) - statistics.mean(non_top_values)


def _paired_cohens_d(deltas: list[float]) -> float:
    """One-sample Cohen's d on a delta vector. NaN if fewer than 2 deltas
    or if stdev == 0."""
    if len(deltas) < 2:
        return float("nan")
    mean = statistics.mean(deltas)
    sd = statistics.stdev(deltas)  # ddof=1
    if sd == 0:
        return float("nan")
    return mean / sd


@dataclass(frozen=True)
class ObservableSummary:
    name: str
    n_runs_contributing: int
    paired_d: float
    fires_expected: bool  # paired_d >= +0.5
    fires_wrong: bool  # paired_d <= -0.5


def _summarise_observable(
    name: str, all_rows: list[PerLineageRow], runs: list[tuple[str, int, int]]
) -> ObservableSummary:
    deltas: list[float] = []
    by_run = _index_rows_by_run(all_rows)
    for run_key in runs:
        run_rows = by_run.get(run_key, [])
        delta = _per_run_paired_delta(run_rows, name)
        if delta is not None:
            deltas.append(delta)
    d = _paired_cohens_d(deltas)
    fires_expected = (not math.isnan(d)) and d >= COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(d)) and d <= -COHENS_D_THRESHOLD
    return ObservableSummary(
        name=name,
        n_runs_contributing=len(deltas),
        paired_d=d,
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


def _evaluate_verdict(summaries: list[ObservableSummary]) -> str:
    n_fire = sum(1 for s in summaries if s.fires_expected)
    n_wrong = sum(1 for s in summaries if s.fires_wrong)
    if n_wrong > 0:
        return VERDICT_HALT_OPPOSITE
    if n_fire >= 2:
        return VERDICT_PREDICTS
    if n_fire == 1:
        return VERDICT_PARTIAL
    return VERDICT_NOT


# ---------------------------------------------------------------------------
# Re-anchor (per pre-reg)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReAnchorRow:
    version: str
    hazard: int
    n_runs_contributing: int
    a_share_h8_derived: float  # NaN if no contributing runs
    a_share_h8_published: float | None
    drift_abs: float | None  # None if no published reference
    halts: bool


def _compute_a_share_h8(all_rows: list[PerLineageRow], version: str) -> tuple[float, int]:
    """Mean over A_null h=8 runs of (max_lineage(b50) / total_b50).
    Returns (mean_share, n_runs_with_total_b50_ge_1)."""
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
    summaries: list[ObservableSummary],
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
            writer.writerow(
                [
                    "reanchor",
                    f"{r.version}/h{r.hazard}/derived",
                    _format_value(r.a_share_h8_derived),
                ]
            )
            writer.writerow(
                [
                    "reanchor",
                    f"{r.version}/h{r.hazard}/published",
                    _format_value(r.a_share_h8_published),
                ]
            )
            writer.writerow(
                [
                    "reanchor",
                    f"{r.version}/h{r.hazard}/drift_abs",
                    _format_value(r.drift_abs),
                ]
            )
            writer.writerow(
                [
                    "reanchor",
                    f"{r.version}/h{r.hazard}/n_runs",
                    str(r.n_runs_contributing),
                ]
            )
            writer.writerow(
                [
                    "reanchor",
                    f"{r.version}/h{r.hazard}/halts",
                    _format_value(r.halts),
                ]
            )
        for s in summaries:
            writer.writerow(["paired_d", f"{s.name}/d", _format_value(s.paired_d)])
            writer.writerow(["paired_d", f"{s.name}/n_runs", str(s.n_runs_contributing)])
            writer.writerow(
                ["paired_d", f"{s.name}/fires_expected", _format_value(s.fires_expected)]
            )
            writer.writerow(["paired_d", f"{s.name}/fires_wrong", _format_value(s.fires_wrong)])
        writer.writerow(["verdict", "verdict", verdict])
        writer.writerow(["verdict", "locked_phrase", locked_phrase])


def _write_audit_log(
    summaries: list[ObservableSummary],
    re_anchor: list[ReAnchorRow],
    verdict: str,
    locked_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=== v0.46 tick-50 readiness decomposition ===\n")
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
    lines.append("\nPaired Cohen's d per primary observable (threshold |d|>=0.5):\n")
    for s in summaries:
        d_str = "nan" if math.isnan(s.paired_d) else f"{s.paired_d:+.3f}"
        flag = ""
        if s.fires_expected:
            flag = " FIRES"
        if s.fires_wrong:
            flag = " WRONG-SIGN"
        lines.append(f"  {s.name:<42} d={d_str}  n={s.n_runs_contributing:>2}{flag}\n")
    lines.append(f"\nVerdict: {verdict}\n")
    lines.append(f'Locked phrase fired: "{locked_phrase}"\n')
    path.write_text("".join(lines))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0915 — orchestrator threads sweep + aggregation + paired_d + re-anchor + verdict + I/O; splitting would obscure the cross-section.
    """Run the full v0.46 audit, writing outputs under ``out_dir``.

    Returns ``(verdict, locked_phrase)``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== v0.46 tick-50 readiness decomposition ===")
    print(f"Corpus: A_null only across {list(SEEDS_BY_VERSION)}; hazards={HAZARDS}")
    print(f"Total runs: {sum(len(s) for s in SEEDS_BY_VERSION.values()) * len(HAZARDS)}")
    print()

    all_rows: list[PerLineageRow] = []
    runs_meta: list[tuple[str, int, int]] = []

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        for version, seeds in SEEDS_BY_VERSION.items():
            for hazard in HAZARDS:
                for seed in seeds:
                    capture = _run_one_a_null_run(version, seed, hazard, runs_root)
                    rows, eventual_top, total_b50 = _aggregate_per_lineage(capture)
                    all_rows.extend(rows)
                    runs_meta.append((version, seed, hazard))
                    print(
                        f"  {version} h={hazard:>2} seed={seed:>2}  "
                        f"living@50={len(capture.tick50_snapshot):>2}  "
                        f"total_b50={total_b50:>3}  "
                        f"top_lineage={eventual_top}"
                    )

    print()
    summaries = [_summarise_observable(name, all_rows, runs_meta) for name in PRIMARY_OBSERVABLES]
    re_anchor = _check_re_anchor(all_rows)

    drift_halt_version: str | None = next((r.version for r in re_anchor if r.halts), None)
    if drift_halt_version is not None:
        verdict = VERDICT_HALT_DRIFT
        locked_phrase = LOCKED_PHRASES[VERDICT_HALT_DRIFT].format(version=drift_halt_version)
    else:
        verdict = _evaluate_verdict(summaries)
        locked_phrase = LOCKED_PHRASES[verdict]

    per_lineage_path = out_dir / "per_run_per_lineage_tick50.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)
    _write_audit_summary_csv(summaries, re_anchor, verdict, locked_phrase, audit_summary_path)
    _write_audit_log(summaries, re_anchor, verdict, locked_phrase, audit_log_path)

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
    print("Paired Cohen's d per primary observable (threshold |d|>=0.5):")
    for s in summaries:
        d_str = "nan" if math.isnan(s.paired_d) else f"{s.paired_d:+.3f}"
        flag = ""
        if s.fires_expected:
            flag = " FIRES"
        if s.fires_wrong:
            flag = " WRONG-SIGN"
        print(f"  {s.name:<42} d={d_str}  n={s.n_runs_contributing:>2}{flag}")

    print()
    print(f"Verdict: {verdict}")
    print(f'Locked phrase: "{locked_phrase}"')
    print()
    print(f"Wrote {per_lineage_path}")
    print(f"Wrote {audit_summary_path}")
    print(f"Wrote {audit_log_path}")

    if verdict in {VERDICT_HALT_OPPOSITE, VERDICT_HALT_DRIFT}:
        raise V046ReducerError(locked_phrase)
    return verdict, locked_phrase


def main() -> None:
    parser = argparse.ArgumentParser(description="v0.46 tick-50 readiness audit")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.46-readiness"),
        help="Directory for v0.46 outputs (default: runs/v0.46-readiness).",
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
