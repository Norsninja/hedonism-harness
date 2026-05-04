"""ASCII snapshot renderer for ``World`` + an optional agent overlay (SPEC §27.11).

Per the ``viz/`` dependency rule (SPEC §27.11), this module imports
``core/`` only — never Mesa, never ``model.py``. The Mesa adapter that
collects ``AgentRenderInfo`` from an ``HHModel`` lives in
``experiments/snapshots.py``.

Glyph priority (top wins when stacked):

    agent (alive)  > agent (dead)  > HAZARD > FOOD > SAFE > WALL > EMPTY

Glyphs are ASCII-only:

    EMPTY  = '.'
    SAFE   = '_'
    FOOD   = '*'
    HAZARD = '#'
    WALL   = 'X'
    alive  = lowercase a..z (id mod 26) so small populations are visually
             distinguishable; falls back to '@' for ids past 26 alive.
    dead   = '+'  (was an agent, now a corpse — same priority precedence as
             alive but distinct glyph)

Coordinate convention: ``y`` increases northward (SPEC), so we emit rows
top-down with ``y = height-1`` first. Columns increase eastward.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from hedonism_harness.core.world import CellKind, World

# Single-char glyphs per cell kind. Keep these stable — tests assert against
# them directly.
TERRAIN_GLYPHS: dict[CellKind, str] = {
    CellKind.EMPTY: ".",
    CellKind.SAFE: "_",
    CellKind.FOOD: "*",
    CellKind.HAZARD: "#",
    CellKind.WALL: "X",
}

DEAD_AGENT_GLYPH = "+"
FALLBACK_AGENT_GLYPH = "@"


@dataclass(frozen=True)
class AgentRenderInfo:
    """Minimal render-side projection of an agent.

    The renderer takes a sequence of these so it does not need to know about
    Mesa, ``HHAgent``, or any model state — keeping ``viz/`` Mesa-free per
    SPEC §27.11.
    """

    agent_id: int
    x: int
    y: int
    alive: bool = True


def _agent_glyph(info: AgentRenderInfo) -> str:
    """Return the glyph used for an agent at render time."""
    if not info.alive:
        return DEAD_AGENT_GLYPH
    # 26-letter rotation so a small population is visually distinguishable.
    if info.agent_id >= 0:
        return chr(ord("a") + (info.agent_id % 26))
    return FALLBACK_AGENT_GLYPH


def render_world(
    world: World,
    agents: Sequence[AgentRenderInfo] = (),
) -> str:
    """Return an ASCII snapshot of the world with optional agent overlay.

    Each row is one terminal line; rows are separated by ``"\\n"`` with no
    trailing newline. Agents at the same cell are resolved by overlay
    priority: alive agents win over dead agents, dead agents win over
    terrain. If two alive agents (or two dead agents) share a cell — which
    a ``capacity=1`` Mesa grid forbids — the earliest in ``agents`` wins, so
    the output remains deterministic for tests.
    """
    width = world.width
    height = world.height

    # Start from the terrain-only grid.
    rows: list[list[str]] = []
    for y in range(height):
        row: list[str] = []
        for x in range(width):
            kind = CellKind(int(world.kind_layer[x, y]))
            row.append(TERRAIN_GLYPHS.get(kind, "?"))
        rows.append(row)

    # Apply agent overlays in two passes (dead first, then alive) so alive
    # always covers dead at the same cell. Within each pass, first-wins on
    # ties — already deterministic via input ordering.
    for info in agents:
        if info.alive:
            continue
        if 0 <= info.x < width and 0 <= info.y < height:
            rows[info.y][info.x] = DEAD_AGENT_GLYPH
    for info in agents:
        if not info.alive:
            continue
        if 0 <= info.x < width and 0 <= info.y < height:
            current = rows[info.y][info.x]
            # Don't overwrite an already-placed alive agent (first-wins on ties).
            if current in TERRAIN_GLYPHS.values() or current == DEAD_AGENT_GLYPH:
                rows[info.y][info.x] = _agent_glyph(info)

    # Emit y = height-1 at the top so north-up convention reads naturally.
    return "\n".join("".join(rows[y]) for y in range(height - 1, -1, -1))
