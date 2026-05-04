# Handoff: Reproduction Emergence Pending

**Date:** 2026-05-04
**Branch:** `main`
**Tip commit:** `f695c6e`
**Status:** v0.4 valence fix + v0.5 trait tuning + v0.6 grid sweep all merged. Diagnostic ladder validated. v0.7 reproduction emergence is the next move.

## Where we left off

`main` carries four merged slices since the last handoff (`positive-control-pending`): v0.3 geometry sweep (structural-masking falsified), v0.4 valence fix (anticipated food pleasure → archetypes work in `tight_gradient`), v0.5 trait tuning (permissive defaults → mixed-phenotype populations), and v0.6 trait grid (27/27 cells qualify; winner `f1.5-h1-r0.55`). 283 tests passing. The v0.6 result revealed the next bottleneck: **0 births in any cell**. Reproduction emergence is the v0.7 question and is unblocked.

## What this session shipped

- v0.3 geometry sweep [[docs/experiments/fear_hunger_v0.3.md]] — three-layout × five-condition × eight-seed null result
- v0.4 valence fix [[src/hedonism_harness/core/valence.py]] — `anticipated_food_pleasure` term (+24 lines, +5 tests); flipped all v0.3 criteria
- v0.5 trait tuning [[docs/experiments/fear_hunger_v0.5.md]] — `permissive_trait_config()` produces mixed phenotypes under random sampling
- v0.6 trait grid [[docs/experiments/fear_hunger_v0.6.md]] — 3×3×3 sweep validates v0.5 zone, winner `f1.5-h1-r0.55` (food=11 vs v0.5's 8)
- Tests: 264 → 283 across the three commits; ruff/format/smoke clean

## Files touched (wikilinks for fast load)

- [[src/hedonism_harness/core/valence.py]] — `anticipated_food_pleasure` is the symmetric counterpart to `safety_pleasure`; gates on `obs_before.hunger_level` (raw, NOT pain-tolerance-filtered)
- [[src/hedonism_harness/experiments/trait_configs.py]] — `default_trait_config()`, `permissive_trait_config()`, parametric `tuned_trait_config(*, fear_max, hunger_min, risk_min)`, `cell_id()`
- [[src/hedonism_harness/experiments/trait_tuning.py]] — v0.5 sweep driver
- [[src/hedonism_harness/experiments/trait_grid.py]] — v0.6 27-cell sweep with four-criterion evaluator + SPEC-distance tie-break
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] — `run_chamber` gains `trait_config: TraitConfig | None` kwarg; `ChamberLayout` already has `spawn_x` from v0.3
- [[src/hedonism_harness/experiments/layouts.py]] — `default_layout()`, `tight_gradient_layout()`, `near_hazard_layout()` from v0.3
- [[tests/test_valence.py]] — 5 new food-anticipation contracts + fear-west regression guard
- [[tests/test_trait_grid.py]] — 13 tests: factory bounds, four-criterion evaluator, failure-mapping winner selector

## Decisions locked in

- **v0.7 fixed trait config**: `tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)` — the v0.6 winner. Hold this fixed, sweep `ReproductionConfig` only.
- **Don't promote to `core/traits.py` defaults yet.** The same v0.5 reasoning still holds — lineage not yet sustained, so the "viable default" story is incomplete.
- **Failure→action mapping must be pre-registered before each experiment.** v0.3 + v0.6 both used this; it pays off.
- **Sensor work is deferred to v0.9.** The v0.3 evidence falsified the structural-masking hypothesis; sensor expansion would be premature.
- **No core/ changes since v0.4.** v0.5 and v0.6 are pure `experiments/` additions.

## Open questions / blockers

- None blocking. User has approved the project ladder through v0.9 and explicitly endorsed v0.7 as next.

## Next concrete step

Cut `claude/repro-emergence-v0.7` from `main`. Hold layout (`tight_gradient`), policy (`HedonismPolicy(exploration_noise=0.05)`), and trait config (`tuned_trait_config(fear_max=1.5, hunger_min=1.0, risk_min=0.55)`) fixed. Sweep only [[src/hedonism_harness/core/config.py]]'s `ReproductionConfig` fields: `energy_threshold` (currently 70 — try {50, 60, 70}), `energy_cost` (currently — check default; sweep {5, 10, 15}), and possibly the `reproduction_drive` trait range floor (try raising from 0.0 to {0.5, 1.0}). Pre-register binary criteria *before running*: (1) ≥1 birth across the 8-seed × 5-founder population in some config; (2) NOT trivial overpopulation (e.g., end_population ≤ 3× founders for any seed, to filter degenerate "infinite reproduction" configs); (3) primary score = `total_births`, tie-break = closest-to-SPEC config. Add a parametric `tuned_reproduction_config(*, energy_threshold, energy_cost, drive_min)` factory in [[src/hedonism_harness/experiments/repro_configs.py]] (new file). Add `experiments/repro_grid.py` driver mirroring [[src/hedonism_harness/experiments/trait_grid.py]] structure: baseline + grid cells + `comparison.csv` + `winner.txt`. Tests: factory bounds (energy_threshold ∈ [10, 100], energy_cost ≥ 0, drive_min ∈ [0, 3]); criterion evaluator + over-population filter + smoke. Then run, write [[docs/experiments/fear_hunger_v0.7.md]] with verdict, commit, FF merge.

## Watch-outs

- **Reproduction is a Mesa-side process** — see [[src/hedonism_harness/model.py]] `_process_birth_queue`. Newborns DO NOT step the tick of birth (snapshot-iteration invariant); first birth observable on tick `T+1` of the parent's reproduce action. Don't conflate `reproduction_requests` (parent emitted intent) with `births` (model accepted the request and instantiated child).
- **Reproduction valence already accounts for `ReproductionConfig.energy_cost`** since v0.4-precursor; if the sweep raises the cost, the harness will feel it.
- The Mesa boundary already enforces capacity=1 grid — child placement requires an unoccupied adjacent cell (per [[src/hedonism_harness/core/reproduction.py]] `process_reproduction`). High-density populations may produce `reproduction_requests > births` due to no available neighbor.
- v0.6's per-cell artifact tree is large (216 run dirs). v0.7 with a 3×3×3 sweep would produce another 216. `runs/` is gitignored — don't commit batch artifacts.
- **Determinism north star**: [[scripts/core_smoke_test.py]] + [[tests/test_simulation_determinism_mesa.py]]. Both passed at handoff time. Adding parametric reproduction factory must not introduce new RNG paths.
- The v0.6 winner cell (`f1.5-h1-r0.55`) produces survivors in only **1 of 8 seeds** at tick 200. v0.7 must not collapse that to zero — keep the existing trait-grid winner check passing as a smoke contract.
- Project ladder (post-v0.7): v0.8 memory arm (`MemoryHedonismPolicy`); v0.9 sensor expansion / default chamber rescue. Don't start either before v0.7 lands.

## CI gate at handoff time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   283 passed
uv run python scripts/core_smoke_test.py  ok
```
