"""Pin ``HHModel.cell_at`` — the public seam over Mesa's per-version
private cell-lookup API.

The wrapper exists so a Mesa upgrade that renames the private
``OrthogonalVonNeumannGrid._cells`` mapping changes one method
(``HHModel.cell_at``) instead of every caller in ``mesa_agents.py``.
This test pins the contract: ``cell_at(x, y)`` must return the cell
whose coordinate is ``(x, y)``.
"""

from __future__ import annotations

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.model import HHModel


def test_cell_at_returns_cell_with_correct_coordinate() -> None:
    cfg = WorldConfig(seed=0, width=4, height=3, food_density=0.0, hazard_density=0.0)
    model = HHModel(cfg, founders=[])
    for x in range(cfg.width):
        for y in range(cfg.height):
            cell = model.cell_at(x, y)
            assert cell.coordinate == (x, y), (
                f"cell_at({x}, {y}).coordinate == {cell.coordinate} violates the (x, y) contract"
            )
