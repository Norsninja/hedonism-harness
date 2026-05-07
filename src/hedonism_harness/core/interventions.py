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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from hedonism_harness.core.body import DeathCause, mark_dead
from hedonism_harness.core.events import LineageKilledByIntervention

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

ROLE_LEADER: str = "leader"
ROLE_SMNONLEADER: str = "size_matched_nonleader"
ROLE_NONE: str = "none"


_VALID_KINDS: frozenset[str] = frozenset({KIND_NULL, KIND_KILL_LEADER, KIND_KILL_SMNONLEADER})


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

    kind: Literal["null", "kill_tick50_leader", "kill_size_matched_nonleader"] = KIND_NULL
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


def apply_intervention(model: HHModel, config: InterventionConfig) -> InterventionResult:
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
    """
    if config.kind == KIND_NULL:
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
