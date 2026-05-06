# v0.33 — tight h*=8 hazard-axis third-stream calibration (pooled 24-seed audit)

**Status:** pre-registered 2026-05-06; sweep + audit not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.33-hazard-axis-third-stream-calibration`
**Predecessors:** v0.21..v0.27 (chamber x hazard x influx x weight
characterisation), v0.28 (food_ladder w=0.75 dip = 2-of-8 seed
concentration; H6), v0.29 (food_ladder dip does not reproduce on
seeds 9..16; **methodological rule introduced**), v0.30 (tight
w*=0.75 small-margin robustness audit on seeds 9..16 — H6 WEAK;
introduces `evaluate_audit` 4-tier classifier), v0.31 (tight w*=0.75
third-stream calibration; **pooled 24-seed H7 FAILURE** demotes the
weight-axis claim), v0.32 (tight h*=8 hazard-axis fresh-stream audit
on seeds 9..16 — H6 WEAK on the {h=4, h=8, h=12} classifier slice;
H1c semantic determinism anchor passed; introduces
`n_hazard_insensitive` and `candidate_label` parameter).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

The v0.32 audit fired **H6 WEAK** on the v0.25 tight h*=8 small-margin
interior-hazard claim against fresh seeds 9..16:

| stream       | seeds | B(h=4) | B(h=8) | B(h=12) | Δ_low | Δ_high |
|--------------|------:|-------:|-------:|--------:|------:|-------:|
| v0.25 source | 1..8  | 113    | 116    | 114     | +3    | +2     |
| v0.32 fresh  | 9..16 | 91     | 96     | 94      | +5    | +2     |

Two streams agree directionally; neither meets the H5 ROBUST >=5-on-Δ_high
bar. The v0.32 doc's H6 -> "third independent seed stream calibration"
decision rule names this slice as the canonical next step, mirroring
v0.30 -> v0.31 verbatim except for the substrate axis.

The active question is **not** "is tight h*=8 a real interior-hazard
optimum?" — v0.32 already prevented promotion. The active question is:

> **Does the weak aggregate direction at tight h*=8 compound across
> three independent 8-seed streams, or does it collapse?**

This is a methodological calibration phase, not a mechanism-discovery
phase. v0.33 ships a third 8-seed stream (seeds 17..24) on the same
cell and applies (a) the v0.32 single-stream classifier (default 8-seed
thresholds, `candidate_label="h=8"`) to seeds 17..24 as a diagnostic
verdict, and (b) a **pre-committed pooled 24-seed classifier** to the
union of streams 1..8, 9..16, 17..24 as the headline. The pooled
classifier reuses the v0.31 surface verbatim with the `candidate_label`
override; only the axis differs.

### Why a pooled rule, and why pre-commit it now

Same discipline that gated v0.31. A post-hoc pooled rule (defined after
seeing stream 3) would defeat the methodological purpose. The pooled
rule below is locked **before any v0.33 sweep runs**.

### Why this closes the calibration phase

After v0.33, the methodological calibration arc that began with v0.29
(food_ladder reproducibility check) and continued through
v0.30 / v0.31 (weight axis) and v0.32 / v0.33 (hazard axis) is **closed
by design**. v0.34+ pivots to per-agent / lineage / lifespan / mutation
observability (the substrate-axis questions the aggregate-optimum
discipline could not answer). The v0.33 Conclusion explicitly demotes
the residual deferred catalog of small-margin v0.21..v0.27 aggregate
optima to "not promoted to mechanism without a new motivating
observation."

## What this slice tests, and what it does NOT test

### Tests

- Whether the 8-seed weak aggregate direction at tight h*=8 persists on
  a third independent stream (seeds 17..24) under the v0.32
  single-stream classifier (diagnostic verdict).
- Whether the 24-seed pool of streams 1..8 ∪ 9..16 ∪ 17..24 fires the
  **pooled 4-tier classifier** with proportionally-scaled thresholds
  (linearly scaled, identical to v0.31: 15/15/3/15).
- Substrate-byte-identity of v0.33 arms to v0.25 / v0.32 arms at the
  matched labels (by-construction guard).
- Per-seed hazard-insensitivity prevalence across the 24-seed pool —
  pre-committed as a candidate primary finding (`n_hazard_insensitive_pool
  ≥ 18/24` mirrors v0.31's `n_weight_insensitive_pool` bar).
- Determinism / additive guard: v0.27..v0.32 prior tests continue to
  pass.

### Does NOT test

- Mechanism promotion. Even pooled H5 ROBUST does **not** declare
  mechanism — it unlocks *investigation*, not declaration.
- food_ladder. Closed by v0.29; v0.33 is tight only.
- Hazards h ∉ {0, 4, 8, 12}. Finer hazard grid is gated behind pooled
  H5 ROBUST.
- Other influxes. Single influx (1.0) only — same cell as v0.25 stream
  1 and v0.32 stream 2.
- The h=0 quarantined "small hazard helps tight" secondary observation
  from v0.32 (h=0 vs h=4 = +13 on 1..8 → +0 on 9..16). Tracked as a
  separate independent claim per the v0.32 quarantine; **NOT bundled
  into v0.33**.
- Cross-influx audit (gated behind pooled H5 ROBUST).
- Other ≤6-birth aggregate optima at n=8 from v0.21..v0.27. Demoted in
  the v0.33 Conclusion regardless of pooled verdict.
- Weight-axis questions (closed by v0.31 H7_pool FAILURE).
- Per-agent / lifespan / heritability inspection (v0.34+).
- HedonismPolicy comparisons (deferred until lineage observability
  matures).
- Fresh seed streams beyond 17..24 (no seeds 25..32 sweep — the pooled
  rule delivers a definitive verdict; further streams on this cell
  would be confirmation theater).

### Deferred (v0.34+ candidates, conditional on v0.33 outcome)

- **Independent of the pooled verdict.** v0.34 begins the per-agent /
  lineage / lifespan / heritability observability arc, starting with a
  minimum viable lens (parent_id → child_id edges, lifespan, offspring
  count, cause-of-death). This is the canonical next slice regardless
  of how v0.33 lands.
- **If pooled H5 ROBUST fires.** Implausible given prior verdict
  reachability (see below). If it fires, log it; do not pivot the
  v0.34 agenda — finer hazard grids on tight remain available as
  later slices, but the lineage observability arc is the higher
  priority.
- **If pooled H6 WEAK fires.** Headline (locked phrase, see below):
  **"Directionally persistent, not mechanistically robust."** No
  further seed-stream audit on this cell. Pivot to v0.34 lineage
  observability as the next slice.
- **If pooled H7 FAILURE fires.** Demote the v0.25 tight h*=8 claim to
  "sample-noise-consistent at n=24." Pivot to v0.34. (Mirrors v0.31's
  weight-axis demotion verbatim.)
- **If pooled H8 REVERSAL fires.** Demote the claim and log
  cross-stream variance as the dominant signal. Pivot to v0.34.

## Conservation framing — unchanged from v0.20..v0.32

No new conservation contract. No mutations to `world.py` / `body.py` /
`model.py` / `gradient_policy.py` / `fear_hunger_chamber.py` /
`population_dynamics.py`. No mutations to existing arm tuples (`ARMS`,
`V0_15..V0_27_ARMS`, `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`,
`V0_31_TIGHT_W_ARMS`, `V0_32_TIGHT_H_ARMS`). Source additions are
limited to:

- A literal-subset arm tuple `V0_33_TIGHT_H_ARMS` in
  `comparison_grid.py` — element-wise identical to `V0_32_TIGHT_H_ARMS`
  by construction (both literal slices of `V0_25_ARMS` at influx=1.0).
- A new sweep driver and a new audit driver under `scripts/`.
- New tests.

No new event types, no new chamber, no new policy. **No refactor of
`evaluate_audit`** — v0.31's `thresholds` parameter and v0.32's
`candidate_label` parameter are reused verbatim.

## Mechanism

v0.33 is two scripts plus an arm-tuple addition.

1. **Sweep** ([[scripts/v0.33_sweep.py]]). Runs `V0_33_TIGHT_H_ARMS` ×
   tight_gradient × seeds 17..24 = 32 runs. Substrate parameters are
   inherited by-construction from V0_25_ARMS via the literal-subset
   constructor (`hazard_damage` ∈ {0, 4, 8, 12}, `ambient_influx_rate`
   = 1.0, `energy_pool_initial` = 1500, `child_funding_mode` =
   PARENT_TRANSFER_POOL_GAP, `hazard_avoidance_weight` = None,
   n_ticks=200, n_founders=5). Persists per-arm comparison.csv into
   `runs/fear-hunger-v0.33-tight_gradient/`. Mirrors
   [[scripts/v0.32_sweep.py]] verbatim with substitutions for arm
   tuple, batch id, and seed range (17..24).

2. **Audit driver** ([[scripts/v0.33_audit.py]]). Loads per-seed
   observables for **three streams** by calling the v0.28 `load_all`
   helper three times against three different runs roots:

   | stream | runs_root | seeds | arms |
   |---|---|---|---|
   | 1 (v0.25 source) | `runs/fear-hunger-v0.25-tight_gradient/arms/` | 1..8  | transfer-1500-hzd{0,4,8,12}-influx-1.0 |
   | 2 (v0.32 fresh)  | `runs/fear-hunger-v0.32-tight_gradient/arms/` | 9..16 | transfer-1500-hzd{0,4,8,12}-influx-1.0 |
   | 3 (v0.33 fresh)  | `runs/fear-hunger-v0.33-tight_gradient/arms/` | 17..24 | transfer-1500-hzd{0,4,8,12}-influx-1.0 |

   The v0.25 runs root contains all 12 arms (4 hazards × 3 influxes);
   v0.33 loads only the 4 influx=1.0 arms via the same
   `weight_labels` slot mapping that v0.32 uses (slot 0.0 → h=0
   baseline, slot 0.5 → h=4 low, slot 0.75 → h=8 medium, slot 1.0 →
   h=12 high). The driver merges the three per-stream `dict[(seed, slot),
   SeedObservables]` into a single 24-key-per-slot dict.

   Three classifier invocations:

   - **Single-stream verdict on stream 3** via `evaluate_audit(b50_at,
     seeds=17..24, candidate_label="h=8")` (default 8-seed thresholds).
     Reports H5/H6/H7/H8 for the v0.33 stream alone.
   - **Pooled verdict on streams 1..3** via `evaluate_audit(b50_at,
     seeds=1..24, thresholds=POOLED_THRESHOLDS, candidate_label="h=8")`.
     Reports pooled H5/H6/H7/H8.
   - **Cross-stream verdict table** showing each stream's individual
     single-stream verdict (recomputed with default thresholds against
     its own 8-seed b50 dict) plus the pooled verdict, side by side.
     Mirrors the v0.31 table layout exactly.

   Writes `runs/fear-hunger-v0.33-tight_gradient/audit.md` containing:
   per-stream aggregate B(h) tables, per-seed b50 + delta tables across
   all 24 seeds (4-arm view; h=0 baseline + classifier slice), single-
   stream verdict for v0.33, pooled verdict, cross-stream verdict
   comparison, and supporting band-resolved trajectory tables (reusing
   v0.28 `_band_aggregate_table`).

   The v0.28 `run_diagnostic(DiagnosticConfig)` is **not invoked** —
   its H5/H6/H7 dip-classifier is shape-mismatched for a peak audit.

### Determinism — anchors

- v0.21..v0.32 events.jsonl artifacts on disk are not regenerated.
  Stream 1 and stream 2 artifacts are loaded from disk verbatim
  (option (a) — verified present at pre-reg time:
  `runs/fear-hunger-v0.25-tight_gradient/arms/transfer-1500-hzd{0,4,8,12}-influx-1.0/seed-{1..8}/events.jsonl`
  and
  `runs/fear-hunger-v0.32-tight_gradient/arms/transfer-1500-hzd{0,4,8,12}-influx-1.0/seed-{9..16}/events.jsonl`).
  v0.33 generates fresh artifacts on a previously-unsimulated seed
  range (17..24) for the same 4 arms.
- v0.21..v0.32 test suites continue to pass (additive guard).
- The v0.30 `evaluate_audit` is reused without modification.
- v0.33 sweep is deterministic per the existing `run_comparison_grid`
  contract.

### Wall time estimate

- Sweep: 32 runs × ~0.3s ≈ 10s (matches v0.32 sweep wall time).
- Audit driver: < 2s on 96 events.jsonl (32 per stream × 3 streams).

## Observables — pre-committed before reading the data

### Single-stream (per stream s ∈ {1, 2, 3})

Reuses the v0.32 single-stream observables verbatim, applied to each
stream's seeds:
- `b50(s, h)`, `B_s(h) := Σ b50` for h ∈ {0, 4, 8, 12}.
- `Δ_low_s := B_s(8) − B_s(4)`, `Δ_high_s := B_s(8) − B_s(12)`.
- `n_favoring_s` (ties allowed; b50@h=8 ≥ both classifier-slice
  neighbours), `n_strict_favoring_s` (strict; descriptive only).

### Pooled across all 24 seeds (s = pool)

- `B_pool(h) := Σ_{seed ∈ 1..24} b50(seed, h)` for h ∈ {0, 4, 8, 12}.
- `Δ_low_pool := B_pool(8) − B_pool(4)`.
- `Δ_high_pool := B_pool(8) − B_pool(12)`.
- `n_favoring_pool := |{seed ∈ 1..24 : b50(seed, 8) ≥ both classifier-slice
  neighbours}|` (ties allowed).

### Pooled descriptive (NOT used by classifier)

- `n_strict_favoring_pool`: strict per-seed preference for h=8 over both
  neighbours.
- **`n_hazard_insensitive_pool := |{seed ∈ 1..24 : b50(seed, 4) ==
  b50(seed, 8) == b50(seed, 12)}|`**. Count of seeds where hazard has
  no effect on late-window productivity in the {h=4, h=8, h=12} slice.
  **Pre-committed as a candidate primary finding** — if
  `n_hazard_insensitive_pool ≥ 18/24`, the headline empirical claim is
  per-seed hazard-insensitivity at this cell, regardless of the
  classifier verdict. (v0.32 had 4/8 byte-identical on stream 2; if
  the rate holds across streams, the pool will land near 12/24, well
  below the 18/24 bar — but the bar is pre-committed for symmetry with
  v0.31.)
- `B_pool(0)`: descriptive baseline (h=0 is NOT in the classifier).
- `total_births_pool(h)`, `total_food_events_pool(h)`,
  `total_hazard_entries_pool(h)`, `total_starvation_deaths_pool(h)`,
  `total_injury_deaths_pool(h)`. 24-seed sums per arm (all 4 arms,
  including h=0 baseline).

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (substrate-identity-by-construction).** `V0_33_TIGHT_H_ARMS` is
  a literal subset of `V0_25_ARMS` — every member is the **same** `Arm`
  instance as the matched-label member of `V0_25_ARMS` (identity, not
  equality). Mirrors v0.32's H1. Halt condition.
- **H1b (cross-version arm-object equivalence).** Arm-object identity
  only: `V0_32_TIGHT_H_ARMS` and `V0_33_TIGHT_H_ARMS` reference the
  same underlying `V0_25_ARMS` instances at the matched labels. Tested
  for explicitness; tripwire if either tuple drifts.
- **H2 (artifact pre-flight).** After the sweep,
  `runs/fear-hunger-v0.33-tight_gradient/arms/transfer-1500-hzd{0,4,8,12}-influx-1.0/seed-{17..24}/events.jsonl`
  exists and is non-empty for every (seed, hazard). Halt condition.
- **H3 (additive guard).** v0.27..v0.32 prior tests still pass after
  the v0.33 additions. Halt condition.
- **H4 (no mutation of pre-v0.33 arm tuples).** `ARMS`, `V0_15..27_ARMS`,
  `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`, `V0_31_TIGHT_W_ARMS`,
  `V0_32_TIGHT_H_ARMS` byte-identical before and after v0.33.

### Cautious form — single-stream verdict on stream 3 only

Reuses the v0.32 4-tier partition verbatim with default thresholds
(5/5/1/5) and `candidate_label="h=8"` on the {h=4, h=8, h=12}
classifier slice:

- **H5 — single-stream ROBUST.** Δ_low_3 ≥ 5 AND Δ_high_3 ≥ 5 AND
  n_favoring_3 ≥ 5.
- **H6 — single-stream WEAK.** Δ_low_3 ≥ 1 AND Δ_high_3 ≥ 1, NOT H5.
- **H7 — single-stream FAILURE.** None of H5/H6/H8.
- **H8 — single-stream REVERSAL.** max(B_3(4), B_3(12)) − B_3(8) ≥ 5.

Priority order H8 → H5 → H6 → H7. **The single-stream verdict is
diagnostic only — it does NOT determine the v0.33 headline.** The
pooled verdict is the headline.

### Cautious form — pooled 24-seed verdict (the v0.33 headline)

Linear (proportional) scaling of the 8-seed thresholds to a 24-seed
pool: 5 × 24/8 = 15; 1 × 24/8 = 3; n_favoring 5 × 24/8 = 15. Same
linear scaling v0.31 used. Linear scaling is **stricter** than √N
noise-scaling (which would give ~9/~2) — intentionally conservative
on the side of "harder to promote."

Priority order — first match wins. Mutually exclusive by construction.

1. **H8_pool — POOLED REVERSAL.** **FIRES iff**
   `max(B_pool(4), B_pool(12)) − B_pool(8) ≥ 15`.
   A neighbour beats h=8 by ≥15 births in the 24-seed aggregate.
   Headline: the v0.25 tight h*=8 finding does not survive at scale,
   and the optimum has actively moved across the pool. Demote the
   claim; log cross-stream variance as the dominant signal.

2. **H5_pool — POOLED ROBUST REPRODUCTION.** **FIRES iff**
   `Δ_low_pool ≥ 15 AND Δ_high_pool ≥ 15 AND n_favoring_pool ≥ 15`.
   h=8 beats both classifier-slice neighbours by ≥15 births in the
   24-seed aggregate AND ≥15 of 24 seeds individually have b50@h=8 ≥
   both neighbours. Headline: directional signal compounds across
   three independent streams. **Unlocks investigation (finer hazard
   grid on tight); does NOT declare mechanism.**

3. **H6_pool — POOLED WEAK REPRODUCTION.** **FIRES iff**
   `Δ_low_pool ≥ 3 AND Δ_high_pool ≥ 3`, NOT H5_pool.
   h=8 beats both classifier-slice neighbours in the 24-seed
   aggregate, but margin is 3..14 in at least one direction. Headline
   (locked phrase, reused verbatim from v0.31): **"Directionally
   persistent, not mechanistically robust."** Two or three streams
   agree directionally but the magnitude does not compound to a robust
   per-seed pattern at scale.

4. **H7_pool — POOLED FAILURE / SAMPLE NOISE.** **FIRES iff** none of
   H5_pool / H6_pool / H8_pool. Equivalent to: h=8 ties or loses to at
   least one classifier-slice neighbour by < 15 in the 24-seed pool,
   or one of the pooled deltas falls below +3. Headline: the v0.25
   +3 / +2 finding does not compound across three streams; demote to
   "sample-noise-consistent at n=24."

### Locked phrase for H6_pool

> **"Directionally persistent, not mechanistically robust."**

Reused verbatim from v0.31's locked phrase. Same discipline; same
wording. Any v0.33 H6_pool result must use exactly this phrasing or a
near-paraphrase that preserves both halves: directional persistence
affirmed, mechanism denied.

### Verdict-space subsection — what each pooled outcome means

| pooled verdict | what it tells us about tight h*=8 | what it unlocks for v0.34+ |
|---|---|---|
| H5_pool ROBUST | direction compounds across three independent 8-seed streams with per-seed support | log result; finer hazard grid stays available but is NOT prioritised; v0.34 lineage observability is still next |
| H6_pool WEAK | direction persists at the aggregate level but not strongly enough at scale to warrant promotion | no further hazard-axis seed-stream audit; v0.34 lineage observability is next |
| H7_pool FAILURE | the v0.25 +3 / +2 finding does not compound; sample-noise-consistent at n=24 | demote claim; v0.34 lineage observability is next |
| H8_pool REVERSAL | the optimum actively moves at scale | demote claim; cross-stream variance is dominant signal; v0.34 lineage observability is next |

**Note:** Every pooled outcome routes to v0.34. The aggregate-optimum
audit phase ends with v0.33; the v0.34 lineage observability arc is
the canonical next slice regardless of pooled verdict. H5_pool would
log a residual finding but not redirect the agenda.

### Pre-committed observation: the existing 1..16 pool already lands in H6_pool territory under the proposed thresholds

Applying the pooled rule to the **existing** v0.25 (1..8) ∪ v0.32
(9..16) data, scaled to 16 seeds (thresholds × 16/8 = ×2; 5→10; 1→2):

- B_16(h=4)  = 113 + 91  = **204**.
- B_16(h=8)  = 116 + 96  = **212**.
- B_16(h=12) = 114 + 94  = **208**.
- Δ_low_16   = 212 − 204 = **+8**.
- Δ_high_16  = 212 − 208 = **+4**.

Under 16-seed thresholds (Δ ≥ 2 for H6_16; Δ ≥ 10 for H5_16; neighbour
lead ≥ 10 for H8_16):
- H8_16 FAILS: max(204, 208) − 212 = −4 (no neighbour leads).
- H5_16 FAILS on Δ_low_16=+8 (need ≥10) and Δ_high_16=+4 (need ≥10).
- H6_16 FIRES: Δ_low_16=+8 ≥ 2 ✓; Δ_high_16=+4 ≥ 2 ✓.

**The existing 16-seed pool already fires the equivalent of pooled H6
WEAK** — and at a slightly larger margin than the v0.31 prior had on
the weight axis (which was Δ_low_16=+11, Δ_high_16=+3). This is the
prior the v0.33 verdict will be measured against. A 24-seed pooled H6
verdict means stream 3 *did not collapse* the direction; a 24-seed
pooled H7 verdict means stream 3 was sufficiently non-confirming to
drop one of the pooled deltas below +3; a 24-seed pooled H5 ROBUST
verdict means stream 3 contributed enough to push both deltas to +15
(a large positive surprise — see "verdict reachability" below).

### Verdict reachability — sanity check on the threshold space

Given the 1..16 numbers (Δ_low_16=+8, Δ_high_16=+4):

- **H5_pool (Δ_low ≥ 15, Δ_high ≥ 15, n_favoring ≥ 15)** — stream 3
  must contribute Δ_low ≥ +7 AND Δ_high ≥ +11 AND ≥ (15 −
  n_favoring_16) per-seed favors. Δ_high ≥ +11 from 8 seeds is large
  given the +2/+2 prior pattern; pooled H5 ROBUST is a genuinely high
  bar.
- **H6_pool (Δ_low ≥ 3, Δ_high ≥ 3, NOT H5)** — Δ_low_16=+8 ≥ 3 with
  +5 of slack; Δ_high_16=+4 with only +1 of slack above the +3
  threshold. Stream 3 contributing Δ_high ≥ −1 preserves H6_pool;
  Δ_high_3 ≤ −2 could tip pooled Δ_high below +3 and collapse to H7.
  Genuinely live verdict space — this is the same H6 ↔ H7 boundary
  v0.31 sat on, except v0.31's slack was Δ_high_16=+3 (only +1 of
  slack); v0.33's slack is Δ_high_16=+4 (+1 of slack again, on
  Δ_high). Stream 3 has slightly more Δ_low headroom than v0.31 had.
- **H7_pool** — fires iff stream 3 contributes Δ_high ≤ −2 (pulling
  pooled Δ_high below +3) without triggering H8.
- **H8_pool (neighbour lead ≥ 15)** — extremely strong stream-3
  inversion required. Implausible given the prior pattern.

Verdict space is genuinely live in the H6_pool ↔ H7_pool boundary;
H5_pool and H8_pool are tail outcomes.

### Anchor identity

No v0.33 cross-version artifact-identity anchor (no v0.33 H9). v0.27 /
v0.28 / v0.29 / v0.30 / v0.31 / v0.32 anchors already cover their
respective artifacts; v0.33's fresh artifacts are seeds 17..24. The
v0.32 H1c semantic determinism anchor (B(h=8, seeds 9..16) = 96)
remains a durable cross-version anchor and is implicitly re-checked by
v0.33 stream-2 reload (any drift would surface in the cross-stream
verdict table).

## Decision rules

| pooled verdict | headline | v0.34+ candidate |
|---|---|---|
| H5_pool ROBUST | direction compounds across 3 streams | log result; finer hazard grid on tight is NOT prioritised; v0.34 lineage observability is next |
| H6_pool WEAK | "directionally persistent, not mechanistically robust" (LOCKED) | no further hazard-axis seed-stream audit; v0.34 lineage observability is next |
| H7_pool FAILURE | v0.25 +3 / +2 finding does not compound; sample-noise-consistent at n=24 | demote claim; v0.34 lineage observability is next |
| H8_pool REVERSAL | optimum actively moves at scale | demote claim; cross-stream variance is dominant signal; v0.34 lineage observability is next |

**Independent of the verdict, if `n_hazard_insensitive_pool ≥ 18/24`,
the headline empirical claim is per-seed hazard-insensitivity at this
cell**, regardless of which pooled hypothesis fires. The aggregate
signal and the per-seed signal can be reported independently in
Results.

**Also independent of the verdict, the v0.33 Conclusion demotes the
remaining catalog of small-margin v0.21..v0.27 aggregate optima** to
"not promoted to mechanism without a new motivating observation." The
calibration phase ends with v0.33 by design.

Halt conditions:
- **H1 / H1b fail** — `V0_33_TIGHT_H_ARMS` not a literal slice. Halt;
  rewrite.
- **H2 fails** — sweep did not produce all 32 events.jsonl. Halt;
  investigate.
- **H3 / H4 fail** — a v0.27..v0.32 contract was broken by v0.33
  additions. Halt; revert offending change.

## Out of scope (v0.33)

- food_ladder.
- Hazards outside {0, 4, 8, 12}; finer hazard grid (gated behind
  pooled H5_pool ROBUST, deprioritised regardless).
- Influxes outside {1.0}.
- The h=0 quarantined "small hazard helps tight" secondary observation
  from v0.32. Tracked as a separate independent claim.
- Other ≤6-birth aggregate optima at n=8 from v0.21..v0.27. Demoted in
  the v0.33 Conclusion.
- Weight-axis questions (closed by v0.31).
- Per-agent / lifespan / heritability inspection (v0.34+).
- HedonismPolicy comparisons (deferred until lineage observability
  matures).
- Reading B substrate seam.
- Long-window observation (n_ticks > 200).
- Reproduction-efficiency / pool-size / cooldown variation.
- Fresh seed streams beyond 17..24 (no seeds 25..32).
- Mechanism declaration. Pooled H5 ROBUST unlocks investigation only.

## Implementation notes

### File-level changes

- **Modify (additive):**
  [[src/hedonism_harness/experiments/comparison_grid.py]] — add
  `V0_33_TIGHT_H_ARMS = tuple(arm for arm in V0_25_ARMS if
  arm.label.endswith("-influx-1.0"))`. Element-wise identical to
  `V0_32_TIGHT_H_ARMS` by construction. ~6 LOC.
- **New:** [[scripts/v0.33_sweep.py]] — 32-run sweep on seeds 17..24.
  Mirrors `v0.32_sweep.py` line-for-line with substitutions: SEEDS =
  17..24, BATCH_ID = `fear-hunger-v0.33-tight_gradient`, arm tuple =
  `V0_33_TIGHT_H_ARMS`. ~85 LOC.
- **New:** [[scripts/v0.33_audit.py]] — audit driver. Imports the v0.28
  module via `importlib.util` (mirrors v0.29..v0.32 pattern); imports
  `evaluate_audit` and `AuditThresholds` from `scripts/v0.30_audit.py`;
  reuses the v0.32 `SLOT_TO_LABEL` weight_labels override. Loads three
  streams via three `DiagnosticConfig` instances; merges per-seed
  dicts; computes single-stream diagnostic verdicts (default thresholds,
  `candidate_label="h=8"`) for each stream, computes pooled verdict
  (POOLED_THRESHOLDS=AuditThresholds(15, 15, 3, 15)) on the 24-seed
  union. Writes audit.md with explicit "Pooled 24-seed verdict (v0.33
  HEADLINE)" + "Single-stream diagnostic verdicts" section labels.
  ~330 LOC.
- **New:** `tests/test_comparison_grid_v0_33.py` —
  `V0_33_TIGHT_H_ARMS` shape (4 arms / hazards {0, 4, 8, 12}) +
  literal-subset identity to `V0_25_ARMS` (H1) + arm-object identity
  to `V0_32_TIGHT_H_ARMS` (H1b) + substrate field pinning + prior arm
  tuples (`ARMS`, `V0_15..27_ARMS`, `V0_29_ARMS`, `V0_30_TIGHT_W_ARMS`,
  `V0_31_TIGHT_W_ARMS`, `V0_32_TIGHT_H_ARMS`) untouched. ~110 LOC.
- **New:** `tests/test_v0_33_audit.py` — synthetic-fixture tests
  parallel to `tests/test_v0_31_audit.py`:
  - `evaluate_audit` invoked with hazard slot keys + `candidate_label
    ="h=8"` produces H7 / H8 labels referencing "h=8" on the pooled
    rule (no regression to "w=0.75").
  - Pooled H5 ROBUST: positive at thresholds (15/15/15) + just-meets
    + n_favoring_pool=14 falls to H6.
  - Pooled H6 WEAK: clear weak (Δ_low=10, Δ_high=5) + just-meets
    (Δ_low=Δ_high=3) + Δ_high=2 falls to H7.
  - Pooled H7 FAILURE: ties one neighbour, loses-by-lt-15.
  - Pooled H8 REVERSAL: leads-by-exactly-15 + does-not-fire-by-14 +
    low-neighbour-leads.
  - Priority H8_pool over H5_pool.
  - 1..16 pre-committed observation fixture: B_16 = (204, 212, 208);
    fires H6 under 16-seed-scaled thresholds (10/10/2/10) — sanity
    check on the proportional-scaling logic for the hazard axis.
  - Cross-stream merge: three 8-seed dicts merged into a 24-seed dict
    is well-formed (no key collisions; correct b50 lookups).
  ~190 LOC.
- **No changes** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`,
  `scripts/v0.28_*.py`, `scripts/v0.29_*.py`, `scripts/v0.30_audit.py`,
  `scripts/v0.31_*.py`, `scripts/v0.32_*.py`. Source modifications
  outside `comparison_grid.py` are zero. (`evaluate_audit`'s
  `thresholds` and `candidate_label` parameters from v0.31 / v0.32 are
  reused without modification.)
- **Documented:** this file (`docs/experiments/fear_hunger_v0.33.md`);
  Results appended after the audit runs.

### Determinism contract

- v0.21..v0.32 events.jsonl artifacts on disk are not regenerated.
- v0.21..v0.32 test suites continue to pass.
- The v0.28 module is imported but not modified — its byte-identity
  contract is preserved.
- The v0.30 `evaluate_audit` is imported but not modified — its
  default-preserving refactors from v0.31 / v0.32 remain anchored.

### LOC estimate

- `experiments/comparison_grid.py`: +6 LOC.
- `scripts/v0.33_sweep.py`: ~85 LOC.
- `scripts/v0.33_audit.py`: ~330 LOC.
- `tests/test_comparison_grid_v0_33.py`: ~110 LOC.
- `tests/test_v0_33_audit.py`: ~190 LOC.
- This doc: ~520 LOC.

Total v0.33 implementation: ~1,240 LOC. Tests should bring the suite
from 828 to ~850 (+~22).

## References

- [[docs/experiments/fear_hunger_v0.25.md]] — v0.25 source: 4-hazard ×
  3-influx grid; tight h*=8 small-margin claim. Source of stream 1.
- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 weight curve;
  source of the sister calibration arc closed by v0.31.
- [[docs/experiments/fear_hunger_v0.28.md]] — `EventBandTrajectory`
  library, `run_diagnostic(DiagnosticConfig)` entrypoint;
  `_band_aggregate_table` reused by v0.33 audit.
- [[docs/experiments/fear_hunger_v0.29.md]] — v0.29 fresh-stream
  reproducibility check; introduces the methodological rule v0.30..
  v0.33 are built on.
- [[docs/experiments/fear_hunger_v0.30.md]] — v0.30 single-stream
  classifier source.
- [[docs/experiments/fear_hunger_v0.31.md]] — v0.31 third-stream
  calibration on the weight axis; introduces `AuditThresholds`,
  `POOLED_THRESHOLDS`, locked H6_pool phrase, three-stream merge
  pattern. v0.33 mirrors v0.31's audit verbatim except for the slot
  mapping and `candidate_label`.
- [[docs/experiments/fear_hunger_v0.32.md]] — v0.32 fresh-stream
  hazard-axis audit; H6 WEAK on stream 2; introduces
  `n_hazard_insensitive` and the `candidate_label` parameter. Source
  of stream 2.
- [[docs/handoffs/2026-05-06-v0.32-shipped-v0.33-planned.md]] —
  handoff specifying the post-calibration arc discussion gate; v0.33
  implementation surface fully documented in v0.32 pre-reg's H6
  decision rule.
- [[src/hedonism_harness/experiments/comparison_grid.py]] —
  V0_25_ARMS / V0_32_TIGHT_H_ARMS source.
- [[scripts/v0.30_audit.py]] — `evaluate_audit` source (no modification
  in v0.33; reuses v0.31 / v0.32 parameter additions).
- [[scripts/v0.31_audit.py]] — three-stream merge / pooled verdict
  pattern v0.33 mirrors.
- [[scripts/v0.32_audit.py]] — `SLOT_TO_LABEL` / `SLOT_TO_HAZARD`
  weight_labels override v0.33 reuses for stream loading.
- [[scripts/v0.32_sweep.py]] — sweep pattern v0.33_sweep mirrors.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".
