"""v0.45 spatial-clustering preflight.

Per [[docs/experiments/fear_hunger_v0.45.md]] §"Pre-implementation
feasibility preflight" (pending — pre-reg drafted from preflight
findings, not the other way around). HARD REQUIREMENT before
locking the v0.45 intervention design.

Decision tree (locked from session discussion):
- If lineages are spatially clustered at tick 50:
    v0.45 = birth-position / spatial-clustering intervention.
- If lineages are spatially mixed:
    v0.45 = founder-position or hazard-topology probe.
- If neither yields a real signal:
    pivot to founder-trait lock-in.

This probe uses ``_run_one_arm_seed``-equivalent path under the
V0_25 anchor (per the v0.43R methodological lesson). For each
(seed in 65..72, hazard in {0, 8}) bucket the probe captures, at
tick 50, the spatial distribution of living agents by lineage,
plus the post-50 birth-location stream from events.jsonl.

Captures:
- Per-lineage living-agent count.
- Per-lineage centroid (mean x, mean y).
- Per-lineage spatial dispersion (mean intra-lineage pairwise L1).
- Inter-lineage separation (mean pairwise L1 between centroids).
- Cluster purity: for each living agent, fraction of its 4-cell
  (N/S/E/W) neighborhood that shares its lineage_id (averaged
  over all living agents).
- Post-50 birth count per lineage.
- Post-50 birth-position stream by lineage.

Aggregates across the 16 (seed, hazard) buckets and emits a
verdict on whether the clustering signal is operative.

Operative-clustering criteria:
1. Mean per-bucket cluster purity >= 0.50 (a randomly mixed
   chamber would score 0.20 with 5 lineages; a fully clustered
   chamber scores 1.0).
2. Inter-lineage centroid separation > intra-lineage dispersion
   in a majority of buckets (lineages are spatially distinct).
3. Post-50 births occur (n_total > 0; otherwise no signal exists
   to disrupt).

Usage:
    uv run python scripts/v0_45_preflight.py
"""

from __future__ import annotations

import json
import math
import statistics
import tempfile
from pathlib import Path

from hedonism_harness.core.interventions import InterventionConfig
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.experiments.comparison_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
    V0_25_ARMS,
    _resolve_layout,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.model import HHModel

CHAMBER = "tight_gradient"
SEEDS = tuple(range(65, 73))
HAZARDS = (0, 8)
N_TICKS = 200
N_FOUNDERS = 5
TICK_50 = 50
PURITY_THRESHOLD = 0.50  # operative-clustering criterion 1


def _capture_tick_50_state(store: dict):
    def observer(model) -> None:
        if model.tick_count == TICK_50 and "snapshot" not in store:
            agents_by_lineage: dict[int, list[tuple[int, int]]] = {}
            occupied_to_lineage: dict[tuple[int, int], int] = {}
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                pos = (int(body.x), int(body.y))
                lid = int(body.lineage_id)
                agents_by_lineage.setdefault(lid, []).append(pos)
                occupied_to_lineage[pos] = lid
            store["snapshot"] = {
                "tick": int(model.tick_count),
                "agents_by_lineage": agents_by_lineage,
                "occupied_to_lineage": occupied_to_lineage,
                "world_width": int(model.world.width),
                "world_height": int(model.world.height),
            }

    return observer


def _l1_distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))


def _centroid(positions: list[tuple[int, int]]) -> tuple[float, float]:
    if not positions:
        return (float("nan"), float("nan"))
    return (
        sum(p[0] for p in positions) / len(positions),
        sum(p[1] for p in positions) / len(positions),
    )


def _intra_lineage_dispersion(positions: list[tuple[int, int]]) -> float:
    """Mean pairwise L1 distance within one lineage's positions.
    0.0 if 0 or 1 positions (no pairs).
    """
    if len(positions) < 2:
        return 0.0
    total = 0.0
    n = 0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            total += _l1_distance(positions[i], positions[j])
            n += 1
    return total / n


def _cluster_purity(occupied_to_lineage: dict[tuple[int, int], int]) -> float:
    """For each living agent, fraction of its 4-cell (N, S, E, W) neighborhood
    that is occupied by an agent of the same lineage. Cells outside the
    chamber or unoccupied don't count as either same or different — we
    compute the ratio over OCCUPIED neighbors only. Return mean across
    all agents that have at least one occupied neighbor; otherwise NaN
    for the run.
    """
    purities: list[float] = []
    for (x, y), my_lineage in occupied_to_lineage.items():
        same = 0
        total = 0
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = (x + dx, y + dy)
            if nb in occupied_to_lineage:
                total += 1
                if occupied_to_lineage[nb] == my_lineage:
                    same += 1
        if total > 0:
            purities.append(same / total)
    if not purities:
        return float("nan")
    return statistics.mean(purities)


def _bucket_summary(snap: dict, post50_births: dict) -> dict:
    agents_by_lineage = snap["agents_by_lineage"]
    occupied_to_lineage = snap["occupied_to_lineage"]
    n_living = sum(len(v) for v in agents_by_lineage.values())
    living_per_lineage = {lid: len(positions) for lid, positions in agents_by_lineage.items()}

    centroids = {lid: _centroid(positions) for lid, positions in agents_by_lineage.items()}
    intra_disp = {
        lid: _intra_lineage_dispersion(positions) for lid, positions in agents_by_lineage.items()
    }
    nonzero_disp = [d for d in intra_disp.values() if d > 0]
    mean_intra_dispersion = statistics.mean(nonzero_disp) if nonzero_disp else 0.0

    centroid_pairs: list[float] = []
    centroid_list = [c for c in centroids.values() if c[0] == c[0]]  # filter NaN
    for i in range(len(centroid_list)):
        for j in range(i + 1, len(centroid_list)):
            centroid_pairs.append(
                abs(centroid_list[i][0] - centroid_list[j][0])
                + abs(centroid_list[i][1] - centroid_list[j][1])
            )
    mean_inter_separation = statistics.mean(centroid_pairs) if centroid_pairs else 0.0

    purity = _cluster_purity(occupied_to_lineage)

    return {
        "n_lineages_present": len(agents_by_lineage),
        "n_living": n_living,
        "living_per_lineage": living_per_lineage,
        "centroids": centroids,
        "intra_dispersion": intra_disp,
        "mean_intra_dispersion": mean_intra_dispersion,
        "mean_inter_centroid_separation": mean_inter_separation,
        "cluster_purity": purity,
        "post_50_births_total": sum(post50_births.values()),
        "post_50_births_per_lineage": post50_births,
    }


def _read_post50_births(events_jsonl: Path) -> dict[int, int]:
    counts: dict[int, int] = {}
    for line in events_jsonl.read_text().splitlines():
        e = json.loads(line)
        if e["type"] != "AgentBorn":
            continue
        ev = e["event"]
        if ev["tick"] <= 50:
            continue
        counts[int(ev["lineage_id"])] = counts.get(int(ev["lineage_id"]), 0) + 1
    return counts


def _run_one_bucket(seed: int, hazard: int, runs_root: Path) -> dict:
    base_label = f"transfer-1500-hzd{hazard}-influx-1.0"
    base = next(arm for arm in V0_25_ARMS if arm.label == base_label)

    layout = _resolve_layout(CHAMBER)
    repro_kwargs = {
        "energy_threshold": (
            base.energy_threshold if base.energy_threshold is not None else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": (base.energy_cost if base.energy_cost is not None else FIXED_ENERGY_COST),
    }
    if base.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = base.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
    trait_cfg = TraitConfig(unbounded_mutation=True)

    captured: dict = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = base.auto_reproduction
        captured["model"] = model

    store: dict = {}

    optional_intervention: InterventionConfig | None = None
    if base.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=base.intervention_kind)

    use_memory = base.memory_type is not None
    memory_type = base.memory_type or "cell_exact"

    run_id = f"seed-{seed}"
    run_chamber(
        seed=seed,
        runs_root=runs_root,
        run_id=run_id,
        n_founders=N_FOUNDERS,
        n_ticks=N_TICKS,
        layout=layout,
        policy_factory=base.policy_factory,
        trait_config=trait_cfg,
        reproduction_config=repro_cfg,
        use_memory=use_memory,
        memory_type=memory_type,
        food_respawn_cooldown=base.food_respawn_cooldown,
        energy_pool_initial=base.energy_pool_initial,
        ambient_influx_rate=base.ambient_influx_rate,
        child_funding_mode=base.child_funding_mode,
        hazard_damage=base.hazard_damage,
        hazard_avoidance_weight=base.hazard_avoidance_weight,
        condition=f"v0.45-preflight-hzd{hazard}",
        setup_observer=setup,
        tick_observer=_capture_tick_50_state(store),
        optional_intervention=optional_intervention,
    )
    snap = store.get("snapshot")
    if snap is None:
        raise RuntimeError(
            f"preflight failed to capture tick-{TICK_50} state for seed={seed} hazard={hazard}"
        )
    events_jsonl = runs_root / run_id / "events.jsonl"
    post50_births = _read_post50_births(events_jsonl)
    return _bucket_summary(snap, post50_births)


def _print_bucket(seed: int, hazard: int, summary: dict) -> None:
    n_lin = summary["n_lineages_present"]
    n_liv = summary["n_living"]
    purity = summary["cluster_purity"]
    purity_str = "nan" if math.isnan(purity) else f"{purity:.3f}"
    intra = summary["mean_intra_dispersion"]
    inter = summary["mean_inter_centroid_separation"]
    n_b50 = summary["post_50_births_total"]
    print(
        f"  seed={seed} hzd={hazard:>2} | "
        f"n_lin={n_lin} n_living={n_liv:>3} "
        f"purity={purity_str:>6} "
        f"intra_disp={intra:>5.2f} "
        f"inter_sep={inter:>5.2f} "
        f"post50_births={n_b50:>3} "
        f"by_lin={dict(summary['living_per_lineage'])}"
    )


def main() -> None:
    print("=== v0.45 spatial-clustering preflight (seeds 65..72) ===")
    print(f"Chamber: {CHAMBER}; hazards: {HAZARDS}; seeds: {SEEDS}")
    print("Anchor: V0_25 (GradientPolicy + auto_reproduction + unbounded_mutation)")
    print(f"State capture: tick=={TICK_50} via tick_observer\n")

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        results: dict[tuple[int, int], dict] = {}
        for hazard in HAZARDS:
            for seed in SEEDS:
                # Each bucket needs its own per-seed dir; use a per-bucket subdir
                bucket_root = runs_root / f"hzd{hazard}-seed{seed}"
                bucket_root.mkdir(parents=True, exist_ok=True)
                summary = _run_one_bucket(seed, hazard, bucket_root)
                results[(seed, hazard)] = summary
                _print_bucket(seed, hazard, summary)

    print("\n=== Operative-clustering criteria evaluation ===\n")

    purities = [
        r["cluster_purity"] for r in results.values() if not math.isnan(r["cluster_purity"])
    ]
    mean_purity = statistics.mean(purities) if purities else float("nan")
    crit1_ok = (not math.isnan(mean_purity)) and mean_purity >= PURITY_THRESHOLD
    purity_str = "nan" if math.isnan(mean_purity) else f"{mean_purity:.3f}"
    print(
        f"[{'PASS' if crit1_ok else 'FAIL'}] Criterion 1: "
        f"mean cluster purity across buckets = {purity_str} "
        f"(threshold: >= {PURITY_THRESHOLD}; random-mixed baseline ~ 0.20 for 5 lineages)"
    )

    n_buckets_with_signal = sum(
        1
        for r in results.values()
        if r["mean_inter_centroid_separation"] > r["mean_intra_dispersion"]
    )
    crit2_ok = n_buckets_with_signal > len(results) // 2
    print(
        f"[{'PASS' if crit2_ok else 'FAIL'}] Criterion 2: "
        f"inter-lineage centroid separation > intra-lineage dispersion in "
        f"{n_buckets_with_signal} / {len(results)} buckets (need > {len(results) // 2})"
    )

    n_buckets_with_post50_births = sum(1 for r in results.values() if r["post_50_births_total"] > 0)
    crit3_ok = n_buckets_with_post50_births == len(results)
    print(
        f"[{'PASS' if crit3_ok else 'FAIL'}] Criterion 3: "
        f"post-50 births occur in every bucket: "
        f"{n_buckets_with_post50_births} / {len(results)}"
    )

    overall = crit1_ok and crit2_ok and crit3_ok
    if overall:
        print(
            "\n=== Overall: PASS - clustering signal operative; "
            "v0.45 = birth-position / spatial-clustering intervention ==="
        )
    elif crit3_ok and not crit1_ok:
        print(
            "\n=== Overall: FAIL on clustering - lineages are spatially mixed; "
            "pivot to founder-position or hazard-topology probe ==="
        )
    else:
        print("\n=== Overall: FAIL - revisit preflight assumptions; do not lock v0.45 design ===")

    print()
    print("Aggregate diagnostics across all 16 buckets:")
    print(f"  Mean cluster purity:                 {mean_purity:.3f}")
    intra_all = [r["mean_intra_dispersion"] for r in results.values()]
    inter_all = [r["mean_inter_centroid_separation"] for r in results.values()]
    living_all = [r["n_living"] for r in results.values()]
    births_all = [r["post_50_births_total"] for r in results.values()]
    print(f"  Mean intra-lineage dispersion:       {statistics.mean(intra_all):.3f}")
    print(f"  Mean inter-centroid separation:      {statistics.mean(inter_all):.3f}")
    print(f"  Mean living agents at tick 50:       {statistics.mean(living_all):.1f}")
    print(f"  Mean post-50 births per bucket:      {statistics.mean(births_all):.1f}")

    print()
    print("Lineage-presence summary at tick 50:")
    for hazard in HAZARDS:
        bucket_lineage_counts = [results[(s, hazard)]["n_lineages_present"] for s in SEEDS]
        print(
            f"  hzd={hazard}: n_lineages_present per seed = {bucket_lineage_counts} "
            f"(mean={statistics.mean(bucket_lineage_counts):.2f})"
        )


if __name__ == "__main__":
    main()
