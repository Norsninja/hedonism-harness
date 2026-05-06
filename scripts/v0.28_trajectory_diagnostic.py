"""v0.28 food_ladder w=0.75 trajectory diagnostic driver.

Loads the 24 on-disk v0.27 events.jsonl artifacts
(``runs/fear-hunger-v0.27-food_ladder/arms/hzd8-avd0.{50,75,1.00}/seed-{1..8}``),
computes per-seed observables, evaluates the pre-registered H5 / H6 / H7
mechanism signatures (with H8 noise-fallback and the H5+H6
"routing-linked tail crash" tie-break), and writes a diagnostic.md
report under ``runs/fear-hunger-v0.28-food_ladder/``.

Pre-reg: [[docs/experiments/fear_hunger_v0.28.md]].

No new sweep is performed. Existing v0.27 artifacts are the input.

Usage:
    uv run python scripts/v0.28_trajectory_diagnostic.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hedonism_harness.experiments.population_dynamics import (
    STARVATION_WINDOWS,
    EventBandTrajectory,
    PopulationTrajectory,
    bucket_by_window,
    load_event_band_trajectory,
    load_population_trajectory,
)

RUNS_ROOT = Path("runs/fear-hunger-v0.27-food_ladder/arms")
OUT_DIR = Path("runs/fear-hunger-v0.28-food_ladder")
WEIGHT_LABELS: dict[float, str] = {
    0.50: "hzd8-avd0.50",
    0.75: "hzd8-avd0.75",
    1.00: "hzd8-avd1.00",
}
WEIGHTS: tuple[float, ...] = tuple(WEIGHT_LABELS)
SEEDS: tuple[int, ...] = tuple(range(1, 9))
N_TICKS = 200
N_FOUNDERS = 5
LATE_BAND = "150-199"

# Pre-reg operational thresholds (verbatim from H5 / H6 / H7).
H5_FLIPPED_DELTA = -5  # flipped seed: b50_at_0.75 - b50_at_0.5 <= -5
H5_UNFLIPPED_DELTA = -1  # unflipped seed: delta >= -1
H5_FLIPPED_MIN = 2
H5_UNFLIPPED_MIN = 4
H5_BAND_SHIFT_FRAC = 0.30
H5_LATE_BIRTH_COLLAPSE_FRAC = 0.50

H6_TAIL_DEFICIT_FRAC = 0.80
H6_TAIL_MAX_SEEDS = 2
H6_LATE_POP_DROP_FRAC = 0.30
H6_POOL_DENIAL_EARLIER_TICKS = 30

H7_NEGATIVE_DELTA_MIN = 6
H7_DELTA_SPREAD_MAX = 4
H7_BAND_AGREEMENT_MIN = 6


# ---------------------------------------------------------------------------
# Per-seed observables
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedObservables:
    """Per-seed observables for one (seed, weight) cell.

    All quantities are derived from the events.jsonl on disk via
    ``load_event_band_trajectory`` + ``load_population_trajectory``.
    """

    seed: int
    weight: float
    b50: int
    total_births: int
    tick_of_peak: int
    peak_population: int
    mean_pop_late: float  # mean_population_window(100, 199)
    first_pool_birth_denied_tick: int | None
    total_pool_birth_denied: int
    total_food_events: int
    total_hazard_entries: int
    total_starvation_deaths: int
    total_injury_deaths: int
    births_per_band: dict[str, int]
    food_per_band: dict[str, int]
    haz_entries_per_band: dict[str, int]
    starv_per_band: dict[str, int]
    inj_per_band: dict[str, int]
    pool_birth_denied_per_band: dict[str, int]


def _load_seed_observables(seed: int, weight: float) -> SeedObservables:
    label = WEIGHT_LABELS[weight]
    events_path = RUNS_ROOT / label / f"seed-{seed}" / "events.jsonl"
    band: EventBandTrajectory = load_event_band_trajectory(events_path, n_ticks=N_TICKS)
    traj: PopulationTrajectory = load_population_trajectory(
        events_path, n_founders=N_FOUNDERS, n_ticks=N_TICKS
    )
    return SeedObservables(
        seed=seed,
        weight=weight,
        b50=band.births_after_tick(50),
        total_births=band.total_births,
        tick_of_peak=traj.tick_of_peak,
        peak_population=traj.peak_population,
        mean_pop_late=traj.mean_population_window(100, N_TICKS - 1),
        first_pool_birth_denied_tick=band.first_pool_birth_denied_tick(),
        total_pool_birth_denied=band.total_pool_birth_denied,
        total_food_events=band.total_food_events,
        total_hazard_entries=band.total_hazard_entries,
        total_starvation_deaths=sum(traj.starvation_deaths_per_tick),
        total_injury_deaths=sum(traj.injury_deaths_per_tick),
        births_per_band=bucket_by_window(band.births_per_tick),
        food_per_band=bucket_by_window(band.food_events_per_tick),
        haz_entries_per_band=bucket_by_window(band.hazard_entries_per_tick),
        starv_per_band=bucket_by_window(traj.starvation_deaths_per_tick),
        inj_per_band=bucket_by_window(traj.injury_deaths_per_tick),
        pool_birth_denied_per_band=bucket_by_window(band.pool_birth_denied_per_tick),
    )


def load_all() -> dict[tuple[int, float], SeedObservables]:
    return {(s, w): _load_seed_observables(s, w) for s in SEEDS for w in WEIGHTS}


# ---------------------------------------------------------------------------
# Hypothesis evaluators
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HypothesisResult:
    name: str
    fired: bool
    detail: str


def _per_seed_b50_delta(
    obs: dict[tuple[int, float], SeedObservables], a: float, b: float
) -> dict[int, int]:
    """delta[seed] = b50_at_b - b50_at_a."""
    return {s: obs[(s, b)].b50 - obs[(s, a)].b50 for s in SEEDS}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _frac_shift(a: float, b: float) -> float:
    """|b - a| / max(a, b) — symmetric relative shift, undefined -> 0."""
    denom = max(abs(a), abs(b))
    return abs(b - a) / denom if denom > 0 else 0.0


def evaluate_h5(obs: dict[tuple[int, float], SeedObservables]) -> HypothesisResult:
    """Routing-threshold flip: per-seed bimodality at w=0.75 vs w=0.5
    plus a band-resolved routing-side shift in the flipped subgroup."""
    delta = _per_seed_b50_delta(obs, 0.50, 0.75)
    flipped = [s for s, d in delta.items() if d <= H5_FLIPPED_DELTA]
    unflipped = [s for s, d in delta.items() if d >= H5_UNFLIPPED_DELTA]
    bimodality_ok = len(flipped) >= H5_FLIPPED_MIN and len(unflipped) >= H5_UNFLIPPED_MIN
    if not bimodality_ok:
        return HypothesisResult(
            name="H5",
            fired=False,
            detail=(
                f"bimodality fails: flipped={len(flipped)} (need >= {H5_FLIPPED_MIN}), "
                f"unflipped={len(unflipped)} (need >= {H5_UNFLIPPED_MIN}); "
                f"deltas={delta}"
            ),
        )

    # Band-shift checks at w=0.75: flipped vs unflipped subgroup means.
    def _mean_band_at(seeds: list[int], field_name: str, band: str) -> float:
        return _mean([float(getattr(obs[(s, 0.75)], field_name)[band]) for s in seeds])

    band_signatures: list[str] = []
    for field_name in ("haz_entries_per_band", "food_per_band"):
        for band, _, _ in STARVATION_WINDOWS:
            f_mean = _mean_band_at(flipped, field_name, band)
            u_mean = _mean_band_at(unflipped, field_name, band)
            if _frac_shift(f_mean, u_mean) >= H5_BAND_SHIFT_FRAC:
                band_signatures.append(
                    f"{field_name}[{band}]: flipped_mean={f_mean:.1f} "
                    f"unflipped_mean={u_mean:.1f} (>= {H5_BAND_SHIFT_FRAC:.0%})"
                )

    f_late_births = _mean_band_at(flipped, "births_per_band", LATE_BAND)
    u_late_births = _mean_band_at(unflipped, "births_per_band", LATE_BAND)
    late_collapse_frac = (
        (u_late_births - f_late_births) / u_late_births if u_late_births > 0 else 0.0
    )
    late_collapse = late_collapse_frac >= H5_LATE_BIRTH_COLLAPSE_FRAC
    if late_collapse:
        band_signatures.append(
            f"births_per_band[{LATE_BAND}] collapsed in flipped: "
            f"flipped_mean={f_late_births:.1f} unflipped_mean={u_late_births:.1f}"
        )

    fired = bool(band_signatures)
    detail_parts = [
        f"flipped seeds (delta <= {H5_FLIPPED_DELTA}): {sorted(flipped)}",
        f"unflipped seeds (delta >= {H5_UNFLIPPED_DELTA}): {sorted(unflipped)}",
        f"band-shift signatures: {band_signatures or 'none'}",
    ]
    return HypothesisResult(name="H5", fired=fired, detail=" | ".join(detail_parts))


def evaluate_h6(obs: dict[tuple[int, float], SeedObservables]) -> HypothesisResult:
    """Tail-seed crash: a small number of seeds (<= 2) account for
    >= 80% of the aggregate b>50 deficit at w=0.75 vs w=0.5, and
    those same seeds do not crash at w=0.5 / w=1.0."""
    delta = _per_seed_b50_delta(obs, 0.50, 0.75)
    deficit_total = sum(d for d in delta.values() if d < 0)
    if deficit_total >= 0:
        return HypothesisResult(
            name="H6",
            fired=False,
            detail=(
                f"no aggregate deficit at w=0.75 vs w=0.5 (total negative delta = {deficit_total})"
            ),
        )

    # Top H6_TAIL_MAX_SEEDS most-negative seeds.
    ranked = sorted(delta.items(), key=lambda kv: kv[1])
    tail = ranked[:H6_TAIL_MAX_SEEDS]
    tail_deficit = sum(d for _, d in tail if d < 0)
    tail_share = tail_deficit / deficit_total if deficit_total != 0 else 0.0

    if tail_share < H6_TAIL_DEFICIT_FRAC:
        return HypothesisResult(
            name="H6",
            fired=False,
            detail=(
                f"top-{H6_TAIL_MAX_SEEDS} tail share = {tail_share:.0%} "
                f"(need >= {H6_TAIL_DEFICIT_FRAC:.0%}); ranked deltas={ranked}"
            ),
        )

    tail_seeds = [s for s, _ in tail if delta[s] < 0]

    crash_signatures: list[str] = []
    for s in tail_seeds:
        late_at_0_75 = obs[(s, 0.75)].mean_pop_late
        late_at_0_50 = obs[(s, 0.50)].mean_pop_late
        late_drop = (late_at_0_50 - late_at_0_75) / late_at_0_50 if late_at_0_50 > 0 else 0.0
        pool_at_0_75 = obs[(s, 0.75)].first_pool_birth_denied_tick
        pool_at_0_50 = obs[(s, 0.50)].first_pool_birth_denied_tick
        pool_earlier = pool_at_0_75 is not None and (
            pool_at_0_50 is None or pool_at_0_50 - pool_at_0_75 >= H6_POOL_DENIAL_EARLIER_TICKS
        )
        if late_drop >= H6_LATE_POP_DROP_FRAC:
            crash_signatures.append(
                f"seed {s}: mean_pop_late {late_at_0_50:.1f} -> "
                f"{late_at_0_75:.1f} ({late_drop:.0%} drop)"
            )
        if pool_earlier:
            crash_signatures.append(
                f"seed {s}: first PoolBirthDenied tick {pool_at_0_50} -> {pool_at_0_75} "
                f"(>= {H6_POOL_DENIAL_EARLIER_TICKS} ticks earlier)"
            )

    # Verify the same seeds do NOT show comparable collapses at w=0.5 / w=1.0
    # (relative to the median seed at those weights).
    def _median_b50(weight: float) -> float:
        vals = sorted(obs[(s, weight)].b50 for s in SEEDS)
        mid = len(vals) // 2
        return float(vals[mid])

    same_seed_safe_at_neighbors = True
    safety_notes: list[str] = []
    for s in tail_seeds:
        for w in (0.50, 1.00):
            seed_b50 = obs[(s, w)].b50
            median = _median_b50(w)
            # Ad-hoc threshold: the tail seed at neighbor weights should be
            # within 5 of median (i.e., not crashing there too).
            if median - seed_b50 >= 5:
                same_seed_safe_at_neighbors = False
                safety_notes.append(f"seed {s} at w={w}: b50={seed_b50} vs median={median:.1f}")

    fired = bool(crash_signatures) and same_seed_safe_at_neighbors
    detail = (
        f"tail seeds (top {H6_TAIL_MAX_SEEDS} negative): {tail_seeds}; "
        f"tail share of deficit = {tail_share:.0%}; "
        f"crash signatures: {crash_signatures or 'none'}; "
        f"safe-at-neighbors: {same_seed_safe_at_neighbors} "
        f"({safety_notes or 'all good'})"
    )
    return HypothesisResult(name="H6", fired=fired, detail=detail)


def evaluate_h7(obs: dict[tuple[int, float], SeedObservables]) -> HypothesisResult:
    """Uniform population-wide degradation: most seeds dip with tight
    clustering and a uniform per-band shift."""
    delta = _per_seed_b50_delta(obs, 0.50, 0.75)
    negatives = [d for d in delta.values() if d < 0]
    if len(negatives) < H7_NEGATIVE_DELTA_MIN:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=(
                f"only {len(negatives)} of {len(SEEDS)} seeds have delta < 0 "
                f"(need >= {H7_NEGATIVE_DELTA_MIN}); deltas={delta}"
            ),
        )

    spread = max(delta.values()) - min(delta.values())
    if spread >= H7_DELTA_SPREAD_MAX:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=(f"delta spread = {spread} (need < {H7_DELTA_SPREAD_MAX}); deltas={delta}"),
        )

    # Uniform band shift: food_per_band[late] lower at w=0.75 than at w=0.5
    # for >= H7_BAND_AGREEMENT_MIN of 8 seeds.
    agreement = sum(
        1
        for s in SEEDS
        if obs[(s, 0.75)].food_per_band[LATE_BAND] < obs[(s, 0.50)].food_per_band[LATE_BAND]
    )
    if agreement < H7_BAND_AGREEMENT_MIN:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=(
                f"food_per_band[{LATE_BAND}] lower at w=0.75 than w=0.5 for only "
                f"{agreement} of 8 seeds (need >= {H7_BAND_AGREEMENT_MIN})"
            ),
        )

    return HypothesisResult(
        name="H7",
        fired=True,
        detail=(
            f"{len(negatives)}/8 seeds delta < 0; spread={spread}; "
            f"food_per_band[{LATE_BAND}] agreement={agreement}/8"
        ),
    )


def classify(h5: HypothesisResult, h6: HypothesisResult, h7: HypothesisResult) -> str:
    """Apply the pre-reg tie-break rules. Returns the classification label."""
    fired = {h.name for h in (h5, h6, h7) if h.fired}
    if fired in ({"H5", "H7"}, {"H6", "H7"}, {"H5", "H6", "H7"}):
        return "HALT (operationally contradictory pair fired; re-evaluate definitions)"
    if fired == {"H5", "H6"}:
        return "ROUTING-LINKED TAIL CRASH (H5 routing flip + H6 tail-seed consequence)"
    if fired == {"H5"}:
        return "ROUTING-THRESHOLD FLIP (H5)"
    if fired == {"H6"}:
        return "TAIL-SEED CRASH (H6)"
    if fired == {"H7"}:
        return "UNIFORM POPULATION-WIDE DEGRADATION (H7)"
    return "STATISTICAL NOISE (H8 fallback) — v0.29 candidate: seeds 9..16 reproducibility test"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _per_seed_b50_table(obs: dict[tuple[int, float], SeedObservables]) -> str:
    header = (
        "| seed | b50 @ w=0.50 | b50 @ w=0.75 | b50 @ w=1.00 "
        "| delta(0.75-0.50) | delta(0.75-1.00) |"
    )
    sep = (
        "|-----:|-------------:|-------------:|-------------:"
        "|-----------------:|-----------------:|"
    )
    rows = [header, sep]
    for s in SEEDS:
        b50_50 = obs[(s, 0.50)].b50
        b50_75 = obs[(s, 0.75)].b50
        b50_100 = obs[(s, 1.00)].b50
        rows.append(
            f"| {s} | {b50_50} | {b50_75} | {b50_100} | "
            f"{b50_75 - b50_50:+d} | {b50_75 - b50_100:+d} |"
        )
    aggs = [sum(obs[(s, w)].b50 for s in SEEDS) for w in WEIGHTS]
    rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | "
        f"**{aggs[1] - aggs[0]:+d}** | **{aggs[1] - aggs[2]:+d}** |"
    )
    return "\n".join(rows)


def _per_seed_late_pop_table(obs: dict[tuple[int, float], SeedObservables]) -> str:
    header = (
        "| seed | mean_pop_late @ 0.50 | @ 0.75 | @ 1.00 "
        "| first PoolBirthDenied @ 0.50 / 0.75 / 1.00 |"
    )
    sep = (
        "|-----:|---------------------:|-------:|-------:"
        "|---------------------------------------------|"
    )
    rows = [header, sep]
    for s in SEEDS:
        m50 = obs[(s, 0.50)].mean_pop_late
        m75 = obs[(s, 0.75)].mean_pop_late
        m100 = obs[(s, 1.00)].mean_pop_late
        p50 = obs[(s, 0.50)].first_pool_birth_denied_tick
        p75 = obs[(s, 0.75)].first_pool_birth_denied_tick
        p100 = obs[(s, 1.00)].first_pool_birth_denied_tick
        rows.append(f"| {s} | {m50:.1f} | {m75:.1f} | {m100:.1f} | {p50} / {p75} / {p100} |")
    return "\n".join(rows)


def _band_aggregate_table(
    obs: dict[tuple[int, float], SeedObservables], field_name: str, title: str
) -> str:
    rows = [f"#### {title}", "", "| weight | 0-49 | 50-99 | 100-149 | 150-199 |"]
    rows.append("|-------:|-----:|------:|--------:|--------:|")
    for w in WEIGHTS:
        bands = {label: 0 for label, _, _ in STARVATION_WINDOWS}
        for s in SEEDS:
            for label in bands:
                bands[label] += getattr(obs[(s, w)], field_name)[label]
        rows.append(
            f"| {w:.2f} | {bands['0-49']} | {bands['50-99']} | "
            f"{bands['100-149']} | {bands['150-199']} |"
        )
    return "\n".join(rows)


def write_report(
    obs: dict[tuple[int, float], SeedObservables],
    results: list[HypothesisResult],
    classification: str,
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "diagnostic.md"
    parts = [
        "# v0.28 food_ladder w=0.75 trajectory diagnostic — report",
        "",
        "**Source:** v0.27 events.jsonl artifacts at "
        "`runs/fear-hunger-v0.27-food_ladder/arms/hzd8-avd0.{50,75,1.00}/"
        "seed-{1..8}/events.jsonl` (24 runs).",
        "",
        f"**Classification:** {classification}",
        "",
        "## Per-seed b>50 across w ∈ {0.5, 0.75, 1.0}",
        "",
        _per_seed_b50_table(obs),
        "",
        "## Per-seed late-window population + first PoolBirthDenied tick",
        "",
        _per_seed_late_pop_table(obs),
        "",
        "## Aggregate band-resolved telemetry (8-seed sums)",
        "",
        _band_aggregate_table(obs, "births_per_band", "Births per band"),
        "",
        _band_aggregate_table(obs, "food_per_band", "Food events per band"),
        "",
        _band_aggregate_table(obs, "haz_entries_per_band", "Hazard entries per band"),
        "",
        _band_aggregate_table(obs, "starv_per_band", "Starvation deaths per band"),
        "",
        _band_aggregate_table(obs, "inj_per_band", "Injury deaths per band"),
        "",
        "## Hypothesis adjudication",
        "",
        "| H | fired | detail |",
        "|---|:-----:|--------|",
    ]
    for r in results:
        parts.append(f"| {r.name} | {'YES' if r.fired else 'no'} | {r.detail} |")
    parts.extend(["", f"**Final classification:** {classification}", ""])
    out_path.write_text("\n".join(parts))
    return out_path


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> None:
    obs = load_all()
    h5 = evaluate_h5(obs)
    h6 = evaluate_h6(obs)
    h7 = evaluate_h7(obs)
    classification = classify(h5, h6, h7)
    out_path = write_report(obs, [h5, h6, h7], classification)
    print(f"Diagnostic report written to {out_path}")
    print(f"Classification: {classification}")
    for r in (h5, h6, h7):
        marker = "FIRES" if r.fired else "does not fire"
        print(f"  {r.name} {marker}: {r.detail}")


if __name__ == "__main__":
    main()
