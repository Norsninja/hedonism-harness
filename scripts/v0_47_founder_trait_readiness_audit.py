"""v0.47 founder-trait predictivity for tick-50 readiness (post-hoc reducer).

Pre-reg: [[docs/experiments/fear_hunger_v0.47.md]]. Question: are founder
traits at tick 0 predictive of which lineage carries the highest tick-50
reproduction-readiness *fraction* on the modern A_null corpus?

Corpus (locked, same as v0.46): A_null arm only across v0.42 / v0.43R /
v0.44 / v0.45, hazards {0, 8}, seeds 41..72 (8 per version, disjoint).
64 runs total.

Primary traits (locked, with mechanistic-prior expected signs):
  reproduction_drive  (+)
  metabolic_rate      (-)
  sensor_radius       (+)

Primary label (verdict-firing):
  high_tick50_readiness_fraction_lineage =
      argmax_lineage(tick50_above_threshold_fraction)
      tiebreak: fraction -> count -> min(lineage_id)

Secondary label (descriptive, cannot fire verdict):
  high_tick50_readiness_count_lineage =
      argmax_lineage(tick50_above_threshold_count)
      tiebreak: count -> fraction -> min(lineage_id)

Effect-size rule (locked, sign-aware):
  per_run_delta_T = founder_T(label_lineage) - mean(founder_T(non_label_lineages))
  paired_d_T      = mean(per_run_delta_T) / stdev(per_run_delta_T, ddof=1)
  fires           iff paired_d_T * sign_T >= +0.5
  halts           iff paired_d_T * sign_T <= -0.5

Verdicts (locked):
  >= 2/3 fire AND 0/3 halt   -> READINESS_TRAITS_PREDICT_READINESS
  exactly 1/3 fires AND 0/3 halt -> READINESS_TRAITS_PARTIALLY_PREDICTIVE
  0/3 fire AND 0/3 halt      -> READINESS_TRAITS_NOT_PREDICTIVE
  any halts                  -> READINESS_TRAITS_OPPOSITE_SIGN_HALT
  re-anchor drift > 1e-3 (v0.42 / v0.44 / v0.45 only) -> CORPUS_REDERIVE_DRIFT_HALT

Conservation framing (unchanged from v0.46): no ``src/`` modifications,
no new sweep arms, no modifications to prior reducer or audit scripts.
v0.36's ``trait_replay.py`` remains byte-identical to its merged form.

Usage:
    uv run python scripts/v0_47_founder_trait_readiness_audit.py
    uv run python scripts/v0_47_founder_trait_readiness_audit.py \
        --out-dir runs/v0.47-readiness-traits
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

from hedonism_harness.core.events import AgentBorn, signal_for
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

# Each version's seed band - disjoint across versions per pre-reg.
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

# Hardcoded re-anchor reference values per v0.46's pre-reg.
PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5

EXPECTED_FOUNDERS: int = 5

# Primary traits with locked expected signs.
PRIMARY_TRAITS: tuple[tuple[str, int], ...] = (
    ("reproduction_drive", +1),
    ("metabolic_rate", -1),
    ("sensor_radius", +1),
)

# Verdicts (locked).
VERDICT_PREDICTS = "READINESS_TRAITS_PREDICT_READINESS"
VERDICT_PARTIAL = "READINESS_TRAITS_PARTIALLY_PREDICTIVE"
VERDICT_NOT = "READINESS_TRAITS_NOT_PREDICTIVE"
VERDICT_HALT_OPPOSITE = "READINESS_TRAITS_OPPOSITE_SIGN_HALT"
VERDICT_HALT_DRIFT = "CORPUS_REDERIVE_DRIFT_HALT"

# Locked phrases (verbatim per pre-reg).
LOCKED_PHRASES: dict[str, str] = {
    VERDICT_PREDICTS: (
        "Founder traits at tick 0 predict tick-50 readiness on the modern A_null corpus."
    ),
    VERDICT_PARTIAL: (
        "Founder traits at tick 0 are partially predictive of tick-50 readiness on the modern "
        "A_null corpus; only one of three primary traits clears the locked threshold."
    ),
    VERDICT_NOT: (
        "Founder traits at tick 0 do not predict tick-50 readiness on the modern A_null corpus; "
        "none of the three primary traits clear the locked threshold."
    ),
    VERDICT_HALT_OPPOSITE: (
        "Halt: a primary trait shows a wrong-direction signal vs. its locked expected sign on "
        "the modern A_null corpus; the founder-trait readiness candidate is incompatible with "
        "the locked sign priors."
    ),
    VERDICT_HALT_DRIFT: (
        "Halt: A_null re-anchor drifted from the published Results value for {version}; "
        "v0.47's deterministic re-execution does not reproduce the published metric within 1e-3."
    ),
}


class V047ReducerError(Exception):
    """Halt condition raised when a v0.47 invariant is violated."""


# ---------------------------------------------------------------------------
# Per-run capture
# ---------------------------------------------------------------------------


@dataclass
class _AgentSnapshot:
    """Living agent state snapshot at tick 50."""

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
    tick50_snapshot: list[_AgentSnapshot] = field(default_factory=list)
    # birth_tick by agent_id; founders normalised to 0 by convention.
    birth_tick_by_agent: dict[int, int] = field(default_factory=dict)
    # lineage_id by agent_id.
    lineage_by_agent: dict[int, int] = field(default_factory=dict)
    # Founder traits keyed by lineage_id; populated at setup_observer time
    # by walking model.agents (founders are present pre-step, with their
    # locked unmutated initial trait draws).
    founder_traits_by_lineage: dict[int, dict[str, float]] = field(default_factory=dict)
    n_tick50_observer_fires: int = 0
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
            f"v0.47: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V047ReducerError(msg)
    return candidates[0]


def _make_setup_observer(
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    """Build a setup_observer that captures founder traits + wires AgentBorn."""

    def setup(model: HHModel) -> None:
        # Founder registration: model.agents already populated with the 5
        # founders at this point. Capture each founder's (lineage_id ->
        # primary trait values) using the locked unmutated initial draws.
        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None:
                continue
            lineage_id = int(body.lineage_id)
            capture.lineage_by_agent[int(body.id)] = lineage_id
            capture.birth_tick_by_agent[int(body.id)] = 0
            traits = body.traits
            capture.founder_traits_by_lineage[lineage_id] = {
                name: float(getattr(traits, name)) for (name, _sign) in PRIMARY_TRAITS
            }

        # Listener for non-founder births; filtered by sender=model.
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

    return setup


def _make_tick50_observer(capture: _RunCapture) -> Callable[[HHModel], None]:
    """Build a tick_observer that snapshots living-agent state at tick 50."""

    def observer(model: HHModel) -> None:
        if model.tick_count != TICK_50:
            return
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
            f"v0.47 corpus must be A_null only; arm {arm.label} has "
            f"intervention_kind={arm.intervention_kind!r}"
        )
        raise V047ReducerError(msg)

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
            condition=f"v0.47-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_tick50_observer(capture),
            optional_intervention=optional_intervention,
        )
    finally:
        for disconnect in disconnects:
            disconnect()

    if capture.n_tick50_observer_fires != 1:
        msg = (
            f"v0.47 invariant: tick_50 observer must fire exactly once for "
            f"{run_id}; got {capture.n_tick50_observer_fires}"
        )
        raise V047ReducerError(msg)
    if not capture.tick50_snapshot:
        msg = (
            f"v0.47 invariant: tick_50 snapshot was empty (no living agents) for "
            f"{run_id}; this should not happen on the V0_25 anchor"
        )
        raise V047ReducerError(msg)
    if len(capture.founder_traits_by_lineage) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.47 invariant: expected exactly {EXPECTED_FOUNDERS} founders for "
            f"{run_id}; captured traits for {len(capture.founder_traits_by_lineage)}"
        )
        raise V047ReducerError(msg)
    return capture


# ---------------------------------------------------------------------------
# Per-lineage row + label assignment per pre-reg tiebreaks
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
    tick50_above_threshold_fraction: float  # NaN when no living agents.
    tick50_above_threshold_count: int  # 0 when no living agents.
    tick50_living_count: int
    b50_count: int
    is_high_tick50_readiness_fraction_lineage: bool
    is_high_tick50_readiness_count_lineage: bool


PER_LINEAGE_FIELDNAMES: list[str] = [
    "version",
    "seed",
    "hazard",
    "run_id",
    "lineage_id",
    "founder_reproduction_drive",
    "founder_metabolic_rate",
    "founder_sensor_radius",
    "tick50_above_threshold_fraction",
    "tick50_above_threshold_count",
    "tick50_living_count",
    "b50_count",
    "is_high_tick50_readiness_fraction_lineage",
    "is_high_tick50_readiness_count_lineage",
]


def _select_fraction_label(
    candidates: list[tuple[int, float, int]],
) -> int | None:
    """``candidates`` is ``[(lineage_id, fraction, count), ...]`` for lineages
    with non-NaN fraction (i.e., at least one living agent at tick 50).
    Tiebreak: fraction -> count -> min(lineage_id). Returns None if empty."""
    if not candidates:
        return None
    best = candidates[0]
    for cand in candidates[1:]:
        # Highest fraction; on tie, highest count; on still-tie, lowest lineage_id.
        if (
            cand[1] > best[1]
            or (cand[1] == best[1] and cand[2] > best[2])
            or (cand[1] == best[1] and cand[2] == best[2] and cand[0] < best[0])
        ):
            best = cand
    return best[0]


def _select_count_label(
    candidates: list[tuple[int, int, float]],
) -> int | None:
    """``candidates`` is ``[(lineage_id, count, fraction), ...]`` over ALL
    lineages (count is well-defined as 0 when no living). Tiebreak: count
    -> fraction -> min(lineage_id). NaN fraction loses ties to non-NaN.
    Returns None if every count is 0 (no comparison possible)."""
    if not candidates:
        return None
    if all(c[1] == 0 for c in candidates):
        return None
    best = candidates[0]
    for cand in candidates[1:]:
        # Highest count; on tie, highest fraction (NaN loses); on still-tie,
        # lowest lineage_id.
        if cand[1] > best[1]:
            best = cand
        elif cand[1] == best[1]:
            cand_frac = cand[2] if not math.isnan(cand[2]) else float("-inf")
            best_frac = best[2] if not math.isnan(best[2]) else float("-inf")
            if cand_frac > best_frac or (cand_frac == best_frac and cand[0] < best[0]):
                best = cand
    return best[0]


def _aggregate_per_lineage(capture: _RunCapture) -> list[PerLineageRow]:
    """Roll up per-agent tick-50 snapshot + founder traits into per-lineage rows."""
    all_lineages = sorted(set(capture.lineage_by_agent.values()))

    # b50_count per lineage = # agents with birth_tick > 50.
    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.47: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V047ReducerError(msg)
            b50_by_lineage[lid] = b50_by_lineage.get(lid, 0) + 1

    # Living-at-tick-50 by lineage.
    living_by_lineage: dict[int, list[_AgentSnapshot]] = {lid: [] for lid in all_lineages}
    for snap in capture.tick50_snapshot:
        living_by_lineage.setdefault(snap.lineage_id, []).append(snap)

    # Per-lineage readiness counts/fractions.
    fraction_by_lineage: dict[int, float] = {}
    count_by_lineage: dict[int, int] = {}
    living_count_by_lineage: dict[int, int] = {}
    for lid in all_lineages:
        living = living_by_lineage.get(lid, [])
        n_living = len(living)
        living_count_by_lineage[lid] = n_living
        n_above = sum(
            1 for s in living if s.energy >= capture.energy_threshold and s.age >= capture.min_age
        )
        count_by_lineage[lid] = n_above
        fraction_by_lineage[lid] = (n_above / n_living) if n_living > 0 else float("nan")

    # Label assignments.
    fraction_candidates = [
        (lid, fraction_by_lineage[lid], count_by_lineage[lid])
        for lid in all_lineages
        if not math.isnan(fraction_by_lineage[lid])
    ]
    fraction_label = _select_fraction_label(fraction_candidates)

    count_candidates = [
        (lid, count_by_lineage[lid], fraction_by_lineage[lid]) for lid in all_lineages
    ]
    count_label = _select_count_label(count_candidates)

    rows: list[PerLineageRow] = []
    run_id = f"{capture.version}-A_null-hzd{capture.hazard}-seed-{capture.seed}"
    for lid in all_lineages:
        founder = capture.founder_traits_by_lineage.get(lid, {})
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
                tick50_above_threshold_fraction=fraction_by_lineage[lid],
                tick50_above_threshold_count=count_by_lineage[lid],
                tick50_living_count=living_count_by_lineage[lid],
                b50_count=b50_by_lineage.get(lid, 0),
                is_high_tick50_readiness_fraction_lineage=(
                    fraction_label is not None and lid == fraction_label
                ),
                is_high_tick50_readiness_count_lineage=(
                    count_label is not None and lid == count_label
                ),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Effect-size + verdict
# ---------------------------------------------------------------------------


def _per_run_paired_delta(
    rows_in_run: list[PerLineageRow], trait_field: str, label_field: str
) -> float | None:
    """Return ``founder_T(label_lineage) - mean(founder_T(non_label_lineages))``
    for one run, or None if the run cannot contribute."""
    label_rows = [r for r in rows_in_run if getattr(r, label_field)]
    if len(label_rows) != 1:
        return None
    label_value = getattr(label_rows[0], trait_field)
    if isinstance(label_value, float) and math.isnan(label_value):
        return None
    non_label = [r for r in rows_in_run if not getattr(r, label_field)]
    non_label_values = [
        getattr(r, trait_field)
        for r in non_label
        if not (isinstance(getattr(r, trait_field), float) and math.isnan(getattr(r, trait_field)))
    ]
    if not non_label_values:
        return None
    return float(label_value) - statistics.mean(non_label_values)


def _paired_cohens_d(deltas: list[float]) -> float:
    """One-sample Cohen's d. NaN if fewer than 2 deltas or stdev == 0."""
    if len(deltas) < 2:
        return float("nan")
    mean = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    if sd == 0:
        return float("nan")
    return mean / sd


@dataclass(frozen=True)
class TraitSummary:
    trait: str
    label: str  # "fraction" | "count"
    sign: int
    n_runs_contributing: int
    paired_d: float
    delta_mean: float
    delta_stdev: float  # NaN if fewer than 2 deltas
    delta_min: float  # NaN if zero deltas
    delta_max: float  # NaN if zero deltas
    fires_expected: bool
    fires_wrong: bool


def _summarise_trait(
    *,
    trait_name: str,
    sign: int,
    label: str,
    label_field: str,
    all_rows: list[PerLineageRow],
    runs: list[tuple[str, int, int]],
) -> TraitSummary:
    deltas: list[float] = []
    by_run = _index_rows_by_run(all_rows)
    trait_field = f"founder_{trait_name}"
    for run_key in runs:
        run_rows = by_run.get(run_key, [])
        delta = _per_run_paired_delta(run_rows, trait_field, label_field)
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
    return TraitSummary(
        trait=trait_name,
        label=label,
        sign=sign,
        n_runs_contributing=len(deltas),
        paired_d=d,
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


def _evaluate_verdict(fraction_summaries: list[TraitSummary]) -> str:
    """Verdict driven exclusively by fraction-label trait summaries."""
    n_fire = sum(1 for s in fraction_summaries if s.fires_expected)
    n_wrong = sum(1 for s in fraction_summaries if s.fires_wrong)
    if n_wrong > 0:
        return VERDICT_HALT_OPPOSITE
    if n_fire >= 2:
        return VERDICT_PREDICTS
    if n_fire == 1:
        return VERDICT_PARTIAL
    return VERDICT_NOT


# ---------------------------------------------------------------------------
# Fraction / count agreement rate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgreementSummary:
    n_runs_well_defined: int
    n_runs_match: int
    agreement_rate: float  # NaN if no well-defined runs


def _compute_agreement(all_rows: list[PerLineageRow]) -> AgreementSummary:
    by_run = _index_rows_by_run(all_rows)
    well_defined = 0
    match = 0
    for rows_in_run in by_run.values():
        frac_label = next(
            (r.lineage_id for r in rows_in_run if r.is_high_tick50_readiness_fraction_lineage),
            None,
        )
        count_label = next(
            (r.lineage_id for r in rows_in_run if r.is_high_tick50_readiness_count_lineage),
            None,
        )
        if frac_label is None or count_label is None:
            continue
        well_defined += 1
        if frac_label == count_label:
            match += 1
    rate = (match / well_defined) if well_defined > 0 else float("nan")
    return AgreementSummary(
        n_runs_well_defined=well_defined, n_runs_match=match, agreement_rate=rate
    )


# ---------------------------------------------------------------------------
# Re-anchor (per pre-reg, cross-version only)
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
    fraction_summaries: list[TraitSummary],
    count_summaries: list[TraitSummary],
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
            for field_name in ("derived", "published", "drift_abs", "n_runs", "halts"):
                value: object
                if field_name == "derived":
                    value = r.a_share_h8_derived
                elif field_name == "published":
                    value = r.a_share_h8_published
                elif field_name == "drift_abs":
                    value = r.drift_abs
                elif field_name == "n_runs":
                    value = r.n_runs_contributing
                else:
                    value = r.halts
                writer.writerow(
                    ["reanchor", f"{r.version}/h{r.hazard}/{field_name}", _format_value(value)]
                )
        for s in fraction_summaries:
            for field_name in (
                "paired_d",
                "n_runs",
                "fires_expected",
                "fires_wrong",
                "delta_mean",
                "delta_stdev",
                "delta_min",
                "delta_max",
            ):
                value = _trait_summary_field(s, field_name)
                writer.writerow(["paired_d", f"{s.trait}/{field_name}", _format_value(value)])
        for s in count_summaries:
            for field_name in (
                "paired_d",
                "n_runs",
                "fires_expected",
                "fires_wrong",
                "delta_mean",
                "delta_stdev",
                "delta_min",
                "delta_max",
            ):
                value = _trait_summary_field(s, field_name)
                writer.writerow(["paired_d_count", f"{s.trait}/{field_name}", _format_value(value)])
        writer.writerow(["agreement", "rate", _format_value(agreement.agreement_rate)])
        writer.writerow(["agreement", "n_runs_well_defined", str(agreement.n_runs_well_defined)])
        writer.writerow(["agreement", "n_runs_match", str(agreement.n_runs_match)])
        writer.writerow(["verdict", "verdict", verdict])
        writer.writerow(["verdict", "locked_phrase", locked_phrase])


def _trait_summary_field(s: TraitSummary, field_name: str) -> object:
    return {
        "paired_d": s.paired_d,
        "n_runs": s.n_runs_contributing,
        "fires_expected": s.fires_expected,
        "fires_wrong": s.fires_wrong,
        "delta_mean": s.delta_mean,
        "delta_stdev": s.delta_stdev,
        "delta_min": s.delta_min,
        "delta_max": s.delta_max,
    }[field_name]


def _write_audit_log(
    fraction_summaries: list[TraitSummary],
    count_summaries: list[TraitSummary],
    agreement: AgreementSummary,
    re_anchor: list[ReAnchorRow],
    verdict: str,
    locked_phrase: str,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=== v0.47 founder-trait predictivity for tick-50 readiness ===\n")
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
    lines.append("\nFraction-label paired_d per primary trait (PRIMARY; verdict-firing):\n")
    for s in fraction_summaries:
        lines.append(_trait_line(s))
    lines.append("\nCount-label paired_d per primary trait (descriptive; cannot fire):\n")
    for s in count_summaries:
        lines.append(_trait_line(s))
    rate_str = "nan" if math.isnan(agreement.agreement_rate) else f"{agreement.agreement_rate:.3f}"
    lines.append(
        f"\nFraction/count label agreement: "
        f"{agreement.n_runs_match}/{agreement.n_runs_well_defined} "
        f"(rate={rate_str})\n"
    )
    lines.append(f"\nVerdict: {verdict}\n")
    lines.append(f'Locked phrase fired: "{locked_phrase}"\n')
    path.write_text("".join(lines))


def _trait_line(s: TraitSummary) -> str:
    d_str = "nan" if math.isnan(s.paired_d) else f"{s.paired_d:+.3f}"
    signed = s.paired_d * s.sign if not math.isnan(s.paired_d) else float("nan")
    signed_str = "nan" if math.isnan(signed) else f"{signed:+.3f}"
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
        f"  {s.trait:<20} sign={sign_label}  d={d_str}  signed_d={signed_str}  "
        f"n={s.n_runs_contributing:>2}  "
        f"delta_mean={mean_str}  sd={sd_str}  min={min_str}  max={max_str}{flag}\n"
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0915 — orchestrator threads sweep + aggregation + paired_d (x2 labels) + agreement + re-anchor + verdict + I/O.
    """Run the full v0.47 audit, writing outputs under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== v0.47 founder-trait predictivity for tick-50 readiness ===")
    print(f"Corpus: A_null only across {list(SEEDS_BY_VERSION)}; hazards={HAZARDS}")
    print(f"Total runs: {sum(len(s) for s in SEEDS_BY_VERSION.values()) * len(HAZARDS)}")
    print(
        "Primary traits: " + ", ".join(f"{n} ({'+' if s > 0 else '-'})" for n, s in PRIMARY_TRAITS)
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
                    frac_top = next(
                        (r.lineage_id for r in rows if r.is_high_tick50_readiness_fraction_lineage),
                        None,
                    )
                    count_top = next(
                        (r.lineage_id for r in rows if r.is_high_tick50_readiness_count_lineage),
                        None,
                    )
                    print(
                        f"  {version} h={hazard:>2} seed={seed:>2}  "
                        f"living@50={len(capture.tick50_snapshot):>2}  "
                        f"frac_top={frac_top}  count_top={count_top}"
                    )

    print()
    fraction_summaries = [
        _summarise_trait(
            trait_name=name,
            sign=sign,
            label="fraction",
            label_field="is_high_tick50_readiness_fraction_lineage",
            all_rows=all_rows,
            runs=runs_meta,
        )
        for (name, sign) in PRIMARY_TRAITS
    ]
    count_summaries = [
        _summarise_trait(
            trait_name=name,
            sign=sign,
            label="count",
            label_field="is_high_tick50_readiness_count_lineage",
            all_rows=all_rows,
            runs=runs_meta,
        )
        for (name, sign) in PRIMARY_TRAITS
    ]
    agreement = _compute_agreement(all_rows)
    re_anchor = _check_re_anchor(all_rows)

    drift_halt_version: str | None = next((r.version for r in re_anchor if r.halts), None)
    if drift_halt_version is not None:
        verdict = VERDICT_HALT_DRIFT
        locked_phrase = LOCKED_PHRASES[VERDICT_HALT_DRIFT].format(version=drift_halt_version)
    else:
        verdict = _evaluate_verdict(fraction_summaries)
        locked_phrase = LOCKED_PHRASES[verdict]

    per_lineage_path = out_dir / "per_run_per_lineage.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)
    _write_audit_summary_csv(
        fraction_summaries,
        count_summaries,
        agreement,
        re_anchor,
        verdict,
        locked_phrase,
        audit_summary_path,
    )
    _write_audit_log(
        fraction_summaries,
        count_summaries,
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
    print("Fraction-label paired_d per primary trait (PRIMARY; verdict-firing):")
    for s in fraction_summaries:
        print(_trait_line(s).rstrip("\n"))
    print()
    print("Count-label paired_d per primary trait (descriptive):")
    for s in count_summaries:
        print(_trait_line(s).rstrip("\n"))
    rate_str = "nan" if math.isnan(agreement.agreement_rate) else f"{agreement.agreement_rate:.3f}"
    print()
    print(
        f"Fraction/count agreement: {agreement.n_runs_match}/{agreement.n_runs_well_defined} "
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
        raise V047ReducerError(locked_phrase)
    return verdict, locked_phrase


def main() -> None:
    parser = argparse.ArgumentParser(description="v0.47 founder-trait readiness audit")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.47-readiness-traits"),
        help="Directory for v0.47 outputs (default: runs/v0.47-readiness-traits).",
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
