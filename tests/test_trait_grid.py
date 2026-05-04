"""Tests for the v0.6 trait-config grid sweep.

Pin the parametric factory's bounds-checking, the four-criterion
evaluator, and the failure-mapping winner-selection logic.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, random_traits, validate_traits
from hedonism_harness.experiments.trait_configs import (
    cell_id,
    permissive_trait_config,
    tuned_trait_config,
)
from hedonism_harness.experiments.trait_grid import (
    FEAR_MAX_LEVELS,
    HUNGER_MIN_LEVELS,
    RISK_MIN_LEVELS,
    GridCell,
    GridCellAggregate,
    all_grid_cells,
    cell_qualifies,
    run_trait_grid,
    select_winning_cell,
)

# ---------------------------------------------------------------------------
# Parametric factory
# ---------------------------------------------------------------------------


def test_grid_has_27_cells_in_three_axes() -> None:
    cells = all_grid_cells()
    assert len(cells) == 27
    assert len(FEAR_MAX_LEVELS) == 3
    assert len(HUNGER_MIN_LEVELS) == 3
    assert len(RISK_MIN_LEVELS) == 3


def test_grid_contains_v05_permissive_cell() -> None:
    """The v0.5 permissive cell (fear=1.5, hunger=1.0, risk=0.4) MUST be in
    the grid so v0.6 directly answers 'did v0.5 get lucky?'"""
    v05 = GridCell(fear_max=1.5, hunger_min=1.0, risk_min=0.4)
    assert v05 in all_grid_cells()

    v05_cfg = v05.to_trait_config()
    perm = permissive_trait_config()
    # The cell must produce a config matching the v0.5 permissive on every range.
    for name in TRAIT_NAMES:
        assert v05_cfg.range_for(name) == perm.range_for(name), name


def test_tuned_trait_config_validates_against_spec() -> None:
    """Any cell must produce a TraitConfig whose samples pass SPEC validation."""
    spec = TraitConfig()
    for cell in all_grid_cells():
        cfg = cell.to_trait_config()
        rng = np.random.default_rng(0)
        for _ in range(8):
            traits = random_traits(cfg, rng)
            validate_traits(traits, spec)


def test_tuned_trait_config_rejects_out_of_spec_args() -> None:
    """Bounds checks must fire on typos."""
    with pytest.raises(ValueError, match="fear_max"):
        tuned_trait_config(fear_max=5.0, hunger_min=1.0, risk_min=0.4)
    with pytest.raises(ValueError, match="hunger_min"):
        tuned_trait_config(fear_max=1.5, hunger_min=-0.1, risk_min=0.4)
    with pytest.raises(ValueError, match="risk_min"):
        tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=2.0)


def test_cell_id_is_stable_and_filesystem_safe() -> None:
    assert cell_id(fear_max=1.5, hunger_min=1.0, risk_min=0.4) == "f1.5-h1-r0.4"
    # Trimming trailing zeros via :g formatting keeps ids short.
    assert cell_id(fear_max=2.0, hunger_min=0.75, risk_min=0.25) == "f2-h0.75-r0.25"


# ---------------------------------------------------------------------------
# Four-criterion evaluator
# ---------------------------------------------------------------------------


def _agg(
    cell_label: str,
    *,
    fear_max: float = 1.5,
    hunger_min: float = 1.0,
    risk_min: float = 0.4,
    **kwargs: object,
) -> GridCellAggregate:
    base: dict[str, object] = {
        "cell_id": cell_label,
        "fear_max": fear_max,
        "hunger_min": hunger_min,
        "risk_min": risk_min,
        "n_seeds": 8,
        "seeds_with_survivors": 0,
        "seeds_with_any_starvation": 8,
        "total_starvation_deaths": 40,
        "total_food_events": 0,
        "total_hazard_entries": 0,
        "total_hazard_damage": 0.0,
        "total_births": 0,
        "total_moves": 0,
        "total_stays": 0,
        "mean_population_end": 0.0,
    }
    base.update(kwargs)
    return GridCellAggregate(**base)  # type: ignore[arg-type]


def test_cell_qualifies_passes_when_all_four_criteria_hold() -> None:
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    cell = _agg(
        "winner",
        total_food_events=8,
        total_hazard_entries=19,
        seeds_with_survivors=2,
        seeds_with_any_starvation=8,
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_no_survivors() -> None:
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    cell = _agg(
        "no-surv",
        total_food_events=20,
        total_hazard_entries=50,
        seeds_with_survivors=0,
        seeds_with_any_starvation=8,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_zero_starvation() -> None:
    """Diversity-collapse guard: every seed full of survivors == over-tuned."""
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    cell = _agg(
        "over-tuned",
        total_food_events=40,
        total_hazard_entries=200,
        seeds_with_survivors=8,
        seeds_with_any_starvation=0,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_food_not_above_baseline() -> None:
    baseline = _agg("baseline", total_food_events=5, total_hazard_entries=1)
    cell = _agg(
        "tied",
        total_food_events=5,  # equal, not greater
        total_hazard_entries=20,
        seeds_with_survivors=2,
        seeds_with_any_starvation=4,
    )
    assert cell_qualifies(cell, baseline) is False


# ---------------------------------------------------------------------------
# Winner selection (failure-mapping)
# ---------------------------------------------------------------------------


def test_select_winning_cell_returns_none_when_no_qualifier() -> None:
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    cells = [_agg("c1"), _agg("c2"), _agg("c3")]
    assert select_winning_cell(cells, baseline) is None


def test_select_winning_cell_picks_highest_food_events() -> None:
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    common = {
        "total_hazard_entries": 20,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
    }
    cells = [
        _agg("c-low", total_food_events=2, **common),
        _agg("c-high", total_food_events=10, **common),
        _agg("c-mid", total_food_events=5, **common),
    ]
    winner = select_winning_cell(cells, baseline)
    assert winner is not None
    assert winner.cell_id == "c-high"


def test_select_winning_cell_tiebreaks_by_distance_to_spec() -> None:
    """When two cells tie on food_events, pick the one closer to SPEC defaults
    (fear=3, hunger=0.25, risk=0). Tightest-conservative wins."""
    baseline = _agg("baseline", total_food_events=0, total_hazard_entries=1)
    common = {
        "total_food_events": 8,
        "total_hazard_entries": 20,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
    }
    near_spec = _agg("near", fear_max=2.0, hunger_min=0.75, risk_min=0.25, **common)
    far_spec = _agg("far", fear_max=1.0, hunger_min=1.25, risk_min=0.55, **common)
    winner = select_winning_cell([near_spec, far_spec], baseline)
    assert winner is not None
    assert winner.cell_id == "near"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_smoke_run_with_tiny_grid_writes_artifacts(tmp_path: Path) -> None:
    """Two-cell mini grid + one seed; pins the artifact tree shape."""
    cells = [
        GridCell(fear_max=1.0, hunger_min=1.0, risk_min=0.4),
        GridCell(fear_max=2.0, hunger_min=1.0, risk_min=0.4),
    ]
    aggs, baseline, winner = run_trait_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == "baseline-spec-default"

    batch_root = tmp_path / "smoke"
    assert (batch_root / "baseline-spec-default" / "seed-1").is_dir()
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()

    # comparison.csv has baseline + cells.
    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert len(rows) == 1 + len(cells)
    assert rows[0]["cell_id"] == "baseline-spec-default"
    assert {r["cell_id"] for r in rows[1:]} == {c.id for c in cells}

    # winner.txt always written, even when winner is None.
    assert (batch_root / "winner.txt").is_file()
    text = (batch_root / "winner.txt").read_text()
    if winner is None:
        assert "no qualifying cell" in text
    else:
        assert winner.cell_id in text
