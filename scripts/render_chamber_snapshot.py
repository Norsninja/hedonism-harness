#!/usr/bin/env python
"""Render a Fear-Hunger Chamber snapshot to stdout.

Builds the chamber, runs it for ``--ticks`` steps, and prints an ASCII
snapshot of terrain + final agent positions. Intended for embedding in
experiment reports and for quick eyeball debugging.

Usage::

    uv run python scripts/render_chamber_snapshot.py
    uv run python scripts/render_chamber_snapshot.py --seed 42 --ticks 100
"""

from __future__ import annotations

import argparse

from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
)
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    build_chamber_layout,
    default_policy_factory,
    paint_chamber,
)
from hedonism_harness.experiments.snapshots import render_model_snapshot
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--n-founders", type=int, default=5)
    parser.add_argument(
        "--initial-only",
        action="store_true",
        help="Render the chamber at t=0 (no run), useful for showing terrain.",
    )
    args = parser.parse_args()

    layout = ChamberLayout()
    world_cfg = build_chamber_layout(layout).model_copy(update={"seed": args.seed})

    spawn_x = layout.safe_x_min + 1
    step_y = max(1, layout.height // args.n_founders)
    spawn_ys = [min(layout.height - 1, i * step_y) for i in range(args.n_founders)]
    founders = [
        FounderSpec(x=spawn_x, y=y, policy_factory=default_policy_factory) for y in spawn_ys
    ]

    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
        trait_config=TraitConfig(),
    )
    paint_chamber(model, layout)

    print(f"# Chamber snapshot — seed={args.seed}")
    print(
        f"# layout: SAFE [{layout.safe_x_min}-{layout.safe_x_max}]  "
        f"HAZARD [{layout.hazard_x_min}-{layout.hazard_x_max}]  "
        f"FOOD [{layout.food_x_min}-{layout.food_x_max}]  "
        f"height={layout.height}"
    )
    print("# tick 0:")
    print(render_model_snapshot(model))

    if args.initial_only:
        return 0

    for _t in range(args.ticks):
        model.step()
        if not any(isinstance(a, HHAgent) and a.body.alive for a in model.agents):
            break

    print(f"\n# tick {model.tick_count}:")
    print(render_model_snapshot(model))
    living = sum(1 for a in model.agents if isinstance(a, HHAgent) and a.body.alive)
    print(f"\n# survivors: {living}/{args.n_founders}, ticks_run: {model.tick_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
