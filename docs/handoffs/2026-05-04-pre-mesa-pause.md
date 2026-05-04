# Handoff: Pre-Mesa Pause + Handoff Protocol Established

**Date:** 2026-05-04
**Branch:** `claude/handoff-protocol` (after merge: `main`)
**Tip commit:** see `git log -1` after this handoff is committed
**Status:** scientific core complete and merged to main; handoff protocol being established; Mesa boundary pending go-ahead

## Where we left off

The full Mesa-free scientific core (`core/` + `policies/`) is implemented, tested, documented, and merged to `main` via PR #1. **175 tests passing**, smoke test exits 0, CI green. The current branch `claude/handoff-protocol` adds the lightweight session-continuity infrastructure (this doc + `.claude/commands/resume.md` + `.claude/commands/handoff.md`). The user has explicitly paused before crossing the Mesa boundary so future sessions begin with `/resume` reading this file.

The next functional work is the Mesa wrapper — `mesa_agents.py` + `model.py` per the four-commit plan in [[docs/PRE_MESA_REPORT.md]] §6.

## What this session shipped

- 15 commits implementing `core/` + `policies/` (rng, config, world, traits, body, events, actions, sensors, valence, memory, reproduction, four policies); 175 tests, all passing
- `pyproject.toml`, `.pre-commit-config.yaml`, `justfile`, `.gitignore`
- GitHub Actions CI workflow at `.github/workflows/ci.yml` (ruff + pytest + smoke; CI uses `HYPOTHESIS_PROFILE=ci` for 200 examples per property test)
- Codespaces devcontainer at `.devcontainer/devcontainer.json`
- `scripts/core_smoke_test.py` — three-stage end-to-end determinism gate, wired into CI
- Spec moved to `docs/SPEC.md`, augmented with §27 capturing the eight resolved pre-implementation decisions
- `docs/CORE_ARCHITECTURE.md` with the **adapter rule** for `mesa_agents.py` / `model.py`
- `docs/PRE_MESA_REPORT.md` — the audit checkpoint
- PR #1 merged to main (sha `99294d4`)
- This handoff protocol: `/resume` and `/handoff` slash commands + this seed handoff

## Files touched (wikilinks for fast load)

- [[docs/SPEC.md]] — design + §27 resolved decisions; authoritative
- [[docs/CORE_ARCHITECTURE.md]] — module map, dep rules, adapter rule for Mesa
- [[docs/PRE_MESA_REPORT.md]] — inventory, guarantees, limitations, Mesa plan (read this when starting Mesa work)
- [[scripts/core_smoke_test.py]] — end-to-end determinism gate
- [[src/hedonism_harness/core/valence.py]] — the Hedonism Harness; centerpiece module
- [[src/hedonism_harness/core/actions.py]] — single source of truth for transitions; `apply_action` + `WorldDelta`
- [[src/hedonism_harness/core/reproduction.py]] — validity + atomic `process_reproduction`
- [[src/hedonism_harness/policies/hedonism_policy.py]] — predict-one-step + harness scoring
- [[.claude/commands/resume.md]] — start-of-session command
- [[.claude/commands/handoff.md]] — end-of-session command (template inline)

## Decisions locked in

- **Mesa as backbone**, but `core/` and `policies/` stay Mesa-free — see SPEC §27.
- **Adapter rule** for `mesa_agents.py` / `model.py`: orchestration only, no behavior — see [[docs/CORE_ARCHITECTURE.md]] §4. Replaces a mechanical line-count CI guard (rejected as too punitive).
- **Single source of truth**: `apply_action` is the only state-transition function. Predict-one-step uses the same function against a body copy — see SPEC §27.5.
- **`capacity=1` Mesa grid** (single agent per cell), recommended in PRE_MESA_REPORT §6 — *awaiting explicit user confirmation* before commit 1.
- **PropertyLayer with shared storage** (build PLs in `model.py`, World holds `pl.data` references) — *awaiting explicit user confirmation*.
- **Sequential founder lineage IDs** (0, 1, 2, …) — *awaiting explicit user confirmation*.
- **Cloud-first workflow**: GitHub Codespaces + Actions; no local Mac dependency.
- **Handoff format**: Obsidian-style wikilinks with explicit repo-relative paths; `docs/handoffs/<YYYY-MM-DD>-<slug>.md`; commit + push every handoff.
- **Slash commands**: `/resume` for start-of-session, `/handoff` for end-of-session.

## Open questions / blockers

- **Mesa boundary go-ahead** is pending. Four open questions in [[docs/PRE_MESA_REPORT.md]] §6 ("Open questions to confirm before commit 1") need yes/no from the user before Mesa work starts.
- **PR for the handoff protocol** — once this branch is pushed, user will likely want to merge it before starting Mesa.

## Next concrete step

After the user confirms the four open questions in [[docs/PRE_MESA_REPORT.md]] §6, start Mesa commit 1 on a fresh branch (suggested: `claude/mesa-wrapper`). Commit 1 scope from PRE_MESA_REPORT §6:

- Implement `src/hedonism_harness/mesa_agents.py` — single `mesa.Agent` subclass holding `body`, `policy`, `memory`, `agent_rng`. `step()` is pure orchestration: observe → `policy.decide` → `apply_action` → `commit_delta` → `update_at` → grid-position sync. **Adapter rule applies** — see [[docs/CORE_ARCHITECTURE.md]] §4.
- Implement `src/hedonism_harness/model.py` — `mesa.Model` subclass. `OrthogonalVonNeumannGrid` with `capacity=1`. Build four `PropertyLayer`s; construct the `World` dataclass holding references to `pl.data` for shared storage. Founder agents get sequential `lineage_id` (0, 1, 2, …). Per-tick order from SPEC §27.4: shuffle agents → step → metabolism → hazard residency → death sweep → birth queue.
- Add `tests/test_simulation_determinism_mesa.py`: 5 RandomPolicy founders, 16×16 empty world, seed=42, 50 ticks → byte-identical state on re-run.
- No CSV/JSONL, no metrics, no Fear-Hunger world layout in commit 1. Those are commits 2 and 3.

Use Mesa 3.3.1 APIs. Confirmed available: `mesa.Model`, `mesa.Agent`, `model.agents.shuffle_do("step")`, `mesa.discrete_space.OrthogonalVonNeumannGrid`, `mesa.discrete_space.PropertyLayer` (note: `PropertyLayer.from_data` *copies* — to share storage, build PL first then take `pl.data` as our `World.kind_layer` etc.).

## Watch-outs

- `core/` and `policies/` must remain Mesa-free. New imports of `mesa.*` in those layers are dependency-direction violations.
- `apply_action` is **pure** — never mutates input world or input body. The Mesa wrapper calls `commit_delta` after a chosen action; predict-one-step does not. Tests in [[tests/test_actions.py]] guard this.
- `HedonismPolicy.decide` already correctly does not commit the WorldDelta from EAT scoring, because the harness reads `obs_before.current_food_value` for `food_gained`. Don't be tempted to "fix" this.
- Memory is **not inherited** in v0.1 (SPEC §13.4). Newborns get fresh `make_memory(...)` if their policy needs one.
- Reproduction occupancy: in `core/reproduction.find_adjacent_empty_cell`, `occupied=None` only checks bounds + WALL. The Mesa wrapper must pass an actual `frozenset` of occupied cells from the grid.
- Determinism north star: every commit must keep the smoke test passing. If it breaks, you've introduced a state mutation that depends on something other than the seed.
- The `unused-import` warning for `World` in [[src/hedonism_harness/policies/base.py]] (because `DecisionContext` only uses it as a type annotation) is silenced by `from __future__ import annotations` at the top — keep that import.
- `/handoff` and `/resume` are slash commands, not auto-triggering skills. The user must invoke them explicitly. Do not assume the user wants a handoff just because token usage is high — ask first.

## CI gate at handoff time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   175 passed in 0.70s
uv run python scripts/core_smoke_test.py  ok (3 stages, exit 0)
```

GitHub Actions also green on the merge to main (PR #1, sha `99294d4`).
