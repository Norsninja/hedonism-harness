# fear_hunger v0.46 — tick-50 readiness decomposition

**Slice:** v0.46
**Type:** post-hoc reducer (decomposition, NOT intervention)
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34 (lineage MVP), v0.35 (eventual-top survival framework), v0.36 (trait-heritability decomposition with fishing protection), v0.42 (leader-kill), v0.43R (density-redistribution), v0.44 (respawn-flow), v0.45 (birth-locality).
**Question being asked (locked):** Is the eventual post-50 dominant lineage already advantaged at tick 50 by reproduction readiness, energy state, or pre-50 reproductive momentum?

The substrate-causal arc (v0.42..v0.45) ruled out four post-tick-50 mechanism layers as *necessary* for the observed late-window dominance share at h=8 (leader removal, density compaction, respawn flow, post-50 offspring placement). v0.45 Results explicitly named pre-50 spatial sorting, founder-position advantage, **trait-linked reproduction readiness**, and topology-mediated energy access ticks 0..50 as the live causal candidates. v0.46 is the **first decomposition slice over the modern intervention corpus** addressing the readiness / energy / momentum subset of those candidates.

## Pre-implementation correction (2026-05-07, before any reducer code)

After reading v0.35's `lineage_survival_replay.py`, the four merged Results documents, and `src/hedonism_harness/model.py`'s per-tick step ordering, three locked items above were corrected before any data was generated. All corrections are dated and recorded here for the historical record (per CLAUDE.md "pre-reg stands as the historical record"). No data has been seen yet — this is a pre-data design fix.

1. **Eventual-dominance label** changed from `argmax(living_count_at_tick_200)` to `argmax(b50_count)` (lineage with the most agents born after tick 50; tiebreak min `lineage_id`). Reason: this is what v0.35's `compute_eventual_top_lineage` (lineage_survival_replay.py:222–244) actually returns and what each prior intervention audit's `post_intervention_top_lineage_b50_share` is computed against. Aligning v0.46's dominance label with the cross-version b50 metric makes the re-anchor structural rather than coincidental.

2. **Re-anchor protocol** changed: v0.43R is excluded from the hardcoded reference set because v0.43R's audit was halted as non-citable per SUBSTRATE_PREFLIGHT_HALT_2 — its merged Results does not publish an `a_share_h8` value. v0.43R A_null runs are still included in the corpus (16 runs) and v0.46 still computes their `a_share_h8` for the audit log; the value just does not gate the verdict via halt. v0.42 / v0.44 / v0.45 published `a_share_h8` values are hardcoded as references with drift tolerance 1e-3.

3. **Tick-50 state-capture path** changed from "events.jsonl arithmetic" to "in-simulation `tick_observer` snapshot during deterministic re-execution under each version's locked V0_25 + A_null arm config". Reason: model.py's per-tick step ordering (action → metabolism → birth-queue → tick_count++; observer fires post-step) introduces an off-by-one between founder ages (50 metabolism cycles) and non-founder ages (49 − birth_tick cycles), and a similar asymmetry in the energy formula. Reconstructing this from events.jsonl with arithmetic is correct in principle but fragile in practice. The `tick_observer` path captures `(energy, age, x, y)` per living agent at exactly `model.tick_count == 50` — exact by construction, no arithmetic. This is the same pattern v0.45's preflight used (script `scripts/v0_45_preflight.py`).

   The reducer becomes "deterministic re-execution + in-memory observation", which qualifies as a post-hoc reducer per CLAUDE.md's lesson "feasibility probes / decomposition reads must use `_run_one_arm_seed` or operate on already-written events.jsonl" — the `_run_one_arm_seed`-equivalent path is explicitly endorsed. No `src/` modification; no new sweep arms; uses each version's existing locked seed band + A_null arm definition (already encoded in `V0_4N_INTERVENTION_ARMS` and the per-version sweep scripts). The on-disk `runs/` corpus is NOT consumed by this reducer — the per-(version, seed, hazard) execution is byte-equivalent to the merged sweep's A_null arm.

   Side benefits: the reducer can run in CI without pre-regenerating sweeps; copy-local helpers from v0.35's replay are no longer necessary (agent_lifetimes.csv is also not consumed). The end-of-run state (used for `eventual_top_lineage_id` and re-anchor) is captured by a final-tick `setup_observer`-equivalent snapshot of `model.agents` after the last `model.step()`.

All other locked items (3 primary observables, expected signs, paired_d formula, verdict structure, locked phrases, conservation framing, secondary metrics, output paths) are unchanged. Test list is updated below to reflect the new state-capture path.

## Conservation framing — unchanged from v0.45

- **No `src/` modifications.** v0.46 is a pure post-hoc consumer of on-disk `events.jsonl`. The `process_reproduction()` keyword-only `birth_redirect_callback` parameter introduced in v0.45 is irrelevant: v0.46 reduces only A_null arms (no callback ever constructed; default-None path).
- **No new sweep.** Corpus is the 64 A_null runs from v0.42 / v0.43R / v0.44 / v0.45's existing sweep scripts. Re-running those sweeps locally is a prerequisite (the `runs/` tree is gitignored) but is not part of v0.46.
- **No modifications to prior reducer scripts.** v0.34's `lineage_replay.py`, v0.35's `lineage_survival_replay.py`, v0.36's `trait_replay.py`, and the four intervention audits remain byte-identical to their merged forms. v0.46's reducer copy-locals any helpers it needs from v0.35 rather than importing.

## Corpus (locked)

| version | seeds | hazards | arms used | runs |
|---|---|---|---|---|
| v0.42 | 41..48 | {0, 8} | A_null only | 16 |
| v0.43R | 49..56 | {0, 8} | A_null only | 16 |
| v0.44 | 57..64 | {0, 8} | A_null only | 16 |
| v0.45 | 65..72 | {0, 8} | A_null only | 16 |
| **total** | | | | **64** |

Seed bands are disjoint across versions; no run-level overlap. All four sweeps share the V0_25 anchor (GradientPolicy + auto_reproduction=True + TraitConfig(unbounded_mutation=True), tight_gradient layout, 5 founders, 200 ticks, food_respawn_cooldown=50, ambient_influx_rate=1.0, transfer-pool funding, energy_pool_initial=1500, hazard_avoidance_weight from V0_25). A_null arm = `InterventionConfig(kind=KIND_NULL)`, byte-identical to `optional_intervention=None` (verified each version by H2e regression).

**Excluded:** all B / C / treatment arms across the four versions. v0.34's 96-run lineage corpus (different anchor / different seeds / different sweep date — keeping it out preserves cross-version comparability of the four-version A_null pool).

## Eventual-dominance label (locked)

For each run:

```
eventual_top_lineage_id = argmax_lineage(b50_count)
  where b50_count = number of agents in lineage with birth_tick_normalized > 50
  ties broken by min(lineage_id)
```

Aligns with v0.35's `compute_eventual_top_lineage` (lineage_survival_replay.py:222–244) and v0.34's `top_lineage_id` (lineage_replay.py:485) so the re-anchor against each prior version's audit-emitted `a_share_h8` is structural, not coincidental.

Reconstructed from `agent_lifetimes.csv` (the same sidecar v0.34/v0.35 reduce over) by counting agents whose `birth_tick_normalized > 50` per lineage. Founder agents (`birth_tick is None` → `birth_tick_normalized = 0`) never contribute to b50_count. Runs with `total_b50 == 0` (no post-50 births at all) yield `eventual_top_lineage_id = None` and contribute NaN to all primary observables — see "NaN handling".

## Primary observables (locked, 3, with expected signs)

Each is computed **per (run, lineage) at tick 50**, then aggregated per-run by comparing the eventual top lineage's value to the mean of the non-top lineages' values in the same run.

| # | name | definition (per lineage at tick 50) | expected sign | candidate from v0.45 caveat |
|---|---|---|---|---|
| 1 | `pre50_reproductive_momentum_count` | cumulative `AgentBorn` events with tick ≤ 50 by `lineage_id` | **+** | trait-linked reproduction readiness / pre-50 momentum |
| 2 | `tick50_above_threshold_fraction` | fraction of living lineage agents with `energy ≥ reproduction_config.energy_threshold AND age ≥ min_age` | **+** | reproduction readiness |
| 3 | `tick50_mean_energy` | mean `energy` across living lineage agents (NaN if no living agents → run dropped from observable's pool, see "NaN handling") | **+** | energy state |

**NaN handling.** A lineage with zero living agents at tick 50 contributes a `pre50_reproductive_momentum_count` (it may have produced births and then extincted — count is well-defined) but contributes NaN for `tick50_above_threshold_fraction` and `tick50_mean_energy`. Per-run paired delta (top minus mean-non-top) is computed only when (a) the run has `total_b50 ≥ 1` (i.e., `eventual_top_lineage_id is not None`) AND (b) both top-lineage and ≥ 1 non-top lineage have non-NaN values for the observable. Runs failing either gate are dropped from that observable's pool with the count reported in the audit.

## Effect-size rule (locked)

For each primary observable:

```
per_run_delta_i = top_lineage_value_i − mean(non_top_lineage_values_i)
paired_d = mean(per_run_delta) / stdev(per_run_delta, ddof=1)
```

(One-sample Cohen's d on the paired delta vector across runs.)

**Decision rule:**
- `paired_d ≥ +0.5` → observable **fires in expected direction**.
- `paired_d ≤ −0.5` → observable **fires in WRONG direction** → halt cell (see verdicts).
- `−0.5 < paired_d < +0.5` → observable does **not** fire.

No p-values, no FDR. Multiple-comparison protection is the small pre-committed primary set of size 3 (per v0.36 fishing-protection pattern). Stdev uses Bessel's correction (ddof=1).

## Re-anchor (locked)

Each predecessor version's audit emits a pooled A_null top-lineage `b50_share` at h=8 — the same metric v0.34's `top_lineage_b50_share` and v0.42..v0.45's `post_intervention_top_lineage_b50_share` use. v0.46 must re-derive that share from each version's on-disk A_null `agent_lifetimes.csv` files and assert agreement against the published reference value. Halt-loud on drift (`CORPUS_REDERIVE_DRIFT_HALT`).

Re-derivation protocol (locked):

```
a_share_h8(version) = mean over (8 A_null runs at h=8) of:
    max_lineage(b50_count) / sum_lineages(b50_count)
  where b50_count = number of agents in lineage with birth_tick_normalized > 50
  runs with total_b50 == 0 contribute NaN and are excluded from the mean
```

Identical formula to v0.34's `top_lineage_b50_share` and the per-version audit's `post_intervention_top_lineage_b50_share`. Hardcoded reference values (extracted from each merged Results document at pre-reg time):

| version | published `a_share_h8` | source |
|---|---|---|
| v0.42 | **0.652** | `docs/experiments/fear_hunger_v0.42.md` line 817 (Results §"Verdict — `MECHANISM_NOT_NECESSARY` fires") |
| v0.43R | **NOT PUBLISHED** | Results halted as non-citable per SUBSTRATE_PREFLIGHT_HALT_2; A_null runs are still on-disk and clean, but no published anchor exists. **v0.43R is excluded from the re-anchor halt** — its A_null h=8 share is computed and printed for the audit log, but does not gate the verdict. |
| v0.44 | **0.878** | `docs/experiments/fear_hunger_v0.44.md` line 1184 (Results §"Per-arm-per-hazard"; bolded) |
| v0.45 | **0.818** | `docs/experiments/fear_hunger_v0.45.md` line 1318 (Results) |

Drift tolerance: `|v0.46_derived - published| > 1e-3` halts. The published values are reported to 3 decimals so 1e-3 is the published precision; tighter tolerance would be spurious.

## Verdicts (locked, 3-way + 2 halts)

| condition | verdict | locked phrase (verbatim) |
|---|---|---|
| ≥ 2/3 primaries fire in expected direction (and 0/3 fire wrong) | `READINESS_PREDICTS_DOMINANCE` | "Tick-50 readiness predicts post-50 dominance on the modern A_null corpus." |
| exactly 1/3 fires (and 0/3 fire wrong) | `READINESS_PARTIALLY_PREDICTIVE` | "Tick-50 readiness is partially predictive of post-50 dominance on the modern A_null corpus; only one of three primary observables clears the locked threshold." |
| 0/3 fire (and 0/3 fire wrong) | `READINESS_NOT_PREDICTIVE` | "Tick-50 readiness does not predict post-50 dominance on the modern A_null corpus; none of the three primary observables clear the locked threshold." |
| any primary fires |paired_d| ≥ 0.5 in WRONG direction | `READINESS_OPPOSITE_SIGN_HALT` | "Halt: tick-50 readiness shows a wrong-direction signal on the modern A_null corpus; the substrate-causal arc's readiness candidate is incompatible with the locked expected signs." |
| any of v0.42 / v0.44 / v0.45's re-derived A_null h=8 share drifts > 1e-3 from its hardcoded reference | `CORPUS_REDERIVE_DRIFT_HALT` | "Halt: A_null re-anchor drifted from the published Results value for v0.NN; the on-disk corpus is not byte-equivalent to the published sweep." |

The 0-of-3-fires verdict (`READINESS_NOT_PREDICTIVE`) and 1-of-3 verdict (`READINESS_PARTIALLY_PREDICTIVE`) are framed correlationally — they do not rule readiness out as a *mechanism*, only as a robust *predictor* under the locked thresholds. Mechanism declarations require a fresh-stream calibration, which v0.46 does not perform (per v0.36 framing discipline).

The `READINESS_PREDICTS_DOMINANCE` phrase is **correlational**, not causal: it does not claim readiness *causes* dominance, only that the eventual top lineage is already differentially advantaged at tick 50 across the modern A_null corpus.

## Cautious framing (per CLAUDE.md)

- "Tick-50 readiness predicts post-50 dominance" — NOT "tick-50 readiness causes post-50 dominance".
- "On the modern A_null corpus" — NOT a chamber-config-independent claim.
- "Eventual top lineage is already differentially advantaged at tick 50" — descriptive of the joint distribution, not a mechanism claim.
- v0.46 explicitly does **not** rule out: pre-50 spatial sorting, founder-position advantage, topology-mediated energy access ticks 0..50, or any post-tick-200 dynamic. These remain live candidates regardless of v0.46's verdict.

## Secondary descriptive metrics (cannot fire verdict)

Reported in `runs/v0.46-readiness/per_run_per_lineage_tick50.csv` for transparency; not used in the decision rule.

- `tick50_living_count` per lineage
- `tick50_total_energy` per lineage (sum across living agents)
- `tick50_valid_adjacent_empty_count` per lineage (sum across living agents of N/S/E/W in-bounds non-WALL unoccupied cells)
- `pre50_food_acquired_count` per lineage (cumulative `AteFood` events with tick ≤ 50 by `lineage_id` of agent)
- `pre50_hazard_damage_received_count` per lineage (cumulative `HazardDamageApplied`)
- `tick50_mean_age` per lineage

These are descriptive only. Even if a secondary metric shows a large effect size, it does NOT fire the verdict; the verdict is determined exclusively by the three primary observables.

## Outputs (locked)

```
runs/v0.46-readiness/per_run_per_lineage_tick50.csv
  columns: version, seed, hazard, run_id, lineage_id,
           tick50_living_count, tick50_mean_energy, tick50_mean_age,
           tick50_above_threshold_count, tick50_above_threshold_fraction,
           tick50_total_energy, tick50_valid_adjacent_empty_count,
           pre50_reproductive_momentum_count,
           pre50_food_acquired_count, pre50_hazard_damage_received_count,
           end_of_run_living, is_eventual_top

runs/v0.46-readiness/audit_summary.csv
  columns: section, key, value
  sections:
    - reanchor: per (version, hazard) re-derived A_null share + reference + drift_abs
    - paired_d: per primary observable (paired_d, n_runs, fires_expected, fires_wrong)
    - verdict: locked verdict + locked phrase

runs/v0.46-readiness/audit_log.txt
  human-readable echo of the audit_summary including
  the locked phrase fired verbatim.
```

## Implementation plan (locked, post-correction)

1. Fresh script `scripts/v0_46_tick50_readiness_audit.py`. Underscore filename (matches v0_43r/v0_44/v0_45 audit naming), CLI: `uv run python scripts/v0_46_tick50_readiness_audit.py [--out-dir runs/v0.46-readiness]`.
2. Per (version, seed, hazard) tuple in the locked corpus, build the same V0_25 + A_null arm config the version's sweep used (re-using `V0_42_INTERVENTION_ARMS[0]` / `V0_43R_INTERVENTION_ARMS[0]` / `V0_44_INTERVENTION_ARMS[0]` / `V0_45_INTERVENTION_ARMS[0]` — the A_null arm — from `comparison_grid.py`).
3. Run `run_chamber(...)` once per tuple with two observers:
   - **`tick_observer`**: fires when `model.tick_count == 50`, snapshots per-living-agent `(agent_id, lineage_id, parent_id, x, y, energy, age, traits)` and per-living-agent reproduction-readiness predicate `(energy ≥ energy_threshold AND age ≥ min_age)`. Stores in a per-run dict keyed by `(version, seed, hazard)`.
   - **End-of-run capture**: after the last `model.step()`, snapshot `birth_tick` per agent (founders: 0; non-founders: from each agent's stored `birth_tick`) and compute `b50_count` per lineage = number of agents (including dead ones) with `birth_tick > 50`.
4. Per (run, lineage) at tick 50: aggregate the 3 primary observables + secondary descriptive metrics over the lineage's living agents at tick 50 (snapshot from step 3's `tick_observer`).
5. Per run: assign `is_eventual_top` per the corrected dominance label (`argmax(b50_count)` from step 3's end-of-run capture). Runs with `total_b50 == 0` get `eventual_top_lineage_id = None` (and contribute NaN to all primary observables, see "NaN handling").
6. Compute paired_d per primary observable across all 64 runs (NaN-aware drops per "NaN handling").
7. Re-anchor: for v0.42 / v0.44 / v0.45 only, compute `a_share_h8 = mean over A_null h=8 runs of (max_lineage(b50_count) / total_b50_in_run)`; compare to hardcoded reference (0.652 / 0.878 / 0.818); halt-loud on |drift| > 1e-3. v0.43R: compute and print, do NOT halt-gate.
8. Emit verdict per the locked decision rule; print + write the locked phrase verbatim.

The reducer is fully self-contained: it reads no on-disk `runs/` artifacts. Re-execution of 64 A_null runs at ~5–10 s each gives a wall time of ~5–10 minutes total — comparable to running each sweep (~17 s per sweep × 4 = ~70 s, plus overhead) but consolidated in one driver. Determinism guaranteed by passing each (version, seed) the same anchor config the merged sweep used.

## Test list (locked, per v0.45 7-point review pattern)

`tests/test_v0_46_tick50_readiness_audit.py`:

1. `test_tick50_observer_fires_once_at_correct_step_boundary` — run `run_chamber` for 100 ticks with a counting `tick_observer`; assert the observer sees `model.tick_count == 50` exactly once and that the snapshot is non-empty (≥ 1 living agent on the V0_25 anchor).
2. `test_eventual_top_lineage_tiebreak_lowest_lineage_id` — synthetic two-lineage tie at tick 200; assert lowest lineage_id wins.
3. `test_pre50_reproductive_momentum_count_matches_filtered_events` — synthetic events with births at ticks 30, 50, 75; assert count = 2 (≤ 50 inclusive).
4. `test_tick50_above_threshold_fraction_predicate` — synthetic agents with energy/age combinations spanning the predicate boundary; assert exact fraction.
5. `test_tick50_mean_energy_nan_when_no_living_agents` — synthetic lineage extinct by tick 40; assert NaN and run dropped from observable's pool.
6. `test_paired_d_formula_one_sample_cohens_d` — known delta vector, assert paired_d matches `mean / stdev_ddof1` exactly.
7. `test_verdict_2_of_3_fires_predicts` — synthetic deltas yielding paired_d (0.6, 0.7, 0.3); assert `READINESS_PREDICTS_DOMINANCE`.
8. `test_verdict_1_of_3_fires_partial` — paired_d (0.6, 0.3, 0.2); assert `READINESS_PARTIALLY_PREDICTIVE`.
9. `test_verdict_0_of_3_fires_not_predictive` — paired_d (0.3, 0.2, 0.4); assert `READINESS_NOT_PREDICTIVE`.
10. `test_verdict_wrong_sign_halt` — paired_d (0.6, −0.6, 0.3); assert `READINESS_OPPOSITE_SIGN_HALT` raised loud.
11. `test_reanchor_drift_halt` — synthetic published-share value 0.5; replay yields 0.6; assert `CORPUS_REDERIVE_DRIFT_HALT` raised loud.
12. `test_corpus_includes_all_four_versions` — assert reducer iterates v0.42 / v0.43R / v0.44 / v0.45 A_null arms only and rejects any B / C arm directories present in `runs/`.
13. `test_secondary_metrics_in_csv_but_do_not_affect_verdict` — synthetic run where secondary metric would fire but primaries do not; assert verdict = `READINESS_NOT_PREDICTIVE`.
14. `test_run_extinction_before_tick_200_halts` — synthetic A_null run with 0 living agents at tick 200; assert `LineageReplayError`.

## Watch-outs (for future-Chronus)

- **`runs/` is gitignored.** Each of the 4 sweeps must be re-run locally before the reducer (`uv run python scripts/v0.42_sweep.py`, etc., ~17s each). Pre-commit which sweeps fired.
- **A_null reference values are hardcoded** (0.652 / 0.878 / 0.818 for v0.42 / v0.44 / v0.45). v0.43R has no published value and is excluded from the halt protocol. If a future correction to a prior version's Results changes those numbers, this slice's pre-reg becomes drift-positive and must be amended.
- **`tick_observer` fires AFTER `model.step()` increments `tick_count`** (`fear_hunger_chamber.py:502-503`). When the observer sees `model.tick_count == 50`, the model has just completed step 49: founder agents have undergone 50 metabolism cycles (steps 0..49); an agent with `body.id` born at tick T has undergone (49 − T) metabolism cycles. The observer reads `body.energy` and `body.age` directly — no arithmetic, no off-by-one risk.
- **`b50_count` reads `body.parent_id` of the live `model.agents`** at end-of-run plus an internal birth-tick map populated at `AgentBorn` emission time (signal listener attached at `setup_observer` time). Founders never contribute to `b50_count` (they have no `AgentBorn` event; `birth_tick = 0` by convention).
- **No `src/` modification.** The reducer uses `setup_observer` and `tick_observer`, both already supported by `fear_hunger_chamber.run_chamber` since v0.45. No new sweep arms; no callback construction; A_null runs use `optional_intervention=InterventionConfig(kind=KIND_NULL)` (byte-identical to `optional_intervention=None`, verified by H2e).
- **Pre-50 reproduction byte-identity** through v0.46 is preserved by construction: v0.46 makes no `src/` change.
- **Locked phrase discipline**: when the verdict fires, the locked-phrase string in the Results section MUST match the table above verbatim. No paraphrase.
- **`is_eventual_top` is a function of tick-200 living count, not of share**. Some prior versions report share thresholds; the dominance label here is purely the argmax (with tiebreak), not a share-fraction threshold.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.46.md` (this file; Results section appended after reducer run)
- `scripts/v0_46_tick50_readiness_audit.py`
- `tests/test_v0_46_tick50_readiness_audit.py`

No other files modified.

## Results

**Status:** reducer executed 2026-05-07 against 64 A_null runs (v0.42 / v0.43R / v0.44 / v0.45, h ∈ {0, 8}, 8 seeds per (version, hazard) bucket). All re-anchors PASS (drift ≤ 0.0003 ≪ 1e-3 tolerance).

### Verdict — `READINESS_PREDICTS_DOMINANCE` fires

> **Locked phrase fires verbatim:** "Tick-50 readiness predicts post-50 dominance on the modern A_null corpus."

Two of three primary observables fire above the locked Cohen's d threshold of +0.5; zero observables fire wrong-sign.

### Paired Cohen's d per primary observable

| # | observable | expected sign | paired_d | n_runs | fires |
|---|---|:-:|:-:|:-:|:-:|
| 1 | `pre50_reproductive_momentum_count` | + | **+1.136** | 64 | **YES** |
| 2 | `tick50_above_threshold_fraction` | + | **+0.810** | 64 | **YES** |
| 3 | `tick50_mean_energy` | + | +0.452 | 64 | no |

Per-run paired delta = `top_lineage_value − mean(non_top_lineage_values)`; paired_d = `mean(per_run_delta) / stdev(per_run_delta, ddof=1)`. All 64 runs contributed to every observable's pool (zero NaN drops; every run had `total_b50 ≥ 1`).

### Re-anchor — all three published versions PASS

| version | n_runs | derived `a_share_h8` | published | |drift| | halt |
|---|:-:|:-:|:-:|:-:|:-:|
| v0.42  | 8 | 0.652 | 0.652 | 0.0003 | no |
| v0.43R | 8 | 0.674 | — (halted, non-citable) | — | n/a |
| v0.44  | 8 | 0.878 | 0.878 | 0.0001 | no |
| v0.45  | 8 | 0.818 | 0.818 | 0.0002 | no |

Re-anchor confirms v0.46's deterministic re-execution is byte-equivalent to each version's merged sweep at the published precision (3 decimals). The on-disk corpus is not a precondition — the reducer derives its anchor from the same `(seed, V0_25, A_null)` execution path each version's sweep used. v0.43R's derived 0.674 is informational; v0.43R's audit was halted as non-citable per SUBSTRATE_PREFLIGHT_HALT_2 and no published reference exists.

### Reading the result correlationally

The locked phrase is **correlational, not causal**: the eventual top lineage is *already differentially advantaged* at tick 50 along two of the three pre-committed readiness axes:

- **Pre-50 reproductive momentum** is the strongest signal (d = +1.136, large effect by Cohen's convention). The eventual top lineage produced ~1.1 standard deviations more pre-50 births than the mean of its non-top peers in the same run, paired across 64 runs.
- **Reproduction-readiness fraction at tick 50** (energy ≥ threshold AND age ≥ min_age) fires at d = +0.810 (large effect). The top lineage carries proportionally more reproduction-ready agents at the tick-50 boundary.
- **Mean energy at tick 50** alone is the weakest (d = +0.452, just below the locked +0.5 threshold). Energy state per se does not predict dominance as cleanly as readiness counts or momentum do.

This is consistent with — but does not prove — the v0.45 caveat candidate "trait-linked reproduction readiness". v0.46 specifically does **not** rule out: pre-50 spatial sorting, founder-position advantage, topology-mediated energy access ticks 0..50, or any post-tick-200 dynamic. These remain live causal candidates regardless of v0.46's verdict.

### What v0.46 establishes (and what it does not)

- ✓ **Establishes**: on the modern A_null corpus (4 versions × 8 seeds × 2 hazards = 64 runs), the eventual post-50 dominant lineage is identifiable at tick 50 by reproductive-momentum count and reproduction-readiness-fraction with large paired effect sizes; mean energy alone is a borderline predictor.
- ✗ **Does not establish**: that readiness *causes* dominance. Mechanism declarations require fresh-stream calibration analogous to v0.30..v0.33; v0.46 is observational decomposition only.
- ✗ **Does not rule out** any of the live causal candidates from v0.45's caveat list: pre-50 spatial sorting, founder-position advantage, topology-mediated energy access ticks 0..50.
- ✗ **Does not generalise** beyond the locked V0_25 anchor (tight_gradient + GradientPolicy + auto_reproduction=True + unbounded_mutation + transfer-pool funding + ambient_influx_rate=1.0).

### Caveats

- **Pre-50 momentum is partly tautological with `b50_count`** in expectation: lineages that produce more pre-50 births tend to produce more post-50 births by sheer continuity (more reproduction-eligible agents at tick 50, more queue-throughput at tick 51+). The +1.136 paired_d is a strong signal but does not isolate a *fresh* mechanism distinct from the b50-based dominance label itself. Reproduction-readiness fraction (d = +0.810) is the cleaner observable in this regard — it measures the *state* of living lineage members at tick 50, not their reproductive history.
- **Mean energy borderline (+0.452)** is below the locked threshold (+0.5) but only by a small margin. A wider effect-size window (say d ≥ 0.4 per v0.36's primary-trait threshold) would have fired all three. The locked +0.5 stands; this is the kind of "single-knob choice changes the verdict" finding that the pre-reg's discipline is designed to surface honestly.
- **Cross-version pooling**: the 64 runs are pooled across 4 versions whose substrate `src/` extensions accumulated additively (v0.42 leader-kill, v0.43R density, v0.44 respawn-flow, v0.45 birth-redirect). All four A_null arms are byte-identical to `optional_intervention=None` (verified by H2e regression on each version's branch); pooling is therefore valid. The h=8 re-anchor passing for all 3 published versions is the strongest available evidence that the cross-version pool is a single distribution.
- **No claim about post-tick-200 dynamics**, no claim about the chamber's other layouts (open_field / hazard_band), no claim about non-V0_25 anchors.

### v0.47 candidate (open; not locked)

The natural next decomposition is whether the readiness signals at tick 50 are **inherited from founder traits** (mutated lineage signatures) or **emergent from trajectory-level path advantage** (which lineage happened to find food first). v0.36's `trait_replay.py` is the analogous decomposition over v0.34 corpus; an extension to the modern A_null corpus, restricted to traits that influence reproduction-readiness (e.g. `metabolic_rate`, `sensor_radius`), would isolate the heritability fraction of the v0.46 finding. This is a reducer slice, not an intervention slice.

### CI gate at v0.46 close

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1587 passed, 7 skipped (was 1573, +14 v0.46)
uv run python scripts/core_smoke_test.py                ok
uv run python scripts/v0_46_tick50_readiness_audit.py   READINESS_PREDICTS_DOMINANCE
```
