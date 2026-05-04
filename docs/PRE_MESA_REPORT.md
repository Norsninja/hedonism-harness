# Pre-Mesa Report

**Snapshot date:** 2026-05-04
**Branch:** `claude/review-project-spec-Q1DQJ`
**Tip commit:** see `git log -1 --format=%H`
**Status:** Mesa-free scientific core complete; Mesa boundary not yet crossed.

This report is the audit checkpoint between the pure scientific core and the Mesa adapter layer. It documents what is built, what is proven, what is not yet wired up, and what comes next. Read this before starting any work in `mesa_agents.py` or `model.py`.

---

## 1. Summary

| Metric | Value |
|---|---|
| Source files (`core/` + `policies/`) | 18 |
| Source LOC (excluding `__init__.py`) | ~1880 |
| Test files | 12 |
| Test LOC | ~2420 |
| Test count | **175 passing, 0 failing** |
| Hypothesis property tests | ~10 (each running 25 examples in dev / 200 in CI) |
| Mesa imports anywhere in the codebase | **0** |
| Pydantic configs (frozen) | 5 (`WorldConfig`, `BodyConfig`, `ActionConfig`, `ReproductionConfig`, `TraitConfig`) |
| Smoke test | `scripts/core_smoke_test.py`, 3 stages, exit 0 |

The scientific core is feature-complete for v0.1 in everything that does not require a simulation orchestrator: world generation, agent body lifecycle, traits, valence harness, memory, sensors, action transitions, four policies, and reproduction logic. What remains for v0.1 lives entirely in the Mesa adapter, metrics, IO, and experiment layers.

---

## 2. Module inventory

### `core/` — pure scientific layer (no Mesa, no IO)

| Module | LOC | Owns | Tests | Key invariants |
|---|---:|---|---:|---|
| `rng.py` | 46 | `RngStreams`, `make_streams`, `spawn_agent_rng`, `STREAM_NAMES` | 4 | Same seed → identical sequences across all named streams. Streams are independent (drawing from one does not advance another). Per-agent RNG is a real `Generator` distinct from its parent. |
| `config.py` | 137 | `WorldConfig`, `BodyConfig`, `ActionConfig`, `ReproductionConfig` | 14 | All configs are frozen Pydantic v2 models (`extra="forbid"`). Range constraints enforced for every numeric field. JSON round-trip preserves equality. `BodyConfig` rejects `starting_*` > `max_*`. |
| `world.py` | 119 | `World` (mutable dataclass, NumPy layers), `Cell` (read-only view), `CellKind` enum, `build_world`, `cell_at`, `in_bounds` | 8 | Same seed → byte-identical kind/food/hazard/safe layers. Different seeds → different layers. `food_value` set only on `FOOD` cells. `hazard_damage` set only on `HAZARD` cells. Food/hazard masks never overlap. Out-of-bounds reads raise. |
| `traits.py` | 154 | `Traits` (frozen dataclass), `TraitConfig`, `TraitRange`, `TRAIT_NAMES`, `INTEGER_TRAITS`, `random_traits`, `mutate_traits`, `validate_traits` | 14 | Generated traits respect ranges under any seed. Mutated traits respect ranges under any seed and any sigma. Mutation is deterministic under seed. `mutation_rate=0` returns clone. `mutation_rate=1` changes ≥1 continuous trait. Integer traits stay integer under aggressive mutation. |
| `body.py` | 123 | `AgentBody` (frozen), `DeathCause`, `make_body`, `apply_metabolism`, `apply_damage`, `apply_energy_delta`, `is_dead`, `infer_death_cause`, `mark_dead` | 23 | `AgentBody` is frozen — every change goes through `dataclasses.replace`. Metabolism never increases energy. Energy delta clamped to `[0, max_energy]` under any input. `INJURY` wins death cause when both vitals at zero. Sensor radius adds metabolic cost linearly. Metabolic rate scales metabolic cost. |
| `events.py` | 102 | `AgentMoved`, `AgentStayed`, `AteFood`, `HazardEntered`, `HazardDamageApplied`, `ReproductionRequested`, `AgentBorn`, `AgentDied`, `AnyEvent` type alias | (covered by callers) | All events are frozen dataclasses. No subscribers, no signals — that is `metrics/`'s concern. |
| `actions.py` | 236 | `Action` enum (7 variants), `MOVE_DIRECTIONS`, `CellMutation`, `WorldDelta`, `EMPTY_DELTA`, `ActionResult`, `apply_action`, `commit_delta`, `get_valid_actions`, `action_energy_cost` | 20 | `apply_action` is pure: never mutates input world or input body. `EAT`'s WorldDelta is uncommitted until caller calls `commit_delta` — predict-one-step relies on this. STAY/MOVE energy charged correctly per action. Moving into HAZARD emits `HazardEntered`. Unknown action raises. `get_valid_actions` filters bounds, walls, food-required-for-eat, and reproduction validity (when `repro_config` provided). |
| `sensors.py` | 190 | `Observation` (frozen, 27 fields), `observe` | 15 | `observe` is pure: never mutates world or body. Observation is frozen. Internal sensors derive from body alone. External directional signals: `value/distance` axial sums, edge-respecting. Memory sensors zero when memory is `None` or unknown shape; populated when `ValenceMemory` provided. |
| `valence.py` | 193 | `ValenceBreakdown` (frozen), `evaluate` | 18 | `total = pleasure - pain - fear - uncertainty - effort` exactly. No NaN/inf under any random traits + arbitrary in-range observation. Hunger pain rises with hunger. Eating pleasure higher when hungry. Pain tolerance reduces felt pain. Risk tolerance reduces fear. Reproduction pleasure scales with reproduction drive. Hazard residency produces hazard pain. Moving away from hazard produces safety pleasure. Recovery/novelty/uncertainty are zero in v0.1 (memory and health-regen wiring placeholders — see §5). |
| `memory.py` | 131 | `ValenceMemory` (mutable), `make_memory`, `alpha_for_strength`, `update_at`, `decay_all`, `directional_signals` | 18 | `alpha_for_strength` is inverse-monotonic with floor `0.05`. EMA blend at α=1 overwrites; at α≈0.05 changes slowly. `update_at` only touches the target cell. `decay_all` shrinks EMAs and leaves visits/tick alone. Directional signals mirror sensor geometry. |
| `reproduction.py` | 175 | `find_adjacent_empty_cell`, `can_reproduce`, `make_child`, `charge_parent`, `process_reproduction` | 24 | `find_adjacent_empty_cell` is N→S→E→W deterministic, skips walls and occupied cells, returns `None` when surrounded. `can_reproduce` requires energy ≥ threshold AND age ≥ min AND local hazard ≤ threshold AND adjacent space exists. `make_child`: lineage inherited, parent_id recorded, traits mutated, energy = `offspring_start_energy`, deterministic under seed. `process_reproduction` is atomic: returns `(parent, child)` on success or `None` with no charge to parent. |

### `policies/` — decision strategies (depends on core only)

| Module | LOC | Owns | Tests | Key invariants |
|---|---:|---|---:|---|
| `base.py` | 65 | `DecisionContext` (frozen), `PolicyDecision` (frozen), `Policy` Protocol | (covered by impls) | Strategy interface only. No state. No behavior. |
| `random_policy.py` | 18 | `RandomPolicy` | (in test_policies.py) | Picks only valid actions. Deterministic under seed. |
| `reflex_policy.py` | 90 | `ReflexPolicy` | " | Eats on food when hungry. Doesn't eat when full (EAT excluded from random fallback). Flees from strongest hazard direction. Seeks strongest food direction. |
| `hedonism_policy.py` | 82 | `HedonismPolicy` | " | Predict-one-step purity: never mutates world or body during scoring. Picks max-valence action. Returns `ValenceBreakdown` for scored choices, `None` for noise picks. Rejects out-of-range `exploration_noise`. Deterministic under seed (including the noise branch). |
| `memory_hedonism_policy.py` | 18 | `MemoryHedonismPolicy` | (in test_memory.py) | Subclass of `HedonismPolicy`. Mechanically identical — distinct class for label clarity in experiments. Reads memory through the sensor layer. |

### Test files

| Test file | LOC | Tests |
|---|---:|---:|
| `test_simulation_determinism.py` | 47 | 3 |
| `test_rng.py` | 63 | 4 |
| `test_world.py` | 109 | 8 |
| `test_config.py` | 52 | 14 |
| `test_traits.py` | 160 | 14 |
| `test_body.py` | 263 | 23 |
| `test_actions.py` | 301 | 20 |
| `test_sensors.py` | 246 | 15 |
| `test_valence.py` | 311 | 18 |
| `test_memory.py` | 264 | 18 |
| `test_reproduction.py` | 354 | 24 |
| `test_policies.py` | 250 | 14 |
| **Total** | **2420** | **175** |

---

## 3. Dependency rules — current vs. SPEC §27.11

The intended rules from SPEC §27.11:

```
core/         -> stdlib + numpy + pydantic + blinker. NO Mesa. NO policies.
policies/     -> core/ only.
mesa_agents.py-> Mesa + core + policies.
model.py      -> Mesa + core + policies + metrics + io.
metrics/      -> core/events. NO io.
io/           -> metrics + core/events.
experiments/  -> model + metrics + io.
viz/          -> core (read-only) + metrics (read-only).
tests/        -> may import anything.
```

Verification of the layers that exist today:

- ✅ **`core/`** imports stdlib + numpy + pydantic only. Verified with `grep -r '^import\|^from' src/hedonism_harness/core/`. No Mesa imports anywhere. No blinker imports (blinker will be wired in `metrics/` per §27.8).
- ✅ **`policies/`** imports `core/` only. No Mesa.
- ⚪ **`mesa_agents.py`**, **`model.py`**, **`metrics/`**, **`io/`**, **`experiments/`**, **`viz/`** do not exist yet (Mesa boundary). Their package directories exist with docstrings stating their dependency rules.

There are no rule violations. The actual code matches the design.

---

## 4. Known guarantees

Things the current 175-test suite *proves* (not just claims):

- **Determinism north star (SPEC §26.12).** Same seed → same world, byte-identical across `kind_layer`, `food_value`, `hazard_damage`, `safe_value`. Tested by example for chosen seeds and via Hypothesis over the entire `uint32` seed range.
- **Cross-module determinism end-to-end.** `scripts/core_smoke_test.py` runs the full loop for 50 ticks at seed 42, hashes every byte that should be deterministic, runs again, asserts identical hashes. Different seed produces different hashes (sanity).
- **RNG stream independence.** Drawing from one named stream does not advance any other.
- **No NaN/inf anywhere in the harness.** `evaluate(...)` produces finite values for any random traits and arbitrary in-range observations under Hypothesis.
- **Frozen configs.** Every config is immutable after construction; mutation attempts raise `ValidationError`.
- **Trait range integrity under mutation.** Mutated traits stay in their configured ranges under any seed and any sigma — Hypothesis-tested.
- **`apply_action` purity.** Verified explicitly that scoring all valid actions against a body leaves the live world and body untouched. This is the foundation of predict-one-step correctness (SPEC §27.5).
- **Reproduction atomicity.** Failed reproduction (no adjacent empty cell) does not charge the parent. The `process_reproduction` return signature distinguishes success from failure unambiguously.
- **Fear-tuned hedonism agents avoid hazards.** Property test: a fearful agent (high `fear_sensitivity`, low `risk_tolerance`, high `injury_pain_sensitivity`) with an adjacent hazard does not step into it.
- **Memory updates only the target cell.** Other cells remain untouched after `update_at`.
- **`alpha_for_strength` floor.** Even with `memory_strength=1`, alpha > 0 — learning never freezes entirely.

---

## 5. Known limitations

Things deliberately deferred or simplified in v0.1. Each item links to the SPEC clause that authorized the deferral.

- **No simulation orchestrator yet.** `mesa_agents.py` and `model.py` do not exist. There is no tick loop above the per-agent level. The Mesa boundary is the next phase.
- **No metrics or IO.** No CSV, JSONL, or `runs/{run_id}/` outputs. `core/events.py` defines event dataclasses but they are not yet wired to blinker signals — that lands with `metrics/aggregators.py` post-Mesa (SPEC §27.8).
- **No visualization.** `viz/` directory exists with a docstring; `terminal.py` and `mesa_viz.py` are not implemented.
- **Recovery pleasure is structurally always zero.** No mechanic regenerates health in v0.1. The harness wiring is in place; once a regen mechanic is added, `recovery_pleasure` becomes non-zero with no code change to the harness (SPEC §11.4).
- **Novelty pleasure is structurally always zero.** Computed from `_remembered_good_total(obs_after)`; with memory enabled, this reads remembered good signals — but those signals are accumulated from felt pleasure, which today equals `breakdown.pleasure` in the smoke test. The novelty interpretation specified in SPEC (visit-count-based) is not implemented; the current wiring treats remembered pleasure as novelty. Address in v0.2 (SPEC §22, §24 v0.2: "More refined paralysis metric").
- **Uncertainty score is hardcoded to 0.0.** The wiring point in `evaluate(...)` is marked. Memory-confidence-based uncertainty lands when we promote it from the placeholder (SPEC §11.5).
- **Reproduction occupancy uses an optional `frozenset`.** Today only the policy layer has visibility into agent positions, and only the Mesa wrapper will have a real occupancy view. Until then, `find_adjacent_empty_cell(occupied=None)` only checks bounds and `WALL`. Reproduction tests pass an explicit occupied set.
- **Hazards are deterministic, not probabilistic.** Damage applied on residency is fixed per cell per tick. Probabilistic hazards deferred (SPEC §27.6).
- **No food regrowth.** Once eaten, cells stay `EMPTY` (SPEC §3 explicitly excludes for v0.1).
- **No multi-agent occupancy at the action layer.** `apply_action(MOVE_*)` does not check whether the destination cell holds another agent. With `capacity=1` Mesa grids, this check moves to the wrapper (it cannot live in `core/` without making `core/` agent-aware, which violates layering).
- **Memory not inherited.** Per SPEC §13.4 and §27 — newborns get fresh memory.
- **Single-agent smoke test only.** `scripts/core_smoke_test.py` runs one agent for 50 ticks. Multi-agent determinism verification lands with the Mesa wrapper's first commit.
- **No `tests/test_events.py` standalone file.** Events are exercised by `test_actions.py` (which asserts the right event types are emitted) and the smoke test (which counts them). A dedicated `test_events.py` would be redundant.

---

## 6. Next: Mesa boundary plan

Four commits, in order, to a runnable Fear-Hunger Conflict Chamber experiment.

### Commit 1 — Mesa wrapper + multi-agent smoke

- `mesa_agents.py`: single `mesa.Agent` subclass holding `body`, `policy`, `memory`, `agent_rng`. `step()` is pure orchestration: observe → decide → apply_action → commit_delta → update memory → sync grid position. No new behavior logic — see `docs/CORE_ARCHITECTURE.md` §4 (the adapter rule).
- `model.py`: `mesa.Model` subclass. Builds `OrthogonalVonNeumannGrid` with `capacity=1`, wires four `PropertyLayer`s with shared NumPy storage to our `World` arrays, builds founder agents (each with unique `lineage_id`), implements per-tick order from SPEC §27.4 (shuffle → step → metabolism → hazard residency damage → death sweep → birth queue), processes `ReproductionRequested` events via `core/reproduction.process_reproduction`.
- One determinism test: build model, tick 100 times, repeat with same seed, assert byte-identical final state across all agents and the world. **This is the multi-agent extension of the v0.1 north star.**
- No CSV/JSONL yet, no Fear-Hunger world layout yet.

### Commit 2 — Events fire + metrics + io

- Define blinker signals (one per event type in `core/events.py`) — keeping them in `core/events.py` per SPEC §27.8 layering (core emits, metrics interprets, io persists).
- `metrics/collectors.py`: Mesa `DataCollector` snapshot wiring (avg energy, population, avg pain/pleasure/fear, trait averages).
- `metrics/aggregators.py`: blinker subscribers maintaining running tallies (event-style metrics from §17).
- `io/run_writer.py`: writes `runs/{run_id}/config.json` + manifest.
- `io/csv_writer.py`: writes `episode_metrics.csv`, `agent_lifetimes.csv`, `lineages.csv`.
- `io/jsonl_writer.py`: writes per-tick events.
- Tests: end-to-end run produces all expected files with expected columns.

### Commit 3 — Fear-Hunger Conflict Chamber + batch runner

- `experiments/fear_hunger_chamber.py`: world layout (safe zone → hazard band → food zone), founder agent setup, run orchestrator.
- `experiments/batch.py`: thin wrapper over `mesa.batch_run` for parameter sweeps.
- Test: chamber runs with seeded `HedonismPolicy` + `ReflexPolicy` populations and produces reproducible CSV outputs.
- CI artifact upload now retrieves `runs/{run_id}/` from each PR.

### Commit 4 — ASCII renderer

- `viz/terminal.py`: Rich `Live` rendering of grid + agent positions + tick/population overlay.
- `--render` CLI flag on the experiment runner.

### Open questions to confirm before commit 1

- **PropertyLayer with shared storage**: build PropertyLayers in `model.py`, then construct our `World` to hold references to `pl.data` for each layer. Mutations to `World.kind_layer` flow through to Mesa's PropertyLayer view. `commit_delta` and `apply_action` need no changes. (Recommended in prior discussion; awaiting confirmation.)
- **Single-agent-per-cell** (`capacity=1`) vs. multi-agent cells. (Recommended `capacity=1` — matches embodied agent semantics + reproduction adjacency check.)
- **Founder lineage IDs** — sequential per founder (0, 1, 2, ...). (Recommended.)
- **Smoke test for commit 1**: 5 `RandomPolicy` founders on 16×16 empty world, seed=42, 50 ticks, repeat with same seed, assert byte-identical final state across all agents and world. (Recommended.)

---

## 7. CI gate

The four-command gate that must pass before the Mesa boundary is crossed:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/core_smoke_test.py
```

Or equivalently:

```sh
just ci
```

GitHub Actions runs this exact sequence on every push (`.github/workflows/ci.yml`). Last verified locally: all four steps pass; pytest reports 175 passed in ~0.7s; smoke test exits 0 with all three stages passing.

---

## 8. Sign-off

The scientific core is done for v0.1. The next code that touches `src/hedonism_harness/` should be `mesa_agents.py` or `model.py`, written as adapters per the rule in `docs/CORE_ARCHITECTURE.md` §4.

If a proposed change to `core/` or `policies/` would invalidate any guarantee in §4 of this report, treat it as breaking and ask explicitly before merging.
