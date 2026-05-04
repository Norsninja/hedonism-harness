"""Tests for the v0.9 memory-arm grid sweep.

Pin the new ``memory_trait_config`` factory's bounds-checking, the
``MemoryTelemetryCollector`` correctness (memory updates,
repeat_food_visits, median_food_event_tick), the joint aggregator, the
v0.7b 6-criterion evaluator applied to the v0.9 cell type, winner
selection (memory-on candidates only; tie-break to SPEC-permissive
memory cell), and a smoke that exercises the full artifact tree.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import pytest

from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
from hedonism_harness.core.traits import TRAIT_NAMES, TraitConfig, random_traits, validate_traits
from hedonism_harness.experiments.fear_hunger_chamber import ChamberRunResult
from hedonism_harness.experiments.memory_grid import (
    BASELINE_CELL_ID,
    MEMORY_DECAY_RATE_MAX_LEVELS,
    MEMORY_STRENGTH_MIN_LEVELS,
    PERMISSIVE_MEMORY_DECAY_RATE_MAX,
    PERMISSIVE_MEMORY_STRENGTH_MIN,
    MemoryCell,
    MemoryCellAggregate,
    aggregate,
    all_grid_cells,
    baseline_cell,
    cell_qualifies,
    run_memory_grid,
    select_winning_cell,
)
from hedonism_harness.experiments.memory_telemetry import (
    MemoryTelemetry,
    MemoryTelemetryCollector,
    empty_telemetry,
)
from hedonism_harness.experiments.trait_configs import (
    memory_cell_id,
    memory_trait_config,
    tuned_trait_config,
)
from hedonism_harness.model import FounderSpec, HHModel

# ---------------------------------------------------------------------------
# memory_trait_config factory
# ---------------------------------------------------------------------------


def test_memory_trait_config_at_permissive_defaults_is_v06_winner() -> None:
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = memory_trait_config(memory_strength_min=0.0, memory_decay_rate_max=0.1)
    for name in TRAIT_NAMES:
        assert cfg.range_for(name) == winner.range_for(name), name


def test_memory_trait_config_raises_strength_floor_only() -> None:
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = memory_trait_config(memory_strength_min=0.5, memory_decay_rate_max=0.1)
    assert cfg.memory_strength.min == 0.5
    assert cfg.memory_strength.max == 1.0  # SPEC ceiling
    for name in TRAIT_NAMES:
        if name == "memory_strength":
            continue
        assert cfg.range_for(name) == winner.range_for(name), name


def test_memory_trait_config_lowers_decay_ceiling_only() -> None:
    winner = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    cfg = memory_trait_config(memory_strength_min=0.0, memory_decay_rate_max=0.02)
    assert cfg.memory_decay_rate.min == 0.0  # SPEC floor preserved
    assert cfg.memory_decay_rate.max == 0.02
    for name in TRAIT_NAMES:
        if name == "memory_decay_rate":
            continue
        assert cfg.range_for(name) == winner.range_for(name), name


def test_memory_trait_config_validates_against_spec() -> None:
    spec = TraitConfig()
    for ms in MEMORY_STRENGTH_MIN_LEVELS:
        for md in MEMORY_DECAY_RATE_MAX_LEVELS:
            cfg = memory_trait_config(memory_strength_min=ms, memory_decay_rate_max=md)
            rng = np.random.default_rng(0)
            for _ in range(8):
                traits = random_traits(cfg, rng)
                validate_traits(traits, spec)


def test_memory_trait_config_rejects_out_of_spec_strength() -> None:
    with pytest.raises(ValueError, match="memory_strength_min"):
        memory_trait_config(memory_strength_min=-0.1, memory_decay_rate_max=0.1)
    with pytest.raises(ValueError, match="memory_strength_min"):
        memory_trait_config(memory_strength_min=1.5, memory_decay_rate_max=0.1)


def test_memory_trait_config_rejects_out_of_spec_decay() -> None:
    with pytest.raises(ValueError, match="memory_decay_rate_max"):
        memory_trait_config(memory_strength_min=0.0, memory_decay_rate_max=-0.01)
    with pytest.raises(ValueError, match="memory_decay_rate_max"):
        memory_trait_config(memory_strength_min=0.0, memory_decay_rate_max=0.5)


def test_memory_cell_id_format() -> None:
    assert memory_cell_id(memory_strength_min=0.0, memory_decay_rate_max=0.1) == "ms0-md0.1"
    assert memory_cell_id(memory_strength_min=0.5, memory_decay_rate_max=0.05) == "ms0.5-md0.05"
    assert memory_cell_id(memory_strength_min=1.0, memory_decay_rate_max=0.02) == "ms1-md0.02"


# ---------------------------------------------------------------------------
# Grid + cell ID
# ---------------------------------------------------------------------------


def test_grid_has_one_baseline_plus_nine_memory_cells() -> None:
    cells = all_grid_cells()
    assert len(cells) == 10
    # Exactly one baseline.
    baselines = [c for c in cells if not c.use_memory]
    assert len(baselines) == 1
    assert baselines[0].id == BASELINE_CELL_ID
    # 9 memory-on cells.
    memory_cells = [c for c in cells if c.use_memory]
    assert len(memory_cells) == 9
    assert len(MEMORY_STRENGTH_MIN_LEVELS) == 3
    assert len(MEMORY_DECAY_RATE_MAX_LEVELS) == 3


def test_baseline_is_mem_off_and_first_in_grid() -> None:
    base = baseline_cell()
    assert base.use_memory is False
    assert base.id == BASELINE_CELL_ID
    cells = all_grid_cells()
    assert cells[0].id == BASELINE_CELL_ID


def test_memory_cell_id_uses_short_form() -> None:
    cell = MemoryCell(use_memory=True, memory_strength_min=0.5, memory_decay_rate_max=0.05)
    assert cell.id == "ms0.5-md0.05"


# ---------------------------------------------------------------------------
# v0.10 layout parameterization
# ---------------------------------------------------------------------------


def test_memory_cell_default_layout_is_tight_gradient() -> None:
    """Default keeps the v0.9 caller bit-identical."""
    from hedonism_harness.experiments.layouts import tight_gradient_layout

    cell = MemoryCell(use_memory=True, memory_strength_min=0.0, memory_decay_rate_max=0.1)
    assert cell.layout_name == "tight_gradient"
    assert cell.to_layout() == tight_gradient_layout()


def test_memory_cell_food_ladder_layout_resolves() -> None:
    """v0.10: ``layout_name='food_ladder'`` returns the food_ladder factory."""
    from hedonism_harness.experiments.layouts import food_ladder_layout

    cell = MemoryCell(
        use_memory=True,
        memory_strength_min=0.0,
        memory_decay_rate_max=0.1,
        layout_name="food_ladder",
    )
    assert cell.to_layout() == food_ladder_layout()


def test_memory_cell_unknown_layout_raises() -> None:
    cell = MemoryCell(
        use_memory=True,
        memory_strength_min=0.0,
        memory_decay_rate_max=0.1,
        layout_name="not_a_real_layout",
    )
    with pytest.raises(ValueError, match="Unknown layout"):
        cell.to_layout()


def test_baseline_cell_threads_layout_name() -> None:
    """The mem-off baseline must run on the same layout as the rest of the grid."""
    base_tight = baseline_cell()
    base_ladder = baseline_cell(layout_name="food_ladder")
    assert base_tight.layout_name == "tight_gradient"
    assert base_ladder.layout_name == "food_ladder"
    # Cell ID is layout-agnostic — the layout context lives in batch_id.
    assert base_tight.id == BASELINE_CELL_ID
    assert base_ladder.id == BASELINE_CELL_ID


def test_all_grid_cells_threads_layout_name() -> None:
    """Every cell in the v0.10 grid carries layout_name='food_ladder'."""
    cells = all_grid_cells(layout_name="food_ladder")
    assert len(cells) == 10
    for c in cells:
        assert c.layout_name == "food_ladder"


def test_all_grid_cells_rejects_unknown_layout() -> None:
    with pytest.raises(ValueError, match="Unknown layout"):
        all_grid_cells(layout_name="nonsense_layout")


def test_baseline_mem_off_uses_v06_winner_trait_config_on_food_ladder() -> None:
    """The v0.10 mem-off cell must reproduce v0.8 ladder-sr1 setup exactly:
    same trait config (v0.6 winner = eligibility_trait_config(sr_min=1)),
    same reproduction config (et=50, ec=35), same layout (food_ladder),
    use_memory=False. This is the criterion-3 baseline reference and the
    determinism cross-check against the v0.8 artifact.
    """
    from hedonism_harness.experiments.trait_configs import (
        eligibility_trait_config,
        tuned_trait_config,
    )

    base = baseline_cell(layout_name="food_ladder")
    assert base.use_memory is False
    # v0.6 winner identity is what tuned_trait_config produces.
    expected = tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)
    assert base.to_trait_config() == expected
    # And that's the same TraitConfig as v0.8's eligibility_trait_config(sr_min=1).
    assert expected == eligibility_trait_config(sensor_radius_min=1)


def test_food_ladder_smoke_run(tmp_path: Path) -> None:
    """End-to-end: a tiny v0.10 grid on food_ladder runs and writes the
    same artifact tree shape as v0.9. Confirms layout parameterization
    flows through the driver."""
    from hedonism_harness.experiments.memory_grid import run_memory_grid

    cells = [
        baseline_cell(layout_name="food_ladder"),
        MemoryCell(
            use_memory=True,
            memory_strength_min=0.0,
            memory_decay_rate_max=0.1,
            layout_name="food_ladder",
        ),
    ]
    aggs, baseline, _winner = run_memory_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="ladder-smoke",
        n_ticks=10,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == BASELINE_CELL_ID
    batch_root = tmp_path / "ladder-smoke"
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()


# ---------------------------------------------------------------------------
# MemoryTelemetryCollector — behavior on a real model
# ---------------------------------------------------------------------------


class _AlwaysStayPolicy:
    """Always picks STAY. Test-only fixture so the founder doesn't move
    and the AteFood path is easy to control."""

    def decide(self, ctx):  # type: ignore[no-untyped-def]
        from hedonism_harness.core.actions import Action
        from hedonism_harness.policies.base import PolicyDecision

        return PolicyDecision(action=Action.STAY, breakdown=None)


def test_telemetry_counts_memory_updates_when_use_memory_true() -> None:
    """A memory-enabled founder that steps for N ticks must accumulate
    N updates in its memory (one per step)."""
    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=10)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysStayPolicy, use_memory=True)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    try:
        for _ in range(5):
            model.step()
            collector.observe_tick()
    finally:
        collector.disconnect()
    telem = collector.finalize()
    assert telem.agents_with_memory_updates == 1
    # update_at runs once per agent step, so visits.sum() == ticks stepped.
    assert telem.total_memory_updates == 5


def test_telemetry_zero_when_use_memory_false() -> None:
    """Founders without memory never appear in the per-agent visits map."""
    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)
    repro_cfg = ReproductionConfig(min_age=10)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysStayPolicy, use_memory=False)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    try:
        for _ in range(5):
            model.step()
            collector.observe_tick()
    finally:
        collector.disconnect()
    telem = collector.finalize()
    assert telem.agents_with_memory_updates == 0
    assert telem.total_memory_updates == 0


def test_telemetry_counts_repeat_food_visits_via_ate_food_events() -> None:
    """``repeat_food_visits`` = sum_over_agents(max(0, count - 1)).

    Drive the collector with synthetic ``AteFood`` events on a real model
    so the signal-bus path is exercised end-to-end.
    """
    from hedonism_harness.core.events import AteFood, signal_for

    world_cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    model = HHModel(world_cfg, founders=[])
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    try:
        sig = signal_for(AteFood)
        # agent 1 ate 3 times -> 2 repeat visits
        # agent 2 ate 1 time  -> 0 repeat visits
        # agent 3 ate 2 times -> 1 repeat visit
        for aid, count in [(1, 3), (2, 1), (3, 2)]:
            for _ in range(count):
                sig.send(model, event=AteFood(agent_id=aid, x=0, y=0, food_gained=1.0))
    finally:
        collector.disconnect()
    telem = collector.finalize()
    assert telem.repeat_food_visits == 3  # 2 + 0 + 1


def test_telemetry_median_food_event_tick_uses_model_clock() -> None:
    """Median tick is computed from the model's ``tick_count`` at the
    moment each ``AteFood`` event is observed."""
    from hedonism_harness.core.events import AteFood, signal_for

    world_cfg = WorldConfig(seed=1, width=4, height=4, food_density=0.0, hazard_density=0.0)
    model = HHModel(world_cfg, founders=[])
    collector = MemoryTelemetryCollector(model)
    collector.connect()
    sig = signal_for(AteFood)
    try:
        # Force tick advancement between sends so events carry distinct ticks.
        for tick in (5, 10, 15):
            model.tick_count = tick
            sig.send(model, event=AteFood(agent_id=1, x=0, y=0, food_gained=1.0))
    finally:
        collector.disconnect()
    telem = collector.finalize()
    assert telem.median_food_event_tick == 10.0
    assert telem.has_food_events is True


def test_empty_telemetry_is_neutral() -> None:
    telem = empty_telemetry()
    assert telem.agents_with_memory_updates == 0
    assert telem.total_memory_updates == 0
    assert telem.repeat_food_visits == 0
    assert math.isnan(telem.median_food_event_tick)


# ---------------------------------------------------------------------------
# Six-criterion evaluator (v0.7b set, applied to v0.9 cells)
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
    agents: int = 0,
    updates: int = 0,
    repeats: int = 0,
    median_tick: float = math.nan,
) -> MemoryTelemetry:
    return MemoryTelemetry(
        agents_with_memory_updates=agents,
        total_memory_updates=updates,
        repeat_food_visits=repeats,
        median_food_event_tick=median_tick,
    )


def _agg(
    cell_label: str,
    *,
    use_memory: bool = True,
    memory_strength_min: float = 0.0,
    memory_decay_rate_max: float = 0.1,
    **kwargs: object,
) -> MemoryCellAggregate:
    base: dict[str, object] = {
        "cell_id": cell_label,
        "use_memory": use_memory,
        "memory_strength_min": memory_strength_min,
        "memory_decay_rate_max": memory_decay_rate_max,
        "n_seeds": 8,
        "seeds_with_survivors": 1,
        "seeds_with_any_starvation": 8,
        "seeds_with_any_births": 0,
        "seeds_with_reproduction_requests": 0,
        "total_starvation_deaths": 30,
        "total_food_events": 10,
        "total_hazard_entries": 23,
        "total_hazard_damage": 0.0,
        "total_births": 0,
        "total_reproduction_requests": 0,
        "total_moves": 0,
        "total_stays": 0,
        "mean_population_end": 0.125,
        "max_population_end": 1,
        "births_per_request": 0.0,
        "total_agents_with_memory_updates": 0,
        "total_memory_updates": 0,
        "total_repeat_food_visits": 0,
        "mean_median_food_event_tick": math.nan,
    }
    base.update(kwargs)
    return MemoryCellAggregate(**base)  # type: ignore[arg-type]


def test_cell_qualifies_passes_when_all_six_criteria_hold() -> None:
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
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
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
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
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
    cell = _agg(
        "at-floor",
        total_births=4,
        seeds_with_any_births=2,
        seeds_with_reproduction_requests=3,
        total_reproduction_requests=4,
        total_food_events=6,  # 10 - 4
        seeds_with_any_starvation=8,
        max_population_end=4,
    )
    assert cell_qualifies(cell, baseline) is True


def test_cell_qualifies_fails_when_invariant_violated() -> None:
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
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
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
    cells = [_agg("c1"), _agg("c2"), _agg("c3")]
    assert select_winning_cell(cells, baseline) is None


def test_select_winning_cell_excludes_baseline_from_candidates() -> None:
    """The mem-off baseline is the comparison anchor; it MUST NOT win
    even if it satisfies all six criteria (which would only happen if v0.8
    tight-sr1 results were non-deterministic).
    """
    baseline = _agg(
        "baseline",
        use_memory=False,
        total_food_events=10,
        total_births=10,  # hypothetically qualifying
        seeds_with_any_births=8,
        seeds_with_reproduction_requests=8,
        total_reproduction_requests=10,
        seeds_with_any_starvation=8,
        max_population_end=5,
    )
    aggregates = [baseline]  # baseline is the only "qualifier" by criteria
    assert select_winning_cell(aggregates, baseline) is None


def test_select_winning_cell_picks_highest_total_births() -> None:
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
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


def test_select_winning_cell_tiebreaks_by_distance_to_permissive() -> None:
    """When births tie, pick the cell closest to the SPEC-permissive
    memory reference (ms_min=0.0, md_max=0.1) in (strength_min, decay_max)
    space. Conservative-tightening rule consistent with v0.7/v0.8."""
    baseline = _agg("baseline", use_memory=False, total_food_events=10)
    common = {
        "total_births": 5,
        "seeds_with_any_births": 3,
        "seeds_with_reproduction_requests": 3,
        "total_reproduction_requests": 8,
        "total_food_events": 6,
        "seeds_with_any_starvation": 8,
        "max_population_end": 4,
    }
    near = _agg(
        "near", memory_strength_min=0.0, memory_decay_rate_max=0.1, **common
    )  # at the reference
    far = _agg("far", memory_strength_min=1.0, memory_decay_rate_max=0.02, **common)  # far corner
    winner = select_winning_cell([near, far], baseline)
    assert winner is not None
    assert winner.cell_id == "near"

    # Verify the reference identity.
    assert PERMISSIVE_MEMORY_STRENGTH_MIN == 0.0
    assert PERMISSIVE_MEMORY_DECAY_RATE_MAX == 0.1


# ---------------------------------------------------------------------------
# Aggregate plumbing
# ---------------------------------------------------------------------------


def test_aggregate_pairs_results_with_telemetry() -> None:
    """The joint aggregate folds telemetry totals + per-seed contributions."""
    cell = MemoryCell(use_memory=True, memory_strength_min=0.5, memory_decay_rate_max=0.05)
    pairs = [
        (
            _result(seed=1, births=2, reproduction_requests=3, food_events=4),
            _telem(agents=2, updates=300, repeats=1, median_tick=50.0),
        ),
        (
            _result(seed=2, births=0, reproduction_requests=0, food_events=5),
            _telem(agents=2, updates=400, repeats=0, median_tick=70.0),
        ),
    ]
    agg = aggregate(cell, pairs)
    assert agg.cell_id == "ms0.5-md0.05"
    assert agg.use_memory is True
    assert agg.total_births == 2
    assert agg.total_reproduction_requests == 3
    assert agg.total_agents_with_memory_updates == 4
    assert agg.total_memory_updates == 700
    assert agg.total_repeat_food_visits == 1
    assert agg.mean_median_food_event_tick == 60.0


def test_aggregate_handles_seed_with_no_food_events_for_median() -> None:
    """Seeds whose median is NaN must be excluded from the mean; the
    aggregate's mean stays NaN if every seed lacked food events."""
    cell = MemoryCell(use_memory=True, memory_strength_min=0.0, memory_decay_rate_max=0.1)
    pairs = [
        (_result(seed=1), _telem(median_tick=math.nan)),
        (_result(seed=2), _telem(median_tick=math.nan)),
    ]
    agg = aggregate(cell, pairs)
    assert math.isnan(agg.mean_median_food_event_tick)


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_smoke_run_with_tiny_grid_writes_artifacts(tmp_path: Path) -> None:
    """Two-cell mini grid + one seed; pins the artifact tree shape and
    the new memory-diagnostic columns."""
    cells = [
        baseline_cell(),  # required as comparison anchor
        MemoryCell(use_memory=True, memory_strength_min=0.0, memory_decay_rate_max=0.1),
    ]
    aggs, baseline, winner = run_memory_grid(
        seeds=[1],
        runs_root=tmp_path,
        batch_id="smoke",
        n_ticks=10,
        n_founders=2,
        snapshot_tick=5,
        cells=cells,
    )
    assert len(aggs) == 2
    assert baseline.cell_id == BASELINE_CELL_ID
    batch_root = tmp_path / "smoke"
    for cell in cells:
        assert (batch_root / "cells" / cell.id / "seed-1").is_dir()
    rows = list(csv.DictReader((batch_root / "comparison.csv").open()))
    assert len(rows) == len(cells)
    assert rows[0]["cell_id"] == BASELINE_CELL_ID
    for col in (
        "use_memory",
        "memory_strength_min",
        "memory_decay_rate_max",
        "total_agents_with_memory_updates",
        "total_memory_updates",
        "total_repeat_food_visits",
        "mean_median_food_event_tick",
    ):
        assert col in rows[0], f"missing column {col!r}"
    text = (batch_root / "winner.txt").read_text()
    if winner is None:
        assert "no qualifying cell" in text
    else:
        assert winner.cell_id in text


def test_smoke_run_raises_when_baseline_cell_missing(tmp_path: Path) -> None:
    cells = [MemoryCell(use_memory=True, memory_strength_min=0.0, memory_decay_rate_max=0.1)]
    with pytest.raises(RuntimeError, match="baseline cell"):
        run_memory_grid(
            seeds=[1],
            runs_root=tmp_path,
            batch_id="smoke-missing-baseline",
            n_ticks=5,
            n_founders=2,
            cells=cells,
        )
