"""ReflexPolicy — handwritten priority rules (SPEC §15.2).

Priority:
    1. On a FOOD cell and hungry  -> EAT
    2. Hazard signal nearby       -> move opposite the strongest hazard direction
    3. Food signal nearby         -> move toward the strongest food direction
    4. Otherwise                  -> uniform random over valid move/STAY actions
"""

from __future__ import annotations

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.sensors import Observation
from hedonism_harness.policies.base import DecisionContext, PolicyDecision

# Map each direction's signal field name to the action that moves toward it
# (or away from it for hazards).
_SIGNAL_TO_TOWARD = {
    "north": Action.MOVE_NORTH,
    "south": Action.MOVE_SOUTH,
    "east": Action.MOVE_EAST,
    "west": Action.MOVE_WEST,
}
_SIGNAL_TO_AWAY = {
    "north": Action.MOVE_SOUTH,
    "south": Action.MOVE_NORTH,
    "east": Action.MOVE_WEST,
    "west": Action.MOVE_EAST,
}


class ReflexPolicy:
    """Authored survival rules for comparison against emergent valence behavior."""

    def __init__(self, hunger_threshold: float = 0.3) -> None:
        self.hunger_threshold = hunger_threshold

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        obs = ctx.observation
        valid = get_valid_actions(ctx.world, ctx.body)

        # 1. Eat if standing on food and at all hungry.
        if obs.on_food and obs.hunger_level > self.hunger_threshold and Action.EAT in valid:
            return PolicyDecision(action=Action.EAT)

        # 2. Flee from the strongest nearby hazard if any direction has signal > 0.
        haz = self._directional_signals(obs, "hazard")
        max_haz_dir, max_haz = max(haz.items(), key=lambda kv: kv[1])
        if max_haz > 0:
            flee = _SIGNAL_TO_AWAY[max_haz_dir]
            if flee in valid:
                return PolicyDecision(action=flee)
            # Try any valid move that isn't toward the hazard.
            seek_alt = self._first_valid_move_avoiding(valid, _SIGNAL_TO_TOWARD[max_haz_dir])
            if seek_alt is not None:
                return PolicyDecision(action=seek_alt)

        # 3. Move toward the strongest food signal.
        food = self._directional_signals(obs, "food")
        max_food_dir, max_food = max(food.items(), key=lambda kv: kv[1])
        if max_food > 0:
            seek = _SIGNAL_TO_TOWARD[max_food_dir]
            if seek in valid:
                return PolicyDecision(action=seek)

        # 4. Otherwise uniform random over moves and STAY. EAT is excluded
        # here because step 1 already considered (and rejected) eating.
        fallback = tuple(a for a in valid if a != Action.EAT)
        if not fallback:
            return PolicyDecision(action=Action.STAY)
        idx = int(ctx.rng.integers(0, len(fallback)))
        return PolicyDecision(action=fallback[idx])

    @staticmethod
    def _directional_signals(obs: Observation, kind: str) -> dict[str, float]:
        return {
            "north": getattr(obs, f"{kind}_signal_north"),
            "south": getattr(obs, f"{kind}_signal_south"),
            "east": getattr(obs, f"{kind}_signal_east"),
            "west": getattr(obs, f"{kind}_signal_west"),
        }

    @staticmethod
    def _first_valid_move_avoiding(valid: tuple[Action, ...], avoid: Action) -> Action | None:
        for action in (Action.MOVE_NORTH, Action.MOVE_SOUTH, Action.MOVE_EAST, Action.MOVE_WEST):
            if action == avoid:
                continue
            if action in valid:
                return action
        return None
