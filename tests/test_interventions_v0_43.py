"""v0.43 substrate-rewrite intervention tests.

Coverage:
  - InterventionConfig accepts the two new kinds
    (``flatten_food_at_tick50``, ``shuffle_food_at_tick50``).
  - ``_eligible_cells`` returns kind in {EMPTY, FOOD} cells, sorted (x, y),
    with HAZARD / WALL / SAFE excluded.
  - ``_eligible_cells_digest`` is a pure function of the cell list; equal
    inputs produce equal digests.
  - ``_food_multiset_digest`` is order-insensitive (multiset semantics)
    and discriminates different multisets.
  - Flatten arm: total food preserved (within tolerance); every eligible
    cell holds the mean; kind = FOOD if mean > 0 else EMPTY; HAZARD,
    WALL, SAFE cells unchanged.
  - Shuffle arm: total food preserved exactly; multiset preserved exactly
    (digest equality); reverse-row-major permutation correctness on a
    small synthetic chamber; HAZARD, WALL, SAFE unchanged.
  - Both arms emit exactly one ``FoodRedistributedByIntervention`` event
    with correct fields.
  - ``apply_intervention`` routes the new kinds correctly.
  - Determinism: same world state at firing produces byte-identical
    post-state (food_value array, kind_layer, event fields).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pytest

from hedonism_harness.core.events import FoodRedistributedByIntervention
from hedonism_harness.core.interventions import (
    DEFAULT_EFFECTIVE_TICK,
    DEFAULT_INTERVENTION_TICK,
    KIND_FLATTEN_FOOD,
    KIND_NULL,
    KIND_SHUFFLE_FOOD,
    InterventionConfig,
    _eligible_cells,
    _eligible_cells_digest,
    _food_multiset_digest,
    apply_intervention,
)
from hedonism_harness.core.world import CellKind

# ---------------------------------------------------------------------------
# Synthetic world + model doubles (no Mesa, no real simulation)
# ---------------------------------------------------------------------------


@dataclass
class _FakeWorld:
    width: int
    height: int
    kind_layer: np.ndarray
    food_value: np.ndarray


@dataclass
class _FakeModel:
    world: _FakeWorld
    tick_count: int = DEFAULT_EFFECTIVE_TICK
    event_log: list = field(default_factory=list)

    def record_event(self, event) -> None:
        self.event_log.append(event)

    # apply_intervention only calls record_event for the food path. The
    # buckets / record_death surface is not used by KIND_FLATTEN_FOOD or
    # KIND_SHUFFLE_FOOD; absence does not break the flow.
    @property
    def agents(self) -> list:
        return []


def _make_world(
    *,
    width: int,
    height: int,
    food_cells: dict[tuple[int, int], float] | None = None,
    hazard_cells: set[tuple[int, int]] | None = None,
    wall_cells: set[tuple[int, int]] | None = None,
    safe_cells: set[tuple[int, int]] | None = None,
) -> _FakeWorld:
    kind_layer = np.full((width, height), int(CellKind.EMPTY), dtype=np.uint8)
    food_value = np.zeros((width, height), dtype=np.float32)
    if food_cells:
        for (x, y), v in food_cells.items():
            kind_layer[x, y] = int(CellKind.FOOD)
            food_value[x, y] = np.float32(v)
    if hazard_cells:
        for x, y in hazard_cells:
            kind_layer[x, y] = int(CellKind.HAZARD)
    if wall_cells:
        for x, y in wall_cells:
            kind_layer[x, y] = int(CellKind.WALL)
    if safe_cells:
        for x, y in safe_cells:
            kind_layer[x, y] = int(CellKind.SAFE)
    return _FakeWorld(width=width, height=height, kind_layer=kind_layer, food_value=food_value)


# ---------------------------------------------------------------------------
# InterventionConfig accepts new kinds
# ---------------------------------------------------------------------------


def test_config_accepts_flatten_food_kind():
    cfg = InterventionConfig(kind=KIND_FLATTEN_FOOD)
    assert cfg.kind == KIND_FLATTEN_FOOD
    assert cfg.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert cfg.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_config_accepts_shuffle_food_kind():
    cfg = InterventionConfig(kind=KIND_SHUFFLE_FOOD)
    assert cfg.kind == KIND_SHUFFLE_FOOD


def test_config_still_rejects_unknown_kind():
    with pytest.raises(ValueError, match="kind must be one of"):
        InterventionConfig(kind="dissolve_chamber")


# ---------------------------------------------------------------------------
# _eligible_cells
# ---------------------------------------------------------------------------


def test_eligible_cells_includes_empty_and_food_only():
    world = _make_world(
        width=4,
        height=3,
        food_cells={(0, 0): 5.0, (1, 1): 3.0},
        hazard_cells={(2, 2)},
        wall_cells={(3, 0)},
        safe_cells={(0, 2)},
    )
    model = _FakeModel(world=world)
    eligible = _eligible_cells(model)
    # Excluded: (2,2) HAZARD, (3,0) WALL, (0,2) SAFE.
    expected = [
        (0, 0),
        (0, 1),  # EMPTY
        (1, 0),  # EMPTY
        (1, 1),
        (1, 2),  # EMPTY
        (2, 0),  # EMPTY
        (2, 1),  # EMPTY
        (3, 1),  # EMPTY
        (3, 2),  # EMPTY
    ]
    assert eligible == expected


def test_eligible_cells_sort_order_is_x_then_y_ascending():
    world = _make_world(width=3, height=3)
    model = _FakeModel(world=world)
    eligible = _eligible_cells(model)
    # All cells eligible (all EMPTY); should iterate (0,0)..(0,2),(1,0)..(1,2),(2,0)..(2,2).
    expected = [(x, y) for x in range(3) for y in range(3)]
    assert eligible == expected


def test_eligible_cells_empty_when_all_excluded():
    world = _make_world(
        width=2,
        height=2,
        hazard_cells={(0, 0), (1, 0), (0, 1), (1, 1)},
    )
    model = _FakeModel(world=world)
    assert _eligible_cells(model) == []


# ---------------------------------------------------------------------------
# Digests
# ---------------------------------------------------------------------------


def test_eligible_cells_digest_is_pure_function():
    cells = [(0, 0), (1, 0), (0, 1)]
    d1 = _eligible_cells_digest(cells)
    d2 = _eligible_cells_digest(cells)
    assert d1 == d2
    # Length: SHA-256 hex is 64 chars.
    assert len(d1) == 64


def test_eligible_cells_digest_distinguishes_different_geometries():
    d1 = _eligible_cells_digest([(0, 0), (1, 0)])
    d2 = _eligible_cells_digest([(0, 0), (0, 1)])
    assert d1 != d2


def test_food_multiset_digest_order_insensitive():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    b = np.array([3.0, 1.0, 2.0], dtype=np.float32)
    assert _food_multiset_digest(a) == _food_multiset_digest(b)


def test_food_multiset_digest_discriminates_different_multisets():
    a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    b = np.array([1.0, 2.0, 4.0], dtype=np.float32)
    assert _food_multiset_digest(a) != _food_multiset_digest(b)


def test_food_multiset_digest_distinguishes_zeros_from_nonzeros():
    a = np.zeros(4, dtype=np.float32)
    b = np.array([0.0, 0.0, 0.0, 0.001], dtype=np.float32)
    assert _food_multiset_digest(a) != _food_multiset_digest(b)


# ---------------------------------------------------------------------------
# Flatten arm
# ---------------------------------------------------------------------------


def test_flatten_preserves_total_food_within_tolerance():
    world = _make_world(
        width=4,
        height=4,
        food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (3, 3): 5.0},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_FLATTEN_FOOD)
    apply_intervention(model, cfg)
    total_after = float(world.food_value.sum())
    assert total_after == pytest.approx(20.0, abs=1e-3)


def test_flatten_writes_mean_to_every_eligible_cell():
    world = _make_world(
        width=2,
        height=2,
        food_cells={(0, 0): 4.0, (1, 0): 2.0, (0, 1): 0.0, (1, 1): 0.0},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_FLATTEN_FOOD)
    apply_intervention(model, cfg)
    # Mean = 6.0 / 4 = 1.5; all four eligible cells now hold 1.5.
    assert world.food_value[0, 0] == pytest.approx(1.5, abs=1e-6)
    assert world.food_value[1, 0] == pytest.approx(1.5, abs=1e-6)
    assert world.food_value[0, 1] == pytest.approx(1.5, abs=1e-6)
    assert world.food_value[1, 1] == pytest.approx(1.5, abs=1e-6)


def test_flatten_sets_kind_to_food_when_mean_positive():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    # Mean = 1.0 > 0, so all eligible cells become FOOD.
    for x in range(2):
        for y in range(2):
            assert int(world.kind_layer[x, y]) == int(CellKind.FOOD)


def test_flatten_sets_kind_to_empty_when_mean_zero():
    world = _make_world(width=2, height=2)  # all EMPTY, food=0
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    # Mean = 0; all eligible cells stay EMPTY.
    for x in range(2):
        for y in range(2):
            assert int(world.kind_layer[x, y]) == int(CellKind.EMPTY)


def test_flatten_leaves_hazard_wall_safe_unchanged():
    world = _make_world(
        width=4,
        height=2,
        food_cells={(0, 0): 4.0, (1, 0): 4.0},
        hazard_cells={(2, 0)},
        wall_cells={(3, 0)},
        safe_cells={(0, 1)},
    )
    pre_kind = world.kind_layer.copy()
    pre_food = world.food_value.copy()
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    # Untouched cells: HAZARD (2,0), WALL (3,0), SAFE (0,1).
    assert world.kind_layer[2, 0] == pre_kind[2, 0]
    assert world.kind_layer[3, 0] == pre_kind[3, 0]
    assert world.kind_layer[0, 1] == pre_kind[0, 1]
    # food_value untouched on those cells too.
    assert world.food_value[2, 0] == pre_food[2, 0]
    assert world.food_value[3, 0] == pre_food[3, 0]
    assert world.food_value[0, 1] == pre_food[0, 1]


def test_flatten_emits_one_event_with_correct_fields():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0, (1, 1): 4.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    food_events = [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]
    assert len(food_events) == 1
    e = food_events[0]
    assert e.intervention_kind == KIND_FLATTEN_FOOD
    assert e.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert e.effective_tick == DEFAULT_EFFECTIVE_TICK
    assert e.n_eligible_cells == 4
    assert e.total_food_before == pytest.approx(8.0, abs=1e-6)
    assert e.total_food_after == pytest.approx(8.0, abs=1e-3)
    # Flatten changes the multiset (was {4,4,0,0}, now {2,2,2,2}).
    assert e.food_multiset_digest_before != e.food_multiset_digest_after


def test_flatten_event_digest_equal_in_already_uniform_case():
    # Two cells, both holding 3.0 -> already uniform; flatten is a no-op.
    world = _make_world(width=1, height=2, food_cells={(0, 0): 3.0, (0, 1): 3.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    e = model.event_log[0]
    assert e.food_multiset_digest_before == e.food_multiset_digest_after
    assert e.n_cells_changed == 0


# ---------------------------------------------------------------------------
# Shuffle arm
# ---------------------------------------------------------------------------


def test_shuffle_preserves_total_food_exactly():
    world = _make_world(
        width=3,
        height=3,
        food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0},
    )
    pre_total = float(world.food_value.sum())
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
    post_total = float(world.food_value.sum())
    assert post_total == pytest.approx(pre_total, abs=1e-6)


def test_shuffle_preserves_multiset_exactly():
    world = _make_world(
        width=3,
        height=3,
        food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0},
    )
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
    e = model.event_log[0]
    assert e.food_multiset_digest_before == e.food_multiset_digest_after


def test_shuffle_uses_reverse_row_major_permutation():
    # 1x4 chamber, all cells eligible, distinct values for unambiguous reverse.
    world = _make_world(
        width=1,
        height=4,
        food_cells={(0, 0): 1.0, (0, 1): 2.0, (0, 2): 3.0, (0, 3): 4.0},
    )
    # Expected eligible order: [(0,0),(0,1),(0,2),(0,3)].
    # Pre values: [1, 2, 3, 4]. Reverse: [4, 3, 2, 1].
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
    assert world.food_value[0, 0] == pytest.approx(4.0)
    assert world.food_value[0, 1] == pytest.approx(3.0)
    assert world.food_value[0, 2] == pytest.approx(2.0)
    assert world.food_value[0, 3] == pytest.approx(1.0)


def test_shuffle_skips_hazard_in_permutation():
    # Hazard at (0, 1); eligible = [(0,0), (0,2), (0,3)] only.
    # Pre values on eligible: [5.0, 0.0, 7.0]. Reverse: [7.0, 0.0, 5.0].
    world = _make_world(
        width=1,
        height=4,
        food_cells={(0, 0): 5.0, (0, 3): 7.0},
        hazard_cells={(0, 1)},
    )
    pre_hazard_kind = int(world.kind_layer[0, 1])
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
    assert world.food_value[0, 0] == pytest.approx(7.0)
    assert world.food_value[0, 2] == pytest.approx(0.0)
    assert world.food_value[0, 3] == pytest.approx(5.0)
    # Hazard cell unchanged.
    assert int(world.kind_layer[0, 1]) == pre_hazard_kind


def test_shuffle_emits_one_event_with_correct_fields():
    world = _make_world(width=1, height=3, food_cells={(0, 0): 1.0, (0, 2): 2.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
    food_events = [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]
    assert len(food_events) == 1
    e = food_events[0]
    assert e.intervention_kind == KIND_SHUFFLE_FOOD
    assert e.n_eligible_cells == 3  # all three EMPTY/FOOD cells
    assert e.total_food_before == pytest.approx(3.0)
    assert e.total_food_after == pytest.approx(3.0)
    # Multiset preserved by shuffle.
    assert e.food_multiset_digest_before == e.food_multiset_digest_after


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_flatten_is_deterministic_across_repeated_application():
    def run_once():
        world = _make_world(
            width=4,
            height=4,
            food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (3, 3): 5.0},
        )
        model = _FakeModel(world=world)
        apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
        return world.food_value.copy(), world.kind_layer.copy()

    f1, k1 = run_once()
    f2, k2 = run_once()
    assert np.array_equal(f1, f2)
    assert np.array_equal(k1, k2)


def test_shuffle_is_deterministic_across_repeated_application():
    def run_once():
        world = _make_world(
            width=3,
            height=3,
            food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0},
        )
        model = _FakeModel(world=world)
        apply_intervention(model, InterventionConfig(kind=KIND_SHUFFLE_FOOD))
        return world.food_value.copy()

    f1 = run_once()
    f2 = run_once()
    assert np.array_equal(f1, f2)


# ---------------------------------------------------------------------------
# Null kind invariance preserved (v0.42 invariant)
# ---------------------------------------------------------------------------


def test_kind_null_does_not_emit_food_event():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0})
    model = _FakeModel(world=world)
    result = apply_intervention(model, InterventionConfig(kind=KIND_NULL))
    assert result.fired is False
    assert not [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]


# ---------------------------------------------------------------------------
# Pathological: empty eligible set
# ---------------------------------------------------------------------------


def test_flatten_on_empty_eligible_set_emits_degenerate_event():
    # All cells HAZARD; no eligible cell.
    world = _make_world(
        width=2,
        height=2,
        hazard_cells={(0, 0), (0, 1), (1, 0), (1, 1)},
    )
    model = _FakeModel(world=world)
    result = apply_intervention(model, InterventionConfig(kind=KIND_FLATTEN_FOOD))
    assert result.fired is True
    e = model.event_log[0]
    assert isinstance(e, FoodRedistributedByIntervention)
    assert e.n_eligible_cells == 0
    assert e.n_cells_changed == 0
    assert e.total_food_before == 0.0
    assert e.total_food_after == 0.0
