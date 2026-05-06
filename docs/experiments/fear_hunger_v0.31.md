# v0.31 — tight w*=0.75 third-stream calibration (pooled 24-seed audit)

**Status:** pre-registered 2026-05-06; sweep + audit not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.31-tight-w075-third-stream-calibration`
**Predecessors:** v0.21..v0.27 (chamber × hazard × influx × weight
characterisation), v0.28 (food_ladder w=0.75 dip = 2-of-8 seed
concentration; H6), v0.29 (food_ladder dip does not reproduce on
seeds 9..16; **methodological rule introduced**), v0.30 (tight w*=0.75
small-margin robustness audit on seeds 9..16 — **H6 WEAK fires**;
introduces `evaluate_audit` 4-tier classifier and `n_strict_favoring`
descriptive observable).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

The v0.30 audit fired **H6 WEAK** on the v0.27 tight w*=0.75 +2-birth
interior-optimum claim against fresh seeds 9..16:

| stream       | seeds | B(0.5) | B(0.75) | B(1.0) | Δ_low | Δ_high |
|--------------|------:|-------:|--------:|-------:|------:|-------:|
| v0.27 source | 1..8  | 113    | 118     | 116    | +5    | +2     |
| v0.30 fresh  | 9..16 | 91     | 97      | 96     | +6    | +1     |

Two streams agree directionally; neither meets the H5 ROBUST ≥5-on-Δ_high
bar. The v0.30 doc's H6 → "third independent seed stream" decision rule
names this slice as the canonical next step.

The active question is **not** "is tight w*=0.75 a real optimum?" — v0.30
already prevented promotion. The active question is:

> **Does the weak aggregate direction at tight w*=0.75 compound across
> three independent 8-seed streams, or does it collapse?**

This is a methodological calibration phase, not a mechanism-discovery
phase. v0.31 ships a third 8-seed stream (seeds 17..24) on the same cell
and applies (a) the existing v0.30 single-stream classifier to seeds
17..24, and (b) a **pre-committed pooled 24-seed classifier** to the
union of streams 1..8, 9..16, 17..24. The pooled classifier is the new
methodological surface; the single-stream classifier is reused.

### Why a pooled rule, and why pre-commit it now

The v0.30 review note was explicit:

> "Do not use a third weak result to promote mechanism unless the pre-reg
> defines a pooled 24-seed rule in advance."

A post-hoc pooled rule (defined after seeing stream 3) would defeat the
methodological discipline the rule is meant to enforce. The pooled rule
below is locked **before any v0.31 sweep runs**.

## What this slice tests, and what it does NOT test

### Tests

- Whether the 8-seed weak aggregate direction at tight w*=0.75 persists
  on a third independent stream (seeds 17..24) under the v0.30 4-tier
  classifier (single-stream verdict).
- Whether the 24-seed pool of streams 1..8 ∪ 9..16 ∪ 17..24 fires the
  **pooled 4-tier classifier** with proportionally-scaled thresholds.
- Substrate-byte-identity of v0.31 arms to v0.27 / v0.29 / v0.30 arms
  at the matched labels (by-construction guard).
- Per-seed weight-insensitivity prevalence across the 24-seed pool —
  pre-committed as a candidate primary finding.
- Determinism / additive guard: v0.27..v0.30 prior tests continue to
  pass.

### Does NOT test

- Mechanism promotion. Even pooled H5 ROBUST does **not** declare
  mechanism — it unlocks *investigation*, not declaration.
- food_ladder. Closed by v0.29 for now; v0.31 is tight only.
- Weights w ∉ {0.5, 0.75, 1.0}. Finer weight grid is gated behind
  pooled H5 ROBUST.
- Other hazards / influxes. Single cell only (h=8, influx=1.0).
- **The v0.25 tight h*=8 hazard-axis interior optimum.** Listed as the
  v0.31 candidate in the v0.30 handoff but **OUT OF SCOPE for this PR**
  — v0.30 H6 → third-stream calibration takes priority. Deferred to
  v0.32+.
- Other ≤6-birth aggregate optima at n=8 from v0.21..v0.27. Deferred.
- Per-agent / lifespan / heritability inspection.
- HedonismPolicy comparisons.
- Fresh seed streams beyond 17..24 (no seeds 25..32 sweep).

### Deferred (v0.32+ candidates, conditional on v0.31 outcome)

- **If pooled H5 ROBUST fires.** Finer weight grid on tight,
  w ∈ {0.6, 0.7, 0.75, 0.8, 0.9}, seeds 1..16 pooled — **investigation,
  not mechanism declaration**. The headline phrasing remains "directional
  signal compounds across three streams"; mechanism status requires
  further substrate-axis evidence beyond a finer grid.
- **If pooled H6 WEAK fires.** No further seed-stream audit on this cell
  for now. Move to v0.25 tight h*=8 hazard-axis audit (v0.32). Headline:
  "directionally persistent across three independent streams, not
  mechanistically robust."
- **If pooled H7 FAILURE fires.** Demote the v0.27 tight w*=0.75 claim
  to "sample-noise-consistent at n=24"; move to v0.25 hazard-axis audit.
- **If pooled H8 REVERSAL fires.** Demote the claim and log the
  cross-stream variance as the dominant signal; move to v0.25 hazard-axis
  audit.
- **In any outcome.** v0.25 hazard-axis audit is the next robustness
  target.

## Conservation framing — unchanged from v0.20..v0.30

No new conservation contract. No mutations to `world.py` / `body.py` /
`model.py` / `gradient_policy.py` / `fear_hunger_chamber.py` /
`population_dynamics.py`. No mutations to existing arm tuples (`ARMS`,
`V0_15..V0_27_ARMS`, `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`). Source
additions are limited to:

- A literal-subset arm tuple `V0_31_TIGHT_W_ARMS` in `comparison_grid.py`
  (mirrors v0.30 substrate-identity-by-construction).
- An additive refactor of `scripts/v0.30_audit.py:evaluate_audit` to
  accept an `AuditThresholds` dataclass with defaults equal to the
  existing 8-seed values. The v0.30 test suite passes unchanged (no
  callers thread thresholds in). v0.31 calls with pooled thresholds.
- A new sweep driver and a new audit driver under `scripts/`.
- New tests.

No new event types, no new chamber, no new policy.

## Mechanism

v0.31 is two scripts plus an arm-tuple addition plus an additive
refactor of the v0.30 classifier.

1. **Sweep** ([[scripts/v0.31_sweep.py]]). Runs `V0_31_TIGHT_W_ARMS` ×
   tight_gradient × seeds 17..24 = 24 runs. Substrate parameters are
   inherited by-construction from V0_27_ARMS via the literal-subset
   constructor (hazard_damage=8, ambient_influx_rate=1.0,
   energy_pool_initial=1500, child_funding_mode=PARENT_TRANSFER_POOL_GAP,
   n_ticks=200, n_founders=5). Persists per-arm comparison.csv into
   `runs/fear-hunger-v0.31-tight_gradient/`. Mirrors
   [[scripts/v0.30_sweep.py]] verbatim except for the seed range and
   batch id.

2. **Audit driver** ([[scripts/v0.31_audit.py]]). Loads per-seed
   observables for **three streams** by calling the v0.28 `load_all`
   helper three times against three different runs roots:

   | stream | runs_root | seeds | arms |
   |---|---|---|---|
   | 1 (v0.27 source) | `runs/fear-hunger-v0.27-tight_gradient/arms/` | 1..8 | hzd8-avd0.{50,75,1.00} |
   | 2 (v0.30 fresh)  | `runs/fear-hunger-v0.30-tight_gradient/arms/` | 9..16 | hzd8-avd0.{50,75,1.00} |
   | 3 (v0.31 fresh)  | `runs/fear-hunger-v0.31-tight_gradient/arms/` | 17..24 | hzd8-avd0.{50,75,1.00} |

   The v0.27 runs root contains five arms (hzd8-avd0.00..1.00); v0.31
   loads only the three relevant labels. The driver merges the three
   per-stream `dict[(seed, w), SeedObservables]` into a single
   24-key-per-weight dict.

   Three classifier invocations:

   - **Single-stream verdict on stream 3** via `evaluate_audit(b50_at,
     seeds=17..24)` (default 8-seed thresholds). Reports H5/H6/H7/H8
     for the v0.31 stream alone.
   - **Pooled verdict on streams 1..3** via `evaluate_audit(b50_at,
     seeds=1..24, thresholds=POOLED_THRESHOLDS)`. Reports pooled
     H5/H6/H7/H8.
   - **Cross-stream verdict table** showing each stream's individual
     single-stream verdict (recomputed with default thresholds against
     its own 8-seed b50 dict) plus the pooled verdict, side by side.

   Writes `runs/fear-hunger-v0.31-tight_gradient/audit.md` containing:
   per-stream aggregate B(w) tables, per-seed b50 + delta tables across
   all 24 seeds, single-stream verdict for v0.31, pooled verdict,
   cross-stream verdict comparison, and supporting band-resolved
   trajectory tables (reusing v0.28 `_band_aggregate_table`). The
   supporting tables are descriptive only.

   The v0.28 `run_diagnostic(DiagnosticConfig)` is **not invoked** —
   its H5/H6/H7 dip-classifier is shape-mismatched for a peak audit.

### Determinism — anchors

- v0.27 / v0.28 / v0.29 / v0.30 events.jsonl artifacts on disk are
  not regenerated. v0.31 generates fresh artifacts on a previously-
  unsimulated seed range (17..24).
- v0.27..v0.30 test suites continue to pass (additive guard).
- The v0.30 `evaluate_audit` refactor preserves its 12 synthetic-fixture
  tests as the determinism anchor for the 8-seed thresholds. Default
  thresholds match the v0.30 hardcoded values exactly.
- v0.31 sweep is deterministic per the existing `run_comparison_grid`
  contract.

### Wall time estimate

- Sweep: 24 runs × ~0.25s ≈ 6s (matches v0.29 / v0.30 sweep wall time).
- Audit driver: < 2s on 72 events.jsonl (24 per stream × 3 streams).

## Observables — pre-committed before reading the data

### Single-stream (per stream s ∈ {1, 2, 3})

Reuses the v0.30 observables verbatim, applied to each stream's seeds:
- `b50(s, w)`, `B_s(w) := Σ b50`, `Δ_low_s`, `Δ_high_s`, `n_favoring_s`,
  `n_strict_favoring_s`.

### Pooled across all 24 seeds (s = pool)

- `B_pool(w) := Σ_{seed ∈ 1..24} b50(seed, w)` for w ∈ {0.5, 0.75, 1.0}.
- `Δ_low_pool := B_pool(0.75) − B_pool(0.5)`.
- `Δ_high_pool := B_pool(0.75) − B_pool(1.0)`.
- `n_favoring_pool := |{seed ∈ 1..24 : b50(seed, 0.75) ≥ both neighbours}|`
  (ties allowed).

### Pooled descriptive (NOT used by classifier)

- `n_strict_favoring_pool := |{seed ∈ 1..24 : b50(seed, 0.75) > both
  neighbours}|`. Strict per-seed preference.
- **`n_weight_insensitive_pool := |{seed ∈ 1..24 : b50(seed, 0.5) ==
  b50(seed, 0.75) == b50(seed, 1.0)}|`.** Count of seeds where weight
  has no effect on late-window productivity. **Pre-committed as a
  candidate primary finding** — if `n_weight_insensitive_pool ≥ 18/24`,
  the headline empirical claim is per-seed weight-insensitivity, not
  the small-margin aggregate direction. (v0.30 had 6/8 byte-identical
  on 9..16; if the rate holds across streams, the pool will land at
  ~18/24.)
- `total_births_pool(w)`, `total_food_events_pool(w)`,
  `total_hazard_entries_pool(w)`, `total_starvation_deaths_pool(w)`,
  `total_injury_deaths_pool(w)`. 24-seed sums per arm.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (substrate-identity-by-construction).** `V0_31_TIGHT_W_ARMS` is
  a literal subset of `V0_27_ARMS` — every member is the **same** `Arm`
  instance as the matched-label member of V0_27_ARMS (identity, not
  equality). Mirrors v0.30's H1. Halt condition.
- **H1b (cross-version arm-object equivalence).** Arm-object identity
  only, not chamber identity: `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`, and
  `V0_31_TIGHT_W_ARMS` should reference the same underlying `V0_27_ARMS`
  instances for the shared labels {hzd8-avd0.50, hzd8-avd0.75,
  hzd8-avd1.00}. The chamber differs at run time (v0.29 was
  food_ladder; v0.30 / v0.31 are tight_gradient); the substrate arm
  objects do not. Tested for explicitness; tripwire if any tuple drifts.
- **H2 (artifact pre-flight).** After the sweep,
  `runs/fear-hunger-v0.31-tight_gradient/arms/hzd8-avd0.{50,75,1.00}/seed-{17..24}/events.jsonl`
  exists and is non-empty for every (seed, weight). Halt condition.
- **H3 (additive guard).** v0.27..v0.30 prior tests still pass after
  the v0.31 additions. Halt condition.
- **H4 (no mutation of pre-v0.31 arm tuples).** `ARMS`, `V0_15..27_ARMS`,
  `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS` byte-identical before and after
  v0.31.
- **H4b (evaluate_audit default-preserving refactor).** Calling
  `evaluate_audit(b50_at, seeds)` with no `thresholds` argument
  produces byte-identical results to the v0.30 implementation on every
  one of the v0.30 12 synthetic fixtures.

### Cautious form — single-stream verdict on stream 3 only

Reuses the v0.30 4-tier partition verbatim with default thresholds (5/5,
5, 1/1, 5):

- **H5 — single-stream ROBUST.** Δ_low_3 ≥ 5 AND Δ_high_3 ≥ 5 AND
  n_favoring_3 ≥ 5. Single-stream w=0.75 robust on seeds 17..24.
- **H6 — single-stream WEAK.** Δ_low_3 ≥ 1 AND Δ_high_3 ≥ 1, NOT H5.
  Single-stream w=0.75 directional but small-margin on seeds 17..24.
- **H7 — single-stream FAILURE.** None of H5/H6/H8.
- **H8 — single-stream REVERSAL.** max(B_3(0.5), B_3(1.0)) − B_3(0.75)
  ≥ 5.

Priority order H8 → H5 → H6 → H7. **The single-stream verdict is
diagnostic only — it does NOT determine the v0.31 headline.** The
pooled verdict is the headline.

### Cautious form — pooled 24-seed verdict (the v0.31 headline)

Linear (proportional) scaling of the 8-seed thresholds to a 24-seed
pool: 5 × 24/8 = 15; 1 × 24/8 = 3; n_favoring 5 × 24/8 = 15. Linear
scaling is **stricter** than √N noise-scaling (which would give ~9/~2)
— intentionally conservative on the side of "harder to promote."

Priority order — first match wins. Mutually exclusive by construction.

1. **H8_pool — POOLED REVERSAL.** **FIRES iff**
   `max(B_pool(0.5), B_pool(1.0)) − B_pool(0.75) ≥ 15`.
   A neighbour beats w=0.75 by ≥15 births in the 24-seed aggregate.
   Headline: the v0.27 tight w*=0.75 finding does not survive at scale,
   and the optimum has actively moved across the pool. Demote the claim;
   log cross-stream variance as the dominant signal.

2. **H5_pool — POOLED ROBUST REPRODUCTION.** **FIRES iff**
   `Δ_low_pool ≥ 15 AND Δ_high_pool ≥ 15 AND n_favoring_pool ≥ 15`.
   w=0.75 beats both neighbours by ≥15 births in the 24-seed aggregate
   AND ≥15 of 24 seeds individually have w=0.75 ≥ both neighbours.
   Headline: directional signal compounds across three independent
   streams. **Unlocks investigation (finer weight grid on tight); does
   NOT declare mechanism.** Mechanism status requires further
   substrate-axis evidence beyond what a finer grid would provide.

3. **H6_pool — POOLED WEAK REPRODUCTION.** **FIRES iff**
   `Δ_low_pool ≥ 3 AND Δ_high_pool ≥ 3`, NOT H5_pool.
   w=0.75 beats both neighbours in the 24-seed aggregate, but margin is
   3..14 in at least one direction. Headline (locked phrase, see below):
   **"Directionally persistent, not mechanistically robust."** Two or
   three streams agree directionally but the magnitude does not compound
   to a robust per-seed pattern at scale.

4. **H7_pool — POOLED FAILURE / SAMPLE NOISE.** **FIRES iff** none of
   H5_pool / H6_pool / H8_pool. Equivalent to: w=0.75 ties or loses to
   at least one neighbour by < 15 in the 24-seed pool, or one of the
   pooled deltas falls below +3. Headline: the v0.27 +2 finding does
   not compound across three streams; demote to "sample-noise-consistent
   at n=24."

### Locked phrase for H6_pool

> **"Directionally persistent, not mechanistically robust."**

This phrase is committed as the headline framing for H6_pool, **before
any v0.31 sweep runs**, to prevent post-hoc rhetorical drift. Any v0.31
H6_pool result must use exactly this phrasing or a near-paraphrase that
preserves both halves: directional persistence affirmed, mechanism
denied. v0.32+ docs that forward-reference H6_pool should preserve the
distinction.

### Verdict-space subsection — what each pooled outcome means

| pooled verdict | what it tells us about tight w*=0.75 | what it unlocks for v0.32+ |
|---|---|---|
| H5_pool ROBUST | direction compounds across three independent 8-seed streams with per-seed support | finer weight grid on tight as **investigation**, not mechanism declaration |
| H6_pool WEAK | direction persists at the aggregate level but not strongly enough at scale to warrant promotion | no further seed-stream audit on this cell; v0.25 hazard-axis audit is next |
| H7_pool FAILURE | the v0.27 +2 finding does not compound; it was sample noise | no further audit on this cell; demote claim; v0.25 hazard-axis audit next |
| H8_pool REVERSAL | the optimum actively moves at scale | demote claim; cross-stream variance is the dominant signal; v0.25 hazard-axis audit next |

**Note:** H5_pool unlocks *investigation*, not declaration. The
methodological rule does not promote the tight w*=0.75 finding to a
mechanism on a single pooled-ROBUST verdict; it admits the finding into
the next phase of inquiry. Mechanism status is a higher bar than this
audit can clear.

### Pre-committed observation: the existing 1..16 pool already lands in H6_pool territory under the proposed thresholds

Applying the pooled rule to the **existing** v0.27 (1..8) ∪ v0.30
(9..16) data, scaled to 16 seeds (thresholds × 16/8 = ×2; 5→10; 1→2):

- B_16(0.5)  = 113 + 91  = **204**.
- B_16(0.75) = 118 + 97  = **215**.
- B_16(1.0)  = 116 + 96  = **212**.
- Δ_low_16  = 215 − 204  = **+11**.
- Δ_high_16 = 215 − 212  = **+3**.

Under 16-seed thresholds (Δ ≥ 2 for H6_16; Δ ≥ 10 for H5_16; neighbour
lead ≥ 10 for H8_16):
- H8_16 FAILS: max(204, 212) − 215 = −3 (no neighbour leads).
- H5_16 FAILS on Δ_high_16 = +3 (need ≥10).
- H6_16 FIRES: Δ_low_16 = +11 ≥ 2 ✓; Δ_high_16 = +3 ≥ 2 ✓.

**The existing 16-seed pool already fires the equivalent of pooled H6
WEAK.** This is the prior the v0.31 verdict will be measured against. A
24-seed pooled H6 verdict means stream 3 *did not collapse* the
direction; a 24-seed pooled H7 verdict means stream 3 was sufficiently
non-confirming to drop one of the pooled deltas below +3; a 24-seed
pooled H5 ROBUST verdict means stream 3 contributed enough to push
both deltas to +15 (a large positive surprise — see "verdict reachability"
below).

### Verdict reachability — sanity check on the threshold space

Given the 1..16 numbers (Δ_low_16=+11, Δ_high_16=+3):

- **H5_pool (Δ_low ≥ 15, Δ_high ≥ 15, n_favoring ≥ 15)** — stream 3
  must contribute Δ_low ≥ +4 AND Δ_high ≥ +12 AND ≥ (15 − n_favoring_16)
  per-seed favors. Δ_high ≥ +12 from 8 seeds is large; the +6/+1 prior
  pattern makes this implausible. Pooled H5 ROBUST is a genuinely high
  bar.
- **H6_pool (Δ_low ≥ 3, Δ_high ≥ 3, NOT H5)** — Δ_high_16 = +3 is
  already at the H6 threshold. Stream 3 contributing Δ_high ≥ 0
  preserves H6_pool; Δ_high_3 < 0 could tip pooled Δ_high below +3 and
  collapse to H7. Genuinely live verdict space.
- **H7_pool** — fires iff stream 3 contributes Δ_high ≤ −1 (pulling
  pooled Δ_high below +3) without triggering H8.
- **H8_pool (neighbour lead ≥ 15)** — extremely strong stream-3
  inversion required. Implausible given the prior pattern.

Verdict space is genuinely live in the H6_pool ↔ H7_pool boundary;
H5_pool and H8_pool are tail outcomes.

### Anchor identity

No v0.31 cross-version artifact-identity anchor (no v0.31 H9). v0.27 /
v0.28 / v0.29 / v0.30 anchors already cover their respective artifacts;
v0.31's artifacts are fresh. The v0.30 evaluate_audit 12 synthetic
fixtures are the determinism anchor for the classifier refactor.

## Decision rules

| pooled verdict | headline | v0.32+ candidate |
|---|---|---|
| H5_pool ROBUST | direction compounds across 3 streams | finer weight grid w ∈ {0.6, 0.7, 0.75, 0.8, 0.9} on tight, seeds 1..24 pooled — **investigation only** |
| H6_pool WEAK | "directionally persistent, not mechanistically robust" (LOCKED) | no further seed-stream audit on this cell; v0.25 tight h*=8 hazard-axis audit is next |
| H7_pool FAILURE | v0.27 +2 finding does not compound; sample-noise-consistent at n=24 | no further audit on this cell; demote claim; v0.25 hazard-axis audit |
| H8_pool REVERSAL | optimum actively moves at scale | demote claim; cross-stream variance is dominant signal; v0.25 hazard-axis audit |

**Independent of the verdict, if `n_weight_insensitive_pool ≥ 18/24`,
the headline empirical claim is per-seed weight-insensitivity at this
cell**, regardless of whether H5/H6/H7/H8_pool fires. The aggregate
signal and the per-seed signal can be reported independently in
Results.

Halt conditions:
- **H1 / H1b fail** — `V0_31_TIGHT_W_ARMS` not a literal slice. Halt;
  rewrite.
- **H2 fails** — sweep did not produce all 24 events.jsonl. Halt;
  investigate.
- **H3 / H4 / H4b fail** — a v0.27..v0.30 contract was broken by v0.31
  additions. Halt; revert offending change.

## Out of scope (v0.31)

- food_ladder.
- Weights outside {0.5, 0.75, 1.0}; finer weight grid (gated behind
  pooled H5_pool ROBUST).
- Hazard-axis or influx-axis sweeps.
- v0.25 tight h*=8 hazard-axis audit (v0.32+ target).
- Other small-margin v0.21..v0.27 findings.
- Heritability, mutation distribution, per-agent trait inspection.
- Lifespan / lineage CSV inspection.
- HedonismPolicy comparisons (quarantined per v0.2 spec).
- Reading B substrate seam.
- Long-window observation (n_ticks > 200).
- Reproduction-efficiency / pool-size / cooldown variation.
- Fresh seed streams beyond 17..24 (no seeds 25..32).
- Mechanism declaration. Pooled H5 ROBUST unlocks investigation only.

## Implementation notes

### File-level changes

- **Modify (additive):**
  [[src/hedonism_harness/experiments/comparison_grid.py]] — add
  `V0_31_TIGHT_W_ARMS = tuple(arm for arm in V0_27_ARMS if arm.label
  in {"hzd8-avd0.50", "hzd8-avd0.75", "hzd8-avd1.00"})`. ~6 LOC.
  Mirrors v0.29 / v0.30 substrate-identity-by-construction.
- **Modify (additive default-preserving refactor):**
  [[scripts/v0.30_audit.py]] — `evaluate_audit(b50_at, seeds, *,
  thresholds=DEFAULT_THRESHOLDS)`. New `AuditThresholds` frozen
  dataclass holds (h5_delta_min, h5_favoring_min, h6_delta_min,
  h8_neighbor_lead_min). `DEFAULT_THRESHOLDS = AuditThresholds(5, 5,
  1, 5)` matches the v0.30 hardcoded values exactly. The v0.30 12
  synthetic-fixture tests pass unchanged (no callers thread thresholds).
  ~25 LOC.
- **New:** [[scripts/v0.31_sweep.py]] — 24-run sweep on seeds 17..24.
  Mirrors `v0.30_sweep.py` line-for-line with substitutions: SEEDS =
  17..24, BATCH_ID = `fear-hunger-v0.31-tight_gradient`, arm tuple =
  `V0_31_TIGHT_W_ARMS`. ~85 LOC.
- **New:** [[scripts/v0.31_audit.py]] — audit driver. Imports the v0.28
  module via `importlib.util` (mirrors v0.29 / v0.30 hyphen-name
  pattern); imports `evaluate_audit` and `AuditThresholds` from
  `scripts/v0.30_audit.py` (same pattern). Loads three streams via
  three `DiagnosticConfig` instances; merges per-seed dicts; computes
  single-stream verdict on stream 3 (default thresholds), pooled
  verdict on 1..24 (POOLED_THRESHOLDS = AuditThresholds(15, 15, 3,
  15)), and per-stream individual verdicts for the cross-stream table.
  Computes `n_weight_insensitive_pool` and per-pool descriptive
  observables. Writes audit.md report. ~280 LOC.
- **New:** `tests/test_comparison_grid_v0_31.py` —
  `V0_31_TIGHT_W_ARMS` shape (3 arms / weights {0.5, 0.75, 1.0}) +
  literal-subset identity to `V0_27_ARMS` (H1) + arm-object identity
  to `V0_29_ARMS` and `V0_30_TIGHT_W_ARMS` (H1b) + substrate field
  pinning + prior arm tuples (`ARMS`, `V0_15..27_ARMS`, `V0_29_ARMS`,
  `V0_30_TIGHT_W_ARMS`) untouched. ~100 LOC.
- **New:** `tests/test_v0_31_audit.py` — synthetic-fixture tests of
  the pooled classifier:
  - Default-preserving refactor (H4b): `evaluate_audit(...)` without
    thresholds matches the v0.30 implementation byte-for-byte on a
    sample of v0.30 fixtures (or via golden-value cross-check).
  - Pooled H5 ROBUST: positive at thresholds (15/15/15) + just-meets
    + n_favoring_pool=14 falls to H6.
  - Pooled H6 WEAK: clear weak (Δ_low=10, Δ_high=5) + just-meets
    (Δ_low=Δ_high=3) + Δ_high=2 falls to H7.
  - Pooled H7 FAILURE: ties one neighbour, loses-by-lt-15.
  - Pooled H8 REVERSAL: leads-by-exactly-15 + does-not-fire-by-14 +
    low-neighbour-leads.
  - Priority H8_pool over H5_pool.
  - 1..16 pre-committed observation fixture: B_16 = (204, 215, 212);
    fires H6 under 16-seed-scaled thresholds (10/10/2/10) — sanity
    check on the proportional-scaling logic.
  - Cross-stream merge: three 8-seed dicts merged into a 24-seed dict
    is well-formed (no key collisions; correct b50 lookups).
  ~180 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`,
  `scripts/v0.28_*.py`, `scripts/v0.29_*.py`. Source modifications
  outside `comparison_grid.py` are limited to the additive refactor
  of `scripts/v0.30_audit.py:evaluate_audit`.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.31.md`);
  Results appended after the audit runs.

### Determinism contract

- v0.27..v0.30 events.jsonl artifacts on disk are not regenerated.
- v0.27..v0.30 test suites continue to pass.
- The v0.28 module is imported but not modified — its byte-identity
  contract is preserved.
- The v0.30 `evaluate_audit` refactor is default-preserving — H4b
  guards.

### LOC estimate

- `experiments/comparison_grid.py`: +6 LOC.
- `scripts/v0.30_audit.py`: +25 LOC (additive refactor).
- `scripts/v0.31_sweep.py`: ~85 LOC.
- `scripts/v0.31_audit.py`: ~280 LOC.
- `tests/test_comparison_grid_v0_31.py`: ~100 LOC.
- `tests/test_v0_31_audit.py`: ~180 LOC.
- This doc: ~480 LOC.

Total v0.31 implementation: ~1,160 LOC. Tests should bring the suite
from 772 to ~795 (+~23).

## References

- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 results; tight
  curve 107/112/113/118/116; H8 fires at the +2-birth boundary. Source
  of stream 1.
- [[docs/experiments/fear_hunger_v0.28.md]] — v0.28 food_ladder dip
  resolution; introduces `EventBandTrajectory` library and
  `run_diagnostic(DiagnosticConfig)` entrypoint. v0.31 reuses
  `load_all` / `_band_aggregate_table` but **not** the H5/H6/H7
  dip-classifier.
- [[docs/experiments/fear_hunger_v0.29.md]] — v0.29 fresh-stream
  reproducibility check on food_ladder; introduces the methodological
  rule v0.30 / v0.31 are built on.
- [[docs/experiments/fear_hunger_v0.30.md]] — v0.30 tight w*=0.75
  audit on seeds 9..16; H6 WEAK fires; introduces `evaluate_audit`
  4-tier classifier and `n_strict_favoring`. Source of stream 2.
- [[docs/handoffs/2026-05-06-v0.30-shipped-v0.31-planned.md]] —
  handoff naming v0.31 as the third-stream calibration target and
  requiring a pre-committed pooled 24-seed rule.
- [[src/hedonism_harness/experiments/comparison_grid.py]] —
  V0_27_ARMS / V0_29_ARMS / V0_30_TIGHT_W_ARMS source.
- [[scripts/v0.30_sweep.py]] — sweep pattern v0.31_sweep mirrors.
- [[scripts/v0.30_audit.py]] — `evaluate_audit` source (additively
  refactored to accept thresholds); `AuditOutcome` reused.
- [[scripts/v0.28_trajectory_diagnostic.py]] — `DiagnosticConfig` /
  `load_all` / `_band_aggregate_table` reused by v0.31 audit.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

*(Pending sweep + audit execution. To be appended once
`scripts/v0.31_audit.py` produces a verdict.)*
