"""v0.38 leader_advantage_replay extension over the v0.41 second fresh seed stream.

Thin wrapper that imports v0.34 + v0.35 + v0.38 helpers via
``importlib.util`` and runs v0.38's per-run leader-advantage logic on a
v0.41-only STREAM_CONFIGS (seeds 33..40 at
``runs/fear-hunger-v0.41-tight_gradient/arms/``), writing to a SEPARATE
output directory ``runs/lineage-v0.38-v0_41-fresh/``.

This script does NOT modify [[scripts/leader_advantage_replay.py]] or
[[scripts/v0_39_leader_advantage_fresh_replay.py]] in any way. It does
NOT regenerate the sealed 96-row outputs at ``runs/lineage-v0.38/`` or
the sealed 32-row outputs at ``runs/lineage-v0.39/``.

The v0.41 fresh per_run.csv is the M3 source for
[[scripts/v0_41_stream_classification_audit.py]] (the v0.41 audit) and
exists alongside the prior sealed outputs under a CLEAN tier-separated
output dir (``v0.38 lens x v0_41-fresh stream``).

Differences from v0.38's main():
  - STREAM_CONFIGS_V041_FRESH includes only the v0.41 stream.
  - v0.34 anchor source is the v0.41-FRESH v0.34 output
    (``runs/lineage-v0.34-v0_41-fresh/run_summary.csv``).
  - v0.35 anchor source is the v0.41-FRESH v0.35 output
    (``runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv``).
  - reassert_b_pool_anchors is still called (static check on imported
    v0.34 LOCKED constants, valid in either context).
  - Per-hazard / indicator / verdict pipeline is NOT re-run; the v0.41
    audit consumes only per_run.csv. The extension stays minimal.
  - Output dir: runs/lineage-v0.38-v0_41-fresh/ (per_run.csv only).

Pre-reg: [[docs/experiments/fear_hunger_v0.41.md]] section "Mechanism"
subsection "v0.38 extension".

Usage:
    uv run python scripts/leader_advantage_replay_v0_41_extension.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import v0.34 + v0.35 + v0.38 helpers additively (no modification)
# ---------------------------------------------------------------------------


_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_LS_PATH = Path(__file__).parent / "lineage_survival_replay.py"
_LA_PATH = Path(__file__).parent / "leader_advantage_replay.py"

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

_la_spec = importlib.util.spec_from_file_location("leader_advantage_replay", _LA_PATH)
assert _la_spec is not None
assert _la_spec.loader is not None
la = importlib.util.module_from_spec(_la_spec)
sys.modules["leader_advantage_replay"] = la
_la_spec.loader.exec_module(la)


# ---------------------------------------------------------------------------
# Locked configuration (committed in pre-reg)
# ---------------------------------------------------------------------------


FRESH_SOURCE_VERSION: str = "v0.41"
FRESH_RUNS_ROOT: Path = Path("runs/fear-hunger-v0.41-tight_gradient/arms")
FRESH_SEEDS: tuple[int, ...] = tuple(range(33, 41))

V0_34_V041_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-v0_41-fresh/run_summary.csv")
V0_35_V041_FRESH_PRE_POST: Path = Path("runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv")
OUT_DIR_FRESH: Path = Path("runs/lineage-v0.38-v0_41-fresh")


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
# Output writer (per_run.csv only; v0.41 audit needs nothing else)
# ---------------------------------------------------------------------------


def write_per_run_only(per_run_rows: list, out_dir: Path = OUT_DIR_FRESH) -> dict[str, Path]:
    paths = {"per_run": out_dir / "per_run.csv"}
    la._write_dataclass_csv(per_run_rows, paths["per_run"], la.PER_RUN_FIELDNAMES)
    return paths


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> None:
    la.reassert_b_pool_anchors()
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
        f"v0.38 leader_advantage_replay (v0.41 fresh extension): {len(runs)} fresh runs discovered",
        flush=True,
    )

    # Anchor sources are the v0.41-FRESH v0.34 + v0.35 extension outputs.
    v34_anchors = la.load_v0_34_anchors(path=V0_34_V041_FRESH_RUN_SUMMARY)
    v35_anchors = la.load_v0_35_anchors(path=V0_35_V041_FRESH_PRE_POST)
    print(
        f"  loaded {len(v34_anchors)} v0.34 anchors, "
        f"{len(v35_anchors)} v0.35 anchors (both from v0.41-fresh)",
        flush=True,
    )

    per_run_rows: list = []
    derived_by_run: dict[tuple[str, str, int], tuple[int, int | None]] = {}
    for source_version, arm_label, hazard, seed, run_dir in runs:
        row = la.summarise_run(source_version, arm_label, hazard, seed, run_dir)
        per_run_rows.append(row)
        derived_by_run[(source_version, arm_label, seed)] = (
            row.leader_lineage_id,
            row.eventual_top_lineage_id,
        )

    la.cross_check_double_anchor(derived_by_run, v34_anchors, v35_anchors)

    paths = write_per_run_only(per_run_rows)

    print()
    print("v0.41 fresh-stream per-run leader_advantage (32 rows):")
    print(f"  {'haz':>3} {'seed':>4}  {'leader':>6} {'b50_l':>5} {'nl_mean':>8} {'adv':>7}")
    for row in per_run_rows:
        print(
            f"  {row.hazard:>3d} {row.seed:>4d}  "
            f"{row.leader_lineage_id:>6d} {row.leader_b50:>5d} "
            f"{row.non_leader_mean_b50:>8.3f} {row.leader_advantage:>+7.3f}",
            flush=True,
        )

    print()
    for label, path in paths.items():
        print(f"  wrote {label:>20}  -> {path}")


if __name__ == "__main__":
    main()
