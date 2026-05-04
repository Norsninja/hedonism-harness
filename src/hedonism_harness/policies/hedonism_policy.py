"""HedonismPolicy — predict-one-step + harness scoring (SPEC §12, §15.3).

Per SPEC §27.5 the policy uses ``apply_action`` itself (single source of truth)
to predict each candidate action's outcome against a body copy, then scores
the predicted state with the Hedonism Harness. The action with the highest
``ValenceBreakdown.total`` wins.

Per SPEC §12, a small ``exploration_noise`` probability bypasses scoring and
picks a uniformly random valid action — keeps populations from collapsing
into perfectly deterministic clones.
"""

from __future__ import annotations

import math

from hedonism_harness.core.actions import (
    Action,
    action_energy_cost,
    apply_action,
    get_valid_actions,
)
from hedonism_harness.core.sensors import observe
from hedonism_harness.core.valence import ValenceBreakdown, evaluate
from hedonism_harness.policies.base import DecisionContext, PolicyDecision


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

        best_action: Action = valid[0]
        best_score: float = -math.inf
        best_breakdown: ValenceBreakdown | None = None

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
            breakdown = evaluate(
                ctx.observation,
                predicted_obs,
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

        return PolicyDecision(action=best_action, breakdown=best_breakdown)
