# v0.39 — fresh-stream calibration of leader post-50 advantage

**Status:** pre-registered 2026-05-06; sweep + reducer not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.39-leader-advantage-fresh-stream`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated at h=8;
`top_lineage_b50_share` rises 0.635 → 0.785 across hazards), v0.35
(founder-survival timing — **H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER
CONTINUITY**; `wad_rate` 0.458 → 0.708 → 0.750 → 0.792), v0.36
(founder-trait heritability replay — **H6 TRAIT-LINKED-FLAT**;
sensor_radius dominant, hazard-flat), v0.37 (dominance timing
decomposition — **H6 STABLER-EARLY-LEADERSHIP**; O2 leader-turnover
0.333 → 0.083; O1 winner-lock-in non-monotone), v0.38 (leader post-50
advantage — **H5 LEADER-ADVANTAGE-AMPLIFIED**; `mean_leader_advantage`
3.948 → 7.375 → 8.531 → 8.990 across hazards {0, 4, 8, 12} on the
96-run v0.34 corpus; spread +5.042 ≥ locked 1.5 bar).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.38 fired **H5 LEADER-ADVANTAGE-AMPLIFIED** on the v0.34 96-run
corpus: hazard amplifies the post-50 reproductive advantage of the
tick-50 leader over the mean of the four non-leader founder lineages.
v0.34..v0.38 are all post-hoc reducers over a single seed corpus
(v0.25 1..8 + v0.32 9..16 + v0.33 17..24); the lineage arc has not
been calibrated against an independent seed stream. v0.39's question
is the discipline-canonical follow-up:

> **Does v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED result reproduce on a
> fresh seed stream (seeds 25..32, n=8 per hazard) under the same
> chamber / influx / hazard parameters?**

This is the same calibration discipline that closed the v0.30..v0.33
weight-axis arc: a single-stream finding is treated as
correlational-on-this-corpus until a fresh stream confirms or
collapses it. v0.39 is the first slice in v0.34..arc that adds a new
sweep; v0.34..v0.38 are all post-hoc reducers.

This is a **fresh-stream calibration follow-up** on v0.38. It is
NOT a sim-mechanics change, NOT a heritability mechanism declaration,
NOT a HedonismPolicy comparison, NOT a per-lineage mortality
decomposition, NOT a windowed-b50 decomposition, NOT a
descendant-trait-drift exploration. v0.39 is the *minimum* additional
discipline needed to promote v0.38's effect from "same-corpus
correlational" to "cross-stream reproducible." It does NOT promote to
mechanism declaration even on success — that requires further
fresh-stream replication and intervention design.

## What this slice tests, and what it does NOT test

### Tests

- Whether **`mean_leader_advantage(h)` on a fresh seed stream
  (25..32)** rises monotonically with hazard across {0, 4, 8, 12} AND
  clears the locked spread bar (`mean(12) − mean(0) ≥ 1.5`).
- Whether **the pooled 128-run corpus** (96 old + 32 fresh) supports
  the same monotone-up + spread story under the same locked rule.
- Two-layer verdict (locked rule below; fresh-stream verdict is the
  PRIMARY headline; pooled verdict is SUPPORTING context).
- Anchor identity for old seeds against existing v0.34's
  `run_summary.csv:top_lineage_id` AND v0.35's
  `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)`.
- Anchor identity for fresh seeds against newly-derived v0.34-extension
  + v0.35-extension outputs (see "Re-anchor stack" below).
- Substrate-byte-identity: v0.34 + v0.35 + v0.38 reducer modules
  imported without modification.

### Does NOT test

- Per-lineage post-50 mortality / extinction-tick. Reserved for v0.40+.
- Windowed b50 decomposition ({50–100, 100–150, 150–200}). Reserved
  for v0.40+.
- Descendant-trait drift. Reserved for v0.40+ if v0.39 fires fresh.
- Policy-stack comparison; HedonismPolicy. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- Sim-mechanics changes; `src/` modifications beyond an additive
  arm-tuple constant `V0_39_TIGHT_H_ARMS` (mirrors the
  v0.32→v0.33 pattern of one binding name per slice; element-wise
  identical to V0_32_TIGHT_H_ARMS).
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- New seed streams beyond 25..32.
- New observables beyond v0.38's locked O1; no winner-overtake
  (v0.38's O2/O3 supporting observables are NOT recomputed in v0.39
  — fresh-stream calibration is on the headline driver only,
  intentionally narrow).
- Promotion to mechanism declaration. A passing fresh-stream verdict
  upgrades the effect to **cross-stream reproducible correlational
  evidence**, NOT to causal mechanism. Mechanism promotion requires
  intervention design (e.g., handicap the tick-50 leader and check
  whether advantage collapses) which is out of scope for v0.39.
- p-values; statistical significance tests; Bonferroni / FDR.
- Re-running v0.36 / v0.37 reducers over the fresh stream. v0.39 is
  scoped to the v0.38 driver only. v0.36 / v0.37 fresh-stream
  calibration is a separate slice if/when motivated.

### Deferred (v0.40+ candidates, conditional on v0.39 outcome)

- **If H5_fresh + H5_pooled both fire.** v0.40 candidates open to:
  per-lineage post-50 mortality decomposition (b); windowed b50 (c);
  descendant-trait drift (d); a second fresh stream (seeds 33..40)
  for further compounding — discipline-canonical second-tier
  calibration.
- **If H5_fresh fires + H5_pooled fails (unlikely structurally —
  pooled includes the old corpus that already fired H5).** Flag as
  inconsistent; v0.40 is internal investigation.
- **If H5_fresh fails + H5_pooled fires.** v0.40 candidate: variance
  decomposition by stream — does the old corpus carry the signal
  alone? Is the fresh stream genuinely null, or noise-dominated at
  n=8? A second fresh stream would help adjudicate.
- **If H5_fresh fails (H6_fresh or H7_fresh).** v0.40 reverts to
  investigating why the old corpus's signal does not survive a fresh
  stream. The lineage arc's correlational story would be marked
  **non-reproducing on fresh-stream calibration**; promotion to any
  mechanism claim is blocked.

### Quarantined v0.36 secondaries (NOT v0.39 inputs)

v0.36's descriptive-only observations (`reproduction_drive` h=0
sign-inversion, `metabolic_rate` hazard-attenuation) remain
quarantined. Not v0.39 inputs.

## Conservation framing — minimal additive change from v0.20..v0.38

v0.39 is the first slice since v0.34 to add a new sweep. The
conservation contract is therefore slightly extended from the
"post-hoc reducer slice" framing of v0.34..v0.38:

- **Zero modifications** to `core/`, `model.py`,
  `experiments/fear_hunger_chamber.py`,
  `experiments/population_dynamics.py`,
  `policies/gradient_policy.py`, `policies/hedonism_policy.py`.
- **Zero modifications** to existing arm tuples
  (V0_25_ARMS, V0_27_ARMS, V0_31_TIGHT_W_ARMS, V0_32_TIGHT_H_ARMS,
  V0_33_TIGHT_H_ARMS).
- **Zero modifications** to [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]], [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]], or any
  `scripts/v0.NN_*.py`.
- **Additive only:** `V0_39_TIGHT_H_ARMS` constant added to
  `src/hedonism_harness/experiments/comparison_grid.py` (mirrors
  v0.32 / v0.33 pattern; literal slice of V0_25_ARMS at influx=1.0
  across hazards {0, 4, 8, 12}; element-wise identical to
  V0_32_TIGHT_H_ARMS by construction; distinct binding name pins
  v0.39's intent).
- **New scripts:** `scripts/v0.39_sweep.py` (sweep driver),
  `scripts/lineage_replay_v0_39_extension.py` (v0.34 extension over
  fresh stream; thin wrapper, no logic duplication),
  `scripts/lineage_survival_replay_v0_39_extension.py` (v0.35
  extension; same pattern), `scripts/leader_advantage_fresh_replay.py`
  (v0.39 reducer).
- **New tests:** paired `tests/test_v0_39_sweep.py`,
  `tests/test_lineage_replay_v0_39_extension.py`,
  `tests/test_lineage_survival_replay_v0_39_extension.py`,
  `tests/test_leader_advantage_fresh_replay.py`.
- **No mutations to existing reducer outputs.** The fresh-stream
  extension reducers write to **separate output dirs**
  (`runs/lineage-v0.34-fresh/`, `runs/lineage-v0.35-fresh/`),
  preserving the existing 96-run outputs at
  `runs/lineage-v0.34/`, `runs/lineage-v0.35/` byte-identical for
  re-anchor against v0.34..v0.38's verdicts.

## Mechanism

v0.39 ships four new scripts (sweep + two extension wrappers + one
reducer), one src/ additive constant, four paired test files, and this
doc.

### 1. Sweep (`scripts/v0.39_sweep.py`)

Mirrors `scripts/v0.33_sweep.py` structurally. Imports
`V0_39_TIGHT_H_ARMS` from
`src/hedonism_harness/experiments/comparison_grid.py`. Runs
4 arms × tight_gradient × seeds 25..32 = 32 fresh runs. Wall-time
estimate ~30s based on v0.32 / v0.33 wall (~13s each on n=8).

Output tree: `runs/fear-hunger-v0.39-tight_gradient/`.

### 2. Extension reducers

Two thin wrappers that import the existing v0.34 / v0.35 reducer
helpers via `importlib.util` (the established pattern; same import
mechanism v0.37 / v0.38 use). Each wrapper:

- Defines a v0.39-only `STREAM_CONFIGS`:
  ```
  STREAM_CONFIGS_FRESH = (
      ("v0.39",
       Path("runs/fear-hunger-v0.39-tight_gradient/arms"),
       tuple(range(25, 33))),
  )
  ```
- Calls the imported helpers to discover, load, reduce the fresh runs.
- Writes outputs to a **separate** dir
  (`runs/lineage-v0.34-fresh/` and `runs/lineage-v0.35-fresh/`) with
  the same CSV schema as the originals (so the v0.39 reducer's
  re-anchor logic can read them with the same parsers).
- **Does NOT re-assert `B_POOL_ANCHORS`** — the v0.34 anchor at
  {4: 312, 8: 321, 12: 312} is over the OLD corpus only; the fresh
  stream's per-hazard B_POOL is an emergent observable on the new
  data, not an anchor.
- **Does re-assert** `EXPECTED_FOUNDERS == 5`, `n_ticks == 200`, and
  per-run founder-count invariants (these are run-level, not
  corpus-level).

Wall-time estimate: ~2s each on the 32-run fresh corpus.

### 3. v0.39 reducer (`scripts/leader_advantage_fresh_replay.py`)

Imports v0.34 + v0.35 + v0.38 helpers via `importlib.util` (no
modification). Reuses v0.38's `compute_leader_advantage` function
verbatim — this is the locked driver observable.

Pure-function pipeline:

- For each fresh run (32 total), call v0.38's `summarise_run` to
  compute per-run `leader_advantage` (and `winner_overtake` for
  consistency with v0.38's per-run schema, even though v0.39 does
  NOT use winner_overtake in its verdict).
- Cross-anchor (halts on drift):
  - **Fresh-corpus v0.34 anchor (H2a):** re-derived `top_lineage_id`
    per fresh run matches
    `runs/lineage-v0.34-fresh/run_summary.csv:top_lineage_id`.
  - **Fresh-corpus v0.35 anchor (H2b):** re-derived
    `(leader_lineage_id_at_tick_50, eventual_top_lineage_id)` per
    fresh run matches
    `runs/lineage-v0.35-fresh/pre_post_dominance.csv`.
  - **Old-corpus v0.34 anchor (H2c):** `runs/lineage-v0.34/run_summary.csv`
    is byte-readable and contains 96 rows. (No re-derivation;
    v0.39 trusts the merged v0.34 output as a sealed artifact.)
  - **Old-corpus v0.35 anchor (H2d):** `runs/lineage-v0.35/pre_post_dominance.csv`
    is byte-readable and contains 96 rows.
- Per-hazard aggregation (fresh stream, n=8 per hazard):
  - `mean_leader_advantage_fresh(h)` for h ∈ {0, 4, 8, 12}.
- Per-hazard aggregation (pooled, n=32 per hazard):
  - `mean_leader_advantage_pooled(h)` over the 96 old + 32 fresh
    runs at each hazard.
- Indicator pass evaluation (locked rules below).
- Two-layer verdict (locked structure below).

Outputs five CSVs under `runs/lineage-v0.39/` (gitignored):

- `per_run.csv` — 32 rows: source_version (= "v0.39"), arm_label,
  hazard, seed, n_ticks, leader_lineage_id_at_tick_50,
  eventual_top_lineage_id, wad,
  leader_b50, mean_non_leader_b50, leader_advantage, winner_overtake.
- `per_hazard_fresh.csv` — 4 rows: hazard, n_runs (=8),
  mean_leader_advantage.
- `per_hazard_pooled.csv` — 4 rows: hazard, n_runs (=32),
  mean_leader_advantage.
- `verdict_fresh.csv` — single row: verdict, locked_phrase,
  monotone_pass, spread_value, spread_threshold, threshold_passes.
- `verdict_pooled.csv` — single row: verdict, locked_phrase,
  monotone_pass, spread_value, spread_threshold, threshold_passes.
- `verdict_combined.csv` — single row: combined_classification (one
  of {"H5_FRESH_AND_POOLED", "H5_FRESH_ONLY", "H5_POOLED_ONLY",
  "NEITHER_H5", "H7_FRESH"}), headline_locked_phrase.

### Locked constants (committed in code at reducer entry)

```
LEADER_TICK: int = 50
N_NON_LEADERS: int = 4
EXPECTED_N_TICKS: int = 200
SPREAD_THRESHOLD: float = 1.5

# Fresh stream
FRESH_SEEDS: tuple[int, ...] = tuple(range(25, 33))
FRESH_RUNS_ROOT: Path = Path("runs/fear-hunger-v0.39-tight_gradient/arms")

# Anchor sources
V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_34_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_PRE_POST: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")

OUT_DIR: Path = Path("runs/lineage-v0.39")
```

Tie-break for all "lineage selection by maximum count" operations:
**lowest lineage_id**, mirroring v0.34..v0.38.

### Determinism — anchors

- v0.21..v0.38 events.jsonl + sidecar artifacts on disk are not
  regenerated. Sidecars (`agent_lifetimes.csv`, `config.json`,
  `manifest.json`) are read verbatim.
- v0.21..v0.38 test suites continue to pass (additive guard).
- [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]] — imported (or in the case
  of trait_replay / lock_in_timing_replay, NOT imported by v0.39),
  not modified.
- `runs/lineage-v0.34/run_summary.csv` and
  `runs/lineage-v0.35/pre_post_dominance.csv` are sealed artifacts
  (96 rows each); v0.39 reads but does NOT regenerate them.
- `runs/lineage-v0.34-fresh/run_summary.csv` and
  `runs/lineage-v0.35-fresh/pre_post_dominance.csv` are NEW
  artifacts (32 rows each), produced by the v0.39 extension
  reducers. v0.39 leader_advantage_fresh_replay halts if either is
  missing.

### Wall-time estimate

- Sweep (`v0.39_sweep.py`): ~30s on 32 runs.
- Extension reducer 1 (`lineage_replay_v0_39_extension.py`): ~2s.
- Extension reducer 2
  (`lineage_survival_replay_v0_39_extension.py`): ~2s.
- v0.39 reducer (`v0_39_leader_advantage_fresh_replay.py`): ~3s.
- Total v0.39 wall time: **~37s** end-to-end on a fresh corpus.

## Observables — pre-committed before reading the data

### Per-fresh-run

- `leader_lineage_id_at_tick_50(run)` — int in {0..4}. Lineage with
  max `births_so_far(50)`; lowest lineage_id wins ties. Reused
  verbatim from v0.35 / v0.38.
- `eventual_top_lineage_id(run)` — int in {0..4} or None.
  Reused from v0.35.
- `wad(run)` — bool. Reused from v0.35.
- `leader_b50(run)` — int. b50 count of the lineage identified by
  `leader_lineage_id_at_tick_50`.
- `mean_non_leader_b50(run)` — float. Mean of b50 across the 4
  non-leader founder lineages.
- **`leader_advantage(run)` — float.** Reused verbatim from v0.38:
  ```
  leader_advantage = leader_b50 − mean_non_leader_b50
  ```
- `winner_overtake(run)` — int. Reused from v0.38 for per-run
  consistency; NOT a v0.39 verdict input.

### Per-hazard (fresh stream, n=8 per hazard)

- `mean_leader_advantage_fresh(h)` — float, h ∈ {0, 4, 8, 12}.
- `n_runs_fresh(h)` — int (=8 by construction).
- `n_wad_true_fresh(h)` — int (descriptive only; NOT a verdict input).

### Per-hazard (pooled, n=32 per hazard)

- `mean_leader_advantage_pooled(h)` — float. Computed as the mean of
  the 24 old + 8 fresh per-run `leader_advantage` values at each
  hazard.
- `n_runs_pooled(h)` — int (=32 by construction).

### Indicator-input (locked)

**Fresh-stream indicator (PRIMARY, drives the headline):**

- `fresh_monotone_up` :=
  `mean_leader_advantage_fresh(0) ≤ mean_leader_advantage_fresh(4)
   ≤ mean_leader_advantage_fresh(8)
   ≤ mean_leader_advantage_fresh(12)` (weak non-decreasing).
- `fresh_monotone_down` :=
  `mean_leader_advantage_fresh(0) ≥ mean_leader_advantage_fresh(4)
   ≥ mean_leader_advantage_fresh(8)
   ≥ mean_leader_advantage_fresh(12)` (weak non-increasing).
- `fresh_spread_up` :=
  `mean_leader_advantage_fresh(12) − mean_leader_advantage_fresh(0) ≥ 1.5`.
- `fresh_spread_down` :=
  `mean_leader_advantage_fresh(0) − mean_leader_advantage_fresh(12) ≥ 1.5`.

**Pooled indicator (SUPPORTING, drives annotation only):**

- `pooled_monotone_up` :=
  `mean_leader_advantage_pooled(0) ≤ … ≤ mean_leader_advantage_pooled(12)`.
- `pooled_monotone_down` :=
  `mean_leader_advantage_pooled(0) ≥ … ≥ mean_leader_advantage_pooled(12)`.
- `pooled_spread_up` :=
  `mean_leader_advantage_pooled(12) − mean_leader_advantage_pooled(0) ≥ 1.5`.
- `pooled_spread_down` :=
  `mean_leader_advantage_pooled(0) − mean_leader_advantage_pooled(12) ≥ 1.5`.

The same 1.5 threshold is reused for the pooled corpus. Justification:
`leader_advantage` is a **within-hazard mean across runs**, not a
count. Adding 8 runs per hazard (24 → 32) does not rescale the mean's
expected magnitude. The 1.5 bar therefore retains the same semantic
meaning across both layers. **No linear scaling.**

### Descriptive (NOT used by verdict)

- `n_wad_true_fresh(h)` — fresh-stream wad-rate per hazard.
  Reported but does NOT enter the verdict (unlike v0.35 / v0.38
  where wad informed the structural decomposition).
- Per-run `winner_overtake` for fresh runs.
- v0.34 + v0.35 anchor coverage report
  (96 old + 32 fresh = 128 anchored).

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive reuse of v0.34 + v0.35 + v0.38 helpers).** v0.39
  imports v0.34's `STREAM_CONFIGS`, `parse_agent_lifetimes`,
  `parse_config`, `parse_manifest`, `assign_founder_lineages`,
  `compute_generation_depths`, `LineageReplayError`,
  `build_agent_rows`, `discover_runs`, `HAZARDS`,
  `EXPECTED_FOUNDERS` from [[scripts/lineage_replay.py]]; v0.35's
  `load_run_agents`, `_agents_by_lineage`, `compute_births_so_far`,
  `compute_eventual_top_lineage`, `compute_leader_at_tick_50` from
  [[scripts/lineage_survival_replay.py]]; v0.38's
  `compute_leader_advantage`, `summarise_run` (or its per-run logic)
  from [[scripts/leader_advantage_replay.py]]. All three imported
  without modification.
- **H1b (no edit to existing arm tuples).** V0_25_ARMS,
  V0_27_ARMS, V0_31_TIGHT_W_ARMS, V0_32_TIGHT_H_ARMS,
  V0_33_TIGHT_H_ARMS unchanged. V0_39_TIGHT_H_ARMS is a NEW
  additive constant; element-wise identical to V0_32_TIGHT_H_ARMS by
  construction (literal slice of V0_25_ARMS at influx=1.0 across
  hazards {0, 4, 8, 12}).
- **H2a (fresh-corpus v0.34 anchor).** Per-fresh-run re-derived
  `top_lineage_id` MUST equal
  `runs/lineage-v0.34-fresh/run_summary.csv:top_lineage_id` for
  every (source_version="v0.39", arm_label, seed). Halts on drift.
- **H2b (fresh-corpus v0.35 anchor).** Per-fresh-run re-derived
  `(leader_lineage_id_at_tick_50, eventual_top_lineage_id)` MUST
  equal
  `runs/lineage-v0.35-fresh/pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)` for every (v0.39, arm, seed). Halts on
  drift.
- **H2c (old-corpus v0.34 sealed).**
  `runs/lineage-v0.34/run_summary.csv` is byte-readable and contains
  exactly 96 rows with the v0.34 schema. v0.39 does NOT regenerate.
  Halts if the file is missing or row-count != 96.
- **H2d (old-corpus v0.35 sealed).**
  `runs/lineage-v0.35/pre_post_dominance.csv` is byte-readable and
  contains exactly 96 rows. v0.39 does NOT regenerate. Halts if
  missing or row-count != 96.
- **H2e (founder count invariant on fresh runs).** Every fresh run
  has exactly 5 founders. Halts if not.
- **H2f (n_ticks invariant on fresh runs).** Every fresh run has
  `n_ticks == 200`. Halts if not.
- **H2g (no run with leader's lineage having b50 == 0).** Unlike
  v0.38 where wad / non-wad split was informative, v0.39's verdict
  is purely on the mean. The `compute_leader_advantage` function
  inherits v0.38's tie-break and zero-handling; no new
  edge-case logic.
- **H3 (additive guard).** v0.21..v0.38 prior tests still pass
  after v0.39 additions.
- **H4 (no mutation of pre-v0.39 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]],
  existing arm tuples in
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before
  and after v0.39.

### Cautious form — two-layer verdict on v0.39's question

The verdict has TWO layers. The fresh-stream verdict is the PRIMARY
headline; the pooled verdict is SUPPORTING context. Disagreement
rules are pre-locked below.

#### Layer 1 — Fresh-stream verdict (PRIMARY headline)

Three-way classifier (mutually exclusive by construction):

- **H5_FRESH — LEADER-ADVANTAGE-AMPLIFIED-ON-FRESH-STREAM.**
  **FIRES iff** `fresh_monotone_up == True AND fresh_spread_up == True`.
- **H6_FRESH — LEADER-ADVANTAGE-DOES-NOT-STRENGTHEN-WITH-HAZARD-ON-FRESH-STREAM.**
  **FIRES iff** neither H5_FRESH nor H7_FRESH fires (i.e., neither
  monotone+spread direction passes). Default outcome.
- **H7_FRESH — LEADER-ADVANTAGE-WEAKENS-WITH-HAZARD-ON-FRESH-STREAM.**
  **FIRES iff** `fresh_monotone_down == True AND fresh_spread_down == True`.

#### Layer 2 — Pooled verdict (SUPPORTING)

Same three-way structure, applied to pooled (96 old + 32 fresh =
128 runs):

- **H5_POOLED.** `pooled_monotone_up AND pooled_spread_up`.
- **H6_POOLED.** Neither.
- **H7_POOLED.** `pooled_monotone_down AND pooled_spread_down`.

#### Combined classification (locked headline rules)

The headline phrasing is determined by both layers' verdicts under
this lookup (mutually exclusive):

| Layer 1 (fresh)  | Layer 2 (pooled) | combined classification    | headline framing                           |
|------------------|------------------|----------------------------|--------------------------------------------|
| H5_FRESH         | H5_POOLED        | **H5_FRESH_AND_POOLED**    | Reproduces on fresh stream + pooled.       |
| H5_FRESH         | H6_POOLED        | H5_FRESH_ONLY (rare)       | Fresh fires; pooled fails. Tension noted.  |
| H5_FRESH         | H7_POOLED        | H5_FRESH_ONLY (impossible) | Fresh fires up; pooled fires down. Halt.   |
| H6_FRESH         | H5_POOLED        | **H5_POOLED_ONLY**         | Fresh fails; pooled persists. Headline IS the fresh failure. |
| H6_FRESH         | H6_POOLED        | **NEITHER_H5**             | Neither layer fires.                       |
| H6_FRESH         | H7_POOLED        | H6_FRESH (rare)            | Pooled flips down; fresh null. Tension.    |
| H7_FRESH         | any              | **H7_FRESH**               | Fresh fires down. Headline IS the down-flip. |

The H5_FRESH × H7_POOLED row is structurally impossible (the pooled
corpus is dominated by the 96 old runs that already showed monotone
up in v0.38; pooling 24 strong + 8 anything cannot produce monotone
down without an extreme reversal in the fresh stream). It is listed
for verdict-table completeness; if it fires, **halt and investigate**
(v0.38 reproducibility check).

### Locked phrases for each combined classification

> **H5_FRESH_AND_POOLED phrase:** "The leader post-50 advantage
> amplification reproduces on the fresh seed stream (25..32) and
> remains present in the pooled 128-run corpus. This upgrades the
> v0.38 effect from same-corpus correlational finding to cross-stream
> reproducible timing-locus evidence. Not a mechanism declaration."

> **H5_FRESH_ONLY phrase (fresh fires, pooled fails — rare; pooled
> includes 96 old runs that already fired):** "The leader post-50
> advantage amplification reproduces on the fresh seed stream
> (25..32) but the pooled 128-run effect does not clear the locked
> spread bar. The discrepancy is unexpected and requires
> investigation; reported as cross-stream-reproducible-with-pooled-
> tension. Not a mechanism declaration."

> **H5_POOLED_ONLY phrase (fresh fails, pooled persists — fresh-
> stream calibration FAILS):** "The fresh seed stream (25..32) does
> not show monotone-up + spread-≥1.5 on `mean_leader_advantage`. The
> pooled 128-run effect persists on the strength of the 96 old runs
> alone. v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED is **not reproduced
> on the fresh stream**; it remains a same-corpus correlational
> finding pending further calibration."

> **NEITHER_H5 phrase:** "Neither the fresh stream (25..32) nor the
> pooled 128-run corpus clears the locked monotone-up + spread-≥1.5
> bar on `mean_leader_advantage`. v0.38's H5 LEADER-ADVANTAGE-
> AMPLIFIED is **not reproduced**; the pooled effect collapses on
> inclusion of the fresh stream. The lineage arc's correlational
> story is marked non-reproducing on fresh-stream calibration."

> **H7_FRESH phrase:** "The fresh seed stream (25..32) shows
> monotone-down with spread ≥ 1.5 on `mean_leader_advantage` — the
> opposite direction from v0.38. v0.38's H5 LEADER-ADVANTAGE-
> AMPLIFIED is **directionally contradicted** on the fresh stream.
> The pooled effect (if any) is not the headline. Halt and
> investigate; the lineage arc requires re-examination."

To be reused verbatim if the corresponding combined classification
fires.

### Caveats — locked, must appear in Results

- **Fresh stream is n=8 per hazard, conservative.** v0.38's stream
  was n=24 per hazard. The 1.5 spread threshold reused on n=8 is a
  more demanding bar (smaller sample, larger sampling noise per
  per-hazard mean). A null fresh-stream result does NOT prove the
  v0.38 effect is spurious; it shows the fresh stream alone does
  not clear the conservative bar. The pooled verdict guards against
  treating a noise-driven fresh failure as a definitive
  non-reproduction by reporting persistence (or collapse) of the
  effect at the 128-run scale.
- **Pooled spread re-uses the 1.5 bar without scaling.** Justified
  because `mean_leader_advantage` is a within-hazard mean across
  runs — not a count. Adding seeds does not change the magnitude
  scale of the mean. Any linear-scaling adjustment would weaken the
  pooled verdict for no good reason.
- **Fresh-stream verdict is the PRIMARY headline regardless of
  pooled outcome.** This prevents the larger old corpus from
  drowning the new test. The pooled verdict provides supporting
  context but never overrides the fresh failure case.
- **No new observables on the fresh stream.** v0.38's O2 (winner
  overtake) and v0.37's O1/O2/O3 are NOT recomputed for v0.39
  verdict purposes. Fresh-stream calibration is intentionally narrow
  on the headline driver — broadening would re-introduce the
  fishing risk that small pre-committed observable sets exist to
  prevent.
- **No mechanism promotion even on H5_FRESH_AND_POOLED.** A
  cross-stream reproducible correlational finding is still
  correlational. Mechanism promotion requires intervention design
  (e.g., handicap the tick-50 leader and check whether the post-50
  advantage collapses) which is **out of scope for v0.39**.
- **Wad-rate is descriptive only on fresh stream.** The
  decomposition v0.38 did (wad=True / wad=False bucket-shift +
  within-bucket spread) is NOT replicated for v0.39's verdict.
  Fresh-stream wad-rate per hazard is reported in `per_run.csv`
  for transparency but does NOT inform any verdict decision.
- **Single fresh stream is not sufficient for mechanism.** Even on
  H5_FRESH_AND_POOLED, the v0.39 outcome is "cross-stream
  reproducible" not "robust." Robustness in the v0.30..v0.33 sense
  requires a third independent stream (seeds 33..40+), which is a
  v0.40+ candidate.

### Verdict reachability — sanity check

We have v0.38's per-hazard means as a strong prior:
3.948 → 7.375 → 8.531 → 8.990 (spread +5.042 on n=24).

If the fresh stream behaves like a sample from the same underlying
distribution:

- **H5_FRESH likely fires.** Spread of +5 on a hazard that affects
  n=8 means each per-hazard mean has standard error ~ s/sqrt(8) ≈
  s/2.83. Even if per-run leader_advantage has SD ≈ 6 (a generous
  noise estimate), per-hazard mean SE ≈ 2.1; the +5 expected spread
  is comfortably > 2.1, suggesting H5_FRESH fires often when the
  underlying effect is real.
- **H7_FRESH ≈ unreachable** under any plausible noise model on the
  v0.38 effect — would require a +5 to −1.5 swing on n=8 across all
  intermediate hazards. Listed for completeness; "halt and
  investigate" if it fires.
- **H6_FRESH (default)** fires whenever H5_FRESH and H7_FRESH both
  fail. Genuinely live: an n=8 stream with monotone-up but spread
  +1.0 (below 1.5 bar) would fall here. Discipline-conservative.

The threshold space is genuinely live in all three regions. None is
a tail-only outcome under noise alone, though H7_FRESH would require
a substantial direction reversal.

### Anchor identity

No v0.39 cross-version artifact-identity anchor beyond v0.34 + v0.35
extension outputs. v0.39's outputs (`runs/lineage-v0.39/`) are
reductions of the fresh corpus, with re-anchor against both the
sealed old reductions AND the new fresh-stream extensions.

## Decision rules

| layer 1 (fresh) | layer 2 (pooled) | combined           | next-step v0.40 candidate                                  |
|-----------------|------------------|--------------------|-----------------------------------------------------------|
| H5_FRESH        | H5_POOLED        | H5_FRESH_AND_POOLED | mortality decomposition (b), windowed b50 (c), drift (d), or 2nd fresh stream — open |
| H5_FRESH        | H6_POOLED        | H5_FRESH_ONLY (rare) | investigate v0.38 / pooled discrepancy                    |
| H5_FRESH        | H7_POOLED        | (impossible)        | halt; recompute v0.38 anchors                             |
| H6_FRESH        | H5_POOLED        | H5_POOLED_ONLY      | second fresh stream (33..40) to disambiguate noise vs absence |
| H6_FRESH        | H6_POOLED        | NEITHER_H5          | lineage arc marked non-reproducing; arc paused            |
| H6_FRESH        | H7_POOLED        | H6_FRESH            | investigate fresh-only-null vs pooled-flip                |
| H7_FRESH        | any              | H7_FRESH            | halt; arc requires re-examination                         |

**Independent of the verdict, v0.40 candidates remain:** mortality
decomposition (b), windowed b50 (c), descendant-trait drift (d),
second fresh stream (e). Activation depends on this slice's outcome.
HedonismPolicy and Mesa remain deferred indefinitely.

Halt conditions:

- **H1 / H1b fail** — v0.34 / v0.35 / v0.38 surface or existing arm
  tuples mutated. Halt; revert.
- **H2a / H2b fail** — fresh-corpus re-anchor mismatch. Halt;
  investigate (likely sweep / extension reducer divergence).
- **H2c / H2d fail** — old-corpus sealed artifact missing or
  row-count != 96. Halt; rebuild old corpus per
  [[docs/artifacts/v0.34_v0.38_local_corpus_manifest.md]].
- **H2e / H2f fail** — fresh run founder-count or n_ticks invariant
  violated. Halt; sweep produced an unexpected corpus.
- **H3 / H4 fail** — a v0.21..v0.38 contract was broken by v0.39
  additions. Halt; revert.

## Out of scope (v0.39)

- v0.36 / v0.37 fresh-stream calibration. Single-driver
  calibration only.
- Per-lineage post-50 mortality / extinction-tick.
- Windowed b50 decomposition.
- Descendant-trait drift, parent-child trait deltas.
- Second fresh seed stream (33..40+).
- Multivariate trait analysis.
- p-values, statistical significance, Bonferroni / FDR.
- Mechanism declaration.
- Edits to any prior `scripts/v0.NN_*.py`,
  [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]],
  or existing arm tuples in `comparison_grid.py`.
- HedonismPolicy comparisons.
- Mesa migration.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.

## Implementation notes

### File-level changes

- **New (src/):** `V0_39_TIGHT_H_ARMS` constant added to
  [[src/hedonism_harness/experiments/comparison_grid.py]] (mirrors
  v0.32 / v0.33 pattern). Element-wise identical to
  V0_32_TIGHT_H_ARMS; literal slice of V0_25_ARMS at influx=1.0
  across hazards {0, 4, 8, 12}; distinct binding name pins v0.39's
  fresh-stream-calibration intent.
- **New (scripts/):**
  - `scripts/v0.39_sweep.py` (~80 LOC) — sweep driver mirroring
    v0.33_sweep.py.
  - `scripts/lineage_replay_v0_39_extension.py` (~120 LOC) — thin
    wrapper importing v0.34 helpers; runs over v0.39-only
    STREAM_CONFIGS; writes to `runs/lineage-v0.34-fresh/`.
  - `scripts/lineage_survival_replay_v0_39_extension.py` (~120 LOC)
    — thin wrapper importing v0.35 helpers; runs over v0.39-only
    STREAM_CONFIGS; writes to `runs/lineage-v0.35-fresh/`.
  - `scripts/v0_39_leader_advantage_fresh_replay.py` (~450 LOC) — v0.39
    reducer; imports v0.34 + v0.35 + v0.38 helpers; computes fresh
    + pooled `mean_leader_advantage`; evaluates two-layer verdict.
- **New (tests/):**
  - `tests/test_v0_39_sweep.py` (~80 LOC, ~6 tests) — arm-tuple
    identity, seed range, output-tree shape.
  - `tests/test_lineage_replay_v0_39_extension.py` (~150 LOC, ~12
    tests) — STREAM_CONFIGS shape, helper-byte-identity, output
    schema match, halt-on-missing-corpus.
  - `tests/test_lineage_survival_replay_v0_39_extension.py` (~150
    LOC, ~12 tests) — same structure.
  - `tests/test_v0_39_leader_advantage_fresh_replay.py` (~500 LOC, ~30
    tests) — per-run computation, fresh-vs-pooled aggregation,
    indicator pass logic, three-way fresh verdict, three-way
    pooled verdict, combined classification lookup, all locked
    phrases, all halt conditions, end-to-end synthetic fixture.
- **No changes** to [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]], any
  `scripts/v0.NN_*.py`, `core/`, `model.py`, chamber / population /
  policy modules. Existing arm tuples unchanged.
- **Documented:** this file. Results appended after the reducer runs.
- **Manifest extension:** post-merge,
  [[docs/artifacts/v0.34_v0.38_local_corpus_manifest.md]] will be
  superseded by `docs/artifacts/v0.34_v0.39_local_corpus_manifest.md`
  (new file, not a renaming) documenting the 128-run regen sequence.

### Determinism contract

- v0.21..v0.38 events.jsonl + sidecar artifacts not regenerated.
- v0.21..v0.38 test suites continue to pass.
- v0.34 + v0.35 + v0.38 reducers imported but not modified. v0.36
  and v0.37 reducers not imported (orthogonal observable families).
- Per-fresh-run double anchor against fresh-extension v0.34 +
  v0.35 outputs.
- Old-corpus v0.34 + v0.35 outputs read but not regenerated; halt
  if missing or row-count != 96.
- Per-fresh-run `n_ticks == 200` re-asserted at extension reducer
  entry.

### LOC estimate

- `src/.../comparison_grid.py`: +~6 LOC (one constant + comment).
- `scripts/v0.39_sweep.py`: ~80 LOC.
- `scripts/lineage_replay_v0_39_extension.py`: ~120 LOC.
- `scripts/lineage_survival_replay_v0_39_extension.py`: ~120 LOC.
- `scripts/v0_39_leader_advantage_fresh_replay.py`: ~450 LOC.
- `tests/test_v0_39_sweep.py`: ~80 LOC.
- `tests/test_lineage_replay_v0_39_extension.py`: ~150 LOC.
- `tests/test_lineage_survival_replay_v0_39_extension.py`: ~150 LOC.
- `tests/test_v0_39_leader_advantage_fresh_replay.py`: ~500 LOC.
- This doc: ~700 LOC.

Total v0.39: ~2,350 LOC. Tests should bring the suite from 1039 to
~1,099 (+~60 across all four test files).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   1039 passed, 6 skipped (v0.23/v0.27 corpus
                                skips; non-regression)
uv run python scripts/core_smoke_test.py  ok
```

## References

- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; H7 mostly-concentrated; secondary monotone-with-
  hazard observation that opens the lineage arc.
- [[docs/experiments/fear_hunger_v0.35.md]] — v0.35
  founder-survival-timing replay; **H6 EXPANSION-SUPPORTED**;
  supplies leader_lineage_id_at_tick_50 + eventual_top_lineage_id
  for v0.39's anchor stack.
- [[docs/experiments/fear_hunger_v0.36.md]] — v0.36
  founder-trait heritability replay; **H6 TRAIT-LINKED-FLAT**;
  hazard-amplified trait selection ruled out as mechanism.
  Orthogonal to v0.39.
- [[docs/experiments/fear_hunger_v0.37.md]] — v0.37 dominance timing
  decomposition; **H6 STABLER-EARLY-LEADERSHIP**. Orthogonal to
  v0.39's headline driver.
- [[docs/experiments/fear_hunger_v0.38.md]] — v0.38 leader post-50
  advantage; **H5 LEADER-ADVANTAGE-AMPLIFIED**. v0.39's anchor
  hypothesis to test on a fresh stream.
- [[docs/artifacts/v0.34_v0.38_local_corpus_manifest.md]] — corpus
  regen cookbook; v0.39 will produce a v0.34_v0.39 successor.
- [[scripts/lineage_replay.py]] — v0.34 reducer; **imported by
  v0.39 extension wrapper without modification**.
- [[scripts/lineage_survival_replay.py]] — v0.35 reducer;
  **imported by v0.39 extension wrapper without modification**.
- [[scripts/leader_advantage_replay.py]] — v0.38 reducer;
  **imported by v0.39 v0_39_leader_advantage_fresh_replay.py without
  modification**. Locked driver observable comes from this module.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

**Status:** executed 2026-05-06. Sweep + extension reducers + v0.39
reducer ran end-to-end on the fresh corpus (32 runs at seeds 25..32).
Outputs under `runs/lineage-v0.39/` (gitignored). Sealed v0.34 +
v0.35 OLD outputs (96 rows each) byte-readable; fresh extension
outputs (32 rows each) re-anchored against derived per-run values
without halts. All invariants (H1, H1b, H2a, H2b, H2c, H2d, H2e,
H2f, H3, H4) held.

### Headline

**Combined classification: H5_POOLED_ONLY.** Fresh stream verdict:
**H6_FRESH** (neither monotone-up nor monotone-down with spread≥1.5).
Pooled (128-run) verdict: **H5_POOLED**.

> **Locked H5_POOLED_ONLY phrase:** "The fresh seed stream (25..32)
> does not show monotone-up + spread->=1.5 on mean_leader_advantage.
> The pooled 128-run effect persists on the strength of the 96 old
> runs alone. v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED is not reproduced
> on the fresh stream; it remains a same-corpus correlational finding
> pending further calibration."

The fresh-stream verdict is the PRIMARY headline per the pre-reg's
locked rule. Pooled persistence is reported as supporting context but
does NOT override the fresh failure: the larger old corpus does not
"drown" the new test under the locked combined-classification logic.

### Per-hazard fresh stream (n=8 each, seeds 25..32)

| hazard | n_runs | n_wad_true | mean_leader_advantage |
|-------:|------:|----------:|---------------------:|
| 0      | 8     | 5         | **6.375**            |
| 4      | 8     | 3         | 5.781                |
| 8      | 8     | 3         | 5.906                |
| 12     | 8     | 3         | 5.500                |

Signed spread (`mean(12) − mean(0)`) = **−0.875 ticks** (NEGATIVE).
Not monotone non-decreasing (h=0 to h=4 declines). Not monotone
non-increasing (h=4 to h=8 rises). Locked rule excludes both
H5_FRESH and H7_FRESH; H6_FRESH fires by default.

### Per-hazard pooled corpus (n=32 each = 24 old + 8 fresh)

| hazard | n_old | n_fresh | n_runs | mean_leader_advantage |
|-------:|------:|-------:|------:|---------------------:|
| 0      | 24    | 8      | 32    | **4.555**            |
| 4      | 24    | 8      | 32    | 6.977                |
| 8      | 24    | 8      | 32    | 7.875                |
| 12     | 24    | 8      | 32    | **8.117**            |

Signed spread = **+3.562**. Strict monotone non-decreasing across all
four hazards. Spread clears the locked 1.5 bar by 2.4×. Pooled
verdict fires H5_POOLED.

### Why H5_POOLED_ONLY fires (not H5_FRESH_AND_POOLED)

- **Fresh stream's mean_leader_advantage is highest at h=0** (6.375),
  not at h=12 (5.500). The hazard-amplification pattern v0.38 observed
  on the v0.34 corpus does NOT reproduce on this fresh stream. h=0's
  fresh mean (6.375) is also notably ABOVE the pooled-h=0 mean (4.555),
  reflecting that the fresh stream's hazard=0 runs are more
  leader-favoured than v0.38's old hazard=0 runs.
- **The pooled verdict still fires** because adding 8 fresh runs at
  each hazard to the 24 old runs preserves the underlying old-corpus
  monotone structure: the fresh signal does not invert the pattern
  strongly enough to drag the pooled means out of monotone-up
  ordering. Pooled spread shrinks (5.042 → 3.562) but remains well
  above the 1.5 bar.
- **The locked combined-classification rule prefers fresh failure as
  the headline.** Per the pre-reg, "fresh-stream verdict is the
  PRIMARY headline regardless of pooled outcome." This prevents the
  larger old corpus from drowning the new test.

### Indicator details

| layer    | monotone_up | monotone_down | signed_spread | spread≥1.5 | reverse_spread≥1.5 | verdict     |
|----------|:-----------:|:-------------:|--------------:|:-----------:|:-------------------:|-------------|
| Fresh    | False       | False         | -0.875        | False       | False               | **H6_FRESH** |
| Pooled   | True        | False         | +3.562        | True        | False               | **H5_POOLED** |

### Cross-stream observation: v0.35 / v0.34 patterns also do NOT replicate

The v0.39 fresh extension reducers wrote
`runs/lineage-v0.34-fresh/pool_summary.csv` and
`runs/lineage-v0.35-fresh/pruning_summary.csv`. These are NOT v0.39
verdict inputs (out of pre-reg scope) but they are descriptively
important for interpreting the H5_POOLED_ONLY result:

**v0.34 lens on fresh stream (from `lineage-v0.34-fresh/pool_summary.csv`):**

| hazard | n_runs | total_b50 | mean_top_lineage_b50_share |
|-------:|------:|---------:|---------------------------:|
| 0      | 8     | 106      | 0.666                      |
| 4      | 8     | 105      | 0.632                      |
| 8      | 8     | 106      | 0.669                      |
| 12     | 8     | 104      | 0.683                      |

Compare to v0.34 OLD (24 seeds): 0.635 → 0.728 → 0.759 → 0.785
(monotone up). Fresh stream's `mean_share` is **non-monotone**
(0.666 / 0.632 / 0.669 / 0.683) and the spread is much smaller
(+0.017 vs +0.150 OLD). The "lineage concentration tightens with
hazard" pattern from v0.34 does not cleanly reproduce on the fresh
stream either.

**v0.35 lens on fresh stream (from `lineage-v0.35-fresh/pruning_summary.csv`):**

| hazard | n_runs | wad_rate | mean_n_lineages_with_post50_birth |
|-------:|------:|--------:|----------------------------------:|
| 0      | 8     | **0.625** | 2.625                           |
| 4      | 8     | 0.375   | 2.375                             |
| 8      | 8     | 0.375   | 2.250                             |
| 12     | 8     | 0.375   | 2.250                             |

Compare to v0.35 OLD: wad_rate 0.458 / 0.708 / 0.750 / 0.792
(monotone up). The fresh stream **inverts** this: h=0 has the
HIGHEST wad-rate (0.625), and h=4/h=8/h=12 are all 0.375 (flat). The
v0.35 H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY pattern does
not reproduce on the fresh stream.

This is a striking cross-observable consistency: the lineage-axis
hazard-amplification patterns we observed across v0.34 / v0.35 / v0.38
all weaken or vanish on this fresh stream (n=8 per hazard). The
v0.39 verdict only adjudicates v0.38's H5 driver, but the
descriptive cross-observable picture is consistent: fresh-stream
calibration does not reproduce the old-corpus lineage-axis
hazard-effects in general, not just v0.38's specific driver.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | v0.34 + v0.35 + v0.38 helpers imported additively; no modification | **HOLDS.** Imports succeed; constants byte-match. |
| H1b | V0_39_TIGHT_H_ARMS additive constant; existing arm tuples unchanged | **HOLDS.** Tests assert element-wise identity to V0_32_TIGHT_H_ARMS / V0_33_TIGHT_H_ARMS / V0_25_ARMS literal slice. |
| H2a | Per-fresh-run derived top_lineage_id matches v0.34-fresh anchor | **HOLDS.** All 32 fresh runs match. |
| H2b | Per-fresh-run derived (leader_lineage_id_at_tick_50, eventual_top_lineage_id) match v0.35-fresh anchors | **HOLDS.** All 32 fresh runs match both columns. |
| H2c | runs/lineage-v0.34/run_summary.csv exists with 96 rows | **HOLDS.** |
| H2d | runs/lineage-v0.35/pre_post_dominance.csv exists with 96 rows | **HOLDS.** |
| H2e | Fresh runs have exactly 5 founders | **HOLDS.** Inherited from v0.34's `assign_founder_lineages`. |
| H2f | Fresh runs have n_ticks == 200 | **HOLDS.** All 32 fresh runs pass. |
| H3 | v0.21..v0.38 prior tests pass after v0.39 additions | **HOLDS.** Suite **1039 → 1101** (+62 v0.39 tests; 6 skips are v0.23 / v0.27 corpus-dependent, non-regression); all green. |
| H4 | Pre-v0.39 surface byte-unchanged | **HOLDS.** Zero edits to `lineage_replay.py`, `lineage_survival_replay.py`, `trait_replay.py`, `lock_in_timing_replay.py`, `leader_advantage_replay.py`, prior `v0.NN_*.py`, prior arm tuples in `comparison_grid.py`, `core/`, `model.py`, chamber / population / policy modules. Only `V0_39_TIGHT_H_ARMS` constant added. |
| Layer-1 (fresh) verdict | H5_FRESH / H6_FRESH / H7_FRESH | **H6_FRESH FIRES.** Spread −0.875; not monotone in either direction. |
| Layer-2 (pooled) verdict | H5_POOLED / H6_POOLED / H7_POOLED | **H5_POOLED FIRES.** Spread +3.562 ≥ 1.5; strict monotone up. |
| Combined classification | one of 7 cells | **H5_POOLED_ONLY FIRES.** Fresh failure with pooled persistence. |

### Secondary observations (NOT pre-committed; descriptive only)

These are striking but explicitly outside the verdict logic. They
must not be promoted to mechanism claims without further
calibration.

**1. Fresh-stream h=0 is the leader-advantage outlier.** The fresh
stream's mean_leader_advantage at h=0 (6.375) is meaningfully higher
than the old-corpus h=0 (3.948). The h=4..h=12 fresh means cluster
tightly around 5.5–5.9. This suggests the fresh stream's hazard=0
runs happened to have unusually leader-favoured early dynamics —
possibly a sampling-noise artifact at n=8, possibly a real
seed-dependent structural feature. With 5/8 of the h=0 fresh runs
having `wad=True` (vs 3/8 at higher hazards), this is consistent
with the fresh-stream h=0 sample favouring early-leader-becomes-
winner outcomes.

**2. wad_rate inversion on fresh stream.** v0.35's locked observation
(wad_rate 0.458 → 0.792 on the OLD corpus) inverts on the fresh
stream (0.625 → 0.375). This is the most striking single deviation
across the lineage-axis arc on this fresh stream. The v0.35 H6
verdict (early-leader continuity) does NOT reproduce here.

**3. Pooled corpus retains the old-corpus signal direction.** Adding
8 fresh runs per hazard to the 24 old runs shifts pooled means but
does not flip the monotone direction. Old-corpus h=0 (mean 3.948)
plus fresh h=0 (6.375) gives pooled h=0 (4.555) — pulled UP by the
fresh sample. Old-corpus h=12 (8.990) plus fresh h=12 (5.500) gives
pooled h=12 (8.117) — pulled DOWN. The pooled spread shrinks from
+5.042 (old alone) to +3.562 (pooled), still clearing the 1.5 bar.

**4. Cross-stream cautious reading.** Combining the descriptive v0.34
+ v0.35 + v0.38 fresh-extension observations with v0.39's primary
verdict, the lineage-axis correlational story we built across
v0.34..v0.38 is **single-stream-specific** on the OLD 96-run corpus.
The fresh n=8/hazard stream does not reproduce the monotone-up
hazard-effects on `top_lineage_b50_share`, on `wad_rate`, or on
`leader_advantage`. The strong monotone signals appear to depend
on the specific seed stream OR the n=24 sample size dampening
sampling noise. v0.40+ candidates: a SECOND fresh stream
(seeds 33..40), and / or per-stream variance decomposition on the
existing four streams (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39
25..32).

### Caveats — locked, fired

- **Fresh stream is n=8 per hazard, conservative.** The 1.5 spread
  threshold reused from v0.38 (n=24 per hazard) is a more demanding
  bar. A null fresh-stream result does NOT prove the v0.38 effect is
  spurious. With 1.5 spread translating to roughly half a standard
  error of the mean at typical observed run-level variance, a real
  underlying effect of magnitude +5 (v0.38) would still likely fire
  H5_FRESH on n=8 — the fresh-stream's failure to fire is therefore
  evidence against the effect being homogeneous across seed streams,
  not just against its absolute magnitude. **The fresh stream's
  signed spread is NEGATIVE (−0.875)** — even noise-only would fire
  H5_FRESH ~50% of the time on a real positive effect. The fresh
  stream's failure is more striking than a marginal noise-driven
  null.
- **Pooled spread re-uses the 1.5 bar without scaling.** Confirmed:
  the pooled verdict fires at +3.562, well clear of the 1.5 bar.
- **No mechanism promotion** even in the H5_POOLED-fires layer. The
  pooled effect remains correlational on a single 96-run-dominated
  corpus. The fresh-stream non-reproduction REMOVES the path to a
  cross-stream-reproducible-correlational tier; mechanism promotion
  would require fresh-stream replication, which v0.39 has now ruled
  out at this scale.
- **Single fresh stream is not sufficient for definitive
  non-reproduction either.** The fresh stream is n=8 per hazard,
  small. A v0.40 SECOND fresh stream (seeds 33..40) would help
  adjudicate noise-vs-absence as the explanation for v0.39's null.
  Until then, the headline is "**not reproduced on the fresh
  stream**" — not "**effect ruled out**."

### Cautious framing — locked dual phrasing

> **The v0.39 fresh-stream calibration failed to reproduce v0.38's
> H5 LEADER-ADVANTAGE-AMPLIFIED.** v0.38's same-corpus correlational
> finding does NOT survive an independent n=8/hazard fresh stream.
> The pooled 128-run effect persists on the strength of the OLD 96
> runs alone.

> **The lineage-axis arc (v0.34..v0.38) is now flagged as
> single-stream-correlational.** Cross-stream reproducibility is NOT
> demonstrated for any of the v0.34, v0.35, or v0.38 monotone
> observables on this fresh stream (descriptive cross-anchor
> observations from the v0.34 / v0.35 fresh extensions). v0.36's
> founder-trait finding (sensor_radius dominant, hazard-flat) was
> NOT tested on the fresh stream and remains unaffected by v0.39.
> v0.37's stabler-early-leadership finding was likewise not tested.

### Implementation summary

- **New (src/, +1 constant):** `V0_39_TIGHT_H_ARMS` added to
  `src/hedonism_harness/experiments/comparison_grid.py` (mirrors
  v0.32 / v0.33 binding pattern; element-wise identical to
  V0_32_TIGHT_H_ARMS by construction).
- **New scripts:**
  - `scripts/v0.39_sweep.py` (~85 LOC) — sweep driver; 32 runs at
    seeds 25..32; ~10s wall time.
  - `scripts/lineage_replay_v0_39_extension.py` (~150 LOC) — v0.34
    extension; writes to `runs/lineage-v0.34-fresh/`.
  - `scripts/lineage_survival_replay_v0_39_extension.py` (~180 LOC)
    — v0.35 extension; anchors against fresh v0.34 output; writes
    to `runs/lineage-v0.35-fresh/`.
  - `scripts/v0_39_leader_advantage_fresh_replay.py` (~600 LOC) —
    v0.39 reducer; computes fresh + pooled `mean_leader_advantage`;
    evaluates two-layer verdict + 7-cell combined classification.
- **New tests:**
  - `tests/test_v0_39_sweep.py` (~80 LOC, 8 tests).
  - `tests/test_lineage_replay_v0_39_extension.py` (~160 LOC,
    12 tests).
  - `tests/test_lineage_survival_replay_v0_39_extension.py`
    (~150 LOC, 12 tests).
  - `tests/test_v0_39_leader_advantage_fresh_replay.py` (~410 LOC,
    30 tests).
- **Pre-reg-locked constants in code:** `LEADER_TICK = 50`,
  `N_NON_LEADERS = 4`, `EXPECTED_N_TICKS = 200`,
  `SPREAD_THRESHOLD = 1.5`, `FRESH_SEEDS = (25..32)`,
  `EXPECTED_OLD_ROW_COUNT = 96`, `EXPECTED_FRESH_ROW_COUNT = 32`.
- **Two-tier re-anchor stack:** sealed v0.34 + v0.35 OLD outputs
  (96 rows; halt on missing or row-count drift) + fresh-extension
  v0.34 + v0.35 outputs (32 rows; per-run cross-check on three
  columns).
- **v0.38 sealed per_run.csv** read for pooled aggregation; row
  count asserted to be 96.
- **Zero edits** to `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`, `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`,
  `scripts/leader_advantage_replay.py`, prior `v0.NN_*.py`, prior
  arm tuples (V0_25_ARMS, V0_27_ARMS, V0_31_TIGHT_W_ARMS,
  V0_32_TIGHT_H_ARMS, V0_33_TIGHT_H_ARMS), `src/` runtime, or any
  pre-v0.39 module.
- **CI gate at handoff time:**

  ```
  uv run ruff check .                                              ok
  uv run ruff format --check .                                     ok
  uv run pytest                                                    1101 passed,
                                                                   6 skipped
                                                                   (skips:
                                                                   v0.23/v0.27
                                                                   corpus
                                                                   artifacts;
                                                                   non-regression)
  uv run python scripts/core_smoke_test.py                         ok
  uv run python scripts/v0.39_sweep.py                             32 runs / 10.3s
  uv run python scripts/lineage_replay_v0_39_extension.py          ok
  uv run python scripts/lineage_survival_replay_v0_39_extension.py ok
  uv run python scripts/v0_39_leader_advantage_fresh_replay.py     H5_POOLED_ONLY
  ```

## Conclusion

v0.39 fires **H5_POOLED_ONLY** on the fresh seed stream (25..32) +
pooled (128-run) corpus. The fresh-stream verdict is **H6_FRESH**:
`mean_leader_advantage` per hazard on the fresh stream
(6.375 → 5.781 → 5.906 → 5.500) is non-monotone with a NEGATIVE
signed spread (−0.875), failing both monotone-up and monotone-down
locked rules. The pooled verdict is **H5_POOLED**:
`mean_leader_advantage` on the 128-run pooled corpus
(4.555 → 6.977 → 7.875 → 8.117) is strict monotone non-decreasing
with spread +3.562, well above the 1.5 bar — but persistence is
carried entirely by the OLD 96 runs.

The locked H5_POOLED_ONLY phrase is the verdict:

> **"The fresh seed stream (25..32) does not show monotone-up +
> spread->=1.5 on mean_leader_advantage. The pooled 128-run effect
> persists on the strength of the 96 old runs alone. v0.38's H5
> LEADER-ADVANTAGE-AMPLIFIED is not reproduced on the fresh stream;
> it remains a same-corpus correlational finding pending further
> calibration."**

Decision:

- **v0.38's H5 effect does NOT reproduce on a fresh seed stream.**
  This is the discipline-canonical outcome: a single-stream
  correlational finding has been tested cross-stream and failed.
  The lineage-axis arc (v0.34..v0.38) is flagged as
  **single-stream-correlational**.
- **Mechanism promotion is blocked.** Even cross-stream
  reproducible correlational evidence is not yet established for
  the leader post-50 advantage; mechanism promotion (which would
  require intervention design beyond v0.39's scope anyway) is
  blocked at an earlier tier.
- **Fresh-stream cross-observable picture is consistent.** v0.34's
  `top_lineage_b50_share` and v0.35's `wad_rate` also fail to
  reproduce monotone-up on this fresh stream (descriptive only;
  not v0.39 verdict inputs). The pattern is broader than v0.38
  alone.
- **v0.40 candidates (per the pre-reg's deferred-list, refined by
  the H5_POOLED_ONLY outcome):**
  - **(e) Second fresh seed stream (seeds 33..40)** to disambiguate
    "noise-driven null at n=8" vs "real cross-stream effect
    absence." Discipline-canonical second-tier follow-up.
  - **(f) Per-stream variance decomposition** on the existing four
    streams (v0.25 1..8 / v0.32 9..16 / v0.33 17..24 / v0.39
    25..32) — does the leader_advantage spread vary substantially
    by stream? This would help characterise the v0.34/v0.35/v0.38
    arc's cross-stream stability.
  - **(b/c/d) v0.40 mortality / windowed-b50 / descendant-drift
    candidates** are deferred indefinitely until the fresh-stream
    calibration question is resolved. Decomposing a non-reproducing
    effect risks chasing structure that doesn't survive cross-
    stream replication.
  - **HedonismPolicy and Mesa** remain deferred indefinitely.
