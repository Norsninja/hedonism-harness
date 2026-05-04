"""HedonismPolicy — predict-one-step + harness scoring (SPEC §12, §15.3).

Per SPEC §27.5 the policy uses ``apply_action`` itself (single source of truth)
to predict each candidate action's outcome against a body copy, then scores
the predicted state with the Hedonism Harness. The action with the highest
``ValenceBreakdown.total`` wins.

Per SPEC §12, a small ``exploration_noise`` probability bypasses scoring and
picks a uniformly random valid action — keeps populations from collapsing
into perfectly deterministic clones.

v0.12 — action-aware directional memory projection
==================================================
``DirectionalMemory`` (v0.11) records "moving north tended to be good/bad"
as 4-vectors. The bare read (``directional_signals_directional``) returns
all four direction slots regardless of which candidate action is being
scored, so every candidate sees the same memory contribution and the
argmax is decision-degenerate (v0.11 result: bit-identical metrics across
all parameter cells). v0.12 fixes the plumbing without changing the
abstraction: when scoring ``MOVE_X`` the policy keeps only the X slot and
zeros the other three; for ``STAY`` / ``EAT`` / ``REPRODUCE`` it zeros all
four (those actions test no direction). To detect "memory swayed the
argmax" without changing valence math, on directional cells the policy
also scores every candidate a second time with the memory fields zeroed
and reports the two winners back via ``PolicyDecision.swayed_by_memory``
and ``action_without_memory``. ``ValenceMemory`` (cell-exact) and the
``None`` path are untouched and remain bit-identical to v0.10.
"""

from __future__ import annotations

import math
from dataclasses import replace

from hedonism_harness.core.actions import (
    Action,
    action_energy_cost,
    apply_action,
    get_valid_actions,
)
from hedonism_harness.core.memory import DirectionalMemory
from hedonism_harness.core.sensors import Observation, observe
from hedonism_harness.core.valence import ValenceBreakdown, evaluate
from hedonism_harness.policies.base import DecisionContext, PolicyDecision

# The 8 ``remembered_*`` fields the harness consumes via
# ``_remembered_good_total`` / ``_remembered_bad_total`` (see core/valence.py).
_MEMORY_FIELDS: tuple[str, ...] = (
    "remembered_good_north",
    "remembered_good_south",
    "remembered_good_east",
    "remembered_good_west",
    "remembered_bad_north",
    "remembered_bad_south",
    "remembered_bad_east",
    "remembered_bad_west",
)
_ZEROED_MEMORY_FIELDS: dict[str, float] = dict.fromkeys(_MEMORY_FIELDS, 0.0)
_ACTION_TO_DIRECTION_NAME: dict[Action, str] = {
    Action.MOVE_NORTH: "north",
    Action.MOVE_SOUTH: "south",
    Action.MOVE_EAST: "east",
    Action.MOVE_WEST: "west",
}


def _zero_memory_fields(obs: Observation) -> Observation:
    """Return ``obs`` with all 8 directional memory fields cleared to 0."""
    return replace(obs, **_ZEROED_MEMORY_FIELDS)


def _project_memory_for_action(obs: Observation, action: Action) -> Observation:
    """Project ``obs``'s 8 directional memory fields onto ``action``.

    ``MOVE_<DIR>``: keep only the ``DIR`` slot of pleasure / pain memory;
    zero the other three directions (and their pain counterparts).

    ``STAY`` / ``EAT`` / ``REPRODUCE``: zero all 8 slots — directional
    memory makes claims about *moves*; a non-move tests no direction.

    Used only on the ``DirectionalMemory`` path. For ``ValenceMemory`` the
    cell-exact ``directional_signals`` already differentiates candidates
    via their predicted ``(x, y)``; no projection is needed there.
    """
    name = _ACTION_TO_DIRECTION_NAME.get(action)
    if name is None:
        return _zero_memory_fields(obs)
    fields: dict[str, float] = dict(_ZEROED_MEMORY_FIELDS)
    fields[f"remembered_good_{name}"] = getattr(obs, f"remembered_good_{name}")
    fields[f"remembered_bad_{name}"] = getattr(obs, f"remembered_bad_{name}")
    return replace(obs, **fields)


class HedonismPolicy:
    """Score every valid action via the harness; pick the highest total.

    With probability ``exploration_noise`` (default 0.03 per SPEC §12) the
    policy bypasses scoring and picks a uniformly random valid action.
    """

    def __init__(self, exploration_noise: float = 0.03) -> None:
        if not (0.0 <= exploration_noise <= 1.0):
            msg = f"exploration_noise must be in [0, 1], got {exploration_noise}"
            raise ValueError(msg)
        self.exploration_noise = exploration_noise

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        valid = get_valid_actions(ctx.world, ctx.body, ctx.reproduction_config, ctx.occupied)

        # Exploration: skip scoring entirely.
        if self.exploration_noise > 0.0 and ctx.rng.random() < self.exploration_noise:
            idx = int(ctx.rng.integers(0, len(valid)))
            return PolicyDecision(action=valid[idx], breakdown=None)

        is_directional = isinstance(ctx.memory, DirectionalMemory)

        best_action: Action = valid[0]
        best_score: float = -math.inf
        best_breakdown: ValenceBreakdown | None = None

        # v0.12: on the directional path also track the would-be argmax
        # winner with memory fields zeroed. The diff between the two
        # winners is the per-decision "memory swayed the argmax" signal
        # surfaced through MemoryTelemetryCollector. Cell-exact and the
        # None path skip this branch entirely (zero overhead, bit-identical
        # behavior). The two scoring passes share ``predicted_obs`` /
        # ``cost`` so the cost is one extra ``evaluate(...)`` per candidate.
        no_mem_best_action: Action = valid[0]
        no_mem_best_score: float = -math.inf

        for candidate in valid:
            result = apply_action(
                ctx.world,
                ctx.body,
                candidate,
                ctx.body_config,
                ctx.action_config,
                ctx.rng,
            )
            # Predicted observation against the live world. EAT's WorldDelta
            # is intentionally not committed — the harness reads
            # ``obs_before.current_food_value`` for food_gained, so the
            # un-committed cell does not pollute the score.
            predicted_obs = observe(ctx.world, result.body, ctx.body_config, ctx.memory)
            cost = action_energy_cost(candidate, ctx.action_config, ctx.reproduction_config)

            scored_obs = (
                _project_memory_for_action(predicted_obs, candidate)
                if is_directional
                else predicted_obs
            )
            breakdown = evaluate(
                ctx.observation,
                scored_obs,
                ctx.body,
                result.body,
                candidate,
                cost,
                ctx.body.traits,
            )
            if breakdown.total > best_score:
                best_score = breakdown.total
                best_action = candidate
                best_breakdown = breakdown

            if is_directional:
                no_mem_obs = _zero_memory_fields(predicted_obs)
                no_mem_breakdown = evaluate(
                    ctx.observation,
                    no_mem_obs,
                    ctx.body,
                    result.body,
                    candidate,
                    cost,
                    ctx.body.traits,
                )
                if no_mem_breakdown.total > no_mem_best_score:
                    no_mem_best_score = no_mem_breakdown.total
                    no_mem_best_action = candidate

        if is_directional:
            return PolicyDecision(
                action=best_action,
                breakdown=best_breakdown,
                swayed_by_memory=best_action != no_mem_best_action,
                action_without_memory=no_mem_best_action,
            )
        return PolicyDecision(action=best_action, breakdown=best_breakdown)
