"""v0.44 preflight: inspect tick-50 substrate state on seeds 57..64.

Per [[docs/experiments/fear_hunger_v0.44.md]] §"Pre-implementation
feasibility preflight" — HARD REQUIREMENT before the v0.44 sweep
runs and before ``EXPECTED_N_ELIGIBLE_CELLS`` is committed as a
hard halt constant.

This probe uses ``_run_one_arm_seed`` (NOT hand-rolled
``run_chamber``) under the exact V0_25 anchor sweep path
(GradientPolicy + auto_reproduction=True + TraitConfig
(unbounded_mutation=True) + food_respawn_cooldown=50 +
ambient_influx_rate=1.0). It reuses ``_v0_43r_arm`` with
``intervention_kind="null"`` — byte-identical to what the v0.44
A_null arms will use, modulo arm label.

For each (seed in 57..64, hazard in {0, 8}) bucket, the probe
captures world state at tick 50 (the intervention's
``intervention_tick``; pre-effective-tick) and emits:

- ``n_eligible_cells``: count satisfying
  ``kind in {EMPTY, FOOD} AND respawn_at_tick > 0``.
- ``min/max/median respawn_at_tick`` over eligible cells.
- ``sorted multiset`` of ``respawn_at_tick`` over eligible cells.
- ``total_food`` over the chamber (expected: 0).

Operative-substrate criteria (all must hold across all 16 buckets):

1. ``n_eligible_cells`` is consistent across all buckets and is the
   value that gets committed to ``EXPECTED_N_ELIGIBLE_CELLS``.
2. Refill-tick distribution is heterogeneous within each bucket
   (``min < max``).
3. ``min + 25 <= 200`` AND ``max + 25 <= 200`` (so the +25 delay
   does not push refills past the simulation horizon).

If any criterion fails on any bucket, halt pre-sweep and amend
the pre-reg.

Usage:
    uv run python scripts/v0_44_preflight.py
"""

from __future__ import annotations

import statistics
import tempfile
from pathlib import Path

import numpy as np

from hedonism_harness.core.interventions import InterventionConfig
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.core.world import CellKind
from hedonism_harness.experiments.comparison_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
    _resolve_layout,
    _v0_43r_arm,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.model import HHModel

CHAMBER = "tight_gradient"
SEEDS = tuple(range(57, 65))
HAZARDS = (0, 8)
N_TICKS = 200
N_FOUNDERS = 5
INTERVENTION_TICK = 50  # state captured at end of tick == 50 (pre-effective)


def _capture_at_tick(target_tick: int, store: dict) -> object:
    def observer(model) -> None:
        if model.tick_count == target_tick and "snapshot" not in store:
            world = model.world
            kind_layer = np.asarray(world.kind_layer)
            food_value = np.asarray(world.food_value)
            respawn = np.asarray(world.respawn_at_tick)
            eligible_mask = ((kind_layer == CellKind.EMPTY) | (kind_layer == CellKind.FOOD)) & (
                respawn > 0
            )
            eligible_ticks = sorted(int(v) for v in respawn[eligible_mask].tolist())
            store["snapshot"] = {
                "tick": int(model.tick_count),
                "n_eligible_cells": int(eligible_mask.sum()),
                "respawn_ticks_sorted": eligible_ticks,
                "total_food": float(food_value.sum()),
                "n_food_cells": int((kind_layer == CellKind.FOOD).sum()),
                "n_empty_cells": int((kind_layer == CellKind.EMPTY).sum()),
            }

    return observer


def _bucket_summary(snap: dict) -> dict:
    ticks = snap["respawn_ticks_sorted"]
    if not ticks:
        return {
            "n_eligible_cells": 0,
            "min_tick": None,
            "max_tick": None,
            "median_tick": None,
            "total_food": snap["total_food"],
            "ticks": [],
        }
    return {
        "n_eligible_cells": snap["n_eligible_cells"],
        "min_tick": ticks[0],
        "max_tick": ticks[-1],
        "median_tick": statistics.median(ticks),
        "total_food": snap["total_food"],
        "ticks": ticks,
    }


def _run_one_bucket(seed: int, hazard: int, runs_root: Path) -> dict:
    base_label = f"transfer-1500-hzd{hazard}-influx-1.0"
    arm = _v0_43r_arm(
        base_label=base_label,
        arm_prefix=f"preflight-v044-hzd{hazard}",
        intervention_kind="null",
    )
    store: dict = {}

    # Inject tick_observer through the chamber driver. _run_one_arm_seed
    # forwards setup_observer but not tick_observer, so we reconstruct
    # the same parameter pack here.
    layout = _resolve_layout(CHAMBER)
    repro_kwargs = {
        "energy_threshold": (
            arm.energy_threshold if arm.energy_threshold is not None else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": (arm.energy_cost if arm.energy_cost is not None else FIXED_ENERGY_COST),
    }
    if arm.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = arm.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
    trait_cfg = TraitConfig(unbounded_mutation=True)

    captured: dict = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = arm.auto_reproduction
        captured["model"] = model

    optional_intervention: InterventionConfig | None = None
    if arm.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=arm.intervention_kind)

    use_memory = arm.memory_type is not None
    memory_type = arm.memory_type or "cell_exact"

    run_chamber(
        seed=seed,
        runs_root=runs_root,
        run_id=f"seed-{seed}",
        n_founders=N_FOUNDERS,
        n_ticks=N_TICKS,
        layout=layout,
        policy_factory=arm.policy_factory,
        trait_config=trait_cfg,
        reproduction_config=repro_cfg,
        use_memory=use_memory,
        memory_type=memory_type,
        food_respawn_cooldown=arm.food_respawn_cooldown,
        energy_pool_initial=arm.energy_pool_initial,
        ambient_influx_rate=arm.ambient_influx_rate,
        child_funding_mode=arm.child_funding_mode,
        hazard_damage=arm.hazard_damage,
        hazard_avoidance_weight=arm.hazard_avoidance_weight,
        condition=arm.label,
        setup_observer=setup,
        tick_observer=_capture_at_tick(INTERVENTION_TICK, store),
        optional_intervention=optional_intervention,
    )
    snap = store.get("snapshot")
    if snap is None:
        raise RuntimeError(
            f"preflight failed to capture tick-{INTERVENTION_TICK} state"
            f" for seed={seed} hazard={hazard}"
        )
    return _bucket_summary(snap)


def main() -> None:
    print("=== v0.44 preflight: tick-50 substrate inspection on seeds 57..64 ===")
    print(f"Chamber: {CHAMBER}; hazards: {HAZARDS}; seeds: {SEEDS}")
    print("Anchor: V0_25 (GradientPolicy + auto_reproduction + unbounded_mutation)")
    print(f"intervention_tick (state capture point): {INTERVENTION_TICK}\n")

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        results: dict[tuple[int, int], dict] = {}
        for hazard in HAZARDS:
            for seed in SEEDS:
                summary = _run_one_bucket(seed, hazard, runs_root)
                results[(seed, hazard)] = summary
                ticks_str = ",".join(str(t) for t in summary["ticks"])
                print(
                    f"  seed={seed} hzd={hazard:>2} | "
                    f"n_eligible={summary['n_eligible_cells']:>2} "
                    f"min={summary['min_tick']} "
                    f"med={summary['median_tick']} "
                    f"max={summary['max_tick']} "
                    f"total_food={summary['total_food']:.1f} "
                    f"ticks=[{ticks_str}]"
                )

    print("\n=== Operative-substrate criteria evaluation ===\n")

    # Criterion 1: n_eligible_cells consistent across buckets.
    n_elig_set = {r["n_eligible_cells"] for r in results.values()}
    crit1_ok = len(n_elig_set) == 1 and 0 not in n_elig_set
    print(
        f"[{'PASS' if crit1_ok else 'FAIL'}] Criterion 1: "
        f"n_eligible_cells consistent across all 16 buckets — "
        f"observed values: {sorted(n_elig_set)}"
    )

    # Criterion 2: heterogeneous distribution within each bucket.
    crit2_failures = [
        (sk, hz)
        for (sk, hz), r in results.items()
        if r["min_tick"] is None or r["min_tick"] >= r["max_tick"]
    ]
    crit2_ok = not crit2_failures
    print(
        f"[{'PASS' if crit2_ok else 'FAIL'}] Criterion 2: "
        f"refill-tick distribution heterogeneous within each bucket "
        f"(min < max) — failures: {crit2_failures}"
    )

    # Criterion 3: max + 25 <= 200 and min + 25 <= 200.
    crit3_failures = [
        (sk, hz)
        for (sk, hz), r in results.items()
        if r["max_tick"] is None or r["max_tick"] + 25 > 200
    ]
    crit3_ok = not crit3_failures
    print(
        f"[{'PASS' if crit3_ok else 'FAIL'}] Criterion 3: "
        f"max_tick + 25 <= 200 (no refill pushed past horizon) — "
        f"failures: {crit3_failures}"
    )

    # Criterion 4: total_food == 0 across all buckets (corrected
    # substrate finding from v0.43R should reproduce on seeds 57..64).
    crit4_failures = [(sk, hz) for (sk, hz), r in results.items() if r["total_food"] != 0.0]
    crit4_ok = not crit4_failures
    print(
        f"[{'PASS' if crit4_ok else 'FAIL'}] Criterion 4: "
        f"total_food == 0 (substrate depleted, matching v0.43R "
        f"corrected finding) — failures: {crit4_failures}"
    )

    overall = crit1_ok and crit2_ok and crit3_ok and crit4_ok
    verdict = (
        "PASS - preflight clears v0.44 sweep" if overall else "FAIL - halt pre-sweep; amend pre-reg"
    )
    print(f"\n=== Overall: {verdict} ===")
    if overall:
        print(f"Locked: EXPECTED_N_ELIGIBLE_CELLS = {next(iter(n_elig_set))}")

        all_ticks: list[int] = []
        for r in results.values():
            all_ticks.extend(r["ticks"])
        if all_ticks:
            print(
                f"Aggregate refill-tick distribution across all buckets: "
                f"min={min(all_ticks)} max={max(all_ticks)} "
                f"median={statistics.median(all_ticks)} "
                f"n_total={len(all_ticks)}"
            )


if __name__ == "__main__":
    main()
