"""v0.34 lineage observability reducer (post-hoc, over existing sidecars).

Reads per-run ``agent_lifetimes.csv`` + ``config.json`` + ``manifest.json``
sidecars across the v0.33 pooled hazard-axis corpus (96 runs:
tight_gradient x influx=1.0 x hazard ∈ {0, 4, 8, 12} x seeds 1..24
sourced from v0.25, v0.32, v0.33 directories), reconstructs per-agent
+ per-lineage observables, and emits four concatenated CSVs under
``runs/lineage-v0.34/``:

  - agents.csv         (one row per agent across all 96 runs)
  - lineages.csv       (one row per (run, lineage_id))
  - run_summary.csv    (one row per (arm, seed))
  - pool_summary.csv   (one row per hazard, aggregating across 24 seeds)

The reducer does NOT parse ``events.jsonl``. It does NOT consume
``trait_fingerprints.csv``. It cross-checks against the existing
per-run ``lineages.csv`` only as a soft warning (the existing
sidecar's ``founder_id`` field names "first descendant agent_id," not
"tick-0 founder," and the existing sidecar omits founders that
produced no descendants).

Halt conditions (raise LineageReplayError):
  - Required sidecar missing.
  - Non-null parent_id pointing at an absent agent.
  - Founder count mismatch (expected exactly 5 per run).
  - Non-founder lineage_id disagrees with founder-ancestor lineage_id.
  - pool_summary total_b50 mismatch against the v0.33 audit's
    pre-committed B_pool(h) anchors for h ∈ {4, 8, 12}.

Pre-reg: [[docs/experiments/fear_hunger_v0.34.md]].

Usage:
    uv run python scripts/lineage_replay.py
"""

from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


HAZARDS: tuple[int, ...] = (0, 4, 8, 12)
ARM_LABEL_FMT = "transfer-1500-hzd{}-influx-1.0"
EXPECTED_FOUNDERS = 5
B50_THRESHOLD_TICK = 50
SINGLE_LINEAGE_MAJORITY_THRESHOLD = 0.5

# Anchors from the v0.33 audit's pooled B_pool(h) — pre-reg H5.
B_POOL_ANCHORS: dict[int, int] = {4: 312, 8: 321, 12: 312}

OUT_DIR = Path("runs/lineage-v0.34")

# Stream layout: (source_version, runs_root, seeds).
STREAM_CONFIGS: tuple[tuple[str, Path, tuple[int, ...]], ...] = (
    (
        "v0.25",
        Path("runs/fear-hunger-v0.25-tight_gradient/arms"),
        tuple(range(1, 9)),
    ),
    (
        "v0.32",
        Path("runs/fear-hunger-v0.32-tight_gradient/arms"),
        tuple(range(9, 17)),
    ),
    (
        "v0.33",
        Path("runs/fear-hunger-v0.33-tight_gradient/arms"),
        tuple(range(17, 25)),
    ),
)


class LineageReplayError(Exception):
    """Halt condition raised when a v0.34 invariant is violated."""


# ---------------------------------------------------------------------------
# Output dataclasses (canonical column order matches CSV header)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    agent_id: int
    lineage_id: int
    parent_id: int | None
    is_founder: bool
    birth_tick: int | None
    birth_tick_normalized: int
    death_tick: int | None
    lifespan: int
    death_cause: str
    generation_depth: int
    offspring_count: int
    born_after_tick_50: bool
    survived_to_end: bool


@dataclass(frozen=True)
class LineageRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    lineage_id: int
    n_agents_total: int
    b50_count: int
    b50_share: float  # NaN when total_b50_in_run == 0
    max_generation_depth: int
    max_lifespan: int
    mean_lifespan: float
    total_offspring_count: int
    n_survivors_at_end: int


@dataclass(frozen=True)
class RunSummaryRow:
    source_version: str
    arm_label: str
    hazard: int
    seed: int
    total_b50: int
    top_lineage_id: int | None  # None when total_b50 == 0
    top_lineage_b50: int | None
    top_lineage_b50_share: float  # NaN when total_b50 == 0
    n_lineages_with_b50_ge_1: int
    n_lineages_alive_at_end: int


@dataclass(frozen=True)
class PoolSummaryRow:
    hazard: int
    n_runs: int
    total_b50: int
    mean_top_lineage_b50_share: float
    median_top_lineage_b50_share: float
    n_runs_single_lineage_majority: int
    n_runs_total_b50_zero: int


# ---------------------------------------------------------------------------
# Sidecar parsing
# ---------------------------------------------------------------------------


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _opt_int(s: str) -> int | None:
    return int(s) if s != "" else None


def parse_agent_lifetimes(run_dir: Path) -> list[dict]:
    """Read agent_lifetimes.csv and return raw per-agent dicts.

    Empty fields (founders' lineage_id / parent_id / birth_tick;
    survivors' death_tick / death_cause) become ``None`` / ``""``.
    """
    path = run_dir / "agent_lifetimes.csv"
    if not path.exists():
        msg = f"agent_lifetimes.csv missing under {run_dir}"
        raise LineageReplayError(msg)
    rows = _read_csv(path)
    parsed: list[dict] = []
    for row in rows:
        parsed.append(
            {
                "agent_id": int(row["agent_id"]),
                "lineage_id": _opt_int(row["lineage_id"]),
                "parent_id": _opt_int(row["parent_id"]),
                "birth_tick": _opt_int(row["birth_tick"]),
                "death_tick": _opt_int(row["death_tick"]),
                "death_cause": row["death_cause"] or "",
                "offspring_count": int(row["offspring_count"]),
            }
        )
    return parsed


def parse_config(run_dir: Path) -> dict:
    """Read config.json and return ``{seed: int, hazard_damage: int}``."""
    path = run_dir / "config.json"
    if not path.exists():
        msg = f"config.json missing under {run_dir}"
        raise LineageReplayError(msg)
    with path.open() as f:
        cfg = json.load(f)
    world = cfg.get("world", {})
    seed = world.get("seed")
    hazard = world.get("hazard_damage_default")
    if seed is None or hazard is None:
        msg = f"config.json under {run_dir} missing world.seed or world.hazard_damage_default"
        raise LineageReplayError(msg)
    return {"seed": int(seed), "hazard_damage": int(hazard)}


def parse_manifest(run_dir: Path) -> int:
    """Read manifest.json and return ``ticks_completed``."""
    path = run_dir / "manifest.json"
    if not path.exists():
        msg = f"manifest.json missing under {run_dir}"
        raise LineageReplayError(msg)
    with path.open() as f:
        manifest = json.load(f)
    ticks = manifest.get("ticks_completed")
    if ticks is None:
        msg = f"manifest.json under {run_dir} missing ticks_completed"
        raise LineageReplayError(msg)
    return int(ticks)


def parse_existing_lineages(run_dir: Path) -> dict[int, dict]:
    """Read the existing per-run lineages.csv and return
    ``{lineage_id: {founder_id, members, ...}}``. Missing file returns
    an empty dict."""
    path = run_dir / "lineages.csv"
    if not path.exists():
        return {}
    rows = _read_csv(path)
    out: dict[int, dict] = {}
    for row in rows:
        out[int(row["lineage_id"])] = {
            "first_descendant_agent_id": int(row["founder_id"]),
            "members": int(row["members"]),
            "births": int(row["births"]),
            "deaths": int(row["deaths"]),
            "extinct": int(row["extinct"]) == 1,
            "max_offspring_chain": int(row["max_offspring_chain"]),
        }
    return out


# ---------------------------------------------------------------------------
# Lineage / generation reconstruction
# ---------------------------------------------------------------------------


def assign_founder_lineages(parsed: list[dict]) -> dict[int, int]:
    """Assign lineage_id to each founder by enumeration order
    (sorted by agent_id, starting at 0). Cross-check that every
    non-founder's lineage_id matches the lineage_id of its founder
    ancestor (BFS root); mismatch raises ``LineageReplayError``.

    Returns ``{agent_id: lineage_id}`` covering all agents (founders +
    descendants).
    """
    founders_sorted = sorted(
        (row for row in parsed if row["parent_id"] is None),
        key=lambda r: r["agent_id"],
    )
    if len(founders_sorted) != EXPECTED_FOUNDERS:
        msg = (
            f"expected exactly {EXPECTED_FOUNDERS} founders "
            f"(parent_id is None), got {len(founders_sorted)}"
        )
        raise LineageReplayError(msg)

    founder_lineage: dict[int, int] = {
        founder["agent_id"]: idx for idx, founder in enumerate(founders_sorted)
    }

    by_id = {row["agent_id"]: row for row in parsed}
    out: dict[int, int] = dict(founder_lineage)

    # Walk descendants; cross-check declared lineage_id against
    # founder-ancestor lineage_id via BFS-by-parent.
    for row in parsed:
        if row["parent_id"] is None:
            continue
        # Walk up to founder.
        cursor = row
        seen: set[int] = set()
        while cursor["parent_id"] is not None:
            pid = cursor["parent_id"]
            if pid in seen:
                msg = (
                    f"cycle detected walking parent chain from "
                    f"agent_id={row['agent_id']}; revisited {pid}"
                )
                raise LineageReplayError(msg)
            seen.add(pid)
            parent = by_id.get(pid)
            if parent is None:
                msg = (
                    f"agent_id={cursor['agent_id']} has parent_id={pid} "
                    f"but no agent row exists with that id"
                )
                raise LineageReplayError(msg)
            cursor = parent
        founder_id = cursor["agent_id"]
        expected_lineage = founder_lineage[founder_id]
        if row["lineage_id"] is not None and row["lineage_id"] != expected_lineage:
            msg = (
                f"agent_id={row['agent_id']} declared lineage_id="
                f"{row['lineage_id']} but founder-ancestor "
                f"agent_id={founder_id} resolves to lineage_id="
                f"{expected_lineage}"
            )
            raise LineageReplayError(msg)
        out[row["agent_id"]] = expected_lineage
    return out


def compute_generation_depths(parsed: list[dict]) -> dict[int, int]:
    """BFS over parent_id → child_id edges. Founders are depth 0.
    Broken parent reference (non-null parent_id with no agent row)
    raises ``LineageReplayError``."""
    by_id = {row["agent_id"]: row for row in parsed}
    children_of: dict[int, list[int]] = {}
    for row in parsed:
        pid = row["parent_id"]
        if pid is not None:
            if pid not in by_id:
                msg = (
                    f"agent_id={row['agent_id']} has parent_id={pid} "
                    f"but no agent row exists with that id "
                    f"(LineageReplayError: broken parent reference)"
                )
                raise LineageReplayError(msg)
            children_of.setdefault(pid, []).append(row["agent_id"])

    depth: dict[int, int] = {}
    queue: deque[int] = deque()
    for row in parsed:
        if row["parent_id"] is None:
            depth[row["agent_id"]] = 0
            queue.append(row["agent_id"])
    while queue:
        node = queue.popleft()
        for child in children_of.get(node, ()):
            if child in depth:
                continue
            depth[child] = depth[node] + 1
            queue.append(child)

    missing = [row["agent_id"] for row in parsed if row["agent_id"] not in depth]
    if missing:
        msg = (
            f"agents not reached from any founder via parent chain: {missing} "
            f"(LineageReplayError: orphan agents)"
        )
        raise LineageReplayError(msg)
    return depth


# ---------------------------------------------------------------------------
# Per-agent assembly
# ---------------------------------------------------------------------------


def build_agent_rows(
    parsed: list[dict],
    lineage_by_agent: dict[int, int],
    depth_by_agent: dict[int, int],
    n_ticks: int,
    *,
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
) -> list[AgentRow]:
    """Assemble the canonical AgentRow list for one run."""
    rows: list[AgentRow] = []
    for raw in parsed:
        is_founder = raw["parent_id"] is None
        birth_tick = raw["birth_tick"]
        birth_tick_normalized = 0 if birth_tick is None else birth_tick
        death_tick = raw["death_tick"]
        survived_to_end = death_tick is None
        lifespan = (
            n_ticks - birth_tick_normalized
            if survived_to_end
            else death_tick - birth_tick_normalized
        )
        rows.append(
            AgentRow(
                source_version=source_version,
                arm_label=arm_label,
                hazard=hazard,
                seed=seed,
                agent_id=raw["agent_id"],
                lineage_id=lineage_by_agent[raw["agent_id"]],
                parent_id=raw["parent_id"],
                is_founder=is_founder,
                birth_tick=birth_tick,
                birth_tick_normalized=birth_tick_normalized,
                death_tick=death_tick,
                lifespan=lifespan,
                death_cause=raw["death_cause"],
                generation_depth=depth_by_agent[raw["agent_id"]],
                offspring_count=raw["offspring_count"],
                born_after_tick_50=birth_tick_normalized > B50_THRESHOLD_TICK,
                survived_to_end=survived_to_end,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Lineage / run / pool aggregation
# ---------------------------------------------------------------------------


def aggregate_lineages(
    agent_rows: list[AgentRow],
    *,
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
) -> list[LineageRow]:
    """Aggregate per-lineage observables for one run."""
    by_lineage: dict[int, list[AgentRow]] = {}
    for row in agent_rows:
        by_lineage.setdefault(row.lineage_id, []).append(row)
    total_b50_in_run = sum(1 for row in agent_rows if row.born_after_tick_50)
    out: list[LineageRow] = []
    for lineage_id in sorted(by_lineage):
        members = by_lineage[lineage_id]
        b50_count = sum(1 for m in members if m.born_after_tick_50)
        b50_share = b50_count / total_b50_in_run if total_b50_in_run > 0 else float("nan")
        lifespans = [m.lifespan for m in members]
        out.append(
            LineageRow(
                source_version=source_version,
                arm_label=arm_label,
                hazard=hazard,
                seed=seed,
                lineage_id=lineage_id,
                n_agents_total=len(members),
                b50_count=b50_count,
                b50_share=b50_share,
                max_generation_depth=max(m.generation_depth for m in members),
                max_lifespan=max(lifespans),
                mean_lifespan=statistics.mean(lifespans),
                total_offspring_count=sum(m.offspring_count for m in members),
                n_survivors_at_end=sum(1 for m in members if m.survived_to_end),
            )
        )
    return out


def summarise_run(
    lineage_rows: list[LineageRow],
    *,
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
) -> RunSummaryRow:
    """Compute the per-run summary observables."""
    total_b50 = sum(lr.b50_count for lr in lineage_rows)
    n_lineages_with_b50_ge_1 = sum(1 for lr in lineage_rows if lr.b50_count >= 1)
    n_lineages_alive_at_end = sum(1 for lr in lineage_rows if lr.n_survivors_at_end >= 1)
    if total_b50 == 0:
        return RunSummaryRow(
            source_version=source_version,
            arm_label=arm_label,
            hazard=hazard,
            seed=seed,
            total_b50=0,
            top_lineage_id=None,
            top_lineage_b50=None,
            top_lineage_b50_share=float("nan"),
            n_lineages_with_b50_ge_1=0,
            n_lineages_alive_at_end=n_lineages_alive_at_end,
        )
    top = max(lineage_rows, key=lambda lr: (lr.b50_count, -lr.lineage_id))
    return RunSummaryRow(
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
        total_b50=total_b50,
        top_lineage_id=top.lineage_id,
        top_lineage_b50=top.b50_count,
        top_lineage_b50_share=top.b50_count / total_b50,
        n_lineages_with_b50_ge_1=n_lineages_with_b50_ge_1,
        n_lineages_alive_at_end=n_lineages_alive_at_end,
    )


def aggregate_pool(run_summaries: list[RunSummaryRow]) -> list[PoolSummaryRow]:
    """Aggregate per-run summaries to one row per hazard."""
    by_hazard: dict[int, list[RunSummaryRow]] = {h: [] for h in HAZARDS}
    for rs in run_summaries:
        if rs.hazard in by_hazard:
            by_hazard[rs.hazard].append(rs)
    out: list[PoolSummaryRow] = []
    for hazard in HAZARDS:
        runs = by_hazard[hazard]
        n_runs = len(runs)
        total_b50 = sum(r.total_b50 for r in runs)
        non_nan_shares = [
            r.top_lineage_b50_share for r in runs if not math.isnan(r.top_lineage_b50_share)
        ]
        n_runs_total_b50_zero = sum(1 for r in runs if r.total_b50 == 0)
        n_runs_single_lineage_majority = sum(
            1
            for r in runs
            if not math.isnan(r.top_lineage_b50_share)
            and r.top_lineage_b50_share >= SINGLE_LINEAGE_MAJORITY_THRESHOLD
        )
        if non_nan_shares:
            mean_share = statistics.mean(non_nan_shares)
            median_share = statistics.median(non_nan_shares)
        else:
            mean_share = float("nan")
            median_share = float("nan")
        out.append(
            PoolSummaryRow(
                hazard=hazard,
                n_runs=n_runs,
                total_b50=total_b50,
                mean_top_lineage_b50_share=mean_share,
                median_top_lineage_b50_share=median_share,
                n_runs_single_lineage_majority=n_runs_single_lineage_majority,
                n_runs_total_b50_zero=n_runs_total_b50_zero,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Cross-checks
# ---------------------------------------------------------------------------


def cross_check_existing_lineages(
    our_lineages: list[LineageRow],
    existing: dict[int, dict],
    run_label: str,
    warn_stream=sys.stderr,
) -> None:
    """Soft check: existing per-run ``lineages.csv``'s ``members``
    field (descendants only) should equal our reconstructed
    ``n_agents_total - 1`` for each lineage the existing sidecar
    covers. Mismatch logs a warning; does NOT halt."""
    by_id = {lr.lineage_id: lr for lr in our_lineages}
    for lineage_id, existing_row in existing.items():
        ours = by_id.get(lineage_id)
        if ours is None:
            print(
                f"  WARN [{run_label}] lineage_id={lineage_id} present in "
                f"existing lineages.csv but absent from reconstruction",
                file=warn_stream,
            )
            continue
        ours_descendants = ours.n_agents_total - 1
        if ours_descendants != existing_row["members"]:
            print(
                f"  WARN [{run_label}] lineage_id={lineage_id} "
                f"reconstructed descendants={ours_descendants} but existing "
                f"members={existing_row['members']}",
                file=warn_stream,
            )


def cross_check_b50_anchors(pool_rows: list[PoolSummaryRow]) -> None:
    """Halt if pool_summary total_b50 disagrees with the v0.33 audit
    pre-committed B_pool(h) anchor for h ∈ {4, 8, 12}."""
    by_hazard = {pr.hazard: pr for pr in pool_rows}
    for hazard, expected in B_POOL_ANCHORS.items():
        actual = by_hazard[hazard].total_b50
        if actual != expected:
            msg = (
                f"H5 anchor mismatch at h={hazard}: "
                f"pool_summary.total_b50={actual} but v0.33 audit's "
                f"pre-committed B_pool({hazard})={expected}. "
                f"Reducer's b50 derivation has drifted; halt."
            )
            raise LineageReplayError(msg)


# ---------------------------------------------------------------------------
# Per-run pipeline
# ---------------------------------------------------------------------------


def process_run(
    source_version: str,
    arm_label: str,
    hazard: int,
    seed: int,
    run_dir: Path,
    *,
    warn_stream=sys.stderr,
) -> tuple[list[AgentRow], list[LineageRow], RunSummaryRow]:
    """Run the full reducer pipeline on one (source_version, arm,
    seed) directory, returning (agent_rows, lineage_rows,
    run_summary)."""
    parsed = parse_agent_lifetimes(run_dir)
    cfg = parse_config(run_dir)
    if cfg["seed"] != seed:
        msg = f"seed mismatch under {run_dir}: config.json={cfg['seed']} but expected {seed}"
        raise LineageReplayError(msg)
    if cfg["hazard_damage"] != hazard:
        msg = (
            f"hazard mismatch under {run_dir}: "
            f"config.json hazard_damage_default={cfg['hazard_damage']} but "
            f"expected {hazard}"
        )
        raise LineageReplayError(msg)
    n_ticks = parse_manifest(run_dir)

    lineage_by_agent = assign_founder_lineages(parsed)
    depth_by_agent = compute_generation_depths(parsed)
    agent_rows = build_agent_rows(
        parsed,
        lineage_by_agent,
        depth_by_agent,
        n_ticks,
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
    )
    lineage_rows = aggregate_lineages(
        agent_rows,
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
    )
    run_summary = summarise_run(
        lineage_rows,
        source_version=source_version,
        arm_label=arm_label,
        hazard=hazard,
        seed=seed,
    )
    existing = parse_existing_lineages(run_dir)
    cross_check_existing_lineages(
        lineage_rows,
        existing,
        run_label=f"{source_version}/{arm_label}/seed-{seed}",
        warn_stream=warn_stream,
    )
    return agent_rows, lineage_rows, run_summary


# ---------------------------------------------------------------------------
# Discovery / driver
# ---------------------------------------------------------------------------


def discover_runs() -> list[tuple[str, str, int, int, Path]]:
    """Iterate the 96 (source_version, arm_label, hazard, seed,
    run_dir) tuples in deterministic sorted order: source_version →
    hazard → seed."""
    out: list[tuple[str, str, int, int, Path]] = []
    for source_version, runs_root, seeds in STREAM_CONFIGS:
        for hazard in HAZARDS:
            arm_label = ARM_LABEL_FMT.format(hazard)
            for seed in seeds:
                run_dir = runs_root / arm_label / f"seed-{seed}"
                out.append((source_version, arm_label, hazard, seed, run_dir))
    return out


# ---------------------------------------------------------------------------
# CSV writing
# ---------------------------------------------------------------------------


def _format_float(value: float) -> str:
    if isinstance(value, float) and math.isnan(value):
        return ""
    return repr(value) if isinstance(value, float) else str(value)


def _format_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return _format_float(value)
    return str(value)


def _write_dataclass_csv(rows: Iterable, path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for row in rows:
            d = asdict(row)
            writer.writerow([_format_value(d[name]) for name in fieldnames])


AGENT_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "agent_id",
    "lineage_id",
    "parent_id",
    "is_founder",
    "birth_tick",
    "birth_tick_normalized",
    "death_tick",
    "lifespan",
    "death_cause",
    "generation_depth",
    "offspring_count",
    "born_after_tick_50",
    "survived_to_end",
]
LINEAGE_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "lineage_id",
    "n_agents_total",
    "b50_count",
    "b50_share",
    "max_generation_depth",
    "max_lifespan",
    "mean_lifespan",
    "total_offspring_count",
    "n_survivors_at_end",
]
RUN_SUMMARY_FIELDNAMES: list[str] = [
    "source_version",
    "arm_label",
    "hazard",
    "seed",
    "total_b50",
    "top_lineage_id",
    "top_lineage_b50",
    "top_lineage_b50_share",
    "n_lineages_with_b50_ge_1",
    "n_lineages_alive_at_end",
]
POOL_SUMMARY_FIELDNAMES: list[str] = [
    "hazard",
    "n_runs",
    "total_b50",
    "mean_top_lineage_b50_share",
    "median_top_lineage_b50_share",
    "n_runs_single_lineage_majority",
    "n_runs_total_b50_zero",
]


def write_outputs(
    agent_rows: list[AgentRow],
    lineage_rows: list[LineageRow],
    run_summaries: list[RunSummaryRow],
    pool_summaries: list[PoolSummaryRow],
    out_dir: Path = OUT_DIR,
) -> dict[str, Path]:
    """Write all four CSVs under ``out_dir`` and return the path map."""
    paths = {
        "agents": out_dir / "agents.csv",
        "lineages": out_dir / "lineages.csv",
        "run_summary": out_dir / "run_summary.csv",
        "pool_summary": out_dir / "pool_summary.csv",
    }
    _write_dataclass_csv(agent_rows, paths["agents"], AGENT_FIELDNAMES)
    _write_dataclass_csv(lineage_rows, paths["lineages"], LINEAGE_FIELDNAMES)
    _write_dataclass_csv(run_summaries, paths["run_summary"], RUN_SUMMARY_FIELDNAMES)
    _write_dataclass_csv(pool_summaries, paths["pool_summary"], POOL_SUMMARY_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    runs = discover_runs()
    print(f"v0.34 lineage_replay: {len(runs)} runs discovered", flush=True)

    all_agent_rows: list[AgentRow] = []
    all_lineage_rows: list[LineageRow] = []
    run_summaries: list[RunSummaryRow] = []
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, lineage_rows, run_summary = process_run(
            source_version, arm_label, hazard, seed, run_dir
        )
        all_agent_rows.extend(agent_rows)
        all_lineage_rows.extend(lineage_rows)
        run_summaries.append(run_summary)

    pool_summaries = aggregate_pool(run_summaries)
    cross_check_b50_anchors(pool_summaries)

    paths = write_outputs(all_agent_rows, all_lineage_rows, run_summaries, pool_summaries)

    print()
    print("Pool summary (one row per hazard):")
    print(
        f"  {'hazard':>6} {'n_runs':>6} {'total_b50':>9} "
        f"{'mean_share':>10} {'median_share':>12} "
        f"{'n_majority':>10} {'n_b50=0':>8}"
    )
    for ps in pool_summaries:
        mean_share = ps.mean_top_lineage_b50_share
        median_share = ps.median_top_lineage_b50_share
        ms = "nan" if math.isnan(mean_share) else f"{mean_share:.3f}"
        meds = "nan" if math.isnan(median_share) else f"{median_share:.3f}"
        print(
            f"  {ps.hazard:>6d} {ps.n_runs:>6d} {ps.total_b50:>9d} "
            f"{ms:>10} {meds:>12} "
            f"{ps.n_runs_single_lineage_majority:>10d} {ps.n_runs_total_b50_zero:>8d}"
        )
    print()
    for label, path in paths.items():
        print(f"  wrote {label:>12}  -> {path}")


if __name__ == "__main__":
    main()
