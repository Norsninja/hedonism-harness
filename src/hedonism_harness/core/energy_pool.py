"""Ambient energy pool for v0.19 strict mass-energy conservation.

The pool is a single non-negative ``float`` budget held on ``HHModel``.
Six flows touch it (see ``docs/experiments/fear_hunger_v0.19.md`` §
"Conservation framing"):

    pool_initial       (config-set, debits not allowed below 0)
    + ambient_influx   (open-ecology arms, deterministic per-tick credit)
    + death residual   (max(0, body.energy) at AgentDied)
    - respawn refill   (food_value_default per cell, fail-soft)
    - child startup    (offspring_start_energy per birth, atomic deny)
    + nothing else     (parent repro cost + metabolism = heat loss)

This module owns the pool primitive only — the integration points
(phase-0 influx, gated respawn, atomic birth debit, death residual
credit) live in ``hedonism_harness/model.py``.

Per SPEC §27.11, this layer imports stdlib only; no Mesa, no IO.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnergyPool:
    """Mutable non-negative energy budget with atomic-debit semantics.

    The pool is constructed once per ``HHModel`` (when
    ``WorldConfig.energy_pool_initial is not None``). Under the
    bit-identity arm (``energy_pool_initial=None``) the pool is never
    constructed and the model's pool path is fully bypassed —
    preserving v0.7..v0.18 byte-identical output.

    Telemetry accumulators are split by category so v0.20 candidate (c)
    parent-funds-child can be designed against per-flow drain data
    without re-instrumenting the substrate.
    """

    current: float
    min_observed: float = field(init=False)
    max_observed: float = field(init=False)
    out_respawn: float = 0.0
    out_child_startup: float = 0.0
    in_death_residual: float = 0.0
    in_ambient_influx: float = 0.0
    debited_count_respawn: int = 0
    debited_count_child_startup: int = 0
    blocked_count_respawn: int = 0
    blocked_count_child_startup: int = 0

    def __post_init__(self) -> None:
        if self.current < 0.0:
            msg = f"EnergyPool initial must be non-negative; got {self.current}"
            raise ValueError(msg)
        self.min_observed = self.current
        self.max_observed = self.current

    def try_debit_respawn(self, amount: float) -> bool:
        """Atomically debit ``amount`` for a food-respawn refill.

        Returns ``True`` and decrements ``current`` on success.
        Returns ``False`` and leaves the pool untouched on failure
        (insufficient funds), incrementing ``blocked_count_respawn``.
        """
        if amount < 0.0:
            msg = f"try_debit_respawn requires non-negative amount; got {amount}"
            raise ValueError(msg)
        if self.current < amount:
            self.blocked_count_respawn += 1
            return False
        self.current -= amount
        self.out_respawn += amount
        self.debited_count_respawn += 1
        self._track_min()
        return True

    def try_debit_child_startup(self, amount: float) -> bool:
        """Atomically debit ``amount`` for a child's starting energy.

        Returns ``True`` and decrements ``current`` on success.
        Returns ``False`` and leaves the pool untouched on failure,
        incrementing ``blocked_count_child_startup``. Caller must
        treat False as "birth denied; parent retains energy_cost".
        """
        if amount < 0.0:
            msg = f"try_debit_child_startup requires non-negative amount; got {amount}"
            raise ValueError(msg)
        if self.current < amount:
            self.blocked_count_child_startup += 1
            return False
        self.current -= amount
        self.out_child_startup += amount
        self.debited_count_child_startup += 1
        self._track_min()
        return True

    def credit_death_residual(self, amount: float) -> None:
        """Credit ``max(0.0, amount)`` from a dying agent's residual energy."""
        clean = max(0.0, float(amount))
        if clean == 0.0:
            return
        self.current += clean
        self.in_death_residual += clean
        self._track_max()

    def credit_ambient_influx(self, amount: float) -> None:
        """Credit ``amount`` per the configured open-ecology rate.

        Called once per tick at phase 0 of ``HHModel.step()``. Negative
        rates would be a config-validation defect; this method asserts
        non-negative for defense in depth.
        """
        if amount < 0.0:
            msg = f"credit_ambient_influx requires non-negative amount; got {amount}"
            raise ValueError(msg)
        if amount == 0.0:
            return
        self.current += amount
        self.in_ambient_influx += amount
        self._track_max()

    def _track_min(self) -> None:
        self.min_observed = min(self.min_observed, self.current)

    def _track_max(self) -> None:
        self.max_observed = max(self.max_observed, self.current)
