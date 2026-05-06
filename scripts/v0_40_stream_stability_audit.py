"""v0.40 cross-stream stability audit of lineage-axis signals.

Tests how much of the v0.34..v0.38 lineage-axis signal was stream-
dependent vs stream-stable, by decomposing the OLD 96-run corpus into
its three constituent streams (v0.25 1..8, v0.32 9..16, v0.33 17..24)
and comparing them against the FRESH 32-run stream (v0.39 25..32).

Reads 6 sealed CSVs (no raw events.jsonl parsing; no helper-function
reuse beyond the LineageReplayError halt class):

  OLD (96 rows each):
    runs/lineage-v0.34/run_summary.csv          -> M1 source
    runs/lineage-v0.35/pre_post_dominance.csv   -> M2 source
    runs/lineage-v0.38/per_run.csv              -> M3 source

  FRESH (32 rows each):
    runs/lineage-v0.34-fresh/run_summary.csv         -> M1 source
    runs/lineage-v0.35-fresh/pre_post_dominance.csv  -> M2 source
    runs/lineage-v0.39/per_run.csv                   -> M3 source

Three observable family:
  M1 = mean(top_lineage_b50_share) per (stream, hazard) — v0.34 lens
  M2 = mean(wad_flag) per (stream, hazard) — v0.35 lens (True=1, False=0)
  M3 = mean(leader_advantage) per (stream, hazard) — v0.38/v0.39 lens

Per-stream agreement (locked):
  m1_agrees(s) := signed_spread_M1(s) > 0       (direction-only)
  m2_agrees(s) := signed_spread_M2(s) > 0       (direction-only)
  m3_agrees(s) := signed_spread_M3(s) >= 1.5    (magnitude-too,
                                                 inherits v0.38/v0.39)
  signed_spread_M(s) = mean_M(s, h=12) - mean_M(s, h=0)

Three-way verdict (mutually exclusive):
  H5 STREAM-STABLE  iff m3_agreement_count >= 3 AND
                        family_agreement_count >= 2
  H7 STREAM-UNSTABLE iff m3_agreement_count <= 1
  H6 STREAM-MIXED   otherwise (default)

Pre-reg: [[docs/experiments/fear_hunger_v0.40.md]].

Outputs five CSVs under ``runs/lineage-v0.40/``:
  - per_stream_per_hazard.csv    (16 rows: 4 streams x 4 hazards)
  - per_stream_summary.csv       (4 rows)
  - metric_summary.csv           (3 rows: M1/M2/M3)
  - verdict.csv                  (1 row)
  - stream_metric_table.csv      (4 rows; agreement boolean per cell)

Usage:
    uv run python scripts/v0_40_stream_stability_audit.py
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
EXPECTED_STREAMS_FRESH: tuple[str, ...] = ("v0.39",)
EXPECTED_STREAMS_ALL: tuple[str, ...] = ("v0.25", "v0.32", "v0.33", "v0.39")

EXPECTED_RUNS_OLD: int = 96
EXPECTED_RUNS_FRESH: int = 32
EXPECTED_RUNS_PER_STREAM_PER_HAZARD: int = 8

# Locked thresholds (item 1 of v0.40 sign-off)
M3_SPREAD_THRESHOLD: float = 1.5  # inherits v0.38/v0.39 lock
# M1, M2 agreement = signed_spread > 0 (direction-only)

# Locked verdict thresholds (item 2 of v0.40 sign-off)
H5_M3_MIN_STREAMS: int = 3
H5_FAMILY_MIN_METRICS: int = 2
H7_M3_MAX_STREAMS: int = 1

V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_38_PER_RUN: Path = Path("runs/lineage-v0.38/per_run.csv")
V0_34_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_PRE_POST: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")
V0_39_PER_RUN: Path = Path("runs/lineage-v0.39/per_run.csv")

OUT_DIR: Path = Path("runs/lineage-v0.40")

VERDICT_STABLE = "H5_STREAM_STABLE"
VERDICT_MIXED = "H6_STREAM_MIXED"
VERDICT_UNSTABLE = "H7_STREAM_UNSTABLE"

LOCKED_H5_PHRASE = (
    "Lineage-axis hazard signals reproduce in at least three of four "
    "seed streams (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39 25..32) "
    "under the locked spread agreement rules. The v0.34..v0.38 arc's "
    "correlational signal is upgraded from single-stream to stream-"
    "stable across the four streams now on disk. Mechanism promotion "
    "still requires intervention design and is not declared by this "
    "audit."
)
LOCKED_H6_PHRASE = (
    "Lineage-axis hazard signals reproduce in some streams but not "
    "enough to clear the H5 STREAM-STABLE bar. The v0.34..v0.38 arc "
    "is stream-mixed: the OLD pooled signal is carried unevenly by "
    "its constituent streams, or the family-level agreement is "
    "partial. v0.41 candidate: a second fresh stream (seeds 33..40) "
    "to disambiguate noise-driven mixed at n=8 vs real stream "
    "variability. Correlational; not a mechanism declaration."
)
LOCKED_H7_PHRASE = (
    "Lineage-axis hazard signals fail to reproduce in at least three "
    "of four seed streams. M3 leader-post-50-advantage clears its "
    "locked spread bar in at most one stream. The v0.34..v0.38 arc is "
    "effectively retracted as stream-unstable: the OLD pooled signal "
    "does not survive per-stream decomposition at the locked "
    "thresholds. v0.41 candidate: targeted investigation of why the "
    "OLD 96-run pool produced a coherent signal that does not "
    "reproduce per-stream. Mechanism work is blocked pending re-"
    "stabilisation."
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
class VerdictRow:
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
    _assert_row_count(V0_38_PER_RUN, "v0.38 OLD per_run", EXPECTED_RUNS_OLD)


def assert_fresh_corpus_sealed() -> None:
    """H2b: all three FRESH CSVs have exactly 32 rows."""
    _assert_row_count(V0_34_FRESH_RUN_SUMMARY, "v0.34 FRESH run_summary", EXPECTED_RUNS_FRESH)
    _assert_row_count(V0_35_FRESH_PRE_POST, "v0.35 FRESH pre_post_dominance", EXPECTED_RUNS_FRESH)
    _assert_row_count(V0_39_PER_RUN, "v0.39 FRESH per_run", EXPECTED_RUNS_FRESH)


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


def load_per_run_records() -> dict[tuple[str, str, int], _PerRun]:  # noqa: PLR0915
    """Load all 128 per-run records keyed by (source_version, arm_label,
    seed). Halts on stream-id drift, bucket-count drift, and cross-CSV
    key misalignment.
    """
    # Read each CSV
    v34_old_rows = _read_rows(V0_34_OLD_RUN_SUMMARY, "v0.34 OLD run_summary")
    v35_old_rows = _read_rows(V0_35_OLD_PRE_POST, "v0.35 OLD pre_post_dominance")
    v38_old_rows = _read_rows(V0_38_PER_RUN, "v0.38 OLD per_run")
    v34_fresh_rows = _read_rows(V0_34_FRESH_RUN_SUMMARY, "v0.34 FRESH run_summary")
    v35_fresh_rows = _read_rows(V0_35_FRESH_PRE_POST, "v0.35 FRESH pre_post_dominance")
    v39_fresh_rows = _read_rows(V0_39_PER_RUN, "v0.39 FRESH per_run")

    # H2c: stream-id drift
    def _streams(rows: list[dict[str, str]]) -> set[str]:
        return {r["source_version"] for r in rows}

    old_streams_seen = _streams(v34_old_rows) | _streams(v35_old_rows) | _streams(v38_old_rows)
    if old_streams_seen != set(EXPECTED_STREAMS_OLD):
        msg = (
            f"H2c OLD stream-id drift: got {sorted(old_streams_seen)} but "
            f"locked expected {sorted(EXPECTED_STREAMS_OLD)}"
        )
        raise lr.LineageReplayError(msg)
    fresh_streams_seen = (
        _streams(v34_fresh_rows) | _streams(v35_fresh_rows) | _streams(v39_fresh_rows)
    )
    if fresh_streams_seen != set(EXPECTED_STREAMS_FRESH):
        msg = (
            f"H2c FRESH stream-id drift: got {sorted(fresh_streams_seen)} but "
            f"locked expected {sorted(EXPECTED_STREAMS_FRESH)}"
        )
        raise lr.LineageReplayError(msg)

    # Build per-tier (source, arm, seed) -> M1/M2/M3 lookups
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

    # Hazard lookup from any one CSV (use v0.34 / v0.34-fresh which have hazard col)
    def _key_hazard(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], int]:
        out: dict[tuple[str, str, int], int] = {}
        for r in rows:
            key = (r["source_version"], r["arm_label"], int(r["seed"]))
            out[key] = int(r["hazard"])
        return out

    m1_old = _key_m1(v34_old_rows)
    m2_old = _key_m2(v35_old_rows)
    m3_old = _key_m3(v38_old_rows)
    haz_old = _key_hazard(v34_old_rows)
    m1_fresh = _key_m1(v34_fresh_rows)
    m2_fresh = _key_m2(v35_fresh_rows)
    m3_fresh = _key_m3(v39_fresh_rows)
    haz_fresh = _key_hazard(v34_fresh_rows)

    # H2e: cross-CSV alignment within each tier
    if not (set(m1_old) == set(m2_old) == set(m3_old)):
        only_in_m1 = set(m1_old) - (set(m2_old) & set(m3_old))
        only_in_m2 = set(m2_old) - (set(m1_old) & set(m3_old))
        only_in_m3 = set(m3_old) - (set(m1_old) & set(m2_old))
        msg = (
            f"H2e OLD cross-CSV key misalignment: "
            f"only_in_m1={sorted(only_in_m1)[:3]}; "
            f"only_in_m2={sorted(only_in_m2)[:3]}; "
            f"only_in_m3={sorted(only_in_m3)[:3]}"
        )
        raise lr.LineageReplayError(msg)
    if not (set(m1_fresh) == set(m2_fresh) == set(m3_fresh)):
        msg = "H2e FRESH cross-CSV key misalignment"
        raise lr.LineageReplayError(msg)

    # Combine into per-run records
    out: dict[tuple[str, str, int], _PerRun] = {}
    for key, m1 in m1_old.items():
        out[key] = _PerRun(
            source_version=key[0],
            arm_label=key[1],
            hazard=haz_old[key],
            seed=key[2],
            m1=m1,
            m2=m2_old[key],
            m3=m3_old[key],
        )
    for key, m1 in m1_fresh.items():
        out[key] = _PerRun(
            source_version=key[0],
            arm_label=key[1],
            hazard=haz_fresh[key],
            seed=key[2],
            m1=m1,
            m2=m2_fresh[key],
            m3=m3_fresh[key],
        )

    if len(out) != EXPECTED_RUNS_OLD + EXPECTED_RUNS_FRESH:
        msg = f"combined per-run count {len(out)} != {EXPECTED_RUNS_OLD + EXPECTED_RUNS_FRESH}"
        raise lr.LineageReplayError(msg)
    return out


def assert_bucket_counts(
    per_run: dict[tuple[str, str, int], _PerRun],
) -> dict[tuple[str, int], list[_PerRun]]:
    """H2d: each (source_version, hazard) bucket has exactly 8 runs.
    Returns the bucketed view as a side effect."""
    buckets: dict[tuple[str, int], list[_PerRun]] = {}
    for stream in EXPECTED_STREAMS_ALL:
        for hazard in EXPECTED_HAZARDS:
            buckets[(stream, hazard)] = []
    for run in per_run.values():
        key = (run.source_version, run.hazard)
        if key not in buckets:
            msg = (
                f"H2d unexpected bucket {key} for run "
                f"({run.source_version}, {run.arm_label}, {run.seed})"
            )
            raise lr.LineageReplayError(msg)
        buckets[key].append(run)
    for (stream, hazard), runs in buckets.items():
        if len(runs) != EXPECTED_RUNS_PER_STREAM_PER_HAZARD:
            msg = (
                f"H2d bucket-count drift at ({stream}, h={hazard}): "
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
# Verdict (three-way, mutually exclusive)
# ---------------------------------------------------------------------------


def evaluate_verdict(metric_summary: list[MetricSummaryRow]) -> VerdictRow:
    by_metric = {r.metric: r for r in metric_summary}
    m3_agreement_count = by_metric["M3"].n_streams_agree
    family_agreement_count = sum(
        1 for r in metric_summary if r.n_streams_agree >= H5_M3_MIN_STREAMS
    )

    if m3_agreement_count >= H5_M3_MIN_STREAMS and family_agreement_count >= H5_FAMILY_MIN_METRICS:
        verdict = VERDICT_STABLE
        phrase = LOCKED_H5_PHRASE
    elif m3_agreement_count <= H7_M3_MAX_STREAMS:
        verdict = VERDICT_UNSTABLE
        phrase = LOCKED_H7_PHRASE
    else:
        verdict = VERDICT_MIXED
        phrase = LOCKED_H6_PHRASE

    return VerdictRow(
        verdict=verdict,
        locked_phrase=phrase,
        m3_agreement_count=m3_agreement_count,
        family_agreement_count=family_agreement_count,
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
VERDICT_FIELDNAMES: list[str] = [
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


def write_outputs(
    per_haz: list[PerStreamPerHazardRow],
    per_stream: list[PerStreamSummaryRow],
    metric_summary: list[MetricSummaryRow],
    verdict: VerdictRow,
    table: list[StreamMetricTableRow],
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_stream_per_hazard": out_dir / "per_stream_per_hazard.csv",
        "per_stream_summary": out_dir / "per_stream_summary.csv",
        "metric_summary": out_dir / "metric_summary.csv",
        "verdict": out_dir / "verdict.csv",
        "stream_metric_table": out_dir / "stream_metric_table.csv",
    }
    _write_dataclass_csv(per_haz, paths["per_stream_per_hazard"], PER_STREAM_PER_HAZARD_FIELDNAMES)
    _write_dataclass_csv(per_stream, paths["per_stream_summary"], PER_STREAM_SUMMARY_FIELDNAMES)
    _write_dataclass_csv(metric_summary, paths["metric_summary"], METRIC_SUMMARY_FIELDNAMES)
    _write_dataclass_csv([verdict], paths["verdict"], VERDICT_FIELDNAMES)
    _write_dataclass_csv(table, paths["stream_metric_table"], STREAM_METRIC_TABLE_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_old_corpus_sealed()
    assert_fresh_corpus_sealed()

    per_run = load_per_run_records()
    print(
        f"v0.40 stream_stability_audit: {len(per_run)} per-run records (96 OLD + 32 FRESH)",
        flush=True,
    )

    buckets = assert_bucket_counts(per_run)

    per_haz = aggregate_per_stream_per_hazard(buckets)
    per_stream = aggregate_per_stream_summary(per_haz)
    metric_summary = build_metric_summary(per_stream)
    table = build_stream_metric_table(per_stream)
    verdict = evaluate_verdict(metric_summary)

    paths = write_outputs(per_haz, per_stream, metric_summary, verdict, table, out_dir=OUT_DIR)

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
    print("Metric agreement summary:")
    for r in metric_summary:
        print(
            f"  {r.metric}: {r.n_streams_agree}/{r.n_streams_total} streams agree "
            f"(rate {r.agreement_rate:.3f})",
            flush=True,
        )

    print()
    print(f"  m3_agreement_count:     {verdict.m3_agreement_count}")
    print(f"  family_agreement_count: {verdict.family_agreement_count}")
    print(f"  v0.40 verdict:          {verdict.verdict}")
    print(f'  locked phrase:          "{verdict.locked_phrase}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>22}  -> {path}")


if __name__ == "__main__":
    main()
