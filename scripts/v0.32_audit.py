"""v0.32 tight h*=8 hazard-axis reproducibility audit driver.

Loads tight_gradient x influx=1.0 x hazard in {0, 4, 8, 12} x seeds
9..16 = 32 runs and applies the v0.30 4-tier classifier (default 8-seed
thresholds) to the {h=4, h=8, h=12} slice with candidate_label="h=8".
h=0 is reported as a descriptive baseline only.

Three-step audit (per v0.32 pre-reg):

  1. **Semantic determinism anchor (H1c, halt condition):**
     B(h=8, seeds 9..16) = 96 exactly. Pins behavioural equivalence
     between V0_25_ARMS substrate (w=None) and V0_27+ explicit w=1.0
     (v0.30 stream 2's column at hzd=8 was 96).
  2. **Classifier slice verdict (single-stream headline):**
     evaluate_audit on the 3-arm slice {h=4, h=8, h=12} mapped to
     (0.50, 0.75, 1.00) classifier slots. candidate_label="h=8".
  3. **Descriptive 4-arm report:**
     per-seed b50 across all four hazards (h=0 baseline + classifier
     slice), n_hazard_insensitive (count of seeds byte-identical
     across {h=4, h=8, h=12}), routing tables, band-resolved telemetry.

The pooled rule does NOT enter v0.32 (no prior fresh-stream observation
to pool with). Pooling is gated to v0.33 if v0.32 fires H6 WEAK.

Pre-reg: [[docs/experiments/fear_hunger_v0.32.md]].
Sweep:   [[scripts/v0.32_sweep.py]].

Usage:
    uv run python scripts/v0.32_sweep.py
    uv run python scripts/v0.32_audit.py
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path

# Import v0.28 + v0.30 modules via importlib (hyphen-named files;
# mirrors the v0.29 / v0.30 / v0.31 patterns).
_V028_PATH = Path(__file__).parent / "v0.28_trajectory_diagnostic.py"
_V028_SPEC = importlib.util.spec_from_file_location("v028_diagnostic", _V028_PATH)
if _V028_SPEC is None or _V028_SPEC.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.28 diagnostic module from {_V028_PATH}"
    raise ImportError(msg)
v028 = importlib.util.module_from_spec(_V028_SPEC)
sys.modules["v028_diagnostic"] = v028
_V028_SPEC.loader.exec_module(v028)

_V030_PATH = Path(__file__).parent / "v0.30_audit.py"
_V030_SPEC = importlib.util.spec_from_file_location("v030_audit", _V030_PATH)
if _V030_SPEC is None or _V030_SPEC.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.30 audit module from {_V030_PATH}"
    raise ImportError(msg)
v030 = importlib.util.module_from_spec(_V030_SPEC)
sys.modules["v030_audit"] = v030
_V030_SPEC.loader.exec_module(v030)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


SEEDS: tuple[int, ...] = tuple(range(9, 17))
RUNS_ROOT = Path("runs/fear-hunger-v0.32-tight_gradient/arms")
OUT_DIR = Path("runs/fear-hunger-v0.32-tight_gradient")
TITLE = "v0.32 tight h*=8 hazard-axis reproducibility audit (seeds 9..16) — report"
SOURCE = (
    "v0.32 events.jsonl artifacts at "
    "`runs/fear-hunger-v0.32-tight_gradient/arms/transfer-1500-hzd{0,4,8,12}-influx-1.0/"
    "seed-{9..16}/events.jsonl` (32 runs)."
)

# Classifier slot keys are positional placeholders for hazards (NOT literal weight values).
SLOT_LOW = 0.50  # -> hazard 4
SLOT_MED = 0.75  # -> hazard 8 (candidate interior peak)
SLOT_HIGH = 1.00  # -> hazard 12
SLOT_BASELINE = 0.00  # -> hazard 0 (descriptive baseline only)
ALL_SLOTS: tuple[float, ...] = (SLOT_BASELINE, SLOT_LOW, SLOT_MED, SLOT_HIGH)
CLASSIFIER_SLOTS: tuple[float, ...] = (SLOT_LOW, SLOT_MED, SLOT_HIGH)
SLOT_TO_HAZARD: dict[float, int] = {
    SLOT_BASELINE: 0,
    SLOT_LOW: 4,
    SLOT_MED: 8,
    SLOT_HIGH: 12,
}
SLOT_TO_LABEL: dict[float, str] = {
    SLOT_BASELINE: "transfer-1500-hzd0-influx-1.0",
    SLOT_LOW: "transfer-1500-hzd4-influx-1.0",
    SLOT_MED: "transfer-1500-hzd8-influx-1.0",
    SLOT_HIGH: "transfer-1500-hzd12-influx-1.0",
}

# H1c semantic determinism anchor target.
ANCHOR_HZD8_SEEDS_9_16_B50_SUM = 96


# ---------------------------------------------------------------------------
# Stream loading
# ---------------------------------------------------------------------------


def load_observables() -> dict[tuple[int, float], object]:
    """Load per-seed observables for all 4 arms x 8 seeds via v0.28."""
    config = v028.DiagnosticConfig(
        runs_root=RUNS_ROOT,
        out_dir=OUT_DIR,
        seeds=SEEDS,
        weight_labels=dict(SLOT_TO_LABEL),
        title=TITLE,
        source_description=SOURCE,
    )
    v028.assert_artifacts_present(config)
    return v028.load_all(config)


# ---------------------------------------------------------------------------
# Semantic determinism anchor (H1c)
# ---------------------------------------------------------------------------


def assert_semantic_determinism_anchor(obs: dict[tuple[int, float], object]) -> int:
    """H1c halt condition: B(h=8, seeds 9..16) = 96. Mismatch raises."""
    b_h8 = sum(obs[(s, SLOT_MED)].b50 for s in SEEDS)  # type: ignore[attr-defined]
    if b_h8 != ANCHOR_HZD8_SEEDS_9_16_B50_SUM:
        msg = (
            f"v0.32 H1c semantic determinism anchor FAILED: "
            f"B(h=8, seeds 9..16) = {b_h8}, expected "
            f"{ANCHOR_HZD8_SEEDS_9_16_B50_SUM} (matching v0.30 stream 2 "
            f"explicit-w=1.0). The substrate-equivalence assumption "
            f"between V0_25_ARMS (w=None) and V0_27+ (w=1.0) is broken; "
            f"halt audit and investigate."
        )
        raise AssertionError(msg)
    return b_h8


# ---------------------------------------------------------------------------
# Descriptive observables
# ---------------------------------------------------------------------------


def n_hazard_insensitive(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> int:
    """Count seeds where b50 is byte-identical across all three classifier-slice hazards."""
    return sum(
        1
        for s in seeds
        if obs[(s, SLOT_LOW)].b50  # type: ignore[attr-defined]
        == obs[(s, SLOT_MED)].b50  # type: ignore[attr-defined]
        == obs[(s, SLOT_HIGH)].b50  # type: ignore[attr-defined]
    )


def routing_totals(
    obs: dict[tuple[int, float], object], seeds: Sequence[int]
) -> dict[float, dict[str, int]]:
    """8-seed sums per arm of routing-channel observables (all 4 arms)."""
    totals: dict[float, dict[str, int]] = {}
    for slot in ALL_SLOTS:
        totals[slot] = {
            "total_births": sum(obs[(s, slot)].total_births for s in seeds),  # type: ignore[attr-defined]
            "b50": sum(obs[(s, slot)].b50 for s in seeds),  # type: ignore[attr-defined]
            "total_food_events": sum(obs[(s, slot)].total_food_events for s in seeds),  # type: ignore[attr-defined]
            "total_hazard_entries": sum(obs[(s, slot)].total_hazard_entries for s in seeds),  # type: ignore[attr-defined]
            "total_starvation_deaths": sum(
                obs[(s, slot)].total_starvation_deaths
                for s in seeds  # type: ignore[attr-defined]
            ),
            "total_injury_deaths": sum(obs[(s, slot)].total_injury_deaths for s in seeds),  # type: ignore[attr-defined]
        }
    return totals


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _per_seed_table(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> str:
    header = (
        "| seed | b50 @ h=0 | b50 @ h=4 | b50 @ h=8 | b50 @ h=12 "
        "| Δ_low(seed) | Δ_high(seed) | favors_h8 | strict | hazard_insensitive |"
    )
    sep = (
        "|-----:|----------:|----------:|----------:|-----------:"
        "|------------:|-------------:|:---------:|:------:|:------------------:|"
    )
    rows = [header, sep]
    for s in seeds:
        b_h0 = obs[(s, SLOT_BASELINE)].b50  # type: ignore[attr-defined]
        b_h4 = obs[(s, SLOT_LOW)].b50  # type: ignore[attr-defined]
        b_h8 = obs[(s, SLOT_MED)].b50  # type: ignore[attr-defined]
        b_h12 = obs[(s, SLOT_HIGH)].b50  # type: ignore[attr-defined]
        d_low = b_h8 - b_h4
        d_high = b_h8 - b_h12
        favors = b_h8 >= b_h4 and b_h8 >= b_h12
        strict = b_h8 > b_h4 and b_h8 > b_h12
        flat = b_h4 == b_h8 == b_h12
        rows.append(
            f"| {s} | {b_h0} | {b_h4} | {b_h8} | {b_h12} | "
            f"{d_low:+d} | {d_high:+d} | "
            f"{'yes' if favors else 'no'} | {'yes' if strict else 'no'} | "
            f"{'yes' if flat else 'no'} |"
        )
    aggs = [sum(obs[(s, slot)].b50 for s in seeds) for slot in ALL_SLOTS]  # type: ignore[attr-defined]
    rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | **{aggs[3]}** | "
        f"**{aggs[2] - aggs[1]:+d}** | **{aggs[2] - aggs[3]:+d}** | — | — | — |"
    )
    return "\n".join(rows)


def _routing_table(totals: dict[float, dict[str, int]]) -> str:
    rows = [
        "| hazard | total_births | b>50 | total_food | hazard_entries | starvation | injury |",
        "|-------:|-------------:|-----:|-----------:|---------------:|-----------:|-------:|",
    ]
    for slot in ALL_SLOTS:
        h = SLOT_TO_HAZARD[slot]
        t = totals[slot]
        rows.append(
            f"| {h} | {t['total_births']} | {t['b50']} | {t['total_food_events']} "
            f"| {t['total_hazard_entries']} | {t['total_starvation_deaths']} "
            f"| {t['total_injury_deaths']} |"
        )
    return "\n".join(rows)


def _band_aggregate_table_for_slots(
    obs: dict[tuple[int, float], object],
    seeds: Sequence[int],
    band_attr: str,
    title: str,
) -> str:
    """Mirror of v028._band_aggregate_table that iterates over the 4 v0.32
    arms (slots 0.0 / 0.5 / 0.75 / 1.0 -> hazards 0 / 4 / 8 / 12) and
    labels rows with hazard, not weight."""
    # Discover band keys from the first arm's first seed.
    sample = obs[(seeds[0], ALL_SLOTS[0])]
    band_dict = getattr(sample, band_attr)
    bands = list(band_dict.keys())
    header = "| hazard | " + " | ".join(bands) + " |"
    sep = "|" + "---:|" * (len(bands) + 1)
    rows = [f"### {title}", "", header, sep]
    for slot in ALL_SLOTS:
        h = SLOT_TO_HAZARD[slot]
        cells = []
        for band in bands:
            total = sum(getattr(obs[(s, slot)], band_attr).get(band, 0) for s in seeds)
            cells.append(str(total))
        rows.append(f"| {h} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def write_report(
    obs: dict[tuple[int, float], object],
    seeds: Sequence[int],
    outcome,
    n_hzd_insens: int,
    totals: dict[float, dict[str, int]],
    anchor_b: int,
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "audit.md"
    n_seeds = len(seeds)
    parts = [
        f"# {TITLE}",
        "",
        f"**Source:** {SOURCE}",
        "",
        "## Single-stream verdict (v0.32 headline)",
        "",
        "Classifier slice: {h=4, h=8, h=12} mapped to (0.50, 0.75, 1.00) "
        "slot keys. Default 8-seed thresholds (5/5/1/5). h=0 is descriptive "
        "baseline only and is NOT in the classifier.",
        "",
        f"**Verdict:** **{outcome.hypothesis} — {outcome.label}**",
        "",
        f"**Operational summary:** {outcome.summary}",
        "",
        "## H1c semantic determinism anchor",
        "",
        (
            f"B(h=8, seeds 9..16) = **{anchor_b}** "
            f"(target {ANCHOR_HZD8_SEEDS_9_16_B50_SUM}). "
            "Pins behavioural equivalence between V0_25_ARMS (w=None) and "
            "V0_27+ explicit w=1.0 against v0.30 stream 2."
        ),
        "",
        "## Aggregate B(h) across all 4 arms",
        "",
        "| hazard | B(h) = Σ b>50 |",
        "|-------:|--------------:|",
        f"| 0 | {totals[SLOT_BASELINE]['b50']} |",
        f"| 4 | {totals[SLOT_LOW]['b50']} |",
        f"| 8 | **{totals[SLOT_MED]['b50']}** |",
        f"| 12 | {totals[SLOT_HIGH]['b50']} |",
        "",
        f"- Δ_low  = B(h=8) - B(h=4)  = **{outcome.delta_low:+d}**",
        f"- Δ_high = B(h=8) - B(h=12) = **{outcome.delta_high:+d}**",
        f"- n_favoring (ties allowed) = **{outcome.n_favoring}/{n_seeds}**",
        (
            f"- n_strict_favoring (strict)  = "
            f"{outcome.n_strict_favoring}/{n_seeds}  *(descriptive only)*"
        ),
        (
            f"- n_hazard_insensitive (descriptive) = "
            f"**{n_hzd_insens}/{n_seeds}**  "
            f"*(byte-identical b50 across h ∈ {{4, 8, 12}}; "
            f"≥ 6/8 = candidate primary finding per pre-reg)*"
        ),
        "",
        f"## Per-seed b>50 across h ∈ {{0, 4, 8, 12}} ({n_seeds} seeds)",
        "",
        _per_seed_table(obs, seeds),
        "",
        "## Routing-channel and productivity totals (all 4 arms; supporting)",
        "",
        _routing_table(totals),
        "",
        f"## Band-resolved telemetry ({n_seeds}-seed sums per hazard)",
        "",
        _band_aggregate_table_for_slots(obs, seeds, "births_per_band", "Births per band"),
        "",
        _band_aggregate_table_for_slots(obs, seeds, "food_per_band", "Food events per band"),
        "",
        _band_aggregate_table_for_slots(
            obs, seeds, "haz_entries_per_band", "Hazard entries per band"
        ),
        "",
        _band_aggregate_table_for_slots(obs, seeds, "starv_per_band", "Starvation deaths per band"),
        "",
        _band_aggregate_table_for_slots(obs, seeds, "inj_per_band", "Injury deaths per band"),
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
    obs = load_observables()

    # Step 1: H1c semantic determinism anchor (halt condition).
    anchor_b = assert_semantic_determinism_anchor(obs)
    print(f"H1c semantic determinism anchor: B(h=8, seeds 9..16) = {anchor_b} ✓")

    # Step 2: Classifier slice verdict.
    b50_at = {(s, slot): obs[(s, slot)].b50 for s in SEEDS for slot in CLASSIFIER_SLOTS}  # type: ignore[attr-defined]
    outcome = v030.evaluate_audit(b50_at, SEEDS, candidate_label="h=8")

    # Step 3: Descriptive 4-arm report.
    n_hzd_insens = n_hazard_insensitive(obs, SEEDS)
    totals = routing_totals(obs, SEEDS)
    out_path = write_report(obs, SEEDS, outcome, n_hzd_insens, totals, anchor_b)

    print()
    print(f"v0.32 single-stream verdict: {outcome.hypothesis} — {outcome.label}")
    print(f"  operational summary:  {outcome.summary}")
    print(f"  n_hazard_insensitive  = {n_hzd_insens}/{len(SEEDS)}")
    print(f"  B(h=0) = {totals[SLOT_BASELINE]['b50']} (descriptive baseline)")
    print()
    print(f"Audit report written to {out_path}")


if __name__ == "__main__":
    main()
