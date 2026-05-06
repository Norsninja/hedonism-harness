"""v0.38 inventory-only scratch (audit artifact; not part of the v0.38 reducer).

Computes per-lineage post-50 birth counts (b50), tick-50 leader,
eventual winner, leader_advantage and winner_overtake for exactly 3
runs (lowest-seed at h=0, h=8, h=12 from the v0.25 stream). No
aggregation, no per-hazard means, no thresholds, no verdict.

Purpose: validate observable computability + sentinel handling
(no-winner / rank2_zero / leader-equals-winner cases) before the
v0.38 pre-reg locks observable semantics.

Pre-pre-reg observable candidates (subject to user lock):
  leader_advantage  = b50(tick50_leader) - mean(b50(non-leaders))
                      4-lineage non-leader denominator.
  winner_overtake   = b50(eventual_winner) - b50(tick50_leader)
                      0 by definition when winner == leader (wad=True).

Retained in tree as the historical record of the pre-pre-reg
inventory phase; superseded by the v0.38 reducer once that lands
and SHOULD NOT be imported by it.

Usage:
    uv run python scripts/v0_38_inventory_scratch.py
"""

from __future__ import annotations

import importlib.util
import statistics
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


def per_lineage_b50(agent_rows: list) -> dict[int, int]:
    """Count agents with born_after_tick_50 per lineage_id."""
    out: dict[int, int] = {}
    for a in agent_rows:
        out.setdefault(a.lineage_id, 0)
        if a.born_after_tick_50:
            out[a.lineage_id] += 1
    return out


SOURCE_VERSION = "v0.25"
RUNS_ROOT = Path("runs/fear-hunger-v0.25-tight_gradient/arms")
SEED = 1
HAZARDS_INVENTORY: tuple[int, ...] = (0, 8, 12)


def main() -> None:
    print(
        f"{'src':>5} {'haz':>3} {'seed':>4}  "
        f"{'b50_per_lineage':>30}  "
        f"{'leader':>6} {'winner':>6} {'wad':>5}  "
        f"{'L_b50':>5} {'NL_mean':>7} {'lead_adv':>8}  "
        f"{'W_b50':>5} {'overtake':>8}",
        flush=True,
    )
    for hazard in HAZARDS_INVENTORY:
        arm_label = lr.ARM_LABEL_FMT.format(hazard)
        run_dir = RUNS_ROOT / arm_label / f"seed-{SEED}"
        agent_rows, _n_ticks = ls.load_run_agents(SOURCE_VERSION, arm_label, hazard, SEED, run_dir)
        b50 = per_lineage_b50(agent_rows)
        # Ensure all 5 lineages represented (defensive; founders always alive
        # at tick 50 per v0.35 H2c, so should always populate).
        for lid in range(5):
            b50.setdefault(lid, 0)
        leader_id, _leader_births = ls.compute_leader_at_tick_50(agent_rows)
        winner_id, _ = ls.compute_eventual_top_lineage(agent_rows)
        wad = winner_id is not None and leader_id == winner_id
        leader_b50 = b50[leader_id]
        non_leader_b50 = [b50[lid] for lid in sorted(b50) if lid != leader_id]
        non_leader_mean = statistics.mean(non_leader_b50) if non_leader_b50 else float("nan")
        lead_adv = leader_b50 - non_leader_mean
        if winner_id is None:
            w_b50 = 0
            overtake = 0
        else:
            w_b50 = b50[winner_id]
            overtake = 0 if wad else (w_b50 - leader_b50)
        b50_str = "{" + " ".join(f"{lid}:{b50[lid]}" for lid in sorted(b50)) + "}"
        print(
            f"{SOURCE_VERSION:>5} {hazard:>3d} {SEED:>4d}  "
            f"{b50_str:>30}  "
            f"{leader_id:>6d} "
            f"{winner_id if winner_id is not None else '-':>6} "
            f"{wad!s:>5}  "
            f"{leader_b50:>5d} {non_leader_mean:>7.2f} {lead_adv:>+8.2f}  "
            f"{w_b50:>5d} {overtake:>+8d}",
            flush=True,
        )


if __name__ == "__main__":
    main()
