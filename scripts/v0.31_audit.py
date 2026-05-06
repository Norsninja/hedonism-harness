"""v0.31 tight w*=0.75 third-stream calibration audit driver.

Loads three independent 8-seed streams of tight_gradient x hazard=8 x
w ∈ {0.5, 0.75, 1.0} runs, applies the v0.30 4-tier classifier as a
**diagnostic** to each stream individually, and applies the same
classifier with **pre-committed pooled thresholds** (linear scaling
of the 8-seed rule: 5/5/1/5 -> 15/15/3/15) to the 24-seed pool.

The pooled verdict is the v0.31 headline. Single-stream verdicts are
diagnostic only — they MUST NOT be read as the experiment's result.

Streams loaded (option (a) — events.jsonl already on disk):
  Stream 1 (v0.27 source) — runs/fear-hunger-v0.27-tight_gradient/arms/, seeds 1..8
  Stream 2 (v0.30 fresh)  — runs/fear-hunger-v0.30-tight_gradient/arms/, seeds 9..16
  Stream 3 (v0.31 fresh)  — runs/fear-hunger-v0.31-tight_gradient/arms/, seeds 17..24

Pooled thresholds: AuditThresholds(15, 15, 3, 15).

Locked H6_pool phrase (do not paraphrase post-hoc):
    "Directionally persistent, not mechanistically robust."

The v0.28 H5/H6/H7 dip-classifier is shape-mismatched for a peak audit
and is deliberately NOT invoked. `n_strict_favoring_pool` and
`n_weight_insensitive_pool` are descriptive only.

Pre-reg: [[docs/experiments/fear_hunger_v0.31.md]].
Sweep:   [[scripts/v0.31_sweep.py]].

Usage:
    uv run python scripts/v0.31_sweep.py
    uv run python scripts/v0.31_audit.py
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path

# Import the v0.28 diagnostic module (hyphen-named filename; mirrors
# scripts/v0.29_diagnostic.py and scripts/v0.30_audit.py patterns).
_V028_PATH = Path(__file__).parent / "v0.28_trajectory_diagnostic.py"
_V028_SPEC = importlib.util.spec_from_file_location("v028_diagnostic", _V028_PATH)
if _V028_SPEC is None or _V028_SPEC.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.28 diagnostic module from {_V028_PATH}"
    raise ImportError(msg)
v028 = importlib.util.module_from_spec(_V028_SPEC)
sys.modules["v028_diagnostic"] = v028
_V028_SPEC.loader.exec_module(v028)

# Import the v0.30 audit module for evaluate_audit + AuditThresholds +
# AuditOutcome (additively refactored to accept thresholds).
_V030_PATH = Path(__file__).parent / "v0.30_audit.py"
_V030_SPEC = importlib.util.spec_from_file_location("v030_audit", _V030_PATH)
if _V030_SPEC is None or _V030_SPEC.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.30 audit module from {_V030_PATH}"
    raise ImportError(msg)
v030 = importlib.util.module_from_spec(_V030_SPEC)
sys.modules["v030_audit"] = v030
_V030_SPEC.loader.exec_module(v030)


WEIGHTS: tuple[float, float, float] = (0.50, 0.75, 1.00)


# ---------------------------------------------------------------------------
# Stream configuration
# ---------------------------------------------------------------------------


STREAM_CONFIGS: tuple[tuple[str, Path, tuple[int, ...]], ...] = (
    (
        "Stream 1 (v0.27 source)",
        Path("runs/fear-hunger-v0.27-tight_gradient/arms"),
        tuple(range(1, 9)),
    ),
    (
        "Stream 2 (v0.30 fresh)",
        Path("runs/fear-hunger-v0.30-tight_gradient/arms"),
        tuple(range(9, 17)),
    ),
    (
        "Stream 3 (v0.31 fresh)",
        Path("runs/fear-hunger-v0.31-tight_gradient/arms"),
        tuple(range(17, 25)),
    ),
)
OUT_DIR = Path("runs/fear-hunger-v0.31-tight_gradient")
TITLE = "v0.31 tight w*=0.75 third-stream calibration (pooled 24-seed audit) — report"


# Pre-committed pooled thresholds (linear scaling of the 8-seed rule).
POOLED_THRESHOLDS = v030.AuditThresholds(
    h5_delta_min=15,
    h5_favoring_min=15,
    h6_delta_min=3,
    h8_neighbor_lead_min=15,
)

# Locked headline phrase for pooled H6 — do NOT paraphrase post-hoc.
LOCKED_H6_POOL_PHRASE = "Directionally persistent, not mechanistically robust."


# ---------------------------------------------------------------------------
# Stream loading + merge
# ---------------------------------------------------------------------------


def load_stream(runs_root: Path, seeds: Sequence[int]) -> dict[tuple[int, float], object]:
    """Load per-seed observables for one stream via the v0.28 helper.

    The v0.28 ``DiagnosticConfig.weight_labels`` defaults to the three
    labels we need ({0.5, 0.75, 1.0} -> hzd8-avd0.{50,75,1.00}); v0.27
    runs roots contain additional arms (0.00, 0.25) but those are
    ignored by the loader.
    """
    config = v028.DiagnosticConfig(
        runs_root=runs_root,
        out_dir=OUT_DIR,
        seeds=tuple(seeds),
        title="(stream)",
        source_description=str(runs_root),
    )
    v028.assert_artifacts_present(config)
    return v028.load_all(config)


def merge_streams(
    per_stream: list[dict[tuple[int, float], object]],
) -> dict[tuple[int, float], object]:
    """Merge three per-stream dicts into a 24-seed dict, asserting no
    key collisions. Anchor for the cross-stream-merge test."""
    merged: dict[tuple[int, float], object] = {}
    for d in per_stream:
        for key in d:
            if key in merged:  # pragma: no cover - defensive
                msg = f"unexpected key collision across streams: {key}"
                raise ValueError(msg)
        merged.update(d)
    return merged


# ---------------------------------------------------------------------------
# Descriptive pooled observables (NOT used by the classifier)
# ---------------------------------------------------------------------------


def n_weight_insensitive(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> int:
    """Count seeds where b50 is byte-identical across all three weights."""
    return sum(
        1
        for s in seeds
        if obs[(s, 0.50)].b50 == obs[(s, 0.75)].b50 == obs[(s, 1.00)].b50  # type: ignore[attr-defined]
    )


def routing_totals(
    obs: dict[tuple[int, float], object], seeds: Sequence[int]
) -> dict[float, dict[str, int]]:
    """24-seed sums per arm of routing-channel observables."""
    totals: dict[float, dict[str, int]] = {}
    for w in WEIGHTS:
        totals[w] = {
            "total_births": sum(obs[(s, w)].total_births for s in seeds),  # type: ignore[attr-defined]
            "b50": sum(obs[(s, w)].b50 for s in seeds),  # type: ignore[attr-defined]
            "total_food_events": sum(obs[(s, w)].total_food_events for s in seeds),  # type: ignore[attr-defined]
            "total_hazard_entries": sum(obs[(s, w)].total_hazard_entries for s in seeds),  # type: ignore[attr-defined]
            "total_starvation_deaths": sum(
                obs[(s, w)].total_starvation_deaths
                for s in seeds  # type: ignore[attr-defined]
            ),
            "total_injury_deaths": sum(obs[(s, w)].total_injury_deaths for s in seeds),  # type: ignore[attr-defined]
        }
    return totals


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _per_stream_b_table(per_stream_b50: list[dict[float, int]], stream_names: list[str]) -> str:
    rows = [
        "| stream | seeds | B(0.5) | B(0.75) | B(1.0) | Δ_low | Δ_high |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name, b in zip(stream_names, per_stream_b50, strict=True):
        d_low = b[0.75] - b[0.50]
        d_high = b[0.75] - b[1.00]
        rows.append(
            f"| {name} | — | {b[0.50]} | {b[0.75]} | {b[1.00]} | {d_low:+d} | {d_high:+d} |"
        )
    return "\n".join(rows)


def _per_seed_24_table(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> str:
    header = (
        "| seed | b50 @ w=0.50 | b50 @ w=0.75 | b50 @ w=1.00 "
        "| Δ_low(seed) | Δ_high(seed) | favors | strict | weight_insensitive |"
    )
    sep = (
        "|-----:|-------------:|-------------:|-------------:"
        "|------------:|-------------:|:------:|:------:|:------------------:|"
    )
    out_rows = [header, sep]
    for s in seeds:
        b50_50 = obs[(s, 0.50)].b50  # type: ignore[attr-defined]
        b50_75 = obs[(s, 0.75)].b50  # type: ignore[attr-defined]
        b50_100 = obs[(s, 1.00)].b50  # type: ignore[attr-defined]
        d_low = b50_75 - b50_50
        d_high = b50_75 - b50_100
        favors = b50_75 >= b50_50 and b50_75 >= b50_100
        strict = b50_75 > b50_50 and b50_75 > b50_100
        flat = b50_50 == b50_75 == b50_100
        out_rows.append(
            f"| {s} | {b50_50} | {b50_75} | {b50_100} | "
            f"{d_low:+d} | {d_high:+d} | "
            f"{'yes' if favors else 'no'} | {'yes' if strict else 'no'} | "
            f"{'yes' if flat else 'no'} |"
        )
    aggs = [sum(obs[(s, w)].b50 for s in seeds) for w in WEIGHTS]  # type: ignore[attr-defined]
    out_rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | "
        f"**{aggs[1] - aggs[0]:+d}** | **{aggs[1] - aggs[2]:+d}** | — | — | — |"
    )
    return "\n".join(out_rows)


def _routing_table(totals: dict[float, dict[str, int]]) -> str:
    rows = [
        "| weight | total_births | b>50 | total_food | hazard_entries | starvation | injury |",
        "|-------:|-------------:|-----:|-----------:|---------------:|-----------:|-------:|",
    ]
    for w in WEIGHTS:
        t = totals[w]
        rows.append(
            f"| {w:.2f} | {t['total_births']} | {t['b50']} | {t['total_food_events']} "
            f"| {t['total_hazard_entries']} | {t['total_starvation_deaths']} "
            f"| {t['total_injury_deaths']} |"
        )
    return "\n".join(rows)


def _verdict_block(label: str, outcome) -> str:
    return (
        f"### {label}\n\n"
        f"**Verdict:** **{outcome.hypothesis} — {outcome.label}**\n\n"
        f"**Operational summary:** {outcome.summary}\n"
    )


def write_report(
    pooled_obs: dict[tuple[int, float], object],
    pooled_seeds: Sequence[int],
    stream_outcomes: list,
    stream_names: list[str],
    pooled_outcome,
    n_weight_insensitive_pool: int,
    pooled_totals: dict[float, dict[str, int]],
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "audit.md"
    n_seeds = len(pooled_seeds)
    per_stream_b50: list[dict[float, int]] = []
    stream_seed_sets: list[Sequence[int]] = [cfg[2] for cfg in STREAM_CONFIGS]
    for seeds in stream_seed_sets:
        per_stream_b50.append(
            {w: sum(pooled_obs[(s, w)].b50 for s in seeds) for w in WEIGHTS}  # type: ignore[attr-defined]
        )

    pooled_h6_extra = ""
    if pooled_outcome.hypothesis == "H6":
        pooled_h6_extra = (
            f"\n**Locked headline phrase (pre-committed in v0.31 pre-reg):**\n\n"
            f"> {LOCKED_H6_POOL_PHRASE}\n"
        )

    parts = [
        f"# {TITLE}",
        "",
        "**Source:** three independent 8-seed streams of tight_gradient x "
        "hazard=8 x w ∈ {0.5, 0.75, 1.0}. v0.27 (1..8), v0.30 (9..16), v0.31 "
        "(17..24).",
        "",
        "**Pooled thresholds (pre-committed):** "
        f"H5 Δ ≥ {POOLED_THRESHOLDS.h5_delta_min} AND n_favoring ≥ "
        f"{POOLED_THRESHOLDS.h5_favoring_min}; "
        f"H6 Δ ≥ {POOLED_THRESHOLDS.h6_delta_min}; "
        f"H8 neighbour lead ≥ {POOLED_THRESHOLDS.h8_neighbor_lead_min}.",
        "",
        "## Pooled 24-seed verdict (v0.31 HEADLINE)",
        "",
        f"**Verdict:** **{pooled_outcome.hypothesis} — {pooled_outcome.label}**",
        "",
        f"**Operational summary:** {pooled_outcome.summary}",
        pooled_h6_extra,
        "## Single-stream diagnostic verdicts",
        "",
        "Single-stream verdicts use the v0.30 default 8-seed thresholds "
        "(5/5/1/5). They are **diagnostic only** — the v0.31 headline is the "
        "pooled verdict above.",
        "",
        *(
            _verdict_block(name, outcome)
            for name, outcome in zip(stream_names, stream_outcomes, strict=True)
        ),
        "## Cross-stream aggregate B(w) and per-stream deltas",
        "",
        _per_stream_b_table(per_stream_b50, stream_names),
        "",
        "## Pooled aggregate B(w) and partition deltas",
        "",
        "| weight | B_pool(w) = Σ b>50 over 24 seeds |",
        "|-------:|---------------------------------:|",
        f"| 0.50 | {pooled_outcome.b_low} |",
        f"| 0.75 | {pooled_outcome.b_med} |",
        f"| 1.00 | {pooled_outcome.b_high} |",
        "",
        f"- Δ_low_pool  = B(0.75) - B(0.5)  = **{pooled_outcome.delta_low:+d}**",
        f"- Δ_high_pool = B(0.75) - B(1.0)  = **{pooled_outcome.delta_high:+d}**",
        f"- n_favoring_pool (ties allowed)   = **{pooled_outcome.n_favoring}/{n_seeds}**",
        (
            f"- n_strict_favoring_pool (strict)  = "
            f"{pooled_outcome.n_strict_favoring}/{n_seeds}  *(descriptive only)*"
        ),
        (
            f"- n_weight_insensitive_pool       = "
            f"**{n_weight_insensitive_pool}/{n_seeds}**  "
            f"*(descriptive; pre-committed candidate primary finding if ≥ 18/24)*"
        ),
        "",
        f"## Per-seed b>50 across w ∈ {{0.5, 0.75, 1.0}} (all {n_seeds} seeds)",
        "",
        _per_seed_24_table(pooled_obs, pooled_seeds),
        "",
        "## Pooled routing-channel and productivity totals (supporting)",
        "",
        _routing_table(pooled_totals),
        "",
        f"## Pooled aggregate band-resolved telemetry ({n_seeds}-seed sums)",
        "",
        v028._band_aggregate_table(pooled_obs, pooled_seeds, "births_per_band", "Births per band"),
        "",
        v028._band_aggregate_table(
            pooled_obs, pooled_seeds, "food_per_band", "Food events per band"
        ),
        "",
        v028._band_aggregate_table(
            pooled_obs, pooled_seeds, "haz_entries_per_band", "Hazard entries per band"
        ),
        "",
        v028._band_aggregate_table(
            pooled_obs, pooled_seeds, "starv_per_band", "Starvation deaths per band"
        ),
        "",
        v028._band_aggregate_table(
            pooled_obs, pooled_seeds, "inj_per_band", "Injury deaths per band"
        ),
        "",
        f"**Final pooled verdict:** {pooled_outcome.hypothesis} — {pooled_outcome.label}",
        "",
    ]
    out_path.write_text("\n".join(parts))
    return out_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    # Load all three streams.
    per_stream_obs = []
    stream_names = []
    for name, runs_root, seeds in STREAM_CONFIGS:
        per_stream_obs.append(load_stream(runs_root, seeds))
        stream_names.append(name)

    pooled_obs = merge_streams(per_stream_obs)
    pooled_seeds = tuple(s for _, _, seeds in STREAM_CONFIGS for s in seeds)

    # Single-stream diagnostic verdicts (default 8-seed thresholds).
    stream_outcomes = []
    for (_name, _root, seeds), obs in zip(STREAM_CONFIGS, per_stream_obs, strict=True):
        b50_at = {(s, w): obs[(s, w)].b50 for s in seeds for w in WEIGHTS}  # type: ignore[attr-defined]
        stream_outcomes.append(v030.evaluate_audit(b50_at, seeds))

    # Pooled 24-seed verdict (v0.31 headline).
    pooled_b50_at = {
        (s, w): pooled_obs[(s, w)].b50
        for s in pooled_seeds
        for w in WEIGHTS  # type: ignore[attr-defined]
    }
    pooled_outcome = v030.evaluate_audit(pooled_b50_at, pooled_seeds, thresholds=POOLED_THRESHOLDS)

    n_wi_pool = n_weight_insensitive(pooled_obs, pooled_seeds)
    pooled_totals = routing_totals(pooled_obs, pooled_seeds)

    out_path = write_report(
        pooled_obs,
        pooled_seeds,
        stream_outcomes,
        stream_names,
        pooled_outcome,
        n_wi_pool,
        pooled_totals,
    )

    print("v0.31 third-stream calibration audit")
    print()
    for name, outcome in zip(stream_names, stream_outcomes, strict=True):
        print(f"  {name:<28} -> {outcome.hypothesis} ({outcome.label})")
        print(f"    {outcome.summary}")
    print()
    print(f"  Pooled 24-seed verdict      -> {pooled_outcome.hypothesis} ({pooled_outcome.label})")
    print(f"    {pooled_outcome.summary}")
    print(f"    n_weight_insensitive_pool = {n_wi_pool}/{len(pooled_seeds)}")
    if pooled_outcome.hypothesis == "H6":
        print()
        print(f"  Locked headline phrase: {LOCKED_H6_POOL_PHRASE}")
    print()
    print(f"Audit report written to {out_path}")


if __name__ == "__main__":
    main()
