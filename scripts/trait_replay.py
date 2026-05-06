"""v0.36 founder-trait heritability replay (post-hoc, third reducer).

Tests whether the founder's trait endowment predicts whether their
lineage becomes the post-50 b50 winner, and whether the predictor
strengthens monotonically with hazard. Imports v0.34 helpers via
``importlib.util`` (no modification). Re-anchors against v0.34's
``run_summary.csv:top_lineage_id`` AND v0.35's
``pre_post_dominance.csv:eventual_top_lineage_id`` (both must match
byte-identical for every (source_version, arm_label, seed); drift
halts).

Pre-reg: [[docs/experiments/fear_hunger_v0.36.md]].

Primary trait set (locked, 3): reproduction_drive, metabolic_rate,
sensor_radius. Expected signs: +1 / -1 / +1. Secondary traits (10)
are reported descriptively only and CANNOT fire any verdict.

Effect-size discipline: per-trait Cohen's d (signed) using pooled
sample std. Magnitude threshold |d(h=12)| >= 0.4. Strengthening
spread |d(h=12)| - |d(h=0)| >= 0.2 with weak monotone non-decreasing.
Sign-alignment via EXPECTED_SIGN.

Three-way verdict (mutually exclusive):
  - H5 TRAIT-LINKED-AND-STRENGTHENING: any primary trait crosses
    threshold AND strengthens AND sign-aligned at h=12.
  - H6 TRAIT-LINKED-FLAT: any primary trait crosses threshold but
    no aligned-sign trait strengthens (includes opposite-sign-only).
  - H7 TRAIT-NEUTRAL: no primary trait crosses threshold.

Outputs four CSVs under ``runs/lineage-v0.36/``:
  - founder_traits.csv               (per-run x founder, 480 rows)
  - winner_vs_nonwinner_by_hazard.csv (per-(hazard x trait), 52 rows)
  - primary_strengthening.csv        (per primary trait, 3 rows)
  - trait_verdict.csv                (single row)

Usage:
    uv run python scripts/trait_replay.py
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
# Import v0.34 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _spec is not None
assert _spec.loader is not None
lr = importlib.util.module_from_spec(_spec)
sys.modules["lineage_replay"] = lr
_spec.loader.exec_module(lr)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg before code)
# ---------------------------------------------------------------------------


PRIMARY_TRAITS: tuple[str, ...] = (
    "reproduction_drive",
    "metabolic_rate",
    "sensor_radius",
)
EXPECTED_SIGN: dict[str, int] = {
    "reproduction_drive": +1,
    "metabolic_rate": -1,
    "sensor_radius": +1,
}
SECONDARY_TRAITS: tuple[str, ...] = (
    "hunger_pain_sensitivity",
    "injury_pain_sensitivity",
    "fear_sensitivity",
    "pleasure_sensitivity",
    "novelty_drive",
    "uncertainty_aversion",
    "pain_tolerance",
    "risk_tolerance",
    "memory_strength",
    "memory_decay_rate",
)
# Output ordering: primary first (so verdict-bearing traits surface up top),
# then secondary in fingerprint-file column order.
ALL_TRAITS: tuple[str, ...] = PRIMARY_TRAITS + SECONDARY_TRAITS

ABS_D_THRESHOLD: float = 0.4
STRENGTHENING_SPREAD_THRESHOLD: float = 0.2

V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_PRE_POST_DOMINANCE: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
OUT_DIR: Path = Path("runs/lineage-v0.36")

VERDICT_LINKED_STRENGTHENING = "H5_TRAIT_LINKED_AND_STRENGTHENING"
VERDICT_LINKED_FLAT = "H6_TRAIT_LINKED_FLAT"
VERDICT_NEUTRAL = "H7_TRAIT_NEUTRAL"

LOCKED_H5_PHRASE = (
    "Founder-trait signature predicts post-50 dominance on the v0.34 corpus, "
    "with effect strengthening monotonically with hazard. Correlational; not "
    "a mechanism declaration."
)
LOCKED_H6_PHRASE = (
    "Founder-trait signature differs between winners and non-winners at h=12 "
    "but does not strengthen with hazard with the expected sign; the "
    "winning-lineage prediction is not consistent with hazard-amplified "
    "heritable selection on this corpus."
)
LOCKED_H7_PHRASE = (
    "No founder-trait predictor of post-50 dominance clears the locked "
    "effect-size threshold on this corpus; founder-trait endowment does not "
    "detectably predict winning lineage identity at this scale."
)

CLASSIFICATION_ALIGNED_STRENGTHENING = "aligned-and-strengthening"
CLASSIFICATION_ALIGNED_FLAT = "aligned-flat"
CLASSIFICATION_OPPOSITE_STRENGTHENING = "opposite-sign-strengthening"
CLASSIFICATION_OPPOSITE_FLAT = "opposite-sign-flat"
CLASSIFICATION_BELOW_THRESHOLD = "below-threshold"


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FounderTraitRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    lineage_id: int
    agent_id: int
    is_winner: bool
    hunger_pain_sensitivity: float
    injury_pain_sensitivity: float
    fear_sensitivity: float
    pleasure_sensitivity: float
    reproduction_drive: float
    novelty_drive: float
    uncertainty_aversion: float
    pain_tolerance: float
    risk_tolerance: float
    memory_strength: float
    memory_decay_rate: float
    sensor_radius: float
    metabolic_rate: float


@dataclass(frozen=True)
class WinnerVsNonwinnerRow:
    hazard: int
    trait: str
    is_primary: bool
    expected_sign: int  # 0 for secondary
    n_winner: int
    n_nonwinner: int
    mean_winner: float
    mean_nonwinner: float
    pooled_std: float
    signed_d: float
    abs_d: float
    sign_aligned: bool  # always False for secondary; only meaningful for primary


@dataclass(frozen=True)
class PrimaryStrengtheningRow:
    trait: str
    expected_sign: int
    abs_d_h0: float
    abs_d_h4: float
    abs_d_h8: float
    abs_d_h12: float
    signed_d_h12: float
    monotone_non_decreasing: bool
    spread: float
    crosses_threshold_at_h12: bool
    strengthens: bool
    sign_aligned_at_h12: bool
    classification: (
        str  # aligned-and-strengthening / aligned-flat / opposite-sign-* / below-threshold
    )


@dataclass(frozen=True)
class VerdictRow:
    verdict: str
    locked_phrase: str
    firing_traits: str  # comma-separated; "" if none


# ---------------------------------------------------------------------------
# Sidecar parsing
# ---------------------------------------------------------------------------


def parse_trait_fingerprints(run_dir: Path) -> dict[int, dict[str, float]]:
    """Read trait_fingerprints.csv and return {agent_id: {trait: value}}.

    All 13 trait columns parsed as float (sensor_radius is integer in
    practice; cast preserves it as float for d computation). Empty
    cells halt.
    """
    path = run_dir / "trait_fingerprints.csv"
    if not path.exists():
        msg = f"trait_fingerprints.csv missing under {run_dir}"
        raise lr.LineageReplayError(msg)
    out: dict[int, dict[str, float]] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = set(ALL_TRAITS) - set(reader.fieldnames or ())
        if missing:
            msg = f"trait_fingerprints.csv under {run_dir} missing columns: {sorted(missing)}"
            raise lr.LineageReplayError(msg)
        for row in reader:
            try:
                agent_id = int(row["agent_id"])
            except (KeyError, ValueError) as e:
                msg = f"trait_fingerprints.csv under {run_dir} bad agent_id row: {row}"
                raise lr.LineageReplayError(msg) from e
            traits: dict[str, float] = {}
            for trait in ALL_TRAITS:
                raw = row[trait]
                if raw == "":
                    msg = (
                        f"trait_fingerprints.csv under {run_dir} agent_id="
                        f"{agent_id} has empty value for trait {trait!r}"
                    )
                    raise lr.LineageReplayError(msg)
                traits[trait] = float(raw)
            out[agent_id] = traits
    return out


# ---------------------------------------------------------------------------
# Anchor loaders / cross-checks
# ---------------------------------------------------------------------------


def load_v0_34_top_lineage_anchors(
    path: Path = V0_34_RUN_SUMMARY,
) -> dict[tuple[str, str, int], int | None]:
    """Load v0.34 top_lineage_id keyed by (source_version, arm_label, seed).
    Empty top_lineage_id (total_b50 == 0) -> None."""
    if not path.exists():
        msg = f"v0.34 run_summary.csv missing at {path} (re-anchor unavailable)"
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], int | None] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            top_id = int(row["top_lineage_id"]) if row["top_lineage_id"] != "" else None
            out[key] = top_id
    return out


def load_v0_35_eventual_top_anchors(
    path: Path = V0_35_PRE_POST_DOMINANCE,
) -> dict[tuple[str, str, int], int | None]:
    """Load v0.35 eventual_top_lineage_id keyed by (source_version, arm_label,
    seed). Empty -> None."""
    if not path.exists():
        msg = (
            f"v0.35 pre_post_dominance.csv missing at {path} "
            f"(re-anchor unavailable; run scripts/lineage_survival_replay.py first)"
        )
        raise lr.LineageReplayError(msg)
    out: dict[tuple[str, str, int], int | None] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["source_version"], row["arm_label"], int(row["seed"]))
            raw = row["eventual_top_lineage_id"]
            out[key] = int(raw) if raw != "" else None
    return out


def cross_check_double_anchor(
    derived_top_by_run: dict[tuple[str, str, int], int | None],
    v34_anchors: dict[tuple[str, str, int], int | None],
    v35_anchors: dict[tuple[str, str, int], int | None],
) -> None:
    """Halt if derived top_lineage_id differs from v0.34 OR v0.35 anchors."""
    for key, derived in derived_top_by_run.items():
        if key not in v34_anchors:
            msg = f"v0.34 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if key not in v35_anchors:
            msg = f"v0.35 anchor missing for {key}"
            raise lr.LineageReplayError(msg)
        if derived != v34_anchors[key]:
            msg = (
                f"H2a v0.34 re-anchor mismatch at {key}: "
                f"derived={derived} != v0.34 top_lineage_id={v34_anchors[key]}"
            )
            raise lr.LineageReplayError(msg)
        if derived != v35_anchors[key]:
            msg = (
                f"H2b v0.35 re-anchor mismatch at {key}: "
                f"derived={derived} != v0.35 eventual_top_lineage_id="
                f"{v35_anchors[key]}"
            )
            raise lr.LineageReplayError(msg)


def reassert_b_pool_anchors() -> None:
    expected = {4: 312, 8: 321, 12: 312}
    if expected != lr.B_POOL_ANCHORS:
        msg = (
            f"H1b anchor mismatch: lr.B_POOL_ANCHORS={lr.B_POOL_ANCHORS} "
            f"but v0.34 pre-reg locks {expected}; halt."
        )
        raise lr.LineageReplayError(msg)
    if lr.EXPECTED_FOUNDERS != 5:
        msg = f"EXPECTED_FOUNDERS drift: {lr.EXPECTED_FOUNDERS} != 5"
        raise lr.LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run founder-trait extraction
# ---------------------------------------------------------------------------


def derive_top_lineage_id(agent_rows: list) -> int | None:
    """Mirror v0.34's summarise_run top_lineage_id selection: lineage with
    max b50_count; lowest lineage_id wins ties; None when total_b50 == 0."""
    by_lineage: dict[int, int] = {}
    for row in agent_rows:
        if row.born_after_tick_50:
            by_lineage[row.lineage_id] = by_lineage.get(row.lineage_id, 0) + 1
    if not by_lineage:
        return None
    total_b50 = sum(by_lineage.values())
    if total_b50 == 0:
        return None
    best_id: int | None = None
    best_count = -1
    for lineage_id in sorted(by_lineage):
        count = by_lineage[lineage_id]
        if count > best_count:
            best_id = lineage_id
            best_count = count
    return best_id


def build_founder_trait_rows(
    agent_rows: list,
    trait_lookup: dict[int, dict[str, float]],
    top_lineage_id: int | None,
    *,
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
) -> list[FounderTraitRow]:
    """Emit one FounderTraitRow per founder for the run."""
    founders = sorted(
        (a for a in agent_rows if a.is_founder),
        key=lambda a: a.lineage_id,
    )
    if len(founders) != lr.EXPECTED_FOUNDERS:
        msg = (
            f"H2c founder-count mismatch under "
            f"{source_version}/{arm_label}/seed-{seed}: "
            f"{len(founders)} != {lr.EXPECTED_FOUNDERS}"
        )
        raise lr.LineageReplayError(msg)
    out: list[FounderTraitRow] = []
    for founder in founders:
        traits = trait_lookup.get(founder.agent_id)
        if traits is None:
            msg = (
                f"H2c founder agent_id={founder.agent_id} "
                f"(lineage_id={founder.lineage_id}) missing from "
                f"trait_fingerprints.csv under "
                f"{source_version}/{arm_label}/seed-{seed}"
            )
            raise lr.LineageReplayError(msg)
        is_winner = top_lineage_id is not None and founder.lineage_id == top_lineage_id
        out.append(
            FounderTraitRow(
                source_version=source_version,
                arm_label=arm_label,
                hazard=hazard,
                seed=seed,
                lineage_id=founder.lineage_id,
                agent_id=founder.agent_id,
                is_winner=is_winner,
                **{trait: traits[trait] for trait in ALL_TRAITS},
            )
        )
    return out


# ---------------------------------------------------------------------------
# Cohen's d computation
# ---------------------------------------------------------------------------


def compute_cohens_d(
    winner_values: list[float],
    nonwinner_values: list[float],
) -> tuple[float, float, float, float, float]:
    """Return (mean_winner, mean_nonwinner, pooled_std, signed_d, abs_d).

    Pooled sample std uses n-1 denominators per group (Cohen's d, sample-
    variance form). NaN for d when pooled_std == 0.
    """
    n_w = len(winner_values)
    n_nw = len(nonwinner_values)
    if n_w == 0 or n_nw == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    mean_w = statistics.mean(winner_values)
    mean_nw = statistics.mean(nonwinner_values)
    if n_w < 2 or n_nw < 2:
        # Variance undefined for a single sample; treat as zero-variance group.
        var_w = 0.0 if n_w < 2 else statistics.variance(winner_values)
        var_nw = 0.0 if n_nw < 2 else statistics.variance(nonwinner_values)
    else:
        var_w = statistics.variance(winner_values)
        var_nw = statistics.variance(nonwinner_values)
    df = n_w + n_nw - 2
    if df <= 0:
        return mean_w, mean_nw, float("nan"), float("nan"), float("nan")
    pooled_var = ((n_w - 1) * var_w + (n_nw - 1) * var_nw) / df
    pooled_std = math.sqrt(pooled_var) if pooled_var >= 0 else float("nan")
    if pooled_std == 0 or math.isnan(pooled_std):
        return mean_w, mean_nw, pooled_std, float("nan"), float("nan")
    signed_d = (mean_w - mean_nw) / pooled_std
    return mean_w, mean_nw, pooled_std, signed_d, abs(signed_d)


# ---------------------------------------------------------------------------
# Per-(hazard x trait) reduction
# ---------------------------------------------------------------------------


def aggregate_winner_vs_nonwinner(
    founder_rows: list[FounderTraitRow],
) -> list[WinnerVsNonwinnerRow]:
    """Compute Cohen's d per (hazard x trait) for ALL traits (primary +
    secondary)."""
    by_hazard: dict[int, list[FounderTraitRow]] = {h: [] for h in lr.HAZARDS}
    for row in founder_rows:
        if row.hazard in by_hazard:
            by_hazard[row.hazard].append(row)
    out: list[WinnerVsNonwinnerRow] = []
    for hazard in lr.HAZARDS:
        rows = by_hazard[hazard]
        for trait in ALL_TRAITS:
            winner_vals = [getattr(r, trait) for r in rows if r.is_winner]
            nonwinner_vals = [getattr(r, trait) for r in rows if not r.is_winner]
            mean_w, mean_nw, pooled_std, signed_d, abs_d = compute_cohens_d(
                winner_vals, nonwinner_vals
            )
            is_primary = trait in PRIMARY_TRAITS
            expected_sign = EXPECTED_SIGN.get(trait, 0)
            sign_aligned = False
            if is_primary and not math.isnan(signed_d):
                sign_aligned = (signed_d > 0 and expected_sign > 0) or (
                    signed_d < 0 and expected_sign < 0
                )
            out.append(
                WinnerVsNonwinnerRow(
                    hazard=hazard,
                    trait=trait,
                    is_primary=is_primary,
                    expected_sign=expected_sign,
                    n_winner=len(winner_vals),
                    n_nonwinner=len(nonwinner_vals),
                    mean_winner=mean_w,
                    mean_nonwinner=mean_nw,
                    pooled_std=pooled_std,
                    signed_d=signed_d,
                    abs_d=abs_d,
                    sign_aligned=sign_aligned,
                )
            )
    return out


# ---------------------------------------------------------------------------
# Per-primary-trait strengthening + classification
# ---------------------------------------------------------------------------


def is_weak_monotone_non_decreasing(values: list[float]) -> bool:
    return all(values[i] <= values[i + 1] for i in range(len(values) - 1))


def classify_primary(
    abs_d_by_h: dict[int, float],
    signed_d_h12: float,
    expected_sign: int,
) -> tuple[bool, float, bool, bool, bool, str]:
    """Return (monotone_non_decreasing, spread, crosses_threshold_at_h12,
    strengthens, sign_aligned_at_h12, classification)."""
    abs_seq = [abs_d_by_h[h] for h in lr.HAZARDS]
    if any(math.isnan(v) for v in abs_seq):
        return (
            False,
            float("nan"),
            False,
            False,
            False,
            CLASSIFICATION_BELOW_THRESHOLD,
        )
    monotone = is_weak_monotone_non_decreasing(abs_seq)
    spread = abs_seq[-1] - abs_seq[0]
    crosses = abs_seq[-1] >= ABS_D_THRESHOLD
    strengthens = monotone and spread >= STRENGTHENING_SPREAD_THRESHOLD
    if math.isnan(signed_d_h12):
        sign_aligned = False
    else:
        sign_aligned = (signed_d_h12 > 0 and expected_sign > 0) or (
            signed_d_h12 < 0 and expected_sign < 0
        )
    if not crosses:
        classification = CLASSIFICATION_BELOW_THRESHOLD
    elif sign_aligned and strengthens:
        classification = CLASSIFICATION_ALIGNED_STRENGTHENING
    elif sign_aligned and not strengthens:
        classification = CLASSIFICATION_ALIGNED_FLAT
    elif (not sign_aligned) and strengthens:
        classification = CLASSIFICATION_OPPOSITE_STRENGTHENING
    else:
        classification = CLASSIFICATION_OPPOSITE_FLAT
    return monotone, spread, crosses, strengthens, sign_aligned, classification


def aggregate_primary_strengthening(
    wvn_rows: list[WinnerVsNonwinnerRow],
) -> list[PrimaryStrengtheningRow]:
    """One row per primary trait with strengthening + classification."""
    by_trait_hazard: dict[tuple[str, int], WinnerVsNonwinnerRow] = {
        (r.trait, r.hazard): r for r in wvn_rows
    }
    out: list[PrimaryStrengtheningRow] = []
    for trait in PRIMARY_TRAITS:
        abs_d_by_h = {h: by_trait_hazard[(trait, h)].abs_d for h in lr.HAZARDS}
        signed_d_h12 = by_trait_hazard[(trait, 12)].signed_d
        expected_sign = EXPECTED_SIGN[trait]
        (
            monotone,
            spread,
            crosses,
            strengthens,
            sign_aligned,
            classification,
        ) = classify_primary(abs_d_by_h, signed_d_h12, expected_sign)
        out.append(
            PrimaryStrengtheningRow(
                trait=trait,
                expected_sign=expected_sign,
                abs_d_h0=abs_d_by_h[0],
                abs_d_h4=abs_d_by_h[4],
                abs_d_h8=abs_d_by_h[8],
                abs_d_h12=abs_d_by_h[12],
                signed_d_h12=signed_d_h12,
                monotone_non_decreasing=monotone,
                spread=spread,
                crosses_threshold_at_h12=crosses,
                strengthens=strengthens,
                sign_aligned_at_h12=sign_aligned,
                classification=classification,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Three-way verdict
# ---------------------------------------------------------------------------


def evaluate_verdict(
    strengthening_rows: list[PrimaryStrengtheningRow],
) -> tuple[str, str, list[str]]:
    """Return (verdict, locked_phrase, firing_traits)."""
    aligned_strengthening = [
        r.trait
        for r in strengthening_rows
        if r.classification == CLASSIFICATION_ALIGNED_STRENGTHENING
    ]
    if aligned_strengthening:
        return VERDICT_LINKED_STRENGTHENING, LOCKED_H5_PHRASE, aligned_strengthening
    above_threshold = [r.trait for r in strengthening_rows if r.crosses_threshold_at_h12]
    if above_threshold:
        return VERDICT_LINKED_FLAT, LOCKED_H6_PHRASE, above_threshold
    return VERDICT_NEUTRAL, LOCKED_H7_PHRASE, []


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


FOUNDER_TRAIT_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "lineage_id",
    "agent_id",
    "is_winner",
    *ALL_TRAITS,
]
WINNER_VS_NONWINNER_FIELDNAMES: list[str] = [
    "hazard",
    "trait",
    "is_primary",
    "expected_sign",
    "n_winner",
    "n_nonwinner",
    "mean_winner",
    "mean_nonwinner",
    "pooled_std",
    "signed_d",
    "abs_d",
    "sign_aligned",
]
PRIMARY_STRENGTHENING_FIELDNAMES: list[str] = [
    "trait",
    "expected_sign",
    "abs_d_h0",
    "abs_d_h4",
    "abs_d_h8",
    "abs_d_h12",
    "signed_d_h12",
    "monotone_non_decreasing",
    "spread",
    "crosses_threshold_at_h12",
    "strengthens",
    "sign_aligned_at_h12",
    "classification",
]
VERDICT_FIELDNAMES: list[str] = ["verdict", "locked_phrase", "firing_traits"]


def write_outputs(
    founder_rows: list[FounderTraitRow],
    wvn_rows: list[WinnerVsNonwinnerRow],
    strengthening_rows: list[PrimaryStrengtheningRow],
    verdict_row: VerdictRow,
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    paths = {
        "founder_traits": out_dir / "founder_traits.csv",
        "winner_vs_nonwinner_by_hazard": out_dir / "winner_vs_nonwinner_by_hazard.csv",
        "primary_strengthening": out_dir / "primary_strengthening.csv",
        "trait_verdict": out_dir / "trait_verdict.csv",
    }
    _write_dataclass_csv(founder_rows, paths["founder_traits"], FOUNDER_TRAIT_FIELDNAMES)
    _write_dataclass_csv(
        wvn_rows,
        paths["winner_vs_nonwinner_by_hazard"],
        WINNER_VS_NONWINNER_FIELDNAMES,
    )
    _write_dataclass_csv(
        strengthening_rows,
        paths["primary_strengthening"],
        PRIMARY_STRENGTHENING_FIELDNAMES,
    )
    _write_dataclass_csv([verdict_row], paths["trait_verdict"], VERDICT_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Per-run loader (reuses v0.34 helpers; no modification)
# ---------------------------------------------------------------------------


def load_run(
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
    run_dir: Path,
) -> tuple[list, dict[int, dict[str, float]], int | None]:
    """Reuse v0.34 helpers; return (agent_rows, trait_lookup,
    derived_top_lineage_id)."""
    parsed = lr.parse_agent_lifetimes(run_dir)
    cfg = lr.parse_config(run_dir)
    if cfg["seed"] != seed:
        msg = f"seed mismatch under {run_dir}: config.json={cfg['seed']} but expected {seed}"
        raise lr.LineageReplayError(msg)
    if cfg["hazard_damage"] != hazard:
        msg = (
            f"hazard mismatch under {run_dir}: "
            f"config.json hazard_damage_default={cfg['hazard_damage']} but "
            f"expected {hazard}"
        )
        raise lr.LineageReplayError(msg)
    n_ticks = lr.parse_manifest(run_dir)
    lineage_by_agent = lr.assign_founder_lineages(parsed)
    depth_by_agent = lr.compute_generation_depths(parsed)
    agent_rows = lr.build_agent_rows(
        parsed,
        lineage_by_agent,
        depth_by_agent,
        n_ticks,
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
    )
    trait_lookup = parse_trait_fingerprints(run_dir)
    derived_top = derive_top_lineage_id(agent_rows)
    return agent_rows, trait_lookup, derived_top


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    reassert_b_pool_anchors()
    runs = lr.discover_runs()
    print(f"v0.36 trait_replay: {len(runs)} runs discovered", flush=True)

    v34_anchors = load_v0_34_top_lineage_anchors()
    v35_anchors = load_v0_35_eventual_top_anchors()
    print(
        f"  loaded {len(v34_anchors)} v0.34 anchors, {len(v35_anchors)} v0.35 anchors",
        flush=True,
    )

    all_founder_rows: list[FounderTraitRow] = []
    derived_top_by_run: dict[tuple[str, str, int], int | None] = {}
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, trait_lookup, derived_top = load_run(
            source_version, arm_label, hazard, seed, run_dir
        )
        derived_top_by_run[(source_version, arm_label, seed)] = derived_top
        founder_rows = build_founder_trait_rows(
            agent_rows,
            trait_lookup,
            derived_top,
            source_version=source_version,
            arm_label=arm_label,
            hazard=hazard,
            seed=seed,
        )
        all_founder_rows.extend(founder_rows)

    cross_check_double_anchor(derived_top_by_run, v34_anchors, v35_anchors)

    wvn_rows = aggregate_winner_vs_nonwinner(all_founder_rows)
    strengthening_rows = aggregate_primary_strengthening(wvn_rows)
    verdict, phrase, firing = evaluate_verdict(strengthening_rows)
    verdict_row = VerdictRow(
        verdict=verdict,
        locked_phrase=phrase,
        firing_traits=",".join(firing),
    )

    paths = write_outputs(all_founder_rows, wvn_rows, strengthening_rows, verdict_row)

    print()
    print("Primary trait strengthening:")
    print(
        f"  {'trait':>22} {'sign':>4} "
        f"{'|d|h0':>6} {'|d|h4':>6} {'|d|h8':>6} {'|d|h12':>7} "
        f"{'signed_d12':>11} {'mono':>5} {'spread':>7} "
        f"{'thr':>4} {'aligned':>8} {'classification':>30}"
    )
    for r in strengthening_rows:
        print(
            f"  {r.trait:>22} {r.expected_sign:>+4d} "
            f"{r.abs_d_h0:>6.3f} {r.abs_d_h4:>6.3f} {r.abs_d_h8:>6.3f} "
            f"{r.abs_d_h12:>7.3f} {r.signed_d_h12:>+11.3f} "
            f"{r.monotone_non_decreasing!s:>5} {r.spread:>7.3f} "
            f"{r.crosses_threshold_at_h12!s:>4} "
            f"{r.sign_aligned_at_h12!s:>8} {r.classification:>30}"
        )

    print()
    print(f"  v0.36 verdict: {verdict}")
    if firing:
        print(f"    firing traits: {', '.join(firing)}")
    print(f'    locked phrase: "{phrase}"')

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>30}  -> {path}")


if __name__ == "__main__":
    main()
