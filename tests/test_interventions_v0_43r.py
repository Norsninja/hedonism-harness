"""v0.43R substrate-rewrite intervention tests (density-reduction +
density-preserving perturbation).

Coverage:
  - InterventionConfig accepts the two new kinds
    (``reduce_food_density_50pct_at_tick50``,
    ``density_preserving_perturbation_at_tick50``).
  - Reduce arm: every eligible cell's food_value multiplied by 0.5;
    total drops to factor * total_before; multiset shifts; HAZARD,
    WALL, SAFE cells unchanged; kind correctly updated where new
    value > 0 (FOOD) else EMPTY.
  - Perturbation arm: per-pair 25/75 redistribution over (x, y)-sorted
    consecutive eligible cells; per-pair sum exactly preserved; grand
    total exactly preserved; multiset shifts on non-degenerate
    substrate; HAZARD, WALL, SAFE cells unchanged; on odd n_eligible,
    last cell unchanged.
  - Both arms emit exactly one ``FoodRedistributedByIntervention``
    event with correct fields.
  - ``apply_intervention`` routes the new kinds correctly.
  - Determinism: same world state at firing produces byte-identical
    post-state.
  - Magnitude-match invariant at uniform substrate: if all eligible
    cells have value v, B sets every cell to 0.5*v; C sets pairs to
    (0.25*2v, 0.75*2v) = (0.5*v, 1.5*v). Per-cell |Δ| = 0.5*v in both
    arms.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pytest

from hedonism_harness.core.events import FoodRedistributedByIntervention
from hedonism_harness.core.interventions import (
    B_DENSITY_FACTOR,
    C_PAIR_SPLIT_FIRST,
    C_PAIR_SPLIT_SECOND,
    DEFAULT_EFFECTIVE_TICK,
    DEFAULT_INTERVENTION_TICK,
    KIND_DENSITY_PRESERVING_PERTURBATION,
    KIND_NULL,
    KIND_REDUCE_DENSITY_50PCT,
    InterventionConfig,
    apply_intervention,
)
from hedonism_harness.core.world import CellKind

# ---------------------------------------------------------------------------
# Synthetic world + model doubles (mirrors test_interventions_v0_43.py)
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


def test_config_accepts_reduce_density_kind():
    cfg = InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT)
    assert cfg.kind == KIND_REDUCE_DENSITY_50PCT
    assert cfg.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert cfg.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_config_accepts_density_preserving_perturbation_kind():
    cfg = InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION)
    assert cfg.kind == KIND_DENSITY_PRESERVING_PERTURBATION


# ---------------------------------------------------------------------------
# Locked constants
# ---------------------------------------------------------------------------


def test_locked_constants_match_pre_reg():
    """B_DENSITY_FACTOR, C_PAIR_SPLIT_FIRST, C_PAIR_SPLIT_SECOND are pre-reg
    anchors; modifying them invalidates the corpus."""
    assert B_DENSITY_FACTOR == 0.5
    assert C_PAIR_SPLIT_FIRST == 0.25
    assert C_PAIR_SPLIT_SECOND == 0.75
    # 25 + 75 = 100 (split sums to 1.0 — preserves total).
    assert pytest.approx(C_PAIR_SPLIT_FIRST + C_PAIR_SPLIT_SECOND) == 1.0


# ---------------------------------------------------------------------------
# Reduce arm
# ---------------------------------------------------------------------------


def test_reduce_density_halves_total():
    world = _make_world(
        width=4,
        height=4,
        food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (3, 3): 5.0},
    )
    pre_total = float(world.food_value.sum())
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    post_total = float(world.food_value.sum())
    assert post_total == pytest.approx(0.5 * pre_total, abs=1e-3)


def test_reduce_density_multiplies_each_cell_by_factor():
    world = _make_world(
        width=2,
        height=2,
        food_cells={(0, 0): 4.0, (1, 0): 2.0, (0, 1): 0.0, (1, 1): 8.0},
    )
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    assert world.food_value[0, 0] == pytest.approx(2.0)
    assert world.food_value[1, 0] == pytest.approx(1.0)
    assert world.food_value[0, 1] == pytest.approx(0.0)
    assert world.food_value[1, 1] == pytest.approx(4.0)


def test_reduce_density_kind_stays_food_when_value_positive():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0})
    # other cells are EMPTY (default)
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    # Cell (0,0) had value 4 -> 2 (still > 0): kind stays FOOD.
    assert int(world.kind_layer[0, 0]) == int(CellKind.FOOD)
    # Other cells stay EMPTY.
    assert int(world.kind_layer[1, 0]) == int(CellKind.EMPTY)
    assert int(world.kind_layer[0, 1]) == int(CellKind.EMPTY)
    assert int(world.kind_layer[1, 1]) == int(CellKind.EMPTY)


def test_reduce_density_leaves_hazard_wall_safe_unchanged():
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
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    # Untouched cells.
    assert world.kind_layer[2, 0] == pre_kind[2, 0]
    assert world.kind_layer[3, 0] == pre_kind[3, 0]
    assert world.kind_layer[0, 1] == pre_kind[0, 1]
    assert world.food_value[2, 0] == pre_food[2, 0]
    assert world.food_value[3, 0] == pre_food[3, 0]
    assert world.food_value[0, 1] == pre_food[0, 1]


def test_reduce_density_emits_one_event_with_correct_fields():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0, (1, 1): 4.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    food_events = [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]
    assert len(food_events) == 1
    e = food_events[0]
    assert e.intervention_kind == KIND_REDUCE_DENSITY_50PCT
    assert e.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert e.effective_tick == DEFAULT_EFFECTIVE_TICK
    assert e.n_eligible_cells == 4
    assert e.total_food_before == pytest.approx(8.0, abs=1e-6)
    assert e.total_food_after == pytest.approx(4.0, abs=1e-3)
    # Multiset shifts (was {4, 4, 0, 0}; now {2, 2, 0, 0}).
    assert e.food_multiset_digest_before != e.food_multiset_digest_after


def test_reduce_density_on_zero_total_substrate_is_noop():
    """If every eligible cell already has value 0, halving keeps them at 0;
    multiset preserved trivially; n_cells_changed = 0."""
    world = _make_world(width=2, height=2)  # all EMPTY, food=0 everywhere
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT))
    e = model.event_log[0]
    assert e.n_cells_changed == 0
    assert e.total_food_before == 0.0
    assert e.total_food_after == 0.0
    assert e.food_multiset_digest_before == e.food_multiset_digest_after


# ---------------------------------------------------------------------------
# Density-preserving perturbation arm
# ---------------------------------------------------------------------------


def test_perturbation_preserves_total_exactly():
    world = _make_world(
        width=3,
        height=4,
        food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (0, 3): 4.0},
    )
    pre_total = float(world.food_value.sum())
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    post_total = float(world.food_value.sum())
    assert post_total == pytest.approx(pre_total, abs=1e-6)


def test_perturbation_per_pair_25_75_split_on_simple_chamber():
    # 1x4 chamber, all FOOD, distinct values for unambiguous pair logic.
    # Eligible order: [(0,0),(0,1),(0,2),(0,3)], values [10, 20, 30, 40].
    # Pair 0: (10, 20) sum=30 -> (7.5, 22.5).
    # Pair 1: (30, 40) sum=70 -> (17.5, 52.5).
    world = _make_world(
        width=1,
        height=4,
        food_cells={(0, 0): 10.0, (0, 1): 20.0, (0, 2): 30.0, (0, 3): 40.0},
    )
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    assert world.food_value[0, 0] == pytest.approx(7.5)
    assert world.food_value[0, 1] == pytest.approx(22.5)
    assert world.food_value[0, 2] == pytest.approx(17.5)
    assert world.food_value[0, 3] == pytest.approx(52.5)


def test_perturbation_pair_sums_preserved():
    # 1x6 chamber.
    world = _make_world(
        width=1,
        height=6,
        food_cells={
            (0, 0): 10.0,
            (0, 1): 20.0,
            (0, 2): 30.0,
            (0, 3): 0.0,
            (0, 4): 5.0,
            (0, 5): 5.0,
        },
    )
    pre_pairs = [
        float(world.food_value[0, 0]) + float(world.food_value[0, 1]),
        float(world.food_value[0, 2]) + float(world.food_value[0, 3]),
        float(world.food_value[0, 4]) + float(world.food_value[0, 5]),
    ]
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    post_pairs = [
        float(world.food_value[0, 0]) + float(world.food_value[0, 1]),
        float(world.food_value[0, 2]) + float(world.food_value[0, 3]),
        float(world.food_value[0, 4]) + float(world.food_value[0, 5]),
    ]
    for pre, post in zip(pre_pairs, post_pairs, strict=True):
        assert post == pytest.approx(pre, abs=1e-6)


def test_perturbation_odd_n_eligible_leaves_last_cell_unchanged():
    # 1x3 chamber. n_eligible=3, odd. Last cell stays unchanged.
    world = _make_world(width=1, height=3, food_cells={(0, 0): 10.0, (0, 1): 20.0, (0, 2): 99.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    # Pair 0: (10, 20) -> (7.5, 22.5). Cell (0, 2) unchanged.
    assert world.food_value[0, 0] == pytest.approx(7.5)
    assert world.food_value[0, 1] == pytest.approx(22.5)
    assert world.food_value[0, 2] == pytest.approx(99.0)


def test_perturbation_multiset_shifts_on_non_degenerate():
    world = _make_world(
        width=1,
        height=4,
        food_cells={(0, 0): 10.0, (0, 1): 20.0, (0, 2): 30.0, (0, 3): 40.0},
    )
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    e = model.event_log[0]
    assert e.food_multiset_digest_before != e.food_multiset_digest_after


def test_perturbation_leaves_hazard_wall_safe_unchanged():
    world = _make_world(
        width=4,
        height=2,
        food_cells={(0, 0): 10.0, (1, 0): 20.0},
        hazard_cells={(2, 0)},
        wall_cells={(3, 0)},
        safe_cells={(0, 1)},
    )
    pre_kind = world.kind_layer.copy()
    pre_food = world.food_value.copy()
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    assert world.kind_layer[2, 0] == pre_kind[2, 0]
    assert world.kind_layer[3, 0] == pre_kind[3, 0]
    assert world.kind_layer[0, 1] == pre_kind[0, 1]
    assert world.food_value[2, 0] == pre_food[2, 0]
    assert world.food_value[3, 0] == pre_food[3, 0]
    assert world.food_value[0, 1] == pre_food[0, 1]


def test_perturbation_emits_one_event_with_correct_fields():
    # NB: must use a non-degenerate pre-state. (10, 30) is a 25/75 fixed
    # point and would yield digest_before == digest_after legitimately.
    # Use uniform (20, 20) -> pair sum 40 -> post (10, 30); multiset
    # transitions from {20, 20} to {10, 30}.
    world = _make_world(width=1, height=2, food_cells={(0, 0): 20.0, (0, 1): 20.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    food_events = [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]
    assert len(food_events) == 1
    e = food_events[0]
    assert e.intervention_kind == KIND_DENSITY_PRESERVING_PERTURBATION
    assert e.n_eligible_cells == 2
    assert e.total_food_before == pytest.approx(40.0)
    assert e.total_food_after == pytest.approx(40.0)
    assert e.food_multiset_digest_before != e.food_multiset_digest_after


def test_perturbation_fixed_point_preserves_multiset_legitimately():
    """A pair already at (a, 3a) where a + 3a = 4a sums to 4a, splitting at
    25/75 yields (a, 3a) — a fixed point. The multiset digest legitimately
    matches before/after, even though the perturbation 'fired'. The audit
    must recognise this as a non-bug degenerate case (analogous to v0.43's
    n_cells_changed == 0 case for flatten on already-uniform substrate).
    """
    world = _make_world(width=1, height=2, food_cells={(0, 0): 10.0, (0, 1): 30.0})
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    e = model.event_log[0]
    # Pre = (10, 30); post = (0.25*40, 0.75*40) = (10, 30). Identical.
    assert world.food_value[0, 0] == pytest.approx(10.0)
    assert world.food_value[0, 1] == pytest.approx(30.0)
    assert e.food_multiset_digest_before == e.food_multiset_digest_after
    assert e.n_cells_changed == 0


def test_perturbation_kind_flip_to_food_when_zero_pair_partner_gets_value():
    # Pair (0, 30) -> (7.5, 22.5). Cell (0, 0) was EMPTY (kind), gets value
    # 7.5 -> kind flips to FOOD.
    world = _make_world(width=1, height=2, food_cells={(0, 1): 30.0})
    # (0, 0) is EMPTY by default.
    model = _FakeModel(world=world)
    apply_intervention(model, InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION))
    assert int(world.kind_layer[0, 0]) == int(CellKind.FOOD)
    assert world.food_value[0, 0] == pytest.approx(7.5)
    assert int(world.kind_layer[0, 1]) == int(CellKind.FOOD)
    assert world.food_value[0, 1] == pytest.approx(22.5)


# ---------------------------------------------------------------------------
# Magnitude match invariant (B vs C at uniform substrate)
# ---------------------------------------------------------------------------


def test_b_and_c_per_cell_magnitude_match_at_uniform_substrate():
    """At a uniform substrate (all eligible cells at value v), B sets every
    cell to 0.5*v (per-cell |Δ| = 0.5*v). C sets pairs to (0.5*v, 1.5*v)
    (per-cell |Δ| = 0.5*v). The per-cell shock magnitude matches.
    """
    v = 20.0
    # B arm.
    world_b = _make_world(width=1, height=4, food_cells={(0, i): v for i in range(4)})
    apply_intervention(
        _FakeModel(world=world_b), InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT)
    )
    b_deltas = [abs(float(world_b.food_value[0, i]) - v) for i in range(4)]
    # C arm.
    world_c = _make_world(width=1, height=4, food_cells={(0, i): v for i in range(4)})
    apply_intervention(
        _FakeModel(world=world_c),
        InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
    )
    c_deltas = [abs(float(world_c.food_value[0, i]) - v) for i in range(4)]
    # Every per-cell |Δ| should equal 0.5*v on both arms at the uniform
    # substrate.
    for d in b_deltas + c_deltas:
        assert d == pytest.approx(0.5 * v)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_reduce_density_is_deterministic():
    def run_once():
        world = _make_world(
            width=4,
            height=4,
            food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (3, 3): 5.0},
        )
        apply_intervention(
            _FakeModel(world=world), InterventionConfig(kind=KIND_REDUCE_DENSITY_50PCT)
        )
        return world.food_value.copy(), world.kind_layer.copy()

    f1, k1 = run_once()
    f2, k2 = run_once()
    assert np.array_equal(f1, f2)
    assert np.array_equal(k1, k2)


def test_perturbation_is_deterministic():
    def run_once():
        world = _make_world(
            width=3,
            height=4,
            food_cells={(0, 0): 5.0, (1, 1): 3.0, (2, 2): 7.0, (0, 3): 4.0},
        )
        apply_intervention(
            _FakeModel(world=world),
            InterventionConfig(kind=KIND_DENSITY_PRESERVING_PERTURBATION),
        )
        return world.food_value.copy()

    f1 = run_once()
    f2 = run_once()
    assert np.array_equal(f1, f2)


# ---------------------------------------------------------------------------
# Null kind invariance preserved
# ---------------------------------------------------------------------------


def test_kind_null_does_not_emit_food_event():
    world = _make_world(width=2, height=2, food_cells={(0, 0): 4.0})
    model = _FakeModel(world=world)
    result = apply_intervention(model, InterventionConfig(kind=KIND_NULL))
    assert result.fired is False
    assert not [e for e in model.event_log if isinstance(e, FoodRedistributedByIntervention)]
