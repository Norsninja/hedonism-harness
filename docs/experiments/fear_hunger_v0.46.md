# fear_hunger v0.46 — tick-50 readiness decomposition

**Slice:** v0.46
**Type:** post-hoc reducer (decomposition, NOT intervention)
**Predecessors:** v0.21..v0.27 (substrate / aggregate-optimum), v0.34 (lineage MVP), v0.35 (eventual-top survival framework), v0.36 (trait-heritability decomposition with fishing protection), v0.42 (leader-kill), v0.43R (density-redistribution), v0.44 (respawn-flow), v0.45 (birth-locality).
**Question being asked (locked):** Is the eventual post-50 dominant lineage already advantaged at tick 50 by reproduction readiness, energy state, or pre-50 reproductive momentum?

The substrate-causal arc (v0.42..v0.45) ruled out four post-tick-50 mechanism layers as *necessary* for the observed late-window dominance share at h=8 (leader removal, density compaction, respawn flow, post-50 offspring placement). v0.45 Results explicitly named pre-50 spatial sorting, founder-position advantage, **trait-linked reproduction readiness**, and topology-mediated energy access ticks 0..50 as the live causal candidates. v0.46 is the **first decomposition slice over the modern intervention corpus** addressing the readiness / energy / momentum subset of those candidates.

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
eventual_top_lineage_id = argmax_lineage(living_count_at_tick_200)
  ties broken by min(lineage_id)
```

Reconstructed from `events.jsonl` by replaying AgentBorn/AgentDied per lineage. Halt-loud (`LineageReplayError`) if any A_null run extincts before tick 200; this should not occur on the modern A_null corpus and a halt indicates the `runs/` tree was regenerated under a different config than the merged sweeps.

## Primary observables (locked, 3, with expected signs)

Each is computed **per (run, lineage) at tick 50**, then aggregated per-run by comparing the eventual top lineage's value to the mean of the non-top lineages' values in the same run.

| # | name | definition (per lineage at tick 50) | expected sign | candidate from v0.45 caveat |
|---|---|---|---|---|
| 1 | `pre50_reproductive_momentum_count` | cumulative `AgentBorn` events with tick ≤ 50 by `lineage_id` | **+** | trait-linked reproduction readiness / pre-50 momentum |
| 2 | `tick50_above_threshold_fraction` | fraction of living lineage agents with `energy ≥ reproduction_config.energy_threshold AND age ≥ min_age` | **+** | reproduction readiness |
| 3 | `tick50_mean_energy` | mean `energy` across living lineage agents (NaN if no living agents → run dropped from observable's pool, see "NaN handling") | **+** | energy state |

**NaN handling.** A lineage with zero living agents at tick 50 contributes a `pre50_reproductive_momentum_count` (it may have produced births and then extincted — count is well-defined) but contributes NaN for `tick50_above_threshold_fraction` and `tick50_mean_energy`. Per-run paired delta (top minus mean-non-top) is computed only when both top-lineage and ≥ 1 non-top lineage have non-NaN values for the observable; runs failing this gate are dropped from that observable's pool with the count reported in the audit.

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

Each predecessor version's published Results section reports an A_null pooled top-lineage share at h=8. v0.46 must re-derive that share from each version's on-disk A_null `events.jsonl` files and assert agreement within float-32 tolerance. Halt-loud on drift (`CORPUS_REDERIVE_DRIFT_HALT`).

Re-derivation protocol (locked):

```
top_lineage_b50_share_at_h8(version) =
    mean over (8 A_null runs at h=8) of:
        (max over lineages of living_count_at_tick_200) / total_living_at_tick_200
```

(Identical formula to v0.34 `B_pool` and v0.42..v0.45's primary observable — re-anchored on `living_count_at_tick_200`, the late-window quantity used by every prior intervention audit.)

The published reference values are pulled from the merged Results section of each version (v0.42, v0.43R, v0.44, v0.45) at reducer initialisation; if a version's Results section does not contain a parseable A_null h=8 share, halt with a config error rather than skip the anchor.

## Verdicts (locked, 3-way + 2 halts)

| condition | verdict | locked phrase (verbatim) |
|---|---|---|
| ≥ 2/3 primaries fire in expected direction (and 0/3 fire wrong) | `READINESS_PREDICTS_DOMINANCE` | "Tick-50 readiness predicts post-50 dominance on the modern A_null corpus." |
| exactly 1/3 fires (and 0/3 fire wrong) | `READINESS_PARTIALLY_PREDICTIVE` | "Tick-50 readiness is partially predictive of post-50 dominance on the modern A_null corpus; only one of three primary observables clears the locked threshold." |
| 0/3 fire (and 0/3 fire wrong) | `READINESS_NOT_PREDICTIVE` | "Tick-50 readiness does not predict post-50 dominance on the modern A_null corpus; none of the three primary observables clear the locked threshold." |
| any primary fires |paired_d| ≥ 0.5 in WRONG direction | `READINESS_OPPOSITE_SIGN_HALT` | "Halt: tick-50 readiness shows a wrong-direction signal on the modern A_null corpus; the substrate-causal arc's readiness candidate is incompatible with the locked expected signs." |
| any version's re-derived A_null h=8 share drifts from its merged-Results value | `CORPUS_REDERIVE_DRIFT_HALT` | "Halt: A_null re-anchor drifted from the merged Results value for v0.NN; the on-disk corpus is not byte-equivalent to the published sweep." |

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

## Implementation plan (locked)

1. Fresh script `scripts/v0_46_tick50_readiness_audit.py`. Underscore filename (matches v0_43r/v0_44/v0_45 audit naming), CLI: `uv run python scripts/v0_46_tick50_readiness_audit.py --runs-root runs/`.
2. Copy-local `_replay_living_state` helper from v0.35's `lineage_survival_replay.py` (NOT import). v0.35's script remains byte-identical. Helper is adapted to additionally track `(agent_id → energy, age)` per tick by deterministic metabolism + `AteFood` / `HazardDamageApplied` deltas (verify metabolism formula matches `src/hedonism_harness/model.py` per-tick agent step exactly).
3. Read each version's merged Results to extract the published A_null h=8 share (string-match a locked anchor in the markdown — see "Watch-outs"). Halt with config error if not found.
4. For each of 64 runs: replay events.jsonl up to tick 50 → emit per-lineage tick-50 row; replay through tick 200 → assign `is_eventual_top` and `end_of_run_living`.
5. Compute paired_d per primary observable across all 64 runs (NaN-aware drops per "NaN handling").
6. Re-anchor: per (version, hazard) compute `top_lineage_b50_share_at_h8`; compare to merged-Results value; halt-loud on |drift| > 1e-4 (float-32 tolerance).
7. Emit verdict per the locked decision rule; print + write the locked phrase verbatim.

## Test list (locked, per v0.45 7-point review pattern)

`tests/test_v0_46_tick50_readiness_audit.py`:

1. `test_replay_recovers_living_count_at_tick200_against_v0_35_anchor` — on a synthetic events.jsonl, copy-local replay produces the same end-of-run living count as v0.35's own replay (re-anchor of the helper itself).
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
- **A_null published-share extraction**: each version's Results section uses its own table format. Plan: lock a regex anchor like `A_null at h=8: <float>` per merged Results, halt-loud on parse failure rather than fall back. Adapt the regex per version if the markdown formats diverge.
- **Metabolism formula** for per-tick energy reconstruction MUST match `src/hedonism_harness/model.py` exactly. Test #1 above re-anchors the helper against v0.35's replay output; any drift here halts the slice.
- **Birth queue ordering**: v0.21..v0.27 birth queue applies the parent energy debit + child startup-energy spawn at queue-process time, which can fall on the same tick as the `ReproductionRequested`. Tick-50 energy reconstruction must apply the parent-debit to anyone who requested reproduction at tick ≤ 50 AND was processed at tick ≤ 50.
- **Pre-50 reproduction byte-identity** through v0.46 is preserved by construction: v0.46 makes no `src/` change.
- **Locked phrase discipline**: when the verdict fires, the locked-phrase string in the Results section MUST match the table above verbatim. No paraphrase.
- **`is_eventual_top` is a function of tick-200 living count, not of share**. Some prior versions report share thresholds; the dominance label here is purely the argmax (with tiebreak), not a share-fraction threshold.

## Files this slice will create

- `docs/experiments/fear_hunger_v0.46.md` (this file; Results section appended after reducer run)
- `scripts/v0_46_tick50_readiness_audit.py`
- `tests/test_v0_46_tick50_readiness_audit.py`

No other files modified.

## Results

*(Appended after reducer run on 64-run modern A_null corpus.)*
