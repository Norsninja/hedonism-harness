"""v0.38 leader post-50 reproductive advantage replay (post-hoc, fifth reducer).

Tests whether tick-50 leadership confers a hazard-amplified post-50
reproductive advantage on the v0.34 corpus. Specifically: does the
difference between the tick-50 leader's post-50 birth count
(``b50``) and the mean ``b50`` of the four non-leader lineages rise
monotonically with hazard, with a meaningful spread?

The question is the second-order follow-up to v0.37 H6
STABLER-EARLY-LEADERSHIP: v0.37 showed early-leadership turnover
drops with hazard and tick-50 margin widens; v0.38 asks whether
that structural stability cashes out as measurable post-50
reproductive advantage that strengthens with hazard.

Imports v0.34 + v0.35 helpers via ``importlib.util`` (no
modification). Re-anchors against v0.34's
``run_summary.csv:top_lineage_id`` AND v0.35's
``pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
eventual_top_lineage_id)``. v0.36 / v0.37 reducers are NOT imported
(structurally orthogonal).

Pre-reg: [[docs/experiments/fear_hunger_v0.38.md]].

Locked observable:
  O1 leader_post50_advantage = b50(leader) - mean(b50(non-leaders))
                               4-lineage non-leader denominator.
                               Driver. Expected up with hazard.
Locked threshold:
  spread (mean(12) - mean(0)) >= 1.5  for H5 LEADER-ADVANTAGE-AMPLIFIED
  spread (mean(0) - mean(12)) >= 1.5  for H7 LEADER-ADVANTAGE-INVERTED
  Otherwise H6 LEADER-ADVANTAGE-FLAT.

Supporting (do NOT fire verdict):
  O2 mean_O1 split by wad status (wad=True vs wad=False)
  O3 mean_winner_overtake in wad=False subset

Tie-break: lowest lineage_id (mirrors v0.35 / v0.37).

Outputs four CSVs under ``runs/lineage-v0.38/``:
  - per_run.csv             (per (run), 96 rows expected)
  - per_hazard.csv          (per hazard, 4 rows)
  - indicator_summary.csv   (1 row: O1)
  - verdict.csv             (single row)

Usage:
    uv run python scripts/leader_advantage_replay.py
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
# Import v0.34 + v0.35 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_LS_PATH = Path(__file__).parent / "lineage_survival_replay.py"

_lr_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _lr_spec is not None
assert _lr_spec.loader is not None
lr = importlib.util.module_from_spec(_lr_spec)
sys.modules["lineage_replay"] = lr
_lr_spec.loader.exec_module(lr)

_ls_spec = importlib.util.spec_from_file_location("lineage_survival_replay", _LS_PATH)
assert _ls_spec is not None
assert _ls_spec.loader is not None
ls = importlib.util.module_from_spec(_ls_spec)
sys.modules["lineage_survival_replay"] = ls
_ls_spec.loader.exec_module(ls)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg before code)
# ---------------------------------------------------------------------------


LEADER_TICK: int = 50
O1_SPREAD_THRESHOLD: float = 1.5  # post-50 birth-count units
N_NON_LEADERS: int = 4
EXPECTED_N_TICKS: int = 200

V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_PRE_POST_DOMINANCE: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
OUT_DIR: Path = Path("runs/lineage-v0.38")

VERDICT_AMPLIFIED = "H5_LEADER_ADVANTAGE_AMPLIFIED"
VERDICT_FLAT = "H6_LEADER_ADVANTAGE_FLAT"
VERDICT_INVERTED = "H7_LEADER_ADVANTAGE_INVERTED"

LOCKED_H5_PHRASE = (
    "Tick-50 leadership's post-50 birth advantage rises with hazard on the "
    "v0.34 corpus; v0.37's stabler-early-leadership signal cashes out as a "
    "hazard-amplified post-50 reproductive advantage. Correlational; not a "
    "mechanism declaration."
)
LOCKED_H6_PHRASE = (
    "Tick-50 leadership's post-50 birth advantage does not strengthen with "
    "hazard on the v0.34 corpus. v0.37's stabler-early-leadership signal "
    "does not map cleanly to a hazard-amplified post-50 reproductive "
    "advantage."
)
LOCKED_H7_PHRASE = (
    "Tick-50 leadership's post-50 birth advantage decreases with hazard on "
    "the v0.34 corpus. Mechanistically surprising; requires fresh-stream "
    "calibration before interpretation."
)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerRunRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    n_ticks: int
    leader_lineage_id: int
    eventual_top_lineage_id: int | None
    wad_flag: bool
    b50_lineage_0: int
    b50_lineage_1: int
    b50_lineage_2: int
    b50_lineage_3: int
    b50_lineage_4: int
    leader_b50: int
    non_leader_mean_b50: float
    leader_advantage: float
    winner_b50: int
    winner_overtake: int


@dataclass(frozen=True)
class PerHazardRow:
    hazard: int
    n_runs: int
    n_wad_true: int
    n_wad_false: int
    n_no_winner: int
    mean_o1: float
    mean_o1_wad_true: float
    mean_o1_wad_false: float
    mean_winner_overtake_wad_false: float


@dataclass(frozen=True)
class IndicatorSummaryRow:
    observable: str  # "O1"
    verdict_role: str  # "driver"
    monotone_pass_up: bool
    monotone_pass_down: bool
    spread_value: float  # signed: mean(12) - mean(0)
    spread_threshold: float
    threshold_passes_up: bool
    threshold_passes_down: bool
    indicator_passes: bool  # True iff up- or down-direction full rule fires
    verdict_direction: str  # "up" | "down" | "none"


@dataclass(frozen=True)
class VerdictRow:
    verdict: str
    locked_phrase: str
    firing_indicator: str  # "O1_up" | "O1_down" | "" for H6


# ---------------------------------------------------------------------------
# Per-run reduction helpers
# ---------------------------------------------------------------------------


def per_lineage_b50(agent_rows: list) -> dict[int, int]:
    """Count agents with born_after_tick_50 per lineage_id; returns dict
    keyed by all 5 lineage ids (0..4) with default 0."""
    out: dict[int, int] = {lid: 0 for lid in range(lr.EXPECTED_FOUNDERS)}
    for a in agent_rows:
        if a.born_after_tick_50:
            out[a.lineage_id] = out.get(a.lineage_id, 0) + 1
    return out


def compute_leader_advantage(
    b50_by_lineage: dict[int, int], leader_id: int
) -> tuple[int, float, float]:
    """Return (leader_b50, non_leader_mean_b50, leader_advantage)."""
    leader_b50 = b50_by_lineage[leader_id]
    non_leader_b50 = [b50_by_lineage[lid] for lid in sorted(b50_by_lineage) if lid != leader_id]
    if not non_leader_b50:
        msg = "compute_leader_advantage: no non-leader lineages"
        raise lr.LineageReplayError(msg)
    non_leader_mean = statistics.mean(non_leader_b50)
    return leader_b50, non_leader_mean, leader_b50 - non_leader_mean


def compute_winner_overtake(
    b50_by_lineage: dict[int, int],
    leader_id: int,
    winner_id: int | None,
    *,
    wad: bool,
) -> tuple[int, int]:
    """Return (winner_b50, winner_overtake). Both 0 when winner is None or
    wad is True (winner == leader => no overtake by definition)."""
    if winner_id is None:
        return 0, 0
    winner_b50 = b50_by_lineage[winner_id]
    if wad:
        return winner_b50, 0
    return winner_b50, winner_b50 - b50_by_lineage[leader_id]


# ---------------------------------------------------------------------------
# Anchor loaders / cross-check
# ---------------------------------------------------------------------------


def load_v0_34_anchors(
    path: Path = V0_34_RUN_SUMMARY,
) -> dict[tuple[str, str, int], int | None]:
    """Load v0.34 top_lineage_id keyed by (source_version, arm_label, seed)."""
    if not path.exists():
        msg = f"v0.34 run_summary.csv missing at {path} (re-anchor unavailable)"
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], int | None] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            top_id = int(row["top_lineage_id"]) if row["top_lineage_id"] != "" else None
            out[key] = top_id
    return out


def load_v0_35_anchors(
    path: Path = V0_35_PRE_POST_DOMINANCE,
) -> dict[tuple[str, str, int], tuple[int, int | None]]:
    """Load v0.35 (leader_lineage_id_at_tick_50, eventual_top_lineage_id)
    keyed by (source_version, arm_label, seed). leader column is always
    int (every run has a tick-50 leader); eventual_top column is int |
    None."""
    if not path.exists():
        msg = (
            f"v0.35 pre_post_dominance.csv missing at {path} "
            f"(re-anchor unavailable; run scripts/lineage_survival_replay.py first)"
        )
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], tuple[int, int | None]] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            leader_id = int(row["leader_lineage_id_at_tick_50"])
            raw_eventual = row["eventual_top_lineage_id"]
            eventual_id = int(raw_eventual) if raw_eventual != "" else None
            out[key] = (leader_id, eventual_id)
    return out


def cross_check_double_anchor(
    derived_by_run: dict[tuple[str, str, int], tuple[int, int | None]],
    v34_anchors: dict[tuple[str, str, int], int | None],
    v35_anchors: dict[tuple[str, str, int], tuple[int, int | None]],
) -> None:
    """Halt if derived (leader_id, top_id) differs from v0.34 OR v0.35."""
    for key, (derived_leader, derived_top) in derived_by_run.items():
        if key not in v34_anchors:
            msg = f"v0.34 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if key not in v35_anchors:
            msg = f"v0.35 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if derived_top != v34_anchors[key]:
            msg = (
                f"H2a v0.34 re-anchor mismatch at {key}: "
                f"derived top={derived_top} != v0.34 top_lineage_id={v34_anchors[key]}"
            )
            raise lr.LineageReplayError(msg)
        v35_leader, v35_top = v35_anchors[key]
        if derived_leader != v35_leader:
            msg = (
                f"H2b v0.35 leader re-anchor mismatch at {key}: "
                f"derived leader={derived_leader} != v0.35 "
                f"leader_lineage_id_at_tick_50={v35_leader}"
            )
            raise lr.LineageReplayError(msg)
        if derived_top != v35_top:
            msg = (
                f"H2b v0.35 winner re-anchor mismatch at {key}: "
                f"derived top={derived_top} != v0.35 "
                f"eventual_top_lineage_id={v35_top}"
            )
            raise lr.LineageReplayError(msg)


def reassert_b_pool_anchors() -> None:
    """H1b: re-assert v0.34's locked B_POOL_ANCHORS + EXPECTED_FOUNDERS."""
    expected = {4: 312, 8: 321, 12: 312}
    if expected != lr.B_POOL_ANCHORS:
        msg = (
            f"H1b anchor mismatch: lr.B_POOL_ANCHORS={lr.B_POOL_ANCHORS} "
            f"but v0.34 pre-reg locks {expected}; halt."
        )
        raise lr.LineageReplayError(msg)
    if lr.EXPECTED_FOUNDERS != 5:
        msg = f"EXPECTED_FOUNDERS drift: {lr.EXPECTED_FOUNDERS} != 5"
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run reduction
# ---------------------------------------------------------------------------


def summarise_run(
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
    run_dir: Path,
) -> PerRunRow:
    agent_rows, n_ticks = ls.load_run_agents(source_version, arm_label, hazard, seed, run_dir)
    if n_ticks != EXPECTED_N_TICKS:
        msg = (
            f"H2d n_ticks drift at {run_dir}: "
            f"manifest n_ticks={n_ticks} but v0.38 locks {EXPECTED_N_TICKS}"
        )
        raise lr.LineageReplayError(msg)
    leader_id, _ = ls.compute_leader_at_tick_50(agent_rows)
    winner_id, _ = ls.compute_eventual_top_lineage(agent_rows)
    wad = winner_id is not None and leader_id == winner_id
    b50 = per_lineage_b50(agent_rows)
    leader_b50, non_leader_mean, leader_adv = compute_leader_advantage(b50, leader_id)
    winner_b50, overtake = compute_winner_overtake(b50, leader_id, winner_id, wad=wad)
    return PerRunRow(
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
        n_ticks=n_ticks,
        leader_lineage_id=leader_id,
        eventual_top_lineage_id=winner_id,
        wad_flag=wad,
        b50_lineage_0=b50[0],
        b50_lineage_1=b50[1],
        b50_lineage_2=b50[2],
        b50_lineage_3=b50[3],
        b50_lineage_4=b50[4],
        leader_b50=leader_b50,
        non_leader_mean_b50=non_leader_mean,
        leader_advantage=leader_adv,
        winner_b50=winner_b50,
        winner_overtake=overtake,
    )


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def _safe_mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def aggregate_per_hazard(per_run_rows: list[PerRunRow]) -> list[PerHazardRow]:
    by_hazard: dict[int, list[PerRunRow]] = {h: [] for h in lr.HAZARDS}
    for row in per_run_rows:
        if row.hazard in by_hazard:
            by_hazard[row.hazard].append(row)
    out: list[PerHazardRow] = []
    for hazard in lr.HAZARDS:
        rows = by_hazard[hazard]
        wad_true = [r for r in rows if r.wad_flag]
        wad_false = [r for r in rows if not r.wad_flag]
        no_winner = [r for r in rows if r.eventual_top_lineage_id is None]
        # Note: no_winner runs are NOT excluded from the all-runs O1 mean
        # (the leader exists regardless of whether there's an eventual winner;
        # the leader_advantage is still well-defined). They ARE excluded from
        # wad-buckets because wad is False when winner is None.
        out.append(
            PerHazardRow(
                hazard=hazard,
                n_runs=len(rows),
                n_wad_true=len(wad_true),
                n_wad_false=len(wad_false),
                n_no_winner=len(no_winner),
                mean_o1=_safe_mean([r.leader_advantage for r in rows]),
                mean_o1_wad_true=_safe_mean([r.leader_advantage for r in wad_true]),
                mean_o1_wad_false=_safe_mean([r.leader_advantage for r in wad_false]),
                mean_winner_overtake_wad_false=_safe_mean(
                    [float(r.winner_overtake) for r in wad_false]
                ),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Indicator + verdict evaluation
# ---------------------------------------------------------------------------


def evaluate_indicator(per_hazard_rows: list[PerHazardRow]) -> IndicatorSummaryRow:
    by_hazard = {row.hazard: row for row in per_hazard_rows}
    means = [by_hazard[h].mean_o1 for h in lr.HAZARDS]
    if any(math.isnan(v) for v in means):
        return IndicatorSummaryRow(
            observable="O1",
            verdict_role="driver",
            monotone_pass_up=False,
            monotone_pass_down=False,
            spread_value=float("nan"),
            spread_threshold=O1_SPREAD_THRESHOLD,
            threshold_passes_up=False,
            threshold_passes_down=False,
            indicator_passes=False,
            verdict_direction="none",
        )
    monotone_up = ls.is_weak_monotone_non_decreasing(means)
    monotone_down = ls.is_weak_monotone_non_increasing(means)
    spread = means[-1] - means[0]  # signed: mean(12) - mean(0)
    threshold_passes_up = spread >= O1_SPREAD_THRESHOLD
    threshold_passes_down = (-spread) >= O1_SPREAD_THRESHOLD
    passes_up = monotone_up and threshold_passes_up
    passes_down = monotone_down and threshold_passes_down
    if passes_up:
        direction = "up"
    elif passes_down:
        direction = "down"
    else:
        direction = "none"
    return IndicatorSummaryRow(
        observable="O1",
        verdict_role="driver",
        monotone_pass_up=monotone_up,
        monotone_pass_down=monotone_down,
        spread_value=spread,
        spread_threshold=O1_SPREAD_THRESHOLD,
        threshold_passes_up=threshold_passes_up,
        threshold_passes_down=threshold_passes_down,
        indicator_passes=passes_up or passes_down,
        verdict_direction=direction,
    )


def evaluate_verdict(indicator: IndicatorSummaryRow) -> tuple[str, str, str]:
    if indicator.verdict_direction == "up":
        return VERDICT_AMPLIFIED, LOCKED_H5_PHRASE, "O1_up"
    if indicator.verdict_direction == "down":
        return VERDICT_INVERTED, LOCKED_H7_PHRASE, "O1_down"
    return VERDICT_FLAT, LOCKED_H6_PHRASE, ""


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


PER_RUN_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "n_ticks",
    "leader_lineage_id",
    "eventual_top_lineage_id",
    "wad_flag",
    "b50_lineage_0",
    "b50_lineage_1",
    "b50_lineage_2",
    "b50_lineage_3",
    "b50_lineage_4",
    "leader_b50",
    "non_leader_mean_b50",
    "leader_advantage",
    "winner_b50",
    "winner_overtake",
]
PER_HAZARD_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "n_wad_true",
    "n_wad_false",
    "n_no_winner",
    "mean_o1",
    "mean_o1_wad_true",
    "mean_o1_wad_false",
    "mean_winner_overtake_wad_false",
]
INDICATOR_SUMMARY_FIELDNAMES: list[str] = [
    "observable",
    "verdict_role",
    "monotone_pass_up",
    "monotone_pass_down",
    "spread_value",
    "spread_threshold",
    "threshold_passes_up",
    "threshold_passes_down",
    "indicator_passes",
    "verdict_direction",
]
VERDICT_FIELDNAMES: list[str] = ["verdict", "locked_phrase", "firing_indicator"]


def write_outputs(
    per_run_rows: list[PerRunRow],
    per_hazard_rows: list[PerHazardRow],
    indicator_row: IndicatorSummaryRow,
    verdict_row: VerdictRow,
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_run": out_dir / "per_run.csv",
        "per_hazard": out_dir / "per_hazard.csv",
        "indicator_summary": out_dir / "indicator_summary.csv",
        "verdict": out_dir / "verdict.csv",
    }
    _write_dataclass_csv(per_run_rows, paths["per_run"], PER_RUN_FIELDNAMES)
    _write_dataclass_csv(per_hazard_rows, paths["per_hazard"], PER_HAZARD_FIELDNAMES)
    _write_dataclass_csv([indicator_row], paths["indicator_summary"], INDICATOR_SUMMARY_FIELDNAMES)
    _write_dataclass_csv([verdict_row], paths["verdict"], VERDICT_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    reassert_b_pool_anchors()
    runs = lr.discover_runs()
    print(f"v0.38 leader_advantage_replay: {len(runs)} runs discovered", flush=True)

    v34_anchors = load_v0_34_anchors()
    v35_anchors = load_v0_35_anchors()
    print(
        f"  loaded {len(v34_anchors)} v0.34 anchors, {len(v35_anchors)} v0.35 anchors",
        flush=True,
    )

    per_run_rows: list[PerRunRow] = []
    derived_by_run: dict[tuple[str, str, int], tuple[int, int | None]] = {}
    for source_version, arm_label, hazard, seed, run_dir in runs:
        row = summarise_run(source_version, arm_label, hazard, seed, run_dir)
        per_run_rows.append(row)
        derived_by_run[(source_version, arm_label, seed)] = (
            row.leader_lineage_id,
            row.eventual_top_lineage_id,
        )

    cross_check_double_anchor(derived_by_run, v34_anchors, v35_anchors)

    per_hazard_rows = aggregate_per_hazard(per_run_rows)
    indicator_row = evaluate_indicator(per_hazard_rows)
    verdict, phrase, firing = evaluate_verdict(indicator_row)
    verdict_row = VerdictRow(verdict=verdict, locked_phrase=phrase, firing_indicator=firing)

    paths = write_outputs(per_run_rows, per_hazard_rows, indicator_row, verdict_row)

    print()
    print("Per-hazard summary:")
    print(
        f"  {'haz':>3} {'n':>3} {'wT':>3} {'wF':>3} {'nW':>3}  "
        f"{'mean_O1':>9} {'mean_O1_wT':>11} {'mean_O1_wF':>11} {'mean_overt_wF':>14}"
    )
    for row in per_hazard_rows:
        print(
            f"  {row.hazard:>3d} {row.n_runs:>3d} "
            f"{row.n_wad_true:>3d} {row.n_wad_false:>3d} {row.n_no_winner:>3d}  "
            f"{row.mean_o1:>9.3f} "
            f"{row.mean_o1_wad_true:>11.3f} "
            f"{row.mean_o1_wad_false:>11.3f} "
            f"{row.mean_winner_overtake_wad_false:>14.3f}",
            flush=True,
        )

    print()
    print("Indicator (O1):")
    print(
        f"  monotone_up   = {indicator_row.monotone_pass_up}\n"
        f"  monotone_down = {indicator_row.monotone_pass_down}\n"
        f"  spread        = {indicator_row.spread_value:+.3f}  "
        f"(threshold {indicator_row.spread_threshold} in either direction)\n"
        f"  threshold_up  = {indicator_row.threshold_passes_up}\n"
        f"  threshold_dn  = {indicator_row.threshold_passes_down}\n"
        f"  indicator     = {indicator_row.indicator_passes} "
        f"({indicator_row.verdict_direction})"
    )

    print()
    print(f"  v0.38 verdict: {verdict}")
    if firing:
        print(f"    firing indicator: {firing}")
    print(f'    locked phrase: "{phrase}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
