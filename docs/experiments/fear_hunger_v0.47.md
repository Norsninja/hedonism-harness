# fear_hunger v0.47 — founder-trait predictivity for tick-50 readiness

**Slice:** v0.47
**Type:** post-hoc reducer (decomposition over the modern A_null corpus, NOT intervention)
**Predecessors:** v0.36 (founder-trait heritability decomposition over the v0.34 corpus, `sensor_radius` fired as aligned-flat under the b50/winner label), v0.46 (`READINESS_PREDICTS_DOMINANCE` on the modern A_null corpus — readiness is a strong predictor of post-50 dominance), v0.42 / v0.43R / v0.44 / v0.45 (intervention slices that produced the modern A_null corpus).
**Question being asked (locked):** Are founder traits at tick 0 predictive of which lineage carries the highest tick-50 reproduction-readiness *fraction* on the modern A_null corpus?

v0.46 established that the eventual post-50 dominant lineage is already differentially advantaged at tick 50 along reproductive-momentum and reproduction-readiness axes (paired_d = +1.136 and +0.810; mean energy borderline at +0.452). v0.46 explicitly did not isolate WHY one lineage carries higher readiness than the others — that gap split into two live causal candidates: (a) heritable founder-trait advantage; (b) trajectory-dependent path advantage (founder spatial position, food-cluster proximity, etc.). v0.47 tests candidate (a) only. Candidate (b) is the natural v0.48 direction, contingent on v0.47's verdict.

The slice is the modern-corpus analogue of v0.36's `trait_replay.py`, retargeted from the b50 dominance label to v0.46's readiness label. The 3 primary traits and their expected signs are pre-committed below; trait-fishing protection follows the v0.36 pattern (small motivated subset, expected signs, opposite-sign halt, secondary metrics descriptive only).

## Conservation framing — unchanged from v0.46

- **No `src/` modifications.** v0.47 is a pure post-hoc reducer using `setup_observer` + `tick_observer` + the `AgentBorn` blinker signal (all already available). It does NOT modify any chamber / population / policy / event module.
- **No new sweep arms.** Corpus is the modern A_null only (same 64-run set as v0.46).
- **No modifications to v0.34 / v0.35 / v0.36 / v0.42..v0.45 / v0.46 reducer or audit scripts.** v0.36's `trait_replay.py` remains byte-identical to its merged form. v0.47 copy-locals only the helpers it actually needs (Cohen's d formula, founder-trait extraction pattern); no `importlib` cross-script imports of v0.36.
- **Reducer is fully self-contained.** Reads no `runs/` artifacts; deterministic re-execution under each version's locked V0_25 + A_null arm config; cross-version consistency verified by re-anchoring derived `a_share_h8` against each version's published value within 1e-3.

## Corpus (locked, same as v0.46)

| version | seeds | hazards | arm | runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | A_null only | 16 |
| v0.43R | 49..56 | {0, 8} | A_null only | 16 |
| v0.44 | 57..64 | {0, 8} | A_null only | 16 |
| v0.45 | 65..72 | {0, 8} | A_null only | 16 |
| **total** | | | | **64** |

Seed bands disjoint across versions; no run-level overlap. All runs share the V0_25 anchor (GradientPolicy + auto_reproduction=True + TraitConfig(unbounded_mutation=True), tight_gradient layout, 5 founders, 200 ticks, food_respawn_cooldown=50, ambient_influx_rate=1.0, transfer-pool funding, energy_pool_initial=1500). A_null arm = `InterventionConfig(kind=KIND_NULL)`, byte-identical to `optional_intervention=None` (verified each version by H2e regression).

## Founder-trait extraction (locked)

Per run, at `setup_observer` time (before the first `model.step()`), walk `model.agents` and record `(lineage_id → founder_traits)` for every founder. Founders are the 5 agents constructed via the chamber driver's setup; their `Traits` dataclass values are the **locked unmutated initial draws** from the chamber's per-arm `TraitConfig`. Descendants' traits are NOT consulted by v0.47 (this is *founder*-trait readiness, not lineage-mean trait readiness).

Per `core/traits.py`:
- `reproduction_drive: float` (line 44)
- `metabolic_rate: float` (line 52)
- `sensor_radius: int` (line 51) — coerced to float for paired_d arithmetic.

## Primary readiness label (locked, fires verdict)

Per run, at `model.tick_count == 50`:

```
high_tick50_readiness_fraction_lineage = argmax_lineage(tick50_above_threshold_fraction)
  tiebreak 1: highest tick50_above_threshold_fraction (the metric itself)
  tiebreak 2: highest tick50_above_threshold_count
  tiebreak 3: lowest lineage_id
```

Where `tick50_above_threshold_fraction` is identical to v0.46's locked observable (per-lineage fraction of living agents at tick 50 with `energy ≥ reproduction_config.energy_threshold AND age ≥ reproduction_config.min_age`).

Lineages with zero living agents at tick 50 yield NaN fraction and are excluded from the argmax pool. If only one lineage has a non-NaN fraction in a given run, no paired comparison is possible and the run drops from every primary observable's pool — see "NaN handling".

## Secondary readiness label (locked, descriptive only — cannot fire verdict)

Per run, at `model.tick_count == 50`:

```
high_tick50_readiness_count_lineage = argmax_lineage(tick50_above_threshold_count)
  tiebreak 1: highest tick50_above_threshold_count (the metric itself)
  tiebreak 2: highest tick50_above_threshold_fraction
  tiebreak 3: lowest lineage_id
```

Where `tick50_above_threshold_count` = number of living agents in the lineage at tick 50 satisfying the reproduction-readiness predicate. This is the **size-weighted** version of the primary label; a 10-agent lineage with 4 ready agents (count=4, fraction=0.4) beats a 1-agent lineage with 1 ready agent (count=1, fraction=1.0) under the count label.

The fraction-label / count-label split mirrors per-capita vs. absolute-count reasoning. The primary verdict is fraction-based per your design lock; the count-based traits paired_d is reported descriptively to expose any divergence between the two readings.

## Primary observables (locked, 3 traits with expected signs)

Each is extracted from the founder agent of each lineage at tick 0 (locked, unmutated). Per-trait, per-run paired delta is computed using the **fraction label** for the verdict-firing path.

| # | trait | expected sign | mechanistic prior |
|---|---|:-:|---|
| 1 | `reproduction_drive` | **+** | Higher drive → reproduces more readily when ready → momentum → above-threshold descendants accumulate. |
| 2 | `metabolic_rate` | **−** | Lower metabolism → less per-tick energy decay → more agents pass the energy threshold at tick 50 → higher fraction. |
| 3 | `sensor_radius` | **+** | Wider sensors → better food localisation → more food acquired → higher tick-50 energy → higher above-threshold fraction. (Sign net of `sensor_radius_metabolic_cost` per `core/body.py`; pre-committed positive on the prior that foraging gain dominates the per-radius metabolism cost.) |

**v0.36 comparison note.** v0.36 used the same expected sign for `metabolic_rate` (`−`), but targeted winner / non-winner founder traits on the older v0.34 corpus. v0.47 retargets the modern A_null corpus and the tick-50 readiness-fraction label. Therefore v0.47 should be read as a new-corpus / new-label decomposition, not as a direct replication of v0.36.

## Effect-size rule (locked, matches v0.46)

For each primary trait `T`:

```
per_run_delta_T = founder_T_value(primary_label_lineage) - mean(founder_T_values(non_primary_label_lineages))
paired_d_T      = mean(per_run_delta_T) / stdev(per_run_delta_T, ddof=1)
```

(One-sample Cohen's d on the paired delta vector across runs.) Only runs where the primary label is well-defined AND ≥ 1 non-primary-label lineage exists contribute to the pool.

**Decision rule:**
- `paired_d_T * sign_T ≥ +0.5` → trait `T` **fires in expected direction**.
- `paired_d_T * sign_T ≤ −0.5` → trait `T` **fires in WRONG direction** → halt cell.
- `−0.5 < paired_d_T * sign_T < +0.5` → trait `T` does **not** fire.

(Mathematically: for `metabolic_rate` with sign `−`, paired_d ≤ −0.5 fires; paired_d ≥ +0.5 wrong-sign halts.) Threshold and ddof match v0.46.

## Re-anchor (locked, cross-version only)

For v0.42 / v0.44 / v0.45 only, compute:

```
a_share_h8(version) = mean over (8 A_null runs at h=8) of:
    max_lineage(b50_count) / sum_lineages(b50_count)
```

Compare to hardcoded references (0.652 / 0.878 / 0.818) extracted from each merged Results document. Halt-loud (`CORPUS_REDERIVE_DRIFT_HALT`) on `|drift| > 1e-3`.

v0.43R compute and print informationally; no halt-gate (Results halted as non-citable per SUBSTRATE_PREFLIGHT_HALT_2; no published reference exists).

Same protocol as v0.46. Inherits the cross-version-pool sanity check; layer-2 own-corpus byte-identity against v0.46's gitignored CSV is intentionally NOT done (would require pre-running v0.46, fragile). Any RNG/config drift that corrupts `tick50_above_threshold_fraction` would also corrupt `b50_count` and thus `a_share_h8` — layer-1 catches the same class of drift.

## NaN handling (locked, matches v0.46)

A lineage with 0 living agents at tick 50 contributes NaN to `tick50_above_threshold_fraction` and `0` to `tick50_above_threshold_count`. Such lineages are excluded from the fraction-label argmax pool. For the count-label argmax, they remain `count = 0` unless all lineages are zero-living, which halts/drops as no comparison possible.

If a run has 0 or 1 lineages with non-NaN fraction values, no paired comparison is possible for the primary fraction label and the run drops from every primary observable's pool with the count reported in the audit (`n_runs_dropped_no_pair`).

## Verdicts (locked, 3-way + 2 halts)

The verdict is determined exclusively by the **fraction label** (primary). The count-label paired_d values are reported descriptively but cannot fire or halt the verdict.

| condition | verdict | locked phrase (verbatim) |
|---|---|---|
| ≥ 2/3 primary traits fire in expected direction (and 0/3 fire wrong) | `READINESS_TRAITS_PREDICT_READINESS` | "Founder traits at tick 0 predict tick-50 readiness on the modern A_null corpus." |
| exactly 1/3 fires in expected direction (and 0/3 fire wrong) | `READINESS_TRAITS_PARTIALLY_PREDICTIVE` | "Founder traits at tick 0 are partially predictive of tick-50 readiness on the modern A_null corpus; only one of three primary traits clears the locked threshold." |
| 0/3 fire (and 0/3 fire wrong) | `READINESS_TRAITS_NOT_PREDICTIVE` | "Founder traits at tick 0 do not predict tick-50 readiness on the modern A_null corpus; none of the three primary traits clear the locked threshold." |
| any primary trait fires `paired_d * sign` ≤ −0.5 | `READINESS_TRAITS_OPPOSITE_SIGN_HALT` | "Halt: a primary trait shows a wrong-direction signal vs. its locked expected sign on the modern A_null corpus; the founder-trait readiness candidate is incompatible with the locked sign priors." |
| any of v0.42 / v0.44 / v0.45's re-derived A_null h=8 share drifts > 1e-3 | `CORPUS_REDERIVE_DRIFT_HALT` | "Halt: A_null re-anchor drifted from the published Results value for v0.NN; v0.47's deterministic re-execution does not reproduce the published metric within 1e-3." |

The `READINESS_TRAITS_PREDICT_READINESS` phrase is **correlational, not causal**: it does not claim founder traits *cause* readiness, only that the high-readiness-fraction lineage's founder is already differentially situated along ≥ 2 of 3 pre-committed trait axes. Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.47 does not perform one.

## Cautious framing (per CLAUDE.md)

- "Founder traits predict tick-50 readiness" — NOT "founder traits cause readiness".
- "On the modern A_null corpus" — NOT a chamber-config-independent claim.
- "Differentially situated at tick 0 along ≥ 2 of 3 axes" — descriptive of the joint distribution, not a mechanism claim.
- v0.47 explicitly does **not** rule out: pre-50 spatial sorting, founder-position advantage, topology-mediated energy access ticks 0..50. These remain live candidates for v0.48 regardless of v0.47's verdict.
- v0.47 does **not** test whether trait-readiness predicts the eventual b50 dominant lineage. That alignment is the v0.46 → v0.47 chain conclusion (readiness predicts dominance per v0.46; founder traits predict readiness per v0.47, conditionally on this slice's verdict). The chained inference is *not* run; the readiness → dominance link is v0.46's contribution.

## Secondary descriptive (cannot fire verdict)

Reported in `runs/v0.47-readiness-traits/audit_summary.csv` for transparency; not used in the decision rule.

1. **Fraction-label paired_d for each of the 3 primary traits** (this IS the primary, but the same delta vector's diagnostic stats are reported here for stability inspection):
   - `delta_mean_T`, `delta_stdev_T`, `delta_min_T`, `delta_max_T` for `T ∈ {reproduction_drive, metabolic_rate, sensor_radius}`.
   - n_runs contributing per trait.

2. **Count-label paired_d for each of the 3 primary traits** (descriptive, cannot fire verdict).
   - paired_d_count_T per trait.
   - delta diagnostic stats per trait.

3. **Fraction / count agreement rate**:
   - Per run: boolean (`high_tick50_readiness_fraction_lineage == high_tick50_readiness_count_lineage`).
   - Aggregate: fraction of well-defined runs where the labels match.

A high agreement rate (> 0.9 say) means the per-capita and absolute-count framings converge; a low rate signals that lineage size is doing real work in the count label that the fraction label normalises out.

## Outputs (locked)

```
runs/v0.47-readiness-traits/per_run_per_lineage.csv
  columns: version, seed, hazard, run_id, lineage_id,
           founder_reproduction_drive, founder_metabolic_rate, founder_sensor_radius,
           tick50_above_threshold_fraction, tick50_above_threshold_count,
           tick50_living_count, b50_count,
           is_high_tick50_readiness_fraction_lineage,
           is_high_tick50_readiness_count_lineage

runs/v0.47-readiness-traits/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor       : per (version, h=8) re-derived a_share_h8 + reference + drift_abs
    - paired_d       : per primary trait under fraction label (paired_d, n_runs, fires_expected, fires_wrong, delta_mean, delta_stdev, delta_min, delta_max)
    - paired_d_count : per primary trait under count label (descriptive; same fields)
    - agreement      : fraction/count label agreement rate, n_runs_well_defined
    - verdict        : locked verdict + locked phrase

runs/v0.47-readiness-traits/audit_log.txt
  human-readable echo, including locked phrase fired verbatim.
```

## Implementation plan (locked)

1. Fresh script `scripts/v0_47_founder_trait_readiness_audit.py`. Underscore filename matches v0.46 convention. CLI: `uv run python scripts/v0_47_founder_trait_readiness_audit.py [--out-dir runs/v0.47-readiness-traits]`.
2. Per (version, seed, hazard) tuple, build the same V0_25 + A_null arm config v0.46 used (`V0_4N_INTERVENTION_ARMS[A_null at hazard]`).
3. Run `run_chamber(...)` once per tuple with two observers:
   - **`setup_observer`**: registers an `AgentBorn` blinker listener (records `agent_id → birth_tick, lineage_id`); walks `model.agents` and captures founders' `Traits` per `lineage_id` into the run's capture; captures `reproduction_config.energy_threshold` and `reproduction_config.min_age` for the readiness predicate.
   - **`tick_observer`**: fires when `model.tick_count == 50`, snapshots living agents `(agent_id, lineage_id, energy, age)`.
4. Per (run, lineage): aggregate `tick50_above_threshold_fraction` + `tick50_above_threshold_count` (re-using v0.46's predicate); compute `b50_count` from end-of-run birth-tick-by-agent.
5. Per run: assign primary fraction-label and secondary count-label per the locked tiebreak rules.
6. Per primary trait: compute paired_d under fraction label (PRIMARY) AND under count label (descriptive). Pool deltas across all 64 runs; NaN-aware.
7. Compute fraction/count agreement rate.
8. Re-anchor: for v0.42 / v0.44 / v0.45 only, derive `a_share_h8` and compare to hardcoded references (0.652 / 0.878 / 0.818); halt on |drift| > 1e-3. v0.43R derive and print informationally.
9. Evaluate verdict per the locked decision rule (fraction-label paired_d only); print + write the locked phrase verbatim.

Wall time: ~5–10 minutes for 64 A_null re-executions (matches v0.46).

## Test list (locked, per v0.45 7-point review pattern)

`tests/test_v0_47_founder_trait_readiness_audit.py`:

1. `test_setup_observer_captures_founder_traits_per_lineage` — run `run_chamber` once with v0.47's setup_observer; assert that exactly 5 founders are captured, that each lineage_id 0..4 has a founder traits dict containing all three primary trait names, and that the trait values fall within `TraitConfig`'s declared ranges.
2. `test_fraction_label_argmax_with_3tier_tiebreak` — synthetic per-lineage capture with two lineages tied on fraction (both 0.5) but different counts (3 vs. 5); assert the count=5 lineage wins. Then construct a 3-way tie on (fraction, count); assert lowest lineage_id wins.
3. `test_count_label_tiebreak_is_count_then_fraction_then_id` — symmetric synthetic case for the secondary count label.
4. `test_paired_d_uses_fraction_label_for_verdict` — synthetic capture where fraction-label paired_d = +0.6 for trait T1 but count-label paired_d = -0.6 for the same trait; assert verdict path uses fraction value (no halt).
5. `test_metabolic_rate_sign_inversion_fires_correctly` — synthetic delta vector for `metabolic_rate` with paired_d = -0.6; assert this fires in expected direction (sign convention).
6. `test_metabolic_rate_wrong_sign_halts` — paired_d for metabolic_rate = +0.6; assert halt cell (positive value but expected sign is negative → wrong-sign).
7. `test_verdict_2_of_3_fires_predicts` — synthetic d-values respecting signs; ≥ 2/3 fire → `READINESS_TRAITS_PREDICT_READINESS`.
8. `test_verdict_1_of_3_fires_partial` — exactly 1/3 fires → PARTIAL.
9. `test_verdict_0_of_3_fires_not_predictive` — 0/3 fire → NOT_PREDICTIVE.
10. `test_verdict_wrong_sign_halt_overrides_fires` — synthetic case where 2 fire but 1 wrong-sign halts → halt cell wins.
11. `test_reanchor_drift_halt` — synthetic per-lineage rows yielding a derived a_share_h8 that drifts > 1e-3 from the hardcoded reference; assert `CORPUS_REDERIVE_DRIFT_HALT` raised.
12. `test_corpus_includes_modern_a_null_only` — assert `SEEDS_BY_VERSION` matches v0.46 exactly; assert reducer rejects any non-A_null arm.
13. `test_fraction_count_agreement_rate_well_defined` — synthetic capture with 4 well-defined runs out of 5 (one with all NaN); 3 of 4 well-defined runs have matching labels; assert agreement rate = 3/4 = 0.75 and `n_runs_well_defined = 4`.
14. `test_descendant_traits_not_consulted` — synthetic capture where founder traits and a descendant's mutated traits differ for the same lineage; assert the reducer's reported founder trait value matches the founder's stored trait, not the descendant's.

## Watch-outs (for future-Chronus)

- **Founder-trait extraction must happen before `model.step()` runs.** The `setup_observer` is called by `run_chamber` after model construction but before the first step; `model.agents` already contains the 5 founders at this point, with their unmutated initial trait draws. Capturing later (e.g., at tick_50 observer time) would risk reading mutated descendants if any founder died and was excluded from the iterable.
- **`sensor_radius` is integer.** Coerce to `float` in the paired_d arithmetic; mean of integer deltas as float division. Test #1 covers this implicitly.
- **`metabolic_rate` sign continuity with v0.36, but different corpus + label.** v0.36 also locked `metabolic_rate` as `−` against winner / non-winner founder traits on the v0.34 corpus. v0.47 retargets the modern A_null corpus and the readiness-fraction label. Future readers: this is a new-corpus / new-label decomposition, not a direct replication of v0.36; the sign convention happens to coincide.
- **Re-anchor reference values are hardcoded** (0.652 / 0.878 / 0.818). v0.43R has no published value; logged informationally. If a future correction to a prior version's Results changes those numbers, this slice's pre-reg becomes drift-positive and must be amended.
- **Pre-50 reproduction byte-identity** through v0.47 is preserved by construction: v0.47 makes no `src/` change.
- **NaN runs with only 1 lineage living at tick 50 drop from the pool.** Should not occur on the V0_25 anchor (which sustains all 5 founders' lineages with at least some descendants by tick 50 in every observed run), but reported in `n_runs_dropped_no_pair` if it ever fires.
- **The fraction/count agreement rate is a sanity check, not a verdict input.** A low rate signals that the per-capita and absolute-count framings disagree; a high rate confirms label robustness. Either way, the verdict is fraction-only per the design lock.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.47.md` (this file; Results section appended after reducer run)
- `scripts/v0_47_founder_trait_readiness_audit.py`
- `tests/test_v0_47_founder_trait_readiness_audit.py`

No other files modified.

## Results

*(Appended after reducer run on the modern A_null corpus.)*
