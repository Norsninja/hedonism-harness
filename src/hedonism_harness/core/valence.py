"""Hedonism Harness — converts predicted state into felt valence (SPEC §11).

This is the centerpiece module. The harness:

  - Takes a before / after pair of (Observation, AgentBody) plus the action
    that was applied and its energy cost.
  - Produces a ``ValenceBreakdown`` whose ``total`` is the score the policy
    should maximize, and whose component fields + ``details`` dict are the
    raw research output for debugging and analysis.

Per SPEC §11.1 the conceptual formula is:

    net_valence = pleasure - pain - fear - uncertainty - effort_cost

Each component is filtered through trait sensitivities. Per SPEC §27.5, the
harness is a pure function — no mutation, no IO, no globals.

v0.1 simplifications:
  - ``recovery_pleasure`` is wired but always zero (no health regeneration).
  - ``novelty_pleasure`` and ``uncertainty_pain`` read 0 because memory
    sensors return 0 until ``ValenceMemory`` lands in step 12. The wiring is
    in place so step 12 only adds non-zero readings, never new code paths.
  - ``reproduction_pleasure`` is wired and uses ``traits.reproduction_drive``;
    actual reproduction validity / child creation lands in step 9.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hedonism_harness.core.actions import Action
from hedonism_harness.core.body import AgentBody
from hedonism_harness.core.sensors import Observation
from hedonism_harness.core.traits import Traits


@dataclass(frozen=True)
class ValenceBreakdown:
    """Felt valence of a candidate action — total + components + raw details.

    ``total = pleasure - pain - fear - uncertainty - effort`` by construction.
    ``details`` carries every named subcomponent for inspection and unit tests.
    """

    total: float
    pleasure: float
    pain: float
    fear: float
    uncertainty: float
    effort: float
    details: dict[str, float] = field(default_factory=dict)


def _hazard_signal_total(obs: Observation) -> float:
    return (
        obs.hazard_signal_north
        + obs.hazard_signal_south
        + obs.hazard_signal_east
        + obs.hazard_signal_west
    )


def _remembered_good_total(obs: Observation) -> float:
    return (
        obs.remembered_good_north
        + obs.remembered_good_south
        + obs.remembered_good_east
        + obs.remembered_good_west
    )


def _remembered_bad_total(obs: Observation) -> float:
    return (
        obs.remembered_bad_north
        + obs.remembered_bad_south
        + obs.remembered_bad_east
        + obs.remembered_bad_west
    )


def evaluate(
    obs_before: Observation,
    obs_after: Observation,
    body_before: AgentBody,
    body_after: AgentBody,
    action: Action,
    action_energy_cost: float,
    traits: Traits,
) -> ValenceBreakdown:
    """Score the predicted outcome of one action through trait-filtered valence."""
    # ---- Pain (SPEC §11.2) -------------------------------------------------
    hunger_pain = (
        obs_after.hunger_level * traits.hunger_pain_sensitivity * (1.0 - traits.pain_tolerance)
    )
    injury_pain = (
        obs_after.injury_level * traits.injury_pain_sensitivity * (1.0 - traits.pain_tolerance)
    )
    # Hazard pain is the immediate next-tick damage from cell residency.
    hazard_pain = obs_after.current_hazard_damage * traits.injury_pain_sensitivity
    energy_cost_pain = action_energy_cost * traits.hunger_pain_sensitivity

    pain = hunger_pain + injury_pain + hazard_pain + energy_cost_pain

    # ---- Fear (SPEC §11.3) -------------------------------------------------
    # Fear reads the predicted hazard exposure: directional signals from the
    # destination + immediate residency. This is "what bad things might happen"
    # rather than "what just happened".
    predicted_hazard_risk = _hazard_signal_total(obs_after) + obs_after.current_hazard_damage
    # Memory adds remembered bad signals for cells around the destination.
    predicted_hazard_risk += _remembered_bad_total(obs_after)
    fear = predicted_hazard_risk * traits.fear_sensitivity * (1.0 - traits.risk_tolerance)

    # ---- Pleasure (SPEC §11.4) ---------------------------------------------
    # Eating: hunger at decision time amplifies the felt pleasure.
    food_gained = obs_before.current_food_value if action == Action.EAT else 0.0
    eating_pleasure = food_gained * obs_before.hunger_level * traits.pleasure_sensitivity

    # Safety: pleasure for reducing predicted hazard exposure between before/after.
    hazard_before = _hazard_signal_total(obs_before) + obs_before.current_hazard_damage
    hazard_after = _hazard_signal_total(obs_after) + obs_after.current_hazard_damage
    safety_reduction = max(0.0, hazard_before - hazard_after)
    safety_pleasure = safety_reduction * traits.pleasure_sensitivity

    # Recovery: positive health delta. Always zero in v0.1 (no regen mechanic).
    health_recovered = max(0.0, body_after.health - body_before.health)
    recovery_pleasure = health_recovered * traits.pleasure_sensitivity

    # Reproduction: opportunity is binary on the REPRODUCE action.
    reproduction_opportunity = 1.0 if action == Action.REPRODUCE else 0.0
    reproduction_pleasure = (
        reproduction_opportunity * traits.reproduction_drive * traits.pleasure_sensitivity
    )

    # Novelty: read from memory sensors (zero without memory in v0.1).
    novelty_score = _remembered_good_total(obs_after)
    novelty_pleasure = novelty_score * traits.novelty_drive

    pleasure = (
        eating_pleasure
        + safety_pleasure
        + recovery_pleasure
        + reproduction_pleasure
        + novelty_pleasure
    )

    # ---- Uncertainty (SPEC §11.5) ------------------------------------------
    # Without memory, uncertainty is zero. With memory, an unknown destination
    # produces uncertainty pain proportional to the agent's aversion.
    uncertainty_score = 0.0  # populated when memory.py lands (step 12).
    uncertainty = uncertainty_score * traits.uncertainty_aversion

    # ---- Effort cost -------------------------------------------------------
    # Already folded into pain via energy_cost_pain; surfaced separately so
    # the breakdown's effort field reads as the raw action cost (research clarity).
    effort = action_energy_cost

    # ---- Total -------------------------------------------------------------
    # SPEC §11.1: net = pleasure - pain - fear - uncertainty - effort_cost.
    # We have already counted action energy as energy_cost_pain above; the
    # spec's "- effort_cost" subtraction at the top level is the identical
    # quantity weighted differently. To match the spec literally and avoid
    # double-counting the same charge, we expose ``effort`` separately and
    # subtract it from the total — but with hunger sensitivity already applied
    # via energy_cost_pain. The net effect: an agent insensitive to hunger
    # still feels effort weakly via the raw effort term. This matches the
    # spec's framing where effort is a baseline drain on top of trait-filtered pain.
    total = pleasure - pain - fear - uncertainty - effort

    details: dict[str, float] = {
        "hunger_pain": hunger_pain,
        "injury_pain": injury_pain,
        "hazard_pain": hazard_pain,
        "energy_cost_pain": energy_cost_pain,
        "predicted_hazard_risk": predicted_hazard_risk,
        "eating_pleasure": eating_pleasure,
        "safety_pleasure": safety_pleasure,
        "recovery_pleasure": recovery_pleasure,
        "reproduction_pleasure": reproduction_pleasure,
        "novelty_pleasure": novelty_pleasure,
        "novelty_score": novelty_score,
        "uncertainty_score": uncertainty_score,
        "food_gained": food_gained,
    }

    return ValenceBreakdown(
        total=total,
        pleasure=pleasure,
        pain=pain,
        fear=fear,
        uncertainty=uncertainty,
        effort=effort,
        details=details,
    )
