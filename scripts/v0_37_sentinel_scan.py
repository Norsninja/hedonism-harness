"""v0.37 sentinel-only scratch (audit artifact; not part of the v0.37 reducer).

Counts ``n_never_leads_pre_end`` per hazard across the full 96-run corpus.
A run contributes 1 to its hazard's count iff the eventual_top_lineage is
NEVER the (tie-break-inclusive) birth-count leader at any tick t in
[0, n_ticks). Runs with eventual_top_lineage is None (total_b50 == 0;
not expected on this corpus) are excluded from the denominator.

No means. No deltas. No thresholds. No verdict. Purpose: validate that
the O1 sentinel path is not rare-theoretical-only before the v0.37
pre-reg locks O1's spread threshold.

Retained as the pre-pre-reg sentinel-validation artifact; superseded by
the v0.37 reducer once that lands and SHOULD NOT be imported by it.

Usage:
    uv run python scripts/v0_37_sentinel_scan.py
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


def winner_ever_leads(agent_rows: list, winner_id: int, n_ticks: int) -> bool:
    return any(leader_lineage_at_tick(agent_rows, t) == winner_id for t in range(n_ticks))


def main() -> None:
    runs = lr.discover_runs()
    by_hazard_total: dict[int, int] = {h: 0 for h in lr.HAZARDS}
    by_hazard_never: dict[int, int] = {h: 0 for h in lr.HAZARDS}
    by_hazard_no_winner: dict[int, int] = {h: 0 for h in lr.HAZARDS}
    for source_version, arm_label, hazard, seed, run_dir in runs:
        agent_rows, n_ticks = ls.load_run_agents(source_version, arm_label, hazard, seed, run_dir)
        winner_id, _ = ls.compute_eventual_top_lineage(agent_rows)
        if winner_id is None:
            by_hazard_no_winner[hazard] += 1
            continue
        by_hazard_total[hazard] += 1
        if not winner_ever_leads(agent_rows, winner_id, n_ticks):
            by_hazard_never[hazard] += 1
    print(f"{'hazard':>7} {'n_runs':>7} {'n_never_leads':>14} {'no_winner':>10}")
    for hazard in lr.HAZARDS:
        print(
            f"{hazard:>7d} "
            f"{by_hazard_total[hazard]:>7d} "
            f"{by_hazard_never[hazard]:>14d} "
            f"{by_hazard_no_winner[hazard]:>10d}"
        )


if __name__ == "__main__":
    main()
