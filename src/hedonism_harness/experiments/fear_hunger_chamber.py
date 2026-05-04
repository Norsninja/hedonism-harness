"""Fear-Hunger Conflict Chamber (SPEC §16) — v0.1 canonical experiment.

The chamber is a horizontal sandwich:

    | SAFE zone | HAZARD band | EMPTY corridor | FOOD zone |

Founders spawn in the safe zone. Energy decays every tick. To eat, an agent
must cross the hazard band — taking damage on residency — and reach the food
zone on the other side. The experiment observes which trait profiles cross,
when hunger overrides fear, and which lineages reproduce.

This module owns the layout function and a single-run driver. The driver
wires ``HHModel`` to the metrics aggregators and IO writers and returns a
summary dict. The driver does not own the random seed — caller passes it
explicitly so batch runs can sweep.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from hedonism_harness.core.config import (
    ActionConfig,
    BodyConfig,
    ReproductionConfig,
    WorldConfig,
)
from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.core.world import CellKind
from hedonism_harness.io.csv_writer import (
    write_agent_lifetimes,
    write_episode_metrics,
    write_lineages,
)
from hedonism_harness.io.jsonl_writer import write_events_jsonl
from hedonism_harness.io.run_writer import (
    RunManifest,
    make_run_dir,
    now_unix,
    write_config,
    write_manifest,
)
from hedonism_harness.mesa_agents import HHAgent
from hedonism_harness.metrics.aggregators import EpisodeAggregator, LifetimeAggregator
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

if TYPE_CHECKING:
    from collections.abc import Callable

    from hedonism_harness.core.traits import Traits
    from hedonism_harness.policies.base import Policy


# ---------------------------------------------------------------------------
# Chamber geometry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChamberLayout:
    """Column ranges for each zone of the chamber. Inclusive endpoints.

    ``world.width`` is computed from ``food_x_max + 1`` so the layout fits
    exactly. Each row is identical — the hazard band is a full vertical wall.

    ``spawn_x`` (optional): the column founders are placed in. ``None`` keeps
    the v0.1/v0.2 default of ``safe_x_min + 1``. Set explicitly to test
    spawn-position variants without changing the chamber proportions
    (see v0.3 ``near_hazard_layout``).

    ``pre_food_x_min`` / ``pre_food_x_max`` (optional, v0.8): an additional
    FOOD band stamped *before* the hazard zone. Used by the v0.8
    ``food_ladder_layout`` so founders can refill in the corridor before
    facing the hazard wall. Both must be set together (or both ``None``).
    """

    safe_x_min: int = 0
    safe_x_max: int = 5
    hazard_x_min: int = 8
    hazard_x_max: int = 11
    food_x_min: int = 14
    food_x_max: int = 19
    height: int = 6
    spawn_x: int | None = None
    pre_food_x_min: int | None = None
    pre_food_x_max: int | None = None

    @property
    def width(self) -> int:
        return self.food_x_max + 1

    @property
    def resolved_spawn_x(self) -> int:
        """Effective spawn column — falls back to ``safe_x_min + 1``."""
        return self.safe_x_min + 1 if self.spawn_x is None else self.spawn_x

    @property
    def has_pre_food(self) -> bool:
        return self.pre_food_x_min is not None and self.pre_food_x_max is not None


def build_chamber_layout(layout: ChamberLayout, hazard_damage: float = 8.0) -> WorldConfig:
    """Return a ``WorldConfig`` sized for ``layout``. Terrain is painted by
    ``paint_chamber`` after the model is constructed (so the painted state
    flows through the shared PropertyLayer storage).
    """
    return WorldConfig(
        seed=0,  # caller overrides
        width=layout.width,
        height=layout.height,
        food_density=0.0,
        hazard_density=0.0,
        hazard_damage_default=hazard_damage,
        food_value_default=20.0,
        safe_value_default=1.0,
    )


def paint_chamber(model: HHModel, layout: ChamberLayout) -> None:
    """Stamp SAFE / HAZARD / FOOD columns onto ``model.world`` in place.

    Writes go through ``model.world`` (which shares storage with the four
    PropertyLayers built in ``HHModel.__init__``) so the chamber terrain is
    visible to Mesa-side consumers as well.

    When ``layout.has_pre_food`` is True, an additional FOOD band is
    stamped at the pre-food columns (used by the v0.8 food_ladder layout).
    """
    cfg = model.world_config
    for y in range(cfg.height):
        for x in range(layout.safe_x_min, layout.safe_x_max + 1):
            model.world.kind_layer[x, y] = CellKind.SAFE
            model.world.safe_value[x, y] = cfg.safe_value_default
        if layout.has_pre_food:
            assert layout.pre_food_x_min is not None
            assert layout.pre_food_x_max is not None
            for x in range(layout.pre_food_x_min, layout.pre_food_x_max + 1):
                model.world.kind_layer[x, y] = CellKind.FOOD
                model.world.food_value[x, y] = cfg.food_value_default
        for x in range(layout.hazard_x_min, layout.hazard_x_max + 1):
            model.world.kind_layer[x, y] = CellKind.HAZARD
            model.world.hazard_damage[x, y] = cfg.hazard_damage_default
        for x in range(layout.food_x_min, layout.food_x_max + 1):
            model.world.kind_layer[x, y] = CellKind.FOOD
            model.world.food_value[x, y] = cfg.food_value_default


# ---------------------------------------------------------------------------
# Run driver
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChamberRunResult:
    """Compact summary of a chamber run — used to build experiment reports."""

    run_id: str
    seed: int
    ticks_completed: int
    population_start: int
    population_end: int
    survivors: int
    starvation_deaths: int
    injury_deaths: int
    food_events: int
    hazard_entries: int
    hazard_damage_total: float
    births: int
    reproduction_requests: int
    moves: int
    stays: int
    output_dir: Path
    notes: dict[str, object] = field(default_factory=dict)


def default_policy_factory() -> Policy:
    return HedonismPolicy(exploration_noise=0.05)


def run_chamber(
    *,
    seed: int,
    runs_root: Path,
    run_id: str,
    n_founders: int = 5,
    n_ticks: int = 200,
    layout: ChamberLayout | None = None,
    policy_factory: Callable[[], Policy] = default_policy_factory,
    write_outputs: bool = True,
    traits_override: Traits | None = None,
    condition: str | None = None,
    trait_config: TraitConfig | None = None,
    reproduction_config: ReproductionConfig | None = None,
    tick_observer: Callable[[HHModel], None] | None = None,
) -> ChamberRunResult:
    """Run one Fear-Hunger Chamber episode and (optionally) persist its outputs.

    ``traits_override``: when provided, every founder shares this exact
    ``Traits`` instance (the v0.2 positive-control seam). When ``None`` the
    v0.1 behavior holds: each founder samples from the configured
    ``TraitConfig``.

    ``trait_config``: when provided, founders sample from this config's
    ranges (the v0.5 default-tuning seam). When ``None`` the SPEC §8.1
    default ``TraitConfig`` is used.

    ``reproduction_config``: when provided, replaces the SPEC §7/§14 default
    ``ReproductionConfig`` (the v0.7 reproduction-emergence seam). When
    ``None`` the SPEC defaults hold.

    ``tick_observer``: optional callable invoked with the model after each
    ``model.step()`` (the v0.8 eligibility-telemetry seam). Runs even on
    the final tick. ``None`` keeps the existing behavior.
    """
    layout = layout or ChamberLayout()
    world_cfg = build_chamber_layout(layout).model_copy(update={"seed": seed})
    body_cfg = BodyConfig()
    action_cfg = ActionConfig()
    repro_cfg = reproduction_config if reproduction_config is not None else ReproductionConfig()
    trait_cfg = trait_config if trait_config is not None else TraitConfig()

    # Founders spaced along the chamber's spawn column.
    spawn_x = layout.resolved_spawn_x
    spawn_ys = _spread_y(n_founders, layout.height)
    founders = [
        FounderSpec(
            x=spawn_x,
            y=y,
            policy_factory=policy_factory,
            traits_override=traits_override,
        )
        for y in spawn_ys
    ]

    model = HHModel(
        world_cfg,
        founders=founders,
        body_config=body_cfg,
        action_config=action_cfg,
        reproduction_config=repro_cfg,
        trait_config=trait_cfg,
    )
    paint_chamber(model, layout)

    # Aggregators scoped to this model so concurrent batch runs don't cross-talk.
    episode = EpisodeAggregator(model=model)
    lifetime = LifetimeAggregator(model=model)
    episode.connect()
    lifetime.connect()

    started_at = now_unix()
    try:
        for _ in range(n_ticks):
            model.step()
            if tick_observer is not None:
                tick_observer(model)
            if not _any_alive(model):
                break
    finally:
        episode.disconnect()
        lifetime.disconnect()

    population_end = sum(1 for a in model.agents if isinstance(a, HHAgent) and a.body.alive)
    summary = ChamberRunResult(
        run_id=run_id,
        seed=seed,
        ticks_completed=model.tick_count,
        population_start=n_founders,
        population_end=population_end,
        survivors=population_end,
        starvation_deaths=episode.tally.starvation_deaths,
        injury_deaths=episode.tally.injury_deaths,
        food_events=episode.tally.food_events,
        hazard_entries=episode.tally.hazard_entries,
        hazard_damage_total=episode.tally.hazard_damage_total,
        births=episode.tally.births,
        reproduction_requests=episode.tally.reproduction_requests,
        moves=episode.tally.moves,
        stays=episode.tally.stays,
        output_dir=runs_root / run_id,
    )

    if write_outputs:
        paths = make_run_dir(runs_root, run_id)
        write_config(
            paths,
            world_config=world_cfg,
            body_config=body_cfg,
            action_config=action_cfg,
            reproduction_config=repro_cfg,
            trait_config=trait_cfg,
        )
        write_manifest(
            paths,
            RunManifest(
                run_id=run_id,
                seed=seed,
                started_at=started_at,
                ended_at=now_unix(),
                ticks_completed=model.tick_count,
                population_start=n_founders,
                population_end=population_end,
                notes={
                    "experiment": "fear_hunger_chamber",
                    **({"condition": condition} if condition else {}),
                },
            ),
        )
        write_episode_metrics(
            paths.episode_metrics_csv,
            run_id=run_id,
            seed=seed,
            ticks_completed=model.tick_count,
            population_start=n_founders,
            population_end=population_end,
            tally=episode.tally,
        )
        traits_by_agent = {a.body.id: a.body.traits for a in model.agents if isinstance(a, HHAgent)}
        write_agent_lifetimes(
            paths.agent_lifetimes_csv,
            lifetime.records.values(),
            traits_by_agent=traits_by_agent,
        )
        write_lineages(paths.lineages_csv, lifetime.records.values())
        write_events_jsonl(paths.events_jsonl, model.event_log)
        _write_summary_md(paths.root, summary)

    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _spread_y(n: int, height: int) -> list[int]:
    """Evenly distribute ``n`` y-coordinates across the chamber height.

    Raises ``ValueError`` when ``n > height`` — the Mesa grid is
    capacity=1 (SPEC §27.4), so two founders at the same cell would
    silently violate placement invariants. Earlier behavior clamped
    overflow indices to ``height - 1``, producing duplicates.

    For ``n <= height`` the algorithm is the historical step-wise
    distribution: ``step = max(1, height // n)``, positions
    ``[min(height - 1, i * step) for i in range(n)]``. This is
    uniqueness-safe under the precondition ``n <= height`` and is
    preserved bit-identically so existing experiment results
    (v0.1..v0.8) remain reproducible.
    """
    if n <= 0:
        return []
    if n > height:
        msg = (
            f"cannot spread {n} founders across height={height}: the Mesa grid "
            "is capacity=1, so founders must occupy distinct cells"
        )
        raise ValueError(msg)
    if n == 1:
        return [height // 2]
    step = max(1, height // n)
    spread = [min(height - 1, i * step) for i in range(n)]
    # Defensive uniqueness check — the precondition above makes this
    # impossible, but assert it explicitly so any future change to the
    # algorithm fails loudly instead of silently colliding founders.
    if len(set(spread)) != len(spread):
        msg = f"_spread_y produced duplicate y-coordinates for n={n}, height={height}: {spread}"
        raise AssertionError(msg)
    return spread


def _any_alive(model: HHModel) -> bool:
    return any(isinstance(a, HHAgent) and a.body.alive for a in model.agents)


def _write_summary_md(run_dir: Path, summary: ChamberRunResult) -> None:
    """One-page markdown of the run's vital statistics — the report artifact."""
    survival_rate = (
        summary.survivors / summary.population_start if summary.population_start else 0.0
    )
    body = f"""# Fear-Hunger Chamber — run `{summary.run_id}`

**Seed:** `{summary.seed}`
**Ticks completed:** {summary.ticks_completed}
**Survivors / founders:** {summary.survivors} / {summary.population_start} ({survival_rate:.0%})

## Population

| Metric | Value |
|---|---:|
| Population (start) | {summary.population_start} |
| Population (end) | {summary.population_end} |
| Births | {summary.births} |
| Starvation deaths | {summary.starvation_deaths} |
| Injury deaths | {summary.injury_deaths} |

## Behavior

| Metric | Value |
|---|---:|
| Food events | {summary.food_events} |
| Hazard entries | {summary.hazard_entries} |
| Hazard damage delivered | {summary.hazard_damage_total:.2f} |
| Reproduction requests | {summary.reproduction_requests} |
| Moves | {summary.moves} |
| Stays | {summary.stays} |

See `episode_metrics.csv`, `agent_lifetimes.csv`, `lineages.csv`,
`events.jsonl` in the same directory for full data.
"""
    (run_dir / "summary.md").write_text(body)
