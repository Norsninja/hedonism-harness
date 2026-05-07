# v0.44 — tick-50 respawn-schedule intervention (substrate causal probe; pivot from v0.43R's depleted-substrate finding)

**Status:** pre-registered 2026-05-07; pending implementation.
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
**H5 LEADER-ADVANTAGE-AMPLIFIED**), v0.39 (fresh-stream calibration —
**H5_POOLED_ONLY**), v0.40 (cross-stream stability — **H5
STREAM-STABLE** on 3 of 4 streams), v0.41 (second fresh-stream
calibration — **v0.41_OLD_LIKE + H5_STREAM_STABLE_N5**), v0.42
(first causal probe — **MECHANISM_NOT_NECESSARY**; tick-50 leader
hard kill did not collapse post-50 dominance), v0.43 (**HALTED
PRE-SWEEP**, retracted; first substrate probe attempt; saturated-zone
claim was config-mismatched), v0.43R (**HALTED POST-SWEEP**,
disqualified; food-density intervention was mechanically a no-op
because the V0_25-anchored substrate is **completely depleted** at
tick 50).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".
**Halted predecessors (this branch):** [[docs/experiments/fear_hunger_v0.43.md]],
[[docs/experiments/fear_hunger_v0.43R.md]].

## Question

v0.43R's halt established the corrected substrate finding: under the
V0_25 anchor (`tight_gradient` + `GradientPolicy` +
`auto_reproduction=True` + `TraitConfig(unbounded_mutation=True)` +
`food_respawn_cooldown=50` + `energy_pool_initial=1500` +
`ambient_influx_rate=1.0`), the 24-cell food zone is **completely
depleted** at tick 50 across all probed seeds (49..56) at both h=0
and h=8. **The causal lever at tick 50 is not `food_value` (already
zero); it is `world.respawn_at_tick`** — which lineage is positioned
to claim the next refill.

The active question for v0.44 is:

> **Is the post-50 respawn FLOW (the timing density of refills
> arriving at scheduled cells over the post-50 window) NECESSARY for
> the post-50 dominance pattern? If we delay every scheduled cell's
> refill by +25 ticks at the tick-50/tick-51 boundary, does post-50
> dominance fail to reconstitute? If we permute the schedule across
> cells (preserving the multiset of refill ticks but shuffling
> cell-to-tick assignments), does dominance reconstitute regardless?**

This is a **flow-rate necessity probe** at the same anchor moment
v0.42 / v0.43R used. The substrate's only operative causal lever
at tick 50 (food values are zero) is the per-cell refill schedule.

The placebo control for v0.44 is a **flow-preserving permutation**:
a deterministic (x, y)-sorted reverse-row-major rebinding of refill
ticks across the same scheduled cells. The multiset of refill ticks
is exactly preserved (so the system-wide flow rate is preserved);
only the spatial-temporal assignment (which cell refills WHEN) is
perturbed. This distinguishes "flow rate matters" (B disrupts; C
does not) from "any schedule rewrite disrupts" (B and C disrupt
comparably) — parallel in cadence to v0.42's leader vs size-matched
control and v0.43R's reduce vs density-preserving control.

If post-50 dominance collapses under the +25-tick delay but not under
the schedule permutation, **respawn flow at tick 50 is necessary**
for the v0.34..v0.41 pattern. If both interventions disrupt
comparably, the system is sensitive to **any schedule rewrite**, not
specifically to flow reduction. If neither disrupts, the causal
source lies further upstream than the respawn-schedule layer (founder-
trait + spatial-position interaction at the depleted moment, hazard
topology, chamber geometry).

## What this slice tests, and what it does NOT test

### Tests

- Whether **`post_intervention_top_lineage_b50_share`** (the same
  primary observable as v0.42 / v0.43R; reused unchanged) in the
  delay arm B drops by ≥ 0.15 relative to the null arm A at h=8,
  AND the schedule-permutation arm C remains within ±0.10 of arm A
  at h=8. **This is the primary respawn-flow-necessity test.**
- Whether the B-vs-A reduction is larger at h=8 than at h=0
  (secondary observable; tests hazard-amplification specificity of
  the respawn-flow-necessity effect).
- Whether the intervention's `RespawnScheduleByIntervention` summary
  events are emitted exactly once per intervention-firing run, with
  the correct `intervention_kind`, `n_eligible_cells`,
  `n_cells_changed`, schedule extrema, and digest fields.
- Whether B preserves
  (`respawn_multiset_after = respawn_multiset_before + 25`
  elementwise on the sorted schedule) and C preserves
  (`sorted(respawn_multiset_after) == sorted(respawn_multiset_before)`)
  the expected schedule invariants.
- Whether the **default-None and `kind="null"` paths** continue to
  be byte-identical to pre-v0.42 / v0.42 / v0.43R behaviour.
- Whether the auxiliary finding **DELAY_ABLATES_REPRODUCTION** fires
  per-hazard: B produced > 2 of 8 runs with zero post-50
  surviving-lineage births at any hazard (parallel to v0.43R's
  DENSITY_REDUCTION_ABLATES_REPRODUCTION, but for the +25-tick
  delay variant).

### Does NOT test

- **Mechanism sufficiency.** Necessity only.
- **Mechanism specificity.** v0.44 cannot distinguish flow-rate-as-
  arrival-density from flow-rate-as-energy-availability from
  flow-rate-as-foraging-cycle-length. Refinement interventions
  reserved for v0.45+.
- **Hazard generalisation.** Only h=0 and h=8 are tested.
- **Cross-stream calibration of the intervention.** Seeds 57..64
  only; v0.45+ candidate.
- **The v0.34..v0.43R corpus.** v0.43R's halt addendum stands as
  the historical record. v0.44 does NOT re-run any prior reducer
  or the disqualified v0.43R sweep.
- **Food-value substrate.** v0.43R's verdict is disqualified, so
  food-density necessity remains untested. v0.44 operates on a
  different substrate layer (refill schedule). A future slice on a
  non-depleted-substrate chamber could revisit food density.
- **Hazard topology disruption.** HAZARD-cell positions and counts
  are unchanged. Reserved for v0.45+ candidate.
- **Chamber-geometry interventions.** Walls inviolate; food zone
  topology preserved.
- **Delay magnitudes other than +25 ticks.** Dose-response (e.g.,
  +50 or +100) is reserved for v0.45+ if v0.44 lands borderline.
- **Permutations other than reverse-row-major.** A single locked
  permutation is used; alternative permutations reserved for
  v0.45+ if the verdict is borderline.
- **Magnitude framing as "spread" or "amplification".** v0.44's
  primary uses absolute-share differences at h=8 (same convention
  as v0.42 / v0.43R).

### Deferred (v0.45+ candidates, conditional on v0.44 outcome)

- **If RESPAWN_FLOW_NECESSARY fires** (B drops; C does not). v0.45
  candidates: (a) hazard-grid expansion; (b) dose-response sweep
  (delays +12 / +25 / +50 / +100); (c) cross-stream calibration on
  seed band 65..72; (d) sufficiency probe (accelerate the schedule
  on a freshly-delayed substrate via subtraction).
- **If SUBSTRATE_PERTURBATION_DISRUPTS fires** (B and C both
  disrupt). v0.45 candidate: refine the permutation magnitude.
  Reverse-row-major is the maximum-displacement permutation over
  an (x, y)-sorted index; a smaller-displacement permutation
  (e.g., adjacent-pair swap) would test whether dominance is
  fragile to any schedule rewrite or only to large rewrites.
- **If RESPAWN_FLOW_NOT_NECESSARY fires** (B does not disrupt).
  v0.45 candidate: pivot to non-substrate causal levers. The
  food-substrate's value layer is established as zero at the
  anchor; the respawn-schedule layer is established as
  non-causal. Remaining substrate-anchored candidates: hazard
  topology (h), founder-trait + spatial-position interaction at
  tick 50, birth-position constraints. Food-substrate causal
  levers at the V0_25 anchor are exhausted.
- **If DELAY_ABLATES_REPRODUCTION fires per-hazard** (auxiliary).
  v0.45 candidate: smaller delay magnitude (+12) to separate
  "delay matters for dominance" from "delay matters for
  reproduction at all".

### Quarantined (not v0.44 inputs)

- v0.34..v0.43R reducer outputs. v0.44 reads only its own sweep
  events (parallel to v0.42 / v0.43R design discipline).
- HedonismPolicy. Mesa migration. v0.36 founder traits. Cross-
  stream calibration.
- The disqualified v0.43R sweep. v0.43R's `runs/` artefacts are
  not v0.44 inputs.
- The halted v0.43 design (no v0.43 sweep was executed).

## Conservation framing — additive over v0.42 / v0.43R substrate primitives

v0.44 extends the already-landed intervention infrastructure with
**two new `kind` values**, **two new helper functions**, and **one
new event class**. The primitives that v0.42 / v0.43 / v0.43R
contributed (and v0.44 reuses unchanged):

- The chamber-runner `optional_intervention` hook (unchanged from
  v0.42).
- v0.42's leader-kill / size-matched-kill paths.
- v0.43's flatten / shuffle paths.
- v0.43R's reduce-density / density-preserving-perturbation paths
  (and the `FoodRedistributedByIntervention` event class).
- The `_eligible_cells` helper and digest helpers in
  `core/interventions.py`.

Modifications under v0.44:

- **Modified module:** `src/hedonism_harness/core/interventions.py`
  - Two new `kind` literal values:
    `"delay_respawn_schedule_plus_25_at_tick50"`,
    `"permute_respawn_schedule_reverse_row_major_at_tick50"`.
  - Two new rewrite functions:
    `_delay_respawn_schedule_over_eligible_cells`,
    `_permute_respawn_schedule_over_eligible_cells`.
  - One new helper:
    `_eligible_respawn_cells` (predicate: `kind ∈ {EMPTY, FOOD} AND
    respawn_at_tick > 0`).
  - One new helper: `_respawn_multiset_digest` (SHA-256 over
    `struct.pack`-ed int32 sorted-ascending `respawn_at_tick` values
    over the eligible-cell set).
  - Extended `apply_intervention` dispatcher with a new branch
    `_apply_respawn_schedule_rewrite` routing the new kinds (parallel
    to `_apply_food_redistribution`).
  - Existing `null` / `kill_*` / `flatten_*` / `shuffle_*` / `reduce_*` /
    `density_preserving_*` paths remain byte-identical.
- **Modified module:** `src/hedonism_harness/core/events.py`
  - One new event class: `RespawnScheduleByIntervention` (frozen
    dataclass; field list locked below). Added to `_SIGNAL_NAMES`
    and `AnyEvent` union.
  - **Existing `FoodRedistributedByIntervention` event class is
    NOT reused** — semantically distinct content (refill schedule
    vs. food values; int32 ticks vs. float32 values), per user
    sign-off.
- **`comparison_grid.py`**: one new constant
  `V0_44_INTERVENTION_ARMS` (additive only; existing arms tuples
  unchanged, including v0.43R's `V0_43R_INTERVENTION_ARMS`).

The following are NOT modified:

- Existing chamber, policy, or population-dynamics behaviour
  outside the new intervention `kind` paths. Default-None and
  `kind="null"` remain byte-identical to pre-v0.42.
- All v0.34..v0.43R reducer scripts and audits.
- The halted v0.43 / disqualified v0.43R pre-regs (preserved as
  historical records).
- Pre-v0.44 events on disk. Re-running prior sweeps with default
  `optional_intervention=None` produces byte-identical events.jsonl
  files.
- v0.42's kill paths, v0.43's flatten/shuffle paths, v0.43R's
  density paths — byte-identical when re-run on v0.44 branch
  (regression test H2e).

## Mechanism

v0.44 ships:

1. Two new intervention kinds in
   `src/hedonism_harness/core/interventions.py`.
2. One new event class in `src/hedonism_harness/core/events.py`.
3. A new sweep driver and arm tuple.
4. A v0.44 audit reducer that consumes the v0.44 sweep events.
5. Paired test files for each addition.
6. This pre-reg.
7. A new manifest doc post-Results.

### 1. Intervention extensions (`src/hedonism_harness/core/interventions.py`)

The existing `InterventionConfig.kind` Literal is extended to:

```python
kind: Literal[
    "null",
    "kill_tick50_leader",
    "kill_size_matched_nonleader",
    "flatten_food_at_tick50",
    "shuffle_food_at_tick50",
    "reduce_food_density_50pct_at_tick50",
    "density_preserving_perturbation_at_tick50",
    "delay_respawn_schedule_plus_25_at_tick50",                # NEW v0.44
    "permute_respawn_schedule_reverse_row_major_at_tick50",    # NEW v0.44
]
```

New eligibility predicate:

```python
def _eligible_respawn_cells(world) -> list[tuple[int, int]]:
    """Return (x, y)-sorted ascending list of cells where:
        kind in {EMPTY, FOOD} AND respawn_at_tick > 0.
    HAZARD/WALL/SAFE cells excluded. respawn_at_tick == 0 means
    'not currently scheduled' (no pending refill); excluded.
    """
```

Two new pure-function helpers:

```python
def _delay_respawn_schedule_over_eligible_cells(world, delay=25) -> ...:
    """B arm. Compute eligible_respawn_cells. For every eligible
    cell:
        respawn_at_tick <- respawn_at_tick + delay
    All other state (kind, food_value, hazard, wall, safe)
    unchanged. Schedule multiset shifts by exactly +delay
    elementwise."""

def _permute_respawn_schedule_over_eligible_cells(world) -> ...:
    """C arm. Compute eligible_respawn_cells (sorted (x, y)
    ascending). Compute reverse-row-major reassignment:
        cells[i].respawn_at_tick <- old_values[n - 1 - i]
    where old_values is the original `respawn_at_tick` list in
    cell-sorted order. Multiset of refill ticks exactly preserved;
    cell-to-tick assignment maximally displaced under the locked
    sort order. All other state unchanged."""
```

Selection rules:

- **`delay_respawn_schedule_plus_25_at_tick50` (B arm)**: at the
  tick-50/tick-51 boundary, add +25 to every eligible cell's
  `respawn_at_tick` value. Per-cell schedule extension uniform.
- **`permute_respawn_schedule_reverse_row_major_at_tick50` (C arm)**:
  at the same boundary, reassign refill ticks across the
  `(x, y)`-sorted eligible-cell list using a reverse-row-major
  index mapping. Multiset of refill ticks exactly preserved →
  system-wide post-50 flow rate exactly preserved.

Determinism contract:

- Both new kinds are pure functions of tick-50 chamber state. No
  new RNG. No `model.streams` draws.
- For a given (seed, hazard, intervention_kind), the intervention
  produces the same post-state every time.
- The +25 delay magnitude is locked. The reverse-row-major
  permutation is locked over `(x, y)` ascending sort.

### Why +25 ticks for B?

The +25 delay is **timing-matched to the post-50 observation
window**:

- Post-50 window is 50 ticks (ticks 51..100 are the v0.34..v0.41
  observation horizon for the primary observable).
- Probe data shows refill ticks at tick 50 are distributed in the
  range 54..67 (median ~60). With food_respawn_cooldown=50 and
  ambient_influx_rate=1.0, the natural cadence after a fresh refill
  is ~50 ticks per cell.
- A +25 delay shifts the **first post-50 refill wave** from the
  early post-50 window (roughly ticks 54..67) into the **late
  post-50 window** (roughly ticks 79..92). This reduces early
  post-50 food availability while preserving a conservative,
  non-ablative intervention magnitude. It may also suppress or
  delay second-cycle refills that would otherwise occur within the
  100-tick observation horizon.
- The intervention is NOT claimed to halve total post-50 refill
  count over the full window; the audit does not measure first-
  half-window flow as a separate observable. The treatment is a
  **timing shift of the first refill wave**, not a flow-rate
  reduction over the full window.

The +25 magnitude is conservative relative to +50 (which would push
the first wave past or near the observation horizon end, risking
reproduction ablation and likely firing the auxiliary at both
hazards) and to +100 (which is far past any natural cadence in the
system).

### Why reverse-row-major for C?

Reverse-row-major over `(x, y)`-sorted cells is the **maximum
index-displacement deterministic permutation under the locked
sort order**:

- Sort cells by `(x, y)` ascending (row-major in the chamber's
  coordinate convention).
- Reverse-pair: cell[0] receives cell[n-1]'s tick; cell[n-1]
  receives cell[0]'s tick; etc.
- For n=24 scheduled cells (probe-indicated; preflight-pending for
  seeds 57..64), this maps each cell's refill tick to the tick of
  the cell at the opposite end of the (x, y)-sorted index.

Properties:

- **Multiset-preserving**: `sorted(after) == sorted(before)`
  exactly (it's a permutation).
- **Maximum index-displacement under the locked sort order**:
  for any cell at sort-index i, the new index is n-1-i; mean
  index-displacement is n/2 (12 positions for n=24). This is
  **not** claimed to be the unique maximum spatial-displacement
  permutation in chamber geometry — alternative sort orders
  (e.g., by hazard-distance, by founder-position) would yield
  different displacement profiles.
- **Deterministic**: no RNG.
- **Self-inverse**: applying twice restores the original.

This makes C a strong schedule-permutation control under a single
locked deterministic rule: if dominance reconstitutes under
maximum index-order cell-to-tick displacement, the spatial pattern
of WHICH cells refill WHEN (along the locked sort order) is not
necessary for the post-50 dominance pattern; if dominance disrupts
under C comparably to B, the system is sensitive to schedule
rewrite generally rather than to flow-rate reduction specifically.
Alternative-permutation refinement (e.g., adjacent-pair swap,
hazard-distance-weighted permutation) is reserved for v0.45+.

### 2. Event class (`core/events.py`) — NEW

```python
@dataclass(frozen=True, slots=True)
class RespawnScheduleByIntervention:
    """Emitted once per intervention firing on a respawn-schedule
    rewrite kind. Distinct from FoodRedistributedByIntervention
    because the rewritten layer is int32 schedule ticks, not
    float32 food values."""
    intervention_kind: str
    intervention_tick: int
    effective_tick: int
    n_eligible_cells: int
    n_cells_changed: int
    min_respawn_tick_before: int
    max_respawn_tick_before: int
    min_respawn_tick_after: int
    max_respawn_tick_after: int
    sum_respawn_tick_before: int
    sum_respawn_tick_after: int
    eligible_cells_digest: str           # SHA-256 over struct.pack
                                          # of (x, y) int32 pairs sorted ascending
    respawn_multiset_digest_before: str  # SHA-256 over struct.pack of
                                          # int32 respawn_at_tick values, sorted asc
    respawn_multiset_digest_after: str
```

Added to `_SIGNAL_NAMES` and the `AnyEvent` union. Wire-format
(JSONL) parallel to `FoodRedistributedByIntervention`.

`fired` semantics carry forward from v0.43 / v0.43R: firing is
event-emission, independent of `n_cells_changed` (B always changes
all eligible cells; C changes all eligible cells unless the
substrate is in a degenerate self-inverse configuration, which the
probe-confirmed 24-cell schedule with heterogeneous ticks is not).

### 3. Sweep + arm tuple (`scripts/v0.44_sweep.py`, `comparison_grid.py` additions)

Three arms × 2 hazards × 8 seeds = **48 runs**. Arm tuple:

```python
V0_44_INTERVENTION_ARMS: tuple[Arm, ...] = (
    # A_null (no intervention; baseline)
    _v0_44_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    _v0_44_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    # B_delay_respawn_schedule_plus_25 (treatment: +25-tick delay)
    _v0_44_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="B_delay_respawn_schedule_plus_25",
               intervention_kind="delay_respawn_schedule_plus_25_at_tick50"),
    _v0_44_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="B_delay_respawn_schedule_plus_25",
               intervention_kind="delay_respawn_schedule_plus_25_at_tick50"),
    # C_permute_respawn_schedule_reverse_row_major (multiset-preserving placebo)
    _v0_44_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="C_permute_respawn_schedule_reverse_row_major",
               intervention_kind="permute_respawn_schedule_reverse_row_major_at_tick50"),
    _v0_44_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="C_permute_respawn_schedule_reverse_row_major",
               intervention_kind="permute_respawn_schedule_reverse_row_major_at_tick50"),
)
```

Arm labels prefixed `v044-` to disambiguate from v0.42 / v0.43 /
v0.43R arms. Output directory: `runs/fear-hunger-v0.44-tight_gradient/`.

Seeds: **57..64** (next disjoint band beyond v0.43R's 49..56;
disjoint from all prior streams 1..8, 9..16, 17..24, 25..32,
33..40, 41..48, 49..56). Substrate parameters inherited from V0_25
substrate via `dataclasses.replace`, identical to v0.43R's wiring.

### 4. v0.44 audit (`scripts/v0_44_intervention_audit.py`)

Imports only `LineageReplayError` via `importlib.util`. Pure stdlib
otherwise.

Reads:

- Per-arm `comparison.csv` from
  `runs/fear-hunger-v0.44-tight_gradient/arms/`.
- Per-run `events.jsonl` (specifically:
  `RespawnScheduleByIntervention` events + post-50 `AgentBorn`
  events for the primary observable).

Halt invariants (5):

- **H2a (run count):** exactly 6 arms × 8 seeds = 48 runs on disk.
- **H2b (intervention-fire count per arm):**
  - A_null arms: 0 events per run.
  - B_delay arms: exactly 1 `RespawnScheduleByIntervention` event
    per run with `intervention_kind="delay_respawn_schedule_plus_25_at_tick50"`.
  - C_permute arms: exactly 1 `RespawnScheduleByIntervention` event
    per run with
    `intervention_kind="permute_respawn_schedule_reverse_row_major_at_tick50"`.
- **H2c (effective_tick):** every fired event has
  `effective_tick=51`.
- **H2d (schedule conservation):**
  - For B (delay): on every fired event,
    `sum_respawn_tick_after == sum_respawn_tick_before + 25 *
    n_eligible_cells`,
    `min_after == min_before + 25`,
    `max_after == max_before + 25`.
    Schedule multiset digest must change (digest_before !=
    digest_after) on any run with `n_eligible_cells > 0`.
  - For C (permute):
    `sum_after == sum_before` exactly,
    `min_after == min_before`, `max_after == max_before`,
    AND `respawn_multiset_digest_after == respawn_multiset_digest_before`
    (the digest is over the sorted multiset, so a permutation must
    preserve it). Halt on digest inequality (indicates an
    arithmetic bug; the permutation must preserve the multiset).
  - For both: `eligible_cells_digest` is consistent across all
    fired events (chamber geometry + which cells are scheduled at
    tick 50 are seed-independent? — see H2d-aux below). Halt on
    drift within an (arm, seed) bucket; cross-seed variation is
    EXPECTED if scheduled-cell membership varies by seed (probe
    showed all 24 cells scheduled at all probed (seed, hazard)
    buckets, so cross-seed digest equality is the locked
    expectation).
  - **H2d-aux (eligible-cell-set stability across seeds):** the
    seeds-49..56 probe indicated that all 24 cells in the food
    zone satisfy `kind ∈ {EMPTY, FOOD} AND respawn_at_tick > 0`
    at tick 50 at both hazards. v0.44 does NOT inherit this lock
    cross-seed; the value is committed only after the required
    v0.44 preflight on seeds 57..64 (under the exact
    `_run_one_arm_seed` sweep path) confirms it. If the preflight
    deviates, halt pre-sweep and amend the pre-reg with the
    observed eligibility before locking. After preflight, every
    fired event must report `n_eligible_cells == EXPECTED_N_ELIGIBLE_CELLS`
    or halt.
  - For both: `n_cells_changed <= n_eligible_cells`.
- **H2e (regression byte-identity):** sampled v0.42 A_null seed
  AND v0.42 B_kill_leader seed re-run with v0.44 code produce
  events.jsonl byte-identical to v0.42's sealed references. Same
  regression as v0.43 / v0.43R; preserved through v0.44 because
  no pre-v0.44 path is modified.
- **C-rises-above-A halt:** if `c_share_h8 > a_share_h8 + 0.10`,
  halt loud (substrate artefact unmodeled).

Computes per-(arm, seed):

- `post_intervention_top_lineage_b50_share` (identical formula to
  v0.42 / v0.43R; no lineage exclusion since no lineage is killed).
- `total_post_50_births`, `top_lineage_id`, `top_lineage_post50_births`.
- Event fields: `intervention_kind`, `n_eligible_cells`,
  `n_cells_changed`, `sum_respawn_tick_before`,
  `sum_respawn_tick_after`, schedule extrema, digests.
- `excluded_zero_post50` (True if `total_post_50_births == 0`).

Aggregates per-(arm, hazard) and computes the locked decision rule.

Outputs eight CSVs under `runs/lineage-v0.44/`:

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
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(57, 65))  # 57..64
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_N_TICKS: int = 200
EXPECTED_INTERVENTION_TICK: int = 50
EXPECTED_EFFECTIVE_TICK: int = 51
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds
EXPECTED_N_ELIGIBLE_CELLS: int = 24  # PREFLIGHT-PENDING: locked
                                     # only after the required v0.44
                                     # preflight on seeds 57..64
                                     # confirms it under the exact
                                     # _run_one_arm_seed sweep path.
                                     # If preflight deviates, halt
                                     # before sweep and amend the
                                     # pre-reg.

# Locked thresholds (parallel to v0.42 / v0.43R)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Auxiliary threshold (parallel to v0.43R's DENSITY_REDUCTION_ABLATION_MAX_EXCLUDED)
AUXILIARY_DELAY_ABLATION_MAX_EXCLUDED: int = 2

# B-arm delay magnitude (locked)
B_DELAY_TICKS: int = 25

# Arm labels
ARM_A_NULL: str = "v044-A_null"
ARM_B_DELAY: str = "v044-B_delay_respawn_schedule_plus_25"
ARM_C_PERMUTE: str = "v044-C_permute_respawn_schedule_reverse_row_major"

# Intervention kind labels (extends v0.43R)
KIND_NULL: str = "null"
KIND_DELAY_RESPAWN_PLUS_25: str = "delay_respawn_schedule_plus_25_at_tick50"
KIND_PERMUTE_RESPAWN_REVERSE_ROW_MAJOR: str = (
    "permute_respawn_schedule_reverse_row_major_at_tick50"
)
```

### Determinism — anchors

- v0.21..v0.43R events.jsonl + sidecar artifacts not re-read by
  the primary v0.44 audit. H2e regression check reads selected
  v0.42 references for fingerprint comparison only.
- All v0.34..v0.43R test suites continue to pass (additive guard).
- Default `optional_intervention=None` is byte-identical to
  pre-v0.42 behaviour.
- `kind="null"` byte-identical to default-None.
- v0.42's kill paths byte-identical when re-run on v0.44 branch.
- v0.43's flatten/shuffle paths byte-identical when re-run on
  v0.44 branch.
- v0.43R's reduce/perturbation paths byte-identical when re-run
  on v0.44 branch.
- Re-running v0.44 sweep with the same seeds produces byte-
  identical events.jsonl files.

### Wall-time estimate

- v0.44 sweep: ~13s (48 runs at locked parameters; comparable to
  v0.42 / v0.43R).
- v0.44 audit: ~3s.
- Total v0.44 incremental wall-time: ~16s.

## Observables — pre-committed before reading the data

### Per-run — 48 rows total

- `arm` ∈ {A_null, B_delay_respawn_schedule_plus_25, C_permute_respawn_schedule_reverse_row_major}.
- `hazard` ∈ {0, 8}.
- `seed` ∈ {57..64}.
- `fired`: bool. True iff a `RespawnScheduleByIntervention` event
  was emitted. False for A_null. Firing is event-emission,
  independent of `n_cells_changed`.
- `intervention_kind`: str.
- `n_eligible_cells`, `n_cells_changed`: int.
- `sum_respawn_tick_before`, `sum_respawn_tick_after`: int.
- `min_respawn_tick_before`, `max_respawn_tick_before`: int.
- `min_respawn_tick_after`, `max_respawn_tick_after`: int.
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
- `respawn_flow_necessary := b_passes AND c_passes`.
- `substrate_perturbation_disrupts := b_passes AND c_below_a`.
- `respawn_flow_not_necessary := NOT b_passes`.
- `c_above_a_unmodeled_substrate_artefact := b_passes AND c_above_a`
  (halt cell — no scientific verdict emitted).
- `primary_fires := respawn_flow_necessary OR
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
- `ablation_threshold_exceeded := b_n_excluded > AUXILIARY_DELAY_ABLATION_MAX_EXCLUDED`.
- `auxiliary_phrase_fires`: bool.

Auxiliary finding is **non-exclusive** of the primary verdict.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive `src/` modification).** Only the new intervention
  kinds + the new event class + the new arm constant + the helper
  functions. All pre-v0.44 kind paths are byte-identical. Includes
  regression tests on a sampled v0.42 A_null seed AND a sampled
  v0.42 B_kill_leader seed.
- **H2a (run count).** Exactly 48 runs on disk after v0.44 sweep.
- **H2b (intervention-fire count per arm).** A_null: 0; B: 1; C: 1.
- **H2c (effective_tick).** Every fired event has
  `effective_tick=51`.
- **H2d (schedule conservation).**
  - For B: `sum_after == sum_before + 25 * n_eligible_cells`;
    `min/max_after == min/max_before + 25`; multiset digest shifts.
  - For C: `sum_after == sum_before`; `min/max_after ==
    min/max_before`; multiset digest is **equal** before and
    after (permutation preserves the sorted multiset).
  - HAZARD/WALL/SAFE positions and counts unchanged.
  - Food-value layer unchanged (this slice does NOT touch
    `food_value`).
- **H2d-aux (eligible-cell-set stability).** All fired events
  emit `n_eligible_cells == 24` across seeds 57..64 at both
  hazards.
- **H2e (regression byte-identity).** v0.42 A_null + B_kill_leader
  reference seeds re-run with v0.44 code produce events.jsonl
  byte-identical to v0.42's sealed references.
- **H3 (additive guard).** v0.21..v0.43R + v0.43-skipped tests
  still pass after v0.44 additions.
- **H4 (no mutation of pre-v0.44 surface).** All pre-v0.44
  scripts, reducers, audits, arm tuples, chamber/policy/population
  modules — byte-identical (modulo additive kinds + event class +
  arm constant + helper functions).

### Cautious form — three-way verdict on v0.44's respawn-flow-necessity question

The verdict is intentionally three-way, mutually exclusive on the
locked decision space, plus one halt cell:

**RESPAWN_FLOW_NECESSARY.** **FIRES iff** `b_passes == True` AND
`c_passes == True`. Headline: delaying the respawn schedule by +25
ticks at the tick-50/tick-51 boundary materially disrupts post-50
dominance, while permuting the schedule across cells (preserving
the multiset of refill ticks) does not. Respawn flow at tick 50 is
**necessary** for the v0.34..v0.41 dominance pattern under the
tested substrate; the specific *cell-to-tick assignment* of refills
is not.

**SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE.** **FIRES iff**
`b_passes == True` AND `c_below_a == True`. Headline: both the
+25-tick delay and the schedule permutation disrupt post-50
dominance. The pattern is sensitive to **any respawn-schedule
rewrite of comparable scope**, not specifically to flow-rate
reduction. v0.34..v0.41's correlational pattern reflects fragility
to schedule-shock rather than a flow-rate-specific causal
mechanism.

**RESPAWN_FLOW_NOT_NECESSARY.** **FIRES iff** `b_passes == False`.
Headline: delaying respawn flow by +25 ticks does not materially
disrupt post-50 dominance; the pattern reconstitutes through a
surviving lineage even with post-50 refill rate halved over the
observation window. Respawn flow at tick 50 is **not necessary**
for the pattern; the causal source lives outside the respawn-
schedule layer (founder-trait + spatial-position interaction at
the depleted moment, hazard topology, chamber geometry, birth-
position constraints).

**C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt cell):** `b_passes
== True` AND `c_above_a == True`. Substrate artefact unmodeled at
pre-reg time. Audit halts loud (`LineageReplayError`); no
scientific verdict emitted.

(All four cells exhaust the rule space:
- `b_passes=True, c_passes=True` → RESPAWN_FLOW_NECESSARY.
- `b_passes=True, c_below_a=True` → SUBSTRATE_PERTURBATION_DISRUPTS.
- `b_passes=True, c_above_a=True` → C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt).
- `b_passes=False, *` → RESPAWN_FLOW_NOT_NECESSARY.)

### Auxiliary finding — independent of primary verdict

**DELAY_ABLATES_REPRODUCTION (per-hazard).** **FIRES iff**
`b_n_excluded_zero_post50 > 2` at any hazard. Reported alongside
the primary verdict; does NOT alter the verdict logic. Headline:
the +25-tick delay pushed refill timing past the threshold required
to sustain post-50 reproduction in this fraction of seeds at this
hazard. **Descriptive substrate finding**: schedule-as-timing can
ablate reproduction at sufficient delay.

### Locked phrases for each verdict

> **RESPAWN_FLOW_NECESSARY phrase:** "Delaying the respawn schedule
> by +25 ticks at the tick-50/tick-51 boundary materially disrupts
> the post-50 dominance pattern at h=8: when every scheduled cell's
> refill is pushed back by half the observation window, the
> surviving lineages do not reconstitute concentration of comparable
> share. The schedule-permutation control (which reassigns refill
> ticks across the (x, y)-sorted scheduled cells via reverse-row-
> major mapping, exactly preserving the multiset of refill ticks
> and the system-wide post-50 flow rate) does NOT produce
> comparable disruption. Under the tested substrate, **respawn
> flow at tick 50 is necessary** for the v0.34..v0.41 dominance
> pattern; the specific *cell-to-tick assignment* of refills
> across the food zone is not. v0.44 does not declare which
> property of respawn flow carries the effect (arrival-density-
> per-window, energy-flux-rate, foraging-cycle-length); refinement
> interventions in v0.45+ are required. Necessity is established
> at one hazard level (h=8) on one seed band (57..64) under one
> delay magnitude (+25); cross-stream calibration and dose-
> response sweeps are reserved for v0.45+. Sufficiency is NOT
> tested."

> **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE phrase:** "Delaying
> respawn flow by +25 ticks disrupts post-50 dominance at h=8,
> but the multiset-preserving schedule-permutation control
> produces comparable disruption. The post-50 dominance pattern
> is sensitive to **any respawn-schedule rewrite of comparable
> scope**, not specifically to flow-rate reduction. v0.34..v0.41's
> correlational pattern reflects fragility to schedule-shock
> rather than a flow-rate-specific causal mechanism. v0.45
> candidate: reduce the C-arm permutation magnitude (e.g.,
> adjacent-pair swap rather than reverse-row-major) to test
> whether the pattern is fragile to any schedule rewrite or only
> to large-displacement rewrites. Mechanism remains unidentified
> at the respawn-schedule level."

> **RESPAWN_FLOW_NOT_NECESSARY phrase:** "Delaying the respawn
> schedule by +25 ticks at the tick-50/tick-51 boundary does not
> materially disrupt the post-50 dominance pattern at h=8. A
> surviving lineage reconstitutes concentration-of-share even when
> the post-50 refill window is shifted by half its width. **Respawn
> flow at tick 50 is not necessary** for post-50 dominance under
> the tested substrate; the causal source lives outside the
> respawn-schedule layer at the anchor moment. v0.42 ruled out
> the tick-50 leader's identity; v0.43R's food-density probe was
> disqualified (substrate depleted); v0.44 rules out tick-50
> respawn flow. Remaining substrate-anchored candidates: founder-
> trait + spatial-position interaction at the depleted moment,
> hazard topology, chamber geometry (wall-adjacency, reachability),
> and birth-position constraints. v0.45 candidate: founder-trait
> lock-in or hazard-relocation intervention."

> **DELAY_ABLATES_REPRODUCTION (auxiliary, per-hazard) phrase:**
> "At hazard h=N, the B_delay_respawn_schedule_plus_25 arm produced
> > 2 of 8 runs with zero post-50 births: the +25-tick delay shifted
> refill timing past the threshold required to sustain post-50
> reproduction itself rather than relocating dominance. This is a
> **descriptive substrate finding** parallel to but independent of
> the share-based primary verdict: the delayed refill window fell
> below the threshold required to sustain post-50 reproduction in
> this fraction of seeds at this hazard. The primary verdict is
> computed over n_used (non-excluded) runs; this auxiliary finding
> is reported alongside but does NOT alter the primary verdict
> logic. v0.45 candidate: use a milder delay magnitude (+12) to
> separate delay-matters-for-dominance from delay-matters-for-
> reproduction-at-all."

### Caveats — locked, must appear in Results

- **Per-arm n is 8.** Conservative on n=8; not bullet-proof
  against noise excursions.
- **Necessity only.** Sufficiency not tested.
- **One seed band.** Seeds 57..64 only.
- **Two hazards only.** {0, 8}.
- **Single locked delay magnitude.** +25 ticks only. Dose-response
  reserved for v0.45+.
- **Single locked permutation.** Reverse-row-major over `(x, y)`-
  sorted scheduled cells. Other permutations reserved for v0.45+.
- **Hazard topology preserved.** HAZARD-cell positions and counts
  unchanged.
- **Walls inviolate.** WALL cells never modified.
- **Food-value layer untouched.** v0.44 operates on `respawn_at_tick`
  only; `food_value` is not modified by either intervention.
- **No biological-realism claim.** Both B (+25 delay) and C
  (deterministic permutation) are abstract substrate rewrites at
  the boundary.
- **Substrate state at h=8 anchor moment is depleted on
  food_value.** v0.43R's corrected substrate finding stands: at
  tick 50 on `tight_gradient` + h=8, food_value is zero across the
  24-cell food zone; respawn_at_tick is heterogeneous in [54, 67]
  (probe data, seeds 49..56). v0.44's B shifts these to [79, 92];
  C reassigns within [54, 67] across the 24 cells.
- **No mechanism declaration even on the strongest outcome.** Even
  on RESPAWN_FLOW_NECESSARY, v0.44 only establishes that flow is
  necessary at one hazard, on one seed band, under one delay
  magnitude. Mechanism specificity (which property of flow)
  requires v0.45+.
- **Effect-size budget.** Same threshold (0.15) and tolerance
  (0.10) as v0.42 / v0.43R. Cross-version comparability
  intentional.

### Reachability — sanity check

All three primary verdicts plus the halt cell are arithmetically
reachable:

- **RESPAWN_FLOW_NECESSARY**: requires B share to drop by ≥ 0.15
  AND C share to stay within ±0.10 of A. Both bars independent
  and live; flow-as-rate as cause would land here.
- **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE**: requires B AND C
  to both drop by ≥ 0.10 from A. If the system is fragile to any
  schedule rewrite of n=24-cell scope, this is where it lands.
- **RESPAWN_FLOW_NOT_NECESSARY**: requires B share to NOT drop by
  ≥ 0.15. If post-50 dominance reconstitutes regardless of refill
  timing, this is where it lands.
- **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt)**: requires C
  share to rise above A by > 0.10 while B drops. Mechanistically
  unmotivated; halt loud.

### Anchor identity

- v0.44 inherits no cross-version artifact-identity anchors against
  prior reducer outputs. It inherits two byte-identity anchors:
  v0.42 A_null + B_kill_leader fingerprints (regression guard, H2e).

## Decision rules

### Primary

| `b_passes` | C-direction             | verdict                                              |
|:----------:|-------------------------|------------------------------------------------------|
| True       | `c_passes` (\|c−a\|≤0.10) | **RESPAWN_FLOW_NECESSARY**                           |
| True       | `c_below_a` (c−a≤−0.10) | **SUBSTRATE_PERTURBATION_DISRUPTS_DOMINANCE**        |
| True       | `c_above_a` (c−a>+0.10) | **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT** (halt)    |
| False      | any                     | **RESPAWN_FLOW_NOT_NECESSARY**                       |

### Auxiliary (independent of primary)

`DELAY_ABLATES_REPRODUCTION` per hazard, fires iff
`b_n_excluded_zero_post50 > 2` at that hazard.

### Secondary (descriptive context only)

`hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.

### Halt conditions

- **H1 fails** — pre-v0.44 surface mutated, OR v0.42 byte-
  identity regression fails. Halt; revert.
- **H2a fails** — run count != 48. Halt.
- **H2b fails** — intervention fires per arm violate locked counts.
  Halt.
- **H2c fails** — `effective_tick` != 51 on any fired event. Halt.
- **H2d fails** — schedule conservation violated (B-arithmetic,
  C-permutation invariance, or cross-arm geometry). Halt.
- **H2d-aux fails** — `n_eligible_cells != 24` on any fired event.
  Halt loud; the locked predicate / probe expectation is violated.
- **H2e fails** — sampled byte-identity regression fails. Halt.
- **H3 / H4 fail** — pre-v0.44 contract broken. Halt; revert.
- **C-rises-above-A cell** — substrate artefact unmodeled. Halt
  loud; do NOT silently bin into a verdict.
- **Substrate-preflight halt** — if a v0.44 feasibility re-probe
  through `_run_one_arm_seed` shows fewer than 24 scheduled cells
  at tick 50 on seeds 57..64 (deviation from the seeds-49..56
  probe), halt pre-sweep and document in addendum (parallel to
  v0.43 / v0.43R halt pattern; methodological lesson preserved).

## Out of scope (v0.44)

- Sufficiency testing.
- Mechanism specificity (which property of respawn flow).
- Hazard generalisation beyond {0, 8}.
- Cross-stream calibration beyond seeds 57..64.
- Cross-stream calibration of v0.42 (deferred candidate).
- Hazard-relocation interventions.
- Chamber-geometry interventions.
- Delay magnitudes other than +25 (dose-response).
- Permutations other than reverse-row-major.
- Food-value substrate (v0.43R disqualified; deferred to a
  non-depleted-substrate chamber redesign).
- HedonismPolicy comparisons.
- Mesa migration.
- Edits to existing v0.34..v0.43R reducer surface or pre-v0.44
  arm tuples.
- Re-running the disqualified v0.43R sweep or the halted v0.43
  design.

## Implementation notes

### File-level changes

- **Modified (in `src/`):**
  - `src/hedonism_harness/core/interventions.py` (~180 LOC added):
    extend `InterventionConfig.kind` Literal with two new values;
    add `_eligible_respawn_cells`, `_respawn_multiset_digest`,
    `_delay_respawn_schedule_over_eligible_cells`,
    `_permute_respawn_schedule_over_eligible_cells`; add
    `_apply_respawn_schedule_rewrite` dispatcher branch. **Existing
    `null` / `kill_*` / `flatten_*` / `shuffle_*` / `reduce_*` /
    `density_preserving_*` paths untouched.**
  - `src/hedonism_harness/core/events.py` (~30 LOC added):
    `RespawnScheduleByIntervention` frozen dataclass + addition to
    `_SIGNAL_NAMES` and `AnyEvent` union.
  - `src/hedonism_harness/experiments/comparison_grid.py` (~30 LOC
    added): new constant `V0_44_INTERVENTION_ARMS` (additive).
- **New (in `scripts/`):**
  - `scripts/v0.44_sweep.py` (~80 LOC).
  - `scripts/v0_44_intervention_audit.py` (~700 LOC).
- **New (in `tests/`):**
  - `tests/test_interventions_v0_44.py` (~280 LOC).
  - `tests/test_world_intervention_hook_v0_44.py` (~140 LOC).
  - `tests/test_v0_44_sweep.py` (~120 LOC).
  - `tests/test_v0_44_intervention_audit.py` (~520 LOC).
- **Documented:** this pre-reg. Results appended after audit.
- **Manifest:** new file
  `docs/artifacts/v0.34_v0.44_local_corpus_manifest.md` post-
  Results.

### Tests required (locked at pre-reg time)

- **Intervention extensions:**
  - `_eligible_respawn_cells(world)` returns (x, y)-sorted ascending
    list; excludes HAZARD/WALL/SAFE; excludes cells with
    `respawn_at_tick == 0`.
  - `_respawn_multiset_digest(world, cells)` is SHA-256 over
    `struct.pack`-ed int32 sorted-ascending tick values.
  - `_delay_respawn_schedule_over_eligible_cells(world, delay=25)`:
    increments every eligible cell's `respawn_at_tick` by 25; sum
    increases by `25 * n`; min/max increase by 25; HAZARD/WALL/
    SAFE/food_value untouched; multiset digest changes.
  - `_permute_respawn_schedule_over_eligible_cells(world)`:
    reassigns by reverse-row-major over (x, y)-sorted cells; sum
    preserved exactly; min/max preserved exactly; multiset digest
    preserved exactly; HAZARD/WALL/SAFE/food_value untouched;
    self-inverse property (applying twice restores).
  - `apply_intervention` routes the new kinds correctly.
  - Determinism: same world state at firing → byte-identical
    post-state.
  - `kind="null"` remains byte-identical to default-None
    (regression).
  - v0.42 / v0.43 / v0.43R kinds remain byte-identical (regression).
- **Event class:**
  - `RespawnScheduleByIntervention` is frozen, slotted, hashable,
    serialisable.
  - All fields populated correctly on emission.
  - Distinct from `FoodRedistributedByIntervention` (separate
    `_SIGNAL_NAMES` entry).
- **World hook:**
  - Both new kinds fire at `tick_count == 51`, emit exactly one
    `RespawnScheduleByIntervention` event with correct fields.
  - B's `sum_after == sum_before + 25 * n_eligible`.
  - C's `sum_after == sum_before` exactly; multiset digest
    preserved.
  - No `AgentDied(cause="INTERVENTION")` events emitted by either
    new kind.
  - No `FoodRedistributedByIntervention` events emitted by the new
    kinds.
  - v0.42 A_null + B_kill_leader byte-identity regression
    (extends v0.43R's regression for the new kinds).
- **Sweep:** locked constants, arm tuple, seeds (57..64), hazards
  ({0, 8}).
- **Audit:** locked thresholds, all 5 H2 halts (a/b/c/d/d-aux/e),
  primary/secondary/auxiliary test arithmetic, three-way verdict
  + halt cell, locked-phrase regression guards, end-to-end
  synthetic fixture.

### Determinism contract

- All new helpers are pure functions of tick-50 chamber state.
- No new RNG. No `model.streams` draws.
- Default-None and `kind="null"` paths byte-identical to pre-v0.42.
- v0.42 / v0.43 / v0.43R kind paths byte-identical when re-run on
  v0.44 branch.
- The +25 delay is locked. The reverse-row-major permutation is
  locked over (x, y) ascending sort.

### LOC estimate

- `interventions.py` extension: ~180 LOC.
- `events.py` extension: ~30 LOC.
- `comparison_grid.py` arm tuple: ~30 LOC.
- Sweep + audit: ~780 LOC.
- 4 test files: ~1,060 LOC.
- This doc: ~800 LOC.
- Manifest (post-Results): ~250 LOC.

Total v0.44: ~3,130 LOC. Tests should bring the suite from 1,414
to ~1,494 (+~80).

### Pre-implementation feasibility preflight on seeds 57..64 (HARD REQUIREMENT)

**This preflight is mandatory before the v0.44 sweep is run, AND
before `EXPECTED_N_ELIGIBLE_CELLS` is committed as a hard halt
constant.** It must use `_run_one_arm_seed` (NOT hand-rolled
`run_chamber` — see v0.43R methodological lesson) under the exact
v0.44 sweep path (V0_25 anchor: GradientPolicy +
auto_reproduction=True + TraitConfig(unbounded_mutation=True) +
food_respawn_cooldown=50 + ambient_influx_rate=1.0).

The preflight must record, for every (seed ∈ 57..64, hazard ∈
{0, 8}) bucket at tick 50:

- `n_eligible_cells` (count of cells satisfying `kind ∈ {EMPTY,
  FOOD} AND respawn_at_tick > 0`).
- min, max, median, and full sorted multiset of `respawn_at_tick`
  values over the eligible-cell set.
- `total_food` over the chamber (expected: 0, matching v0.43R's
  corrected substrate finding; deviation halts).

Operative-substrate criteria (all must hold across all 16 buckets
to clear preflight):

- `n_eligible_cells` is consistent across all 16 buckets and is
  the value that gets committed to `EXPECTED_N_ELIGIBLE_CELLS`.
  v0.44 does NOT assume the seeds-49..56 value of 24 carries
  over.
- Refill-tick distribution is heterogeneous within each bucket
  (`min < max`).
- Refill ticks lie within a window such that `min + 25` and
  `max + 25` are both ≤ N_TICKS (= 200), so the +25 delay does
  not push refills past the simulation horizon.

If any criterion fails on any bucket, v0.44 halts pre-sweep
(parallel to v0.43 / v0.43R). The pre-reg is amended with the
observed values and the halt addendum before any sweep is run.
This is the **same halt-loud discipline** that produced the
v0.43R correction; **do NOT proceed to sweep on the seeds-49..56
extrapolation alone**.

The preflight is a documentation step, not a sweep. Its outputs
are committed to the pre-reg's "Preflight findings" subsection
(added on completion). It does NOT alter `src/`.

### Preflight findings (executed 2026-05-07)

**Status: PASS — preflight clears the v0.44 sweep.** All four
operative-substrate criteria hold across all 16 (seed, hazard)
buckets. Driver: `[[scripts/v0_44_preflight.py]]`. Path used:
`_run_one_arm_seed`-equivalent reconstruction via `_v0_43r_arm`
with `intervention_kind="null"` (byte-identical to the v0.44
A_null arms' eventual sweep path). Substrate captured at end of
`tick_count == 50` via `tick_observer`.

| seed | hzd | n_eligible | min | median | max | total_food |
|-----:|----:|-----------:|----:|-------:|----:|-----------:|
| 57   | 0   | 24         | 54  | 64.0   | 71  | 0.0        |
| 58   | 0   | 24         | 54  | 61.5   | 67  | 0.0        |
| 59   | 0   | 24         | 54  | 59.0   | 65  | 0.0        |
| 60   | 0   | 24         | 54  | 64.0   | 70  | 0.0        |
| 61   | 0   | 24         | 54  | 62.0   | 65  | 0.0        |
| 62   | 0   | 24         | 54  | 60.0   | 67  | 0.0        |
| 63   | 0   | 24         | 54  | 64.5   | 70  | 0.0        |
| 64   | 0   | 24         | 54  | 62.0   | 66  | 0.0        |
| 57   | 8   | 24         | 54  | 67.0   | 75  | 0.0        |
| 58   | 8   | 24         | 54  | 68.5   | 78  | 0.0        |
| 59   | 8   | 24         | 54  | 60.0   | 66  | 0.0        |
| 60   | 8   | 24         | 54  | 67.0   | 75  | 0.0        |
| 61   | 8   | 24         | 54  | 62.0   | 66  | 0.0        |
| 62   | 8   | 24         | 54  | 60.0   | 67  | 0.0        |
| 63   | 8   | 24         | 54  | 68.5   | 79  | 0.0        |
| 64   | 8   | 24         | 54  | 62.0   | 68  | 0.0        |

Aggregate refill-tick distribution across all 16 buckets
(n=384 = 16 × 24): **min=54, median=63.0, max=79**.

Criteria evaluation:

- **[PASS] Criterion 1** — `n_eligible_cells` consistent across
  all 16 buckets. Observed value: **24** in every bucket.
  `EXPECTED_N_ELIGIBLE_CELLS = 24` is now committed.
- **[PASS] Criterion 2** — refill-tick distribution heterogeneous
  within every bucket (`min < max` on all 16 buckets; `min=54`
  uniformly, `max ∈ [65, 79]`).
- **[PASS] Criterion 3** — `max_tick + 25 ≤ 200` on every bucket
  (worst case: seed 63 hzd 8, `max=79 → max+25=104`, well within
  the 200-tick simulation horizon).
- **[PASS] Criterion 4** — `total_food == 0.0` on every bucket
  (matches v0.43R's corrected substrate finding; the 24-cell food
  zone is completely depleted at tick 50 across the seeds-57..64
  band as well).

Substrate observations consistent with seeds 49..56 probe (which
showed refill ticks 54..67) but extended: seeds-57..64 buckets at
h=8 reach `max_tick=79`. The +25 delay shifts the first wave from
54..79 (early window) into 79..104 (mid-to-late window, with seed
63 hzd 8's max-delayed refill at tick 104, four ticks past the
50-tick observation window's end at tick 100). Implication for
the auxiliary: at h=8, the +25 delay pushes a non-negligible
fraction of first-wave refills past the observation horizon end;
DELAY_ABLATES_REPRODUCTION is plausibly reachable at h=8 (parallel
to the design intent).

The pre-reg's locked sweep can now proceed. **Implementation
gate: not yet opened — awaiting user signoff that the preflight
clears the way to begin v0.44 src/ + scripts/ + tests/
implementation.**

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1414 passed, 7 skipped (baseline including
                                v0.43 substrate-finding skip + v0.43R no-op
                                disqualification)
uv run python scripts/core_smoke_test.py   ok
```

(Pre-reg adds no executable code; CI is identical to v0.43R-halt
state.)

## Results

**Status:** pending implementation, feasibility re-probe, sweep,
and audit. Results appended after the audit fires (or after a
substrate-preflight halt, whichever applies).
