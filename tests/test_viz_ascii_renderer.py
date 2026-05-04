"""Tests for ``viz/ascii_renderer`` + the experiments/snapshots adapter.

Three things this test file enforces:

  1. Terrain glyphs at expected positions (round-trip CellKind -> char).
  2. Overlay priority: alive agent > dead agent > terrain.
  3. ``viz/`` does not import Mesa or the model layer (SPEC §27.11).
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.core.world import CellKind, build_world
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    build_chamber_layout,
    paint_chamber,
)
from hedonism_harness.experiments.snapshots import (
    collect_agent_render_info,
    render_model_snapshot,
)
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.random_policy import RandomPolicy
from hedonism_harness.viz.ascii_renderer import (
    DEAD_AGENT_GLYPH,
    TERRAIN_GLYPHS,
    AgentRenderInfo,
    render_world,
)


def _empty_world(width: int = 6, height: int = 4) -> WorldConfig:
    return WorldConfig(seed=1, width=width, height=height, food_density=0.0, hazard_density=0.0)


def test_empty_world_renders_only_terrain_glyphs() -> None:
    cfg = _empty_world(width=4, height=2)
    world = build_world(cfg)
    out = render_world(world)
    # height=2, width=4 -> exactly two rows of 4 chars each, '.' for EMPTY.
    assert out == "....\n...."


def test_terrain_glyphs_match_table() -> None:
    """Each CellKind renders to its glyph entry in TERRAIN_GLYPHS."""
    cfg = _empty_world(width=5, height=2)
    world = build_world(cfg)
    # Bottom row (y=0) carries the five glyph kinds in order.
    world.kind_layer[0, 0] = CellKind.EMPTY
    world.kind_layer[1, 0] = CellKind.SAFE
    world.kind_layer[2, 0] = CellKind.FOOD
    world.kind_layer[3, 0] = CellKind.HAZARD
    world.kind_layer[4, 0] = CellKind.WALL
    rows = render_world(world).split("\n")
    bottom = rows[-1]
    assert bottom == "._*#X"
    assert bottom[0] == TERRAIN_GLYPHS[CellKind.EMPTY]
    assert bottom[1] == TERRAIN_GLYPHS[CellKind.SAFE]
    assert bottom[2] == TERRAIN_GLYPHS[CellKind.FOOD]
    assert bottom[3] == TERRAIN_GLYPHS[CellKind.HAZARD]
    assert bottom[4] == TERRAIN_GLYPHS[CellKind.WALL]


def test_north_up_orientation() -> None:
    """The first emitted row corresponds to ``y = height - 1``."""
    cfg = _empty_world(width=3, height=3)
    world = build_world(cfg)
    # Mark the top row (y=2) with FOOD so we can identify it.
    for x in range(3):
        world.kind_layer[x, 2] = CellKind.FOOD
    rows = render_world(world).split("\n")
    assert rows[0] == "***"
    assert rows[1] == "..."
    assert rows[2] == "..."


def test_alive_agent_overlays_terrain() -> None:
    cfg = _empty_world(width=3, height=2)
    world = build_world(cfg)
    world.kind_layer[1, 1] = CellKind.FOOD
    info = AgentRenderInfo(agent_id=0, x=1, y=1, alive=True)
    rows = render_world(world, [info]).split("\n")
    # y=1 is the top row; agent at x=1 should appear as 'a' (id 0 -> 'a').
    assert rows[0] == ".a."
    # Bottom row is unchanged.
    assert rows[1] == "..."


def test_alive_agent_wins_over_dead_agent_at_same_cell() -> None:
    cfg = _empty_world(width=3, height=2)
    world = build_world(cfg)
    dead = AgentRenderInfo(agent_id=1, x=1, y=0, alive=False)
    alive = AgentRenderInfo(agent_id=2, x=1, y=0, alive=True)
    rows = render_world(world, [dead, alive]).split("\n")
    # Two rows total. Bottom row (y=0) holds the agents.
    assert rows[-1] == ".c."  # id 2 -> 'c'
    assert DEAD_AGENT_GLYPH not in rows[-1]


def test_dead_agent_overlays_terrain_when_no_alive() -> None:
    cfg = _empty_world(width=3, height=2)
    world = build_world(cfg)
    world.kind_layer[1, 0] = CellKind.HAZARD
    dead = AgentRenderInfo(agent_id=1, x=1, y=0, alive=False)
    rows = render_world(world, [dead]).split("\n")
    assert rows[-1][1] == DEAD_AGENT_GLYPH


def test_agent_glyph_uses_id_modulo_26() -> None:
    cfg = _empty_world(width=4, height=2)
    world = build_world(cfg)
    infos = [
        AgentRenderInfo(agent_id=0, x=0, y=0),
        AgentRenderInfo(agent_id=1, x=1, y=0),
        AgentRenderInfo(agent_id=25, x=2, y=0),
        AgentRenderInfo(agent_id=26, x=3, y=0),
    ]
    rows = render_world(world, infos).split("\n")
    # 26 % 26 -> 0 -> 'a'.
    assert rows[-1] == "abza"


def test_render_model_snapshot_uses_world_and_alive_agents() -> None:
    cfg = WorldConfig(seed=42, width=8, height=4, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        cfg,
        founders=[
            FounderSpec(x=2, y=1, policy_factory=RandomPolicy),
            FounderSpec(x=5, y=2, policy_factory=RandomPolicy),
        ],
    )
    snapshot = render_model_snapshot(model)
    rows = snapshot.split("\n")
    # height=4 -> 4 rows, top row is y=3.
    assert len(rows) == 4
    # Founders haven't moved yet. HHModel hands out body ids starting at 1, so
    # the first founder is id=1 -> 'b' and the second is id=2 -> 'c'.
    assert rows[3 - 1][2] == "b"  # y=1 -> row index 2, x=2.
    assert rows[3 - 2][5] == "c"  # y=2 -> row index 1, x=5.


def test_render_chamber_layout_matches_zone_columns() -> None:
    """The chamber rendered at t=0 places SAFE / HAZARD / FOOD glyphs in their columns."""
    layout = ChamberLayout()
    world_cfg = build_chamber_layout(layout).model_copy(update={"seed": 1})
    model = HHModel(world_cfg, founders=[])
    paint_chamber(model, layout)
    rows = render_model_snapshot(model).split("\n")
    # Sample any row — every row is identical in this layout.
    sample = rows[0]
    for x in range(layout.safe_x_min, layout.safe_x_max + 1):
        assert sample[x] == TERRAIN_GLYPHS[CellKind.SAFE], f"x={x}: expected SAFE"
    for x in range(layout.hazard_x_min, layout.hazard_x_max + 1):
        assert sample[x] == TERRAIN_GLYPHS[CellKind.HAZARD], f"x={x}: expected HAZARD"
    for x in range(layout.food_x_min, layout.food_x_max + 1):
        assert sample[x] == TERRAIN_GLYPHS[CellKind.FOOD], f"x={x}: expected FOOD"


def test_collect_agent_render_info_is_sorted_and_lossless() -> None:
    cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        cfg,
        founders=[
            FounderSpec(x=0, y=0, policy_factory=RandomPolicy),
            FounderSpec(x=1, y=1, policy_factory=RandomPolicy),
            FounderSpec(x=2, y=2, policy_factory=RandomPolicy),
        ],
    )
    infos = list(collect_agent_render_info(model))
    assert [info.agent_id for info in infos] == sorted(info.agent_id for info in infos)
    assert all(isinstance(info, AgentRenderInfo) for info in infos)


def test_out_of_bounds_agent_positions_are_ignored() -> None:
    """Defensive: an AgentRenderInfo with bad coordinates must not crash or leak."""
    cfg = _empty_world(width=3, height=3)
    world = build_world(cfg)
    bad = AgentRenderInfo(agent_id=0, x=99, y=99, alive=True)
    out = render_world(world, [bad])
    # Same as terrain-only output.
    assert out == "...\n...\n..."


# ---------------------------------------------------------------------------
# Layering discipline (SPEC §27.11)
# ---------------------------------------------------------------------------


def test_viz_module_does_not_import_mesa_or_model() -> None:
    """``viz/`` may import core only — no Mesa, no model.py, no policies."""
    src = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "hedonism_harness"
        / "viz"
        / "ascii_renderer.py"
    ).read_text()
    tree = ast.parse(src)
    forbidden_prefixes = ("mesa", "hedonism_harness.model", "hedonism_harness.mesa_agents")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in forbidden_prefixes:
                    assert not alias.name.startswith(prefix), (
                        f"viz/ascii_renderer.py imports forbidden module: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for prefix in forbidden_prefixes:
                assert not module.startswith(prefix), (
                    f"viz/ascii_renderer.py imports forbidden module: {module}"
                )


def test_render_world_does_not_mutate_inputs() -> None:
    cfg = _empty_world(width=4, height=3)
    world = build_world(cfg)
    world.kind_layer[1, 1] = CellKind.HAZARD
    world.hazard_damage[1, 1] = 5.0
    before_kind = world.kind_layer.copy()
    before_hazard = world.hazard_damage.copy()
    info = AgentRenderInfo(agent_id=0, x=1, y=1)
    render_world(world, [info])
    np.testing.assert_array_equal(world.kind_layer, before_kind)
    np.testing.assert_array_equal(world.hazard_damage, before_hazard)
