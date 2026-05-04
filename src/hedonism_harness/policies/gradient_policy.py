"""GradientPolicy — primitive reflex cell (v0.2 reflex-cell substrate).

Single-tick decision based on the agent's current observation only. No
predict-one-step. No call to ``evaluate``. No multi-component harness.

Decision rule (v0.2 spec §"Cell behaviors" + §"Architecture decisions"):

  1. If on a cell with food, return ``Action.EAT`` (reflex; no choice).
  2. Otherwise compute net pleasure-minus-pain pull per cardinal direction:

         pleasure_pull[d] = food_signal_d * pleasure_sensitivity * (1 + hunger_level)
         pain_pull[d]     = hazard_signal_d * fear_sensitivity * (1 - risk_tolerance)
         net[d]           = pleasure_pull[d] - pain_pull[d]

     STAY's net pull is 0. Pick the action with the highest net pull
     among valid actions, ties broken via ctx.rng.

  3. Never return ``Action.REPRODUCE`` — auto-reproduction is a
     substrate phase in ``model.step()``, not a behavior.

The hunger amplification ``(1 + hunger_level)`` is the only place internal
body state enters the policy. It implements substrate-aligned sensitization:
a hungry cell perceives food gradients more strongly. This mirrors real
chemotaxis where hunger-state modulates sensor gain.

Traits read by GradientPolicy:
  - ``pleasure_sensitivity``  (multiplier on pleasure pull)
  - ``fear_sensitivity``      (multiplier on pain pull)
  - ``risk_tolerance``        (counter-weighting on pain pull)
  - ``sensor_radius``         (consumed by ``sensors.observe``, not here)

All other Traits fields are inert under GradientPolicy. They still mutate
across generations (see core/traits.py) and remain in the lineage record.

Per v0.2 spec §"Out of scope": no memory, no novelty, no predict-one-step,
no harness call.
"""

from __future__ import annotations

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.policies.base import DecisionContext, PolicyDecision

# Direction -> (action, food_signal_attr, hazard_signal_attr).
_DIRECTIONS: tuple[tuple[Action, str, str], ...] = (
    (Action.MOVE_NORTH, "food_signal_north", "hazard_signal_north"),
    (Action.MOVE_SOUTH, "food_signal_south", "hazard_signal_south"),
    (Action.MOVE_EAST, "food_signal_east", "hazard_signal_east"),
    (Action.MOVE_WEST, "food_signal_west", "hazard_signal_west"),
)


class GradientPolicy:
    """Reflex cell — gradient-following decision rule. v0.2 spec §"Policy"."""

    def decide(self, ctx: DecisionContext) -> PolicyDecision:
        obs = ctx.observation
        body = ctx.body
        traits = body.traits

        valid = get_valid_actions(ctx.world, body, ctx.reproduction_config, ctx.occupied)

        # Reflex: on food, eat. No deliberation.
        if obs.on_food and obs.current_food_value > 0.0 and Action.EAT in valid:
            return PolicyDecision(action=Action.EAT)

        # Compute net pleasure-minus-pain pull per cardinal direction.
        # Hunger amplification on the pleasure channel — substrate-aligned
        # sensitization (a hungry cell perceives food gradients more strongly).
        hunger_amp = 1.0 + obs.hunger_level
        pleasure_w = traits.pleasure_sensitivity * hunger_amp
        pain_w = traits.fear_sensitivity * (1.0 - traits.risk_tolerance)

        # Net pull per cardinal MOVE direction. The cell only moves when
        # there is a strictly positive net pull along some direction —
        # neutral or negative gradients leave it in place (STAY). This
        # is the substrate-aligned semantics: a cell does not move
        # without a pleasure-pain reason, and STAY is the default rest
        # state, not one option among equals.
        best_action: Action = Action.STAY
        best_net: float = 0.0
        ties: list[Action] = []

        for action, food_attr, hazard_attr in _DIRECTIONS:
            if action not in valid:
                continue
            food_signal = float(getattr(obs, food_attr))
            hazard_signal = float(getattr(obs, hazard_attr))
            net = pleasure_w * food_signal - pain_w * hazard_signal
            if net > best_net:
                best_net = net
                best_action = action
                ties = [action]
            elif net == best_net and net > 0.0:
                ties.append(action)

        # Tie-break only among strictly-positive ties; otherwise STAY
        # remains the resting choice.
        if len(ties) > 1:
            idx = int(ctx.rng.integers(0, len(ties)))
            best_action = ties[idx]

        return PolicyDecision(action=best_action)
