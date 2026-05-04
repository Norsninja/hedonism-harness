"""Per-agent valence memory map (SPEC §13).

A ``ValenceMemory`` holds four parallel ``(width, height)`` NumPy layers:

  - ``pleasure_ema``: exponential moving average of pleasure felt at each cell.
  - ``pain_ema``: same for pain.
  - ``visits``: visit count per cell.
  - ``last_seen_tick``: tick number of the most recent visit.

Per SPEC §13.4, individual memories are not inherited in v0.1 — each newborn
agent gets a fresh memory if its policy is the memory-enabled variant.

Per SPEC §27.11 this module imports stdlib + numpy only.

Memory is intentionally mutable: ``update_at`` and ``decay_all`` mutate arrays
in place to avoid allocating ~64 KB per agent per tick.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
