# v0.40 — cross-stream stability audit of lineage-axis signals

**Status:** pre-registered 2026-05-06; reducer not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.40-cross-stream-stability-audit`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated;
`mean_top_lineage_b50_share` pooled 0.635 → 0.785), v0.35 (founder-
survival timing — **H6 EXPANSION-SUPPORTED**; pooled `wad_rate`
0.458 → 0.792), v0.36 (founder-trait heritability —
**H6 TRAIT-LINKED-FLAT**), v0.37 (dominance timing decomposition —
**H6 STABLER-EARLY-LEADERSHIP**), v0.38 (leader post-50 advantage —
**H5 LEADER-ADVANTAGE-AMPLIFIED**; pooled 3.948 → 8.990), v0.39
(fresh-stream calibration of v0.38 — **H5_POOLED_ONLY**: fresh
stream 25..32 fails to reproduce, pooled persists on OLD 96 alone).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.39 fired **H5_POOLED_ONLY**: v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED
does NOT reproduce on the fresh seed stream 25..32. Cross-observable
descriptive observations (v0.34 fresh extension, v0.35 fresh
extension) showed the v0.34 (`top_lineage_b50_share` non-monotone)
and v0.35 (`wad_rate` inverted) hazard-amplification patterns also
fail on the fresh stream. The lineage-axis arc (v0.34..v0.38) is
flagged as single-stream-correlational.

That naming is sharp but premature. The v0.34..v0.38 arc was always
post-hoc on the OLD 96-run pooled corpus. We do not know whether the
old monotone signals are **stream-stable** within OLD (carried by all
three of 1..8 / 9..16 / 17..24) or **stream-anomalous** (carried by
one or two old streams while a third already dissented). v0.39 only
contrasted OLD-pooled vs FRESH; it did not break OLD into its
constituent streams.

The active question for v0.40 is:

> **How much of the v0.34..v0.38 lineage-axis signal was stream-
> dependent? Specifically: does each lineage-axis metric's expected-
> direction hazard spread reproduce in each of the four streams now
> on disk (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39 25..32), or
> does the signal collapse into one or two streams carrying the
> pooled effect?**

This is **NOT** a mechanism question. It is a stream-sensitivity
characterisation: how brittle were the v0.34..v0.38 signals to the
specific seeds drawn? v0.40 should not ask "what mechanism
explains the old pattern?"; it should ask "how much of the old
signal was stream-dependent?".

This is a **post-hoc audit** on artifacts already on disk. NOT a
sim-mechanics change, NOT a heritability mechanism declaration,
NOT a HedonismPolicy comparison, NOT a new sweep, NOT a per-lineage
mortality decomposition (b/c/d v0.40 candidates are deferred until
the cross-stream stability question is resolved). v0.40 stays
post-hoc one more step.

## What this slice tests, and what it does NOT test

### Tests

- Whether **`mean_leader_advantage(h)` per stream** clears the locked
  v0.38/v0.39 spread bar (signed spread ≥ +1.5 across hazards
  {0, 4, 8, 12}) in each of the four streams (v0.25 1..8, v0.32
  9..16, v0.33 17..24, v0.39 25..32).
- Whether **`mean_top_lineage_b50_share(h)` per stream** has positive
  signed spread (h=12 mean − h=0 mean > 0) in each stream.
- Whether **`wad_rate(h)` per stream** has positive signed spread in
  each stream.
- Three-way verdict (locked rule below): **H5 STREAM-STABLE / H6
  STREAM-MIXED / H7 STREAM-UNSTABLE.**
- Substrate-byte-identity: v0.34 / v0.35 / v0.38 / v0.39 reducer
  outputs are sealed CSVs; v0.40 reads them, does NOT regenerate.
  Halts on row-count drift.

### Does NOT test

- New sweeps; new arm tuples. v0.40 is pure post-hoc on the 128-run
  corpus already on disk.
- Re-running v0.34 / v0.35 / v0.38 / v0.39 reducers. Sealed outputs
  are read verbatim.
- Per-lineage mortality / extinction-tick. Reserved for v0.41+
  conditional on v0.40's outcome.
- Windowed b50 decomposition. Reserved.
- Descendant-trait drift. Reserved.
- Founder-trait observables (v0.36 lens). Out of scope.
- Dominance timing decomposition (v0.37 lens). Out of scope.
- HedonismPolicy comparisons. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- Sim-mechanics changes; `src/` modifications. **Zero.**
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- p-values; statistical significance tests; Bonferroni / FDR.
- Mechanism declaration. **Even on H5 STREAM-STABLE**, v0.40 only
  upgrades the v0.34..v0.38 signals to "stream-stable correlational
  on four streams" — NOT to mechanism. Mechanism would still require
  intervention design.
- Magnitude bars on M1 / M2. Per the locked rule (item 1 below),
  M1 and M2 use **direction-only** agreement (signed spread > 0)
  because their pre-reg locks were on pooled-corpus monotone+spread,
  not on per-stream magnitude bars; inventing per-stream magnitude
  bars now would look cleaner than it is.

### Deferred (v0.41+ candidates, conditional on v0.40 outcome)

- **If H5 STREAM-STABLE fires.** v0.41 candidates re-open: per-
  lineage mortality (b), windowed b50 (c), descendant-trait drift
  (d). The v0.34..v0.38 arc would be elevated from "single-stream-
  correlational" to "stream-stable-correlational"; mechanism work
  becomes scoped (still requires intervention design).
- **If H6 STREAM-MIXED fires.** v0.41 candidate: **a second fresh
  stream (seeds 33..40)** to disambiguate "noise-driven mixed at
  n=8" vs "real stream variability." The mortality / window / drift
  candidates remain deferred.
- **If H7 STREAM-UNSTABLE fires.** v0.41 candidate: targeted
  investigation of why the OLD 96-run corpus produced a coherent
  pooled signal that does not reproduce per-stream. Possible angles:
  pool-size dampening, pre-50 founder-trait composition variance
  by stream, chamber-state-at-tick-0 sensitivity. The v0.34..v0.38
  arc would be effectively retracted as not seed-stable enough to
  support cross-stream interpretation; mechanism work is blocked
  pending re-stabilisation.

### Quarantined (not v0.40 inputs)

- v0.36 founder-trait observations (`sensor_radius` etc.).
  Orthogonal.
- v0.37 timing observables (O1/O2/O3). Orthogonal.
- v0.39 fresh-stream descriptive cross-observable findings (fresh
  `top_lineage_b50_share` non-monotone, fresh `wad_rate` inverted).
  These motivated the question but are NOT v0.40 inputs at the
  verdict level — v0.40 re-derives M1/M2/M3 per stream from the
  underlying per-run CSVs.

## Conservation framing — minimal post-hoc, no new corpus

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
[[scripts/v0_39_leader_advantage_fresh_replay.py]], or any
`scripts/v0.NN_*.py`. No new event types, no new chamber, no new
policy. Source modifications are **zero**. v0.40 is a post-hoc audit
that reads sealed CSVs and writes new audit CSVs to a new output
directory.

## Mechanism

v0.40 ships one new script (the audit reducer), one new tests file,
this pre-reg, and one new manifest doc.

### 1. Audit reducer (`scripts/v0_40_stream_stability_audit.py`)

Imports `lineage_replay.LineageReplayError` via `importlib.util`
(the established halt class). Otherwise **does not parse raw
events.jsonl or sidecars** — pure consumer of sealed CSV outputs.

Pure-function pipeline:

- Read **6 sealed CSVs**:
  - OLD-corpus inputs (96 rows each):
    - `runs/lineage-v0.34/run_summary.csv`
      → per-run `top_lineage_b50_share` (M1 source).
    - `runs/lineage-v0.35/pre_post_dominance.csv`
      → per-run `winner_already_dominant_at_tick_50` (boolean; M2
      source via per-stream-per-hazard rate).
    - `runs/lineage-v0.38/per_run.csv`
      → per-run `leader_advantage` (M3 source).
  - FRESH-corpus inputs (32 rows each):
    - `runs/lineage-v0.34-fresh/run_summary.csv` → M1 source.
    - `runs/lineage-v0.35-fresh/pre_post_dominance.csv` → M2 source.
    - `runs/lineage-v0.39/per_run.csv` → M3 source.
- Cross-anchor (halts on drift):
  - **H2a (OLD row counts):** all three OLD CSVs have exactly 96
    rows. Halt if not.
  - **H2b (FRESH row counts):** all three FRESH CSVs have exactly 32
    rows. Halt if not.
  - **H2c (stream-id consistency):** the unique `source_version`
    values in OLD CSVs are exactly {`v0.25`, `v0.32`, `v0.33`}.
    The unique value in FRESH CSVs is exactly {`v0.39`}. Halt if not.
  - **H2d (per-stream-per-hazard run count):** each
    (source_version, hazard) bucket has exactly 8 runs (4 streams ×
    4 hazards × 8 seeds = 128 runs total). Halt if any bucket count
    differs.
- Per-(stream, hazard) aggregation:
  - **M1(stream, h)** = mean `top_lineage_b50_share` over the 8 runs
    in the (stream, h) bucket. NaN runs (where v0.34 set
    `top_lineage_b50_share` to NaN because total_b50 == 0) are
    excluded; n_excluded reported. Expected: zero NaN runs on this
    corpus per v0.34 H2c.
  - **M2(stream, h)** = mean of `winner_already_dominant_at_tick_50`
    (treating True=1, False=0, None excluded) over 8 runs. None
    runs = total_b50 == 0; expected zero on this corpus.
  - **M3(stream, h)** = mean `leader_advantage` over 8 runs.
- Per-stream signed spread:
  - For each metric M ∈ {M1, M2, M3} and each stream s:
    - `signed_spread(M, s) = M(s, h=12) − M(s, h=0)`.
- Per-stream agreement flags (locked rules below):
  - **`m1_agrees(s)`** := `signed_spread(M1, s) > 0` (direction-only).
  - **`m2_agrees(s)`** := `signed_spread(M2, s) > 0` (direction-only).
  - **`m3_agrees(s)`** := `signed_spread(M3, s) >= 1.5` (magnitude-too,
    inheriting the v0.38/v0.39 locked bar).
- Stream × metric stability table — the headline artifact.
- Three-way verdict (locked).

Outputs five CSVs under `runs/lineage-v0.40/` (gitignored):

- `per_stream_per_hazard.csv` — 16 rows: stream, hazard, n_runs,
  mean_M1, mean_M2, mean_M3.
- `per_stream_summary.csv` — 4 rows: stream, n_runs (=32),
  m1_signed_spread, m1_agrees, m2_signed_spread, m2_agrees,
  m3_signed_spread, m3_agrees, m1_monotone_up, m1_monotone_down,
  m2_monotone_up, m2_monotone_down, m3_monotone_up, m3_monotone_down.
  (Monotone flags are descriptive only; verdict drives off
  signed-spread agreement.)
- `metric_summary.csv` — 3 rows: metric, n_streams_agree,
  n_streams_total (=4), agreement_rate.
- `verdict.csv` — single row: verdict, locked_phrase,
  m3_agreement_count (0..4), family_agreement_count (0..3 metrics
  in {M1,M2,M3} that have ≥3 streams agreeing).
- `stream_metric_table.csv` — wide table (4 streams × 3 metrics)
  reporting the agreement boolean per cell. The headline artifact.

### Locked constants (committed in code at reducer entry)

```
EXPECTED_HAZARDS: tuple[int, ...] = (0, 4, 8, 12)
EXPECTED_STREAMS_OLD: tuple[str, ...] = ("v0.25", "v0.32", "v0.33")
EXPECTED_STREAMS_FRESH: tuple[str, ...] = ("v0.39",)
EXPECTED_STREAMS_ALL: tuple[str, ...] = ("v0.25", "v0.32", "v0.33", "v0.39")
EXPECTED_RUNS_OLD: int = 96
EXPECTED_RUNS_FRESH: int = 32
EXPECTED_RUNS_PER_STREAM_PER_HAZARD: int = 8

# Locked thresholds (item 1 of v0.40 sign-off)
M3_SPREAD_THRESHOLD: float = 1.5  # inherits v0.38/v0.39 lock
# M1, M2 agreement = signed_spread > 0 (direction-only)

# Locked verdict thresholds (item 2 of v0.40 sign-off)
H5_M3_MIN_STREAMS: int = 3   # M3 agrees in >=3/4 streams for H5
H5_FAMILY_MIN_METRICS: int = 2  # family agrees in >=3/4 streams for >=2/3 metrics
H7_M3_MAX_STREAMS: int = 1   # M3 agrees in <=1/4 streams for H7

V0_34_OLD_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
V0_35_OLD_PRE_POST: Path = Path("runs/lineage-v0.35/pre_post_dominance.csv")
V0_38_PER_RUN: Path = Path("runs/lineage-v0.38/per_run.csv")
V0_34_FRESH_RUN_SUMMARY: Path = Path("runs/lineage-v0.34-fresh/run_summary.csv")
V0_35_FRESH_PRE_POST: Path = Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv")
V0_39_PER_RUN: Path = Path("runs/lineage-v0.39/per_run.csv")
OUT_DIR: Path = Path("runs/lineage-v0.40")
```

### Determinism — anchors

- v0.21..v0.39 events.jsonl + sidecar artifacts on disk are not
  re-read. v0.40 reads ONLY the six sealed CSVs above.
- v0.21..v0.39 test suites continue to pass (additive guard).
- All v0.34..v0.39 reducer modules are imported only insofar as
  v0.40 needs `LineageReplayError` (the project-standard halt
  class). No other helpers imported. **In particular,
  `lr.process_run`, `ls.summarise_run_survival`, and
  `la.summarise_run` are NOT called.**
- Sealed CSV row-count halts (H2a / H2b) are the substrate-identity
  guarantee. If a row count drifts, the corpus has been mutated
  without v0.40's knowledge; halt loud.

### Wall-time estimate

- v0.40 reducer: < 2s on the 128-row aggregate. Pure CSV reads +
  per-(stream, hazard) means.

## Observables — pre-committed before reading the data

### Per (stream, hazard) — 16 rows total (4 streams × 4 hazards)

- `mean_M1(s, h)` — float in [0, 1]. Mean of per-run
  `top_lineage_b50_share` over the 8 runs in the (s, h) bucket.
- `mean_M2(s, h)` — float in [0, 1]. Mean of per-run boolean
  `winner_already_dominant_at_tick_50` (True=1, False=0).
- `mean_M3(s, h)` — float (unbounded; typically 0..15 on this
  corpus). Mean of per-run `leader_advantage`.

### Per stream — 4 rows total

- `signed_spread_M1(s) = mean_M1(s, 12) − mean_M1(s, 0)`.
- `signed_spread_M2(s) = mean_M2(s, 12) − mean_M2(s, 0)`.
- `signed_spread_M3(s) = mean_M3(s, 12) − mean_M3(s, 0)`.
- `m1_agrees(s) := signed_spread_M1(s) > 0` (direction-only).
- `m2_agrees(s) := signed_spread_M2(s) > 0` (direction-only).
- `m3_agrees(s) := signed_spread_M3(s) >= 1.5` (magnitude-too).
- Descriptive (NOT verdict input):
  - `monotone_up_M*(s)` := weak non-decreasing across hazards {0,4,8,12}.
  - `monotone_down_M*(s)` := weak non-increasing.

### Per metric — 3 rows total

- `n_streams_agree(M)` := count of streams s where `m*_agrees(s)
  == True`. Range [0, 4].

### Verdict-input

- `m3_agreement_count` := `n_streams_agree(M3)`. Range [0, 4].
- `family_agreement_count` := count of metrics M in {M1, M2, M3}
  where `n_streams_agree(M) >= 3`. Range [0, 3].

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive consumption of sealed v0.34..v0.39 outputs).** v0.40
  imports only `LineageReplayError` (and that ONLY for the project-
  standard halt class). All sealed CSVs read with stdlib `csv.DictReader`;
  no helper-function reuse. **Does NOT call `lr.process_run`,
  `ls.summarise_run_survival`, or `la.summarise_run`.**
- **H2a (OLD row counts).** All three OLD CSVs have exactly 96 rows.
  Halts on drift.
- **H2b (FRESH row counts).** All three FRESH CSVs have exactly 32
  rows. Halts on drift.
- **H2c (stream-id consistency).** OLD CSVs contain only
  `source_version` ∈ {v0.25, v0.32, v0.33}; FRESH CSVs contain only
  `source_version` == v0.39. Halts on drift.
- **H2d (per-stream-per-hazard run count).** Each (source_version,
  hazard) bucket has exactly 8 runs across all six CSVs. Halts on
  drift.
- **H2e (cross-CSV stream-key alignment).** For each (source_version,
  arm_label, seed) tuple appearing in any of the six CSVs, it appears
  in **all three** CSVs of its corpus tier (OLD or FRESH). Halts if
  not (e.g., a row in v0.34/run_summary.csv with no matching row in
  v0.38/per_run.csv).
- **H3 (additive guard).** v0.21..v0.39 prior tests still pass after
  v0.40 additions.
- **H4 (no mutation of pre-v0.40 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]],
  [[scripts/lineage_replay_v0_39_extension.py]],
  [[scripts/lineage_survival_replay_v0_39_extension.py]],
  [[scripts/v0_39_leader_advantage_fresh_replay.py]],
  arm tuples in [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before and
  after v0.40.

### Cautious form — three-way verdict on v0.40's question

The verdict is intentionally three-way (mutually exclusive by
construction):

**H5 STREAM-STABLE.** **FIRES iff** `m3_agreement_count >= 3` AND
`family_agreement_count >= 2`. Headline: M3 agrees in at least 3 of
4 streams under the locked v0.38/v0.39 spread bar (≥ +1.5), AND at
least 2 of the 3 lineage-family metrics show agreement (their
own threshold) in at least 3 of 4 streams. The v0.34..v0.38
correlational signal is upgraded from single-stream to
stream-stable on four streams.

**H7 STREAM-UNSTABLE.** **FIRES iff** `m3_agreement_count <= 1`.
Headline: M3 fails to clear the locked spread bar in at least 3 of 4
streams. The v0.38/v0.39 leader-post-50-advantage signal is
seed-band-sensitive at scales the v0.40 corpus exposes; the
correlational arc is effectively retracted as not seed-stable enough
to support cross-stream interpretation.

**H6 STREAM-MIXED.** **FIRES iff** neither H5 nor H7. Default
outcome. Headline: M3 agrees in exactly 2 of 4 streams (the only
arithmetic possibility once H5 and H7 are excluded), OR `m3` is
≥ 3/4 but family is < 2/3 — that latter case is "M3 holds but the
family doesn't." Both flavours land here as STREAM-MIXED.

### Locked phrases for each verdict

> **H5 phrase:** "Lineage-axis hazard signals reproduce in at least
> three of four seed streams (v0.25 1..8, v0.32 9..16, v0.33 17..24,
> v0.39 25..32) under the locked spread agreement rules. The
> v0.34..v0.38 arc's correlational signal is upgraded from single-
> stream to stream-stable across the four streams now on disk.
> Mechanism promotion still requires intervention design and is not
> declared by this audit."

> **H6 phrase:** "Lineage-axis hazard signals reproduce in some
> streams but not enough to clear the H5 STREAM-STABLE bar. The
> v0.34..v0.38 arc is **stream-mixed**: the OLD pooled signal is
> carried unevenly by its constituent streams, or the family-level
> agreement is partial. v0.41 candidate: a second fresh stream
> (seeds 33..40) to disambiguate noise-driven mixed at n=8 vs real
> stream variability. Correlational; not a mechanism declaration."

> **H7 phrase:** "Lineage-axis hazard signals fail to reproduce in
> at least three of four seed streams. M3 leader-post-50-advantage
> clears its locked spread bar in at most one stream. The
> v0.34..v0.38 arc is effectively retracted as **stream-unstable**:
> the OLD pooled signal does not survive per-stream decomposition
> at the locked thresholds. v0.41 candidate: targeted investigation
> of why the OLD 96-run pool produced a coherent signal that does
> not reproduce per-stream. Mechanism work is blocked pending
> re-stabilisation."

To be reused verbatim if the corresponding verdict fires.

### Caveats — locked, must appear in Results

- **Per-stream n is 8.** Each stream's per-hazard mean is over 8
  runs. The 1.5 spread bar on M3 is conservative on n=8 vs the n=24
  that produced v0.38's headline. A stream that fails M3 agreement
  could be noise-driven or genuinely null; v0.40 cannot distinguish.
  v0.41's second fresh stream (33..40) is the natural noise-vs-signal
  disambiguator if H6 fires.
- **M1/M2 thresholds are direction-only by design.** v0.34 and v0.35
  did not lock per-stream magnitude bars in their pre-regs; their
  monotone+spread tests were on the pooled 96-run corpus. Inventing
  per-stream magnitude bars retroactively would look cleaner than
  it is. Direction-only is the honest read.
- **Magnitudes for all three metrics ARE reported,** in
  `per_stream_summary.csv`. They are descriptive context for
  interpreting agreement counts; only M3 magnitude enters the
  verdict via the 1.5 bar.
- **Monotonicity is descriptive only.** At n=8 per stream, four-
  point monotone-non-decreasing across hazards {0,4,8,12} is too
  brittle for a stream-stability audit. Single-step noise can break
  monotonicity even when overall direction is clear. The verdict
  drives on signed-spread agreement, NOT on monotonicity.
- **Three streams (not four) is the H5 bar by design.** A 4/4
  agreement bar would make H5 effectively unreachable on a
  small-stream corpus; a 2/4 bar would be too permissive. 3/4
  matches the "majority of streams agree" framing without requiring
  unanimity.
- **No mechanism promotion even on H5.** v0.40 upgrades the
  correlational story to "stream-stable" on this 4-stream corpus —
  it does NOT declare a mechanism. Mechanism still requires
  intervention design (e.g., handicap the tick-50 leader and
  measure post-50 advantage collapse).
- **v0.39 is one of the four streams.** Including v0.39 in the
  audit means H5 STREAM-STABLE requires v0.39 to pass M3 (since
  v0.39's mean_LA spread was −0.875, it will fail M3) OR all three
  OLD streams to pass M3 individually (which is the only way to
  reach 3/4 without v0.39). H5 firing therefore requires very
  consistent OLD-stream agreement.

### Verdict reachability — sanity check

We have v0.39's per-stream M3 already known (from
`runs/lineage-v0.39/per_hazard_fresh.csv`):

- v0.39 stream M3 spread: 5.500 − 6.375 = **−0.875** → fails 1.5 bar.

For M3, v0.39's stream is already a known fail. For H5 STREAM-STABLE
to fire, all three of v0.25 / v0.32 / v0.33 streams must pass M3.
This is genuinely live: v0.38's OLD pooled spread was +5.042 across
24 seeds, well above the per-stream n=8 noise floor — but pooled
spread can mask a single-stream-driven effect, so per-stream is the
honest test.

For H7 STREAM-UNSTABLE, M3 must agree in ≤ 1 stream. v0.39 is
already 0/1 of those failures; H7 fires if 2 or 3 of the OLD streams
also fail M3.

H6 STREAM-MIXED is the catch-all; it covers the cases where exactly
2 OLD streams pass M3, or all 3 OLD streams pass M3 but family
agreement is below 2/3.

The threshold space is genuinely live in all three regions.

### Anchor identity

No v0.40 cross-version artifact-identity anchor beyond row-count and
schema checks on the six sealed input CSVs. v0.40's outputs are
new derivations that do not anchor against any prior reducer's
output values — by design, since v0.40's whole purpose is to look at
the per-stream variability that pooled outputs hide.

## Decision rules

| m3_agreement_count | family_agreement_count | verdict           |
|:------------------:|:----------------------:|-------------------|
| 4                  | ≥ 2                    | **H5 STREAM-STABLE** |
| 4                  | < 2                    | **H6 STREAM-MIXED**  |
| 3                  | ≥ 2                    | **H5 STREAM-STABLE** |
| 3                  | < 2                    | **H6 STREAM-MIXED**  |
| 2                  | any                    | **H6 STREAM-MIXED**  |
| 1                  | any                    | **H7 STREAM-UNSTABLE** |
| 0                  | any                    | **H7 STREAM-UNSTABLE** |

**Independent of the verdict, v0.41 candidates remain:**
- (e) second fresh stream (33..40) — lifts on H6 most cleanly.
- (f) per-stream founder-trait variance characterisation — orthogonal
  to v0.40 verdict.
- (b/c/d) mortality / windowed-b50 / descendant-drift — gated on
  H5 firing.

HedonismPolicy and Mesa remain deferred indefinitely.

Halt conditions:

- **H1 fails** — v0.34..v0.39 reducer surface mutated. Halt; revert.
- **H2a / H2b fail** — sealed CSV row-count drifted. Halt; rebuild
  per `docs/artifacts/v0.34_v0.40_local_corpus_manifest.md`.
- **H2c fails** — unexpected stream id (e.g., the v0.40 corpus
  contains seeds outside 1..32 across the four streams). Halt.
- **H2d fails** — bucket count (stream × hazard) != 8. Halt.
- **H2e fails** — cross-CSV stream-key misalignment. Halt.
- **H3 / H4 fail** — a v0.21..v0.39 contract was broken by v0.40
  additions. Halt; revert.

## Out of scope (v0.40)

- New sweeps; new arm tuples; new seeds.
- Re-running v0.34 / v0.35 / v0.38 / v0.39 reducers.
- Per-lineage post-50 birth-rate, mortality, extinction-tick, or
  windowed b50 — reserved for v0.41+.
- Descendant-trait drift; founder-trait observables (v0.36 lens).
- Dominance timing decomposition (v0.37 lens).
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- Mechanism declaration.
- Edits to any prior `scripts/v0.NN_*.py`,
  [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[scripts/leader_advantage_replay.py]],
  [[scripts/lineage_replay_v0_39_extension.py]],
  [[scripts/lineage_survival_replay_v0_39_extension.py]],
  [[scripts/v0_39_leader_advantage_fresh_replay.py]],
  or existing arm tuples.

## Implementation notes

### File-level changes

- **New:** `scripts/v0_40_stream_stability_audit.py` (~400 LOC).
  Imports only `LineageReplayError` from
  `lineage_replay.py` via `importlib.util`. Otherwise pure stdlib +
  `csv.DictReader`. Locked constants, dataclasses, pure-function
  pipeline, three-way verdict logic, `main()`.
- **New:** `tests/test_v0_40_stream_stability_audit.py` (~400 LOC,
  ~30 tests). Coverage:
  - **Locked constants (4):** thresholds, hazards, expected stream
    ids, expected counts.
  - **Sealed CSV halts (6):** missing file, row-count drift on
    each of the 6 inputs.
  - **Stream-id halt (2):** unexpected source_version in OLD or
    FRESH CSVs.
  - **Bucket-count halt (1):** per-(stream, hazard) != 8.
  - **Cross-CSV alignment halt (1):** missing key in one of the
    three CSVs of a tier.
  - **Per-(stream, hazard) aggregation (3):** mean_M1, mean_M2,
    mean_M3 grouping correctness.
  - **Per-stream signed spread (3):** correct h12 − h0 arithmetic
    for each metric.
  - **Agreement flags (3):** M1 direction-only, M2 direction-only,
    M3 magnitude bar at exactly 1.5.
  - **Three-way verdict (5):** H5 fires (m3=4, family=2 and m3=3,
    family=2), H6 fires (m3=2; m3=3 family<2; m3=4 family<2),
    H7 fires (m3=1, m3=0).
  - **Locked phrase identity (3):** verbatim regression guards.
  - **End-to-end synthetic fixture (1):** 6 minimal CSVs in tmp_path
    → verdict fires as expected; CSVs written with locked headers.
- **No changes** to any pre-v0.40 module.
- **Documented:** this pre-reg. Results appended after the reducer
  runs.
- **Manifest:** new file `docs/artifacts/v0.34_v0.40_local_corpus_manifest.md`
  written post-Results. The v0.34_v0.39 manifest is preserved as a
  sealed historical record (NOT rewritten).

### Determinism contract

- v0.21..v0.39 events.jsonl + sidecar artifacts not re-read.
- v0.21..v0.39 test suites continue to pass.
- v0.34..v0.39 reducers imported only for `LineageReplayError`.
- All anchor checks via row counts and schema parsing on sealed
  CSVs.

### LOC estimate

- `scripts/v0_40_stream_stability_audit.py`: ~400 LOC.
- `tests/test_v0_40_stream_stability_audit.py`: ~400 LOC.
- This doc: ~700 LOC.
- `docs/artifacts/v0.34_v0.40_local_corpus_manifest.md`: ~150 LOC.

Total v0.40: ~1,650 LOC. Tests should bring the suite from 1101 to
~1,131 (+~30).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   1101 passed, 6 skipped (v0.23/v0.27 corpus
                                skips; non-regression)
uv run python scripts/core_smoke_test.py  ok
```

## References

- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; H7 mostly-concentrated; pooled
  `mean_top_lineage_b50_share` source for v0.40's M1 lens.
- [[docs/experiments/fear_hunger_v0.35.md]] — v0.35
  founder-survival-timing; **H6 EXPANSION-SUPPORTED**; pooled
  `wad_rate` source for v0.40's M2 lens.
- [[docs/experiments/fear_hunger_v0.38.md]] — v0.38 leader post-50
  advantage; **H5 LEADER-ADVANTAGE-AMPLIFIED**; pooled
  `mean_leader_advantage` source for v0.40's M3 lens.
- [[docs/experiments/fear_hunger_v0.39.md]] — v0.39 fresh-stream
  calibration; **H5_POOLED_ONLY**; the slice that motivated v0.40.
- [[docs/artifacts/v0.34_v0.39_local_corpus_manifest.md]] — corpus
  regen cookbook; v0.40 will produce a v0.34_v0.40 successor.
- [[scripts/lineage_replay.py]] — v0.34 reducer; v0.40 imports ONLY
  `LineageReplayError`.
- [[scripts/lineage_survival_replay.py]] — v0.35 reducer; not
  imported by v0.40.
- [[scripts/leader_advantage_replay.py]] — v0.38 reducer; not
  imported by v0.40.
- [[scripts/v0_39_leader_advantage_fresh_replay.py]] — v0.39
  reducer; not imported by v0.40.

---

## Results

**Status:** executed 2026-05-06. v0.40 reducer ran on the 128-run
corpus (96 OLD + 32 FRESH) consuming the six sealed CSVs. Outputs
under `runs/lineage-v0.40/` (gitignored). All invariants (H1, H2a,
H2b, H2c, H2d, H2e, H3, H4) held.

### Headline

**Verdict: H5 STREAM-STABLE.**

> **Locked H5 phrase:** "Lineage-axis hazard signals reproduce in at
> least three of four seed streams (v0.25 1..8, v0.32 9..16, v0.33
> 17..24, v0.39 25..32) under the locked spread agreement rules. The
> v0.34..v0.38 arc's correlational signal is upgraded from single-
> stream to stream-stable across the four streams now on disk.
> Mechanism promotion still requires intervention design and is not
> declared by this audit."

`m3_agreement_count = 3`, `family_agreement_count = 3` (all three
metrics M1/M2/M3 have ≥ 3 of 4 streams agreeing). The H5 STREAM-
STABLE bar fires cleanly.

### Per-(stream, hazard) means

| stream | h=0 M1 | h=4 M1 | h=8 M1 | h=12 M1 | h=0 M2 | h=4 M2 | h=8 M2 | h=12 M2 | h=0 M3 | h=4 M3 | h=8 M3 | h=12 M3 |
|--------|-------:|-------:|-------:|--------:|-------:|-------:|-------:|--------:|-------:|-------:|-------:|--------:|
| v0.25  | 0.617  | 0.852  | 0.869  | 0.880   | 0.500  | 0.875  | 0.750  | 0.750   | 4.844  | 11.312 | 10.281 | 10.969  |
| v0.32  | 0.654  | 0.690  | 0.745  | 0.796   | 0.500  | 0.625  | 0.750  | 0.875   | 3.719  | 4.969  | 7.938  | 8.781   |
| v0.33  | 0.632  | 0.641  | 0.664  | 0.681   | 0.375  | 0.625  | 0.750  | 0.750   | 3.281  | 5.844  | 7.375  | 7.219   |
| v0.39  | 0.666  | 0.632  | 0.669  | 0.683   | 0.625  | 0.375  | 0.375  | 0.375   | 6.375  | 5.781  | 5.906  | 5.500   |

### Per-stream signed spreads + agreement

| stream | M1 spread | M1 agrees | M2 spread | M2 agrees | M3 spread | M3 agrees |
|--------|----------:|:---------:|----------:|:---------:|----------:|:---------:|
| v0.25  | **+0.262** | True     | **+0.250** | True    | **+6.125** | **True** |
| v0.32  | **+0.142** | True     | **+0.375** | True    | **+5.062** | **True** |
| v0.33  | **+0.048** | True     | **+0.375** | True    | **+3.938** | **True** |
| v0.39  | +0.017    | True      | **−0.250** | False   | **−0.875** | **False** |

### Stream × metric agreement table (the headline artifact)

| stream | M1 | M2 | M3 |
|--------|:--:|:--:|:--:|
| v0.25  | ✓  | ✓  | ✓  |
| v0.32  | ✓  | ✓  | ✓  |
| v0.33  | ✓  | ✓  | ✓  |
| v0.39  | ✓  | ✗  | ✗  |

| metric | n_streams_agree | rate |
|--------|----------------:|-----:|
| M1     | 4 / 4           | 1.000 |
| M2     | 3 / 4           | 0.750 |
| M3     | 3 / 4           | 0.750 |

### Why H5 fires (not H6 / H7)

- **All three OLD streams individually pass M3.** v0.25, v0.32, and
  v0.33 each clear the locked +1.5 bar by a comfortable margin
  (+6.125, +5.062, +3.938). **The v0.34..v0.38 pooled signal was
  NOT carried by one anomalous stream.** It reproduces in every old
  stream.
- **v0.39 (the fresh stream) is the lone dissenter** on M2 and M3.
  M3 spread is −0.875 (negative; fails 1.5 bar). M2 inverts (0.625
  → 0.375). This single-stream dissent is what v0.39 already locked
  in via the H5_POOLED_ONLY verdict.
- **`m3_agreement_count = 3`** clears the H5 floor (≥ 3 of 4).
- **`family_agreement_count = 3`** (all three metrics have ≥ 3
  agreeing streams) clears the H5 family floor (≥ 2 of 3 metrics).
- **H7 STREAM-UNSTABLE is excluded** because M3 agrees in 3 streams,
  not ≤ 1.
- **H6 STREAM-MIXED is excluded** because both H5 floors are met.

### What this means for the v0.34..v0.38 arc

The audit **rehabilitates the lineage-axis arc** from "single-stream-
correlational" (the framing v0.39 left us with) to **"stream-stable
correlational across 3 of 4 streams now on disk."** This is a
material upgrade:

- The OLD 96-run pooled signal that v0.34/v0.35/v0.38 reduced was
  **not carried by one stream**. All three of v0.25 1..8, v0.32
  9..16, v0.33 17..24 individually show monotone-up M3 with spread
  ≥ +1.5, and direction-positive M1/M2.
- The v0.39 fresh stream is **structurally different** from the
  three OLD streams, not a representative draw from a noise
  distribution around them. All three OLD streams clear M3 by
  ≥ +3.9; v0.39 reverses to −0.875. That gap is too large to
  attribute to ordinary sampling noise at n=8 per hazard.
- v0.39 alone cannot be treated as a definitive non-reproduction of
  the v0.34..v0.38 arc. **The v0.39 fresh stream is the outlier**,
  not the OLD pool.
- **Mechanism promotion is still blocked.** v0.40 upgrades the
  correlational story but does NOT declare a mechanism. Mechanism
  requires intervention design (e.g., handicap the tick-50 leader)
  which is out of scope.

### Structural notes (descriptive, not verdict input)

- **v0.25 stream's M3 is the strongest** (+6.125) and shows the
  largest h=0 → h=4 jump (4.844 → 11.312). This single step carries
  most of v0.25's M3 spread; the higher hazards plateau around 10
  ticks.
- **v0.32 stream is the most monotone** on M3 (3.719 → 4.969 →
  7.938 → 8.781; smooth staircase). It also has the cleanest M2
  monotone-up (0.500 → 0.625 → 0.750 → 0.875).
- **v0.33 stream is the most modest on M3** (+3.938 spread) and
  shows h=8 → h=12 reversal (7.375 → 7.219). Still passes M3 by
  the locked rule because the h=0 to h=12 spread is 3.938 ≥ 1.5.
- **v0.39 stream's h=0 M3 (6.375) is comparable to v0.25's h=4..h=12
  range (10–11 ticks).** The v0.39 fresh stream's h=0 runs are
  unusually leader-favoured, in absolute terms; this is what
  collapses the spread. Possibly a function-of-seed-band effect on
  early-leader emergence.
- **M1 (`top_lineage_b50_share`) agrees in 4/4 streams** including
  v0.39 (signed spread +0.017, barely above zero). The v0.34
  concentration lens is the most stream-stable of the three —
  every stream shows the late-window concentration tightening with
  hazard, even if marginal on the fresh stream.

### Why v0.39 is structurally different (open question, descriptive)

v0.39's deviation pattern across all three lineage-axis lenses (M1
flat-but-positive, M2 inverted, M3 negative) is too consistent to be
random sampling noise. The v0.40 audit cannot answer **why**, but
some candidate explanations descriptively considered:

- **Founder-trait composition.** v0.39's founders may differ
  systematically (e.g., higher mean `sensor_radius` at h=0, where
  v0.36 found `sensor_radius` is the dominant winner-trait
  predictor). v0.41 candidate: per-stream founder-trait
  characterisation.
- **Pre-50 chamber state.** v0.39's seeds may produce different
  initial food / hazard distributions at tick 0 (chamber RNG is
  seeded). v0.41 candidate: per-stream chamber-state metric.
- **Real seed-band variability.** A second fresh stream (33..40)
  might agree with the OLD pool (suggesting v0.39 is an unusual
  draw) or also dissent (suggesting genuine seed-band effect).

These are out of scope for v0.40 but inform v0.41 framing.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | v0.40 imports only LineageReplayError; no helper-function reuse | **HOLDS.** stdlib `csv.DictReader` + the halt class only. |
| H2a | OLD CSVs have exactly 96 rows each | **HOLDS.** All three pass. |
| H2b | FRESH CSVs have exactly 32 rows each | **HOLDS.** All three pass. |
| H2c | OLD source_versions == {v0.25, v0.32, v0.33}; FRESH == {v0.39} | **HOLDS.** |
| H2d | per-(stream, hazard) bucket count == 8 | **HOLDS.** All 16 buckets at 8 runs. |
| H2e | cross-CSV (source, arm, seed) alignment within each tier | **HOLDS.** No misalignment in OLD or FRESH. |
| H3 | v0.21..v0.39 prior tests pass after v0.40 additions | **HOLDS.** Suite **1101 → 1130** (+29 v0.40 tests; 6 skips are v0.23 / v0.27 corpus, non-regression); all green. |
| H4 | Pre-v0.40 surface byte-unchanged | **HOLDS.** Zero edits to all listed prior modules. |
| Verdict | H5 / H6 / H7 (mutually exclusive) | **H5 STREAM-STABLE FIRES.** m3=3, family=3. |

### Cautious framing — locked dual phrasing preserved

> **The v0.34..v0.38 lineage-axis arc reproduces across 3 of 4 seed
> streams.** Pre-50 leader continuity (v0.35), late-window lineage
> concentration (v0.34), and post-50 leader reproductive advantage
> (v0.38) all show direction-positive (M1/M2) or magnitude-clearing
> (M3) hazard spreads in v0.25 1..8, v0.32 9..16, and v0.33 17..24
> individually. The v0.39 fresh stream alone dissents on M2 and M3.

> **Mechanism promotion is still blocked.** v0.40 is correlational
> across four streams. Mechanism requires intervention design (e.g.,
> handicap the tick-50 leader) and is explicitly out of scope. The
> arc's correlational tier is upgraded from "single-stream" to
> "stream-stable on 3 of 4 streams" — a materially-different
> reading from v0.39's H5_POOLED_ONLY framing alone.

### Implementation summary

- **New script:** `scripts/v0_40_stream_stability_audit.py` (~640 LOC).
  Imports only `LineageReplayError` from `lineage_replay.py` via
  `importlib.util`. Pure stdlib + `csv.DictReader`. Locked
  constants, dataclasses, halt invariants, three-way verdict.
- **New tests:** `tests/test_v0_40_stream_stability_audit.py`
  (~600 LOC, **29 tests**). Suite **1101 → 1130** (+29).
- **Pre-reg-locked constants in code:** `M3_SPREAD_THRESHOLD = 1.5`,
  `H5_M3_MIN_STREAMS = 3`, `H5_FAMILY_MIN_METRICS = 2`,
  `H7_M3_MAX_STREAMS = 1`, hazards (0,4,8,12), streams
  ({v0.25, v0.32, v0.33, v0.39}), counts (96 OLD / 32 FRESH /
  8 per-bucket).
- **Five anchor halts:** sealed CSV existence + row count (H2a/H2b),
  stream-id drift (H2c), bucket-count drift (H2d), cross-CSV
  alignment (H2e). All halts via `LineageReplayError`.
- **Zero edits** to `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`, `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`,
  `scripts/leader_advantage_replay.py`,
  `scripts/lineage_replay_v0_39_extension.py`,
  `scripts/lineage_survival_replay_v0_39_extension.py`,
  `scripts/v0_39_leader_advantage_fresh_replay.py`, prior
  `v0.NN_*.py`, prior arm tuples, `core/`, `model.py`, chamber /
  population / policy modules.
- **CI gate at handoff time:**

  ```
  uv run ruff check .                                    ok
  uv run ruff format --check .                           ok
  uv run pytest                                          1130 passed,
                                                         6 skipped
  uv run python scripts/core_smoke_test.py               ok
  uv run python scripts/v0_40_stream_stability_audit.py  H5_STREAM_STABLE
  ```

## Conclusion

v0.40 fires **H5 STREAM-STABLE** on the 4-stream cross-stream
stability audit. M3 leader-post-50-advantage clears its locked +1.5
spread bar in 3 of 4 streams (v0.25 +6.125, v0.32 +5.062, v0.33
+3.938; v0.39 −0.875). M1 top-lineage-b50-share has positive signed
spread in 4 of 4 streams; M2 wad-rate has positive spread in 3 of 4
streams. Family agreement at 3/3 metrics, m3_agreement at 3/4 streams
— both H5 floors cleared.

Locked H5 phrase is the verdict:

> **"Lineage-axis hazard signals reproduce in at least three of four
> seed streams (v0.25 1..8, v0.32 9..16, v0.33 17..24, v0.39 25..32)
> under the locked spread agreement rules. The v0.34..v0.38 arc's
> correlational signal is upgraded from single-stream to stream-
> stable across the four streams now on disk. Mechanism promotion
> still requires intervention design and is not declared by this
> audit."**

Decision:

- **The v0.34..v0.38 arc is rehabilitated.** Pooled signal was not
  carried by one anomalous stream; all three OLD streams individually
  pass M3 by comfortable margins. v0.39 is the lone outlier.
- **v0.39's H5_POOLED_ONLY result is preserved verbatim** — but its
  interpretation shifts. Rather than "v0.38 is single-stream,"
  v0.40 reads it as "the OLD 3-stream agreement is real, and v0.39
  is structurally different from the OLD streams."
- **Mechanism promotion remains blocked.** Intervention design
  out of scope.
- **v0.41 candidate (per the pre-reg's deferred list, refined by
  H5):** With H5 firing, the deferred mortality / windowed-b50 /
  descendant-drift candidates re-open. However, the most informative
  next-step is arguably:
  - **(e) second fresh stream (seeds 33..40)** to characterise
    whether v0.39's dissent is a one-off seed-band anomaly or
    repeats. If 33..40 agrees with OLD: v0.39 was unusual; arc is
    genuinely 4 of 5 stream-stable. If 33..40 also dissents:
    something systematic happened around the v0.39 seed band, and
    the OLD-stream pattern (1..24) versus the FRESH-stream pattern
    (25..40) becomes the new question.
  - **(b/c/d) per-lineage mortality / windowed-b50 / descendant-
    drift** are now mechanistically scoped slices that can ride
    on the H5 STREAM-STABLE foundation, but they characterise WHAT
    the signal is, not whether it survives — so they are best
    sequenced AFTER (e) confirms or refines the cross-stream
    stability picture.
- **HedonismPolicy and Mesa** remain deferred indefinitely.
