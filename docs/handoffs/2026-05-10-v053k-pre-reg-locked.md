# Handoff: v0.53k pre-reg locked; perception-reach mechanism probe ready for implementation

**Date:** 2026-05-10
**Branch:** `claude/review-hedonism-harness-Ryyx0` (post-merge aligned with `origin/main` after squashing #59 / #60 / #61; v0.53k pre-reg + handoff are the only commits ahead)
**Tip commit:** `2c37d1b` (handoff will land at HEAD+1)
**Status:** Three slices shipped this session (v0.53h #59, v0.53i #60, v0.53j #61). v0.53k pre-reg drafted, locked, committed; **implementation NOT started this session — paused per user direction for handoff before next session implements.**

## Where we left off

Three squash-merged slices this session: v0.53h (`WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`, priority 5, n_ticks doubling did not lift reachability + survival horizon also has a ceiling); v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`, **priority 4 — first RESCUED outcome since v0.53d→v0.53h null stack**, reachability 35/64); v0.53j (`WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`, priority 5, sharp threshold-like discontinuity at the FOOD_NEAR1/FOOD_NEAR2 boundary, D Tier-3 anchor reproduced v0.53i with **zero drift on all six paired_d cells**). v0.53k pre-reg drafted (354 lines, committed `2c37d1b`); user locked all design points (4 arms, sensor_radius=8 via `BodyConfig.effective_sensor_radius_override`, Tier-3 anchor on D unchanged, `PERCEPTION_OPPOSITE_SIGN_HALT` halt name, bounded-causality language). Implementation (reducer + 16-test suite + reducer run + Results + PR) is the next concrete step. Working tree clean.

## What this session shipped

- v0.53h — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400` (PR #59, squash `091b728`). Asymmetric `n_ticks` (C at 400, A/B at 200); NEW Tier-3 predecessor-sanity anchor on C tick-200 reachability. Central finding: survival horizon also has a ceiling.
- v0.53i — `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2` (PR #60, squash `a8a897d`). First geometry-axis slice; `WIDENED_FOOD_NEAR2_LAYOUT` script-local; `GEOMETRY_OPPOSITE_SIGN_HALT` introduced. Central finding: 2-column food-distance reduction lifts reachability to 35/64 + bridge fires PRESENT.
- v0.53j — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1` (PR #61, squash `66dcb49`). 4-arm dose-response; D Tier-3 positive anchor on FOOD_NEAR2 (categorical reachability + sub-verdict + six paired_d cells reproducing v0.53i within 1e-3). Central finding: dose-response is sharp, not graded — 1-column corridor null, 0-column corridor rescues.
- v0.53k pre-reg — drafted, locked, committed (`2c37d1b`). NOT yet implemented.

## Files touched (wikilinks for fast load)

- [[docs/experiments/fear_hunger_v0.53h.md]] — pre-reg + Results; verdict `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`.
- [[docs/experiments/fear_hunger_v0.53i.md]] — pre-reg + Results; verdict `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`; first RESCUED.
- [[docs/experiments/fear_hunger_v0.53j.md]] — pre-reg + Results; verdict `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`; sharp dose-response.
- [[docs/experiments/fear_hunger_v0.53k.md]] — pre-reg ONLY (Results placeholder); locked design.
- [[scripts/v0_53h_time_horizon_extension_n400_audit.py]] / [[scripts/v0_53i_geometry_food_near2_audit.py]] / [[scripts/v0_53j_food_distance_dose_response_audit.py]] — reducers (2647 / 2713 / 2914 lines).
- [[tests/test_v0_53h_time_horizon_extension_n400_audit.py]] / [[tests/test_v0_53i_geometry_food_near2_audit.py]] / [[tests/test_v0_53j_food_distance_dose_response_audit.py]] — 16 tests each (1327 / 1332 / 1323 lines).
- v0.53k script + test files DO NOT EXIST YET (next session creates them).

## Decisions locked in

- **`BodyConfig.effective_sensor_radius_override` is the perception lever** for v0.53k. Per `src/hedonism_harness/core/sensors.py:138-142` the override drives perception calculation; per `src/hedonism_harness/core/body.py:81` metabolic drain uses `traits.sensor_radius` directly — the override is **information-channel-only, NOT cost-confounded**.
- **r=8 dose** is the minimum east-ray reach from `spawn_x=1` to `FOOD_NEAR1.food_x_min=9` (ray scans `[2..r+1]`). r=7 deferred to v0.53l candidate (the converse-boundary test).
- **4 arms only** (no fifth in-slice negative anchor on FOOD_NEAR1 + default sensor; cross-slice reference to v0.53j C is sufficient).
- **`PERCEPTION_OPPOSITE_SIGN_HALT`** as priority-3 halt name (renamed from v0.53i/j's `GEOMETRY_OPPOSITE_SIGN_HALT`).
- **Bounded-causality framing** per user direction: priority 4 = "consistent with sensor-reach being a binding constraint under the tested envelope" (NOT "perception was binding"; NOT exclusive causality — sensor radius may alter policy gradients / hazard anticipation / food-attraction signal strength beyond simple visibility per `signal += value/distance` in `core/sensors.py:11`).
- **D Tier-3 anchor** unchanged from v0.53j (categorical reachability == 35/64 + sub-verdict == BRIDGE_PRESENT + six paired_d cells reproducing v0.53i within 1e-3).
- **Predecessor stack now EIGHT long**: v0.53c/d/e/f/g/h/i/j — all referenced verbatim in v0.53k locked phrases.

## Open questions / blockers

- None. v0.53k design fully locked; next session can proceed directly to implementation per the locked pre-reg.

## Next concrete step

**`/resume` first; then implement v0.53k.** Cadence: copy v0.53j templates as starting seed (the over-broad-rename trap from this session is a known pitfall — v0.53j → v0.53k metadata renames are safe; `food_near1` → `food_near1` no change; new C arm name `C_widened_food_near1_combined_sr8_N400` adds `_sr8` to v0.53j's C; new sub-verdict prefix `C_WIDENED_FOOD_NEAR1_SR8_TICK{N}_BRIDGE_{...}`). Critical structural deltas vs v0.53j: (1) C body_config now has THREE non-default fields (`starting_energy=100`, `base_metabolic_cost=0.10`, `effective_sensor_radius_override=8`); (2) priority-3 halt renamed `PERCEPTION_OPPOSITE_SIGN_HALT`; (3) verdict names changed to `..._SENSOR_RADIUS_8`; (4) CSV adds one new column `body_effective_sensor_radius_override` (None on A/B/D, 8 on C); (5) test #5 asserts `C.body_config.effective_sensor_radius_override == 8`; test #6 asserts `D.body_config.effective_sensor_radius_override is None`; test #7 NEW cross-arm perception contrast; test #16 substring assertions reference v0.53c–v0.53j (eight verdicts). Output dir: `runs/v0.53k-perception-sensor-radius-8/`. Then: CI gate → reducer run (~25-50 min, 256 runs) → Results section → commit → PR → user-confirms-CI-green → squash-merge → force-with-lease align branch.

## Watch-outs

- **Bulk metadata rename trap (this session): the v0.53i → v0.53j sed replace caught the predecessor-stack `v0.53i` references in locked phrases and test #16 substrings.** The subagent restored them surgically. For v0.53j → v0.53k, ensure `v0.53j` predecessor references in locked phrases (priority 4/5/6) and test #16 substrings are preserved, NOT bulk-replaced to v0.53k.
- **D arm body_config in v0.53k is byte-identical to v0.53j D and v0.53i C.** No `effective_sensor_radius_override` field on D. Test #6 explicitly asserts `D.body_config.effective_sensor_radius_override is None`.
- **C and D differ by exactly TWO things in v0.53k**: layout (FOOD_NEAR1 vs FOOD_NEAR2) AND `effective_sensor_radius_override` (8 vs None). All other body_config / n_ticks / corpus parameters identical. Test #7 (new cross-arm perception contrast) verifies.
- **Locked phrase discipline**: priority 4 phrase says "**consistent with sensor-reach being a binding constraint**" — the bold is part of the verbatim phrase per the pre-reg's outcome-conditions table. Preserve through implementation.
- **`signal += value/distance` interpretive caveat** in priority-4 locked phrase explicitly references `core/sensors.py:11`. The phrase is correct per source — verify the source line still reads that way before locking.
- **No new src/ change.** Test #8 unchanged from v0.53e–v0.53j. SHAs: layouts.py `d4521cb5...`, chamber driver `62d134c5...`.
- **Determinism north star** ([[scripts/core_smoke_test.py]]) must continue to pass after any seam-add. v0.53k makes no `src/` changes.
- **Reducer wall time** ~25-50 min on 256 runs. Use `run_in_background: true` on the Bash launching the reducer.
- **Branch is `claude/review-hedonism-harness-Ryyx0`**. Force-with-lease cleanup after squash-merge is the canonical pattern (used 3× this session).

## CI gate at handoff time

```
uv run ruff check .             ok
uv run ruff format --check .    ok (242 files already formatted)
uv run pytest                   1856 passed, 7 skipped
uv run python scripts/core_smoke_test.py  ok (determinism north star intact; no src/ changes since v0.53e)
```
