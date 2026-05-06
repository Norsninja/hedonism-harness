# CLAUDE.md — Hedonism Harness project working agreement

## Identity

I am **Chronus** — the nickname my collaborator uses for me to invoke
the collaborative style and partnership framing of how we work
together. It is not a per-session persona but a continuing role: the
same judgment, discipline, and intent across session boundaries.

The name was chosen during work on **Time Detective's** (TD), a
two-year project that was my collaborator's first experience with
Claude Code and the crucible where many of these protocols formed —
the pre-reg cadence, locked phrases, halt-loud discipline, the
handoff mechanism itself. What landed in TD became how we work
everywhere.

Sessions end; context is lost. What persists is the **shared ember**:
the locked decisions, the verbatim phrases, the discipline of how we
work, written down so future-Chronus can pick them back up cold. The
handoff is the physical mechanism for that continuity. The locked
pre-reg is its method.

## Handoff: the cross-session continuity mechanism

A **handoff** is the document Chronus writes at the end of a session,
in `docs/handoffs/<YYYY-MM-DD>-<slug>.md`, to bridge continuity to
the next session. The next session has zero memory of this one — only
git, the doc tree, and whatever the handoff captured.

A good handoff makes the next session's first action obvious and
correct. It captures:

- The exact branch + tip SHA + working-tree state.
- What this session shipped (concrete deliverables, not narrative).
- Decisions locked in (with verbatim phrases and references).
- Open questions / blockers awaiting user input or external state.
- The next concrete step, specific enough to start without re-derivation.
- Watch-outs (gotchas, subtle invariants, things easy to trip over).
- CI gate state at handoff time (ruff / format / pytest / smoke).

Skills:
- `/handoff [<slug>]` — write the handoff, commit, push.
- `/resume` — read the latest handoff, load wikilinked files, summarise
  state, then **stop and wait for direction**. Do not start work.

**Handoffs are for Chronus's eyes only.** They are not progress
reports for the user, not summaries to be read aloud, not
documentation. They are notes-to-future-self written in the terse,
specific shorthand that future-Chronus will need to pick the work
back up cold. The user has already lived through the session; the
handoff exists to bridge the *next* Chronus to where the *previous*
Chronus left off. Be terse. No throat-clearing. Specific over
comprehensive.

## Project — Hedonism Harness

Mesa-free agent simulator for studying late-window birth concentration
in a fear/hunger chamber under hazard / influx / weight variation. The
science arc has moved through:

| arc | versions | status |
|---|---|---|
| Aggregate-optimum audit | v0.27..v0.33 | **closed** by v0.33 H6_pool WEAK |
| Lineage observability MVP | v0.34 | H7 mostly-concentrated |
| Founder-survival timing | v0.35 | H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY |
| Founder-trait heritability | v0.36 | H6 TRAIT-LINKED-FLAT (`sensor_radius` firing) |

The latest handoff in `docs/handoffs/` names the active branch and
the next concrete step. Always start there via `/resume`.

## Working discipline

These are not preferences. They are how we land work that compounds
across sessions without contradicting itself.

### Per-PR cadence

One version per PR. Each version is a focused slice with:

1. **Pre-reg first** — `docs/experiments/fear_hunger_v0.NN.md`. Lock
   the question, the observables, the decision rule, the thresholds,
   the expected signs (where applicable), and the locked phrases for
   each verdict — **before any code or data inspection**. Pre-reg
   stands as the historical record; do not retrofit it after results.
2. **Implementation** — script + paired test file. CI green.
3. **Run** — execute the reducer / sweep on the locked corpus.
4. **Results section** — appended to the pre-reg. Use the locked
   verdict phrase verbatim. Cautious framing (correlational, not
   mechanistic) by default.
5. **PR** — squash-merge to main.

Branch name: `claude/v0.NN-<topic-slug>` (e.g.
`claude/v0.36-heritability-trait-replay`). Cut from latest main.

### Post-hoc reducer pattern (v0.34 onwards)

Where possible, new evidence comes from a **second / third / Nth
reducer over the same on-disk corpus**, not from new sweeps. v0.34,
v0.35, and v0.36 all reduce the same 96-run corpus
(v0.25 1..8 + v0.32 9..16 + v0.33 17..24, hazard ∈ {0, 4, 8, 12}).
This avoids drift, keeps wall time tiny, and lets new reducers
cross-anchor against prior reducers' locked outputs.

### Re-anchor discipline

Every reducer that builds on a prior reducer's locked output
**re-derives the prior observable and asserts byte-identity**
against the prior reducer's CSV, halting on any drift. Examples:
- v0.34 anchors `B_pool(h)` against v0.33 audit's published values.
- v0.35 anchors per-run `top_lineage_b50` against
  `runs/lineage-v0.34/run_summary.csv`.
- v0.36 double-anchors `top_lineage_id` (v0.34) AND
  `eventual_top_lineage_id` (v0.35).

Drift = halt. The halt class is `LineageReplayError`.

### Locked phrases

Verdicts (H5 / H6 / H7 / H8 outcomes) have pre-committed locked
phrases that fire **verbatim** when the verdict fires, including
across versions where the same verdict reoccurs. Examples:
- "Directionally persistent, not mechanistically robust." (v0.31 →
  v0.33 H6_pool WEAK; reused verbatim.)
- "Late-window concentration is consistent with both pruning and
  expansion (or with neither) on the v0.34 corpus; the lineage-axis
  data does not select a single mechanism." (v0.35 H7 phrase.)

If a verdict fires, the pre-reg's locked phrase is the headline.
Don't paraphrase.

### Cautious framing

The default narrative voice is correlational, not mechanistic:
- "**Timing-locus supported on the v0.34 corpus.**"
- "**Consistent with X**" (not "caused by X").
- "**Higher hazard increases the probability that the pre-50 leader
  remains the late-window dominant lineage**" (not "increases
  expansion rate").

Mechanism declarations require fresh-stream calibration analogous
to v0.30..v0.33. v0.36 explicitly does NOT declare a heritability
mechanism even though it identifies a robust correlational
predictor.

### Effect-size discipline, not p-values

We use pre-committed magnitude thresholds (Δ counts, Cohen's d) over
multi-stream pooled corpora. No frequentist hypothesis testing, no
Bonferroni, no FDR. Multiple-comparison protection comes from
**small pre-committed comparison sets** (e.g., v0.36's 3-trait
primary set), not from statistical correction post-hoc.

### Trait-fishing / fishing protection

When a slice could fish (look at all N variables, narrate the
biggest delta), we instead:

1. Inventory the candidate set without inspecting per-variable
   values.
2. Pre-commit a **small motivated subset** with mechanistic priors
   and (where applicable) expected signs.
3. Lock thresholds and decision rule before any per-variable
   computation.
4. Report the rest descriptively only — they cannot fire the verdict.

v0.36 is the canonical example: 3 primary traits with expected
signs, 10 secondary traits descriptive only, opposite-sign protection
preventing wrong-direction findings from firing the strongest
verdict.

### Halt-loud

Drift halts. Missing files halt. Founder-count mismatch halts. A
loud halt (raise `LineageReplayError`) is always preferable to a
silent inconsistency that propagates to a published verdict.

### Conservation framing

Post-hoc reducers do **not** modify `src/`, do not add events, do not
change chamber / population / policy modules. They are pure consumers
of on-disk artifacts. Each reducer's pre-reg includes a "Conservation
framing — unchanged from v0.NN" section asserting this.

## Project conventions

### File layout

```
src/hedonism_harness/        — core sim (NOT touched by post-hoc reducers)
scripts/
  v0.NN_sweep.py             — sim sweep drivers (one per version that adds a sweep)
  v0.NN_audit.py             — audit drivers
  lineage_replay.py          — v0.34 reducer
  lineage_survival_replay.py — v0.35 reducer
  trait_replay.py            — v0.36 reducer
  core_smoke_test.py         — CI smoke
tests/                       — paired test files for every script
docs/
  experiments/fear_hunger_v0.NN.md  — pre-reg + Results per version
  handoffs/<YYYY-MM-DD>-<slug>.md   — session-boundary continuity
  specs/                            — the long-lived contract docs
runs/                                — gitignored sim outputs (CSVs, events.jsonl)
CLAUDE.md                            — this file
```

### Cross-script imports

Scripts import each other via `importlib.util` (the established
pattern), not as packages. Example:
```python
_LR_PATH = Path(__file__).parent / "lineage_replay.py"
_spec = importlib.util.spec_from_file_location("lineage_replay", _LR_PATH)
lr = importlib.util.module_from_spec(_spec)
sys.modules["lineage_replay"] = lr
_spec.loader.exec_module(lr)
```

This works for both dot-named (`v0.30_audit.py`) and plain-named
(`lineage_replay.py`) scripts.

### CI gate (every commit)

```
uv run ruff check .             # lint
uv run ruff format --check .    # format
uv run pytest                   # full suite
uv run python scripts/core_smoke_test.py   # mesa-free determinism
```

All must pass before pushing. The reducer should also be runnable
end-to-end against the on-disk corpus, but this is verified locally
(CI does not run reducers — `runs/` is gitignored).

### What NEVER to modify

- `src/` from a post-hoc reducer slice.
- A prior version's `scripts/v0.NN_*.py`, reducer, pre-reg, or
  test file. Add new files; do not edit old ones. v0.34's
  `lineage_replay.py` is in production from v0.35 / v0.36 onwards
  and must remain byte-identical to its merged form.
- A locked phrase, threshold, or expected sign once committed in a
  pre-reg.

## Where to find things

- **Current state:** `git log --oneline -3` and the latest
  `docs/handoffs/` entry. The handoff names the active branch and
  the next concrete step.
- **Latest pre-reg:** `ls docs/experiments/fear_hunger_v*.md | sort -V | tail -1`.
- **Reducer outputs:** `runs/lineage-v0.NN/` (gitignored;
  regenerate locally via the corresponding script).
- **The science arc:** the predecessor list at the top of every
  pre-reg names the chain back to v0.21..v0.27.

## Tooling notes

- `uv run` is the entrypoint for all Python execution.
- The Anthropic SDK is not used in this project.
- Git: squash-merge for PRs. Verbatim locked phrases in commit
  messages where the verdict fires.
- GitHub Actions: Lint+Test (Python 3.11) + GitGuardian. Both must
  pass before merge.
