"""v0.39 fresh-stream calibration of v0.38 H5 LEADER-ADVANTAGE-AMPLIFIED.

Tests whether v0.38's mean_leader_advantage(h) monotone-up + spread>=1.5
result reproduces on a fresh seed stream (25..32, n=8 per hazard) at
the same chamber / influx / hazard parameters.

Two-layer verdict:
  - Layer 1 (fresh, n=8/hazard): PRIMARY headline.
    H5_FRESH (monotone-up + spread>=1.5) /
    H6_FRESH (neither) /
    H7_FRESH (monotone-down + reverse-spread>=1.5).
  - Layer 2 (pooled, 96 old + 32 fresh = 128 runs, n=32/hazard):
    SUPPORTING. Same three-way structure.
  - Combined classification (locked headline lookup; see pre-reg
    section "Combined classification (locked headline rules)"):
    H5_FRESH_AND_POOLED / H5_FRESH_ONLY / H5_POOLED_ONLY /
    NEITHER_H5 / H7_FRESH / halt-on-impossible.

Imports v0.34 + v0.35 + v0.38 helpers via ``importlib.util`` (no
modification). Re-anchor against:
  - sealed runs/lineage-v0.34/run_summary.csv (96 rows; halt if missing)
  - sealed runs/lineage-v0.35/pre_post_dominance.csv (96 rows; halt if missing)
  - fresh runs/lineage-v0.34-fresh/run_summary.csv (32 rows; halt if missing)
  - fresh runs/lineage-v0.35-fresh/pre_post_dominance.csv (32 rows; halt if missing)

Pre-reg: [[docs/experiments/fear_hunger_v0.39.md]].

Locked observable: v0.38's leader_advantage = leader_b50 -
mean(non_leader_b50) per run; reused verbatim from
[[scripts/leader_advantage_replay.py]].
Locked threshold: spread >= 1.5 in either direction (same as v0.38;
no linear scaling for the pooled corpus since the observable is a
within-hazard mean).
Sentinel handling: inherits v0.38's compute_leader_advantage; no new
edge-case logic.

Outputs six CSVs under ``runs/lineage-v0.39/``:
  - per_run.csv             (32 rows; v0.38 PerRunRow schema)
  - per_hazard_fresh.csv    (4 rows)
  - per_hazard_pooled.csv   (4 rows)
  - verdict_fresh.csv       (1 row)
  - verdict_pooled.csv      (1 row)
  - verdict_combined.csv    (1 row)

Usage:
    uv run python scripts/v0_39_leader_advantage_fresh_replay.py
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
# Import v0.34 + v0.35 + v0.38 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_LS_PATH = Path(__file__).parent / "lineage_survival_replay.py"
_LA_PATH = Path(__file__).parent / "leader_advantage_replay.py"

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

_la_spec = importlib.util.spec_from_file_location("leader_advantage_replay", _LA_PATH)
assert _la_spec is not None
assert _la_spec.loader is not None
la = importlib.util.module_from_spec(_la_spec)
sys.modules["leader_advantage_replay"] = la
_la_spec.loader.exec_module(la)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg before code)
# ---------------------------------------------------------------------------


LEADER_TICK: int = 50
N_NON_LEADERS: int = 4
EXPECTED_N_TICKS: int = 200
SPREAD_THRESHOLD: float = 1.5

FRESH_SOURCE_VERSION: str = "v0.39"
FRESH_RUNS_ROOT: Path = Path("runs/fear-hunger-v0.39-tight_gradient/arms")
FRESH_SEEDS: tuple[int, ...] = tuple(range(25, 33))

V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_34_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_PRE_POST: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")
V0_38_PER_RUN: Path = Path("runs/lineage-v0.38/per_run.csv")

OUT_DIR: Path = Path("runs/lineage-v0.39")

EXPECTED_OLD_ROW_COUNT: int = 96
EXPECTED_FRESH_ROW_COUNT: int = 32

VERDICT_H5_FRESH = "H5_FRESH"
VERDICT_H6_FRESH = "H6_FRESH"
VERDICT_H7_FRESH = "H7_FRESH"
VERDICT_H5_POOLED = "H5_POOLED"
VERDICT_H6_POOLED = "H6_POOLED"
VERDICT_H7_POOLED = "H7_POOLED"

COMBINED_H5_FRESH_AND_POOLED = "H5_FRESH_AND_POOLED"
COMBINED_H5_FRESH_ONLY = "H5_FRESH_ONLY"
COMBINED_H5_POOLED_ONLY = "H5_POOLED_ONLY"
COMBINED_NEITHER_H5 = "NEITHER_H5"
COMBINED_H7_FRESH = "H7_FRESH_HEADLINE"
COMBINED_H6_FRESH_POOLED_DOWN = "H6_FRESH_POOLED_DOWN"

LOCKED_H5_FRESH_AND_POOLED_PHRASE = (
    "The leader post-50 advantage amplification reproduces on the "
    "fresh seed stream (25..32) and remains present in the pooled "
    "128-run corpus. This upgrades the v0.38 effect from same-corpus "
    "correlational finding to cross-stream reproducible timing-locus "
    "evidence. Not a mechanism declaration."
)
LOCKED_H5_FRESH_ONLY_PHRASE = (
    "The leader post-50 advantage amplification reproduces on the "
    "fresh seed stream (25..32) but the pooled 128-run effect does "
    "not clear the locked spread bar. The discrepancy is unexpected "
    "and requires investigation; reported as cross-stream-"
    "reproducible-with-pooled-tension. Not a mechanism declaration."
)
LOCKED_H5_POOLED_ONLY_PHRASE = (
    "The fresh seed stream (25..32) does not show monotone-up + "
    "spread->=1.5 on mean_leader_advantage. The pooled 128-run effect "
    "persists on the strength of the 96 old runs alone. v0.38's H5 "
    "LEADER-ADVANTAGE-AMPLIFIED is not reproduced on the fresh "
    "stream; it remains a same-corpus correlational finding pending "
    "further calibration."
)
LOCKED_NEITHER_H5_PHRASE = (
    "Neither the fresh stream (25..32) nor the pooled 128-run corpus "
    "clears the locked monotone-up + spread->=1.5 bar on "
    "mean_leader_advantage. v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED is "
    "not reproduced; the pooled effect collapses on inclusion of the "
    "fresh stream. The lineage arc's correlational story is marked "
    "non-reproducing on fresh-stream calibration."
)
LOCKED_H7_FRESH_HEADLINE_PHRASE = (
    "The fresh seed stream (25..32) shows monotone-down with "
    "spread->=1.5 on mean_leader_advantage - the opposite direction "
    "from v0.38. v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED is "
    "directionally contradicted on the fresh stream. The pooled "
    "effect (if any) is not the headline. Halt and investigate; the "
    "lineage arc requires re-examination."
)
LOCKED_H6_FRESH_POOLED_DOWN_PHRASE = (
    "The fresh seed stream (25..32) does not clear the locked "
    "monotone-up + spread->=1.5 bar; the pooled 128-run corpus "
    "flips to monotone-down with spread->=1.5. The lineage arc's "
    "correlational story is marked non-reproducing on fresh-stream "
    "calibration with a pooled directional flip; investigate."
)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerHazardFreshRow:
    hazard: int
    n_runs: int
    n_wad_true: int
    mean_leader_advantage: float


@dataclass(frozen=True)
class PerHazardPooledRow:
    hazard: int
    n_runs: int
    n_old: int
    n_fresh: int
    mean_leader_advantage: float


@dataclass(frozen=True)
class VerdictRow:
    verdict: str
    locked_phrase: str
    monotone_pass_up: bool
    monotone_pass_down: bool
    spread_value: float  # signed: mean(12) - mean(0)
    spread_threshold: float
    threshold_passes_up: bool
    threshold_passes_down: bool


@dataclass(frozen=True)
class VerdictCombinedRow:
    combined_classification: str
    headline_locked_phrase: str
    fresh_verdict: str
    pooled_verdict: str


# ---------------------------------------------------------------------------
# Sealed-artifact + fresh-anchor loaders
# ---------------------------------------------------------------------------


def _csv_row_count(path: Path) -> int:
    """Return the number of data rows (excluding header) in ``path``."""
    with path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return sum(1 for _ in reader)


def assert_old_corpus_sealed() -> None:
    """H2c / H2d: sealed v0.34 + v0.35 outputs exist at 96 rows each."""
    for path, label in (
        (V0_34_OLD_RUN_SUMMARY, "v0.34 old run_summary"),
        (V0_35_OLD_PRE_POST, "v0.35 old pre_post_dominance"),
    ):
        if not path.exists():
            msg = (
                f"{label} missing at {path}; rebuild via "
                f"docs/artifacts/v0.34_v0.38_local_corpus_manifest.md"
            )
            raise lr.LineageReplayError(msg)
        n = _csv_row_count(path)
        if n != EXPECTED_OLD_ROW_COUNT:
            msg = (
                f"{label} row-count drift at {path}: "
                f"got {n} but locked expected {EXPECTED_OLD_ROW_COUNT}"
            )
            raise lr.LineageReplayError(msg)


def assert_fresh_anchors_present() -> None:
    """H2a / H2b prerequisite: fresh-extension v0.34 + v0.35 outputs
    exist at 32 rows each."""
    for path, label in (
        (V0_34_FRESH_RUN_SUMMARY, "v0.34 fresh run_summary"),
        (V0_35_FRESH_PRE_POST, "v0.35 fresh pre_post_dominance"),
    ):
        if not path.exists():
            msg = (
                f"{label} missing at {path}; run "
                f"scripts/lineage_replay_v0_39_extension.py and "
                f"scripts/lineage_survival_replay_v0_39_extension.py "
                f"first"
            )
            raise lr.LineageReplayError(msg)
        n = _csv_row_count(path)
        if n != EXPECTED_FRESH_ROW_COUNT:
            msg = (
                f"{label} row-count drift at {path}: "
                f"got {n} but locked expected {EXPECTED_FRESH_ROW_COUNT}"
            )
            raise lr.LineageReplayError(msg)


def load_fresh_v0_34_anchors() -> dict[tuple[str, str, int], int | None]:
    """Load fresh v0.34 top_lineage_id keyed by
    (source_version, arm_label, seed)."""
    out: dict[tuple[str, str, int], int | None] = {}
    with V0_34_FRESH_RUN_SUMMARY.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            top_id = int(row["top_lineage_id"]) if row["top_lineage_id"] != "" else None
            out[key] = top_id
    return out


def load_fresh_v0_35_anchors() -> dict[tuple[str, str, int], tuple[int | None, int | None]]:
    """Load fresh v0.35 (leader_lineage_id_at_tick_50,
    eventual_top_lineage_id) keyed by (source_version, arm_label, seed)."""
    out: dict[tuple[str, str, int], tuple[int | None, int | None]] = {}
    with V0_35_FRESH_PRE_POST.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            leader = (
                int(row["leader_lineage_id_at_tick_50"])
                if row["leader_lineage_id_at_tick_50"] != ""
                else None
            )
            eventual = (
                int(row["eventual_top_lineage_id"])
                if row["eventual_top_lineage_id"] != ""
                else None
            )
            out[key] = (leader, eventual)
    return out


def load_v0_38_per_run_leader_advantage() -> dict[tuple[str, str, int], tuple[int, float]]:
    """Load v0.38's per-run (hazard, leader_advantage) keyed by
    (source_version, arm_label, seed). 96 entries expected.

    leader_advantage is the locked driver observable; reusing v0.38's
    sealed per_run.csv ensures the pooled aggregation uses byte-
    identical values for the old 96 runs.
    """
    if not V0_38_PER_RUN.exists():
        msg = (
            f"v0.38 per_run.csv missing at {V0_38_PER_RUN}; "
            f"rebuild via scripts/leader_advantage_replay.py"
        )
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], tuple[int, float]] = {}
    with V0_38_PER_RUN.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            hazard = int(row["hazard"])
            adv = float(row["leader_advantage"])
            out[key] = (hazard, adv)
    if len(out) != EXPECTED_OLD_ROW_COUNT:
        msg = (
            f"v0.38 per_run.csv row count {len(out)} != "
            f"{EXPECTED_OLD_ROW_COUNT}; sealed artifact has drifted"
        )
        raise lr.LineageReplayError(msg)
    return out


# ---------------------------------------------------------------------------
# Fresh-corpus discovery + per-run cross-anchor
# ---------------------------------------------------------------------------


def discover_fresh_runs() -> list[tuple[str, str, int, int, Path]]:
    """Iterate the 32 fresh (source_version, arm_label, hazard, seed,
    run_dir) tuples in deterministic sorted order: hazard -> seed."""
    out: list[tuple[str, str, int, int, Path]] = []
    for hazard in lr.HAZARDS:
        arm_label = lr.ARM_LABEL_FMT.format(hazard)
        for seed in FRESH_SEEDS:
            run_dir = FRESH_RUNS_ROOT / arm_label / f"seed-{seed}"
            out.append((FRESH_SOURCE_VERSION, arm_label, hazard, seed, run_dir))
    return out


def cross_anchor_fresh_run(
    row: la.PerRunRow,
    v34_fresh: dict[tuple[str, str, int], int | None],
    v35_fresh: dict[tuple[str, str, int], tuple[int | None, int | None]],
) -> None:
    """Halt if a fresh per-run row's derived (top_lineage_id,
    leader_lineage_id_at_tick_50, eventual_top_lineage_id) disagrees
    with the fresh-extension v0.34 + v0.35 anchors."""
    key = (row.source_version, row.arm_label, row.seed)
    if key not in v34_fresh:
        msg = f"H2a v0.34-fresh anchor missing for {key}"
        raise lr.LineageReplayError(msg)
    if key not in v35_fresh:
        msg = f"H2b v0.35-fresh anchor missing for {key}"
        raise lr.LineageReplayError(msg)
    if row.eventual_top_lineage_id != v34_fresh[key]:
        msg = (
            f"H2a v0.34-fresh re-anchor mismatch at {key}: "
            f"derived eventual_top_lineage_id={row.eventual_top_lineage_id} "
            f"!= v0.34-fresh top_lineage_id={v34_fresh[key]}"
        )
        raise lr.LineageReplayError(msg)
    leader_expected, eventual_expected = v35_fresh[key]
    if row.leader_lineage_id != leader_expected:
        msg = (
            f"H2b v0.35-fresh re-anchor mismatch at {key}: "
            f"derived leader_lineage_id={row.leader_lineage_id} "
            f"!= v0.35-fresh leader_lineage_id_at_tick_50={leader_expected}"
        )
        raise lr.LineageReplayError(msg)
    if row.eventual_top_lineage_id != eventual_expected:
        msg = (
            f"H2b v0.35-fresh re-anchor mismatch at {key}: "
            f"derived eventual_top_lineage_id={row.eventual_top_lineage_id} "
            f"!= v0.35-fresh eventual_top_lineage_id={eventual_expected}"
        )
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-hazard aggregation
# ---------------------------------------------------------------------------


def aggregate_per_hazard_fresh(per_run_rows: list[la.PerRunRow]) -> list[PerHazardFreshRow]:
    by_hazard: dict[int, list[la.PerRunRow]] = {h: [] for h in lr.HAZARDS}
    for row in per_run_rows:
        if row.hazard in by_hazard:
            by_hazard[row.hazard].append(row)
    out: list[PerHazardFreshRow] = []
    for hazard in lr.HAZARDS:
        rows = by_hazard[hazard]
        mean = statistics.mean(r.leader_advantage for r in rows) if rows else float("nan")
        out.append(
            PerHazardFreshRow(
                hazard=hazard,
                n_runs=len(rows),
                n_wad_true=sum(1 for r in rows if r.wad_flag),
                mean_leader_advantage=mean,
            )
        )
    return out


def aggregate_per_hazard_pooled(
    fresh_per_run_rows: list[la.PerRunRow],
    old_v0_38_per_run: dict[tuple[str, str, int], tuple[int, float]],
) -> list[PerHazardPooledRow]:
    """Pool: for each hazard, mean leader_advantage across (96 old +
    32 fresh) runs."""
    fresh_by_hazard: dict[int, list[float]] = {h: [] for h in lr.HAZARDS}
    for row in fresh_per_run_rows:
        if row.hazard in fresh_by_hazard:
            fresh_by_hazard[row.hazard].append(row.leader_advantage)

    old_by_hazard: dict[int, list[float]] = {h: [] for h in lr.HAZARDS}
    for hazard, adv in old_v0_38_per_run.values():
        if hazard in old_by_hazard:
            old_by_hazard[hazard].append(adv)

    out: list[PerHazardPooledRow] = []
    for hazard in lr.HAZARDS:
        old_vals = old_by_hazard[hazard]
        fresh_vals = fresh_by_hazard[hazard]
        all_vals = old_vals + fresh_vals
        mean = statistics.mean(all_vals) if all_vals else float("nan")
        out.append(
            PerHazardPooledRow(
                hazard=hazard,
                n_runs=len(all_vals),
                n_old=len(old_vals),
                n_fresh=len(fresh_vals),
                mean_leader_advantage=mean,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Indicator + verdict evaluation (locked rules)
# ---------------------------------------------------------------------------


def _evaluate_layer(
    means_in_hazard_order: list[float],
    spread_threshold: float,
    h5_verdict: str,
    h6_verdict: str,
    h7_verdict: str,
    h5_phrase: str,
    h6_phrase: str,
    h7_phrase: str,
) -> VerdictRow:
    """Three-way verdict: H5 (up + spread), H6 (neither), H7 (down + reverse-spread)."""
    if any(math.isnan(v) for v in means_in_hazard_order):
        return VerdictRow(
            verdict=h6_verdict,
            locked_phrase=h6_phrase,
            monotone_pass_up=False,
            monotone_pass_down=False,
            spread_value=float("nan"),
            spread_threshold=spread_threshold,
            threshold_passes_up=False,
            threshold_passes_down=False,
        )
    monotone_up = ls.is_weak_monotone_non_decreasing(means_in_hazard_order)
    monotone_down = ls.is_weak_monotone_non_increasing(means_in_hazard_order)
    signed_spread = means_in_hazard_order[-1] - means_in_hazard_order[0]
    threshold_passes_up = signed_spread >= spread_threshold
    threshold_passes_down = (-signed_spread) >= spread_threshold
    if monotone_up and threshold_passes_up:
        return VerdictRow(
            verdict=h5_verdict,
            locked_phrase=h5_phrase,
            monotone_pass_up=True,
            monotone_pass_down=monotone_down,
            spread_value=signed_spread,
            spread_threshold=spread_threshold,
            threshold_passes_up=True,
            threshold_passes_down=threshold_passes_down,
        )
    if monotone_down and threshold_passes_down:
        return VerdictRow(
            verdict=h7_verdict,
            locked_phrase=h7_phrase,
            monotone_pass_up=monotone_up,
            monotone_pass_down=True,
            spread_value=signed_spread,
            spread_threshold=spread_threshold,
            threshold_passes_up=threshold_passes_up,
            threshold_passes_down=True,
        )
    return VerdictRow(
        verdict=h6_verdict,
        locked_phrase=h6_phrase,
        monotone_pass_up=monotone_up,
        monotone_pass_down=monotone_down,
        spread_value=signed_spread,
        spread_threshold=spread_threshold,
        threshold_passes_up=threshold_passes_up,
        threshold_passes_down=threshold_passes_down,
    )


# Layer-1 / Layer-2 phrases are NOT the headline — only the combined
# classification has a locked phrase. Layer phrases are placeholder
# strings used for the per-layer verdict CSVs (machine-readable
# metadata). They are NOT publication-facing.
_LAYER_PLACEHOLDER_H5 = "layer fired H5 (monotone-up + spread)"
_LAYER_PLACEHOLDER_H6 = "layer fired H6 (neither up nor down)"
_LAYER_PLACEHOLDER_H7 = "layer fired H7 (monotone-down + reverse spread)"


def evaluate_fresh_verdict(per_hazard_fresh: list[PerHazardFreshRow]) -> VerdictRow:
    by_h = {r.hazard: r for r in per_hazard_fresh}
    means = [by_h[h].mean_leader_advantage for h in lr.HAZARDS]
    return _evaluate_layer(
        means,
        SPREAD_THRESHOLD,
        VERDICT_H5_FRESH,
        VERDICT_H6_FRESH,
        VERDICT_H7_FRESH,
        _LAYER_PLACEHOLDER_H5,
        _LAYER_PLACEHOLDER_H6,
        _LAYER_PLACEHOLDER_H7,
    )


def evaluate_pooled_verdict(per_hazard_pooled: list[PerHazardPooledRow]) -> VerdictRow:
    by_h = {r.hazard: r for r in per_hazard_pooled}
    means = [by_h[h].mean_leader_advantage for h in lr.HAZARDS]
    return _evaluate_layer(
        means,
        SPREAD_THRESHOLD,
        VERDICT_H5_POOLED,
        VERDICT_H6_POOLED,
        VERDICT_H7_POOLED,
        _LAYER_PLACEHOLDER_H5,
        _LAYER_PLACEHOLDER_H6,
        _LAYER_PLACEHOLDER_H7,
    )


def evaluate_combined_classification(fresh: VerdictRow, pooled: VerdictRow) -> VerdictCombinedRow:
    """Locked combined-classification lookup (pre-reg section
    'Combined classification (locked headline rules)').

    Halt on H5_FRESH x H7_POOLED (structurally near-impossible given
    the pooled corpus is dominated by 96 old monotone-up runs).
    """
    f = fresh.verdict
    p = pooled.verdict

    # Halt: H5_FRESH x H7_POOLED is structurally suspicious.
    if f == VERDICT_H5_FRESH and p == VERDICT_H7_POOLED:
        msg = (
            "H5_FRESH x H7_POOLED combined verdict: structurally "
            "near-impossible (pooled corpus is dominated by 96 v0.38 "
            "monotone-up runs). Halt and investigate v0.38 anchors / "
            "data selection / extension reducer logic."
        )
        raise lr.LineageReplayError(msg)

    if f == VERDICT_H5_FRESH and p == VERDICT_H5_POOLED:
        return VerdictCombinedRow(
            combined_classification=COMBINED_H5_FRESH_AND_POOLED,
            headline_locked_phrase=LOCKED_H5_FRESH_AND_POOLED_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    if f == VERDICT_H5_FRESH and p == VERDICT_H6_POOLED:
        return VerdictCombinedRow(
            combined_classification=COMBINED_H5_FRESH_ONLY,
            headline_locked_phrase=LOCKED_H5_FRESH_ONLY_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    if f == VERDICT_H6_FRESH and p == VERDICT_H5_POOLED:
        return VerdictCombinedRow(
            combined_classification=COMBINED_H5_POOLED_ONLY,
            headline_locked_phrase=LOCKED_H5_POOLED_ONLY_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    if f == VERDICT_H6_FRESH and p == VERDICT_H6_POOLED:
        return VerdictCombinedRow(
            combined_classification=COMBINED_NEITHER_H5,
            headline_locked_phrase=LOCKED_NEITHER_H5_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    if f == VERDICT_H6_FRESH and p == VERDICT_H7_POOLED:
        return VerdictCombinedRow(
            combined_classification=COMBINED_H6_FRESH_POOLED_DOWN,
            headline_locked_phrase=LOCKED_H6_FRESH_POOLED_DOWN_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    if f == VERDICT_H7_FRESH:
        return VerdictCombinedRow(
            combined_classification=COMBINED_H7_FRESH,
            headline_locked_phrase=LOCKED_H7_FRESH_HEADLINE_PHRASE,
            fresh_verdict=f,
            pooled_verdict=p,
        )
    msg = f"unreachable combined verdict: fresh={f} pooled={p}"
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


PER_HAZARD_FRESH_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "n_wad_true",
    "mean_leader_advantage",
]
PER_HAZARD_POOLED_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "n_old",
    "n_fresh",
    "mean_leader_advantage",
]
VERDICT_FIELDNAMES: list[str] = [
    "verdict",
    "locked_phrase",
    "monotone_pass_up",
    "monotone_pass_down",
    "spread_value",
    "spread_threshold",
    "threshold_passes_up",
    "threshold_passes_down",
]
VERDICT_COMBINED_FIELDNAMES: list[str] = [
    "combined_classification",
    "headline_locked_phrase",
    "fresh_verdict",
    "pooled_verdict",
]


def write_outputs(
    per_run_rows: list[la.PerRunRow],
    per_hazard_fresh: list[PerHazardFreshRow],
    per_hazard_pooled: list[PerHazardPooledRow],
    verdict_fresh: VerdictRow,
    verdict_pooled: VerdictRow,
    verdict_combined: VerdictCombinedRow,
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_run": out_dir / "per_run.csv",
        "per_hazard_fresh": out_dir / "per_hazard_fresh.csv",
        "per_hazard_pooled": out_dir / "per_hazard_pooled.csv",
        "verdict_fresh": out_dir / "verdict_fresh.csv",
        "verdict_pooled": out_dir / "verdict_pooled.csv",
        "verdict_combined": out_dir / "verdict_combined.csv",
    }
    _write_dataclass_csv(per_run_rows, paths["per_run"], la.PER_RUN_FIELDNAMES)
    _write_dataclass_csv(per_hazard_fresh, paths["per_hazard_fresh"], PER_HAZARD_FRESH_FIELDNAMES)
    _write_dataclass_csv(
        per_hazard_pooled, paths["per_hazard_pooled"], PER_HAZARD_POOLED_FIELDNAMES
    )
    _write_dataclass_csv([verdict_fresh], paths["verdict_fresh"], VERDICT_FIELDNAMES)
    _write_dataclass_csv([verdict_pooled], paths["verdict_pooled"], VERDICT_FIELDNAMES)
    _write_dataclass_csv([verdict_combined], paths["verdict_combined"], VERDICT_COMBINED_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_old_corpus_sealed()
    assert_fresh_anchors_present()

    runs = discover_fresh_runs()
    expected_n = len(lr.HAZARDS) * len(FRESH_SEEDS)
    if len(runs) != expected_n:
        msg = f"discover_fresh_runs returned {len(runs)} runs but expected {expected_n}"
        raise lr.LineageReplayError(msg)
    print(
        f"v0.39 leader_advantage_fresh_replay: {len(runs)} fresh runs",
        flush=True,
    )

    v34_fresh = load_fresh_v0_34_anchors()
    v35_fresh = load_fresh_v0_35_anchors()
    v0_38_per_run = load_v0_38_per_run_leader_advantage()
    print(
        f"  loaded {len(v34_fresh)} v0.34-fresh, {len(v35_fresh)} "
        f"v0.35-fresh, {len(v0_38_per_run)} v0.38 per-run anchors",
        flush=True,
    )

    per_run_rows: list[la.PerRunRow] = []
    for source_version, arm_label, hazard, seed, run_dir in runs:
        row = la.summarise_run(source_version, arm_label, hazard, seed, run_dir)
        cross_anchor_fresh_run(row, v34_fresh, v35_fresh)
        per_run_rows.append(row)

    per_hazard_fresh = aggregate_per_hazard_fresh(per_run_rows)
    per_hazard_pooled = aggregate_per_hazard_pooled(per_run_rows, v0_38_per_run)
    verdict_fresh = evaluate_fresh_verdict(per_hazard_fresh)
    verdict_pooled = evaluate_pooled_verdict(per_hazard_pooled)
    verdict_combined = evaluate_combined_classification(verdict_fresh, verdict_pooled)

    paths = write_outputs(
        per_run_rows,
        per_hazard_fresh,
        per_hazard_pooled,
        verdict_fresh,
        verdict_pooled,
        verdict_combined,
    )

    print()
    print("Per-hazard FRESH (n=8 each):")
    print(f"  {'hazard':>6} {'n_runs':>6} {'n_wad':>6} {'mean_LA':>10}")
    for r in per_hazard_fresh:
        print(
            f"  {r.hazard:>6d} {r.n_runs:>6d} {r.n_wad_true:>6d} {r.mean_leader_advantage:>10.3f}",
            flush=True,
        )

    print()
    print("Per-hazard POOLED (n=32 each = 24 old + 8 fresh):")
    print(f"  {'hazard':>6} {'n_runs':>6} {'n_old':>6} {'n_fresh':>7} {'mean_LA':>10}")
    for r in per_hazard_pooled:
        print(
            f"  {r.hazard:>6d} {r.n_runs:>6d} {r.n_old:>6d} "
            f"{r.n_fresh:>7d} {r.mean_leader_advantage:>10.3f}",
            flush=True,
        )

    print()
    print(
        f"Fresh verdict:    {verdict_fresh.verdict}  "
        f"(spread={verdict_fresh.spread_value:.3f}, "
        f"mono_up={verdict_fresh.monotone_pass_up}, "
        f"mono_down={verdict_fresh.monotone_pass_down})"
    )
    print(
        f"Pooled verdict:   {verdict_pooled.verdict}  "
        f"(spread={verdict_pooled.spread_value:.3f}, "
        f"mono_up={verdict_pooled.monotone_pass_up}, "
        f"mono_down={verdict_pooled.monotone_pass_down})"
    )
    print()
    print(f"Combined:         {verdict_combined.combined_classification}")
    print(f'Headline phrase:  "{verdict_combined.headline_locked_phrase}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
