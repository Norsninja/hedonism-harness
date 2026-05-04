"""Run directory creation and config/manifest persistence (SPEC §17, §26.5).

Every experiment run writes to ``runs/{run_id}/`` with this layout::

    runs/{run_id}/
        config.json         # resolved Pydantic config snapshot
        manifest.json       # versions, seed, started_at, ended_at, counts
        episode_metrics.csv # populated by csv_writer
        agent_lifetimes.csv # populated by csv_writer
        lineages.csv        # populated by csv_writer
        events.jsonl        # populated by jsonl_writer

This module owns the directory and the metadata files; ``csv_writer.py`` and
``jsonl_writer.py`` own their respective formats. Per SPEC §27.11, ``io/`` is
the only layer permitted to touch the filesystem.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hedonism_harness.core.config import (
        ActionConfig,
        BodyConfig,
        ReproductionConfig,
        WorldConfig,
    )
    from hedonism_harness.core.traits import TraitConfig


@dataclass
class RunPaths:
    """The set of files within a single ``runs/{run_id}/`` directory."""

    root: Path
    config_json: Path
    manifest_json: Path
    episode_metrics_csv: Path
    agent_lifetimes_csv: Path
    lineages_csv: Path
    events_jsonl: Path

    @classmethod
    def under(cls, root: Path) -> RunPaths:
        return cls(
            root=root,
            config_json=root / "config.json",
            manifest_json=root / "manifest.json",
            episode_metrics_csv=root / "episode_metrics.csv",
            agent_lifetimes_csv=root / "agent_lifetimes.csv",
            lineages_csv=root / "lineages.csv",
            events_jsonl=root / "events.jsonl",
        )


@dataclass
class RunManifest:
    """JSON-friendly summary of a run. Updated at run-start and run-end."""

    run_id: str
    seed: int
    started_at: float
    ended_at: float | None = None
    ticks_completed: int | None = None
    population_start: int | None = None
    population_end: int | None = None
    notes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "ticks_completed": self.ticks_completed,
            "population_start": self.population_start,
            "population_end": self.population_end,
            "notes": self.notes,
        }


def make_run_dir(runs_root: Path, run_id: str) -> RunPaths:
    """Create ``runs_root/run_id/`` (and parents) and return the file layout.

    Idempotent: creates only what doesn't exist; does not clobber existing files.
    """
    root = runs_root / run_id
    root.mkdir(parents=True, exist_ok=True)
    return RunPaths.under(root)


def write_config(
    paths: RunPaths,
    *,
    world_config: WorldConfig,
    body_config: BodyConfig,
    action_config: ActionConfig,
    reproduction_config: ReproductionConfig,
    trait_config: TraitConfig,
) -> None:
    """Serialize the resolved Pydantic config bundle to ``config.json``."""
    payload = {
        "world": world_config.model_dump(),
        "body": body_config.model_dump(),
        "action": action_config.model_dump(),
        "reproduction": reproduction_config.model_dump(),
        "trait": trait_config.model_dump(),
    }
    paths.config_json.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_manifest(paths: RunPaths, manifest: RunManifest) -> None:
    """Persist a manifest snapshot. Safe to call multiple times during a run."""
    paths.manifest_json.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))


def now_unix() -> float:
    """Wall-clock timestamp helper (kept here so tests can monkey-patch)."""
    return time.time()
