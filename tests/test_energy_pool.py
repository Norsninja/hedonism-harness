"""Unit tests for v0.19 ``EnergyPool``: atomic debit, credit, telemetry.

The ``EnergyPool`` is the v0.19 strict-conservation primitive — every
energy creation (food respawn, child startup) must be drawn from a
finite pool, every energy loss tracked. These tests cover the
primitive in isolation; integration with ``HHModel`` lives in
``tests/test_v0_19_conservation.py``.
"""

from __future__ import annotations

import pytest

from hedonism_harness.core.energy_pool import EnergyPool


def test_init_records_min_max_at_starting_value() -> None:
    pool = EnergyPool(current=100.0)
    assert pool.current == 100.0
    assert pool.min_observed == 100.0
    assert pool.max_observed == 100.0


def test_init_rejects_negative_initial() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        EnergyPool(current=-1.0)


def test_init_accepts_zero() -> None:
    pool = EnergyPool(current=0.0)
    assert pool.current == 0.0
    assert pool.min_observed == 0.0


def test_try_debit_respawn_succeeds_when_funded() -> None:
    pool = EnergyPool(current=100.0)
    assert pool.try_debit_respawn(20.0) is True
    assert pool.current == 80.0
    assert pool.out_respawn == 20.0
    assert pool.debited_count_respawn == 1
    assert pool.blocked_count_respawn == 0


def test_try_debit_respawn_fails_when_underfunded() -> None:
    pool = EnergyPool(current=10.0)
    assert pool.try_debit_respawn(20.0) is False
    # Pool unchanged on failure.
    assert pool.current == 10.0
    assert pool.out_respawn == 0.0
    assert pool.debited_count_respawn == 0
    assert pool.blocked_count_respawn == 1


def test_try_debit_respawn_at_exact_balance_succeeds() -> None:
    pool = EnergyPool(current=20.0)
    assert pool.try_debit_respawn(20.0) is True
    assert pool.current == 0.0


def test_try_debit_respawn_rejects_negative_amount() -> None:
    pool = EnergyPool(current=100.0)
    with pytest.raises(ValueError, match="non-negative"):
        pool.try_debit_respawn(-5.0)


def test_try_debit_child_startup_succeeds_when_funded() -> None:
    pool = EnergyPool(current=100.0)
    assert pool.try_debit_child_startup(30.0) is True
    assert pool.current == 70.0
    assert pool.out_child_startup == 30.0
    assert pool.debited_count_child_startup == 1
    assert pool.blocked_count_child_startup == 0


def test_try_debit_child_startup_fails_when_underfunded() -> None:
    pool = EnergyPool(current=20.0)
    assert pool.try_debit_child_startup(30.0) is False
    assert pool.current == 20.0
    assert pool.out_child_startup == 0.0
    assert pool.blocked_count_child_startup == 1


def test_per_flow_counters_are_independent() -> None:
    """Respawn and child-startup debits must not leak into each other."""
    pool = EnergyPool(current=100.0)
    pool.try_debit_respawn(20.0)
    pool.try_debit_child_startup(30.0)
    assert pool.out_respawn == 20.0
    assert pool.out_child_startup == 30.0
    assert pool.debited_count_respawn == 1
    assert pool.debited_count_child_startup == 1


def test_credit_death_residual_credits_pool() -> None:
    pool = EnergyPool(current=50.0)
    pool.credit_death_residual(15.0)
    assert pool.current == 65.0
    assert pool.in_death_residual == 15.0


def test_credit_death_residual_clamps_negative_to_zero() -> None:
    """Starvation deaths can in principle pass body.energy <= 0 — the
    pool primitive defensively clamps to zero rather than raising."""
    pool = EnergyPool(current=50.0)
    pool.credit_death_residual(-3.0)
    assert pool.current == 50.0
    assert pool.in_death_residual == 0.0


def test_credit_death_residual_zero_is_noop() -> None:
    """Starvation deaths typically credit 0 (energy was already at 0).
    Zero-amount credits should not bump max_observed or accumulators."""
    pool = EnergyPool(current=50.0)
    pool.credit_death_residual(0.0)
    assert pool.current == 50.0
    assert pool.in_death_residual == 0.0
    assert pool.max_observed == 50.0


def test_credit_ambient_influx_credits_pool() -> None:
    pool = EnergyPool(current=100.0)
    pool.credit_ambient_influx(60.0)
    assert pool.current == 160.0
    assert pool.in_ambient_influx == 60.0


def test_credit_ambient_influx_zero_is_noop() -> None:
    pool = EnergyPool(current=100.0)
    pool.credit_ambient_influx(0.0)
    assert pool.current == 100.0
    assert pool.in_ambient_influx == 0.0


def test_credit_ambient_influx_rejects_negative() -> None:
    pool = EnergyPool(current=100.0)
    with pytest.raises(ValueError, match="non-negative"):
        pool.credit_ambient_influx(-1.0)


def test_min_observed_tracks_lowest_pool_state() -> None:
    pool = EnergyPool(current=100.0)
    pool.try_debit_respawn(20.0)  # 80
    pool.try_debit_child_startup(30.0)  # 50
    pool.try_debit_respawn(20.0)  # 30
    pool.credit_death_residual(40.0)  # 70
    assert pool.min_observed == 30.0


def test_max_observed_tracks_highest_pool_state() -> None:
    pool = EnergyPool(current=100.0)
    pool.credit_ambient_influx(50.0)  # 150
    pool.try_debit_child_startup(30.0)  # 120
    pool.credit_death_residual(20.0)  # 140
    pool.credit_ambient_influx(70.0)  # 210
    assert pool.max_observed == 210.0


def test_min_max_invariants_hold_under_no_motion() -> None:
    pool = EnergyPool(current=42.0)
    assert pool.min_observed == 42.0
    assert pool.max_observed == 42.0


def test_blocked_debit_does_not_change_min_observed() -> None:
    """A failed debit must not drag min_observed below current."""
    pool = EnergyPool(current=10.0)
    pool.try_debit_respawn(20.0)  # blocked; pool stays at 10
    assert pool.min_observed == 10.0


def test_full_flow_smoke() -> None:
    """End-to-end: a sequence of mixed debits and credits maintains
    consistent accounting across all counters."""
    pool = EnergyPool(current=200.0)
    # Two successful respawns.
    pool.try_debit_respawn(20.0)
    pool.try_debit_respawn(20.0)
    # Three successful child startups.
    pool.try_debit_child_startup(30.0)
    pool.try_debit_child_startup(30.0)
    pool.try_debit_child_startup(30.0)
    # Death residual.
    pool.credit_death_residual(45.0)
    # Influx.
    pool.credit_ambient_influx(15.0)
    # Final state.
    assert pool.current == 200.0 - 40.0 - 90.0 + 45.0 + 15.0
    assert pool.out_respawn == 40.0
    assert pool.out_child_startup == 90.0
    assert pool.in_death_residual == 45.0
    assert pool.in_ambient_influx == 15.0
    assert pool.debited_count_respawn == 2
    assert pool.debited_count_child_startup == 3
    assert pool.blocked_count_respawn == 0
    assert pool.blocked_count_child_startup == 0
