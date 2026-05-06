"""v0.35 lineage_survival_replay extension over the v0.39 fresh seed stream.

Thin wrapper that imports v0.34 + v0.35 helpers via ``importlib.util``
and runs them on a v0.39-only STREAM_CONFIGS (seeds 25..32 at
``runs/fear-hunger-v0.39-tight_gradient/arms/``), writing to a SEPARATE
output directory ``runs/lineage-v0.35-fresh/``.

This script does NOT modify [[scripts/lineage_replay.py]] or
[[scripts/lineage_survival_replay.py]] in any way. It does NOT
regenerate the sealed 96-row outputs at ``runs/lineage-v0.35/``.

The fresh outputs are anchor sources for
[[scripts/v0_39_leader_advantage_fresh_replay.py]] (the v0.39 reducer)
and exist alongside the sealed outputs.

Differences from v0.35's main():
  - STREAM_CONFIGS_FRESH includes only the v0.39 stream.
  - v0.34 anchor source is the FRESH v0.34 output
    (``runs/lineage-v0.34-fresh/run_summary.csv``), NOT the sealed
    96-row v0.34 output. The fresh extension reducer must run before
    this script (writes the fresh anchor file).
  - reassert_b_pool_anchors is still called: that asserts the v0.34
    LOCKED constants are byte-identical (a static check on imported
    values, not a corpus check); valid in either context.
  - aggregate_pruning_summary is computed for the fresh stream (4 rows).
  - Output dir: runs/lineage-v0.35-fresh/.

Pre-reg: [[docs/experiments/fear_hunger_v0.39.md]] section "Mechanism"
subsection "Extension reducers".

Usage:
    uv run python scripts/lineage_survival_replay_v0_39_extension.py
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import v0.34 + v0.35 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_LS_PATH = Path(__file__).parent / "lineage_survival_replay.py"

_lr_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _lr_spec is not None
assert _lr_spec.loader is not None
lr = importlib.util.module_from_spec(_lr_spec)
sys.modules["lineage_replay"] = lr
_lr_spec.loader.exec_module(lr)

_ls_spec = importlib.util.spec_from_file_location("lineage_survival_replay", _LS_PATH)
assert _ls_spec is not None
assert _ls_spec.loader is not None
ls = importlib.util.module_from_spec(_ls_spec)
sys.modules["lineage_survival_replay"] = ls
_ls_spec.loader.exec_module(ls)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg)
# ---------------------------------------------------------------------------


FRESH_SOURCE_VERSION: str = "v0.39"
FRESH_RUNS_ROOT: Path = Path("runs/fear-hunger-v0.39-tight_gradient/arms")
FRESH_SEEDS: tuple[int, ...] = tuple(range(25, 33))

V0_34_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
OUT_DIR_FRESH: Path = Path("runs/lineage-v0.35-fresh")


STREAM_CONFIGS_FRESH: tuple[tuple[str, Path, tuple[int, ...]], ...] = (
    (FRESH_SOURCE_VERSION, FRESH_RUNS_ROOT, FRESH_SEEDS),
)


# ---------------------------------------------------------------------------
# Discovery (mirrors lr.discover_runs but over STREAM_CONFIGS_FRESH)
# ---------------------------------------------------------------------------


def discover_fresh_runs() -> list[tuple[str, str, int, int, Path]]:
    """Iterate the 32 (source_version, arm_label, hazard, seed,
    run_dir) tuples in deterministic sorted order: hazard -> seed."""
    out: list[tuple[str, str, int, int, Path]] = []
    for source_version, runs_root, seeds in STREAM_CONFIGS_FRESH:
        for hazard in lr.HAZARDS:
            arm_label = lr.ARM_LABEL_FMT.format(hazard)
            for seed in seeds:
                run_dir = runs_root / arm_label / f"seed-{seed}"
                out.append((source_version, arm_label, hazard, seed, run_dir))
    return out


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    ls.reassert_b_pool_anchors()
    runs = discover_fresh_runs()
    expected_n_runs = len(lr.HAZARDS) * len(FRESH_SEEDS)
    if len(runs) != expected_n_runs:
        msg = (
            f"discover_fresh_runs returned {len(runs)} runs but "
            f"expected {expected_n_runs} "
            f"(={len(lr.HAZARDS)} hazards x {len(FRESH_SEEDS)} seeds)"
        )
        raise lr.LineageReplayError(msg)
    print(
        f"v0.35 lineage_survival_replay (v0.39 fresh extension): {len(runs)} fresh runs discovered",
        flush=True,
    )

    # Anchor source is the FRESH v0.34 extension output, NOT the sealed
    # 96-row file at runs/lineage-v0.34/run_summary.csv.
    anchors = ls.load_v0_34_anchors(path=V0_34_FRESH_RUN_SUMMARY)
    print(
        f"  loaded {len(anchors)} fresh-stream v0.34 anchors from {V0_34_FRESH_RUN_SUMMARY}",
        flush=True,
    )

    all_timeline: list = []
    all_extinction: list = []
    all_dominance: list = []
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, n_ticks = ls.load_run_agents(source_version, arm_label, hazard, seed, run_dir)
        timeline_rows, extinction_rows, dominance_row = ls.summarise_run_survival(
            agent_rows,
            n_ticks,
            source_version=source_version,
            arm_label=arm_label,
            hazard=hazard,
            seed=seed,
        )
        all_timeline.extend(timeline_rows)
        all_extinction.extend(extinction_rows)
        all_dominance.append(dominance_row)

    ls.cross_check_top_lineage_b50_against_v0_34(all_dominance, anchors)

    pruning_summary = ls.aggregate_pruning_summary(all_timeline, all_extinction, all_dominance)

    paths = ls.write_outputs(
        all_timeline,
        all_extinction,
        all_dominance,
        pruning_summary,
        out_dir=OUT_DIR_FRESH,
    )

    print()
    print("Fresh-stream pruning summary (one row per hazard):")
    print(f"  {'hazard':>6} {'n_runs':>6} {'fa_t50':>8} {'wad_rate':>9} {'mean_post50':>11}")
    for ps in pruning_summary:
        wad = ps.winner_already_dominant_at_tick_50_rate
        wad_disp = "nan" if math.isnan(wad) else f"{wad:.3f}"
        print(
            f"  {ps.hazard:>6d} {ps.n_runs:>6d} "
            f"{ps.mean_founders_alive_at_t50:>8.3f} "
            f"{wad_disp:>9} "
            f"{ps.mean_n_lineages_with_post50_birth:>11.3f}",
            flush=True,
        )

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
