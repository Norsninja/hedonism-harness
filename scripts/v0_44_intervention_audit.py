"""v0.44 intervention audit: post-intervention top-lineage b50 share under
tick-50 respawn-schedule rewrites.

Tests the v0.44 respawn-flow-necessity question on the 48-run intervention
corpus (3 arms x 2 hazards x 8 seeds):

  Primary:   B_delay_respawn_schedule_plus_25 at h=8 reduces post_intervention_
             top_lineage_b50_share by >= 0.15 below A_null AND
             C_permute_respawn_schedule_reverse_row_major stays within +/- 0.10
             of A_null at h=8.
  Secondary: B-vs-A reduction is larger at h=8 than at h=0 (descriptive only).

Verdict (locked, mutually exclusive on b_passes / c-direction):
  RESPAWN_FLOW_NECESSARY                         iff b_passes AND c_passes.
  SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE      iff b_passes AND c_below_a.
  RESPAWN_FLOW_NOT_NECESSARY                     iff not b_passes.
  C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt)  iff b_passes AND c_above_a.

Auxiliary (per-hazard, non-exclusive):
  DELAY_ABLATES_REPRODUCTION fires at hazard h iff
  B_delay_respawn_schedule_plus_25's n_excluded_zero_post50 > 2 (out of 8).

Reads (per-arm-per-seed):
  - runs/fear-hunger-v0.44-tight_gradient/arms/<arm>/seed-<n>/events.jsonl
    for AgentBorn (post-50 births) and RespawnScheduleByIntervention
    (schedule conservation H2d).

Halt invariants (locked):
  - H2a (run count): 48 runs on disk.
  - H2b (intervention-fire count per arm): A_null=0; B=1 delay fire;
    C=1 permute fire.
  - H2c (effective_tick): every fired event has effective_tick=51.
  - H2d (schedule conservation):
      * For B: sum_after == sum_before + 25 * n_eligible_cells exactly;
        min_after == min_before + 25; max_after == max_before + 25;
        respawn_multiset_digest_before != respawn_multiset_digest_after.
      * For C: sum_after == sum_before exactly; min_after == min_before;
        max_after == max_before; respawn_multiset_digest_before ==
        respawn_multiset_digest_after exactly (permutation preserves
        the sorted multiset).
      * eligible_cells_digest consistent across all fired events at the
        same hazard bucket; n_cells_changed <= n_eligible_cells.
  - H2d-aux (eligible-cell-set stability):
      n_eligible_cells == EXPECTED_N_ELIGIBLE_CELLS (= 24, locked by
      preflight on seeds 57..64).
  - H2e (regression byte-identity): NOT enforced here; lives in
    [[tests/test_world_intervention_hook_v0_44.py]].
  - C_RISES_ABOVE_A_GUARD: if C share rises strictly above A by > 0.10,
    halt loud (substrate artefact unmodeled).

Pre-reg: [[docs/experiments/fear_hunger_v0.44.md]].

Outputs eight CSVs under ``runs/lineage-v0.44/``:
  - per_run.csv               (48 rows)
  - per_arm_per_hazard.csv    (6 rows: 3 arms x 2 hazards)
  - intervention_summary.csv  (6 rows)
  - primary_test.csv          (1 row, with explicit verdict booleans)
  - secondary_test.csv        (1 row)
  - verdict.csv               (1 row)
  - auxiliary_findings.csv    (2 rows: one per hazard)
  - schedule_conservation.csv (per-(arm, hazard) totals + digest stats)

Usage:
    uv run python scripts/v0_44_intervention_audit.py
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
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(57, 65))  # 57..64
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds
EXPECTED_N_ELIGIBLE_CELLS: int = 24  # locked by preflight on seeds 57..64

# Locked thresholds (parallel to v0.42 / v0.43R)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Auxiliary threshold
AUXILIARY_DELAY_ABLATION_MAX_EXCLUDED: int = 2

# B-arm delay magnitude (locked at +25)
B_DELAY_TICKS: int = 25

# Arm labels (mirror V0_44_INTERVENTION_ARMS)
ARM_A_NULL: str = "A_null"
ARM_B_DELAY: str = "B_delay_respawn_schedule_plus_25"
ARM_C_PERMUTE: str = "C_permute_respawn_schedule_reverse_row_major"

ALL_ARMS: tuple[str, ...] = (ARM_A_NULL, ARM_B_DELAY, ARM_C_PERMUTE)

# Intervention-kind strings (one per arm)
KIND_NULL: str = "null"
KIND_DELAY_RESPAWN_PLUS_25: str = "delay_respawn_schedule_plus_25_at_tick50"
KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR: str = "permute_respawn_schedule_reverse_row_major_at_tick50"

# Verdict labels
VERDICT_FLOW_NECESSARY = "RESPAWN_FLOW_NECESSARY"
VERDICT_PERTURBATION_DISRUPTS = "SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE"
VERDICT_FLOW_NOT_NECESSARY = "RESPAWN_FLOW_NOT_NECESSARY"


LOCKED_FLOW_NECESSARY_PHRASE = (
    "Delaying the respawn schedule by +25 ticks at the tick-50/tick-51 "
    "boundary materially disrupts the post-50 dominance pattern at h=8: "
    "when every scheduled cell's refill is pushed back by half the "
    "observation window, the surviving lineages do not reconstitute "
    "concentration of comparable share. The schedule-permutation control "
    "(which reassigns refill ticks across the (x, y)-sorted scheduled "
    "cells via reverse-row-major mapping, exactly preserving the multiset "
    "of refill ticks and the system-wide post-50 flow rate) does NOT "
    "produce comparable disruption. Under the tested substrate, respawn "
    "flow at tick 50 is necessary for the v0.34..v0.41 dominance pattern; "
    "the specific cell-to-tick assignment of refills across the food zone "
    "is not. v0.44 does not declare which property of respawn flow "
    "carries the effect; refinement interventions in v0.45+ are required. "
    "Necessity is established at one hazard level (h=8) on one seed band "
    "(57..64) under one delay magnitude (+25); cross-stream calibration "
    "and dose-response sweeps are reserved for v0.45+. Sufficiency is "
    "NOT tested."
)
LOCKED_PERTURBATION_DISRUPTS_PHRASE = (
    "Delaying respawn flow by +25 ticks disrupts post-50 dominance at "
    "h=8, but the multiset-preserving schedule-permutation control "
    "produces comparable disruption. The post-50 dominance pattern is "
    "sensitive to any respawn-schedule rewrite of comparable scope, not "
    "specifically to flow-rate reduction. v0.34..v0.41's correlational "
    "pattern reflects fragility to schedule-shock rather than a flow-"
    "rate-specific causal mechanism. v0.45 candidate: reduce the C-arm "
    "permutation magnitude (e.g., adjacent-pair swap rather than "
    "reverse-row-major) to test whether the pattern is fragile to any "
    "schedule rewrite or only to large-displacement rewrites. Mechanism "
    "remains unidentified at the respawn-schedule level."
)
LOCKED_FLOW_NOT_NECESSARY_PHRASE = (
    "Delaying the respawn schedule by +25 ticks at the tick-50/tick-51 "
    "boundary does not materially disrupt the post-50 dominance pattern "
    "at h=8. A surviving lineage reconstitutes concentration-of-share "
    "even when the post-50 refill window is shifted by half its width. "
    "Respawn flow at tick 50 is not necessary for post-50 dominance "
    "under the tested substrate; the causal source lives outside the "
    "respawn-schedule layer at the anchor moment. v0.42 ruled out the "
    "tick-50 leader's identity; v0.43R's food-density probe was "
    "disqualified (substrate depleted); v0.44 rules out tick-50 respawn "
    "flow. Remaining substrate-anchored candidates: founder-trait + "
    "spatial-position interaction at the depleted moment, hazard "
    "topology, chamber geometry (wall-adjacency, reachability), and "
    "birth-position constraints. v0.45 candidate: founder-trait lock-in "
    "or hazard-relocation intervention."
)
LOCKED_DELAY_ABLATES_REPRODUCTION_PHRASE = (
    "At hazard h={h}, the B_delay_respawn_schedule_plus_25 arm produced "
    "{n_excluded} of 8 runs with zero post-50 births: the +25-tick delay "
    "shifted refill timing past the threshold required to sustain post-50 "
    "reproduction itself rather than relocating dominance. This is a "
    "descriptive substrate finding parallel to but independent of the "
    "share-based primary verdict: the delayed refill window fell below "
    "the threshold required to sustain post-50 reproduction in this "
    "fraction of seeds at this hazard. The primary verdict is computed "
    "over n_used (non-excluded) runs; this auxiliary finding is reported "
    "alongside but does NOT alter the primary verdict logic. v0.45 "
    "candidate: use a milder delay magnitude (+12) to separate "
    "delay-matters-for-dominance from delay-matters-for-reproduction-"
    "at-all."
)


RUNS_ROOT: Path = Path("runs")
SWEEP_ROOT: Path = RUNS_ROOT / "fear-hunger-v0.44-tight_gradient" / "arms"
OUT_DIR: Path = RUNS_ROOT / "lineage-v0.44"


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerRunRow:
    arm: str
    hazard: int
    seed: int
    fired: bool
    intervention_kind: str
    n_eligible_cells: int
    n_cells_changed: int
    min_respawn_tick_before: int
    max_respawn_tick_before: int
    min_respawn_tick_after: int
    max_respawn_tick_after: int
    sum_respawn_tick_before: int
    sum_respawn_tick_after: int
    eligible_cells_digest: str
    respawn_multiset_digest_before: str
    respawn_multiset_digest_after: str
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
    respawn_flow_necessary: bool
    substrate_perturbation_disrupts: bool
    respawn_flow_not_necessary: bool
    c_above_a_unmodeled_substrate_artefact: bool
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
    respawn_flow_necessary: bool
    substrate_perturbation_disrupts: bool
    respawn_flow_not_necessary: bool
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
class ScheduleConservationRow:
    arm: str
    hazard: int
    n_runs: int
    mean_min_before: float
    mean_max_before: float
    mean_sum_before: float
    mean_min_after: float
    mean_max_after: float
    mean_sum_after: float
    n_runs_with_multiset_changed: int
    n_runs_with_eligible_cells_drift: int


# ---------------------------------------------------------------------------
# Sweep discovery
# ---------------------------------------------------------------------------


_ARM_DIRS: dict[str, dict[int, str]] = {
    ARM_A_NULL: {
        0: "v044-A_null-hzd0-influx-1.0",
        8: "v044-A_null-hzd8-influx-1.0",
    },
    ARM_B_DELAY: {
        0: "v044-B_delay_respawn_schedule_plus_25-hzd0-influx-1.0",
        8: "v044-B_delay_respawn_schedule_plus_25-hzd8-influx-1.0",
    },
    ARM_C_PERMUTE: {
        0: "v044-C_permute_respawn_schedule_reverse_row_major-hzd0-influx-1.0",
        8: "v044-C_permute_respawn_schedule_reverse_row_major-hzd8-influx-1.0",
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
            f"v0.44 sweep incomplete: {len(missing)} events.jsonl missing. "
            f"First missing: {missing[0]}"
        )
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run reduction
# ---------------------------------------------------------------------------


def _read_events_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _reduce_one_run(arm: str, hazard: int, seed: int) -> PerRunRow:  # noqa: PLR0912, PLR0915
    """Read events.jsonl for one (arm, hazard, seed), apply H2 invariants
    (b/c/d/d-aux), and return one PerRunRow.
    """
    events = _read_events_jsonl(_events_path(arm, hazard, seed))
    summaries = [e for e in events if e["type"] == "RespawnScheduleByIntervention"]

    if arm == ARM_A_NULL:
        # H2b: zero respawn-schedule events on A_null.
        if summaries:
            msg = (
                f"H2b violation: A_null arm hzd={hazard} seed={seed} emitted "
                f"{len(summaries)} RespawnScheduleByIntervention events; expected 0"
            )
            raise lr.LineageReplayError(msg)
        fired = False
        intervention_kind = KIND_NULL
        n_eligible_cells = 0
        n_cells_changed = 0
        min_before = 0
        max_before = 0
        min_after = 0
        max_after = 0
        sum_before = 0
        sum_after = 0
        eligible_cells_digest = ""
        digest_before = ""
        digest_after = ""
    else:
        # H2b: B and C must each fire exactly once.
        if len(summaries) != 1:
            msg = (
                f"H2b violation: arm={arm} hzd={hazard} seed={seed} emitted "
                f"{len(summaries)} RespawnScheduleByIntervention events; expected 1"
            )
            raise lr.LineageReplayError(msg)
        ev = summaries[0]["event"]
        expected_kind = (
            KIND_DELAY_RESPAWN_PLUS_25
            if arm == ARM_B_DELAY
            else KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR
        )
        if ev["intervention_kind"] != expected_kind:
            msg = (
                f"H2b kind mismatch: arm={arm} hzd={hazard} seed={seed} "
                f"intervention_kind={ev['intervention_kind']!r}; "
                f"expected {expected_kind!r}"
            )
            raise lr.LineageReplayError(msg)
        # H2c: effective_tick.
        if ev["effective_tick"] != EXPECTED_EFFECTIVE_TICK:
            msg = (
                f"H2c effective_tick mismatch: arm={arm} hzd={hazard} seed={seed} "
                f"effective_tick={ev['effective_tick']}; expected {EXPECTED_EFFECTIVE_TICK}"
            )
            raise lr.LineageReplayError(msg)
        # H2d-aux: eligible-cell-set stability (preflight-locked).
        n_eligible_cells = int(ev["n_eligible_cells"])
        if n_eligible_cells != EXPECTED_N_ELIGIBLE_CELLS:
            msg = (
                f"H2d-aux violation: arm={arm} hzd={hazard} seed={seed} "
                f"n_eligible_cells={n_eligible_cells}; "
                f"expected {EXPECTED_N_ELIGIBLE_CELLS} (locked by preflight)"
            )
            raise lr.LineageReplayError(msg)
        # H2d: schedule conservation.
        n_cells_changed = int(ev["n_cells_changed"])
        min_before = int(ev["min_respawn_tick_before"])
        max_before = int(ev["max_respawn_tick_before"])
        min_after = int(ev["min_respawn_tick_after"])
        max_after = int(ev["max_respawn_tick_after"])
        sum_before = int(ev["sum_respawn_tick_before"])
        sum_after = int(ev["sum_respawn_tick_after"])
        eligible_cells_digest = ev["eligible_cells_digest"]
        digest_before = ev["respawn_multiset_digest_before"]
        digest_after = ev["respawn_multiset_digest_after"]
        if n_cells_changed > n_eligible_cells:
            msg = (
                f"H2d invariant violation: arm={arm} hzd={hazard} seed={seed} "
                f"n_cells_changed={n_cells_changed} > n_eligible_cells={n_eligible_cells}"
            )
            raise lr.LineageReplayError(msg)
        if arm == ARM_B_DELAY:
            expected_sum = sum_before + B_DELAY_TICKS * n_eligible_cells
            if sum_after != expected_sum:
                msg = (
                    f"H2d B-conservation sum mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"sum_after={sum_after}; expected {expected_sum} "
                    f"(= {sum_before} + {B_DELAY_TICKS} * {n_eligible_cells})"
                )
                raise lr.LineageReplayError(msg)
            if min_after != min_before + B_DELAY_TICKS:
                msg = (
                    f"H2d B-conservation min mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"min_after={min_after}; expected {min_before + B_DELAY_TICKS}"
                )
                raise lr.LineageReplayError(msg)
            if max_after != max_before + B_DELAY_TICKS:
                msg = (
                    f"H2d B-conservation max mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"max_after={max_after}; expected {max_before + B_DELAY_TICKS}"
                )
                raise lr.LineageReplayError(msg)
            # B must change the multiset (uniform shift => digest must differ).
            if digest_before == digest_after:
                msg = (
                    f"H2d B-multiset invariant: arm={arm} hzd={hazard} seed={seed} "
                    f"+25 shift produced identical multiset digest "
                    f"(arithmetic bug suspected). digest={digest_before}"
                )
                raise lr.LineageReplayError(msg)
        else:  # ARM_C_PERMUTE
            if sum_after != sum_before:
                msg = (
                    f"H2d C-conservation sum mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"sum_after={sum_after}; expected {sum_before}"
                )
                raise lr.LineageReplayError(msg)
            if min_after != min_before:
                msg = (
                    f"H2d C-conservation min mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"min_after={min_after}; expected {min_before}"
                )
                raise lr.LineageReplayError(msg)
            if max_after != max_before:
                msg = (
                    f"H2d C-conservation max mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"max_after={max_after}; expected {max_before}"
                )
                raise lr.LineageReplayError(msg)
            # C is a permutation: multiset digest MUST be preserved exactly.
            if digest_before != digest_after:
                msg = (
                    f"H2d C-multiset bug: arm={arm} hzd={hazard} seed={seed} "
                    f"permutation produced different multiset digest "
                    f"(arithmetic bug suspected)."
                )
                raise lr.LineageReplayError(msg)
        fired = True
        intervention_kind = ev["intervention_kind"]

    # Compute post_intervention_top_lineage_b50_share over ALL 5 lineages
    # (no exclusion — no lineage is killed by schedule rewrite).
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
        fired=fired,
        intervention_kind=intervention_kind,
        n_eligible_cells=n_eligible_cells,
        n_cells_changed=n_cells_changed,
        min_respawn_tick_before=min_before,
        max_respawn_tick_before=max_before,
        min_respawn_tick_after=min_after,
        max_respawn_tick_after=max_after,
        sum_respawn_tick_before=sum_before,
        sum_respawn_tick_after=sum_after,
        eligible_cells_digest=eligible_cells_digest,
        respawn_multiset_digest_before=digest_before,
        respawn_multiset_digest_after=digest_after,
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


def build_schedule_conservation(per_run: list[PerRunRow]) -> list[ScheduleConservationRow]:
    out: list[ScheduleConservationRow] = []
    for arm in ALL_ARMS:
        for hazard in EXPECTED_HAZARDS:
            bucket = [r for r in per_run if r.arm == arm and r.hazard == hazard]
            if arm == ARM_A_NULL:
                out.append(
                    ScheduleConservationRow(
                        arm=arm,
                        hazard=hazard,
                        n_runs=len(bucket),
                        mean_min_before=float("nan"),
                        mean_max_before=float("nan"),
                        mean_sum_before=float("nan"),
                        mean_min_after=float("nan"),
                        mean_max_after=float("nan"),
                        mean_sum_after=float("nan"),
                        n_runs_with_multiset_changed=0,
                        n_runs_with_eligible_cells_drift=0,
                    )
                )
                continue
            mean_min_before = statistics.mean([r.min_respawn_tick_before for r in bucket])
            mean_max_before = statistics.mean([r.max_respawn_tick_before for r in bucket])
            mean_sum_before = statistics.mean([r.sum_respawn_tick_before for r in bucket])
            mean_min_after = statistics.mean([r.min_respawn_tick_after for r in bucket])
            mean_max_after = statistics.mean([r.max_respawn_tick_after for r in bucket])
            mean_sum_after = statistics.mean([r.sum_respawn_tick_after for r in bucket])
            n_multiset_changed = sum(
                1
                for r in bucket
                if r.respawn_multiset_digest_before != r.respawn_multiset_digest_after
            )
            digests = {r.eligible_cells_digest for r in bucket}
            n_drift = max(0, len(digests) - 1)
            if n_drift > 0:
                msg = (
                    f"H2d eligible_cells_digest drift: arm={arm} hzd={hazard} "
                    f"observed {len(digests)} distinct digests across {len(bucket)} runs"
                )
                raise lr.LineageReplayError(msg)
            out.append(
                ScheduleConservationRow(
                    arm=arm,
                    hazard=hazard,
                    n_runs=len(bucket),
                    mean_min_before=mean_min_before,
                    mean_max_before=mean_max_before,
                    mean_sum_before=mean_sum_before,
                    mean_min_after=mean_min_after,
                    mean_max_after=mean_max_after,
                    mean_sum_after=mean_sum_after,
                    n_runs_with_multiset_changed=n_multiset_changed,
                    n_runs_with_eligible_cells_drift=n_drift,
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
    b8 = _share_at(per_arm, ARM_B_DELAY, 8)
    c8 = _share_at(per_arm, ARM_C_PERMUTE, 8)
    delta_b = b8 - a8
    delta_c = c8 - a8
    b_passes = delta_b <= -PRIMARY_B_REDUCTION_THRESHOLD
    c_passes = abs(delta_c) <= PRIMARY_C_TOLERANCE
    c_below_a = delta_c <= -PRIMARY_C_TOLERANCE
    c_above_a = delta_c > PRIMARY_C_TOLERANCE
    flow_necessary = b_passes and c_passes
    perturbation_disrupts = b_passes and c_below_a
    flow_not_necessary = not b_passes
    c_above_a_unmodeled = b_passes and c_above_a
    primary_fires = flow_necessary or perturbation_disrupts
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
        respawn_flow_necessary=flow_necessary,
        substrate_perturbation_disrupts=perturbation_disrupts,
        respawn_flow_not_necessary=flow_not_necessary,
        c_above_a_unmodeled_substrate_artefact=c_above_a_unmodeled,
        primary_fires=primary_fires,
    )


def evaluate_secondary_test(
    per_arm: list[PerArmPerHazardRow], primary: PrimaryTestRow
) -> SecondaryTestRow:
    a0 = _share_at(per_arm, ARM_A_NULL, 0)
    b0 = _share_at(per_arm, ARM_B_DELAY, 0)
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
    # Halt cell: C share rises strictly above A by > 0.10 while B drops.
    if primary.c_above_a_unmodeled_substrate_artefact:
        msg = (
            "C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT: c_share_h8 - a_share_h8 = "
            f"{primary.delta_c_minus_a_h8:+.3f} > {PRIMARY_C_TOLERANCE} "
            "while b_passes=True; the schedule-permutation control increased "
            "post-50 dominance above null. This is mechanistically "
            "unmotivated under the v0.44 model and indicates a substrate "
            "artefact unmodeled at pre-reg time. Halt loud."
        )
        raise lr.LineageReplayError(msg)

    if primary.respawn_flow_necessary:
        return VerdictRow(
            verdict=VERDICT_FLOW_NECESSARY,
            locked_phrase=LOCKED_FLOW_NECESSARY_PHRASE,
            respawn_flow_necessary=True,
            substrate_perturbation_disrupts=False,
            respawn_flow_not_necessary=False,
            primary_fires=True,
            secondary_fires=secondary.secondary_fires,
        )
    if primary.substrate_perturbation_disrupts:
        return VerdictRow(
            verdict=VERDICT_PERTURBATION_DISRUPTS,
            locked_phrase=LOCKED_PERTURBATION_DISRUPTS_PHRASE,
            respawn_flow_necessary=False,
            substrate_perturbation_disrupts=True,
            respawn_flow_not_necessary=False,
            primary_fires=True,
            secondary_fires=secondary.secondary_fires,
        )
    return VerdictRow(
        verdict=VERDICT_FLOW_NOT_NECESSARY,
        locked_phrase=LOCKED_FLOW_NOT_NECESSARY_PHRASE,
        respawn_flow_necessary=False,
        substrate_perturbation_disrupts=False,
        respawn_flow_not_necessary=True,
        primary_fires=False,
        secondary_fires=secondary.secondary_fires,
    )


def evaluate_auxiliary_findings(per_arm: list[PerArmPerHazardRow]) -> list[AuxiliaryFindingRow]:
    out: list[AuxiliaryFindingRow] = []
    for hazard in EXPECTED_HAZARDS:
        b_row = next(r for r in per_arm if r.arm == ARM_B_DELAY and r.hazard == hazard)
        n_excl = b_row.n_excluded_zero_post50
        ablation_threshold_exceeded = n_excl > AUXILIARY_DELAY_ABLATION_MAX_EXCLUDED
        phrase = (
            LOCKED_DELAY_ABLATES_REPRODUCTION_PHRASE.format(h=hazard, n_excluded=n_excl)
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
    "fired",
    "intervention_kind",
    "n_eligible_cells",
    "n_cells_changed",
    "min_respawn_tick_before",
    "max_respawn_tick_before",
    "min_respawn_tick_after",
    "max_respawn_tick_after",
    "sum_respawn_tick_before",
    "sum_respawn_tick_after",
    "eligible_cells_digest",
    "respawn_multiset_digest_before",
    "respawn_multiset_digest_after",
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
    "respawn_flow_necessary",
    "substrate_perturbation_disrupts",
    "respawn_flow_not_necessary",
    "c_above_a_unmodeled_substrate_artefact",
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
    "respawn_flow_necessary",
    "substrate_perturbation_disrupts",
    "respawn_flow_not_necessary",
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
SCHEDULE_CONSERVATION_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "n_runs",
    "mean_min_before",
    "mean_max_before",
    "mean_sum_before",
    "mean_min_after",
    "mean_max_after",
    "mean_sum_after",
    "n_runs_with_multiset_changed",
    "n_runs_with_eligible_cells_drift",
]


def write_outputs(
    per_run: list[PerRunRow],
    per_arm: list[PerArmPerHazardRow],
    intervention_summary: list[InterventionSummaryRow],
    primary: PrimaryTestRow,
    secondary: SecondaryTestRow,
    verdict: VerdictRow,
    auxiliary: list[AuxiliaryFindingRow],
    schedule_conservation: list[ScheduleConservationRow],
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
        "schedule_conservation": out_dir / "schedule_conservation.csv",
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
        schedule_conservation,
        paths["schedule_conservation"],
        SCHEDULE_CONSERVATION_FIELDNAMES,
    )
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_sweep_present()
    per_run = reduce_all_runs()
    print(
        f"v0.44 intervention_audit: {len(per_run)} per-run records "
        f"(3 arms x 2 hazards x 8 seeds = {EXPECTED_RUNS_TOTAL})",
        flush=True,
    )

    per_arm = aggregate_per_arm_per_hazard(per_run)
    intervention_summary = build_intervention_summary(per_arm)
    schedule_conservation = build_schedule_conservation(per_run)
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
        schedule_conservation,
    )

    print()
    print("Per-(arm, hazard) post-intervention top-lineage b50 share:")
    print(f"  {'arm':>54} {'h':>3} {'n_runs':>6} {'n_used':>6} {'mean':>8} {'median':>8}")
    for r in per_arm:
        m = "nan" if math.isnan(r.mean_share) else f"{r.mean_share:.3f}"
        med = "nan" if math.isnan(r.median_share) else f"{r.median_share:.3f}"
        print(
            f"  {r.arm:>54} {r.hazard:>3d} {r.n_runs:>6d} {r.n_runs_used:>6d} {m:>8} {med:>8}",
            flush=True,
        )

    print()
    print("Schedule conservation:")
    print(
        f"  {'arm':>54} {'h':>3} {'n':>3} "
        f"{'min_b':>6} {'max_b':>6} {'sum_b':>8} "
        f"{'min_a':>6} {'max_a':>6} {'sum_a':>8} "
        f"{'mset_chg':>8}"
    )
    for r in schedule_conservation:
        if math.isnan(r.mean_min_before):
            print(
                f"  {r.arm:>54} {r.hazard:>3d} {r.n_runs:>3d} "
                f"{'-':>6} {'-':>6} {'-':>8} {'-':>6} {'-':>6} {'-':>8} "
                f"{r.n_runs_with_multiset_changed:>8d}",
                flush=True,
            )
        else:
            print(
                f"  {r.arm:>54} {r.hazard:>3d} {r.n_runs:>3d} "
                f"{r.mean_min_before:>6.1f} {r.mean_max_before:>6.1f} "
                f"{r.mean_sum_before:>8.1f} "
                f"{r.mean_min_after:>6.1f} {r.mean_max_after:>6.1f} "
                f"{r.mean_sum_after:>8.1f} "
                f"{r.n_runs_with_multiset_changed:>8d}",
                flush=True,
            )

    print()
    print("Primary test (h=8):")
    print(
        f"  A_null={primary.a_share_h8:.3f}  "
        f"B_delay={primary.b_share_h8:.3f}  "
        f"C_permute={primary.c_share_h8:.3f}"
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
    print(f"  v0.44 verdict: {verdict.verdict}")
    print(f'    locked phrase: "{verdict.locked_phrase}"')

    print()
    print("Auxiliary findings (DELAY_ABLATES_REPRODUCTION):")
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
