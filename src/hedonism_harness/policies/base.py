"""Policy protocol + decision context (SPEC §27.2).

A ``Policy`` is a stateless decision strategy composed into the Mesa agent
wrapper. Per SPEC §27.11, ``policies/`` may import ``core/`` but not Mesa,
not IO, not metrics.

The wrapper hands every policy the same ``DecisionContext`` bundle on every
tick and expects back a ``PolicyDecision`` (chosen action + optional
``ValenceBreakdown`` for hedonism-style policies).

Random and reflex policies ignore most fields of the context. Hedonism
policies use everything in it to call ``apply_action`` against a body copy
for each candidate action and score the predicted outcome with the harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from hedonism_harness.core.actions import Action
from hedonism_harness.core.body import AgentBody
from hedonism_harness.core.config import ActionConfig, BodyConfig, ReproductionConfig
from hedonism_harness.core.sensors import Observation
from hedonism_harness.core.valence import ValenceBreakdown
from hedonism_harness.core.world import World


@dataclass(frozen=True)
class DecisionContext:
    """All state a policy is allowed to read at decision time.

    The Mesa agent wrapper builds one of these per agent per tick before
    invoking ``policy.decide(ctx)``.
    """

    world: World
    body: AgentBody
    observation: Observation
    rng: np.random.Generator
    body_config: BodyConfig
    action_config: ActionConfig
    memory: object | None = None  # ValenceMemory when wired in step 12.
    reproduction_config: ReproductionConfig | None = None
    occupied: frozenset[tuple[int, int]] | None = None


@dataclass(frozen=True)
class PolicyDecision:
    """A policy's chosen action and the breakdown that justified it.

    ``breakdown`` is ``None`` for policies that do not score actions
    (RandomPolicy, ReflexPolicy). HedonismPolicy populates it.

    ``swayed_by_memory`` and ``action_without_memory`` are the v0.12
    action-aware-directional-memory introspection seam. They are
    populated only by ``HedonismPolicy`` when ``ctx.memory`` is a
    ``DirectionalMemory``: the policy then scores every candidate twice
    (once with the memory projection applied, once with memory zeroed)
    and reports whether the two argmax winners diverged. Other policies
    and other memory types leave these fields at their defaults.
    """

    action: Action
    breakdown: ValenceBreakdown | None = None
    swayed_by_memory: bool = False
    action_without_memory: Action | None = None


class Policy(Protocol):
    """Stateless decision strategy. Implementations are interchangeable."""

    def decide(self, ctx: DecisionContext) -> PolicyDecision: ...
