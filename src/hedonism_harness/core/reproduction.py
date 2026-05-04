"""Asexual reproduction: validity, child construction, request processing (SPEC §14).

Per SPEC §27.7 reproduction validity is checked at the action-filter layer
(``get_valid_actions``) so REPRODUCE is never a selectable action when the
parent cannot follow through. ``apply_action(REPRODUCE)`` itself only emits a
``ReproductionRequested`` event; the simulation loop calls
``process_reproduction`` to atomically charge the parent's energy and
construct the child on the same step (or skip with no charge if no adjacent
empty cell remains).

Children inherit their parent's ``lineage_id`` and get a fresh ``parent_id``
reference. Founder agents each get a unique ``lineage_id`` (assigned by the
simulation at world setup, not here).

Per SPEC §13.4 individual memory is not inherited in v0.1 — the agent wrapper
allocates a fresh ``ValenceMemory`` for the child if the policy requires one.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from hedonism_harness.core.body import AgentBody, make_body
from hedonism_harness.core.config import BodyConfig, ReproductionConfig
from hedonism_harness.core.traits import TraitConfig, mutate_traits
from hedonism_harness.core.world import CellKind, World, in_bounds

# Adjacent step offsets — von Neumann neighborhood (no diagonals).
_ADJACENT_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, 1),
    (0, -1),
    (1, 0),
    (-1, 0),
)


def _local_hazard_signal(world: World, x: int, y: int, radius: int = 2) -> float:
    """Sum hazard_damage / distance over an axial scan from (x, y).

    Mirrors the geometry of ``sensors._scan_axial`` so the reproduction
    hazard threshold reads the same kind of signal the agent's senses do.
    """
    total = 0.0
    for dx, dy in _ADJACENT_OFFSETS:
        for d in range(1, radius + 1):
            nx, ny = x + dx * d, y + dy * d
            if not in_bounds(world, nx, ny):
                break
            v = float(world.hazard_damage[nx, ny])
            if v != 0.0:
                total += v / d
    return total


def _is_placeable(
    world: World, x: int, y: int, occupied: frozenset[tuple[int, int]] | None
) -> bool:
    if not in_bounds(world, x, y):
        return False
    if CellKind(int(world.kind_layer[x, y])) == CellKind.WALL:
        return False
    return not (occupied is not None and (x, y) in occupied)


def find_adjacent_empty_cell(
    world: World,
    body: AgentBody,
    occupied: frozenset[tuple[int, int]] | None = None,
) -> tuple[int, int] | None:
    """Return an adjacent (von Neumann) cell that is in-bounds, not WALL, and unoccupied.

    Order is deterministic (N, S, E, W) so the same world state always yields
    the same placement under fixed seed.
    """
    for dx, dy in _ADJACENT_OFFSETS:
        nx, ny = body.x + dx, body.y + dy
        if _is_placeable(world, nx, ny, occupied):
            return (nx, ny)
    return None


def can_reproduce(
    world: World,
    body: AgentBody,
    config: ReproductionConfig,
    occupied: frozenset[tuple[int, int]] | None = None,
) -> bool:
    """Return True iff the parent meets every condition for reproduction.

    Conditions per SPEC §14 + §27.7:
      - energy >= energy_threshold
      - age >= min_age
      - local_hazard_signal <= hazard_threshold
      - at least one adjacent in-bounds non-WALL unoccupied cell exists
    """
    if body.energy < config.energy_threshold:
        return False
    if body.age < config.min_age:
        return False
    if _local_hazard_signal(world, body.x, body.y) > config.hazard_threshold:
        return False
    return find_adjacent_empty_cell(world, body, occupied) is not None


def make_child(
    parent: AgentBody,
    *,
    parent_rng: np.random.Generator,
    trait_config: TraitConfig,
    body_config: BodyConfig,
    reproduction_config: ReproductionConfig,
    child_id: int,
    x: int,
    y: int,
) -> AgentBody:
    """Construct a fresh child body from a parent (mutated traits, lineage inherited).

    The child's body is built from ``body_config`` defaults but overridden with
    ``offspring_start_energy``. Memory is not assigned here; the agent wrapper
    allocates one if its policy needs it (SPEC §13.4).
    """
    child_traits = mutate_traits(parent.traits, trait_config, parent_rng)
    fresh = make_body(
        body_id=child_id,
        lineage_id=parent.lineage_id,
        parent_id=parent.id,
        x=x,
        y=y,
        traits=child_traits,
        config=body_config,
    )
    return dataclasses.replace(fresh, energy=reproduction_config.offspring_start_energy)


def charge_parent(parent: AgentBody, config: ReproductionConfig) -> AgentBody:
    """Debit the parent's energy by ``config.energy_cost``, floored at 0."""
    new_energy = max(0.0, parent.energy - config.energy_cost)
    return dataclasses.replace(parent, energy=new_energy)


def process_reproduction(
    world: World,
    parent: AgentBody,
    *,
    parent_rng: np.random.Generator,
    trait_config: TraitConfig,
    body_config: BodyConfig,
    reproduction_config: ReproductionConfig,
    child_id: int,
    occupied: frozenset[tuple[int, int]] | None = None,
) -> tuple[AgentBody, AgentBody] | None:
    """Atomic reproduction step: charge parent + create child, or do nothing.

    Returns ``(updated_parent, child)`` on success. Returns ``None`` if no
    adjacent empty cell remains at process time (per SPEC §27.7, no energy
    is lost on failure).
    """
    placement = find_adjacent_empty_cell(world, parent, occupied)
    if placement is None:
        return None
    x, y = placement
    updated_parent = charge_parent(parent, reproduction_config)
    child = make_child(
        parent,
        parent_rng=parent_rng,
        trait_config=trait_config,
        body_config=body_config,
        reproduction_config=reproduction_config,
        child_id=child_id,
        x=x,
        y=y,
    )
    return (updated_parent, child)
