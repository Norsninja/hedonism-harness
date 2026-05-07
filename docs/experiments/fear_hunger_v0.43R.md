# v0.43R — tick-50 food-density intervention (substrate causal probe, replacement for halted v0.43)

**Status:** pre-registered 2026-05-07; **HALTED POST-SWEEP 2026-05-07**
on substrate-mismatch finding #2 (see SUBSTRATE_PREFLIGHT_HALT_2
addendum at the bottom). Sweep ran (48 runs, ~18s); audit ran (~3s)
and emitted a mechanical `FOOD_DENSITY_NOT_NECESSARY` verdict from
no-op data. **The verdict is NOT cited as a scientific result.**
Replacement track: v0.44 candidate (respawn-schedule intervention)
pending feasibility probe.
**Date:** 2026-05-07
**Branch:** `claude/v0.43-resource-flattening-intervention`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated;
`mean_top_lineage_b50_share` pooled 0.635 → 0.785), v0.35 (founder-
survival timing — **H6 EXPANSION-SUPPORTED**; pooled `wad_rate`
0.458 → 0.792), v0.36 (founder-trait heritability —
**H6 TRAIT-LINKED-FLAT**), v0.37 (dominance timing decomposition —
**H6 STABLER-EARLY-LEADERSHIP**), v0.38 (leader post-50 advantage —
**H5 LEADER-ADVANTAGE-AMPLIFIED**; pooled 3.948 → 8.990), v0.39
(fresh-stream calibration of v0.38 — **H5_POOLED_ONLY**), v0.40
(cross-stream stability audit — **H5 STREAM-STABLE** on 3 of 4
streams), v0.41 (second fresh-stream calibration —
**v0.41_OLD_LIKE + H5_STREAM_STABLE_N5** on 4 of 5 streams), v0.42
(first causal probe — **MECHANISM_NOT_NECESSARY**; tick-50 leader
hard kill at the boundary did not collapse post-50 dominance), v0.43
(**HALTED PRE-SWEEP** on substrate feasibility finding: at h=8 the
food zone is fully saturated at tick 50 across all probed seeds,
making chamber-wide flatten and reverse-row-major shuffle no-ops at
the primary test hazard; the pre-reg's eligibility predicate
`kind ∈ {EMPTY, FOOD}` is literally correct but the scientific intent
required an EMPTY footprint that does not exist in `tight_gradient`'s
fully-painted layout).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".
**Halted predecessor:** [[docs/experiments/fear_hunger_v0.43.md]] —
SUBSTRATE_PREFLIGHT_HALT preserved as part of the v0.43 record;
the additive `src/` extension (event class + intervention helpers +
arm constant) lands in this slice and is reused.

## Question

v0.42 ruled out the tick-50 leader's identity as a necessary causal
carrier of post-50 dominance under hard-kill removal. v0.43's
flatten/shuffle design proved non-operative at the primary test
hazard (h=8) because the food zone is at maximum density at the
v0.34..v0.42 anchor moment — the substrate has nothing to flatten
or relocate when every eligible cell already holds the same value.

The substrate feasibility probe revealed an **independent finding
of its own**: under `tight_gradient` + `food_respawn_cooldown=50` +
`hazard_damage=8`, the 24-cell food zone is saturated (24 × 20.0 =
480.0) across the entire seed band 49..56 from at least tick 20
onwards. The post-50 dominance pattern emerges from a **food-
superabundant** substrate at the locking moment. Whatever drives
dominance at h=8 is reading off a substrate where food is not
scarce.

The active question for v0.43R is:

> **Is food DENSITY (per-cell food magnitude) at the tick-50 anchor
> moment NECESSARY for the post-50 dominance pattern? If we halve
> every eligible cell's food value at the tick-50/tick-51 boundary,
> does post-50 dominance fail to reconstitute, or does it persist
> regardless of food abundance?**

This is a **density-magnitude necessity probe** at the same anchor
moment v0.42 used. It is not a spatial-redistribution probe (v0.43's
question, which proved non-operative); it is a magnitude probe at a
saturated substrate. The cleanest causal lever the substrate offers
at h=8 tick 50 is its global density.

The placebo control for v0.43R is a **density-preserving
perturbation**: a deterministic per-pair value redistribution that
preserves total food density while shifting the multiset. This
distinguishes "density matters" (B disrupts; C does not) from "any
substrate value rewrite disrupts" (both B and C disrupt
comparably) — parallel in cadence to v0.42's leader vs size-matched-
non-leader control.

If post-50 dominance collapses under density halving but not under
density-preserving perturbation, **food density at tick 50 is
necessary** for the v0.34..v0.41 pattern. If both interventions
disrupt comparably, the system is sensitive to **any substrate
value rewrite**, not specifically to density reduction. If neither
disrupts, the causal source lies further upstream than the food
substrate's value layer (hazard topology, chamber geometry, founder-
trait + spatial-position interaction, birth-position constraints).

## What this slice tests, and what it does NOT test

### Tests

- Whether **`post_intervention_top_lineage_b50_share`** (the same
  primary observable as v0.42 / v0.43) in the density-halving arm B
  drops by ≥ 0.15 relative to the null arm A at h=8, AND the
  density-preserving perturbation arm C remains within ±0.10 of arm
  A at h=8. **This is the primary density-necessity test.**
- Whether the B-vs-A reduction is larger at h=8 than at h=0
  (secondary observable; tests hazard-amplification specificity of
  the density-necessity effect).
- Whether the intervention's `FoodRedistributedByIntervention`
  summary events are emitted exactly once per intervention-firing
  run, with the correct `intervention_kind`, `total_food_before`,
  `total_food_after`, and `n_cells_changed` fields.
- Whether B preserves (`total_food_after ≈ 0.5 × total_food_before`)
  and C preserves (`total_food_after ≈ total_food_before`) the
  expected density invariants.
- Whether the **default-None and `kind="null"` paths** continue to
  be byte-identical to pre-v0.42 / v0.42 behaviour.
- Whether the auxiliary finding **DENSITY_REDUCTION_ABLATES_REPRODUCTION**
  fires per-hazard: B produced > 2 of 8 runs with zero post-50
  surviving-lineage births at any hazard (parallel to v0.43's
  FLATTEN_ABLATES_REPRODUCTION but for the density-reduction
  variant).

### Does NOT test

- **Mechanism sufficiency.** Necessity only.
- **Mechanism specificity.** v0.43R cannot distinguish food-energy-
  per-pickup from food-zone-occupancy-time from foraging-route-
  geometry. Refinement interventions reserved for v0.44+.
- **Hazard generalisation.** Only h=0 and h=8 are tested.
- **Cross-stream calibration of the intervention.** Seeds 49..56
  only; v0.44+ candidate.
- **The v0.34..v0.43 corpus.** v0.43's halt addendum stands as the
  historical record. v0.43R does NOT re-run any prior reducer or
  the halted v0.43 sweep.
- **Spatial concentration disruption.** v0.43R does not destroy the
  food zone's spatial layout (kind topology preserved). Spatial-
  redistribution interventions are reserved for v0.44+, conditional
  on a chamber redesign that has untyped EMPTY space outside the
  food zone (the tight_gradient chamber's saturated-zone layout
  rules out chamber-wide redistribution at h=8).
- **Hazard topology disruption.** HAZARD-cell positions and counts
  are unchanged. Reserved for v0.44+ candidate (h).
- **Wall-cell modifications.** Walls are inviolate.
- **Density factors other than 0.5.** Dose-response (e.g., factor=
  0.25) is reserved for v0.44+ if v0.43R lands borderline.
- **Magnitude framing as "spread" or "amplification".** v0.43R's
  primary uses absolute-share differences at h=8 (same convention
  as v0.42 / v0.43).

### Deferred (v0.44+ candidates, conditional on v0.43R outcome)

- **If FOOD_DENSITY_NECESSARY fires** (B drops; C does not). v0.44
  candidates: (a) hazard-grid expansion; (b) dose-response sweep
  (factors 0.75 / 0.5 / 0.25); (c) cross-stream calibration on
  seed band 57..64; (d) sufficiency probe (boost density on a
  freshly-depleted substrate via injection).
- **If SUBSTRATE_PERTURBATION_DISRUPTS fires** (B and C both
  disrupt). v0.44 candidate: refine the perturbation magnitude.
  C's per-cell |Δ| is matched to B's (see Mechanism §C-arm
  algorithm); a smaller-magnitude C perturbation would test
  whether the dominance pattern is fragile to any value rewrite
  at all, or only to large rewrites.
- **If FOOD_DENSITY_NOT_NECESSARY fires** (B does not disrupt).
  v0.44 candidate: pivot to non-food substrate interventions —
  hazard relocation (h), chamber geometry sweep (i). Food-layer
  causal levers are exhausted; the cause lives outside the food
  substrate at the anchor moment.
- **If DENSITY_REDUCTION_ABLATES_REPRODUCTION fires per-hazard**
  (auxiliary). v0.44 candidate: smaller density factor (0.75) to
  separate "density matters for dominance" from "density matters
  for reproduction at all".

### Quarantined (not v0.43R inputs)

- v0.34..v0.42 reducer outputs. v0.43R reads only its own sweep
  events (parallel to v0.43's design discipline).
- HedonismPolicy. Mesa migration. v0.36 founder traits. Cross-
  stream calibration.
- The halted v0.43 sweep. **No v0.43 sweep was executed**, so there
  is no v0.43 corpus to read. The halted v0.43 pre-reg stands as
  the historical record of a pre-sweep halt.

## Conservation framing — additive over v0.43's substrate primitives

v0.43R extends v0.43's already-landed substrate-rewrite primitives
with two new `kind` values and two new helper functions. The
primitives that v0.43 contributed (and v0.43R reuses unchanged):

- `FoodRedistributedByIntervention` event class (with the digest
  fields). v0.43R writes the same event with new
  `intervention_kind` strings.
- The `_eligible_cells` / `_eligible_cells_digest` /
  `_food_multiset_digest` helpers in `core/interventions.py`.
- The chamber-runner `optional_intervention` hook (unchanged from
  v0.42).

Modifications under v0.43R:

- **Modified module:** `src/hedonism_harness/core/interventions.py`
  - Two new `kind` literal values: `"reduce_food_density_50pct_at_tick50"`,
    `"density_preserving_perturbation_at_tick50"`.
  - Two new rewrite functions:
    `_reduce_food_density_over_eligible_cells`,
    `_density_preserving_perturbation_over_eligible_cells`.
  - Extended `apply_intervention` dispatcher to route the new kinds
    through `_apply_food_redistribution` (existing v0.43 entry
    point reused with kind dispatch on rewrite logic).
  - Existing `null` / `kill_tick50_leader` /
    `kill_size_matched_nonleader` / `flatten_food_at_tick50` /
    `shuffle_food_at_tick50` paths remain byte-identical.
- **No new event types.** The existing
  `FoodRedistributedByIntervention` event suffices for both new
  kinds (kind label is a field; same digest semantics apply: B
  digest changes, C digest changes).
- **No new chamber-runner hook.** v0.42's hook is reused.
- **`comparison_grid.py`**: one new constant
  `V0_43R_INTERVENTION_ARMS` (additive only; existing arms tuples
  unchanged, including v0.43's `V0_43_INTERVENTION_ARMS`).

The following are NOT modified:

- Existing chamber, policy, or population-dynamics behaviour
  outside the new intervention `kind` paths. Default-None and
  `kind="null"` remain byte-identical to pre-v0.42.
- All v0.34..v0.42 reducer scripts and audits.
- The halted v0.43 pre-reg (preserved as historical record).
- Pre-v0.43R events on disk. Re-running prior sweeps with default
  `optional_intervention=None` produces byte-identical events.jsonl
  files.
- v0.42's kill paths — byte-identical when re-run on v0.43R branch
  (regression test H2e, parallel to v0.43's).

## Mechanism

v0.43R ships:

1. Two new intervention kinds in
   `src/hedonism_harness/core/interventions.py`.
2. A new sweep driver and arm tuple.
3. A v0.43R audit reducer that consumes the v0.43R sweep events.
4. Paired test files for each addition.
5. This pre-reg.
6. A new manifest doc post-Results.

### 1. Intervention extensions (`src/hedonism_harness/core/interventions.py`)

The existing `InterventionConfig.kind` Literal is extended to:

```python
kind: Literal[
    "null",
    "kill_tick50_leader",
    "kill_size_matched_nonleader",
    "flatten_food_at_tick50",
    "shuffle_food_at_tick50",
    "reduce_food_density_50pct_at_tick50",       # NEW v0.43R
    "density_preserving_perturbation_at_tick50", # NEW v0.43R
]
```

Two new pure-function helpers:

```python
def _reduce_food_density_over_eligible_cells(world, factor=0.5) -> ...:
    """B arm. Compute eligible_cells. For every eligible cell:
    food_value <- factor * food_value. Update kind to FOOD if
    new_value > 0 else EMPTY. Hazard, wall, safe cells unchanged.
    Total food preserved at factor * total_food_before."""

def _density_preserving_perturbation_over_eligible_cells(world) -> ...:
    """C arm. Compute eligible_cells (sorted (x, y)). For each
    consecutive pair (i, i+1) where i is even:
        s = food_value[cells[i]] + food_value[cells[i+1]]
        food_value[cells[i]] = 0.25 * s
        food_value[cells[i+1]] = 0.75 * s
    If n_eligible is odd, the last cell stays unchanged. Update
    kind cell-by-cell (FOOD if new_value > 0 else EMPTY). Hazard,
    wall, safe cells unchanged. Total food exactly preserved
    (each pair sum preserved)."""
```

Selection rules:

- **`reduce_food_density_50pct_at_tick50` (B arm)**: at tick 50/51
  boundary, multiply every eligible cell's `food_value` by 0.5.
  Cell kind updates to FOOD where new value > 0 else EMPTY (in
  practice: cells already at value > 0 stay FOOD; cells at value =
  0 stay EMPTY). Hazard/wall/safe cells unchanged. Total food
  drops to exactly 0.5 × total_food_before.
- **`density_preserving_perturbation_at_tick50` (C arm)**: at the
  same boundary, redistribute `food_value` within consecutive
  `(x, y)`-sorted eligible-cell pairs using a 25/75 split: the
  first cell of each pair receives 25% of the pair's combined
  value, the second cell receives 75%. Per-pair sum exactly
  preserved → grand total exactly preserved. Cell kind updates
  per-cell. Hazard/wall/safe unchanged.

Determinism contract:

- Both new kinds are pure functions of tick-50 chamber state. No
  new RNG. No `model.streams` draws.
- For a given (seed, hazard, intervention_kind), the intervention
  produces the same post-state every time.
- The 25/75 split is a fixed deterministic rule; reverse-pair
  iteration order is locked at `(x, y)` ascending pairs.

### Why 25/75 for C?

The 25/75 split is **magnitude-matched to B's halving**:

- B per-cell change at h=8 (saturated, all v=20): every cell
  transitions 20 → 10. Per-cell |Δ| = 10.
- C per-cell change at h=8: each pair `(20, 20)` transitions to
  `(0.25 × 40, 0.75 × 40) = (10, 30)`. Per-cell |Δ| = 10 (cell 0
  drops by 10; cell 1 rises by 10).

Both interventions perturb every saturated cell by exactly 10
units in absolute value. Total food differs (B halves, C
preserves), but the per-cell shock magnitude is matched. This
makes C a tight magnitude-matched control for B: if dominance
disrupts under both, the disruption is shock-driven; if only
under B, the disruption is density-driven.

For h=0 (heterogeneous substrate), per-cell magnitudes differ
between B and C because pair sums vary. The h=8 case (where the
primary test fires) is the cleanest comparison.

### 2. Event reuse (`core/events.py`)

`FoodRedistributedByIntervention` (added in v0.43's commit) is
reused unchanged. The two new kinds emit the same event class,
distinguished by `intervention_kind` field value.

### 3. Sweep + arm tuple (`scripts/v0.43R_sweep.py`,
   `comparison_grid.py` additions)

Three arms × 2 hazards × 8 seeds = **48 runs**. Arm tuple:

```python
V0_43R_INTERVENTION_ARMS: tuple[Arm, ...] = (
    # A_null (no intervention; baseline)
    _v0_43r_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    _v0_43r_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    # B_reduce_food_density_50pct (treatment: density halved)
    _v0_43r_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="B_reduce_food_density_50pct",
                intervention_kind="reduce_food_density_50pct_at_tick50"),
    _v0_43r_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="B_reduce_food_density_50pct",
                intervention_kind="reduce_food_density_50pct_at_tick50"),
    # C_density_preserving_perturbation (multiset-shifting placebo, density preserved)
    _v0_43r_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="C_density_preserving_perturbation",
                intervention_kind="density_preserving_perturbation_at_tick50"),
    _v0_43r_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="C_density_preserving_perturbation",
                intervention_kind="density_preserving_perturbation_at_tick50"),
)
```

Arm labels prefixed `v043R-` to disambiguate from the halted v0.43
arms. Output directory: `runs/fear-hunger-v0.43R-tight_gradient/`.

Seeds: 49..56 (same as halted v0.43 design). Substrate parameters
inherited from V0_25 substrate via `dataclasses.replace`, identical
to the halted v0.43 wiring.

### 4. v0.43R audit (`scripts/v0_43R_intervention_audit.py`)

Imports only `LineageReplayError` via `importlib.util`. Pure stdlib
otherwise.

Reads:

- Per-arm `comparison.csv` from
  `runs/fear-hunger-v0.43R-tight_gradient/arms/`.
- Per-run `events.jsonl` (specifically:
  `FoodRedistributedByIntervention` events + post-50 `AgentBorn`
  events for the primary observable).

Halt invariants (5):

- **H2a (run count):** exactly 6 arms × 8 seeds = 48 runs on disk.
- **H2b (intervention-fire count per arm):**
  - A_null arms: 0 events per run.
  - B_reduce arms: exactly 1 event per run with
    `intervention_kind="reduce_food_density_50pct_at_tick50"`.
  - C_perturbation arms: exactly 1 event per run with
    `intervention_kind="density_preserving_perturbation_at_tick50"`.
- **H2c (effective_tick):** every fired event has
  `effective_tick=51`.
- **H2d (substrate conservation):**
  - For B (reduce): `abs(total_food_after - 0.5 *
    total_food_before) <= max(1e-3, 1e-5 * total_food_before)`.
    Multiset must change (digest_before != digest_after) on any
    run with `total_food_before > 0`.
  - For C (perturbation): `abs(total_food_after -
    total_food_before) <= max(1e-3, 1e-5 * total_food_before)`.
    Multiset must change (digest_before != digest_after) EXCEPT
    in the legitimate degenerate case where every pair sums to
    a value that splits identically — i.e., the substrate was
    already in 25/75 form, vanishingly rare in practice. On any
    C run where digest equality holds AND `n_cells_changed > 0`,
    halt — indicates an arithmetic bug. (If `n_cells_changed ==
    0` legitimately, both digests match and we record without
    halting.)
  - For both: `eligible_cells_digest` is consistent across all
    fired events (chamber geometry is seed-independent at tick
    50). Halt on drift.
  - For both: `n_eligible_cells` consistent with chamber geometry;
    `n_cells_changed <= n_eligible_cells`.
- **H2e (regression byte-identity):** sampled v0.42 A_null seed
  AND v0.42 B_kill_leader seed re-run with v0.43R code produce
  events.jsonl byte-identical to v0.42's sealed references. (Same
  invariant v0.43 declared; preserved through v0.43R because no
  pre-v0.43 path is modified.)
- **C-rises-above-A halt:** if `c_share_h8 > a_share_h8 + 0.10`,
  halt loud (substrate artefact unmodeled).

Computes per-(arm, seed):

- `post_intervention_top_lineage_b50_share` (identical formula to
  v0.42 / v0.43; no lineage exclusion since no lineage is killed).
- `total_post_50_births`, `top_lineage_id`, `top_lineage_post50_births`.
- Event fields: `intervention_kind`, `n_cells_changed`,
  `total_food_before`, `total_food_after`, digests.
- `excluded_zero_post50` (NaN if total_post_50_births = 0).

Aggregates per-(arm, hazard) and computes the locked decision rule.

Outputs eight CSVs under `runs/lineage-v0.43R/`:

- `per_run.csv` — 48 rows.
- `per_arm_per_hazard.csv` — 6 rows.
- `intervention_summary.csv` — 6 rows.
- `primary_test.csv` — 1 row (with explicit verdict booleans;
  see Decision rules).
- `secondary_test.csv` — 1 row.
- `verdict.csv` — 1 row.
- `auxiliary_findings.csv` — 2 rows (one per hazard).
- `byte_identity_anchor.csv` — 2 rows (v0.42 A_null + B_kill_leader
  fingerprints).

### Locked constants

```python
EXPECTED_HAZARDS: tuple[int, ...] = (0, 8)
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(49, 57))  # 49..56
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_N_TICKS: int = 200
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds

# Locked thresholds (parallel to v0.42 / v0.43)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Auxiliary threshold (parallel to v0.43's FLATTEN_ABLATES_REPRODUCTION)
AUXILIARY_DENSITY_REDUCTION_ABLATION_MAX_EXCLUDED: int = 2

# Conservation tolerances
TOTAL_FOOD_ABS_TOL: float = 1e-3
TOTAL_FOOD_REL_TOL: float = 1e-5

# B-arm density factor (locked)
B_DENSITY_FACTOR: float = 0.5

# C-arm split (locked)
C_PAIR_SPLIT_FIRST: float = 0.25
C_PAIR_SPLIT_SECOND: float = 0.75

# Arm labels
ARM_A_NULL: str = "v043R-A_null"
ARM_B_REDUCE: str = "v043R-B_reduce_food_density_50pct"
ARM_C_PERTURBATION: str = "v043R-C_density_preserving_perturbation"

# Intervention kind labels (extends v0.43)
KIND_NULL: str = "null"
KIND_REDUCE_DENSITY_50PCT: str = "reduce_food_density_50pct_at_tick50"
KIND_DENSITY_PRESERVING_PERTURBATION: str = "density_preserving_perturbation_at_tick50"
```

### Determinism — anchors

- v0.21..v0.42 events.jsonl + sidecar artifacts not re-read by the
  primary v0.43R audit. H2e regression check reads selected v0.42
  references for fingerprint comparison only.
- All v0.34..v0.42 test suites continue to pass (additive guard).
- Default `optional_intervention=None` is byte-identical to
  pre-v0.42 behaviour.
- `kind="null"` byte-identical to default-None.
- `kind="kill_tick50_leader"` and `kind="kill_size_matched_nonleader"`
  paths byte-identical when re-run on v0.43R branch.
- `kind="flatten_food_at_tick50"` and `kind="shuffle_food_at_tick50"`
  (v0.43's halted-but-landed kinds) byte-identical when re-run on
  v0.43R branch — they're not invoked by v0.43R but their code
  paths exist in `core/interventions.py` unchanged.
- Re-running v0.43R sweep with the same seeds produces byte-
  identical events.jsonl files.

### Wall-time estimate

- v0.43R sweep: ~13s (48 runs at locked parameters; comparable to
  v0.42).
- v0.43R audit: ~3s.
- Total v0.43R incremental wall-time: ~16s.

## Observables — pre-committed before reading the data

### Per-run — 48 rows total

- `arm` ∈ {A_null, B_reduce_food_density_50pct, C_density_preserving_perturbation}.
- `hazard` ∈ {0, 8}.
- `seed` ∈ {49..56}.
- `fired`: bool. True iff a `FoodRedistributedByIntervention` event
  was emitted. False for A_null. (v0.43's redefined `fired`
  semantics carry forward: firing is event-emission, independent
  of `n_cells_changed`.)
- `intervention_kind`: str.
- `n_eligible_cells`, `n_cells_changed`: int.
- `total_food_before`, `total_food_after`: float.
- `total_post_50_births`: int.
- `top_lineage_id`, `top_lineage_post50_births`: int.
- `post_intervention_top_lineage_b50_share`: float in [0, 1] (NaN
  if total_post_50_births == 0).
- `excluded_zero_post50`: bool.

### Per-(arm, hazard) — 6 rows total

- `mean_post_intervention_top_lineage_b50_share` (excluding NaN).
- `n_runs_used`, `n_excluded_zero_post50`.

### Primary test (`primary_test.csv` — 1 row)

- `a_share_h8`, `b_share_h8`, `c_share_h8`.
- `delta_b_minus_a_h8 := b_share_h8 - a_share_h8`.
- `delta_c_minus_a_h8 := c_share_h8 - a_share_h8`.
- `b_passes := delta_b_minus_a_h8 <= -PRIMARY_B_REDUCTION_THRESHOLD`.
- `c_passes := abs(delta_c_minus_a_h8) <= PRIMARY_C_TOLERANCE`.
- `c_below_a := delta_c_minus_a_h8 <= -PRIMARY_C_TOLERANCE`.
- `c_above_a := delta_c_minus_a_h8 > PRIMARY_C_TOLERANCE`.
- `food_density_necessary := b_passes AND c_passes`.
- `substrate_perturbation_disrupts := b_passes AND c_below_a`.
- `food_density_not_necessary := NOT b_passes`.
- `c_above_a_unmodeled_substrate_artefact := b_passes AND c_above_a`
  (halt cell — no scientific verdict emitted).
- `primary_fires := food_density_necessary OR
  substrate_perturbation_disrupts`.
- `verdict`: derived from booleans above (see Decision rules).

### Secondary test (`secondary_test.csv` — 1 row)

- `delta_b_minus_a_h0`, `delta_b_minus_a_h8`.
- `hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
- `secondary_fires := primary_fires AND hazard_amplified`.

### Auxiliary findings (`auxiliary_findings.csv` — 2 rows, one per hazard)

- `hazard`.
- `b_n_excluded_zero_post50`: number of B runs at this hazard with
  zero post-50 births (out of 8).
- `ablation_threshold_exceeded := b_n_excluded > 2`.
- `auxiliary_phrase_fires`: bool.

Auxiliary finding is **non-exclusive** of the primary verdict.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive `src/` modification).** Only the new intervention
  kinds + the new arm constant + the helper functions. All
  pre-v0.43R kind paths are byte-identical. Includes regression
  tests on a sampled v0.42 A_null seed AND a sampled v0.42
  B_kill_leader seed.
- **H2a (run count).** Exactly 48 runs on disk after v0.43R sweep.
- **H2b (intervention-fire count per arm).** A_null: 0; B: 1; C:
  1.
- **H2c (effective_tick).** Every fired event has
  `effective_tick=51`.
- **H2d (substrate conservation).**
  - For B: `total_food_after ≈ 0.5 × total_food_before` within
    tolerance; multiset shifts.
  - For C: `total_food_after ≈ total_food_before` within
    tolerance; multiset shifts (digest inequality) on any run
    where pair sums permit.
  - HAZARD/WALL/SAFE positions and counts unchanged.
- **H2e (regression byte-identity).** v0.42 A_null + B_kill_leader
  reference seeds re-run with v0.43R code produce events.jsonl
  byte-identical to v0.42's sealed references.
- **H3 (additive guard).** v0.21..v0.42 + v0.43-skipped tests
  still pass after v0.43R additions.
- **H4 (no mutation of pre-v0.43R surface).** All pre-v0.43R
  scripts, reducers, audits, arm tuples, chamber/policy/population
  modules — byte-identical (modulo additive kinds + arm constant
  + helper functions in `core/interventions.py`).

### Cautious form — three-way verdict on v0.43R's density-necessity question

The verdict is intentionally three-way, mutually exclusive on the
locked decision space, plus one halt cell:

**FOOD_DENSITY_NECESSARY.** **FIRES iff** `b_passes == True` AND
`c_passes == True`. Headline: halving the food density at the
tick-50/tick-51 boundary materially disrupts post-50 dominance,
while preserving total density (with a per-pair magnitude-matched
perturbation) does not. Food density at tick 50 is **necessary**
for the v0.34..v0.41 dominance pattern under the tested substrate;
the specific *distribution* of food values is not.

**SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE.** **FIRES iff**
`b_passes == True` AND `c_below_a == True`. Headline: both
density-halving and density-preserving perturbation disrupt
post-50 dominance. The pattern is sensitive to **any food-value
rewrite of comparable per-cell magnitude**, not specifically to
density reduction. v0.34..v0.41's correlational pattern reflects
fragility to substrate-shock rather than a density-specific causal
mechanism.

**FOOD_DENSITY_NOT_NECESSARY.** **FIRES iff** `b_passes == False`.
Headline: halving food density does not materially disrupt
post-50 dominance; the pattern reconstitutes through a surviving
lineage even with food abundance reduced by 50%. Food density at
tick 50 is **not necessary** for the pattern; the causal source
lives outside the food-substrate's value layer (hazard topology,
chamber geometry, founder-trait + spatial-position interaction,
birth-position constraints).

**C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt cell):** `b_passes
== True` AND `c_above_a == True`. Substrate artefact unmodeled at
pre-reg time. Audit halts loud (`LineageReplayError`); no
scientific verdict emitted.

(All four cells exhaust the rule space:
- `b_passes=True, c_passes=True` → FOOD_DENSITY_NECESSARY.
- `b_passes=True, c_below_a=True` → SUBSTRATE_PERTURBATION_DISRUPTS.
- `b_passes=True, c_above_a=True` → C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt).
- `b_passes=False, *` → FOOD_DENSITY_NOT_NECESSARY.)

### Auxiliary finding — independent of primary verdict

**DENSITY_REDUCTION_ABLATES_REPRODUCTION (per-hazard).** **FIRES
iff** `b_n_excluded_zero_post50 > 2` at any hazard. Reported
alongside the primary verdict; does NOT alter the verdict logic.
Headline: halving food density reduced per-cell food intake below
the threshold required to sustain post-50 reproduction in this
fraction of seeds at this hazard. **Descriptive substrate finding**:
density-as-magnitude can ablate reproduction at sufficient
reduction.

### Locked phrases for each verdict

> **FOOD_DENSITY_NECESSARY phrase:** "Halving the food density at
> the tick-50/tick-51 boundary materially disrupts the post-50
> dominance pattern at h=8: when food abundance is reduced by 50%
> across every eligible cell, the surviving lineages do not
> reconstitute concentration of comparable share. The density-
> preserving perturbation control (which redistributes food
> values across (x, y)-sorted consecutive pairs at a 25/75 split,
> preserving total density and matching per-cell magnitude) does
> NOT produce comparable disruption. Under the tested substrate,
> **food density at tick 50 is necessary** for the v0.34..v0.41
> dominance pattern; the specific *distribution* of food values
> across the food zone is not. v0.43R does not declare which
> property of food density carries the effect (food-energy-per-
> pickup, foraging-route geometry, hazard-adjacent niche
> structure); refinement interventions in v0.44+ are required.
> Necessity is established at one hazard level (h=8) on one seed
> band (49..56); cross-stream calibration and dose-response
> sweeps are reserved for v0.44+. Sufficiency is NOT tested."

> **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE phrase:** "Halving
> food density disrupts post-50 dominance at h=8, but the
> magnitude-matched density-preserving perturbation control
> produces comparable disruption. The post-50 dominance pattern
> is sensitive to **any food-value rewrite of comparable per-cell
> magnitude**, not specifically to density reduction. v0.34..v0.41's
> correlational pattern reflects fragility to substrate-shock
> rather than a density-specific causal mechanism. v0.44 candidate:
> reduce the C-arm's perturbation magnitude to test whether the
> pattern is fragile to any substrate value rewrite or only to
> large-magnitude rewrites. Mechanism remains unidentified at
> the food-density level."

> **FOOD_DENSITY_NOT_NECESSARY phrase:** "Halving the food density
> at the tick-50/tick-51 boundary does not materially disrupt the
> post-50 dominance pattern at h=8. A surviving lineage
> reconstitutes concentration-of-share even when food abundance
> is reduced by 50% across the food zone. **Food density at tick
> 50 is not necessary** for post-50 dominance under the tested
> substrate; the causal source lives outside the food-substrate's
> value layer at the anchor moment. v0.42 ruled out the tick-50
> leader's identity; v0.43R rules out tick-50 food density.
> Remaining substrate-anchored candidates: hazard topology,
> chamber geometry (wall-adjacency, reachability), founder-trait
> + spatial-position interaction at tick 50, and birth-position
> constraints. v0.44 candidate: hazard relocation intervention
> (h)."

> **DENSITY_REDUCTION_ABLATES_REPRODUCTION (auxiliary, per-hazard)
> phrase:** "At hazard h=N, the B_reduce_food_density_50pct arm
> produced > 2 of 8 runs with zero post-50 births: halving food
> density ablated reproduction itself rather than relocating
> dominance. This is a **descriptive substrate finding** parallel
> to but independent of the share-based primary verdict: the
> reduced per-cell food intake fell below the threshold required
> to sustain post-50 reproduction in this fraction of seeds at
> this hazard. The primary verdict is computed over n_used (non-
> excluded) runs; this auxiliary finding is reported alongside
> but does NOT alter the primary verdict logic. v0.44 candidate:
> use a milder density factor (e.g., 0.75) to separate
> density-matters-for-dominance from density-matters-for-
> reproduction-at-all."

### Caveats — locked, must appear in Results

- **Per-arm n is 8.** Conservative on n=8; not bullet-proof
  against noise excursions.
- **Necessity only.** Sufficiency not tested.
- **One seed band.** Seeds 49..56 only.
- **Two hazards only.** {0, 8}.
- **Hard density rewrite.** Both B (50% halving) and C (25/75
  pair redistribution) are deterministic rewrites at the boundary.
  No biological-realism claim.
- **Hazard topology preserved.** HAZARD-cell positions and counts
  unchanged. v0.43R does NOT test hazard-substrate causality;
  reserved for v0.44+ candidate (h).
- **Walls inviolate.** WALL cells never modified.
- **No respawn / position-targeted influx.** Substrate dynamics
  preserved. Influx in `tight_gradient` credits a global pool (no
  per-cell injection); the intervention's value rewrites persist
  unless cells are subsequently eaten.
- **No mechanism declaration even on the strongest outcome.** Even
  on FOOD_DENSITY_NECESSARY, v0.43R only establishes that density
  is necessary at one hazard, on one seed band, under one density
  factor. Mechanism specificity (which property of density)
  requires v0.44+.
- **Effect-size budget.** Same threshold (0.15) and tolerance
  (0.10) as v0.42 / v0.43. Cross-version comparability intentional.
- **Substrate state at h=8 anchor moment is saturated.** The probe
  finding documented in v0.43's halt addendum stands: at tick 50
  on `tight_gradient` + h=8, the food zone is at 480.0 across all
  seeds 49..56. v0.43R's B halves this to 240.0; C preserves at
  480.0 with multiset shifted. The substrate's saturation is
  intentionally NOT addressed by v0.43R (chamber design is held
  constant for comparability with v0.42).
- **C's per-cell magnitude match is exact only at h=8.** At h=0
  (heterogeneous substrate), per-cell |Δ| varies pair-by-pair
  because pair sums vary. The h=8 primary test is the cleanest
  comparison; h=0 is secondary descriptive context.
- **B's halving is uniform across all eligible cells.** Cells at
  value=0 (EMPTY-from-eating) stay at 0 after halving (`0 * 0.5
  = 0`); only cells with positive value transition. At h=8 (no
  EMPTY cells), every cell transitions; at h=0 (5–14 EMPTY cells
  per seed), only the FOOD cells transition. This asymmetry is
  acknowledged and does not affect the verdict logic (the primary
  test is at h=8, where every cell transitions).

### Reachability — sanity check

All three primary verdicts plus the halt cell are arithmetically
reachable:

- **FOOD_DENSITY_NECESSARY**: requires B share to drop by ≥ 0.15
  AND C share to stay within ±0.10 of A. Both bars independent
  and live; density-as-magnitude as cause would land here.
- **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE**: requires B AND C
  to both drop by ≥ 0.10 from A. If the system is fragile to any
  per-cell value rewrite of magnitude 10, this is where it lands.
- **FOOD_DENSITY_NOT_NECESSARY**: requires B share to NOT drop by
  ≥ 0.15. If post-50 dominance reconstitutes regardless of density,
  this is where it lands.
- **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt)**: requires C
  share to rise above A by > 0.10 while B drops. Mechanistically
  unmotivated; halt loud.

### Anchor identity

- v0.43R inherits no cross-version artifact-identity anchors against
  prior reducer outputs. It inherits two byte-identity anchors:
  v0.42 A_null + B_kill_leader fingerprints (regression guard, H2e).

## Decision rules

### Primary

| `b_passes` | C-direction             | verdict                                              |
|:----------:|-------------------------|------------------------------------------------------|
| True       | `c_passes` (\|c−a\|≤0.10) | **FOOD_DENSITY_NECESSARY**                           |
| True       | `c_below_a` (c−a≤−0.10) | **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE**        |
| True       | `c_above_a` (c−a>+0.10) | **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT** (halt)    |
| False      | any                     | **FOOD_DENSITY_NOT_NECESSARY**                       |

### Auxiliary (independent of primary)

`DENSITY_REDUCTION_ABLATES_REPRODUCTION` per hazard, fires iff
`b_n_excluded_zero_post50 > 2` at that hazard.

### Secondary (descriptive context only)

`hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.

### Halt conditions

- **H1 fails** — pre-v0.43R surface mutated, OR v0.42 byte-
  identity regression fails. Halt; revert.
- **H2a fails** — run count != 48. Halt.
- **H2b fails** — intervention fires per arm violate locked counts.
  Halt.
- **H2c fails** — `effective_tick` != 51 on any fired event. Halt.
- **H2d fails** — substrate conservation violated. Halt.
- **H2e fails** — sampled byte-identity regression fails. Halt.
- **H3 / H4 fail** — pre-v0.43R contract broken. Halt; revert.
- **C-rises-above-A cell** — substrate artefact unmodeled. Halt
  loud; do NOT silently bin into a verdict.

## Out of scope (v0.43R)

- Sufficiency testing.
- Mechanism specificity (which property of density).
- Hazard generalisation beyond {0, 8}.
- Cross-stream calibration beyond seeds 49..56.
- Cross-stream calibration of v0.42 (deferred candidate (j)).
- Hazard-relocation interventions.
- Chamber-geometry interventions.
- Density factors other than 0.5 (dose-response).
- Spatial-redistribution interventions (would require chamber
  redesign per the v0.43 halt finding).
- HedonismPolicy comparisons.
- Mesa migration.
- Edits to existing v0.34..v0.43 reducer surface or pre-v0.43R
  arm tuples.
- Re-running the halted v0.43 sweep (no v0.43 sweep was executed).

## Implementation notes

### File-level changes

- **Modified (in `src/`):**
  - `src/hedonism_harness/core/interventions.py` (~150 LOC added):
    extend `InterventionConfig.kind` Literal with two new values;
    add `_reduce_food_density_over_eligible_cells`,
    `_density_preserving_perturbation_over_eligible_cells`; extend
    `_apply_food_redistribution` dispatcher to route the new kinds.
    **Existing `null` / `kill_*` / `flatten_*` / `shuffle_*` paths
    untouched.**
  - `src/hedonism_harness/experiments/comparison_grid.py` (~30 LOC
    added): new constant `V0_43R_INTERVENTION_ARMS` (additive).
- **No new event types.** `FoodRedistributedByIntervention` reused.
- **New (in `scripts/`):**
  - `scripts/v0.43R_sweep.py` (~80 LOC).
  - `scripts/v0_43R_intervention_audit.py` (~600 LOC).
- **New (in `tests/`):**
  - `tests/test_interventions_v0_43R.py` (~250 LOC).
  - `tests/test_world_intervention_hook_v0_43R.py` (~120 LOC).
  - `tests/test_v0_43R_sweep.py` (~120 LOC).
  - `tests/test_v0_43R_intervention_audit.py` (~500 LOC).
- **Documented:** this pre-reg. Results appended after audit.
- **Manifest:** new file
  `docs/artifacts/v0.34_v0.43R_local_corpus_manifest.md` post-
  Results. The v0.34_v0.42 manifest is preserved as a sealed
  historical record; v0.43's halted-design manifest is not
  written (no sweep was executed).

### Tests required (locked at pre-reg time)

- **Intervention extensions:**
  - `_reduce_food_density_over_eligible_cells(world, factor=0.5)`
    halves every eligible cell's food_value; preserves
    `total_after = factor * total_before` within tolerance; sets
    kind to FOOD if new > 0 else EMPTY; HAZARD/WALL/SAFE
    untouched.
  - `_density_preserving_perturbation_over_eligible_cells(world)`
    redistributes within `(x, y)`-sorted consecutive pairs at 25/75
    split; per-pair sum exactly preserved; grand total exactly
    preserved; multiset shifts on any non-degenerate substrate;
    HAZARD/WALL/SAFE untouched; on odd n_eligible, last cell
    unchanged.
  - `apply_intervention` routes the new kinds correctly.
  - Determinism: same world state at firing → byte-identical
    post-state.
  - `kind="null"` remains byte-identical to default-None
    (regression).
- **World hook:**
  - Both new kinds fire at `tick_count == 51`, emit exactly one
    `FoodRedistributedByIntervention` event with correct fields.
  - B's `total_food_after ≈ 0.5 × total_food_before`.
  - C's `total_food_after ≈ total_food_before`; multiset shifts.
  - No `AgentDied(cause="INTERVENTION")` events emitted by either
    new kind.
  - v0.42 A_null + B_kill_leader byte-identity regression
    (extends v0.43's regression for the new kinds).
- **Sweep:** locked constants, arm tuple, seeds, hazards.
- **Audit:** locked thresholds, all 5 H2 halts, primary/secondary/
  auxiliary test arithmetic, three-way verdict + halt cell,
  locked-phrase regression guards, end-to-end synthetic fixture.

### Determinism contract

- All new helpers are pure functions of tick-50 chamber state.
- No new RNG. No `model.streams` draws.
- Default-None and `kind="null"` paths byte-identical to pre-v0.42.
- v0.42 kill paths byte-identical when re-run on v0.43R branch.
- v0.43's flatten/shuffle paths (landed but not invoked by v0.43R)
  byte-identical when re-run on v0.43R branch.

### LOC estimate

- `interventions.py` extension: ~150 LOC.
- `comparison_grid.py` arm tuple: ~30 LOC.
- Sweep + audit: ~700 LOC.
- 4 test files: ~1,000 LOC.
- This doc: ~700 LOC.
- Manifest (post-Results): ~250 LOC.

Total v0.43R: ~2,800 LOC. Tests should bring the suite from 1,333
to ~1,373 (+~40).

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1333 passed, 7 skipped (baseline including
                                v0.43 substrate-finding skip)
uv run python scripts/core_smoke_test.py   ok
```

(Pre-reg adds no executable code; CI is identical to v0.43-WIP
state.)

## Results

**Status:** sweep + audit executed 2026-05-07; **verdict halted as
non-citable.** The audit emitted `FOOD_DENSITY_NOT_NECESSARY`
mechanically because `delta(B−A) = 0.000` and `delta(C−A) = 0.000`
on every (hazard, seed) bucket. **The locked verdict phrase is NOT
fired** — the intervention was a no-op (see
SUBSTRATE_PREFLIGHT_HALT_2 below).

## SUBSTRATE_PREFLIGHT_HALT_2 (2026-05-07)

This is the **second substrate-mismatch finding** in the v0.43 / v0.43R
arc. It is documented as a first-class halt rather than as a result.

### What the sweep produced

48-run sweep (`scripts/v0.43r_sweep.py`) ran cleanly. All 32 fired
events (16 B + 16 C runs) carry the same numeric profile:

| field                      | value (every fired event, every seed, both hazards) |
|----------------------------|-----------------------------------------------------:|
| `n_eligible_cells`         | 24                                                    |
| `n_cells_changed`          | **0**                                                 |
| `total_food_before`        | **0.0**                                               |
| `total_food_after`         | **0.0**                                               |
| `food_multiset_digest_before == food_multiset_digest_after` | True |

Both interventions operated on a substrate where every eligible cell
had `food_value = 0`. Halving zeros yields zeros; the 25/75
pair-redistribution of `(0, 0)` yields `(0, 0)`. Multiset digest is
trivially preserved. Per-cell magnitude shock is zero.

### Cause: v0.43R pre-reg's substrate model was wrong

The v0.43R pre-reg's locked claim was that at h=8 tick 50 the food
zone is **saturated** (24 × 20 = 480). That claim was inherited from
the v0.43 SUBSTRATE_PREFLIGHT_HALT addendum, which characterized the
substrate based on a feasibility probe run with the **wrong simulation
config**:

- Probe (incorrect): `policy_factory` defaulted to `HedonismPolicy`,
  `auto_reproduction` defaulted to `False`. Population stayed at 5
  founders. Foraging was minimal. Food zone stayed at 480 across all
  ticks.
- Actual sweep config (V0_25 anchor): `policy_factory =
  GradientPolicy`, `auto_reproduction = True`,
  `trait_config = TraitConfig(unbounded_mutation=True)`. By tick ~10,
  population multiplied to 14+ agents who aggressively forage and
  deplete the 24-cell zone faster than `food_respawn_cooldown=50`
  refills it. **By tick ~44 the zone is at 0; it stays at 0 through
  tick 50/51 across all 8 seeds at both hazards.**

The earlier probe was a hand-rolled `run_chamber` invocation that
skipped the policy/auto-reproduction wiring that
`comparison_grid._run_one_arm_seed` applies. The shortcut produced
opposite-direction misleading data.

### Methodological lesson (locked into the project record)

> **Always feasibility-probe through the actual sweep code path
> (`_run_one_arm_seed` or `run_comparison_grid`), never through a
> hand-rolled `run_chamber` invocation.** The sweep applies
> `arm.policy_factory`, `arm.auto_reproduction`,
> `TraitConfig(unbounded_mutation=True)`, and the `setup_observer`
> that enables auto-reproduction; a hand-rolled invocation that
> omits any of these will produce a substrate that does not match the
> sweep's actual dynamics.

This lesson must propagate to v0.44+ feasibility probes.

### Retracted claim (was in v0.43's SUBSTRATE_PREFLIGHT_HALT)

The v0.43 halt addendum's "h=8 tick-50 substrate is saturated" finding
is **retracted** as config-mismatched. The corrected substrate finding
(below) supersedes it. The v0.43 addendum is preserved as the
historical record of the original (incorrect) characterization, with
a retraction note added at the top of that addendum.

### Corrected substrate finding (legitimate; survives the halt)

> Under the V0_25-anchored substrate (`tight_gradient` chamber +
> `GradientPolicy` + `auto_reproduction=True` +
> `TraitConfig(unbounded_mutation=True)` +
> `food_respawn_cooldown=50` + `energy_pool_initial=1500` +
> `ambient_influx_rate=1.0`), the 24-cell food zone is **completely
> depleted** at tick 50 across all probed seeds (49..56) at both
> h=0 and h=8. The post-50 dominance pattern that v0.34..v0.41
> measured emerges from a substrate where, at the locking tick, food
> has been totally consumed and the system is subsisting on respawn
> flow. **The causal lever at tick 50 is not `food_value` (already
> zero); it is `world.respawn_at_tick` — which lineage is positioned
> to claim the next refill.**

### What this halt preserves

- The pre-reg's locked phrases for `FOOD_DENSITY_NECESSARY` /
  `SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE` /
  `FOOD_DENSITY_NOT_NECESSARY` are **not fired**. The mechanical
  `FOOD_DENSITY_NOT_NECESSARY` emission from the audit is
  disqualified by the no-op condition (`delta = 0` because the
  intervention literally did nothing). Citing it would be a category
  error analogous to v0.43's halted-design no-op.
- The v0.43R `src/` extension (the `KIND_REDUCE_DENSITY_50PCT` and
  `KIND_DENSITY_PRESERVING_PERTURBATION` kinds, helpers, dispatcher
  branch) is **preserved**. v0.42 / v0.43 byte-identity invariants
  hold. Future versions can invoke these kinds against a
  non-depleted substrate (different chamber or earlier tick) without
  modification.
- All v0.43R tests (24 unit + 12 hook + 11 sweep + 36 audit = 83
  tests) pass on the v0.43R branch.

### v0.44 candidate (locked direction; design pending feasibility probe)

> **Pivot to a respawn-schedule intervention.**

The substrate's causal lever at tick 50 is not the (depleted)
food-value layer; it is the per-cell respawn schedule
(`world.respawn_at_tick`). v0.44 will operate on this layer:

- **A_null**: no intervention.
- **B_delay_respawn_schedule**: at tick 50/51, add a constant offset
  to every cell's `respawn_at_tick` value (where currently
  scheduled). Slows post-50 refill flow. Tests "is the post-50 food
  flow rate causal?".
- **C_permute_respawn_schedule**: at tick 50/51, permute the
  scheduled refill ticks among the scheduled cells. Same multiset
  of refill times, different cell-to-time assignments. Tests "is
  the spatial pattern of WHICH cells refill WHEN causal, given the
  same overall flow rate?".

Open v0.44 design questions (deferred to v0.44 pre-reg discussion):

- Delay magnitude (B): +25 / +50 / +100 ticks?
- Permutation scope (C): all cells with `respawn_at_tick > 0`, or
  only those with `respawn_at_tick > 51` (scheduled for *future*
  refill)?
- Eligible-cell predicate: cells with `respawn_at_tick > 0` (i.e.,
  scheduled), excluding HAZARD/WALL/SAFE.

A feasibility probe (using `_run_one_arm_seed` per the
methodological lesson above) will tabulate the per-(seed, hazard)
distribution of `respawn_at_tick` values at tick 50 before v0.44
locks. If the substrate has heterogeneous schedules (likely, given
agents stagger their consumption), B and C will be operative; if
schedules are clustered or absent, v0.44 needs another redesign.

### CI gate at v0.43R halt time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1414 passed, 7 skipped (6 baseline + 1 v0.43
                                substrate-finding skip)
uv run python scripts/core_smoke_test.py                ok
uv run python scripts/v0.43r_sweep.py                   completed (no-op)
uv run python scripts/v0_43r_intervention_audit.py      completed; verdict
                                                        FOOD_DENSITY_NOT_NECESSARY
                                                        emitted but DISQUALIFIED
                                                        per this halt addendum.
```
