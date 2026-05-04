"""Mesa -> render adapter (SPEC §27.11).

``viz/ascii_renderer`` only knows about ``core/World`` and a
plain ``AgentRenderInfo`` dataclass. This adapter walks an ``HHModel``,
projects each ``HHAgent`` to ``AgentRenderInfo``, and calls the renderer.

Living here (in ``experiments/``) instead of ``viz/`` preserves the
dependency direction: ``viz/`` may not import Mesa or the model layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.viz.ascii_renderer import AgentRenderInfo, render_world

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hedonism_harness.model import HHModel


def collect_agent_render_info(model: HHModel) -> Sequence[AgentRenderInfo]:
    """Project every ``HHAgent`` in the model to a render-side ``AgentRenderInfo``.

    Sorted by ``agent_id`` so the rendered output is deterministic across
    AgentSet iteration order.
    """
    infos = [
        AgentRenderInfo(
            agent_id=a.body.id,
            x=a.body.x,
            y=a.body.y,
            alive=a.body.alive,
        )
        for a in model.agents
        if isinstance(a, HHAgent)
    ]
    infos.sort(key=lambda info: info.agent_id)
    return infos


def render_model_snapshot(model: HHModel) -> str:
    """Return an ASCII snapshot of ``model.world`` with all agents overlaid."""
    return render_world(model.world, collect_agent_render_info(model))
