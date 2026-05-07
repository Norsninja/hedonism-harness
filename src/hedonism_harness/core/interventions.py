"""v0.42: experimental intervention layer for causal probes.

This module is the FIRST sim-mechanics change since v0.27. It adds an
optional, deterministic, additive intervention that can extinct a chosen
lineage at the tick-50/tick-51 boundary, leaving the surviving lineages
to continue from a counterfactual state.

The default-None code path is byte-identical to all pre-v0.42 behaviour;
``run_chamber(optional_intervention=None, ...)`` produces events.jsonl
files indistinguishable from v0.21..v0.41 outputs (regression-guarded by
[[tests/test_world_intervention_hook.py]]).

Pre-reg: [[docs/experiments/fear_hunger_v0.42.md]].

Selection rules (locked):

- ``leader``: at the moment the intervention fires, the lineage with the
  most living agents wins. Tie-break: lowest ``lineage_id`` (mirrors
  v0.35 / v0.37 / v0.38 convention).
- ``size_matched_nonleader``: at the moment the intervention fires,
  among non-leader lineages with >=1 living agent, choose the one whose
  living-agent count is closest to the leader's count. Tie-break:
  lowest ``lineage_id``. If no non-leader lineage has any living agents,
  ``InterventionResult.control_unavailable=True`` and no kill happens.

Determinism contract:

- Selection is a pure function of living-agent state at the firing
  moment. The state is itself deterministic given the seed.
- No new RNG is introduced; no shuffling happens during selection.
- Killing all agents of the chosen lineage uses each agent's existing
  ``mark_dead`` -> ``record_death`` -> ``CellAgent.remove`` path, so
  pool residual is credited normally and the per-agent
  ``AgentDied(cause=DeathCause.INTERVENTION)`` event is emitted.
- One summary ``LineageKilledByIntervention`` event is emitted after
  all per-agent deaths fire, so downstream audits can find the
  intervention's target lineage and role without scanning every
  AgentDied.

The intervention type variants (``"null"``, ``"kill_tick50_leader"``,
``"kill_size_matched_nonleader"``) are explicit string literals rather
than an enum so v0.43+ can extend the catalogue (birth-suppression,
energy-drain, etc.) without modifying this module's existing logic.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

from hedonism_harness.core.body import DeathCause, mark_dead
from hedonism_harness.core.events import (
    BirthRedirectedByIntervention,
    FoodRedistributedByIntervention,
    LineageKilledByIntervention,
    RespawnScheduleByIntervention,
)
from hedonism_harness.core.world import CellKind

if TYPE_CHECKING:
    from hedonism_harness.mesa_agents import HHAgent
    from hedonism_harness.model import HHModel


# ---------------------------------------------------------------------------
# Locked anchors (committed in pre-reg; mutating these is a corpus invalidation)
# ---------------------------------------------------------------------------


DEFAULT_INTERVENTION_TICK: int = 50  # tick at which leader is identified
DEFAULT_EFFECTIVE_TICK: int = 51  # tick at which agents are killed


KIND_NULL: str = "null"
KIND_KILL_LEADER: str = "kill_tick50_leader"
KIND_KILL_SMNONLEADER: str = "kill_size_matched_nonleader"
# v0.43 substrate-rewrite kinds (additive; no agent deaths emitted).
# Halted pre-sweep on substrate-mismatch finding (h=8 saturation); the code
# paths remain dispatchable for byte-identity regression but are unused by
# V0_43R_INTERVENTION_ARMS. See [[docs/experiments/fear_hunger_v0.43.md]]
# SUBSTRATE_PREFLIGHT_HALT addendum.
KIND_FLATTEN_FOOD: str = "flatten_food_at_tick50"
KIND_SHUFFLE_FOOD: str = "shuffle_food_at_tick50"
# v0.43R substrate-rewrite kinds (additive; no agent deaths emitted).
# Replacement for halted v0.43 design; operative at h=8 (the v0.42 primary
# test hazard) on the saturated substrate. See
# [[docs/experiments/fear_hunger_v0.43R.md]].
KIND_REDUCE_DENSITY_50PCT: str = "reduce_food_density_50pct_at_tick50"
KIND_DENSITY_PRESERVING_PERTURBATION: str = "density_preserving_perturbation_at_tick50"
# v0.44 respawn-schedule rewrite kinds (additive; no agent deaths emitted).
# Operates on ``world.respawn_at_tick`` rather than ``world.food_value``;
# emits ``RespawnScheduleByIntervention``. See
# [[docs/experiments/fear_hunger_v0.44.md]].
KIND_DELAY_RESPAWN_PLUS_25: str = "delay_respawn_schedule_plus_25_at_tick50"
KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR: str = "permute_respawn_schedule_reverse_row_major_at_tick50"
# v0.45 birth-position rewrite kinds (additive; no agent deaths emitted).
# Continuous firing from ``effective_tick >= 51``; the chamber driver gates
# the per-birth callback at the call site (``tick > 50``). Operates on
# offspring placement only; default reproduction (tick <= 50, A_null arms,
# pre-v0.45 sweeps) is byte-identical. Emits
# ``BirthRedirectedByIntervention`` once per successful redirect. See
# [[docs/experiments/fear_hunger_v0.45.md]].
KIND_UNIFORM_VALID_REGION_BIRTH: str = "uniform_valid_region_birth_position_after_tick50"
KIND_UNIFORM_NEIGHBOR_BIRTH: str = "uniform_neighbor_birth_position_after_tick50"

# v0.45 RNG stream label (locked; consumed via ``model.streams``).
V045_RNG_STREAM_LABEL: str = "v0_45_birth_position_intervention"

# v0.45 birth-redirection eligibility predicate scopes both B (global) and
# C (parent-adjacent) eligible-cell sets to non-HAZARD non-WALL non-occupied
# in-bounds cells. This is INTERVENTION-LOCAL; ``core/reproduction.py``'s
# ``_is_placeable`` is unchanged.
_V045_BIRTH_SAFE_KINDS: frozenset[int] = frozenset(
    {int(CellKind.EMPTY), int(CellKind.FOOD), int(CellKind.SAFE)}
)

ROLE_LEADER: str = "leader"
ROLE_SMNONLEADER: str = "size_matched_nonleader"
ROLE_NONE: str = "none"

# v0.43: cells with kind in this set at tick 50 are eligible for food
# redistribution. HAZARD, WALL, SAFE cells are preserved untouched.
_ELIGIBLE_KINDS: frozenset[int] = frozenset({int(CellKind.EMPTY), int(CellKind.FOOD)})

# v0.43R locked constants (pre-reg-anchored; mutating these is a corpus invalidation).
B_DENSITY_FACTOR: float = 0.5
C_PAIR_SPLIT_FIRST: float = 0.25
C_PAIR_SPLIT_SECOND: float = 0.75

# v0.44 locked constants (pre-reg-anchored).
B_DELAY_TICKS: int = 25


_VALID_KINDS: frozenset[str] = frozenset(
    {
        KIND_NULL,
        KIND_KILL_LEADER,
        KIND_KILL_SMNONLEADER,
        KIND_FLATTEN_FOOD,
        KIND_SHUFFLE_FOOD,
        KIND_REDUCE_DENSITY_50PCT,
        KIND_DENSITY_PRESERVING_PERTURBATION,
        KIND_DELAY_RESPAWN_PLUS_25,
        KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
        KIND_UNIFORM_VALID_REGION_BIRTH,
        KIND_UNIFORM_NEIGHBOR_BIRTH,
    }
)


_BIRTH_REDIRECT_KINDS: frozenset[str] = frozenset(
    {
        KIND_UNIFORM_VALID_REGION_BIRTH,
        KIND_UNIFORM_NEIGHBOR_BIRTH,
    }
)


_FOOD_REDISTRIBUTION_KINDS: frozenset[str] = frozenset(
    {
        KIND_FLATTEN_FOOD,
        KIND_SHUFFLE_FOOD,
        KIND_REDUCE_DENSITY_50PCT,
        KIND_DENSITY_PRESERVING_PERTURBATION,
    }
)


_RESPAWN_SCHEDULE_KINDS: frozenset[str] = frozenset(
    {
        KIND_DELAY_RESPAWN_PLUS_25,
        KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR,
    }
)


@dataclass(frozen=True)
class InterventionConfig:
    """Configuration for a v0.42 hard-kill intervention.

    ``kind``:
      - ``"null"``: no intervention fires. Equivalent to passing
        ``None`` to ``run_chamber``; included as an explicit value so
        the v0.42 sweep can label the A_null arm without special-casing
        the comparison-grid wiring.
      - ``"kill_tick50_leader"``: extinct the lineage with the most
        living agents at ``intervention_tick``.
      - ``"kill_size_matched_nonleader"``: extinct the non-leader
        lineage whose living-agent count is closest to the leader's at
        ``intervention_tick``. ``control_unavailable=True`` if no
        non-leader has any living agents.

    ``intervention_tick`` / ``effective_tick``: the boundary at which
    the intervention fires. Default values are the v0.42 locked
    anchors (50, 51); changing them at the CONFIG site is allowed so
    v0.43+ can probe other boundaries without modifying this module.
    """

    kind: Literal[
        "null",
        "kill_tick50_leader",
        "kill_size_matched_nonleader",
        "flatten_food_at_tick50",
        "shuffle_food_at_tick50",
        "reduce_food_density_50pct_at_tick50",
        "density_preserving_perturbation_at_tick50",
        "delay_respawn_schedule_plus_25_at_tick50",
        "permute_respawn_schedule_reverse_row_major_at_tick50",
        "uniform_valid_region_birth_position_after_tick50",
        "uniform_neighbor_birth_position_after_tick50",
    ] = KIND_NULL
    intervention_tick: int = DEFAULT_INTERVENTION_TICK
    effective_tick: int = DEFAULT_EFFECTIVE_TICK

    def __post_init__(self) -> None:
        if self.kind not in _VALID_KINDS:
            msg = (
                f"InterventionConfig.kind must be one of {sorted(_VALID_KINDS)}; got {self.kind!r}"
            )
            raise ValueError(msg)
        if self.effective_tick != self.intervention_tick + 1:
            msg = (
                f"InterventionConfig requires effective_tick == intervention_tick + 1; "
                f"got intervention_tick={self.intervention_tick}, "
                f"effective_tick={self.effective_tick}"
            )
            raise ValueError(msg)


@dataclass(frozen=True)
class InterventionResult:
    """Outcome of one intervention firing.

    ``fired``: True iff at least one agent was killed by the intervention.
    False for ``kind="null"``, and for ``kind="kill_size_matched_nonleader"``
    when ``control_unavailable=True``.

    ``lineage_id``: the target lineage's id, or ``None`` if the intervention
    did not fire.

    ``lineage_role``: ``"leader"`` | ``"size_matched_nonleader"`` | ``"none"``.

    ``n_killed``: count of agents extincted. 0 when ``fired=False``.

    ``control_unavailable``: True iff ``kind="kill_size_matched_nonleader"``
    AND no non-leader lineage had any living agents at firing time.
    """

    fired: bool
    lineage_id: int | None
    lineage_role: str  # ROLE_LEADER | ROLE_SMNONLEADER | ROLE_NONE
    n_killed: int
    control_unavailable: bool


# ---------------------------------------------------------------------------
# Selection helpers (pure functions of living-agent state)
# ---------------------------------------------------------------------------


def _living_agents_by_lineage(model: HHModel) -> dict[int, list[HHAgent]]:
    """Bucket living agents by ``lineage_id``. Lower lineage_ids appear
    first in the per-bucket list because Mesa's AgentSet preserves
    spawn order within ``model.agents`` and founders spawn in
    ascending lineage_id order.

    Duck-typed: any object exposing ``.body.alive`` and ``.body.lineage_id``
    counts. Real callers pass ``HHAgent`` instances; tests use lightweight
    fakes with the same surface.
    """
    out: dict[int, list[HHAgent]] = {}
    for agent in model.agents:
        body = getattr(agent, "body", None)
        if body is None:
            continue
        if not getattr(body, "alive", False):
            continue
        out.setdefault(body.lineage_id, []).append(agent)
    return out


def _identify_leader(buckets: dict[int, list[HHAgent]]) -> int | None:
    """Return the lineage_id with the most living agents; tie-break by
    lowest lineage_id. Return None if no lineage has any living agents.
    """
    if not buckets:
        return None
    best_lineage: int | None = None
    best_count: int = -1
    for lineage_id in sorted(buckets):  # ascending lineage_id (tie-break)
        count = len(buckets[lineage_id])
        if count > best_count:
            best_count = count
            best_lineage = lineage_id
    return best_lineage


def _identify_size_matched_nonleader(
    buckets: dict[int, list[HHAgent]], leader_id: int
) -> int | None:
    """Return the non-leader lineage_id whose living-agent count is closest
    to the leader's. Tie-break by lowest lineage_id. Return None if no
    non-leader lineage has any living agents.
    """
    leader_count = len(buckets.get(leader_id, []))
    candidates = [
        (lineage_id, len(agents))
        for lineage_id, agents in buckets.items()
        if lineage_id != leader_id
    ]
    if not candidates:
        return None
    # Ascending lineage_id ensures the lowest-id wins ties on |count - leader_count|.
    candidates.sort(key=lambda pair: pair[0])
    best_lineage: int | None = None
    best_distance: int | None = None
    for lineage_id, count in candidates:
        distance = abs(count - leader_count)
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_lineage = lineage_id
    return best_lineage


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def _kill_lineage(model: HHModel, agents: list[HHAgent]) -> int:
    """Extinct ``agents`` via the existing ``mark_dead`` / ``record_death`` /
    ``CellAgent.remove`` path. Returns the count actually killed (some
    agents may already be dead in pathological cases; those are skipped).

    This mirrors the per-agent steps of ``HHAgent.death_sweep`` for
    starvation/injury, except the cause is ``DeathCause.INTERVENTION``
    and the call originates outside ``model.step()``. Pool residual is
    credited via ``model.record_death`` -> ``EnergyPool.credit_death_residual``
    using each body's surviving energy, preserving conservation invariants
    that v0.19 onwards rely on.
    """
    n_killed = 0
    for agent in agents:
        if not agent.body.alive:
            continue
        agent.body = mark_dead(agent.body, DeathCause.INTERVENTION)
        model.record_death(agent)
        agent.remove()
        n_killed += 1
    return n_killed


def apply_intervention(  # noqa: PLR0911 — additive verdict-cell dispatch; refactor would obscure intent.
    model: HHModel, config: InterventionConfig
) -> InterventionResult:
    """Apply ``config`` to ``model`` at the firing moment. Caller is
    responsible for invoking this exactly once per run, at
    ``model.tick_count == config.effective_tick``. The chamber driver
    enforces that contract via [[experiments/fear_hunger_chamber.py]].

    Behaviour by kind:

    - ``KIND_NULL``: no-op. Returns ``InterventionResult(fired=False, ...)``.
      No event is emitted; events.jsonl is byte-identical to the
      no-intervention path on this seed.
    - ``KIND_KILL_LEADER``: identify the tick-50 leader, kill all of that
      lineage's living agents, emit one ``LineageKilledByIntervention``
      summary event with ``lineage_role=ROLE_LEADER``.
    - ``KIND_KILL_SMNONLEADER``: identify the tick-50 leader (for the
      size match), then identify the size-matched non-leader, then kill
      all of that lineage's living agents and emit the summary event
      with ``lineage_role=ROLE_SMNONLEADER``. If no non-leader has any
      living agents, set ``control_unavailable=True`` and emit no event.
    - ``KIND_FLATTEN_FOOD`` (v0.43): redistribute food uniformly across
      all eligible cells (kind in {EMPTY, FOOD}) and update kind to
      FOOD where mean > 0 else EMPTY. Emit one
      ``FoodRedistributedByIntervention`` event. No agents killed.
    - ``KIND_SHUFFLE_FOOD`` (v0.43): reverse-row-major permutation of
      food values across (x, y)-sorted eligible cells. Multiset
      preserved exactly. Emit one ``FoodRedistributedByIntervention``
      event. No agents killed.
    """
    if config.kind == KIND_NULL:
        return InterventionResult(
            fired=False,
            lineage_id=None,
            lineage_role=ROLE_NONE,
            n_killed=0,
            control_unavailable=False,
        )

    if config.kind in _FOOD_REDISTRIBUTION_KINDS:
        return _apply_food_redistribution(model, config)

    if config.kind in _RESPAWN_SCHEDULE_KINDS:
        return _apply_respawn_schedule_rewrite(model, config)

    if config.kind in _BIRTH_REDIRECT_KINDS:
        # v0.45 birth-redirection kinds fire continuously per-birth via
        # the chamber driver's call-site callback; ``apply_intervention``
        # at tick 51 is a no-op for these kinds. The callback is already
        # installed on ``model.v045_birth_redirect_callback`` by the
        # chamber driver setup; this function is invoked once at tick 51
        # and returns immediately without emitting any event or killing
        # any agent.
        return InterventionResult(
            fired=False,
            lineage_id=None,
            lineage_role=ROLE_NONE,
            n_killed=0,
            control_unavailable=False,
        )

    buckets = _living_agents_by_lineage(model)
    leader_id = _identify_leader(buckets)
    if leader_id is None:
        # No living lineage at firing time; nothing to kill regardless of kind.
        return InterventionResult(
            fired=False,
            lineage_id=None,
            lineage_role=ROLE_NONE,
            n_killed=0,
            control_unavailable=(config.kind == KIND_KILL_SMNONLEADER),
        )

    if config.kind == KIND_KILL_LEADER:
        target_id = leader_id
        target_role = ROLE_LEADER
        control_unavailable = False
    elif config.kind == KIND_KILL_SMNONLEADER:
        smnonleader_id = _identify_size_matched_nonleader(buckets, leader_id)
        if smnonleader_id is None:
            return InterventionResult(
                fired=False,
                lineage_id=None,
                lineage_role=ROLE_NONE,
                n_killed=0,
                control_unavailable=True,
            )
        target_id = smnonleader_id
        target_role = ROLE_SMNONLEADER
        control_unavailable = False
    else:  # pragma: no cover — guarded by InterventionConfig.__post_init__.
        msg = f"unreachable kind {config.kind!r}"
        raise AssertionError(msg)

    target_agents = buckets.get(target_id, [])
    n_killed = _kill_lineage(model, target_agents)

    summary = LineageKilledByIntervention(
        lineage_id=target_id,
        n_killed=n_killed,
        lineage_role=target_role,
        intervention_tick=config.intervention_tick,
        effective_tick=config.effective_tick,
    )
    model.record_event(summary)

    return InterventionResult(
        fired=True,
        lineage_id=target_id,
        lineage_role=target_role,
        n_killed=n_killed,
        control_unavailable=control_unavailable,
    )


# ---------------------------------------------------------------------------
# v0.43 food-redistribution helpers
# ---------------------------------------------------------------------------


def _eligible_cells(model: HHModel) -> list[tuple[int, int]]:
    """Return cells with ``kind in {EMPTY, FOOD}`` at the firing moment,
    sorted by ``(x, y)`` ascending. Excludes HAZARD, WALL, SAFE cells.
    Pure function of ``model.world.kind_layer``; no RNG.
    """
    kind_layer = model.world.kind_layer
    width = model.world.width
    height = model.world.height
    out: list[tuple[int, int]] = []
    # Iterate (x, y) ascending so the result is already sorted.
    for x in range(width):
        for y in range(height):
            if int(kind_layer[x, y]) in _ELIGIBLE_KINDS:
                out.append((x, y))
    return out


def _eligible_cells_digest(cells: list[tuple[int, int]]) -> str:
    """SHA-256 hex of ``(x, y)`` pairs joined with newlines. Pure function
    of the cell list; identical across runs at the same chamber config.
    """
    payload = b"\n".join(f"{x},{y}".encode() for (x, y) in cells)
    return hashlib.sha256(payload).hexdigest()


def _food_multiset_digest(values: np.ndarray) -> str:
    """SHA-256 hex over the float32 ``values`` vector, sorted ascending,
    packed via ``struct.pack(f"<{n}f", *sorted_vals)``. Two arrays produce
    the same digest iff they share the same multiset (exact float32
    equality after sort).
    """
    vals_f32 = np.asarray(values, dtype=np.float32)
    sorted_vals = np.sort(vals_f32)
    packed = struct.pack(f"<{len(sorted_vals)}f", *sorted_vals.tolist())
    return hashlib.sha256(packed).hexdigest()


def _apply_food_redistribution(model: HHModel, config: InterventionConfig) -> InterventionResult:
    """Apply a v0.43 substrate-rewrite intervention. Both kinds:

    - Compute ``eligible`` (cells with kind in {EMPTY, FOOD}, sorted (x, y)).
    - Snapshot pre-state: ``values_before``, ``digest_before``,
      ``cells_digest``, ``total_food_before``.
    - For B (flatten): write mean to every eligible cell.
    - For C (shuffle): write reverse-row-major permutation.
    - Recompute kind_layer for eligible cells based on new food_value
      (FOOD if > 0 else EMPTY); HAZARD, WALL, SAFE cells untouched.
    - Compute post-state digests and totals.
    - Emit ``FoodRedistributedByIntervention``.

    The intervention always fires (always emits the event), even in
    degenerate cases (already-uniform food before flatten; reverse
    permutation that fixes all values). ``n_cells_changed`` records
    whether any cell's ``food_value`` or ``kind`` actually changed.
    """
    cells = _eligible_cells(model)
    n_eligible = len(cells)

    if n_eligible == 0:
        # Pathological chamber: no eligible cells. Emit a degenerate event
        # so the audit can detect the condition without a special path,
        # then return fired=True (event emitted) with zero changes.
        empty_digest = hashlib.sha256(b"").hexdigest()
        summary = FoodRedistributedByIntervention(
            intervention_kind=config.kind,
            intervention_tick=config.intervention_tick,
            effective_tick=config.effective_tick,
            n_eligible_cells=0,
            n_cells_changed=0,
            total_food_before=0.0,
            total_food_after=0.0,
            eligible_cells_digest=empty_digest,
            food_multiset_digest_before=empty_digest,
            food_multiset_digest_after=empty_digest,
        )
        model.record_event(summary)
        return InterventionResult(
            fired=True,
            lineage_id=None,
            lineage_role=ROLE_NONE,
            n_killed=0,
            control_unavailable=False,
        )

    food_layer = model.world.food_value
    kind_layer = model.world.kind_layer

    xs = np.array([x for (x, _y) in cells], dtype=np.int64)
    ys = np.array([y for (_x, y) in cells], dtype=np.int64)
    values_before = food_layer[xs, ys].astype(np.float32, copy=True)
    kinds_before = kind_layer[xs, ys].astype(np.uint8, copy=True)
    total_before = float(values_before.sum(dtype=np.float64))
    cells_digest = _eligible_cells_digest(cells)
    digest_before = _food_multiset_digest(values_before)

    if config.kind == KIND_FLATTEN_FOOD:
        # Float32 division mirrors the storage type so the audit's
        # tolerance is meaningful. mean is broadcast as float32.
        mean_val = np.float32(total_before) / np.float32(n_eligible)
        values_after = np.full(n_eligible, mean_val, dtype=np.float32)
    elif config.kind == KIND_SHUFFLE_FOOD:
        # Reverse the (x, y)-sorted vector in place.
        values_after = values_before[::-1].copy()
    elif config.kind == KIND_REDUCE_DENSITY_50PCT:
        # v0.43R B arm. Multiply every eligible cell by B_DENSITY_FACTOR
        # (locked at 0.5). Total drops to factor * total_before exactly
        # (modulo float32 epsilon).
        values_after = (values_before * np.float32(B_DENSITY_FACTOR)).astype(np.float32, copy=False)
    elif config.kind == KIND_DENSITY_PRESERVING_PERTURBATION:
        # v0.43R C arm. Per-pair 25/75 redistribution over (x, y)-sorted
        # consecutive eligible cells. Each pair (i, i+1) where i is even
        # gets:
        #     new[i]   = C_PAIR_SPLIT_FIRST  * (old[i] + old[i+1])
        #     new[i+1] = C_PAIR_SPLIT_SECOND * (old[i] + old[i+1])
        # Per-pair sum exactly preserved; grand total exactly preserved.
        # If n_eligible is odd, the last cell stays unchanged.
        values_after = values_before.copy()
        n_pairs = n_eligible - (n_eligible % 2)
        for i in range(0, n_pairs, 2):
            pair_sum = np.float32(values_after[i]) + np.float32(values_after[i + 1])
            values_after[i] = np.float32(C_PAIR_SPLIT_FIRST) * pair_sum
            values_after[i + 1] = np.float32(C_PAIR_SPLIT_SECOND) * pair_sum
    else:  # pragma: no cover — guarded by InterventionConfig.__post_init__.
        msg = f"unreachable food-redistribution kind {config.kind!r}"
        raise AssertionError(msg)

    # FOOD where new value > 0 else EMPTY. Excludes hazard/wall/safe (those
    # cells were not in the eligible set).
    kinds_after = np.where(
        values_after > np.float32(0.0),
        np.uint8(int(CellKind.FOOD)),
        np.uint8(int(CellKind.EMPTY)),
    ).astype(np.uint8)

    # n_cells_changed counts cells whose food_value OR kind changed.
    food_changed_mask = values_after != values_before
    kind_changed_mask = kinds_after != kinds_before
    changed_mask = food_changed_mask | kind_changed_mask
    n_cells_changed = int(changed_mask.sum())

    # Write back to the world layers.
    food_layer[xs, ys] = values_after
    kind_layer[xs, ys] = kinds_after

    total_after = float(values_after.sum(dtype=np.float64))
    digest_after = _food_multiset_digest(values_after)

    summary = FoodRedistributedByIntervention(
        intervention_kind=config.kind,
        intervention_tick=config.intervention_tick,
        effective_tick=config.effective_tick,
        n_eligible_cells=n_eligible,
        n_cells_changed=n_cells_changed,
        total_food_before=total_before,
        total_food_after=total_after,
        eligible_cells_digest=cells_digest,
        food_multiset_digest_before=digest_before,
        food_multiset_digest_after=digest_after,
    )
    model.record_event(summary)

    return InterventionResult(
        fired=True,
        lineage_id=None,
        lineage_role=ROLE_NONE,
        n_killed=0,
        control_unavailable=False,
    )


# ---------------------------------------------------------------------------
# v0.44 respawn-schedule helpers
# ---------------------------------------------------------------------------


def _eligible_respawn_cells(model: HHModel) -> list[tuple[int, int]]:
    """Return cells with ``kind in {EMPTY, FOOD} AND respawn_at_tick > 0`` at
    the firing moment, sorted by ``(x, y)`` ascending. Excludes HAZARD,
    WALL, SAFE cells; excludes cells with no pending refill
    (``respawn_at_tick == 0``).
    """
    kind_layer = model.world.kind_layer
    respawn = model.world.respawn_at_tick
    width = model.world.width
    height = model.world.height
    out: list[tuple[int, int]] = []
    for x in range(width):
        for y in range(height):
            if int(kind_layer[x, y]) in _ELIGIBLE_KINDS and int(respawn[x, y]) > 0:
                out.append((x, y))
    return out


def _respawn_multiset_digest(values: np.ndarray) -> str:
    """SHA-256 hex over the int32 ``values`` vector, sorted ascending,
    packed via ``struct.pack(f"<{n}i", *sorted_vals)``. Two arrays produce
    the same digest iff they share the same multiset (exact int32 equality
    after sort).
    """
    vals_i32 = np.asarray(values, dtype=np.int32)
    sorted_vals = np.sort(vals_i32)
    packed = struct.pack(f"<{len(sorted_vals)}i", *sorted_vals.tolist())
    return hashlib.sha256(packed).hexdigest()


def _apply_respawn_schedule_rewrite(
    model: HHModel, config: InterventionConfig
) -> InterventionResult:
    """Apply a v0.44 respawn-schedule rewrite. Two kinds:

    - ``KIND_DELAY_RESPAWN_PLUS_25`` (B arm): increment every eligible
      cell's ``respawn_at_tick`` by ``B_DELAY_TICKS`` (locked at +25).
      Schedule multiset shifts by exactly +25 elementwise.
    - ``KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR`` (C arm): reassign refill
      ticks across (x, y)-sorted eligible cells via reverse-row-major
      mapping (``new[i] = old[n - 1 - i]``). Multiset of refill ticks
      exactly preserved; min/max/sum unchanged.

    Both kinds:
      - Operate only on ``world.respawn_at_tick``.
      - Leave ``food_value``, ``kind_layer``, hazard/wall/safe untouched.
      - Always fire (always emit ``RespawnScheduleByIntervention``);
        ``n_cells_changed`` records whether any cell's value actually
        changed (B always changes all eligible cells; C changes any cell
        whose new tick differs from its old tick).
    """
    cells = _eligible_respawn_cells(model)
    n_eligible = len(cells)

    if n_eligible == 0:
        empty_digest = hashlib.sha256(b"").hexdigest()
        summary = RespawnScheduleByIntervention(
            intervention_kind=config.kind,
            intervention_tick=config.intervention_tick,
            effective_tick=config.effective_tick,
            n_eligible_cells=0,
            n_cells_changed=0,
            min_respawn_tick_before=0,
            max_respawn_tick_before=0,
            min_respawn_tick_after=0,
            max_respawn_tick_after=0,
            sum_respawn_tick_before=0,
            sum_respawn_tick_after=0,
            eligible_cells_digest=empty_digest,
            respawn_multiset_digest_before=empty_digest,
            respawn_multiset_digest_after=empty_digest,
        )
        model.record_event(summary)
        return InterventionResult(
            fired=True,
            lineage_id=None,
            lineage_role=ROLE_NONE,
            n_killed=0,
            control_unavailable=False,
        )

    respawn_layer = model.world.respawn_at_tick

    xs = np.array([x for (x, _y) in cells], dtype=np.int64)
    ys = np.array([y for (_x, y) in cells], dtype=np.int64)
    values_before = respawn_layer[xs, ys].astype(np.int32, copy=True)
    cells_digest = _eligible_cells_digest(cells)
    digest_before = _respawn_multiset_digest(values_before)
    sum_before = int(values_before.sum(dtype=np.int64))
    min_before = int(values_before.min())
    max_before = int(values_before.max())

    if config.kind == KIND_DELAY_RESPAWN_PLUS_25:
        values_after = (values_before + np.int32(B_DELAY_TICKS)).astype(np.int32, copy=False)
    elif config.kind == KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR:
        values_after = values_before[::-1].copy()
    else:  # pragma: no cover — guarded by InterventionConfig.__post_init__.
        msg = f"unreachable respawn-schedule kind {config.kind!r}"
        raise AssertionError(msg)

    n_cells_changed = int((values_after != values_before).sum())

    respawn_layer[xs, ys] = values_after

    sum_after = int(values_after.sum(dtype=np.int64))
    min_after = int(values_after.min())
    max_after = int(values_after.max())
    digest_after = _respawn_multiset_digest(values_after)

    summary = RespawnScheduleByIntervention(
        intervention_kind=config.kind,
        intervention_tick=config.intervention_tick,
        effective_tick=config.effective_tick,
        n_eligible_cells=n_eligible,
        n_cells_changed=n_cells_changed,
        min_respawn_tick_before=min_before,
        max_respawn_tick_before=max_before,
        min_respawn_tick_after=min_after,
        max_respawn_tick_after=max_after,
        sum_respawn_tick_before=sum_before,
        sum_respawn_tick_after=sum_after,
        eligible_cells_digest=cells_digest,
        respawn_multiset_digest_before=digest_before,
        respawn_multiset_digest_after=digest_after,
    )
    model.record_event(summary)

    return InterventionResult(
        fired=True,
        lineage_id=None,
        lineage_role=ROLE_NONE,
        n_killed=0,
        control_unavailable=False,
    )


# ---------------------------------------------------------------------------
# v0.45 birth-redirection helpers + callback factory
# ---------------------------------------------------------------------------


def _is_v045_birth_safe_placeable(
    world,
    x: int,
    y: int,
    occupied: frozenset[tuple[int, int]] | None,
) -> bool:
    """v0.45 birth-redirection eligibility predicate. Returns True iff:

    - ``(x, y)`` is in-bounds (``0 <= x < world.width`` and
      ``0 <= y < world.height``).
    - ``world.kind_layer[x, y]`` is one of ``{EMPTY, FOOD, SAFE}``
      (excludes WALL and HAZARD).
    - ``(x, y)`` is not in ``occupied``.

    INTERVENTION-LOCAL: this predicate is used only by the v0.45
    birth-redirect callback. ``core/reproduction.py``'s ``_is_placeable``
    is unchanged and continues to govern default reproduction
    semantics (which permits HAZARD cells; the default chamber
    driver's behaviour is preserved exactly).
    """
    if x < 0 or y < 0:
        return False
    if x >= world.width or y >= world.height:
        return False
    if int(world.kind_layer[x, y]) not in _V045_BIRTH_SAFE_KINDS:
        return False
    return not (occupied is not None and (x, y) in occupied)


def _v045_eligible_global_cells(
    world,
    occupied: frozenset[tuple[int, int]] | None,
) -> list[tuple[int, int]]:
    """v0.45 B arm. Return all cells (x, y) satisfying
    ``_is_v045_birth_safe_placeable``, sorted (x, y) ascending.
    Excludes HAZARD/WALL and occupied/out-of-bounds cells.
    """
    out: list[tuple[int, int]] = []
    for x in range(world.width):
        for y in range(world.height):
            if _is_v045_birth_safe_placeable(world, x, y, occupied):
                out.append((x, y))
    return out


def _v045_eligible_neighbor_cells(
    world,
    parent,
    occupied: frozenset[tuple[int, int]] | None,
) -> list[tuple[int, int]]:
    """v0.45 C arm. Return parent's N/S/E/W neighbors filtered by
    ``_is_v045_birth_safe_placeable``, in deterministic (x, y)
    ascending order over the surviving neighbors.
    """
    candidates = [(parent.x + dx, parent.y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    valid = [c for c in candidates if _is_v045_birth_safe_placeable(world, c[0], c[1], occupied)]
    valid.sort()
    return valid


def make_v045_birth_redirect_callback(
    config: InterventionConfig,
    model,
):
    """Build the v0.45 birth-redirect callback bound to the
    intervention kind and the model's RNG.

    The returned callable receives ``(world, parent_body, occupied,
    original_placement)`` and returns either ``(x, y)`` for the
    redirected child or ``None`` to skip the birth.

    The callback is NEVER invoked for ``tick <= 50``; that gate
    lives in the call site (``mesa_agents.HHAgent._attempt_reproduction``).
    The callback assumes ``tick > 50`` unconditionally.

    Behaviour by kind:

    - B (``KIND_UNIFORM_VALID_REGION_BIRTH``): pick uniformly at
      random from ``_v045_eligible_global_cells(world, occupied)``
      using a dedicated RNG spawned from ``model.streams.mutation``.
      If empty, increment ``model.v045_skipped_redirect_counter`` and
      return ``None``.
    - C (``KIND_UNIFORM_NEIGHBOR_BIRTH``): pick uniformly at random
      from ``_v045_eligible_neighbor_cells(world, parent, occupied)``
      using the same RNG. If empty, increment the counter and
      return ``None``.

    On a successful redirect, the callback emits one
    ``BirthRedirectedByIntervention`` event (via
    ``model.record_event``) and returns the redirected ``(x, y)``.
    """
    if config.kind not in _BIRTH_REDIRECT_KINDS:
        msg = f"make_v045_birth_redirect_callback: kind {config.kind!r} is not a v0.45 kind"
        raise ValueError(msg)

    # Spawn a dedicated RNG from the mutation stream. v0.42..v0.44 sweeps
    # don't construct this callback so their mutation sequences are unaffected.
    callback_rng = model.streams.mutation.spawn(1)[0]
    kind = config.kind

    def callback(world, parent, occupied, original_placement):
        # Augment occupied with the parent's own cell. Mesa's grid is
        # capacity=1 and ``occupied_cells_excluding(parent)`` deliberately
        # omits the parent's cell so default ``find_adjacent_empty_cell``
        # works (the child is placed adjacent, not on the parent). The
        # v0.45 callback selects from the chamber-wide / neighbor-wide
        # eligible set, so we MUST exclude the parent's cell explicitly
        # to avoid picking it and crashing Mesa's add_agent.
        occupied_plus_parent = (occupied or frozenset()) | {(parent.x, parent.y)}
        if kind == KIND_UNIFORM_VALID_REGION_BIRTH:
            eligible = _v045_eligible_global_cells(world, occupied_plus_parent)
        else:  # KIND_UNIFORM_NEIGHBOR_BIRTH
            eligible = _v045_eligible_neighbor_cells(world, parent, occupied_plus_parent)
        n_valid = len(eligible)
        if n_valid == 0:
            model.v045_skipped_redirect_counter += 1
            return None
        idx = int(callback_rng.integers(0, n_valid))
        chosen = eligible[idx]
        # Emit the event (model.record_event wraps in LoggedEvent envelope).
        original_x = -1 if original_placement is None else int(original_placement[0])
        original_y = -1 if original_placement is None else int(original_placement[1])
        target_kind = CellKind(int(world.kind_layer[chosen[0], chosen[1]])).name
        manhattan = abs(parent.x - chosen[0]) + abs(parent.y - chosen[1])
        preserved_adjacency = manhattan == 1
        event = BirthRedirectedByIntervention(
            intervention_kind=kind,
            tick=int(model.tick_count),
            parent_id=int(parent.id),
            parent_lineage_id=int(parent.lineage_id),
            parent_x=int(parent.x),
            parent_y=int(parent.y),
            original_x=original_x,
            original_y=original_y,
            redirected_x=int(chosen[0]),
            redirected_y=int(chosen[1]),
            n_valid_cells=n_valid,
            target_cell_kind=target_kind,
            preserved_parent_adjacency=preserved_adjacency,
            rng_stream_label=V045_RNG_STREAM_LABEL,
        )
        model.record_event(event)
        return chosen

    return callback
