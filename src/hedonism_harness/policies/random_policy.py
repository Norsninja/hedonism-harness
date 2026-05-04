"""RandomPolicy — uniform sample over valid actions (SPEC §15.1)."""

from __future__ import annotations

from hedonism_harness.core.actions import get_valid_actions
from hedonism_harness.policies.base import DecisionContext, PolicyDecision


class RandomPolicy:
    """Picks a valid action uniformly at random.

    Purpose per SPEC §15.1: baseline chaos, smoke testing the environment.
    """

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        valid = get_valid_actions(ctx.world, ctx.body)
        idx = int(ctx.rng.integers(0, len(valid)))
        return PolicyDecision(action=valid[idx], breakdown=None)
