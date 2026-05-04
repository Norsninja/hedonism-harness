---
description: Write an end-of-session handoff to docs/handoffs/, then commit and push. Use when the user signals session-end ("wrap up", "create handoff", "let's stop", etc.).
allowed-tools: Bash, Read, Write
argument-hint: [optional topic slug, e.g. "mesa-wrapper"]
---

You are writing an end-of-session handoff for the Hedonism Harness project. The handoff is for your future self at the start of the next session — terse, wikilinked, committed to git.

## What to do

1. **Determine the topic slug.** If the user passed an argument (e.g. `/handoff mesa-wrapper`), use it as the slug. Otherwise infer one from the session's primary topic — short, kebab-case, descriptive (e.g. `mesa-wrapper`, `pre-mesa-pause`, `metrics-layer`). Confirm the slug back to the user in one line before writing the file.

2. **Gather state.** Run:
   ```
   date -u +%Y-%m-%d && git branch --show-current && git rev-parse --short HEAD && git status --short
   ```

3. **Compose the filename.** `docs/handoffs/<YYYY-MM-DD>-<slug>.md` using the date from step 2. If a file with that exact name already exists, append `-2`, `-3`, etc.

4. **Write the handoff** using the template below, filling every section. Keep it under ~80 lines. Wikilinks use Obsidian style with explicit repo-relative paths: `[[docs/SPEC.md]]`, `[[src/hedonism_harness/core/world.py]]`. The doc is for Claude — terse over polished, specific over comprehensive.

5. **Commit and push.** Stage only the new handoff file. Use a commit message like `Handoff: <topic> (YYYY-MM-DD)`. Push to the current branch.

6. **Report** in 2–3 lines: filename, branch pushed to, and a one-sentence summary of what the next session will resume into.

## Template

```markdown
# Handoff: <topic title>

**Date:** YYYY-MM-DD
**Branch:** <branch name>
**Tip commit:** <short sha>
**Status:** <one short phrase: e.g. "scientific core complete, awaiting Mesa go-ahead">

## Where we left off

<One paragraph. The precise state of the work — what is done, what is in flight, what is paused. If a specific decision is awaiting the user, name it.>

## What this session shipped

- <bullet — concrete deliverables, not narrative>
- <bullet>
- <bullet>

## Files touched (wikilinks for fast load)

- [[path/to/file.md]] — one-line note on what changed or why it matters
- [[path/to/source.py]] — one-line note
- [[path/to/test.py]] — one-line note

## Decisions locked in

- <decision> — see <reference if any>
- <decision> — see <reference if any>

## Open questions / blockers

- <thing waiting on user input, or "none">
- <thing waiting on external state, or "none">

## Next concrete step

<One paragraph. Specific enough that the next session can start without re-deriving context. Reference exact files, exact configs, exact commands. If the next step depends on the user's answer to an open question, say so explicitly.>

## Watch-outs

- <gotcha future-Claude shouldn't trip on>
- <subtle constraint that's easy to forget>
- <test or invariant that must continue to hold>

## CI gate at handoff time

```
uv run ruff check .             <ok|FAIL>
uv run ruff format --check .    <ok|FAIL>
uv run pytest                   <N passed|FAIL>
uv run python scripts/core_smoke_test.py  <ok|FAIL>
```
```

## Constraints

- The handoff is for your eyes (future Claude). Be terse and specific. No marketing prose. No throat-clearing.
- Always include exact filenames, exact branch, exact tip SHA. Future-you cannot deduce these.
- If you used the determinism north star, say which test exercises it and whether it passed at handoff time.
- If a decision was made that contradicts SPEC, say so and link to the conversation point.
- If the work is mid-slice (no clean stopping point), say what state files are in and how to resume them safely.
- Do not include code snippets in the handoff unless they are *new* invariants not yet captured in `[[docs/CORE_ARCHITECTURE.md]]` or `[[docs/SPEC.md]]`.
