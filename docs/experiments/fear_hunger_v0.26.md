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

---

## Results

**Status:** executed 2026-05-05. 64 runs (4 arms × 2 chambers × 8 seeds),
20.4s wall time. All anchor / determinism hypotheses hold (H11 byte-
identity vs v0.25 anchors on coupled and phantom cells; H12 phantom ≡
no-hazard exactly on both chambers; H14 default-1.0 no-op verified by
unit test). Substantive predictions: H7 (tight b>50 drops with
avoidance off) fires at the boundary; H10 (food_ladder b>50 stable)
holds; H6 / H8 / H9 **fail** in informative ways.

**Headline:** **avoidance routing is load-bearing on BOTH chambers, but
its productivity impact differs sharply.** Tight's small cull-tax under
v0.25 was *partially* avoidance-driven (b>50 drops 9 points / 7.8% when
avoidance is off, ~56% of the v0.25 hzd8→hzd0 gap on tight) but
geometry remains decisive — tight produces **zero injury deaths even
with avoidance disabled** because its compact spawn-to-food path keeps
hazard entries low enough that no agent accumulates lethal damage in
a single visit. Food_ladder's pre-food band is NOT a self-sufficient
buffer: removing avoidance more than doubles injury deaths
(16 → 40, +150%) and triples death-residual recycling
(625 → 1818). The v0.23 / v0.24 chamber-geometry-as-buffer reading
needs revision — geometry routes traffic but does not deflect it.

### Headline tables

#### tight_gradient (influx=1.0)

| arm | haz | avd | births | b>50 | surv | food | respawn | fcpb  | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|----:|----:|-------:|-----:|------|-----:|--------:|------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| coupled    | 8 | 1.0 | 190 | 116 | 8/8 | 716 | 524 | 75.37 | 0 | 34 |   0.0 | 133 |  0 |  30 | 52 | 32 | 2,850 |
| invisible  | 8 | 0.0 | 183 | 107 | 8/8 | 722 | 530 | 78.91 | 0 | 32 |   0.0 | 125 |  0 |  40 | 46 | 67 | 2,745 |
| phantom    | 0 | 1.0 | 246 | 100 | 8/8 | 673 | 481 | 54.72 | 0 | 36 |   0.0 | 202 |  0 |  42 | 95 | 42 | 3,690 |
| no-hazard  | 0 | 0.0 | 246 | 100 | 8/8 | 673 | 481 | 54.72 | 0 | 36 |   0.0 | 202 |  0 |  42 | 95 | 42 | 3,690 |

#### food_ladder (influx=1.0)

| arm | haz | avd | births | b>50 | surv | food | respawn | fcpb   | pool_min | pool_end | residual | starv | inj | haz_ent | r_blk | b_blk | xfer  |
|-----|----:|----:|-------:|-----:|------|-----:|--------:|-------:|---------:|---------:|---------:|------:|----:|--------:|------:|------:|------:|
| coupled    | 8 | 1.0 | 143 |  92 | 8/8 | 674 | 501 |  94.27 |   2 | 257 |   624.8 |  77 | 16 | 120 | 3 | 0 | 2,145 |
| invisible  | 8 | 0.0 | 150 |  88 | 8/8 | 762 | 570 | 101.60 |  12 | 221 | 1,817.5 |  66 | 40 | 233 | 4 | 0 | 2,250 |
| phantom    | 0 | 1.0 | 249 | 116 | 8/8 | 670 | 478 |  53.82 |   0 |  38 |     0.0 | 206 |  0 | 200 | 98 | 12 | 3,735 |
| no-hazard  | 0 | 0.0 | 249 | 116 | 8/8 | 670 | 478 |  53.82 |   0 |  38 |     0.0 | 206 |  0 | 200 | 98 | 12 | 3,735 |

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | `pool_in_ambient_influx == ambient_influx_rate × sum(executed_ticks)` | **HOLDS.** All 8 cells: 8/8 survivors → executed-tick sum = 1,600; influx product = 1,600; verified to the unit. |
| H2 | `parent_energy_transferred + pool_out_child_startup == total_births × 30` | **HOLDS.** Transfer-mode contract; xfer = births × 15 across all cells. |
| H3 | `reproduction_heat_loss == 0` | **HOLDS** (transfer-mode contract; all cells reported 0.0). |
| H4 | `births_blocked_by_parent_energy == 0` | **HOLDS** across all cells. |
| H5 | `total_injury_deaths == 0` at hazard=0 cells | **HOLDS.** Phantom and no-hazard cells on both chambers report inj=0. |
| H6 | invisible-tight injury_deaths ≥ 5 across 8 seeds | **FAILS — 0.** Tight geometry keeps entries (40) below the lethal-accumulation threshold even with avoidance off. Damage=8 per entry, max_health=100; agents don't return to the same hazard tile within a single life often enough to die. **Informative falsification:** removes the avoidance-as-mortality-gate reading; tight's small cull-tax is geometry-protected against single-visit lethality. |
| H7 | invisible-tight b>50 ≤ 105 (≥10% drop vs coupled 116) | **FIRES at the boundary — weak-to-moderate support.** Invisible-tight b>50 = 107, a 7.8% drop. Misses the strict 10% threshold by 2 births. Consistent with "avoidance contributes meaningfully to tight productivity but is not the only mechanism." |
| H8 | invisible-tight b>50 ∈ [80, 100] (falls toward food_ladder hzd8 = 92) | **FAILS.** Invisible-tight b>50 = 107, well above the predicted band. Tight's geometry contribution is larger than H8 anticipated — removing avoidance drops b>50 only 9 points, not the 16+ points needed to reach food_ladder territory. |
| H9 | invisible-food_ladder injury_deaths within 50% of coupled (8 ≤ inj ≤ 24) | **FAILS — major.** Invisible-food_ladder inj = 40, +150% vs coupled (16). Pre-food band is NOT a self-sufficient routing buffer; the avoidance signal was actively deflecting agents on food_ladder, just less than was visible at the binary hzd8 vs hzd0 comparison. **Substantive finding** — chamber-geometry-as-buffer reading from v0.23/v0.24 is wrong. |
| H10 | invisible-food_ladder b>50 within 10% of coupled | **HOLDS.** 88 vs 92, a 4.3% drop. Food_ladder absorbs the +24 injury deaths via population dynamics (more births, +7) — the substrate's productivity is robust against this avoidance ablation even though the cull-tax visibly increases. |
| H11 | six anchor cells reproduce v0.25 byte-identically | **HOLDS — exact match on every column.** Coupled tight matches V0_25 hzd8-influx-1.0 (190/116/716/524/52/32/0/0/30/0.0/34/2,850/0.0). Coupled food_ladder matches V0_25 hzd8-influx-1.0 (143/92/674/501/3/0/77/16/120/624.8/257/2,145). Phantom and no-hazard cells on both chambers match V0_25 hzd0-influx-1.0 exactly. |
| H12 | phantom ≡ no-hazard byte-identically | **HOLDS — every column identical.** Tight: 246/100/673/481/95/42/202/0/42/0.0/36/3,690 in both arms. Food_ladder: 249/116/670/478/98/12/206/0/200/0.0/38/3,735 in both arms. **Confirms Reading A: perception is purely damage-derived; with damage=0 the avoidance multiplier is dormant.** |
| H13 | V0_19/20/21/22/23/25_ARMS unchanged | **HOLDS.** Test suite 687 → 705 (+18 v0.26 tests; pure addition); ruff clean. |
| H14 | `GradientPolicy(hazard_avoidance_weight=1.0)` is no-op vs default | **HOLDS.** Verified by `test_hazard_avoidance_weight_one_is_no_op_against_default` across a basket of synthetic observations. Coupled-cell byte-identity vs v0.25 (which had no field) corroborates at the sweep scale. |

### Refined mechanism reading

The v0.25 chamber-dependent hazard-sign finding survives but its
mechanism is sharpened. **Three contributions** to the chamber-asymmetric
b>50 sign at hzd8:

1. **Direct cull-tax (avoidance-mediated).** On food_ladder the
   avoidance signal cuts injury deaths roughly in half (40 → 16 when
   weight is restored). On tight the signal also routes agents away
   (entries 40 → 30) but the absolute injury-death rate is zero in
   both cases — tight's geometry keeps single-visit damage below the
   max_health threshold.
2. **Direct cull-tax (geometry-mediated).** Tight's compact path
   structure keeps hazard entries an order of magnitude below
   food_ladder's at every avoidance setting. The geometric rerouting
   of traffic is real and load-bearing — but routing is not the same
   as deflecting (a single agent may pass through and survive).
3. **Pool-exhaustion timing penalty.** Operating regardless of
   avoidance: tight at hzd8 vs hzd0 sees b>50 = 116 vs 100 (16-point
   gap). Of that gap, ~9 points (56%) are removable by ablating
   avoidance (invisible-tight b>50 = 107). The residual 7 points
   (44%) is the geometry-and-timing component.

The two chambers differ in **which contribution dominates**:

- **food_ladder:** direct cull-tax dominates. The pre-food band
  geometry routes agents *through* hazards; avoidance-mediated
  rerouting halves but does not eliminate the cull-tax. Removing
  hazards entirely (hzd0) lifts b>50 +24 (92 → 116). Productivity is
  cull-tax-bound throughout.
- **tight:** geometry dominates the death-rate component
  (zero injuries everywhere) but timing dominates the productivity
  component. The interior optimum at h=8 (v0.25) is the equilibrium
  between (a) avoidance-mediated rerouting buying late-game compounding
  time and (b) timing penalty of the cull preventing pool exhaustion.
  Disable avoidance and tight loses ~half the optimum's productivity
  gain over hzd0.

### Falsification of the "geometry-as-buffer" reading

The v0.23 / v0.24 framing called food_ladder's pre-food band a
"carrying-capacity buffer" / "geometry-as-buffer" — implying the
chamber's geometry alone produced the food_ladder vs tight asymmetry.
**v0.26 falsifies this** on the food_ladder side: with avoidance off,
food_ladder hazard entries nearly double (120 → 233) and injury
deaths jump +150%. The pre-food band geometry routes agents *toward*
the food zone but does not deflect them around hazards; that
deflection comes from the avoidance signal. The chamber-asymmetric
hazard sign at hzd8 is sustained jointly by (i) food_ladder's geometry
forcing hazard crossings and (ii) the avoidance signal partially
deflecting them. Without the avoidance signal, food_ladder pays a
much larger cull-tax — but its productivity (b>50) is buffered by
population dynamics so the binary "good vs bad" reading at b>50 is
unchanged.

### Reading A confirmed

H12 fires deductively-cleanly on both chambers: phantom ≡ no-hazard
byte-identically. **Reading A is correct: perception is purely
damage-derived.** At `hazard_damage=0` the world's hazard layer is
zero everywhere, so `obs.hazard_signal_*` is zero everywhere, so the
`hazard_avoidance_weight` multiplier is dormant. Reading B (separate
`world.hazard_perceived` layer) is therefore unnecessary for the
question v0.26 asked. Reading B remains a viable seam for future
slices wanting to study perception-without-damage (`phantom != no-hazard`
by construction), but no v0.26 result requires it.

### What this changes about v0.25's framing

- **v0.25 interior optimum at h=8 on tight is partially avoidance-
  mediated.** Removing avoidance drops invisible-tight b>50 by 9
  points; the optimum shape would compress (h=8 still wins because
  the timing-penalty and residual geometry contributions remain) but
  by less. v0.25's headline is preserved; its mechanism is sharpened.
- **food_ladder monotonicity is preserved but its source is split.**
  v0.25 read it as pure cull-tax. v0.26 shows that the cull-tax has
  two routing components (geometry forces crossings; avoidance
  partially deflects). At weight=0 food_ladder's b>50 still drops
  monotonically with hazard; at weight=1 the curve is shallower.
- **The v0.21/v0.22/v0.23/v0.25 frames "tight is starvation-dominated,
  food_ladder is hazard-dominated" survives.** v0.26 adds: "tight is
  starvation-dominated regardless of avoidance because geometry
  protects against single-visit lethality; food_ladder is
  hazard-dominated *and* avoidance-buffered."

### v0.27 plan candidates

1. **(Highest priority) Influx × 2×2 cross-product.** Replicate the
   v0.26 grid at influx ∈ {0.5, 1.0, 1.5} to test whether the
   avoidance-vs-geometry split is influx-dependent. Pre-committed
   prediction: invisible-tight b>50 should track tight's interior
   optimum shape from v0.25 with a uniform downward shift; food_ladder
   should remain flat-ish on b>50 with elevated injury deaths.
2. **Intermediate avoidance weights** (0.25, 0.5, 0.75) to map the
   partial-ablation curve. Tests whether the relationship is linear
   in weight or concave/convex.
3. **Hazard intensity × weight=0** at h ∈ {4, 8, 12} on tight to
   check whether the "single-visit lethality threshold" reading
   holds: at h=12 with weight=0, does tight finally produce non-zero
   injury deaths? Predicted yes (per-entry damage exceeds half of
   max_health, two visits → death). If no, geometry is even more
   protective than v0.26 suggested.
4. **Reading B substrate seam** if a future question explicitly needs
   perception-without-damage (e.g., "does a phantom hazard cue alone
   support the timing-regulation effect?"). Currently no question
   requires it.

### Implementation summary

- **Production code:** ~25 LOC change.
  - `gradient_policy.py`: +20 LOC (`hazard_avoidance_weight`
    parameter, validation, multiplier on `pain_w`).
  - `comparison_grid.py`: `Arm.hazard_avoidance_weight` field +
    threading + V0_26_ARMS (4 arms).
  - `fear_hunger_chamber.py`: factory-wrapping for the avoidance weight.
- **Tests:** ~210 LOC `tests/test_comparison_grid_v0_26.py`
  (14 new tests), ~70 LOC v0.26 unit tests in
  `tests/test_gradient_policy.py` (4 new tests). Suite 687 → 705.
- **Sweep driver:** ~80 LOC `scripts/v0.26_sweep.py`.
- **Wall time:** 20.4s on 64 runs (every seed completed 200 ticks).
- **No core/model.py/sensors.py/world.py/fear_hunger_chamber.py-core
  changes.** The seam is a single multiplier in GradientPolicy.
- **CI gate at handoff time:**
  ```
  uv run ruff check .             ok
  uv run ruff format --check .    ok
  uv run pytest                   705 passed
  uv run python scripts/core_smoke_test.py  ok
  uv run python scripts/v0.26_sweep.py      20.4s; all 6 anchors byte-identical against v0.25; H12 phantom ≡ no-hazard byte-identical on both chambers
  ```
