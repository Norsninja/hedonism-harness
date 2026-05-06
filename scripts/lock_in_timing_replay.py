"""v0.37 dominance-timing decomposition reducer (post-hoc, fourth reducer).

Decomposes v0.35's H6 EXPANSION-SUPPORTED finding (early-leader continuity
strengthening with hazard, wad_rate 0.458 -> 0.708 -> 0.750 -> 0.792)
into two distinct timing-locus mechanisms:

  - Earlier-eventual-winner-lock-in: O1 mean_winner_first_leader_tick(h)
    declines monotonically with hazard; the eventual winner reaches
    birth-count leadership earlier under hazard.
  - Stabler-early-leadership: O2 mean_leader_turnover_count_25_to_100(h)
    declines monotonically with hazard; the early-leadership contest
    (whoever holds it transiently) is less churny under hazard.

These are NOT the same mechanism. O1 is winner-centric; O2/O3 are
leader-centric. The four-way verdict (H5 / H6 / H7 / H8) keeps them
disambiguated.

Imports v0.34 + v0.35 helpers via ``importlib.util`` (no modification).
Re-anchors against v0.34's ``run_summary.csv:top_lineage_id`` AND v0.35's
``pre_post_dominance.csv:eventual_top_lineage_id`` (both must match
byte-identical for every (source_version, arm_label, seed); drift
halts).

Pre-reg: [[docs/experiments/fear_hunger_v0.37.md]].

Locked observables:
  O1 winner_first_leader_tick      (driver, expected down with hazard)
  O2 leader_turnover_count_25_100  (driver, expected down with hazard)
  O3 margin_rank1_minus_rank2_at50 (supporting only)
Locked thresholds:
  O1 spread (mean(0)-mean(12)) >= 25 ticks
  O2 spread (mean(0)-mean(12)) >= 0.25
  O3 spread (mean(12)-mean(0)) >= 1.0  (NOT verdict-firing)
Sentinel: O1 = n_ticks (= 200) when winner never leads pre-end.
Tie-break: lowest lineage_id.

Outputs four CSVs under ``runs/lineage-v0.37/``:
  - per_run.csv             (per (run), 96 rows expected)
  - per_hazard.csv          (per hazard, 4 rows)
  - indicator_summary.csv   (3 rows: O1/O2/O3)
  - verdict.csv             (single row)

Usage:
    uv run python scripts/lock_in_timing_replay.py
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


LEADER_TICK_O3: int = 50
O2_SNAPSHOT_TICKS: tuple[int, ...] = (25, 50, 75, 100)

O1_SPREAD_THRESHOLD: int = 25
O2_SPREAD_THRESHOLD: float = 0.25
O3_SPREAD_THRESHOLD: float = 1.0

EXPECTED_N_TICKS: int = 200

V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_PRE_POST_DOMINANCE: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
OUT_DIR: Path = Path("runs/lineage-v0.37")

VERDICT_EARLIER = "H5_EARLIER_WINNER_LOCK_IN"
VERDICT_STABLER = "H6_STABLER_EARLY_LEADERSHIP"
VERDICT_COMPOUND = "H7_COMPOUND_LOCK_IN"
VERDICT_UNRESOLVED = "H8_UNRESOLVED"

LOCKED_H5_PHRASE = (
    "Eventual-winner lock-in occurs earlier with hazard on the v0.34 "
    "corpus; early-leadership turnover does not separate. Correlational; "
    "not a mechanism declaration."
)
LOCKED_H6_PHRASE = (
    "Early-leadership turnover drops with hazard on the v0.34 corpus; "
    "eventual-winner timing does not separate. This supports a "
    "stabler-early-competition timing locus rather than earlier winner "
    "emergence. Correlational; not a mechanism declaration."
)
LOCKED_H7_PHRASE = (
    "Both eventual-winner timing and early-leadership stability tighten "
    "with hazard on the v0.34 corpus. Compound timing locus; "
    "correlational; not a mechanism declaration."
)
LOCKED_H8_PHRASE = (
    "Neither eventual-winner-timing nor early-leadership-turnover "
    "indicators separate with hazard on the v0.34 corpus; the "
    "early-leader-continuity rise observed in v0.35 is not resolved by "
    "this lens. Descendant-trait drift remains the canonical v0.38 "
    "candidate."
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
    eventual_top_lineage_id: int | None
    o1_winner_first_leader_tick: int
    o2_leader_turnover_count_25_to_100: int
    o3_rank1_births: int
    o3_rank2_births: int
    o3_margin: int
    never_leads_flag: bool
    rank2_zero_flag: bool
    L25: int
    L50: int
    L75: int
    L100: int


@dataclass(frozen=True)
class PerHazardRow:
    hazard: int
    n_runs: int
    n_never_leads: int
    n_no_winner: int
    mean_o1: float
    mean_o2: float
    mean_o3: float


@dataclass(frozen=True)
class IndicatorSummaryRow:
    observable: str  # "O1" | "O2" | "O3"
    verdict_role: str  # "driver" | "supporting"
    monotone_pass: bool
    spread_value: float
    spread_threshold: float
    threshold_passes: bool
    indicator_passes: bool


@dataclass(frozen=True)
class VerdictRow:
    verdict: str
    locked_phrase: str
    firing_indicators: str  # "" for H8


# ---------------------------------------------------------------------------
# Per-tick leader (parameterised over arbitrary t)
# ---------------------------------------------------------------------------


def leader_at_tick(agent_rows: list, tick: int) -> int:
    """Return lineage_id with max births_so_far at ``tick``; lowest
    lineage_id wins ties. Mirrors v0.35.compute_leader_at_tick_50 but
    parameterised over arbitrary t.
    """
    by_lineage = ls._agents_by_lineage(agent_rows)
    best_id: int | None = None
    best_count = -1
    for lineage_id in sorted(by_lineage):
        c = ls.compute_births_so_far(by_lineage[lineage_id], tick)
        if c > best_count:
            best_id = lineage_id
            best_count = c
    if best_id is None:
        msg = "leader_at_tick: no lineages present"
        raise lr.LineageReplayError(msg)
    return best_id


# ---------------------------------------------------------------------------
# Per-run observables
# ---------------------------------------------------------------------------


def compute_o1(agent_rows: list, winner_id: int, n_ticks: int) -> int:
    """Smallest tick t in [0, n_ticks) where leader_at_tick(t) == winner_id;
    sentinel ``n_ticks`` when winner never leads pre-end."""
    for t in range(n_ticks):
        if leader_at_tick(agent_rows, t) == winner_id:
            return t
    return n_ticks


def compute_o2(agent_rows: list) -> int:
    """Count of pairs in {(25,50),(50,75),(75,100)} where leader changes;
    range [0, 3]."""
    leaders = [leader_at_tick(agent_rows, t) for t in O2_SNAPSHOT_TICKS]
    return sum(1 for i in range(len(leaders) - 1) if leaders[i] != leaders[i + 1])


def compute_o3(agent_rows: list) -> tuple[int, int, int, bool]:
    """Return (rank1_births, rank2_births, margin, rank2_zero_flag) at
    tick 50. Rank order: descending births_so_far, lowest lineage_id
    breaks ties. Margin floored at 0."""
    by_lineage = ls._agents_by_lineage(agent_rows)
    pairs: list[tuple[int, int]] = []
    for lineage_id in sorted(by_lineage):
        c = ls.compute_births_so_far(by_lineage[lineage_id], LEADER_TICK_O3)
        pairs.append((lineage_id, c))
    pairs.sort(key=lambda p: (-p[1], p[0]))
    r1 = pairs[0][1] if pairs else 0
    r2 = pairs[1][1] if len(pairs) > 1 else 0
    return r1, r2, max(0, r1 - r2), r2 == 0


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
) -> dict[tuple[str, str, int], int | None]:
    """Load v0.35 eventual_top_lineage_id keyed by (source_version,
    arm_label, seed)."""
    if not path.exists():
        msg = (
            f"v0.35 pre_post_dominance.csv missing at {path} "
            f"(re-anchor unavailable; run scripts/lineage_survival_replay.py first)"
        )
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], int | None] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            raw = row["eventual_top_lineage_id"]
            out[key] = int(raw) if raw != "" else None
    return out


def cross_check_double_anchor(
    derived_top_by_run: dict[tuple[str, str, int], int | None],
    v34_anchors: dict[tuple[str, str, int], int | None],
    v35_anchors: dict[tuple[str, str, int], int | None],
) -> None:
    """Halt if derived top_lineage_id differs from v0.34 OR v0.35 anchors."""
    for key, derived in derived_top_by_run.items():
        if key not in v34_anchors:
            msg = f"v0.34 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if key not in v35_anchors:
            msg = f"v0.35 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if derived != v34_anchors[key]:
            msg = (
                f"H2a v0.34 re-anchor mismatch at {key}: "
                f"derived={derived} != v0.34 top_lineage_id={v34_anchors[key]}"
            )
            raise lr.LineageReplayError(msg)
        if derived != v35_anchors[key]:
            msg = (
                f"H2b v0.35 re-anchor mismatch at {key}: "
                f"derived={derived} != v0.35 eventual_top_lineage_id={v35_anchors[key]}"
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
    """Read sidecars + reduce to a single PerRunRow."""
    agent_rows, n_ticks = ls.load_run_agents(source_version, arm_label, hazard, seed, run_dir)
    if n_ticks != EXPECTED_N_TICKS:
        msg = (
            f"H2d n_ticks drift at {run_dir}: "
            f"manifest n_ticks={n_ticks} but v0.37 locks {EXPECTED_N_TICKS}"
        )
        raise lr.LineageReplayError(msg)
    winner_id, _ = ls.compute_eventual_top_lineage(agent_rows)
    if winner_id is None:
        # No winner (total_b50 == 0); defensive placeholder. Not expected on
        # this corpus per v0.34 n_runs_total_b50_zero == 0 per hazard.
        return PerRunRow(
            source_version=source_version,
            arm_label=arm_label,
            hazard=hazard,
            seed=seed,
            n_ticks=n_ticks,
            eventual_top_lineage_id=None,
            o1_winner_first_leader_tick=n_ticks,
            o2_leader_turnover_count_25_to_100=0,
            o3_rank1_births=0,
            o3_rank2_births=0,
            o3_margin=0,
            never_leads_flag=True,
            rank2_zero_flag=True,
            L25=0,
            L50=0,
            L75=0,
            L100=0,
        )
    o1 = compute_o1(agent_rows, winner_id, n_ticks)
    o2 = compute_o2(agent_rows)
    r1, r2, margin, rank2_zero = compute_o3(agent_rows)
    return PerRunRow(
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
        n_ticks=n_ticks,
        eventual_top_lineage_id=winner_id,
        o1_winner_first_leader_tick=o1,
        o2_leader_turnover_count_25_to_100=o2,
        o3_rank1_births=r1,
        o3_rank2_births=r2,
        o3_margin=margin,
        never_leads_flag=(o1 == n_ticks),
        rank2_zero_flag=rank2_zero,
        L25=leader_at_tick(agent_rows, 25),
        L50=leader_at_tick(agent_rows, 50),
        L75=leader_at_tick(agent_rows, 75),
        L100=leader_at_tick(agent_rows, 100),
    )


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def aggregate_per_hazard(per_run_rows: list[PerRunRow]) -> list[PerHazardRow]:
    """Aggregate to one PerHazardRow per hazard in lr.HAZARDS order."""
    by_hazard: dict[int, list[PerRunRow]] = {h: [] for h in lr.HAZARDS}
    for row in per_run_rows:
        if row.hazard in by_hazard:
            by_hazard[row.hazard].append(row)
    out: list[PerHazardRow] = []
    for hazard in lr.HAZARDS:
        rows = by_hazard[hazard]
        n_runs = len(rows)
        n_never = sum(1 for r in rows if r.never_leads_flag)
        n_no_winner = sum(1 for r in rows if r.eventual_top_lineage_id is None)
        if rows:
            mean_o1 = statistics.mean(r.o1_winner_first_leader_tick for r in rows)
            mean_o2 = statistics.mean(r.o2_leader_turnover_count_25_to_100 for r in rows)
            mean_o3 = statistics.mean(r.o3_margin for r in rows)
        else:
            mean_o1 = float("nan")
            mean_o2 = float("nan")
            mean_o3 = float("nan")
        out.append(
            PerHazardRow(
                hazard=hazard,
                n_runs=n_runs,
                n_never_leads=n_never,
                n_no_winner=n_no_winner,
                mean_o1=mean_o1,
                mean_o2=mean_o2,
                mean_o3=mean_o3,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Indicator + verdict evaluation
# ---------------------------------------------------------------------------


def _build_indicator(
    observable: str,
    verdict_role: str,
    means_in_hazard_order: list[float],
    spread_threshold: float,
    *,
    direction_down_with_hazard: bool,
) -> IndicatorSummaryRow:
    if any(math.isnan(v) for v in means_in_hazard_order):
        return IndicatorSummaryRow(
            observable=observable,
            verdict_role=verdict_role,
            monotone_pass=False,
            spread_value=float("nan"),
            spread_threshold=spread_threshold,
            threshold_passes=False,
            indicator_passes=False,
        )
    if direction_down_with_hazard:
        monotone = ls.is_weak_monotone_non_increasing(means_in_hazard_order)
        spread = means_in_hazard_order[0] - means_in_hazard_order[-1]
    else:
        monotone = ls.is_weak_monotone_non_decreasing(means_in_hazard_order)
        spread = means_in_hazard_order[-1] - means_in_hazard_order[0]
    threshold_passes = spread >= spread_threshold
    return IndicatorSummaryRow(
        observable=observable,
        verdict_role=verdict_role,
        monotone_pass=monotone,
        spread_value=spread,
        spread_threshold=spread_threshold,
        threshold_passes=threshold_passes,
        indicator_passes=monotone and threshold_passes,
    )


def evaluate_indicators(per_hazard_rows: list[PerHazardRow]) -> list[IndicatorSummaryRow]:
    """Return three IndicatorSummaryRow (O1, O2, O3) using locked rules."""
    by_hazard = {row.hazard: row for row in per_hazard_rows}
    o1_means = [by_hazard[h].mean_o1 for h in lr.HAZARDS]
    o2_means = [by_hazard[h].mean_o2 for h in lr.HAZARDS]
    o3_means = [by_hazard[h].mean_o3 for h in lr.HAZARDS]
    return [
        _build_indicator(
            "O1", "driver", o1_means, O1_SPREAD_THRESHOLD, direction_down_with_hazard=True
        ),
        _build_indicator(
            "O2", "driver", o2_means, O2_SPREAD_THRESHOLD, direction_down_with_hazard=True
        ),
        _build_indicator(
            "O3", "supporting", o3_means, O3_SPREAD_THRESHOLD, direction_down_with_hazard=False
        ),
    ]


def evaluate_verdict(
    indicators: list[IndicatorSummaryRow],
) -> tuple[str, str, list[str]]:
    """Four-way verdict: H5/H6/H7/H8 driven by O1 + O2 only."""
    by_obs = {ind.observable: ind for ind in indicators}
    o1_passes = by_obs["O1"].indicator_passes
    o2_passes = by_obs["O2"].indicator_passes
    if o1_passes and o2_passes:
        return VERDICT_COMPOUND, LOCKED_H7_PHRASE, ["O1", "O2"]
    if o1_passes:
        return VERDICT_EARLIER, LOCKED_H5_PHRASE, ["O1"]
    if o2_passes:
        return VERDICT_STABLER, LOCKED_H6_PHRASE, ["O2"]
    return VERDICT_UNRESOLVED, LOCKED_H8_PHRASE, []


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
    "eventual_top_lineage_id",
    "o1_winner_first_leader_tick",
    "o2_leader_turnover_count_25_to_100",
    "o3_rank1_births",
    "o3_rank2_births",
    "o3_margin",
    "never_leads_flag",
    "rank2_zero_flag",
    "L25",
    "L50",
    "L75",
    "L100",
]
PER_HAZARD_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "n_never_leads",
    "n_no_winner",
    "mean_o1",
    "mean_o2",
    "mean_o3",
]
INDICATOR_SUMMARY_FIELDNAMES: list[str] = [
    "observable",
    "verdict_role",
    "monotone_pass",
    "spread_value",
    "spread_threshold",
    "threshold_passes",
    "indicator_passes",
]
VERDICT_FIELDNAMES: list[str] = ["verdict", "locked_phrase", "firing_indicators"]


def write_outputs(
    per_run_rows: list[PerRunRow],
    per_hazard_rows: list[PerHazardRow],
    indicator_rows: list[IndicatorSummaryRow],
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
    _write_dataclass_csv(indicator_rows, paths["indicator_summary"], INDICATOR_SUMMARY_FIELDNAMES)
    _write_dataclass_csv([verdict_row], paths["verdict"], VERDICT_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    reassert_b_pool_anchors()
    runs = lr.discover_runs()
    print(f"v0.37 lock_in_timing_replay: {len(runs)} runs discovered", flush=True)

    v34_anchors = load_v0_34_anchors()
    v35_anchors = load_v0_35_anchors()
    print(
        f"  loaded {len(v34_anchors)} v0.34 anchors, {len(v35_anchors)} v0.35 anchors",
        flush=True,
    )

    per_run_rows: list[PerRunRow] = []
    derived_top_by_run: dict[tuple[str, str, int], int | None] = {}
    for source_version, arm_label, hazard, seed, run_dir in runs:
        row = summarise_run(source_version, arm_label, hazard, seed, run_dir)
        per_run_rows.append(row)
        derived_top_by_run[(source_version, arm_label, seed)] = row.eventual_top_lineage_id

    cross_check_double_anchor(derived_top_by_run, v34_anchors, v35_anchors)

    per_hazard_rows = aggregate_per_hazard(per_run_rows)
    indicator_rows = evaluate_indicators(per_hazard_rows)
    verdict, phrase, firing = evaluate_verdict(indicator_rows)
    verdict_row = VerdictRow(
        verdict=verdict,
        locked_phrase=phrase,
        firing_indicators=",".join(firing),
    )

    paths = write_outputs(per_run_rows, per_hazard_rows, indicator_rows, verdict_row)

    print()
    print("Per-hazard summary:")
    print(
        f"  {'hazard':>6} {'n_runs':>6} {'n_never':>8} {'n_no_win':>8} "
        f"{'mean_o1':>10} {'mean_o2':>10} {'mean_o3':>10}"
    )
    for row in per_hazard_rows:
        print(
            f"  {row.hazard:>6d} {row.n_runs:>6d} "
            f"{row.n_never_leads:>8d} {row.n_no_winner:>8d} "
            f"{row.mean_o1:>10.3f} {row.mean_o2:>10.3f} {row.mean_o3:>10.3f}",
            flush=True,
        )

    print()
    print("Indicator summary:")
    print(
        f"  {'obs':>3} {'role':>11} {'mono':>5} "
        f"{'spread':>8} {'thresh':>7} {'th_pass':>8} {'passes':>7}"
    )
    for r in indicator_rows:
        print(
            f"  {r.observable:>3} {r.verdict_role:>11} {r.monotone_pass!s:>5} "
            f"{r.spread_value:>8.3f} {r.spread_threshold:>7.3f} "
            f"{r.threshold_passes!s:>8} {r.indicator_passes!s:>7}",
            flush=True,
        )

    print()
    print(f"  v0.37 verdict: {verdict}")
    if firing:
        print(f"    firing indicators: {', '.join(firing)}")
    print(f'    locked phrase: "{phrase}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
