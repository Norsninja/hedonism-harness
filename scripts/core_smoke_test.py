#!/usr/bin/env python
"""Pre-Mesa core smoke test.

Proves that the entire Mesa-free core loop coheres end-to-end:

  build world -> create body -> assign traits -> observe -> choose action ->
  apply action -> commit delta -> update memory -> emit/read events ->
  repeat for N ticks -> same seed produces same final state.

Exits 0 on success, 1 on failure. Prints a tutorial-style trace so reading
this script teaches the API the same way it gates CI.

Run locally:
    uv run python scripts/core_smoke_test.py

Or via the justfile:
    just smoke
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter

from hedonism_harness.core.actions import (
    apply_action,
    commit_delta,
)
from hedonism_harness.core.body import (
    apply_metabolism,
    infer_death_cause,
    is_dead,
    make_body,
    mark_dead,
)
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.memory import (
    decay_all,
    make_memory,
    update_at,
)
from hedonism_harness.core.rng import make_streams
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.traits import TraitConfig, random_traits
from hedonism_harness.core.world import build_world
from hedonism_harness.policies import DecisionContext, MemoryHedonismPolicy

N_TICKS = 50
SEED_A = 42
SEED_B = 12345  # different seed -> different result, sanity check

SECTION = "─" * 60


def banner(title: str) -> None:
    print(f"\n{SECTION}\n  {title}\n{SECTION}")


def hash_state(world, body, memory, event_counter: Counter) -> str:
    """Return a sha256 hex of every byte that should be deterministic."""
    h = hashlib.sha256()
    h.update(world.kind_layer.tobytes())
    h.update(world.food_value.tobytes())
    h.update(world.hazard_damage.tobytes())
    h.update(world.safe_value.tobytes())
    h.update(memory.pleasure_ema.tobytes())
    h.update(memory.pain_ema.tobytes())
    h.update(memory.visits.tobytes())
    h.update(memory.last_seen_tick.tobytes())
    h.update(repr(body).encode())
    for name in sorted(event_counter):
        h.update(f"{name}={event_counter[name]}".encode())
    return h.hexdigest()


def run_one_episode(seed: int, *, verbose: bool) -> tuple[str, dict]:
    """Walk the core loop for N_TICKS, return (state_hash, summary_dict)."""
    streams = make_streams(seed)

    world_cfg = WorldConfig(
        seed=seed,
        width=12,
        height=12,
        food_density=0.10,
        hazard_density=0.05,
    )
    body_cfg = BodyConfig()
    action_cfg = ActionConfig()
    repro_cfg = ReproductionConfig()
    trait_cfg = TraitConfig()

    if verbose:
        print(f"  built configs (seed={seed})")

    world = build_world(world_cfg)
    if verbose:
        food_count = int((world.food_value > 0).sum())
        haz_count = int((world.hazard_damage > 0).sum())
        print(
            f"  built world {world.width}x{world.height}: "
            f"{food_count} food cells, {haz_count} hazard cells"
        )

    traits = random_traits(trait_cfg, streams.mutation)
    body = make_body(
        body_id=1,
        lineage_id=0,
        parent_id=None,
        x=world.width // 2,
        y=world.height // 2,
        traits=traits,
        config=body_cfg,
    )
    if verbose:
        print(
            f"  created body at ({body.x},{body.y}) "
            f"with sensor_radius={body.traits.sensor_radius}, "
            f"metabolic_rate={body.traits.metabolic_rate:.2f}"
        )

    memory = make_memory(world.width, world.height)
    policy = MemoryHedonismPolicy(exploration_noise=0.0)
    if verbose:
        print(f"  initialized {type(memory).__name__} and {type(policy).__name__}")

    event_counter: Counter[str] = Counter()
    death_cause = None
    ticks_run = 0

    for tick in range(N_TICKS):
        ticks_run = tick + 1
        if is_dead(body):
            cause = infer_death_cause(body)
            if cause is not None:
                body = mark_dead(body, cause)
                death_cause = cause.name
            break

        observation = observe(world, body, body_cfg, memory=memory)

        ctx = DecisionContext(
            world=world,
            body=body,
            observation=observation,
            rng=streams.action_noise,
            body_config=body_cfg,
            action_config=action_cfg,
            memory=memory,
            reproduction_config=repro_cfg,
            occupied=None,
        )
        decision = policy.decide(ctx)

        result = apply_action(
            world, body, decision.action, body_cfg, action_cfg, streams.action_noise
        )
        commit_delta(world, result.delta)

        # Memory update: feed back the felt pleasure/pain at the new cell.
        pleasure = decision.breakdown.pleasure if decision.breakdown else 0.0
        pain = decision.breakdown.pain if decision.breakdown else 0.0
        update_at(
            memory,
            result.body.x,
            result.body.y,
            pleasure=pleasure,
            pain=pain,
            traits=body.traits,
            tick=tick,
        )

        for event in result.events:
            event_counter[type(event).__name__] += 1

        body = apply_metabolism(result.body, body_cfg)
        decay_all(memory, body.traits.memory_decay_rate)

        if verbose and tick < 3:
            print(
                f"  tick {tick}: action={decision.action.name}, "
                f"pos=({body.x},{body.y}), energy={body.energy:.1f}, "
                f"score={decision.breakdown.total:.2f}"
                if decision.breakdown
                else f"  tick {tick}: action={decision.action.name} (noise)"
            )

    summary = {
        "seed": seed,
        "ticks_run": ticks_run,
        "alive": body.alive,
        "death_cause": death_cause,
        "final_pos": (body.x, body.y),
        "final_energy": round(body.energy, 4),
        "final_health": round(body.health, 4),
        "memory_visits_total": int(memory.visits.sum()),
        "events": dict(event_counter),
    }
    state_hash = hash_state(world, body, memory, event_counter)
    return state_hash, summary


def main() -> int:
    print(SECTION)
    print("  Hedonism Harness — Pre-Mesa Core Smoke Test")
    print(SECTION)

    banner("Stage 1 — verbose walkthrough at seed=" + str(SEED_A))
    hash_a, summary_a = run_one_episode(SEED_A, verbose=True)
    print(f"\n  state_hash = {hash_a[:16]}...")
    for k, v in summary_a.items():
        print(f"  {k}: {v}")

    banner("Stage 2 — determinism check (re-run same seed)")
    hash_a_repeat, summary_a_repeat = run_one_episode(SEED_A, verbose=False)
    print(f"  state_hash = {hash_a_repeat[:16]}...")
    if hash_a != hash_a_repeat:
        print("\nFAIL: same-seed determinism broken.")
        print(f"  first run : {hash_a}")
        print(f"  second run: {hash_a_repeat}")
        diffs = {
            k: (summary_a[k], summary_a_repeat[k])
            for k in summary_a
            if summary_a[k] != summary_a_repeat[k]
        }
        if diffs:
            print(f"  diffs     : {diffs}")
        return 1
    if summary_a != summary_a_repeat:
        print("\nFAIL: hashes match but summaries differ — investigate.")
        return 1
    print("  PASS: identical state hash and summary.")

    banner("Stage 3 — variation check (different seed)")
    hash_b, _ = run_one_episode(SEED_B, verbose=False)
    print(f"  state_hash (seed={SEED_B}) = {hash_b[:16]}...")
    if hash_a == hash_b:
        print("\nFAIL: different seeds produced identical state. Determinism plumbing is suspect.")
        return 1
    print("  PASS: different seed -> different state.")

    banner("Result")
    print("  All three stages passed.")
    print("  The Mesa-free core loop coheres end-to-end and is")
    print("  reproducible under fixed seed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
