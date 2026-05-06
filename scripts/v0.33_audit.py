"""v0.33 tight h*=8 hazard-axis third-stream calibration audit driver.

Loads three independent 8-seed streams of tight_gradient x influx=1.0 x
hazard ∈ {0, 4, 8, 12} runs, applies the v0.30 4-tier classifier (with
`candidate_label="h=8"`) on the {h=4, h=8, h=12} classifier slice as a
**diagnostic** to each stream individually, and applies the same
classifier with **pre-committed pooled thresholds** (linear scaling of
the 8-seed rule: 5/5/1/5 -> 15/15/3/15) to the 24-seed pool as the
v0.33 headline. h=0 is descriptive baseline only and is NOT in the
classifier.

The pooled verdict is the v0.33 headline. Single-stream verdicts are
diagnostic only — they MUST NOT be read as the experiment's result.

Streams loaded (option (a) — events.jsonl already on disk):
  Stream 1 (v0.25 source) — runs/fear-hunger-v0.25-tight_gradient/arms/, seeds 1..8
  Stream 2 (v0.32 fresh)  — runs/fear-hunger-v0.32-tight_gradient/arms/, seeds 9..16
  Stream 3 (v0.33 fresh)  — runs/fear-hunger-v0.33-tight_gradient/arms/, seeds 17..24

Pooled thresholds: AuditThresholds(15, 15, 3, 15). Mirrors v0.31 verbatim.

Locked H6_pool phrase (do not paraphrase post-hoc; reused verbatim from
v0.31):
    "Directionally persistent, not mechanistically robust."

`n_strict_favoring_pool` and `n_hazard_insensitive_pool` are descriptive
only.

Pre-reg: [[docs/experiments/fear_hunger_v0.33.md]].
Sweep:   [[scripts/v0.33_sweep.py]].

Usage:
    uv run python scripts/v0.33_sweep.py
    uv run python scripts/v0.33_audit.py
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from pathlib import Path

# Import v0.28 + v0.30 modules via importlib (hyphen-named files;
# mirrors the v0.29..v0.32 patterns).
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


# Classifier slot keys are positional placeholders for hazards (NOT literal
# weight values). Mirrors scripts/v0.32_audit.py.
SLOT_BASELINE = 0.00  # -> hazard 0 (descriptive baseline only)
SLOT_LOW = 0.50  # -> hazard 4
SLOT_MED = 0.75  # -> hazard 8 (candidate interior peak)
SLOT_HIGH = 1.00  # -> hazard 12
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


STREAM_CONFIGS: tuple[tuple[str, Path, tuple[int, ...]], ...] = (
    (
        "Stream 1 (v0.25 source)",
        Path("runs/fear-hunger-v0.25-tight_gradient/arms"),
        tuple(range(1, 9)),
    ),
    (
        "Stream 2 (v0.32 fresh)",
        Path("runs/fear-hunger-v0.32-tight_gradient/arms"),
        tuple(range(9, 17)),
    ),
    (
        "Stream 3 (v0.33 fresh)",
        Path("runs/fear-hunger-v0.33-tight_gradient/arms"),
        tuple(range(17, 25)),
    ),
)
OUT_DIR = Path("runs/fear-hunger-v0.33-tight_gradient")
TITLE = "v0.33 tight h*=8 hazard-axis third-stream calibration (pooled 24-seed audit) — report"


# Pre-committed pooled thresholds (linear scaling of the 8-seed rule).
# Identical to v0.31's POOLED_THRESHOLDS by design.
POOLED_THRESHOLDS = v030.AuditThresholds(
    h5_delta_min=15,
    h5_favoring_min=15,
    h6_delta_min=3,
    h8_neighbor_lead_min=15,
)

# Locked headline phrase for pooled H6 — do NOT paraphrase post-hoc.
# Reused verbatim from v0.31.
LOCKED_H6_POOL_PHRASE = "Directionally persistent, not mechanistically robust."

# Classifier candidate label — pinned for the hazard axis.
CANDIDATE_LABEL = "h=8"


# ---------------------------------------------------------------------------
# Stream loading + merge
# ---------------------------------------------------------------------------


def load_stream(runs_root: Path, seeds: Sequence[int]) -> dict[tuple[int, float], object]:
    """Load per-seed observables for one stream via the v0.28 helper.

    The 4-arm hazard-axis ``weight_labels`` override (slot keys 0.0 /
    0.5 / 0.75 / 1.0 -> hazard arms 0 / 4 / 8 / 12 at influx=1.0) is
    shared with the v0.32 audit. v0.25's runs root contains all 12
    arms (4 hazards x 3 influxes); the loader picks only the four
    influx=1.0 labels.
    """
    config = v028.DiagnosticConfig(
        runs_root=runs_root,
        out_dir=OUT_DIR,
        seeds=tuple(seeds),
        weight_labels=dict(SLOT_TO_LABEL),
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
    """24-seed sums per arm of routing-channel observables (all 4 arms)."""
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


def _per_stream_b_table(per_stream_b50: list[dict[float, int]], stream_names: list[str]) -> str:
    rows = [
        "| stream | B(h=0) | B(h=4) | B(h=8) | B(h=12) | Δ_low | Δ_high |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, b in zip(stream_names, per_stream_b50, strict=True):
        d_low = b[SLOT_MED] - b[SLOT_LOW]
        d_high = b[SLOT_MED] - b[SLOT_HIGH]
        rows.append(
            f"| {name} | {b[SLOT_BASELINE]} | {b[SLOT_LOW]} | {b[SLOT_MED]} "
            f"| {b[SLOT_HIGH]} | {d_low:+d} | {d_high:+d} |"
        )
    return "\n".join(rows)


def _per_seed_24_table(obs: dict[tuple[int, float], object], seeds: Sequence[int]) -> str:
    header = (
        "| seed | b50 @ h=0 | b50 @ h=4 | b50 @ h=8 | b50 @ h=12 "
        "| Δ_low(seed) | Δ_high(seed) | favors_h8 | strict | hazard_insensitive |"
    )
    sep = (
        "|-----:|----------:|----------:|----------:|-----------:"
        "|------------:|-------------:|:---------:|:------:|:------------------:|"
    )
    out_rows = [header, sep]
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
        out_rows.append(
            f"| {s} | {b_h0} | {b_h4} | {b_h8} | {b_h12} | "
            f"{d_low:+d} | {d_high:+d} | "
            f"{'yes' if favors else 'no'} | {'yes' if strict else 'no'} | "
            f"{'yes' if flat else 'no'} |"
        )
    aggs = [sum(obs[(s, slot)].b50 for s in seeds) for slot in ALL_SLOTS]  # type: ignore[attr-defined]
    out_rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | **{aggs[3]}** | "
        f"**{aggs[2] - aggs[1]:+d}** | **{aggs[2] - aggs[3]:+d}** | — | — | — |"
    )
    return "\n".join(out_rows)


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
    """Mirror of v028._band_aggregate_table that iterates the 4 v0.33
    arms (slots 0.0 / 0.5 / 0.75 / 1.0 -> hazards 0 / 4 / 8 / 12) and
    labels rows by hazard rather than weight."""
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
    n_hazard_insensitive_pool: int,
    pooled_totals: dict[float, dict[str, int]],
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "audit.md"
    n_seeds = len(pooled_seeds)
    per_stream_b50: list[dict[float, int]] = []
    stream_seed_sets: list[Sequence[int]] = [cfg[2] for cfg in STREAM_CONFIGS]
    for seeds in stream_seed_sets:
        per_stream_b50.append(
            {slot: sum(pooled_obs[(s, slot)].b50 for s in seeds) for slot in ALL_SLOTS}  # type: ignore[attr-defined]
        )

    pooled_h6_extra = ""
    if pooled_outcome.hypothesis == "H6":
        pooled_h6_extra = (
            f"\n**Locked headline phrase (pre-committed in v0.33 pre-reg; "
            f"reused verbatim from v0.31):**\n\n"
            f"> {LOCKED_H6_POOL_PHRASE}\n"
        )

    parts = [
        f"# {TITLE}",
        "",
        "**Source:** three independent 8-seed streams of tight_gradient x "
        "influx=1.0 x hazard ∈ {0, 4, 8, 12}. v0.25 (1..8), v0.32 (9..16), "
        "v0.33 (17..24). h=0 is descriptive baseline only and is NOT in the "
        "classifier; the classifier slice is {h=4, h=8, h=12} mapped to "
        "(0.50, 0.75, 1.00) slot keys.",
        "",
        "**Pooled thresholds (pre-committed):** "
        f"H5 Δ ≥ {POOLED_THRESHOLDS.h5_delta_min} AND n_favoring ≥ "
        f"{POOLED_THRESHOLDS.h5_favoring_min}; "
        f"H6 Δ ≥ {POOLED_THRESHOLDS.h6_delta_min}; "
        f"H8 neighbour lead ≥ {POOLED_THRESHOLDS.h8_neighbor_lead_min}.",
        "",
        "## Pooled 24-seed verdict (v0.33 HEADLINE)",
        "",
        f"**Verdict:** **{pooled_outcome.hypothesis} — {pooled_outcome.label}**",
        "",
        f"**Operational summary:** {pooled_outcome.summary}",
        pooled_h6_extra,
        "## Single-stream diagnostic verdicts",
        "",
        "Single-stream verdicts use the v0.30 default 8-seed thresholds "
        '(5/5/1/5) with `candidate_label="h=8"`. They are **diagnostic '
        "only** — the v0.33 headline is the pooled verdict above.",
        "",
        *(
            _verdict_block(name, outcome)
            for name, outcome in zip(stream_names, stream_outcomes, strict=True)
        ),
        "## Cross-stream aggregate B(h) and per-stream deltas",
        "",
        _per_stream_b_table(per_stream_b50, stream_names),
        "",
        "## Pooled aggregate B(h) and partition deltas",
        "",
        "| hazard | B_pool(h) = Σ b>50 over 24 seeds |",
        "|-------:|---------------------------------:|",
        (
            f"| 0 | {pooled_totals[SLOT_BASELINE]['b50']} | "
            f"*(descriptive baseline; NOT in classifier)*"
        ),
        f"| 4 | {pooled_outcome.b_low} |",
        f"| 8 | **{pooled_outcome.b_med}** |",
        f"| 12 | {pooled_outcome.b_high} |",
        "",
        f"- Δ_low_pool  = B(h=8) - B(h=4)  = **{pooled_outcome.delta_low:+d}**",
        f"- Δ_high_pool = B(h=8) - B(h=12) = **{pooled_outcome.delta_high:+d}**",
        f"- n_favoring_pool (ties allowed) = **{pooled_outcome.n_favoring}/{n_seeds}**",
        (
            f"- n_strict_favoring_pool (strict)  = "
            f"{pooled_outcome.n_strict_favoring}/{n_seeds}  *(descriptive only)*"
        ),
        (
            f"- n_hazard_insensitive_pool       = "
            f"**{n_hazard_insensitive_pool}/{n_seeds}**  "
            f"*(descriptive; pre-committed candidate primary finding if ≥ 18/24)*"
        ),
        "",
        f"## Per-seed b>50 across h ∈ {{0, 4, 8, 12}} (all {n_seeds} seeds)",
        "",
        _per_seed_24_table(pooled_obs, pooled_seeds),
        "",
        "## Pooled routing-channel and productivity totals (all 4 arms; supporting)",
        "",
        _routing_table(pooled_totals),
        "",
        f"## Pooled aggregate band-resolved telemetry ({n_seeds}-seed sums per hazard)",
        "",
        _band_aggregate_table_for_slots(
            pooled_obs, pooled_seeds, "births_per_band", "Births per band"
        ),
        "",
        _band_aggregate_table_for_slots(
            pooled_obs, pooled_seeds, "food_per_band", "Food events per band"
        ),
        "",
        _band_aggregate_table_for_slots(
            pooled_obs, pooled_seeds, "haz_entries_per_band", "Hazard entries per band"
        ),
        "",
        _band_aggregate_table_for_slots(
            pooled_obs, pooled_seeds, "starv_per_band", "Starvation deaths per band"
        ),
        "",
        _band_aggregate_table_for_slots(
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

    # Single-stream diagnostic verdicts (default 8-seed thresholds,
    # candidate_label="h=8" on the {h=4, h=8, h=12} classifier slice).
    stream_outcomes = []
    for (_name, _root, seeds), obs in zip(STREAM_CONFIGS, per_stream_obs, strict=True):
        b50_at = {
            (s, slot): obs[(s, slot)].b50  # type: ignore[attr-defined]
            for s in seeds
            for slot in CLASSIFIER_SLOTS
        }
        stream_outcomes.append(v030.evaluate_audit(b50_at, seeds, candidate_label=CANDIDATE_LABEL))

    # Pooled 24-seed verdict (v0.33 headline).
    pooled_b50_at = {
        (s, slot): pooled_obs[(s, slot)].b50  # type: ignore[attr-defined]
        for s in pooled_seeds
        for slot in CLASSIFIER_SLOTS
    }
    pooled_outcome = v030.evaluate_audit(
        pooled_b50_at,
        pooled_seeds,
        thresholds=POOLED_THRESHOLDS,
        candidate_label=CANDIDATE_LABEL,
    )

    n_hi_pool = n_hazard_insensitive(pooled_obs, pooled_seeds)
    pooled_totals = routing_totals(pooled_obs, pooled_seeds)

    out_path = write_report(
        pooled_obs,
        pooled_seeds,
        stream_outcomes,
        stream_names,
        pooled_outcome,
        n_hi_pool,
        pooled_totals,
    )

    print("v0.33 third-stream calibration audit (hazard axis)")
    print()
    for name, outcome in zip(stream_names, stream_outcomes, strict=True):
        print(f"  {name:<28} -> {outcome.hypothesis} ({outcome.label})")
        print(f"    {outcome.summary}")
    print()
    print(f"  Pooled 24-seed verdict      -> {pooled_outcome.hypothesis} ({pooled_outcome.label})")
    print(f"    {pooled_outcome.summary}")
    print(f"    n_hazard_insensitive_pool = {n_hi_pool}/{len(pooled_seeds)}")
    print(f"    B(h=0) = {pooled_totals[SLOT_BASELINE]['b50']} (descriptive baseline)")
    if pooled_outcome.hypothesis == "H6":
        print()
        print(f"  Locked headline phrase: {LOCKED_H6_POOL_PHRASE}")
    print()
    print(f"Audit report written to {out_path}")


if __name__ == "__main__":
    main()
