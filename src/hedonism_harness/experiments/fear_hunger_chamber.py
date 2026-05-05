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
    ChildFundingMode,
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

    def __post_init__(self) -> None:
        """Validate the pre-food contract.

        Three invariants pinned (v0.8 hygiene-2 follow-up):

          1. Both ``pre_food_x_min`` and ``pre_food_x_max`` are set
             together, or both are ``None``. A half-set pair is a typo
             that would silently disable the band.
          2. ``pre_food_x_min <= pre_food_x_max``. Inverted ranges
             paint zero columns silently.
          3. The pre-food band must not overlap any of the safe,
             hazard, or terminal-food bands. Overlapping columns get
             stamped twice with conflicting ``CellKind`` values; the
             last write wins, which is order-of-statement in
             ``paint_chamber`` — a fragile and silent failure mode.

        Validation only fires when the pre-food fields are set (the
        v0.8 ``food_ladder`` is the only stock layout that uses them).
        Other layout invariants (band ordering, non-overlap among
        safe/hazard/food, in-bounds-ness) are deliberately out of
        scope for this slice — broader layout validation is its own
        follow-up.
        """
        # Invariant 1: both-or-neither.
        min_set = self.pre_food_x_min is not None
        max_set = self.pre_food_x_max is not None
        if min_set != max_set:
            msg = (
                "ChamberLayout.pre_food_x_min and pre_food_x_max must be "
                f"set together (or both None); got min={self.pre_food_x_min!r} "
                f"max={self.pre_food_x_max!r}"
            )
            raise ValueError(msg)
        if not min_set:
            return  # No pre-food band; remaining invariants are vacuous.

        # Type narrowing for the checks below — both are non-None here.
        pf_min = self.pre_food_x_min
        pf_max = self.pre_food_x_max
        assert pf_min is not None
        assert pf_max is not None

        # Invariant 2: ordering.
        if pf_min > pf_max:
            msg = (
                f"ChamberLayout.pre_food_x_min ({pf_min}) must be "
                f"<= pre_food_x_max ({pf_max}); inverted ranges paint zero columns"
            )
            raise ValueError(msg)

        # Invariant 3: no overlap with safe / hazard / terminal-food bands.
        bands = (
            ("safe", self.safe_x_min, self.safe_x_max),
            ("hazard", self.hazard_x_min, self.hazard_x_max),
            ("food", self.food_x_min, self.food_x_max),
        )
        for name, lo, hi in bands:
            # Inclusive-range overlap: max(starts) <= min(ends).
            if max(pf_min, lo) <= min(pf_max, hi):
                msg = (
                    f"ChamberLayout.pre_food band [{pf_min}, {pf_max}] overlaps "
                    f"{name} band [{lo}, {hi}]; paint_chamber would stamp these "
                    "columns with conflicting CellKind values"
                )
                raise ValueError(msg)


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
    """Compact summary of a chamber run — used to build experiment reports.

    v0.19 adds energy-pool telemetry. All pool fields default to ``None``
    or ``0.0`` when no ambient pool was configured (the v0.7..v0.18
    default), so existing call sites continue to work without changes.
    Per-flow counters are read from the model's ``EnergyPool`` after the
    run loop terminates; the model state outlives the loop.
    """

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
    pool_initial: float | None = None
    pool_min: float | None = None
    pool_max: float | None = None
    pool_end: float | None = None
    pool_out_respawn: float = 0.0
    pool_out_child_startup: float = 0.0
    pool_in_death_residual: float = 0.0
    pool_in_ambient_influx: float = 0.0
    pool_blocked_count_respawn: int = 0
    pool_blocked_count_child_startup: int = 0
    # v0.20 conservation-ledger telemetry. Defaults preserve the
    # v0.7..v0.19 ChamberRunResult shape: ``reproduction_heat_loss`` is
    # populated under POOL_FULL (= energy_cost x successful births;
    # captures the v0.19 heat-loss-per-birth ledger);
    # ``parent_energy_transferred_to_child`` is populated under
    # PARENT_TRANSFER_POOL_GAP (= energy_cost x successful births);
    # ``births_blocked_by_parent_energy`` counts the new transfer-mode-
    # only failure path (parent's energy dropped below energy_cost
    # between queue and process time).
    reproduction_heat_loss: float = 0.0
    parent_energy_transferred_to_child: float = 0.0
    births_blocked_by_parent_energy: int = 0
    notes: dict[str, object] = field(default_factory=dict)


def default_policy_factory() -> Policy:
    return HedonismPolicy(exploration_noise=0.05)


def run_chamber(  # noqa: PLR0912, PLR0915 — single chamber-driver wiring; extraction would obscure the lifecycle.
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
    use_memory: bool = False,
    memory_type: str = "cell_exact",
    food_respawn_cooldown: int | None = None,
    energy_pool_initial: float | None = None,
    ambient_influx_rate: float | None = None,
    child_funding_mode: ChildFundingMode | None = None,
    hazard_damage: float | None = None,
    setup_observer: Callable[[HHModel], None] | None = None,
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

    ``use_memory``: when ``True``, every founder is created with a fresh
    memory of the type chosen by ``memory_type`` (the v0.9 memory-arm seam,
    extended in v0.11 to select representation). Children of memory-enabled
    parents also receive fresh memory per SPEC §13.4. When ``False`` (default),
    founders have ``memory=None`` and the memory directional signals score as
    zeros in ``core/valence``.

    ``memory_type``: only consulted when ``use_memory=True``. ``"cell_exact"``
    (default — keeps v0.9/v0.10 callers bit-identical) uses ``ValenceMemory``;
    ``"directional"`` uses the v0.11 ``DirectionalMemory`` (4-vector
    chemotaxis-style tendencies, no spatial map).

    ``hazard_damage``: v0.22 per-tile hazard damage override. ``None``
    (default) preserves v0.7..v0.21 bit-identity — ``build_chamber_layout``
    runs at its default (``8.0``), the value v0.18..v0.21 sweeps inherited.
    A finite value threads into ``WorldConfig.hazard_damage_default``.
    Used by ``V0_22_ARMS`` to test whether hazard-injury death-residual
    recycling is load-bearing for the v0.21 food_ladder productivity
    plateau under transfer mode at influx=1.0/tick.

    ``setup_observer``: optional callable invoked with the model **after**
    ``paint_chamber`` and aggregator ``connect()``, **before** the first
    ``model.step()``. The v0.8 eligibility-telemetry seam uses this hook
    to install per-event signal subscribers eagerly so events emitted
    during tick 0 are not missed. ``None`` keeps the existing behavior.

    ``tick_observer``: optional callable invoked with the model after each
    ``model.step()`` (the v0.8 eligibility-telemetry seam). Runs even on
    the final tick. ``None`` keeps the existing behavior.
    """
    layout = layout or ChamberLayout()
    # v0.22: thread per-tile hazard damage into build_chamber_layout when set.
    # ``None`` (default) keeps the build_chamber_layout default (8.0) that
    # v0.7..v0.21 inherited; preserves bit-identity for every prior arm.
    if hazard_damage is not None:
        world_cfg = build_chamber_layout(layout, hazard_damage=hazard_damage).model_copy(
            update={"seed": seed}
        )
    else:
        world_cfg = build_chamber_layout(layout).model_copy(update={"seed": seed})
    if food_respawn_cooldown is not None:
        # v0.18: thread cooldown into the frozen WorldConfig. Default
        # None preserves v0.7..v0.17 bit-identity (no respawn).
        world_cfg = world_cfg.model_copy(update={"food_respawn_cooldown": food_respawn_cooldown})
    if energy_pool_initial is not None:
        # v0.19: thread initial pool size into the frozen WorldConfig.
        # Default None preserves v0.7..v0.18 bit-identity (no pool path).
        world_cfg = world_cfg.model_copy(update={"energy_pool_initial": energy_pool_initial})
    if ambient_influx_rate is not None:
        # v0.19: thread per-tick influx rate. The WorldConfig validator
        # rejects influx > 0 without a pool — preserves the conservation
        # framing.
        world_cfg = world_cfg.model_copy(update={"ambient_influx_rate": ambient_influx_rate})
    body_cfg = BodyConfig()
    action_cfg = ActionConfig()
    repro_cfg = reproduction_config if reproduction_config is not None else ReproductionConfig()
    if child_funding_mode is not None:
        # v0.20: thread the funding mode into the (frozen) ReproductionConfig.
        # ``None`` (default) preserves whatever mode the caller's
        # ``reproduction_config`` already carries — typically POOL_FULL,
        # the v0.7..v0.19 default. Reconstruct (rather than ``model_copy``)
        # so the cross-field validator (offspring_start_energy >=
        # energy_cost under TRANSFER) re-fires; ``model_copy`` would skip
        # it. Pre-existing v0.7..v0.19 callers passing the bare default
        # ``ReproductionConfig`` with ``child_funding_mode=None`` are
        # unaffected (the early return preserves the existing
        # reference).
        repro_cfg = ReproductionConfig(
            **{**repro_cfg.model_dump(), "child_funding_mode": child_funding_mode}
        )
    trait_cfg = trait_config if trait_config is not None else TraitConfig()

    # Founders spaced along the chamber's spawn column.
    spawn_x = layout.resolved_spawn_x
    spawn_ys = spread_y(n_founders, layout.height)
    founders = [
        FounderSpec(
            x=spawn_x,
            y=y,
            policy_factory=policy_factory,
            traits_override=traits_override,
            use_memory=use_memory,
            memory_type=memory_type,
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

    # External setup hook fires AFTER aggregator connects but BEFORE the
    # first step so subscribers see every tick-0 event.
    if setup_observer is not None:
        setup_observer(model)

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
    # v0.19: snapshot pool telemetry off the live model after the run loop.
    # All fields stay None / 0 when no pool was configured.
    pool = model.energy_pool
    pool_kwargs: dict[str, object] = {}
    if pool is not None:
        pool_kwargs = {
            "pool_initial": float(world_cfg.energy_pool_initial)
            if world_cfg.energy_pool_initial is not None
            else None,
            "pool_min": float(pool.min_observed),
            "pool_max": float(pool.max_observed),
            "pool_end": float(pool.current),
            "pool_out_respawn": float(pool.out_respawn),
            "pool_out_child_startup": float(pool.out_child_startup),
            "pool_in_death_residual": float(pool.in_death_residual),
            "pool_in_ambient_influx": float(pool.in_ambient_influx),
            "pool_blocked_count_respawn": int(pool.blocked_count_respawn),
            "pool_blocked_count_child_startup": int(pool.blocked_count_child_startup),
        }
    # v0.20: snapshot the conservation-ledger accumulators off the model.
    # Always populated regardless of mode — under POOL_FULL only
    # ``reproduction_heat_loss`` increments; under TRANSFER only
    # ``parent_energy_transferred_to_child``. ``births_blocked_by_parent_energy``
    # is always 0 under POOL_FULL (the gate fires only under TRANSFER mode).
    v0_20_kwargs: dict[str, object] = {
        "reproduction_heat_loss": float(model.reproduction_heat_loss),
        "parent_energy_transferred_to_child": float(model.parent_energy_transferred_to_child),
        "births_blocked_by_parent_energy": int(model.births_blocked_by_parent_energy),
    }
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
        **pool_kwargs,  # type: ignore[arg-type]
        **v0_20_kwargs,  # type: ignore[arg-type]
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


def spread_y(n: int, height: int) -> list[int]:
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
        msg = f"spread_y produced duplicate y-coordinates for n={n}, height={height}: {spread}"
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
