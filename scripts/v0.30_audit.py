"""v0.30 tight w*=0.75 small-margin robustness audit driver.

Audits the v0.27 tight w*=0.75 +2-birth interior-optimum claim against a
fresh seed stream (9..16). Applies the 4-tier robustness partition
defined in [[docs/experiments/fear_hunger_v0.30.md]]:

    Priority order (first match wins):
      H8 — REVERSAL:  max(B(0.5), B(1.0)) - B(0.75) >= 5
      H5 — ROBUST:    Δ_low >= 5 AND Δ_high >= 5 AND n_favoring >= 5
      H6 — WEAK:      Δ_low >= 1 AND Δ_high >= 1, NOT H5
      H7 — FAILURE:   none of H5 / H6 / H8

    where:
      Δ_low      = B(0.75) - B(0.5)
      Δ_high     = B(0.75) - B(1.0)
      n_favoring = |{ s : b50(s, 0.75) >= b50(s, 0.5)
                       AND b50(s, 0.75) >= b50(s, 1.0) }|

The v0.28 H5/H6/H7 dip-classifier is shape-mismatched for a peak audit
and is deliberately NOT invoked here. Per-seed observables and band-
resolved trajectory tables are reused from the v0.28 module
(`load_all`, `_band_aggregate_table`) as supporting evidence only.

n_strict_favoring (strict-greater per-seed preference) is reported
descriptively and is NOT used by the classifier.

Pre-reg: [[docs/experiments/fear_hunger_v0.30.md]].
Sweep:   [[scripts/v0.30_sweep.py]].

Usage:
    uv run python scripts/v0.30_sweep.py
    uv run python scripts/v0.30_audit.py
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# Import the v0.28 diagnostic module directly (hyphen-named filename
# precludes a package-level import). Mirrors scripts/v0.29_diagnostic.py.
_V028_PATH = Path(__file__).parent / "v0.28_trajectory_diagnostic.py"
_spec = importlib.util.spec_from_file_location("v028_diagnostic", _V028_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.28 diagnostic module from {_V028_PATH}"
    raise ImportError(msg)
v028 = importlib.util.module_from_spec(_spec)
sys.modules["v028_diagnostic"] = v028
_spec.loader.exec_module(v028)


SEEDS: tuple[int, ...] = tuple(range(9, 17))
RUNS_ROOT = Path("runs/fear-hunger-v0.30-tight_gradient/arms")
OUT_DIR = Path("runs/fear-hunger-v0.30-tight_gradient")
TITLE = "v0.30 tight w*=0.75 small-margin robustness audit (seeds 9..16) — report"
SOURCE = (
    "v0.30 events.jsonl artifacts at "
    "`runs/fear-hunger-v0.30-tight_gradient/arms/hzd8-avd0.{50,75,1.00}/"
    "seed-{9..16}/events.jsonl` (24 runs)."
)

WEIGHTS: tuple[float, float, float] = (0.50, 0.75, 1.00)


# ---------------------------------------------------------------------------
# Pure-function classifier (testable in isolation)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditThresholds:
    """4-tier classifier thresholds.

    Defaults match the v0.30 single-stream rule (5 / 5 / 1 / 5). v0.31
    pools 24 seeds and calls with linearly-scaled thresholds (15 / 15 /
    3 / 15). The classifier itself is identical; only the cut-points
    differ.
    """

    h5_delta_min: int = 5
    h5_favoring_min: int = 5
    h6_delta_min: int = 1
    h8_neighbor_lead_min: int = 5


DEFAULT_THRESHOLDS = AuditThresholds()


@dataclass(frozen=True)
class AuditOutcome:
    """Result of the 4-tier robustness partition.

    ``hypothesis`` is one of {"H5", "H6", "H7", "H8"}.
    ``label`` is the human-readable headline. Threshold values are
    interpolated from the active ``AuditThresholds`` so the same
    classifier produces self-describing labels for both 8-seed and
    24-seed pooled invocations.
    ``summary`` is a single-line operational summary (deltas + counts).
    """

    hypothesis: str
    label: str
    summary: str
    b_low: int
    b_med: int
    b_high: int
    delta_low: int
    delta_high: int
    n_favoring: int
    n_strict_favoring: int


def evaluate_audit(
    b50_at: dict[tuple[int, float], int],
    seeds: Sequence[int],
    *,
    thresholds: AuditThresholds = DEFAULT_THRESHOLDS,
    candidate_label: str = "w=0.75",
) -> AuditOutcome:
    """Apply the 4-tier robustness partition to per-seed b50.

    ``b50_at[(seed, weight)]`` -> int. ``seeds`` is the seed set;
    weights are fixed at {0.5, 0.75, 1.0}. ``thresholds`` defaults to
    the v0.30 8-seed rule; v0.31 calls with the pooled 24-seed
    thresholds.

    ``candidate_label`` is interpolated into the human-readable H7 / H8
    labels. Default ``"w=0.75"`` preserves v0.30 / v0.31 audit-report
    output byte-identical. v0.32 passes ``"h=8"`` because the slot
    keys (0.50, 0.75, 1.00) are positional placeholders for hazards
    {4, 8, 12} on the hazard-axis audit, not literal weight values.
    """
    b_low = sum(b50_at[(s, 0.50)] for s in seeds)
    b_med = sum(b50_at[(s, 0.75)] for s in seeds)
    b_high = sum(b50_at[(s, 1.00)] for s in seeds)
    delta_low = b_med - b_low
    delta_high = b_med - b_high
    neighbor_lead = max(b_low, b_high) - b_med

    n_favoring = sum(
        1
        for s in seeds
        if b50_at[(s, 0.75)] >= b50_at[(s, 0.50)] and b50_at[(s, 0.75)] >= b50_at[(s, 1.00)]
    )
    n_strict_favoring = sum(
        1
        for s in seeds
        if b50_at[(s, 0.75)] > b50_at[(s, 0.50)] and b50_at[(s, 0.75)] > b50_at[(s, 1.00)]
    )

    summary = (
        f"B(0.5)={b_low} B(0.75)={b_med} B(1.0)={b_high}; "
        f"Δ_low={delta_low:+d} Δ_high={delta_high:+d}; "
        f"n_favoring={n_favoring}/{len(seeds)} "
        f"n_strict_favoring={n_strict_favoring}/{len(seeds)}"
    )

    # Priority order: H8 -> H5 -> H6 -> H7.
    if neighbor_lead >= thresholds.h8_neighbor_lead_min:
        return AuditOutcome(
            hypothesis="H8",
            label=(
                f"REVERSAL — a neighbour beats {candidate_label} by "
                f">= {thresholds.h8_neighbor_lead_min} births"
            ),
            summary=summary,
            b_low=b_low,
            b_med=b_med,
            b_high=b_high,
            delta_low=delta_low,
            delta_high=delta_high,
            n_favoring=n_favoring,
            n_strict_favoring=n_strict_favoring,
        )
    if (
        delta_low >= thresholds.h5_delta_min
        and delta_high >= thresholds.h5_delta_min
        and n_favoring >= thresholds.h5_favoring_min
    ):
        return AuditOutcome(
            hypothesis="H5",
            label=(
                f"ROBUST REPRODUCTION — both Δ >= {thresholds.h5_delta_min} "
                f"and n_favoring >= {thresholds.h5_favoring_min}"
            ),
            summary=summary,
            b_low=b_low,
            b_med=b_med,
            b_high=b_high,
            delta_low=delta_low,
            delta_high=delta_high,
            n_favoring=n_favoring,
            n_strict_favoring=n_strict_favoring,
        )
    if delta_low >= thresholds.h6_delta_min and delta_high >= thresholds.h6_delta_min:
        return AuditOutcome(
            hypothesis="H6",
            label=(
                "WEAK REPRODUCTION — beats both neighbours, but small-margin "
                "or per-seed inconsistent"
            ),
            summary=summary,
            b_low=b_low,
            b_med=b_med,
            b_high=b_high,
            delta_low=delta_low,
            delta_high=delta_high,
            n_favoring=n_favoring,
            n_strict_favoring=n_strict_favoring,
        )
    return AuditOutcome(
        hypothesis="H7",
        label=(
            f"FAILURE / SAMPLE NOISE — {candidate_label} does not clear "
            f"the weak two-neighbour threshold and no reversal threshold fires"
        ),
        summary=summary,
        b_low=b_low,
        b_med=b_med,
        b_high=b_high,
        delta_low=delta_low,
        delta_high=delta_high,
        n_favoring=n_favoring,
        n_strict_favoring=n_strict_favoring,
    )


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _per_seed_b50_table(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> str:
    header = (
        "| seed | b50 @ w=0.50 | b50 @ w=0.75 | b50 @ w=1.00 "
        "| Δ_low(seed) | Δ_high(seed) | favors_w0.75 | strict |"
    )
    sep = (
        "|-----:|-------------:|-------------:|-------------:"
        "|------------:|-------------:|:------------:|:------:|"
    )
    rows = [header, sep]
    for s in seeds:
        b50_50 = obs[(s, 0.50)].b50  # type: ignore[attr-defined]
        b50_75 = obs[(s, 0.75)].b50  # type: ignore[attr-defined]
        b50_100 = obs[(s, 1.00)].b50  # type: ignore[attr-defined]
        d_low = b50_75 - b50_50
        d_high = b50_75 - b50_100
        favors = b50_75 >= b50_50 and b50_75 >= b50_100
        strict = b50_75 > b50_50 and b50_75 > b50_100
        rows.append(
            f"| {s} | {b50_50} | {b50_75} | {b50_100} | "
            f"{d_low:+d} | {d_high:+d} | "
            f"{'yes' if favors else 'no'} | {'yes' if strict else 'no'} |"
        )
    aggs = [sum(obs[(s, w)].b50 for s in seeds) for w in WEIGHTS]
    rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | "
        f"**{aggs[1] - aggs[0]:+d}** | **{aggs[1] - aggs[2]:+d}** | — | — |"
    )
    return "\n".join(rows)


def _routing_channel_table(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> str:
    rows = [
        "| weight | total_births | b>50 | total_food | hazard_entries | starvation | injury |",
        "|-------:|-------------:|-----:|-----------:|---------------:|-----------:|-------:|",
    ]
    for w in WEIGHTS:
        births = sum(obs[(s, w)].total_births for s in seeds)
        b50 = sum(obs[(s, w)].b50 for s in seeds)
        food = sum(obs[(s, w)].total_food_events for s in seeds)
        haz = sum(obs[(s, w)].total_hazard_entries for s in seeds)
        starv = sum(obs[(s, w)].total_starvation_deaths for s in seeds)
        inj = sum(obs[(s, w)].total_injury_deaths for s in seeds)
        rows.append(f"| {w:.2f} | {births} | {b50} | {food} | {haz} | {starv} | {inj} |")
    return "\n".join(rows)


def write_report(
    config,
    obs: dict[tuple[int, float], object],
    outcome: AuditOutcome,
) -> Path:
    config.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = config.out_dir / "audit.md"
    n_seeds = len(config.seeds)
    parts = [
        f"# {config.title}",
        "",
        f"**Source:** {config.source_description}",
        "",
        f"**Verdict:** **{outcome.hypothesis} — {outcome.label}**",
        "",
        f"**Operational summary:** {outcome.summary}",
        "",
        "## Aggregate B(w) and partition deltas",
        "",
        "| weight | B(w) = Σ b>50 |",
        "|-------:|--------------:|",
        f"| 0.50 | {outcome.b_low} |",
        f"| 0.75 | {outcome.b_med} |",
        f"| 1.00 | {outcome.b_high} |",
        "",
        f"- Δ_low  = B(0.75) - B(0.5)  = **{outcome.delta_low:+d}**",
        f"- Δ_high = B(0.75) - B(1.0)  = **{outcome.delta_high:+d}**",
        f"- n_favoring (ties allowed)   = **{outcome.n_favoring}/{n_seeds}**",
        (
            f"- n_strict_favoring (strict)  = "
            f"{outcome.n_strict_favoring}/{n_seeds}  *(descriptive only)*"
        ),
        "",
        "## Per-seed b>50 across w ∈ {0.5, 0.75, 1.0}",
        "",
        _per_seed_b50_table(obs, config.seeds),
        "",
        "## Routing-channel and productivity totals (supporting)",
        "",
        _routing_channel_table(obs, config.seeds),
        "",
        f"## Aggregate band-resolved telemetry ({n_seeds}-seed sums)",
        "",
        v028._band_aggregate_table(obs, config.seeds, "births_per_band", "Births per band"),
        "",
        v028._band_aggregate_table(obs, config.seeds, "food_per_band", "Food events per band"),
        "",
        v028._band_aggregate_table(
            obs, config.seeds, "haz_entries_per_band", "Hazard entries per band"
        ),
        "",
        v028._band_aggregate_table(
            obs, config.seeds, "starv_per_band", "Starvation deaths per band"
        ),
        "",
        v028._band_aggregate_table(obs, config.seeds, "inj_per_band", "Injury deaths per band"),
        "",
        f"**Final verdict:** {outcome.hypothesis} — {outcome.label}",
        "",
    ]
    out_path.write_text("\n".join(parts))
    return out_path


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    config = v028.DiagnosticConfig(
        runs_root=RUNS_ROOT,
        out_dir=OUT_DIR,
        seeds=SEEDS,
        title=TITLE,
        source_description=SOURCE,
    )
    v028.assert_artifacts_present(config)
    obs = v028.load_all(config)

    b50_at = {(s, w): obs[(s, w)].b50 for s in SEEDS for w in WEIGHTS}
    outcome = evaluate_audit(b50_at, SEEDS)

    out_path = write_report(config, obs, outcome)

    print(f"v0.30 verdict:           {outcome.hypothesis} — {outcome.label}")
    print(f"  operational summary:   {outcome.summary}")
    print(f"Audit report written to  {out_path}")


if __name__ == "__main__":
    main()
