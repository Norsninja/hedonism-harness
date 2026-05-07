"""v0.42 intervention audit: post-intervention top-lineage b50 share.

Tests the v0.42 mechanism necessity question on the 48-run intervention
corpus (3 arms x 2 hazards x 8 seeds):

  Primary:   B_kill_leader at h=8 reduces post_intervention_top_lineage_b50_share
             by >= 0.15 below A_null AND C_kill_smnonleader stays within
             +/- 0.10 of A_null.
  Secondary: B-vs-A reduction is larger at h=8 than at h=0
             (descriptive context only; does not fire verdict).

Verdict (locked, mutually exclusive):
  MECHANISM_NECESSITY_SUPPORTED   iff primary fires.
  MECHANISM_GENERAL_DISRUPTION    iff B drops AND C also drops by >= 0.10.
  MECHANISM_NOT_NECESSARY         iff B does not drop by >= 0.15.

Reads (per-arm-per-seed):
  - runs/fear-hunger-v0.42-tight_gradient/arms/<arm>/seed-<n>/events.jsonl
    for AgentBorn (post-50 births), LineageKilledByIntervention (target
    lineage_id and role), AgentDied(cause=INTERVENTION) (paired-deaths
    invariant H2d).

Halt invariants (locked):
  - H2a (run count): 48 runs on disk.
  - H2b (intervention-fire count per arm): A_null=0; B=1 leader-role per
    run; C=0 or 1 smnonleader-role per run.
  - H2c (effective_tick): every fired summary has effective_tick=51.
  - H2d (intervention conservation): per fired summary, count of paired
    AgentDied(cause=INTERVENTION) at effective_tick equals n_killed.
  - H2e (regression byte-identity): NOT enforced here; it lives in
    [[tests/test_world_intervention_hook.py]]. The audit assumes the
    sweep was produced by the v0.42 chamber driver.
  - C_RISES_ABOVE_A_GUARD: if C share rises strictly above A by > 0.10,
    halt loud (substrate artefact unmodeled).

Pre-reg: [[docs/experiments/fear_hunger_v0.42.md]].

Outputs eight CSVs under ``runs/lineage-v0.42/``:
  - per_run.csv             (48 rows)
  - per_arm_per_hazard.csv  (6 rows: 3 arms x 2 hazards)
  - intervention_summary.csv (6 rows)
  - primary_test.csv         (1 row)
  - secondary_test.csv       (1 row)
  - verdict.csv              (1 row)
  - c_control_availability.csv (1 row)

Usage:
    uv run python scripts/v0_42_intervention_audit.py
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
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(41, 49))  # 41..48
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds

# Locked thresholds (item 1 of v0.42 sign-off)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Arm labels (mirror V0_42_INTERVENTION_ARMS)
ARM_A_NULL: str = "A_null"
ARM_B_KILL_LEADER: str = "B_kill_leader"
ARM_C_KILL_SMNONLEADER: str = "C_kill_smnonleader"

ALL_ARMS: tuple[str, ...] = (ARM_A_NULL, ARM_B_KILL_LEADER, ARM_C_KILL_SMNONLEADER)

# Intervention-kind strings (one per arm)
KIND_NULL: str = "null"
KIND_KILL_LEADER: str = "kill_tick50_leader"
KIND_KILL_SMNONLEADER: str = "kill_size_matched_nonleader"

# Lineage role strings (per LineageKilledByIntervention)
ROLE_LEADER: str = "leader"
ROLE_SMNONLEADER: str = "size_matched_nonleader"

# Verdict labels
VERDICT_NECESSITY = "MECHANISM_NECESSITY_SUPPORTED"
VERDICT_DISRUPTION = "MECHANISM_GENERAL_DISRUPTION"
VERDICT_NOT_NECESSARY = "MECHANISM_NOT_NECESSARY"

LOCKED_NECESSITY_PHRASE = (
    "Hard-killing the tick-50 leader lineage at the tick-50/tick-51 boundary "
    "materially disrupts the post-50 dominance pattern at h=8: the surviving "
    "four lineages do not reconstitute concentration of comparable share. The "
    "size-matched non-leader control does not produce the same disruption. "
    "Under the tested substrate, the tick-50 leader's identity is necessary "
    "for the v0.34..v0.41 dominance pattern. v0.42 does not declare a "
    "specific mechanism (reproductive priority, spatial position, energy "
    "stockpile, founder traits, or local food control); refinement "
    "interventions in v0.43+ are required. Necessity is established at one "
    "hazard level (h=8) on one seed band (41..48); cross-stream calibration "
    "of this finding is reserved for v0.43+. Sufficiency is NOT tested."
)
LOCKED_DISRUPTION_PHRASE = (
    "Hard-killing the tick-50 leader lineage disrupts post-50 dominance at "
    "h=8, but a size-matched non-leader removal produces a comparable "
    "disruption. The post-50 dominance pattern is size-shock-sensitive, not "
    "leader-identity-specific. The v0.34..v0.41 leader-advantage framing "
    "names a correlate but not a mechanism. v0.43 candidate: finer-grained "
    "control sweep (kill smaller non-leaders; spread across size buckets) "
    "to test whether any large-lineage shock disrupts the pattern "
    "equivalently, or whether there is a graded size-effect. Mechanism "
    "remains unidentified at the leader-identity level."
)
LOCKED_NOT_NECESSARY_PHRASE = (
    "Hard-killing the tick-50 leader lineage does not materially disrupt the "
    "post-50 dominance pattern at h=8. A surviving lineage reconstitutes "
    "concentration of comparable share. The tick-50 leader's identity is "
    "not necessary under the tested substrate; post-50 dominance is a "
    "property of the chamber + population dynamics, not of the specific "
    "tick-50 leader lineage. v0.34..v0.41's leader-advantage correlation "
    "reflects which lineage HAPPENED to be ahead at tick 50, not a causal "
    "lever the leader holds. v0.43 candidate: pivot to substrate-level "
    "interventions (resource concentration shock, hazard relocation) rather "
    "than lineage-level interventions."
)

RUNS_ROOT: Path = Path("runs")
SWEEP_ROOT: Path = RUNS_ROOT / "fear-hunger-v0.42-tight_gradient" / "arms"
OUT_DIR: Path = RUNS_ROOT / "lineage-v0.42"


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerRunRow:
    arm: str
    hazard: int
    seed: int
    fired: bool
    lineage_id: int | None
    lineage_role: str
    n_killed: int
    control_unavailable: bool
    total_post_50_births_among_survivors: int
    top_lineage_post50_births: int
    post_intervention_top_lineage_b50_share: float


@dataclass(frozen=True)
class PerArmPerHazardRow:
    arm: str
    hazard: int
    n_runs: int
    n_runs_used: int
    n_excluded_zero_post50: int
    n_control_unavailable: int
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
    primary_fires: bool
    secondary_fires: bool


@dataclass(frozen=True)
class CControlAvailabilityRow:
    n_runs_total_c: int
    n_control_unavailable: int
    availability_rate: float


# ---------------------------------------------------------------------------
# Sweep discovery
# ---------------------------------------------------------------------------


_ARM_DIRS: dict[str, dict[int, str]] = {
    ARM_A_NULL: {
        0: "v042-A_null-hzd0-influx-1.0",
        8: "v042-A_null-hzd8-influx-1.0",
    },
    ARM_B_KILL_LEADER: {
        0: "v042-B_kill_leader-hzd0-influx-1.0",
        8: "v042-B_kill_leader-hzd8-influx-1.0",
    },
    ARM_C_KILL_SMNONLEADER: {
        0: "v042-C_kill_smnonleader-hzd0-influx-1.0",
        8: "v042-C_kill_smnonleader-hzd8-influx-1.0",
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
            f"v0.42 sweep incomplete: {len(missing)} events.jsonl missing. "
            f"First missing: {missing[0]}"
        )
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run reduction
# ---------------------------------------------------------------------------


def _read_events_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _reduce_one_run(arm: str, hazard: int, seed: int) -> PerRunRow:  # noqa: PLR0912, PLR0915
    """Read events.jsonl for one (arm, hazard, seed), apply H2 invariants,
    and return one PerRunRow.

    H2b/H2c/H2d invariants are checked here:
      A_null arms: 0 LineageKilledByIntervention events.
      B/C arms:    0 or 1 events with the expected lineage_role.
                   If 1, effective_tick must == EXPECTED_EFFECTIVE_TICK
                   AND count of AgentDied(cause=INTERVENTION) at that tick
                   must == n_killed.
    """
    events = _read_events_jsonl(_events_path(arm, hazard, seed))

    summaries = [e for e in events if e["type"] == "LineageKilledByIntervention"]

    if arm == ARM_A_NULL:
        if summaries:
            msg = (
                f"H2b violation: A_null arm {arm} hzd={hazard} seed={seed} "
                f"emitted {len(summaries)} LineageKilledByIntervention events; expected 0"
            )
            raise lr.LineageReplayError(msg)
        fired = False
        lineage_id: int | None = None
        lineage_role = "none"
        n_killed = 0
        control_unavailable = False
        killed_lineage_ids: set[int] = set()
    else:
        if len(summaries) > 1:
            msg = (
                f"H2b violation: arm={arm} hzd={hazard} seed={seed} emitted "
                f"{len(summaries)} LineageKilledByIntervention events; expected 0 or 1"
            )
            raise lr.LineageReplayError(msg)
        if not summaries:
            # control_unavailable allowed for C only.
            if arm == ARM_B_KILL_LEADER:
                msg = (
                    f"H2b violation: arm={arm} hzd={hazard} seed={seed} did not fire "
                    f"the leader-kill intervention; expected exactly 1 firing"
                )
                raise lr.LineageReplayError(msg)
            fired = False
            lineage_id = None
            lineage_role = "none"
            n_killed = 0
            control_unavailable = True
            killed_lineage_ids = set()
        else:
            summary = summaries[0]
            ev = summary["event"]
            expected_role = ROLE_LEADER if arm == ARM_B_KILL_LEADER else ROLE_SMNONLEADER
            if ev["lineage_role"] != expected_role:
                msg = (
                    f"H2b role mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"summary.lineage_role={ev['lineage_role']!r}; expected {expected_role!r}"
                )
                raise lr.LineageReplayError(msg)
            if ev["effective_tick"] != EXPECTED_EFFECTIVE_TICK:
                msg = (
                    f"H2c effective_tick mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"effective_tick={ev['effective_tick']}; expected "
                    f"{EXPECTED_EFFECTIVE_TICK}"
                )
                raise lr.LineageReplayError(msg)
            # H2d: count AgentDied(cause=INTERVENTION) at effective_tick.
            n_intervention_deaths = sum(
                1
                for e in events
                if e["type"] == "AgentDied"
                and e["tick"] == EXPECTED_EFFECTIVE_TICK
                and e["event"]["cause"] == "INTERVENTION"
            )
            if n_intervention_deaths != ev["n_killed"]:
                msg = (
                    f"H2d conservation mismatch: arm={arm} hzd={hazard} seed={seed} "
                    f"n_killed={ev['n_killed']} but observed "
                    f"{n_intervention_deaths} AgentDied(INTERVENTION) at tick "
                    f"{EXPECTED_EFFECTIVE_TICK}"
                )
                raise lr.LineageReplayError(msg)
            fired = True
            lineage_id = ev["lineage_id"]
            lineage_role = ev["lineage_role"]
            n_killed = ev["n_killed"]
            control_unavailable = False
            killed_lineage_ids = {lineage_id}

    # Compute post_intervention_top_lineage_b50_share.
    # "Post-intervention" = exclude killed lineages.
    # "Top-lineage" = surviving lineage with most post-50 births.
    # "Share" = top / sum_over_surviving.
    post50_births_by_lineage: dict[int, int] = {}
    for e in events:
        if e["type"] != "AgentBorn":
            continue
        ev = e["event"]
        if ev["tick"] <= 50:
            continue
        lineage = ev["lineage_id"]
        if lineage in killed_lineage_ids:
            continue
        post50_births_by_lineage[lineage] = post50_births_by_lineage.get(lineage, 0) + 1

    total_post50 = sum(post50_births_by_lineage.values())
    if total_post50 == 0:
        # Run is excluded from arm aggregation; share is NaN.
        top_births = 0
        share = float("nan")
    else:
        top_lineage = max(
            post50_births_by_lineage,
            key=lambda lid: (post50_births_by_lineage[lid], -lid),  # tie-break: lowest lid wins
        )
        top_births = post50_births_by_lineage[top_lineage]
        share = top_births / total_post50

    return PerRunRow(
        arm=arm,
        hazard=hazard,
        seed=seed,
        fired=fired,
        lineage_id=lineage_id,
        lineage_role=lineage_role,
        n_killed=n_killed,
        control_unavailable=control_unavailable,
        total_post_50_births_among_survivors=total_post50,
        top_lineage_post50_births=top_births,
        post_intervention_top_lineage_b50_share=share,
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
            n_control_unavail = sum(1 for r in bucket if r.control_unavailable)
            usable = [
                r.post_intervention_top_lineage_b50_share
                for r in bucket
                if not math.isnan(r.post_intervention_top_lineage_b50_share)
                and not r.control_unavailable
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
                    n_control_unavailable=n_control_unavail,
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
    b8 = _share_at(per_arm, ARM_B_KILL_LEADER, 8)
    c8 = _share_at(per_arm, ARM_C_KILL_SMNONLEADER, 8)
    delta_b = b8 - a8
    delta_c = c8 - a8
    b_passes = delta_b <= -PRIMARY_B_REDUCTION_THRESHOLD
    c_passes = abs(delta_c) <= PRIMARY_C_TOLERANCE
    return PrimaryTestRow(
        a_share_h8=a8,
        b_share_h8=b8,
        c_share_h8=c8,
        delta_b_minus_a_h8=delta_b,
        delta_c_minus_a_h8=delta_c,
        b_passes=b_passes,
        c_passes=c_passes,
        primary_fires=b_passes and c_passes,
    )


def evaluate_secondary_test(
    per_arm: list[PerArmPerHazardRow], primary: PrimaryTestRow
) -> SecondaryTestRow:
    a0 = _share_at(per_arm, ARM_A_NULL, 0)
    b0 = _share_at(per_arm, ARM_B_KILL_LEADER, 0)
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
    # Guard against substrate artefact: C share rises strictly above A by > 0.10.
    if primary.delta_c_minus_a_h8 > PRIMARY_C_TOLERANCE:
        msg = (
            "C-rises-above-A guard: c_share_h8 - a_share_h8 = "
            f"{primary.delta_c_minus_a_h8:+.3f} > {PRIMARY_C_TOLERANCE}; "
            "post-50 dominance INCREASES under size-matched non-leader removal. "
            "This is mechanistically unmotivated under the v0.42 model and "
            "indicates a substrate artefact unmodeled at pre-reg time. Halt loud."
        )
        raise lr.LineageReplayError(msg)

    if primary.primary_fires:
        return VerdictRow(
            verdict=VERDICT_NECESSITY,
            locked_phrase=LOCKED_NECESSITY_PHRASE,
            primary_fires=True,
            secondary_fires=secondary.secondary_fires,
        )

    # primary did not fire. Two non-firing pathways:
    #   B did not drop by >= 0.15  -> MECHANISM_NOT_NECESSARY
    #   B dropped AND C also dropped (within tolerance violated by a downward C)
    #     -> MECHANISM_GENERAL_DISRUPTION
    if not primary.b_passes:
        return VerdictRow(
            verdict=VERDICT_NOT_NECESSARY,
            locked_phrase=LOCKED_NOT_NECESSARY_PHRASE,
            primary_fires=False,
            secondary_fires=secondary.secondary_fires,
        )
    # b_passes but c_passes failed AND not c-rises-above (already guarded).
    # That means C dropped by > 0.10 below A.
    return VerdictRow(
        verdict=VERDICT_DISRUPTION,
        locked_phrase=LOCKED_DISRUPTION_PHRASE,
        primary_fires=False,
        secondary_fires=secondary.secondary_fires,
    )


def build_c_control_availability(per_run: list[PerRunRow]) -> CControlAvailabilityRow:
    c_runs = [r for r in per_run if r.arm == ARM_C_KILL_SMNONLEADER]
    n_total = len(c_runs)
    n_unavail = sum(1 for r in c_runs if r.control_unavailable)
    rate = (n_total - n_unavail) / n_total if n_total else float("nan")
    return CControlAvailabilityRow(
        n_runs_total_c=n_total,
        n_control_unavailable=n_unavail,
        availability_rate=rate,
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


PER_RUN_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "seed",
    "fired",
    "lineage_id",
    "lineage_role",
    "n_killed",
    "control_unavailable",
    "total_post_50_births_among_survivors",
    "top_lineage_post50_births",
    "post_intervention_top_lineage_b50_share",
]
PER_ARM_PER_HAZARD_FIELDNAMES: list[str] = [
    "arm",
    "hazard",
    "n_runs",
    "n_runs_used",
    "n_excluded_zero_post50",
    "n_control_unavailable",
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
VERDICT_FIELDNAMES: list[str] = ["verdict", "locked_phrase", "primary_fires", "secondary_fires"]
C_CONTROL_FIELDNAMES: list[str] = ["n_runs_total_c", "n_control_unavailable", "availability_rate"]


def write_outputs(
    per_run: list[PerRunRow],
    per_arm: list[PerArmPerHazardRow],
    intervention_summary: list[InterventionSummaryRow],
    primary: PrimaryTestRow,
    secondary: SecondaryTestRow,
    verdict: VerdictRow,
    c_avail: CControlAvailabilityRow,
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "per_run": out_dir / "per_run.csv",
        "per_arm_per_hazard": out_dir / "per_arm_per_hazard.csv",
        "intervention_summary": out_dir / "intervention_summary.csv",
        "primary_test": out_dir / "primary_test.csv",
        "secondary_test": out_dir / "secondary_test.csv",
        "verdict": out_dir / "verdict.csv",
        "c_control_availability": out_dir / "c_control_availability.csv",
    }
    _write_dataclass_csv(per_run, paths["per_run"], PER_RUN_FIELDNAMES)
    _write_dataclass_csv(per_arm, paths["per_arm_per_hazard"], PER_ARM_PER_HAZARD_FIELDNAMES)
    _write_dataclass_csv(
        intervention_summary, paths["intervention_summary"], INTERVENTION_SUMMARY_FIELDNAMES
    )
    _write_dataclass_csv([primary], paths["primary_test"], PRIMARY_FIELDNAMES)
    _write_dataclass_csv([secondary], paths["secondary_test"], SECONDARY_FIELDNAMES)
    _write_dataclass_csv([verdict], paths["verdict"], VERDICT_FIELDNAMES)
    _write_dataclass_csv([c_avail], paths["c_control_availability"], C_CONTROL_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    assert_sweep_present()
    per_run = reduce_all_runs()
    print(
        f"v0.42 intervention_audit: {len(per_run)} per-run records "
        f"(3 arms x 2 hazards x 8 seeds = {EXPECTED_RUNS_TOTAL})",
        flush=True,
    )

    per_arm = aggregate_per_arm_per_hazard(per_run)
    intervention_summary = build_intervention_summary(per_arm)
    primary = evaluate_primary_test(per_arm)
    secondary = evaluate_secondary_test(per_arm, primary)
    verdict = evaluate_verdict(primary, secondary)
    c_avail = build_c_control_availability(per_run)

    paths = write_outputs(
        per_run, per_arm, intervention_summary, primary, secondary, verdict, c_avail
    )

    print()
    print("Per-(arm, hazard) post-intervention top-lineage b50 share:")
    print(f"  {'arm':>20} {'h':>3} {'n_runs':>6} {'n_used':>6} {'mean':>8} {'median':>8}")
    for r in per_arm:
        m = "nan" if math.isnan(r.mean_share) else f"{r.mean_share:.3f}"
        med = "nan" if math.isnan(r.median_share) else f"{r.median_share:.3f}"
        print(
            f"  {r.arm:>20} {r.hazard:>3d} {r.n_runs:>6d} {r.n_runs_used:>6d} {m:>8} {med:>8}",
            flush=True,
        )

    print()
    print("Primary test (h=8):")
    print(
        f"  A_null={primary.a_share_h8:.3f}  "
        f"B_kill_leader={primary.b_share_h8:.3f}  "
        f"C_kill_smnonleader={primary.c_share_h8:.3f}"
    )
    print(
        f"  delta(B-A)={primary.delta_b_minus_a_h8:+.3f}  "
        f"delta(C-A)={primary.delta_c_minus_a_h8:+.3f}"
    )
    print(
        f"  b_passes={primary.b_passes}  c_passes={primary.c_passes}  "
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
    print(f"  v0.42 verdict: {verdict.verdict}")
    print(f'    locked phrase: "{verdict.locked_phrase}"')

    print()
    print("C control availability:")
    print(
        f"  total_C_runs={c_avail.n_runs_total_c}  "
        f"control_unavailable={c_avail.n_control_unavailable}  "
        f"availability_rate={c_avail.availability_rate:.3f}"
    )

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>22}  -> {path}")


if __name__ == "__main__":
    main()
