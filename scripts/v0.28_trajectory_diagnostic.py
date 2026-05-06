"""v0.28 / v0.29 food_ladder w=0.75 trajectory diagnostic.

Loads per-seed events.jsonl artifacts under a configurable runs root,
computes per-seed observables (via `EventBandTrajectory` +
`PopulationTrajectory`), evaluates the pre-registered H5 / H6 / H7
mechanism signatures (with H8 noise-fallback and the H5+H6
"routing-linked tail crash" tie-break), and writes a markdown report.

Pre-regs:
  - v0.28: [[docs/experiments/fear_hunger_v0.28.md]] (seeds 1..8 on
    v0.27 food_ladder artifacts).
  - v0.29: [[docs/experiments/fear_hunger_v0.29.md]] (seeds 9..16 on
    fresh v0.29 food_ladder artifacts; reuses this module via
    `run_diagnostic(config)`).

Module-level constants are the v0.28 defaults. v0.29 imports
`run_diagnostic` and `DiagnosticConfig`, calling them with
`runs_root` / `seeds` / `out_dir` / `title` / `source_description`
overrides; the v0.28 entrypoint remains a thin caller using the
defaults so its behavior is unchanged after the v0.29 refactor.

Usage (v0.28):
    uv run python scripts/v0.28_trajectory_diagnostic.py
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from hedonism_harness.experiments.population_dynamics import (
    STARVATION_WINDOWS,
    EventBandTrajectory,
    PopulationTrajectory,
    bucket_by_window,
    load_event_band_trajectory,
    load_population_trajectory,
)

# v0.28 defaults — v0.29 callers override via DiagnosticConfig.
DEFAULT_RUNS_ROOT = Path("runs/fear-hunger-v0.27-food_ladder/arms")
DEFAULT_OUT_DIR = Path("runs/fear-hunger-v0.28-food_ladder")
DEFAULT_WEIGHT_LABELS: dict[float, str] = {
    0.50: "hzd8-avd0.50",
    0.75: "hzd8-avd0.75",
    1.00: "hzd8-avd1.00",
}
DEFAULT_SEEDS: tuple[int, ...] = tuple(range(1, 9))
DEFAULT_N_TICKS = 200
DEFAULT_N_FOUNDERS = 5
DEFAULT_TITLE = "v0.28 food_ladder w=0.75 trajectory diagnostic — report"
DEFAULT_SOURCE = (
    "v0.27 events.jsonl artifacts at "
    "`runs/fear-hunger-v0.27-food_ladder/arms/hzd8-avd0.{50,75,1.00}/"
    "seed-{1..8}/events.jsonl` (24 runs)."
)
LATE_BAND = "150-199"

# Pre-reg operational thresholds (verbatim from v0.28 H5 / H6 / H7).
H5_FLIPPED_DELTA = -5
H5_UNFLIPPED_DELTA = -1
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
# Diagnostic configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosticConfig:
    """Configuration for one run of the diagnostic.

    The v0.28 entrypoint constructs this with the default v0.27 paths
    and seeds; v0.29 (and any future caller) overrides ``runs_root`` /
    ``out_dir`` / ``seeds`` / ``title`` / ``source_description``.

    Operational thresholds (H5 / H6 / H7) and the analysis weights
    {0.5, 0.75, 1.0} are deliberately fixed at module scope and not
    parameterised: the diagnostic's scientific contract is to apply
    the **same** classifier to different seed streams.
    """

    runs_root: Path = DEFAULT_RUNS_ROOT
    out_dir: Path = DEFAULT_OUT_DIR
    weight_labels: dict[float, str] = field(default_factory=lambda: dict(DEFAULT_WEIGHT_LABELS))
    seeds: tuple[int, ...] = DEFAULT_SEEDS
    n_ticks: int = DEFAULT_N_TICKS
    n_founders: int = DEFAULT_N_FOUNDERS
    title: str = DEFAULT_TITLE
    source_description: str = DEFAULT_SOURCE

    @property
    def weights(self) -> tuple[float, ...]:
        return tuple(self.weight_labels)


# ---------------------------------------------------------------------------
# Per-seed observables
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SeedObservables:
    """Per-seed observables for one (seed, weight) cell."""

    seed: int
    weight: float
    b50: int
    total_births: int
    tick_of_peak: int
    peak_population: int
    mean_pop_late: float  # mean_population_window(100, n_ticks - 1)
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


def _events_path(config: DiagnosticConfig, seed: int, weight: float) -> Path:
    return config.runs_root / config.weight_labels[weight] / f"seed-{seed}" / "events.jsonl"


def assert_artifacts_present(config: DiagnosticConfig) -> None:
    """Pre-flight check: every expected (seed, weight) events.jsonl
    file exists and is non-empty. Cheap protection against path /
    labeling errors. v0.29 H8b in the pre-reg.
    """
    missing: list[str] = []
    empty: list[str] = []
    for s in config.seeds:
        for w in config.weights:
            path = _events_path(config, s, w)
            if not path.is_file():
                missing.append(str(path))
            elif path.stat().st_size == 0:
                empty.append(str(path))
    if missing or empty:
        msg_parts = []
        if missing:
            msg_parts.append(f"missing files: {missing}")
        if empty:
            msg_parts.append(f"empty files: {empty}")
        raise FileNotFoundError("; ".join(msg_parts))


def _load_seed_observables(config: DiagnosticConfig, seed: int, weight: float) -> SeedObservables:
    events_path = _events_path(config, seed, weight)
    band: EventBandTrajectory = load_event_band_trajectory(events_path, n_ticks=config.n_ticks)
    traj: PopulationTrajectory = load_population_trajectory(
        events_path, n_founders=config.n_founders, n_ticks=config.n_ticks
    )
    return SeedObservables(
        seed=seed,
        weight=weight,
        b50=band.births_after_tick(50),
        total_births=band.total_births,
        tick_of_peak=traj.tick_of_peak,
        peak_population=traj.peak_population,
        mean_pop_late=traj.mean_population_window(100, config.n_ticks - 1),
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


def load_all(config: DiagnosticConfig) -> dict[tuple[int, float], SeedObservables]:
    return {
        (s, w): _load_seed_observables(config, s, w) for s in config.seeds for w in config.weights
    }


# ---------------------------------------------------------------------------
# Hypothesis evaluators (parametrised on the seeds tuple)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HypothesisResult:
    name: str
    fired: bool
    detail: str


def _per_seed_b50_delta(
    obs: dict[tuple[int, float], SeedObservables],
    seeds: Sequence[int],
    a: float,
    b: float,
) -> dict[int, int]:
    """delta[seed] = b50_at_b - b50_at_a."""
    return {s: obs[(s, b)].b50 - obs[(s, a)].b50 for s in seeds}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _frac_shift(a: float, b: float) -> float:
    """|b - a| / max(|a|, |b|) — symmetric relative shift."""
    denom = max(abs(a), abs(b))
    return abs(b - a) / denom if denom > 0 else 0.0


def evaluate_h5(
    obs: dict[tuple[int, float], SeedObservables], seeds: Sequence[int]
) -> HypothesisResult:
    """Routing-threshold flip: per-seed bimodality at w=0.75 vs w=0.5
    plus a band-resolved routing-side shift in the flipped subgroup."""
    delta = _per_seed_b50_delta(obs, seeds, 0.50, 0.75)
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

    def _mean_band_at(group: list[int], field_name: str, band: str) -> float:
        return _mean([float(getattr(obs[(s, 0.75)], field_name)[band]) for s in group])

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


def evaluate_h6(
    obs: dict[tuple[int, float], SeedObservables], seeds: Sequence[int]
) -> HypothesisResult:
    """Tail-seed crash: <= 2 seeds carry >= 80% of the aggregate
    b>50 deficit at w=0.75 vs w=0.5; those seeds show a crash signature
    and do not crash at w=0.5 / w=1.0."""
    delta = _per_seed_b50_delta(obs, seeds, 0.50, 0.75)
    deficit_total = sum(d for d in delta.values() if d < 0)
    if deficit_total >= 0:
        return HypothesisResult(
            name="H6",
            fired=False,
            detail=(
                f"no aggregate deficit at w=0.75 vs w=0.5 (total negative delta = {deficit_total})"
            ),
        )

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

    def _median_b50(weight: float) -> float:
        vals = sorted(obs[(s, weight)].b50 for s in seeds)
        mid = len(vals) // 2
        return float(vals[mid])

    same_seed_safe_at_neighbors = True
    safety_notes: list[str] = []
    for s in tail_seeds:
        for w in (0.50, 1.00):
            seed_b50 = obs[(s, w)].b50
            median = _median_b50(w)
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


def evaluate_h7(
    obs: dict[tuple[int, float], SeedObservables], seeds: Sequence[int]
) -> HypothesisResult:
    """Uniform population-wide degradation: most seeds dip with tight
    clustering and a uniform per-band shift."""
    delta = _per_seed_b50_delta(obs, seeds, 0.50, 0.75)
    n_seeds = len(seeds)
    negatives = [d for d in delta.values() if d < 0]
    if len(negatives) < H7_NEGATIVE_DELTA_MIN:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=(
                f"only {len(negatives)} of {n_seeds} seeds have delta < 0 "
                f"(need >= {H7_NEGATIVE_DELTA_MIN}); deltas={delta}"
            ),
        )

    spread = max(delta.values()) - min(delta.values())
    if spread >= H7_DELTA_SPREAD_MAX:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=f"delta spread = {spread} (need < {H7_DELTA_SPREAD_MAX}); deltas={delta}",
        )

    agreement = sum(
        1
        for s in seeds
        if obs[(s, 0.75)].food_per_band[LATE_BAND] < obs[(s, 0.50)].food_per_band[LATE_BAND]
    )
    if agreement < H7_BAND_AGREEMENT_MIN:
        return HypothesisResult(
            name="H7",
            fired=False,
            detail=(
                f"food_per_band[{LATE_BAND}] lower at w=0.75 than w=0.5 for only "
                f"{agreement} of {n_seeds} seeds (need >= {H7_BAND_AGREEMENT_MIN})"
            ),
        )

    return HypothesisResult(
        name="H7",
        fired=True,
        detail=(
            f"{len(negatives)}/{n_seeds} seeds delta < 0; spread={spread}; "
            f"food_per_band[{LATE_BAND}] agreement={agreement}/{n_seeds}"
        ),
    )


def classify(h5: HypothesisResult, h6: HypothesisResult, h7: HypothesisResult) -> str:
    """Apply the v0.28 pre-reg tie-break rules. Returns the
    classification label."""
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


def _per_seed_b50_table(obs: dict[tuple[int, float], SeedObservables], seeds: Sequence[int]) -> str:
    header = (
        "| seed | b50 @ w=0.50 | b50 @ w=0.75 | b50 @ w=1.00 "
        "| delta(0.75-0.50) | delta(0.75-1.00) |"
    )
    sep = (
        "|-----:|-------------:|-------------:|-------------:"
        "|-----------------:|-----------------:|"
    )
    rows = [header, sep]
    for s in seeds:
        b50_50 = obs[(s, 0.50)].b50
        b50_75 = obs[(s, 0.75)].b50
        b50_100 = obs[(s, 1.00)].b50
        rows.append(
            f"| {s} | {b50_50} | {b50_75} | {b50_100} | "
            f"{b50_75 - b50_50:+d} | {b50_75 - b50_100:+d} |"
        )
    aggs = [sum(obs[(s, w)].b50 for s in seeds) for w in (0.50, 0.75, 1.00)]
    rows.append(
        f"| **sum** | **{aggs[0]}** | **{aggs[1]}** | **{aggs[2]}** | "
        f"**{aggs[1] - aggs[0]:+d}** | **{aggs[1] - aggs[2]:+d}** |"
    )
    return "\n".join(rows)


def _per_seed_late_pop_table(
    obs: dict[tuple[int, float], SeedObservables], seeds: Sequence[int]
) -> str:
    header = (
        "| seed | mean_pop_late @ 0.50 | @ 0.75 | @ 1.00 "
        "| first PoolBirthDenied @ 0.50 / 0.75 / 1.00 |"
    )
    sep = (
        "|-----:|---------------------:|-------:|-------:"
        "|---------------------------------------------|"
    )
    rows = [header, sep]
    for s in seeds:
        m50 = obs[(s, 0.50)].mean_pop_late
        m75 = obs[(s, 0.75)].mean_pop_late
        m100 = obs[(s, 1.00)].mean_pop_late
        p50 = obs[(s, 0.50)].first_pool_birth_denied_tick
        p75 = obs[(s, 0.75)].first_pool_birth_denied_tick
        p100 = obs[(s, 1.00)].first_pool_birth_denied_tick
        rows.append(f"| {s} | {m50:.1f} | {m75:.1f} | {m100:.1f} | {p50} / {p75} / {p100} |")
    return "\n".join(rows)


def _band_aggregate_table(
    obs: dict[tuple[int, float], SeedObservables],
    seeds: Sequence[int],
    field_name: str,
    title: str,
) -> str:
    rows = [f"#### {title}", "", "| weight | 0-49 | 50-99 | 100-149 | 150-199 |"]
    rows.append("|-------:|-----:|------:|--------:|--------:|")
    for w in (0.50, 0.75, 1.00):
        bands = {label: 0 for label, _, _ in STARVATION_WINDOWS}
        for s in seeds:
            for label in bands:
                bands[label] += getattr(obs[(s, w)], field_name)[label]
        rows.append(
            f"| {w:.2f} | {bands['0-49']} | {bands['50-99']} | "
            f"{bands['100-149']} | {bands['150-199']} |"
        )
    return "\n".join(rows)


def write_report(
    config: DiagnosticConfig,
    obs: dict[tuple[int, float], SeedObservables],
    results: list[HypothesisResult],
    classification: str,
) -> Path:
    config.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = config.out_dir / "diagnostic.md"
    n_seeds = len(config.seeds)
    parts = [
        f"# {config.title}",
        "",
        f"**Source:** {config.source_description}",
        "",
        f"**Classification:** {classification}",
        "",
        "## Per-seed b>50 across w ∈ {0.5, 0.75, 1.0}",
        "",
        _per_seed_b50_table(obs, config.seeds),
        "",
        "## Per-seed late-window population + first PoolBirthDenied tick",
        "",
        _per_seed_late_pop_table(obs, config.seeds),
        "",
        f"## Aggregate band-resolved telemetry ({n_seeds}-seed sums)",
        "",
        _band_aggregate_table(obs, config.seeds, "births_per_band", "Births per band"),
        "",
        _band_aggregate_table(obs, config.seeds, "food_per_band", "Food events per band"),
        "",
        _band_aggregate_table(obs, config.seeds, "haz_entries_per_band", "Hazard entries per band"),
        "",
        _band_aggregate_table(obs, config.seeds, "starv_per_band", "Starvation deaths per band"),
        "",
        _band_aggregate_table(obs, config.seeds, "inj_per_band", "Injury deaths per band"),
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
# Orchestrator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosticOutcome:
    classification: str
    h5: HypothesisResult
    h6: HypothesisResult
    h7: HypothesisResult
    out_path: Path


def run_diagnostic(config: DiagnosticConfig) -> DiagnosticOutcome:
    """End-to-end diagnostic: pre-flight artifact check, load,
    evaluate H5/H6/H7, classify, write report. Returns the
    classification + per-hypothesis results + report path."""
    assert_artifacts_present(config)
    obs = load_all(config)
    h5 = evaluate_h5(obs, config.seeds)
    h6 = evaluate_h6(obs, config.seeds)
    h7 = evaluate_h7(obs, config.seeds)
    classification = classify(h5, h6, h7)
    out_path = write_report(config, obs, [h5, h6, h7], classification)
    return DiagnosticOutcome(classification=classification, h5=h5, h6=h6, h7=h7, out_path=out_path)


# ---------------------------------------------------------------------------
# v0.28 entrypoint (thin caller using defaults)
# ---------------------------------------------------------------------------


def main() -> None:
    outcome = run_diagnostic(DiagnosticConfig())
    print(f"Diagnostic report written to {outcome.out_path}")
    print(f"Classification: {outcome.classification}")
    for r in (outcome.h5, outcome.h6, outcome.h7):
        marker = "FIRES" if r.fired else "does not fire"
        print(f"  {r.name} {marker}: {r.detail}")


if __name__ == "__main__":
    main()
