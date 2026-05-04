"""Aggregator tests: episode tally + per-agent lifetime records."""

from __future__ import annotations

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.events import (
    AgentBorn,
    AgentDied,
    AgentMoved,
    AteFood,
    HazardDamageApplied,
    HazardEntered,
    ReproductionRequested,
    emit,
)
from hedonism_harness.metrics.aggregators import (
    EpisodeAggregator,
    LifetimeAggregator,
)


def test_episode_aggregator_counts_events() -> None:
    agg = EpisodeAggregator()
    agg.connect()
    try:
        emit(None, AgentBorn(agent_id=2, parent_id=1, lineage_id=0, x=0, y=0, tick=3))
        emit(None, AgentBorn(agent_id=3, parent_id=1, lineage_id=0, x=0, y=1, tick=4))
        emit(None, AgentDied(agent_id=2, cause=DeathCause.STARVATION, tick=10))
        emit(None, AgentDied(agent_id=3, cause=DeathCause.INJURY, tick=11))
        emit(None, AteFood(agent_id=1, x=1, y=1, food_gained=10.0))
        emit(None, HazardEntered(agent_id=1, x=2, y=2))
        emit(None, HazardDamageApplied(agent_id=1, x=2, y=2, damage=4.0))
        emit(None, HazardDamageApplied(agent_id=1, x=2, y=2, damage=2.5))
        emit(None, ReproductionRequested(agent_id=1, x=0, y=0))
        emit(None, AgentMoved(agent_id=1, from_x=0, from_y=0, to_x=1, to_y=0))
    finally:
        agg.disconnect()

    t = agg.tally
    assert t.births == 2
    assert t.deaths == 2
    assert t.starvation_deaths == 1
    assert t.injury_deaths == 1
    assert t.food_events == 1
    assert t.hazard_entries == 1
    assert t.hazard_damage_total == 6.5
    assert t.reproduction_requests == 1
    assert t.moves == 1
    assert t.stays == 0


def test_lifetime_aggregator_records_per_agent() -> None:
    agg = LifetimeAggregator()
    agg.connect()
    try:
        emit(None, AgentBorn(agent_id=2, parent_id=1, lineage_id=7, x=3, y=3, tick=5))
        emit(None, AteFood(agent_id=2, x=4, y=3, food_gained=12.0))
        emit(None, HazardEntered(agent_id=2, x=5, y=3))
        emit(None, HazardDamageApplied(agent_id=2, x=5, y=3, damage=2.0))
        emit(None, AgentMoved(agent_id=2, from_x=5, from_y=3, to_x=5, to_y=4))
        emit(None, AgentDied(agent_id=2, cause=DeathCause.INJURY, tick=20))
    finally:
        agg.disconnect()

    rec = agg.records[2]
    assert rec.parent_id == 1
    assert rec.lineage_id == 7
    assert rec.birth_tick == 5
    assert rec.death_tick == 20
    assert rec.death_cause == DeathCause.INJURY
    assert rec.food_events == 1
    assert rec.hazard_entries == 1
    assert rec.hazard_damage_total == 2.0
    assert rec.moves == 1
    # Cells visited: birth (3,3), eat (4,3), move-to (5,4). HazardEntered is
    # not added because it duplicates the AgentMoved->to cell already counted.
    assert rec.unique_cells_visited == {(3, 3), (4, 3), (5, 4)}

    # Parent's offspring count was incremented on the AgentBorn event.
    parent_rec = agg.records[1]
    assert parent_rec.offspring_count == 1


def test_aggregator_disconnect_is_idempotent() -> None:
    agg = EpisodeAggregator()
    agg.connect()
    agg.connect()  # second connect is a no-op
    agg.disconnect()
    agg.disconnect()  # second disconnect is a no-op
    # Emit after disconnect; tally should not change.
    emit(None, AteFood(agent_id=1, x=0, y=0, food_gained=1.0))
    assert agg.tally.food_events == 0
