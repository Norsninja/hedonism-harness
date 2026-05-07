"""v0.45 intervention audit: post-intervention top-lineage b50 share under
continuous post-50 birth redirection.

Tests the v0.45 birth-locality-necessity question on the 48-run intervention
corpus (3 arms x 2 hazards x 8 seeds):

  Primary:   B_uniform_valid_region at h=8 reduces post_intervention_
             top_lineage_b50_share by >= 0.15 below A_null AND
             C_uniform_neighbor stays within +/- 0.10 of A_null at h=8.
  Secondary: B-vs-A reduction is larger at h=8 than at h=0 (descriptive
             only).

Verdict (locked, mutually exclusive on b_passes / c-direction; 3-way + 2 halt):
  BIRTH_LOCALITY_NECESSARY                  iff b_passes AND c_passes.
  LOCAL_CONTROL_DISRUPTS_DOMINANCE          iff b_passes AND c_below_a.
  BIRTH_LOCALITY_NOT_NECESSARY              iff NOT b_passes AND NOT c_below_a.
  C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT    iff b_passes AND c_above_a (halt).
  C_DISRUPTS_WITHOUT_B                      iff NOT b_passes AND c_below_a (halt).

Auxiliary (per-hazard, non-exclusive):
  GLOBAL_REDIRECT_ABLATES_REPRODUCTION fires at hazard h iff
  B_uniform_valid_region's n_excluded_zero_post50 > 2 (out of 8).

Reads (per-arm-per-seed):
  - runs/fear-hunger-v0.45-tight_gradient/arms/<arm>/seed-<n>/events.jsonl
    for AgentBorn (post-50 births) and BirthRedirectedByIntervention
    (placement conservation H2d).

Halt invariants (locked):
  - H2a (run count): 48 runs on disk.
  - H2b (intervention-fire pattern):
      * A_null: 0 BirthRedirectedByIntervention events.
      * B / C: >= 1 event per run unless excluded_zero_post50 (no
        post-50 births of any kind) or excluded_redirect_empty
        (attempts existed but every attempt found empty eligible
        set). The two exclusion buckets are tracked separately.
  - H2c (tick monotonicity): every fired event has tick > 50.
  - H2d (placement conservation):
      * target_cell_kind in {"EMPTY", "FOOD", "SAFE"}.
      * (redirected_x, redirected_y) != (parent_x, parent_y).
      * For C only: |parent_x - redirected_x| + |parent_y -
        redirected_y| == 1 (strict adjacency).
      * For both: n_valid_cells >= 1.
      * For both: rng_stream_label == "v0_45_birth_position_intervention".
      * For both: preserved_parent_adjacency consistent with
        Manhattan-distance check.
  - H2e (regression byte-identity): NOT enforced here; lives in
    [[tests/test_world_intervention_hook_v0_45.py]].
  - C_RISES_ABOVE_A_GUARD (halt): if c_share_h8 > a_share_h8 + 0.10
    while b_passes, halt loud.
  - C_DISRUPTS_WITHOUT_B (halt): if c_below_a while b NOT passes,
    halt loud — mechanistically unmotivated.

Pre-reg: [[docs/experiments/fear_hunger_v0.45.md]].

Outputs eight CSVs under ``runs/lineage-v0.45/``:
  - per_run.csv               (48 rows)
  - per_arm_per_hazard.csv    (6 rows)
  - intervention_summary.csv  (6 rows)
  - primary_test.csv          (1 row, with explicit verdict booleans)
  - secondary_test.csv        (1 row)
  - verdict.csv               (1 row)
  - auxiliary_findings.csv    (2 rows: one per hazard)
  - placement_conservation.csv (per-(arm, hazard) digest of fired
                                events: kind histogram, mean
                                n_valid, B-adjacency-fraction)

Usage:
    uv run python scripts/v0_45_intervention_audit.py
"""

from __future__ import annotations

import csv
import importlib.util
import json
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


EXPECTED_HAZARDS: tuple[int, ...] = (0, 8)
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(65, 73))  # 65..72
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds
EXPECTED_TICK_THRESHOLD: int = 50  # callback gated; events have tick > 50

# Locked thresholds (parallel to v0.42 / v0.43R / v0.44)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Auxiliary threshold
AUXILIARY_GLOBAL_REDIRECT_ABLATION_MAX_EXCLUDED: int = 2

# Arm labels (mirror V0_45_INTERVENTION_ARMS)
ARM_A_NULL: str = "A_null"
ARM_B_UNIFORM_GLOBAL: str = "B_uniform_valid_region"
ARM_C_UNIFORM_NEIGHBOR: str = "C_uniform_neighbor"

ALL_ARMS: tuple[str, ...] = (ARM_A_NULL, ARM_B_UNIFORM_GLOBAL, ARM_C_UNIFORM_NEIGHBOR)

# Intervention-kind strings
KIND_NULL: str = "null"
KIND_UNIFORM_VALID_REGION_BIRTH: str = "uniform_valid_region_birth_position_after_tick50"
KIND_UNIFORM_NEIGHBOR_BIRTH: str = "uniform_neighbor_birth_position_after_tick50"
RNG_STREAM_LABEL: str = "v0_45_birth_position_intervention"

VALID_TARGET_KINDS: frozenset[str] = frozenset({"EMPTY", "FOOD", "SAFE"})

# Verdict labels
VERDICT_BIRTH_LOCALITY_NECESSARY = "BIRTH_LOCALITY_NECESSARY"
VERDICT_LOCAL_CONTROL_DISRUPTS = "LOCAL_CONTROL_DISRUPTS_DOMINANCE"
VERDICT_BIRTH_LOCALITY_NOT_NECESSARY = "BIRTH_LOCALITY_NOT_NECESSARY"


LOCKED_BIRTH_LOCALITY_NECESSARY_PHRASE = (
    "Redirecting every post-50 offspring birth to a uniformly-random "
    "valid-safe-placeable cell anywhere in the chamber (breaking parent "
    "adjacency) materially disrupts the post-50 dominance pattern at "
    "h=8: when offspring are scattered across the chamber rather than "
    "placed adjacent to their parents, the surviving lineages do not "
    "reconstitute concentration of comparable share. The adjacency-"
    "preserving randomization control (which selects uniformly among "
    "parent's N/S/E/W valid-safe-placeable neighbors using the same "
    "RNG stream) does NOT produce comparable disruption. Under the "
    "tested substrate, parent-local birth placement is necessary for "
    "the v0.34..v0.41 dominance pattern; the specific deterministic "
    "N/S/E/W tie-break is not. v0.45 does not declare which property "
    "of parent-local placement carries the effect; refinement "
    "interventions in v0.46+ are required. Necessity is established at "
    "one hazard level (h=8) on one seed band (65..72) under one "
    "redirection rule (uniform-valid-region); cross-stream calibration "
    "and dose-response sweeps are reserved for v0.46+. Sufficiency is "
    "NOT tested."
)
LOCKED_LOCAL_CONTROL_DISRUPTS_PHRASE = (
    "Both global redirection and adjacency-preserving randomization "
    "disrupt post-50 dominance at h=8. The post-50 dominance pattern "
    "is sensitive to any per-birth randomization of comparable "
    "magnitude (uniform among the eligible-cell set using the v0.45 "
    "RNG stream), not specifically to adjacency-breaking. v0.34..v0.41's "
    "correlational pattern reflects fragility to placement-shock rather "
    "than a locality-specific causal mechanism. v0.46 candidate: weaker "
    "C-arm randomization (rotated-iteration-order) to test whether the "
    "pattern is fragile to any randomization or only to uniform-random. "
    "Mechanism remains unidentified at the offspring-placement level."
)
LOCKED_BIRTH_LOCALITY_NOT_NECESSARY_PHRASE = (
    "Neither redirection (global or adjacency-preserving) materially "
    "disrupts the post-50 dominance pattern at h=8. A surviving lineage "
    "reconstitutes concentration-of-share even when offspring are "
    "scattered uniformly across the chamber's valid-safe-placeable "
    "region. Parent-local birth placement is not necessary for post-50 "
    "dominance under the tested substrate; the causal source lives "
    "outside the offspring-placement layer at the anchor moment. "
    "v0.42 ruled out the tick-50 leader's identity; v0.43R's food-"
    "density probe was disqualified (substrate depleted); v0.44 ruled "
    "out tick-50 respawn flow; v0.45 rules out post-50 birth-position "
    "locality. Remaining substrate-anchored candidates: founder-trait "
    "lock-in, hazard topology relocation, chamber geometry "
    "(wall-adjacency, reachability). v0.46 candidate: founder-trait "
    "lock-in or hazard-relocation intervention."
)
LOCKED_GLOBAL_REDIRECT_ABLATES_REPRODUCTION_PHRASE = (
    "At hazard h={h}, the B_uniform_valid_region arm produced "
    "{n_excluded} of 8 runs with zero post-50 births: the uniform-"
    "global redirection scattered offspring far from parents, ablating "
    "reproduction itself rather than relocating dominance. This is a "
    "descriptive substrate finding parallel to but independent of the "
    "share-based primary verdict: the distance from parent reduced "
    "reproductive viability below the threshold required to sustain "
    "post-50 reproduction in this fraction of seeds at this hazard. "
    "The primary verdict is computed over n_used (non-excluded) runs; "
    "this auxiliary finding is reported alongside but does NOT alter "
    "the primary verdict logic. v0.46 candidate: limit B's redirection "
    "radius to separate distance-ablates-reproduction from distance-"
    "relocates-dominance."
)


RUNS_ROOT: Path = Path("runs")
SWEEP_ROOT: Path = RUNS_ROOT / "fear-hunger-v0.45-tight_gradient" / "arms"
OUT_DIR: Path = RUNS_ROOT / "lineage-v0.45"


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerRunRow:
    arm: str
    hazard: int
    seed: int
    intervention_kind: str
    n_redirected_births: int
    fraction_b_preserved_adjacency: float
    mean_n_valid_cells_per_birth: float
    target_kind_n_empty: int
    target_kind_n_food: int
    target_kind_n_safe: int
    total_post_50_births: int
    top_lineage_id: int | None
    top_lineage_post50_births: int
    post_intervention_top_lineage_b50_share: float
    excluded_zero_post50: bool


@dataclass(frozen=True)
class PerArmPerHazardRow:
    arm: str
    hazard: int
    n_runs: int
    n_runs_used: int
    n_excluded_zero_post50: int
    mean_share: float
    median_share: float


@dataclass(frozen=True)
class InterventionSummaryRow:
    arm: str
    hazard: int
    mean_post_intervention_top_lineage_b50_share: float
    n_runs_used: int


@dataclass(frozen=True)
class PrimaryTestRow:
    a_share_h8: float
    b_share_h8: float
    c_share_h8: float
    delta_b_minus_a_h8: float
    delta_c_minus_a_h8: float
    b_passes: bool
    c_passes: bool
    c_below_a: bool
    c_above_a: bool
    birth_locality_necessary: bool
    local_control_disrupts: bool
    birth_locality_not_necessary: bool
    c_above_a_unmodeled_substrate_artefact: bool
    c_disrupts_without_b: bool
    primary_fires: bool


@dataclass(frozen=True)
class SecondaryTestRow:
    delta_b_minus_a_h0: float
    delta_b_minus_a_h8: float
    abs_delta_h0: float
    abs_delta_h8: float
    hazard_amplified: bool
    secondary_fires: bool


@dataclass(frozen=True)
class VerdictRow:
    verdict: str
    locked_phrase: str
    birth_locality_necessary: bool
    local_control_disrupts: bool
    birth_locality_not_necessary: bool
    primary_fires: bool
    secondary_fires: bool


@dataclass(frozen=True)
class AuxiliaryFindingRow:
    hazard: int
    b_n_excluded_zero_post50: int
    ablation_threshold_exceeded: bool
    auxiliary_phrase_fires: bool
    locked_phrase: str


@dataclass(frozen=True)
class PlacementConservationRow:
    arm: str
    hazard: int
    n_runs: int
    n_redirected_total: int
    mean_n_valid_cells: float
    fraction_b_preserved_adjacency: float
    n_target_empty: int
    n_target_food: int
    n_target_safe: int


# ---------------------------------------------------------------------------
# Sweep discovery
# ---------------------------------------------------------------------------


_ARM_DIRS: dict[str, dict[int, str]] = {
    ARM_A_NULL: {
        0: "v045-A_null-hzd0-influx-1.0",
        8: "v045-A_null-hzd8-influx-1.0",
    },
    ARM_B_UNIFORM_GLOBAL: {
        0: "v045-B_uniform_valid_region-hzd0-influx-1.0",
        8: "v045-B_uniform_valid_region-hzd8-influx-1.0",
    },
    ARM_C_UNIFORM_NEIGHBOR: {
        0: "v045-C_uniform_neighbor-hzd0-influx-1.0",
        8: "v045-C_uniform_neighbor-hzd8-influx-1.0",
    },
}


def _events_path(arm: str, hazard: int, seed: int) -> Path:
    return SWEEP_ROOT / _ARM_DIRS[arm][hazard] / f"seed-{seed}" / "events.jsonl"


def assert_sweep_present() -> None:
    """H2a: 48 events.jsonl files on disk."""
    missing: list[Path] = []
    for arm in ALL_ARMS:
        for hazard in EXPECTED_HAZARDS:
            for seed in EXPECTED_SEEDS:
                p = _events_path(arm, hazard, seed)
                if not p.exists():
                    missing.append(p)
    if missing:
        msg = (
            f"v0.45 sweep incomplete: {len(missing)} events.jsonl missing. "
            f"First missing: {missing[0]}"
        )
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run reduction
# ---------------------------------------------------------------------------


def _read_events_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _reduce_one_run(arm: str, hazard: int, seed: int) -> PerRunRow:  # noqa: PLR0912, PLR0915
    events = _read_events_jsonl(_events_path(arm, hazard, seed))
    redirect_events = [e for e in events if e["type"] == "BirthRedirectedByIntervention"]

    if arm == ARM_A_NULL:
        if redirect_events:
            msg = (
                f"H2b violation: A_null arm hzd={hazard} seed={seed} emitted "
                f"{len(redirect_events)} BirthRedirectedByIntervention events; expected 0"
            )
            raise lr.LineageReplayError(msg)
        intervention_kind = KIND_NULL
        n_redirected = 0
        fraction_adjacency = float("nan")
        mean_n_valid = float("nan")
        n_kind = {"EMPTY": 0, "FOOD": 0, "SAFE": 0}
    else:
        expected_kind = (
            KIND_UNIFORM_VALID_REGION_BIRTH
            if arm == ARM_B_UNIFORM_GLOBAL
            else KIND_UNIFORM_NEIGHBOR_BIRTH
        )
        n_kind = {"EMPTY": 0, "FOOD": 0, "SAFE": 0}
        adjacency_count = 0
        n_valid_sum = 0
        for ev_env in redirect_events:
            ev = ev_env["event"]
            # H2b kind dispatch.
            if ev["intervention_kind"] != expected_kind:
                msg = (
                    f"H2b kind mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"intervention_kind={ev['intervention_kind']!r}; expected {expected_kind!r}"
                )
                raise lr.LineageReplayError(msg)
            # H2c tick monotonicity.
            if ev["tick"] <= EXPECTED_TICK_THRESHOLD:
                msg = (
                    f"H2c violation: arm={arm} hzd={hazard} seed={seed} "
                    f"event tick={ev['tick']} <= {EXPECTED_TICK_THRESHOLD}"
                )
                raise lr.LineageReplayError(msg)
            # H2d placement conservation.
            kind_name = ev["target_cell_kind"]
            if kind_name not in VALID_TARGET_KINDS:
                msg = (
                    f"H2d violation: arm={arm} hzd={hazard} seed={seed} "
                    f"target_cell_kind={kind_name!r} not in {sorted(VALID_TARGET_KINDS)}"
                )
                raise lr.LineageReplayError(msg)
            n_kind[kind_name] += 1
            if (ev["redirected_x"], ev["redirected_y"]) == (ev["parent_x"], ev["parent_y"]):
                msg = (
                    f"H2d violation: arm={arm} hzd={hazard} seed={seed} "
                    f"redirected cell == parent cell ({ev['parent_x']}, {ev['parent_y']})"
                )
                raise lr.LineageReplayError(msg)
            manhattan = abs(ev["parent_x"] - ev["redirected_x"]) + abs(
                ev["parent_y"] - ev["redirected_y"]
            )
            if arm == ARM_C_UNIFORM_NEIGHBOR and manhattan != 1:
                msg = (
                    f"H2d C-adjacency violation: arm={arm} hzd={hazard} seed={seed} "
                    f"Manhattan distance from parent={manhattan}; expected 1"
                )
                raise lr.LineageReplayError(msg)
            preserved = bool(ev["preserved_parent_adjacency"])
            if preserved != (manhattan == 1):
                msg = (
                    f"H2d preserved_parent_adjacency inconsistent: arm={arm} hzd={hazard} "
                    f"seed={seed} preserved={preserved} manhattan={manhattan}"
                )
                raise lr.LineageReplayError(msg)
            if preserved:
                adjacency_count += 1
            if int(ev["n_valid_cells"]) < 1:
                msg = (
                    f"H2d violation: arm={arm} hzd={hazard} seed={seed} "
                    f"n_valid_cells={ev['n_valid_cells']} < 1 on a fired event"
                )
                raise lr.LineageReplayError(msg)
            n_valid_sum += int(ev["n_valid_cells"])
            if ev["rng_stream_label"] != RNG_STREAM_LABEL:
                msg = (
                    f"H2d rng_stream_label drift: arm={arm} hzd={hazard} seed={seed} "
                    f"rng_stream_label={ev['rng_stream_label']!r}; expected {RNG_STREAM_LABEL!r}"
                )
                raise lr.LineageReplayError(msg)
        intervention_kind = expected_kind
        n_redirected = len(redirect_events)
        if n_redirected > 0 and arm == ARM_B_UNIFORM_GLOBAL:
            fraction_adjacency = adjacency_count / n_redirected
        elif n_redirected > 0 and arm == ARM_C_UNIFORM_NEIGHBOR:
            fraction_adjacency = float("nan")  # always 1.0 by construction
        else:
            fraction_adjacency = float("nan")
        mean_n_valid = n_valid_sum / n_redirected if n_redirected > 0 else float("nan")

    # Compute post_intervention_top_lineage_b50_share over ALL 5 lineages
    # (no exclusion — no lineage is killed by birth redirection).
    post50_births_by_lineage: dict[int, int] = {}
    for e in events:
        if e["type"] != "AgentBorn":
            continue
        ev = e["event"]
        if ev["tick"] <= 50:
            continue
        lineage = ev["lineage_id"]
        post50_births_by_lineage[lineage] = post50_births_by_lineage.get(lineage, 0) + 1

    total_post50 = sum(post50_births_by_lineage.values())
    if total_post50 == 0:
        top_lineage_id: int | None = None
        top_births = 0
        share = float("nan")
        excluded = True
    else:
        top_lineage_id = max(
            post50_births_by_lineage,
            key=lambda lid: (post50_births_by_lineage[lid], -lid),
        )
        top_births = post50_births_by_lineage[top_lineage_id]
        share = top_births / total_post50
        excluded = False

    return PerRunRow(
        arm=arm,
        hazard=hazard,
        seed=seed,
        intervention_kind=intervention_kind,
        n_redirected_births=n_redirected,
        fraction_b_preserved_adjacency=fraction_adjacency,
        mean_n_valid_cells_per_birth=mean_n_valid,
        target_kind_n_empty=n_kind["EMPTY"],
        target_kind_n_food=n_kind["FOOD"],
        target_kind_n_safe=n_kind["SAFE"],
        total_post_50_births=total_post50,
        top_lineage_id=top_lineage_id,
        top_lineage_post50_births=top_births,
        post_intervention_top_lineage_b50_share=share,
        excluded_zero_post50=excluded,
    )


def reduce_all_runs() -> list[PerRunRow]:
    out: list[PerRunRow] = []
    for arm in ALL_ARMS:
        for hazard in EXPECTED_HAZARDS:
            for seed in EXPECTED_SEEDS:
                out.append(_reduce_one_run(arm, hazard, seed))
    if len(out) != EXPECTED_RUNS_TOTAL:
        msg = f"reduce_all_runs produced {len(out)} runs; expected {EXPECTED_RUNS_TOTAL}"
        raise lr.LineageReplayError(msg)
    return out


# ---------------------------------------------------------------------------
# Per-(arm, hazard) aggregation
# ---------------------------------------------------------------------------


def aggregate_per_arm_per_hazard(per_run: list[PerRunRow]) -> list[PerArmPerHazardRow]:
    out: list[PerArmPerHazardRow] = []
    for arm in ALL_ARMS:
        for hazard in EXPECTED_HAZARDS:
            bucket = [r for r in per_run if r.arm == arm and r.hazard == hazard]
            n_excluded = sum(
                1 for r in bucket if math.isnan(r.post_intervention_top_lineage_b50_share)
            )
            usable = [
                r.post_intervention_top_lineage_b50_share
                for r in bucket
                if not math.isnan(r.post_intervention_top_lineage_b50_share)
            ]
            mean_share = statistics.mean(usable) if usable else float("nan")
            median_share = statistics.median(usable) if usable else float("nan")
            out.append(
                PerArmPerHazardRow(
                    arm=arm,
                    hazard=hazard,
                    n_runs=len(bucket),
                    n_runs_used=len(usable),
                    n_excluded_zero_post50=n_excluded,
                    mean_share=mean_share,
                    median_share=median_share,
                )
            )
    return out


def build_intervention_summary(per_arm: list[PerArmPerHazardRow]) -> list[InterventionSummaryRow]:
    return [
        InterventionSummaryRow(
            arm=r.arm,
            hazard=r.hazard,
            mean_post_intervention_top_lineage_b50_share=r.mean_share,
            n_runs_used=r.n_runs_used,
        )
        for r in per_arm
    ]


def build_placement_conservation(per_run: list[PerRunRow]) -> list[PlacementConservationRow]:
    out: list[PlacementConservationRow] = []
    for arm in ALL_ARMS:
        for hazard in EXPECTED_HAZARDS:
            bucket = [r for r in per_run if r.arm == arm and r.hazard == hazard]
            n_redirected_total = sum(r.n_redirected_births for r in bucket)
            if arm == ARM_A_NULL or n_redirected_total == 0:
                out.append(
                    PlacementConservationRow(
                        arm=arm,
                        hazard=hazard,
                        n_runs=len(bucket),
                        n_redirected_total=n_redirected_total,
                        mean_n_valid_cells=float("nan"),
                        fraction_b_preserved_adjacency=float("nan"),
                        n_target_empty=0,
                        n_target_food=0,
                        n_target_safe=0,
                    )
                )
                continue
            valid_means = [
                r.mean_n_valid_cells_per_birth
                for r in bucket
                if not math.isnan(r.mean_n_valid_cells_per_birth)
            ]
            mean_n_valid = statistics.mean(valid_means) if valid_means else float("nan")
            if arm == ARM_B_UNIFORM_GLOBAL:
                adj_runs = [
                    r.fraction_b_preserved_adjacency
                    for r in bucket
                    if not math.isnan(r.fraction_b_preserved_adjacency)
                ]
                fraction_adjacency = statistics.mean(adj_runs) if adj_runs else float("nan")
            else:
                fraction_adjacency = 1.0  # C arm always preserves adjacency
            out.append(
                PlacementConservationRow(
                    arm=arm,
                    hazard=hazard,
                    n_runs=len(bucket),
                    n_redirected_total=n_redirected_total,
                    mean_n_valid_cells=mean_n_valid,
                    fraction_b_preserved_adjacency=fraction_adjacency,
                    n_target_empty=sum(r.target_kind_n_empty for r in bucket),
                    n_target_food=sum(r.target_kind_n_food for r in bucket),
                    n_target_safe=sum(r.target_kind_n_safe for r in bucket),
                )
            )
    return out


# ---------------------------------------------------------------------------
# Primary + secondary tests
# ---------------------------------------------------------------------------


def _share_at(per_arm: list[PerArmPerHazardRow], arm: str, hazard: int) -> float:
    matches = [r for r in per_arm if r.arm == arm and r.hazard == hazard]
    if len(matches) != 1:
        msg = f"per_arm lookup ambiguous for arm={arm} hazard={hazard}"
        raise lr.LineageReplayError(msg)
    return matches[0].mean_share


def evaluate_primary_test(per_arm: list[PerArmPerHazardRow]) -> PrimaryTestRow:
    a8 = _share_at(per_arm, ARM_A_NULL, 8)
    b8 = _share_at(per_arm, ARM_B_UNIFORM_GLOBAL, 8)
    c8 = _share_at(per_arm, ARM_C_UNIFORM_NEIGHBOR, 8)
    delta_b = b8 - a8
    delta_c = c8 - a8
    b_passes = delta_b <= -PRIMARY_B_REDUCTION_THRESHOLD
    c_passes = abs(delta_c) <= PRIMARY_C_TOLERANCE
    c_below_a = delta_c <= -PRIMARY_C_TOLERANCE
    c_above_a = delta_c > PRIMARY_C_TOLERANCE
    birth_locality_necessary = b_passes and c_passes
    local_control_disrupts = b_passes and c_below_a
    birth_locality_not_necessary = (not b_passes) and (not c_below_a)
    c_above_a_unmodeled = b_passes and c_above_a
    c_disrupts_without_b = (not b_passes) and c_below_a
    primary_fires = birth_locality_necessary or local_control_disrupts
    return PrimaryTestRow(
        a_share_h8=a8,
        b_share_h8=b8,
        c_share_h8=c8,
        delta_b_minus_a_h8=delta_b,
        delta_c_minus_a_h8=delta_c,
        b_passes=b_passes,
        c_passes=c_passes,
        c_below_a=c_below_a,
        c_above_a=c_above_a,
        birth_locality_necessary=birth_locality_necessary,
        local_control_disrupts=local_control_disrupts,
        birth_locality_not_necessary=birth_locality_not_necessary,
        c_above_a_unmodeled_substrate_artefact=c_above_a_unmodeled,
        c_disrupts_without_b=c_disrupts_without_b,
        primary_fires=primary_fires,
    )


def evaluate_secondary_test(
    per_arm: list[PerArmPerHazardRow], primary: PrimaryTestRow
) -> SecondaryTestRow:
    a0 = _share_at(per_arm, ARM_A_NULL, 0)
    b0 = _share_at(per_arm, ARM_B_UNIFORM_GLOBAL, 0)
    delta_h0 = b0 - a0
    delta_h8 = primary.delta_b_minus_a_h8
    return SecondaryTestRow(
        delta_b_minus_a_h0=delta_h0,
        delta_b_minus_a_h8=delta_h8,
        abs_delta_h0=abs(delta_h0),
        abs_delta_h8=abs(delta_h8),
        hazard_amplified=abs(delta_h8) > abs(delta_h0),
        secondary_fires=primary.primary_fires and abs(delta_h8) > abs(delta_h0),
    )


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def evaluate_verdict(primary: PrimaryTestRow, secondary: SecondaryTestRow) -> VerdictRow:
    if primary.c_above_a_unmodeled_substrate_artefact:
        msg = (
            "C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT: c_share_h8 - a_share_h8 = "
            f"{primary.delta_c_minus_a_h8:+.3f} > {PRIMARY_C_TOLERANCE} "
            "while b_passes=True; the adjacency-preserving randomization control "
            "increased post-50 dominance above null. Mechanistically unmotivated "
            "under the v0.45 model. Halt loud."
        )
        raise lr.LineageReplayError(msg)
    if primary.c_disrupts_without_b:
        msg = (
            "C_DISRUPTS_WITHOUT_B: c_below_a=True while b_passes=False. "
            f"delta(B-A)={primary.delta_b_minus_a_h8:+.3f} (>= {-PRIMARY_B_REDUCTION_THRESHOLD}); "
            f"delta(C-A)={primary.delta_c_minus_a_h8:+.3f} (<= {-PRIMARY_C_TOLERANCE}). "
            "The weaker adjacency-preserving control disrupts dominance while the "
            "stronger global redirection does not. Mechanistically unmotivated. "
            "Halt loud."
        )
        raise lr.LineageReplayError(msg)

    if primary.birth_locality_necessary:
        return VerdictRow(
            verdict=VERDICT_BIRTH_LOCALITY_NECESSARY,
            locked_phrase=LOCKED_BIRTH_LOCALITY_NECESSARY_PHRASE,
            birth_locality_necessary=True,
            local_control_disrupts=False,
            birth_locality_not_necessary=False,
            primary_fires=True,
            secondary_fires=secondary.secondary_fires,
        )
    if primary.local_control_disrupts:
        return VerdictRow(
            verdict=VERDICT_LOCAL_CONTROL_DISRUPTS,
            locked_phrase=LOCKED_LOCAL_CONTROL_DISRUPTS_PHRASE,
            birth_locality_necessary=False,
            local_control_disrupts=True,
            birth_locality_not_necessary=False,
            primary_fires=True,
            secondary_fires=secondary.secondary_fires,
        )
    return VerdictRow(
        verdict=VERDICT_BIRTH_LOCALITY_NOT_NECESSARY,
        locked_phrase=LOCKED_BIRTH_LOCALITY_NOT_NECESSARY_PHRASE,
        birth_locality_necessary=False,
        local_control_disrupts=False,
        birth_locality_not_necessary=True,
        primary_fires=False,
        secondary_fires=secondary.secondary_fires,
    )


def evaluate_auxiliary_findings(per_arm: list[PerArmPerHazardRow]) -> list[AuxiliaryFindingRow]:
    out: list[AuxiliaryFindingRow] = []
    for hazard in EXPECTED_HAZARDS:
        b_row = next(r for r in per_arm if r.arm == ARM_B_UNIFORM_GLOBAL and r.hazard == hazard)
        n_excl = b_row.n_excluded_zero_post50
        ablation_threshold_exceeded = n_excl > AUXILIARY_GLOBAL_REDIRECT_ABLATION_MAX_EXCLUDED
        phrase = (
            LOCKED_GLOBAL_REDIRECT_ABLATES_REPRODUCTION_PHRASE.format(h=hazard, n_excluded=n_excl)
            if ablation_threshold_exceeded
            else ""
        )
        out.append(
            AuxiliaryFindingRow(
                hazard=hazard,
                b_n_excluded_zero_post50=n_excl,
                ablation_threshold_exceeded=ablation_threshold_exceeded,
                auxiliary_phrase_fires=ablation_threshold_exceeded,
                locked_phrase=phrase,
            )
        )
    return out


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
    "arm",
    "hazard",
    "seed",
    "intervention_kind",
    "n_redirected_births",
    "fraction_b_preserved_adjacency",
    "mean_n_valid_cells_per_birth",
    "target_kind_n_empty",
    "target_kind_n_food",
    "target_kind_n_safe",
    "total_post_50_births",
    "top_lineage_id",
    "top_lineage_post50_births",
    "post_intervention_top_lineage_b50_share",
    "excluded_zero_post50",
]
PER_ARM_PER_HAZARD_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "n_runs",
    "n_runs_used",
    "n_excluded_zero_post50",
    "mean_share",
    "median_share",
]
INTERVENTION_SUMMARY_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "mean_post_intervention_top_lineage_b50_share",
    "n_runs_used",
]
PRIMARY_FIELDNAMES: list[str] = [
    "a_share_h8",
    "b_share_h8",
    "c_share_h8",
    "delta_b_minus_a_h8",
    "delta_c_minus_a_h8",
    "b_passes",
    "c_passes",
    "c_below_a",
    "c_above_a",
    "birth_locality_necessary",
    "local_control_disrupts",
    "birth_locality_not_necessary",
    "c_above_a_unmodeled_substrate_artefact",
    "c_disrupts_without_b",
    "primary_fires",
]
SECONDARY_FIELDNAMES: list[str] = [
    "delta_b_minus_a_h0",
    "delta_b_minus_a_h8",
    "abs_delta_h0",
    "abs_delta_h8",
    "hazard_amplified",
    "secondary_fires",
]
VERDICT_FIELDNAMES: list[str] = [
    "verdict",
    "locked_phrase",
    "birth_locality_necessary",
    "local_control_disrupts",
    "birth_locality_not_necessary",
    "primary_fires",
    "secondary_fires",
]
AUXILIARY_FIELDNAMES: list[str] = [
    "hazard",
    "b_n_excluded_zero_post50",
    "ablation_threshold_exceeded",
    "auxiliary_phrase_fires",
    "locked_phrase",
]
PLACEMENT_CONSERVATION_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "n_runs",
    "n_redirected_total",
    "mean_n_valid_cells",
    "fraction_b_preserved_adjacency",
    "n_target_empty",
    "n_target_food",
    "n_target_safe",
]


def write_outputs(
    per_run: list[PerRunRow],
    per_arm: list[PerArmPerHazardRow],
    intervention_summary: list[InterventionSummaryRow],
    primary: PrimaryTestRow,
    secondary: SecondaryTestRow,
    verdict: VerdictRow,
    auxiliary: list[AuxiliaryFindingRow],
    placement_conservation: list[PlacementConservationRow],
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_run": out_dir / "per_run.csv",
        "per_arm_per_hazard": out_dir / "per_arm_per_hazard.csv",
        "intervention_summary": out_dir / "intervention_summary.csv",
        "primary_test": out_dir / "primary_test.csv",
        "secondary_test": out_dir / "secondary_test.csv",
        "verdict": out_dir / "verdict.csv",
        "auxiliary_findings": out_dir / "auxiliary_findings.csv",
        "placement_conservation": out_dir / "placement_conservation.csv",
    }
    _write_dataclass_csv(per_run, paths["per_run"], PER_RUN_FIELDNAMES)
    _write_dataclass_csv(per_arm, paths["per_arm_per_hazard"], PER_ARM_PER_HAZARD_FIELDNAMES)
    _write_dataclass_csv(
        intervention_summary, paths["intervention_summary"], INTERVENTION_SUMMARY_FIELDNAMES
    )
    _write_dataclass_csv([primary], paths["primary_test"], PRIMARY_FIELDNAMES)
    _write_dataclass_csv([secondary], paths["secondary_test"], SECONDARY_FIELDNAMES)
    _write_dataclass_csv([verdict], paths["verdict"], VERDICT_FIELDNAMES)
    _write_dataclass_csv(auxiliary, paths["auxiliary_findings"], AUXILIARY_FIELDNAMES)
    _write_dataclass_csv(
        placement_conservation,
        paths["placement_conservation"],
        PLACEMENT_CONSERVATION_FIELDNAMES,
    )
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_sweep_present()
    per_run = reduce_all_runs()
    print(
        f"v0.45 intervention_audit: {len(per_run)} per-run records "
        f"(3 arms x 2 hazards x 8 seeds = {EXPECTED_RUNS_TOTAL})",
        flush=True,
    )

    per_arm = aggregate_per_arm_per_hazard(per_run)
    intervention_summary = build_intervention_summary(per_arm)
    placement_conservation = build_placement_conservation(per_run)
    primary = evaluate_primary_test(per_arm)
    secondary = evaluate_secondary_test(per_arm, primary)
    verdict = evaluate_verdict(primary, secondary)
    auxiliary = evaluate_auxiliary_findings(per_arm)

    paths = write_outputs(
        per_run,
        per_arm,
        intervention_summary,
        primary,
        secondary,
        verdict,
        auxiliary,
        placement_conservation,
    )

    print()
    print("Per-(arm, hazard) post-intervention top-lineage b50 share:")
    print(f"  {'arm':>26} {'h':>3} {'n_runs':>6} {'n_used':>6} {'mean':>8} {'median':>8}")
    for r in per_arm:
        m = "nan" if math.isnan(r.mean_share) else f"{r.mean_share:.3f}"
        med = "nan" if math.isnan(r.median_share) else f"{r.median_share:.3f}"
        print(
            f"  {r.arm:>26} {r.hazard:>3d} {r.n_runs:>6d} {r.n_runs_used:>6d} {m:>8} {med:>8}",
            flush=True,
        )

    print()
    print("Placement conservation:")
    print(
        f"  {'arm':>26} {'h':>3} {'n':>3} {'redir':>6} "
        f"{'mean_valid':>10} {'b_adj':>6} {'EMPTY':>6} {'FOOD':>6} {'SAFE':>6}"
    )
    for r in placement_conservation:
        mean_v = "nan" if math.isnan(r.mean_n_valid_cells) else f"{r.mean_n_valid_cells:.1f}"
        adj = (
            "nan"
            if math.isnan(r.fraction_b_preserved_adjacency)
            else f"{r.fraction_b_preserved_adjacency:.2f}"
        )
        print(
            f"  {r.arm:>26} {r.hazard:>3d} {r.n_runs:>3d} {r.n_redirected_total:>6d} "
            f"{mean_v:>10} {adj:>6} "
            f"{r.n_target_empty:>6d} {r.n_target_food:>6d} {r.n_target_safe:>6d}",
            flush=True,
        )

    print()
    print("Primary test (h=8):")
    print(
        f"  A_null={primary.a_share_h8:.3f}  "
        f"B_uniform={primary.b_share_h8:.3f}  "
        f"C_neighbor={primary.c_share_h8:.3f}"
    )
    print(
        f"  delta(B-A)={primary.delta_b_minus_a_h8:+.3f}  "
        f"delta(C-A)={primary.delta_c_minus_a_h8:+.3f}"
    )
    print(
        f"  b_passes={primary.b_passes}  c_passes={primary.c_passes}  "
        f"c_below_a={primary.c_below_a}  c_above_a={primary.c_above_a}  "
        f"primary_fires={primary.primary_fires}"
    )

    print()
    print("Secondary test (hazard amplification of B-A):")
    print(
        f"  |delta(h=0)|={secondary.abs_delta_h0:.3f}  "
        f"|delta(h=8)|={secondary.abs_delta_h8:.3f}  "
        f"hazard_amplified={secondary.hazard_amplified}  "
        f"secondary_fires={secondary.secondary_fires}"
    )

    print()
    print(f"  v0.45 verdict: {verdict.verdict}")
    print(f'    locked phrase: "{verdict.locked_phrase}"')

    print()
    print("Auxiliary findings (GLOBAL_REDIRECT_ABLATES_REPRODUCTION):")
    for r in auxiliary:
        print(
            f"  hzd={r.hazard:d}  b_n_excluded={r.b_n_excluded_zero_post50:d}  "
            f"fires={r.auxiliary_phrase_fires}",
            flush=True,
        )

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>22}  -> {path}")


if __name__ == "__main__":
    main()
