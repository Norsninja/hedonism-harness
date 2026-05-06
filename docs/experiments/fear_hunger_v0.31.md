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

**Status:** executed 2026-05-06. 24 fresh runs on tight_gradient × seeds
17..24 × `V0_31_TIGHT_W_ARMS` written to
`runs/fear-hunger-v0.31-tight_gradient/`. Audit driver
(`scripts/v0.31_audit.py`) loaded all three streams (v0.27 1..8, v0.30
9..16, v0.31 17..24), applied single-stream diagnostic verdicts (default
8-seed thresholds) and the pre-committed pooled 24-seed verdict
(thresholds 15/15/3/15). Full per-seed report:
`runs/fear-hunger-v0.31-tight_gradient/audit.md`.

### Headline

**Pooled 24-seed verdict: H7_pool — FAILURE / SAMPLE NOISE.**

| weight | B_pool(w) = Σ b>50 over 24 seeds |
|-------:|---------------------------------:|
| 0.50 | 312 |
| 0.75 | **322** |
| 1.00 | 321 |

- Δ_low_pool  = B(0.75) − B(0.5)  = **+10**  (≥ 3 ✓ for H6, < 15 for H5).
- Δ_high_pool = B(0.75) − B(1.0)  = **+1**   (< 3 — **fails H6 threshold**;
  < 15 for H5).
- Neighbour lead  = max(312, 321) − 322 = **−1**  (< 15 — H8 fails).
- `n_favoring_pool`        = **20/24**  (ties allowed).
- `n_strict_favoring_pool` = **0/24**   (descriptive only).
- `n_weight_insensitive_pool` = **17/24**  (descriptive; ~71% of seeds
  byte-identical on b>50 across all three weights).

The pooled directional signal **does not compound** across three
independent 8-seed streams. The +6 (Δ_low) / +3 (Δ_high) pattern
observed in the 1..16 pool collapses to +10 / +1 in the 1..24 pool —
Δ_high drops below the pre-committed H6_pool threshold of +3. **The
v0.27 +2-birth tight w*=0.75 interior-optimum claim is demoted to
"sample-noise-consistent at n=24."**

### Stream 3 collapsed the direction

Single-stream verdict on the v0.31 fresh stream (seeds 17..24):

| weight | B_3(w) = Σ b>50 |
|-------:|----------------:|
| 0.50 | 108 |
| 0.75 | **107** |
| 1.00 | 109 |

- Δ_low_3  = 107 − 108 = **−1**.
- Δ_high_3 = 107 − 109 = **−2**.
- max neighbour lead = max(108, 109) − 107 = 2 (< 5 → H8 fails).
- Single-stream classification: **H7 — FAILURE / SAMPLE NOISE**
  (w=0.75 ties or loses to a neighbour by < 5 births).

w=0.75 actually loses to **both** neighbours on this fresh stream. The
two prior streams' directional agreement does not extend to stream 3 at
the aggregate level.

### Cross-stream verdict table

| stream | seeds | B(0.5) | B(0.75) | B(1.0) | Δ_low | Δ_high | n_fav | n_strict | single-stream verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Stream 1 (v0.27 source) | 1..8  | 113 | 118 | 116 | +5 | +2 | 7/8 | 0/8 | H6 WEAK |
| Stream 2 (v0.30 fresh)  | 9..16 |  91 |  97 |  96 | +6 | +1 | 7/8 | 0/8 | H6 WEAK |
| Stream 3 (v0.31 fresh)  | 17..24 | 108 | 107 | 109 | −1 | −2 | 6/8 | 0/8 | **H7 FAILURE** |
| **Pooled**              | **1..24** | **312** | **322** | **321** | **+10** | **+1** | **20/24** | **0/24** | **H7_pool FAILURE** |

Two streams agreed weakly (H6 / H6); the third did not (H7). The pooled
verdict is H7_pool because Δ_high_pool=+1 falls below the pre-committed
H6 threshold of +3. Linear scaling of the 8-seed rule was tight enough
to discriminate "two-stream agreement" from "three-stream compounding."

### The per-seed pattern is the substantive finding (n_weight_insensitive_pool = 17/24)

The pre-committed candidate primary finding (`n_weight_insensitive_pool
≥ 18/24`) was **just missed**: 17 of 24 seeds (~71%) are byte-identical
on b>50 across all three weights. Per-seed b>50 across the 24-seed pool:

- **Weight-insensitive seeds (17):** 1, 2, 3, 4, 5, 10, 11, 12, 14, 15,
  16, 17, 20, 21, 22, 23, 24. b50 identical at all three weights.
- **Seed 6:** +5 Δ_low, +0 Δ_high (w=0.5 alone is lower).
- **Seed 7:** +0 Δ_low, +4 Δ_high (w=1.0 alone is lower).
- **Seed 8:** +0 Δ_low, **−2 Δ_high** (w=1.0 wins by 2).
- **Seed 9:** +0 Δ_low, +6 Δ_high (w=1.0 alone is much lower).
- **Seed 13:** +6 Δ_low, **−5 Δ_high** (per-seed REVERSAL — H8 single-seed).
- **Seed 18:** +0 Δ_low, **−2 Δ_high** (w=1.0 wins by 2).
- **Seed 19:** **−1 Δ_low**, +0 Δ_high (w=0.5 wins by 1).

The pooled Δ_high = +1 is the **residual of single-seed swings going
in opposite directions**: seed 7 (+4) + seed 9 (+6) − seed 8 (−2) −
seed 13 (−5) − seed 18 (−2) = +1, with the other 19 seeds contributing
0. **Not a single seed in the 24-seed pool prefers w=0.75 strictly over
both neighbours** (`n_strict_favoring_pool = 0/24`). The aggregate
signal is statistical debris.

The "n_weight_insensitive ≥ 18/24" pre-committed threshold was missed
by 1, but the per-seed weight-insensitivity *rate* (~71%) is the
dominant empirical finding regardless of where the H7/H6 boundary
falls. **At hazard=8 in tight_gradient, w ∈ {0.5, 0.75, 1.0} is mostly
weight-insensitive on b>50 at the per-seed level**, with aggregate
deltas in the 0..2 birth range driven by a handful of single-seed
swings.

### Routing-channel — flat-then-drop, consistent across all three streams

Pooled 24-seed routing observables:

| weight | total_births | b>50 | total_food | hazard_entries | starvation | injury |
|-------:|-------------:|-----:|-----------:|---------------:|-----------:|-------:|
| 0.50 | 547 | 312 | 2169 | 119 | 333 | 0 |
| 0.75 | 553 | 322 | 2168 | 119 | 327 | 0 |
| 1.00 | 555 | 321 | 2173 | 110 | 326 | 0 |

Hazard entries: 119 → 119 → 110 (~3-step drop at w=1.0). Same flat-
then-drop shape v0.27 / v0.30 saw on stream 1 / stream 2. Injury deaths
= 0 across all three weights — tight geometry protects against
single-visit lethality regardless of weight, holding through three
independent streams. **The routing channel is the part of the substrate
that responds reliably to weight; the productivity channel is not.**

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | `V0_31_TIGHT_W_ARMS` is a literal subset of `V0_27_ARMS` (instance identity) | **HOLDS.** `test_v0_31_tight_w_arms_are_literal_v0_27_subset`. |
| H1b | Arm-object identity to `V0_29_ARMS` and `V0_30_TIGHT_W_ARMS` at matched labels | **HOLDS.** `test_v0_31_tight_w_arms_share_arm_objects_with_v0_29_arms` + `_v0_30_tight_w_arms`. |
| H2 | Sweep produces 24 events.jsonl files (artifact pre-flight) | **HOLDS.** `assert_artifacts_present` passes for all three streams. |
| H3 | v0.27 / v0.28 / v0.29 / v0.30 prior tests pass after v0.31 additions | **HOLDS.** Suite 772 → 805 (+33 v0.31 tests); all green. |
| H4 | Pre-v0.31 arm tuples unchanged | **HOLDS.** Pinned in `tests/test_comparison_grid_v0_31.py`. |
| H4b | `evaluate_audit` default-preserving refactor (v0.30 12 fixtures pass unchanged) | **HOLDS.** `tests/test_v0_30_audit.py` 12/12 green; `test_evaluate_audit_default_thresholds_match_explicit_default` anchors equivalence. |
| H5_pool | ROBUST: Δ_low ≥ 15 AND Δ_high ≥ 15 AND n_favoring ≥ 15 | **FAILS** on Δ_high_pool=+1 (need ≥ 15) and Δ_low_pool=+10 (need ≥ 15). |
| H6_pool | WEAK: Δ_low ≥ 3 AND Δ_high ≥ 3, NOT H5 | **FAILS** on Δ_high_pool=+1 (need ≥ 3). |
| H7_pool | FAILURE: none of H5_pool / H6_pool / H8_pool | **FIRES.** |
| H8_pool | REVERSAL: max(B(0.5), B(1.0)) − B(0.75) ≥ 15 | **FAILS.** Lead = −1 (no neighbour beats w=0.75 in pool aggregate). |

Pre-committed observation (v0.31 pre-reg): the existing 1..16 pool fires
the equivalent of H6_pool under 16-seed-scaled thresholds (Δ_low_16=+11
≥ 2 ✓; Δ_high_16=+3 ≥ 2 ✓). **The v0.31 fresh stream collapsed the
Δ_high direction sufficiently to drop the pooled Δ_high from +3 (1..16)
to +1 (1..24), tipping the 24-seed pool from H6_pool territory to
H7_pool territory.** The H6 → H7 boundary identified in the pre-reg's
verdict-reachability analysis ("Δ_high(17..24) < 0 could tip pooled
Δ_high below +3") is exactly what fired.

### What this means for the v0.27 tight w*=0.75 claim

**Demoted to sample-noise-consistent at n=24.** Under the v0.29
methodological rule and the v0.31 pre-committed pooled thresholds:

- The directional signal does **not** compound across three independent
  8-seed streams. Two streams agreed weakly; the third did not.
- The pooled Δ_high = +1 over 24 seeds is *below* the pre-committed
  weak-reproduction threshold of +3.
- Per-seed strict preference is absent across the entire 24-seed pool
  (`n_strict_favoring_pool = 0/24`).
- ~71% of seeds (17/24) are byte-identical on b>50 across the three
  weights — the productivity channel is mostly weight-insensitive in
  this band at this cell.
- The aggregate-level appearance of an "interior optimum at w=0.75" in
  the 1..16 pool is residual of a small number of single-seed swings
  that happened to favor w=0.75 in streams 1 and 2; stream 3's
  single-seed swings did not.

**Safer phrasing for forward references** (to be applied to v0.27's
"tight w*=0.75 +2-birth interior optimum" claim in v0.27 / v0.28 /
v0.29 / v0.30 forward-mention sites if those docs are next-touched):

> At 8 seeds per stream, tight_gradient productivity in
> w ∈ {0.5, 0.75, 1.0} is mostly weight-insensitive at hazard=8
> (~71% of seeds byte-identical on b>50 across the three weights in
> the 24-seed pool). Three independent seed streams (v0.27 1..8,
> v0.30 9..16, v0.31 17..24) produce single-stream verdicts of
> H6 WEAK, H6 WEAK, H7 FAILURE; the pooled 24-seed verdict under
> linearly-scaled thresholds (15/15/3/15) is **H7 FAILURE / SAMPLE
> NOISE**. The v0.27 +2-birth interior-optimum claim is
> sample-noise-consistent at n=24 and is not a mechanism. The
> routing channel (hazard entries / starvation deaths) responds
> reliably to weight at the aggregate level; the productivity
> channel does not.

### v0.32+ candidates (per pre-reg decision rules)

The pre-reg's H7_pool decision rule is unambiguous:

> H7_pool FAILURE | v0.27 +2 finding does not compound;
> sample-noise-consistent at n=24 | no further audit on this cell;
> v0.25 tight h*=8 hazard-axis audit is next.

Concrete next slice (v0.32):
- **v0.25 tight h*=8 hazard-axis interior optimum audit** on a fresh
  seed stream. Cell: tight_gradient, h ∈ {0, 4, 8, 12}, influx=1.0,
  w=1.0, seeds 9..16. ~32 runs. Reuse `evaluate_audit` with the
  default 8-seed thresholds (single-stream verdict only — no pooling
  needed for a single audit).

**Do NOT** introduce a finer weight grid on tight w (gated behind
H5_pool ROBUST, which did not fire — and now will not without a
fundamentally different study design).

**Do NOT** sweep seeds 25..32 on this cell. The pooled rule has
delivered a definitive H7_pool FAILURE; further seed streams on the
same cell would be confirmation theater, not science.

The `n_weight_insensitive_pool = 17/24` near-miss could motivate a
*targeted* per-seed inspection of the 7 non-flat seeds (6, 7, 8, 9, 13,
18, 19) to characterise *what* makes those seeds weight-sensitive when
the other 17 are not — but that's a substrate-axis question, not a
weight-axis one. Defer until the hazard-axis audit settles.

### Implementation summary

- **Library extension (additive only):** `V0_31_TIGHT_W_ARMS = tuple(
  arm for arm in V0_27_ARMS if arm.label in (...))` in
  `experiments/comparison_grid.py`. Substrate-byte-identity to
  V0_27_ARMS / V0_29_ARMS / V0_30_TIGHT_W_ARMS by-construction.
- **Additive default-preserving refactor:** `scripts/v0.30_audit.py`
  `evaluate_audit(b50_at, seeds, *, thresholds=DEFAULT_THRESHOLDS)`.
  New `AuditThresholds` frozen dataclass with field defaults
  `(5, 5, 1, 5)`. Labels parameterised from threshold values so
  pooled invocations print pooled thresholds (15) rather than
  single-stream ones (5). v0.30 12 synthetic-fixture tests pass
  unchanged.
- **Sweep:** `scripts/v0.31_sweep.py` mirrors the v0.30 sweep
  line-for-line with `SEEDS = tuple(range(17, 25))`,
  `BATCH_ID = "fear-hunger-v0.31-tight_gradient"`,
  `arms = V0_31_TIGHT_W_ARMS`. 24 runs in ~7.9s.
- **Audit driver:** `scripts/v0.31_audit.py` — loads three streams via
  three `DiagnosticConfig` instances against three runs roots (v0.27 /
  v0.30 / v0.31), merges per-seed dicts, computes single-stream
  verdicts (default thresholds) for each stream, computes pooled
  verdict (POOLED_THRESHOLDS=AuditThresholds(15, 15, 3, 15)) on the
  24-seed union, computes `n_weight_insensitive_pool` and other
  descriptive observables. Writes audit.md with explicit "Pooled 24-
  seed verdict (v0.31 HEADLINE)" + "Single-stream diagnostic
  verdicts" section labels to prevent later confusion. ~370 LOC.
- **Tests:** `tests/test_comparison_grid_v0_31.py` (14 tests —
  shape / pinning / H1 / H1b two-way / H4 invariants);
  `tests/test_v0_31_audit.py` (19 tests — default-preserving refactor
  anchor, threshold pinning, pooled H5/H6/H7/H8 positive fixtures and
  boundaries, priority H8_pool over H5_pool, 16-seed-scaled pre-
  committed observation, cross-stream merge, label parameterisation).
  Suite: **772 → 805** (+33 v0.31 tests); all green.
- **No simulation-mechanics changes; no `core/` / `model.py` /
  `experiments/fear_hunger_chamber.py` /
  `experiments/population_dynamics.py` /
  `policies/gradient_policy.py` / `policies/hedonism_policy.py` /
  `scripts/v0.28_*.py` / `scripts/v0.29_*.py` changes.** Source
  modifications outside `comparison_grid.py` are limited to the
  additive refactor of `scripts/v0.30_audit.py:evaluate_audit`
  (default-preserving; H4b anchor passes).
- **CI gate at handoff time:**
  ```
  uv run ruff check .                           ok
  uv run ruff format --check .                  ok
  uv run pytest                                 805 passed
  uv run python scripts/core_smoke_test.py      ok
  uv run python scripts/v0.31_sweep.py          done in 7.9s
  uv run python scripts/v0.31_audit.py          H7_pool FAILURE
  ```
