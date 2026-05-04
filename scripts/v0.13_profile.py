"""v0.13 Phase 1 — memory-channel calibration profile.

Read-only diagnostic: dump ``ValenceBreakdown`` details for every valid
candidate action across three pre-registered scenarios, plus a by-tick
birth-distribution histogram from the v0.10 / v0.12 winner runs. No
``core/`` math is changed.

Output: a markdown table per scenario + a histogram, written to
``runs/fear-hunger-v0.13-profile/traces.md``.

See [[docs/experiments/fear_hunger_v0.13.md]] for pre-registration.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from hedonism_harness.core.actions import (
    Action,
    action_energy_cost,
    apply_action,
    get_valid_actions,
)
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    WorldConfig,
)
from hedonism_harness.core.memory import DirectionalMemory
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.valence import ValenceBreakdown, evaluate
from hedonism_harness.experiments.fear_hunger_chamber import paint_chamber, spread_y
from hedonism_harness.experiments.layouts import (
    food_ladder_layout,
    tight_gradient_layout,
)
from hedonism_harness.experiments.memory_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config
from hedonism_harness.experiments.trait_configs import memory_trait_config
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import (
    HedonismPolicy,
    _project_memory_for_action,
    _zero_memory_fields,
)

# ---------------------------------------------------------------------------
# Fixed run identity — match the v0.12b ms1-md0.1 winner exactly.
# ---------------------------------------------------------------------------

WINNER_MEMORY_STRENGTH_MIN: float = 1.0
WINNER_MEMORY_DECAY_RATE_MAX: float = 0.1
WINNER_LAYOUT: str = "food_ladder"
WINNER_SEED: int = 1
N_FOUNDERS: int = 5
N_TICKS_PROFILE: int = 50  # the pre-registered tick boundary (watch-out)


def _build_winner_model(
    *,
    seed: int = WINNER_SEED,
    memory_strength_min: float = WINNER_MEMORY_STRENGTH_MIN,
    memory_decay_rate_max: float = WINNER_MEMORY_DECAY_RATE_MAX,
    layout_name: str = WINNER_LAYOUT,
) -> HHModel:
    """Reproduce a v0.12 directional cell at the given (seed, layout, cell).

    Defaults match the v0.12b ms1-md0.1 food_ladder winner; pass
    ``memory_strength_min=0.0`` for the fast-EMA ms0-md0.1 variant; pass
    ``layout_name="tight_gradient"`` to switch chamber.
    """
    layout = food_ladder_layout() if layout_name == "food_ladder" else tight_gradient_layout()
    world_cfg = WorldConfig(
        seed=seed,
        width=layout.width,
        height=layout.height,
        food_density=0.0,
        hazard_density=0.0,
    )
    spawn_x = layout.resolved_spawn_x
    spawn_ys = spread_y(N_FOUNDERS, layout.height)
    trait_cfg = memory_trait_config(
        memory_strength_min=memory_strength_min,
        memory_decay_rate_max=memory_decay_rate_max,
    )
    repro_cfg = tuned_reproduction_config(
        energy_threshold=FIXED_ENERGY_THRESHOLD,
        energy_cost=FIXED_ENERGY_COST,
    )
    founders = [
        FounderSpec(
            x=spawn_x,
            y=y,
            policy_factory=lambda: HedonismPolicy(exploration_noise=0.05),
            use_memory=True,
            memory_type="directional",
        )
        for y in spawn_ys
    ]
    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=repro_cfg,
        trait_config=trait_cfg,
    )
    paint_chamber(model, layout)
    return model


def _candidate_breakdowns(
    model: HHModel, agent: HHAgent
) -> list[tuple[Action, ValenceBreakdown, ValenceBreakdown]]:
    """Score every valid action twice — projected and zeroed — like
    HedonismPolicy.decide does. Return a list of
    ``(candidate, breakdown_with_projection, breakdown_with_memory_zeroed)``
    triples for inspection.
    """
    occupied = model.occupied_cells_excluding(agent)
    obs_before = observe(model.world, agent.body, model.body_config, memory=agent.memory)
    valid = get_valid_actions(model.world, agent.body, model.reproduction_config, occupied)
    rows: list[tuple[Action, ValenceBreakdown, ValenceBreakdown]] = []
    is_directional = isinstance(agent.memory, DirectionalMemory)
    for candidate in valid:
        result = apply_action(
            model.world,
            agent.body,
            candidate,
            model.body_config,
            model.action_config,
            agent.agent_rng,
        )
        predicted_obs = observe(model.world, result.body, model.body_config, agent.memory)
        cost = action_energy_cost(candidate, model.action_config, model.reproduction_config)
        scored = (
            _project_memory_for_action(predicted_obs, candidate)
            if is_directional
            else predicted_obs
        )
        bd_proj = evaluate(
            obs_before,
            scored,
            agent.body,
            result.body,
            candidate,
            cost,
            agent.body.traits,
        )
        zeroed = _zero_memory_fields(predicted_obs) if is_directional else predicted_obs
        bd_zero = evaluate(
            obs_before,
            zeroed,
            agent.body,
            result.body,
            candidate,
            cost,
            agent.body.traits,
        )
        rows.append((candidate, bd_proj, bd_zero))
    return rows


def _format_breakdown_table(
    rows: list[tuple[Action, ValenceBreakdown, ValenceBreakdown]],
) -> str:
    """Markdown table: per candidate action, the harness components +
    novelty_pleasure + the with/without-memory totals."""
    out: list[str] = []
    out.append(
        "| action | total_proj | total_zero | Δ | pleasure | pain | fear | novelty_pleasure |"
        " eating_pleasure | anticipated_food_pleasure | safety_pleasure |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for action, bd_proj, bd_zero in rows:
        d = bd_proj.details
        out.append(
            f"| {action.name} | {bd_proj.total:7.3f} | {bd_zero.total:7.3f} |"
            f" {bd_proj.total - bd_zero.total:+6.3f} |"
            f" {bd_proj.pleasure:6.3f} | {bd_proj.pain:6.3f} | {bd_proj.fear:6.3f} |"
            f" {d.get('novelty_pleasure', 0.0):6.3f} |"
            f" {d.get('eating_pleasure', 0.0):6.3f} |"
            f" {d.get('anticipated_food_pleasure', 0.0):6.3f} |"
            f" {d.get('safety_pleasure', 0.0):6.3f} |"
        )
    return "\n".join(out)


def _agent_state_summary(agent: HHAgent, model: HHModel) -> str:
    """One-line snapshot of an agent's relevant state for the trace header."""
    obs = observe(model.world, agent.body, model.body_config, memory=agent.memory)
    mem = agent.memory
    if isinstance(mem, DirectionalMemory):
        pt = ", ".join(
            f"{name}={float(mem.pleasure_tendency[i]):.2f}"
            for i, name in enumerate(("N", "S", "E", "W"))
        )
        qt = ", ".join(
            f"{name}={float(mem.pain_tendency[i]):.2f}"
            for i, name in enumerate(("N", "S", "E", "W"))
        )
        mem_summary = f"pleasure_tendency=[{pt}]  pain_tendency=[{qt}]"
    else:
        mem_summary = f"memory={type(mem).__name__ if mem else 'None'}"
    return (
        f"agent_id={agent.body.id} pos=({agent.body.x},{agent.body.y}) "
        f"energy={agent.body.energy:.1f}/{model.body_config.max_energy:.1f} "
        f"hunger_level={obs.hunger_level:.2f} "
        f"on_food={obs.on_food} on_hazard={obs.on_hazard} on_safe={obs.on_safe}\n"
        f"  {mem_summary}"
    )


# ---------------------------------------------------------------------------
# Scenario 1 — hungry agent on food, captured organically from the run.
# ---------------------------------------------------------------------------


def _capture_on_food_block(
    *,
    layout_name: str,
    memory_strength_min: float,
    seeds: Iterable[int],
) -> tuple[str | None, str | None]:
    """Sweep ``seeds``; return (swayed_block, any_block) markdown strings.

    Each block renders its breakdown table **at match time**, so the
    agent's state cannot be mutated by later ticks. Returns the first
    swayed-on-food capture found and the first any-on-food capture.
    """
    swayed_block: str | None = None
    any_block: str | None = None
    for seed in seeds:
        if swayed_block is not None:
            break
        model = _build_winner_model(
            seed=seed,
            memory_strength_min=memory_strength_min,
            layout_name=layout_name,
        )
        for tick in range(200):
            model.step()
            for a in model.agents:
                if not isinstance(a, HHAgent) or not a.body.alive:
                    continue
                obs = observe(model.world, a.body, model.body_config, memory=a.memory)
                if not (obs.on_food and obs.hunger_level >= 0.4):
                    continue
                rows = _candidate_breakdowns(model, a)
                argmax_proj = max(rows, key=lambda r: r[1].total)[0]
                argmax_zero = max(rows, key=lambda r: r[2].total)[0]
                kind = "swayed-on-food" if argmax_proj != argmax_zero else "any-on-food"
                block = (
                    f"Captured at tick={tick} ({kind}) from a directional "
                    f"+ action-aware run, seed={seed}, layout={layout_name}.\n\n"
                    f"```\n{_agent_state_summary(a, model)}\n```\n\n"
                    + _format_breakdown_table(rows)
                    + "\n"
                )
                if kind == "swayed-on-food" and swayed_block is None:
                    swayed_block = block
                elif kind == "any-on-food" and any_block is None:
                    any_block = block
            if swayed_block is not None:
                break
    return swayed_block, any_block


def trace_1_hungry_on_food(*, fast_ema: bool = False, layout_name: str = WINNER_LAYOUT) -> str:
    """Render trace 1 across seeds 1..8, preferring a swayed-on-food
    capture. ``fast_ema=True`` switches to ms0-md0.1; ``layout_name``
    selects food_ladder (default) or tight_gradient (where v0.12 showed
    EAT-overrides cluster densely)."""
    cell_label = "ms0-md0.1 (fast EMA)" if fast_ema else "ms1-md0.1 (winner)"
    swayed, any_block = _capture_on_food_block(
        layout_name=layout_name,
        memory_strength_min=0.0 if fast_ema else WINNER_MEMORY_STRENGTH_MIN,
        seeds=[1, 2, 3, 4, 5, 42, 100, 2024],
    )
    body = swayed or any_block
    if body is None:
        return trace_1_synthetic_fallback()
    suffix = "b" if fast_ema else "a"
    if layout_name != WINNER_LAYOUT:
        suffix = "c"
    title = f"Trace 1{suffix} — hungry agent on food, {cell_label}, layout={layout_name}"
    return f"## {title}\n\n" + body


def trace_1_synthetic_fallback() -> str:
    """Synthetic version of trace 1 — only used when no organic match
    appears in the first 50 ticks (extremely unlikely on food_ladder)."""
    model = _build_synthetic_model(layout_name="food_ladder")
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    # Drain energy to make the agent hungry.
    agent.body = replace(agent.body, energy=20.0)
    # Ensure agent is on food.
    food_x = model.world.kind_layer.shape[0] - 2
    agent.body = replace(agent.body, x=food_x, y=2)
    # Fill east tendency from "recent eating."
    assert isinstance(agent.memory, DirectionalMemory)
    agent.memory.pleasure_tendency[2] = 8.0  # east
    rows = _candidate_breakdowns(model, agent)
    return (
        "## Trace 1 — hungry agent on food (synthetic fallback)\n\n"
        f"```\n{_agent_state_summary(agent, model)}\n```\n\n" + _format_breakdown_table(rows) + "\n"
    )


# ---------------------------------------------------------------------------
# Synthetic scenarios 2 + 3.
# ---------------------------------------------------------------------------


def _build_synthetic_model(*, layout_name: str) -> HHModel:
    """Build a single-founder model on the named layout — used to host
    the synthetic scenarios with hand-set agent state."""
    layout = food_ladder_layout() if layout_name == "food_ladder" else tight_gradient_layout()
    world_cfg = WorldConfig(
        seed=42,
        width=layout.width,
        height=layout.height,
        food_density=0.0,
        hazard_density=0.0,
    )
    trait_cfg = memory_trait_config(
        memory_strength_min=WINNER_MEMORY_STRENGTH_MIN,
        memory_decay_rate_max=WINNER_MEMORY_DECAY_RATE_MAX,
    )
    repro_cfg = tuned_reproduction_config(
        energy_threshold=FIXED_ENERGY_THRESHOLD,
        energy_cost=FIXED_ENERGY_COST,
    )
    founders = [
        FounderSpec(
            x=layout.resolved_spawn_x,
            y=layout.height // 2,
            policy_factory=lambda: HedonismPolicy(exploration_noise=0.05),
            use_memory=True,
            memory_type="directional",
        )
    ]
    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=repro_cfg,
        trait_config=trait_cfg,
    )
    paint_chamber(model, layout)
    return model


def trace_2_hungry_off_food_pointing() -> str:
    """Hungry agent in the corridor with food visible eastward AND memory
    pointing east. Tests whether memory + anticipated_food coherently
    steer (the case memory is supposed to help)."""
    model = _build_synthetic_model(layout_name="food_ladder")
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    # Place in the corridor (between hazard and food zone), low energy.
    layout = food_ladder_layout()
    corridor_x = (layout.hazard_x_max + layout.food_x_min) // 2
    target_y = layout.height // 2
    new_body = replace(agent.body, x=corridor_x, y=target_y, energy=25.0)
    agent.body = new_body
    agent.cell = model.cell_at(corridor_x, target_y)
    # Plant a strong east tendency.
    assert isinstance(agent.memory, DirectionalMemory)
    agent.memory.pleasure_tendency[2] = 8.0  # east
    rows = _candidate_breakdowns(model, agent)
    return (
        "## Trace 2 — hungry agent off food, food visible east, "
        "memory pointing east (synthetic)\n\n"
        f"```\n{_agent_state_summary(agent, model)}\n```\n\n" + _format_breakdown_table(rows) + "\n"
    )


def trace_3_sated_off_food_pointing() -> str:
    """Sated agent in the safe zone with memory pointing east. The sated
    regime is where the missing hunger-gate on novelty_pleasure matters
    most — anticipated_food_pleasure (gated on hunger) goes silent
    while novelty_pleasure stays at full strength."""
    model = _build_synthetic_model(layout_name="food_ladder")
    agent = next(a for a in model.agents if isinstance(a, HHAgent))
    layout = food_ladder_layout()
    safe_x = layout.safe_x_min + 2
    target_y = layout.height // 2
    new_body = replace(agent.body, x=safe_x, y=target_y, energy=model.body_config.max_energy)
    agent.body = new_body
    agent.cell = model.cell_at(safe_x, target_y)
    # Plant a strong east tendency.
    assert isinstance(agent.memory, DirectionalMemory)
    agent.memory.pleasure_tendency[2] = 8.0  # east
    rows = _candidate_breakdowns(model, agent)
    return (
        "## Trace 3 — sated agent off food, memory pointing east "
        "(synthetic)\n\n"
        f"```\n{_agent_state_summary(agent, model)}\n```\n\n" + _format_breakdown_table(rows) + "\n"
    )


# ---------------------------------------------------------------------------
# By-tick birth distribution from existing run artifacts.
# ---------------------------------------------------------------------------


def _read_birth_ticks(events_jsonl: Path) -> list[int]:
    """Read AgentBorn events from one events.jsonl, return their ticks."""
    ticks: list[int] = []
    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "AgentBorn":
                ticks.append(int(row["tick"]))
    return ticks


def _format_histogram(
    title: str, ticks: Iterable[int], *, bucket_size: int = 25, n_ticks: int = 200
) -> str:
    """Render a one-line histogram of ticks bucketed every ``bucket_size``."""
    counter: Counter[int] = Counter()
    for t in ticks:
        bucket = (t // bucket_size) * bucket_size
        counter[bucket] += 1
    out: list[str] = [f"### {title}", ""]
    out.append("| bucket (ticks) | births |")
    out.append("|---|---:|")
    for bucket_start in range(0, n_ticks, bucket_size):
        n = counter.get(bucket_start, 0)
        bar = "#" * n if n else ""
        out.append(f"| {bucket_start:3d}-{bucket_start + bucket_size - 1:3d} | {n} {bar} |")
    out.append(f"| **total** | **{sum(counter.values())}** |")
    out.append("")
    return "\n".join(out)


def birth_distribution_section(roots: dict[str, Path]) -> str:
    """Aggregate AgentBorn ticks across all seeds under each root."""
    out: list[str] = ["## By-tick birth distribution\n"]
    for label, root in roots.items():
        if not root.exists():
            out.append(f"*{label}: artifact tree not present at {root!s}*\n")
            continue
        all_ticks: list[int] = []
        seed_dirs = sorted(root.glob("seed-*"))
        for seed_dir in seed_dirs:
            jsonl = seed_dir / "events.jsonl"
            if jsonl.exists():
                all_ticks.extend(_read_birth_ticks(jsonl))
        out.append(
            _format_histogram(
                f"{label} (across {len(seed_dirs)} seeds)",
                all_ticks,
            )
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> None:
    out_root = Path("runs/fear-hunger-v0.13-profile")
    out_root.mkdir(parents=True, exist_ok=True)

    sections: list[str] = [
        "# v0.13 Phase 1 — memory-channel calibration profile\n",
        "Read-only diagnostic. Three pre-registered scenario traces "
        "show the per-candidate harness breakdown, then a by-tick "
        "birth-distribution histogram tests whether reproduction "
        "stalls after a first burst.\n",
        "Generated by `scripts/v0.13_profile.py`. See "
        "[[docs/experiments/fear_hunger_v0.13.md]] for pre-registration.\n",
    ]
    # Three trace 1 variants: winner (slow EMA, food_ladder), fast-EMA on
    # food_ladder, and fast-EMA on tight_gradient (where v0.12 EAT-overrides
    # cluster). Together they triangulate whether the override pattern is
    # an artifact of cell parameters, chamber, or both.
    sections.append(trace_1_hungry_on_food(fast_ema=False))
    sections.append(trace_1_hungry_on_food(fast_ema=True))
    sections.append(trace_1_hungry_on_food(fast_ema=True, layout_name="tight_gradient"))
    sections.append(trace_2_hungry_off_food_pointing())
    sections.append(trace_3_sated_off_food_pointing())

    sections.append(
        birth_distribution_section(
            {
                "v0.12b food_ladder ms1-md0.1 (winner)": Path(
                    "runs/fear-hunger-v0.12b/cells/ms1-md0.1"
                ),
                "v0.12b food_ladder mem-off (baseline)": Path(
                    "runs/fear-hunger-v0.12b/cells/mem-off"
                ),
                "v0.12a tight_gradient ms1-md0.1": Path("runs/fear-hunger-v0.12a/cells/ms1-md0.1"),
            }
        )
    )

    output = "\n".join(sections)
    out_path = out_root / "traces.md"
    out_path.write_text(output)
    print(f"wrote {out_path}")
    print(f"  {len(output.splitlines())} lines")


if __name__ == "__main__":
    main()
