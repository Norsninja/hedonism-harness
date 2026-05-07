"""Typed event dataclasses + named blinker signals (SPEC §27.8).

Core/ emits events. Metrics/ subscribes to interpret. Io/ persists what
metrics produces.

The signal table at the bottom of this module gives every event type a
process-wide ``blinker.NamedSignal``. Emitters do not subscribe; subscribers
live in ``metrics/aggregators.py``. Tests can connect ad-hoc via
``signal_for(EventType).connect(callback)``. Per SPEC §27.11, ``core/`` may
import blinker — it is the one cross-cutting communication primitive allowed
in the scientific layer.

All events carry the simulation tick implicitly via the emission site or the
subscriber's clock; we only attach a ``tick`` field where the event is
decoupled from per-tick emission (births, deaths, lineage events).
"""

from __future__ import annotations

from dataclasses import dataclass

import blinker

from hedonism_harness.core.body import DeathCause


@dataclass(frozen=True)
class AgentMoved:
    agent_id: int
    from_x: int
    from_y: int
    to_x: int
    to_y: int


@dataclass(frozen=True)
class AgentStayed:
    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class AteFood:
    agent_id: int
    x: int
    y: int
    food_gained: float


@dataclass(frozen=True)
class HazardEntered:
    """Emitted when an agent moves into a HAZARD cell. Damage event is separate."""

    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class HazardDamageApplied:
    """Emitted by the simulation loop after per-tick hazard residency damage."""

    agent_id: int
    x: int
    y: int
    damage: float


@dataclass(frozen=True)
class ReproductionRequested:
    """Emitted when an agent takes the REPRODUCE action.

    The simulation loop's birth queue consumes this and produces ``AgentBorn``.
    """

    agent_id: int
    x: int
    y: int


@dataclass(frozen=True)
class AgentBorn:
    agent_id: int
    parent_id: int
    lineage_id: int
    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class AgentDied:
    agent_id: int
    cause: DeathCause
    tick: int


@dataclass(frozen=True)
class FoodRespawned:
    """Emitted by ``HHModel._apply_food_respawn`` (v0.18) when a previously-
    consumed FOOD cell refills under the cooldown mechanism.

    No agent_id — this is an environmental event. Carries its own ``tick``
    so subscribers (and the events.jsonl writer) can disambiguate ordering
    when multiple cells refill on the same tick.
    """

    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class PoolRespawnDenied:
    """v0.19: a scheduled food respawn was denied because the ambient
    energy pool could not fund the refill (pool < food_value_default).

    Emitted from ``HHModel._apply_food_respawn`` instead of a
    ``FoodRespawned`` for the affected cell. The cell stays EMPTY and
    its respawn schedule is cleared (sentinel reset to 0 — see v0.19
    pre-reg §"Respawn failure semantics", option (i)).
    """

    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class PoolBirthDenied:
    """v0.19: a queued birth was denied because the ambient energy pool
    could not fund the child's startup energy (pool < offspring_start_energy).

    Emitted from ``HHModel._process_birth_queue`` instead of an
    ``AgentBorn`` for the affected parent. The parent's reproduction
    cost is NOT debited; the parent stays alive and re-enters the
    eligibility pool next tick (mirrors the existing
    ``find_adjacent_empty_cell`` rejection contract in
    ``core/reproduction.process_reproduction``).

    Under v0.20 ``PARENT_TRANSFER_POOL_GAP`` mode, this is emitted when
    the pool cannot fund the gap (``offspring_start_energy -
    energy_cost``) rather than the full ``offspring_start_energy``; the
    contract (parent retains energy, no child created) is unchanged.
    """

    parent_id: int
    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class BirthDeniedParentEnergy:
    """v0.20: a queued birth was denied because the parent's body energy
    fell below ``reproduction_cost`` between queueing and birth processing.

    Only emitted under ``PARENT_TRANSFER_POOL_GAP`` mode. Under the v0.7..v0.19
    ``POOL_FULL`` path, ``charge_parent`` debits unconditionally (energy floors
    at 0); v0.20 transfer mode adds an explicit pre-check because routing a
    sub-cost parent contribution into the child would underfund the child's
    startup. On denial, no state changes: parent retains its full energy, pool
    is untouched, no child is created. Parent re-enters the eligibility pool
    next tick.
    """

    parent_id: int
    x: int
    y: int
    tick: int


@dataclass(frozen=True)
class LineageKilledByIntervention:
    """v0.42: emitted at the tick-50/tick-51 boundary when a leader-kill or
    size-matched-non-leader-kill intervention extincts a lineage.

    The intervention identifies the target lineage from tick-50 living-agent
    state (anchor: ``intervention_tick=50``), then kills all of that lineage's
    living agents before tick 51's first phase begins (anchor:
    ``effective_tick=51``). Each killed agent additionally emits a normal
    ``AgentDied(cause=DeathCause.INTERVENTION)`` event; this summary event
    pairs with that group so downstream audits can identify the intervention's
    target lineage and role without scanning every AgentDied.

    ``lineage_role``: one of ``"leader"`` (arm B) or
    ``"size_matched_nonleader"`` (arm C). Reported separately so audit code
    can distinguish the placebo control from the leader-kill treatment.

    ``n_killed``: count of agents extincted by this intervention. Equals
    the number of paired ``AgentDied(cause=INTERVENTION)`` events at
    ``effective_tick``.
    """

    lineage_id: int
    n_killed: int
    lineage_role: str  # "leader" | "size_matched_nonleader"
    intervention_tick: int  # tick at which leader was identified (50)
    effective_tick: int  # tick at which agents were killed (51)


@dataclass(frozen=True)
class FoodRedistributedByIntervention:
    """v0.43: emitted at the tick-50/tick-51 boundary when a substrate-level
    food redistribution intervention fires. Two kinds:

    - ``"flatten_food_at_tick50"`` (arm B): uniform-mean redistribution of
      food across all eligible cells (kind in {EMPTY, FOOD}). Total food
      preserved within float-32 tolerance; multiset NOT preserved.
    - ``"shuffle_food_at_tick50"`` (arm C): reverse-row-major permutation
      of food values across (x, y)-sorted eligible cells. Total food and
      multiset BOTH exactly preserved.

    Both kinds preserve HAZARD and WALL cell positions and counts. Neither
    emits ``AgentDied`` — no agents are killed by substrate rewrite (agents
    that later starve emit ``AgentDied(cause=STARVATION)`` through the
    existing path).

    Digests (locked formats):

    - ``eligible_cells_digest``: SHA-256 hex of
      ``b"\\n".join(f"{x},{y}".encode() for (x, y) in sorted_eligible_cells)``.
      Pure function of tick-50 chamber kind topology; identical across all
      runs at the same chamber config (seed-independent).
    - ``food_multiset_digest_before`` / ``food_multiset_digest_after``:
      SHA-256 hex of ``struct.pack(f"<{n}f", *sorted_vals)`` where
      ``sorted_vals`` is the float32 ``food_value`` vector over eligible
      cells, sorted ascending. Equality across pre/post verifies multiset
      preservation exactly without storing snapshots.

    Audit conservation (v0.43):

    - For B: ``digest_before != digest_after`` (flatten changes the multiset)
      EXCEPT in the legitimate ``n_cells_changed == 0`` degenerate case
      (substrate already uniform pre-intervention).
    - For C: ``digest_before == digest_after`` (multiset preserved by
      permutation).
    - For both: ``abs(total_food_after - total_food_before)`` within
      float-32 tolerance.
    """

    intervention_kind: str  # "flatten_food_at_tick50" | "shuffle_food_at_tick50"
    intervention_tick: int  # 50
    effective_tick: int  # 51
    n_eligible_cells: int  # cells with kind in {EMPTY, FOOD} at tick 50
    n_cells_changed: int  # cells whose food_value or kind changed
    total_food_before: float
    total_food_after: float
    eligible_cells_digest: str
    food_multiset_digest_before: str
    food_multiset_digest_after: str


@dataclass(frozen=True)
class RespawnScheduleByIntervention:
    """v0.44: emitted at the tick-50/tick-51 boundary when a respawn-schedule
    rewrite intervention fires. Two kinds:

    - ``"delay_respawn_schedule_plus_25_at_tick50"`` (arm B): every eligible
      cell's ``respawn_at_tick`` is incremented by +25. Schedule multiset
      shifts by +25 elementwise; min/max/sum all shift by +25; food_value
      and kind topology unchanged.
    - ``"permute_respawn_schedule_reverse_row_major_at_tick50"`` (arm C):
      ``respawn_at_tick`` values are reassigned across (x, y)-sorted
      eligible cells via reverse-row-major mapping. Multiset of refill
      ticks exactly preserved; min/max/sum unchanged; food_value and kind
      topology unchanged.

    Eligibility predicate: ``kind in {EMPTY, FOOD} AND respawn_at_tick > 0``.
    HAZARD/WALL/SAFE cells excluded; cells with ``respawn_at_tick == 0`` (no
    pending refill) excluded.

    Distinct from ``FoodRedistributedByIntervention`` because the rewritten
    layer is int32 schedule ticks, not float32 food values; the digest /
    extrema fields differ accordingly.

    Digests (locked formats):

    - ``eligible_cells_digest``: SHA-256 hex of
      ``b"\\n".join(f"{x},{y}".encode() for (x, y) in sorted_eligible_cells)``.
      Pure function of tick-50 eligibility set.
    - ``respawn_multiset_digest_before`` / ``respawn_multiset_digest_after``:
      SHA-256 hex of ``struct.pack(f"<{n}i", *sorted_ticks)`` where
      ``sorted_ticks`` is the int32 ``respawn_at_tick`` vector over eligible
      cells, sorted ascending.

    Audit conservation (v0.44):

    - For B (delay): ``sum_after == sum_before + 25 * n_eligible_cells``;
      ``min_after == min_before + 25``; ``max_after == max_before + 25``;
      ``digest_before != digest_after`` (multiset shifted).
    - For C (permute): ``sum_after == sum_before``; ``min_after ==
      min_before``; ``max_after == max_before``; ``digest_before ==
      digest_after`` (permutation preserves the sorted multiset).
    """

    intervention_kind: str  # "delay_respawn_schedule_plus_25_at_tick50" |
    #                        "permute_respawn_schedule_reverse_row_major_at_tick50"
    intervention_tick: int  # 50
    effective_tick: int  # 51
    n_eligible_cells: int
    n_cells_changed: int
    min_respawn_tick_before: int
    max_respawn_tick_before: int
    min_respawn_tick_after: int
    max_respawn_tick_after: int
    sum_respawn_tick_before: int
    sum_respawn_tick_after: int
    eligible_cells_digest: str
    respawn_multiset_digest_before: str
    respawn_multiset_digest_after: str


AnyEvent = (
    AgentMoved
    | AgentStayed
    | AteFood
    | HazardEntered
    | HazardDamageApplied
    | ReproductionRequested
    | AgentBorn
    | AgentDied
    | FoodRespawned
    | PoolRespawnDenied
    | PoolBirthDenied
    | BirthDeniedParentEnergy
    | LineageKilledByIntervention
    | FoodRedistributedByIntervention
    | RespawnScheduleByIntervention
)


@dataclass(frozen=True)
class LoggedEvent:
    """Tick-stamped envelope for an event in ``HHModel.event_log``.

    Most events do not carry their own ``tick`` field (movements, eats,
    hazard damage). Instead of bloating every event dataclass with a tick
    field, the model wraps each event with the current ``tick_count`` at
    emission time. ``io/jsonl_writer.py`` reads the envelope to produce
    ``{"tick": T, "type": ..., "event": {...}}`` JSONL lines.
    """

    tick: int
    event: AnyEvent


# ---------------------------------------------------------------------------
# Named blinker signals — one per event type
# ---------------------------------------------------------------------------
#
# Subscribers connect via ``signal_for(EventType).connect(handler)``. Senders
# call ``signal_for(type(event)).send(model, event=event)``. The ``model``
# sender lets subscribers filter by simulation instance during batch runs.
#
# Signals are NamedSignals (process-wide singletons keyed by name); creating a
# second signal with the same name returns the same object. Tests can
# disconnect handlers in teardown via ``.disconnect(handler)``.

_SIGNAL_NAMES: dict[type, str] = {
    AgentMoved: "hh.agent_moved",
    AgentStayed: "hh.agent_stayed",
    AteFood: "hh.ate_food",
    HazardEntered: "hh.hazard_entered",
    HazardDamageApplied: "hh.hazard_damage_applied",
    ReproductionRequested: "hh.reproduction_requested",
    AgentBorn: "hh.agent_born",
    AgentDied: "hh.agent_died",
    FoodRespawned: "hh.food_respawned",
    PoolRespawnDenied: "hh.pool_respawn_denied",
    PoolBirthDenied: "hh.pool_birth_denied",
    BirthDeniedParentEnergy: "hh.birth_denied_parent_energy",
    LineageKilledByIntervention: "hh.lineage_killed_by_intervention",
    FoodRedistributedByIntervention: "hh.food_redistributed_by_intervention",
    RespawnScheduleByIntervention: "hh.respawn_schedule_by_intervention",
}


def signal_for(event_type: type) -> blinker.NamedSignal:
    """Return the blinker signal corresponding to an event class."""
    name = _SIGNAL_NAMES.get(event_type)
    if name is None:
        msg = f"No signal registered for event type {event_type!r}"
        raise KeyError(msg)
    return blinker.signal(name)


def emit(sender: object, event: AnyEvent) -> None:
    """Send ``event`` on its named signal. ``sender`` is conventionally the model."""
    signal_for(type(event)).send(sender, event=event)
