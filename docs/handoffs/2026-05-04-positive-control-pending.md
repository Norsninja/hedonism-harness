# Handoff: Positive-Control Trait Experiment Pending

**Date:** 2026-05-04
**Branch:** `main`
**Tip commit:** `d63000c`
**Status:** Mesa boundary + events/metrics/io + Fear-Hunger Chamber + ASCII viz all merged to main; v0.1 negative result documented; positive-control trait experiment is the next move.

## Where we left off

`main` carries four merged slices since the pre-Mesa pause: Mesa wrapper (`HHModel` + `HHAgent`, capacity=1, shared-storage PropertyLayers, sequential founder lineage IDs), events/metrics/io (blinker signals on `core/events.py`, scoped aggregators with sender filtering, JSONL tick envelopes, run dir + CSV/JSONL writers), four pre-cursor fixes (reproduction cost in scoring, sender filtering, tick envelope, defensive `decision.action ∈ get_valid_actions` assertion, HazardDamageApplied emission), Fear-Hunger Chamber + batch runner with experiment report at [[docs/experiments/fear_hunger_v0.1.md]], and the snapshot ASCII renderer at [[src/hedonism_harness/viz/ascii_renderer.py]] with chamber snapshot embedded in the v0.1 report. **227 tests passing**, smoke test exits 0. `claude/mesa-wrapper` and `claude/viz-ascii` are merged and can be deleted.

The v0.1 pilot result is **fear paralysis across all 8 seeds**: 40/40 starvation deaths, 0 hazard entries, 0 food events, 0 births. The next question is whether the harness *can* express different phenotypes when traits are biased, not whether default traits cross.

## What this session shipped

- Mesa boundary commits 1–3 + viz commit (4 PRs worth, all merged via FF to main, sha trail `7f89a63 → f8fbcea → 43d8d93 → d63000c`)
- 227 tests (was 175 at pre-Mesa pause; +52 across Mesa, signals, metrics, io, newborn-defer, chamber, viz)
- First experiment artifact: [[docs/experiments/fear_hunger_v0.1.md]] with embedded ASCII snapshot
- Reusable `scripts/render_chamber_snapshot.py` for embedding terrain + agent positions in future reports

## Files touched (wikilinks for fast load)

- [[docs/experiments/fear_hunger_v0.1.md]] — pilot result + embedded snapshot; baseline for v0.2 comparison
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] — chamber layout + `run_chamber` driver; reuse for v0.2
- [[src/hedonism_harness/experiments/batch.py]] — `run_chamber_batch(seeds=, batch_id=)`; sweep entry point
- [[src/hedonism_harness/experiments/snapshots.py]] — Mesa→viz adapter; use to embed v0.2 condition snapshots
- [[src/hedonism_harness/viz/ascii_renderer.py]] — Mesa-free renderer; AST-test guards layering
- [[src/hedonism_harness/core/traits.py]] — `Traits`, `TraitConfig`, `random_traits`, `mutate_traits`; archetype factories should live in `experiments/`, not here
- [[src/hedonism_harness/core/actions.py]] — `action_energy_cost(REPRODUCE, ...)` now reads `ReproductionConfig.energy_cost`
- [[src/hedonism_harness/metrics/aggregators.py]] — `EpisodeAggregator(model=...)` for sender-filtered batch isolation
- [[src/hedonism_harness/model.py]] — `event_log` is now `list[LoggedEvent]`; iterators access `.event` and `.tick`

## Decisions locked in

- Adapter layer is **orchestration only** — see [[docs/CORE_ARCHITECTURE.md]] §4. Chamber + viz live above the line; renderer is `core`-only per [[docs/SPEC.md]] §27.11.
- `LoggedEvent(tick, event)` envelopes are the canonical `event_log` shape; raw events still flow on signals.
- Reproduction cost in scoring uses `ReproductionConfig.energy_cost` so harness "feels" the same charge `process_reproduction` later applies.
- Trait archetype factories for v0.2 land in `experiments/`, **not** in `core/traits.py`. Do **not** modify global `TraitConfig` defaults yet.
- Branch flow: each slice merges FF to `main`; new work cuts a fresh branch from `main`.

## Open questions / blockers

- None blocking — user has approved the next experiment direction (positive-control trait archetypes first).

## Next concrete step

Cut `claude/positive-control-traits` from `main`. Add archetype factories in a new file [[src/hedonism_harness/experiments/trait_archetypes.py]] producing four bundles (`Fearful`, `Reckless`, `Balanced`, `Explorer`) that build `Traits` instances at the extremes of [[docs/SPEC.md]] §8.1 ranges (do not touch `core/traits.py`). Add a `run_chamber_condition(seed, archetype, ...)` variant in [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] that takes a `Callable[[np.random.Generator], Traits]` instead of using `random_traits`, OR — cleaner — extend `FounderSpec` with an optional `traits_override`. Add [[src/hedonism_harness/experiments/positive_control.py]] that runs each archetype across 8 seeds, captures one chamber snapshot per condition via [[src/hedonism_harness/experiments/snapshots.py]], and writes [[docs/experiments/fear_hunger_v0.2.md]] with a comparison table (default vs Fearful vs Reckless vs Balanced vs Explorer). Tests: archetype trait values respect SPEC §8.1 ranges + each archetype produces deterministic founders under fixed seed. Goal is binary: **does at least one archetype cross the hazard band and reach food?** If yes → tune defaults. If no → inspect [[src/hedonism_harness/core/valence.py]].

## Watch-outs

- Founder body ids start at 1 (not 0); first agent renders as `b`. Snapshot tests must account.
- `paint_chamber` writes through `model.world` which shares storage with PropertyLayers — never recreate `World` after the model exists or the link breaks (no test guards this; see [[tests/test_simulation_determinism_mesa.py]] `test_property_layer_storage_is_shared_with_world`).
- Trait archetypes must respect [[docs/SPEC.md]] §8.1 ranges or `validate_traits` raises.
- `HHModel.event_log` stores `LoggedEvent`, not raw events — JSONL writer expects envelopes.
- `HedonismPolicy(exploration_noise=0)` is determinism-friendly but produces zero divergence in the safe zone; v0.2 may need ≥0.05 to break ties between archetypes.
- Determinism north star: [[scripts/core_smoke_test.py]] + [[tests/test_simulation_determinism_mesa.py]] (Smoke A + B). Both passed at handoff time.
- The 5% noise + same-seed determinism test in v0.1 had to bump to 80 ticks before different seeds diverged in the safe zone; v0.2 archetype tests should run ≥150 ticks for meaningful divergence.

## CI gate at handoff time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   227 passed
uv run python scripts/core_smoke_test.py  ok
```
