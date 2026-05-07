"""v0.41 stream classification audit + n=5 stability re-run.

Tests two locked questions on the now-five-stream lineage-axis corpus:

  Primary:   classify the v0.41 stream's M1/M2/M3 agreement bitmap into
             one of three pre-committed cells (v0.41_OLD_LIKE,
             v0.41_V039_LIKE, v0.41_NOVEL_MIXED).
  Secondary: re-run v0.40's stream-stability audit at n=5 with thresholds
             scaled to preserve the 75/25 bars (H5: m3 >= 4/5 streams AND
             family >= 2/3 metrics each >= 4/5; H7: m3 <= 1/5; H6 default).

Reads 9 sealed CSVs (no raw events.jsonl parsing; no helper-function reuse
beyond the LineageReplayError halt class):

  OLD tier (96 rows each):
    runs/lineage-v0.34/run_summary.csv               -> M1 source (v0.25/.32/.33)
    runs/lineage-v0.35/pre_post_dominance.csv        -> M2 source
    runs/lineage-v0.38/per_run.csv                   -> M3 source

  FRESH-v0.39 tier (32 rows each):
    runs/lineage-v0.34-fresh/run_summary.csv         -> M1 source (v0.39)
    runs/lineage-v0.35-fresh/pre_post_dominance.csv  -> M2 source
    runs/lineage-v0.39/per_run.csv                   -> M3 source

  FRESH-v0.41 tier (32 rows each; NEW):
    runs/lineage-v0.34-v0_41-fresh/run_summary.csv         -> M1 source (v0.41)
    runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv  -> M2 source
    runs/lineage-v0.38-v0_41-fresh/per_run.csv             -> M3 source

Three observable family (inherited verbatim from v0.40):
  M1 = mean(top_lineage_b50_share) per (stream, hazard) -- v0.34 lens
  M2 = mean(wad_flag) per (stream, hazard) -- v0.35 lens (True=1, False=0)
  M3 = mean(leader_advantage) per (stream, hazard) -- v0.38/v0.39/v0.41 lens

Per-stream agreement (locked, inherited from v0.40):
  m1_agrees(s) := signed_spread_M1(s) > 0       (direction-only)
  m2_agrees(s) := signed_spread_M2(s) > 0       (direction-only)
  m3_agrees(s) := signed_spread_M3(s) >= 1.5    (magnitude-too)
  signed_spread_M(s) = mean_M(s, h=12) - mean_M(s, h=0)

Primary v0.41 cells (locked, mutually exclusive):
  v0.41_OLD_LIKE       iff (m1, m2, m3) == (True, True, True)
  v0.41_V039_LIKE      iff (m1, m2, m3) == (True, False, False)
  v0.41_NOVEL_MIXED    otherwise (any other 6 of 8 bitmaps)

Secondary n=5 verdict (locked, mutually exclusive):
  H5_STREAM_STABLE_N5    iff m3_count >= 4 AND family_count >= 2
  H7_STREAM_UNSTABLE_N5  iff m3_count <= 1
  H6_STREAM_MIXED_N5     otherwise (default)

Pre-reg: [[docs/experiments/fear_hunger_v0.41.md]].

Outputs eight CSVs under ``runs/lineage-v0.41/``:
  - per_stream_per_hazard.csv    (20 rows: 5 streams x 4 hazards)
  - per_stream_summary.csv       (5 rows)
  - metric_summary.csv           (3 rows: M1/M2/M3)
  - v041_bitmap.csv              (1 row)
  - v041_classification.csv      (1 row: cell + locked phrase)
  - n5_verdict.csv               (1 row: H5/H6/H7 STREAM-*-N5 + locked phrase)
  - stream_metric_table.csv      (5 rows; agreement boolean per cell)
  - combined_summary.csv         (1 row: cell + n5 verdict + joint headline)

Usage:
    uv run python scripts/v0_41_stream_classification_audit.py
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
# Import only the LineageReplayError halt class (project standard)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_lr_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _lr_spec is not None
assert _lr_spec.loader is not None
lr = importlib.util.module_from_spec(_lr_spec)
sys.modules["lineage_replay"] = lr
_lr_spec.loader.exec_module(lr)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg before code)
# ---------------------------------------------------------------------------


EXPECTED_HAZARDS: tuple[int, ...] = (0, 4, 8, 12)
EXPECTED_STREAMS_OLD: tuple[str, ...] = ("v0.25", "v0.32", "v0.33")
EXPECTED_STREAMS_FRESH_V039: tuple[str, ...] = ("v0.39",)
EXPECTED_STREAMS_FRESH_V041: tuple[str, ...] = ("v0.41",)
EXPECTED_STREAMS_ALL: tuple[str, ...] = ("v0.25", "v0.32", "v0.33", "v0.39", "v0.41")

EXPECTED_RUNS_OLD: int = 96
EXPECTED_RUNS_FRESH_V039: int = 32
EXPECTED_RUNS_FRESH_V041: int = 32
EXPECTED_RUNS_PER_STREAM_PER_HAZARD: int = 8

# Inherited from v0.38/v0.39/v0.40 (do NOT mutate)
M3_SPREAD_THRESHOLD: float = 1.5

# Scaled n=5 thresholds (item 1 of v0.41 sign-off)
H5_M3_MIN_STREAMS_N5: int = 4
H5_FAMILY_MIN_METRICS_N5: int = 2
H7_M3_MAX_STREAMS_N5: int = 1

# Locked v0.41 bitmap cells (item 2 of v0.41 sign-off)
V0_41_BITMAP_OLD_LIKE: tuple[bool, bool, bool] = (True, True, True)
V0_41_BITMAP_V039_LIKE: tuple[bool, bool, bool] = (True, False, False)

V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_38_OLD_PER_RUN: Path = Path("runs/lineage-v0.38/per_run.csv")
V0_34_FRESH_V039: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_V039: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")
V0_38_FRESH_V039: Path = Path("runs/lineage-v0.39/per_run.csv")
V0_34_FRESH_V041: Path = Path("runs/lineage-v0.34-v0_41-fresh/run_summary.csv")
V0_35_FRESH_V041: Path = Path("runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv")
V0_38_FRESH_V041: Path = Path("runs/lineage-v0.38-v0_41-fresh/per_run.csv")

OUT_DIR: Path = Path("runs/lineage-v0.41")

# Cell labels
CELL_OLD_LIKE = "v0.41_OLD_LIKE"
CELL_V039_LIKE = "v0.41_V039_LIKE"
CELL_NOVEL_MIXED = "v0.41_NOVEL_MIXED"

# n=5 verdict labels
VERDICT_STABLE_N5 = "H5_STREAM_STABLE_N5"
VERDICT_MIXED_N5 = "H6_STREAM_MIXED_N5"
VERDICT_UNSTABLE_N5 = "H7_STREAM_UNSTABLE_N5"

LOCKED_OLD_LIKE_PHRASE = (
    "Seeds 33..40 reproduce the OLD-stream M1/M2/M3 agreement pattern in "
    "full. v0.39 is the lone outlier across the now-five-stream corpus and "
    "is best read as a one-off n=8 noise excursion rather than evidence of "
    "a systematic post-v0.33 deviation. The v0.34..v0.38 lineage-axis arc's "
    "stream-stability claim is reinforced from 3 of 4 streams to 4 of 5 "
    "streams. Mechanism promotion still requires intervention design and is "
    "not declared by this audit."
)
LOCKED_V039_LIKE_PHRASE = (
    "Seeds 33..40 reproduce v0.39's exact dissent pattern: M1 agrees, M2 "
    "and M3 do not. The OLD-vs-FRESH split observed in v0.39 is now seen "
    "across two independent fresh streams. v0.39 was not a one-off; "
    "something systematic distinguishes the post-v0.33 seed band from the "
    "OLD pool's 1..24 region. The v0.34..v0.38 arc's stream-stability "
    "claim is conditional on OLD streams only; cross-band generalisation "
    "is unsupported. Mechanism work on the OLD signal is blocked pending "
    "investigation of the OLD-vs-FRESH split."
)
LOCKED_NOVEL_MIXED_PHRASE = (
    "Seeds 33..40 do not cleanly match either the OLD-stream pattern or "
    "v0.39's dissent pattern. Cross-stream variability becomes the "
    "immediate object of study. The v0.34..v0.38 arc's stream-stability "
    "claim weakens; how much depends on which metrics agreed and which "
    "did not (see v041_bitmap.csv). Mechanism work remains blocked. "
    "v0.42 candidates: third fresh stream OR per-stream founder-trait "
    "variance characterisation."
)

LOCKED_H5_N5_PHRASE = (
    "Lineage-axis hazard signals reproduce in at least four of five seed "
    "streams (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39 25..32, v0.41 "
    "33..40) under the inherited v0.40 spread agreement rules. The "
    "v0.34..v0.38 arc's correlational signal upgrades from stream-stable "
    "on 4 streams to stream-stable on 5 streams. Mechanism promotion "
    "still requires intervention design and is not declared by this "
    "audit."
)
LOCKED_H6_N5_PHRASE = (
    "Lineage-axis hazard signals reproduce in some streams but not enough "
    "to clear the H5_STREAM_STABLE_N5 bar (>= 4/5 on M3, >= 2/3 metric "
    "families each >= 4/5 streams). The v0.34..v0.38 arc is stream-mixed "
    "at n=5: the OLD pooled signal is carried unevenly by its constituent "
    "streams, or the family-level agreement is partial. Correlational; "
    "not a mechanism declaration."
)
LOCKED_H7_N5_PHRASE = (
    "Lineage-axis hazard signals fail to reproduce in at least four of "
    "five seed streams. M3 leader-post-50-advantage clears its locked "
    "+1.5 spread bar in at most one stream. The v0.34..v0.38 arc is "
    "effectively retracted as stream-unstable at n=5: the OLD pooled "
    "signal does not survive per-stream decomposition once two fresh "
    "streams are included. Mechanism work is blocked pending "
    "re-stabilisation."
)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerStreamPerHazardRow:
    stream: str
    hazard: int
    n_runs: int
    mean_m1: float
    mean_m2: float
    mean_m3: float


@dataclass(frozen=True)
class PerStreamSummaryRow:
    stream: str
    n_runs: int
    m1_signed_spread: float
    m1_agrees: bool
    m1_monotone_up: bool
    m1_monotone_down: bool
    m2_signed_spread: float
    m2_agrees: bool
    m2_monotone_up: bool
    m2_monotone_down: bool
    m3_signed_spread: float
    m3_agrees: bool
    m3_monotone_up: bool
    m3_monotone_down: bool


@dataclass(frozen=True)
class MetricSummaryRow:
    metric: str  # "M1" | "M2" | "M3"
    n_streams_agree: int
    n_streams_total: int
    agreement_rate: float


@dataclass(frozen=True)
class V041BitmapRow:
    m1_agrees: bool
    m2_agrees: bool
    m3_agrees: bool
    bitmap_cell: str  # one of CELL_OLD_LIKE / CELL_V039_LIKE / CELL_NOVEL_MIXED


@dataclass(frozen=True)
class V041ClassificationRow:
    bitmap_cell: str
    locked_phrase: str


@dataclass(frozen=True)
class N5VerdictRow:
    verdict: str
    locked_phrase: str
    m3_agreement_count: int
    family_agreement_count: int


@dataclass(frozen=True)
class StreamMetricTableRow:
    stream: str
    m1_agrees: bool
    m2_agrees: bool
    m3_agrees: bool


@dataclass(frozen=True)
class CombinedSummaryRow:
    v041_cell: str
    n5_verdict: str
    joint_headline: str


# ---------------------------------------------------------------------------
# Per-run records loaded from sealed CSVs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _PerRun:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    m1: float | None  # top_lineage_b50_share
    m2: float | None  # wad_flag as 1.0/0.0
    m3: float | None  # leader_advantage


# ---------------------------------------------------------------------------
# Sealed CSV loading + halt invariants
# ---------------------------------------------------------------------------


def _read_rows(path: Path, label: str) -> list[dict[str, str]]:
    if not path.exists():
        msg = f"{label} sealed CSV missing at {path}"
        raise lr.LineageReplayError(msg)
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _assert_row_count(path: Path, label: str, expected: int) -> None:
    rows = _read_rows(path, label)
    if len(rows) != expected:
        msg = f"{label} row-count drift at {path}: got {len(rows)} but locked expected {expected}"
        raise lr.LineageReplayError(msg)


def assert_old_corpus_sealed() -> None:
    """H2a: all three OLD CSVs have exactly 96 rows."""
    _assert_row_count(V0_34_OLD_RUN_SUMMARY, "v0.34 OLD run_summary", EXPECTED_RUNS_OLD)
    _assert_row_count(V0_35_OLD_PRE_POST, "v0.35 OLD pre_post_dominance", EXPECTED_RUNS_OLD)
    _assert_row_count(V0_38_OLD_PER_RUN, "v0.38 OLD per_run", EXPECTED_RUNS_OLD)


def assert_fresh_v039_corpus_sealed() -> None:
    """H2b: all three FRESH-v0.39 CSVs have exactly 32 rows."""
    _assert_row_count(V0_34_FRESH_V039, "v0.34 FRESH-v0.39 run_summary", EXPECTED_RUNS_FRESH_V039)
    _assert_row_count(
        V0_35_FRESH_V039, "v0.35 FRESH-v0.39 pre_post_dominance", EXPECTED_RUNS_FRESH_V039
    )
    _assert_row_count(V0_38_FRESH_V039, "v0.39 per_run", EXPECTED_RUNS_FRESH_V039)


def assert_fresh_v041_corpus_sealed() -> None:
    """H2c: all three FRESH-v0.41 CSVs have exactly 32 rows."""
    _assert_row_count(V0_34_FRESH_V041, "v0.34 FRESH-v0.41 run_summary", EXPECTED_RUNS_FRESH_V041)
    _assert_row_count(
        V0_35_FRESH_V041, "v0.35 FRESH-v0.41 pre_post_dominance", EXPECTED_RUNS_FRESH_V041
    )
    _assert_row_count(V0_38_FRESH_V041, "v0.38 FRESH-v0.41 per_run", EXPECTED_RUNS_FRESH_V041)


def _parse_optional_float(raw: str) -> float | None:
    if raw == "":
        return None
    return float(raw)


def _parse_optional_bool(raw: str) -> float | None:
    """Parse the v0.35 winner_already_dominant_at_tick_50 column.
    True/False -> 1.0/0.0; empty -> None (run had total_b50 == 0)."""
    if raw == "":
        return None
    if raw == "True":
        return 1.0
    if raw == "False":
        return 0.0
    msg = f"unexpected wad_flag value: {raw!r}"
    raise lr.LineageReplayError(msg)


def _streams_seen(rows_lists: list[list[dict[str, str]]]) -> set[str]:
    out: set[str] = set()
    for rows in rows_lists:
        out.update(r["source_version"] for r in rows)
    return out


def _key_m1(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], float | None]:
    out: dict[tuple[str, str, int], float | None] = {}
    for r in rows:
        key = (r["source_version"], r["arm_label"], int(r["seed"]))
        out[key] = _parse_optional_float(r["top_lineage_b50_share"])
    return out


def _key_m2(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], float | None]:
    out: dict[tuple[str, str, int], float | None] = {}
    for r in rows:
        key = (r["source_version"], r["arm_label"], int(r["seed"]))
        out[key] = _parse_optional_bool(r["winner_already_dominant_at_tick_50"])
    return out


def _key_m3(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], float | None]:
    out: dict[tuple[str, str, int], float | None] = {}
    for r in rows:
        key = (r["source_version"], r["arm_label"], int(r["seed"]))
        out[key] = _parse_optional_float(r["leader_advantage"])
    return out


def _key_hazard(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], int]:
    out: dict[tuple[str, str, int], int] = {}
    for r in rows:
        key = (r["source_version"], r["arm_label"], int(r["seed"]))
        out[key] = int(r["hazard"])
    return out


def _assert_streams(seen: set[str], expected: tuple[str, ...], tier: str) -> None:
    if seen != set(expected):
        msg = (
            f"H2d {tier} stream-id drift: got {sorted(seen)} but locked expected {sorted(expected)}"
        )
        raise lr.LineageReplayError(msg)


def _assert_tier_alignment(m1: dict, m2: dict, m3: dict, tier: str) -> None:
    if not (set(m1) == set(m2) == set(m3)):
        only_in_m1 = set(m1) - (set(m2) & set(m3))
        only_in_m2 = set(m2) - (set(m1) & set(m3))
        only_in_m3 = set(m3) - (set(m1) & set(m2))
        msg = (
            f"H2f {tier} cross-CSV key misalignment: "
            f"only_in_m1={sorted(only_in_m1)[:3]}; "
            f"only_in_m2={sorted(only_in_m2)[:3]}; "
            f"only_in_m3={sorted(only_in_m3)[:3]}"
        )
        raise lr.LineageReplayError(msg)


def _build_tier(
    m1_rows: list[dict[str, str]],
    m2_rows: list[dict[str, str]],
    m3_rows: list[dict[str, str]],
    haz_rows: list[dict[str, str]],
    tier: str,
) -> dict[tuple[str, str, int], _PerRun]:
    m1 = _key_m1(m1_rows)
    m2 = _key_m2(m2_rows)
    m3 = _key_m3(m3_rows)
    haz = _key_hazard(haz_rows)
    _assert_tier_alignment(m1, m2, m3, tier)
    out: dict[tuple[str, str, int], _PerRun] = {}
    for key, m1_v in m1.items():
        out[key] = _PerRun(
            source_version=key[0],
            arm_label=key[1],
            hazard=haz[key],
            seed=key[2],
            m1=m1_v,
            m2=m2[key],
            m3=m3[key],
        )
    return out


def load_per_run_records() -> dict[tuple[str, str, int], _PerRun]:
    """Load all 160 per-run records keyed by (source_version, arm_label,
    seed). Halts on stream-id drift, bucket-count drift, and cross-CSV
    key misalignment.
    """
    v34_old_rows = _read_rows(V0_34_OLD_RUN_SUMMARY, "v0.34 OLD run_summary")
    v35_old_rows = _read_rows(V0_35_OLD_PRE_POST, "v0.35 OLD pre_post_dominance")
    v38_old_rows = _read_rows(V0_38_OLD_PER_RUN, "v0.38 OLD per_run")
    v34_v039_rows = _read_rows(V0_34_FRESH_V039, "v0.34 FRESH-v0.39 run_summary")
    v35_v039_rows = _read_rows(V0_35_FRESH_V039, "v0.35 FRESH-v0.39 pre_post_dominance")
    v38_v039_rows = _read_rows(V0_38_FRESH_V039, "v0.39 per_run")
    v34_v041_rows = _read_rows(V0_34_FRESH_V041, "v0.34 FRESH-v0.41 run_summary")
    v35_v041_rows = _read_rows(V0_35_FRESH_V041, "v0.35 FRESH-v0.41 pre_post_dominance")
    v38_v041_rows = _read_rows(V0_38_FRESH_V041, "v0.38 FRESH-v0.41 per_run")

    # H2d: stream-id drift per tier
    _assert_streams(
        _streams_seen([v34_old_rows, v35_old_rows, v38_old_rows]),
        EXPECTED_STREAMS_OLD,
        "OLD",
    )
    _assert_streams(
        _streams_seen([v34_v039_rows, v35_v039_rows, v38_v039_rows]),
        EXPECTED_STREAMS_FRESH_V039,
        "FRESH-v0.39",
    )
    _assert_streams(
        _streams_seen([v34_v041_rows, v35_v041_rows, v38_v041_rows]),
        EXPECTED_STREAMS_FRESH_V041,
        "FRESH-v0.41",
    )

    out: dict[tuple[str, str, int], _PerRun] = {}
    out.update(_build_tier(v34_old_rows, v35_old_rows, v38_old_rows, v34_old_rows, "OLD"))
    out.update(
        _build_tier(v34_v039_rows, v35_v039_rows, v38_v039_rows, v34_v039_rows, "FRESH-v0.39")
    )
    out.update(
        _build_tier(v34_v041_rows, v35_v041_rows, v38_v041_rows, v34_v041_rows, "FRESH-v0.41")
    )

    expected_total = EXPECTED_RUNS_OLD + EXPECTED_RUNS_FRESH_V039 + EXPECTED_RUNS_FRESH_V041
    if len(out) != expected_total:
        msg = f"combined per-run count {len(out)} != {expected_total}"
        raise lr.LineageReplayError(msg)
    return out


def assert_bucket_counts(
    per_run: dict[tuple[str, str, int], _PerRun],
) -> dict[tuple[str, int], list[_PerRun]]:
    """H2e: each (source_version, hazard) bucket has exactly 8 runs.
    Returns the bucketed view as a side effect."""
    buckets: dict[tuple[str, int], list[_PerRun]] = {}
    for stream in EXPECTED_STREAMS_ALL:
        for hazard in EXPECTED_HAZARDS:
            buckets[(stream, hazard)] = []
    for run in per_run.values():
        key = (run.source_version, run.hazard)
        if key not in buckets:
            msg = (
                f"H2e unexpected bucket {key} for run "
                f"({run.source_version}, {run.arm_label}, {run.seed})"
            )
            raise lr.LineageReplayError(msg)
        buckets[key].append(run)
    for (stream, hazard), runs in buckets.items():
        if len(runs) != EXPECTED_RUNS_PER_STREAM_PER_HAZARD:
            msg = (
                f"H2e bucket-count drift at ({stream}, h={hazard}): "
                f"got {len(runs)} but locked expected "
                f"{EXPECTED_RUNS_PER_STREAM_PER_HAZARD}"
            )
            raise lr.LineageReplayError(msg)
    return buckets


# ---------------------------------------------------------------------------
# Per-(stream, hazard) aggregation
# ---------------------------------------------------------------------------


def _safe_mean(values: list[float | None]) -> float:
    clean = [v for v in values if v is not None]
    if not clean:
        return float("nan")
    return statistics.mean(clean)


def aggregate_per_stream_per_hazard(
    buckets: dict[tuple[str, int], list[_PerRun]],
) -> list[PerStreamPerHazardRow]:
    out: list[PerStreamPerHazardRow] = []
    for stream in EXPECTED_STREAMS_ALL:
        for hazard in EXPECTED_HAZARDS:
            runs = buckets[(stream, hazard)]
            out.append(
                PerStreamPerHazardRow(
                    stream=stream,
                    hazard=hazard,
                    n_runs=len(runs),
                    mean_m1=_safe_mean([r.m1 for r in runs]),
                    mean_m2=_safe_mean([r.m2 for r in runs]),
                    mean_m3=_safe_mean([r.m3 for r in runs]),
                )
            )
    return out


# ---------------------------------------------------------------------------
# Per-stream signed spread + agreement flags (locked rules)
# ---------------------------------------------------------------------------


def _is_weak_monotone_non_decreasing(vals: list[float]) -> bool:
    return all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))


def _is_weak_monotone_non_increasing(vals: list[float]) -> bool:
    return all(vals[i] >= vals[i + 1] for i in range(len(vals) - 1))


def aggregate_per_stream_summary(
    per_haz: list[PerStreamPerHazardRow],
) -> list[PerStreamSummaryRow]:
    by_stream: dict[str, dict[int, PerStreamPerHazardRow]] = {s: {} for s in EXPECTED_STREAMS_ALL}
    for row in per_haz:
        by_stream[row.stream][row.hazard] = row

    out: list[PerStreamSummaryRow] = []
    for stream in EXPECTED_STREAMS_ALL:
        by_h = by_stream[stream]
        m1_seq = [by_h[h].mean_m1 for h in EXPECTED_HAZARDS]
        m2_seq = [by_h[h].mean_m2 for h in EXPECTED_HAZARDS]
        m3_seq = [by_h[h].mean_m3 for h in EXPECTED_HAZARDS]

        m1_spread = m1_seq[-1] - m1_seq[0]
        m2_spread = m2_seq[-1] - m2_seq[0]
        m3_spread = m3_seq[-1] - m3_seq[0]

        out.append(
            PerStreamSummaryRow(
                stream=stream,
                n_runs=sum(by_h[h].n_runs for h in EXPECTED_HAZARDS),
                m1_signed_spread=m1_spread,
                m1_agrees=(m1_spread > 0),  # direction-only
                m1_monotone_up=_is_weak_monotone_non_decreasing(m1_seq),
                m1_monotone_down=_is_weak_monotone_non_increasing(m1_seq),
                m2_signed_spread=m2_spread,
                m2_agrees=(m2_spread > 0),  # direction-only
                m2_monotone_up=_is_weak_monotone_non_decreasing(m2_seq),
                m2_monotone_down=_is_weak_monotone_non_increasing(m2_seq),
                m3_signed_spread=m3_spread,
                m3_agrees=(m3_spread >= M3_SPREAD_THRESHOLD),  # magnitude-too
                m3_monotone_up=_is_weak_monotone_non_decreasing(m3_seq),
                m3_monotone_down=_is_weak_monotone_non_increasing(m3_seq),
            )
        )
    return out


def build_metric_summary(per_stream: list[PerStreamSummaryRow]) -> list[MetricSummaryRow]:
    n_total = len(per_stream)
    out: list[MetricSummaryRow] = []
    for metric, getter in (
        ("M1", lambda r: r.m1_agrees),
        ("M2", lambda r: r.m2_agrees),
        ("M3", lambda r: r.m3_agrees),
    ):
        agree = sum(1 for r in per_stream if getter(r))
        out.append(
            MetricSummaryRow(
                metric=metric,
                n_streams_agree=agree,
                n_streams_total=n_total,
                agreement_rate=agree / n_total,
            )
        )
    return out


def build_stream_metric_table(
    per_stream: list[PerStreamSummaryRow],
) -> list[StreamMetricTableRow]:
    return [
        StreamMetricTableRow(
            stream=r.stream,
            m1_agrees=r.m1_agrees,
            m2_agrees=r.m2_agrees,
            m3_agrees=r.m3_agrees,
        )
        for r in per_stream
    ]


# ---------------------------------------------------------------------------
# Primary verdict — v0.41 stream bitmap classification
# ---------------------------------------------------------------------------


def classify_v041_bitmap(per_stream: list[PerStreamSummaryRow]) -> V041BitmapRow:
    v041_rows = [r for r in per_stream if r.stream == "v0.41"]
    if len(v041_rows) != 1:
        msg = f"expected exactly one v0.41 row in per_stream summary; got {len(v041_rows)}"
        raise lr.LineageReplayError(msg)
    r = v041_rows[0]
    bitmap = (r.m1_agrees, r.m2_agrees, r.m3_agrees)
    if bitmap == V0_41_BITMAP_OLD_LIKE:
        cell = CELL_OLD_LIKE
    elif bitmap == V0_41_BITMAP_V039_LIKE:
        cell = CELL_V039_LIKE
    else:
        cell = CELL_NOVEL_MIXED
    return V041BitmapRow(
        m1_agrees=r.m1_agrees,
        m2_agrees=r.m2_agrees,
        m3_agrees=r.m3_agrees,
        bitmap_cell=cell,
    )


def build_v041_classification(bitmap: V041BitmapRow) -> V041ClassificationRow:
    if bitmap.bitmap_cell == CELL_OLD_LIKE:
        phrase = LOCKED_OLD_LIKE_PHRASE
    elif bitmap.bitmap_cell == CELL_V039_LIKE:
        phrase = LOCKED_V039_LIKE_PHRASE
    else:
        phrase = LOCKED_NOVEL_MIXED_PHRASE
    return V041ClassificationRow(bitmap_cell=bitmap.bitmap_cell, locked_phrase=phrase)


# ---------------------------------------------------------------------------
# Secondary verdict — n=5 v0.40-style stream audit (scaled thresholds)
# ---------------------------------------------------------------------------


def evaluate_n5_verdict(metric_summary: list[MetricSummaryRow]) -> N5VerdictRow:
    by_metric = {r.metric: r for r in metric_summary}
    m3_agreement_count = by_metric["M3"].n_streams_agree
    family_agreement_count = sum(
        1 for r in metric_summary if r.n_streams_agree >= H5_M3_MIN_STREAMS_N5
    )

    if (
        m3_agreement_count >= H5_M3_MIN_STREAMS_N5
        and family_agreement_count >= H5_FAMILY_MIN_METRICS_N5
    ):
        verdict = VERDICT_STABLE_N5
        phrase = LOCKED_H5_N5_PHRASE
    elif m3_agreement_count <= H7_M3_MAX_STREAMS_N5:
        # Guardrail branch — unreachable under sealed v0.40 inputs (3 OLD M3
        # passes already locked). Retained so a corpus drift surfaces loud.
        verdict = VERDICT_UNSTABLE_N5
        phrase = LOCKED_H7_N5_PHRASE
    else:
        verdict = VERDICT_MIXED_N5
        phrase = LOCKED_H6_N5_PHRASE

    return N5VerdictRow(
        verdict=verdict,
        locked_phrase=phrase,
        m3_agreement_count=m3_agreement_count,
        family_agreement_count=family_agreement_count,
    )


# ---------------------------------------------------------------------------
# Combined summary (joint headline — descriptive only, no locked phrase)
# ---------------------------------------------------------------------------


def build_combined_summary(bitmap: V041BitmapRow, n5: N5VerdictRow) -> CombinedSummaryRow:
    headline = (
        f"v0.41 stream classified as {bitmap.bitmap_cell}; "
        f"n=5 stream audit fires {n5.verdict} "
        f"(m3={n5.m3_agreement_count}/5, family={n5.family_agreement_count}/3)."
    )
    return CombinedSummaryRow(
        v041_cell=bitmap.bitmap_cell,
        n5_verdict=n5.verdict,
        joint_headline=headline,
    )


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


PER_STREAM_PER_HAZARD_FIELDNAMES: list[str] = [
    "stream",
    "hazard",
    "n_runs",
    "mean_m1",
    "mean_m2",
    "mean_m3",
]
PER_STREAM_SUMMARY_FIELDNAMES: list[str] = [
    "stream",
    "n_runs",
    "m1_signed_spread",
    "m1_agrees",
    "m1_monotone_up",
    "m1_monotone_down",
    "m2_signed_spread",
    "m2_agrees",
    "m2_monotone_up",
    "m2_monotone_down",
    "m3_signed_spread",
    "m3_agrees",
    "m3_monotone_up",
    "m3_monotone_down",
]
METRIC_SUMMARY_FIELDNAMES: list[str] = [
    "metric",
    "n_streams_agree",
    "n_streams_total",
    "agreement_rate",
]
V041_BITMAP_FIELDNAMES: list[str] = [
    "m1_agrees",
    "m2_agrees",
    "m3_agrees",
    "bitmap_cell",
]
V041_CLASSIFICATION_FIELDNAMES: list[str] = ["bitmap_cell", "locked_phrase"]
N5_VERDICT_FIELDNAMES: list[str] = [
    "verdict",
    "locked_phrase",
    "m3_agreement_count",
    "family_agreement_count",
]
STREAM_METRIC_TABLE_FIELDNAMES: list[str] = [
    "stream",
    "m1_agrees",
    "m2_agrees",
    "m3_agrees",
]
COMBINED_SUMMARY_FIELDNAMES: list[str] = ["v041_cell", "n5_verdict", "joint_headline"]


def write_outputs(
    per_haz: list[PerStreamPerHazardRow],
    per_stream: list[PerStreamSummaryRow],
    metric_summary: list[MetricSummaryRow],
    bitmap: V041BitmapRow,
    classification: V041ClassificationRow,
    n5_verdict: N5VerdictRow,
    table: list[StreamMetricTableRow],
    combined: CombinedSummaryRow,
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_stream_per_hazard": out_dir / "per_stream_per_hazard.csv",
        "per_stream_summary": out_dir / "per_stream_summary.csv",
        "metric_summary": out_dir / "metric_summary.csv",
        "v041_bitmap": out_dir / "v041_bitmap.csv",
        "v041_classification": out_dir / "v041_classification.csv",
        "n5_verdict": out_dir / "n5_verdict.csv",
        "stream_metric_table": out_dir / "stream_metric_table.csv",
        "combined_summary": out_dir / "combined_summary.csv",
    }
    _write_dataclass_csv(per_haz, paths["per_stream_per_hazard"], PER_STREAM_PER_HAZARD_FIELDNAMES)
    _write_dataclass_csv(per_stream, paths["per_stream_summary"], PER_STREAM_SUMMARY_FIELDNAMES)
    _write_dataclass_csv(metric_summary, paths["metric_summary"], METRIC_SUMMARY_FIELDNAMES)
    _write_dataclass_csv([bitmap], paths["v041_bitmap"], V041_BITMAP_FIELDNAMES)
    _write_dataclass_csv(
        [classification], paths["v041_classification"], V041_CLASSIFICATION_FIELDNAMES
    )
    _write_dataclass_csv([n5_verdict], paths["n5_verdict"], N5_VERDICT_FIELDNAMES)
    _write_dataclass_csv(table, paths["stream_metric_table"], STREAM_METRIC_TABLE_FIELDNAMES)
    _write_dataclass_csv([combined], paths["combined_summary"], COMBINED_SUMMARY_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_old_corpus_sealed()
    assert_fresh_v039_corpus_sealed()
    assert_fresh_v041_corpus_sealed()

    per_run = load_per_run_records()
    expected_total = EXPECTED_RUNS_OLD + EXPECTED_RUNS_FRESH_V039 + EXPECTED_RUNS_FRESH_V041
    print(
        f"v0.41 stream_classification_audit: {len(per_run)} per-run records "
        f"(96 OLD + 32 FRESH-v0.39 + 32 FRESH-v0.41 = {expected_total})",
        flush=True,
    )

    buckets = assert_bucket_counts(per_run)

    per_haz = aggregate_per_stream_per_hazard(buckets)
    per_stream = aggregate_per_stream_summary(per_haz)
    metric_summary = build_metric_summary(per_stream)
    table = build_stream_metric_table(per_stream)
    bitmap = classify_v041_bitmap(per_stream)
    classification = build_v041_classification(bitmap)
    n5_verdict = evaluate_n5_verdict(metric_summary)
    combined = build_combined_summary(bitmap, n5_verdict)

    paths = write_outputs(
        per_haz,
        per_stream,
        metric_summary,
        bitmap,
        classification,
        n5_verdict,
        table,
        combined,
        out_dir=OUT_DIR,
    )

    print()
    print("Per-(stream, hazard) means:")
    print(f"  {'stream':>6} {'h':>3} {'n':>3} {'M1':>8} {'M2':>8} {'M3':>10}")
    for row in per_haz:
        m1 = "nan" if math.isnan(row.mean_m1) else f"{row.mean_m1:.3f}"
        m2 = "nan" if math.isnan(row.mean_m2) else f"{row.mean_m2:.3f}"
        m3 = "nan" if math.isnan(row.mean_m3) else f"{row.mean_m3:.3f}"
        print(
            f"  {row.stream:>6} {row.hazard:>3d} {row.n_runs:>3d} {m1:>8} {m2:>8} {m3:>10}",
            flush=True,
        )

    print()
    print("Per-stream signed spreads + agreement:")
    print(
        f"  {'stream':>6} "
        f"{'M1_spr':>8} {'M1ok':>5} "
        f"{'M2_spr':>8} {'M2ok':>5} "
        f"{'M3_spr':>8} {'M3ok':>5}"
    )
    for r in per_stream:
        print(
            f"  {r.stream:>6} "
            f"{r.m1_signed_spread:>+8.3f} {r.m1_agrees!s:>5} "
            f"{r.m2_signed_spread:>+8.3f} {r.m2_agrees!s:>5} "
            f"{r.m3_signed_spread:>+8.3f} {r.m3_agrees!s:>5}",
            flush=True,
        )

    print()
    print("Stream x metric agreement table:")
    print(f"  {'stream':>6} {'M1':>5} {'M2':>5} {'M3':>5}")
    for r in table:
        print(
            f"  {r.stream:>6} {r.m1_agrees!s:>5} {r.m2_agrees!s:>5} {r.m3_agrees!s:>5}",
            flush=True,
        )

    print()
    print("Metric agreement summary (n=5):")
    for r in metric_summary:
        print(
            f"  {r.metric}: {r.n_streams_agree}/{r.n_streams_total} streams agree "
            f"(rate {r.agreement_rate:.3f})",
            flush=True,
        )

    print()
    print(f"  v0.41 bitmap: ({bitmap.m1_agrees}, {bitmap.m2_agrees}, {bitmap.m3_agrees})")
    print(f"  v0.41 cell:   {bitmap.bitmap_cell}")
    print(f'  locked phrase: "{classification.locked_phrase}"')

    print()
    print(f"  m3_agreement_count:     {n5_verdict.m3_agreement_count}/5")
    print(f"  family_agreement_count: {n5_verdict.family_agreement_count}/3")
    print(f"  n=5 verdict:            {n5_verdict.verdict}")
    print(f'  locked phrase:          "{n5_verdict.locked_phrase}"')

    print()
    print(f"  combined headline:  {combined.joint_headline}")

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>22}  -> {path}")


if __name__ == "__main__":
    main()
