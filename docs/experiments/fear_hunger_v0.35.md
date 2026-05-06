# v0.35 — founder survival timing and lineage pruning replay

**Status:** pre-registered 2026-05-06; reducer + sweep not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.35-lineage-pruning-founder-survival`
**Predecessors:** v0.21..v0.27 (chamber x hazard x influx x weight
characterisation, aggregate-optimum audit phase), v0.28 -> v0.29 ->
v0.30 -> v0.31 (weight-axis calibration, **H7_pool FAILURE** at v0.31),
v0.32 -> v0.33 (hazard-axis calibration, **H6_pool WEAK** at v0.33;
locked phrase: "Directionally persistent, not mechanistically robust"),
v0.34 (lineage observability MVP — **H7 mostly-concentrated** at h=8 of
the v0.33 24-seed pool; secondary post-hoc observation: dominance rises
monotonically with hazard).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.34 fired **H7 mostly-concentrated** on the v0.33 pooled corpus at
h=8 (mean `top_lineage_b50_share` = 0.759, 22/24 single-lineage majority,
8/24 single-lineage monopoly). The headline lineage-axis finding was
that the +9/+9 aggregate-level h=8 advantage from v0.33 is per-seed
**dynasty volatility under aggregate stability** — at any given seed
one lineage typically owns most of the late-window births, but which
lineage varies seed-to-seed.

v0.34 also surfaced a **secondary observation** (NOT pre-committed,
post-hoc): mean `top_lineage_b50_share` rises monotonically with hazard
across the 96-run corpus.

| hazard | mean top_lineage_b50_share | n_majority (>=0.5) / 24 |
|-------:|---------------------------:|------------------------:|
| 0      | 0.635 | (per v0.34 Results)     |
| 4      | 0.728 |                         |
| 8      | 0.759 | 22/24                   |
| 12     | 0.785 |                         |

That is the motivating prior for v0.35. v0.34's lineage lens cannot
distinguish two competing mechanisms for that monotone trend; v0.35
exists to do so. The active question is:

> **Does increasing hazard concentrate late-window productivity by
> reducing founder-line survival before tick 50 (pruning-driven), or
> by allowing one surviving lineage to expand after tick 50
> (expansion-driven)?**

This is a **targeted post-hoc follow-up** on the v0.34 secondary
observation. It is NOT a heritability slice, NOT a Gini slice, NOT a
sim-mechanics change, NOT a HedonismPolicy comparison, and does NOT
involve any new sweep. v0.35 stays post-hoc one more step.

### Why both indicators rather than a single test

The mechanisms are not mutually exclusive. A clean pre-registration must
be able to fire **PRUNING-SUPPORTED**, **EXPANSION-SUPPORTED**, or
**MIXED-OR-UNRESOLVED** without forcing a choice when the data is
genuinely ambiguous. The three-way verdict is locked below.

### Why this closes the lineage-observability follow-up arc

v0.34 was the lineage MVP; v0.35 is the targeted causal-fork follow-up.
After v0.35, the lineage-axis arc reaches a natural pause point. Whether
the next slice is a heritability lens (v0.36+) or a HedonismPolicy
comparison or a different chamber depends on v0.35's verdict — locked
in the per-verdict v0.36+ candidate table below, not pre-committed
beyond it.

## What this slice tests, and what it does NOT test

### Tests

- Whether **founder-line survival at tick 50** declines monotonically
  with hazard across the v0.34 96-run corpus.
- Whether **`winner_already_dominant_at_tick_50` rate** rises
  monotonically with hazard across the v0.34 96-run corpus.
- Whether the joint pattern fires PRUNING-SUPPORTED, EXPANSION-SUPPORTED,
  or MIXED-OR-UNRESOLVED under the pre-committed three-way rule.
- Per-run `top_lineage_b50` re-anchoring against v0.34's
  `run_summary.csv` (byte-identical for each (source_version, arm_label,
  seed); drift halts).
- Substrate-byte-identity: the v0.34 reducer is imported from
  [[scripts/lineage_replay.py]] without modification.

### Does NOT test

- Heritability. Whether the dominant lineage shares systematic traits
  with its founder is **out of scope**. Gated to v0.36+.
- Gini / inequality coefficients beyond v0.34's `top_lineage_b50_share`
  (which is consumed only for the re-anchor cross-check, not as a v0.35
  primary observable).
- HedonismPolicy comparisons. Deferred until v0.35 lands.
- Mesa migration. Deferred indefinitely; the post-hoc reducer pattern
  closes the case for staying on the current core.
- Mechanism declaration. Even a clean PRUNING-SUPPORTED or
  EXPANSION-SUPPORTED verdict at n=96 does **not** declare a robust
  mechanism — it identifies which of two candidate stories the
  lineage-axis data is consistent with. Promotion to a mechanism would
  require a fresh-stream calibration analogous to v0.30..v0.33.
- New sweeps. Zero new simulator runs. Zero edits to any
  `scripts/v0.NN_*.py`. Zero edits to `src/` (no in-sim observability
  required).
- Trait-level analysis. `trait_fingerprints.csv` is on disk per-run but
  is **not consumed** by v0.35. Reserved for v0.36+.
- Events.jsonl parsing. v0.34 set the precedent of zero events parsing
  for the lineage lens; v0.35 keeps that.
- Hazards outside {0, 4, 8, 12} or other influxes. Same 96-run corpus
  as v0.34.

### Deferred (v0.36+ candidates, conditional on v0.35 outcome)

Independent of the v0.35 verdict, v0.36 is the canonical next slice
for **heritability** — adding parent-trait inheritance observables on
top of the existing lineage substrate. v0.35's verdict shapes the
v0.36 framing but does not reroute it:

- **If PRUNING-SUPPORTED fires.** Headline: hazard concentrates
  late-window dominance via differential founder-line survival. v0.36
  heritability lens asks whether *which* founders survive at high
  hazard correlates with a heritable trait (e.g., hazard avoidance
  proclivity).
- **If EXPANSION-SUPPORTED fires.** Headline: hazard concentrates
  late-window dominance by amplifying the early leader. v0.36
  heritability lens asks whether the eventual winner's lineage carries
  a heritable trait that explains the post-50 expansion advantage.
- **If MIXED-OR-UNRESOLVED fires.** No directional headline. v0.36
  heritability lens proceeds as the canonical follow-up regardless,
  but with framing "lineage observability identified concentration but
  not its temporal locus."

## Conservation framing — unchanged from v0.20..v0.34

No new conservation contract. No mutations to `world.py` / `body.py` /
`model.py` / `gradient_policy.py` / `fear_hunger_chamber.py` /
`population_dynamics.py`. No mutations to existing arm tuples. No new
event types, no new chamber, no new policy. Source modifications are
**zero**. v0.35 is a second post-hoc reducer that imports v0.34's
helpers additively and writes new CSVs under a new output directory.

## Mechanism

v0.35 is one new script plus one new tests file plus this doc. No
sweep driver: the corpus already exists on disk from v0.25 / v0.32 /
v0.33.

1. **Reducer** ([[scripts/lineage_survival_replay.py]]). Imports v0.34
   helpers from [[scripts/lineage_replay.py]] via the established
   `importlib.util` pattern (hyphen-named scripts):
   - `STREAM_CONFIGS` — the 3-stream × 8-seed × 4-hazard corpus
     descriptor.
   - `parse_agent_lifetimes`, `parse_config`, `parse_manifest` —
     per-run sidecar parsers.
   - `assign_founder_lineages`, `compute_generation_depths` —
     lineage-id assignment + BFS over parent_id edges.
   - `LineageReplayError` — halt class.
   - `EXPECTED_FOUNDERS = 5`, `B50_THRESHOLD_TICK = 50`,
     `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` — re-imported as
     constants for cross-check assertions.

   Pure-function pipeline (parallel to v0.34's structure):
   - `compute_founder_active_at_tick(agents, lineage_id, tick, n_ticks)`
     — bool. True iff there exists an agent in the lineage with
     `birth_tick_normalized <= tick` AND
     `(death_tick is None AND tick < n_ticks) OR (death_tick is not None
     AND tick < death_tick)`. Pre-committed semantics; see "Snapshot
     tick semantics" below.
   - `compute_extinction_tick(agents, lineage_id, n_ticks)` — int |
     None. Returns `max(death_tick)` over lineage members iff every
     member has a non-null `death_tick` (lineage extinct within
     window); else None (lineage extant beyond `n_ticks`). Note: a
     lineage with all members dead by tick T but a descendant born
     after T cannot occur by definition (descendants are born to live
     parents); the `max(death_tick)` is a clean reduction.
   - `compute_births_so_far(agents, lineage_id, tick)` — int. Count of
     lineage members with `birth_tick_normalized <= tick`. Founders
     contribute 1 each (their `birth_tick_normalized` is 0 by v0.34
     convention).
   - `compute_leader_at_tick_50(agents, lineage_ids, n_lineages)` —
     int (lineage_id). The lineage with the highest `births_so_far`
     at tick 50, with **lowest lineage_id as tie-break** (locked).
   - `compute_eventual_top_lineage(agents, lineage_ids, n_lineages,
     b50_threshold_tick=50)` — int. The lineage with the highest count
     of members with `birth_tick_normalized > 50`, with **lowest
     lineage_id as tie-break** (locked, mirrors v0.34).
   - `compute_winner_already_dominant_at_tick_50(leader, eventual_top)`
     — bool. `leader == eventual_top`.
   - `summarise_run(agents, run_meta)` — produces three per-run
     records: a list of `FounderTimelineRow` (one per (lineage,
     snapshot_tick)), a list of `FounderExtinctionRow` (one per
     lineage), and a single `PrePostDominanceRow`.
   - `aggregate_pruning_summary(per_run_records, by_hazard)` —
     produces one `PruningSummaryRow` per hazard.
   - `cross_check_top_lineage_b50_against_v0_34(rows, v0_34_path)` —
     halts on byte-mismatch per (source_version, arm_label, seed).
   - `evaluate_three_way_verdict(pruning_summary)` — returns one of
     `"PRUNING-SUPPORTED"`, `"EXPANSION-SUPPORTED"`,
     `"MIXED-OR-UNRESOLVED"` per the locked rule below.

   Outputs four CSVs under `runs/lineage-v0.35/` (gitignored under
   `runs/`):
   - `founder_timeline.csv` — per-run × founder × snapshot tick.
   - `founder_extinction.csv` — per-run × founder.
   - `pre_post_dominance.csv` — per-run.
   - `pruning_summary.csv` — per-hazard aggregate + verdict.

2. **Snapshot tick set** (locked):
   ```
   SNAPSHOT_TICKS = (0, 25, 50, 75, 100, 150, 200)
   ```
   Tick 0 is included as an invariant check
   (`founders_alive_at_t0 == 5` by construction; halts if any run
   violates). Decision-rule input is **tick 50 only**; the other six
   snapshots feed `pruning_summary.csv` for descriptive shape and feed
   `founder_timeline.csv` for per-run inspection but do not enter the
   verdict.

3. **Snapshot tick semantics** (locked, pre-committed before code):
   A founder lineage is **active at tick T** iff there exists an agent
   in the lineage satisfying:
   ```
   birth_tick_normalized <= T AND
   ((death_tick is None AND T < n_ticks) OR
    (death_tick is not None AND T < death_tick))
   ```
   Equivalently: an agent contributes to "active at T" iff T lies in
   the half-open interval `[birth_tick_normalized, death_tick or
   n_ticks)`. T == death_tick means the agent has just died; not
   active. T == birth_tick_normalized means the agent has just been
   born; active.

4. **Tie-break rule** (locked, mirrors v0.34): For every "lineage
   selection by maximum count" operation, ties are broken by **lowest
   lineage_id**. This applies to:
   - `compute_leader_at_tick_50` (max births_so_far at T=50).
   - `compute_eventual_top_lineage` (max b50 count, T > 50).
   - Any other max-by-count selection introduced by v0.35.

5. **Re-anchor cross-check** (locked, halts): The reducer recomputes
   `top_lineage_b50` per run using the same algorithm as v0.34
   (lineage with max count of members with `birth_tick_normalized > 50`,
   lowest lineage_id wins ties). The recomputed value MUST equal
   v0.34's `runs/lineage-v0.34/run_summary.csv:top_lineage_b50` for
   every `(source_version, arm_label, seed)` triple. Any mismatch
   halts via `LineageReplayError`. This is the v0.35 analog of
   v0.34's `cross_check_b50_anchors` (which itself halts on drift
   from `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}`).

6. **B_pool anchor cross-check** (locked, halts): v0.34's
   `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` are re-asserted at
   v0.35 reducer entry as a sanity check on the imported v0.34
   surface. Drift halts.

### Determinism — anchors

- v0.21..v0.34 events.jsonl artifacts on disk are not regenerated.
  Sidecars (`agent_lifetimes.csv`, `config.json`, `manifest.json`)
  are read verbatim.
- v0.21..v0.34 test suites continue to pass (additive guard).
- [[scripts/lineage_replay.py]] is **imported, not modified**.
- Re-anchor against v0.34's `run_summary.csv:top_lineage_b50` (96
  runs); halt on any drift.

### Wall time estimate

- Reducer: < 5s on the same 96-run corpus v0.34 reduced. (v0.34's
  full reducer runs in < 5s; v0.35 is a second pass over the same
  in-memory `AgentRow` set with additional per-tick / per-lineage
  reductions.)

## Observables — pre-committed before reading the data

### Per-run

- `founders_alive_at_T` for T in `SNAPSHOT_TICKS` — int in [0, 5].
- `extinction_tick(lineage)` for lineage in {0, 1, 2, 3, 4} — int |
  None.
- `births_so_far_at_50(lineage)` — int >= 1 for surviving founders;
  >= 0 (== 0 impossible since founder counts as a birth at tick 0).
- `b50(lineage) = |{agent in lineage : birth_tick_normalized > 50}|`
  — int >= 0.
- `leader_at_tick_50` — lineage_id in {0..4}.
- `eventual_top_lineage` — lineage_id in {0..4}.
- `winner_already_dominant_at_tick_50` — bool.
- `top_lineage_b50` — int (re-anchored against v0.34).

### Per-hazard (24 runs each)

- `mean_founders_alive_at_T` for T in `SNAPSHOT_TICKS` — float in
  [0, 5].
- `median_extinction_tick` — int | None (median over founder lineages
  that go extinct within `n_ticks`; None if every founder lineage in
  the hazard is extant).
- `p_lineage_extinct_within_window` — float in [0, 1] (fraction of
  founder lineages, across 24 runs × 5 founders = 120 lineage-runs
  per hazard, that go extinct within `n_ticks`).
- `winner_already_dominant_at_tick_50_rate` — float in [0, 1]
  (fraction of 24 runs where leader_at_tick_50 == eventual_top).
- `mean_n_lineages_with_post50_birth` — float in [0, 5] (mean over
  24 runs of the count of founder lineages contributing >= 1 birth
  at tick > 50).

### Cross-corpus / verdict-input

- `m(h) := mean_founders_alive_at_50(h)` for h in {0, 4, 8, 12}.
- `r(h) := winner_already_dominant_at_tick_50_rate(h)` for h in
  {0, 4, 8, 12}.
- Pruning indicator (boolean): `m(0) >= m(4) >= m(8) >= m(12)` AND
  `m(0) - m(12) >= 0.5`.
- Expansion indicator (boolean): `r(0) <= r(4) <= r(8) <= r(12)` AND
  `r(12) - r(0) >= 0.15`.

### Descriptive (NOT used by verdict)

- Per-hazard mean number of `extant`-status founder lineages at end
  of run (`founders_alive_at_t200`).
- Per-snapshot survivor curves shape (concave, convex, linear) —
  visible in `pruning_summary.csv`; commentary only.
- Per-hazard distribution of `extinction_tick` (median + IQR) —
  commentary only.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive reuse of v0.34 helpers).** v0.35 imports
  `STREAM_CONFIGS`, `parse_agent_lifetimes`, `parse_config`,
  `parse_manifest`, `assign_founder_lineages`,
  `compute_generation_depths`, and `LineageReplayError` from
  [[scripts/lineage_replay.py]] **without modification**. Tested by
  byte-comparing the v0.34 module hash before and after v0.35 test
  suite execution; tests skip on environment hash mismatch only.
- **H1b (v0.34 anchor re-assertion).** `B_POOL_ANCHORS = {4: 312,
  8: 321, 12: 312}` are re-asserted at v0.35 reducer entry; halts on
  drift.
- **H2 (re-anchor against v0.34).** Recomputed per-run
  `top_lineage_b50` MUST equal v0.34's
  `runs/lineage-v0.34/run_summary.csv:top_lineage_b50` for every
  `(source_version, arm_label, seed)`; halts on any byte-mismatch.
- **H2b (founder count invariant).** Every run has exactly 5 founders
  (parent_id is None); halts if not.
- **H2c (tick-0 founder-alive invariant).** For every run,
  `founders_alive_at_t0 == 5` (every founder is alive at tick 0 by
  construction, since `birth_tick_normalized == 0` for founders and
  `death_tick > 0` always). Halts if not.
- **H3 (additive guard).** v0.21..v0.34 prior tests still pass after
  the v0.35 additions. Halt condition.
- **H4 (no mutation of pre-v0.35 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  [[src/hedonism_harness/experiments/fear_hunger_chamber.py]],
  [[src/hedonism_harness/experiments/population_dynamics.py]] —
  byte-identical before and after v0.35.

### Cautious form — three-way verdict on the v0.35 question

The decision rule is intentionally three-way (not binary). The two
indicators are computed independently; the verdict combines them.

**Pruning indicator (boolean):**
- `m(h=0) >= m(h=4) >= m(h=8) >= m(h=12)` (weak monotone non-
  increasing across the four hazards) AND
- `m(h=0) - m(h=12) >= 0.5` (meaningful spread; ~10% of the 5-founder
  population, equivalent to ~12 fewer founder-survival events at h=12
  vs h=0 across 24 runs).

**Expansion indicator (boolean):**
- `r(h=0) <= r(h=4) <= r(h=8) <= r(h=12)` (weak monotone non-
  decreasing across the four hazards) AND
- `r(h=12) - r(h=0) >= 0.15` (~3.6 of 24 runs of difference; smaller
  signal-to-noise than pruning's spread, but defensible).

**Three-way verdict (mutually exclusive by construction):**

1. **H5 — PRUNING-SUPPORTED.** **FIRES iff** pruning indicator
   passes AND expansion indicator does NOT pass.
   Headline: late-window concentration is consistent with
   differential founder-line survival before tick 50; the eventual
   winner is not strongly predictable from the pre-50 leader.

2. **H6 — EXPANSION-SUPPORTED.** **FIRES iff** expansion indicator
   passes AND pruning indicator does NOT pass.
   Headline: late-window concentration is consistent with the early
   leader expanding; founders survive past tick 50 across hazards
   roughly equally.

3. **H7 — MIXED-OR-UNRESOLVED.** **FIRES iff** both indicators pass,
   OR neither passes.
   Headline: the two-mechanism story is not cleanly distinguishable
   on this corpus. Report both indicator values without a directional
   claim.

The classifier is mutually exclusive by construction; no priority
ordering required. There is no "ROBUST" tier (analogous to v0.31..
v0.33's H5 ROBUST) because v0.35 is post-hoc on a single 96-run
corpus — promotion to robustness would require a fresh-stream
calibration analogous to v0.30..v0.33, which is out of scope.

### Locked phrase for H7 MIXED-OR-UNRESOLVED

> **"Late-window concentration is consistent with both pruning and
> expansion (or with neither) on the v0.34 corpus; the lineage-axis
> data does not select a single mechanism."**

To be reused verbatim if H7 fires.

### Verdict-space subsection — what each outcome means

| verdict | indicator state | what it tells us | v0.36+ candidate |
|---|---|---|---|
| H5 PRUNING-SUPPORTED | pruning passes; expansion fails | hazard kills founder lines pre-50 (some lineages absent from late-window competition entirely); winner emerges from surviving pool | v0.36 heritability: do *which* founders survive correlate with a heritable trait? |
| H6 EXPANSION-SUPPORTED | expansion passes; pruning fails | all/most founders persist past tick 50; one lineage out-reproduces others post-50; pre-50 leader predicts eventual winner | v0.36 heritability: does the winner's lineage carry a heritable trait explaining post-50 expansion? |
| H7 MIXED (both pass) | pruning + expansion both pass | severe pruning AND survivors decided early; mechanisms compound | v0.36 heritability proceeds; framing "concentration is multi-stage" |
| H7 UNRESOLVED (neither passes) | pruning + expansion both fail | dominance-rises-with-hazard at the aggregate level is not cleanly explained by either timing-locus story | v0.36 heritability proceeds with neutral framing |

**Note:** Every verdict routes to v0.36 heritability as the canonical
next slice. The verdict shapes the v0.36 framing but does not reroute
it.

### Verdict reachability — sanity check on the threshold space

v0.34 reported `top_lineage_b50_share` rising from 0.635 (h=0) to
0.785 (h=12) — a 0.150 spread. That rise sets the prior for the
expansion indicator's `r(h=12) - r(h=0) >= 0.15` threshold (these are
two different observables — `top_lineage_b50_share` is a
within-run aggregate, `r(h)` is the per-run leader-matches-winner
rate — but they share a mechanism interpretation under
EXPANSION-SUPPORTED, so the v0.34 spread provides a defensible bar).

Verdict reachability:
- **H5 PRUNING-SUPPORTED** — fires if `m(h=0) - m(h=12) >= 0.5`
  AND `r(h=12) - r(h=0) < 0.15`. Genuinely live: hazard mortality is
  the dominant intuitive cost mechanism; if it differentially kills
  founder lines without changing post-50 dynamics, this fires.
- **H6 EXPANSION-SUPPORTED** — fires if all founders survive past
  tick 50 across hazards (`m(h=12) ≈ m(h=0) ≈ 5`, so spread < 0.5)
  AND the pre-50 leader predicts the eventual winner increasingly
  often as hazard rises by >= 0.15. Genuinely live: with 5 founders
  on a 200-tick run, low hazard might support all 5 founder lines
  through tick 50.
- **H7 MIXED-OR-UNRESOLVED** — fires if both hold (severe pruning
  AND post-50 dynamics dominated by surviving leader), or neither
  (pruning is non-monotonic OR rate-spread is < 0.15).

The threshold space is genuinely live in all three regions. None is
a tail-only outcome.

### Anchor identity

No v0.35 cross-version artifact-identity anchor (no v0.35 H9). v0.27
/ v0.28 / v0.29 / v0.30 / v0.31 / v0.32 / v0.33 / v0.34 anchors
already cover their respective artifacts; v0.35's outputs are
**reductions of the same on-disk corpus v0.34 reduced**, so the
re-anchor against v0.34's `top_lineage_b50` (H2) is the structural
guarantee.

## Decision rules

| verdict | decision | v0.36+ candidate |
|---|---|---|
| H5 PRUNING-SUPPORTED | pruning is the timing-locus consistent with the v0.34 secondary observation | v0.36 heritability: which-founders-survive trait correlation |
| H6 EXPANSION-SUPPORTED | expansion is the timing-locus consistent with the v0.34 secondary observation | v0.36 heritability: winner-lineage trait correlation |
| H7 MIXED-OR-UNRESOLVED | locked phrase fires; lineage-axis data does not select a mechanism | v0.36 heritability proceeds with neutral framing |

**Independent of the verdict, v0.36 begins the heritability arc.**
v0.35 is a targeted causal-fork follow-up, not a pivot point.

Halt conditions:
- **H1 / H1b fail** — v0.34 surface mutated. Halt; revert offending
  change.
- **H2 fails** — recomputed `top_lineage_b50` does not match
  v0.34's `run_summary.csv`. Halt; investigate (likely a v0.34
  helper drift or an algorithm divergence).
- **H2b fails** — a run does not have exactly 5 founders. Halt;
  v0.34's `EXPECTED_FOUNDERS = 5` invariant broken.
- **H2c fails** — `founders_alive_at_t0 != 5` for any run. Halt;
  founder definition broken.
- **H3 / H4 fail** — a v0.21..v0.34 contract was broken by v0.35
  additions. Halt; revert offending change.

## Out of scope (v0.35)

- Heritability / inherited traits / mutation deltas.
- `trait_fingerprints.csv` consumption.
- `events.jsonl` parsing.
- Gini / Lorenz / Shannon entropy on b50 distribution.
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications.
- New sweeps / new seed streams.
- Hazards outside {0, 4, 8, 12}.
- Influxes outside {1.0}.
- Other chambers / non-`tight_gradient`.
- Mechanism declaration. Even a clean H5 or H6 verdict does NOT
  declare a robust mechanism; it identifies a timing locus on n=96.
- Post-tick-50 sub-snapshots beyond the locked SNAPSHOT_TICKS
  (granularity of {75, 100, 150, 200} is sufficient for descriptive
  shape; finer post-50 ticks are a deferred candidate gated to v0.36+
  if the verdict warrants).
- Edits to any prior `scripts/v0.NN_*.py` (zero-touch on prior
  scripts, set by v0.34 and continued).
- Edits to [[scripts/lineage_replay.py]] (additive imports only).

## Implementation notes

### File-level changes

- **New:** [[scripts/lineage_survival_replay.py]] — post-hoc reducer.
  Imports v0.34 helpers via `importlib.util` (mirrors the pattern
  used by v0.31..v0.33 audit scripts importing `v0.30_audit.py`).
  Defines:
  - `SNAPSHOT_TICKS = (0, 25, 50, 75, 100, 150, 200)`.
  - `PRUNING_FOUNDER_SPREAD_THRESHOLD = 0.5`.
  - `EXPANSION_RATE_SPREAD_THRESHOLD = 0.15`.
  - `OUT_DIR = Path("runs/lineage-v0.35")`.
  - `V0_34_RUN_SUMMARY = Path("runs/lineage-v0.34/run_summary.csv")`.
  - Dataclasses `FounderTimelineRow`, `FounderExtinctionRow`,
    `PrePostDominanceRow`, `PruningSummaryRow`.
  - Pure functions per "Mechanism" section.
  - `main()` — discovers runs via v0.34's `STREAM_CONFIGS`, parses
    sidecars, computes per-run records, aggregates per-hazard,
    cross-checks B_pool anchors + per-run top_lineage_b50, evaluates
    three-way verdict, writes four CSVs, prints headline.
  - Estimate ~250 LOC.
- **New:** `tests/test_lineage_survival_replay.py` —
  - Snapshot-tick semantics: birth_tick=10, death_tick=50; active at
    T=49 (yes); active at T=50 (no); active at T=10 (yes); active at
    T=9 (no).
  - Tick-0 founder-active invariant: 5 founders all born at tick 0
    with death_tick > 0; founders_alive_at_t0 == 5.
  - Extinction tick: lineage with members [(0, 100), (40, 150)]
    extinct at tick 150.
  - Extant lineage: any member with `death_tick is None` returns
    extant.
  - Births so far at T=50: counts members with birth_tick_normalized
    <= 50 (founders included).
  - Leader at tick 50 with tie-break (lowest lineage_id wins ties).
  - Eventual top lineage matches v0.34's `top_lineage` algorithm.
  - winner_already_dominant_at_tick_50 boolean correctness.
  - Pruning indicator: monotone decline + spread >= 0.5 returns True;
    non-monotone returns False; monotone with spread < 0.5 returns
    False.
  - Expansion indicator: monotone rise + spread >= 0.15 returns True;
    non-monotone returns False; monotone with spread < 0.15 returns
    False.
  - Three-way verdict: PRUNING-SUPPORTED (pruning True, expansion
    False), EXPANSION-SUPPORTED (pruning False, expansion True),
    MIXED-OR-UNRESOLVED (both True), MIXED-OR-UNRESOLVED (both
    False).
  - End-to-end on a tmp_path synthetic run-tree (4 founders × 1
    descendant fixture); halts on `top_lineage_b50` drift; halts on
    founder count != 5.
  - v0.34 helper imports succeed and constants match
    (`B_POOL_ANCHORS`, `EXPECTED_FOUNDERS`,
    `B50_THRESHOLD_TICK`, `SINGLE_LINEAGE_MAJORITY_THRESHOLD`).
  - Estimate ~22 tests, ~200 LOC.
- **No changes** to [[scripts/lineage_replay.py]],
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  any `scripts/v0.NN_*.py`, `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`.
- **Documented:** this file
  (`docs/experiments/fear_hunger_v0.35.md`); Results appended after
  the reducer runs.

### Determinism contract

- v0.21..v0.34 events.jsonl + sidecar artifacts on disk are not
  regenerated.
- v0.21..v0.34 test suites continue to pass.
- [[scripts/lineage_replay.py]] is imported but not modified — its
  byte-identity contract is preserved.
- `runs/lineage-v0.34/run_summary.csv:top_lineage_b50` per
  `(source_version, arm_label, seed)` is the byte-anchor for
  re-derivation; drift halts.

### LOC estimate

- `scripts/lineage_survival_replay.py`: ~250 LOC.
- `tests/test_lineage_survival_replay.py`: ~200 LOC.
- This doc: ~430 LOC.

Total v0.35 implementation: ~880 LOC. Tests should bring the suite
from 883 to ~905 (+~22).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   883 passed
uv run python scripts/core_smoke_test.py  ok
```

## References

- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; H7 mostly-concentrated fires; secondary
  monotone-with-hazard observation that motivates v0.35.
- [[docs/experiments/fear_hunger_v0.33.md]] — v0.33 hazard-axis
  pooled audit; H6_pool WEAK; closes the aggregate-optimum
  calibration arc and pivots to the lineage-axis arc that v0.34
  began.
- [[scripts/lineage_replay.py]] — v0.34 reducer; **imported by v0.35
  without modification**.
- [[scripts/v0.33_audit.py]] — three-stream merge / pooled verdict
  pattern; v0.35 mirrors the importlib.util reuse pattern but does
  NOT need three-stream merging (v0.34 already collapsed the corpus).
- [[docs/handoffs/2026-05-06-v0.34-shipped-v0.35-pruning-planned.md]]
  — handoff specifying v0.35 implementation surface verbatim from
  user-locked scope.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".
