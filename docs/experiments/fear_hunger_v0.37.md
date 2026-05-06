# v0.37 — dominance timing decomposition (winner lock-in vs early-leader stability)

**Status:** pre-registered 2026-05-06; reducer not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.37-lock-in-timing-decomposition`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated at h=8;
secondary post-hoc observation: `top_lineage_b50_share` rises
monotonically with hazard 0.635 → 0.785), v0.35 (founder-survival
timing — **H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY**;
`winner_already_dominant_at_tick_50_rate` rises 0.458 → 0.708 →
0.750 → 0.792 across hazards {0, 4, 8, 12}; pre-50 founder pruning
*excluded* as the timing locus), v0.36 (founder-trait heritability
replay — **H6 TRAIT-LINKED-FLAT**; `sensor_radius` clears
|d(h=12)|≥0.4 with the expected sign but does not strengthen with
hazard, spread |d(12)|−|d(0)| = +0.082 < locked 0.2 bar;
**hazard-amplified founder-trait selection is ruled out** as the
mechanism for v0.35's early-leader continuity).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.35 narrowed v0.34's monotone-with-hazard observation to an
**early-leader continuity** locus: the pre-50 birth-count leader
becomes the post-50 b50 winner more often as hazard rises (rate
0.458 → 0.792). v0.36 ruled out hazard-amplified founder-trait
selection as the mechanism for that strengthening: founder-trait
effects are robust (sensor_radius |d| ≈ 1.18–1.35 across all
hazards) but **flat with hazard** (spread +0.082 < locked +0.2 bar).

That leaves v0.35's strengthening pattern unexplained at the
timing-locus level. The active question for v0.37 is:

> **Is hazard's rising early-leader continuity explained by (a) the
> eventual winner reaching birth-count leadership earlier under
> hazard, or by (b) early leadership (whoever holds it) being more
> stable / more decisive under hazard, or by both?**

These are not the same mechanism. (a) is **winner-centric**: the
specific lineage that ends up winning takes the lead sooner under
hazard. (b) is **leader-centric**: whoever happens to lead early
holds the lead more stably or with a wider margin under hazard,
regardless of whether they are the eventual winner. The v0.36
inventory case at v0.25 / hzd=0 / seed=1 demonstrates the
distinction: the eventual winner does not lead until tick 161, but
some other lineage stably leads through the entire {25, 50, 75, 100}
window and ties for top by margin at tick 50.

This is a **targeted post-hoc follow-up** on v0.35 + v0.36. It is
NOT a sim-mechanics change, NOT a heritability mechanism declaration,
NOT a HedonismPolicy comparison, NOT a new sweep, NOT a
descendant-trait-drift exploration (descendant drift is the v0.38+
candidate gated on v0.37 H8). v0.37 stays post-hoc one more step.

### Observable inventory (read once, before pre-reg locks)

The inventory phase ran two scripts (committed under
[[scripts/v0_37_inventory_scratch.py]] and
[[scripts/v0_37_sentinel_scan.py]]; both will be removed before the
v0.37 PR per the cleanup convention noted in "Implementation notes"
below):

1. **3-run computability check** (lowest seed at h ∈ {0, 8, 12} from
   the v0.25 stream): O1, O2, O3 computed cleanly; no NaN, no halt;
   sentinel path exercised in code but not triggered by data on
   these 3 runs. Surfaced the leader-centric vs winner-centric
   semantic split (see "Observable semantics" below).
2. **Full-corpus sentinel scan** (96 runs):
   `n_never_leads_pre_end` = {h=0: 2, h=4: 1, h=8: 1, h=12: 1} out
   of 24 runs each (5/96 ≈ 5.2%). O1's mean is **not**
   sentinel-dominated; O1 reads cleanly as a tick-count.

The inventory does NOT compute per-hazard means, deltas, or
thresholds. The inventory does NOT precommit any verdict. The
inventory exists solely to validate observable computability and
sentinel handling before this pre-reg locks O1/O2/O3 spread
thresholds.

### Observable semantics (locked, pre-committed)

The three observables split into two semantic groups:

- **O1 is winner-centric.** It tracks when the *eventual winner*
  first becomes the (tie-break-inclusive) birth-count leader. A
  monotone drop of mean_O1 with hazard reads as
  **earlier-eventual-winner-lock-in**.
- **O2 and O3 are leader-centric.** They track stability /
  decisiveness of the *current* leader at the locked snapshot pairs,
  regardless of whether the current leader is the eventual winner.
  A monotone drop of mean_O2 reads as **stabler-early-leadership**;
  a monotone rise of mean_O3 reads as **more-decisive-early-margin**.

These semantics matter because **H5 EARLIER-WINNER-LOCK-IN and H6
STABLER-EARLY-LEADERSHIP claim different things**. H6 does NOT claim
that the eventual winner locks in earlier; it claims that the early
contest (whoever wins it transiently) is less churny under hazard.
The pre-reg locks this distinction so the Results headline cannot
silently conflate them.

## What this slice tests, and what it does NOT test

### Tests

- Whether **mean_winner_first_leader_tick(h)** declines monotonically
  with hazard across the v0.34 96-run corpus.
- Whether **mean_leader_turnover_count_25_to_100(h)** declines
  monotonically with hazard.
- Whether **mean_margin_rank1_minus_rank2_at_tick_50(h)** rises
  monotonically with hazard (supporting only; cannot fire any
  verdict).
- Whether the joint pattern fires H5 EARLIER-WINNER-LOCK-IN, H6
  STABLER-EARLY-LEADERSHIP, H7 COMPOUND-LOCK-IN, or H8 UNRESOLVED
  under the pre-committed four-way rule below.
- Anchor identity against v0.34's `run_summary.csv:top_lineage_id`
  AND v0.35's `pre_post_dominance.csv:eventual_top_lineage_id` for
  every (source_version, arm_label, seed). Drift halts.
- Substrate-byte-identity: v0.34 + v0.35 reducers imported without
  modification.

### Does NOT test

- Descendant-trait drift, parent-child trait deltas, or selection
  *within* a lineage. Reserved for v0.38+ if v0.37 fires H8.
- Per-lineage post-50 birth-rate differentials (the literal
  "expansion rate" claim v0.35 also did NOT directly test).
- Heritability mechanism declaration. v0.36's `sensor_radius`
  finding is in scope as a deferred observation only (it does not
  enter v0.37's verdict).
- Causal mechanism declaration. Even a clean H5 / H6 / H7 verdict
  identifies a *correlational* timing-locus story consistent with
  one of two (or both) lock-in mechanisms; it does not declare a
  robust mechanism. Promotion to mechanism requires fresh-stream
  calibration analogous to v0.30..v0.33.
- p-values or statistical significance. Effect-size / spread-only
  thresholds, consistent with v0.30..v0.36 discipline.
- Multiple-comparison-correction beyond the small-family
  pre-commitment (2 verdict-driving observables + 1 supporting).
  No Bonferroni; no FDR. The 2-observable verdict family IS the
  family-wise control.
- HedonismPolicy comparisons. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- Sim-mechanics changes; `src/` modifications. Zero.
- New sweeps; new seed streams; new chambers; new hazards.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- O3 firing a verdict. O3 is descriptive support only.
- Sub-snapshot leader-turnover detection. O2 is locked at the
  {25→50, 50→75, 75→100} snapshot pairs; sub-snapshot churn is
  not detectable. Acknowledged caveat (see "Caveats" below).
- Post-100 leader-turnover detection. O2's window ends at tick 100
  by lock; O1's window covers the full [0, n_ticks). Acknowledged
  caveat.

### Deferred (v0.38+ candidates, conditional on v0.37 outcome)

- **If H5 EARLIER-WINNER-LOCK-IN fires.** v0.38 candidate:
  fresh-stream calibration analogous to v0.30..v0.33 — replay the
  H5 verdict on a fresh seed range to test whether the
  earlier-winner-lock-in effect compounds across streams.
- **If H6 STABLER-EARLY-LEADERSHIP fires.** v0.38 candidate:
  per-lineage post-50 birth-rate differentials conditional on
  pre-50 leadership status, to disambiguate "stable early
  leadership predicts winner via persistence" vs "stable early
  leadership predicts winner via post-50 expansion."
- **If H7 COMPOUND-LOCK-IN fires.** v0.38 candidate: variance
  decomposition — quantify how much of v0.35's wad_rate spread
  (0.333) is captured by O1 vs O2 individually vs jointly.
- **If H8 UNRESOLVED fires.** v0.38 candidate: descendant-trait
  drift lens (parent-child trait perturbation by survival /
  reproduction outcome); the timing-locus lens has been exhausted.

### Quarantined v0.36 secondaries (NOT v0.37 inputs)

v0.36's descriptive-only observations remain quarantined: the
`reproduction_drive` h=0 sign-inversion (signed_d = −0.55) and
`metabolic_rate` hazard-attenuation (|d| 0.555 → 0.255). These
are mechanistically suggestive but did not fire any v0.36 verdict
under the locked rule. They are NOT v0.37 inputs and do NOT shape
v0.37's verdict. Promotion to mechanism for either requires
fresh-stream calibration.

## Conservation framing — unchanged from v0.20..v0.36

No new conservation contract. No mutations to `core/`, `model.py`,
`experiments/fear_hunger_chamber.py`,
`experiments/population_dynamics.py`,
`policies/gradient_policy.py`, `policies/hedonism_policy.py`. No
mutations to existing arm tuples. No mutations to
[[scripts/lineage_replay.py]],
[[scripts/lineage_survival_replay.py]], or
[[scripts/trait_replay.py]]. No new event types, no new chamber, no
new policy. Source modifications are **zero**. v0.37 is a fourth
post-hoc reducer that imports v0.34 + v0.35 helpers additively and
writes new CSVs under a new output directory.

## Mechanism

v0.37 is one new script plus one new tests file plus this doc.

1. **Reducer** (`scripts/lock_in_timing_replay.py`). Imports v0.34
   helpers from [[scripts/lineage_replay.py]] and v0.35 helpers from
   [[scripts/lineage_survival_replay.py]] via `importlib.util` (the
   established pattern). v0.36's `trait_replay.py` is NOT imported
   (no founder-trait observables in v0.37).

   Pure-function pipeline:
   - For each run, reuse v0.35's `load_run_agents` to get
     `agent_rows + n_ticks`.
   - Re-derive `eventual_top_lineage_id` per run via v0.35's
     `compute_eventual_top_lineage` (lineage with max `b50_count`;
     lowest lineage_id wins ties).
   - Cross-anchor (halts on drift):
     - **v0.34 anchor (H2a):** re-derived `top_lineage_id` per run
       matches `runs/lineage-v0.34/run_summary.csv:top_lineage_id`
       for every (source, arm, seed).
     - **v0.35 anchor (H2b):** re-derived `eventual_top_lineage_id`
       per run matches
       `runs/lineage-v0.35/pre_post_dominance.csv:eventual_top_lineage_id`
       for every (source, arm, seed).
   - For each run, compute:
     - `O1_winner_first_leader_tick` — smallest tick t in
       [0, n_ticks) where `leader_at_tick(t) ==
       eventual_top_lineage_id`. Sentinel `n_ticks` if winner never
       leads. `leader_at_tick(t)` = lineage with max
       `births_so_far(t)`, lowest lineage_id wins ties.
     - `O2_leader_turnover_count_25_to_100` — count of pairs in
       {(25,50), (50,75), (75,100)} where `leader_at_tick(t1) !=
       leader_at_tick(t2)`. Range [0, 3].
     - `O3_margin_rank1_minus_rank2_at_tick_50` —
       `births_so_far(rank1, t=50) - births_so_far(rank2, t=50)`,
       where `rank1` / `rank2` are the lineages with the highest
       and second-highest `births_so_far` at tick 50, with lowest
       lineage_id breaking ties. Floor at 0.
     - `never_leads_pre_end` — `O1 == n_ticks` (bool).
     - `rank2_zero_flag` — `births_so_far(rank2, t=50) == 0` (bool;
       theoretical-only on this corpus per v0.35 H2c).
     - Snapshot leader trajectory `(L25, L50, L75, L100)` —
       descriptive context, not verdict input.
   - Per-hazard aggregation:
     - `mean_O1(h)`, `mean_O2(h)`, `mean_O3(h)`, `n_runs(h)`,
       `n_never_leads(h)`, `n_no_winner(h)`.
     - Indicator passes (locked):
       - `O1_passes(h0..h12)` := monotone non-increasing across
         hazards AND `mean_O1(0) - mean_O1(12) >= 25`.
       - `O2_passes(h0..h12)` := monotone non-increasing AND
         `mean_O2(0) - mean_O2(12) >= 0.25`.
       - `O3_passes(h0..h12)` := monotone non-decreasing AND
         `mean_O3(12) - mean_O3(0) >= 1.0` (supporting, NOT verdict-
         firing).
   - Four-way verdict (see "Decision rules" below).

   Outputs four CSVs under `runs/lineage-v0.37/` (gitignored):
   - `per_run.csv` — 96 rows: source, arm, hazard, seed,
     eventual_top_lineage_id, O1, O2, O3_r1_births, O3_r2_births,
     O3_margin, never_leads_flag, rank2_zero_flag, L25, L50, L75,
     L100.
   - `per_hazard.csv` — 4 rows: hazard, n_runs, n_never_leads,
     n_no_winner, mean_O1, mean_O2, mean_O3.
   - `indicator_summary.csv` — 3 rows (one per observable):
     observable, monotone_pass, spread_value, spread_threshold,
     threshold_passes, indicator_passes, verdict_role
     (driver/supporting).
   - `verdict.csv` — single row: verdict, locked_phrase,
     firing_indicators (comma-separated; "" for H8).

2. **Locked constants** (committed in code at reducer entry):
   ```
   LEADER_TICK_O3: int = 50
   O2_SNAPSHOT_TICKS: tuple[int, ...] = (25, 50, 75, 100)
   O1_SPREAD_THRESHOLD: int = 25
   O2_SPREAD_THRESHOLD: float = 0.25
   O3_SPREAD_THRESHOLD: float = 1.0
   V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
   V0_35_PRE_POST_DOMINANCE: Path = Path(
       "runs/lineage-v0.35/pre_post_dominance.csv"
   )
   OUT_DIR: Path = Path("runs/lineage-v0.37")
   ```

   Tie-break for all "lineage selection by maximum count" operations:
   **lowest lineage_id**, mirroring v0.35.

### Determinism — anchors

- v0.21..v0.36 events.jsonl + sidecar artifacts on disk are not
  regenerated. Sidecars (`agent_lifetimes.csv`, `config.json`,
  `manifest.json`) are read verbatim.
- v0.21..v0.36 test suites continue to pass (additive guard).
- [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]], and
  [[scripts/trait_replay.py]] are imported (or, in v0.36's case,
  not imported), not modified.
- Re-anchor against v0.34's `run_summary.csv:top_lineage_id` AND
  v0.35's `pre_post_dominance.csv:eventual_top_lineage_id` (96
  runs); halt on any drift. v0.36's `founder_traits.csv` is NOT
  re-anchored (different observable family; v0.36 is structurally
  orthogonal to v0.37).
- v0.34's `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` and
  `EXPECTED_FOUNDERS = 5` are re-asserted at v0.37 reducer entry.

### Wall time estimate

- Reducer: < 5s on the 96-run corpus. Per-run cost is dominated by
  the per-tick leader scan for O1 (200 × 5 lineages × naive
  per-lineage births_so_far). An optimisation pass (only recompute
  at birth ticks) is possible but unnecessary at this scale.

## Observables — pre-committed before reading the data

### Per-run

- `eventual_top_lineage_id(run)` — int in {0..4} or None when
  total_b50 == 0. Computed via v0.35's
  `compute_eventual_top_lineage`.
- `leader_at_tick(t, run)` for t in [0, n_ticks) — int in {0..4}.
  Lineage with max `births_so_far(t)`, lowest lineage_id wins
  ties.
- `O1_winner_first_leader_tick(run)` — int in [0, n_ticks].
  `n_ticks` is the locked sentinel for "winner never leads
  pre-end."
- `O2_leader_turnover_count_25_to_100(run)` — int in [0, 3].
- `O3_margin_rank1_minus_rank2_at_tick_50(run)` — int >= 0.
- `never_leads_flag(run)` — bool.
- `rank2_zero_flag(run)` — bool. Theoretical-only on this corpus
  (v0.35 H2c invariant: every founder is alive at tick 50, so
  every lineage has `births_so_far(50) >= 1`, so rank2 >= 1).

### Per-hazard (24 runs each)

- `mean_O1(h)`, `mean_O2(h)`, `mean_O3(h)` — float.
- `n_runs(h)` — int (24 by construction).
- `n_never_leads(h)` — int in [0, 24]. Pre-pre-reg sentinel scan
  reported {h=0: 2, h=4: 1, h=8: 1, h=12: 1}.
- `n_no_winner(h)` — int. Expected 0 on this corpus per v0.34's
  `n_runs_total_b50_zero == 0` per hazard.

### Indicator-input (locked)

- `O1_passes` := monotone-non-increasing(`mean_O1`) AND
  `mean_O1(0) - mean_O1(12) >= O1_SPREAD_THRESHOLD (= 25)`.
- `O2_passes` := monotone-non-increasing(`mean_O2`) AND
  `mean_O2(0) - mean_O2(12) >= O2_SPREAD_THRESHOLD (= 0.25)`.
- `O3_passes` := monotone-non-decreasing(`mean_O3`) AND
  `mean_O3(12) - mean_O3(0) >= O3_SPREAD_THRESHOLD (= 1.0)`.
  **Supporting only; cannot fire any verdict.**

### Descriptive (NOT used by verdict)

- Snapshot leader trajectory `(L25, L50, L75, L100)` per run.
- Per-hazard `n_never_leads` reported alongside `mean_O1` for
  transparency.
- Per-hazard distribution of `O1`, `O2`, `O3` values
  (median, IQR) — commentary only.
- Whether `eventual_top_lineage_id` matches `L50` (this is exactly
  v0.35's `winner_already_dominant_at_tick_50` observable;
  reproduced here for descriptive cross-reference; halts if
  mismatched against v0.35's `pre_post_dominance.csv`).

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive reuse of v0.34 + v0.35 helpers).** v0.37 imports
  v0.34's `STREAM_CONFIGS`, `parse_agent_lifetimes`, `parse_config`,
  `parse_manifest`, `assign_founder_lineages`,
  `compute_generation_depths`, `LineageReplayError`,
  `build_agent_rows`, `discover_runs`, `HAZARDS`,
  `EXPECTED_FOUNDERS`, `B_POOL_ANCHORS` from
  [[scripts/lineage_replay.py]]; and v0.35's `load_run_agents`,
  `_agents_by_lineage`, `compute_births_so_far`,
  `compute_eventual_top_lineage`, `compute_leader_at_tick_50`
  (re-used as a sanity reference; v0.37 reimplements
  `leader_at_tick(t)` for arbitrary t) from
  [[scripts/lineage_survival_replay.py]]. Both modules imported
  without modification.
- **H1b (v0.34 anchor re-assertion).** `B_POOL_ANCHORS = {4: 312,
  8: 321, 12: 312}` and `EXPECTED_FOUNDERS = 5` are re-asserted at
  v0.37 reducer entry. Drift halts.
- **H2a (v0.34 anchor).** Re-derived per-run `top_lineage_id` MUST
  equal v0.34's
  `runs/lineage-v0.34/run_summary.csv:top_lineage_id` for every
  (source, arm, seed). Halts on drift.
- **H2b (v0.35 anchor).** Re-derived per-run
  `eventual_top_lineage_id` MUST equal v0.35's
  `runs/lineage-v0.35/pre_post_dominance.csv:eventual_top_lineage_id`
  for every (source, arm, seed). Halts on drift.
- **H2c (founder count invariant).** Every run has exactly 5
  founders (parent_id is None); halts if not. Inherited from v0.34's
  `assign_founder_lineages`.
- **H2d (sentinel value invariant).** `O1_SENTINEL_VALUE` per run
  equals `n_ticks` from that run's `manifest.json`. The reducer
  reads `n_ticks` per run via v0.34's `parse_manifest`; v0.37 does
  NOT hardcode 200. Halts if any run's `n_ticks != 200` (defensive;
  the locked corpus has `N_TICKS = 200` everywhere by sweep
  construction).
- **H3 (additive guard).** v0.21..v0.36 prior tests still pass
  after v0.37 additions.
- **H4 (no mutation of pre-v0.37 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before
  and after v0.37.

### Cautious form — four-way verdict on v0.37's question

The decision rule is intentionally four-way (mutually exclusive
by construction). The 2-observable verdict family (O1, O2) is the
family-wise control; no Bonferroni correction is applied beyond it.
O3 is supporting-only and does NOT enter the verdict.

**Per-observable indicator rules (locked):**

- `O1_passes` := `mean_O1(0) >= mean_O1(4) >= mean_O1(8) >=
  mean_O1(12)` AND `mean_O1(0) - mean_O1(12) >= 25` (ticks).
- `O2_passes` := `mean_O2(0) >= mean_O2(4) >= mean_O2(8) >=
  mean_O2(12)` AND `mean_O2(0) - mean_O2(12) >= 0.25` (turnover
  events).
- `O3_passes` := `mean_O3(0) <= mean_O3(4) <= mean_O3(8) <=
  mean_O3(12)` AND `mean_O3(12) - mean_O3(0) >= 1.0` (births).
  **Computed and reported, but NOT a verdict input.**

**Four-way verdict (mutually exclusive):**

1. **H5 — EARLIER-WINNER-LOCK-IN.** **FIRES iff** `O1_passes ==
   True AND O2_passes == False`. Headline: hazard's rising
   early-leader continuity is consistent with the **eventual
   winner reaching birth-count leadership earlier under hazard**;
   early-leadership turnover does not separate.

2. **H6 — STABLER-EARLY-LEADERSHIP.** **FIRES iff** `O1_passes ==
   False AND O2_passes == True`. Headline: hazard's rising
   early-leader continuity is consistent with **early leadership
   (whoever holds it) being more stable under hazard**;
   eventual-winner timing does not separate. Note: this does NOT
   claim that the eventual winner locks in earlier — only that the
   pre-50 leadership contest is less churny.

3. **H7 — COMPOUND-LOCK-IN.** **FIRES iff** `O1_passes == True AND
   O2_passes == True`. Headline: both eventual-winner timing and
   early-leadership stability tighten with hazard; the timing
   locus is compound.

4. **H8 — UNRESOLVED.** **FIRES iff** `O1_passes == False AND
   O2_passes == False`. Headline: neither eventual-winner-timing
   nor early-leadership-turnover separates with hazard at this
   scale on the v0.34 corpus; the timing-locus lens has been
   exhausted. Descendant-trait drift becomes the canonical v0.38
   candidate.

The classifier is mutually exclusive by construction; no priority
ordering required. There is no "ROBUST" tier. v0.37 is post-hoc
on a single 96-run corpus — promotion to a robust mechanism would
require fresh-stream calibration analogous to v0.30..v0.33, which
is out of scope.

### Locked phrases for each verdict

> **H5 phrase:** "Eventual-winner lock-in occurs earlier with hazard
> on the v0.34 corpus; early-leadership turnover does not separate.
> Correlational; not a mechanism declaration."

> **H6 phrase:** "Early-leadership turnover drops with hazard on the
> v0.34 corpus; eventual-winner timing does not separate. This
> supports a stabler-early-competition timing locus rather than
> earlier winner emergence. Correlational; not a mechanism
> declaration."

> **H7 phrase:** "Both eventual-winner timing and early-leadership
> stability tighten with hazard on the v0.34 corpus. Compound
> timing locus; correlational; not a mechanism declaration."

> **H8 phrase:** "Neither eventual-winner-timing nor
> early-leadership-turnover indicators separate with hazard on the
> v0.34 corpus; the early-leader-continuity rise observed in v0.35
> is not resolved by this lens. Descendant-trait drift remains the
> canonical v0.38 candidate."

To be reused verbatim if the corresponding verdict fires.

### Caveats — locked, must appear in Results

- **O2 is coarse.** It only observes turnover at the locked snapshot
  pairs {25→50, 50→75, 75→100}. It does NOT detect sub-snapshot
  churn (a leader change between, say, ticks 30 and 49 is
  invisible). It does NOT detect post-100 takeovers (e.g., the v0.25
  / hzd=0 / seed=1 case where the eventual winner becomes leader
  at tick 161). Acknowledged limit; H6 fires on the locked
  observable, not on a sub-snapshot or post-100 observable.
- **O2 and O3 are leader-centric, not eventual-winner-centric.**
  H6 STABLER-EARLY-LEADERSHIP claims that the early-leadership
  contest is less churny under hazard, NOT that the eventual
  winner locks in earlier. The eventual-winner timing claim
  belongs to O1 and to H5 / H7. Results MUST preserve this
  distinction; conflating them is a verdict-language failure.
- **O1 is the eventual-winner timing observable** and carries the
  winner-lock-in claim. Sentinel rate (5/96 ≈ 5.2% on this corpus)
  is reported alongside `mean_O1` per hazard.
- **O3 is supporting only.** Its indicator pass status is reported
  in `indicator_summary.csv` and contextualises H6 / H7 (a wider
  margin at tick 50 with hazard is consistent with stabler
  early-leadership) but does NOT enter the verdict logic. A
  passing O3 alongside a failing O1 + failing O2 still fires H8.

### Verdict reachability — sanity check

We have no prior data on per-hazard mean values for O1, O2, O3 on
this corpus. The thresholds are set conservatively-but-loosely:

- **O1 spread = 25 ticks**: 12.5% of n_ticks=200; in the spirit of
  v0.35's 10%-of-population spread on `m(h)`. Big enough to matter,
  not so strict it becomes inert.
- **O2 spread = 0.25**: across 24 runs at hazard 0 vs 24 runs at
  hazard 12, this is "six fewer turnover events at h=12 than h=0
  on average." Conservative-but-loose given O2's [0, 3] range and
  its potential sparsity (inventory's 3 runs all showed O2 = 0
  at the locked snapshot pairs; the corpus may or may not exhibit
  more turnover on average).
- **O3 spread = 1.0 birth**: one full birth's worth of
  rank1-rank2 margin widening between h=0 and h=12. Supporting
  only.
- **H5** fires if winner-lock-in tightens with hazard but
  early-leadership stability does not. Genuinely live: the
  inventory's h=8/12 runs both showed O1 = 9 (very early winner
  lock-in) vs h=0 O1 = 161 (very late). Single-run anecdotes; not
  evidence for or against the verdict, but the threshold range is
  in scope.
- **H6** fires if early-leadership stability tightens with hazard
  but winner-lock-in timing does not. Genuinely live but
  threshold-sensitive: O2 may be too sparse on this corpus for
  the 0.25-spread bar to fire even if the ordinal pattern is
  present.
- **H7** fires if both. Genuinely live: the two observables can
  trivially correlate (an earlier-locking-in winner who stays in
  the lead generates fewer turnovers).
- **H8** fires if neither. Genuinely live: timing-locus lens
  may not resolve at this scale; descendant-drift is the
  contingent v0.38 candidate.

The threshold space is genuinely live in all four regions. None
is a tail-only outcome.

### Anchor identity

No v0.37 cross-version artifact-identity anchor (no v0.37 H9).
v0.34 + v0.35 anchors already cover the underlying lineage
assignments and winner identity. v0.37's outputs are reductions
of the same on-disk corpus, with re-anchor against both prior
reductions.

## Decision rules

| verdict | O1 | O2 | decision | v0.38+ candidate |
|---|:---:|:---:|---|---|
| H5 EARLIER-WINNER-LOCK-IN | passes | fails | timing-locus consistent with eventual-winner reaching leadership earlier under hazard | fresh-stream calibration on H5 |
| H6 STABLER-EARLY-LEADERSHIP | fails | passes | timing-locus consistent with stabler early-leadership contest under hazard (not winner lock-in) | per-lineage post-50 birth-rate differentials |
| H7 COMPOUND-LOCK-IN | passes | passes | both timing loci tighten with hazard; compound | variance decomposition: O1 vs O2 contribution to wad_rate spread |
| H8 UNRESOLVED | fails | fails | timing-locus lens does not resolve on this corpus | descendant-trait drift |

**Independent of the verdict, v0.38 remains post-hoc.** v0.37 closes
the targeted timing-locus follow-up; HedonismPolicy and Mesa remain
deferred indefinitely.

Halt conditions:
- **H1 / H1b fail** — v0.34 / v0.35 surface mutated. Halt; revert.
- **H2a / H2b fail** — re-anchor mismatch. Halt; investigate
  (likely algorithm divergence or drift).
- **H2c fails** — founder count != 5. Halt.
- **H2d fails** — `n_ticks != 200` for any run. Halt.
- **H3 / H4 fail** — a v0.21..v0.36 contract was broken by v0.37
  additions. Halt; revert.

## Out of scope (v0.37)

- Descendants. Only founder-lineage birth counts are consumed.
- O3 firing the verdict.
- Sub-snapshot leader-turnover.
- Post-100 leader-turnover (O2 window ends at tick 100; O1 covers
  full [0, n_ticks)).
- Per-lineage post-50 birth-rate differentials (the literal
  expansion-rate claim deferred to v0.38+ if H6 fires).
- Founder-trait observables. v0.36's lens is structurally
  orthogonal; not consumed here.
- Descendant-trait drift, parent-child trait deltas. Reserved
  for v0.38+ if v0.37 fires H8.
- Multivariate trait distance / PCA / clustering.
- p-values, statistical significance tests, Bonferroni / FDR /
  permutation tests.
- Lineage-mean trait vectors.
- Tick-50 LEADER-vs-non-leader trait comparison.
- Trait-trait correlations.
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications.
- New sweeps; new seed streams.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- Mechanism declaration. Even a clean H5 / H6 / H7 verdict
  identifies a *correlation* consistent with one of two (or both)
  timing loci; promotion requires fresh-stream calibration.
- Edits to any prior `scripts/v0.NN_*.py`,
  [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]], or
  [[scripts/trait_replay.py]].

## Implementation notes

### File-level changes

- **New:** `scripts/lock_in_timing_replay.py` — post-hoc reducer
  (~350 LOC). Imports `lineage_replay` and `lineage_survival_replay`
  via `importlib.util`. Defines locked constants, dataclasses
  (`PerRunRow`, `PerHazardRow`, `IndicatorSummaryRow`, `VerdictRow`),
  pure-function pipeline, four-way verdict logic, and `main()`.
- **New:** `tests/test_lock_in_timing_replay.py` — synthetic-fixture
  tests (~350 LOC, ~28 tests). Coverage:
  - **Per-tick leader (4–6):** tick-0 winner==leader tie-break case;
    winner-never-leads sentinel case; winner-becomes-leader-at-last-
    tick edge; winner-becomes-leader-mid-window case;
    winner-becomes-leader-then-loses-and-regains case (O1 captures
    the *first* tick).
  - **O2 turnover (4–6):** all-stable (O2=0); single-pair-change
    (O2=1); all-changing (O2=3); tie-break-at-snapshot-boundary
    (lowest lineage_id wins).
  - **O3 margin (3–5):** tied tick-50 (O3_margin=0); unique top;
    rank2_zero edge case (theoretical).
  - **Indicator rules (6):** O1 monotone-pass + spread-pass;
    O1 monotone-pass + spread-fail; O1 monotone-fail; O2 same trio;
    O3 supporting-only (does not change verdict).
  - **Verdict (4):** each of H5/H6/H7/H8 fires under its
    pre-committed indicator combination.
  - **Re-anchor halt (2):** v0.34 mismatch; v0.35 mismatch.
  - **Substrate-immutability (3):** byte-identity of imported
    v0.34 / v0.35 module hashes; helper signature stability;
    `B_POOL_ANCHORS` + `EXPECTED_FOUNDERS` re-assertion.
  - **End-to-end (1):** synthetic 4-run tmp_path tree; verdict
    fires as expected; CSVs written with locked headers.
  - **Sentinel-handling (1):** per-run `n_ticks` parsed from
    manifest matches the locked sentinel value used in `O1`.
  - Estimate ~28 tests, ~350 LOC.
- **No changes** to [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]], any `scripts/v0.NN_*.py`, `core/`,
  `model.py`, chamber / population / policy modules.
- **Documented:** this file. Results appended after the reducer
  runs.
- **Removed before v0.37 PR:** `scripts/v0_37_inventory_scratch.py`
  and `scripts/v0_37_sentinel_scan.py` (both committed during
  the pre-pre-reg inventory phase as audit artifacts; superseded
  by the v0.37 reducer once it lands and SHOULD NOT be imported by
  it). If any of their useful logic is needed by the reducer, it
  is reimplemented inside `lock_in_timing_replay.py` rather than
  imported from the scratches.

### Determinism contract

- v0.21..v0.36 events.jsonl + sidecar artifacts not regenerated.
- v0.21..v0.36 test suites continue to pass.
- v0.34 + v0.35 reducers imported but not modified. v0.36 reducer
  not imported (no founder-trait observables).
- Per-run double anchor against v0.34 `run_summary.csv:
  top_lineage_id` and v0.35 `pre_post_dominance.csv:
  eventual_top_lineage_id`.
- Per-run `n_ticks` parsed from manifest is the O1 sentinel value
  (defensive against a future corpus with `n_ticks != 200`).

### LOC estimate

- `scripts/lock_in_timing_replay.py`: ~350 LOC.
- `tests/test_lock_in_timing_replay.py`: ~350 LOC.
- This doc: ~700 LOC.

Total v0.37: ~1,400 LOC. Tests should bring the suite from 972 to
~1,000 (+~28).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   972 passed
uv run python scripts/core_smoke_test.py  ok
```

(Pre-pre-reg inventory phase added two scratch scripts; those are
committed but will be removed before the v0.37 PR per the cleanup
note above. Test suite is unchanged at 972 because the scratches
have no test files.)

## References

- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; H7 mostly-concentrated; secondary
  monotone-with-hazard observation that motivates v0.35..v0.37.
- [[docs/experiments/fear_hunger_v0.35.md]] — v0.35
  founder-survival-timing replay; **H6 EXPANSION-SUPPORTED**
  (= EARLY-LEADER CONTINUITY); supplies the per-run winner identity
  v0.37 re-anchors against; pre-50 founder pruning excluded as the
  timing locus.
- [[docs/experiments/fear_hunger_v0.36.md]] — v0.36
  founder-trait heritability replay; **H6 TRAIT-LINKED-FLAT**;
  hazard-amplified founder-trait selection ruled out as the
  mechanism for v0.35's early-leader continuity. Motivates v0.37's
  timing-locus decomposition.
- [[scripts/lineage_replay.py]] — v0.34 reducer; **imported by
  v0.37 without modification**.
- [[scripts/lineage_survival_replay.py]] — v0.35 reducer;
  **imported by v0.37 without modification**.
- [[scripts/trait_replay.py]] — v0.36 reducer; NOT imported by
  v0.37 (structurally orthogonal observable family).
- [[scripts/v0_37_inventory_scratch.py]] — pre-pre-reg
  observable-computability check (3 runs); audit artifact;
  removed before v0.37 PR.
- [[scripts/v0_37_sentinel_scan.py]] — pre-pre-reg
  sentinel-rate scan (96 runs); audit artifact; removed before
  v0.37 PR.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

**Status:** not yet executed. Reducer
(`scripts/lock_in_timing_replay.py`) will run over the same 96-run
corpus v0.34 / v0.35 / v0.36 reduced. Outputs under
`runs/lineage-v0.37/` (gitignored). Results section appended after
reducer execution, with the locked verdict phrase fired verbatim.
