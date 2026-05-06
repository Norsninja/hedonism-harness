# v0.30 — tight w*=0.75 small-margin robustness audit (single target)

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.30-small-margin-robustness-audit`
**Predecessors:** v0.21..v0.27 (chamber × hazard × influx × weight
characterisation; see v0.29 for the full chain), v0.28 (food_ladder
w=0.75 dip = 2-of-8 seed concentration; H6), v0.29 (food_ladder dip
does not reproduce on seeds 9..16; H9 fires; secondary finding —
food_ladder w=0.5 vs w=1.0 optimum reverses across seed streams;
**methodological rule introduced**).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.27 reported a weak interior optimum on the **tight_gradient**
chamber at hazard=8 on the avoidance-weight axis:

| w | 0.00 | 0.25 | 0.50 | **0.75** | 1.00 |
|---|-----:|-----:|-----:|---------:|-----:|
| b>50 | 107 | 112 | 113 | **118** | 116 |

The v0.27 H8 fired *at* the pre-committed +2-birth boundary (w=0.75
beats w=1.0 by exactly +2; w=0.75 beats w=0.50 by +5). The v0.27 doc
itself flagged the result: "a fresh seed stream could plausibly flip
the interior-optimum / saturation reading on tight."

v0.29 made the methodological rule explicit:

> **At 8 seeds, do not promote small aggregate optima into mechanisms
> unless they reproduce across a fresh seed stream or have strong
> per-seed consistency.**

v0.30 audits the v0.27 tight w*=0.75 finding under that rule. The
audit re-runs the 3-arm cell (w ∈ {0.5, 0.75, 1.0}) on the **same
fresh seed stream** v0.29 used (seeds 9..16) and partitions the
outcome conservatively across four mutually exclusive classes:
**ROBUST / WEAK / FAILURE / REVERSAL**.

This is a **robustness audit, not a discovery sweep.** It does not
search for new mechanisms. The aggregate robustness classification
is the **primary** verdict; per-seed and trajectory observables are
**supporting evidence only**.

### Why the v0.28 H5/H6/H7 dip-classifier is NOT the v0.30 primary

The v0.28 `run_diagnostic(DiagnosticConfig)` classifier (H5 routing
flip / H6 tail crash / H7 uniform degradation / H8 noise) was
constructed for a *deficit* at w=0.75 on food_ladder — it asks
whether a **valley** at w=0.75 is bimodal, tail-driven, uniform, or
noise. v0.30 audits a **peak** at w=0.75 on tight; the dip-classifier
is the wrong shape. v0.30 ships a new aggregate-classification
surface scoped to peak claims; the v0.28 classifier is left
untouched.

## What this slice tests, and what it does NOT test

### Tests

- Whether the v0.27 tight w*=0.75 +2-birth interior-optimum claim
  reproduces on a fresh seed stream under a stricter operational
  definition (4-tier partition with explicit thresholds).
- Substrate-byte-identity of v0.30 arms to the v0.27 / v0.29 arms
  at the matched labels (by-construction guard).
- Determinism / additive guard: v0.27 / v0.28 / v0.29 prior tests
  continue to pass.

### Does NOT test

- food_ladder. v0.29 closed it for the moment; v0.30 is tight only.
- Weights w ∈ {0.0, 0.25}. The v0.27 monotone-rising portion of the
  curve is not under audit; the audit window is the high-weight
  neighbourhood where the optimum was claimed.
- Other hazards or influxes. Single cell only (h=8, influx=1.0).
- **The v0.25 tight h*=8 hazard-axis interior optimum.** Listed as
  the next priority in the v0.30 handoff but **OUT OF SCOPE for
  this PR** — one target per PR until the methodology stabilises.
  Deferred to v0.31.
- Other ≤6-birth aggregate optima at n=8 from v0.21..v0.27. Deferred.
- Per-agent / lifespan / heritability inspection.
- Reading B substrate seam.
- HedonismPolicy comparisons.
- Fresh seed streams beyond 9..16 (no 17..24 sweep).
- Finer weight grid (w ∈ {0.6, 0.7, 0.8, 0.9}). Out of scope until
  the audit produces a verdict.

### Deferred (v0.31+ candidates, conditional on v0.30 outcome)

- **If H5 ROBUST fires.** Finer weight grid on tight, w ∈ {0.6,
  0.7, 0.75, 0.8, 0.9}, seeds 1..16 pooled — characterise the
  optimum.
- **If H6 WEAK fires.** A third independent seed stream (17..24) on
  the same cell — does the small-margin directional signal compound
  across streams, or is it a coin-flip survivor? The methodological
  rule explicitly **prohibits** promotion on a single Weak result.
- **If H7 FAILURE fires.** No further audit on this cell; demote
  the v0.27 tight w*=0.75 claim to "sample-noise-consistent at n=8."
- **If H8 REVERSAL fires.** No further audit on this cell; demote
  the v0.27 claim and log the cross-stream variance as the dominant
  signal.
- **In any outcome.** Move to the v0.25 tight h*=8 hazard-axis
  audit (v0.31) as the next robustness-audit target.

## Conservation framing — unchanged from v0.20..v0.29

No new conservation contract. No mutations to `world.py` / `body.py`
/ `model.py` / `gradient_policy.py` / `fear_hunger_chamber.py`. No
mutations to existing arm tuples (`ARMS`, `V0_15..V0_27_ARMS`,
`V0_29_ARMS`). Source additions are limited to:

- A literal-subset arm tuple `V0_30_TIGHT_W_ARMS` in
  `comparison_grid.py` (mirrors v0.29 substrate-identity-by-
  construction).
- A new sweep driver and a new audit driver under `scripts/`.
- New tests.

No new event types, no new chamber, no new policy.

## Mechanism

v0.30 is two scripts plus an arm-tuple addition.

1. **Sweep** ([[scripts/v0.30_sweep.py]]). Runs
   `V0_30_TIGHT_W_ARMS` × tight_gradient × seeds 9..16 = 24 runs.
   Substrate parameters: hazard_damage=8, ambient_influx_rate=1.0,
   energy_pool_initial=1500, child_funding_mode=PARENT_TRANSFER_POOL_GAP
   (transfer mode), n_ticks=200, n_founders=5 — all by-construction
   inherited from V0_27_ARMS via the literal-subset constructor.
   Persists per-arm comparison.csv into
   `runs/fear-hunger-v0.30-tight_gradient/`. Mirrors
   [[scripts/v0.29_sweep.py]] verbatim except for the chamber name,
   batch id, and arm tuple.
2. **Audit driver** ([[scripts/v0.30_audit.py]]). Loads per-seed
   observables via the v0.28 `load_all(config)` helper (reused by
   import; no behavior change to the v0.28 module). Computes the
   aggregate `B(w)`, the per-seed `b50` vector, and the per-seed
   favoring count. Applies the 4-tier classifier (H8 → H5 → H6 → H7
   priority). Writes
   `runs/fear-hunger-v0.30-tight_gradient/audit.md` containing:
   aggregate-B table, per-seed b50 + delta table, the outcome line,
   and supporting band-resolved trajectory tables (reusing v0.28
   `_band_aggregate_table`). The supporting tables are **descriptive
   only**; they do not feed the classifier.

The v0.28 `run_diagnostic(DiagnosticConfig)` is **not invoked** from
v0.30 — its H5/H6/H7 dip-classifier is shape-mismatched for a peak
audit. The reusable parts of the v0.28 module are `load_all`,
`_load_seed_observables`, `SeedObservables`, `DiagnosticConfig`, and
`_band_aggregate_table`; v0.30 reuses those and writes its own
classifier + report.

### Determinism — anchors

- v0.30 generates fresh artifacts on a previously-unsimulated cell
  (tight_gradient × seeds 9..16). There is no v0.30 cross-version
  H9-style anchor; the v0.27 / v0.28 / v0.29 anchors already cover
  their respective artifacts.
- The v0.27 events.jsonl artifacts on disk are not regenerated.
- v0.27 / v0.28 / v0.29 test suites continue to pass (additive guard).
- v0.30 sweep is deterministic per the existing
  `run_comparison_grid` contract.

## Observables — pre-committed before reading the data

Per-seed primary:
- `b50(s, w) := sum of AgentBorn events with tick > 50` for
  `s ∈ {9..16}`, `w ∈ {0.5, 0.75, 1.0}`.

Aggregate primary:
- `B(w) := sum_{s ∈ 9..16} b50(s, w)` for `w ∈ {0.5, 0.75, 1.0}`.
- `Δ_low := B(0.75) − B(0.5)`.
- `Δ_high := B(0.75) − B(1.0)`.

Per-seed favoring (primary):
- `seed_favors_w075(s) := b50(s, 0.75) ≥ b50(s, 0.5)
                         AND b50(s, 0.75) ≥ b50(s, 1.0)`.
  (Ties allowed — "directionally consistent".)
- `n_favoring := |{s ∈ 9..16 : seed_favors_w075(s)}|`.

Supporting (descriptive only — not used by the classifier):
- `total_births(w)`, `total_food_events(w)`,
  `total_hazard_entries(w)`, `total_starvation_deaths(w)`,
  `total_injury_deaths(w)` (8-seed sums per arm).
- Routing-channel monotonicity check: hazard entries / injury deaths
  / starvation deaths non-increasing in weight (tight already
  protects against single-visit lethality at every weight per v0.26;
  observable carried for descriptive parity).
- Per-band birth / food / hazard / death tables via
  `_band_aggregate_table`.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (substrate-identity-by-construction).** `V0_30_TIGHT_W_ARMS`
  is a literal subset of `V0_27_ARMS` — every member is the **same**
  `Arm` instance as the matched-label member of V0_27_ARMS (identity,
  not equality). Mirrors v0.29's H6. Halt condition.
- **H1b (cross-version equivalence).** Each `V0_30_TIGHT_W_ARMS`
  member is also the same `Arm` instance as the matched-label
  member of `V0_29_ARMS` (since both v0.29 and v0.30 are 3-arm
  subsets of V0_27_ARMS at the same labels, by symmetry the two
  tuples must be element-wise identical). Tested for explicitness;
  acts as a tripwire if either tuple drifts.
- **H2 (artifact pre-flight).** After the sweep,
  `runs/fear-hunger-v0.30-tight_gradient/arms/hzd8-avd0.{50,75,1.00}/seed-{9..16}/events.jsonl`
  exists and is non-empty for every (seed, weight). Halt condition.
- **H3 (additive guard).** v0.27 / v0.28 / v0.29 prior tests still
  pass after the v0.30 additions. Halt condition.
- **H4 (no mutation of pre-v0.30 arm tuples).** `ARMS`, `V0_15..27_ARMS`,
  `V0_29_ARMS` byte-identical before and after v0.30.

### Cautious form (aggregate robustness partition)

The decision is the **aggregate classification**: exactly one of H5 /
H6 / H7 / H8 fires. Priority order — first match wins. Mutual
exclusivity is by construction.

1. **H8 — REVERSAL.** **FIRES iff**
   `max(B(0.5), B(1.0)) − B(0.75) ≥ 5`.
   A neighbour beats w=0.75 by ≥ 5 births. Headline: the v0.27 tight
   w*=0.75 finding does not reproduce, **and** the optimum has moved
   on the fresh stream. Mechanism reading: the +2 v0.27 result was
   sample noise; cross-stream variance dominates.

2. **H5 — ROBUST REPRODUCTION.** **FIRES iff**
   `Δ_low ≥ 5  AND  Δ_high ≥ 5  AND  n_favoring ≥ 5`.
   w=0.75 beats both neighbours by ≥ 5 births in aggregate **AND**
   ≥ 5 of 8 seeds individually have w=0.75 ≥ both neighbours.
   Headline: the tight w*=0.75 interior optimum is real — survives
   a fresh stream with a meaningful margin and per-seed consistency.

3. **H6 — WEAK REPRODUCTION.** **FIRES iff**
   `Δ_low ≥ 1  AND  Δ_high ≥ 1`  AND  H5 does not fire.
   w=0.75 beats both neighbours, but margin is 1–4 births in at
   least one direction OR per-seed consistency is absent (n_favoring
   < 5). Headline: directionally consistent with v0.27 but still
   small-margin; under the v0.29 methodological rule this **does
   NOT** promote the finding to a mechanism. Result framed as: "two
   seed streams agree directionally but the magnitude remains within
   sample-noise bounds."

4. **H7 — FAILURE / SAMPLE NOISE.** **FIRES iff** none of H5 / H6 /
   H8 fires. Equivalent to: w=0.75 ties or loses to at least one
   neighbour by < 5 births. Headline: the v0.27 +2 finding is sample
   noise; the fresh stream does not reproduce the optimum but does
   not strongly invert it.

### Pre-committed observation: under the 4-tier partition, the v0.27 (1..8) data itself fires WEAK, not ROBUST

Applying the v0.30 classifier to the v0.27 (1..8) numbers (113 / 118
/ 116):

- `Δ_low = 118 − 113 = +5` (just-meets the H5 ≥5 threshold).
- `Δ_high = 118 − 116 = +2` (sub-threshold; needs ≥5).
- Both deltas ≥ 1 ✓; H5 ≥5-on-both fails; **H6 WEAK fires** on the
  v0.27 source data.

This is intentional and is documented here so the result is not
re-interpreted post-hoc. The v0.30 audit's purpose under the
methodological rule is to test whether the fresh-stream reading
(also a single 8-seed sample) lands at H5 (Robust — would compound
to a mechanism), H6 (Weak — directional but still small-margin), H7
(Failure — noise), or H8 (Reversal — actively non-reproducible). A
ROBUST verdict on a fresh stream when the source stream itself was
WEAK would be a mild positive surprise; a WEAK or worse verdict is
the more probable prior given v0.29's food_ladder reversal precedent.

### Anchor identity

No v0.30 cross-version anchor (no v0.30 H9). v0.27 / v0.28 / v0.29
anchors already cover their respective artifacts; v0.30's artifacts
are fresh.

## Decision rules

| outcome | headline | v0.31 candidate |
|---|---|---|
| H5 ROBUST | tight w*=0.75 survives | finer weight grid w ∈ {0.6, 0.7, 0.75, 0.8, 0.9} on tight, seeds 1..16 pooled |
| H6 WEAK | directional reproduction, still small-margin | third seed stream (17..24) on the same cell — does it compound? |
| H7 FAILURE | v0.27 +2 was noise; demote claim | no further audit on this cell; move to v0.25 tight h*=8 hazard-axis audit |
| H8 REVERSAL | v0.27 +2 was noise AND optimum moved | no further audit; log cross-stream variance as dominant signal; move to v0.25 hazard-axis audit |

In every outcome, **update the v0.27 forward-references** in v0.27 /
v0.28 / v0.29 docs to reflect the audited interpretation. Per the
v0.29 doc precedent, the safer phrasing for a non-Robust outcome is
"at 8 seeds, tight productivity in w=0.5–1.0 is small-margin
weight-(in)sensitive; cross-stream aggregate variance can flip the
+2-birth interior optimum reading."

Halt conditions:
- **H1 / H1b fail** — `V0_30_TIGHT_W_ARMS` constructed by accident as
  a copy or mutation. Halt; rewrite as a literal slice.
- **H2 fails** — sweep did not produce all 24 events.jsonl files.
  Halt; investigate the sweep driver.
- **H3 / H4 fail** — a v0.27..v0.29 contract was broken by the v0.30
  additions. Halt; revert the offending change.

## Out of scope (v0.30)

- food_ladder (closed by v0.29 for now).
- Weights outside {0.5, 0.75, 1.0}; finer weight grid.
- Hazard-axis or influx-axis sweeps.
- v0.25 tight h*=8 hazard-axis audit (v0.31 target).
- Other small-margin v0.21..v0.27 findings.
- Heritability, mutation distribution, per-agent trait inspection.
- Lifespan / lineage CSV inspection.
- HedonismPolicy comparisons (quarantined per v0.2 spec).
- Reading B substrate seam.
- Long-window observation (n_ticks > 200).
- Reproduction-efficiency / pool-size / cooldown variation.
- Fresh seed streams beyond 9..16.

## Implementation notes

### File-level changes

- **Modify (additive only):**
  [[src/hedonism_harness/experiments/comparison_grid.py]] — add
  `V0_30_TIGHT_W_ARMS = tuple(arm for arm in V0_27_ARMS if arm.label
  in {"hzd8-avd0.50", "hzd8-avd0.75", "hzd8-avd1.00"})`. ~6 LOC.
  Mirrors v0.29 substrate-identity-by-construction.
- **New:** [[scripts/v0.30_sweep.py]] — 24-run sweep. Mirrors
  `v0.29_sweep.py` line-for-line with substitutions: chamber =
  `tight_gradient`, batch id = `fear-hunger-v0.30-tight_gradient`,
  arm tuple = `V0_30_TIGHT_W_ARMS`. ~85 LOC.
- **New:** [[scripts/v0.30_audit.py]] — audit driver. Imports the
  v0.28 module via `importlib.util` (mirrors v0.29 hyphen-name
  pattern). Calls `v028.assert_artifacts_present(config)` and
  `v028.load_all(config)`. Computes `B(w)`, `Δ_low`, `Δ_high`,
  `n_favoring`. Applies the H8→H5→H6→H7 priority classifier. Writes
  the audit.md report with aggregate + per-seed + outcome + (using
  `v028._band_aggregate_table`) supporting band-resolved trajectory
  tables. ~160 LOC.
- **New:** `tests/test_comparison_grid_v0_30.py` —
  `V0_30_TIGHT_W_ARMS` shape (3 arms / weights {0.5, 0.75, 1.0}) +
  literal-subset identity to `V0_27_ARMS` + element-wise identity to
  `V0_29_ARMS` (H1 + H1b) + substrate field pinning + prior arm
  tuples (`ARMS`, `V0_15..27_ARMS`, `V0_29_ARMS`) untouched. ~90 LOC.
- **New:** `tests/test_v0_30_audit.py` — synthetic-fixture tests of
  the 4-tier classifier: one fixture per outcome (H5 / H6 / H7 / H8)
  confirming priority ordering and threshold semantics; boundary
  cases at Δ = 1 and Δ = 5 and at n_favoring = 4 / 5; the v0.27
  (1..8) source-data fixture firing H6 WEAK as documented above.
  ~140 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`,
  `policies/hedonism_policy.py`,
  `scripts/v0.28_trajectory_diagnostic.py`,
  `scripts/v0.29_*.py`. The v0.28 H5/H6/H7 dip-classifier is left
  untouched (wrong shape for a peak audit).
- **Documented:** this file (`docs/experiments/fear_hunger_v0.30.md`);
  Results appended after the audit runs.

### Determinism contract

- v0.27 / v0.28 / v0.29 events.jsonl artifacts on disk are not
  regenerated.
- v0.27 / v0.28 / v0.29 test suites continue to pass.
- The v0.28 module is imported but not modified — its byte-identity
  contract is preserved.

### Wall time estimate

- Sweep: 24 runs × ~0.25s ≈ 6s (matches v0.29 sweep wall time at
  identical n_ticks / n_founders).
- Audit driver: < 1s on 24 events.jsonl (~2,400 events each).

### LOC estimate

- `experiments/comparison_grid.py`: +6 LOC.
- `scripts/v0.30_sweep.py`: ~85 LOC.
- `scripts/v0.30_audit.py`: ~160 LOC.
- `tests/test_comparison_grid_v0_30.py`: ~90 LOC.
- `tests/test_v0_30_audit.py`: ~140 LOC.
- This doc: ~330 LOC.

Total v0.30 implementation: ~810 LOC. Tests should bring the suite
from 748 to ~770.

## References

- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 results; tight
  curve 107/112/113/118/116; H8 fires at the +2-birth boundary.
  Source of the v0.30 audit target.
- [[docs/experiments/fear_hunger_v0.28.md]] — v0.28 food_ladder dip
  resolution; introduces `EventBandTrajectory` library and
  `run_diagnostic(DiagnosticConfig)` entrypoint. v0.30 reuses
  `load_all` / `_band_aggregate_table` but **not** the H5/H6/H7
  dip-classifier.
- [[docs/experiments/fear_hunger_v0.29.md]] — v0.29 fresh-stream
  reproducibility check on food_ladder; introduces the methodological
  rule v0.30 is built on.
- [[docs/handoffs/2026-05-06-v0.29-shipped-v0.30-planned.md]] —
  handoff naming v0.30 as the small-margin robustness audit and
  listing audit-target priority order.
- [[src/hedonism_harness/experiments/comparison_grid.py]] —
  V0_27_ARMS / V0_29_ARMS source.
- [[scripts/v0.29_sweep.py]] — sweep pattern v0.30_sweep mirrors.
- [[scripts/v0.28_trajectory_diagnostic.py]] — `DiagnosticConfig` /
  `load_all` / `_band_aggregate_table` reused by v0.30 audit.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".
