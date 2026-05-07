# v0.45 — birth-position / spatial-clustering causal probe (continuous post-50 birth redirection)

**Status:** pre-registered 2026-05-07; pending implementation.
**Date:** 2026-05-07
**Branch:** `claude/v0.45-birth-position-spatial-bottleneck`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated), v0.35 (founder-
survival timing — **H6 EXPANSION-SUPPORTED**), v0.36 (founder-trait
heritability — **H6 TRAIT-LINKED-FLAT**), v0.37 (dominance timing —
**H6 STABLER-EARLY-LEADERSHIP**), v0.38 (leader post-50 advantage —
**H5 LEADER-ADVANTAGE-AMPLIFIED**), v0.39 (fresh-stream calibration —
**H5_POOLED_ONLY**), v0.40 (cross-stream stability — **H5
STREAM-STABLE**), v0.41 (second fresh-stream calibration —
**v0.41_OLD_LIKE + H5_STREAM_STABLE_N5**), v0.42 (first causal probe —
**MECHANISM_NOT_NECESSARY**; tick-50 leader hard kill did not collapse
post-50 dominance), v0.43 (**HALTED**, retracted; saturated-zone
claim was config-mismatched), v0.43R (**HALTED**, disqualified;
food-density probe was a no-op because the V0_25 substrate is
completely depleted at tick 50), v0.44 (**RESPAWN_FLOW_NOT_NECESSARY**;
+25-tick respawn-schedule delay did not collapse post-50 dominance).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

The substrate-causal arc (v0.42 → v0.43R → v0.44) closed with three
negative findings: tick-50 leader identity not necessary, food-density
probe disqualified (substrate depleted), respawn flow not necessary.
v0.44's locked phrase explicitly named the remaining substrate-anchored
candidates: founder-trait + spatial-position interaction at the
depleted moment, hazard topology, chamber geometry (wall-adjacency,
reachability), and birth-position constraints.

The v0.45 spatial-clustering preflight (`[[scripts/v0_45_preflight.py]]`,
seeds 65..72 × hazards {0, 8}) confirmed that lineages are spatially
clustered at tick 50 with mean cluster purity 0.708 (vs random-mixed
baseline 0.20) and mean inter-centroid separation 4.68 vs intra-
lineage dispersion 2.48 (16/16 buckets). Lineages occupy spatially
distinct chamber regions at the locking tick — the substrate condition
that makes a birth-position intervention operative.

The active question for v0.45 is:

> **Is post-50 dominance dependent on parent-local birth placement
> and the spatial-cluster inheritance it produces? If we redirect
> every offspring birth after tick 50 to a uniformly-random valid
> cell anywhere in the chamber (breaking parent adjacency), does
> post-50 dominance fail to reconstitute? If we redirect to a
> uniformly-random valid adjacent neighbor (preserving adjacency
> but breaking deterministic placement), does dominance reconstitute
> regardless?**

This is a **birth-locality necessity probe** under continuous post-50
firing. The intervention semantics are different from v0.42 / v0.43R
/ v0.44 (single-tick substrate rewrite at the 50/51 boundary): v0.45
fires per-reproduction-event from `effective_tick >= 51` through end
of run.

The placebo control C is a **adjacency-preserving randomization**:
offspring still spawn in a parent-adjacent cell (preserving the
spatial-cluster inheritance mechanism) but the choice among valid
adjacent cells is uniform-random rather than the existing
deterministic N/S/E/W first-fit. This distinguishes "spatial-cluster
inheritance is necessary" (B disrupts; C does not) from "any per-
birth randomization disrupts dominance" (B and C disrupt comparably) —
parallel in cadence to v0.42's leader vs size-matched-non-leader
control, v0.43R's reduce vs density-preserving control, and v0.44's
delay vs permute control.

If post-50 dominance collapses under global redirection but not
under adjacency-preserving randomization, **birth locality at tick
50+ is necessary** for the v0.34..v0.41 dominance pattern. If both
interventions disrupt comparably, the system is sensitive to **any
per-birth randomization**, not specifically to adjacency-breaking.
If neither disrupts, the causal source lies further upstream than
the offspring-placement layer (founder traits, hazard topology,
chamber geometry).

## What this slice tests, and what it does NOT test

### Tests

- Whether **`post_intervention_top_lineage_b50_share`** (the same
  primary observable as v0.42 / v0.43R / v0.44; reused unchanged)
  in arm B drops by ≥ 0.15 relative to A at h=8, AND C remains
  within ±0.10 of A at h=8. **This is the primary birth-locality-
  necessity test.**
- Whether the B-vs-A reduction is larger at h=8 than at h=0
  (descriptive secondary observable; tests hazard-amplification
  specificity).
- Whether the intervention's `BirthRedirectedByIntervention`
  summary events are emitted exactly once per redirected birth,
  with the correct `intervention_kind`, `parent_id`,
  `parent_lineage_id`, `original_x/y`, `redirected_x/y`,
  `n_valid_cells`, and `preserved_parent_adjacency` fields.
- Whether **default-None and `kind="null"` paths** continue to be
  byte-identical to pre-v0.42 / v0.42 / v0.43R / v0.44 behaviour.
- Whether the auxiliary finding **GLOBAL_REDIRECT_ABLATES_REPRODUCTION**
  fires per-hazard: B produced > 2 of 8 runs with zero post-50
  surviving-lineage births at any hazard.

### Does NOT test

- **Mechanism sufficiency.** Necessity only.
- **Mechanism specificity.** v0.45 cannot distinguish parent-
  adjacency-as-spatial-mechanism from parent-adjacency-as-
  energy-transfer-proximity from parent-adjacency-as-foraging-
  cycle-locality. Refinement interventions reserved for v0.46+.
- **Hazard generalisation.** Only h=0 and h=8 are tested.
- **Cross-stream calibration of the intervention.** Seeds 65..72
  only; v0.46+ candidate.
- **The v0.34..v0.44 corpus.** v0.45 reads only its own sweep
  events.
- **Founder placement at tick 0.** Founders still use the existing
  deterministic `spread_y` placement (seed-independent). v0.45
  intervenes on offspring births only, post-tick-50.
- **Hazard topology disruption.** HAZARD-cell positions and
  counts are unchanged. Reserved for v0.46+ candidate.
- **Chamber-geometry interventions.** Walls inviolate; food zone
  topology preserved.
- **Pre-50 births.** All pre-50 reproduction events use the
  default `find_adjacent_empty_cell` path; intervention fires
  only on birth events with `tick > 50`.
- **Founder-trait lock-in.** Reserved for v0.46+ candidate.
- **Magnitude framing as "spread" or "amplification".** v0.45's
  primary uses absolute-share differences at h=8 (same convention
  as v0.42 / v0.43R / v0.44).

### Deferred (v0.46+ candidates, conditional on v0.45 outcome)

- **If BIRTH_LOCALITY_NECESSARY fires** (B drops; C does not).
  v0.46 candidates: (a) hazard-grid expansion; (b) cross-stream
  calibration on seed band 73..80; (c) sufficiency probe (force
  spatial clustering on a globally-randomized substrate via
  cluster injection); (d) refinement: distance-graded redirection
  (uniform within radius r of parent for r ∈ {1, 3, 5, ∞}).
- **If LOCAL_CONTROL_DISRUPTS_DOMINANCE fires** (B and C both
  disrupt). v0.46 candidate: weaker C-arm randomization (e.g.,
  rotated-iteration-order) to test whether the pattern is
  fragile to any randomization or only to uniform-random.
- **If BIRTH_LOCALITY_NOT_NECESSARY fires** (neither disrupts).
  v0.46 candidate: pivot to founder-trait lock-in or hazard-
  topology relocation. Spatial-placement causal levers exhausted.
- **If GLOBAL_REDIRECT_ABLATES_REPRODUCTION fires per-hazard**
  (auxiliary). v0.46 candidate: limit B's redirection radius
  (e.g., uniform within distance 5 of parent) to separate
  "global redirection ablates reproduction" from "global
  redirection disrupts dominance".

### Quarantined (not v0.45 inputs)

- v0.34..v0.44 reducer outputs. v0.45 reads only its own sweep
  events.
- HedonismPolicy. Mesa migration. v0.36 founder traits. Cross-
  stream calibration.
- The disqualified v0.43R sweep, halted v0.43 design, and v0.44
  events; v0.45 sweep is independent.

## Conservation framing — additive over v0.42..v0.44 + first
extension to `core/reproduction.py`

v0.45 extends the already-landed intervention infrastructure with
**two new `kind` values**, **one new event class**, **one new
optional callback parameter on `process_reproduction()`**, and **one
new helper predicate**. The v0.42–v0.44 surface is unchanged.

**v0.45 is the first slice that adds a parameter to `core/reproduction.py`.**
The change is additive: a new optional `birth_redirect_callback`
parameter defaulting to `None`. When `None` (the default), the
function behaves byte-identically to v0.21..v0.44. When provided,
the callback is consulted per reproduction event to determine the
child's placement coordinates. v0.42–v0.44 sweeps re-run on the
v0.45 branch produce events.jsonl byte-identical to their original
outputs (regression-guarded by H2e).

The primitives that v0.42 / v0.43 / v0.43R / v0.44 contributed
(unchanged in v0.45):

- The chamber-runner `optional_intervention` hook for tick-50/51
  single-fire interventions (preserved; orthogonal to v0.45's
  per-birth callback).
- v0.42's leader-kill / size-matched-kill paths.
- v0.43's flatten / shuffle paths.
- v0.43R's reduce-density / density-preserving-perturbation paths.
- v0.44's delay-respawn / permute-respawn paths.
- The `_eligible_cells`, `_eligible_cells_digest`,
  `_food_multiset_digest`, `_eligible_respawn_cells`,
  `_respawn_multiset_digest` helpers in `core/interventions.py`.

Modifications under v0.45:

- **Modified module:** `src/hedonism_harness/core/interventions.py`
  - Two new `kind` literal values:
    `"uniform_valid_region_birth_position_after_tick50"` (B),
    `"uniform_neighbor_birth_position_after_tick50"` (C).
  - One new helper predicate:
    `_is_v045_birth_safe_placeable(world, x, y, occupied)` —
    returns `True` iff cell is in-bounds, unoccupied, and
    `kind ∈ {EMPTY, FOOD, SAFE}` (excludes WALL and HAZARD).
    **Intervention-local; does not modify `core/reproduction.py`'s
    `_is_placeable`.**
  - One new helper: `_v045_eligible_global_cells(world, occupied)` —
    returns the list of cells satisfying the predicate over the
    entire chamber.
  - One new helper: `_v045_eligible_neighbor_cells(world, parent,
    occupied)` — returns parent's N/S/E/W cells filtered by the
    predicate.
  - One new callable factory: `make_v045_birth_redirect_callback(
    config, model)` — returns the per-birth callback bound to the
    intervention kind and the model's RNG stream.
  - Existing `null` / `kill_*` / `flatten_*` / `shuffle_*` /
    `reduce_*` / `density_preserving_*` / `delay_*` / `permute_*`
    paths remain byte-identical.
- **Modified module:** `src/hedonism_harness/core/events.py`
  - One new event class: `BirthRedirectedByIntervention` (frozen
    dataclass; field list locked below). Added to `_SIGNAL_NAMES`
    and `AnyEvent` union.
- **Modified module:** `src/hedonism_harness/core/reproduction.py`
  - One new optional parameter on `process_reproduction()`:
    `birth_redirect_callback: Callable[[World, AgentBody,
    frozenset], tuple[int, int] | None] | None = None`. When
    `None`, the existing `find_adjacent_empty_cell` path runs
    unchanged. When provided, the callback's return value
    (a `(x, y)` tuple, or `None` to skip this birth) overrides
    placement; if the callback returns `None`, the birth is
    skipped (no charge, no child). If the callback returns a
    cell that fails `_is_placeable`, the birth is skipped (audit
    halts in-run? — see "Hook contract" §below).
  - **No other modification.** Default-None preserves v0.21..v0.44
    byte-identity exactly.
- **Modified module:** `src/hedonism_harness/experiments/fear_hunger_chamber.py`
  - Chamber driver constructs the `birth_redirect_callback` from
    `optional_intervention` when the kind is one of v0.45's two
    new kinds, and threads it through to `process_reproduction()`.
- **Modified module:** `src/hedonism_harness/model.py` (or `mesa_agents.py`,
  whichever owns the `_attempt_reproduction` path) — propagates
  the callback from chamber driver into the per-agent reproduction
  call site. **No semantic change to the default-None path.**
- **`comparison_grid.py`**: one new constant
  `V0_45_INTERVENTION_ARMS` (additive only; existing arms tuples
  unchanged).

The following are NOT modified:

- Existing chamber, policy, or population-dynamics behaviour
  outside the new kind paths.
- All v0.34..v0.44 reducer scripts and audits.
- Pre-v0.45 events on disk. Re-running prior sweeps with default
  `optional_intervention=None` produces byte-identical events.jsonl
  files.
- v0.42's kill paths, v0.43's flatten/shuffle paths, v0.43R's
  density paths, v0.44's respawn-schedule paths — byte-identical
  when re-run on v0.45 branch (H2e regression).
- Founder placement at tick 0 (`spread_y`).
- The default `find_adjacent_empty_cell` placement order (N/S/E/W).
- `_is_placeable` semantics in `core/reproduction.py`.

## Mechanism

v0.45 ships:

1. Two new intervention kinds + helpers + predicate in
   `src/hedonism_harness/core/interventions.py`.
2. One new event class in `src/hedonism_harness/core/events.py`.
3. One additive parameter on `process_reproduction()` in
   `src/hedonism_harness/core/reproduction.py`.
4. Chamber-driver wiring in
   `src/hedonism_harness/experiments/fear_hunger_chamber.py`.
5. Per-agent reproduction-call-site wiring (in `mesa_agents.py`
   and/or `model.py`).
6. A new sweep driver and arm tuple.
7. A v0.45 audit reducer that consumes the v0.45 sweep events.
8. Paired test files for each addition.
9. This pre-reg.

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
    "delay_respawn_schedule_plus_25_at_tick50",
    "permute_respawn_schedule_reverse_row_major_at_tick50",
    "uniform_valid_region_birth_position_after_tick50",   # NEW v0.45 (B)
    "uniform_neighbor_birth_position_after_tick50",       # NEW v0.45 (C)
]
```

New eligibility predicate (intervention-local):

```python
def _is_v045_birth_safe_placeable(
    world, x: int, y: int, occupied: frozenset[tuple[int, int]] | None
) -> bool:
    """v0.45 birth-redirection eligibility predicate. Returns True iff:
      - in_bounds(world, x, y),
      - kind in {EMPTY, FOOD, SAFE} (excludes WALL and HAZARD),
      - (x, y) not in occupied.
    Used for both B (global) and C (adjacent) eligible-cell selection.
    DOES NOT replace core/reproduction.py's _is_placeable; that
    helper governs default reproduction semantics and remains
    byte-identical."""
```

Two new helpers:

```python
def _v045_eligible_global_cells(world, occupied) -> list[tuple[int, int]]:
    """B arm. Return all cells (x, y) satisfying
    _is_v045_birth_safe_placeable, sorted (x, y) ascending. Excludes
    HAZARD/WALL and occupied/out-of-bounds."""

def _v045_eligible_neighbor_cells(world, parent, occupied) -> list[tuple[int, int]]:
    """C arm. Return parent's N/S/E/W neighbors filtered by
    _is_v045_birth_safe_placeable, in deterministic (x, y) ascending
    order over the surviving neighbors."""
```

One callable factory:

```python
def make_v045_birth_redirect_callback(config, model):
    """Returns a callable suitable for ``birth_redirect_callback``
    in process_reproduction(). The callable receives (world, parent_body,
    occupied) and returns either (x, y) for the redirected child or
    None to skip the birth.

    Behavior by kind:
      - B (uniform_valid_region_birth_position_after_tick50):
        if model.tick_count <= 50: defer to default placement (return
            None? — see hook contract);
        else: pick uniformly at random from
            _v045_eligible_global_cells(...) using
            model.streams['v0_45_birth_position_intervention'].
            If the eligible set is empty, return None (birth skipped).
      - C (uniform_neighbor_birth_position_after_tick50):
        if model.tick_count <= 50: defer to default placement;
        else: pick uniformly at random from
            _v045_eligible_neighbor_cells(...) using the same RNG
            stream. If empty, return None (birth skipped).

    The callback emits one BirthRedirectedByIntervention event per
    redirected birth (including events for tick > 50 redirected
    placements; pre-50 events are NOT emitted because the callback
    defers without firing)."""
```

Hook contract for `birth_redirect_callback`:

- The callback is invoked by `process_reproduction()` *in place of*
  the default `find_adjacent_empty_cell` call when
  `birth_redirect_callback is not None`.
- Return value semantics:
  - `(x, y)` tuple (any in-bounds non-WALL unoccupied cell):
    placement proceeds at that cell.
  - `None`: birth is skipped (no charge, no child, no event other
    than whatever the callback chose to emit).
- Pre-tick-51 invocations: the callback **defers to default**
  placement by returning the result of `find_adjacent_empty_cell`
  itself (so the v0.45 callback acts as an intercepting wrapper,
  preserving v0.21..v0.44 semantics for ticks <= 50). The callback
  does **not** emit `BirthRedirectedByIntervention` for these
  pre-50 deferrals.
- Post-tick-50 invocations: the callback selects from its kind-
  specific eligible-cell set (B or C); on success emits one
  `BirthRedirectedByIntervention` event and returns the selected
  cell; on empty-set returns `None` (birth skipped, no event).

Determinism contract:

- v0.45 introduces **one new RNG stream** with locked label
  `"v0_45_birth_position_intervention"`. All stochasticity lives
  in this stream.
- For a given (seed, hazard, intervention_kind), the per-birth
  callback produces the same redirected cell every time (since
  the stream draws are seed-derived and the stream label is
  locked).
- No new sources of entropy outside this stream; default-None
  paths byte-identical to v0.44.

### Why uniform-global for B?

The preflight established that lineages at tick 50 are spatially
clustered (mean cluster purity 0.708 vs 0.20 random-mixed baseline).
The default `find_adjacent_empty_cell` placement (N/S/E/W first-fit)
produces parent-adjacent offspring → lineages stay locally coherent
through reproduction. **Breaking parent-adjacency** is the most
direct intervention on the spatial-cluster-inheritance mechanism.

Uniform-random over the chamber's `_is_v045_birth_safe_placeable`
cells:

- **Maximally disrupts spatial clustering**: post-50 births land
  uniformly across the chamber rather than within parent's 1-cell
  neighborhood.
- **Preserves the birth event**: agents still spawn when they would
  have spawned, and at the same total rate (modulo the rare empty-
  eligible-set case). Only the *spatial* assignment changes.
- **Excludes HAZARD by predicate**: prevents conflating "broke
  spatial locality" with "placed newborn on hazard, killing it."
  This is the single most important design constraint on B (per
  user's insight).

### Why uniform-neighbor for C?

C is **magnitude-matched to B in the per-birth randomization-source
sense**: both use the same RNG stream, both make a uniform-random
selection at every post-50 birth, both use the same eligibility
predicate (excludes HAZARD/WALL, requires unoccupied).

The only difference: **C's eligible-cell set is parent's N/S/E/W
neighbors** (preserves adjacency), while **B's is the entire chamber**
(breaks adjacency).

This means:
- If only B disrupts dominance → adjacency-locality is the
  necessary mechanism.
- If both B and C disrupt → any per-birth randomization at the
  uniform-among-valid-cells magnitude shocks dominance.
- If neither disrupts → the dominance pattern is robust to per-
  birth placement randomization in either form.

C's adjacency-preservation parallels v0.43R's
`density_preserving_perturbation` (which preserved total food but
shifted the multiset) and v0.44's
`permute_respawn_schedule_reverse_row_major` (which preserved the
schedule multiset but permuted cell-to-tick assignments). All three
controls share the pattern: **break the determinism of the
substrate-rewrite layer being tested while preserving the
conservation invariant of that layer**.

### 2. Event class (`core/events.py`) — NEW

```python
@dataclass(frozen=True, slots=True)
class BirthRedirectedByIntervention:
    """v0.45: emitted once per offspring birth event with tick > 50
    when the birth-redirect callback fires. One event per redirected
    birth; mean ~12.9 events per run on the v0.45 sweep corpus
    (preflight estimate; actual count depends on sweep dynamics).

    Two intervention kinds:
    - "uniform_valid_region_birth_position_after_tick50" (B):
      eligible_cells = chamber-wide cells satisfying
      _is_v045_birth_safe_placeable. preserved_parent_adjacency
      may be True or False per event (True if the random draw
      happened to land adjacent; expected to be small for B).
    - "uniform_neighbor_birth_position_after_tick50" (C):
      eligible_cells = parent's N/S/E/W neighbors filtered by
      _is_v045_birth_safe_placeable. preserved_parent_adjacency
      is always True.

    Eligibility predicate excludes HAZARD/WALL/out-of-bounds/
    occupied cells (intervention-local; does not affect default
    reproduction).

    Audit conservation (v0.45):
    - For B and C: redirected cell satisfies
      _is_v045_birth_safe_placeable at the firing moment.
    - For C: |original_x - redirected_x| + |original_y - redirected_y|
      <= 1 (adjacency preserved; pure tie-break randomness).
    - For B: no adjacency invariant; redirected cell is anywhere in
      eligible set."""

    intervention_kind: str
    tick: int                      # the model.tick_count when birth fires
    parent_id: int
    parent_lineage_id: int
    parent_x: int                  # parent's position (origin of default placement)
    parent_y: int
    original_x: int                # what find_adjacent_empty_cell would have returned
    original_y: int                # (None-encoded as -1 if default would have skipped)
    redirected_x: int              # what the callback chose
    redirected_y: int
    n_valid_cells: int             # size of eligible-cell set at this firing
    preserved_parent_adjacency: bool
    rng_stream_label: str          # "v0_45_birth_position_intervention" (locked)
```

Added to `_SIGNAL_NAMES` and the `AnyEvent` union.

### 3. Reproduction extension (`core/reproduction.py`) — additive

```python
def process_reproduction(
    parent: AgentBody,
    world: World,
    config: ReproductionConfig,
    trait_config: TraitConfig,
    parent_rng: random.Random,
    child_id: int,
    occupied: frozenset[tuple[int, int]] | None = None,
    birth_redirect_callback: Callable[..., tuple[int, int] | None] | None = None,  # NEW v0.45
) -> tuple[AgentBody, AgentBody] | None:
    """[existing docstring] ...

    v0.45 (additive): when birth_redirect_callback is provided, the
    callback is consulted in place of find_adjacent_empty_cell to
    determine the child's coordinates. A None return value skips
    the birth. The default-None path preserves v0.21..v0.44 behavior
    byte-identically."""
```

Default-None preserves byte-identity exactly: when `None`, the
existing `find_adjacent_empty_cell(world, parent, occupied)` path
runs unchanged.

### 4. Sweep + arm tuple (`scripts/v0.45_sweep.py`, `comparison_grid.py` additions)

Three arms × 2 hazards × 8 seeds = **48 runs**. Arm tuple:

```python
V0_45_INTERVENTION_ARMS: tuple[Arm, ...] = (
    # A_null (no intervention; baseline)
    _v0_45_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    _v0_45_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="A_null", intervention_kind="null"),
    # B_uniform_valid_region (treatment: break parent adjacency)
    _v0_45_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="B_uniform_valid_region",
               intervention_kind="uniform_valid_region_birth_position_after_tick50"),
    _v0_45_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="B_uniform_valid_region",
               intervention_kind="uniform_valid_region_birth_position_after_tick50"),
    # C_uniform_neighbor (placebo: preserve adjacency, randomize tie-break)
    _v0_45_arm(base_label="transfer-1500-hzd0-influx-1.0", arm_prefix="C_uniform_neighbor",
               intervention_kind="uniform_neighbor_birth_position_after_tick50"),
    _v0_45_arm(base_label="transfer-1500-hzd8-influx-1.0", arm_prefix="C_uniform_neighbor",
               intervention_kind="uniform_neighbor_birth_position_after_tick50"),
)
```

Arm labels prefixed `v045-`. Output directory:
`runs/fear-hunger-v0.45-tight_gradient/`.

Seeds: **65..72** (next disjoint band beyond v0.44's 57..64;
disjoint from all prior streams 1..8, 9..16, 17..24, 25..32,
33..40, 41..48, 49..56, 57..64). Substrate parameters inherited
from V0_25 substrate via `dataclasses.replace`.

### 5. v0.45 audit (`scripts/v0_45_intervention_audit.py`)

Imports only `LineageReplayError` via `importlib.util`. Pure stdlib
otherwise.

Reads:

- Per-arm `comparison.csv` from
  `runs/fear-hunger-v0.45-tight_gradient/arms/`.
- Per-run `events.jsonl` (specifically:
  `BirthRedirectedByIntervention` events + post-50 `AgentBorn`
  events for the primary observable).

Halt invariants (5):

- **H2a (run count):** exactly 6 arms × 8 seeds = 48 runs on disk.
- **H2b (intervention-fire pattern per arm):**
  - A_null: 0 `BirthRedirectedByIntervention` events per run.
  - B_uniform_valid_region: at least 1 event per run with
    `tick > 50` and `intervention_kind="uniform_valid_region_birth_position_after_tick50"`,
    UNLESS the run's auxiliary `excluded_zero_post50 == True`
    (no post-50 births of any kind, so no redirections to fire).
  - C_uniform_neighbor: same with the C kind.
- **H2c (tick monotonicity):** every fired event has
  `tick > 50`. Pre-50 events are forbidden (callback defers
  pre-50).
- **H2d (placement conservation):**
  - For both B and C: every fired event's `(redirected_x, redirected_y)`
    satisfies `_is_v045_birth_safe_placeable` at the firing moment
    (i.e., the audit re-evaluates the predicate against the chamber
    state captured in the event; halt on violation).
  - For C only: `|original_x - redirected_x| + |original_y -
    redirected_y| <= 1` (parent-adjacency preserved by predicate
    construction).
  - For both: `n_valid_cells >= 1` on every fired event (callback
    only fires when the eligible set is non-empty).
  - For both: `rng_stream_label == "v0_45_birth_position_intervention"`.
  - For both: `preserved_parent_adjacency` is consistent with the
    Manhattan-distance predicate (always True for C; True/False
    per-event for B).
- **H2e (regression byte-identity):** sampled v0.42 A_null seed +
  v0.42 B_kill_leader seed + v0.43R B_reduce seed + v0.44 B_delay
  seed re-run with v0.45 code produce events.jsonl byte-identical
  to their respective sealed references. Same regression as v0.44
  with v0.43R and v0.44 paths added; preserved through v0.45
  because no pre-v0.45 path is modified.
- **C-rises-above-A halt:** if `c_share_h8 > a_share_h8 + 0.10`,
  halt loud (substrate artefact unmodeled). Locked from v0.43R
  / v0.44.
- **C_DISRUPTS_WITHOUT_B halt:** if `b_passes == False AND c_below_a
  == True`, halt loud (mechanistically unmotivated; C disrupts but
  B does not).

Computes per-(arm, seed):

- `post_intervention_top_lineage_b50_share` (identical formula to
  v0.42 / v0.43R / v0.44; no lineage exclusion since no lineage
  is killed).
- `total_post_50_births`, `top_lineage_id`, `top_lineage_post50_births`.
- `n_redirected_births`: count of BirthRedirectedByIntervention
  events in the run (0 for A_null; otherwise positive for B/C
  unless excluded).
- `mean_n_valid_cells_per_birth`: average over fired events.
- `fraction_b_preserved_adjacency`: for B runs, fraction of fired
  events with `preserved_parent_adjacency == True` (diagnostic for
  how often random global selection happened to land adjacent;
  expected small).
- `excluded_zero_post50` (True if `total_post_50_births == 0`).

Aggregates per-(arm, hazard) and computes the locked decision rule.

Outputs eight CSVs under `runs/lineage-v0.45/`:

- `per_run.csv` — 48 rows.
- `per_arm_per_hazard.csv` — 6 rows.
- `intervention_summary.csv` — 6 rows.
- `primary_test.csv` — 1 row (with explicit verdict booleans).
- `secondary_test.csv` — 1 row.
- `verdict.csv` — 1 row.
- `auxiliary_findings.csv` — 2 rows (one per hazard).
- `placement_conservation.csv` — per-(arm, hazard) digest of
  fired-event statistics.

### Locked constants

```python
EXPECTED_HAZARDS: tuple[int, ...] = (0, 8)
EXPECTED_SEEDS: tuple[int, ...] = tuple(range(65, 73))  # 65..72
EXPECTED_N_FOUNDERS: int = 5
EXPECTED_N_TICKS: int = 200
EXPECTED_RUNS_TOTAL: int = 48  # 6 arms x 8 seeds
EXPECTED_TICK_THRESHOLD: int = 50  # callback defers for tick <= 50

# Locked thresholds (parallel to v0.42 / v0.43R / v0.44)
PRIMARY_B_REDUCTION_THRESHOLD: float = 0.15
PRIMARY_C_TOLERANCE: float = 0.10

# Auxiliary threshold
AUXILIARY_GLOBAL_REDIRECT_ABLATION_MAX_EXCLUDED: int = 2

# Arm labels
ARM_A_NULL: str = "v045-A_null"
ARM_B_UNIFORM_GLOBAL: str = "v045-B_uniform_valid_region"
ARM_C_UNIFORM_NEIGHBOR: str = "v045-C_uniform_neighbor"

# Intervention kind labels
KIND_NULL: str = "null"
KIND_UNIFORM_VALID_REGION_BIRTH: str = "uniform_valid_region_birth_position_after_tick50"
KIND_UNIFORM_NEIGHBOR_BIRTH: str = "uniform_neighbor_birth_position_after_tick50"

# RNG stream label (locked; consumed by model.streams)
RNG_STREAM_LABEL: str = "v0_45_birth_position_intervention"
```

### Determinism — anchors

- v0.21..v0.44 events.jsonl + sidecar artifacts not re-read by the
  primary v0.45 audit. H2e regression check reads selected v0.42 /
  v0.43R / v0.44 references for fingerprint comparison only.
- All v0.34..v0.44 test suites continue to pass (additive guard).
- Default `optional_intervention=None` is byte-identical to
  pre-v0.42 behaviour.
- `kind="null"` byte-identical to default-None (no per-birth
  callback constructed).
- v0.42 / v0.43 / v0.43R / v0.44 kind paths byte-identical when
  re-run on v0.45 branch.
- Re-running v0.45 sweep with the same seeds produces byte-
  identical events.jsonl files.
- Pre-50 reproduction events byte-identical to v0.44 (callback
  defers; no `BirthRedirectedByIntervention` event emitted).

### Wall-time estimate

- v0.45 sweep: ~25s (48 runs; expected longer than v0.42 / v0.43R
  / v0.44 sweeps because B's global redirection scatters lineages,
  potentially altering reproduction dynamics; at h=8 the auxiliary
  may fire and reduce simulation work).
- v0.45 audit: ~5s (more events per run to iterate vs v0.44).
- Total v0.45 incremental wall-time: ~30s.

## Observables — pre-committed before reading the data

### Per-run — 48 rows total

- `arm` ∈ {A_null, B_uniform_valid_region, C_uniform_neighbor}.
- `hazard` ∈ {0, 8}.
- `seed` ∈ {65..72}.
- `n_redirected_births`: int (>=0; 0 for A_null).
- `mean_n_valid_cells_per_birth`: float (NaN for A_null and runs
  with `n_redirected_births == 0`).
- `fraction_b_preserved_adjacency`: float in [0, 1] (NaN for
  A_null and C runs; for B, the fraction of fired events where
  random global selection happened to land in parent's N/S/E/W).
- `total_post_50_births`: int (count of `AgentBorn` events with
  `tick > 50`, regardless of redirection).
- `top_lineage_id`, `top_lineage_post50_births`: int.
- `post_intervention_top_lineage_b50_share`: float in [0, 1]
  (NaN if total_post_50_births == 0).
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
- `birth_locality_necessary := b_passes AND c_passes`.
- `local_control_disrupts := b_passes AND c_below_a`.
- `birth_locality_not_necessary := NOT b_passes AND NOT c_below_a`.
- `c_above_a_unmodeled_substrate_artefact := b_passes AND c_above_a`
  (halt cell — no scientific verdict emitted).
- `c_disrupts_without_b := NOT b_passes AND c_below_a`
  (halt cell — mechanistically unmotivated).
- `primary_fires := birth_locality_necessary OR local_control_disrupts`.
- `verdict`: derived from booleans above (see Decision rules).

### Secondary test (`secondary_test.csv` — 1 row)

- `delta_b_minus_a_h0`, `delta_b_minus_a_h8`.
- `hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.
- `secondary_fires := primary_fires AND hazard_amplified`.

### Auxiliary findings (`auxiliary_findings.csv` — 2 rows, one per hazard)

- `hazard`.
- `b_n_excluded_zero_post50`: number of B runs at this hazard with
  zero post-50 births (out of 8).
- `ablation_threshold_exceeded := b_n_excluded > AUXILIARY_GLOBAL_REDIRECT_ABLATION_MAX_EXCLUDED`.
- `auxiliary_phrase_fires`: bool.

Auxiliary finding is **non-exclusive** of the primary verdict.

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive `src/` modification).** Only the new intervention
  kinds, event class, helpers, predicate, and additive parameter
  on `process_reproduction()`. All pre-v0.45 kind paths are byte-
  identical. Includes regression tests on sampled v0.42 /
  v0.43R / v0.44 seeds.
- **H2a (run count).** Exactly 48 runs on disk after v0.45 sweep.
- **H2b (intervention-fire pattern per arm).** A_null: 0 events;
  B and C: ≥ 1 event per run unless `excluded_zero_post50`.
- **H2c (tick monotonicity).** Every fired event has `tick > 50`.
- **H2d (placement conservation).**
  - Redirected cell satisfies `_is_v045_birth_safe_placeable` at
    firing moment (re-evaluated in audit against captured chamber
    state).
  - For C: redirected cell is parent-adjacent (Manhattan distance
    <= 1).
  - For both: `rng_stream_label == "v0_45_birth_position_intervention"`.
- **H2e (regression byte-identity).** v0.42 / v0.43R / v0.44
  reference seeds re-run with v0.45 code produce events.jsonl
  byte-identical to their sealed references.
- **H3 (additive guard).** v0.21..v0.44 + v0.43-skipped tests
  still pass after v0.45 additions.
- **H4 (no mutation of pre-v0.45 surface).** All pre-v0.45
  scripts, reducers, audits, arm tuples, chamber/policy/population
  modules — byte-identical (modulo the additive parameter on
  `process_reproduction()`, which is default-None preserved).

### Cautious form — three-way verdict on v0.45's birth-locality-necessity question

The verdict is intentionally three-way, mutually exclusive on the
locked decision space, plus two halt cells:

**BIRTH_LOCALITY_NECESSARY.** **FIRES iff** `b_passes == True` AND
`c_passes == True`. Headline: redirecting offspring to uniform-
random valid-safe-placeable cells anywhere in the chamber
(breaking parent adjacency) materially disrupts post-50 dominance,
while redirecting to uniform-random valid-safe-placeable cells
adjacent to the parent (preserving adjacency) does not. Parent-
local birth placement and the spatial-cluster inheritance it
produces are **necessary** for the v0.34..v0.41 dominance pattern
under the tested substrate; the specific deterministic N/S/E/W
tie-break is not.

**LOCAL_CONTROL_DISRUPTS_DOMINANCE.** **FIRES iff** `b_passes ==
True` AND `c_below_a == True`. Headline: both global redirection
and adjacency-preserving randomization disrupt post-50 dominance.
The pattern is sensitive to **any per-birth randomization**, not
specifically to adjacency-breaking. v0.34..v0.41's correlational
pattern reflects fragility to placement-shock rather than a
locality-specific causal mechanism.

**BIRTH_LOCALITY_NOT_NECESSARY.** **FIRES iff** `NOT b_passes`
AND `NOT c_below_a`. Headline: neither redirection (global or
local) materially disrupts post-50 dominance. Parent-local birth
placement is **not necessary** for the pattern; the causal source
lives outside the offspring-placement layer (founder traits,
hazard topology, chamber geometry).

**C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt cell):** `b_passes
== True` AND `c_above_a == True`. Substrate artefact unmodeled at
pre-reg time. Audit halts loud (`LineageReplayError`); no
scientific verdict emitted. Parallel to v0.43R / v0.44.

**C_DISRUPTS_WITHOUT_B (halt cell):** `b_passes == False` AND
`c_below_a == True`. Mechanistically unmotivated: C (the weaker
adjacency-preserving randomization) disrupts dominance while B
(the stronger global redirection) does not. Audit halts loud
(`LineageReplayError`); no scientific verdict emitted. Indicates a
substrate artefact unmodeled at pre-reg time.

(All five cells exhaust the rule space:
- `b_passes=True, c_passes=True` → BIRTH_LOCALITY_NECESSARY.
- `b_passes=True, c_below_a=True` → LOCAL_CONTROL_DISRUPTS_DOMINANCE.
- `b_passes=True, c_above_a=True` → C_ABOVE_A_UNMODELED (halt).
- `b_passes=False, c_passes` ∨ `c_above_a` → BIRTH_LOCALITY_NOT_NECESSARY.
- `b_passes=False, c_below_a=True` → C_DISRUPTS_WITHOUT_B (halt).)

### Auxiliary finding — independent of primary verdict

**GLOBAL_REDIRECT_ABLATES_REPRODUCTION (per-hazard).** **FIRES
iff** `b_n_excluded_zero_post50 > 2` at any hazard. Reported
alongside the primary verdict; does NOT alter the verdict logic.
Headline: redirecting offspring to uniform-random valid-safe-
placeable global cells reduced reproductive viability below the
threshold required to sustain post-50 reproduction in this
fraction of seeds at this hazard. **Descriptive substrate
finding**: scattering offspring across the chamber can ablate
reproduction at sufficient distance from parent.

### Locked phrases for each verdict

> **BIRTH_LOCALITY_NECESSARY phrase:** "Redirecting every post-50
> offspring birth to a uniformly-random valid-safe-placeable cell
> anywhere in the chamber (breaking parent adjacency) materially
> disrupts the post-50 dominance pattern at h=8: when offspring
> are scattered across the chamber rather than placed adjacent
> to their parents, the surviving lineages do not reconstitute
> concentration of comparable share. The adjacency-preserving
> randomization control (which selects uniformly among parent's
> N/S/E/W valid-safe-placeable neighbors using the same RNG
> stream) does NOT produce comparable disruption. Under the
> tested substrate, **parent-local birth placement is necessary**
> for the v0.34..v0.41 dominance pattern; the specific
> deterministic N/S/E/W tie-break is not. v0.45 does not declare
> which property of parent-local placement carries the effect
> (spatial-cluster integrity, energy-transfer proximity,
> foraging-cycle locality); refinement interventions in v0.46+
> are required. Necessity is established at one hazard level
> (h=8) on one seed band (65..72) under one redirection rule
> (uniform-valid-region); cross-stream calibration and dose-
> response sweeps are reserved for v0.46+. Sufficiency is NOT
> tested."

> **LOCAL_CONTROL_DISRUPTS_DOMINANCE phrase:** "Both global
> redirection and adjacency-preserving randomization disrupt
> post-50 dominance at h=8. The post-50 dominance pattern is
> sensitive to **any per-birth randomization** of comparable
> magnitude (uniform among the eligible-cell set using the
> v0.45 RNG stream), not specifically to adjacency-breaking.
> v0.34..v0.41's correlational pattern reflects fragility to
> placement-shock rather than a locality-specific causal
> mechanism. v0.46 candidate: weaker C-arm randomization
> (rotated-iteration-order) to test whether the pattern is
> fragile to any randomization or only to uniform-random.
> Mechanism remains unidentified at the offspring-placement
> level."

> **BIRTH_LOCALITY_NOT_NECESSARY phrase:** "Neither redirection
> (global or adjacency-preserving) materially disrupts the post-
> 50 dominance pattern at h=8. A surviving lineage reconstitutes
> concentration-of-share even when offspring are scattered
> uniformly across the chamber's valid-safe-placeable region.
> **Parent-local birth placement is not necessary** for post-50
> dominance under the tested substrate; the causal source lives
> outside the offspring-placement layer at the anchor moment.
> v0.42 ruled out the tick-50 leader's identity; v0.43R's food-
> density probe was disqualified (substrate depleted); v0.44
> ruled out tick-50 respawn flow; v0.45 rules out post-50
> birth-position locality. Remaining substrate-anchored
> candidates: founder-trait lock-in, hazard topology
> relocation, chamber geometry (wall-adjacency, reachability).
> v0.46 candidate: founder-trait lock-in or hazard-relocation
> intervention."

> **GLOBAL_REDIRECT_ABLATES_REPRODUCTION (auxiliary, per-hazard)
> phrase:** "At hazard h={h}, the B_uniform_valid_region arm
> produced {n_excluded} of 8 runs with zero post-50 births: the
> uniform-global redirection scattered offspring far from
> parents, ablating reproduction itself rather than relocating
> dominance. This is a **descriptive substrate finding** parallel
> to but independent of the share-based primary verdict: the
> distance from parent reduced reproductive viability below the
> threshold required to sustain post-50 reproduction in this
> fraction of seeds at this hazard. The primary verdict is
> computed over n_used (non-excluded) runs; this auxiliary
> finding is reported alongside but does NOT alter the primary
> verdict logic. v0.46 candidate: limit B's redirection radius
> (e.g., uniform within distance 5 of parent) to separate
> distance-ablates-reproduction from distance-relocates-
> dominance."

### Caveats — locked, must appear in Results

- **Per-arm n is 8.** Conservative on n=8.
- **Necessity only.** Sufficiency not tested.
- **One seed band.** Seeds 65..72 only.
- **Two hazards only.** {0, 8}.
- **Single locked redirection rule.** Uniform over the eligible-
  cell set defined by `_is_v045_birth_safe_placeable`. Other
  redirection rules (radius-bounded, kind-biased, etc.) reserved
  for v0.46+.
- **Single locked C-arm placebo.** Uniform-neighbor. Other
  controls (rotated-iteration, deterministic-permutation)
  reserved for v0.46+.
- **HAZARD-cell exclusion locked in B/C eligibility.** This is
  intentional and necessary to isolate the spatial-locality
  effect from hazard-placement mortality. Including HAZARD cells
  in the eligible set would conflate "broke spatial locality"
  with "placed newborn on hazard, killing it."
- **Walls inviolate.** WALL cells never modified or selected.
- **Founder placement at tick 0 untouched.** v0.45 intervenes on
  offspring births only, post-tick-50.
- **Pre-50 reproduction byte-identical to v0.44.** The callback
  defers for `tick <= 50`; no `BirthRedirectedByIntervention`
  events emitted pre-50.
- **No biological-realism claim.** Both B (uniform-global
  redirection) and C (uniform-neighbor selection) are abstract
  placement rules.
- **Substrate at h=8 anchor moment is depleted on `food_value`**
  (v0.43R corrected finding) and operative on `respawn_at_tick`
  scheduling (v0.44 finding) but those layers are NOT modified by
  v0.45.
- **No mechanism declaration even on the strongest outcome.**
  Even on BIRTH_LOCALITY_NECESSARY, v0.45 only establishes that
  parent-local placement is necessary at one hazard, on one seed
  band, under one redirection rule. Mechanism specificity (which
  property of parent-local placement) requires v0.46+.
- **Effect-size budget.** Same threshold (0.15) and tolerance
  (0.10) as v0.42 / v0.43R / v0.44. Cross-version comparability
  intentional.

### Reachability — sanity check

All three primary verdicts plus the two halt cells are
arithmetically reachable:

- **BIRTH_LOCALITY_NECESSARY**: requires B share to drop by ≥ 0.15
  AND C share to stay within ±0.10 of A. Both bars independent
  and live; locality-as-spatial-cluster-mechanism would land here.
- **LOCAL_CONTROL_DISRUPTS_DOMINANCE**: requires B AND C to both
  drop by ≥ 0.10 from A. If the system is fragile to any
  uniform-random per-birth selection, this is where it lands.
- **BIRTH_LOCALITY_NOT_NECESSARY**: requires B share to NOT drop
  by ≥ 0.15. If post-50 dominance reconstitutes regardless of
  offspring placement, this is where it lands.
- **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT (halt)**: requires C
  share to rise above A by > 0.10 while B drops. Mechanistically
  unmotivated; halt loud.
- **C_DISRUPTS_WITHOUT_B (halt)**: requires C to drop while B does
  not. The weaker adjacency-preserving control disrupting while
  the stronger global redirection does not is mechanistically
  unmotivated; halt loud.

### Anchor identity

- v0.45 inherits no cross-version artifact-identity anchors against
  prior reducer outputs. It inherits four byte-identity anchors:
  v0.42 A_null + B_kill_leader, v0.43R B_reduce, v0.44 B_delay
  fingerprints (regression guard, H2e).

## Decision rules

### Primary

| `b_passes` | C-direction             | verdict                                              |
|:----------:|-------------------------|------------------------------------------------------|
| True       | `c_passes` (\|c−a\|≤0.10) | **BIRTH_LOCALITY_NECESSARY**                         |
| True       | `c_below_a` (c−a≤−0.10) | **LOCAL_CONTROL_DISRUPTS_DOMINANCE**                 |
| True       | `c_above_a` (c−a>+0.10) | **C_ABOVE_A_UNMODELED_SUBSTRATE_ARTEFACT** (halt)    |
| False      | `c_passes` ∨ `c_above_a`| **BIRTH_LOCALITY_NOT_NECESSARY**                     |
| False      | `c_below_a` (c−a≤−0.10) | **C_DISRUPTS_WITHOUT_B** (halt)                      |

### Auxiliary (independent of primary)

`GLOBAL_REDIRECT_ABLATES_REPRODUCTION` per hazard, fires iff
`b_n_excluded_zero_post50 > 2` at that hazard.

### Secondary (descriptive context only)

`hazard_amplified := abs(delta_b_minus_a_h8) > abs(delta_b_minus_a_h0)`.

### Halt conditions

- **H1 fails** — pre-v0.45 surface mutated, OR v0.42/v0.43R/v0.44
  byte-identity regression fails. Halt; revert.
- **H2a fails** — run count != 48. Halt.
- **H2b fails** — intervention-fire pattern violates locked
  expectations. Halt.
- **H2c fails** — any fired event with `tick <= 50`. Halt.
- **H2d fails** — placement conservation violated (predicate not
  satisfied, C-arm adjacency broken, RNG stream label drift).
  Halt.
- **H2e fails** — sampled byte-identity regression fails. Halt.
- **H3 / H4 fail** — pre-v0.45 contract broken. Halt; revert.
- **C-rises-above-A cell** — substrate artefact unmodeled. Halt
  loud.
- **C-disrupts-without-B cell** — mechanistically unmotivated.
  Halt loud.
- **Substrate-preflight halt** — preflight already executed and
  passed (committed at `b91b4d3`). No additional pre-sweep
  preflight required.

## Out of scope (v0.45)

- Sufficiency testing.
- Mechanism specificity (which property of parent-local placement).
- Hazard generalisation beyond {0, 8}.
- Cross-stream calibration beyond seeds 65..72.
- Founder-placement intervention at tick 0.
- Hazard-relocation interventions.
- Chamber-geometry interventions.
- Pre-50 birth interventions.
- Redirection rules other than uniform-among-eligible.
- C-arm placebos other than uniform-neighbor.
- HedonismPolicy comparisons.
- Mesa migration.
- Edits to existing v0.34..v0.44 reducer surface or pre-v0.45
  arm tuples.
- Re-running v0.42 / v0.43R / v0.44 sweeps (artefact regression
  via H2e only, no full re-sweep).

## Implementation notes

### File-level changes

- **Modified (in `src/`):**
  - `src/hedonism_harness/core/interventions.py` (~250 LOC added):
    extend `InterventionConfig.kind` Literal with two new values;
    add `_is_v045_birth_safe_placeable`,
    `_v045_eligible_global_cells`, `_v045_eligible_neighbor_cells`,
    `make_v045_birth_redirect_callback`. **Existing kind paths
    untouched.**
  - `src/hedonism_harness/core/events.py` (~50 LOC added):
    `BirthRedirectedByIntervention` frozen dataclass + addition to
    `_SIGNAL_NAMES` and `AnyEvent` union.
  - `src/hedonism_harness/core/reproduction.py` (~30 LOC added):
    one new optional parameter on `process_reproduction()` with
    None-preserves-byte-identity contract.
  - `src/hedonism_harness/experiments/fear_hunger_chamber.py` (~30
    LOC added): chamber driver constructs the callback from
    `optional_intervention` when the kind is one of v0.45's two
    new kinds and threads it through to `process_reproduction()`.
  - `src/hedonism_harness/mesa_agents.py` and/or
    `src/hedonism_harness/model.py` (~15 LOC added): propagate the
    callback through the `_attempt_reproduction` call site.
  - `src/hedonism_harness/experiments/comparison_grid.py` (~30 LOC
    added): new constant `V0_45_INTERVENTION_ARMS` (additive).
- **New (in `scripts/`):**
  - `scripts/v0.45_sweep.py` (~80 LOC).
  - `scripts/v0_45_intervention_audit.py` (~750 LOC).
  - (Existing `scripts/v0_45_preflight.py` already committed.)
- **New (in `tests/`):**
  - `tests/test_interventions_v0_45.py` (~350 LOC).
  - `tests/test_world_intervention_hook_v0_45.py` (~180 LOC).
  - `tests/test_v0_45_sweep.py` (~140 LOC).
  - `tests/test_v0_45_intervention_audit.py` (~600 LOC).
  - `tests/test_reproduction_v0_45_callback.py` (~100 LOC) —
    additive-parameter regression test for `process_reproduction()`.
- **Documented:** this pre-reg. Results appended after audit.

### Tests required (locked at pre-reg time)

- **Predicate + helpers:**
  - `_is_v045_birth_safe_placeable` excludes WALL, HAZARD,
    out-of-bounds, occupied; includes EMPTY, FOOD, SAFE.
  - `_v045_eligible_global_cells` returns sorted (x, y) ascending.
  - `_v045_eligible_neighbor_cells` returns parent's N/S/E/W
    filtered, sorted.
  - Determinism: same world state → byte-identical eligible-cell
    list.
- **Callback factory:**
  - For tick <= 50, callback returns
    `find_adjacent_empty_cell(world, parent, occupied)` (defers).
  - For tick > 50 with B kind, callback returns a cell from
    `_v045_eligible_global_cells(...)` selected via the locked
    RNG stream.
  - For tick > 50 with C kind, callback returns a cell from
    `_v045_eligible_neighbor_cells(...)` selected via the same
    stream.
  - Empty eligible set → callback returns None.
  - Same seed + same chamber state + same kind → byte-identical
    redirected cell.
- **Reproduction extension:**
  - Default-None: `process_reproduction()` byte-identical to
    pre-v0.45 (regression).
  - Callback-provided + returns valid cell: child placed at
    callback's cell.
  - Callback-provided + returns None: birth skipped (no charge,
    no child).
  - Callback-provided + returns invalid cell: ??? (recommend
    halt with `ValueError` to surface bugs early).
- **Event class:**
  - `BirthRedirectedByIntervention` is frozen, slotted, hashable,
    serialisable.
  - All fields populated correctly on emission.
  - Distinct from pre-v0.45 event types.
- **World hook (chamber-driver):**
  - Both new kinds emit one `BirthRedirectedByIntervention` per
    post-50 birth with correct fields.
  - No emission for pre-50 births (callback defers).
  - `kind="null"` byte-identical to default-None (regression).
  - v0.42 / v0.43R / v0.44 kinds remain dispatchable + byte-
    identical (regression).
- **Sweep:** locked constants, arm tuple, seeds (65..72),
  hazards ({0, 8}).
- **Audit:** locked thresholds, all H2 halts, primary/secondary/
  auxiliary test arithmetic, three-way verdict + 2 halt cells,
  locked-phrase regression guards, end-to-end synthetic fixture.

### Determinism contract

- All new helpers (predicate, eligible-cell selectors) are pure
  functions of chamber state at call time.
- The callback consumes one new RNG stream
  (`v0_45_birth_position_intervention`); all stochasticity scoped
  there.
- Default-None and `kind="null"` paths byte-identical to pre-v0.42.
- v0.42 / v0.43 / v0.43R / v0.44 kind paths byte-identical when
  re-run on v0.45 branch.

### LOC estimate

- `interventions.py` extension: ~250 LOC.
- `events.py` extension: ~50 LOC.
- `reproduction.py` extension: ~30 LOC (additive parameter).
- `fear_hunger_chamber.py` wiring: ~30 LOC.
- `mesa_agents.py` / `model.py` wiring: ~15 LOC.
- `comparison_grid.py` arm tuple: ~30 LOC.
- Sweep + audit: ~830 LOC.
- 5 test files: ~1,370 LOC.
- This doc: ~1,000 LOC.

Total v0.45: ~3,605 LOC. Tests should bring the suite from 1,494
to ~1,594 (+~100).

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1494 passed, 7 skipped (baseline including
                                v0.43 substrate-finding skip + v0.43R no-op
                                disqualification + v0.44 80 new tests)
uv run python scripts/core_smoke_test.py   ok
uv run python scripts/v0_45_preflight.py   PASS (already executed; commit b91b4d3)
```

(Pre-reg adds no executable code; CI is identical to v0.45-preflight
commit state.)

## Results

**Status:** pending implementation, sweep, and audit. Results
appended after the audit fires (or after a halt, whichever applies).
