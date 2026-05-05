# v0.26 — perception-vs-damage decoupling: was tight's small cull-tax driven by GradientPolicy avoidance?

**Status:** pre-registration; not yet executed.
**Date:** 2026-05-05
**Branch:** `claude/v0.26-perception-vs-damage-decoupling`
**Predecessors:** v0.21 (chamber-asymmetric influx frontier at hazard=8;
food_ladder primary i\*=0.5/tick, tight primary i\*=1.5/tick), v0.22
(narrow hazard sweep on food_ladder at influx=1.0; recycling-as-net-tax
confirmed, food_ladder b>50 monotone non-increasing in hazard:
116/96/92/65), v0.23 (hazard-zero influx frontier on both chambers;
chamber-dependent hazard sign discovered — food_ladder gains ~+30 b>50
per arm when hazards removed, tight loses ~−13), v0.24 (population-
dynamics diagnostic falsified the strict population-governor reading —
late-window populations *rise* at hazard=0 on both chambers, not crash;
substituting mechanism candidate **pool-exhaustion-timing**), v0.25
(hazard × influx sweep — tight has an interior productivity optimum at
h=8 across all influxes; food_ladder is monotone non-increasing in
hazard. Pool-exhaustion-timing on b>50 confirmed with productivity-
ceiling refinement at extreme hazard. **Open question:** was tight's
small cull-tax driven by `GradientPolicy` avoidance routing, or by
chamber geometry alone?).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
(substrate axis).

## Question

v0.25 confirmed that **tight has an interior productivity optimum at
hazard=8** across all influxes — the cull-tax-vs-timing-penalty balance
nets out non-monotonically because tight's cull-tax is small. The v0.25
results doc identified two architectural reasons tight's cull-tax could
be small:

1. **GradientPolicy avoidance routing.** At `hazard_damage > 0`, the
   per-tile damage layer feeds into `sensors.observe` as
   `obs.hazard_signal_*`, which the policy multiplies by `pain_w` to
   produce avoidance pull. Agents are routed *around* the hazard wall.
2. **Chamber geometry alone.** tight's compact spawn-to-food path may
   not require crossing the hazard band at all — the layout itself
   keeps agents out of harm's way regardless of avoidance routing.

These are not mutually exclusive. v0.25 cannot discriminate them
because `hazard_damage` and the avoidance signal are coupled by
construction (`obs.hazard_signal_*` is computed by scanning
`world.hazard_damage`, so when damage=0 the signal is zero and
avoidance is dormant).

**v0.26 decouples damage from avoidance via a `GradientPolicy`-side
seam: a new `hazard_avoidance_weight: float = 1.0` parameter that
multiplies `pain_w` in the policy's net-pull computation
(`pain_w = traits.fear_sensitivity * (1 - traits.risk_tolerance) *
hazard_avoidance_weight`).** Default 1.0 preserves bit-identity for
every prior arm. Setting `hazard_avoidance_weight = 0.0` zeroes the
avoidance pull *while leaving per-tile hazard damage applied to body
physics intact*. This isolates the routing-vs-damage components
cleanly.

The pre-committed 2×2 design (per Reading A — pure policy seam):

| arm | `hazard_damage` | `hazard_avoidance_weight` | meaning |
|---|---:|---:|---|
| coupled    | 8.0 | 1.0 | current behavior; **byte-identical to v0.25 hazard=8 anchor** |
| invisible  | 8.0 | 0.0 | damage applies, no avoidance pull — **substantive new cell** |
| phantom    | 0.0 | 1.0 | weight is non-zero but `hazard_signal_*` is zero (damage=0 zeroes the layer); **byte-identical to v0.25 hazard=0 anchor** |
| no-hazard  | 0.0 | 0.0 | clean substrate baseline; **byte-identical to v0.25 hazard=0 anchor** |

The phantom and no-hazard cells **must** reproduce v0.25 hazard=0
byte-identically. If they don't, the architecture's perception-purely-
damage-derived assumption (Reading A) is wrong, and the v0.23
"hazard-perception caveat" framing was incomplete. This is a
deductive identity under Reading A: at `hazard_damage=0`,
`world.hazard_damage` is zero everywhere, so `obs.hazard_signal_*` is
zero everywhere, so any multiplier produces zero — phantom and
no-hazard cells run identical control flow.

The substantive new cell is **invisible** (damage=8, weight=0). On
tight, this cell answers the open v0.25 question:

- If invisible-tight `total_injury_deaths` is much larger than
  coupled-tight `total_injury_deaths` (which v0.25 reported as 0 across
  all hazards via avoidance routing), then **avoidance was load-bearing
  for tight's small cull-tax**. Without the avoidance signal, agents
  cross the hazard band freely and the tight cull-tax becomes large.
- If invisible-tight b>50 falls toward food_ladder's monotone-decreasing
  shape (i.e., dropping below coupled-tight b>50 by something like the
  v0.25 food_ladder cull-tax magnitude), then the v0.25 "tight has an
  interior optimum at h=8" finding is **avoidance-routing-mediated**, not
  geometry-mediated. The interior optimum vanishes when avoidance is
  removed.
- If invisible-tight b>50 ≈ coupled-tight b>50, then the avoidance
  signal was *not* the load-bearing mechanism — geometry alone keeps
  tight agents out of the hazard band. The v0.25 finding survives even
  without avoidance.

## What this slice tests, and what it does NOT test

### Tests

- **Whether GradientPolicy hazard avoidance is load-bearing for tight's
  small cull-tax** at hazard=8. The invisible-tight cell directly
  answers this.
- **Whether the chamber-geometry-as-buffer reading from v0.23/v0.24
  needs further revision.** food_ladder negative control: if invisible-
  food_ladder behaves substantially differently from coupled-food_ladder
  on b>50, then food_ladder's pre-food band geometry was *not*
  self-sufficient for hazard avoidance — the avoidance signal was
  contributing on food_ladder too. Either outcome is informative.
- **Whether the perception-purely-damage-derived assumption holds.**
  Phantom and no-hazard byte-identity is the deductive halt-condition
  check.
- **Conservation invariants** continue to hold across the new cells
  (H1/H2/H3/H4/H5 from v0.25's invariant pre-reg).

### Does NOT test

- **Long-window stability** at n_ticks > 200. Same window as v0.21+.
- **Pool-size sensitivity.** Pool=1500 throughout.
- **Reproduction efficiency variation.** Transfer mode throughout.
- **Influx grid extension.** v0.26 fixes influx=1.0 (the v0.25 anchor
  cell where the chamber-dependent finding is sharpest). Influx
  extension is a v0.27 candidate.
- **Hazard intensity variation.** v0.26 fixes hazard ∈ {0, 8} (the
  v0.25 endpoint pair). The intermediate-hazard interaction with
  weight is a v0.27 candidate.
- **Intermediate avoidance weights** (e.g., 0.5). The 2×2 binary
  design is the cleanest causal-separation; partial-avoidance
  characterisation is a v0.27 candidate.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec. The
  `hazard_avoidance_weight` parameter only affects `GradientPolicy`;
  `HedonismPolicy` is unchanged.
- **Reading B (separate `world.hazard_perceived` layer).** Out of
  scope. v0.26 is the policy-side seam only.

### Deferred (v0.27+ candidates, conditional on v0.26 outcome)

- **Influx-extension sweep** at the 2×2 grid: v0.27 might replicate
  v0.26 across influx ∈ {0.5, 1.0, 1.5} if the invisible cells reveal
  influx-dependent dynamics worth mapping.
- **Intermediate-hazard sweep** at weight=0: v0.27 might run the
  invisible 2×2 across hazard ∈ {4, 8, 12} to map how cull-tax
  scales with damage when avoidance is off.
- **Reading B (substrate seam):** if v0.26 shows invisible food_ladder
  is meaningfully different from coupled food_ladder, the
  `world.hazard_perceived` layer separation may be needed to isolate
  perception-without-damage (phantom-distinct).

## Conservation framing — unchanged from v0.20/v0.21/v0.22/v0.23/v0.25

v0.26 introduces no new conservation contract. The six-flow
PARENT_TRANSFER_POOL_GAP bookkeeping is preserved exactly; the only
new variable is `hazard_avoidance_weight` (policy-side, no ledger
impact). The H4 conservation invariant
(`parent_energy_transferred_to_child + pool_out_child_startup ==
total_births × offspring_start_energy`) holds across the v0.26 grid by
construction.

## Mechanism

The seam is local to two files:

1. **`src/hedonism_harness/policies/gradient_policy.py`**: add a
   `hazard_avoidance_weight: float = 1.0` parameter to
   `GradientPolicy.__init__`. Multiply `pain_w` by it in `decide()`.
   Default 1.0 produces bit-identical behavior to v0.25.
2. **`src/hedonism_harness/experiments/comparison_grid.py`**: add
   `Arm.hazard_avoidance_weight: float | None = None`. Mirrors the
   v0.22 `Arm.hazard_damage` pattern.
3. **`src/hedonism_harness/experiments/fear_hunger_chamber.py`**: add
   `hazard_avoidance_weight: float | None = None` to `run_chamber`.
   When set, wrap the caller-supplied `policy_factory` so each
   constructed `GradientPolicy` instance receives the configured
   weight (other policy types are passed through untouched). `None`
   preserves v0.7..v0.25 bit-identity.

No core changes (`world.py`, `sensors.py`, `body.py`, `model.py`).
No new event types. No ledger changes. The v0.20/v0.21/v0.22/v0.23/v0.25
telemetry surface is sufficient for v0.26 analysis.

### Determinism — anchors

V0_26_ARMS contains explicit byte-identity anchors against the v0.25
sweep artifacts on disk:

| chamber | hazard | weight | anchor source | b>50 anchor |
|---|---:|---:|---|---:|
| tight       | 8 | 1.0 | v0.25 transfer-1500-hzd8-influx-1.0  | 116 |
| tight       | 0 | 1.0 | v0.25 transfer-1500-hzd0-influx-1.0  | 100 |
| tight       | 0 | 0.0 | v0.25 transfer-1500-hzd0-influx-1.0  | 100 |
| food_ladder | 8 | 1.0 | v0.25 transfer-1500-hzd8-influx-1.0  |  92 |
| food_ladder | 0 | 1.0 | v0.25 transfer-1500-hzd0-influx-1.0  | 116 |
| food_ladder | 0 | 0.0 | v0.25 transfer-1500-hzd0-influx-1.0  | 116 |

Six anchors total: coupled and (phantom, no-hazard) on both chambers.
The two new cells are (tight, 8, 0.0) and (food_ladder, 8, 0.0) —
**invisible hazard on each chamber**.

Failure of any anchor is a halt condition. Phantom-vs-no-hazard
identity is itself a halt condition (deductive under Reading A).

## Arms

Four arms × two chambers × eight seeds = **64 runs**. Smaller than
v0.21/v0.22/v0.23/v0.25 because the question is sharply defined and
the 2×2 grid plus the negative-control chamber covers it.

| arm | hazard | weight | label | role |
|---|---:|---:|---|---|
| A | 8.0 | 1.0 | hzd8-avd1.0  | coupled / default; v0.25 hzd8 anchor |
| B | 8.0 | 0.0 | hzd8-avd0.0  | invisible hazard; **substantive new cell** |
| C | 0.0 | 1.0 | hzd0-avd1.0  | phantom hazard; v0.25 hzd0 anchor |
| D | 0.0 | 0.0 | hzd0-avd0.0  | no hazard; v0.25 hzd0 anchor |

Substrate per arm: `energy_cost=15`, `energy_threshold=50`,
`offspring_start_energy=30`, `food_respawn_cooldown=50`,
`energy_pool_initial=1500`, `ambient_influx_rate=1.0`,
`child_funding_mode=PARENT_TRANSFER_POOL_GAP`, reflex-baseline policy
(GradientPolicy, no scalar memory), `unbounded_mutation=True`,
`n_ticks=200`, `n_founders=5`. Same 8 seeds (1..8) as v0.21/v0.22/v0.23/v0.25.

### Telemetry to watch

Aggregate observables per cell, summed across 8 seeds:

- **Productivity headline.** `total_births`, `births_after_tick_50`
  (b>50), `seeds_with_survivors`.
- **Death cause distribution.** `total_starvation_deaths`,
  `total_injury_deaths`. **Decisive observable for invisible-tight:
  if avoidance was load-bearing, invisible-tight injury_deaths >>
  coupled-tight injury_deaths (which was 0 in v0.25).**
- **Hazard exposure.** `total_hazard_entries`. At weight=0 with
  damage>0, agents enter hazards freely; entries count is the
  routing-side observable.
- **Pool ledger.** `pool_min_observed`, `pool_end`,
  `pool_in_ambient_influx` (H1 invariant), `pool_out_respawn`,
  `pool_out_child_startup`, `pool_in_death_residual`. At hazard=8
  with weight=0, `pool_in_death_residual` should rise materially
  because more agents die in hazards (recycling channel reactivated).
- **Block telemetry.** `total_pool_birth_denied`,
  `total_pool_respawn_denied`,
  `total_births_blocked_by_parent_energy` (expected 0).
- **Conservation invariant.**
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.

## Pre-registered hypotheses

Two-tier structure consistent with v0.15..v0.25: **strong-form** for
mechanism + invariants, **cautious-form** for the substantive
mechanism predictions, plus **determinism** for the byte-identity
anchors.

### Strong form (mechanism + invariants)

- **H1.** `pool_in_ambient_influx == ambient_influx_rate ×
  sum(executed_ticks_per_seed)` per arm per chamber. v0.20
  conservation contract.
- **H2.** v0.20 H4 invariant holds at every v0.26 cell:
  `parent_energy_transferred_to_child + pool_out_child_startup ==
  total_births × offspring_start_energy`.
- **H3.** `reproduction_heat_loss == 0` at every v0.26 cell.
- **H4.** `births_blocked_by_parent_energy == 0` at every v0.26 cell.
- **H5.** `total_injury_deaths == 0` at every `hazard_damage = 0` cell
  (arms C and D on both chambers). Direct hard pin.

### Cautious form (perception-vs-damage decoupling predictions)

- **H6 (invisible-tight injury_deaths >> coupled-tight injury_deaths).**
  At (tight, hazard=8, weight=0), `total_injury_deaths` is at least
  20× the (tight, hazard=8, weight=1) value — i.e., at least 20× zero,
  which is operationally "any non-zero". Concretely we pre-commit:
  **invisible-tight `total_injury_deaths` ≥ 5 (across 8 seeds)**.
  v0.25 reported coupled-tight injury_deaths = 0 across all hazards
  via avoidance. **Strong-cautious; falsification weight: high.** A
  null result here (invisible-tight injury_deaths still 0 or near-0)
  would mean avoidance is not load-bearing for tight's hazard
  exposure — geometry alone routes agents around the wall, and the
  v0.25 interior-optimum-at-h=8 finding survives unchanged.
- **H7 (invisible-tight b>50 < coupled-tight b>50).** At (tight,
  hazard=8), removing avoidance reduces b>50 by at least 10% relative
  to the coupled cell (i.e., invisible-tight b>50 ≤ 105 vs coupled
  anchor 116). **Cautious; the substantive headline.** A null result
  (invisible-tight b>50 ≈ coupled-tight b>50) would mean the v0.25
  interior optimum was *not* avoidance-mediated — tight's geometry
  alone keeps the cull-tax low, and the v0.25 finding is robust.
- **H8 (invisible-tight b>50 falls toward food_ladder's hazard=8 b>50).**
  Strong reading of H7: invisible-tight b>50 falls into the range
  spanned by food_ladder hazard=8 b>50 (= 92 from v0.25). The
  prediction is invisible-tight b>50 ∈ [80, 100]. **Cautious;
  conditional on H7 firing.** A failure of H8 with H7 holding
  qualitatively means avoidance contributes a partial component but
  geometry is also load-bearing — the chamber asymmetry has
  multiple sources.
- **H9 (food_ladder negative control: invisible-food_ladder ≈
  coupled-food_ladder).** At food_ladder hazard=8, weight=0 vs
  weight=1, `total_injury_deaths` is within 50% (i.e., not a
  qualitative shift). Pre-food band geometry should already route
  food_ladder agents through hazards regardless of avoidance, so
  removing avoidance shouldn't change the cull-tax much. **Cautious;
  if H9 fails, the chamber-geometry-as-buffer reading from
  v0.23/v0.24 needs revision.** v0.25 reported coupled-food_ladder
  hazard=8 injury_deaths ≈ 16 across 8 seeds; the H9 band is
  [8, 24].
- **H10 (food_ladder negative control on b>50).** At food_ladder
  hazard=8, invisible-food_ladder b>50 is within 10% of coupled-
  food_ladder b>50 (= 92 from v0.25). **Cautious; corroborating H9.**

### Determinism

- **H11 (six anchor cells reproduce v0.25 byte-identically).** Listed
  in the anchor table above. All sixteen aggregate columns
  (`total_births`, `births_after_tick_50`, `total_food_events`,
  `total_food_respawn_events`, `total_pool_respawn_denied`,
  `total_pool_birth_denied`, `total_starvation_deaths`,
  `total_injury_deaths`, `total_hazard_entries`, `pool_out_respawn`,
  `pool_out_child_startup`, `pool_in_death_residual`, `pool_min`,
  `pool_end`, `parent_energy_transferred_to_child`,
  `reproduction_heat_loss`) match the v0.25 hzd8 / hzd0 anchors at
  influx=1.0 on each chamber. Halt condition.
- **H12 (phantom ≡ no-hazard byte-identically).** Arms C and D produce
  identical aggregates on each chamber. Deductive identity under
  Reading A. Halt condition.
- **H13 (V0_19/20/21/22/23/25_ARMS unchanged).** No prior arm tuple
  or core surface modified. Verified by re-running existing test
  suites; halt condition.
- **H14 (`GradientPolicy(hazard_avoidance_weight=1.0)` is a no-op).**
  Direct test: a fresh `GradientPolicy()` and `GradientPolicy(
  hazard_avoidance_weight=1.0)` produce identical decisions on a
  fixed observation/context. Halt condition.

## Decision rules

- **H6 + H7 + H8 fire (and H9/H10 hold).** **Avoidance routing was
  load-bearing for tight's small cull-tax.** Tight's interior
  productivity optimum at h=8 was an avoidance-mediated effect; the
  v0.25 finding survives but is sharpened — the chamber-asymmetric
  hazard sign is fundamentally about whether the policy can route
  around hazards, and tight's geometry only "buffered" because
  avoidance was active. Headline finding for v0.26.
- **H6 fires + H7 fails (injury deaths rise but b>50 unchanged).**
  Surprising: removing avoidance lets agents enter hazards, they
  die more, but the population sustains b>50 anyway. Likely
  population dynamics (more births compensate for more deaths) —
  v0.27 candidate: population-trajectory diagnostic on the invisible
  cells using the v0.24 library.
- **H6 fails (invisible-tight injury_deaths still 0 or near-0).**
  **Avoidance was NOT load-bearing for tight; geometry alone routes
  agents around the wall.** v0.25's interior-optimum-at-h=8 finding
  is robust against avoidance ablation. v0.27 candidate: investigate
  what specific tight geometry feature produces the avoidance-
  independent routing (path length, dead-end structure).
- **H7 fires but H8 fails.** Avoidance contributes partially; tight's
  cull-tax has multiple components. v0.27 might decompose by
  sweeping intermediate weights ∈ {0.25, 0.5, 0.75} to map the
  partial-ablation curve.
- **H9 fails (invisible-food_ladder differs substantially from
  coupled).** Pre-food band geometry was NOT self-sufficient — the
  avoidance signal was contributing on food_ladder too. The
  chamber-geometry-as-buffer reading from v0.23 / v0.24 needs
  revision. v0.27 candidate: re-examine food_ladder layout for
  routing-side dependencies.
- **H1/H2/H3/H4/H5 invariants fail.** Halt; v0.26 results
  uninterpretable.
- **H11 fails.** Wiring defect in the new seam. Halt and audit.
- **H12 fails (phantom ≠ no-hazard).** Reading A is wrong — perception
  is NOT purely damage-derived. The architecture has additional
  perception coupling we haven't located. Halt and audit; reconsider
  Reading B (substrate seam).
- **H13 fails.** Prior arm tuples broken; halt.
- **H14 fails.** GradientPolicy seam defect: weight=1.0 must be a
  no-op. Halt and audit.

## Out of scope (v0.26)

- **Influx grid extension.** v0.27+ candidate.
- **Hazard intensity variation.** v0.27+ candidate.
- **Intermediate avoidance weights.** v0.27+ candidate.
- **Reading B (substrate-side perception layer).** Out of scope; v0.26
  is the policy-side seam only.
- **Long-window stability.** v0.27+ candidate.
- **Pool-size sweep.** Held at 1500.
- **HedonismPolicy comparisons.** Quarantined per v0.2 spec.

## Implementation notes

### File-level changes

- **Modify:** [[src/hedonism_harness/policies/gradient_policy.py]] —
  add `hazard_avoidance_weight: float = 1.0` to `__init__`. Validate
  `>= 0.0`. Multiply `pain_w` by `self.hazard_avoidance_weight` in
  `decide()`. ~10 LOC.
- **Modify:** [[src/hedonism_harness/experiments/comparison_grid.py]]
  — add `Arm.hazard_avoidance_weight: float | None = None`. Append
  `V0_26_ARMS` tuple of 4 `Arm` instances per the table above.
  Thread the new field through `_run_one_arm_seed` to `run_chamber`.
  ~80 LOC.
- **Modify:** [[src/hedonism_harness/experiments/fear_hunger_chamber.py]]
  — add `hazard_avoidance_weight: float | None = None` to
  `run_chamber`. When non-None, wrap the policy_factory so each
  constructed `GradientPolicy` instance gets the weight set. `None`
  preserves v0.7..v0.25 bit-identity (factory unchanged). ~15 LOC.
- **New:** [[scripts/v0.26_sweep.py]] — sweep driver mirroring
  `scripts/v0.25_sweep.py`; runs both chambers over `V0_26_ARMS`.
  Headline table preserves the v0.25 column structure; adds a
  `weight` column to make the 2×2 grid scannable. ~95 LOC.
- **New:** `tests/test_comparison_grid_v0_26.py` — V0_26_ARMS shape;
  per-arm (hazard, weight) pinning; substrate-economics-fixed;
  prior arms (V0_19/20/21/22/23/25) unchanged; phantom-≡-no-hazard
  smoke test (one-seed run); H14 GradientPolicy default-1.0-is-no-op
  unit test. ~210 LOC.
- **Modify:** [[tests/test_gradient_policy.py]] — add a
  `hazard_avoidance_weight=0` unit test confirming pain_w → 0 on a
  fixed observation. ~30 LOC.
- **No changes** to `core/world.py`, `core/sensors.py`,
  `core/body.py`, `core/model.py`,
  `experiments/population_dynamics.py`. The seam is policy-only.
- **Documented:** this file (`docs/experiments/fear_hunger_v0.26.md`);
  results appended after the sweep.

### Determinism contract

- `V0_19/20/21/22/23/25_ARMS` continue to produce identical sweep
  outputs after v0.26 changes (no prior surface modified;
  `hazard_avoidance_weight=None` on existing arms means the
  factory wrapping is skipped, which means the policy is constructed
  exactly as before).
- Default `GradientPolicy()` is bit-identical to
  `GradientPolicy(hazard_avoidance_weight=1.0)` (H14).
- The six anchor cells in `V0_26_ARMS` reproduce v0.25 aggregates
  byte-identically (H11, H12).

### Wall time estimate

64 runs × 200 ticks. v0.21 took 22s for 80 runs, v0.23 took 30s for
80 runs, v0.25 took 58.5s for 192 runs. v0.26 estimated 20–25s.

### LOC estimate

- `policies/gradient_policy.py`: +10 LOC.
- `experiments/comparison_grid.py`: +80 LOC (V0_26_ARMS + Arm field).
- `experiments/fear_hunger_chamber.py`: +15 LOC (factory wrapping).
- `scripts/v0.26_sweep.py`: ~95 LOC.
- New tests: ~210 LOC.
- `tests/test_gradient_policy.py`: +30 LOC.
- This doc: ~440 LOC.

Total v0.26 implementation: ~880 LOC. Comparable to prior slices.
The seam is small (~25 LOC of production change); the bulk of the
work is V0_26_ARMS + tests + driver + doc.

## References

- [[docs/experiments/fear_hunger_v0.25.md]] — v0.25 results;
  pool-exhaustion-timing on b>50 confirmed; tight interior optimum at
  h=8. Source of the open avoidance-vs-geometry question.
- [[docs/experiments/fear_hunger_v0.24.md]] — v0.24 population-
  governor falsification; pool-exhaustion-timing mechanism.
- [[docs/experiments/fear_hunger_v0.23.md]] — v0.23 chamber-
  dependent hazard sign; the §"Hazard-perception caveat" framing
  that v0.26 addresses directly.
- [[docs/experiments/fear_hunger_v0.22.md]] — v0.22 recycling-as-net-
  tax on food_ladder.
- [[src/hedonism_harness/policies/gradient_policy.py]] — the policy
  receiving the new `hazard_avoidance_weight` seam.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework" —
  the substrate axis.
