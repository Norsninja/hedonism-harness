"""v0.34 lineage_replay extension over the v0.41 second fresh seed stream.

Thin wrapper that imports v0.34's lineage_replay helpers via
``importlib.util`` and runs them on a v0.41-only STREAM_CONFIGS
(seeds 33..40 at ``runs/fear-hunger-v0.41-tight_gradient/arms/``),
writing to a SEPARATE output directory ``runs/lineage-v0.34-v0_41-fresh/``.

This script does NOT modify [[scripts/lineage_replay.py]] or
[[scripts/lineage_replay_v0_39_extension.py]] in any way. It does NOT
regenerate the sealed 96-row outputs at ``runs/lineage-v0.34/`` or the
sealed 32-row outputs at ``runs/lineage-v0.34-fresh/``. The v0.41 fresh
outputs are anchor sources for
[[scripts/v0_41_stream_classification_audit.py]] (the v0.41 audit) and
exist alongside the prior sealed outputs.

Differences from v0.34's main():
  - STREAM_CONFIGS_V041_FRESH includes only the v0.41 stream.
  - cross_check_b50_anchors is NOT called: B_POOL_ANCHORS lock the
    OLD corpus only ({4: 312, 8: 321, 12: 312}); the v0.41 stream's
    per-hazard B_POOL is an emergent observable, not an anchor.
  - Per-run invariants (founder count, hazard match, seed match) are
    inherited from process_run via the imported helpers.
  - Output dir: runs/lineage-v0.34-v0_41-fresh/.

Pre-reg: [[docs/experiments/fear_hunger_v0.41.md]] section "Mechanism"
subsection "v0.34 extension".

Usage:
    uv run python scripts/lineage_replay_v0_41_extension.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import v0.34 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"

_lr_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
assert _lr_spec is not None
assert _lr_spec.loader is not None
lr = importlib.util.module_from_spec(_lr_spec)
sys.modules["lineage_replay"] = lr
_lr_spec.loader.exec_module(lr)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg)
# ---------------------------------------------------------------------------


FRESH_SOURCE_VERSION: str = "v0.41"
FRESH_RUNS_ROOT: Path = Path("runs/fear-hunger-v0.41-tight_gradient/arms")
FRESH_SEEDS: tuple[int, ...] = tuple(range(33, 41))

OUT_DIR_FRESH: Path = Path("runs/lineage-v0.34-v0_41-fresh")


# v0.41-only STREAM_CONFIGS, structurally identical to lr.STREAM_CONFIGS
# entry shape but covering only the v0.41 fresh stream.
STREAM_CONFIGS_V041_FRESH: tuple[tuple[str, Path, tuple[int, ...]], ...] = (
    (FRESH_SOURCE_VERSION, FRESH_RUNS_ROOT, FRESH_SEEDS),
)


# ---------------------------------------------------------------------------
# Discovery (mirrors lr.discover_runs but over STREAM_CONFIGS_V041_FRESH)
# ---------------------------------------------------------------------------


def discover_v041_fresh_runs() -> list[tuple[str, str, int, int, Path]]:
    """Iterate the 32 (source_version, arm_label, hazard, seed,
    run_dir) tuples in deterministic sorted order: hazard -> seed."""
    out: list[tuple[str, str, int, int, Path]] = []
    for source_version, runs_root, seeds in STREAM_CONFIGS_V041_FRESH:
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
    runs = discover_v041_fresh_runs()
    expected_n_runs = len(lr.HAZARDS) * len(FRESH_SEEDS)
    if len(runs) != expected_n_runs:
        msg = (
            f"discover_v041_fresh_runs returned {len(runs)} runs but "
            f"expected {expected_n_runs} "
            f"(={len(lr.HAZARDS)} hazards x {len(FRESH_SEEDS)} seeds)"
        )
        raise lr.LineageReplayError(msg)
    print(
        f"v0.34 lineage_replay (v0.41 fresh extension): {len(runs)} fresh runs discovered",
        flush=True,
    )

    all_agent_rows: list = []
    all_lineage_rows: list = []
    run_summaries: list = []
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, lineage_rows, run_summary = lr.process_run(
            source_version, arm_label, hazard, seed, run_dir
        )
        all_agent_rows.extend(agent_rows)
        all_lineage_rows.extend(lineage_rows)
        run_summaries.append(run_summary)

    pool_summaries = lr.aggregate_pool(run_summaries)
    # NOTE: cross_check_b50_anchors intentionally NOT called.
    # B_POOL_ANCHORS lock the old corpus; v0.41 fresh stream's per-hazard
    # B_POOL is an emergent observable, not an anchor.

    paths = lr.write_outputs(
        all_agent_rows,
        all_lineage_rows,
        run_summaries,
        pool_summaries,
        out_dir=OUT_DIR_FRESH,
    )

    print()
    print("v0.41 fresh-stream pool summary (one row per hazard):")
    print(
        f"  {'hazard':>6} {'n_runs':>6} {'total_b50':>10} "
        f"{'mean_share':>11} {'median_share':>13} {'n_majority':>11}"
    )
    for ps in pool_summaries:
        print(
            f"  {ps.hazard:>6d} {ps.n_runs:>6d} {ps.total_b50:>10d} "
            f"{ps.mean_top_lineage_b50_share:>11.3f} "
            f"{ps.median_top_lineage_b50_share:>13.3f} "
            f"{ps.n_runs_single_lineage_majority:>11d}",
            flush=True,
        )

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>15}  -> {path}")


if __name__ == "__main__":
    main()
