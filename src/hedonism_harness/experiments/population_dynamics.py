"""Pure-function library for events.jsonl -> population time-series.

Used by the v0.24 population-dynamics diagnostic to compute per-run
population trajectories, lifespan distributions, and per-tick
starvation-death counts from existing events.jsonl artifacts.

Founders are seeded at tick 0 with no AgentBorn event; the loader
relies on the caller-supplied ``n_founders`` to seed the initial
population. Subsequent births and deaths are derived from AgentBorn
and AgentDied events. Lifespans for agents alive at run end use
``n_ticks`` as the death-tick endpoint.

See [[docs/experiments/fear_hunger_v0.24.md]] for the pre-registered
hypotheses these aggregates feed.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

# Numeric type variable for ``bucket_by_window`` — preserves the
# input element type (int sums stay int; float sums stay float).
_N = TypeVar("_N", int, float)

# Pre-committed starvation-death bucket boundaries (50-tick windows
# across the 200-tick observation window). Defined here so the
# diagnostic and any downstream tooling agree on bucket semantics.
STARVATION_WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("0-49", 0, 50),
    ("50-99", 50, 100),
    ("100-149", 100, 150),
    ("150-199", 150, 200),
)


@dataclass(frozen=True)
class PopulationTrajectory:
    """Per-run population dynamics derived from a single events.jsonl.

    ``population_at_tick``: length ``n_ticks``; population at END of
    each tick t after processing all events at that tick. Index 0 is
    end-of-tick-0 (= n_founders + births_at_0 - deaths_at_0).

    ``lifespans``: ``(birth_tick, death_tick)`` per agent that ever
    existed. Founders use ``birth_tick=0``; agents alive at run end
    use ``death_tick = n_ticks`` so lifespan = ``death_tick - birth_tick``.

    ``starvation_deaths_per_tick`` / ``injury_deaths_per_tick``:
    length ``n_ticks``; count of STARVATION / INJURY AgentDied
    events at each tick.
    """

    population_at_tick: tuple[int, ...]
    lifespans: tuple[tuple[int, int], ...]
    starvation_deaths_per_tick: tuple[int, ...]
    injury_deaths_per_tick: tuple[int, ...]

    @property
    def peak_population(self) -> int:
        return max(self.population_at_tick) if self.population_at_tick else 0

    @property
    def tick_of_peak(self) -> int:
        if not self.population_at_tick:
            return 0
        return self.population_at_tick.index(self.peak_population)

    def mean_population_window(self, t_start: int, t_end: int) -> float:
        """Mean population over inclusive tick range [t_start, t_end].

        Indices outside ``population_at_tick`` are clipped. Returns
        0.0 if the clipped window is empty.
        """
        n = len(self.population_at_tick)
        if n == 0:
            return 0.0
        lo = max(0, t_start)
        hi = min(n - 1, t_end)
        if lo > hi:
            return 0.0
        window = self.population_at_tick[lo : hi + 1]
        return sum(window) / len(window)


def load_population_trajectory(  # noqa: PLR0912 — single-pass event dispatch is cohesive.
    events_jsonl: Path, n_founders: int, n_ticks: int
) -> PopulationTrajectory:
    """Walk events.jsonl once to build the population trajectory.

    Single forward pass. Founders are inferred structurally: any
    agent_id present in AgentDied without a corresponding AgentBorn
    is a founder that died; the count of founders alive at run end
    is ``n_founders - died_founder_count``. Founders alive at run
    end have lifespan ``n_ticks``.
    """
    if n_ticks < 0:
        msg = f"n_ticks must be non-negative; got {n_ticks}"
        raise ValueError(msg)
    if n_founders < 0:
        msg = f"n_founders must be non-negative; got {n_founders}"
        raise ValueError(msg)

    births_at: dict[int, int] = {}
    starv_at: dict[int, int] = {}
    injury_at: dict[int, int] = {}
    birth_tick: dict[int, int] = {}
    death_tick: dict[int, int] = {}

    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = row.get("type")
            tick = int(row.get("tick", 0))
            event = row.get("event", {})
            if kind == "AgentBorn":
                aid = event.get("agent_id")
                if aid is not None:
                    birth_tick[int(aid)] = tick
                    births_at[tick] = births_at.get(tick, 0) + 1
            elif kind == "AgentDied":
                aid = event.get("agent_id")
                cause = event.get("cause")
                if aid is not None:
                    death_tick[int(aid)] = tick
                    if cause == "STARVATION":
                        starv_at[tick] = starv_at.get(tick, 0) + 1
                    elif cause == "INJURY":
                        injury_at[tick] = injury_at.get(tick, 0) + 1

    # Population trajectory.
    pop_at: list[int] = []
    current = n_founders
    for t in range(n_ticks):
        current += births_at.get(t, 0)
        current -= starv_at.get(t, 0)
        current -= injury_at.get(t, 0)
        pop_at.append(current)

    # Lifespans.
    died_founder_ids = {aid for aid in death_tick if aid not in birth_tick}
    n_died_founders = len(died_founder_ids)
    n_alive_founders = max(0, n_founders - n_died_founders)
    lifespans: list[tuple[int, int]] = []
    for aid, bt in birth_tick.items():
        dt = death_tick.get(aid, n_ticks)
        lifespans.append((bt, dt))
    for fid in died_founder_ids:
        lifespans.append((0, death_tick[fid]))
    for _ in range(n_alive_founders):
        lifespans.append((0, n_ticks))

    starv_list = tuple(starv_at.get(t, 0) for t in range(n_ticks))
    inj_list = tuple(injury_at.get(t, 0) for t in range(n_ticks))

    return PopulationTrajectory(
        population_at_tick=tuple(pop_at),
        lifespans=tuple(lifespans),
        starvation_deaths_per_tick=starv_list,
        injury_deaths_per_tick=inj_list,
    )


@dataclass(frozen=True)
class CellAggregate:
    """Cross-seed aggregation for a single (chamber, hazard, influx) cell.

    All means are arithmetic means across the cell's seeds. Lifespan
    percentiles are computed on the pooled lifespan distribution
    across all agents in all seeds (linear interpolation between
    rank-adjacent samples; same convention as numpy.percentile linear).

    ``starvation_deaths_by_window``: total starvation deaths summed
    across all seeds, bucketed by 50-tick windows per
    ``STARVATION_WINDOWS``.
    """

    n_seeds: int
    mean_peak_population: float
    mean_tick_of_peak: float
    mean_population_t_gt_100: float
    lifespan_p50: float
    lifespan_p90: float
    starvation_deaths_by_window: dict[str, int]

    @property
    def starvation_peak_window(self) -> str:
        """Window label whose total starvation count is largest.

        Ties broken by earliest window.
        """
        if not self.starvation_deaths_by_window:
            return ""
        ordered = [w[0] for w in STARVATION_WINDOWS]
        return max(ordered, key=lambda w: self.starvation_deaths_by_window.get(w, 0))


def _percentile(sorted_data: list[int], p: float) -> float:
    """Linear-interpolation percentile (numpy-compatible default).

    Expects ``sorted_data`` already sorted ascending. Returns 0.0
    on empty input.
    """
    n = len(sorted_data)
    if n == 0:
        return 0.0
    k = (n - 1) * p
    f = int(k)
    c = min(f + 1, n - 1)
    return float(sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f]))


def aggregate_cell(
    trajectories: list[PopulationTrajectory],
    *,
    n_ticks: int,
    late_window_start: int = 100,
) -> CellAggregate:
    """Aggregate a list of per-seed trajectories into a CellAggregate."""
    n = len(trajectories)
    if n == 0:
        return CellAggregate(
            n_seeds=0,
            mean_peak_population=0.0,
            mean_tick_of_peak=0.0,
            mean_population_t_gt_100=0.0,
            lifespan_p50=0.0,
            lifespan_p90=0.0,
            starvation_deaths_by_window={w[0]: 0 for w in STARVATION_WINDOWS},
        )
    peaks = [t.peak_population for t in trajectories]
    tick_peaks = [t.tick_of_peak for t in trajectories]
    late_means = [t.mean_population_window(late_window_start, n_ticks - 1) for t in trajectories]
    all_lifespans = sorted(dt - bt for traj in trajectories for bt, dt in traj.lifespans)
    p50 = _percentile(all_lifespans, 0.5)
    p90 = _percentile(all_lifespans, 0.9)
    buckets: dict[str, int] = {w[0]: 0 for w in STARVATION_WINDOWS}
    for traj in trajectories:
        for t, count in enumerate(traj.starvation_deaths_per_tick):
            for label, lo, hi in STARVATION_WINDOWS:
                if lo <= t < hi:
                    buckets[label] += count
                    break
    return CellAggregate(
        n_seeds=n,
        mean_peak_population=sum(peaks) / n,
        mean_tick_of_peak=sum(tick_peaks) / n,
        mean_population_t_gt_100=sum(late_means) / n,
        lifespan_p50=p50,
        lifespan_p90=p90,
        starvation_deaths_by_window=buckets,
    )


# ---------------------------------------------------------------------------
# v0.28 — event-band trajectory aggregation
# ---------------------------------------------------------------------------
#
# Pure-function additions for the v0.28 food_ladder w=0.75 trajectory
# diagnostic. ``PopulationTrajectory`` (v0.24) exposes population /
# lifespans / per-tick deaths but not per-tick births / food / hazard /
# pool-block events; ``EventBandTrajectory`` covers the gap. v0.24's
# ``PopulationTrajectory`` and ``load_population_trajectory`` are
# byte-identical before and after this addition (purely additive).
#
# See [[docs/experiments/fear_hunger_v0.28.md]] for the pre-registered
# hypotheses these aggregates feed.


def bucket_by_window(
    per_tick: Sequence[_N],
    windows: tuple[tuple[str, int, int], ...] = STARVATION_WINDOWS,
) -> dict[str, _N]:
    """Sum a per-tick series into half-open ``[lo, hi)`` windows.

    ``per_tick[t]`` is added to the first window with ``lo <= t < hi``.
    Ticks outside every window's range are silently dropped (same
    semantics as v0.24's ``aggregate_cell`` internal bucketing).
    Windows must be disjoint; the first match wins on overlap.

    Returns a dict keyed by window label, with one entry per window
    in ``windows`` (zero-initialised). Numeric type is preserved:
    ``Sequence[int]`` -> ``dict[str, int]``; ``Sequence[float]`` ->
    ``dict[str, float]``.
    """
    buckets: dict[str, _N] = {label: 0 for label, _, _ in windows}  # type: ignore[misc]
    for t, value in enumerate(per_tick):
        for label, lo, hi in windows:
            if lo <= t < hi:
                buckets[label] = buckets[label] + value
                break
    return buckets


@dataclass(frozen=True)
class EventBandTrajectory:
    """Per-tick event aggregates from a single events.jsonl.

    Each field is length ``n_ticks`` (events at tick ``>= n_ticks`` are
    silently dropped, mirroring ``load_population_trajectory``). Index
    ``t`` is the count (or sum, for ``hazard_damage_per_tick``) of
    events stamped at tick ``t``.

    Companion to ``PopulationTrajectory`` — does not duplicate its
    death-cause series. v0.28 callers typically load both for a single
    run and read across them.
    """

    births_per_tick: tuple[int, ...]
    food_events_per_tick: tuple[int, ...]
    hazard_entries_per_tick: tuple[int, ...]
    hazard_damage_per_tick: tuple[float, ...]
    pool_birth_denied_per_tick: tuple[int, ...]
    pool_respawn_denied_per_tick: tuple[int, ...]

    @property
    def total_births(self) -> int:
        return sum(self.births_per_tick)

    @property
    def total_food_events(self) -> int:
        return sum(self.food_events_per_tick)

    @property
    def total_hazard_entries(self) -> int:
        return sum(self.hazard_entries_per_tick)

    @property
    def total_pool_birth_denied(self) -> int:
        return sum(self.pool_birth_denied_per_tick)

    @property
    def total_pool_respawn_denied(self) -> int:
        return sum(self.pool_respawn_denied_per_tick)

    def births_after_tick(self, threshold: int) -> int:
        """Sum ``births_per_tick[t]`` for ``t > threshold`` — matches
        v0.27's ``births_after_tick_50`` aggregation (strict ``>``)."""
        return sum(self.births_per_tick[threshold + 1 :])

    def first_pool_birth_denied_tick(self) -> int | None:
        """Tick of the first ``PoolBirthDenied`` event, or ``None`` if
        the event never fired in this run. Pool-pressure-onset proxy."""
        for t, count in enumerate(self.pool_birth_denied_per_tick):
            if count > 0:
                return t
        return None


def load_event_band_trajectory(events_jsonl: Path, n_ticks: int) -> EventBandTrajectory:
    """Walk events.jsonl once and build per-tick event aggregates.

    Single forward pass, mirroring ``load_population_trajectory``'s
    parsing discipline (silently skips malformed JSON lines; reads
    ``tick`` from the row, ``cause``/``damage`` from the inner
    ``event``). Events at ``tick >= n_ticks`` are dropped.
    """
    if n_ticks < 0:
        msg = f"n_ticks must be non-negative; got {n_ticks}"
        raise ValueError(msg)

    births = [0] * n_ticks
    food = [0] * n_ticks
    haz_entries = [0] * n_ticks
    haz_damage = [0.0] * n_ticks
    pool_birth_blk = [0] * n_ticks
    pool_resp_blk = [0] * n_ticks

    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            tick = int(row.get("tick", 0))
            if tick < 0 or tick >= n_ticks:
                continue
            kind = row.get("type")
            event = row.get("event", {})
            if kind == "AgentBorn":
                births[tick] += 1
            elif kind == "AteFood":
                food[tick] += 1
            elif kind == "HazardEntered":
                haz_entries[tick] += 1
            elif kind == "HazardDamageApplied":
                haz_damage[tick] += float(event.get("damage", 0.0))
            elif kind == "PoolBirthDenied":
                pool_birth_blk[tick] += 1
            elif kind == "PoolRespawnDenied":
                pool_resp_blk[tick] += 1

    return EventBandTrajectory(
        births_per_tick=tuple(births),
        food_events_per_tick=tuple(food),
        hazard_entries_per_tick=tuple(haz_entries),
        hazard_damage_per_tick=tuple(haz_damage),
        pool_birth_denied_per_tick=tuple(pool_birth_blk),
        pool_respawn_denied_per_tick=tuple(pool_resp_blk),
    )
