# fear_hunger v0.54 — mechanism synthesis for the v0.53 arc (coverage × alignment on the lineage-perception axis)

**Slice:** v0.54
**Type:** **synthesis document, not a sweep.** No reducer, no halt cascade, no locked-phrase pre-registration table, no Results section under fresh data. The document integrates v0.46–v0.53n into a single bounded mechanism reading and **freezes the claim ladder** before any further empirical slicing. v0.54 makes no `src/` changes, runs no new experiments, and does not re-anchor any prior slice's locked verdict. All thirteen v0.53 predecessor verdicts (v0.53b..v0.53n) and the v0.46–v0.52b stack stand as historical contracts.
**Predecessors:** v0.27..v0.33 (aggregate-optimum audit closed by `H6_pool WEAK`), v0.34 (lineage observability MVP; H7 mostly-concentrated), v0.35 (founder-survival timing; `H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY`), v0.36 (`H6 TRAIT-LINKED-FLAT` with `sensor_radius` firing), v0.46–v0.52b (full predecessor stack), v0.53–v0.53b (`BRIDGE_PARTIALLY_GENERALIZES` / `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`), v0.53c (`...AT_TICK_200`), v0.53d (`...UNDER_RELAXED_INFLUX`), v0.53e (`RELAXED_OPPOSITE_SIGN_HALT`), v0.53f (`...UNDER_BASE_METABOLIC_COST_010`), v0.53g (`...UNDER_COMBINED_SE100_BMC010`), v0.53h (`...AT_TIME_HORIZON_400`), v0.53i (`WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`), v0.53j (`...UNDER_FOOD_NEAR1`), v0.53k (`WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`), v0.53l (`WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`), v0.53m (`WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`), v0.53n (`MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A`).

## 1. The arc in one paragraph

The original project question — does late-window birth concentration reflect aggregate optimization at the v0.27 chamber configuration? — was closed by v0.27..v0.33 with `H6_pool WEAK` ("directionally persistent, not mechanistically robust"). Lineage observability was added in v0.34..v0.36, which surfaced an unexpected post-hoc correlation: under the heritability fingerprint (v0.36), `sensor_radius` was the trait most consistently linked to per-lineage outcome differences at the tested chamber configurations. v0.48 measured this directly as a **spatial / foraging bridge** — `is_high_sensor_radius_lineage` (Label A) and `is_high_tick{N}_readiness_fraction_lineage` (Label B) firing under a +0.5 paired_d effect-size rule on three primary observables across a 64-run V0_25 corpus. The v0.53 series probed the bridge mechanism along five axes — geometry (v0.53b/c/i/j), substrate energy / metabolic cost (v0.53d/e/f/g), time horizon (v0.53h), perception scope (v0.53k/l/m), and **alignment** (v0.53n) — converging on a bounded mechanism reading at v0.53n. v0.54 freezes that reading as a claim ladder before any further slicing.

## 2. Claim ladder (frozen for this arc)

**Scope qualifier (applies to every "can claim" entry below):** Within **V0_25 × `widened_food_near1` layout × combined-budget `BodyConfig(starting_energy=100.0, base_metabolic_cost=0.10)` × `n_ticks=400` × `effective_sensor_radius_override=8` × 5-founder population × 64-run V0_25 corpus**, v0.53 can claim:

### Can claim

1. **Under the tested widened/FOOD_NEAR1 envelope, reachability is access-mediated.** The choice of which lineage receives `effective_sensor_radius_override = 8` does not change the reachability run-share at 1/5 coverage (v0.53l C: 61/64; v0.53n D: 61/64 — same exact 61-run cohort across alignment). 5/5 coverage lifts the final 3/64 to 64/64 (v0.53k C / v0.53n E). 0/5 coverage yields 0/64 (v0.53j C). The reachability axis localizes to "is there a boosted lineage at all?" — not to "which lineage is boosted?" at 1/5.
2. **Under the tested envelope, Label A is alignment-mediated.** The trait-indexed bridge fires PRESENT when the boost is aligned with the max-sensor lineage label (v0.53l C: `+4.4 / +4.4 / +3.8`); fires **wrong-sign with near-mirror magnitude** when the boost is trait-opposed (v0.53n D: `−4.4 / −4.4 / −3.3`); dilutes monotonically when coverage broadens with alignment preserved (v0.53m D top-2: `+1.2 / +1.2 / +2.3`); collapses into the ±0.5 deadband when alignment is meaningless (v0.53k C / v0.53n E model-wide: `−0.019 / −0.019 / −0.002`). The lineage label tracks **the boosted lineage**, not the underlying trait, when alignment is varied at fixed coverage.
3. **Under the tested envelope, Label B is readiness / access-success indexed.** Label B fires PRESENT on the boosted lineage in every arm with rescued reachability — `+44.8 / +44.8 / +7.2` (v0.53l C max-only), `+2.1 / +2.1 / +0.7` (v0.53m D top-2), `+35.7 / +35.7 / +6.8` (v0.53n D min-only), `+0.7 / +0.7 / +0.6` (v0.53k C / v0.53n E model-wide). Magnitudes reflect structural-concentration of outcome on the boosted lineage(s); they are not direct biological-strength measures of the underlying trait correlation.
4. **Under the tested envelope, model-wide access homogenizes the original trait bridge.** Universal `effective_sensor_radius_override = 8` (v0.53k C / v0.53n E) removes between-lineage perception heterogeneity by construction; Label A falls into the deadband while Label B retains a small PRESENT signal indexed on early-readiness rather than perception.
5. **Under the tested envelope, min-lineage access flips Label A while preserving reachability and Label B.** Assigning the perception boost to the lowest-sensor founder (v0.53n D) inverts Label A's expected sign without disrupting reachability or Label B firing — the strongest single-slice evidence within the tested envelope that Label A's PRESENT expression in v0.53l/m tracks the boosted-lineage alignment, not raw trait causation.

### Cannot claim

1. **Perception is the only cause.** The `signal += value / distance` gradient (`core/sensors.py:11`), policy gradients, hazard anticipation, food-attraction signal strength, and other secondary channels all share the sensor_radius lever. v0.53 isolates the **information channel** via `effective_sensor_radius_override` but does not separate visibility from gradient strength.
2. **Geometry is solved generally.** v0.53i/j established that the FOOD_NEAR1/FOOD_NEAR2 boundary is sharp at 1-column resolution under the tested envelope; v0.53k/l/m/n added perception coverage and alignment dimensions. The geometry × perception × policy × budget interaction at non-FOOD_NEAR layouts, at other `r` doses, at other `n_ticks` horizons, or under non-V0_25 substrates is not characterized.
3. **Max sensor directly causes success independent of override / access.** v0.53l/m showed Label A firing PRESENT under trait-aligned override; v0.53n showed sign-flip under trait-opposed override with comparable magnitude. The trait correlation in v0.48 / v0.36 was real, but v0.53 does not establish that the trait causes success independently of the access channel under the tested envelope. The trait-mediated reading is not falsified — it is **localized** to alignment dependence.
4. **Survival asymmetry proves metabolic cost.** v0.53n recorded tick-400 living-population run-shares of 0.594 (C max-only), 0.875 (E model-wide), and 0.953 (D min-only). The tentative interpretation — `sensor_radius` correlates with `metabolic_rate` in V0_25's TraitConfig, so max-sensor dominance carries higher aggregate metabolic load — is descriptive and plausible but **not mechanistically established by v0.53**. The survival pattern is a candidate finding for v0.53o-optional diagnostic; v0.54 does not close it.

## 3. The four readings, narrated

### 3.1 Reachability is access-mediated

| arm | coverage | alignment | tick-400 reach |
|---|:-:|:-:|:-:|
| v0.53j C (no override) | 0/5 | — | 0/64 |
| v0.53l C / v0.53n C (max-only) | 1/5 | trait-aligned | 61/64 |
| **v0.53n D (min-only)** | **1/5** | **trait-OPPOSED** | **61/64** |
| v0.53m D (top-2) | 2/5 | trait-aligned | (n/a in v0.53n) |
| v0.53k C / v0.53n E (model-wide) | 5/5 | homogenized | 64/64 |

The 61-run cohort that rescues on v0.53l C is the **identical run-by-run cohort** that rescues on v0.53n D (verified by per-`run_id` audit log cross-reference). The 3/64 runs that fail to rescue at 1/5 coverage fail under both alignment conditions, implying a structural per-run mode (founder death before reproduction, etc.) rather than an alignment-dependent failure. The final 3-run gap to 64/64 closes only at 5/5 coverage, where every founder can independently access food.

**The bounded claim:** under FOOD_NEAR1 × combined-budget × `n_ticks=400`, **the existence of at least one boosted lineage** (not its identity) determines reachability up to a 3-run structural ceiling.

### 3.2 Label A is alignment-mediated

| arm | coverage | alignment | Label A signed_d (events / energy / distance) |
|---|:-:|:-:|:-:|
| v0.53l C (max-only) | 1/5 | trait-aligned | **+4.41 / +4.41 / +3.82** |
| **v0.53n D (min-only)** | **1/5** | **trait-OPPOSED** | **−4.44 / −4.44 / −3.29** |
| v0.53m D (top-2) | 2/5 | trait-aligned | +1.17 / +1.17 / +2.35 |
| v0.53k C / v0.53n E (model-wide) | 5/5 | homogenized | −0.019 / −0.019 / −0.002 |

The v0.53l ↔ v0.53n D pair is a **near-mirror** in magnitude with inverted sign. The trait-indexed label `is_high_sensor_radius_lineage` selects the max-sensor lineage in every run; what changes between v0.53l C and v0.53n D is whether that lineage receives the access boost. When it does, Label A fires PRESENT at `+4.4`; when the boost goes to its antipode (the min-sensor lineage), Label A fires wrong-sign at `−4.4`. The structural symmetry localizes the firing mechanism to **boosted-lineage alignment**, not to the underlying `sensor_radius` value the label uses for selection.

At 2/5 coverage with alignment preserved (v0.53m D top-2), Label A fires PRESENT at `+1.2` — sharper-than-linear decay relative to the 1/5 max-only `+4.4`. The dilution is non-linear because the runner-up is in the non-label pool at the same effective sensor radius as Label A's selected lineage, contracting `delta_mean(label_a)` to ≈ 0.75 × max-only's value with `delta_stdev` not contracting commensurately. At 5/5 (homogenized), the alignment concept is meaningless and Label A is in the deadband by construction.

**The bounded claim:** Label A's PRESENT expression in v0.53l/m **is mediated by alignment between the boosted access channel and the max-sensor lineage label**, not by raw trait causation. Trait-aligned access produces near-mirror sign-flip when alignment is inverted at fixed coverage; the bridge fingerprint is alignment-dependent.

### 3.3 Label B is readiness / access-success indexed

| arm | coverage | alignment | Label B signed_d (events / energy / distance) |
|---|:-:|:-:|:-:|
| v0.53l C (max-only) | 1/5 | trait-aligned | +44.79 / +44.79 / +7.20 |
| **v0.53n D (min-only)** | **1/5** | **trait-OPPOSED** | **+35.72 / +35.72 / +6.80** |
| v0.53m D (top-2) | 2/5 | trait-aligned | +2.10 / +2.10 / +0.70 |
| v0.53k C / v0.53n E (model-wide) | 5/5 | homogenized | +0.70 / +0.70 / +0.59 |

Label B (`is_high_tick400_readiness_fraction_lineage`) indexes the lineage with the highest early-readiness fraction at the measurement window. Under 1/5 coverage Label B selects the lineage that successfully crossed into the food zone, which **is the boosted lineage** in both alignment conditions. Magnitudes are large at 1/5 because the boosted lineage is the sole successful forager (`label_lineage_value` >> `mean(non_label)` because non-label lineages have near-zero food acquisition). At 2/5 the contrast halves; at 5/5 the contrast nearly vanishes (universal access homogenizes readiness too).

The large Label B magnitudes are **structural-concentration channels** — outcome compression onto the boosted lineage(s) — not linear biological-strength measures of any underlying trait correlation. Comparing the `+44.8` of v0.53l C to the `+35.7` of v0.53n D as a biological-strength delta would be a category error.

**The bounded claim:** Label B is a readiness / access-success indicator, expressible wherever any lineage achieves food access regardless of alignment.

### 3.4 Survival asymmetry — an open thread

| arm | coverage | alignment | tick-400 living-population run-share |
|---|:-:|:-:|:-:|
| v0.53l C / v0.53n C (max-only) | 1/5 | trait-aligned | 0.594 |
| v0.53m D (top-2) | 2/5 | trait-aligned | 0.672 |
| v0.53k C / v0.53n E (model-wide) | 5/5 | homogenized | 0.875 |
| **v0.53n D (min-only)** | **1/5** | **trait-OPPOSED** | **0.953** |

Under 1/5 coverage with **trait-opposed** alignment, population survival is highest (`0.953`). Under universal access (5/5 homogenized), survival is `0.875`. Under 1/5 trait-aligned, survival is `0.594`. The asymmetry is large enough to be probably-not-noise.

**The survival asymmetry is descriptive.** A plausible candidate is **trait-package correlation** — potentially involving metabolic rate, movement cost, hazard exposure, reproduction timing, energy transfer mode, or their interaction — but v0.54 does not establish which channel explains the pattern, and the founder Trait vectors / descendant counts / cause-of-death distributions on the v0.53l C vs v0.53n D corpora have not been inspected in this synthesis.

**This thread is not closed by v0.54.** The trait-package distribution per arm, the per-lineage descendant count over time, the cause-of-death distribution (starvation vs injury), the cross-lineage interference modes (e.g., does the boosted lineage starve adjacent lineages by monopolizing food cells?), and the reproduction-rate differential are all candidate diagnostics for v0.53o — **optional**, not required.

## 4. Canonical coverage × alignment matrix

| coverage | alignment | arm origin | reach (tick-400) | Label A signed_d | Label B signed_d | survival | status |
|:-:|:-:|---|:-:|:-:|:-:|:-:|---|
| 0/5 (no override) | — (alignment meaningless) | v0.53j C | 0/64 | NA | NA | 0.000 (extinct) | characterized |
| 1/5 | trait-aligned (max) | v0.53l C / v0.53n C | 61/64 | +4.41 / +4.41 / +3.82 | +44.79 / +44.79 / +7.20 | 0.594 | characterized |
| **1/5** | **trait-opposed (min)** | **v0.53n D** | **61/64** | **−4.44 / −4.44 / −3.29** | **+35.72 / +35.72 / +6.80** | **0.953** | **characterized** |
| 1/5 | random (non-max, non-min) | — | — | — | — | — | **not run** |
| 2/5 | trait-aligned (top-2) | v0.53m D | (cross-slice; reach n/a here) | +1.17 / +1.17 / +2.35 | +2.10 / +2.10 / +0.70 | 0.672 | characterized |
| 2/5 | trait-opposed (bottom-2) | — | — | — | — | — | **not run** |
| 2/5 | random (any other 2-of-5) | — | — | — | — | — | **not run** |
| 3/5 | trait-aligned (top-3) | — | — | — | — | — | **not run** |
| 3/5 | trait-opposed (bottom-3) | — | — | — | — | — | **not run** |
| 4/5 | trait-aligned (top-4) | — | — | — | — | — | **not run** |
| 4/5 | trait-opposed (bottom-4) | — | — | — | — | — | **not run** |
| 5/5 (model-wide) | homogenized (alignment meaningless) | v0.53k C / v0.53n E | 64/64 | −0.019 / −0.019 / −0.002 | +0.70 / +0.70 / +0.59 | 0.875 | characterized |

The matrix maps two axes — coverage (rows by override-targeting count, from 0/5 to 5/5) and alignment (columns by selection rule's relation to Label A's `is_high_sensor_radius_lineage` selector). Cells marked **"not run"** were not sampled by the v0.53 arc and should be read as "no data" rather than "no signal" — interpolation across the matrix is not supported by v0.53. The 2/5 trait-opposed (bottom-2) cell and the random-non-aligned cells at 1/5 and 2/5 are the closest natural extensions if the alignment-mediation reading is to be cross-checked under different selection rules; v0.53o (optional) does not address them and would not need to.

## 5. What v0.54 explicitly does NOT do

- **No fresh-stream calibration.** Every v0.53 verdict stands on the existing v0.42 / v0.43R / v0.44 / v0.45 corpus stream. Cross-stream replication on an independent corpus is the v0.55+ contract; v0.54 does not assert any v0.53 verdict has been elevated to mechanism beyond the alignment-mediation claim ladder above.
- **No per-lineage diagnostic.** The survival asymmetry is logged as a candidate finding; v0.54 does not adjudicate the metabolic-correlation reading vs reproduction-rate-differential vs cross-lineage-interference vs trait-package-pleiotropy. That is v0.53o-optional territory.
- **No `src/` changes.** The v0.53l-tip seams (`per_founder_traits_overrides` + always-consume invariant) are the production interface for any future per-lineage probe; `tests/sha_pins.py` is the canonical SHA register. v0.54 does not modify either.
- **No spec changes.** SPEC §16 (chamber), §27 (tick order), §13.4 (memory), §10.2 (sensor model) all stand. The v0.48 bridge framework's selectors and effect-size rule are not reopened.
- **No mechanism declaration beyond the claim ladder.** §2's can-claim list is the upper bound of what v0.54 asserts. Bare phrases like "perception is the binding cause" or "the bridge is access-mediated" or "trait pleiotropy explains the survival gap" are explicitly out of scope.

## 6. Open framing

### 6.1 v0.53o (OPTIONAL — per-lineage trait-package + dose-response diagnostic)

**v0.53o is optional and should only be opened if the next user-directed question is to explain the survival asymmetry. It is not required to validate the v0.53 mechanism arc or the v0.54 claim ladder.**

**Likely scope if run:** mostly observational; compare max-lineage and min-lineage founder Trait vectors and descendant outcome distributions across v0.53l C and v0.53n D using the existing on-disk corpora. Add a dose-response axis on `r ∈ {6, 7, 8, 10}` at min-lineage scope only if the static comparison shows ambiguity. Do not add new mechanics unless the diagnostic reveals a specific confound.

**Locked precondition:** v0.53o is not authorized without explicit user direction after v0.54 review. Chronus should not treat v0.53o as morally required just because the survival asymmetry is logged here.

### 6.2 v0.55+ (fresh-stream calibration territory)

Any escalation of a v0.46–v0.53n verdict from "consistent with X" to "X mechanism established" requires fresh-stream calibration on an independent corpus (analogous to v0.30..v0.33 on the aggregate-optimum arc). The Tier-1 + Tier-2 + Tier-3 anchor stack used in v0.53 enforces internal determinism, not cross-stream generalization. v0.54 does not start that work; the arc here is closed at the alignment-mediation claim ladder.

### 6.3 Out of scope (not v0.53 / v0.54 territory)

- Mesa-side migration / wrapper changes (long-running parallel arc; see `docs/CORE_ARCHITECTURE.md` and `docs/SPEC.md`).
- Long-horizon-only behaviors (`n_ticks` ≫ 400).
- Non-V0_25 substrate explorations (would re-open the v0.27..v0.33 aggregate-optimum question).
- Reading-A causal-generalization on FOOD_NEAR1 + rescued reachability cells (deferred since v0.49–v0.52b).

## 7. Files / references

### Primary v0.53 slice docs (predecessor stack, twelve verdicts)

- [[docs/experiments/fear_hunger_v0.53b.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_100`
- [[docs/experiments/fear_hunger_v0.53c.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TICK_200`
- [[docs/experiments/fear_hunger_v0.53d.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_RELAXED_INFLUX`
- [[docs/experiments/fear_hunger_v0.53e.md]] — `RELAXED_OPPOSITE_SIGN_HALT`
- [[docs/experiments/fear_hunger_v0.53f.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_BASE_METABOLIC_COST_010`
- [[docs/experiments/fear_hunger_v0.53g.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_COMBINED_SE100_BMC010`
- [[docs/experiments/fear_hunger_v0.53h.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_AT_TIME_HORIZON_400`
- [[docs/experiments/fear_hunger_v0.53i.md]] — `WIDENED_BRIDGE_RESCUED_BY_FOOD_NEAR2`
- [[docs/experiments/fear_hunger_v0.53j.md]] — `WIDENED_BELOW_REACHABILITY_THRESHOLD_UNDER_FOOD_NEAR1`
- [[docs/experiments/fear_hunger_v0.53k.md]] — `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`
- [[docs/experiments/fear_hunger_v0.53l.md]] — `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`
- [[docs/experiments/fear_hunger_v0.53m.md]] — `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`
- [[docs/experiments/fear_hunger_v0.53n.md]] — `MIN_LINEAGE_ACCESS_RESCUES_REACHABILITY_AND_DECOUPLES_LABEL_A`

### Upstream context

- [[docs/experiments/fear_hunger_v0.48.md]] — v0.48 spatial / foraging bridge (Label A + Label B definitions; effect-size rule; tick-50 sub-verdict on V0_25 corpus)
- [[docs/experiments/fear_hunger_v0.36.md]] — v0.36 heritability fingerprint (`sensor_radius` firing as TRAIT-LINKED-FLAT under primary 3-trait set)
- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage observability MVP
- [[docs/experiments/fear_hunger_v0.27.md]] — v0.27 baseline / aggregate-optimum question that v0.27..v0.33 closed

### Implementation seams (carry-forward state, unchanged in v0.54)

- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] — `run_chamber()` with `per_founder_traits_overrides` parameter (v0.53l-tip seam)
- [[src/hedonism_harness/model.py]] — `_spawn_founder` always-consume invariant (v0.53l-tip seam)
- [[tests/sha_pins.py]] — canonical SHA register for mutable experiment-seam files; unchanged from v0.53l-tip
- [[scripts/v0_53l_perception_max_lineage_sensor_radius_8_audit.py]] — v0.53l reducer (canonical max-only path)
- [[scripts/v0_53m_perception_top2_lineage_sensor_radius_8_audit.py]] — v0.53m reducer (top-K helpers shared with v0.53n)
- [[scripts/v0_53n_perception_min_lineage_sensor_radius_8_audit.py]] — v0.53n reducer (bottom-K helpers; alignment-control)

### Spec / architecture (untouched contract docs)

- [[docs/SPEC.md]]
- [[docs/CORE_ARCHITECTURE.md]]

## 8. Watch-outs for future sessions

- **The v0.53 claim ladder in §2 is frozen for purposes of reporting this arc.** Future experiments may extend or revise the broader model — including the v0.48 bridge framework, the Label A/B selectors, the V0_25 corpus shape, or the chamber geometry — but should **not retrofit the v0.53 interpretation**. v0.54 is the historical contract for what v0.53b..v0.53n observed under the tested envelope; downstream slices add to the record rather than rewrite it.
- **The locked phrases on v0.53k/l/m/n stand verbatim.** v0.54's narrative explanations (e.g., "alignment-mediated", "structural-concentration channel") are synthesis-level shorthand; they do not replace the verbatim Results phrases on the individual slice docs.
- **The v0.27 closure stands.** v0.53's mechanism reading is downstream-of-original-goal but legitimate science on a separate question (the v0.48 bridge mechanism). Nothing in v0.54 reopens the v0.27..v0.33 aggregate-optimum verdict.
- **Survival asymmetry is descriptive only in v0.54.** Any further use of the `0.953 / 0.875 / 0.594` numbers as evidence for "the trait costs energy" must come with explicit "consistent with" framing until v0.53o (or fresh-stream replication) establishes the mechanism.
- **Lineage-perception axis sampling is sparse.** Five of nine canonical cells are characterized. Future readers should not interpolate the unmeasured cells without acknowledging the sparse coverage.
- **`per_founder_traits_overrides` propagation contract.** Override Traits are inherited by all descendants via `dataclasses.replace`'s preservation of the override field on child Traits sampled in `process_reproduction`. This is the production-side guarantee that the boosted lineage's access advantage is heritable through the run. If a future slice tests **non-heritable** override (boost only the founder, not descendants), the seam will need extension.

---

**End v0.54.** The v0.53 mechanism arc closes here. Next concrete step is user direction: either (a) v0.53o-optional diagnostic, (b) v0.55+ fresh-stream calibration, (c) Mesa-side migration arc, or (d) a different question entirely.
