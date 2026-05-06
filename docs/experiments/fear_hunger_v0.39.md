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
- v0.39 reducer (`leader_advantage_fresh_replay.py`): ~3s.
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
  - `scripts/leader_advantage_fresh_replay.py` (~450 LOC) — v0.39
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
  - `tests/test_leader_advantage_fresh_replay.py` (~500 LOC, ~30
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
- `scripts/leader_advantage_fresh_replay.py`: ~450 LOC.
- `tests/test_v0_39_sweep.py`: ~80 LOC.
- `tests/test_lineage_replay_v0_39_extension.py`: ~150 LOC.
- `tests/test_lineage_survival_replay_v0_39_extension.py`: ~150 LOC.
- `tests/test_leader_advantage_fresh_replay.py`: ~500 LOC.
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
  **imported by v0.39 leader_advantage_fresh_replay.py without
  modification**. Locked driver observable comes from this module.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

_To be appended after the v0.39 sweep + extension reducers + reducer
have executed. Locked phrases above will fire verbatim on the
combined classification's row._
