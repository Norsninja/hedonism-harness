"""Smoke + determinism tests for the Fear-Hunger Conflict Chamber."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from hedonism_harness.core.world import CellKind
from hedonism_harness.experiments.batch import run_chamber_batch
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberLayout,
    build_chamber_layout,
    paint_chamber,
    run_chamber,
    spread_y,
)
from hedonism_harness.model import HHModel


def test_layout_columns_paint_correctly() -> None:
    layout = ChamberLayout()
    cfg = build_chamber_layout(layout).model_copy(update={"seed": 0})
    model = HHModel(cfg, founders=[])
    paint_chamber(model, layout)

    # Sample a row and verify column kinds.
    y = layout.height // 2
    for x in range(layout.safe_x_min, layout.safe_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.SAFE
    for x in range(layout.hazard_x_min, layout.hazard_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.HAZARD
        assert model.world.hazard_damage[x, y] > 0
    for x in range(layout.food_x_min, layout.food_x_max + 1):
        assert model.world.kind_layer[x, y] == CellKind.FOOD
        assert model.world.food_value[x, y] > 0
    # Gap columns between zones remain EMPTY.
    gap_x = layout.safe_x_max + 1
    assert model.world.kind_layer[gap_x, y] == CellKind.EMPTY


def test_run_chamber_writes_all_artifacts(tmp_path: Path) -> None:
    result = run_chamber(
        seed=42,
        runs_root=tmp_path,
        run_id="t1",
        n_founders=3,
        n_ticks=20,
    )
    assert result.run_id == "t1"
    assert result.population_start == 3
    assert result.ticks_completed > 0

    out_dir = tmp_path / "t1"
    expected = [
        "config.json",
        "manifest.json",
        "episode_metrics.csv",
        "agent_lifetimes.csv",
        "lineages.csv",
        "events.jsonl",
        "summary.md",
    ]
    for name in expected:
        f = out_dir / name
        assert f.is_file(), f"missing {name}"
        assert f.stat().st_size > 0

    # episode_metrics.csv has the seed we passed.
    rows = list(csv.DictReader((out_dir / "episode_metrics.csv").open()))
    assert len(rows) == 1
    assert rows[0]["seed"] == "42"

    # events.jsonl is in envelope shape: {"tick": int, "type": str, "event": dict}.
    lines = (out_dir / "events.jsonl").read_text().strip().splitlines()
    assert lines, "events.jsonl should not be empty"
    payload = json.loads(lines[0])
    assert {"tick", "type", "event"} <= set(payload.keys())


def test_run_chamber_is_deterministic_under_same_seed(tmp_path: Path) -> None:
    """Same seed -> same per-run summary fields. Validates the chamber driver
    didn't introduce hidden RNG (e.g. via wall-clock or dict ordering)."""
    a = run_chamber(seed=42, runs_root=tmp_path, run_id="a", n_founders=3, n_ticks=15)
    b = run_chamber(seed=42, runs_root=tmp_path, run_id="b", n_founders=3, n_ticks=15)

    fields_to_compare = (
        "ticks_completed",
        "population_end",
        "starvation_deaths",
        "injury_deaths",
        "food_events",
        "hazard_entries",
        "hazard_damage_total",
        "births",
        "reproduction_requests",
        "moves",
        "stays",
    )
    for f in fields_to_compare:
        assert getattr(a, f) == getattr(b, f), f"{f} diverged across same-seed runs"


def test_run_chamber_different_seed_produces_different_outcome(tmp_path: Path) -> None:
    """Seeds that change the trait roll + exploration_noise sequence must change
    at least one observed counter over a long-enough run.

    Short runs in the safe zone tend to alias (agents STAY, noise rarely
    fires), so we run long enough that metabolism + occasional moves diverge.
    """
    a = run_chamber(seed=42, runs_root=tmp_path, run_id="a", n_founders=3, n_ticks=80)
    b = run_chamber(seed=12345, runs_root=tmp_path, run_id="b", n_founders=3, n_ticks=80)
    # At least one non-trivial counter differs across seeds.
    assert (
        a.moves != b.moves
        or a.food_events != b.food_events
        or a.hazard_entries != b.hazard_entries
        or a.starvation_deaths != b.starvation_deaths
        or a.injury_deaths != b.injury_deaths
    )


def test_aggregator_sender_filtering_isolates_runs(tmp_path: Path) -> None:
    """Two chamber runs sharing a process must not cross-contaminate metrics.

    This is the practical test of the sender-filtering decision: the
    aggregators inside ``run_chamber`` are scoped to their model, so each
    run reports its own counters.
    """
    run_chamber(seed=1, runs_root=tmp_path, run_id="a", n_founders=2, n_ticks=10)
    run_chamber(seed=2, runs_root=tmp_path, run_id="b", n_founders=2, n_ticks=10)
    # If sender filtering were broken, run b would inherit run a's tallies
    # (running totals would never reset). They are independent objects, so
    # any equality is coincidence — but at least one counter usually differs.
    # The real guarantee is "they each only saw their own model's events" —
    # we assert this by counting per-run lifetime records.
    rows_a = list(csv.DictReader((tmp_path / "a" / "agent_lifetimes.csv").open()))
    rows_b = list(csv.DictReader((tmp_path / "b" / "agent_lifetimes.csv").open()))
    assert len(rows_a) == 2
    assert len(rows_b) == 2


def test_batch_runner_writes_summary_csv(tmp_path: Path) -> None:
    results = run_chamber_batch(
        seeds=[1, 2, 3],
        runs_root=tmp_path,
        batch_id="batch-A",
        n_ticks=10,
        n_founders=2,
    )
    assert len(results) == 3
    summary_csv = tmp_path / "batch-A" / "summary.csv"
    assert summary_csv.is_file()
    rows = list(csv.DictReader(summary_csv.open()))
    assert [r["seed"] for r in rows] == ["1", "2", "3"]
    # Each per-seed run dir exists.
    for seed in (1, 2, 3):
        run_dir = tmp_path / "batch-A" / f"seed-{seed}"
        assert run_dir.is_dir()
        assert (run_dir / "summary.md").is_file()


# ---------------------------------------------------------------------------
# Spawn safety (capacity=1 grid invariant)
# ---------------------------------------------------------------------------


def test_spread_y_returns_unique_coordinates_for_n_le_height() -> None:
    """Every supported (n, height) pair must produce unique y-coordinates;
    Mesa's capacity=1 grid silently fails if two founders land on the same
    cell at init."""
    for height in (3, 4, 6, 8, 10):
        for n in range(1, height + 1):
            ys = spread_y(n, height)
            assert len(ys) == n
            assert len(set(ys)) == n, f"duplicates at n={n}, height={height}: {ys}"
            assert all(0 <= y < height for y in ys), (
                f"out-of-bounds y at n={n}, height={height}: {ys}"
            )


def test_spread_y_preserves_v01_to_v08_distribution() -> None:
    """Pin the historical step-wise distribution so existing experiment
    artifacts (v0.1..v0.8) remain bit-reproducible."""
    # Default chamber: n=5, height=6.
    assert spread_y(5, 6) == [0, 1, 2, 3, 4]
    # tight_gradient + n=2 founders.
    assert spread_y(2, 6) == [0, 3]
    # Single founder lands at midpoint.
    assert spread_y(1, 6) == [3]
    # Empty population (defensive).
    assert spread_y(0, 6) == []


def test_spread_y_raises_when_n_exceeds_height() -> None:
    """Capacity=1 grid + n > height would force duplicates. The function
    must reject the request loudly instead of silently colliding founders.
    """
    with pytest.raises(ValueError, match="capacity=1"):
        spread_y(7, 6)
    with pytest.raises(ValueError, match="capacity=1"):
        spread_y(11, 10)


def test_run_chamber_rejects_overflow_founders() -> None:
    """End-to-end: passing n_founders > layout.height must surface as a
    ValueError from run_chamber via spread_y, not as a Mesa placement
    crash deep in the step loop."""
    layout = ChamberLayout(height=4)  # height=4
    with pytest.raises(ValueError, match="capacity=1"):
        run_chamber(
            seed=1,
            runs_root=Path("/tmp"),
            run_id="overflow",
            n_founders=10,
            n_ticks=1,
            layout=layout,
            write_outputs=False,
        )


# ---------------------------------------------------------------------------
# v0.9 use_memory seam
# ---------------------------------------------------------------------------


def test_run_chamber_use_memory_false_gives_founders_with_no_memory() -> None:
    """v0.9 default: ``use_memory=False`` produces founders whose ``memory``
    is ``None``. Captured at tick 0 via ``setup_observer`` to inspect the
    founders before any step runs."""
    from hedonism_harness.mesa_agents import HHAgent

    captured: list[bool] = []

    def setup(model: HHModel) -> None:
        for agent in model.agents:
            if isinstance(agent, HHAgent):
                captured.append(agent.memory is None)

    run_chamber(
        seed=1,
        runs_root=Path("/tmp"),
        run_id="memory-off-test",
        n_founders=3,
        n_ticks=1,
        layout=ChamberLayout(),
        write_outputs=False,
        setup_observer=setup,
    )

    assert len(captured) == 3
    assert all(captured), "use_memory=False must give founders memory=None"


def test_run_chamber_use_memory_true_gives_founders_with_valence_memory() -> None:
    """v0.9 seam: ``use_memory=True`` produces founders whose ``memory`` is
    a fresh ``ValenceMemory`` sized to the chamber. Snapshot inside the
    setup callback before any step runs (otherwise the same memory object
    is mutated by the agent's first update_at)."""
    from hedonism_harness.mesa_agents import HHAgent

    captured: list[dict[str, int]] = []

    def setup(model: HHModel) -> None:
        for agent in model.agents:
            if isinstance(agent, HHAgent):
                assert agent.memory is not None, "use_memory=True must give founders memory"
                captured.append(
                    {
                        "width": agent.memory.width,
                        "height": agent.memory.height,
                        "visits_sum": int(agent.memory.visits.sum()),
                        "last_seen_min": int(agent.memory.last_seen_tick.min()),
                        "last_seen_max": int(agent.memory.last_seen_tick.max()),
                    }
                )

    layout = ChamberLayout()
    run_chamber(
        seed=1,
        runs_root=Path("/tmp"),
        run_id="memory-on-test",
        n_founders=3,
        n_ticks=1,
        layout=layout,
        write_outputs=False,
        use_memory=True,
        setup_observer=setup,
    )

    assert len(captured) == 3
    for snap in captured:
        assert snap["width"] == layout.width
        assert snap["height"] == layout.height
        assert snap["visits_sum"] == 0
        assert snap["last_seen_min"] == -1
        assert snap["last_seen_max"] == -1


def test_run_chamber_use_memory_true_children_get_fresh_memory() -> None:
    """SPEC §13.4: children of memory-enabled parents must receive a fresh
    ``ValenceMemory``, not inherit the parent's. v0.9 depends on this so
    that memory experience is per-lifetime, not heritable.

    Strategy: build a tiny model where the founder is forced to reproduce
    every tick, run a few ticks, find a child, assert its ``visits``
    array is all-zero relative to the parent's accumulated visits."""
    from hedonism_harness.core.actions import Action, get_valid_actions
    from hedonism_harness.core.config import BodyConfig, ReproductionConfig, WorldConfig
    from hedonism_harness.core.memory import ValenceMemory
    from hedonism_harness.mesa_agents import HHAgent
    from hedonism_harness.model import FounderSpec, HHModel
    from hedonism_harness.policies.base import PolicyDecision

    class _AlwaysReproducePolicy:
        def decide(self, ctx):  # type: ignore[no-untyped-def]
            valid = get_valid_actions(ctx.world, ctx.body, ctx.reproduction_config, ctx.occupied)
            if Action.REPRODUCE in valid:
                return PolicyDecision(action=Action.REPRODUCE, breakdown=None)
            return PolicyDecision(action=Action.STAY, breakdown=None)

    world_cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    body_cfg = BodyConfig(starting_energy=100.0)  # max_energy default
    repro_cfg = ReproductionConfig(min_age=0, hazard_threshold=10.0, energy_cost=20.0)
    model = HHModel(
        world_cfg,
        founders=[FounderSpec(x=4, y=4, policy_factory=_AlwaysReproducePolicy, use_memory=True)],
        body_config=body_cfg,
        reproduction_config=repro_cfg,
    )

    # Tick exactly once: the parent reproduces (one update_at call against
    # the parent's memory), the child is appended at end-of-tick, and per
    # SPEC §27.4 the newborn does NOT step on its birth tick. So at this
    # point the child has never run update_at on its own memory.
    model.step()

    agents = [a for a in model.agents if isinstance(a, HHAgent)]
    parent = next(a for a in agents if a.body.parent_id is None)
    children = [a for a in agents if a.body.parent_id is not None]

    assert children, "expected at least one child after the reproduction tick"
    assert parent.memory is not None
    # Parent has been updating memory each step — visits are nonzero.
    assert int(parent.memory.visits.sum()) > 0

    for child in children:
        assert child.memory is not None
        assert isinstance(child.memory, ValenceMemory)
        # Child memory must NOT be the parent's instance.
        assert child.memory is not parent.memory
        # Child memory is fresh on the birth tick (newborn-defer keeps it
        # un-stepped until T+1). Per SPEC §13.4, no inheritance.
        assert int(child.memory.visits.sum()) == 0
        assert int(child.memory.last_seen_tick.min()) == -1
