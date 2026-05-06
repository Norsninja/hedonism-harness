# v0.32 — tight h*=8 hazard-axis reproducibility audit

**Status:** pre-registered 2026-05-06; sweep + audit not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.32-hazard-axis-tight-audit`
**Predecessors:** v0.21..v0.25 (substrate sweeps, hazard × influx
characterisation; v0.25 named the tight h*=8 interior-optimum claim),
v0.26..v0.27 (avoidance-weight axis introduction), v0.30 (tight w*=0.75
small-margin audit; H6 WEAK), v0.31 (third-stream calibration of v0.30;
**pooled H7 FAILURE** — w*=0.75 demoted to sample-noise-consistent at
n=24).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

The v0.25 doc reported a **tight interior maximum at hazard=8** across
all three shared influxes. At influx=1.0 specifically (the v0.32 audit
cell), the source numbers (seeds 1..8) are:

| h=0 | h=4 | **h=8** | h=12 |
|---:|---:|---:|---:|
| 100 | 113 | **116** | 114 |

Applying the v0.30 4-tier classifier with default 8-seed thresholds
(5 / 5 / 1 / 5) to the **interior-optimum slice {h=4, h=8, h=12}**:

- Δ_low_v25 (h=8 vs h=4)  = 116 − 113 = **+3**.
- Δ_high_v25 (h=8 vs h=12) = 116 − 114 = **+2**.
- Both deltas ≥ 1 ✓; H5 ≥5-on-both fails; **H6 WEAK fires** on the v0.25
  source data.

This is the same small-margin shape v0.27 / v0.30 saw on the
**weight axis** at hazard=8 (Δ_low=+5, Δ_high=+2). The v0.32 active
question is therefore narrowly framed:

> **Does the v0.25 tight_gradient × influx=1.0 × h=8 small-margin
> interior-hazard signal reproduce on a fresh seed stream (9..16)?**

This is a **fresh-stream reproducibility audit of a weak source signal**,
not a mechanism-confirming experiment. The source stream itself fires
H6 (not H5); v0.32 calibrates whether the directional signal persists
on a single fresh stream. Mechanism declaration remains locked behind
pooled / cross-stream / finer-grid follow-up regardless of v0.32's
single-stream verdict.

### Why no pooling in v0.32

v0.31 introduced the pooled 24-seed rule for the weight-axis question
because the v0.30 single-stream verdict was already H6 WEAK and the
question was "does the direction compound across three streams?". v0.32
is the *first* fresh-stream audit on the hazard axis — there is no
prior fresh-stream observation to pool with. The pooled rule belongs to
v0.33+ if v0.32 fires H6 (third-stream-style calibration on a future
seed range).

## What this slice tests, and what it does NOT test

### Tests

- Whether the v0.25 tight × influx=1.0 × h=8 +3 / +2 interior-optimum
  claim reproduces on seeds 9..16 under the v0.30 4-tier classifier
  (single-stream verdict, default 8-seed thresholds).
- Substrate-identity-by-construction of v0.32 arms to V0_25_ARMS at
  the matched labels.
- **Semantic determinism anchor**: at hzd=8 / influx=1.0 / seeds 9..16,
  v0.32 reproduces the previously observed explicit-w=1.0 aggregate
  `B = 96` from v0.30's cross-stream table. This is a *behavioural*
  equivalence check — `hazard_avoidance_weight=None` (v0.25 substrate)
  vs explicit `w=1.0` (v0.27+ wrapper path) should be observationally
  equal, not literally byte-identical at the configuration level.
  Failure halts the audit.
- Determinism / additive guard: v0.27..v0.31 prior tests continue to
  pass.

### Does NOT test

- Mechanism declaration. Even H5 ROBUST does NOT declare mechanism on
  v0.32 alone; it unlocks pooled / cross-stream / finer-grid follow-up
  in v0.33+.
- food_ladder. v0.25 already reported food_ladder b>50 monotone
  non-increasing in hazard; food_ladder has no interior-hazard optimum
  to audit. Out of scope.
- Influx ∈ {0.5, 1.5}. v0.25 reported the interior optimum holds at all
  three influxes; v0.32 audits influx=1.0 only. Cross-influx support
  is deferred to v0.33+ if v0.32 fires H5.
- The `h=0` baseline as part of the classifier. v0.25 already
  established that "small hazard helps tight" (h=0 vs h=4 is +13 at
  influx=1.0); that's a structural claim, not a local-interior-optimum
  question. h=0 is reported as a descriptive baseline only.
- Finer hazard grid (h ∈ {2, 6, 8, 10, 14}). Gated behind H5 ROBUST.
- Avoidance-weight axis. Closed by v0.31 H7_pool FAILURE for the
  tight w*=0.75 cell.
- Per-agent / lifespan / heritability inspection.
- HedonismPolicy comparisons.
- Fresh seed streams beyond 9..16.
- Explicit w=1.0 arms for v0.32. The audit uses the literal v0.25
  substrate (w=None).

### Deferred (v0.33+ candidates, conditional on v0.32 outcome)

Mirrors the v0.30→v0.31 pattern with the verdict-specific framings the
user committed in the v0.32 review:

- **If H5 ROBUST fires.** Fresh-stream robust reproduction. Candidate
  survives — but mechanism declaration remains locked. v0.33 may pool
  1..16 under linear-scaled thresholds (analogous to v0.31), run a
  third stream (seeds 17..24), or refine the hazard grid (h ∈ {2, 6,
  8, 10, 14} at influx=1.0). Choose ONE in v0.33's pre-reg; do not
  combine.
- **If H6 WEAK fires.** Weak directional reproduction. This becomes
  the exact v0.30 situation. v0.33 should be a third-stream-style
  calibration on seeds 17..24, with a pre-committed pooled 24-seed
  rule (linearly-scaled thresholds 15/15/3/15, same as v0.31).
- **If H7 FAILURE fires.** Sample-noise-consistent at n=8. Demote the
  v0.25 tight h*=8 claim to "directionally consistent only on seeds
  1..8; not robust on a fresh stream"; move to the next axis. No
  further audit on this hazard cell.
- **If H8 REVERSAL fires.** Active reversal on the fresh stream.
  Demote more strongly; log cross-stream variance as the dominant
  signal; move to the next axis. No further audit on this hazard cell.
- **In any outcome.** Per-seed weight-insensitivity-style observable
  on the hazard axis (`n_hazard_insensitive`) reported as a candidate
  finding. If ≥ 6/8 seeds are byte-identical on b50 across {h=4, h=8,
  h=12}, the headline empirical finding is per-seed
  hazard-insensitivity at this cell.

## Conservation framing — unchanged from v0.20..v0.31

No new conservation contract. No mutations to `world.py` / `body.py` /
`model.py` / `gradient_policy.py` / `fear_hunger_chamber.py` /
`population_dynamics.py`. No mutations to existing arm tuples (`ARMS`,
`V0_15..V0_27_ARMS`, `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`,
`V0_31_TIGHT_W_ARMS`). Source additions are limited to:

- A literal-subset arm tuple `V0_32_TIGHT_H_ARMS` in
  `comparison_grid.py` (4 arms, hazard ∈ {0, 4, 8, 12}, influx=1.0,
  w=None — pre-v0.26 default avoidance behaviour).
- An additive default-preserving refactor of
  `scripts/v0.30_audit.py:evaluate_audit` to accept a `candidate_label`
  string parameter (default `"w=0.75"`); the H7 / H8 labels currently
  hard-code "w=0.75" in their human-readable text and v0.32 needs
  "h=8". The classifier behaviour is unchanged.
- A new sweep driver and a new audit driver under `scripts/`.
- New tests.

No new event types, no new chamber, no new policy.

## Mechanism

v0.32 is two scripts plus an arm-tuple addition plus an additive
label refactor of the v0.30 classifier.

1. **Sweep** ([[scripts/v0.32_sweep.py]]). Runs `V0_32_TIGHT_H_ARMS` ×
   tight_gradient × seeds 9..16 = 32 runs. Substrate parameters are
   inherited by-construction from V0_25_ARMS via the literal-subset
   constructor (`hazard_damage` ∈ {0, 4, 8, 12}, `ambient_influx_rate`
   = 1.0, `energy_pool_initial` = 1500, `child_funding_mode` =
   PARENT_TRANSFER_POOL_GAP, `hazard_avoidance_weight` = None,
   n_ticks=200, n_founders=5). Persists per-arm comparison.csv into
   `runs/fear-hunger-v0.32-tight_gradient/`. Mirrors
   [[scripts/v0.31_sweep.py]] with substitutions for arm tuple, batch
   id, and seed range (sames seeds 9..16 as v0.30 stream 2 by design,
   for the semantic determinism anchor).

2. **Audit driver** ([[scripts/v0.32_audit.py]]). Loads per-seed
   observables via the v0.28 `load_all` helper. Runs three steps:

   - **Semantic determinism anchor** (halt condition). Computes
     `B(h=8, seeds 9..16) := Σ b50` and asserts equality to **96**.
     If the assertion fails, halt the audit and report the
     discrepancy. This pins behavioural equivalence between the v0.25
     substrate (w=None) and the explicit-w=1.0 path observed at v0.30
     stream 2.
   - **Classifier slice**. Constructs a 3-arm `b50_at` dict mapped
     from hazard to classifier slot:
       - `h=4`  → `0.50` (low slot)
       - `h=8`  → `0.75` (medium / candidate slot)
       - `h=12` → `1.00` (high slot)
     Calls `evaluate_audit(b50_at, seeds=9..16, candidate_label="h=8")`
     with default 8-seed thresholds. The classifier itself is
     behaviour-identical to its v0.30 invocation; only the displayed
     candidate label changes.
   - **Descriptive 4-arm report**. Per-seed b50 across all four
     hazards (h=0 included as descriptive baseline), per-seed
     `Δ_low(seed)` and `Δ_high(seed)` on the {h=4, h=8, h=12} slice,
     `n_favoring`, `n_strict_favoring`, **`n_hazard_insensitive`**
     (count of seeds where b50 is byte-identical across all three
     classifier-slice hazards). Routing-channel and band-resolved
     trajectory tables via `v028._band_aggregate_table` for the four
     arms.

   Writes `runs/fear-hunger-v0.32-tight_gradient/audit.md` with
   explicit verdict labels: "Single-stream verdict (v0.32 headline)"
   for the {h=4, h=8, h=12} classifier verdict, plus a "Descriptive
   baseline" section for h=0.

   The v0.28 `run_diagnostic(DiagnosticConfig)` is **not invoked**.

### Determinism — anchors

- v0.21..v0.31 events.jsonl artifacts on disk are not regenerated.
  v0.32 generates fresh artifacts on a previously-unsimulated cell
  (V0_32_TIGHT_H_ARMS × seeds 9..16).
- v0.21..v0.31 test suites continue to pass (additive guard).
- The v0.30 `evaluate_audit` `candidate_label` refactor is
  default-preserving — H4b guards (default `candidate_label="w=0.75"`
  reproduces v0.30 / v0.31 audit-report output byte-identical to the
  pre-refactor implementation).
- v0.32 sweep is deterministic per the existing `run_comparison_grid`
  contract.
- **Semantic determinism anchor** (H1c, halt condition): hzd=8 /
  influx=1.0 / seeds 9..16 b50 sum = 96 exactly. Pins behavioural
  equivalence between v0.25 substrate (w=None) and v0.27+ explicit
  w=1.0.

### Wall time estimate

- Sweep: 32 runs × ~0.3s ≈ 10s.
- Audit driver: < 1s on 32 events.jsonl.

## Observables — pre-committed before reading the data

### Per-seed primary

- `b50(s, h) := Σ AgentBorn events with tick > 50` for `s ∈ {9..16}`,
  `h ∈ {0, 4, 8, 12}`.

### Aggregate primary (classifier slice {h=4, h=8, h=12})

- `B(h) := Σ_{s ∈ 9..16} b50(s, h)` for `h ∈ {4, 8, 12}`.
- `Δ_low := B(h=8) − B(h=4)`.
- `Δ_high := B(h=8) − B(h=12)`.

### Per-seed favoring (primary, classifier slice)

- `seed_favors_h8(s) := b50(s, h=8) ≥ b50(s, h=4)
                       AND b50(s, h=8) ≥ b50(s, h=12)`.
  (Ties allowed.)
- `n_favoring := |{s ∈ 9..16 : seed_favors_h8(s)}|`.

### Descriptive (NOT used by classifier)

- `n_strict_favoring`. Strict per-seed preference (no ties). v0.30 /
  v0.31 carry-forward.
- **`n_hazard_insensitive`** := count of seeds where `b50(s, h=4) ==
  b50(s, h=8) == b50(s, h=12)`. Analogous to v0.31's
  `n_weight_insensitive`. **Pre-committed candidate finding**: if
  `n_hazard_insensitive ≥ 6/8`, the headline empirical claim is per-seed
  hazard-insensitivity in the {h=4, h=8, h=12} window at this cell.
  (v0.31 had 17/24 ≈ 71% on the weight axis; if ≥ 6/8 = 75% holds on
  the hazard axis, the per-seed pattern is the dominant phenomenon
  regardless of the H5/H6/H7/H8 verdict.)
- `B(h=0)` aggregate at h=0 (descriptive baseline).
- `total_births(h)`, `total_food_events(h)`,
  `total_hazard_entries(h)`, `total_starvation_deaths(h)`,
  `total_injury_deaths(h)` (8-seed sums per arm; h ∈ {0, 4, 8, 12}).
- Routing-channel monotonicity check: hazard entries / injury deaths
  / starvation deaths across hazards 0 → 4 → 8 → 12 (descriptive).

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (substrate-identity-by-construction).** `V0_32_TIGHT_H_ARMS` is
  a literal subset of `V0_25_ARMS` — every member is the **same** `Arm`
  instance as the matched-label member of V0_25_ARMS (identity, not
  equality). Halt condition.
- **H1c (semantic determinism anchor).** `Σ b50(s, h=8)` for `s ∈
  9..16` equals **96** exactly (matching v0.30 stream 2's explicit
  w=1.0 column). Halt condition. Pins behavioural equivalence between
  v0.25 substrate (w=None) and v0.27+ explicit w=1.0 — they should be
  observationally equal, not literally byte-identical at the
  configuration level.
- **H2 (artifact pre-flight).** After the sweep,
  `runs/fear-hunger-v0.32-tight_gradient/arms/transfer-1500-hzd{0,4,8,12}-influx-1.0/seed-{9..16}/events.jsonl`
  exists and is non-empty for every (seed, hazard). Halt condition.
- **H3 (additive guard).** v0.27..v0.31 prior tests still pass after
  the v0.32 additions. Halt condition.
- **H4 (no mutation of pre-v0.32 arm tuples).** `ARMS`, `V0_15..27_ARMS`,
  `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`, `V0_31_TIGHT_W_ARMS` byte-
  identical before and after v0.32.
- **H4b (evaluate_audit `candidate_label` default-preserving refactor).**
  Calling `evaluate_audit(b50_at, seeds)` with no `candidate_label`
  argument produces byte-identical results to the pre-refactor
  implementation (defaults to `"w=0.75"`); the v0.30 12 synthetic
  fixtures pass unchanged.

### Cautious form (single-stream verdict on the {h=4, h=8, h=12} slice)

The decision is the **single-stream classification on seeds 9..16**:
exactly one of H5 / H6 / H7 / H8 fires. Priority order — first match
wins. Mutual exclusivity is by construction. Default 8-seed thresholds
(5/5/1/5).

1. **H8 — REVERSAL.** **FIRES iff**
   `max(B(h=4), B(h=12)) − B(h=8) ≥ 5`.
   A neighbour beats h=8 by ≥ 5 births. Headline: the v0.25 tight h*=8
   finding does not reproduce, AND the optimum has moved.
   **Demote claim more strongly; no further audit on this hazard cell.**

2. **H5 — ROBUST REPRODUCTION.** **FIRES iff**
   `Δ_low ≥ 5  AND  Δ_high ≥ 5  AND  n_favoring ≥ 5`.
   h=8 beats both neighbours by ≥ 5 births in aggregate AND ≥ 5 of 8
   seeds individually have h=8 ≥ both neighbours.
   **Headline: fresh-stream robust reproduction. Candidate survives.**
   But: mechanism declaration remains locked behind pooled / cross-
   stream / finer-grid follow-up. A single fresh H5 result does not
   erase the source stream's H6 (small-margin) status.

3. **H6 — WEAK REPRODUCTION.** **FIRES iff**
   `Δ_low ≥ 1  AND  Δ_high ≥ 1`  AND  H5 does not fire.
   **Headline: weak directional reproduction.** This is the v0.30
   situation on the hazard axis — directionally consistent across two
   streams (1..8 and 9..16), magnitude small. v0.33 should be a
   third-stream-style calibration with a pre-committed pooled 24-seed
   rule (analogous to v0.31).

4. **H7 — FAILURE / SAMPLE NOISE.** **FIRES iff** none of H5 / H6 /
   H8 fires. Equivalent to: h=8 ties or loses to at least one
   neighbour by < 5 births in aggregate.
   **Headline: sample-noise-consistent at n=8. Demote the tight h*=8
   claim; move to next axis.**

### Pre-committed observation: under the same partition, the v0.25 (1..8) source data fires WEAK

Applying the v0.30 default classifier to the v0.25 (1..8) numbers
(113 / 116 / 114 at h ∈ {4, 8, 12}, influx=1.0):

- `Δ_low_v25  = 116 − 113 = +3` (sub-threshold for H5; meets H6).
- `Δ_high_v25 = 116 − 114 = +2` (sub-threshold for H5; meets H6).
- Both ≥ 1 ✓; H5 ≥ 5-on-both fails; **H6 WEAK fires** on the v0.25
  source data.

This is intentional and is documented here so the result is not
re-interpreted post-hoc. The v0.32 audit's purpose is to test whether
the fresh-stream reading lands at H5 (Robust — would unlock follow-up),
H6 (Weak — directional but still small-margin, would trigger v0.33
calibration), H7 (Failure), or H8 (Reversal). A H6 verdict on the
fresh stream when the source itself is H6 is the most probable prior;
H7 / H8 would demote the claim; H5 would unlock follow-up but not
declare mechanism.

### Verdict-space subsection — what each outcome means

| verdict | what it tells us about tight h*=8 | what it unlocks for v0.33+ |
|---|---|---|
| H5 ROBUST | fresh-stream robust reproduction; candidate survives | pooled 1..16, third stream (17..24), OR finer hazard grid — choose ONE; **mechanism declaration remains locked** |
| H6 WEAK | weak directional reproduction (the v0.30 situation on hazard axis) | third-stream-style calibration on seeds 17..24 with pre-committed pooled 24-seed rule (linearly-scaled thresholds 15/15/3/15, mirrors v0.31) |
| H7 FAILURE | the v0.25 +3 / +2 finding is sample-noise-consistent at n=8 | demote claim; no further audit on this hazard cell; move to next axis |
| H8 REVERSAL | optimum actively moves on fresh stream | demote more strongly; cross-stream variance is dominant signal; move to next axis |

**Note:** H5 unlocks *follow-up*, not declaration. The methodological
rule does not promote the tight h*=8 finding to a mechanism on a single
fresh-stream H5 verdict; it admits the finding into the next phase of
inquiry. The source stream's H6 status remains a fact that follow-up
must address.

### Anchor identity

H1c is the v0.32 cross-version anchor: hzd=8 / influx=1.0 / seeds 9..16
b50 sum = 96 (matches v0.30 stream 2 explicit-w=1.0 column). v0.27 /
v0.28 / v0.29 / v0.30 / v0.31 anchors already cover their respective
artifacts; v0.32's other artifacts (h ∈ {0, 4, 12} / seeds 9..16) are
fresh.

## Decision rules

| verdict | headline | v0.33+ candidate |
|---|---|---|
| H5 ROBUST | fresh-stream robust reproduction; candidate survives | pooled 1..16 OR third-stream OR finer-grid; **no mechanism declaration** |
| H6 WEAK | weak directional reproduction | third-stream calibration on seeds 17..24 with pre-committed pooled 24-seed rule |
| H7 FAILURE | sample-noise-consistent at n=8; demote claim | move to next axis |
| H8 REVERSAL | active reversal; demote more strongly | move to next axis |

**Independent of the verdict, if `n_hazard_insensitive ≥ 6/8`, the
headline empirical claim is per-seed hazard-insensitivity in the
{h=4, h=8, h=12} window**, regardless of which H5/H6/H7/H8 fires.
The aggregate signal and the per-seed signal can be reported
independently in Results.

Halt conditions:
- **H1 fails** — `V0_32_TIGHT_H_ARMS` not a literal slice. Halt;
  rewrite.
- **H1c fails** — semantic determinism anchor mismatched (B(h=8,
  seeds 9..16) ≠ 96). Halt; investigate the substrate-equivalence
  assumption between V0_25_ARMS (w=None) and V0_27+ (w=1.0). DO NOT
  proceed to verdict computation if this assertion fails.
- **H2 fails** — sweep did not produce all 32 events.jsonl. Halt;
  investigate.
- **H3 / H4 / H4b fail** — a v0.27..v0.31 contract was broken by v0.32
  additions. Halt; revert.

## Out of scope (v0.32)

- Mechanism declaration. (Even H5 only unlocks follow-up.)
- food_ladder.
- Influx ∈ {0.5, 1.5}. (Cross-influx support deferred to v0.33+ if H5.)
- Explicit w=1.0 arms. (Use literal V0_25_ARMS slice.)
- Finer hazard grid (h ∈ {2, 6, 10, 14}). Gated behind H5 ROBUST.
- Pooling across streams. (No prior fresh-stream observation to pool
  with; pooling enters in v0.33 if H6 fires.)
- Avoidance-weight axis. (Closed by v0.31 H7_pool FAILURE.)
- Other small-margin v0.21..v0.27 findings.
- Heritability, mutation distribution, per-agent trait inspection.
- Lifespan / lineage CSV inspection.
- HedonismPolicy comparisons (quarantined per v0.2 spec).
- Reading B substrate seam.
- Long-window observation (n_ticks > 200).
- Fresh seed streams beyond 9..16.

## Implementation notes

### File-level changes

- **Modify (additive):**
  [[src/hedonism_harness/experiments/comparison_grid.py]] — add
  `V0_32_TIGHT_H_ARMS = tuple(arm for arm in V0_25_ARMS if
  arm.label.endswith("-influx-1.0"))`. ~6 LOC.
  Substrate-byte-identity to V0_25_ARMS by-construction (4 arms;
  hazard ∈ {0, 4, 8, 12}; influx=1.0; w=None).
- **Modify (additive default-preserving refactor):**
  [[scripts/v0.30_audit.py]] — `evaluate_audit(b50_at, seeds, *,
  thresholds=DEFAULT_THRESHOLDS, candidate_label="w=0.75")`. The H7 /
  H8 labels currently embed `"w=0.75"`; parameterising the candidate
  label lets v0.32 pass `"h=8"` without behaviour change. Default
  preserves byte-identity of v0.30 / v0.31 audit-report output.
  ~10 LOC.
- **New:** [[scripts/v0.32_sweep.py]] — 32-run sweep. Mirrors
  `v0.31_sweep.py` line-for-line with substitutions: SEEDS = 9..16,
  CHAMBER = "tight_gradient", BATCH_ID =
  `fear-hunger-v0.32-tight_gradient`, arm tuple =
  `V0_32_TIGHT_H_ARMS`. ~85 LOC.
- **New:** [[scripts/v0.32_audit.py]] — audit driver. Imports v0.28 +
  v0.30 modules via `importlib.util` (mirrors v0.29 / v0.30 / v0.31
  patterns). Loads per-seed observables for the 4-arm cell
  (`weight_labels` overridden to map `0.0`/`0.50`/`0.75`/`1.00` slots
  to the four hazard arm directories — see implementation note below).
  Performs:
    1. **Semantic determinism anchor** (halt if B(h=8, seeds 9..16)
       ≠ 96).
    2. **Classifier slice verdict** via `evaluate_audit` with
       `candidate_label="h=8"` and default thresholds.
    3. **4-arm descriptive report** including h=0 baseline,
       n_hazard_insensitive, routing tables, band-resolved telemetry.
  Writes audit.md. ~280 LOC.
- **New:** `tests/test_comparison_grid_v0_32.py` —
  `V0_32_TIGHT_H_ARMS` shape (4 arms / hazards {0, 4, 8, 12} / all
  influx=1.0 / all w=None) + literal-subset identity to V0_25_ARMS
  (H1) + substrate field pinning + prior arm tuples (`ARMS`,
  `V0_15..27_ARMS`, `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`,
  `V0_31_TIGHT_W_ARMS`) untouched. ~110 LOC.
- **New:** `tests/test_v0_32_audit.py` — synthetic-fixture tests:
  - **Default-preserving refactor (H4b)**: `evaluate_audit(...)`
    without `candidate_label` matches a pre-refactor golden value.
  - **`candidate_label` parameterisation**: passing
    `candidate_label="h=8"` produces H7 / H8 labels containing
    `"h=8"` and not containing `"w=0.75"`.
  - **Hazard slot mapping**: a v0.32-style fixture with hazards
    {h=4, h=8, h=12} mapped to (0.50, 0.75, 1.00) keys produces a
    correct verdict.
  - **v0.25 source-data fixture** (1..8 → 113/116/114): aggregates to
    B = 113/116/114, Δ_low=+3, Δ_high=+2; fires **H6 WEAK** under
    default thresholds. Pins the documented pre-committed observation.
  ~150 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`,
  `scripts/v0.28_*.py`, `scripts/v0.29_*.py`, `scripts/v0.31_*.py`.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.32.md`);
  Results appended after the audit runs.

### Implementation note: weight_labels override for the 4-arm cell

The v0.28 `DiagnosticConfig.weight_labels` defaults to a 3-key dict
mapping `{0.50, 0.75, 1.00} → {hzd8-avd0.50, hzd8-avd0.75,
hzd8-avd1.00}`. v0.32's runs root contains 4 hazard subdirectories
labeled `transfer-1500-hzd{0,4,8,12}-influx-1.0`. The audit driver
overrides `weight_labels` to:

```python
{
    0.00: "transfer-1500-hzd0-influx-1.0",
    0.50: "transfer-1500-hzd4-influx-1.0",
    0.75: "transfer-1500-hzd8-influx-1.0",
    1.00: "transfer-1500-hzd12-influx-1.0",
}
```

`load_all` then returns `obs[(seed, w)]` keyed by these slots. The
classifier consumes the {0.50, 0.75, 1.00} subset; the descriptive
section uses all four. The slot key is a *positional placeholder*, not
a semantic weight value; the audit report's headers and labels make
this explicit.

### Determinism contract

- v0.21..v0.31 events.jsonl artifacts on disk are not regenerated.
- v0.21..v0.31 test suites continue to pass.
- The v0.28 module is imported but not modified.
- The v0.30 `evaluate_audit` `candidate_label` refactor is
  default-preserving — H4b guards.
- H1c (semantic determinism anchor) is the run-time halt condition.

### LOC estimate

- `experiments/comparison_grid.py`: +6 LOC.
- `scripts/v0.30_audit.py`: +10 LOC (additive label refactor).
- `scripts/v0.32_sweep.py`: ~85 LOC.
- `scripts/v0.32_audit.py`: ~280 LOC.
- `tests/test_comparison_grid_v0_32.py`: ~110 LOC.
- `tests/test_v0_32_audit.py`: ~150 LOC.
- This doc: ~620 LOC.

Total v0.32 implementation: ~1,260 LOC. Tests should bring the suite
from 805 to ~825 (+~20).

## References

- [[docs/experiments/fear_hunger_v0.25.md]] — source claim; tight
  interior maximum at h=8 across all three influxes; influx=1.0 row
  100/113/116/114. Source of the v0.32 audit target.
- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 weight-axis
  results; same small-margin shape that v0.30 / v0.31 audited.
- [[docs/experiments/fear_hunger_v0.30.md]] — introduces
  `evaluate_audit` 4-tier classifier; cross-stream B(h=8, seeds 9..16)
  = 96 (the v0.32 H1c semantic determinism anchor target).
- [[docs/experiments/fear_hunger_v0.31.md]] — pooled 24-seed rule
  precedent; H7_pool FAILURE on the weight axis. v0.32 follows the
  same methodological discipline (single-stream first; pooling only
  in v0.33 if H6 fires).
- [[docs/handoffs/2026-05-06-v0.30-shipped-v0.31-planned.md]] — the
  v0.31 handoff named the v0.25 tight h*=8 hazard-axis audit as the
  next robustness target after v0.31.
- [[src/hedonism_harness/experiments/comparison_grid.py]] —
  V0_25_ARMS source.
- [[scripts/v0.31_sweep.py]] — sweep pattern v0.32_sweep mirrors.
- [[scripts/v0.30_audit.py]] — `evaluate_audit` source (additively
  refactored to accept `candidate_label`); `AuditOutcome` /
  `AuditThresholds` reused.
- [[scripts/v0.28_trajectory_diagnostic.py]] — `DiagnosticConfig` /
  `load_all` / `_band_aggregate_table` reused.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

*(Pending sweep + audit execution. To be appended once
`scripts/v0.32_audit.py` produces a verdict.)*
