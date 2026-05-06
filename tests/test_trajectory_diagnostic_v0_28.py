"""Tests for v0.28 ``EventBandTrajectory`` + ``load_event_band_trajectory``
+ ``bucket_by_window`` (additive extension to ``population_dynamics``).

Covers:
  - bucket_by_window: int/float type preservation, custom windows,
    half-open ``[lo, hi)`` semantics, ticks outside windows dropped,
    empty-input behavior.
  - EventBandTrajectory: derived properties (totals, births_after_tick,
    first_pool_birth_denied_tick).
  - load_event_band_trajectory on synthetic events: per-type counting,
    HazardDamageApplied damage summation, malformed-line tolerance,
    out-of-window tick dropping, n_ticks validation.
  - H1 / H2 invariants on a real v0.27 events.jsonl artifact.
  - H9 anchor identity: aggregating across the 8 seeds at each of
    w in {0.5, 0.75, 1.0} on food_ladder reproduces the v0.27
    results-doc cells exactly.

The H9 anchor test is the halt-condition byte-identity guard for the
v0.28 diagnostic: if it fails the loader cannot be trusted to derive
seed-level signatures from the same events.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedonism_harness.experiments.population_dynamics import (
    EventBandTrajectory,
    bucket_by_window,
    load_event_band_trajectory,
    load_population_trajectory,
)

# ---------------------------------------------------------------------------
# bucket_by_window
# ---------------------------------------------------------------------------


def test_bucket_by_window_int_preserves_int_type() -> None:
    """Sequence[int] input -> dict[str, int] output (no float coercion)."""
    per_tick = tuple(1 for _ in range(200))
    result = bucket_by_window(per_tick)
    assert result == {"0-49": 50, "50-99": 50, "100-149": 50, "150-199": 50}
    for value in result.values():
        assert type(value) is int


def test_bucket_by_window_float_preserves_float_type() -> None:
    """Sequence[float] input -> dict[str, float] output."""
    per_tick = tuple(0.5 for _ in range(200))
    result = bucket_by_window(per_tick)
    assert result == {"0-49": 25.0, "50-99": 25.0, "100-149": 25.0, "150-199": 25.0}
    for value in result.values():
        assert type(value) is float


def test_bucket_by_window_half_open_semantics() -> None:
    """Tick 49 lands in 0-49; tick 50 lands in 50-99 (lo<=t<hi)."""
    per_tick = [0] * 200
    per_tick[49] = 1
    per_tick[50] = 1
    per_tick[99] = 1
    per_tick[100] = 1
    result = bucket_by_window(per_tick)
    assert result == {"0-49": 1, "50-99": 2, "100-149": 1, "150-199": 0}


def test_bucket_by_window_drops_ticks_outside_windows() -> None:
    """Ticks outside every window's [lo, hi) range are silently ignored."""
    per_tick = [0] * 250
    per_tick[200] = 7  # past the 0..199 coverage
    per_tick[249] = 3
    result = bucket_by_window(per_tick)
    assert sum(result.values()) == 0


def test_bucket_by_window_custom_windows() -> None:
    """Caller-supplied windows are honored; default is STARVATION_WINDOWS."""
    custom = (("early", 0, 10), ("late", 10, 20))
    per_tick = [1] * 20
    result = bucket_by_window(per_tick, windows=custom)
    assert result == {"early": 10, "late": 10}


def test_bucket_by_window_empty_input_returns_zero_buckets() -> None:
    """Empty per_tick -> all zero buckets, one per window label."""
    result: dict[str, int] = bucket_by_window([])
    assert result == {"0-49": 0, "50-99": 0, "100-149": 0, "150-199": 0}


# ---------------------------------------------------------------------------
# EventBandTrajectory derived properties
# ---------------------------------------------------------------------------


def _make_event_band(
    *,
    births: tuple[int, ...] = (),
    food: tuple[int, ...] = (),
    haz_entries: tuple[int, ...] = (),
    haz_damage: tuple[float, ...] = (),
    pool_birth: tuple[int, ...] = (),
    pool_resp: tuple[int, ...] = (),
    n_ticks: int = 200,
) -> EventBandTrajectory:
    """Pad each per-tick series to n_ticks and build an EventBandTrajectory."""

    def _pad_int(seq: tuple[int, ...]) -> tuple[int, ...]:
        return seq + (0,) * (n_ticks - len(seq))

    def _pad_float(seq: tuple[float, ...]) -> tuple[float, ...]:
        return seq + (0.0,) * (n_ticks - len(seq))

    return EventBandTrajectory(
        births_per_tick=_pad_int(births),
        food_events_per_tick=_pad_int(food),
        hazard_entries_per_tick=_pad_int(haz_entries),
        hazard_damage_per_tick=_pad_float(haz_damage),
        pool_birth_denied_per_tick=_pad_int(pool_birth),
        pool_respawn_denied_per_tick=_pad_int(pool_resp),
    )


def test_event_band_totals_sum_per_tick_series() -> None:
    band = _make_event_band(
        births=(1, 0, 2, 0, 3),
        food=(0, 1, 1, 0, 0),
        haz_entries=(0, 0, 0, 1, 1),
        pool_birth=(0, 0, 0, 0, 4),
        pool_resp=(0, 1, 0, 0, 0),
    )
    assert band.total_births == 6
    assert band.total_food_events == 2
    assert band.total_hazard_entries == 2
    assert band.total_pool_birth_denied == 4
    assert band.total_pool_respawn_denied == 1


def test_event_band_births_after_tick_uses_strict_gt() -> None:
    """births_after_tick(50) sums ticks 51..n_ticks-1 (strict > 50,
    matching v0.27's births_after_tick_50 contract)."""
    series = [0] * 200
    series[50] = 1
    series[51] = 1
    series[199] = 1
    band = _make_event_band(births=tuple(series))
    assert band.births_after_tick(50) == 2  # tick 50 excluded; ticks 51, 199 included


def test_event_band_first_pool_birth_denied_tick() -> None:
    """Returns first tick with a positive count, or None if never."""
    pool_birth = [0] * 200
    pool_birth[37] = 2
    pool_birth[88] = 1
    band = _make_event_band(pool_birth=tuple(pool_birth))
    assert band.first_pool_birth_denied_tick() == 37


def test_event_band_first_pool_birth_denied_tick_returns_none_when_absent() -> None:
    band = _make_event_band(n_ticks=200)
    assert band.first_pool_birth_denied_tick() is None


# ---------------------------------------------------------------------------
# load_event_band_trajectory on synthetic events.jsonl
# ---------------------------------------------------------------------------


def _write_events(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "events.jsonl"
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


def test_loader_counts_each_event_type(tmp_path: Path) -> None:
    rows = [
        {"type": "AgentBorn", "tick": 5, "event": {"agent_id": 1}},
        {"type": "AgentBorn", "tick": 5, "event": {"agent_id": 2}},
        {"type": "AteFood", "tick": 7, "event": {"agent_id": 1, "food_gained": 20.0}},
        {"type": "HazardEntered", "tick": 10, "event": {"agent_id": 3, "x": 8, "y": 0}},
        {"type": "HazardDamageApplied", "tick": 10, "event": {"agent_id": 3, "damage": 8.0}},
        {"type": "HazardDamageApplied", "tick": 10, "event": {"agent_id": 3, "damage": 4.5}},
        {"type": "PoolBirthDenied", "tick": 100, "event": {"parent_id": 7}},
        {"type": "PoolRespawnDenied", "tick": 150, "event": {"x": 4, "y": 2}},
        # Non-tracked types should be ignored.
        {"type": "AgentMoved", "tick": 5, "event": {"agent_id": 1}},
        {"type": "AgentStayed", "tick": 5, "event": {"agent_id": 2}},
    ]
    band = load_event_band_trajectory(_write_events(tmp_path, rows), n_ticks=200)
    assert band.total_births == 2
    assert band.total_food_events == 1
    assert band.total_hazard_entries == 1
    assert band.total_pool_birth_denied == 1
    assert band.total_pool_respawn_denied == 1
    assert band.births_per_tick[5] == 2
    assert band.food_events_per_tick[7] == 1
    assert band.hazard_damage_per_tick[10] == pytest.approx(12.5)


def test_loader_drops_events_at_or_after_n_ticks(tmp_path: Path) -> None:
    """Events at tick >= n_ticks are silently dropped (mirrors
    load_population_trajectory which iterates range(n_ticks))."""
    rows = [
        {"type": "AgentBorn", "tick": 199, "event": {"agent_id": 1}},
        {"type": "AgentBorn", "tick": 200, "event": {"agent_id": 2}},
        {"type": "AgentBorn", "tick": 250, "event": {"agent_id": 3}},
    ]
    band = load_event_band_trajectory(_write_events(tmp_path, rows), n_ticks=200)
    assert band.total_births == 1
    assert band.births_per_tick[199] == 1


def test_loader_drops_negative_ticks(tmp_path: Path) -> None:
    rows = [
        {"type": "AgentBorn", "tick": -1, "event": {"agent_id": 1}},
        {"type": "AgentBorn", "tick": 0, "event": {"agent_id": 2}},
    ]
    band = load_event_band_trajectory(_write_events(tmp_path, rows), n_ticks=10)
    assert band.total_births == 1
    assert band.births_per_tick[0] == 1


def test_loader_skips_malformed_json_lines(tmp_path: Path) -> None:
    """Bad JSON lines are silently skipped (mirrors load_population_trajectory)."""
    path = tmp_path / "events.jsonl"
    with path.open("w") as f:
        f.write('{"type": "AgentBorn", "tick": 1, "event": {"agent_id": 1}}\n')
        f.write("this is not json\n")
        f.write('{"type": "AteFood", "tick": 2, "event": {"agent_id": 1}}\n')
    band = load_event_band_trajectory(path, n_ticks=10)
    assert band.total_births == 1
    assert band.total_food_events == 1


def test_loader_rejects_negative_n_ticks(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text("")
    with pytest.raises(ValueError, match="n_ticks must be non-negative"):
        load_event_band_trajectory(path, n_ticks=-1)


def test_loader_handles_empty_events_file(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text("")
    band = load_event_band_trajectory(path, n_ticks=200)
    assert band.total_births == 0
    assert band.total_food_events == 0
    assert band.total_hazard_entries == 0
    assert sum(band.hazard_damage_per_tick) == 0.0
    assert band.first_pool_birth_denied_tick() is None


# ---------------------------------------------------------------------------
# H1 / H2 invariants on a real v0.27 artifact
# ---------------------------------------------------------------------------


_V27_FOOD_LADDER_ROOT = Path("runs/fear-hunger-v0.27-food_ladder/arms")


def _real_artifact_available(label: str, seed: int) -> bool:
    return (_V27_FOOD_LADDER_ROOT / label / f"seed-{seed}" / "events.jsonl").is_file()


@pytest.mark.skipif(
    not _real_artifact_available("hzd8-avd0.50", 1),
    reason="v0.27 food_ladder artifacts not on disk; run scripts/v0.27_sweep.py",
)
def test_h1_event_count_partition_on_real_artifact() -> None:
    """H1: per-tick aggregates partition the events.jsonl event counts.

    sum(births_per_tick) == count(AgentBorn events at tick < 200), etc.
    Verified on a single real (w=0.50, seed=1) cell.
    """
    path = _V27_FOOD_LADDER_ROOT / "hzd8-avd0.50" / "seed-1" / "events.jsonl"
    band = load_event_band_trajectory(path, n_ticks=200)

    raw_counts = {
        "AgentBorn": 0,
        "AteFood": 0,
        "HazardEntered": 0,
        "PoolBirthDenied": 0,
        "PoolRespawnDenied": 0,
    }
    raw_haz_damage = 0.0
    with path.open() as f:
        for line in f:
            row = json.loads(line)
            tick = int(row.get("tick", 0))
            if tick < 0 or tick >= 200:
                continue
            kind = row.get("type")
            if kind in raw_counts:
                raw_counts[kind] += 1
            elif kind == "HazardDamageApplied":
                raw_haz_damage += float(row["event"]["damage"])

    assert band.total_births == raw_counts["AgentBorn"]
    assert band.total_food_events == raw_counts["AteFood"]
    assert band.total_hazard_entries == raw_counts["HazardEntered"]
    assert band.total_pool_birth_denied == raw_counts["PoolBirthDenied"]
    assert band.total_pool_respawn_denied == raw_counts["PoolRespawnDenied"]
    assert sum(band.hazard_damage_per_tick) == pytest.approx(raw_haz_damage)


@pytest.mark.skipif(
    not _real_artifact_available("hzd8-avd0.50", 1),
    reason="v0.27 food_ladder artifacts not on disk",
)
def test_h2_band_partition_sums_to_per_tick_total() -> None:
    """H2: bucket_by_window partitions the 0..n_ticks-1 range, so
    sum(buckets.values()) == sum(per_tick) for a 200-tick series.
    """
    path = _V27_FOOD_LADDER_ROOT / "hzd8-avd0.50" / "seed-1" / "events.jsonl"
    band = load_event_band_trajectory(path, n_ticks=200)
    for series in (
        band.births_per_tick,
        band.food_events_per_tick,
        band.hazard_entries_per_tick,
        band.pool_birth_denied_per_tick,
        band.pool_respawn_denied_per_tick,
    ):
        assert sum(bucket_by_window(series).values()) == sum(series)
    # Float series (hazard damage) handled separately to preserve type.
    haz_buckets = bucket_by_window(band.hazard_damage_per_tick)
    assert sum(haz_buckets.values()) == pytest.approx(sum(band.hazard_damage_per_tick))


# ---------------------------------------------------------------------------
# H9 anchor identity: aggregate across 8 seeds reproduces v0.27 cells
# ---------------------------------------------------------------------------


# v0.27 food_ladder results-doc cells (8-seed sums) at each weight.
# Source: docs/experiments/fear_hunger_v0.27.md results table.
# Schema: (label, total_births, b>50, total_food, total_haz_entries,
#          total_starv, total_inj, total_pool_birth_denied)
_V27_FOOD_LADDER_ANCHORS: tuple[tuple[str, int, int, int, int, int, int, int], ...] = (
    ("hzd8-avd0.50", 154, 98, 685, 163, 81, 25, 0),
    ("hzd8-avd0.75", 145, 89, 688, 145, 78, 20, 6),
    ("hzd8-avd1.00", 143, 92, 674, 120, 77, 16, 0),
)


@pytest.mark.skipif(
    not all(
        _real_artifact_available(label, seed)
        for label, *_ in _V27_FOOD_LADDER_ANCHORS
        for seed in range(1, 9)
    ),
    reason="v0.27 food_ladder artifacts (3 weights x 8 seeds) not on disk",
)
@pytest.mark.parametrize("anchor", _V27_FOOD_LADDER_ANCHORS, ids=lambda a: a[0])
def test_h9_anchor_identity_against_v0_27_aggregates(
    anchor: tuple[str, int, int, int, int, int, int, int],
) -> None:
    """Halt-condition byte-identity guard for the v0.28 diagnostic.

    Summing per-seed loader output across the 8 seeds at one weight on
    food_ladder must match the v0.27 results doc to the unit. Failure
    means either the events.jsonl files on disk do not match what the
    v0.27 chamber CSVs say, or the loader has a defect — either is a
    halt for v0.28.
    """
    label, exp_births, exp_b50, exp_food, exp_haz, exp_starv, exp_inj, exp_blk = anchor

    total_births = 0
    total_b50 = 0
    total_food = 0
    total_haz = 0
    total_starv = 0
    total_inj = 0
    total_blk = 0

    for seed in range(1, 9):
        path = _V27_FOOD_LADDER_ROOT / label / f"seed-{seed}" / "events.jsonl"
        band = load_event_band_trajectory(path, n_ticks=200)
        traj = load_population_trajectory(path, n_founders=5, n_ticks=200)
        total_births += band.total_births
        total_b50 += band.births_after_tick(50)
        total_food += band.total_food_events
        total_haz += band.total_hazard_entries
        total_starv += sum(traj.starvation_deaths_per_tick)
        total_inj += sum(traj.injury_deaths_per_tick)
        total_blk += band.total_pool_birth_denied

    assert total_births == exp_births, f"{label}: births {total_births} vs {exp_births}"
    assert total_b50 == exp_b50, f"{label}: b>50 {total_b50} vs {exp_b50}"
    assert total_food == exp_food, f"{label}: food {total_food} vs {exp_food}"
    assert total_haz == exp_haz, f"{label}: haz_entries {total_haz} vs {exp_haz}"
    assert total_starv == exp_starv, f"{label}: starv {total_starv} vs {exp_starv}"
    assert total_inj == exp_inj, f"{label}: inj {total_inj} vs {exp_inj}"
    assert total_blk == exp_blk, f"{label}: pool_birth_denied {total_blk} vs {exp_blk}"
