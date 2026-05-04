"""Multi-agent determinism tests at the Mesa boundary (commit 1).

Smoke A — RandomPolicy founders on an empty world. Proves Mesa scheduling +
grid + agent_order shuffle are deterministic.

Smoke B — HedonismPolicy founders on a world with food + hazards. Proves the
full decision stack (observe -> decide -> apply_action -> commit_delta ->
memory update) survives Mesa orchestration deterministically.

Both compare:
  - final hashed world+body state
  - a compact (tick, agent_id, action, x, y, energy, health, alive) trace
  - the event log (type names + counts)

A third assertion verifies that ``World``'s array fields share storage with
their corresponding ``PropertyLayer.data`` buffers (writes to one are visible
in the other).
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Callable

import numpy as np

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.core.world import CellKind
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy
from hedonism_harness.policies.random_policy import RandomPolicy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


TraceRow = tuple[int, int, str, int, int, float, float, bool]


def _alive_agent_state(model: HHModel) -> list[TraceRow]:
    """Snapshot of every (alive or dead) agent's body state as a tuple."""
    rows: list[TraceRow] = []
    for agent in model.agents:
        if not isinstance(agent, HHAgent):
            continue
        rows.append(
            (
                model.tick_count,
                agent.body.id,
                "",  # action filled at step time, not snapshot time
                agent.body.x,
                agent.body.y,
                round(agent.body.energy, 6),
                round(agent.body.health, 6),
                agent.body.alive,
            )
        )
    rows.sort(key=lambda r: r[1])
    return rows


def _hash_world_and_bodies(model: HHModel) -> str:
    h = hashlib.sha256()
    h.update(model.world.kind_layer.tobytes())
    h.update(model.world.food_value.tobytes())
    h.update(model.world.hazard_damage.tobytes())
    h.update(model.world.safe_value.tobytes())
    bodies = sorted(
        (a.body for a in model.agents if isinstance(a, HHAgent)),
        key=lambda b: b.id,
    )
    for body in bodies:
        h.update(repr(body).encode())
    return h.hexdigest()


def _event_trace(model: HHModel) -> list[tuple[int, str, tuple]]:
    """Return a deterministic per-event trace: (tick, type_name, repr_tuple).

    Each ``model.event_log`` entry is a ``LoggedEvent`` envelope; we read both
    the tick and the inner event so a single off-by-one tick mismatch fails
    this assertion immediately.
    """
    return [(le.tick, type(le.event).__name__, repr(le.event)) for le in model.event_log]


def _event_counts(model: HHModel) -> Counter[str]:
    return Counter(type(le.event).__name__ for le in model.event_log)


def _founders_at(
    coords: list[tuple[int, int]],
    factory: Callable[[], object],
    *,
    use_memory: bool = False,
) -> list[FounderSpec]:
    return [
        FounderSpec(x=x, y=y, policy_factory=factory, use_memory=use_memory) for (x, y) in coords
    ]


def _seed_world_with_food_and_hazards(model: HHModel) -> None:
    """Sprinkle deterministic food + hazard cells around the founder positions
    so the HedonismPolicy actually has terrain to react to.

    Writes go through ``model.world`` (which shares storage with the PLs), so
    this also exercises the shared-storage path during setup.
    """
    rng = np.random.default_rng(7)
    w, h = model.world.width, model.world.height
    n_food = 12
    n_haz = 6
    for _ in range(n_food):
        x = int(rng.integers(0, w))
        y = int(rng.integers(0, h))
        if model.world.kind_layer[x, y] == CellKind.EMPTY:
            model.world.kind_layer[x, y] = CellKind.FOOD
            model.world.food_value[x, y] = 20.0
    for _ in range(n_haz):
        x = int(rng.integers(0, w))
        y = int(rng.integers(0, h))
        if model.world.kind_layer[x, y] == CellKind.EMPTY:
            model.world.kind_layer[x, y] = CellKind.HAZARD
            model.world.hazard_damage[x, y] = 5.0


# ---------------------------------------------------------------------------
# Smoke A — RandomPolicy + empty world (scheduler/grid determinism)
# ---------------------------------------------------------------------------


def _build_smoke_a(seed: int) -> HHModel:
    cfg = WorldConfig(seed=seed, width=16, height=16, food_density=0.0, hazard_density=0.0)
    founders = _founders_at(
        [(2, 2), (5, 8), (8, 8), (10, 4), (13, 13)],
        factory=RandomPolicy,
    )
    return HHModel(cfg, founders)


def _run(model: HHModel, ticks: int) -> tuple[str, list[tuple[str, tuple]], Counter[str]]:
    for _ in range(ticks):
        model.step()
    return _hash_world_and_bodies(model), _event_trace(model), _event_counts(model)


def test_smoke_a_random_policy_5_founders_50_ticks_byte_identical() -> None:
    h1, trace1, counts1 = _run(_build_smoke_a(seed=42), ticks=50)
    h2, trace2, counts2 = _run(_build_smoke_a(seed=42), ticks=50)
    assert h1 == h2, "Smoke A: state hash diverged between identical-seed runs."
    assert trace1 == trace2, "Smoke A: event trace diverged between identical-seed runs."
    assert counts1 == counts2


def test_smoke_a_different_seed_produces_different_state() -> None:
    h_a, _, _ = _run(_build_smoke_a(seed=42), ticks=50)
    h_b, _, _ = _run(_build_smoke_a(seed=12345), ticks=50)
    assert h_a != h_b, "Same state across distinct seeds — RNG plumbing leak."


# ---------------------------------------------------------------------------
# Smoke B — HedonismPolicy + food/hazards (decision stack determinism)
# ---------------------------------------------------------------------------


def _build_smoke_b(seed: int) -> HHModel:
    cfg = WorldConfig(seed=seed, width=16, height=16, food_density=0.0, hazard_density=0.0)
    # exploration_noise=0 to remove the easy stochastic path; we want determinism
    # through the scoring branch.
    founders = _founders_at(
        [(3, 3), (12, 4), (4, 12), (12, 12), (8, 8)],
        factory=lambda: HedonismPolicy(exploration_noise=0.0),
    )
    model = HHModel(cfg, founders)
    _seed_world_with_food_and_hazards(model)
    return model


def test_smoke_b_hedonism_policy_byte_identical_state_and_trace() -> None:
    h1, trace1, counts1 = _run(_build_smoke_b(seed=42), ticks=50)
    h2, trace2, counts2 = _run(_build_smoke_b(seed=42), ticks=50)
    assert h1 == h2, "Smoke B: state hash diverged on re-run with same seed."
    assert trace1 == trace2, "Smoke B: event trace diverged on re-run with same seed."
    assert counts1 == counts2


def test_smoke_b_different_seed_produces_different_trace() -> None:
    _, trace_a, _ = _run(_build_smoke_b(seed=42), ticks=50)
    _, trace_b, _ = _run(_build_smoke_b(seed=12345), ticks=50)
    assert trace_a != trace_b


# ---------------------------------------------------------------------------
# PropertyLayer shared-storage assertion
# ---------------------------------------------------------------------------


def test_property_layer_storage_is_shared_with_world() -> None:
    """``World.kind_layer is property_layers['kind'].data`` after model construction.

    If Mesa ever changes ``PropertyLayer`` to copy on attach, this test is the
    canary that breaks first — long before subtle drift between Mesa's view of
    terrain and ``apply_action``'s view.
    """
    model = _build_smoke_a(seed=42)
    pls = model._property_layers
    assert model.world.kind_layer is pls["kind"].data
    assert model.world.food_value is pls["food_value"].data
    assert model.world.hazard_damage is pls["hazard_damage"].data
    assert model.world.safe_value is pls["safe_value"].data

    # Mutation through World is visible through the PL.
    model.world.kind_layer[0, 0] = CellKind.WALL
    assert int(pls["kind"].data[0, 0]) == int(CellKind.WALL)

    # And vice versa.
    pls["food_value"].data[1, 1] = 42.5
    assert float(model.world.food_value[1, 1]) == 42.5


# ---------------------------------------------------------------------------
# Tick-loop invariants
# ---------------------------------------------------------------------------


def test_tick_count_increments_per_step() -> None:
    model = _build_smoke_a(seed=42)
    assert model.tick_count == 0
    model.step()
    assert model.tick_count == 1
    model.step()
    assert model.tick_count == 2


def test_capacity_one_no_two_agents_share_a_cell() -> None:
    """After 50 ticks of RandomPolicy the wrapper's occupancy filter must hold."""
    model = _build_smoke_a(seed=42)
    for _ in range(50):
        model.step()
        positions = [(a.body.x, a.body.y) for a in model.agents if isinstance(a, HHAgent)]
        assert len(positions) == len(set(positions)), (
            f"capacity=1 violated at tick {model.tick_count}: {positions}"
        )
