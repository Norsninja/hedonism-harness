"""End-to-end IO test: run a small model, write run dir, verify file shapes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from hedonism_harness.core.body import DeathCause
from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.events import (
    AgentBorn,
    AgentDied,
    AteFood,
    emit,
)
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.io.csv_writer import (
    AGENT_LIFETIME_COLUMNS,
    EPISODE_METRICS_COLUMNS,
    LINEAGE_COLUMNS,
    write_agent_lifetimes,
    write_episode_metrics,
    write_lineages,
)
from hedonism_harness.io.jsonl_writer import write_events_jsonl
from hedonism_harness.io.run_writer import (
    RunManifest,
    make_run_dir,
    write_config,
    write_manifest,
)
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.metrics.aggregators import EpisodeAggregator, LifetimeAggregator
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.random_policy import RandomPolicy


def test_run_dir_and_config_json(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "abc-123")
    assert paths.root.is_dir()
    assert paths.root.name == "abc-123"
    write_config(
        paths,
        world_config=WorldConfig(seed=1, width=4, height=4),
        body_config=BodyConfig(),
        action_config=ActionConfig(),
        reproduction_config=ReproductionConfig(),
        trait_config=TraitConfig(),
    )
    payload = json.loads(paths.config_json.read_text())
    assert payload["world"]["seed"] == 1
    assert payload["body"]["max_energy"] == 100.0
    assert "trait" in payload


def test_manifest_round_trip(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "m1")
    manifest = RunManifest(run_id="m1", seed=42, started_at=1000.0)
    write_manifest(paths, manifest)
    out = json.loads(paths.manifest_json.read_text())
    assert out["run_id"] == "m1"
    assert out["seed"] == 42
    assert out["ticks_completed"] is None  # not yet filled


def test_episode_metrics_csv_writes_one_row(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "e1")
    agg = EpisodeAggregator()
    agg.tally.births = 3
    agg.tally.deaths = 1
    agg.tally.starvation_deaths = 1
    agg.tally.food_events = 7
    agg.tally.hazard_damage_total = 12.5
    agg.tally.moves = 50
    write_episode_metrics(
        paths.episode_metrics_csv,
        run_id="e1",
        seed=42,
        ticks_completed=100,
        population_start=5,
        population_end=7,
        tally=agg.tally,
    )
    rows = list(csv.DictReader(paths.episode_metrics_csv.open()))
    assert len(rows) == 1
    row = rows[0]
    assert set(row.keys()) == set(EPISODE_METRICS_COLUMNS)
    assert row["births"] == "3"
    assert row["hazard_damage_total"] == "12.5"


def test_agent_lifetimes_csv_round_trip(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "a1")

    agg = LifetimeAggregator()
    agg.connect()
    try:
        # Founder (no AgentBorn event).
        emit(None, AteFood(agent_id=1, x=0, y=0, food_gained=10.0))
        emit(None, AgentDied(agent_id=1, cause=DeathCause.STARVATION, tick=50))
        # Child.
        emit(None, AgentBorn(agent_id=2, parent_id=1, lineage_id=0, x=1, y=0, tick=20))
        emit(None, AgentDied(agent_id=2, cause=DeathCause.INJURY, tick=60))
    finally:
        agg.disconnect()

    write_agent_lifetimes(paths.agent_lifetimes_csv, agg.records.values())
    rows = list(csv.DictReader(paths.agent_lifetimes_csv.open()))
    assert {r["agent_id"] for r in rows} == {"1", "2"}
    assert set(rows[0].keys()) == set(AGENT_LIFETIME_COLUMNS)
    by_id = {r["agent_id"]: r for r in rows}
    assert by_id["1"]["death_cause"] == "STARVATION"
    assert by_id["1"]["food_events"] == "1"
    assert by_id["1"]["offspring_count"] == "1"
    assert by_id["2"]["birth_tick"] == "20"
    assert by_id["2"]["parent_id"] == "1"
    assert by_id["2"]["lineage_id"] == "0"


def test_lineages_csv_extinct_when_all_dead(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "l1")
    agg = LifetimeAggregator()
    agg.connect()
    try:
        # Founder of lineage 0.
        emit(None, AgentDied(agent_id=1, cause=DeathCause.STARVATION, tick=10))
        agg.records[1].lineage_id = 0  # founder lineage seeded externally.
        # Child + child's child both dead.
        emit(None, AgentBorn(agent_id=2, parent_id=1, lineage_id=0, x=0, y=0, tick=5))
        emit(None, AgentDied(agent_id=2, cause=DeathCause.INJURY, tick=15))
    finally:
        agg.disconnect()

    write_lineages(paths.lineages_csv, agg.records.values())
    rows = list(csv.DictReader(paths.lineages_csv.open()))
    assert len(rows) == 1
    row = rows[0]
    assert set(row.keys()) == set(LINEAGE_COLUMNS)
    assert row["lineage_id"] == "0"
    assert row["extinct"] == "1"


def test_events_jsonl_one_line_per_event(tmp_path: Path) -> None:
    paths = make_run_dir(tmp_path / "runs", "j1")
    events = [
        AgentBorn(agent_id=2, parent_id=1, lineage_id=0, x=0, y=0, tick=5),
        AteFood(agent_id=1, x=1, y=1, food_gained=10.0),
        AgentDied(agent_id=2, cause=DeathCause.STARVATION, tick=20),
    ]
    write_events_jsonl(paths.events_jsonl, events)
    lines = paths.events_jsonl.read_text().strip().split("\n")
    assert len(lines) == 3
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["event"] == "AgentBorn"
    assert payloads[2]["event"] == "AgentDied"
    assert payloads[2]["cause"] == "STARVATION"


def test_full_run_writes_all_files(tmp_path: Path) -> None:
    """Wire metrics + io to a real model run and confirm every file exists."""
    cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        cfg,
        founders=[FounderSpec(x=2, y=2, policy_factory=RandomPolicy)],
    )

    episode = EpisodeAggregator()
    lifetime = LifetimeAggregator()
    episode.connect()
    lifetime.connect()
    try:
        for _ in range(20):
            model.step()
    finally:
        episode.disconnect()
        lifetime.disconnect()

    paths = make_run_dir(tmp_path / "runs", "full")
    write_config(
        paths,
        world_config=cfg,
        body_config=model.body_config,
        action_config=model.action_config,
        reproduction_config=model.reproduction_config,
        trait_config=model.trait_config,
    )
    write_manifest(
        paths,
        RunManifest(
            run_id="full",
            seed=cfg.seed,
            started_at=0.0,
            ended_at=1.0,
            ticks_completed=model.tick_count,
            population_start=1,
            population_end=sum(1 for a in model.agents if isinstance(a, HHAgent)),
        ),
    )
    write_episode_metrics(
        paths.episode_metrics_csv,
        run_id="full",
        seed=cfg.seed,
        ticks_completed=model.tick_count,
        population_start=1,
        population_end=sum(1 for a in model.agents if isinstance(a, HHAgent)),
        tally=episode.tally,
    )
    traits_by_agent = {a.body.id: a.body.traits for a in model.agents if isinstance(a, HHAgent)}
    write_agent_lifetimes(
        paths.agent_lifetimes_csv, lifetime.records.values(), traits_by_agent=traits_by_agent
    )
    write_lineages(paths.lineages_csv, lifetime.records.values())
    write_events_jsonl(paths.events_jsonl, model.event_log)

    for f in (
        paths.config_json,
        paths.manifest_json,
        paths.episode_metrics_csv,
        paths.agent_lifetimes_csv,
        paths.lineages_csv,
        paths.events_jsonl,
    ):
        assert f.is_file(), f"{f} missing"
        assert f.stat().st_size > 0, f"{f} empty"
