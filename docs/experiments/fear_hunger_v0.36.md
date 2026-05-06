# v0.36 — heritability replay (founder-trait predictors of post-50 lineage dominance)

**Status:** pre-registered 2026-05-06; reducer not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.36-heritability-trait-replay`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated at h=8), v0.35
(founder survival timing — **H6 EXPANSION-SUPPORTED**, locked dual
phrasing "= EARLY-LEADER CONTINUITY": pre-50 founder pruning
*excluded* as the timing locus, `winner_already_dominant_at_tick_50`
rate rises monotonically 0.458 → 0.708 → 0.750 → 0.792 across
hazards {0, 4, 8, 12}).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.35 narrowed the v0.34 secondary observation
(`top_lineage_b50_share` rises monotonically with hazard) to an
**early-leader continuity** locus: the pre-50 birth-count leader
becomes the post-50 b50 winner more often as hazard rises. Pre-50
founder pruning was *excluded* — every founder lineage is alive at
tick 50 in every run, regardless of hazard.

That leaves an open structural question: **is there a heritable
trait signature that distinguishes winning founder lineages from
non-winning ones, and does that signature strengthen with hazard?**

> **Active question:** **Do early-leading / eventual-winning lineages
> differ systematically in inherited founder traits from non-winning
> lineages, with effect sizes that strengthen monotonically with
> hazard?**

This is a **targeted post-hoc follow-up** on v0.35. It is NOT a sim
mechanics change, NOT a heritability mechanism declaration, NOT a
HedonismPolicy comparison, NOT a new sweep, NOT a broad trait-mining
exploration. v0.36 stays post-hoc one more step.

### Trait inventory (read once, before pre-reg locks)

`trait_fingerprints.csv` carries 13 heritable trait columns per
agent. Schema is byte-identical across v0.25 / v0.32 / v0.33 streams
(verified by inspection of one run from each stream; same column
order, same dtypes). Each agent has one row; founders have empty
`parent_id`; descendants inherit the parent vector with a small
per-trait perturbation (verified by inspection: typically one or two
trait coordinates drift per generation, the rest are byte-identical
to parent).

| # | trait | mechanistic role |
|--:|---|---|
| 1 | `hunger_pain_sensitivity`   | weights hunger drive in policy |
| 2 | `injury_pain_sensitivity`   | weights injury drive |
| 3 | `fear_sensitivity`          | weights fear drive |
| 4 | `pleasure_sensitivity`      | weights pleasure |
| 5 | **`reproduction_drive`**    | direct multiplier on birth probability |
| 6 | `novelty_drive`             | weights novelty seek |
| 7 | `uncertainty_aversion`      | weights uncertainty avoid |
| 8 | `pain_tolerance`            | threshold for pain triggering |
| 9 | `risk_tolerance`            | threshold for risk-taking |
| 10 | `memory_strength`          | learning weight |
| 11 | `memory_decay_rate`        | learning forgetting |
| 12 | **`sensor_radius`**         | integer in {1..6}; food-detection range |
| 13 | **`metabolic_rate`**        | per-tick energy depletion |

**Trait-fishing protection:** v0.36 locks a **3-trait primary set**
(bolded above) with pre-committed mechanistic hypotheses and signed
expectations. All other 10 traits are **secondary descriptive only**
and **cannot fire any v0.36 verdict**. The primary set is locked
before any per-lineage trait values are inspected; this doc is the
locking record.

## What this slice tests, and what it does NOT test

### Tests

- Whether the **founder trait vector** of a lineage's tick-0 founder
  predicts whether that lineage becomes the post-50 b50 winner of its
  run.
- Whether the predictor strengthens monotonically with hazard across
  {0, 4, 8, 12}.
- Whether the signed direction of any predictor matches the
  pre-committed mechanistic expectation.
- Anchor identity against v0.34's `run_summary.csv:top_lineage_id`
  AND v0.35's `pre_post_dominance.csv:eventual_top_lineage_id` for
  every (source_version, arm_label, seed). Drift halts.
- Substrate-byte-identity: v0.34 + v0.35 reducers imported without
  modification.

### Does NOT test

- Descendant-trait drift, parent-child trait deltas, or selection
  *within* a lineage. Founder-trait vector only. Descendants are
  not consumed.
- Trait-trait correlations or multivariate distance. Per-trait
  univariate Cohen's d only.
- Causal mechanism declaration. Even a clean
  H_TRAIT-LINKED-AND-STRENGTHENING verdict identifies a *correlation*
  consistent with heritable-trait selection on this corpus; it does
  not declare that a specific trait causes early-leader continuity.
- p-values or statistical significance. Effect-size thresholds only,
  consistent with v0.30..v0.35 discipline.
- Multiple-comparison-correction beyond the small-family
  pre-commitment (3 primary traits). No Bonferroni; no FDR. The
  pre-committed 3-trait set IS the family-wise control.
- HedonismPolicy comparisons. Deferred until at least v0.37.
- Mesa migration. Closed indefinitely.
- Sim-mechanics changes; `src/` modifications. Zero.
- New sweeps; new seed streams; new chambers; new hazards.
- The 10 secondary traits are reported descriptively but cannot fire
  the verdict, no matter how large their winner-vs-nonwinner
  Cohen's d.
- Tick-50 LEADER-vs-non-leader comparisons (different from
  WINNER-vs-non-winner). The user-locked v0.36 question targets
  eventual-winner vs non-winning lineages. Tick-50 leader as a
  predictor is descriptive only.

### Deferred (v0.37+ candidates, conditional on v0.36 outcome)

- **If H_TRAIT-LINKED-AND-STRENGTHENING fires.** v0.37 candidate:
  fresh-stream calibration analogous to v0.30..v0.33 — replay the
  primary-trait verdict on a fresh seed range to test whether the
  effect compounds across streams.
- **If H_TRAIT-LINKED-FLAT fires.** v0.37 candidate: descendant-trait
  drift lens (parent-child trait perturbation + survival/reproduction
  by perturbation magnitude). The flat-with-hazard pattern is more
  consistent with neutral-drift selection than with hazard-amplified
  selection.
- **If H_TRAIT-NEUTRAL fires.** v0.37 candidate: chamber-axis
  exploration (food_ladder, larger chambers) — the founder-trait
  null on tight_gradient may reflect chamber geometry dominating
  over trait variation.

## Conservation framing — unchanged from v0.20..v0.35

No new conservation contract. No mutations to `core/`, `model.py`,
`experiments/fear_hunger_chamber.py`,
`experiments/population_dynamics.py`,
`policies/gradient_policy.py`, `policies/hedonism_policy.py`. No
mutations to existing arm tuples. No mutations to
[[scripts/lineage_replay.py]] or
[[scripts/lineage_survival_replay.py]]. No new event types, no new
chamber, no new policy. Source modifications are **zero**. v0.36 is
a third post-hoc reducer that imports v0.34 + v0.35 helpers
additively and writes new CSVs under a new output directory.

## Mechanism

v0.36 is one new script plus one new tests file plus this doc.

1. **Reducer** ([[scripts/trait_replay.py]]). Imports v0.34 helpers
   from [[scripts/lineage_replay.py]] via `importlib.util` (the
   established pattern). v0.35's `pre_post_dominance.csv` is read
   from disk for the re-anchor.

   Pure-function pipeline:
   - `parse_trait_fingerprints(run_dir)` — read
     `trait_fingerprints.csv`, return `{agent_id: dict[str, float]}`
     covering all 13 trait columns.
   - For each run, identify the 5 founders via v0.34's
     `assign_founder_lineages` (founder = `parent_id is None`);
     index founder traits by `lineage_id`.
   - Re-derive `eventual_top_lineage_id` per run via v0.34's
     `summarise_run` (lineage with max `b50_count`; lowest
     lineage_id wins ties).
   - Cross-anchor (halts on drift):
     - v0.34 anchor: `top_lineage_id` matches
       `runs/lineage-v0.34/run_summary.csv` for every (source, arm,
       seed).
     - v0.35 anchor: `eventual_top_lineage_id` matches
       `runs/lineage-v0.35/pre_post_dominance.csv` for every
       (source, arm, seed).
   - For each run, label the 5 founders as winner=True for
     `lineage_id == eventual_top_lineage_id` else winner=False.
     Founders in runs with `eventual_top_lineage_id is None`
     (`total_b50 == 0`; none in the 96-run corpus by v0.34's
     `n_runs_total_b50_zero == 0` per hazard, but defensive)
     are excluded from the comparison entirely.
   - For each (hazard, primary_trait), compute:
     - `mean_winner(h, t)` = mean trait value over the 24 winner
       founders at hazard h.
     - `mean_nonwinner(h, t)` = mean trait value over the (24 × 4)
       = 96 non-winner founders at hazard h.
     - `pooled_std(h, t)` = sqrt((var_winner * (n_w - 1) +
       var_nonwinner * (n_nw - 1)) / (n_w + n_nw - 2)).
     - `signed_d(h, t)` = (`mean_winner` − `mean_nonwinner`) /
       `pooled_std`.
     - `abs_d(h, t)` = |`signed_d(h, t)`|.
     - `sign_aligned(t)` = sign(`signed_d(h, t)`) ==
       `EXPECTED_SIGN[t]`. (Computed per hazard; reported per
       hazard.)
   - Three-way verdict: see "Decision rules" below.

   Outputs four CSVs under `runs/lineage-v0.36/` (gitignored):
   - `founder_traits.csv` — per (run × founder) = 480 rows × 13
     trait columns + `is_winner` flag.
   - `winner_vs_nonwinner_by_hazard.csv` — per (hazard × trait) =
     4 × 13 = 52 rows: signed_d, abs_d, sign_aligned, mean_winner,
     mean_nonwinner, pooled_std, n_winner, n_nonwinner.
   - `primary_strengthening.csv` — per primary trait (3 rows):
     |d(h=0)|, |d(h=4)|, |d(h=8)|, |d(h=12)|, monotone_non_decreasing,
     spread, signed_at_h12, sign_aligned_at_h12,
     classification ∈ {`aligned`, `opposite-sign`, `below-threshold`}.
   - `trait_verdict.csv` — single row: verdict, reasoning.

2. **Locked constants** (committed in code at reducer entry):
   ```
   PRIMARY_TRAITS: tuple[str, ...] = (
       "reproduction_drive",
       "metabolic_rate",
       "sensor_radius",
   )
   EXPECTED_SIGN: dict[str, int] = {
       "reproduction_drive": +1,
       "metabolic_rate": -1,
       "sensor_radius": +1,
   }
   SECONDARY_TRAITS: tuple[str, ...] = (...10 traits...)
   ABS_D_THRESHOLD: float = 0.4
   STRENGTHENING_SPREAD_THRESHOLD: float = 0.2
   V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
   V0_35_PRE_POST_DOMINANCE: Path = Path(
       "runs/lineage-v0.35/pre_post_dominance.csv"
   )
   OUT_DIR: Path = Path("runs/lineage-v0.36")
   ```

### Determinism — anchors

- v0.21..v0.35 events.jsonl + sidecar artifacts on disk are not
  regenerated. `trait_fingerprints.csv` is read verbatim.
- v0.21..v0.35 test suites continue to pass (additive guard).
- [[scripts/lineage_replay.py]] and
  [[scripts/lineage_survival_replay.py]] are imported, not modified.
- Re-anchor against v0.34's `run_summary.csv:top_lineage_id` AND
  v0.35's `pre_post_dominance.csv:eventual_top_lineage_id` (96 runs);
  halt on any drift.

### Wall time estimate

- Reducer: < 5s on the 96-run corpus. Trait-file I/O is on the order
  of 96 small CSVs; per-trait reductions are O(N_founders) per
  hazard.

## Observables — pre-committed before reading the data

### Per-founder

- `founder_trait_vector(lineage_id, run)` — 13-dim vector from
  `trait_fingerprints.csv` keyed by founder `agent_id`.
- `is_winner(lineage_id, run)` — `lineage_id == eventual_top_lineage_id`.

### Per-(hazard × trait)

- `mean_winner(h, t), mean_nonwinner(h, t), pooled_std(h, t)`.
- `signed_d(h, t)`, `abs_d(h, t)` — Cohen's d, signed and absolute.
- `sign_aligned(h, t)` — boolean, sign(signed_d) == EXPECTED_SIGN[t]
  (only meaningful for primary traits).

### Per-primary-trait (3 traits)

- `monotone_non_decreasing(t)` — `|d(0)| <= |d(4)| <= |d(8)| <= |d(12)|`.
- `spread(t) = abs_d(h=12, t) - abs_d(h=0, t)`.
- `crosses_threshold_at_h12(t)` — `abs_d(h=12, t) >= 0.4`.
- `strengthens(t)` — `monotone_non_decreasing(t) AND spread(t) >= 0.2`.
- `classification(t)` ∈ {
    "aligned-and-strengthening",
    "aligned-flat",
    "opposite-sign-strengthening",
    "opposite-sign-flat",
    "below-threshold"
  } — derived from
  `(crosses_threshold_at_h12, sign_aligned_at_h12, strengthens)`.

### Descriptive (NOT used by verdict)

- 10 secondary traits' winner-vs-nonwinner d values per hazard.
  Reported in `winner_vs_nonwinner_by_hazard.csv`. Cannot fire the
  v0.36 verdict, no matter the magnitude.
- Per-trait `mean_winner`, `mean_nonwinner`, `pooled_std`, `n`.
- Founder-trait variance within hazard.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive reuse of v0.34 + v0.35 helpers).** v0.36 imports
  `STREAM_CONFIGS`, `parse_agent_lifetimes`, `parse_config`,
  `parse_manifest`, `assign_founder_lineages`,
  `compute_generation_depths`, `LineageReplayError`,
  `summarise_run` (or its components) from
  [[scripts/lineage_replay.py]] without modification. v0.36 reads
  v0.35's `pre_post_dominance.csv` from disk for the re-anchor.
- **H1b (v0.34 anchor re-assertion).** `B_POOL_ANCHORS = {4: 312,
  8: 321, 12: 312}` and `EXPECTED_FOUNDERS = 5` are re-asserted at
  v0.36 reducer entry.
- **H2a (v0.34 anchor).** Re-derived per-run `top_lineage_id` MUST
  equal v0.34's `runs/lineage-v0.34/run_summary.csv:top_lineage_id`
  for every (source, arm, seed). Halts on drift.
- **H2b (v0.35 anchor).** Re-derived per-run
  `eventual_top_lineage_id` MUST equal v0.35's
  `runs/lineage-v0.35/pre_post_dominance.csv:eventual_top_lineage_id`
  for every (source, arm, seed). Halts on drift.
- **H2c (founder-trait completeness).** Every founder identified by
  v0.34's `assign_founder_lineages` (5 per run × 96 runs = 480) MUST
  have a matching row in `trait_fingerprints.csv` with all 13 trait
  columns non-empty. Halts on missing.
- **H3 (additive guard).** v0.21..v0.35 prior tests still pass after
  v0.36 additions.
- **H4 (no mutation of pre-v0.36 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before and
  after v0.36.

### Cautious form — three-way verdict on v0.36's question

The decision rule is intentionally three-way (mutually exclusive by
construction). The 3-trait primary set is the family-wise control;
no Bonferroni correction is applied beyond it.

**Per-trait absolute-d magnitude rule (locked):**
- `crosses_threshold(t) := abs_d(h=12, t) >= 0.4`.

**Per-trait strengthening rule (locked):**
- `monotone_non_decreasing(t) := abs_d(0,t) <= abs_d(4,t) <= abs_d(8,t) <= abs_d(12,t)`.
- `spread(t) := abs_d(12,t) - abs_d(0,t)`.
- `strengthens(t) := monotone_non_decreasing(t) AND spread(t) >= 0.2`.

**Per-trait sign-alignment rule (locked):**
- `sign_aligned_at_h12(t) := sign(signed_d(12, t)) == EXPECTED_SIGN[t]`.
- `EXPECTED_SIGN = {reproduction_drive: +1, metabolic_rate: -1, sensor_radius: +1}`.

**Three-way verdict:**

1. **H5 — TRAIT-LINKED-AND-STRENGTHENING.** **FIRES iff** there
   exists a primary trait `t` with:
   - `crosses_threshold(t) == True` AND
   - `strengthens(t) == True` AND
   - `sign_aligned_at_h12(t) == True`.
   Headline: founder-trait endowment predicts post-50 lineage
   dominance, with the predictor strengthening with hazard, and the
   sign of the effect aligning with the pre-committed mechanistic
   expectation.

2. **H6 — TRAIT-LINKED-FLAT.** **FIRES iff** H5 does NOT fire AND
   there exists a primary trait `t` with `crosses_threshold(t) ==
   True`. Headline: founder-trait endowment differs between winners
   and non-winners at h=12, but either does not strengthen
   monotonically with hazard, or strengthens with the wrong sign.

3. **H7 — TRAIT-NEUTRAL.** **FIRES iff** no primary trait has
   `crosses_threshold(t) == True`. Headline: founder-trait endowment
   does not predict post-50 lineage dominance at the locked
   effect-size threshold on this corpus.

### Locked phrases for each verdict

> **H5 phrase:** "Founder-trait signature predicts post-50 dominance
> on the v0.34 corpus, with effect strengthening monotonically with
> hazard. Correlational; not a mechanism declaration."

> **H6 phrase:** "Founder-trait signature differs between winners and
> non-winners at h=12 but does not strengthen with hazard with the
> expected sign; the winning-lineage prediction is not consistent
> with hazard-amplified heritable selection on this corpus."

> **H7 phrase:** "No founder-trait predictor of post-50 dominance
> clears the locked effect-size threshold on this corpus; founder-
> trait endowment does not detectably predict winning lineage
> identity at this scale."

### Opposite-sign protection (non-verdict note, locked)

If a primary trait crosses `abs_d(h=12) >= 0.4` with the **opposite
sign** of its `EXPECTED_SIGN`, the trait's classification is
`opposite-sign-strengthening` or `opposite-sign-flat` and the trait
**cannot fire H_TRAIT-LINKED-AND-STRENGTHENING**. It contributes to
H_TRAIT-LINKED-FLAT (via the magnitude rule) but the Results
section MUST label the finding as opposite-sign and surface it as a
contradiction of the proposed mechanism, not as confirmation.

Example: if `metabolic_rate` shows `signed_d(h=12) = +0.6` (winners
have HIGHER metabolic_rate than non-winners), `crosses_threshold` is
True, `strengthens` may be True, but `sign_aligned_at_h12` is False
(EXPECTED_SIGN is −1). The verdict cannot be H5; it is at most H6.
The Results section must explicitly note that the finding contradicts
the proposed survival-cost story.

### Verdict reachability — sanity check

We have no prior data on per-trait Cohen's d in this corpus. The
threshold is set to be conservative enough to avoid narrating tiny
differences (Cohen's d ≥ 0.4 is between "small" and "medium") but
loose enough to admit a meaningful exploratory result.

- **H5** fires if at least one of three named traits shows a
  meaningful effect that strengthens with hazard with the right sign.
  Genuinely live: hazard-amplified heritable selection is the most
  parsimonious story for v0.35's early-leader-continuity finding.
- **H6** fires if any primary trait shows a meaningful effect at
  h=12 but does not meet all three (sign + strengthening + magnitude)
  conditions. Genuinely live: trait differences may exist but be
  hazard-independent (drift / sampling artifact) or mechanistically
  surprising (opposite sign).
- **H7** fires if no primary trait meets the magnitude bar.
  Genuinely live: with 24 winners vs 96 non-winners per hazard, a
  null result would mean founder-trait endowment is essentially
  uninformative for predicting winning at this corpus size.

### Anchor identity

No v0.36 cross-version artifact-identity anchor (no v0.36 H9). v0.34
+ v0.35 anchors already cover the underlying lineage assignments.
v0.36's outputs are reductions of the same on-disk corpus, with
re-anchor against both prior reductions.

## Decision rules

| verdict | decision | v0.37+ candidate |
|---|---|---|
| H5 TRAIT-LINKED-AND-STRENGTHENING | founder-trait endowment is hazard-amplified predictor of winning | v0.37 fresh-stream calibration on the firing primary trait |
| H6 TRAIT-LINKED-FLAT | founder-trait differences exist but hazard-independent or wrong-sign | v0.37 descendant-drift lens (parent-child trait perturbation by survival) |
| H7 TRAIT-NEUTRAL | founder-trait endowment is not a detectable predictor on this corpus | v0.37 chamber-axis exploration (chamber geometry may dominate) |

**Independent of the verdict, v0.37+ remains post-hoc.** v0.36 closes
the targeted founder-trait follow-up; HedonismPolicy and Mesa remain
deferred indefinitely.

Halt conditions:
- **H1 / H1b fail** — v0.34 / v0.35 surface mutated. Halt; revert.
- **H2a / H2b fail** — re-anchor mismatch. Halt; investigate (likely
  algorithm divergence or drift).
- **H2c fails** — founder is missing from `trait_fingerprints.csv`,
  or a trait column is empty. Halt.
- **H3 / H4 fail** — a v0.21..v0.35 contract was broken by v0.36
  additions. Halt; revert.

## Out of scope (v0.36)

- Descendants. Only founders are consumed.
- The 10 secondary traits cannot fire the verdict (descriptive only).
- Multivariate trait distance / PCA / clustering.
- p-values, statistical significance tests, Bonferroni / FDR /
  permutation tests.
- Lineage-mean trait vectors (averages over founders + descendants).
  Reserved for v0.37+ if the founder-only result warrants.
- Tick-50 leader-vs-nonleader trait comparison. Different question
  from winner-vs-nonwinner; descriptive only if reported.
- Trait-trait correlations.
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications.
- New sweeps; new seed streams.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- Mechanism declaration. Even a clean H5 verdict identifies a
  *correlation* consistent with heritable selection; promotion
  requires fresh-stream calibration (v0.37 candidate).
- Edits to any prior `scripts/v0.NN_*.py`,
  [[scripts/lineage_replay.py]], or
  [[scripts/lineage_survival_replay.py]].

## Implementation notes

### File-level changes

- **New:** [[scripts/trait_replay.py]] — post-hoc reducer (~280 LOC).
  Imports `lineage_replay` via `importlib.util`. Defines locked
  constants, dataclasses (`FounderTraitRow`,
  `WinnerVsNonwinnerRow`, `PrimaryStrengtheningRow`, `VerdictRow`),
  pure-function pipeline, three-way verdict logic, and `main()`.
- **New:** `tests/test_trait_replay.py` — synthetic-fixture tests
  covering: trait parsing, founder-trait extraction, signed/abs d
  computation on hand-built fixtures, sign_aligned per primary
  trait, monotone_non_decreasing on hand-built sequences,
  strengthening predicate, classification logic for all 5
  classifications, three-way verdict for all four indicator-pair
  states (H5 fires, H6 fires via flat-aligned, H6 fires via
  opposite-sign-strengthening, H7 fires), re-anchor halt on drift,
  founder-missing-from-trait-file halt, end-to-end on tmp_path
  synthetic corpus. Estimate ~22 tests, ~280 LOC.
- **No changes** to [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]], any `scripts/v0.NN_*.py`,
  `core/`, `model.py`, chamber / population / policy modules.
- **Documented:** this file. Results appended after the reducer
  runs.

### Determinism contract

- v0.21..v0.35 events.jsonl + sidecar artifacts not regenerated.
- v0.21..v0.35 test suites continue to pass.
- v0.34 + v0.35 reducers imported but not modified.
- Per-run double anchor against v0.34 `run_summary.csv` and v0.35
  `pre_post_dominance.csv`.

### LOC estimate

- `scripts/trait_replay.py`: ~280 LOC.
- `tests/test_trait_replay.py`: ~280 LOC.
- This doc: ~520 LOC.

Total v0.36: ~1,080 LOC. Tests should bring the suite from 924 to
~946 (+~22).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   924 passed
uv run python scripts/core_smoke_test.py  ok
```

## References

- [[docs/experiments/fear_hunger_v0.35.md]] — v0.35 founder-survival-
  timing replay; H6 EXPANSION-SUPPORTED (= EARLY-LEADER CONTINUITY)
  fires; supplies the per-run winner identity v0.36 re-anchors
  against.
- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; supplies the founder-lineage assignment and the
  primary `top_lineage_b50` anchor.
- [[scripts/lineage_replay.py]] — v0.34 reducer; **imported by v0.36
  without modification**.
- [[scripts/lineage_survival_replay.py]] — v0.35 reducer; v0.36 reads
  its `pre_post_dominance.csv` output as the re-anchor source.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

**Status:** executed 2026-05-06. Reducer ([[scripts/trait_replay.py]])
ran over the same 96-run corpus v0.34 / v0.35 reduced. Outputs under
`runs/lineage-v0.36/` (gitignored). Re-anchor (H2a + H2b) against
v0.34's `run_summary.csv:top_lineage_id` AND v0.35's
`pre_post_dominance.csv:eventual_top_lineage_id` passed for all 96
runs (no mismatch). All invariants (H1, H1b, H2c, H3, H4) held.

### Headline

**Verdict: H6 — TRAIT-LINKED-FLAT.** Firing trait: **`sensor_radius`**
(`aligned-flat`).

> **Locked H6 phrase:** "Founder-trait signature differs between
> winners and non-winners at h=12 but does not strengthen with hazard
> with the expected sign; the winning-lineage prediction is not
> consistent with hazard-amplified heritable selection on this
> corpus."

The verdict fires because `sensor_radius` clears the magnitude bar
at h=12 with the expected sign, but its effect does not strengthen
monotonically with hazard. Neither `reproduction_drive` nor
`metabolic_rate` clears the magnitude bar at h=12. Per the locked
pre-reg rule (and the locked opposite-sign protection), v0.36
**cannot** declare H_TRAIT-LINKED-AND-STRENGTHENING on this corpus.

### Per-primary-trait classification

| trait | expected_sign | \|d\|(h=0) | \|d\|(h=4) | \|d\|(h=8) | \|d\|(h=12) | signed_d(h=12) | mono | spread | crosses | aligned | classification |
|---|---:|------:|------:|------:|------:|------:|---:|------:|---:|---:|---|
| `sensor_radius` | +1 | 1.183 | 1.351 | 1.307 | **1.265** | **+1.265** | False | +0.082 | **True** | **True** | **aligned-flat** |
| `reproduction_drive` | +1 | 0.551 | 0.206 | 0.028 | 0.158 | +0.158 | False | −0.393 | False | True | below-threshold |
| `metabolic_rate` | −1 | 0.555 | 0.469 | 0.248 | 0.255 | −0.255 | False | −0.300 | False | True | below-threshold |

`mono` = weak monotone non-decreasing across {0, 4, 8, 12}.
`spread` = `|d|(h=12) − |d|(h=0)`.
`crosses` = `|d|(h=12) ≥ 0.4`.
`aligned` = `sign(signed_d(h=12)) == EXPECTED_SIGN`.

### Per-trait per-hazard means (winner vs non-winner)

| hazard | trait | n_w | n_nw | mean_winner | mean_nonwinner | pooled_std | signed_d |
|-------:|---|---:|---:|------:|------:|------:|------:|
| 0  | reproduction_drive | 24 | 96 | 1.011 | 1.466 | 0.826 | **−0.551** |
| 4  | reproduction_drive | 24 | 96 | 1.236 | 1.410 | 0.843 | −0.206 |
| 8  | reproduction_drive | 24 | 96 | 1.394 | 1.370 | 0.846 | +0.028 |
| 12 | reproduction_drive | 24 | 96 | 1.482 | 1.348 | 0.845 | +0.158 |
| 0  | metabolic_rate | 24 | 96 | 1.070 | 1.313 | 0.439 | **−0.555** |
| 4  | metabolic_rate | 24 | 96 | 1.099 | 1.306 | 0.442 | −0.469 |
| 8  | metabolic_rate | 24 | 96 | 1.176 | 1.287 | 0.447 | −0.248 |
| 12 | metabolic_rate | 24 | 96 | 1.173 | 1.287 | 0.447 | −0.255 |
| 0  | sensor_radius | 24 | 96 | **5.125** | **3.250** | 1.585 | **+1.183** |
| 4  | sensor_radius | 24 | 96 | **5.292** | **3.208** | 1.543 | **+1.351** |
| 8  | sensor_radius | 24 | 96 | **5.250** | **3.219** | 1.554 | **+1.307** |
| 12 | sensor_radius | 24 | 96 | **5.208** | **3.229** | 1.565 | **+1.265** |

### Why H_TRAIT-LINKED-AND-STRENGTHENING does NOT fire

For H5 to fire, a primary trait must satisfy three locked conditions
*at h=12*: (a) `|d| ≥ 0.4`, (b) monotone non-decreasing across
{0, 4, 8, 12} with spread ≥ 0.2, and (c) signed direction matches
EXPECTED_SIGN.

- `sensor_radius` satisfies (a) and (c) but fails (b): `|d|` peaks
  at h=4 (1.351) and slightly declines through h=12 (1.265). The
  spread (h=12 − h=0) is **+0.082**, well below the locked +0.2
  threshold. Classification: `aligned-flat`.
- `reproduction_drive` and `metabolic_rate` both fail (a) — neither
  reaches `|d| ≥ 0.4` at h=12 (0.158 and 0.255 respectively).
  Classification: `below-threshold` for both.

H5 is unreachable on this data.

### Why H6 TRAIT-LINKED-FLAT fires (not H7)

For H7 to fire, no primary trait may have `|d|(h=12) ≥ 0.4`.
`sensor_radius` clears that bar at 1.265, so H7 is excluded.
`sensor_radius` is the lone firing trait under the locked H6
condition.

### Cautious framing — locked dual phrasing preserved

> **The v0.36 verdict is correlational and timing-locus level only.**
> It does NOT declare a heritable mechanism. v0.36 identifies a
> founder-trait signature (`sensor_radius`) that distinguishes
> winning from non-winning lineages on the v0.34 corpus, with effect
> magnitudes at all four hazards. It explicitly does NOT find that
> the signature strengthens with hazard.

> **The v0.35 early-leader-continuity finding is NOT explained by
> hazard-amplified founder-trait selection on this corpus.** The
> primary trait whose effect we hypothesised would amplify with
> hazard (`reproduction_drive`) does not even clear the magnitude
> threshold at h=12. The trait that does clear the threshold
> (`sensor_radius`) is essentially hazard-independent.

### Secondary observations (NOT pre-committed; descriptive only)

These are striking but explicitly outside the verdict logic. They
must not be promoted to mechanism claims without fresh-stream
calibration.

**1. `sensor_radius` is the strongest founder-trait predictor of
winning observed in this exploratory lens.** Winners' founders
average sensor_radius ≈ 5.2 (out of 6 max; >87% of the trait's
maximum value); non-winners average ≈ 3.2. The Cohen's d magnitude
(1.18–1.35) is in "very large effect" range across all four hazards.
The effect is robust to hazard but does not amplify with it.

**2. `reproduction_drive` shows a signed-direction inversion across
the hazard axis.** At h=0, winners have *lower* reproduction_drive
than non-winners (signed_d = **−0.551**, OPPOSITE the expected sign
of +1). At h=8 the effect crosses zero. At h=12 the sign aligns
with expectation but the magnitude is small (signed_d = +0.158).
Per the locked opposite-sign protection: this is a descriptive
opposite-sign observation at h=0 only; the locked verdict
classification at h=12 is `below-threshold`. The mechanistic story
("higher reproduction_drive → more births → winning") is NOT
supported by the h=0 data and is at most weakly supported by the
h=12 data.

**3. `metabolic_rate` is aligned at all hazards but attenuates with
hazard.** Winners have lower metabolic_rate at every hazard
(signed_d ranges −0.555 to −0.248), but the effect halves between
h=0 and h=12. This is the OPPOSITE of "hazard-amplified": the
predictor weakens as hazard rises. Below-threshold at h=12.

**4. Combined narrative (cautious).** On this corpus,
heritable-trait differences between winners and non-winners
EXIST and are mostly aligned with mechanistic expectations at low
hazard, but they DON'T strengthen with hazard — they either stay
flat (sensor_radius) or attenuate (metabolic_rate, reproduction_drive).
This is more consistent with a "fixed selection ceiling" or
"selection saturated by chamber geometry" story than with
"hazard amplifies heritable selection." It does NOT close the
question of what causes early-leader continuity to strengthen with
hazard, but it rules out the simplest founder-trait-amplification
story.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | v0.34 helpers imported additively; no modification to `lineage_replay.py` or `lineage_survival_replay.py` | **HOLDS.** Imports succeed; constants byte-match. |
| H1b | `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` and `EXPECTED_FOUNDERS = 5` re-asserted | **HOLDS.** |
| H2a | Re-derived `top_lineage_id` byte-identical to v0.34 `run_summary.csv` | **HOLDS.** All 96 runs match. |
| H2b | Re-derived `eventual_top_lineage_id` byte-identical to v0.35 `pre_post_dominance.csv` | **HOLDS.** All 96 runs match. |
| H2c | Every founder has all 13 trait columns non-empty in `trait_fingerprints.csv` | **HOLDS.** 480/480 founders matched. |
| H3 | v0.21..v0.35 prior tests pass after v0.36 additions | **HOLDS.** Suite 924 → 972 (+48 v0.36 tests); all green. |
| H4 | Pre-v0.36 surface byte-unchanged | **HOLDS.** Zero edits to `lineage_replay.py`, `lineage_survival_replay.py`, prior `v0.NN_*.py`, `comparison_grid.py`, `core/`, `model.py`, chamber / population / policy modules. |
| H5 | TRAIT-LINKED-AND-STRENGTHENING | **FAILS.** No primary trait clears `|d|(h=12) ≥ 0.4` AND strengthens AND sign-aligned simultaneously. |
| H6 | TRAIT-LINKED-FLAT | **FIRES.** `sensor_radius` is `aligned-flat` (`|d|(h=12) = 1.265 ≥ 0.4`, but spread = +0.082 < 0.2 and not monotone). |
| H7 | TRAIT-NEUTRAL | **FAILS** (H6 fires). |

### What this means for the v0.35 early-leader-continuity finding

v0.35 narrowed the v0.34 monotone-with-hazard observation
(`top_lineage_b50_share` rising 0.635 → 0.785) to an early-leader
continuity locus. v0.36 narrows further:

- **Founder-trait endowment matters.** `sensor_radius` is a very
  large founder-trait predictor of winning at all hazards.
- **Founder-trait amplification with hazard is NOT supported.** The
  early-leader-continuity strengthening with hazard is NOT explained
  by founder-trait differences becoming more pronounced as hazard
  rises. The candidate primary traits either don't strengthen
  (`sensor_radius`) or weaken (`metabolic_rate`, `reproduction_drive`)
  as hazard rises.
- **Open question.** What does cause `winner_already_dominant_at_tick_50`
  to rise with hazard, given that founder traits don't show
  hazard-amplified separation? Two non-exhaustive candidates: (i)
  hazard-induced selection on **descendant-trait drift** (winners'
  lineages may accumulate trait perturbations that selection favors
  more sharply at high hazard); (ii) **policy-stack non-linearities**
  whereby modest founder-trait differences map onto larger fitness
  differences at high hazard via the mediating policy. Neither is
  tested by v0.36; both are deferred candidates.

### Cautious forward-reference phrasing

For v0.34 / v0.35 / v0.36 forward-mention sites:

> Founder-trait endowment is a robust predictor of post-50 lineage
> dominance on the v0.34 corpus, dominated by `sensor_radius` (winner
> founders' mean ≈ 5.2 vs non-winner mean ≈ 3.2; Cohen's d ≈ 1.2–1.35
> across all four hazards). The signature does NOT strengthen with
> hazard: spread |d|(h=12) − |d|(h=0) for `sensor_radius` is +0.082,
> below the pre-committed +0.2 threshold. The two other primary
> traits hypothesised to amplify with hazard (`reproduction_drive`,
> `metabolic_rate`) fail to clear the magnitude threshold at h=12.
> Hazard-amplified founder-trait selection is therefore NOT the
> mechanism for v0.35's early-leader continuity finding on this
> corpus.

### Implementation summary

- **New script:** `scripts/trait_replay.py` (~600 LOC). Imports
  `lineage_replay.py` helpers via `importlib.util`. Pure-function
  pipeline producing four CSVs.
- **New tests:** `tests/test_trait_replay.py` (~660 LOC; **48
  tests**). Suite **924 → 972** (+48); all green.
- **Pre-reg-locked constants in code:** `PRIMARY_TRAITS`,
  `EXPECTED_SIGN`, `SECONDARY_TRAITS`, `ABS_D_THRESHOLD = 0.4`,
  `STRENGTHENING_SPREAD_THRESHOLD = 0.2`.
- **Double re-anchor:** v0.34 `run_summary.csv:top_lineage_id` AND
  v0.35 `pre_post_dominance.csv:eventual_top_lineage_id`. All 96
  runs match both anchors byte-identical.
- **Zero edits** to `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`, prior `scripts/v0.NN_*.py`,
  `src/`, or any pre-v0.36 module.
- **CI gate at handoff time:**
  ```
  uv run ruff check .                                   ok
  uv run ruff format --check .                          ok
  uv run pytest                                         972 passed
  uv run python scripts/core_smoke_test.py              ok
  uv run python scripts/trait_replay.py                 H6 TRAIT-LINKED-FLAT
                                                        (sensor_radius firing)
  ```

## Conclusion

v0.36 fires **H6 — TRAIT-LINKED-FLAT** on the 96-run v0.34 corpus.
`sensor_radius` is the firing primary trait: winner founders have
sensor_radius means of 5.1–5.3 across all four hazards, vs
non-winner means of 3.2 across all four hazards (Cohen's d
1.18–1.35, robustly aligned with the expected positive sign).
However, the effect does NOT strengthen monotonically with hazard;
the spread `|d|(h=12) − |d|(h=0)` is +0.082, well below the locked
+0.2 threshold. Neither `reproduction_drive` nor `metabolic_rate`
clears the magnitude threshold at h=12 (0.158 and 0.255
respectively). The locked H6 phrase is the verdict:

> **"Founder-trait signature differs between winners and non-winners
> at h=12 but does not strengthen with hazard with the expected
> sign; the winning-lineage prediction is not consistent with
> hazard-amplified heritable selection on this corpus."**

Decision:
- **Founder-trait endowment is a robust predictor of post-50 lineage
  dominance**, dominated by `sensor_radius`. This is a meaningful
  exploratory finding even though it does not fire H5.
- **Hazard-amplified founder-trait selection is NOT the mechanism
  for v0.35's early-leader continuity** on this corpus. The primary
  traits' effects either stay flat with hazard (`sensor_radius`) or
  weaken (`metabolic_rate`, `reproduction_drive`).
- **A descriptive opposite-sign observation at h=0 for
  `reproduction_drive`** (winners have *lower* reproduction_drive
  than non-winners; signed_d = −0.55 vs expected +1) is logged but
  does NOT fire any verdict per the locked rule (`crosses_threshold`
  is checked at h=12 only). It is mechanistically suggestive — under
  food-limited h=0, lower reproduction_drive may be optimal — but
  promotion requires fresh-stream calibration.
- **v0.37 candidates** (per the pre-reg's deferred-list):
  descendant-trait drift lens (parent-child trait perturbation +
  survival/reproduction by perturbation magnitude) is the most direct
  follow-up given that founder-trait amplification is excluded as a
  mechanism for early-leader continuity. Chamber-axis exploration is
  the broader follow-up. HedonismPolicy comparisons remain deferred.
