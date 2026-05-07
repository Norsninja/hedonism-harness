"""v0.42 core/interventions.py unit tests.

Coverage:
  - InterventionConfig validation (kind set, effective_tick == intervention_tick + 1).
  - Selection rules (leader, size-matched non-leader) on synthetic
    living-agent buckets with various tie-break configurations.
  - control_unavailable when no non-leader exists.
  - apply_intervention behaviour for each kind:
    * KIND_NULL: returns fired=False, no events emitted, no agents killed.
    * KIND_KILL_LEADER: kills the tick-50 leader's living agents only.
    * KIND_KILL_SMNONLEADER: kills the size-matched non-leader's living
      agents only; control_unavailable when no non-leader exists.
  - Event emission: AgentDied(cause=DeathCause.INTERVENTION) for each
    killed agent + one LineageKilledByIntervention summary event.
  - Pool residual conservation: bodies' surviving energy is credited to
    the energy pool when one is configured.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.events import AgentDied, LineageKilledByIntervention
from hedonism_harness.core.interventions import (
    DEFAULT_EFFECTIVE_TICK,
    DEFAULT_INTERVENTION_TICK,
    KIND_KILL_LEADER,
    KIND_KILL_SMNONLEADER,
    KIND_NULL,
    ROLE_LEADER,
    ROLE_NONE,
    ROLE_SMNONLEADER,
    InterventionConfig,
    apply_intervention,
)

# ---------------------------------------------------------------------------
# Synthetic model + agent doubles (no Mesa, no real simulation)
# ---------------------------------------------------------------------------


@dataclass
class _FakeBody:
    id: int
    lineage_id: int
    energy: float
    alive: bool = True
    death_cause: DeathCause | None = None


class _FakeAgent:
    """Just enough surface for apply_intervention's path:
    body, remove(), and isinstance(... HHAgent) compatibility.
    """

    def __init__(self, body: _FakeBody) -> None:
        self.body = body
        self.removed = False

    def remove(self) -> None:
        self.removed = True


class _FakePool:
    def __init__(self) -> None:
        self.credits: list[float] = []

    def credit_death_residual(self, amount: float) -> None:
        self.credits.append(float(amount))


class _FakeModel:
    def __init__(self, agents: list[_FakeAgent], *, with_pool: bool = True) -> None:
        self.agents = agents
        self.tick_count = DEFAULT_EFFECTIVE_TICK  # firing moment
        self.event_log: list = []
        self.energy_pool: _FakePool | None = _FakePool() if with_pool else None
        self.events_emitted: list = []

    def record_event(self, event) -> None:
        self.event_log.append(event)
        self.events_emitted.append(event)

    def record_death(self, agent: _FakeAgent) -> None:
        cause = agent.body.death_cause
        if cause is None:
            msg = "_FakeModel.record_death called before mark_dead"
            raise AssertionError(msg)
        if self.energy_pool is not None:
            self.energy_pool.credit_death_residual(float(agent.body.energy))
        died = AgentDied(agent_id=agent.body.id, cause=cause, tick=self.tick_count)
        self.event_log.append(died)
        self.events_emitted.append(died)


def _make_agents(buckets: dict[int, list[float]]) -> list[_FakeAgent]:
    """``buckets`` maps lineage_id -> list of energies. Returns flat list of
    fake agents; agent_ids are assigned sequentially in lineage_id-then-
    list-position order.
    """
    out: list[_FakeAgent] = []
    next_id = 1
    for lineage_id in sorted(buckets):
        for energy in buckets[lineage_id]:
            out.append(
                _FakeAgent(_FakeBody(id=next_id, lineage_id=lineage_id, energy=float(energy)))
            )
            next_id += 1
    return out


# ---------------------------------------------------------------------------
# InterventionConfig validation
# ---------------------------------------------------------------------------


def test_config_default_kind_is_null():
    cfg = InterventionConfig()
    assert cfg.kind == KIND_NULL
    assert cfg.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert cfg.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_config_rejects_unknown_kind():
    with pytest.raises(ValueError, match="kind must be one of"):
        InterventionConfig(kind="kill_random")


def test_config_requires_effective_tick_one_after_intervention_tick():
    with pytest.raises(ValueError, match="effective_tick == intervention_tick \\+ 1"):
        InterventionConfig(kind=KIND_KILL_LEADER, intervention_tick=50, effective_tick=52)


def test_config_accepts_custom_boundary_when_consistent():
    cfg = InterventionConfig(kind=KIND_KILL_LEADER, intervention_tick=10, effective_tick=11)
    assert cfg.intervention_tick == 10
    assert cfg.effective_tick == 11


# ---------------------------------------------------------------------------
# KIND_NULL: no-op
# ---------------------------------------------------------------------------


def test_null_kind_does_nothing():
    agents = _make_agents({0: [10.0, 10.0], 1: [10.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_NULL))

    assert result.fired is False
    assert result.lineage_id is None
    assert result.lineage_role == ROLE_NONE
    assert result.n_killed == 0
    assert result.control_unavailable is False
    assert model.events_emitted == []
    assert all(a.body.alive for a in agents)
    assert all(not a.removed for a in agents)


# ---------------------------------------------------------------------------
# Leader selection (KIND_KILL_LEADER)
# ---------------------------------------------------------------------------


def test_kill_leader_picks_largest_lineage():
    agents = _make_agents({0: [5.0], 1: [5.0, 5.0, 5.0], 2: [5.0, 5.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert result.fired is True
    assert result.lineage_id == 1  # 3 agents > others
    assert result.lineage_role == ROLE_LEADER
    assert result.n_killed == 3


def test_kill_leader_tie_break_lowest_lineage_id():
    agents = _make_agents({2: [5.0, 5.0], 5: [5.0, 5.0], 7: [5.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert result.lineage_id == 2  # tied with 5; lower wins
    assert result.n_killed == 2


def test_kill_leader_only_kills_leader_lineage_not_others():
    agents = _make_agents({0: [10.0], 1: [10.0, 10.0]})
    model = _FakeModel(agents)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    by_lineage = {a.body.lineage_id: a for a in agents}
    leader_agents = [a for a in agents if a.body.lineage_id == 1]
    nonleader_agents = [a for a in agents if a.body.lineage_id == 0]
    assert all(not a.body.alive for a in leader_agents)
    assert all(a.body.death_cause == DeathCause.INTERVENTION for a in leader_agents)
    assert all(a.removed for a in leader_agents)
    assert all(a.body.alive for a in nonleader_agents)
    assert by_lineage[0].body.death_cause is None


def test_kill_leader_emits_lineage_summary_event():
    agents = _make_agents({0: [3.0], 1: [3.0, 3.0]})
    model = _FakeModel(agents)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    summaries = [e for e in model.events_emitted if isinstance(e, LineageKilledByIntervention)]
    assert len(summaries) == 1
    s = summaries[0]
    assert s.lineage_id == 1
    assert s.n_killed == 2
    assert s.lineage_role == ROLE_LEADER
    assert s.intervention_tick == DEFAULT_INTERVENTION_TICK
    assert s.effective_tick == DEFAULT_EFFECTIVE_TICK


def test_kill_leader_emits_one_agent_died_per_killed_agent():
    agents = _make_agents({0: [2.0], 1: [2.0, 2.0, 2.0]})
    model = _FakeModel(agents)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    deaths = [e for e in model.events_emitted if isinstance(e, AgentDied)]
    assert len(deaths) == 3
    assert all(d.cause == DeathCause.INTERVENTION for d in deaths)
    assert all(d.tick == DEFAULT_EFFECTIVE_TICK for d in deaths)


def test_kill_leader_credits_pool_residual_with_body_energies():
    agents = _make_agents({0: [4.0], 1: [7.0, 11.0]})
    model = _FakeModel(agents, with_pool=True)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert model.energy_pool is not None
    assert sorted(model.energy_pool.credits) == [7.0, 11.0]


def test_kill_leader_no_pool_does_not_raise():
    agents = _make_agents({0: [4.0], 1: [7.0, 11.0]})
    model = _FakeModel(agents, with_pool=False)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert result.fired is True
    assert result.n_killed == 2


# ---------------------------------------------------------------------------
# Size-matched non-leader selection (KIND_KILL_SMNONLEADER)
# ---------------------------------------------------------------------------


def test_kill_smnonleader_picks_closest_size_to_leader():
    # Leader has 5 agents; non-leaders have 1, 3, 4 -> closest to 5 is 4 (lineage 3).
    agents = _make_agents({0: [1.0] * 5, 1: [1.0], 2: [1.0, 1.0, 1.0], 3: [1.0, 1.0, 1.0, 1.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    assert result.fired is True
    assert result.lineage_id == 3
    assert result.lineage_role == ROLE_SMNONLEADER
    assert result.n_killed == 4


def test_kill_smnonleader_tie_break_lowest_lineage_id():
    # Leader = lineage 0 with 4 agents. Non-leaders 1, 2, 3 each have 2 agents.
    # All equally distant from 4; tie-break picks lineage 1.
    agents = _make_agents({0: [1.0] * 4, 1: [1.0, 1.0], 2: [1.0, 1.0], 3: [1.0, 1.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    assert result.lineage_id == 1
    assert result.n_killed == 2


def test_kill_smnonleader_does_not_kill_the_leader():
    agents = _make_agents({0: [1.0] * 4, 1: [1.0, 1.0]})
    model = _FakeModel(agents)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    leader_agents = [a for a in agents if a.body.lineage_id == 0]
    placebo_agents = [a for a in agents if a.body.lineage_id == 1]
    assert all(a.body.alive for a in leader_agents)
    assert all(not a.body.alive for a in placebo_agents)


def test_kill_smnonleader_control_unavailable_when_no_nonleader_alive():
    agents = _make_agents({0: [1.0, 1.0, 1.0]})
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    assert result.fired is False
    assert result.control_unavailable is True
    assert result.lineage_id is None
    assert result.lineage_role == ROLE_NONE
    assert result.n_killed == 0
    # No events emitted — including no LineageKilledByIntervention.
    assert all(not isinstance(e, LineageKilledByIntervention) for e in model.events_emitted)
    assert all(not isinstance(e, AgentDied) for e in model.events_emitted)


def test_kill_smnonleader_emits_summary_with_smnonleader_role():
    agents = _make_agents({0: [1.0, 1.0], 1: [1.0]})
    model = _FakeModel(agents)
    apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    summaries = [e for e in model.events_emitted if isinstance(e, LineageKilledByIntervention)]
    assert len(summaries) == 1
    assert summaries[0].lineage_role == ROLE_SMNONLEADER
    assert summaries[0].lineage_id == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_living_agents_at_firing_returns_no_op_for_kill_leader():
    """If everyone is already dead, kill-leader returns fired=False."""
    agents = _make_agents({0: [1.0]})
    agents[0].body.alive = False  # mark already-dead
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert result.fired is False
    assert result.lineage_id is None
    assert result.control_unavailable is False


def test_no_living_agents_at_firing_marks_control_unavailable_for_smnonleader():
    agents = _make_agents({0: [1.0]})
    agents[0].body.alive = False
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_SMNONLEADER))

    assert result.fired is False
    assert result.control_unavailable is True


def test_kill_leader_skips_already_dead_agents_in_target_lineage():
    """If some leader-lineage agents are already dead pre-firing, they are
    skipped (not double-killed). n_killed reflects only freshly-killed agents.
    """
    agents = _make_agents({0: [1.0], 1: [1.0, 1.0, 1.0]})
    agents[1].body.alive = False  # one of lineage-1 is already dead
    model = _FakeModel(agents)
    result = apply_intervention(model, InterventionConfig(kind=KIND_KILL_LEADER))

    assert result.fired is True
    assert result.lineage_id == 1
    # Buckets only contain alive agents, so the dead lineage-1 agent never
    # entered the bucket and isn't counted as alive at firing. n_killed
    # equals the number of alive lineage-1 agents pre-firing (2).
    assert result.n_killed == 2
