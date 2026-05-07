# v0.41 — second fresh-stream calibration of lineage-axis stability

**Status:** pre-registered 2026-05-07; sweep + reducers + audit not yet
executed.
**Date:** 2026-05-07
**Branch:** `claude/v0.41-second-fresh-stream-calibration`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated;
`mean_top_lineage_b50_share` pooled 0.635 → 0.785), v0.35 (founder-
survival timing — **H6 EXPANSION-SUPPORTED**; pooled `wad_rate`
0.458 → 0.792), v0.36 (founder-trait heritability —
**H6 TRAIT-LINKED-FLAT**), v0.37 (dominance timing decomposition —
**H6 STABLER-EARLY-LEADERSHIP**), v0.38 (leader post-50 advantage —
**H5 LEADER-ADVANTAGE-AMPLIFIED**; pooled 3.948 → 8.990), v0.39
(fresh-stream calibration of v0.38 — **H5_POOLED_ONLY**: fresh stream
25..32 fails to reproduce, pooled persists on OLD 96 alone), v0.40
(cross-stream stability audit at n=4 — **H5 STREAM-STABLE**: M3 spread
≥ +1.5 in 3 of 4 streams (v0.25 +6.125, v0.32 +5.062, v0.33 +3.938,
v0.39 −0.875); v0.39 is the lone outlier).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.40 fired **H5 STREAM-STABLE** on a 4-stream corpus: 3 of 4 streams
agree on M3 (leader_advantage spread ≥ +1.5), and at least 2 of 3
metric families agree in 3 of 4 streams. **v0.39 was the lone
outlier** — the only stream that failed M3, M2, AND was structurally
distinct (M2 inverted, M3 negative). v0.40's headline rehabilitates
the v0.34..v0.38 lineage-axis arc as **stream-stable across 3 of 4
streams**, with v0.39 reframed from "v0.38 doesn't reproduce" to
"v0.39 is structurally different."

But two readings of v0.39 remain compatible with v0.40:

1. **One-off seed-band anomaly.** v0.39 was an unusually unstable n=8
   draw from the same noise distribution that the OLD streams sampled
   from. Another fresh stream would re-stabilise on the OLD pattern.
2. **Systematic post-v0.33 deviation.** Something about the post-v0.33
   seed band (or simulator state, or sampling, or pre-v0.34 implicit
   priors) changed between OLD and FRESH. v0.39's dissent is the
   first observation of a real OLD-vs-FRESH split that future fresh
   streams will continue to show.

The active question for v0.41 is:

> **Does a second fresh stream (seeds 33..40) at the same locked
> parameters agree with the OLD pool's M1/M2/M3 pattern, agree with
> v0.39's dissent pattern, or land somewhere novel?**

This is **NOT** a mechanism question. It is a fork test: which of
the two readings of v0.39 survives a second draw. v0.41 should not
ask "what mechanism explains the OLD/FRESH split?"; it should ask
"is the OLD/FRESH split real or was v0.39 a noise excursion?"

v0.41 ships **one new sweep** (seeds 33..40) plus three thin extension
reducers (mirroring v0.39's pattern over v0.34/v0.35/v0.38) and **one
new audit** that re-runs v0.40-style stream classification at n=5 and
adds a v0.41-bitmap classifier. v0.41 stays narrow and additive.

## What this slice tests, and what it does NOT test

### Tests

- Whether the v0.41 stream's per-stream M1/M2/M3 agreement bitmap
  matches one of three pre-committed cells: **v0.41_OLD_LIKE** (✓✓✓),
  **v0.41_V039_LIKE** (✓✗✗), or **v0.41_NOVEL_MIXED** (anything else).
  This is the **primary verdict.**
- Whether the v0.34..v0.38 lineage-axis arc continues to fire H5
  STREAM-STABLE under the **v0.40 audit re-run at n=5 streams** with
  scaled thresholds (H5: m3 ≥ 4/5 streams AND family ≥ 2/3 metrics
  each ≥ 4/5 streams; H7: m3 ≤ 1/5 streams; H6: otherwise). This is
  the **secondary verdict.**
- Substrate-byte-identity: v0.34 / v0.35 / v0.38 / v0.39 reducer
  outputs are sealed CSVs; v0.41 audit reads them, does NOT
  regenerate. Halts on row-count drift.
- Pre-flight anchor (minimal, not a full inventory): v0.40 sealed
  outputs exist or are regenerable; v0.39 fresh stream remains
  seeds 25..32; v0.41 is reserved for seeds 33..40; no prior sealed
  CSVs are modified.

### Does NOT test

- New observable families. M1 / M2 / M3 are inherited verbatim from
  v0.40. No new mechanism candidates, no founder-trait re-derivation,
  no descendant-drift, no per-lineage mortality decomposition. All
  reserved indefinitely or for v0.42+ conditional on v0.41 outcome.
- Pooled-corpus verdicts. v0.41 has **NO pooled-corpus aggregation,
  no pooled spread, no pooled verdict.** v0.39's pooled question was
  "does v0.38 reproduce on fresh"; v0.40's question was "is the
  pooled effect stream-stable"; v0.41's question is **per-stream
  classification only**, with the n=5 audit as descriptive update.
- Mechanism declaration. Even on the strongest outcome
  (v0.41_OLD_LIKE + n=5 H5 STREAM-STABLE), v0.41 only upgrades the
  arc's stream-stability claim from "3 of 4" to "4 of 5". Mechanism
  promotion still requires intervention design.
- HedonismPolicy comparisons; Mesa migration. Both deferred
  indefinitely.
- Sim-mechanics changes; `src/` modifications beyond an additive
  `V0_41_TIGHT_H_ARMS` constant in `comparison_grid.py` (mirrors
  V0_32 / V0_33 / V0_39 pattern verbatim).
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- Re-running v0.34..v0.40 reducers. Sealed outputs are read verbatim
  by v0.41 audit; their substrate byte-identity is the v0.41
  re-anchor stack.
- p-values; statistical significance tests; Bonferroni / FDR.
- A full inventory phase. v0.41 inherits the v0.40 observable
  family entirely; no new computability questions.

### Deferred (v0.42+ candidates, conditional on v0.41 outcome)

- **If v0.41_OLD_LIKE fires AND n=5 H5 STREAM-STABLE.** v0.42
  candidates re-open: per-lineage mortality (b), windowed b50 (c),
  descendant-trait drift (d). Arc elevates from "3 of 4" to "4 of 5"
  stream-stable; mechanism work becomes scoped (still requires
  intervention design).
- **If v0.41_V039_LIKE fires.** The OLD-vs-FRESH split is real. v0.42
  candidate: characterise what changed between seed band 1..24 and
  25..40. Possible angles: founder-trait composition variance by
  band, pre-tick-0 chamber-state sensitivity, simulator-state
  determinism artifacts. Mechanism work on the OLD signal is blocked
  until OLD-vs-FRESH is understood.
- **If v0.41_NOVEL_MIXED fires.** Stream variability is the immediate
  object of study. v0.42 candidate: a third or fourth fresh stream
  to bound noise vs structure on the post-v0.33 region, OR a
  per-stream founder-trait variance characterisation to look for
  the source of inter-stream variability. Mechanism work remains
  blocked.
- **If n=5 H7 STREAM-UNSTABLE fires.** The v0.40 H5 verdict is
  effectively retracted. The arc becomes "stream-stable on n=4 but
  collapses on n=5" — i.e., not stream-stable at all. v0.42 work
  goes back to characterising why the OLD pool produced a coherent
  signal at all.

### Quarantined (not v0.41 inputs)

- v0.36 founder-trait observations. Orthogonal to M1/M2/M3.
- v0.37 timing observables (O1/O2/O3). Orthogonal.
- v0.39's structural distinctness (M2 inverted, M3 negative on the
  same stream). v0.41 will not investigate WHY v0.39 was distinct;
  it will only test whether v0.41 follows v0.39's pattern.

## Conservation framing — minimal additive, one new sweep

No conservation contract changes. Zero modifications to `core/`,
`model.py`, `experiments/fear_hunger_chamber.py`,
`experiments/population_dynamics.py`,
`policies/gradient_policy.py`, `policies/hedonism_policy.py`. No
mutations to existing arm tuples (V0_25_ARMS, V0_27_ARMS,
V0_31_TIGHT_W_ARMS, V0_32_TIGHT_H_ARMS, V0_33_TIGHT_H_ARMS,
V0_39_TIGHT_H_ARMS). No mutations to
[[scripts/lineage_replay.py]],
[[scripts/lineage_survival_replay.py]],
[[scripts/trait_replay.py]],
[[scripts/lock_in_timing_replay.py]],
[[scripts/leader_advantage_replay.py]],
[[scripts/lineage_replay_v0_39_extension.py]],
[[scripts/lineage_survival_replay_v0_39_extension.py]],
[[scripts/v0_39_leader_advantage_fresh_replay.py]],
[[scripts/v0_40_stream_stability_audit.py]], or any
`scripts/v0.NN_*.py`. No new event types, no new chamber, no new
policy. The only `src/` change is **one additive line**:
`V0_41_TIGHT_H_ARMS = V0_32_TIGHT_H_ARMS` (or an element-wise literal
copy at influx=1.0; chosen at implementation time to mirror the
v0.39 pattern exactly).

## Mechanism

v0.41 ships one new sweep, three thin extension reducers, one new
audit script, paired test files, this pre-reg, and one new manifest.

### 1. Sweep (`scripts/v0.41_sweep.py`)

Mirrors `scripts/v0.39_sweep.py` exactly except for seed range
(33..40) and arm constant (V0_41_TIGHT_H_ARMS). Writes to
`runs/fear-hunger-v0.41-tight_gradient/` (gitignored). Sidecars
include `agent_lifetimes.csv`, `config.json`, `manifest.json`,
events.jsonl, and per-arm `comparison.csv` — the standard sweep
output footprint.

### 2. v0.34 extension (`scripts/lineage_replay_v0_41_extension.py`)

Imports v0.34 helpers from `lineage_replay.py` via importlib (the
established cross-script import pattern). Runs the v0.34 logic over
v0.41 stream only. Skips `B_POOL_ANCHORS` check (the OLD anchors
don't apply to fresh streams). Writes
`runs/lineage-v0.34-v0_41-fresh/run_summary.csv` (32 rows;
source_version=v0.41).

### 3. v0.35 extension (`scripts/lineage_survival_replay_v0_41_extension.py`)

Imports v0.35 helpers from `lineage_survival_replay.py` via
importlib. Runs v0.35 logic over v0.41 stream only. Anchors against
`runs/lineage-v0.34-v0_41-fresh/run_summary.csv` (NOT against the
sealed 96-row OLD output, NOT against v0.39 fresh). Writes
`runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv` (32 rows;
source_version=v0.41).

### 4. v0.38 extension (`scripts/leader_advantage_replay_v0_41_extension.py`)

Imports v0.38 helpers from `leader_advantage_replay.py` via importlib.
Runs v0.38 logic over v0.41 stream only. Anchors against
`runs/lineage-v0.34-v0_41-fresh/run_summary.csv` and
`runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv`. Writes
`runs/lineage-v0.38-v0_41-fresh/per_run.csv` (32 rows;
source_version=v0.41).

### 5. v0.41 audit (`scripts/v0_41_stream_classification_audit.py`)

Imports `lineage_replay.LineageReplayError` via importlib (the
established halt class). Otherwise pure stdlib + `csv.DictReader` —
no helper-function reuse, no events.jsonl parsing, no sidecar reads.

Reads **9 sealed CSVs** total (3 per metric × 3 corpus tiers):

- **OLD tier (96 rows each):**
  - `runs/lineage-v0.34/run_summary.csv` → M1 source (v0.25, v0.32, v0.33)
  - `runs/lineage-v0.35/pre_post_dominance.csv` → M2 source
  - `runs/lineage-v0.38/per_run.csv` → M3 source
- **FRESH-v0.39 tier (32 rows each):**
  - `runs/lineage-v0.34-fresh/run_summary.csv` → M1 source (v0.39)
  - `runs/lineage-v0.35-fresh/pre_post_dominance.csv` → M2 source
  - `runs/lineage-v0.39/per_run.csv` → M3 source
- **FRESH-v0.41 tier (32 rows each; NEW):**
  - `runs/lineage-v0.34-v0_41-fresh/run_summary.csv` → M1 source (v0.41)
  - `runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv` → M2 source
  - `runs/lineage-v0.38-v0_41-fresh/per_run.csv` → M3 source

Re-anchor stack (halts loud on drift via `LineageReplayError`):

- **H2a (OLD row counts):** all three OLD CSVs have exactly 96 rows.
- **H2b (FRESH-v0.39 row counts):** all three FRESH-v0.39 CSVs have
  exactly 32 rows.
- **H2c (FRESH-v0.41 row counts):** all three FRESH-v0.41 CSVs have
  exactly 32 rows.
- **H2d (stream-id consistency):** OLD CSVs `source_version` ∈
  {v0.25, v0.32, v0.33}; FRESH-v0.39 CSVs ⊆ {v0.39}; FRESH-v0.41
  CSVs ⊆ {v0.41}.
- **H2e (per-stream-per-hazard run count):** each (source_version,
  hazard) bucket has exactly 8 runs across all nine CSVs (5 streams
  × 4 hazards × 8 seeds = 160 runs total).
- **H2f (cross-CSV stream-key alignment within tier):** for each
  (source_version, arm_label, seed) tuple in any tier's M1 CSV, it
  appears in the same tier's M2 and M3 CSVs.

Per-(stream, hazard) aggregation, per-stream signed spread, per-stream
agreement flags — all computed exactly as in v0.40, with the
inherited locked rules:

- `m1_agrees(s)` := `signed_spread(M1, s) > 0` (direction-only).
- `m2_agrees(s)` := `signed_spread(M2, s) > 0` (direction-only).
- `m3_agrees(s)` := `signed_spread(M3, s) >= 1.5` (magnitude-too).

#### Primary verdict — v0.41 stream bitmap classification

The v0.41 stream's three booleans `(m1_agrees, m2_agrees, m3_agrees)`
form a 3-bit bitmap. Pre-committed cells:

- **v0.41_OLD_LIKE**: bitmap == (✓, ✓, ✓). v0.41 reproduces all
  three OLD-stream agreement metrics.
- **v0.41_V039_LIKE**: bitmap == (✓, ✗, ✗). v0.41 reproduces v0.39's
  exact dissent pattern (M1 holds; M2 and M3 fail).
- **v0.41_NOVEL_MIXED**: any other bitmap (6 of 8 possible cells).
  v0.41 does not cleanly match either the OLD pattern or v0.39's
  dissent.

The cell that fires is the primary headline.

#### Secondary verdict — n=5 v0.40-style stream audit (scaled thresholds)

Re-runs the v0.40 logic across all 5 streams (v0.25, v0.32, v0.33,
v0.39, v0.41) with thresholds **scaled to preserve the 75/25 bars**:

- **H5_STREAM_STABLE_N5**: m3_agreement_count ≥ 4/5 streams AND
  family_agreement_count ≥ 2/3 metrics, where a metric counts as a
  family agreement only if that metric agrees in ≥ 4/5 streams.
- **H7_STREAM_UNSTABLE_N5**: m3_agreement_count ≤ 1/5 streams.
- **H6_STREAM_MIXED_N5**: otherwise.

Outputs eight CSVs under `runs/lineage-v0.41/` (gitignored):

- `per_stream_per_hazard.csv` — 20 rows: stream, hazard, n_runs,
  mean_M1, mean_M2, mean_M3.
- `per_stream_summary.csv` — 5 rows: stream, n_runs (=32),
  m1_signed_spread, m1_agrees, m2_signed_spread, m2_agrees,
  m3_signed_spread, m3_agrees, m1/m2/m3 monotone flags
  (descriptive only).
- `metric_summary.csv` — 3 rows: metric, n_streams_agree,
  n_streams_total (=5), agreement_rate.
- `v041_bitmap.csv` — single row: m1_agrees, m2_agrees, m3_agrees,
  bitmap_cell (one of OLD_LIKE / V039_LIKE / NOVEL_MIXED).
- `v041_classification.csv` — single row: bitmap_cell, locked_phrase
  (verbatim).
- `n5_verdict.csv` — single row: verdict (H5/H6/H7 STREAM-*-N5),
  m3_agreement_count (0..5), family_agreement_count (0..3),
  locked_phrase (verbatim).
- `stream_metric_table.csv` — wide table (5 streams × 3 metrics)
  reporting agreement boolean per cell.
- `combined_summary.csv` — single row: v041_cell, n5_verdict,
  joint_headline. Only reachable pairings are emitted; H7_N5 is
  retained as a guardrail branch but should not fire under sealed
  v0.40 inputs (see Reachability sanity check below). The joint
  headline is framed in the Results section rather than a locked
  phrase.

### Locked constants (committed in code at audit entry)

```
EXPECTED_HAZARDS: tuple[int, ...] = (0, 4, 8, 12)
EXPECTED_STREAMS_OLD: tuple[str, ...] = ("v0.25", "v0.32", "v0.33")
EXPECTED_STREAMS_FRESH_V039: tuple[str, ...] = ("v0.39",)
EXPECTED_STREAMS_FRESH_V041: tuple[str, ...] = ("v0.41",)
EXPECTED_STREAMS_ALL: tuple[str, ...] = (
    "v0.25", "v0.32", "v0.33", "v0.39", "v0.41"
)
EXPECTED_RUNS_OLD: int = 96
EXPECTED_RUNS_FRESH_V039: int = 32
EXPECTED_RUNS_FRESH_V041: int = 32
EXPECTED_RUNS_PER_STREAM_PER_HAZARD: int = 8

# Inherited from v0.38/v0.39/v0.40 (do NOT mutate)
M3_SPREAD_THRESHOLD: float = 1.5

# Scaled n=5 thresholds (item 1 of v0.41 sign-off)
H5_M3_MIN_STREAMS_N5: int = 4   # M3 agrees in >=4/5 streams for H5
H5_FAMILY_MIN_METRICS_N5: int = 2  # >=2/3 metrics each >=4/5 streams
H7_M3_MAX_STREAMS_N5: int = 1   # M3 agrees in <=1/5 streams for H7

# Locked v0.41 bitmap cells (item 2 of v0.41 sign-off)
V0_41_BITMAP_OLD_LIKE: tuple[bool, bool, bool] = (True, True, True)
V0_41_BITMAP_V039_LIKE: tuple[bool, bool, bool] = (True, False, False)
# Any other 3-bool tuple maps to V0_41_NOVEL_MIXED.

V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_38_OLD_PER_RUN: Path = Path("runs/lineage-v0.38/per_run.csv")
V0_34_FRESH_V039: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_V039: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")
V0_38_FRESH_V039: Path = Path("runs/lineage-v0.39/per_run.csv")
V0_34_FRESH_V041: Path = Path("runs/lineage-v0.34-v0_41-fresh/run_summary.csv")
V0_35_FRESH_V041: Path = Path("runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv")
V0_38_FRESH_V041: Path = Path("runs/lineage-v0.38-v0_41-fresh/per_run.csv")
OUT_DIR: Path = Path("runs/lineage-v0.41")
```

### Determinism — anchors

- v0.21..v0.40 events.jsonl + sidecar artifacts on disk are not
  re-read by the audit. The audit reads ONLY the nine sealed CSVs
  above. (The three v0.41 extension reducers DO read v0.41 sweep
  sidecars; that is their proper input.)
- v0.21..v0.40 test suites continue to pass (additive guard).
- All v0.34..v0.40 reducer modules are imported only insofar as the
  v0.41 extensions need their helpers and the audit needs
  `LineageReplayError`. **No mutation of any pre-v0.41 module.**
- Sealed CSV row-count halts (H2a / H2b / H2c) are the substrate-
  identity guarantee. If a row count drifts, the corpus has been
  mutated without v0.41's knowledge; halt loud.

### Wall-time estimate

- v0.41 sweep: ~10s (mirrors v0.39 sweep cost; 32 runs at locked
  parameters).
- v0.34 / v0.35 / v0.38 extensions: ~1s each.
- v0.41 audit: ~2s on the 160-row aggregate (pure CSV reads + per-
  (stream, hazard) means + bitmap lookup + n=5 verdict).
- **Total v0.41 incremental wall-time:** ~15s.
- Full regen from clean clone (v0.41 corpus included): ~96s (OLD
  sweeps unchanged) + ~10s (v0.41 sweep) + ~17s (OLD reducers + v0.39
  + v0.41 extensions) + ~2s (v0.40 audit) + ~2s (v0.41 audit) ≈
  **~127s end-to-end.**

## Observables — pre-committed before reading the data

### Per (stream, hazard) — 20 rows total (5 streams × 4 hazards)

- `mean_M1(s, h)` — float in [0, 1]. Mean per-run
  `top_lineage_b50_share` over 8 runs. NaN runs (total_b50 == 0)
  excluded; n_excluded reported.
- `mean_M2(s, h)` — float in [0, 1]. Mean per-run boolean
  `winner_already_dominant_at_tick_50` (True=1, False=0; None
  excluded).
- `mean_M3(s, h)` — float (typically 0..15). Mean per-run
  `leader_advantage`.

### Per stream — 5 rows total

- `signed_spread_M1(s) = mean_M1(s, 12) − mean_M1(s, 0)`.
- `signed_spread_M2(s) = mean_M2(s, 12) − mean_M2(s, 0)`.
- `signed_spread_M3(s) = mean_M3(s, 12) − mean_M3(s, 0)`.
- `m1_agrees(s) := signed_spread_M1(s) > 0`.
- `m2_agrees(s) := signed_spread_M2(s) > 0`.
- `m3_agrees(s) := signed_spread_M3(s) >= 1.5`.
- Descriptive (NOT verdict input):
  - `monotone_up_M*(s)` := weak non-decreasing across {0,4,8,12}.
  - `monotone_down_M*(s)` := weak non-increasing.

### v0.41 stream — bitmap

- `v041_bitmap := (m1_agrees(v0.41), m2_agrees(v0.41), m3_agrees(v0.41))`.
- `v041_cell := classify(v041_bitmap)` ∈ {OLD_LIKE, V039_LIKE,
  NOVEL_MIXED}.

### Per metric — 3 rows total

- `n_streams_agree(M)` := count of streams s where `m*_agrees(s) ==
  True`. Range [0, 5].

### n=5 verdict-input

- `m3_agreement_count` := `n_streams_agree(M3)`. Range [0, 5].
- `family_agreement_count` := count of metrics M ∈ {M1, M2, M3} where
  `n_streams_agree(M) >= 4`. Range [0, 3].

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive consumption of sealed v0.34..v0.40 outputs).** v0.41
  audit imports only `LineageReplayError`. All sealed CSVs read with
  stdlib `csv.DictReader`; no helper-function reuse. **Does NOT call
  `lr.process_run`, `ls.summarise_run_survival`, `la.summarise_run`,
  or any v0.40 audit helper.**
- **H2a (OLD row counts).** All three OLD CSVs have exactly 96 rows.
  Halts on drift.
- **H2b (FRESH-v0.39 row counts).** All three FRESH-v0.39 CSVs have
  exactly 32 rows. Halts on drift.
- **H2c (FRESH-v0.41 row counts).** All three FRESH-v0.41 CSVs have
  exactly 32 rows. Halts on drift.
- **H2d (stream-id consistency).** OLD CSVs contain only
  `source_version` ∈ {v0.25, v0.32, v0.33}; FRESH-v0.39 CSVs contain
  only v0.39; FRESH-v0.41 CSVs contain only v0.41. Halts on drift.
- **H2e (per-stream-per-hazard run count).** Each (source_version,
  hazard) bucket has exactly 8 runs across all nine CSVs. Halts on
  drift.
- **H2f (cross-CSV stream-key alignment).** For each (source_version,
  arm_label, seed) tuple in any tier's M1 CSV, it appears in that
  tier's M2 and M3 CSVs. Halts if not.
- **H3 (additive guard).** v0.21..v0.40 prior tests still pass after
  v0.41 additions.
- **H4 (no mutation of pre-v0.41 surface).** All
  `scripts/v0.NN_*.py`, `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`, `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`,
  `scripts/leader_advantage_replay.py`,
  `scripts/lineage_replay_v0_39_extension.py`,
  `scripts/lineage_survival_replay_v0_39_extension.py`,
  `scripts/v0_39_leader_advantage_fresh_replay.py`,
  `scripts/v0_40_stream_stability_audit.py`, existing arm tuples in
  `comparison_grid.py`, chamber / population / policy modules —
  byte-identical before and after v0.41.

### Cautious form — primary verdict on v0.41's bitmap

The primary verdict is three-way (mutually exclusive by
construction):

**v0.41_OLD_LIKE.** **FIRES iff** `v041_bitmap == (True, True, True)`.
v0.41 reproduces the OLD-stream pattern across all three lineage-axis
metrics under the locked v0.40 agreement rules.

**v0.41_V039_LIKE.** **FIRES iff** `v041_bitmap == (True, False,
False)`. v0.41 reproduces v0.39's exact dissent pattern: M1 holds,
M2 and M3 fail.

**v0.41_NOVEL_MIXED.** **FIRES iff** neither of the above. v0.41 does
not cleanly match either the OLD pattern or v0.39's dissent.

### Cautious form — secondary verdict on n=5 stream stability

Three-way (mutually exclusive by construction):

**H5_STREAM_STABLE_N5.** **FIRES iff** `m3_agreement_count >= 4` AND
`family_agreement_count >= 2`. The v0.34..v0.38 lineage-axis arc is
**stream-stable on 4 of 5 streams** at the locked thresholds.

**H7_STREAM_UNSTABLE_N5.** **FIRES iff** `m3_agreement_count <= 1`.
M3 fails to clear +1.5 spread in at least 4 of 5 streams. The arc is
effectively retracted.

**H6_STREAM_MIXED_N5.** **FIRES iff** neither H5 nor H7. M3 agrees in
2 or 3 of 5 streams, OR M3 ≥ 4/5 but family < 2/3.

### Locked phrases — primary verdict (v0.41 bitmap)

> **v0.41_OLD_LIKE phrase:** "Seeds 33..40 reproduce the OLD-stream
> M1/M2/M3 agreement pattern in full. v0.39 is the lone outlier
> across the now-five-stream corpus and is best read as a one-off
> n=8 noise excursion rather than evidence of a systematic post-
> v0.33 deviation. The v0.34..v0.38 lineage-axis arc's stream-
> stability claim is reinforced from 3 of 4 streams to 4 of 5
> streams. Mechanism promotion still requires intervention design
> and is not declared by this audit."

> **v0.41_V039_LIKE phrase:** "Seeds 33..40 reproduce v0.39's exact
> dissent pattern: M1 agrees, M2 and M3 do not. The OLD-vs-FRESH
> split observed in v0.39 is now seen across two independent fresh
> streams. v0.39 was not a one-off; something systematic
> distinguishes the post-v0.33 seed band from the OLD pool's
> 1..24 region. The v0.34..v0.38 arc's stream-stability claim is
> conditional on OLD streams only; cross-band generalisation is
> unsupported. Mechanism work on the OLD signal is blocked pending
> investigation of the OLD-vs-FRESH split."

> **v0.41_NOVEL_MIXED phrase:** "Seeds 33..40 do not cleanly match
> either the OLD-stream pattern or v0.39's dissent pattern. Cross-
> stream variability becomes the immediate object of study. The
> v0.34..v0.38 arc's stream-stability claim weakens; how much
> depends on which metrics agreed and which did not (see
> `v041_bitmap.csv`). Mechanism work remains blocked. v0.42
> candidates: third fresh stream OR per-stream founder-trait
> variance characterisation."

### Locked phrases — secondary verdict (n=5 stream audit)

> **H5_STREAM_STABLE_N5 phrase:** "Lineage-axis hazard signals
> reproduce in at least four of five seed streams (v0.25 1..8, v0.32
> 9..16, v0.33 17..24, v0.39 25..32, v0.41 33..40) under the
> inherited v0.40 spread agreement rules. The v0.34..v0.38 arc's
> correlational signal upgrades from stream-stable on 4 streams to
> stream-stable on 5 streams. Mechanism promotion still requires
> intervention design and is not declared by this audit."

> **H6_STREAM_MIXED_N5 phrase:** "Lineage-axis hazard signals
> reproduce in some streams but not enough to clear the
> H5_STREAM_STABLE_N5 bar (≥ 4/5 on M3, ≥ 2/3 metric families each
> ≥ 4/5 streams). The v0.34..v0.38 arc is stream-mixed at n=5: the
> OLD pooled signal is carried unevenly by its constituent streams,
> or the family-level agreement is partial. Correlational; not a
> mechanism declaration."

> **H7_STREAM_UNSTABLE_N5 phrase:** "Lineage-axis hazard signals
> fail to reproduce in at least four of five seed streams. M3
> leader-post-50-advantage clears its locked +1.5 spread bar in at
> most one stream. The v0.34..v0.38 arc is effectively retracted
> as stream-unstable at n=5: the OLD pooled signal does not survive
> per-stream decomposition once two fresh streams are included.
> Mechanism work is blocked pending re-stabilisation."

To be reused verbatim if the corresponding verdict fires.

### Caveats — locked, must appear in Results

- **Per-stream n is 8.** Each stream's per-hazard mean is over 8
  runs. The 1.5 spread bar on M3 is conservative on n=8 vs the n=24
  that produced v0.38's headline. Inherited unchanged from v0.40.
- **M1/M2 thresholds are direction-only by design** (inherited from
  v0.40). Per-stream magnitude bars on M1/M2 were never pre-
  committed in v0.34/v0.35.
- **Magnitudes for all three metrics ARE reported** in
  `per_stream_summary.csv`. Descriptive context only; only M3
  magnitude enters either verdict via the 1.5 bar.
- **Monotonicity is descriptive only.** At n=8 per stream, four-
  point monotone-non-decreasing is too brittle. Inherited from v0.40.
- **n=5 thresholds preserve the v0.40 75/25 bars.** H5: ≥ 4/5 = 80%
  (≥ v0.40's 75%); H7: ≤ 1/5 = 20% (≤ v0.40's 25%). Absolute counts
  were considered and rejected: 3/5 = 60% would erode the v0.40
  standard.
- **No pooled-corpus verdict in v0.41.** This is by design. v0.39
  asked the pooled question; v0.40 asked the pooled-vs-stream
  question; v0.41 is per-stream only. The bitmap classification
  characterises v0.41's status; the n=5 audit re-runs v0.40's
  stream-stability question on the larger corpus.
- **v0.41 does not investigate WHY v0.39 dissented** — only whether
  v0.41 follows the same dissent pattern. The "why" is reserved for
  v0.42+ conditional on v0.41 outcome.
- **No mechanism promotion under any verdict.** Even on
  v0.41_OLD_LIKE + n=5 H5 STREAM-STABLE, the arc remains
  correlational. Mechanism still requires intervention design.

### Verdict reachability — sanity check

Known per-stream M3 spreads from v0.40
(`runs/lineage-v0.40/per_stream_summary.csv`):

- v0.25: +6.125 ✓
- v0.32: +5.062 ✓
- v0.33: +3.938 ✓
- v0.39: −0.875 ✗

For the n=5 secondary verdict:

- **H5_STREAM_STABLE_N5** requires ≥ 4/5 streams pass M3. With v0.39
  already a known fail (0/1 of those failures), v0.41 must also pass
  M3 for the count to reach 4. Live and hinges on v0.41's M3.
- **H7_STREAM_UNSTABLE_N5** requires ≤ 1/5 stream pass M3. With
  three OLD streams already passing (3/3 OLD passes), H7 is
  arithmetically unreachable. **H7 cannot fire** given the OLD
  streams' known M3 values.
- **H6_STREAM_MIXED_N5** is the catch-all. Fires if v0.41 fails M3
  (m3_count = 3/5 = below 4) OR if family agreement falls below 2/3
  (e.g., a metric loses ≥4/5 because v0.41 plus v0.39 both dissent
  on it).

Family thresholds reachability (each metric's ≥ 4/5 status):

- M1 at n=4 was 4/4 (all streams agreed). For ≥ 4/5 at n=5, v0.41
  must have m1_agrees == True. Otherwise M1 drops to 4/5 = still
  pass. Wait — 4/5 ≥ 4 trivially passes. **M1 passes the family
  bar regardless of v0.41's M1.** Even if v0.41 dissents on M1,
  M1 stays 4/5 = ≥4/5.
- M2 at n=4 was 3/4 (v0.39 dissented). For ≥ 4/5 at n=5, v0.41 must
  have m2_agrees == True (giving 4/5). If v0.41 dissents on M2, M2
  drops to 3/5 < 4/5 — fails the family bar.
- M3 at n=4 was 3/4 (v0.39 dissented). For ≥ 4/5 at n=5, v0.41 must
  have m3_agrees == True (giving 4/5). If v0.41 dissents on M3, M3
  drops to 3/5 — fails.

So family_agreement_count at n=5 is:

- 3 if v0.41 passes both M2 and M3 (M1 always passes); 2 if v0.41
  passes exactly one of {M2, M3}; 1 if v0.41 fails both M2 and M3
  (v0.41_V039_LIKE pattern).

For H5_STREAM_STABLE_N5 (m3 ≥ 4/5 AND family ≥ 2): v0.41 must pass
M3 (gives m3=4/5, family ≥ 2 since M1 always passes and M3 just
joined). So **H5_STREAM_STABLE_N5 fires iff v0.41 passes M3.**

For v0.41_OLD_LIKE (✓✓✓): all three pass; v0.41 passes M3 → H5
STREAM-STABLE-N5 fires too. **Joint: v0.41_OLD_LIKE + H5.**

For v0.41_V039_LIKE (✓✗✗): v0.41 fails M3; family drops to M1 only
(1/3) — but actually at n=5: M1=4/5 pass, M2=3/5 fail, M3=3/5 fail.
family=1; m3=3. H6 fires (m3=3 ≤ 4 and ≤ 1 false). **Joint:
v0.41_V039_LIKE + H6.**

For v0.41_NOVEL_MIXED (any other 6 cells): depends on the bitmap.
Several joint cells possible. The Results section reports the
specific pairing; no separate locked phrase.

### Anchor identity

No v0.41 cross-version artifact-identity anchor beyond row-count and
schema checks on the nine sealed input CSVs (and the three new
v0.41 extension outputs anchoring against each other within the
v0.41 fresh tier). v0.41's outputs are new derivations; by design,
they do not anchor against v0.40's output values — v0.41 reads the
same upstream sealed CSVs that v0.40 read, plus the three new v0.41
extensions.

## Decision rules

### Primary (v0.41 bitmap)

| `(m1, m2, m3)` | cell                  |
|:--------------:|:---------------------:|
| (T, T, T)      | **v0.41_OLD_LIKE**    |
| (T, F, F)      | **v0.41_V039_LIKE**   |
| any other      | **v0.41_NOVEL_MIXED** |

### Secondary (n=5 stream audit)

| `m3_count` | `family_count` | verdict                    |
|:----------:|:--------------:|----------------------------|
| 5          | ≥ 2            | **H5_STREAM_STABLE_N5**    |
| 5          | < 2            | **H6_STREAM_MIXED_N5**     |
| 4          | ≥ 2            | **H5_STREAM_STABLE_N5**    |
| 4          | < 2            | **H6_STREAM_MIXED_N5**     |
| 3          | any            | **H6_STREAM_MIXED_N5**     |
| 2          | any            | **H6_STREAM_MIXED_N5**     |
| 1          | any            | **H7_STREAM_UNSTABLE_N5**  |
| 0          | any            | **H7_STREAM_UNSTABLE_N5**  |

(H7 unreachable given known OLD M3 passes; included for completeness.)

### Halt conditions

- **H1 fails** — v0.34..v0.40 reducer surface mutated. Halt; revert.
- **H2a / H2b / H2c fail** — sealed CSV row-count drifted. Halt;
  rebuild per `docs/artifacts/v0.34_v0.41_local_corpus_manifest.md`
  (to be created post-Results).
- **H2d fails** — unexpected stream id. Halt.
- **H2e fails** — bucket count (stream × hazard) != 8. Halt.
- **H2f fails** — cross-CSV stream-key misalignment. Halt.
- **H3 / H4 fail** — a v0.21..v0.40 contract was broken by v0.41
  additions. Halt; revert.

## Out of scope (v0.41)

- New observable families. Inherits M1/M2/M3 verbatim from v0.40.
- New mechanism candidates.
- Pooled-corpus aggregation of any kind.
- Per-lineage post-50 birth-rate, mortality, extinction-tick, or
  windowed b50 — reserved for v0.42+.
- Descendant-trait drift; founder-trait observables (v0.36 lens).
- Dominance timing decomposition (v0.37 lens).
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications beyond an additive
  `V0_41_TIGHT_H_ARMS` constant (mirror of v0.32/v0.33/v0.39).
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- Mechanism declaration under any verdict.
- Edits to any prior `scripts/v0.NN_*.py`,
  `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`,
  `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`,
  `scripts/leader_advantage_replay.py`,
  `scripts/lineage_replay_v0_39_extension.py`,
  `scripts/lineage_survival_replay_v0_39_extension.py`,
  `scripts/v0_39_leader_advantage_fresh_replay.py`,
  `scripts/v0_40_stream_stability_audit.py`,
  or existing arm tuples.
- A full inventory phase. Pre-flight anchors only.

## Implementation notes

### File-level changes

- **New:** `scripts/v0.41_sweep.py` (~85 LOC, mirrors v0.39 sweep).
- **New:** `scripts/lineage_replay_v0_41_extension.py` (~150 LOC,
  mirrors v0.39 extension).
- **New:** `scripts/lineage_survival_replay_v0_41_extension.py`
  (~180 LOC, mirrors v0.39 extension).
- **New:** `scripts/leader_advantage_replay_v0_41_extension.py`
  (~200 LOC, mirrors v0.38 reducer logic over v0.41 stream).
- **New:** `scripts/v0_41_stream_classification_audit.py` (~700 LOC,
  evolves v0.40 audit pattern; adds bitmap classifier; reads 9 CSVs).
- **New:** five paired test files under `tests/`:
  - `test_v0_41_sweep.py` (~120 LOC, mirrors v0.39 sweep test).
  - `test_lineage_replay_v0_41_extension.py` (~150 LOC).
  - `test_lineage_survival_replay_v0_41_extension.py` (~150 LOC).
  - `test_leader_advantage_replay_v0_41_extension.py` (~180 LOC).
  - `test_v0_41_stream_classification_audit.py` (~600 LOC, ~40
    tests covering halts, aggregation, bitmap cells, n=5 verdict
    cells, locked-phrase regression, end-to-end synthetic).
- **One-line additive change:** `V0_41_TIGHT_H_ARMS` constant in
  [[src/hedonism_harness/experiments/comparison_grid.py]] (mirrors
  v0.39 pattern).
- **No changes** to any pre-v0.41 module.
- **Documented:** this pre-reg. Results appended after the audit
  runs.
- **Manifest:** new file
  `docs/artifacts/v0.34_v0.41_local_corpus_manifest.md` written
  post-Results. The v0.34_v0.40 manifest is preserved as a sealed
  historical record (NOT rewritten).

### Determinism contract

- v0.21..v0.40 events.jsonl + sidecar artifacts not re-read by the
  audit.
- v0.21..v0.40 test suites continue to pass.
- v0.34..v0.40 reducers imported only via importlib for helpers
  (extensions) or for `LineageReplayError` (audit).
- All anchor checks via row counts and schema parsing on sealed
  CSVs.

### LOC estimate

- Sweep + 3 extensions + audit: ~1,315 LOC.
- 5 test files: ~1,200 LOC.
- This doc: ~600 LOC.
- Manifest: ~150 LOC.

Total v0.41: ~3,265 LOC. Tests should bring the suite from 1130 to
~1,170 (+~40).

### CI gate at pre-reg time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1130 passed, 6 skipped (baseline)
uv run python scripts/core_smoke_test.py   ok
```

(Pre-reg adds no executable code; CI is identical to handoff.)

## Results

**Status:** sweep + 3 extension reducers + audit executed 2026-05-07.

### Primary verdict — `v0.41_OLD_LIKE`

The v0.41 stream's M1/M2/M3 agreement bitmap is **(True, True, True)**.
Cell: **v0.41_OLD_LIKE.**

> **Locked phrase fires verbatim:** "Seeds 33..40 reproduce the OLD-
> stream M1/M2/M3 agreement pattern in full. v0.39 is the lone outlier
> across the now-five-stream corpus and is best read as a one-off n=8
> noise excursion rather than evidence of a systematic post-v0.33
> deviation. The v0.34..v0.38 lineage-axis arc's stream-stability claim
> is reinforced from 3 of 4 streams to 4 of 5 streams. Mechanism
> promotion still requires intervention design and is not declared by
> this audit."

### Secondary verdict — `H5_STREAM_STABLE_N5`

`m3_agreement_count = 4/5`. `family_agreement_count = 3/3`.

> **Locked phrase fires verbatim:** "Lineage-axis hazard signals
> reproduce in at least four of five seed streams (v0.25 1..8, v0.32
> 9..16, v0.33 17..24, v0.39 25..32, v0.41 33..40) under the inherited
> v0.40 spread agreement rules. The v0.34..v0.38 arc's correlational
> signal upgrades from stream-stable on 4 streams to stream-stable on
> 5 streams. Mechanism promotion still requires intervention design
> and is not declared by this audit."

### Per-stream signed spreads (`runs/lineage-v0.41/per_stream_summary.csv`)

| stream | M1 spread | M1 ✓ | M2 spread | M2 ✓ | M3 spread | M3 ✓ |
|--------|----------:|:----:|----------:|:----:|----------:|:----:|
| v0.25  | +0.262    | True | +0.250    | True | **+6.125** | **True** |
| v0.32  | +0.142    | True | +0.375    | True | **+5.062** | **True** |
| v0.33  | +0.048    | True | +0.375    | True | **+3.938** | **True** |
| v0.39  | +0.017    | True | −0.250    | False | **−0.875** | **False** |
| v0.41  | +0.083    | True | +0.250    | True | **+2.031** | **True** |

### Stream × metric agreement (`runs/lineage-v0.41/stream_metric_table.csv`)

| stream | M1 | M2 | M3 |
|--------|:--:|:--:|:--:|
| v0.25  | ✓  | ✓  | ✓  |
| v0.32  | ✓  | ✓  | ✓  |
| v0.33  | ✓  | ✓  | ✓  |
| v0.39  | ✓  | ✗  | ✗  |
| v0.41  | ✓  | ✓  | ✓  |

### Metric agreement summary (`runs/lineage-v0.41/metric_summary.csv`)

| metric | n_streams_agree | rate |
|--------|----------------:|-----:|
| M1     | 5 / 5           | 1.000 |
| M2     | 4 / 5           | 0.800 |
| M3     | 4 / 5           | 0.800 |

All three metrics individually clear the ≥ 4/5 family bar; M1 unanimous.

### Per-(stream, hazard) means (`runs/lineage-v0.41/per_stream_per_hazard.csv`)

v0.41 stream alone (8 runs per hazard):

| hazard | mean_M1 | mean_M2 | mean_M3 |
|-------:|--------:|--------:|--------:|
| 0      | 0.582   | 0.375   | 4.000   |
| 4      | 0.633   | 0.375   | 4.688   |
| 8      | 0.664   | 0.500   | 5.969   |
| 12     | 0.665   | 0.625   | 6.031   |

All three metrics drift positively across hazards; M3 in particular
rises from 4.000 → 6.031 across {0, 4, 8, 12}. Spread +2.031 clears
the locked +1.5 bar with margin.

### Combined headline (`runs/lineage-v0.41/combined_summary.csv`)

> v0.41 stream classified as v0.41_OLD_LIKE; n=5 stream audit fires
> H5_STREAM_STABLE_N5 (m3=4/5, family=3/3).

### Caveats reasserted (locked, must appear in Results)

- **Per-stream n is 8.** v0.41's per-hazard means are over 8 runs
  each. M3 spread of +2.031 sits ~0.5 above the +1.5 bar — comfortable
  but not enormous. A different 8-seed draw could plausibly land
  closer to the bar.
- **M1/M2 thresholds are direction-only by design.** v0.41 passed M1
  (+0.083) and M2 (+0.250) on direction; magnitude was not the bar.
  Both are positive but smaller than the OLD streams' M1 spreads
  (v0.25 +0.262, v0.32 +0.142, v0.33 +0.048 — note v0.33's M1 is
  also small at +0.048, so v0.41's +0.083 is mid-range).
- **Magnitudes for all three metrics ARE reported** (table above);
  descriptive context for interpretation, not verdict input beyond
  M3.
- **Monotonicity is descriptive only.** v0.41 happens to be
  monotone-up on all three metrics, but monotonicity does not enter
  the verdict by design.
- **n=5 thresholds preserve the v0.40 75/25 bars.** ≥ 4/5 = 80% on
  M3, ≥ 4/5 each on family ≥ 2/3. H5_N5 fires with the strongest
  possible margin: m3=4/5 AND family=3/3.
- **No pooled-corpus verdict was computed.** v0.41 is per-stream
  only.
- **v0.41 did not investigate WHY v0.39 dissented** — only whether
  v0.41 follows the same dissent pattern. v0.41 does not, and v0.39
  is now the lone outlier across the 5-stream corpus.
- **No mechanism promotion.** Even with v0.41_OLD_LIKE +
  H5_STREAM_STABLE_N5 firing in the strongest joint cell, the arc
  remains correlational. Mechanism still requires intervention
  design.

### Reachability narrative — what we ruled out vs ruled in

- **v0.41_V039_LIKE was reachable but did not fire.** The fork test
  was genuinely live: had v0.41's M2 inverted and M3 turned negative
  (mirroring v0.39 25..32), the locked V039_LIKE phrase would have
  fired and the arc would have been pinned to OLD-only. Instead,
  v0.41's M2 spread is +0.250 (matching v0.32/v0.33's +0.375 to
  within seed-stream noise) and M3 spread is +2.031 (positive,
  above bar).
- **v0.41_NOVEL_MIXED was reachable and did not fire.** The 6 of 8
  alternative bitmaps were all live — v0.41 could have passed any
  proper subset of {M1, M2, M3} that wasn't (✓✓✓) or (✓✗✗). The
  bitmap is exactly (✓, ✓, ✓), the OLD-stream pattern.
- **H7_STREAM_UNSTABLE_N5 was unreachable a priori** given the
  three OLD streams' known M3 passes (locked at v0.40 sign-off).
  This was reasserted in pre-reg's reachability section. The
  verdict held.
- **H6_STREAM_MIXED_N5 was reachable in two pathways:** (a) v0.41
  fails M3 (would force m3=3/5 < 4/5), or (b) v0.41 passes M3 but
  causes a family metric to drop below 4/5 (impossible at n=5
  since OLD already has all three at ≥ 3/4 = 4/5 with v0.41 either
  preserving or improving). v0.41 passed M3, so neither pathway
  fired.

### Strategic update at v0.41 close

The v0.34..v0.38 lineage-axis arc is now **stream-stable across 4 of
5 seed streams** (v0.25, v0.32, v0.33, v0.41 ✓; v0.39 ✗). v0.39 is
reframed from "structurally distinct fresh stream" to "one-off n=8
noise excursion." The arc's correlational status holds; mechanism
promotion remains blocked pending intervention design.

The post-hoc reducer arc (v0.34..v0.41) is correlationally complete
on a 5-stream corpus. There is no further within-arc question that a
sixth post-hoc reducer can resolve. Future work splits along three
axes:

- **Mechanism**: intervention design (handicap the tick-50 leader
  and measure post-50 advantage collapse). Out of scope for any
  post-hoc reducer slice; requires sim-mechanics work.
- **Robustness**: per-lineage mortality (b), windowed b50 (c),
  descendant-trait drift (d) — re-opened by v0.40+v0.41's 4-of-5
  stream-stable foundation. These characterise WHAT the signal is,
  not WHETHER it survives.
- **Generalisation**: parameter-grid expansion (other influxes,
  other chambers, other founder counts) — orthogonal to the seed-
  stream calibration question that v0.39..v0.41 answered.

HedonismPolicy and Mesa remain deferred indefinitely.

### CI gate at Results time

```
uv run ruff check .             ok
uv run ruff format --check .    ok
uv run pytest                   1225 passed, 6 skipped (v0.23/v0.27 corpus
                                skips; non-regression). +95 from handoff.
uv run python scripts/core_smoke_test.py                ok
uv run python scripts/v0_41_stream_classification_audit.py
                                v0.41_OLD_LIKE + H5_STREAM_STABLE_N5
                                (re-runnable; idempotent on sealed inputs)
```
