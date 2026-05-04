"""Tests for the v0.7 reproduction-config grid sweep.

Pin the parametric factory's bounds-checking, the four-criterion
evaluator (births / food preserved / diversity / overpopulation),
the failure-mapping winner-selection logic, and a smoke test that
exercises the artifact tree shape.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from hedonism_harness.core.config import ReproductionConfig
from hedonism_harness.experiments.repro_configs import (
    SPEC_ENERGY_COST,
    SPEC_ENERGY_THRESHOLD,
    repro_cell_id,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.repro_grid import (
    DEFAULT_N_FOUNDERS,
    ENERGY_COST_LEVELS,
    ENERGY_THRESHOLD_LEVELS,
    OVERPOPULATION_MULTIPLIER,
    GridCell,
    GridCellAggregate,
    all_grid_cells,
    baseline_cell,
    cell_qualifies,
    run_repro_grid,
    select_winning_cell,
)

# ---------------------------------------------------------------------------
# Parametric factory
# ---------------------------------------------------------------------------


def test_grid_has_9_cells_in_two_axes() -> None:
    cells = all_grid_cells()
    assert len(cells) == 9
    assert len(ENERGY_THRESHOLD_LEVELS) == 3
    assert len(ENERGY_COST_LEVELS) == 3


def test_baseline_cell_is_spec_default_and_present_in_grid() -> None:
    """The (et=70, ec=35) baseline cell MUST be one of the 9 grid cells.

    The v0.7 design uses the SPEC-default cell as the baseline reference;
    if it's missing from the grid, criterion 2 (food preservation) has
    no comparison anchor.
    """
    base = baseline_cell()
    assert base.energy_threshold == SPEC_ENERGY_THRESHOLD
    assert base.energy_cost == SPEC_ENERGY_COST
    assert base in all_grid_cells()


def test_tuned_reproduction_config_returns_a_valid_repro_config() -> None:
    cfg = tuned_reproduction_config(energy_threshold=50.0, energy_cost=15.0)
    assert isinstance(cfg, ReproductionConfig)
    assert cfg.energy_threshold == 50.0
    assert cfg.energy_cost == 15.0
    # Other knobs must hold at SPEC defaults so the sweep is isolated.
    assert cfg.offspring_start_energy == 30.0
    assert cfg.min_age == 10
    assert cfg.hazard_threshold == 0.5


def test_tuned_reproduction_config_rejects_out_of_bounds_args() -> None:
    """Bounds checks must fire on typos."""
    with pytest.raises(ValueError, match="energy_threshold"):
        tuned_reproduction_config(energy_threshold=-1.0, energy_cost=15.0)
    with pytest.raises(ValueError, match="energy_threshold"):
        tuned_reproduction_config(energy_threshold=200.0, energy_cost=15.0)
    with pytest.raises(ValueError, match="energy_cost"):
        tuned_reproduction_config(energy_threshold=70.0, energy_cost=-5.0)
    with pytest.raises(ValueError, match="energy_cost"):
        tuned_reproduction_config(energy_threshold=70.0, energy_cost=200.0)


def test_repro_cell_id_is_stable_and_filesystem_safe() -> None:
    assert repro_cell_id(energy_threshold=70.0, energy_cost=35.0) == "et70-ec35"
    assert repro_cell_id(energy_threshold=50.0, energy_cost=15.0) == "et50-ec15"
    # :g formatting trims trailing zeros.
    assert repro_cell_id(energy_threshold=60.0, energy_cost=25.0) == "et60-ec25"


# ---------------------------------------------------------------------------
# Four-criterion evaluator
# ---------------------------------------------------------------------------


def _agg(
    cell_label: str,
    *,
    energy_threshold: float = 70.0,
    energy_cost: float = 35.0,
    **kwargs: object,
) -> GridCellAggregate:
    base: dict[str, object] = {
        "cell_id": cell_label,
        "energy_threshold": energy_threshold,
        "energy_cost": energy_cost,
        "n_seeds": 8,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
        "seeds_with_any_births": 0,
        "total_starvation_deaths": 30,
        "total_food_events": 11,
        "total_hazard_entries": 24,
        "total_hazard_damage": 0.0,
        "total_births": 0,
        "total_reproduction_requests": 0,
        "total_moves": 0,
        "total_stays": 0,
        "mean_population_end": 0.125,
        "max_population_end": 1,
    }
    base.update(kwargs)
    return GridCellAggregate(**base)  # type: ignore[arg-type]


def test_cell_qualifies_passes_when_all_four_criteria_hold() -> None:
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cell = _agg(
        "winner",
        total_births=3,
        total_food_events=11,  # >= baseline (preserved)
        seeds_with_any_starvation=8,
        max_population_end=4,  # <= 15
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_zero_births() -> None:
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cell = _agg(
        "no-births",
        total_births=0,
        total_food_events=11,
        seeds_with_any_starvation=8,
        max_population_end=1,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_food_drops_below_baseline() -> None:
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cell = _agg(
        "tanked-food",
        total_births=2,
        total_food_events=10,  # < baseline
        seeds_with_any_starvation=8,
        max_population_end=3,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_zero_starvation() -> None:
    """Diversity-collapse guard: every seed full of survivors == over-tuned."""
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cell = _agg(
        "no-diversity",
        total_births=10,
        total_food_events=20,
        seeds_with_any_starvation=0,  # collapse
        max_population_end=10,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_overpopulation_explodes() -> None:
    """Overpopulation guard: one explosive seed disqualifies via max."""
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cap = OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS  # 15
    cell = _agg(
        "explosive",
        total_births=40,
        total_food_events=30,
        seeds_with_any_starvation=4,
        max_population_end=cap + 1,  # 16 — one seed broke the cap
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_passes_when_max_population_equals_cap() -> None:
    """Boundary check: max_population_end == 3 * n_founders is allowed."""
    baseline = _agg("baseline", total_food_events=11, max_population_end=1, total_births=0)
    cap = OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS
    cell = _agg(
        "at-cap",
        total_births=20,
        total_food_events=30,
        seeds_with_any_starvation=4,
        max_population_end=cap,
    )
    assert cell_qualifies(cell, baseline) is True


# ---------------------------------------------------------------------------
# Winner selection (failure-mapping)
# ---------------------------------------------------------------------------


def test_select_winning_cell_returns_none_when_no_qualifier() -> None:
    baseline = _agg("baseline", total_food_events=11, total_births=0)
    cells = [_agg("c1"), _agg("c2"), _agg("c3")]
    assert select_winning_cell(cells, baseline) is None


def test_select_winning_cell_picks_highest_total_births() -> None:
    baseline = _agg("baseline", total_food_events=11, total_births=0)
    common = {
        "total_food_events": 11,
        "seeds_with_any_starvation": 8,
        "max_population_end": 4,
    }
    cells = [
        _agg("c-low", total_births=2, **common),
        _agg("c-high", total_births=7, **common),
        _agg("c-mid", total_births=4, **common),
    ]
    winner = select_winning_cell(cells, baseline)
    assert winner is not None
    assert winner.cell_id == "c-high"


def test_select_winning_cell_tiebreaks_by_distance_to_spec() -> None:
    """When two cells tie on births, pick the one closer to SPEC defaults
    (et=70, ec=35). Conservative-tightening rule."""
    baseline = _agg("baseline", total_food_events=11, total_births=0)
    common = {
        "total_births": 5,
        "total_food_events": 11,
        "seeds_with_any_starvation": 8,
        "max_population_end": 4,
    }
    near_spec = _agg("near", energy_threshold=60.0, energy_cost=25.0, **common)
    far_spec = _agg("far", energy_threshold=50.0, energy_cost=15.0, **common)
    winner = select_winning_cell([near_spec, far_spec], baseline)
    assert winner is not None
    assert winner.cell_id == "near"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_smoke_run_with_tiny_grid_writes_artifacts(tmp_path: Path) -> None:
    """Two-cell mini grid + one seed; pins the artifact tree shape.

    The (70, 35) baseline cell must be one of the cells supplied so the
    driver can resolve the baseline reference without a separate run.
    """
    cells = [
        GridCell(energy_threshold=50.0, energy_cost=15.0),
        baseline_cell(),  # (70, 35) — required as the baseline reference
    ]
    aggs, baseline, winner = run_repro_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == "et70-ec35"

    batch_root = tmp_path / "smoke"
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()

    # comparison.csv should have one row per unique cell (baseline appears once).
    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert len(rows) == len(cells)
    assert rows[0]["cell_id"] == "et70-ec35"  # baseline first
    assert {r["cell_id"] for r in rows} == {c.id for c in cells}

    # winner.txt always written, even when winner is None.
    assert (batch_root / "winner.txt").is_file()
    text = (batch_root / "winner.txt").read_text()
    if winner is None:
        assert "no qualifying cell" in text
    else:
        assert winner.cell_id in text


def test_smoke_run_raises_when_baseline_cell_missing(tmp_path: Path) -> None:
    """If the caller filters out the baseline cell, the driver must error
    rather than silently proceed without a comparison anchor."""
    cells = [GridCell(energy_threshold=50.0, energy_cost=15.0)]
    with pytest.raises(RuntimeError, match="baseline cell"):
        run_repro_grid(
            seeds=[1],
            runs_root=tmp_path,
            batch_id="smoke-missing-baseline",
            n_ticks=5,
            n_founders=2,
            cells=cells,
        )
