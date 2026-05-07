"""v0.45 birth-position intervention unit tests.

Coverage:
  - InterventionConfig accepts the two new kinds.
  - _is_v045_birth_safe_placeable predicate (in_bounds + non-WALL +
    non-HAZARD + unoccupied).
  - _v045_eligible_global_cells / _v045_eligible_neighbor_cells
    helpers return correct sorted (x, y) lists.
  - make_v045_birth_redirect_callback returns a callable that:
    - Picks uniformly from the eligible set using the locked stream.
    - Emits a BirthRedirectedByIntervention with all required fields
      including target_cell_kind.
    - Returns None on empty eligible set and increments the model's
      skipped counter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import numpy as np

from hedonism_harness.core.events import BirthRedirectedByIntervention
from hedonism_harness.core.interventions import (
    DEFAULT_EFFECTIVE_TICK,
    DEFAULT_INTERVENTION_TICK,
    KIND_NULL,
    KIND_UNIFORM_NEIGHBOR_BIRTH,
    KIND_UNIFORM_VALID_REGION_BIRTH,
    V045_RNG_STREAM_LABEL,
    InterventionConfig,
    _is_v045_birth_safe_placeable,
    _v045_eligible_global_cells,
    _v045_eligible_neighbor_cells,
    make_v045_birth_redirect_callback,
)
from hedonism_harness.core.world import CellKind


@dataclass
class _FakeWorld:
    width: int
    height: int
    kind_layer: np.ndarray


@dataclass
class _FakeStreams:
    mutation: np.random.Generator


@dataclass
class _FakeModel:
    world: _FakeWorld
    streams: _FakeStreams
    tick_count: int = 60
    event_log: list = field(default_factory=list)
    v045_skipped_redirect_counter: int = 0

    def record_event(self, event) -> None:
        self.event_log.append(event)


def _make_world(
    *,
    width: int,
    height: int,
    food_cells: set[tuple[int, int]] | None = None,
    hazard_cells: set[tuple[int, int]] | None = None,
    wall_cells: set[tuple[int, int]] | None = None,
    safe_cells: set[tuple[int, int]] | None = None,
) -> _FakeWorld:
    kind_layer = np.full((width, height), int(CellKind.EMPTY), dtype=np.uint8)
    if food_cells:
        for x, y in food_cells:
            kind_layer[x, y] = int(CellKind.FOOD)
    if hazard_cells:
        for x, y in hazard_cells:
            kind_layer[x, y] = int(CellKind.HAZARD)
    if wall_cells:
        for x, y in wall_cells:
            kind_layer[x, y] = int(CellKind.WALL)
    if safe_cells:
        for x, y in safe_cells:
            kind_layer[x, y] = int(CellKind.SAFE)
    return _FakeWorld(width=width, height=height, kind_layer=kind_layer)


def _make_model(world: _FakeWorld, *, seed: int = 0) -> _FakeModel:
    return _FakeModel(world=world, streams=_FakeStreams(mutation=np.random.default_rng(seed)))


# ---------------------------------------------------------------------------
# Config kinds
# ---------------------------------------------------------------------------


def test_config_accepts_uniform_valid_region_birth_kind():
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    assert cfg.kind == KIND_UNIFORM_VALID_REGION_BIRTH
    assert cfg.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert cfg.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_config_accepts_uniform_neighbor_birth_kind():
    cfg = InterventionConfig(kind=KIND_UNIFORM_NEIGHBOR_BIRTH)
    assert cfg.kind == KIND_UNIFORM_NEIGHBOR_BIRTH


# ---------------------------------------------------------------------------
# Predicate
# ---------------------------------------------------------------------------


def test_predicate_includes_empty_food_safe():
    world = _make_world(
        width=4,
        height=4,
        food_cells={(1, 1)},
        safe_cells={(2, 2)},
    )
    occupied: frozenset[tuple[int, int]] = frozenset()
    assert _is_v045_birth_safe_placeable(world, 0, 0, occupied) is True  # EMPTY
    assert _is_v045_birth_safe_placeable(world, 1, 1, occupied) is True  # FOOD
    assert _is_v045_birth_safe_placeable(world, 2, 2, occupied) is True  # SAFE


def test_predicate_excludes_hazard():
    world = _make_world(width=4, height=4, hazard_cells={(1, 1)})
    assert _is_v045_birth_safe_placeable(world, 1, 1, None) is False


def test_predicate_excludes_wall():
    world = _make_world(width=4, height=4, wall_cells={(2, 2)})
    assert _is_v045_birth_safe_placeable(world, 2, 2, None) is False


def test_predicate_excludes_out_of_bounds():
    world = _make_world(width=4, height=4)
    assert _is_v045_birth_safe_placeable(world, -1, 0, None) is False
    assert _is_v045_birth_safe_placeable(world, 0, -1, None) is False
    assert _is_v045_birth_safe_placeable(world, 4, 0, None) is False
    assert _is_v045_birth_safe_placeable(world, 0, 4, None) is False


def test_predicate_excludes_occupied():
    world = _make_world(width=4, height=4)
    occupied = frozenset({(0, 0)})
    assert _is_v045_birth_safe_placeable(world, 0, 0, occupied) is False
    assert _is_v045_birth_safe_placeable(world, 1, 0, occupied) is True


# ---------------------------------------------------------------------------
# Eligible-cell helpers
# ---------------------------------------------------------------------------


def test_eligible_global_cells_excludes_hazard_wall_returns_sorted():
    world = _make_world(
        width=3,
        height=3,
        hazard_cells={(0, 0), (2, 2)},
        wall_cells={(1, 1)},
    )
    cells = _v045_eligible_global_cells(world, frozenset())
    # 9 - 3 = 6 eligible cells, in (x, y) ascending order.
    assert cells == [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]


def test_eligible_global_cells_excludes_occupied():
    world = _make_world(width=2, height=2)
    occupied = frozenset({(0, 0), (1, 1)})
    cells = _v045_eligible_global_cells(world, occupied)
    assert cells == [(0, 1), (1, 0)]


def test_eligible_neighbor_cells_returns_only_adjacent():
    world = _make_world(width=5, height=5)
    parent = SimpleNamespace(x=2, y=2)
    cells = _v045_eligible_neighbor_cells(world, parent, frozenset())
    # (1, 2), (2, 1), (2, 3), (3, 2) sorted ascending.
    assert cells == [(1, 2), (2, 1), (2, 3), (3, 2)]


def test_eligible_neighbor_cells_excludes_hazard_and_occupied():
    world = _make_world(width=5, height=5, hazard_cells={(1, 2)})
    parent = SimpleNamespace(x=2, y=2)
    occupied = frozenset({(2, 1)})
    cells = _v045_eligible_neighbor_cells(world, parent, occupied)
    # Excluded: (1, 2) HAZARD, (2, 1) occupied. Remaining: (2, 3), (3, 2).
    assert cells == [(2, 3), (3, 2)]


def test_eligible_neighbor_cells_at_corner():
    world = _make_world(width=3, height=3)
    parent = SimpleNamespace(x=0, y=0)
    cells = _v045_eligible_neighbor_cells(world, parent, frozenset())
    # Only (0, 1) and (1, 0) are in-bounds neighbors of (0, 0).
    assert cells == [(0, 1), (1, 0)]


# ---------------------------------------------------------------------------
# Callback factory
# ---------------------------------------------------------------------------


def _make_parent(x: int, y: int, *, body_id: int = 1, lineage_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, id=body_id, lineage_id=lineage_id)


def test_callback_b_picks_from_global_eligible_set_and_emits_event():
    world = _make_world(width=3, height=3, hazard_cells={(0, 0)})
    model = _make_model(world, seed=42)
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(1, 1)
    occupied = frozenset({(1, 1)})  # parent occupies its own cell
    result = callback(world, parent, occupied, original_placement=(2, 1))
    assert result is not None
    assert result in [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)]
    # One event emitted.
    events = [e for e in model.event_log if isinstance(e, BirthRedirectedByIntervention)]
    assert len(events) == 1
    e = events[0]
    assert e.intervention_kind == KIND_UNIFORM_VALID_REGION_BIRTH
    assert e.parent_x == 1
    assert e.parent_y == 1
    assert e.original_x == 2
    assert e.original_y == 1
    assert (e.redirected_x, e.redirected_y) == result
    assert e.target_cell_kind in {"EMPTY", "FOOD", "SAFE"}
    assert e.rng_stream_label == V045_RNG_STREAM_LABEL


def test_callback_c_picks_from_neighbor_eligible_set_and_preserves_adjacency():
    world = _make_world(width=4, height=4)
    model = _make_model(world, seed=7)
    cfg = InterventionConfig(kind=KIND_UNIFORM_NEIGHBOR_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(2, 2)
    occupied = frozenset({(2, 2)})
    result = callback(world, parent, occupied, original_placement=(2, 3))
    assert result is not None
    rx, ry = result
    assert abs(rx - 2) + abs(ry - 2) == 1, "C must preserve parent adjacency"
    e = next(e for e in model.event_log if isinstance(e, BirthRedirectedByIntervention))
    assert e.preserved_parent_adjacency is True


def test_callback_b_returns_none_on_empty_global_set():
    # All non-occupied cells are HAZARD; eligible set is empty.
    world = _make_world(
        width=2,
        height=2,
        hazard_cells={(0, 1), (1, 0), (1, 1)},
    )
    model = _make_model(world, seed=1)
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(0, 0)
    occupied = frozenset({(0, 0)})
    result = callback(world, parent, occupied, original_placement=None)
    assert result is None
    assert model.v045_skipped_redirect_counter == 1
    # No event emitted.
    events = [e for e in model.event_log if isinstance(e, BirthRedirectedByIntervention)]
    assert events == []


def test_callback_c_returns_none_when_all_neighbors_are_hazard():
    world = _make_world(
        width=5,
        height=5,
        hazard_cells={(1, 2), (2, 1), (2, 3), (3, 2)},
    )
    model = _make_model(world, seed=3)
    cfg = InterventionConfig(kind=KIND_UNIFORM_NEIGHBOR_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(2, 2)
    occupied = frozenset({(2, 2)})
    result = callback(world, parent, occupied, original_placement=(1, 2))
    assert result is None
    assert model.v045_skipped_redirect_counter == 1


def test_callback_determinism_same_seed_same_state_yields_same_result():
    world1 = _make_world(width=4, height=4)
    world2 = _make_world(width=4, height=4)
    model1 = _make_model(world1, seed=99)
    model2 = _make_model(world2, seed=99)
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    cb1 = make_v045_birth_redirect_callback(cfg, model1)
    cb2 = make_v045_birth_redirect_callback(cfg, model2)
    parent = _make_parent(1, 1)
    occupied = frozenset({(1, 1)})
    r1 = cb1(world1, parent, occupied, original_placement=None)
    r2 = cb2(world2, parent, occupied, original_placement=None)
    assert r1 == r2


def test_callback_records_target_cell_kind_correctly():
    world = _make_world(width=3, height=3, food_cells={(0, 0)}, safe_cells={(0, 1)})
    model = _make_model(world, seed=11)
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(2, 2)
    occupied = frozenset({(2, 2)})
    callback(world, parent, occupied, original_placement=None)
    e = next(e for e in model.event_log if isinstance(e, BirthRedirectedByIntervention))
    expected_kind = CellKind(int(world.kind_layer[e.redirected_x, e.redirected_y])).name
    assert e.target_cell_kind == expected_kind


def test_factory_rejects_non_v045_kind():
    world = _make_world(width=3, height=3)
    model = _make_model(world)
    cfg = InterventionConfig(kind=KIND_NULL)
    try:
        make_v045_birth_redirect_callback(cfg, model)
    except ValueError:
        return
    raise AssertionError("expected ValueError for non-v0.45 kind")


def test_callback_original_placement_none_encoded_as_minus_one():
    world = _make_world(width=3, height=3)
    model = _make_model(world, seed=5)
    cfg = InterventionConfig(kind=KIND_UNIFORM_VALID_REGION_BIRTH)
    callback = make_v045_birth_redirect_callback(cfg, model)
    parent = _make_parent(1, 1)
    occupied = frozenset({(1, 1)})
    callback(world, parent, occupied, original_placement=None)
    e = next(e for e in model.event_log if isinstance(e, BirthRedirectedByIntervention))
    assert e.original_x == -1
    assert e.original_y == -1
