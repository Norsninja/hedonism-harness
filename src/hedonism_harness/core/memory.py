"""Per-agent valence memory (SPEC §13).

Three memory representations live here:

  - ``ValenceMemory`` (cell-exact, the v0.1 default): four parallel
    ``(width, height)`` NumPy layers — ``pleasure_ema``, ``pain_ema``,
    ``visits``, ``last_seen_tick``. Records "this cell was good/bad."
    Used by v0.9 + v0.10. Mismatched to consumable food: cells stay
    "good" in memory after their food is consumed (a stale-attractor
    pull), partially mitigated by per-tick decay (SPEC §13.3).
  - ``DirectionalMemory`` (v0.11 abstraction): two 4-vectors
    ``pleasure_tendency[N,S,E,W]`` and ``pain_tendency[N,S,E,W]``.
    Records "moving north tended to be good/bad." Survives food
    consumption naturally because the abstraction was never about a
    specific cell. Multi-cell-tier abstraction; rich for what a single
    cell would have.
  - ``ScalarMemory`` (v0.15 abstraction): one float
    ``last_total_food_signal`` plus the last move direction
    ``last_move_action``. The prokaryotic-chemotaxis tier — minimum
    state that yields run/tumble behavior. Used by ``GradientPolicy``
    in the sensor-blackout branch only (when ``best_net == 0``); see
    [[docs/experiments/fear_hunger_v0.15.md]] §"Mechanism".

Per SPEC §13.4, individual memories are not inherited — each newborn
agent gets a fresh memory if its policy is memory-enabled.

Per SPEC §27.11 this module imports stdlib + numpy only — except for
``Action``, which lives in ``core.actions`` and is needed by
``ScalarMemory.last_move_action``. ``core.actions`` does not import
``core.memory`` so the dependency is acyclic.

Memory is intentionally mutable: ``update_at*`` and ``decay_*`` mutate
arrays in place to avoid allocating per agent per tick.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hedonism_harness.core.actions import Action
from hedonism_harness.core.traits import Traits


@dataclass
class ValenceMemory:
    """NumPy-backed per-agent memory of pleasure/pain associations per cell."""

    pleasure_ema: np.ndarray  # float32 (W, H)
    pain_ema: np.ndarray  # float32 (W, H)
    visits: np.ndarray  # uint32 (W, H)
    last_seen_tick: np.ndarray  # int32 (W, H), -1 = never visited
    width: int
    height: int


def make_memory(width: int, height: int) -> ValenceMemory:
    """Allocate fresh zeroed memory layers for a (width, height) grid."""
    shape = (width, height)
    return ValenceMemory(
        pleasure_ema=np.zeros(shape, dtype=np.float32),
        pain_ema=np.zeros(shape, dtype=np.float32),
        visits=np.zeros(shape, dtype=np.uint32),
        last_seen_tick=np.full(shape, -1, dtype=np.int32),
        width=width,
        height=height,
    )


def alpha_for_strength(memory_strength: float) -> float:
    """Map ``traits.memory_strength`` (in [0, 1]) to the EMA update rate.

    High memory_strength -> slow update (current value barely overwrites old).
    Low memory_strength  -> fast update (current dominates).

    A floor of 0.05 ensures even maximum-memory agents still update at all
    so that learning never freezes entirely.
    """
    return max(0.05, 1.0 - memory_strength)


def update_at(
    memory: ValenceMemory,
    x: int,
    y: int,
    pleasure: float,
    pain: float,
    traits: Traits,
    tick: int,
) -> None:
    """EMA-update the memory cell at ``(x, y)`` with new pleasure/pain.

    Mutates ``memory`` in place. Per SPEC §13.2:
      ``new = (1 - alpha) * old + alpha * current``
    """
    alpha = alpha_for_strength(traits.memory_strength)
    memory.pleasure_ema[x, y] = (1.0 - alpha) * memory.pleasure_ema[x, y] + alpha * pleasure
    memory.pain_ema[x, y] = (1.0 - alpha) * memory.pain_ema[x, y] + alpha * pain
    memory.visits[x, y] += 1
    memory.last_seen_tick[x, y] = tick


def decay_all(memory: ValenceMemory, decay_rate: float) -> None:
    """In-place per-tick decay of pleasure_ema and pain_ema by (1 - decay_rate).

    Per SPEC §13.3. ``decay_rate`` typically comes from ``traits.memory_decay_rate``.
    """
    if decay_rate <= 0.0:
        return
    factor = 1.0 - decay_rate
    memory.pleasure_ema *= factor
    memory.pain_ema *= factor


def directional_signals(
    memory: ValenceMemory, origin_x: int, origin_y: int, radius: int
) -> dict[str, float]:
    """Sum ``pleasure_ema / distance`` and ``pain_ema / distance`` along each axis.

    Mirrors the geometry of ``sensors._scan_axial`` so memory readings combine
    naturally with external food/hazard signals in the harness.

    Returns a dict with all eight keys
    (``remembered_good_{N,S,E,W}`` and ``remembered_bad_{N,S,E,W}``).
    """
    steps = (
        ("north", 0, 1),
        ("south", 0, -1),
        ("east", 1, 0),
        ("west", -1, 0),
    )
    out: dict[str, float] = {}
    for name, dx, dy in steps:
        good = 0.0
        bad = 0.0
        for d in range(1, radius + 1):
            x, y = origin_x + dx * d, origin_y + dy * d
            if not (0 <= x < memory.width and 0 <= y < memory.height):
                break
            p = float(memory.pleasure_ema[x, y])
            q = float(memory.pain_ema[x, y])
            if p != 0.0:
                good += p / d
            if q != 0.0:
                bad += q / d
        out[f"remembered_good_{name}"] = good
        out[f"remembered_bad_{name}"] = bad
    return out


# ---------------------------------------------------------------------------
# DirectionalMemory (v0.11): bacterial-chemotaxis-style relative-direction
# learning. The agent does not record "this cell was good"; it records
# "moving north tended to be good/bad."
# ---------------------------------------------------------------------------

# Index convention for the 4-vectors. Matches ``actions.MOVE_DIRECTIONS``
# semantics: north = +y, east = +x.
_DIR_NORTH: int = 0
_DIR_SOUTH: int = 1
_DIR_EAST: int = 2
_DIR_WEST: int = 3
DIRECTION_NAMES: tuple[str, ...] = ("north", "south", "east", "west")


@dataclass
class DirectionalMemory:
    """Per-agent directional valence tendencies (4 directions).

    ``pleasure_tendency`` and ``pain_tendency`` each carry one EMA-tracked
    scalar per cardinal direction (north, south, east, west). Updates
    fire only when the agent moves: the move direction's slot absorbs
    the realized pleasure/pain through the same EMA recurrence as
    ``ValenceMemory`` (``alpha = alpha_for_strength(traits.memory_strength)``).
    """

    pleasure_tendency: np.ndarray  # float32 (4,)
    pain_tendency: np.ndarray  # float32 (4,)


def make_directional_memory() -> DirectionalMemory:
    """Allocate fresh zeroed directional tendencies."""
    return DirectionalMemory(
        pleasure_tendency=np.zeros(4, dtype=np.float32),
        pain_tendency=np.zeros(4, dtype=np.float32),
    )


def _direction_index(dx: int, dy: int) -> int | None:
    """Map a move displacement to its direction slot. ``None`` if no move."""
    if dx == 0 and dy == 1:
        return _DIR_NORTH
    if dx == 0 and dy == -1:
        return _DIR_SOUTH
    if dx == 1 and dy == 0:
        return _DIR_EAST
    if dx == -1 and dy == 0:
        return _DIR_WEST
    return None


def update_directional(
    memory: DirectionalMemory,
    dx: int,
    dy: int,
    pleasure: float,
    pain: float,
    traits: Traits,
) -> None:
    """EMA-update the tendency for the move direction implied by ``(dx, dy)``.

    Mutates ``memory`` in place. Skips when ``(dx, dy)`` is not a unit
    cardinal move (STAY / EAT / REPRODUCE keep the agent in place; those
    actions produce no directional learning signal).
    """
    idx = _direction_index(dx, dy)
    if idx is None:
        return
    alpha = alpha_for_strength(traits.memory_strength)
    memory.pleasure_tendency[idx] = (1.0 - alpha) * memory.pleasure_tendency[idx] + alpha * pleasure
    memory.pain_tendency[idx] = (1.0 - alpha) * memory.pain_tendency[idx] + alpha * pain


def decay_directional(memory: DirectionalMemory, decay_rate: float) -> None:
    """In-place per-tick decay of pleasure / pain tendency vectors.

    Per SPEC §13.3. ``decay_rate`` typically comes from
    ``traits.memory_decay_rate``.
    """
    if decay_rate <= 0.0:
        return
    factor = 1.0 - decay_rate
    memory.pleasure_tendency *= factor
    memory.pain_tendency *= factor


def directional_signals_directional(memory: DirectionalMemory) -> dict[str, float]:
    """Read the 8 ``remembered_good/bad_<dir>`` signals from a DirectionalMemory.

    Mirrors the output shape of ``directional_signals`` (cell-exact) so
    the sensor layer can treat both memory representations uniformly:
    each direction's good signal is ``max(0, pleasure_tendency)`` and
    each bad signal is ``max(0, pain_tendency)``. Negative tendencies
    (e.g., from a tick where pleasure was unusually low) clamp to 0 so
    the harness never sees "anti-pleasure" in a pleasure channel.
    """
    out: dict[str, float] = {}
    for idx, name in enumerate(DIRECTION_NAMES):
        p = float(memory.pleasure_tendency[idx])
        q = float(memory.pain_tendency[idx])
        out[f"remembered_good_{name}"] = p if p > 0.0 else 0.0
        out[f"remembered_bad_{name}"] = q if q > 0.0 else 0.0
    return out


# ---------------------------------------------------------------------------
# ScalarMemory (v0.15): chemotaxis-tier scalar memory. Two fields, no EMA,
# no spatial map. Used by ``GradientPolicy`` in the sensor-blackout branch
# only (when no direction has a strictly-positive net pull); see
# [[docs/experiments/fear_hunger_v0.15.md]] §"Mechanism".
# ---------------------------------------------------------------------------


@dataclass
class ScalarMemory:
    """Per-agent scalar comparator + last-move record.

    ``last_total_food_signal``: the sum of the four cardinal
    ``obs.food_signal_*`` channels at the previous tick. The cell uses
    the one-tick-lag derivative (``current_total - last_total_food_signal``)
    as a "is the food situation getting better" comparator, mirroring
    prokaryotic chemotaxis run/tumble.

    ``last_move_action``: the action selected on the previous tick.
    ``Action.STAY`` at construction (founders have no last move). Used
    by the policy's persistence branch to repeat the previous direction
    when the gradient is in blackout but the recent past was at least
    as good as the present.

    Defaults reflect the founder state: the cell has not yet sensed
    anything and has not yet moved.
    """

    last_total_food_signal: float = 0.0
    last_move_action: Action = Action.STAY


def make_scalar_memory() -> ScalarMemory:
    """Allocate a fresh ``ScalarMemory`` in its founder default state."""
    return ScalarMemory()


def update_scalar(
    memory: ScalarMemory,
    *,
    total_food_signal: float,
    action: Action,
) -> None:
    """In-place update of ``memory`` after a decision.

    Called once per tick after ``policy.decide`` has chosen ``action``
    against the observation that produced ``total_food_signal``. The
    one-tick lag the policy reads next tick is exactly the values
    written here.
    """
    memory.last_total_food_signal = float(total_food_signal)
    memory.last_move_action = action
