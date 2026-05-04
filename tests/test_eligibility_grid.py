"""Tests for the v0.8 structural eligibility-rescue grid sweep.

Pin the new ``eligibility_trait_config`` factory's bounds-checking, the
``EligibilityTelemetryCollector`` correctness (eligible_agent_ticks,
first_eligibility_tick, max_energy_after_min_age,
food_events_after_min_age, deaths_before_min_age, median_death_age),
the joint aggregator, the v0.7b 6-criterion evaluator applied to the
v0.8 cell type, winner selection, and a smoke test that exercises the
artifact tree (incl. the new diagnostic CSV columns).
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, random_traits, validate_traits
from hedonism_harness.experiments.eligibility_grid import (
    BASELINE_LAYOUT_NAME,
    BASELINE_SENSOR_RADIUS_MIN,
    LAYOUT_NAMES,
    SENSOR_RADIUS_MIN_LEVELS,
    EligibilityCell,
    EligibilityCellAggregate,
    aggregate,
    all_grid_cells,
    baseline_cell,
    cell_qualifies,
    eligibility_cell_id,
    run_eligibility_grid,
    select_winning_cell,
)
from hedonism_harness.experiments.eligibility_telemetry import (
    EligibilityTelemetry,
    EligibilityTelemetryCollector,
    empty_telemetry,
)
from hedonism_harness.experiments.fear_hunger_chamber import ChamberRunResult
from hedonism_harness.experiments.layouts import (
    food_ladder_layout,
    tight_gradient_layout,
)
from hedonism_harness.experiments.trait_configs import (
    eligibility_trait_config,
    tuned_trait_config,
)
from hedonism_harness.model import FounderSpec, HHModel

# ---------------------------------------------------------------------------
# eligibility_trait_config factory
# ---------------------------------------------------------------------------


def test_eligibility_trait_config_at_sr_min_one_is_v06_winner() -> None:
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = eligibility_trait_config(sensor_radius_min=1)
    for name in TRAIT_NAMES:
        assert cfg.range_for(name) == winner.range_for(name), name


def test_eligibility_trait_config_raises_sensor_floor_only() -> None:
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = eligibility_trait_config(sensor_radius_min=3)
    assert cfg.sensor_radius.min == 3
    assert cfg.sensor_radius.max == 6  # SPEC ceiling
    for name in TRAIT_NAMES:
        if name == "sensor_radius":
            continue
        assert cfg.range_for(name) == winner.range_for(name), name


def test_eligibility_trait_config_validates_against_spec() -> None:
    spec = TraitConfig()
    for sr_min in SENSOR_RADIUS_MIN_LEVELS:
        cfg = eligibility_trait_config(sensor_radius_min=sr_min)
        rng = np.random.default_rng(0)
        for _ in range(8):
            traits = random_traits(cfg, rng)
            validate_traits(traits, spec)


def test_eligibility_trait_config_rejects_out_of_spec_sr_min() -> None:
    with pytest.raises(ValueError, match="sensor_radius_min"):
        eligibility_trait_config(sensor_radius_min=0)
    with pytest.raises(ValueError, match="sensor_radius_min"):
        eligibility_trait_config(sensor_radius_min=99)


# ---------------------------------------------------------------------------
# Grid + cell ID
# ---------------------------------------------------------------------------


def test_grid_has_9_cells_in_two_axes() -> None:
    cells = all_grid_cells()
    assert len(cells) == 9
    assert len(LAYOUT_NAMES) == 3
    assert len(SENSOR_RADIUS_MIN_LEVELS) == 3


def test_baseline_is_tight_gradient_sr1_and_in_grid() -> None:
    base = baseline_cell()
    assert base.layout_name == BASELINE_LAYOUT_NAME
    assert base.sensor_radius_min == BASELINE_SENSOR_RADIUS_MIN
    assert base in all_grid_cells()


def test_eligibility_cell_id_uses_short_layout_form() -> None:
    assert eligibility_cell_id(layout_name="tight_gradient", sensor_radius_min=1) == "tight-sr1"
    assert eligibility_cell_id(layout_name="widened_gradient", sensor_radius_min=2) == "widened-sr2"
    assert eligibility_cell_id(layout_name="food_ladder", sensor_radius_min=3) == "ladder-sr3"


# ---------------------------------------------------------------------------
# EligibilityTelemetryCollector — behavior on a real model
# ---------------------------------------------------------------------------


class _AlwaysReproducePolicy:
    """Picks REPRODUCE if valid; STAY otherwise. Test-only fixture."""

    def decide(self, ctx):  # type: ignore[no-untyped-def]
        from hedonism_harness.core.actions import Action, get_valid_actions
        from hedonism_harness.policies.base import PolicyDecision

        valid = get_valid_actions(ctx.world, ctx.body, ctx.reproduction_config, ctx.occupied)
        if Action.REPRODUCE in valid:
            return PolicyDecision(action=Action.REPRODUCE, breakdown=None)
        return PolicyDecision(action=Action.STAY, breakdown=None)


def _build_repro_ready_model() -> tuple[HHModel, ReproductionConfig]:
    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=0, hazard_threshold=10.0)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysReproducePolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    return model, repro_cfg


class _AlwaysStayPolicy:
    """Always picks STAY. Test-only fixture so the founder remains eligible
    across many ticks instead of immediately reproducing and falling below
    the threshold."""

    def decide(self, ctx):  # type: ignore[no-untyped-def]
        from hedonism_harness.core.actions import Action
        from hedonism_harness.policies.base import PolicyDecision

        return PolicyDecision(action=Action.STAY, breakdown=None)


def test_telemetry_counts_eligibility_for_eligible_founder() -> None:
    """A founder that meets all reproduction conditions every tick must be
    counted at least once. Use STAY so the parent does not exhaust its
    energy by reproducing."""
    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=0, hazard_threshold=10.0)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysStayPolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    collector = EligibilityTelemetryCollector(model, repro_cfg)
    collector.connect()
    try:
        for _ in range(3):
            model.step()
            collector.observe_tick()
    finally:
        collector.disconnect()
    telem = collector.finalize()
    # Founder is eligible from the start (min_age=0, energy >= threshold).
    # STAY costs only the action's stay_cost + base metabolism, so it
    # remains above the 70 threshold for all 3 ticks.
    assert telem.eligible_agent_ticks >= 3
    assert telem.had_any_eligibility is True
    assert telem.first_eligibility_tick is not None
    assert telem.first_eligibility_tick >= 1  # observed AFTER first step


def test_telemetry_max_energy_after_min_age_filters_by_age() -> None:
    """``max_energy_after_min_age`` must not include observations made
    while the agent is younger than ``min_age``."""
    world_cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=80.0)
    # min_age=2 — founder is too young at ticks 0 and 1.
    repro_cfg = ReproductionConfig(min_age=2)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=2, y=2, policy_factory=_AlwaysReproducePolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    collector = EligibilityTelemetryCollector(model, repro_cfg)
    collector.connect()
    try:
        for _ in range(5):
            model.step()
            collector.observe_tick()
    finally:
        collector.disconnect()
    telem = collector.finalize()
    # Energy drains via metabolism each tick; peak observable when age >= 2
    # is strictly less than starting_energy=80.
    assert telem.max_energy_after_min_age < 80.0
    assert telem.max_energy_after_min_age > 0.0


def test_telemetry_records_death_age_and_under_min_age_count() -> None:
    """An agent dying before min_age must be counted; the median death
    age aggregates over all observed deaths."""
    # Founder has tiny starting energy and high metabolism so it dies fast.
    world_cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=1.0)
    repro_cfg = ReproductionConfig(min_age=10)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=2, y=2, policy_factory=_AlwaysReproducePolicy)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    collector = EligibilityTelemetryCollector(model, repro_cfg)
    collector.connect()
    try:
        for _ in range(20):
            model.step()
            collector.observe_tick()
    finally:
        collector.disconnect()
    telem = collector.finalize()
    assert telem.deaths_before_min_age >= 1
    assert not math.isnan(telem.median_death_age)
    assert telem.median_death_age < 10.0  # died before min_age


def test_empty_telemetry_is_neutral() -> None:
    telem = empty_telemetry()
    assert telem.eligible_agent_ticks == 0
    assert telem.had_any_eligibility is False
    assert telem.first_eligibility_tick is None
    assert math.isnan(telem.median_death_age)


# ---------------------------------------------------------------------------
# Six-criterion evaluator (v0.7b set, applied to v0.8 cells)
# ---------------------------------------------------------------------------


def _result(
    *,
    seed: int = 1,
    births: int = 0,
    reproduction_requests: int = 0,
    food_events: int = 0,
    starvation_deaths: int = 0,
    population_end: int = 0,
    hazard_entries: int = 0,
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


def _telem(
    *,
    eligible: int = 0,
    first: int | None = None,
    max_energy: float = 0.0,
    food_after: int = 0,
    deaths_before: int = 0,
    median_death: float = math.nan,
) -> EligibilityTelemetry:
    return EligibilityTelemetry(
        eligible_agent_ticks=eligible,
        had_any_eligibility=eligible > 0,
        first_eligibility_tick=first,
        max_energy_after_min_age=max_energy,
        food_events_after_min_age=food_after,
        deaths_before_min_age=deaths_before,
        median_death_age=median_death,
    )


def _agg(
    cell_label: str,
    *,
    layout_name: str = "tight_gradient",
    sensor_radius_min: int = 1,
    **kwargs: object,
) -> EligibilityCellAggregate:
    base: dict[str, object] = {
        "cell_id": cell_label,
        "layout_name": layout_name,
        "sensor_radius_min": sensor_radius_min,
        "n_seeds": 8,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
        "seeds_with_any_births": 0,
        "seeds_with_reproduction_requests": 0,
        "seeds_with_reproduction_eligibility": 0,
        "total_starvation_deaths": 30,
        "total_food_events": 11,
        "total_hazard_entries": 24,
        "total_hazard_damage": 0.0,
        "total_births": 0,
        "total_reproduction_requests": 0,
        "total_eligible_agent_ticks": 0,
        "total_food_events_after_min_age": 0,
        "total_deaths_before_min_age": 0,
        "total_moves": 0,
        "total_stays": 0,
        "mean_population_end": 0.125,
        "max_population_end": 1,
        "births_per_request": 0.0,
        "mean_first_eligibility_tick": math.nan,
        "max_energy_after_min_age": 0.0,
        "median_death_age": math.nan,
    }
    base.update(kwargs)
    return EligibilityCellAggregate(**base)  # type: ignore[arg-type]


def test_cell_qualifies_passes_when_all_six_criteria_hold() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "winner",
        total_births=4,
        seeds_with_any_births=3,
        seeds_with_reproduction_requests=4,
        total_reproduction_requests=6,
        total_food_events=8,
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_only_one_seed_has_births() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "single-seed",
        total_births=4,
        seeds_with_any_births=1,
        seeds_with_reproduction_requests=1,
        total_reproduction_requests=4,
        total_food_events=7,
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is False


def test_cell_qualifies_uses_corrected_food_floor() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "at-floor",
        total_births=4,
        seeds_with_any_births=2,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,
        total_food_events=7,  # 11 - 4
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_invariant_violated() -> None:
    baseline = _agg("baseline", total_food_events=11)
    cell = _agg(
        "invariant-broken",
        total_births=5,
        seeds_with_any_births=3,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,  # < births
        total_food_events=10,
        seeds_with_any_starvation=8,
        max_population_end=3,
    )
    assert cell_qualifies(cell, baseline) is False


# ---------------------------------------------------------------------------
# Winner selection
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
        "total_food_events": 5,
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


def test_select_winning_cell_tiebreaks_by_distance_to_baseline() -> None:
    """When births tie, pick the cell closest to (tight_gradient, sr_min=1)
    in (layout_ordinal, sensor_radius_min) space."""
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
    near_baseline = _agg("near", layout_name="tight_gradient", sensor_radius_min=2, **common)
    far_baseline = _agg("far", layout_name="food_ladder", sensor_radius_min=3, **common)
    winner = select_winning_cell([near_baseline, far_baseline], baseline)
    assert winner is not None
    assert winner.cell_id == "near"


# ---------------------------------------------------------------------------
# Aggregate plumbing
# ---------------------------------------------------------------------------


def test_aggregate_pairs_results_with_telemetry() -> None:
    """The joint aggregate folds telemetry totals + per-seed telemetry-derived
    flags (e.g., seeds_with_reproduction_eligibility)."""
    cell = EligibilityCell(layout_name="tight_gradient", sensor_radius_min=2)
    pairs = [
        (
            _result(seed=1, births=2, reproduction_requests=3, food_events=4),
            _telem(eligible=10, first=15, max_energy=70.0, food_after=2, deaths_before=1),
        ),
        (
            _result(seed=2, births=0, reproduction_requests=0, food_events=5),
            _telem(eligible=0, first=None, max_energy=0.0),
        ),
    ]
    agg = aggregate(cell, pairs)
    assert agg.cell_id == "tight-sr2"
    assert agg.total_births == 2
    assert agg.total_reproduction_requests == 3
    assert agg.total_eligible_agent_ticks == 10
    assert agg.seeds_with_reproduction_eligibility == 1  # only seed=1 had eligibility
    assert agg.total_food_events_after_min_age == 2
    assert agg.total_deaths_before_min_age == 1
    assert agg.max_energy_after_min_age == 70.0
    assert agg.mean_first_eligibility_tick == 15.0  # only seed=1 contributed


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_smoke_run_with_tiny_grid_writes_artifacts(tmp_path: Path) -> None:
    """Two-cell mini grid + one seed; pins the artifact tree shape and the
    new diagnostic columns."""
    cells = [
        baseline_cell(),  # required
        EligibilityCell(layout_name="food_ladder", sensor_radius_min=3),
    ]
    aggs, baseline, winner = run_eligibility_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=15,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == "tight-sr1"
    batch_root = tmp_path / "smoke"
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()
    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert len(rows) == len(cells)
    assert rows[0]["cell_id"] == "tight-sr1"
    # New diagnostic columns must appear.
    for col in (
        "total_eligible_agent_ticks",
        "seeds_with_reproduction_eligibility",
        "max_energy_after_min_age",
        "median_death_age",
        "mean_first_eligibility_tick",
        "total_food_events_after_min_age",
        "total_deaths_before_min_age",
    ):
        assert col in rows[0], f"missing diagnostic column {col!r}"

    text = (batch_root / "winner.txt").read_text()
    if winner is None:
        assert "no qualifying cell" in text
    else:
        assert winner.cell_id in text


def test_smoke_run_raises_when_baseline_cell_missing(tmp_path: Path) -> None:
    cells = [EligibilityCell(layout_name="food_ladder", sensor_radius_min=3)]
    with pytest.raises(RuntimeError, match="baseline cell"):
        run_eligibility_grid(
            seeds=[1],
            runs_root=tmp_path,
            batch_id="smoke-missing-baseline",
            n_ticks=5,
            n_founders=2,
            cells=cells,
        )


def test_run_chamber_tick_observer_fires_each_step() -> None:
    """Direct test of the new tick_observer hook on run_chamber."""
    from hedonism_harness.experiments.fear_hunger_chamber import run_chamber

    layout = tight_gradient_layout()
    calls: list[int] = []

    def observer(model: HHModel) -> None:
        calls.append(model.tick_count)

    run_chamber(
        seed=1,
        runs_root=Path("/tmp"),
        run_id="observer-test",
        n_founders=2,
        n_ticks=5,
        layout=layout,
        write_outputs=False,
        tick_observer=observer,
    )
    # Observer fires after each model.step(), so tick_count progresses.
    assert len(calls) >= 1
    assert calls == sorted(calls)
    assert calls[0] >= 1


def test_run_chamber_food_ladder_runs_without_crashing() -> None:
    """End-to-end: the v0.8 food_ladder layout (which adds the pre-food
    band) must run a full episode through run_chamber without errors."""
    from hedonism_harness.experiments.fear_hunger_chamber import run_chamber

    result = run_chamber(
        seed=1,
        runs_root=Path("/tmp"),
        run_id="food-ladder-smoke",
        n_founders=2,
        n_ticks=20,
        layout=food_ladder_layout(),
        trait_config=eligibility_trait_config(sensor_radius_min=2),
        write_outputs=False,
    )
    assert result.ticks_completed > 0
