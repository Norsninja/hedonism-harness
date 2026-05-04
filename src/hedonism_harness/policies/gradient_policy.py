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

v0.15 sensor-blackout branch
----------------------------
When ``best_net == 0`` (no direction has strictly-positive net pull) and
``ctx.memory`` is a ``ScalarMemory``, the policy fires a chemotaxis-style
run/tumble decision instead of falling through to STAY. See
[[docs/experiments/fear_hunger_v0.15.md]] §"Mechanism".

  - Sated veto: if ``obs.hunger_level <= 0`` -> STAY (energy economy).
  - ``blackout_mode == "chemotaxis"`` (default):
      * ``dS = current_total_food_signal - memory.last_total_food_signal``
      * ``dS >= 0`` and last move was a MOVE still in ``valid``: persist
        (return the same direction).
      * ``dS < 0`` and at least one MOVE is valid: tumble (uniform random
        over valid MOVE actions via ctx.rng).
      * Otherwise: STAY.
  - ``blackout_mode == "persistence_only"``: ignore ``dS`` entirely;
    persist if last move is a valid MOVE, else STAY. Tumble never fires.

The blackout branch is the only place ``ScalarMemory`` is consumed. With
``ctx.memory=None`` (the v0.14 default arm) the branch is skipped and
the policy is bit-identical to v0.14 regardless of ``blackout_mode``.

Per v0.2 spec §"Out of scope": no spatial map, no novelty, no
predict-one-step, no harness call. ScalarMemory is the cell-tier memory
budget — one float plus a categorical, not a spatial or directional map.
"""

from __future__ import annotations

from typing import Literal

from hedonism_harness.core.actions import Action, get_valid_actions
from hedonism_harness.core.memory import ScalarMemory
from hedonism_harness.policies.base import DecisionContext, PolicyDecision

# Direction -> (action, food_signal_attr, hazard_signal_attr).
_DIRECTIONS: tuple[tuple[Action, str, str], ...] = (
    (Action.MOVE_NORTH, "food_signal_north", "hazard_signal_north"),
    (Action.MOVE_SOUTH, "food_signal_south", "hazard_signal_south"),
    (Action.MOVE_EAST, "food_signal_east", "hazard_signal_east"),
    (Action.MOVE_WEST, "food_signal_west", "hazard_signal_west"),
)
_MOVE_ACTIONS: frozenset[Action] = frozenset(
    {Action.MOVE_NORTH, Action.MOVE_SOUTH, Action.MOVE_EAST, Action.MOVE_WEST}
)

BlackoutMode = Literal["chemotaxis", "persistence_only"]


class GradientPolicy:
    """Reflex cell — gradient-following decision rule. v0.2 spec §"Policy".

    ``blackout_mode`` (v0.15) selects the behavior when no direction has
    a strictly-positive net pull AND the agent carries a ``ScalarMemory``:

      - ``"chemotaxis"`` (default): persist while improving / steady,
        tumble while worsening. The thesis-aligned chemotaxis cell.
      - ``"persistence_only"``: persist regardless of the derivative.
        Used by arm B of the v0.15 comparison to isolate the
        persistence component from the derivative-tumble component.

    With ``ctx.memory=None`` the blackout branch is skipped and the
    policy is bit-identical to v0.14 regardless of ``blackout_mode``.
    """

    def __init__(self, blackout_mode: BlackoutMode = "chemotaxis") -> None:
        if blackout_mode not in ("chemotaxis", "persistence_only"):
            msg = f"blackout_mode must be 'chemotaxis' or 'persistence_only', got {blackout_mode!r}"
            raise ValueError(msg)
        self.blackout_mode: BlackoutMode = blackout_mode

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

        # Strictly-positive gradient wins outright (with tie-break).
        if best_net > 0.0:
            if len(ties) > 1:
                idx = int(ctx.rng.integers(0, len(ties)))
                best_action = ties[idx]
            return PolicyDecision(action=best_action)

        # Sensor blackout: no direction has a strictly-positive net pull.
        # v0.14 fell through to STAY here; v0.15 consults ScalarMemory if
        # one is attached.
        if isinstance(ctx.memory, ScalarMemory):
            blackout_action = self._blackout_decide(ctx, valid)
            return PolicyDecision(action=blackout_action)

        return PolicyDecision(action=Action.STAY)

    def _blackout_decide(self, ctx: DecisionContext, valid: tuple[Action, ...]) -> Action:
        """Resolve the v0.15 sensor-blackout case.

        Precondition: ``ctx.memory`` is a ``ScalarMemory`` and no direction
        has a strictly-positive gradient pull. Returns the action the cell
        will take. See module docstring for the decision tree.
        """
        memory = ctx.memory
        assert isinstance(memory, ScalarMemory)  # narrow for the type checker.

        obs = ctx.observation

        # Sated veto: a cell with no hunger does not waste energy on
        # speculative motion in a blackout.
        if obs.hunger_level <= 0.0:
            return Action.STAY

        last = memory.last_move_action
        last_is_valid_move = last in _MOVE_ACTIONS and last in valid

        if self.blackout_mode == "persistence_only":
            # Run regardless of derivative. Tests whether persistence alone
            # carries any compounding effect (arm B of v0.15).
            return last if last_is_valid_move else Action.STAY

        # blackout_mode == "chemotaxis": run while improving / steady,
        # tumble while worsening.
        current_total = (
            float(obs.food_signal_north)
            + float(obs.food_signal_south)
            + float(obs.food_signal_east)
            + float(obs.food_signal_west)
        )
        d_signal = current_total - memory.last_total_food_signal

        if d_signal >= 0.0 and last_is_valid_move:
            return last

        if d_signal < 0.0:
            valid_moves = tuple(a for a in _MOVE_ACTIONS if a in valid)
            if valid_moves:
                idx = int(ctx.rng.integers(0, len(valid_moves)))
                return valid_moves[idx]

        return Action.STAY
