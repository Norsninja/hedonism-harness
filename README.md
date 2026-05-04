# Hedonism Harness

A 2D artificial-life experiment testing whether survival, exploration, paralysis, risk-taking, and reproduction can emerge from inherited pleasure/pain thresholds rather than handcrafted behavior rules.

The project models agents as embodied organisms with internal states, limited sensors, valence memory, and inherited traits. Agents are not told to seek food, flee danger, or explore. Instead, they evaluate possible actions through a pleasure/pain harness and reproduce with mutated thresholds.

## Core Question

Can different tolerances to hunger, fear, pain, novelty, pleasure, and uncertainty produce distinct survival strategies over generations?

## v0.1 Experiment

The first canonical experiment is the **Fear-Hunger Conflict Chamber**:

- Agent starts in a safe but food-poor zone.
- Food exists beyond a hazardous region.
- Hunger pain rises over time.
- Fear rises near danger.
- The experiment observes when hunger overcomes paralysis, which trait profiles survive, and which reproduce.

## Status

Early scaffolding. See [`docs/SPEC.md`](docs/SPEC.md) for the full specification.

## Architecture

- **Mesa 3.x** as the agent-based-modeling backbone.
- **Pydantic v2** for composed configuration.
- **NumPy** for vectorized world state via Mesa `PropertyLayer`.
- **Blinker** for typed event signals between core and metrics/io layers.
- **Hypothesis** for property-based testing of valence, mutation, and determinism invariants.

Strict layering: `core/` emits events, `metrics/` interprets, `io/` persists. The scientific core (`core/` + `policies/`) has no dependency on Mesa, Pandas, or persistence — keeping the experiment portable, fast to test, and free of god-modules.

See [`docs/SPEC.md` §27](docs/SPEC.md) for the authoritative architecture and dependency rules.

## Development

```sh
just install            # uv sync with dev extras
just test               # run pytest
just test-determinism   # run only determinism-tagged tests
just smoke              # run scripts/core_smoke_test.py end-to-end
just lint               # ruff check
just format             # ruff format
just fix                # ruff check --fix && ruff format
just ci                 # the exact sequence CI runs locally
just precommit-install  # install git hooks
```

The smoke test (`scripts/core_smoke_test.py`) is the gate that proves the Mesa-free core loop coheres end-to-end: build world → create body → assign traits → observe → choose action → apply action → commit delta → update memory → emit events → repeat → same seed reproduces same final state. It runs in CI after pytest.

### Cloud workflow

This project is set up to run entirely from the cloud:

- **GitHub Codespaces** — open the repo on GitHub → `Code` → `Codespaces` → `Create codespace on <branch>`. The devcontainer (`.devcontainer/devcontainer.json`) installs uv, syncs dependencies, and configures VS Code with Ruff + pytest. After ~90 seconds you can run `just test` in the integrated terminal.
- **GitHub Actions** — every push triggers `.github/workflows/ci.yml`, which runs lint, format check, and the full test suite under the thorough Hypothesis profile (`HYPOTHESIS_PROFILE=ci`). Once the simulation produces `runs/{run_id}/` outputs (post-Mesa), they upload as workflow artifacts retrievable from the PR Checks tab.

You do not need a local Python environment to develop or test this project.

## Determinism Promise

> Given the same seed, the same model config produces the same world, the same first N events, and the same final metrics.

This is the v0.1 north star. Every change is gated on it.
