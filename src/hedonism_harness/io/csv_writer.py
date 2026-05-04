"""CSV writers for episode metrics, agent lifetimes, and lineage tree (SPEC §17).

Three files end up in ``runs/{run_id}/``:

    episode_metrics.csv  — one row, the run-level summary (SPEC §17.1).
    agent_lifetimes.csv  — one row per agent (SPEC §17.2).
    lineages.csv         — one row per lineage_id, with founder + extinction info.

Per SPEC §27.11, ``io/`` may import ``metrics/`` and ``core/events``; it does
not touch Mesa or policies.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from hedonism_harness.core.body import DeathCause

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from hedonism_harness.core.traits import Traits
    from hedonism_harness.metrics.aggregators import EpisodeTally, LifetimeRecord


# ---------------------------------------------------------------------------
# episode_metrics.csv
# ---------------------------------------------------------------------------

EPISODE_METRICS_COLUMNS: tuple[str, ...] = (
    "run_id",
    "seed",
    "ticks_completed",
    "population_start",
    "population_end",
    "births",
    "deaths",
    "starvation_deaths",
    "injury_deaths",
    "food_events",
    "hazard_entries",
    "hazard_damage_total",
    "reproduction_requests",
    "moves",
    "stays",
)


def write_episode_metrics(
    path: Path,
    *,
    run_id: str,
    seed: int,
    ticks_completed: int,
    population_start: int,
    population_end: int,
    tally: EpisodeTally,
) -> None:
    row = {
        "run_id": run_id,
        "seed": seed,
        "ticks_completed": ticks_completed,
        "population_start": population_start,
        "population_end": population_end,
        "births": tally.births,
        "deaths": tally.deaths,
        "starvation_deaths": tally.starvation_deaths,
        "injury_deaths": tally.injury_deaths,
        "food_events": tally.food_events,
        "hazard_entries": tally.hazard_entries,
        "hazard_damage_total": round(tally.hazard_damage_total, 6),
        "reproduction_requests": tally.reproduction_requests,
        "moves": tally.moves,
        "stays": tally.stays,
    }
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EPISODE_METRICS_COLUMNS)
        writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# agent_lifetimes.csv
# ---------------------------------------------------------------------------

AGENT_LIFETIME_COLUMNS: tuple[str, ...] = (
    "agent_id",
    "lineage_id",
    "parent_id",
    "birth_tick",
    "death_tick",
    "death_cause",
    "offspring_count",
    "food_events",
    "hazard_entries",
    "hazard_damage_total",
    "moves",
    "stays",
    "unique_cells_visited",
    "traits_json",
)


def _death_cause_str(cause: DeathCause | None) -> str:
    return cause.name if cause is not None else ""


def _traits_json(traits: Traits | None) -> str:
    if traits is None:
        return ""
    return json.dumps(asdict(traits), sort_keys=True)


def write_agent_lifetimes(
    path: Path,
    records: Iterable[LifetimeRecord],
    *,
    traits_by_agent: dict[int, Traits] | None = None,
) -> None:
    """Write one row per agent.

    ``traits_by_agent`` is supplied by the experiment driver (which has the
    living + dead bodies on hand); the metrics layer doesn't track traits
    because traits are body state, not events.
    """
    traits_by_agent = traits_by_agent or {}
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AGENT_LIFETIME_COLUMNS)
        writer.writeheader()
        for rec in sorted(records, key=lambda r: r.agent_id):
            writer.writerow(
                {
                    "agent_id": rec.agent_id,
                    "lineage_id": rec.lineage_id if rec.lineage_id is not None else "",
                    "parent_id": rec.parent_id if rec.parent_id is not None else "",
                    "birth_tick": rec.birth_tick if rec.birth_tick is not None else "",
                    "death_tick": rec.death_tick if rec.death_tick is not None else "",
                    "death_cause": _death_cause_str(rec.death_cause),
                    "offspring_count": rec.offspring_count,
                    "food_events": rec.food_events,
                    "hazard_entries": rec.hazard_entries,
                    "hazard_damage_total": round(rec.hazard_damage_total, 6),
                    "moves": rec.moves,
                    "stays": rec.stays,
                    "unique_cells_visited": len(rec.unique_cells_visited),
                    "traits_json": _traits_json(traits_by_agent.get(rec.agent_id)),
                }
            )


# ---------------------------------------------------------------------------
# lineages.csv
# ---------------------------------------------------------------------------

LINEAGE_COLUMNS: tuple[str, ...] = (
    "lineage_id",
    "founder_id",
    "members",
    "births",
    "deaths",
    "extinct",
    "max_offspring_chain",
)


def derive_lineages(records: Iterable[LifetimeRecord]) -> list[dict[str, object]]:
    """Roll up per-agent records into per-lineage summaries.

    A lineage is "extinct" when every record with that ``lineage_id`` has a
    non-null ``death_tick``. ``max_offspring_chain`` is a placeholder for the
    deepest parent->child path; v0.1 reports the maximum offspring count
    observed in the lineage (a cheap proxy until Phylotrackpy lands).
    """
    by_lineage: dict[int, list[LifetimeRecord]] = {}
    for rec in records:
        if rec.lineage_id is None:
            continue
        by_lineage.setdefault(rec.lineage_id, []).append(rec)

    rows: list[dict[str, object]] = []
    for lineage_id, members in sorted(by_lineage.items()):
        founder = next((m for m in members if m.parent_id is None), None)
        founder_id = founder.agent_id if founder is not None else members[0].agent_id
        births = sum(1 for m in members if m.birth_tick is not None)
        deaths = sum(1 for m in members if m.death_tick is not None)
        extinct = all(m.death_tick is not None for m in members)
        max_offspring = max((m.offspring_count for m in members), default=0)
        rows.append(
            {
                "lineage_id": lineage_id,
                "founder_id": founder_id,
                "members": len(members),
                "births": births,
                "deaths": deaths,
                "extinct": int(extinct),
                "max_offspring_chain": max_offspring,
            }
        )
    return rows


def write_lineages(path: Path, records: Iterable[LifetimeRecord]) -> None:
    rows = derive_lineages(records)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LINEAGE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
