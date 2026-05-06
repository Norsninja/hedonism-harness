"""v0.37 inventory-only scratch (audit artifact; not part of the v0.37 reducer).

Computes O1/O2/O3 for exactly 3 runs (lowest-seed at h=0, h=8, h=12 from
the v0.25 stream). No aggregation, no per-hazard means, no thresholds, no
verdict. Purpose: validate observable computability + sentinel handling
before the v0.37 pre-reg locks observable semantics. Retained in tree as
the historical record of the pre-pre-reg inventory phase; superseded by
the v0.37 reducer once that lands and SHOULD NOT be imported by it.

Locked observables (per pre-pre-reg agreement):
  O1 winner_first_leader_tick:
       smallest tick t in [0, n_ticks) where the eventual_top_lineage is
       the (tie-break-inclusive) birth-count leader; sentinel = n_ticks
       when winner never leads pre-end.
  O2 leader_turnover_count_25_to_100:
       count of adjacent pairs in {(25,50), (50,75), (75,100)} where
       leader_lineage_id changes (range [0, 3]).
  O3 margin_rank1_minus_rank2_at_tick_50:
       births_so_far(rank1) - births_so_far(rank2) at tick 50, where
       rank1/rank2 are lineages by descending births_so_far at tick 50
       (tie-break: lowest lineage_id wins).

Usage:
    uv run python scripts/v0_37_inventory_scratch.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_LR = Path(__file__).parent / "lineage_replay.py"
_LS = Path(__file__).parent / "lineage_survival_replay.py"

_lr_spec = importlib.util.spec_from_file_location("lineage_replay", _LR)
assert _lr_spec is not None
assert _lr_spec.loader is not None
lr = importlib.util.module_from_spec(_lr_spec)
sys.modules["lineage_replay"] = lr
_lr_spec.loader.exec_module(lr)

_ls_spec = importlib.util.spec_from_file_location("lineage_survival_replay", _LS)
assert _ls_spec is not None
assert _ls_spec.loader is not None
ls = importlib.util.module_from_spec(_ls_spec)
sys.modules["lineage_survival_replay"] = ls
_ls_spec.loader.exec_module(ls)


def leader_lineage_at_tick(agent_rows: list, tick: int) -> int:
    """Return the lineage_id with max births_so_far at tick T;
    tie-break = lowest lineage_id. Mirrors v0.35.compute_leader_at_tick_50."""
    by_lineage = ls._agents_by_lineage(agent_rows)
    best_id: int | None = None
    best_count = -1
    for lineage_id in sorted(by_lineage):
        c = ls.compute_births_so_far(by_lineage[lineage_id], tick)
        if c > best_count:
            best_id = lineage_id
            best_count = c
    assert best_id is not None
    return best_id


def compute_o1(agent_rows: list, winner_id: int, n_ticks: int) -> int:
    """Smallest tick in [0, n_ticks) where leader == winner; n_ticks if never."""
    for t in range(n_ticks):
        if leader_lineage_at_tick(agent_rows, t) == winner_id:
            return t
    return n_ticks


def compute_o2(agent_rows: list) -> int:
    """Leader-turnover count across {(25,50),(50,75),(75,100)}; range [0, 3]."""
    leaders = [leader_lineage_at_tick(agent_rows, t) for t in (25, 50, 75, 100)]
    return sum(1 for i in range(len(leaders) - 1) if leaders[i] != leaders[i + 1])


def compute_o3(agent_rows: list) -> tuple[int, int, bool]:
    """At tick 50: rank1 births, rank2 births, rank2_zero_flag.

    Sort lineages by (-births_so_far_at_50, lineage_id) so tie-break = lowest
    lineage_id first.
    """
    by_lineage = ls._agents_by_lineage(agent_rows)
    pairs: list[tuple[int, int]] = []
    for lineage_id in sorted(by_lineage):
        c = ls.compute_births_so_far(by_lineage[lineage_id], 50)
        pairs.append((lineage_id, c))
    pairs.sort(key=lambda p: (-p[1], p[0]))
    rank1_births = pairs[0][1] if pairs else 0
    rank2_births = pairs[1][1] if len(pairs) > 1 else 0
    return rank1_births, rank2_births, rank2_births == 0


SOURCE_VERSION = "v0.25"
RUNS_ROOT = Path("runs/fear-hunger-v0.25-tight_gradient/arms")
SEED = 1
HAZARDS_INVENTORY: tuple[int, ...] = (0, 8, 12)


def main() -> None:
    print(
        f"{'src':>6} {'arm':>30} {'haz':>3} {'seed':>4} "
        f"{'n_ticks':>7} {'winner':>6} "
        f"{'O1':>4} {'O2':>3} {'O3_r1':>5} {'O3_r2':>5} "
        f"{'never_leads':>11} {'rank2_zero':>10}",
        flush=True,
    )
    for hazard in HAZARDS_INVENTORY:
        arm_label = lr.ARM_LABEL_FMT.format(hazard)
        run_dir = RUNS_ROOT / arm_label / f"seed-{SEED}"
        agent_rows, n_ticks = ls.load_run_agents(SOURCE_VERSION, arm_label, hazard, SEED, run_dir)
        winner_id, _ = ls.compute_eventual_top_lineage(agent_rows)
        if winner_id is None:
            print(f"  hazard={hazard}: total_b50 == 0; winner is None — SKIP")
            continue
        o1 = compute_o1(agent_rows, winner_id, n_ticks)
        o2 = compute_o2(agent_rows)
        o3_r1, o3_r2, rank2_zero = compute_o3(agent_rows)
        never_leads = o1 == n_ticks
        print(
            f"{SOURCE_VERSION:>6} {arm_label:>30} {hazard:>3d} {SEED:>4d} "
            f"{n_ticks:>7d} {winner_id:>6d} "
            f"{o1:>4d} {o2:>3d} {o3_r1:>5d} {o3_r2:>5d} "
            f"{never_leads!s:>11} {rank2_zero!s:>10}",
            flush=True,
        )


if __name__ == "__main__":
    main()
