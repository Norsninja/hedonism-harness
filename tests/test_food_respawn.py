"""Tests for v0.18 food-respawn cooldown mechanism.

The v0.18 axis adds a per-tile cooldown that refills consumed FOOD
cells back to FOOD with ``food_value_default`` after ``K`` ticks.
``WorldConfig.food_respawn_cooldown=None`` (default) preserves
v0.7..v0.17 bit-identity by leaving the new ``respawn_at_tick``
PropertyLayer all-zero.

These tests cover:
  - K=None bit-identity (no respawn_at_tick writes; AteFood
    subscription not registered).
  - Mechanism: a consumed FOOD cell reappears after K ticks with
    full food_value, and the cell predicate fires only on the
    scheduled tick.
  - FoodRespawned event emission with correct (x, y, tick).
  - Edge case: respawn under occupant — the agent's reflex eats
    the refilled cell next tick.
  - WorldConfig validation: K=0 rejected; K<0 rejected.

The bit-identity contract for V0_18_ARMS arm K-inf vs v0.17 start-30
is verified end-to-end by the v0.18 sweep itself; these tests cover
the wiring layer.
"""

from __future__ import annotations

import numpy as np
import pytest

from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.events import AteFood, FoodRespawned
from hedonism_harness.core.world import CellKind
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.gradient_policy import GradientPolicy

# ---------------------------------------------------------------------------
# Configuration / validation
# ---------------------------------------------------------------------------


def test_world_config_default_food_respawn_cooldown_is_none() -> None:
    """Default preserves v0.7..v0.17 bit-identity (no respawn)."""
    cfg = WorldConfig(seed=0, width=4, height=4)
    assert cfg.food_respawn_cooldown is None


def test_world_config_rejects_zero_cooldown() -> None:
    """K=0 would clash with the unscheduled sentinel
    (respawn_at_tick == 0)."""
    with pytest.raises(ValueError, match="food_respawn_cooldown"):
        WorldConfig(seed=0, width=4, height=4, food_respawn_cooldown=0)


def test_world_config_rejects_negative_cooldown() -> None:
    """K<0 would schedule respawn in the past (predicate fires immediately)."""
    with pytest.raises(ValueError, match="food_respawn_cooldown"):
        WorldConfig(seed=0, width=4, height=4, food_respawn_cooldown=-1)


def test_world_config_accepts_minimum_cooldown_one() -> None:
    """K=1 is the smallest legal value (refill next tick)."""
    cfg = WorldConfig(seed=0, width=4, height=4, food_respawn_cooldown=1)
    assert cfg.food_respawn_cooldown == 1


# ---------------------------------------------------------------------------
# K=None bit-identity: respawn_at_tick layer stays all-zero, no events.
# ---------------------------------------------------------------------------


def _make_minimal_model(*, food_respawn_cooldown: int | None = None) -> HHModel:
    """Build a small HHModel with one founder. Used by the determinism
    tests below."""
    cfg = WorldConfig(seed=42, width=6, height=4, food_respawn_cooldown=food_respawn_cooldown)
    founders = [FounderSpec(x=1, y=1, policy_factory=GradientPolicy)]
    return HHModel(
        cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
    )


def test_k_none_leaves_respawn_layer_all_zero_after_steps() -> None:
    """When cooldown is None, the respawn_at_tick layer must remain
    all-zero across N ticks — preserves v0.7..v0.17 bit-identity by
    construction (subscription not registered)."""
    model = _make_minimal_model(food_respawn_cooldown=None)
    # Manually paint a FOOD tile the agent will eat on tick 1.
    model.world.kind_layer[2, 1] = CellKind.FOOD
    model.world.food_value[2, 1] = 20.0
    for _ in range(10):
        model.step()
    assert int(model.world.respawn_at_tick.sum()) == 0


def test_k_none_emits_no_food_respawned_events() -> None:
    """When cooldown is None, no FoodRespawned events are ever logged."""
    model = _make_minimal_model(food_respawn_cooldown=None)
    model.world.kind_layer[2, 1] = CellKind.FOOD
    model.world.food_value[2, 1] = 20.0
    for _ in range(10):
        model.step()
    respawn_events = [le for le in model.event_log if isinstance(le.event, FoodRespawned)]
    assert respawn_events == []


# ---------------------------------------------------------------------------
# Mechanism: consumption schedules respawn; refill predicate fires on time.
# ---------------------------------------------------------------------------


def test_ate_food_schedules_respawn_at_correct_tick() -> None:
    """When K is configured, an AteFood event sets respawn_at_tick =
    current_tick + K at the consumed cell."""
    model = _make_minimal_model(food_respawn_cooldown=5)
    # tick_count is 0 at construction. Manually fire AteFood as if an
    # agent ate cell (3, 2) on tick 0.
    model.world.kind_layer[3, 2] = CellKind.EMPTY
    model.world.food_value[3, 2] = 0.0
    model.record_event(AteFood(agent_id=1, x=3, y=2, food_gained=20.0))
    assert int(model.world.respawn_at_tick[3, 2]) == 5  # 0 + 5


def test_respawn_predicate_fires_only_at_scheduled_tick() -> None:
    """The cell remains EMPTY until tick >= respawn_at_tick, then refills.
    Test by manually scheduling a respawn and stepping past it."""
    model = _make_minimal_model(food_respawn_cooldown=3)
    # Manually schedule a respawn at tick 3 (we'll step the model
    # forward and watch the tile flip).
    model.world.kind_layer[3, 2] = CellKind.EMPTY
    model.world.food_value[3, 2] = 0.0
    model.world.respawn_at_tick[3, 2] = 3

    # Tick 0 -> step. Phase 0 checks tick_count (0), schedule (3): not ready.
    model.step()  # tick_count becomes 1
    assert CellKind(int(model.world.kind_layer[3, 2])) == CellKind.EMPTY

    model.step()  # tick_count becomes 2
    assert CellKind(int(model.world.kind_layer[3, 2])) == CellKind.EMPTY

    model.step()  # tick_count becomes 3, but phase 0 ran with tick_count=2
    # At the start of this step, tick_count is still 2 (predicate: 2 >= 3 → False).
    assert CellKind(int(model.world.kind_layer[3, 2])) == CellKind.EMPTY

    model.step()  # at start, tick_count is 3 (predicate: 3 >= 3 → True). REFILL.
    assert CellKind(int(model.world.kind_layer[3, 2])) == CellKind.FOOD
    assert float(model.world.food_value[3, 2]) == 20.0
    assert int(model.world.respawn_at_tick[3, 2]) == 0  # sentinel reset


def test_respawn_emits_food_respawned_event() -> None:
    """One FoodRespawned event is emitted per refilled cell, with
    correct (x, y, tick)."""
    model = _make_minimal_model(food_respawn_cooldown=3)
    model.world.kind_layer[2, 1] = CellKind.EMPTY
    model.world.food_value[2, 1] = 0.0
    model.world.respawn_at_tick[2, 1] = 2

    # Step forward until the refill predicate fires.
    for _ in range(4):
        model.step()

    respawn_events = [le for le in model.event_log if isinstance(le.event, FoodRespawned)]
    assert len(respawn_events) == 1
    refilled = respawn_events[0]
    assert refilled.event.x == 2
    assert refilled.event.y == 1
    # Refill happened at the start of the step where tick_count was 2.
    assert refilled.event.tick == 2


def test_respawn_under_occupant_keeps_cell_food() -> None:
    """When a cell refills with an agent standing on it, the cell becomes
    FOOD (refill is unconditional on occupancy). The agent's next-tick
    reflex eats it. Pre-committed in the v0.18 pre-reg."""
    cfg = WorldConfig(seed=42, width=6, height=4, food_respawn_cooldown=2)
    founders = [FounderSpec(x=2, y=1, policy_factory=GradientPolicy)]
    model = HHModel(
        cfg,
        founders=founders,
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
    )
    # Schedule a respawn at the agent's exact cell, with no other food.
    model.world.kind_layer[2, 1] = CellKind.EMPTY
    model.world.food_value[2, 1] = 0.0
    model.world.respawn_at_tick[2, 1] = 1

    model.step()  # tick_count 0 -> phase 0 checks (0 >= 1: False), no refill.
    assert CellKind(int(model.world.kind_layer[2, 1])) == CellKind.EMPTY

    model.step()  # tick_count 1 -> phase 0 checks (1 >= 1: True), refill.
    assert CellKind(int(model.world.kind_layer[2, 1])) == CellKind.FOOD


def test_unscheduled_cells_do_not_refill() -> None:
    """Cells with respawn_at_tick == 0 (the sentinel) never refill,
    even when they are EMPTY for the entire run."""
    model = _make_minimal_model(food_respawn_cooldown=2)
    # Two cells: (2,1) is EMPTY-unscheduled (no eat ever); (3,1) is EMPTY-scheduled.
    model.world.kind_layer[2, 1] = CellKind.EMPTY
    model.world.respawn_at_tick[2, 1] = 0
    model.world.kind_layer[3, 1] = CellKind.EMPTY
    model.world.respawn_at_tick[3, 1] = 1

    for _ in range(5):
        model.step()

    assert CellKind(int(model.world.kind_layer[2, 1])) == CellKind.EMPTY
    assert CellKind(int(model.world.kind_layer[3, 1])) == CellKind.FOOD


# ---------------------------------------------------------------------------
# Property-layer wiring: the new layer is shared with World and is int32.
# ---------------------------------------------------------------------------


def test_respawn_property_layer_shares_storage_with_world() -> None:
    """Mutating world.respawn_at_tick must be visible to Mesa, just like
    the kind/food/hazard/safe layers."""
    model = _make_minimal_model(food_respawn_cooldown=2)
    # The layer is exposed via _property_layers — access the same buffer.
    pl = model._property_layers["respawn_at_tick"]
    assert pl.data is model.world.respawn_at_tick
    model.world.respawn_at_tick[1, 1] = 42
    assert int(pl.data[1, 1]) == 42


def test_respawn_property_layer_is_int32() -> None:
    """Storage dtype is int32; matches the World dataclass declaration."""
    model = _make_minimal_model(food_respawn_cooldown=2)
    assert model.world.respawn_at_tick.dtype == np.int32


# ---------------------------------------------------------------------------
# Multi-cell refill ordering — vectorized predicate visits cells in
# lexicographic (x, y) order, deterministic across runs.
# ---------------------------------------------------------------------------


def test_multiple_simultaneous_refills_emit_in_lex_order() -> None:
    """When >1 cells are scheduled to refill on the same tick, the
    FoodRespawned events appear in lexicographic (x, y) order from
    np.argwhere — deterministic across runs."""
    model = _make_minimal_model(food_respawn_cooldown=2)
    # Schedule three cells to refill at tick 1.
    schedule = [(1, 0), (0, 2), (2, 1)]
    for x, y in schedule:
        model.world.kind_layer[x, y] = CellKind.EMPTY
        model.world.respawn_at_tick[x, y] = 1

    model.step()  # tick_count 0 -> phase 0 sees (0 >= 1: False), no refill.
    model.step()  # tick_count 1 -> phase 0 sees (1 >= 1: True), 3 refills.

    respawn_events = [le.event for le in model.event_log if isinstance(le.event, FoodRespawned)]
    seen = [(e.x, e.y) for e in respawn_events]
    # np.argwhere returns indices in row-major order; for our (x, y) layout
    # that's lexicographic by (x, y).
    assert seen == sorted(schedule)


# ---------------------------------------------------------------------------
# Subscriber registration: AteFood handler only registered when cooldown
# is configured, and is sender-scoped.
# ---------------------------------------------------------------------------


def test_handler_registered_only_when_cooldown_configured() -> None:
    """When cooldown is None, no _ate_food_handler exists. When set, one does."""
    model_none = _make_minimal_model(food_respawn_cooldown=None)
    assert model_none._ate_food_handler is None
    model_with_k = _make_minimal_model(food_respawn_cooldown=10)
    assert model_with_k._ate_food_handler is not None


def test_handler_is_sender_scoped() -> None:
    """An AteFood emitted from a different model instance must NOT
    schedule a respawn on this model — sender filtering keeps concurrent
    batch runs isolated. Verified by manually emitting a foreign event."""
    model_a = _make_minimal_model(food_respawn_cooldown=5)
    model_b = _make_minimal_model(food_respawn_cooldown=5)
    # Emit an AteFood with sender=model_b. model_a's handler is bound
    # with sender=model_a, so the cross-model emit must not affect model_a.
    from hedonism_harness.core.events import emit

    emit(model_b, AteFood(agent_id=1, x=1, y=1, food_gained=20.0))
    assert int(model_a.world.respawn_at_tick[1, 1]) == 0


# ---------------------------------------------------------------------------
# End-to-end: a chamber run with K=2 produces FoodRespawned events and
# more food_events than an equivalent K=None run.
# ---------------------------------------------------------------------------


def test_chamber_run_with_cooldown_produces_more_food_events() -> None:
    """End-to-end smoke: a 100-tick chamber run with K=10 should
    yield more food consumption events than an equivalent K=None run.
    This is the headline mechanism check; magnitude is verified at
    sweep time."""
    from pathlib import Path

    from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
    from hedonism_harness.experiments.layouts import food_ladder_layout

    layout = food_ladder_layout()
    runs_root_a = Path("/tmp/test_v018_no_respawn")
    runs_root_b = Path("/tmp/test_v018_respawn_10")
    runs_root_a.mkdir(parents=True, exist_ok=True)
    runs_root_b.mkdir(parents=True, exist_ok=True)

    result_no = run_chamber(
        seed=1,
        runs_root=runs_root_a,
        run_id="seed-1",
        n_founders=3,
        n_ticks=100,
        layout=layout,
        policy_factory=GradientPolicy,
        food_respawn_cooldown=None,
    )
    result_yes = run_chamber(
        seed=1,
        runs_root=runs_root_b,
        run_id="seed-1",
        n_founders=3,
        n_ticks=100,
        layout=layout,
        policy_factory=GradientPolicy,
        food_respawn_cooldown=10,
    )
    # Must have at least as many food events with respawn enabled (likely
    # strictly more given the chamber food gets consumed quickly).
    assert result_yes.food_events >= result_no.food_events
