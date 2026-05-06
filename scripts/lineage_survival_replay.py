"""v0.35 founder survival timing and lineage pruning replay (post-hoc).

Second post-hoc reducer over the same 96-run corpus that v0.34 reduced
(v0.25 seeds 1..8 + v0.32 seeds 9..16 + v0.33 seeds 17..24, hazard in
{0, 4, 8, 12}, tight_gradient, influx=1.0). Imports
``scripts/lineage_replay.py`` helpers additively (no modification).

Pre-reg: [[docs/experiments/fear_hunger_v0.35.md]].

Question: does increasing hazard concentrate late-window productivity
by reducing founder-line survival before tick 50 (pruning-driven), or
by allowing one surviving lineage to continue as the post-50 winner
(early-leader continuity / expansion-supported)?

Outputs four CSVs under ``runs/lineage-v0.35/``:
  - founder_timeline.csv   (per-run x founder x snapshot tick)
  - founder_extinction.csv (per-run x founder)
  - pre_post_dominance.csv (per-run)
  - pruning_summary.csv    (per-hazard aggregate + verdict)

Halt conditions (raise LineageReplayError, sourced from v0.34):
  - v0.34 helper imports fail / B_POOL_ANCHORS drift.
  - Recomputed per-run top_lineage_b50 / top_lineage_id disagrees with
    v0.34 run_summary.csv.
  - founder count != 5 (inherited from v0.34's assign_founder_lineages).
  - founders_alive_at_t0 != 5 for any run (v0.35 invariant H2c).
  - SNAPSHOT_TICKS contains a value > n_ticks for any run.

Usage:
    uv run python scripts/lineage_survival_replay.py
"""

from __future__ import annotations

import csv
import importlib.util
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Import v0.34 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _spec is not None
assert _spec.loader is not None
lr = importlib.util.module_from_spec(_spec)
sys.modules["lineage_replay"] = lr
_spec.loader.exec_module(lr)


# ---------------------------------------------------------------------------
# v0.35 configuration (locked in pre-reg before code)
# ---------------------------------------------------------------------------


SNAPSHOT_TICKS: tuple[int, ...] = (0, 25, 50, 75, 100, 150, 200)
LEADER_TICK: int = 50  # tick at which leader-by-pre-50-births is measured
B50_THRESHOLD_TICK: int = lr.B50_THRESHOLD_TICK  # == 50; reused from v0.34

# Three-way verdict thresholds (locked).
PRUNING_FOUNDER_SPREAD_THRESHOLD: float = 0.5
EXPANSION_RATE_SPREAD_THRESHOLD: float = 0.15

V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
OUT_DIR: Path = Path("runs/lineage-v0.35")

VERDICT_PRUNING = "H5_PRUNING_SUPPORTED"
VERDICT_EXPANSION = "H6_EXPANSION_SUPPORTED"
VERDICT_MIXED = "H7_MIXED_OR_UNRESOLVED"

# Locked H7 phrase; reused verbatim if the verdict fires.
LOCKED_H7_PHRASE = (
    "Late-window concentration is consistent with both pruning and expansion "
    "(or with neither) on the v0.34 corpus; the lineage-axis data does not "
    "select a single mechanism."
)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FounderTimelineRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    lineage_id: int
    snapshot_tick: int
    active: bool
    n_alive_in_lineage: int
    births_so_far: int


@dataclass(frozen=True)
class FounderExtinctionRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    lineage_id: int
    extinction_tick: int | None  # None if extant at end of run
    last_birth_tick: int
    n_members: int


@dataclass(frozen=True)
class PrePostDominanceRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    leader_lineage_id_at_tick_50: int
    leader_births_at_tick_50: int
    eventual_top_lineage_id: int | None
    eventual_top_b50: int | None
    winner_already_dominant_at_tick_50: bool | None
    n_lineages_with_post50_birth: int


@dataclass(frozen=True)
class PruningSummaryRow:
    hazard: int
    n_runs: int
    mean_founders_alive_at_t0: float
    mean_founders_alive_at_t25: float
    mean_founders_alive_at_t50: float
    mean_founders_alive_at_t75: float
    mean_founders_alive_at_t100: float
    mean_founders_alive_at_t150: float
    mean_founders_alive_at_t200: float
    median_extinction_tick: float  # NaN if no lineages extinct in window
    p_lineage_extinct_within_window: float
    winner_already_dominant_at_tick_50_rate: float  # NaN if all runs total_b50==0
    mean_n_lineages_with_post50_birth: float


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _agents_by_lineage(agent_rows: list) -> dict[int, list]:
    out: dict[int, list] = {}
    for row in agent_rows:
        out.setdefault(row.lineage_id, []).append(row)
    return out


def compute_founder_active_at_tick(agents_in_lineage: list, tick: int, n_ticks: int) -> bool:
    """Active iff exists agent with birth <= tick AND tick < (death or n_ticks).

    Half-open interval [birth_tick_normalized, death_tick or n_ticks).
    """
    for agent in agents_in_lineage:
        upper = n_ticks if agent.death_tick is None else agent.death_tick
        if agent.birth_tick_normalized <= tick < upper:
            return True
    return False


def compute_n_alive_in_lineage(agents_in_lineage: list, tick: int, n_ticks: int) -> int:
    """Count of agents in lineage alive at ``tick`` (half-open interval)."""
    n = 0
    for agent in agents_in_lineage:
        upper = n_ticks if agent.death_tick is None else agent.death_tick
        if agent.birth_tick_normalized <= tick < upper:
            n += 1
    return n


def compute_births_so_far(agents_in_lineage: list, tick: int) -> int:
    """Cumulative birth count in lineage by tick T (founders count at T>=0)."""
    return sum(1 for agent in agents_in_lineage if agent.birth_tick_normalized <= tick)


def compute_extinction_tick(agents_in_lineage: list) -> int | None:
    """Lineage is extinct iff every member has a non-null death_tick; the
    extinction tick is then ``max(death_tick)``. Returns None for extant
    lineages.
    """
    if any(agent.death_tick is None for agent in agents_in_lineage):
        return None
    return max(agent.death_tick for agent in agents_in_lineage)


def compute_last_birth_tick(agents_in_lineage: list) -> int:
    return max(agent.birth_tick_normalized for agent in agents_in_lineage)


def compute_leader_at_tick_50(agent_rows: list) -> tuple[int, int]:
    """Return (lineage_id, births_so_far) for the lineage with the highest
    pre-50 cumulative birth count. Tie-break: lowest lineage_id.

    Every lineage contributes at least its founder (birth_tick_normalized=0
    <= 50), so this is always well-defined for runs with 5 founders.
    """
    by_lineage = _agents_by_lineage(agent_rows)
    candidates: list[tuple[int, int]] = []
    for lineage_id in sorted(by_lineage):
        births = compute_births_so_far(by_lineage[lineage_id], LEADER_TICK)
        candidates.append((lineage_id, births))
    if not candidates:
        msg = "compute_leader_at_tick_50: no lineages present"
        raise lr.LineageReplayError(msg)
    # Max by births, tie-break by lowest lineage_id (sort already ascending).
    best = candidates[0]
    for lineage_id, births in candidates[1:]:
        if births > best[1]:
            best = (lineage_id, births)
    return best


def compute_eventual_top_lineage(agent_rows: list) -> tuple[int | None, int | None]:
    """Return (lineage_id, b50_count) for the lineage with the highest
    count of members born after tick 50. Tie-break: lowest lineage_id.
    Returns (None, None) when total_b50 == 0.

    Mirrors v0.34's ``summarise_run`` algorithm exactly so re-anchoring is
    structural, not coincidental.
    """
    by_lineage = _agents_by_lineage(agent_rows)
    b50_by_lineage: dict[int, int] = {}
    for lineage_id, members in by_lineage.items():
        b50_by_lineage[lineage_id] = sum(1 for a in members if a.born_after_tick_50)
    total_b50 = sum(b50_by_lineage.values())
    if total_b50 == 0:
        return None, None
    best_id = -1
    best_count = -1
    for lineage_id in sorted(b50_by_lineage):
        count = b50_by_lineage[lineage_id]
        if count > best_count:
            best_id = lineage_id
            best_count = count
    return best_id, best_count


def is_weak_monotone_non_increasing(values: list[float]) -> bool:
    return all(values[i] >= values[i + 1] for i in range(len(values) - 1))


def is_weak_monotone_non_decreasing(values: list[float]) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def evaluate_pruning_indicator(m_by_hazard: dict[int, float]) -> bool:
    values = [m_by_hazard[h] for h in lr.HAZARDS]
    monotone = is_weak_monotone_non_increasing(values)
    spread = m_by_hazard[lr.HAZARDS[0]] - m_by_hazard[lr.HAZARDS[-1]]
    return monotone and spread >= PRUNING_FOUNDER_SPREAD_THRESHOLD


def evaluate_expansion_indicator(r_by_hazard: dict[int, float]) -> bool:
    values = [r_by_hazard[h] for h in lr.HAZARDS]
    monotone = is_weak_monotone_non_decreasing(values)
    spread = r_by_hazard[lr.HAZARDS[-1]] - r_by_hazard[lr.HAZARDS[0]]
    return monotone and spread >= EXPANSION_RATE_SPREAD_THRESHOLD


def evaluate_three_way_verdict(pruning_pass: bool, expansion_pass: bool) -> str:
    if pruning_pass and not expansion_pass:
        return VERDICT_PRUNING
    if expansion_pass and not pruning_pass:
        return VERDICT_EXPANSION
    return VERDICT_MIXED


# ---------------------------------------------------------------------------
# Per-run survival pipeline
# ---------------------------------------------------------------------------


def summarise_run_survival(
    agent_rows: list,
    n_ticks: int,
    *,
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
) -> tuple[list[FounderTimelineRow], list[FounderExtinctionRow], PrePostDominanceRow]:
    """Compute v0.35 per-run records from agent_rows + n_ticks."""
    by_lineage = _agents_by_lineage(agent_rows)
    if len(by_lineage) != lr.EXPECTED_FOUNDERS:
        msg = (
            f"expected exactly {lr.EXPECTED_FOUNDERS} lineages per run; "
            f"got {len(by_lineage)} for "
            f"{source_version}/{arm_label}/seed-{seed}"
        )
        raise lr.LineageReplayError(msg)

    timeline_rows: list[FounderTimelineRow] = []
    for lineage_id in sorted(by_lineage):
        members = by_lineage[lineage_id]
        for tick in SNAPSHOT_TICKS:
            if tick > n_ticks:
                msg = (
                    f"snapshot_tick={tick} exceeds n_ticks={n_ticks} for "
                    f"{source_version}/{arm_label}/seed-{seed}"
                )
                raise lr.LineageReplayError(msg)
            n_alive = compute_n_alive_in_lineage(members, tick, n_ticks)
            timeline_rows.append(
                FounderTimelineRow(
                    source_version=source_version,
                    arm_label=arm_label,
                    hazard=hazard,
                    seed=seed,
                    lineage_id=lineage_id,
                    snapshot_tick=tick,
                    active=n_alive >= 1,
                    n_alive_in_lineage=n_alive,
                    births_so_far=compute_births_so_far(members, tick),
                )
            )

    # H2c invariant: founders_alive_at_t0 == 5.
    founders_alive_at_t0 = sum(1 for r in timeline_rows if r.snapshot_tick == 0 and r.active)
    if founders_alive_at_t0 != lr.EXPECTED_FOUNDERS:
        msg = (
            f"founders_alive_at_t0={founders_alive_at_t0} != "
            f"{lr.EXPECTED_FOUNDERS} for "
            f"{source_version}/{arm_label}/seed-{seed} "
            f"(LineageReplayError: tick-0 founder-active invariant)"
        )
        raise lr.LineageReplayError(msg)

    extinction_rows: list[FounderExtinctionRow] = []
    for lineage_id in sorted(by_lineage):
        members = by_lineage[lineage_id]
        extinction_rows.append(
            FounderExtinctionRow(
                source_version=source_version,
                arm_label=arm_label,
                hazard=hazard,
                seed=seed,
                lineage_id=lineage_id,
                extinction_tick=compute_extinction_tick(members),
                last_birth_tick=compute_last_birth_tick(members),
                n_members=len(members),
            )
        )

    leader_id, leader_births = compute_leader_at_tick_50(agent_rows)
    eventual_top_id, eventual_top_b50 = compute_eventual_top_lineage(agent_rows)
    winner_already_dominant: bool | None = (
        None if eventual_top_id is None else leader_id == eventual_top_id
    )
    n_lineages_with_post50_birth = sum(
        1 for lineage_id in by_lineage if any(a.born_after_tick_50 for a in by_lineage[lineage_id])
    )
    dominance_row = PrePostDominanceRow(
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
        leader_lineage_id_at_tick_50=leader_id,
        leader_births_at_tick_50=leader_births,
        eventual_top_lineage_id=eventual_top_id,
        eventual_top_b50=eventual_top_b50,
        winner_already_dominant_at_tick_50=winner_already_dominant,
        n_lineages_with_post50_birth=n_lineages_with_post50_birth,
    )
    return timeline_rows, extinction_rows, dominance_row


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def _mean_founders_alive_at(
    timeline_rows: list[FounderTimelineRow],
    runs_in_hazard: list[tuple[str, str, int]],
    tick: int,
) -> float:
    """Mean over runs of (count of lineages active at ``tick``)."""
    by_run: dict[tuple[str, str, int], int] = {key: 0 for key in runs_in_hazard}
    for row in timeline_rows:
        if row.snapshot_tick != tick:
            continue
        key = (row.source_version, row.arm_label, row.seed)
        if key in by_run and row.active:
            by_run[key] += 1
    return statistics.mean(by_run.values())


def aggregate_pruning_summary(
    timeline_rows: list[FounderTimelineRow],
    extinction_rows: list[FounderExtinctionRow],
    dominance_rows: list[PrePostDominanceRow],
) -> list[PruningSummaryRow]:
    runs_by_hazard: dict[int, list[tuple[str, str, int]]] = {h: [] for h in lr.HAZARDS}
    for row in dominance_rows:
        if row.hazard in runs_by_hazard:
            runs_by_hazard[row.hazard].append((row.source_version, row.arm_label, row.seed))

    extinction_by_hazard: dict[int, list[FounderExtinctionRow]] = {h: [] for h in lr.HAZARDS}
    for row in extinction_rows:
        if row.hazard in extinction_by_hazard:
            extinction_by_hazard[row.hazard].append(row)

    dominance_by_hazard: dict[int, list[PrePostDominanceRow]] = {h: [] for h in lr.HAZARDS}
    for row in dominance_rows:
        if row.hazard in dominance_by_hazard:
            dominance_by_hazard[row.hazard].append(row)

    out: list[PruningSummaryRow] = []
    for hazard in lr.HAZARDS:
        runs = runs_by_hazard[hazard]
        n_runs = len(runs)

        mean_alive = {
            tick: _mean_founders_alive_at(timeline_rows, runs, tick) for tick in SNAPSHOT_TICKS
        }

        ext_within = [
            r.extinction_tick for r in extinction_by_hazard[hazard] if r.extinction_tick is not None
        ]
        median_ext = statistics.median(ext_within) if ext_within else float("nan")
        n_lineages_total = len(extinction_by_hazard[hazard])
        p_extinct = len(ext_within) / n_lineages_total if n_lineages_total > 0 else float("nan")

        wad_values = [
            r.winner_already_dominant_at_tick_50
            for r in dominance_by_hazard[hazard]
            if r.winner_already_dominant_at_tick_50 is not None
        ]
        wad_rate = (
            statistics.mean(1 if v else 0 for v in wad_values) if wad_values else float("nan")
        )

        mean_n_post50 = (
            statistics.mean(r.n_lineages_with_post50_birth for r in dominance_by_hazard[hazard])
            if dominance_by_hazard[hazard]
            else float("nan")
        )

        out.append(
            PruningSummaryRow(
                hazard=hazard,
                n_runs=n_runs,
                mean_founders_alive_at_t0=mean_alive[0],
                mean_founders_alive_at_t25=mean_alive[25],
                mean_founders_alive_at_t50=mean_alive[50],
                mean_founders_alive_at_t75=mean_alive[75],
                mean_founders_alive_at_t100=mean_alive[100],
                mean_founders_alive_at_t150=mean_alive[150],
                mean_founders_alive_at_t200=mean_alive[200],
                median_extinction_tick=median_ext,
                p_lineage_extinct_within_window=p_extinct,
                winner_already_dominant_at_tick_50_rate=wad_rate,
                mean_n_lineages_with_post50_birth=mean_n_post50,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Re-anchor against v0.34 run_summary.csv (halts on drift)
# ---------------------------------------------------------------------------


def load_v0_34_anchors(
    path: Path = V0_34_RUN_SUMMARY,
) -> dict[tuple[str, str, int], tuple[int | None, int | None]]:
    """Load v0.34's per-run (top_lineage_b50, top_lineage_id) keyed by
    (source_version, arm_label, seed). Empty strings -> None."""
    if not path.exists():
        msg = f"v0.34 run_summary.csv missing at {path} (re-anchor unavailable)"
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], tuple[int | None, int | None]] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            top_b50 = int(row["top_lineage_b50"]) if row["top_lineage_b50"] != "" else None
            top_id = int(row["top_lineage_id"]) if row["top_lineage_id"] != "" else None
            out[key] = (top_b50, top_id)
    return out


def cross_check_top_lineage_b50_against_v0_34(
    dominance_rows: list[PrePostDominanceRow],
    anchors: dict[tuple[str, str, int], tuple[int | None, int | None]],
) -> None:
    """Halt if any per-run (eventual_top_b50, eventual_top_lineage_id)
    disagrees with v0.34's run_summary.csv. Locked re-anchor (H2)."""
    for row in dominance_rows:
        key = (row.source_version, row.arm_label, row.seed)
        if key not in anchors:
            msg = f"v0.34 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        expected_b50, expected_id = anchors[key]
        if row.eventual_top_b50 != expected_b50 or row.eventual_top_lineage_id != expected_id:
            msg = (
                f"H2 re-anchor mismatch at {key}: "
                f"v0.35 (b50={row.eventual_top_b50}, id={row.eventual_top_lineage_id}) "
                f"!= v0.34 run_summary.csv "
                f"(b50={expected_b50}, id={expected_id})"
            )
            raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Sanity check on imported v0.34 anchors
# ---------------------------------------------------------------------------


def reassert_b_pool_anchors() -> None:
    """H1b: re-assert v0.34's B_POOL_ANCHORS at reducer entry."""
    expected = {4: 312, 8: 321, 12: 312}
    if expected != lr.B_POOL_ANCHORS:
        msg = (
            f"H1b anchor mismatch: lr.B_POOL_ANCHORS={lr.B_POOL_ANCHORS} "
            f"but v0.34 pre-reg locks {expected}; halt."
        )
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------


def _format_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return repr(value)
    return str(value)


def _write_dataclass_csv(rows, path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for row in rows:
            d = asdict(row)
            writer.writerow([_format_value(d[name]) for name in fieldnames])


FOUNDER_TIMELINE_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "lineage_id",
    "snapshot_tick",
    "active",
    "n_alive_in_lineage",
    "births_so_far",
]
FOUNDER_EXTINCTION_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "lineage_id",
    "extinction_tick",
    "last_birth_tick",
    "n_members",
]
PRE_POST_DOMINANCE_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "leader_lineage_id_at_tick_50",
    "leader_births_at_tick_50",
    "eventual_top_lineage_id",
    "eventual_top_b50",
    "winner_already_dominant_at_tick_50",
    "n_lineages_with_post50_birth",
]
PRUNING_SUMMARY_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "mean_founders_alive_at_t0",
    "mean_founders_alive_at_t25",
    "mean_founders_alive_at_t50",
    "mean_founders_alive_at_t75",
    "mean_founders_alive_at_t100",
    "mean_founders_alive_at_t150",
    "mean_founders_alive_at_t200",
    "median_extinction_tick",
    "p_lineage_extinct_within_window",
    "winner_already_dominant_at_tick_50_rate",
    "mean_n_lineages_with_post50_birth",
]


def write_outputs(
    timeline_rows: list[FounderTimelineRow],
    extinction_rows: list[FounderExtinctionRow],
    dominance_rows: list[PrePostDominanceRow],
    pruning_summary: list[PruningSummaryRow],
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "founder_timeline": out_dir / "founder_timeline.csv",
        "founder_extinction": out_dir / "founder_extinction.csv",
        "pre_post_dominance": out_dir / "pre_post_dominance.csv",
        "pruning_summary": out_dir / "pruning_summary.csv",
    }
    _write_dataclass_csv(timeline_rows, paths["founder_timeline"], FOUNDER_TIMELINE_FIELDNAMES)
    _write_dataclass_csv(
        extinction_rows, paths["founder_extinction"], FOUNDER_EXTINCTION_FIELDNAMES
    )
    _write_dataclass_csv(dominance_rows, paths["pre_post_dominance"], PRE_POST_DOMINANCE_FIELDNAMES)
    _write_dataclass_csv(pruning_summary, paths["pruning_summary"], PRUNING_SUMMARY_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Per-run loader (reuses v0.34 helpers; no modification)
# ---------------------------------------------------------------------------


def load_run_agents(
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
    run_dir: Path,
) -> tuple[list, int]:
    """Reuse v0.34 helpers to produce (agent_rows, n_ticks) for one run."""
    parsed = lr.parse_agent_lifetimes(run_dir)
    cfg = lr.parse_config(run_dir)
    if cfg["seed"] != seed:
        msg = f"seed mismatch under {run_dir}: config.json={cfg['seed']} but expected {seed}"
        raise lr.LineageReplayError(msg)
    if cfg["hazard_damage"] != hazard:
        msg = (
            f"hazard mismatch under {run_dir}: "
            f"config.json hazard_damage_default={cfg['hazard_damage']} but "
            f"expected {hazard}"
        )
        raise lr.LineageReplayError(msg)
    n_ticks = lr.parse_manifest(run_dir)
    lineage_by_agent = lr.assign_founder_lineages(parsed)
    depth_by_agent = lr.compute_generation_depths(parsed)
    agent_rows = lr.build_agent_rows(
        parsed,
        lineage_by_agent,
        depth_by_agent,
        n_ticks,
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
    )
    return agent_rows, n_ticks


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    reassert_b_pool_anchors()
    runs = lr.discover_runs()
    print(f"v0.35 lineage_survival_replay: {len(runs)} runs discovered", flush=True)

    anchors = load_v0_34_anchors()
    print(f"  loaded {len(anchors)} v0.34 run-summary anchors", flush=True)

    all_timeline: list[FounderTimelineRow] = []
    all_extinction: list[FounderExtinctionRow] = []
    all_dominance: list[PrePostDominanceRow] = []
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, n_ticks = load_run_agents(source_version, arm_label, hazard, seed, run_dir)
        timeline_rows, extinction_rows, dominance_row = summarise_run_survival(
            agent_rows,
            n_ticks,
            source_version=source_version,
            arm_label=arm_label,
            hazard=hazard,
            seed=seed,
        )
        all_timeline.extend(timeline_rows)
        all_extinction.extend(extinction_rows)
        all_dominance.append(dominance_row)

    cross_check_top_lineage_b50_against_v0_34(all_dominance, anchors)

    pruning_summary = aggregate_pruning_summary(all_timeline, all_extinction, all_dominance)

    paths = write_outputs(all_timeline, all_extinction, all_dominance, pruning_summary)

    m_by_hazard = {ps.hazard: ps.mean_founders_alive_at_t50 for ps in pruning_summary}
    r_by_hazard = {ps.hazard: ps.winner_already_dominant_at_tick_50_rate for ps in pruning_summary}
    pruning_pass = evaluate_pruning_indicator(m_by_hazard)
    expansion_pass = evaluate_expansion_indicator(r_by_hazard)
    verdict = evaluate_three_way_verdict(pruning_pass, expansion_pass)

    print()
    print("Pruning summary (one row per hazard):")
    print(
        f"  {'hazard':>6} {'n':>3} "
        f"{'fa_t0':>6} {'fa_t25':>7} {'fa_t50':>7} {'fa_t75':>7} "
        f"{'fa_t100':>8} {'fa_t150':>8} {'fa_t200':>8} "
        f"{'med_ext':>8} {'p_ext':>6} {'wad_rate':>9} {'n_post50':>9}"
    )
    for ps in pruning_summary:
        med_val = ps.median_extinction_tick
        med = "nan" if isinstance(med_val, float) and math.isnan(med_val) else f"{med_val:.0f}"
        wad = (
            "nan"
            if math.isnan(ps.winner_already_dominant_at_tick_50_rate)
            else f"{ps.winner_already_dominant_at_tick_50_rate:.3f}"
        )
        print(
            f"  {ps.hazard:>6d} {ps.n_runs:>3d} "
            f"{ps.mean_founders_alive_at_t0:>6.3f} "
            f"{ps.mean_founders_alive_at_t25:>7.3f} "
            f"{ps.mean_founders_alive_at_t50:>7.3f} "
            f"{ps.mean_founders_alive_at_t75:>7.3f} "
            f"{ps.mean_founders_alive_at_t100:>8.3f} "
            f"{ps.mean_founders_alive_at_t150:>8.3f} "
            f"{ps.mean_founders_alive_at_t200:>8.3f} "
            f"{med:>8} "
            f"{ps.p_lineage_extinct_within_window:>6.3f} "
            f"{wad:>9} "
            f"{ps.mean_n_lineages_with_post50_birth:>9.3f}"
        )

    print()
    print(
        f"  pruning indicator (m(0)>=m(4)>=m(8)>=m(12) AND "
        f"m(0)-m(12)>={PRUNING_FOUNDER_SPREAD_THRESHOLD}): {pruning_pass}"
    )
    spread_m = m_by_hazard[lr.HAZARDS[0]] - m_by_hazard[lr.HAZARDS[-1]]
    print(
        f"    observed: m(0)={m_by_hazard[0]:.3f}, "
        f"m(12)={m_by_hazard[12]:.3f}, spread={spread_m:.3f}"
    )
    print(
        f"  expansion indicator (r(0)<=r(4)<=r(8)<=r(12) AND "
        f"r(12)-r(0)>={EXPANSION_RATE_SPREAD_THRESHOLD}): {expansion_pass}"
    )
    spread_r = r_by_hazard[lr.HAZARDS[-1]] - r_by_hazard[lr.HAZARDS[0]]
    print(
        f"    observed: r(0)={r_by_hazard[0]:.3f}, "
        f"r(12)={r_by_hazard[12]:.3f}, spread={spread_r:.3f}"
    )

    print()
    print(f"  v0.35 verdict: {verdict}")
    if verdict == VERDICT_MIXED:
        print(f'    locked phrase: "{LOCKED_H7_PHRASE}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
