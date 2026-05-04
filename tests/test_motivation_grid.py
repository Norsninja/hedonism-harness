"""Tests for the v0.7b reproduction-motivation grid sweep.

Pin the new ``motivation_trait_config`` factory's bounds-checking, the
six-criterion evaluator (incl. the principled corrected food rule and
the request-vs-birth invariant guard), the new metrics
(``births_per_request``, ``seeds_with_reproduction_requests``), winner
selection logic, and a smoke test that exercises the artifact tree.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, random_traits, validate_traits
from hedonism_harness.experiments.fear_hunger_chamber import ChamberRunResult
from hedonism_harness.experiments.motivation_grid import (
    DEFAULT_N_FOUNDERS,
    DRIVE_MIN_LEVELS,
    ENERGY_COST_FIXED,
    ENERGY_THRESHOLD_LEVELS,
    OVERPOPULATION_MULTIPLIER,
    SPEC_DRIVE_MIN,
    MotivationCell,
    MotivationCellAggregate,
    aggregate,
    all_grid_cells,
    baseline_cell,
    cell_qualifies,
    motivation_cell_id,
    run_motivation_grid,
    select_winning_cell,
)
from hedonism_harness.experiments.trait_configs import (
    motivation_trait_config,
    tuned_trait_config,
)

# ---------------------------------------------------------------------------
# Parametric factory
# ---------------------------------------------------------------------------


def test_grid_has_9_cells_in_two_axes() -> None:
    cells = all_grid_cells()
    assert len(cells) == 9
    assert len(ENERGY_THRESHOLD_LEVELS) == 3
    assert len(DRIVE_MIN_LEVELS) == 3


def test_baseline_is_joint_spec_default_and_present_in_grid() -> None:
    base = baseline_cell()
    assert base.energy_threshold == 70.0
    assert base.drive_min == SPEC_DRIVE_MIN
    assert base in all_grid_cells()


def test_energy_cost_is_fixed_at_spec_default() -> None:
    """v0.7b deliberately freezes the cost axis at the SPEC default."""
    assert ENERGY_COST_FIXED == 35.0


def test_motivation_trait_config_at_drive_min_zero_is_v06_winner() -> None:
    """drive_min=0.0 must reproduce the v0.6 winner trait config exactly."""
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = motivation_trait_config(drive_min=0.0)
    for name in TRAIT_NAMES:
        assert cfg.range_for(name) == winner.range_for(name), name


def test_motivation_trait_config_raises_drive_floor_only() -> None:
    """drive_min only changes ``reproduction_drive``; other ranges are
    identical to the v0.6 winner."""
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = motivation_trait_config(drive_min=1.0)
    assert cfg.reproduction_drive.min == 1.0
    assert cfg.reproduction_drive.max == 3.0  # SPEC ceiling preserved
    for name in TRAIT_NAMES:
        if name == "reproduction_drive":
            continue
        assert cfg.range_for(name) == winner.range_for(name), name


def test_motivation_trait_config_validates_against_spec() -> None:
    """Any drive_min in {0.0, 0.5, 1.0} must produce a TraitConfig whose
    samples pass SPEC validation."""
    spec = TraitConfig()
    for dm in DRIVE_MIN_LEVELS:
        cfg = motivation_trait_config(drive_min=dm)
        rng = np.random.default_rng(0)
        for _ in range(8):
            traits = random_traits(cfg, rng)
            validate_traits(traits, spec)


def test_motivation_trait_config_rejects_out_of_spec_drive_min() -> None:
    with pytest.raises(ValueError, match="drive_min"):
        motivation_trait_config(drive_min=-0.1)
    with pytest.raises(ValueError, match="drive_min"):
        motivation_trait_config(drive_min=5.0)


def test_motivation_cell_id_is_stable_and_filesystem_safe() -> None:
    assert motivation_cell_id(energy_threshold=70.0, drive_min=0.0) == "et70-dm0"
    assert motivation_cell_id(energy_threshold=50.0, drive_min=1.0) == "et50-dm1"
    assert motivation_cell_id(energy_threshold=60.0, drive_min=0.5) == "et60-dm0.5"


# ---------------------------------------------------------------------------
# New metrics: births_per_request + seeds_with_reproduction_requests
# ---------------------------------------------------------------------------


def _result(
    *,
    seed: int = 1,
    births: int = 0,
    reproduction_requests: int = 0,
    food_events: int = 0,
    hazard_entries: int = 0,
    starvation_deaths: int = 0,
    population_end: int = 0,
) -> ChamberRunResult:
    return ChamberRunResult(
        run_id=f"r-{seed}",
        seed=seed,
        ticks_completed=200,
        population_start=5,
        population_end=population_end,
        survivors=population_end,
        starvation_deaths=starvation_deaths,
        injury_deaths=0,
        food_events=food_events,
        hazard_entries=hazard_entries,
        hazard_damage_total=0.0,
        births=births,
        reproduction_requests=reproduction_requests,
        moves=0,
        stays=0,
        output_dir=Path("/tmp/never-read"),
    )


def test_births_per_request_is_zero_when_no_requests() -> None:
    cell = MotivationCell(energy_threshold=70.0, drive_min=0.0)
    agg = aggregate(cell, [_result(reproduction_requests=0, births=0) for _ in range(8)])
    assert agg.total_reproduction_requests == 0
    assert agg.total_births == 0
    assert agg.births_per_request == 0.0


def test_births_per_request_computes_ratio() -> None:
    cell = MotivationCell(energy_threshold=50.0, drive_min=1.0)
    results = [
        _result(seed=1, reproduction_requests=4, births=2, starvation_deaths=1, population_end=2),
        _result(seed=2, reproduction_requests=6, births=3, starvation_deaths=1, population_end=3),
    ]
    agg = aggregate(cell, results)
    assert agg.total_births == 5
    assert agg.total_reproduction_requests == 10
    assert agg.births_per_request == 0.5


def test_seeds_with_reproduction_requests_distinguishes_obsessive_from_general() -> None:
    """One obsessive seed (10 reqs) vs. five seeds each requesting once
    have the same ``total_reproduction_requests`` (10) but different
    ``seeds_with_reproduction_requests`` — that's the whole point."""
    cell = MotivationCell(energy_threshold=50.0, drive_min=1.0)
    obsessive = [
        _result(seed=1, reproduction_requests=10, births=2),
        *[_result(seed=s, reproduction_requests=0, births=0) for s in range(2, 9)],
    ]
    general = [_result(seed=s, reproduction_requests=2, births=1) for s in range(1, 6)] + [
        _result(seed=s, reproduction_requests=0, births=0) for s in range(6, 9)
    ]
    obs_agg = aggregate(cell, obsessive)
    gen_agg = aggregate(cell, general)
    assert obs_agg.total_reproduction_requests == 10
    assert gen_agg.total_reproduction_requests == 10
    assert obs_agg.seeds_with_reproduction_requests == 1
    assert gen_agg.seeds_with_reproduction_requests == 5


# ---------------------------------------------------------------------------
# Six-criterion evaluator
# ---------------------------------------------------------------------------


def _agg(
    cell_label: str,
    *,
    energy_threshold: float = 70.0,
    drive_min: float = 0.0,
    **kwargs: object,
) -> MotivationCellAggregate:
    base: dict[str, object] = {
        "cell_id": cell_label,
        "energy_threshold": energy_threshold,
        "drive_min": drive_min,
        "n_seeds": 8,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
        "seeds_with_any_births": 0,
        "seeds_with_reproduction_requests": 0,
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
        "births_per_request": 0.0,
    }
    base.update(kwargs)
    return MotivationCellAggregate(**base)  # type: ignore[arg-type]


def test_cell_qualifies_passes_when_all_six_criteria_hold() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "winner",
        total_births=4,
        seeds_with_any_births=3,
        seeds_with_reproduction_requests=4,
        total_reproduction_requests=6,
        total_food_events=8,  # >= baseline (11) - births (4) = 7
        seeds_with_any_starvation=8,
        max_population_end=4,
        births_per_request=4 / 6,
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_too_few_births() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "one-birth",
        total_births=1,
        seeds_with_any_births=1,
        seeds_with_reproduction_requests=1,
        total_reproduction_requests=1,
        total_food_events=10,
        seeds_with_any_starvation=8,
        max_population_end=1,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_births_concentrated_in_one_seed() -> None:
    """Diversity guard: 4 births in a single seed must still fail."""
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "obsessive",
        total_births=4,
        seeds_with_any_births=1,  # single-seed concentration
        seeds_with_reproduction_requests=1,
        total_reproduction_requests=4,
        total_food_events=7,  # >= 11 - 4
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_uses_corrected_food_floor() -> None:
    """Criterion 3: food_events >= baseline - births. A 4-event drop
    against 4 births is still qualifying because it matches the
    structural one-tick-displaces-one-food-event finding from v0.7."""
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "at-floor",
        total_births=4,
        seeds_with_any_births=2,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,
        total_food_events=7,  # exactly 11 - 4
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is True

    # One below the floor fails.
    cell_below = _agg(
        "below-floor",
        total_births=4,
        seeds_with_any_births=2,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,
        total_food_events=6,  # below 11 - 4
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell_below, baseline) is False


def test_cell_qualifies_fails_when_zero_starvation() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "no-diversity",
        total_births=10,
        seeds_with_any_births=8,
        seeds_with_reproduction_requests=8,
        total_reproduction_requests=10,
        total_food_events=20,
        seeds_with_any_starvation=0,  # collapse
        max_population_end=10,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_overpopulation_explodes() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cap = OVERPOPULATION_MULTIPLIER * DEFAULT_N_FOUNDERS  # 15
    cell = _agg(
        "explosive",
        total_births=40,
        seeds_with_any_births=8,
        seeds_with_reproduction_requests=8,
        total_reproduction_requests=40,
        total_food_events=30,
        seeds_with_any_starvation=4,
        max_population_end=cap + 1,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_fails_when_invariant_violated() -> None:
    """Criterion 6 — defense in depth. births > requests would indicate
    the metrics layer regressed; the criterion catches it."""
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "invariant-broken",
        total_births=5,
        seeds_with_any_births=3,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,  # < births — impossible if metrics are sound
        total_food_events=10,
        seeds_with_any_starvation=8,
        max_population_end=3,
    )
    assert cell_qualifies(cell, baseline) is False


# ---------------------------------------------------------------------------
# Winner selection (failure-mapping)
# ---------------------------------------------------------------------------


def test_select_winning_cell_returns_none_when_no_qualifier() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cells = [_agg("c1"), _agg("c2"), _agg("c3")]
    assert select_winning_cell(cells, baseline) is None


def test_select_winning_cell_picks_highest_total_births() -> None:
    baseline = _agg("baseline", total_food_events=11)
    common = {
        "seeds_with_any_births": 3,
        "seeds_with_reproduction_requests": 3,
        "total_reproduction_requests": 20,
        "total_food_events": 5,  # >= 11 - 6 (worst-case births here is 7)
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
    """When two cells tie on births, pick the one closer to joint SPEC
    defaults (et=70, dm=0.0)."""
    baseline = _agg("baseline", total_food_events=11)
    common = {
        "total_births": 5,
        "seeds_with_any_births": 3,
        "seeds_with_reproduction_requests": 3,
        "total_reproduction_requests": 8,
        "total_food_events": 7,
        "seeds_with_any_starvation": 8,
        "max_population_end": 4,
    }
    near_spec = _agg("near", energy_threshold=60.0, drive_min=0.5, **common)
    far_spec = _agg("far", energy_threshold=50.0, drive_min=1.0, **common)
    winner = select_winning_cell([near_spec, far_spec], baseline)
    assert winner is not None
    assert winner.cell_id == "near"


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_smoke_run_with_tiny_grid_writes_artifacts(tmp_path: Path) -> None:
    """Two-cell mini grid + one seed; pins the artifact tree shape and
    ensures the new metric columns appear in comparison.csv."""
    cells = [
        MotivationCell(energy_threshold=50.0, drive_min=1.0),
        baseline_cell(),  # required as the baseline reference
    ]
    aggs, baseline, winner = run_motivation_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == "et70-dm0"

    batch_root = tmp_path / "smoke"
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()

    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert len(rows) == len(cells)
    assert rows[0]["cell_id"] == "et70-dm0"  # baseline first
    # The two new metric columns must be present.
    assert "births_per_request" in rows[0]
    assert "seeds_with_reproduction_requests" in rows[0]

    assert (batch_root / "winner.txt").is_file()
    if winner is None:
        assert "no qualifying cell" in (batch_root / "winner.txt").read_text()
    else:
        assert winner.cell_id in (batch_root / "winner.txt").read_text()


def test_smoke_run_raises_when_baseline_cell_missing(tmp_path: Path) -> None:
    cells = [MotivationCell(energy_threshold=50.0, drive_min=1.0)]
    with pytest.raises(RuntimeError, match="baseline cell"):
        run_motivation_grid(
            seeds=[1],
            runs_root=tmp_path,
            batch_id="smoke-missing-baseline",
            n_ticks=5,
            n_founders=2,
            cells=cells,
        )
