"""v0.44 respawn-schedule rewrite intervention tests.

Coverage:
  - InterventionConfig accepts the two new kinds
    (``delay_respawn_schedule_plus_25_at_tick50``,
    ``permute_respawn_schedule_reverse_row_major_at_tick50``).
  - Eligibility predicate
    (``kind in {EMPTY, FOOD} AND respawn_at_tick > 0``) excludes
    HAZARD/WALL/SAFE and cells with respawn_at_tick == 0.
  - Delay arm: every eligible cell's respawn_at_tick incremented by +25;
    sum increases by 25 * n; min/max increase by 25; food_value and
    kind unchanged; multiset digest shifts.
  - Permute arm: reverse-row-major reassignment over (x, y)-sorted
    eligible cells; sum/min/max preserved exactly; multiset digest
    preserved exactly; food_value and kind unchanged; self-inverse.
  - Both arms emit exactly one ``RespawnScheduleByIntervention`` event
    with correct fields.
  - ``apply_intervention`` routes the new kinds correctly.
  - Determinism: same world state at firing produces byte-identical
    post-state.
  - HAZARD/WALL/SAFE cells preserved bytewise.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from hedonism_harness.core.events import RespawnScheduleByIntervention
from hedonism_harness.core.interventions import (
    B_DELAY_TICKS,
    DEFAULT_EFFECTIVE_TICK,
    DEFAULT_INTERVENTION_TICK,
    KIND_DELAY_RESPAWN_PLUS_25,
    KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
    InterventionConfig,
    _eligible_respawn_cells,
    _respawn_multiset_digest,
    apply_intervention,
)
from hedonism_harness.core.world import CellKind


@dataclass
class _FakeWorld:
    width: int
    height: int
    kind_layer: np.ndarray
    food_value: np.ndarray
    respawn_at_tick: np.ndarray


@dataclass
class _FakeModel:
    world: _FakeWorld
    tick_count: int = DEFAULT_EFFECTIVE_TICK
    event_log: list = field(default_factory=list)

    def record_event(self, event) -> None:
        self.event_log.append(event)

    @property
    def agents(self) -> list:
        return []


def _make_world(
    *,
    width: int,
    height: int,
    scheduled_cells: dict[tuple[int, int], int] | None = None,
    food_cells: dict[tuple[int, int], float] | None = None,
    hazard_cells: set[tuple[int, int]] | None = None,
    wall_cells: set[tuple[int, int]] | None = None,
    safe_cells: set[tuple[int, int]] | None = None,
) -> _FakeWorld:
    """``scheduled_cells`` maps (x, y) -> respawn_at_tick value (>0).
    All scheduled cells default to kind=EMPTY unless also in ``food_cells``.
    """
    kind_layer = np.full((width, height), int(CellKind.EMPTY), dtype=np.uint8)
    food_value = np.zeros((width, height), dtype=np.float32)
    respawn = np.zeros((width, height), dtype=np.int32)
    if food_cells:
        for (x, y), v in food_cells.items():
            kind_layer[x, y] = int(CellKind.FOOD)
            food_value[x, y] = np.float32(v)
    if scheduled_cells:
        for (x, y), tick in scheduled_cells.items():
            respawn[x, y] = np.int32(tick)
    if hazard_cells:
        for x, y in hazard_cells:
            kind_layer[x, y] = int(CellKind.HAZARD)
    if wall_cells:
        for x, y in wall_cells:
            kind_layer[x, y] = int(CellKind.WALL)
    if safe_cells:
        for x, y in safe_cells:
            kind_layer[x, y] = int(CellKind.SAFE)
    return _FakeWorld(
        width=width,
        height=height,
        kind_layer=kind_layer,
        food_value=food_value,
        respawn_at_tick=respawn,
    )


# ---------------------------------------------------------------------------
# InterventionConfig accepts new kinds
# ---------------------------------------------------------------------------


def test_config_accepts_delay_kind():
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    assert cfg.kind == KIND_DELAY_RESPAWN_PLUS_25
    assert cfg.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert cfg.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_config_accepts_permute_kind():
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    assert cfg.kind == KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR


def test_b_delay_constant_is_25():
    assert B_DELAY_TICKS == 25


# ---------------------------------------------------------------------------
# Eligibility predicate
# ---------------------------------------------------------------------------


def test_eligibility_excludes_hazard_wall_safe():
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 60, (1, 0): 60, (2, 0): 60},
        hazard_cells={(0, 0)},  # this cell becomes HAZARD even though scheduled
        wall_cells={(1, 0)},
        safe_cells={(2, 0)},
    )
    cells = _eligible_respawn_cells(_FakeModel(world=world))
    assert cells == []


def test_eligibility_excludes_unscheduled_cells():
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(1, 1): 60, (2, 2): 70},
    )
    cells = _eligible_respawn_cells(_FakeModel(world=world))
    assert cells == [(1, 1), (2, 2)]


def test_eligibility_includes_food_cells_with_schedule():
    world = _make_world(
        width=4,
        height=4,
        food_cells={(0, 0): 10.0, (1, 1): 5.0},
        scheduled_cells={(0, 0): 60, (1, 1): 65},
    )
    cells = _eligible_respawn_cells(_FakeModel(world=world))
    assert cells == [(0, 0), (1, 1)]


def test_eligibility_sorted_xy_ascending():
    world = _make_world(
        width=5,
        height=5,
        scheduled_cells={(2, 0): 60, (0, 2): 60, (1, 1): 60, (0, 1): 60},
    )
    cells = _eligible_respawn_cells(_FakeModel(world=world))
    assert cells == [(0, 1), (0, 2), (1, 1), (2, 0)]


# ---------------------------------------------------------------------------
# Delay arm (B)
# ---------------------------------------------------------------------------


def test_delay_increments_every_eligible_cell_by_25():
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67, (3, 3): 79},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    apply_intervention(model, cfg)
    assert int(world.respawn_at_tick[0, 0]) == 79
    assert int(world.respawn_at_tick[1, 1]) == 85
    assert int(world.respawn_at_tick[2, 2]) == 92
    assert int(world.respawn_at_tick[3, 3]) == 104


def test_delay_emits_one_event_with_correct_fields():
    world = _make_world(
        width=3,
        height=3,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    apply_intervention(model, cfg)
    events = [e for e in model.event_log if isinstance(e, RespawnScheduleByIntervention)]
    assert len(events) == 1
    e = events[0]
    assert e.intervention_kind == KIND_DELAY_RESPAWN_PLUS_25
    assert e.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert e.effective_tick == DEFAULT_EFFECTIVE_TICK
    assert e.n_eligible_cells == 3
    assert e.n_cells_changed == 3
    assert e.min_respawn_tick_before == 54
    assert e.max_respawn_tick_before == 67
    assert e.sum_respawn_tick_before == 54 + 60 + 67
    assert e.min_respawn_tick_after == 79
    assert e.max_respawn_tick_after == 92
    assert e.sum_respawn_tick_after == 79 + 85 + 92
    assert e.respawn_multiset_digest_before != e.respawn_multiset_digest_after


def test_delay_preserves_food_and_kind_layers():
    world = _make_world(
        width=3,
        height=3,
        food_cells={(0, 0): 5.0, (1, 1): 7.0},
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    food_before = world.food_value.copy()
    kind_before = world.kind_layer.copy()
    apply_intervention(model, cfg)
    assert np.array_equal(world.food_value, food_before)
    assert np.array_equal(world.kind_layer, kind_before)


def test_delay_preserves_hazard_wall_safe_bytes():
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 60, (1, 1): 60},
        hazard_cells={(2, 0), (3, 0)},
        wall_cells={(2, 1)},
        safe_cells={(3, 1)},
    )
    model = _FakeModel(world=world)
    kind_before = world.kind_layer.copy()
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    apply_intervention(model, cfg)
    assert np.array_equal(world.kind_layer, kind_before)
    # respawn at hazard/wall/safe cells should remain 0 (untouched).
    assert int(world.respawn_at_tick[2, 0]) == 0
    assert int(world.respawn_at_tick[3, 0]) == 0
    assert int(world.respawn_at_tick[2, 1]) == 0
    assert int(world.respawn_at_tick[3, 1]) == 0


def test_delay_is_deterministic_byte_identical():
    schedules = {(x, y): 50 + (x * 3 + y) for x in range(4) for y in range(4)}
    w1 = _make_world(width=4, height=4, scheduled_cells=schedules)
    w2 = _make_world(width=4, height=4, scheduled_cells=schedules)
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    apply_intervention(_FakeModel(world=w1), cfg)
    apply_intervention(_FakeModel(world=w2), cfg)
    assert np.array_equal(w1.respawn_at_tick, w2.respawn_at_tick)


# ---------------------------------------------------------------------------
# Permute arm (C)
# ---------------------------------------------------------------------------


def test_permute_reverse_row_major_assignment():
    # 4 cells (sorted (x, y) ascending) with distinct ticks.
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67, (3, 3): 79},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    apply_intervention(model, cfg)
    # cell[i] receives old cell[n-1-i].
    assert int(world.respawn_at_tick[0, 0]) == 79
    assert int(world.respawn_at_tick[1, 1]) == 67
    assert int(world.respawn_at_tick[2, 2]) == 60
    assert int(world.respawn_at_tick[3, 3]) == 54


def test_permute_preserves_multiset_exactly():
    world = _make_world(
        width=3,
        height=3,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    sorted_before = sorted(int(v) for v in world.respawn_at_tick.flatten() if v > 0)
    apply_intervention(model, cfg)
    sorted_after = sorted(int(v) for v in world.respawn_at_tick.flatten() if v > 0)
    assert sorted_before == sorted_after


def test_permute_preserves_sum_min_max_exactly():
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67, (3, 3): 79},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    apply_intervention(model, cfg)
    e = next(ev for ev in model.event_log if isinstance(ev, RespawnScheduleByIntervention))
    assert e.sum_respawn_tick_after == e.sum_respawn_tick_before
    assert e.min_respawn_tick_after == e.min_respawn_tick_before
    assert e.max_respawn_tick_after == e.max_respawn_tick_before
    assert e.respawn_multiset_digest_before == e.respawn_multiset_digest_after


def test_permute_is_self_inverse():
    schedules = {(x, y): 54 + (x * 3 + y) * 2 for x in range(3) for y in range(3)}
    world = _make_world(width=3, height=3, scheduled_cells=schedules)
    model = _FakeModel(world=world)
    snap_before = world.respawn_at_tick.copy()
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    apply_intervention(model, cfg)
    apply_intervention(model, cfg)
    assert np.array_equal(world.respawn_at_tick, snap_before)


def test_permute_emits_one_event_with_correct_fields():
    world = _make_world(
        width=3,
        height=3,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    apply_intervention(model, cfg)
    events = [e for e in model.event_log if isinstance(e, RespawnScheduleByIntervention)]
    assert len(events) == 1
    e = events[0]
    assert e.intervention_kind == KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR
    assert e.n_eligible_cells == 3
    assert e.sum_respawn_tick_after == e.sum_respawn_tick_before
    assert e.respawn_multiset_digest_after == e.respawn_multiset_digest_before


def test_permute_preserves_food_and_kind_layers():
    world = _make_world(
        width=3,
        height=3,
        food_cells={(0, 0): 5.0, (1, 1): 7.0},
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    food_before = world.food_value.copy()
    kind_before = world.kind_layer.copy()
    apply_intervention(model, cfg)
    assert np.array_equal(world.food_value, food_before)
    assert np.array_equal(world.kind_layer, kind_before)


def test_permute_n_cells_changed_excludes_fixed_points():
    # Symmetric multiset: pair (54, 79) at ends swaps; middle cells with
    # equal values stay fixed under reverse-row-major.
    world = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 60, (3, 3): 79},
    )
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR)
    apply_intervention(model, cfg)
    e = next(ev for ev in model.event_log if isinstance(ev, RespawnScheduleByIntervention))
    # Cell 0 (54) <- cell 3's 79; cell 1 (60) <- cell 2's 60 (fixed); etc.
    assert e.n_cells_changed == 2  # only the (0, 0)/(3, 3) pair changes


# ---------------------------------------------------------------------------
# Empty-eligibility degenerate path
# ---------------------------------------------------------------------------


def test_delay_on_no_scheduled_cells_emits_degenerate_event():
    world = _make_world(width=3, height=3)  # no scheduled cells
    model = _FakeModel(world=world)
    cfg = InterventionConfig(kind=KIND_DELAY_RESPAWN_PLUS_25)
    apply_intervention(model, cfg)
    events = [e for e in model.event_log if isinstance(e, RespawnScheduleByIntervention)]
    assert len(events) == 1
    e = events[0]
    assert e.n_eligible_cells == 0
    assert e.n_cells_changed == 0


# ---------------------------------------------------------------------------
# Multiset digest helper
# ---------------------------------------------------------------------------


def test_multiset_digest_invariant_under_permutation():
    a = np.array([54, 60, 67, 79], dtype=np.int32)
    b = np.array([79, 67, 60, 54], dtype=np.int32)
    assert _respawn_multiset_digest(a) == _respawn_multiset_digest(b)


def test_multiset_digest_changes_under_value_shift():
    a = np.array([54, 60, 67, 79], dtype=np.int32)
    b = a + np.int32(B_DELAY_TICKS)
    assert _respawn_multiset_digest(a) != _respawn_multiset_digest(b)


# ---------------------------------------------------------------------------
# Magnitude-match invariant: B and C touch the same eligible-cell set.
# ---------------------------------------------------------------------------


def test_b_and_c_eligible_cell_sets_identical():
    world_b = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67, (3, 3): 79},
    )
    world_c = _make_world(
        width=4,
        height=4,
        scheduled_cells={(0, 0): 54, (1, 1): 60, (2, 2): 67, (3, 3): 79},
    )
    cells_b = _eligible_respawn_cells(_FakeModel(world=world_b))
    cells_c = _eligible_respawn_cells(_FakeModel(world=world_c))
    assert cells_b == cells_c
