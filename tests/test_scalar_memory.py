"""Tests for v0.15 ScalarMemory — chemotaxis-tier scalar memory.

ScalarMemory is the prokaryotic-chemotaxis tier: one float
(``last_total_food_signal``) plus the last move direction
(``last_move_action``). No EMA, no spatial map, no decay. The next
``update_scalar`` overwrites both fields; one-tick lag is the entire
memory window.

These tests exercise the data layer only. Policy-level behavior lives
in tests/test_gradient_policy_scalar_memory.py.
"""

from __future__ import annotations

from hedonism_harness.core.actions import Action
from hedonism_harness.core.memory import (
    ScalarMemory,
    make_scalar_memory,
    update_scalar,
)


def test_make_scalar_memory_returns_founder_defaults() -> None:
    """A fresh ScalarMemory carries (0.0, Action.STAY) — the founder state."""
    memory = make_scalar_memory()
    assert isinstance(memory, ScalarMemory)
    assert memory.last_total_food_signal == 0.0
    assert memory.last_move_action == Action.STAY


def test_update_scalar_overwrites_both_fields() -> None:
    """update_scalar replaces both fields with the values from this tick.

    There is no EMA / smoothing — the previous tick's values are gone
    after one update. This is intentional: cell-tier memory is a one-tick
    comparator, not an accumulator.
    """
    memory = make_scalar_memory()
    update_scalar(memory, total_food_signal=3.5, action=Action.MOVE_NORTH)
    assert memory.last_total_food_signal == 3.5
    assert memory.last_move_action == Action.MOVE_NORTH

    update_scalar(memory, total_food_signal=1.25, action=Action.MOVE_EAST)
    assert memory.last_total_food_signal == 1.25
    assert memory.last_move_action == Action.MOVE_EAST


def test_update_scalar_accepts_zero_total_signal() -> None:
    """Zero is a valid sensed value — the blackout case the policy reads."""
    memory = make_scalar_memory()
    update_scalar(memory, total_food_signal=0.0, action=Action.MOVE_WEST)
    assert memory.last_total_food_signal == 0.0
    assert memory.last_move_action == Action.MOVE_WEST


def test_update_scalar_with_non_move_action() -> None:
    """STAY / EAT are recordable; the policy treats them as 'no last move'."""
    memory = make_scalar_memory()
    update_scalar(memory, total_food_signal=2.0, action=Action.STAY)
    assert memory.last_move_action == Action.STAY

    update_scalar(memory, total_food_signal=2.5, action=Action.EAT)
    assert memory.last_move_action == Action.EAT


def test_scalar_memory_is_mutable_dataclass() -> None:
    """The class is mutable — direct assignment works (mirror of
    ValenceMemory / DirectionalMemory). update_scalar is the canonical
    update path; direct assignment exists for test setup convenience.
    """
    memory = ScalarMemory(last_total_food_signal=7.0, last_move_action=Action.MOVE_SOUTH)
    memory.last_total_food_signal = 9.0
    memory.last_move_action = Action.MOVE_NORTH
    assert memory.last_total_food_signal == 9.0
    assert memory.last_move_action == Action.MOVE_NORTH


def test_two_scalar_memories_are_independent_instances() -> None:
    """make_scalar_memory returns a fresh instance each call (no shared state)."""
    a = make_scalar_memory()
    b = make_scalar_memory()
    update_scalar(a, total_food_signal=4.0, action=Action.MOVE_NORTH)
    assert b.last_total_food_signal == 0.0
    assert b.last_move_action == Action.STAY
