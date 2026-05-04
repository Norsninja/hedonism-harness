# Core Architecture

This document describes the **current implementation** of the Hedonism Harness `core/` and `policies/` layers. For design intent and decision history see [`SPEC.md`](SPEC.md), particularly §27.

This doc is short on purpose. Detailed API stays in module docstrings.

---

## 1. Layer overview

The project has four code layers, each with explicit dependency rules:

```
viz/         (read-only consumer of core + metrics)
io/          (persists what metrics interprets)
metrics/     (interprets events from core)
experiments/ (orchestrates model + metrics + io)
─────────────────────────────────────────────────
model.py     (Mesa Model adapter — orchestration only)
mesa_agents.py (Mesa Agent adapter — orchestration only)
─────────────────────────────────────────────────
policies/    (decision strategies; depends on core only)
─────────────────────────────────────────────────
core/        (pure scientific layer; no Mesa, no IO)
```

Layers above the line do not exist yet (Mesa boundary). Layers below are the **175-test, fully Mesa-free scientific core**.

---

## 2. Module map

### `core/` — pure scientific layer

| Module | Owns | One-line description |
|---|---|---|
| `rng.py` | `RngStreams`, `make_streams`, `spawn_agent_rng` | Named NumPy RNG streams from a master seed. |
| `config.py` | `WorldConfig`, `BodyConfig`, `ActionConfig`, `ReproductionConfig` | Pydantic v2 frozen configs, JSON round-trippable. |
| `world.py` | `World`, `Cell`, `CellKind`, `build_world`, `cell_at`, `in_bounds` | Deterministic NumPy-backed grid + read-only cell view. |
| `traits.py` | `Traits`, `TraitConfig`, `TraitRange`, `random_traits`, `mutate_traits`, `validate_traits` | Inherited genome + Gaussian mutation. |
| `body.py` | `AgentBody`, `DeathCause`, `make_body`, `apply_metabolism`, `apply_damage`, `apply_energy_delta`, `is_dead`, `infer_death_cause`, `mark_dead` | Pure agent body + lifecycle helpers. |
| `events.py` | `AgentMoved`, `AgentStayed`, `AteFood`, `HazardEntered`, `HazardDamageApplied`, `ReproductionRequested`, `AgentBorn`, `AgentDied`, `AnyEvent` | Typed event dataclasses; no signals or subscribers. |
| `actions.py` | `Action` enum, `WorldDelta`, `ActionResult`, `apply_action`, `commit_delta`, `get_valid_actions`, `action_energy_cost` | Single source of truth for state transitions. |
| `sensors.py` | `Observation`, `observe` | Internal + axial external + memory sensors as one frozen dataclass. |
| `valence.py` | `ValenceBreakdown`, `evaluate` | The Hedonism Harness — converts predicted state into felt valence. |
| `memory.py` | `ValenceMemory`, `make_memory`, `alpha_for_strength`, `update_at`, `decay_all`, `directional_signals` | Per-agent NumPy-backed valence map. |
| `reproduction.py` | `find_adjacent_empty_cell`, `can_reproduce`, `make_child`, `charge_parent`, `process_reproduction` | Asexual reproduction validity + atomic processing. |

### `policies/` — decision strategies

| Module | Owns | One-line description |
|---|---|---|
| `base.py` | `DecisionContext`, `PolicyDecision`, `Policy` Protocol | Stateless strategy interface. |
| `random_policy.py` | `RandomPolicy` | Uniform sample over valid actions; baseline. |
| `reflex_policy.py` | `ReflexPolicy` | Authored priority rules: eat-if-hungry, flee-hazard, seek-food, fallback. |
| `hedonism_policy.py` | `HedonismPolicy` | Predict-one-step + harness scoring + exploration noise. |
| `memory_hedonism_policy.py` | `MemoryHedonismPolicy` | HedonismPolicy variant expecting `ctx.memory` to be set. |

---

## 3. Dependency direction

Strict, enforced by review:

```
core/         -> stdlib + numpy + pydantic. No Mesa. No policies. No io. No metrics.
policies/     -> core/ only.
mesa_agents.py-> Mesa + core + policies.
model.py      -> Mesa + core + policies + metrics + io.
metrics/      -> core/events. No io.
io/           -> metrics + core/events.
experiments/  -> model + metrics + io.
viz/          -> core (read-only) + metrics (read-only).
tests/        -> may import anything.
```

**Why this matters:** the scientific core is portable, fast to test, and free of god-modules. Any Mesa upgrade affects only the adapter layer. Any IO change affects only `io/`.

---

## 4. The adapter rule (mesa_agents.py / model.py)

**These two files are adapters, not behavior.** When they land they must remain orchestration-only.

What adapters MAY do:
- Create wrappers
- Call `observe(...)`
- Call `policy.decide(...)`
- Call `apply_action(...)`
- Call `commit_delta(...)`
- Call `update_at(...)` for memory
- Emit events via blinker signals
- Queue births / process the birth queue
- Wire `DataCollector` snapshots
- Sync agent position with Mesa's grid

What adapters MUST NOT do:
- Implement new behavior logic
- Implement valence math (lives in `core/valence.py`)
- Implement trait generation or mutation (lives in `core/traits.py`)
- Implement memory update or decay rules (lives in `core/memory.py`)
- Implement reproduction validity or child construction (lives in `core/reproduction.py`)
- Implement action transitions (lives in `core/actions.py`)
- Implement world generation (lives in `core/world.py`)
- Decide which actions are valid (lives in `core/actions.get_valid_actions`)

If an adapter file starts to contain any of the forbidden categories above, **stop and refactor**. The right home is one of the existing `core/` or `policies/` modules, or a new one alongside them.

This rule replaces a mechanical line-count check (which would punish legitimate orchestration code or encourage worse patterns like splitting one messy file into several thin-but-messy files). Review the file's *content* against the lists above; line count is irrelevant.

---

## 5. How to add a new module

Checklist for any new file under `src/hedonism_harness/`:

1. **Pick the correct layer** (see §3). If unsure, the module probably belongs in `core/`.
2. **Confirm dependency direction.** A `core/` module may not import from any layer above it. Run `uv run ruff check .` — `I001` will catch import-order violations and a future import-linter rule will enforce layer boundaries.
3. **Module docstring** must state:
   - What the module owns (one paragraph).
   - Reference to the SPEC section it implements (e.g. "SPEC §13").
   - Any v0.1 simplifications (e.g. "memory inheritance deferred to v0.2 per §13.4").
4. **Dataclasses are frozen** unless mutation in place is required for performance (see `World`, `ValenceMemory`).
5. **Pure functions, no global RNG.** Functions that consume randomness take an `np.random.Generator` parameter explicitly.
6. **One test file per module.** `tests/test_{module}.py`. Cover both example tests and Hypothesis property tests for any function with a meaningful invariant.
7. **No print, no logging, no IO.** That belongs in `io/` (and currently does not exist for `core/` modules).
8. **No Mesa imports** in `core/` or `policies/`. Period.

---

## 6. Test layout

One test file per module under `src/hedonism_harness/`:

```
tests/
  conftest.py                        # Hypothesis profiles (dev / ci)
  test_simulation_determinism.py     # The v0.1 north-star tests
  test_world.py                      # 8 tests
  test_traits.py                     # 14 tests
  test_body.py                       # 23 tests
  test_actions.py                    # 20 tests
  test_sensors.py                    # 15 tests
  test_valence.py                    # 18 tests
  test_memory.py                     # 18 tests
  test_reproduction.py               # 24 tests
  test_policies.py                   # 14 tests
  test_rng.py                        # 4 tests
  test_config.py                     # 14 tests
```

Total: 175 unit/property tests + 1 cross-module smoke script in `scripts/core_smoke_test.py`.

Hypothesis profiles in `tests/conftest.py`:
- `dev` (default): 25 examples per property, 200ms deadline.
- `ci`: 200 examples per property, 1s deadline. Selected via `HYPOTHESIS_PROFILE=ci`.

---

## 7. The determinism north star

> Given the same seed, the same model config produces the same world, the same first N events, and the same final metrics.

This is the v0.1 success gate from SPEC §26.12. It is enforced by:

- `tests/test_simulation_determinism.py` (3 example + property tests at the world layer)
- `tests/test_rng.py` (4 tests on stream independence)
- Hypothesis property tests across `world`, `traits`, `valence`, and `body` (each verifying NaN-freedom + range invariants under any seed)
- `scripts/core_smoke_test.py` (end-to-end: same seed → same final hashed state across the full core loop)

Any change that breaks any of these breaks the project. Treat them as the load-bearing assertions.
