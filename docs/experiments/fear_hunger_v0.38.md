# v0.38 — leader post-50 reproductive advantage replay

**Status:** pre-registered 2026-05-06; reducer not yet executed.
**Date:** 2026-05-06
**Branch:** `claude/v0.38-leader-post50-advantage`
**Predecessors:** v0.21..v0.27 (aggregate-optimum audit, closed),
v0.28..v0.33 (calibration arc, closed by v0.33 H6_pool WEAK), v0.34
(lineage observability MVP — H7 mostly-concentrated at h=8;
secondary post-hoc observation: `top_lineage_b50_share` rises
monotonically with hazard 0.635 → 0.785), v0.35 (founder-survival
timing — **H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY**;
`winner_already_dominant_at_tick_50_rate` rises 0.458 → 0.708 →
0.750 → 0.792 across hazards {0, 4, 8, 12}; pre-50 founder pruning
*excluded*), v0.36 (founder-trait heritability — **H6
TRAIT-LINKED-FLAT**; sensor_radius dominant founder-trait predictor
of winning, robust at all hazards (|d| 1.18–1.35) but
hazard-flat (spread +0.082)), v0.37 (dominance timing decomposition
— **H6 STABLER-EARLY-LEADERSHIP**; O2
`leader_turnover_count_25_to_100` drops 0.333 → 0.292 → 0.167 →
0.083 (spread 0.250 = locked 0.25 threshold exactly); O1
`winner_first_leader_tick` shows large total spread (27.875 ticks)
but is non-monotone (h=4 → h=8 reverses by 2.584 ticks); supporting
O3 `margin_rank1_minus_rank2_at_tick_50` passes monotone-up +
spread (3.17 → 5.42, spread 2.25 ≥ 1.0)).
**Spec:** [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

## Question

v0.37 H6 STABLER-EARLY-LEADERSHIP fired on the v0.34 corpus: at the
locked snapshot pairs {(25→50), (50→75), (75→100)}, the
birth-count leader changes less often as hazard rises. Combined
with v0.37's supporting O3 (the rank-1-vs-rank-2 margin at tick 50
widens with hazard), the v0.37 verdict reads:

> "Hazard makes the early-leadership contest both **stabler**
> (less turnover) and **more decisive** (wider tick-50 margin)."

That is a *structural* claim about leadership stability and margin.
It does NOT directly claim that **being the tick-50 leader** confers
a post-50 *reproductive* advantage that **strengthens with hazard**.
That second-order claim is the v0.38 question:

> **Does v0.37's stabler-early-leadership signal cash out as a
> hazard-amplified post-50 reproductive advantage? Specifically:
> does the difference between the tick-50 leader's post-50 birth
> count and the mean post-50 birth count of the four non-leader
> lineages rise monotonically with hazard?**

This is a **targeted post-hoc follow-up** on v0.37. It is NOT a
sim-mechanics change, NOT a heritability mechanism declaration, NOT
a HedonismPolicy comparison, NOT a new sweep, NOT a descendant-trait
exploration, NOT a policy-stack analysis. v0.38 stays narrow on the
single question above and keeps the post-hoc reducer pattern that
v0.34..v0.37 established.

### Observable inventory (read once, before pre-reg locks)

The inventory phase ran one script
([[scripts/v0_38_inventory_scratch.py]]; will be removed before the
v0.38 PR per the cleanup convention). On 3 runs (lowest-seed at
h ∈ {0, 8, 12} from the v0.25 stream):

| haz | seed | b50_per_lineage | leader | winner | wad | L_b50 | NL_mean | lead_adv | W_b50 | overtake |
|----:|-----:|-----------------|-------:|-------:|:---:|------:|--------:|---------:|------:|---------:|
| 0   | 1    | {0:0 1:0 2:6 3:0 4:7} | 2 | 4 | False | 6 | 1.75 | +4.25 | 7 | +1 |
| 8   | 1    | {0:0 1:0 2:12 3:0 4:2} | 2 | 2 | True | 12 | 0.50 | +11.50 | 12 | 0 |
| 12  | 1    | {0:0 1:0 2:12 3:0 4:2} | 2 | 2 | True | 12 | 0.50 | +11.50 | 12 | 0 |

The inventory does NOT compute per-hazard means, deltas, or
thresholds. The inventory does NOT precommit any verdict. It exists
solely to validate observable computability and edge-case handling
before this pre-reg locks O1's spread threshold and verdict
structure.

### Observable semantics (locked, pre-committed)

- **O1 is leader-centric.** It compares the tick-50 leader's
  post-50 birth count (`b50`) against the mean `b50` of the four
  non-leader lineages, *averaged across all 24 runs at hazard h*.
  When `wad=True` (tick-50 leader IS the eventual winner — the
  majority of high-hazard runs per v0.35's wad_rate 0.46 → 0.79),
  O1 numerically equals the eventual-winner-vs-non-winners
  advantage in that run. When `wad=False`, O1 is the
  early-leader-vs-non-leaders advantage; the eventual winner is
  one of the four non-leaders in those runs, and may have its own
  post-50 advantage that O1 does NOT separately track.
- **O2 (supporting) splits the hazard trend by `wad` status.**
  Reports `mean_O1_wad_true(h)` and `mean_O1_wad_false(h)`
  separately. Diagnostic only — cannot fire any verdict. Per
  v0.35's wad_rate, the `wad=False` subset shrinks at high
  hazard (≈13/24 at h=0 to ≈5/24 at h=12); O2's per-bucket means
  may be statistically thin at h=12 in the wad=False bucket.
- **O3 (supporting) measures winner-overtake in wad=False runs.**
  `mean(b50(eventual_winner) − b50(tick50_leader))` averaged over
  wad=False runs at hazard h. A small overtake (≈ 0–2 b50)
  indicates that even when the eventual winner is NOT the tick-50
  leader, the leader still ends up near-top-of-pack on b50; a
  large overtake indicates post-50 selection is decisive over
  early-leadership status. Diagnostic only.
- **No minimum-absolute-advantage bar is locked.** The verdict
  rule is *spread-only* (and monotonicity-only), per v0.35 / v0.37
  discipline. The pre-reg explicitly does NOT claim that O1 is
  meaningfully large in absolute terms; if H6 fires, the
  Results MUST report absolute `mean_O1(h)` values descriptively
  but MUST NOT claim "leader has a substantial advantage" in the
  H6 headline.

## What this slice tests, and what it does NOT test

### Tests

- Whether **`mean_leader_post50_advantage(h)`** rises monotonically
  with hazard across the v0.34 96-run corpus.
- Whether the spread `mean_O1(12) − mean_O1(0)` clears the locked
  1.5-b50 bar (or, in the inverted direction, whether
  `mean_O1(0) − mean_O1(12)` clears the same bar).
- Whether the joint pattern fires H5 LEADER-ADVANTAGE-AMPLIFIED,
  H6 LEADER-ADVANTAGE-FLAT, or H7 LEADER-ADVANTAGE-INVERTED under
  the pre-committed three-way rule below.
- Anchor identity against v0.34's `run_summary.csv:top_lineage_id`
  AND v0.35's
  `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)` for every (source_version, arm_label,
  seed). Drift halts.
- Substrate-byte-identity: v0.34, v0.35, v0.37 reducers imported
  without modification (or, in v0.37's case, not imported — see
  Conservation framing below).

### Does NOT test

- Per-lineage policy-stack analysis. Why the leader has the
  advantage they have is not in scope.
- Heritability mechanism declaration. v0.36's sensor_radius
  finding is structurally orthogonal; not consumed here.
- Descendant-trait drift, parent-child trait deltas. Reserved
  for v0.39+ if v0.38 fires H6 (the question becomes "what other
  axis explains v0.37 H6 if not post-50 reproductive advantage?").
- Causal mechanism declaration. Even a clean H5 verdict identifies
  a *correlation* on a single corpus; promotion to mechanism
  requires fresh-stream calibration analogous to v0.30..v0.33.
- p-values or statistical significance. Effect-size / spread-only
  thresholds, consistent with v0.30..v0.37 discipline.
- Multiple-comparison-correction beyond the small-family
  pre-commitment (1 verdict-driving observable + 2 supporting).
  The 1-observable verdict family IS the family-wise control.
- Minimum-absolute-O1 bar. The verdict is spread-only +
  monotonicity-only. Whether O1 is "large" in absolute terms is
  reported descriptively in Results but is NOT a verdict input.
- HedonismPolicy comparisons. Deferred indefinitely.
- Mesa migration. Closed indefinitely.
- Sim-mechanics changes; `src/` modifications. Zero.
- New sweeps; new seed streams; new chambers; new hazards.
- Hazards outside {0, 4, 8, 12}; influxes outside {1.0}; chambers
  outside `tight_gradient`.
- O2 / O3 firing the verdict.
- Sub-snapshot leadership transitions (v0.37 caveat carried
  forward; tick-50 leadership is the locked snapshot).

### Deferred (v0.39+ candidates, conditional on v0.38 outcome)

- **If H5 LEADER-ADVANTAGE-AMPLIFIED fires.** v0.39 candidate:
  fresh-stream calibration analogous to v0.30..v0.33 — replay
  H5 on a fresh seed range to test whether the
  hazard-amplified-leader-advantage effect compounds across
  streams.
- **If H6 LEADER-ADVANTAGE-FLAT fires.** v0.39 candidate:
  per-lineage post-50 mortality / extinction-tick analysis. If
  hazard does NOT amplify the leader's reproductive advantage but
  DOES make the leader-contest stabler (v0.37 H6), the missing
  link may be hazard-amplified post-50 *mortality of the trailing
  lineages* rather than amplified reproduction of the leader.
- **If H7 LEADER-ADVANTAGE-INVERTED fires.** v0.39 candidate:
  halt and re-examine v0.37's H6 reading; an inverted O1
  contradicts the implied causal arrow from v0.37 H6. Fresh-stream
  calibration becomes the prerequisite for any continued
  interpretation.

## Conservation framing — unchanged from v0.20..v0.37

No new conservation contract. No mutations to `core/`, `model.py`,
`experiments/fear_hunger_chamber.py`,
`experiments/population_dynamics.py`,
`policies/gradient_policy.py`, `policies/hedonism_policy.py`. No
mutations to existing arm tuples. No mutations to
[[scripts/lineage_replay.py]],
[[scripts/lineage_survival_replay.py]],
[[scripts/trait_replay.py]], or
[[scripts/lock_in_timing_replay.py]]. No new event types, no new
chamber, no new policy. Source modifications are **zero**. v0.38 is
a fifth post-hoc reducer that imports v0.34 + v0.35 helpers
additively and writes new CSVs under a new output directory. v0.36
and v0.37 reducers are NOT imported (v0.36's lens is trait-axis,
v0.37's lens is timing-axis; v0.38's lens is post-50-births-axis,
structurally orthogonal to both).

## Mechanism

v0.38 is one new script plus one new tests file plus this doc.

1. **Reducer** (`scripts/leader_advantage_replay.py`). Imports v0.34
   helpers from [[scripts/lineage_replay.py]] and v0.35 helpers from
   [[scripts/lineage_survival_replay.py]] via `importlib.util` (the
   established pattern). v0.36 and v0.37 reducers are NOT imported.

   Pure-function pipeline:
   - For each run, reuse v0.35's `load_run_agents` to get
     `agent_rows + n_ticks`.
   - Compute per-lineage `b50` (count of agents with
     `born_after_tick_50 == True` per `lineage_id`); 5 lineages,
     all populated by v0.35's H2c invariant (founders alive at
     tick 50).
   - Compute `tick50_leader_id` via v0.35's
     `compute_leader_at_tick_50` (max `births_so_far(50)`,
     lowest lineage_id breaks ties).
   - Compute `eventual_top_lineage_id` via v0.35's
     `compute_eventual_top_lineage` (max `b50`, lowest lineage_id
     breaks ties; None when total_b50 == 0).
   - Compute `wad := (winner_id is not None) AND (leader_id ==
     winner_id)`.
   - Cross-anchor (halts on drift):
     - **H2a (v0.34 anchor):** re-derived `top_lineage_id` per run
       matches `runs/lineage-v0.34/run_summary.csv:top_lineage_id`
       for every (source, arm, seed).
     - **H2b (v0.35 anchor):** re-derived
       `(leader_lineage_id_at_tick_50, eventual_top_lineage_id)`
       per run matches v0.35's
       `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
       eventual_top_lineage_id)` for every (source, arm, seed).
       Both columns checked.
   - For each run, compute:
     - `leader_b50 := b50[leader_id]`.
     - `non_leader_mean_b50 := mean({b50[lid] : lid != leader_id})`
       (4 lineages).
     - `leader_advantage := leader_b50 - non_leader_mean_b50`.
     - `winner_b50 := b50[winner_id]` if winner_id else 0.
     - `winner_overtake := winner_b50 - leader_b50` if not wad
       else 0. Only meaningful in wad=False runs.
   - Per-hazard aggregation:
     - `mean_O1(h)` over all 24 runs.
     - `n_wad_true(h)`, `n_wad_false(h)` (split for O2 + O3).
     - `mean_O1_wad_true(h)` = mean leader_advantage over the
       wad=True subset at hazard h.
     - `mean_O1_wad_false(h)` = mean leader_advantage over the
       wad=False subset at hazard h.
     - `mean_winner_overtake_wad_false(h)` = mean winner_overtake
       over the wad=False subset at hazard h. Reported as `nan`
       when n_wad_false(h) == 0 (defensive; n=24 per hazard
       virtually guarantees at least one wad=False run, but the
       reducer must not divide by zero).
     - `n_no_winner(h)` = count of runs with `winner_id is None`.
       Expected 0 per v0.34's `n_runs_total_b50_zero == 0`.
       Excluded from O1 / O2 / O3 numerators.
   - Indicator pass (locked):
     - `O1_passes_up := monotone_non_decreasing(mean_O1) AND
       (mean_O1(12) - mean_O1(0) >= 1.5)`.
     - `O1_passes_down := monotone_non_increasing(mean_O1) AND
       (mean_O1(0) - mean_O1(12) >= 1.5)`.
     - O2 and O3 indicator-pass status reported but **NOT** a
       verdict input.
   - Three-way verdict (see "Decision rules" below).

   Outputs four CSVs under `runs/lineage-v0.38/` (gitignored):
   - `per_run.csv` — 96 rows: source, arm, hazard, seed,
     n_ticks, leader_lineage_id, eventual_top_lineage_id,
     wad_flag, b50_lineage_0..4 (5 columns), leader_b50,
     non_leader_mean_b50, leader_advantage, winner_b50,
     winner_overtake.
   - `per_hazard.csv` — 4 rows: hazard, n_runs, n_wad_true,
     n_wad_false, n_no_winner, mean_O1, mean_O1_wad_true,
     mean_O1_wad_false, mean_winner_overtake_wad_false.
   - `indicator_summary.csv` — 1 row (O1 only; O2 / O3 reported
     in `per_hazard.csv`): observable, verdict_role,
     monotone_pass_up, monotone_pass_down, spread_value,
     spread_threshold, threshold_passes_up, threshold_passes_down,
     indicator_passes (boolean: any direction's full rule
     fires), verdict_direction (one of "up" / "down" / "none").
   - `verdict.csv` — single row: verdict, locked_phrase,
     firing_indicator (one of "O1_up" / "O1_down" / "" for H6).

2. **Locked constants** (committed in code at reducer entry):
   ```
   LEADER_TICK: int = 50
   O1_SPREAD_THRESHOLD: float = 1.5  # post-50 birth-count units
   N_NON_LEADERS: int = 4
   EXPECTED_N_TICKS: int = 200
   V0_34_RUN_SUMMARY: Path = Path("runs/lineage-v0.34/run_summary.csv")
   V0_35_PRE_POST_DOMINANCE: Path = Path(
       "runs/lineage-v0.35/pre_post_dominance.csv"
   )
   OUT_DIR: Path = Path("runs/lineage-v0.38")
   ```

   Tie-break for "lineage selection by maximum count" operations:
   **lowest lineage_id**, mirroring v0.35 / v0.37.

### Determinism — anchors

- v0.21..v0.37 events.jsonl + sidecar artifacts on disk are not
  regenerated. Sidecars (`agent_lifetimes.csv`, `config.json`,
  `manifest.json`) are read verbatim.
- v0.21..v0.37 test suites continue to pass (additive guard).
- [[scripts/lineage_replay.py]] and
  [[scripts/lineage_survival_replay.py]] imported, not modified.
  [[scripts/trait_replay.py]] and
  [[scripts/lock_in_timing_replay.py]] not imported and not
  modified.
- Re-anchor against v0.34's `run_summary.csv:top_lineage_id` AND
  v0.35's `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)` (96 runs); halt on any drift.
- v0.34's `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` and
  `EXPECTED_FOUNDERS = 5` re-asserted at v0.38 reducer entry.

### Wall time estimate

- Reducer: < 5s on the 96-run corpus. Per-run cost is dominated by
  v0.35's `load_run_agents` (sidecar parsing); per-lineage b50
  reduction is O(N_agents_in_run).

## Observables — pre-committed before reading the data

### Per-run

- `tick50_leader_id(run)` — int in {0..4}. Computed via
  v0.35's `compute_leader_at_tick_50`.
- `eventual_top_lineage_id(run)` — int in {0..4} or None when
  total_b50 == 0. Computed via v0.35's
  `compute_eventual_top_lineage`.
- `wad(run)` — bool. True iff `winner is not None AND leader ==
  winner`.
- `b50_per_lineage(run)` — dict {0..4: int >= 0}.
- `leader_b50(run)`, `non_leader_mean_b50(run)`,
  `leader_advantage(run)` — float.
- `winner_b50(run)`, `winner_overtake(run)` — int. `winner_b50 = 0`
  and `winner_overtake = 0` when winner_id is None or wad is True.

### Per-hazard (24 runs each)

- `mean_O1(h)` — float (mean leader_advantage over all 24 runs).
- `n_wad_true(h)`, `n_wad_false(h)` — int.
- `mean_O1_wad_true(h)`, `mean_O1_wad_false(h)` — float.
  (Reported as nan when the corresponding subset is empty.)
- `mean_winner_overtake_wad_false(h)` — float. (Reported as nan
  when `n_wad_false(h) == 0`.)
- `n_no_winner(h)` — int. Expected 0 on this corpus.

### Indicator-input (locked)

- `O1_passes_up` := monotone-non-decreasing(`mean_O1` across {0,
  4, 8, 12}) AND `mean_O1(12) - mean_O1(0) >= 1.5`.
- `O1_passes_down` := monotone-non-increasing(`mean_O1`) AND
  `mean_O1(0) - mean_O1(12) >= 1.5`.

These are mutually exclusive **except** when `mean_O1` is exactly
constant across all four hazards (spread = 0). In that case,
neither directional spread bar fires (0 < 1.5), so neither
`O1_passes_up` nor `O1_passes_down` is True; H6 LEADER-ADVANTAGE-
FLAT fires. Locked rule: H6 is the default; it fires whenever
neither directional indicator fires.

### Descriptive (NOT used by verdict)

- O2: `mean_O1_wad_true(h)` and `mean_O1_wad_false(h)` per hazard.
- O3: `mean_winner_overtake_wad_false(h)` per hazard.
- Absolute O1 magnitudes: `mean_O1(h)` for each hazard (reported in
  Results regardless of verdict; the verdict does not depend on
  whether O1 is "large" in absolute terms).
- Per-run `b50` distribution (descriptive, not aggregated).

## Pre-registered hypotheses

### Strong form (substrate identity + invariants)

- **H1 (additive reuse of v0.34 + v0.35 helpers).** v0.38 imports
  v0.34's `STREAM_CONFIGS`, `parse_agent_lifetimes`,
  `parse_config`, `parse_manifest`, `assign_founder_lineages`,
  `compute_generation_depths`, `LineageReplayError`,
  `build_agent_rows`, `discover_runs`, `HAZARDS`,
  `EXPECTED_FOUNDERS`, `B_POOL_ANCHORS` from
  [[scripts/lineage_replay.py]]; and v0.35's `load_run_agents`,
  `_agents_by_lineage`, `compute_leader_at_tick_50`,
  `compute_eventual_top_lineage`,
  `is_weak_monotone_non_increasing`,
  `is_weak_monotone_non_decreasing` from
  [[scripts/lineage_survival_replay.py]]. Both modules imported
  without modification.
- **H1b (v0.34 anchor re-assertion).** `B_POOL_ANCHORS = {4: 312,
  8: 321, 12: 312}` and `EXPECTED_FOUNDERS = 5` are re-asserted at
  v0.38 reducer entry. Drift halts.
- **H2a (v0.34 anchor).** Re-derived per-run `top_lineage_id`
  MUST equal v0.34's
  `runs/lineage-v0.34/run_summary.csv:top_lineage_id` for every
  (source, arm, seed). Halts on drift.
- **H2b (v0.35 anchor — TWO columns).** Re-derived per-run
  `leader_lineage_id_at_tick_50` AND `eventual_top_lineage_id`
  MUST both equal v0.35's
  `runs/lineage-v0.35/pre_post_dominance.csv` values for every
  (source, arm, seed). Halts on drift.
- **H2c (founder count invariant).** Every run has exactly 5
  founders. Inherited from v0.34's `assign_founder_lineages`.
- **H2d (n_ticks invariant).** `n_ticks == 200` for every run.
  Halts if not.
- **H3 (additive guard).** v0.21..v0.37 prior tests still pass
  after v0.38 additions.
- **H4 (no mutation of pre-v0.38 surface).** All
  `scripts/v0.NN_*.py`, [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]],
  [[src/hedonism_harness/experiments/comparison_grid.py]],
  chamber / population / policy modules — byte-identical before
  and after v0.38.

### Cautious form — three-way verdict on v0.38's question

The decision rule is intentionally three-way (mutually exclusive
by construction). The 1-observable verdict family (O1 only) is the
family-wise control; no Bonferroni correction is applied. O2 and
O3 are supporting-only and do NOT enter the verdict.

**Per-direction indicator rules (locked):**

- `O1_passes_up` := `mean_O1(0) <= mean_O1(4) <= mean_O1(8) <=
  mean_O1(12)` AND `mean_O1(12) - mean_O1(0) >= 1.5`
  (post-50 birth-count units).
- `O1_passes_down` := `mean_O1(0) >= mean_O1(4) >= mean_O1(8) >=
  mean_O1(12)` AND `mean_O1(0) - mean_O1(12) >= 1.5`.
- O2 / O3 indicator status: reported but **NOT** verdict inputs.

**Three-way verdict (mutually exclusive):**

1. **H5 — LEADER-ADVANTAGE-AMPLIFIED.** **FIRES iff** `O1_passes_up
   == True`. Headline: tick-50 leadership's post-50 birth advantage
   rises monotonically with hazard with a meaningful spread.

2. **H6 — LEADER-ADVANTAGE-FLAT.** **FIRES iff** `O1_passes_up ==
   False AND O1_passes_down == False`. Headline: the leader
   advantage does not strengthen with hazard. Note: H6 fires
   regardless of whether `mean_O1` is large or small in absolute
   terms; it does NOT claim that an advantage exists, only that
   it does not strengthen with hazard.

3. **H7 — LEADER-ADVANTAGE-INVERTED.** **FIRES iff** `O1_passes_down
   == True`. Headline: the leader advantage *decreases*
   monotonically with hazard with a meaningful reverse-direction
   spread. Mechanistically surprising; would suggest hazard works
   against the leader's reproductive payoff.

The classifier is mutually exclusive by construction. There is no
"ROBUST" tier. v0.38 is post-hoc on a single 96-run corpus —
promotion to a robust mechanism would require fresh-stream
calibration analogous to v0.30..v0.33, which is out of scope.

### Locked phrases for each verdict

> **H5 phrase:** "Tick-50 leadership's post-50 birth advantage rises
> with hazard on the v0.34 corpus; v0.37's stabler-early-leadership
> signal cashes out as a hazard-amplified post-50 reproductive
> advantage. Correlational; not a mechanism declaration."

> **H6 phrase:** "Tick-50 leadership's post-50 birth advantage does
> not strengthen with hazard on the v0.34 corpus. v0.37's
> stabler-early-leadership signal does not map cleanly to a
> hazard-amplified post-50 reproductive advantage."

> **H7 phrase:** "Tick-50 leadership's post-50 birth advantage
> decreases with hazard on the v0.34 corpus. Mechanistically
> surprising; requires fresh-stream calibration before
> interpretation."

To be reused verbatim if the corresponding verdict fires.

### Caveats — locked, must appear in Results

- **No minimum-absolute-O1 bar.** The verdict is
  spread-only + monotonicity-only. Absolute `mean_O1(h)` values
  MUST be reported in Results descriptively, but H6 in particular
  MUST NOT be paraphrased to claim "leader has a substantial
  advantage" — H6 only claims the spread does not pass.
- **O2 (wad-split) interpretation is constrained.** The
  `wad=False` subset shrinks at high hazard (per v0.35's wad_rate
  trend). `mean_O1_wad_false(12)` may rest on n ≈ 5 runs, vs n ≈
  13 at h=0. Per-bucket trend interpretation must acknowledge
  this thinness; O2 is descriptive support only.
- **O3 winner-overtake is wad=False-only.** When wad=True,
  winner_overtake is 0 by construction (winner == leader). O3 is
  only meaningful in the wad=False subset.
- **v0.38's leader-centric framing matches v0.37's.** When wad=True
  (majority of high-hazard runs), the tick-50 leader IS the
  eventual winner, and O1 numerically equals the
  eventual-winner-vs-non-winners advantage. v0.38 does NOT make
  the additional claim that the eventual-winner advantage rises
  with hazard *because they are the eventual winner*. The
  observable is structurally about tick-50 leadership status, not
  about eventual-winner status, regardless of whether they are the
  same lineage in any given run.
- **Cautious framing locked.** "Consistent with X on the v0.34
  corpus," not "X causes Y." Even a clean H5 verdict is
  correlational on a single corpus.

### Verdict reachability — sanity check

- **H5 fires** if mean leader_advantage rises monotonically across
  {0, 4, 8, 12} with a spread of at least 1.5 b50 between h=0
  and h=12. Genuinely live: the inventory's single-run delta
  (h=0 vs h=8/12) was ~7 b50, suggesting the cross-run mean
  could land in the 1–4 range.
- **H6 fires** if the indicator is non-monotone, or if monotone
  but with insufficient spread (in either direction). Genuinely
  live: O1 may saturate or noise-out with hazard if the
  reproductive advantage is established by tick 50 and amplified
  similarly under all hazards.
- **H7 fires** if the indicator is monotone-decreasing with at
  least 1.5 b50 of spread in the reverse direction. Genuinely
  live but unexpected; the mechanism backbone of v0.37 H6
  (stabler leadership) would predict H5 if it cashes out.
  An H7 firing would force a halt and re-examination of the
  v0.37 reading.

The threshold space is genuinely live in all three regions. None
is a tail-only outcome.

### Anchor identity

No v0.38 cross-version artifact-identity anchor (no v0.38 H9).
v0.34 + v0.35 anchors already cover the underlying lineage
assignments, the tick-50 leader identity, and the eventual-winner
identity. v0.38's outputs are reductions of the same on-disk
corpus, with re-anchor against both prior reductions.

## Decision rules

| verdict | O1 condition | decision | v0.39+ candidate |
|---|---|---|---|
| H5 LEADER-ADVANTAGE-AMPLIFIED | O1_passes_up | hazard-amplified post-50 reproductive advantage of tick-50 leadership | fresh-stream calibration on H5 |
| H6 LEADER-ADVANTAGE-FLAT | neither up nor down | the v0.37 stability signal does not map to a hazard-amplified post-50 reproductive advantage | per-lineage post-50 mortality / extinction-tick analysis |
| H7 LEADER-ADVANTAGE-INVERTED | O1_passes_down | unexpected reverse-direction effect | halt and re-examine v0.37 H6 reading; fresh-stream calibration prerequisite |

**Independent of the verdict, v0.39 remains post-hoc.** v0.38
closes the targeted post-50-reproductive-advantage follow-up;
HedonismPolicy and Mesa remain deferred indefinitely.

Halt conditions:
- **H1 / H1b fail** — v0.34 / v0.35 surface mutated. Halt; revert.
- **H2a / H2b fail** — re-anchor mismatch. Halt; investigate.
- **H2c fails** — founder count != 5. Halt.
- **H2d fails** — `n_ticks != 200` for any run. Halt.
- **H3 / H4 fail** — a v0.21..v0.37 contract was broken by v0.38
  additions. Halt; revert.

## Out of scope (v0.38)

- Per-lineage policy-stack analysis.
- Heritability mechanism declaration; founder-trait observables
  consumption.
- Descendant-trait drift, parent-child trait deltas.
- p-values, statistical significance tests, Bonferroni / FDR /
  permutation tests.
- Multi-tick post-50 birth-rate trajectories (v0.38 collapses
  post-50 to a single b50 count per lineage, mirroring v0.34).
- Tick-50 LEADER-vs-non-leader trait comparison (different lens;
  v0.36 already addressed founder-trait predictors of winning).
- HedonismPolicy comparisons.
- Mesa migration.
- Sim-mechanics changes; `src/` modifications.
- New sweeps; new seed streams.
- Hazards outside {0, 4, 8, 12}.
- Influxes outside {1.0}.
- Other chambers / non-`tight_gradient`.
- Mechanism declaration. Even a clean H5 verdict identifies a
  *correlation* on a single corpus.
- Edits to any prior `scripts/v0.NN_*.py`,
  [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]], or
  [[scripts/lock_in_timing_replay.py]].
- Minimum-absolute-O1 bar (verdict is spread-only +
  monotonicity-only).

## Implementation notes

### File-level changes

- **New:** `scripts/leader_advantage_replay.py` — post-hoc reducer
  (~350 LOC). Imports `lineage_replay` and `lineage_survival_replay`
  via `importlib.util`. Defines locked constants, dataclasses
  (`PerRunRow`, `PerHazardRow`, `IndicatorSummaryRow`,
  `VerdictRow`), pure-function pipeline, three-way verdict logic,
  and `main()`.
- **New:** `tests/test_leader_advantage_replay.py` — synthetic-
  fixture tests (~350 LOC, ~28 tests). Coverage:
  - **Per-lineage b50 (3):** founder-only run; founder + post-50
    descendants; founder + pre-50-only descendants (b50 = 0 for
    those agents).
  - **leader_advantage (4):** wad=True (leader == winner);
    wad=False (leader ≠ winner); leader has b50=0 and non-leaders
    average > 0 (negative leader_advantage); all-equal b50
    (leader_advantage = 0).
  - **winner_overtake (3):** wad=True returns 0; wad=False
    positive; wad=False negative (winner has fewer b50 than
    leader — possible when v0.34's lowest-lineage_id tie-break
    picks a different lineage as eventual_top than as
    "intuitively most fertile post-50").
  - **Indicator rules (5):** monotone-up + spread-up;
    monotone-up + spread-fail; monotone-down + reverse-spread;
    non-monotone; all-equal (spread=0, neither direction fires).
  - **Three-way verdict (3):** each of H5 / H6 / H7 fires under
    its pre-committed indicator state.
  - **Re-anchor halt (3):** v0.34 mismatch, v0.35
    leader-column mismatch, v0.35 winner-column mismatch.
  - **Substrate-immutability (3):** byte-identity of imported
    v0.34 / v0.35 module hashes; helper signature stability;
    `B_POOL_ANCHORS` + `EXPECTED_FOUNDERS` re-assertion.
  - **End-to-end (2):** synthetic 4-run tmp_path tree fires
    expected verdict; CSVs written with locked headers.
  - **Sentinel-handling (2):** wad-split of empty bucket
    yields nan in mean_O1_wad_*; n_no_winner counted but
    excluded from O1 numerator.
  - Estimate ~28 tests, ~350 LOC.
- **No changes** to [[scripts/lineage_replay.py]],
  [[scripts/lineage_survival_replay.py]],
  [[scripts/trait_replay.py]],
  [[scripts/lock_in_timing_replay.py]], any
  `scripts/v0.NN_*.py`, `core/`, `model.py`, chamber / population
  / policy modules.
- **Documented:** this file. Results appended after the reducer
  runs.
- **Removed before v0.38 PR:**
  [[scripts/v0_38_inventory_scratch.py]] (committed during the
  pre-pre-reg inventory phase as audit artifact; superseded by
  the v0.38 reducer once it lands and SHOULD NOT be imported by
  it). If any of its useful logic is needed by the reducer, it is
  reimplemented inside `leader_advantage_replay.py` rather than
  imported from the scratch.

### Determinism contract

- v0.21..v0.37 events.jsonl + sidecar artifacts not regenerated.
- v0.21..v0.37 test suites continue to pass.
- v0.34 + v0.35 reducers imported but not modified. v0.36 and
  v0.37 reducers not imported (structurally orthogonal).
- Per-run double anchor against v0.34
  `run_summary.csv:top_lineage_id` and v0.35
  `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)`.

### LOC estimate

- `scripts/leader_advantage_replay.py`: ~350 LOC.
- `tests/test_leader_advantage_replay.py`: ~350 LOC.
- This doc: ~700 LOC.

Total v0.38: ~1,400 LOC. Tests should bring the suite from 1005
to ~1,033 (+~28).

### CI gate at pre-reg time

```
uv run ruff check .             ok (pre-reg-only commit; no code added)
uv run ruff format --check .    ok
uv run pytest                   1005 passed, 6 skipped (v0.23/v0.27 corpus
                                skips; non-regression)
uv run python scripts/core_smoke_test.py  ok
```

(Pre-pre-reg inventory phase added one scratch script; that is
committed but will be removed before the v0.38 PR per the cleanup
note above. Test suite is unchanged at 1005 because the scratch has
no test files.)

## References

- [[docs/experiments/fear_hunger_v0.34.md]] — v0.34 lineage
  observability MVP; supplies the per-run `top_lineage_id` anchor
  and the b50 (post-tick-50 birth count) algorithm v0.38 reuses.
- [[docs/experiments/fear_hunger_v0.35.md]] — v0.35
  founder-survival-timing replay; supplies the
  `leader_lineage_id_at_tick_50` and `eventual_top_lineage_id`
  anchors v0.38 re-anchors against; supplies the
  `compute_leader_at_tick_50` and `compute_eventual_top_lineage`
  helpers v0.38 imports.
- [[docs/experiments/fear_hunger_v0.36.md]] — v0.36
  founder-trait heritability replay; structurally orthogonal to
  v0.38 (trait-axis vs post-50-births-axis). NOT consumed.
- [[docs/experiments/fear_hunger_v0.37.md]] — v0.37 dominance
  timing decomposition; **H6 STABLER-EARLY-LEADERSHIP**; motivates
  v0.38's question (does the v0.37 stability signal cash out as
  hazard-amplified post-50 reproductive advantage?). NOT consumed
  computationally.
- [[scripts/lineage_replay.py]] — v0.34 reducer; **imported by
  v0.38 without modification**.
- [[scripts/lineage_survival_replay.py]] — v0.35 reducer;
  **imported by v0.38 without modification**.
- [[scripts/trait_replay.py]] — v0.36 reducer; NOT imported.
- [[scripts/lock_in_timing_replay.py]] — v0.37 reducer; NOT
  imported.
- [[scripts/v0_38_inventory_scratch.py]] — pre-pre-reg
  observable-computability check; audit artifact; removed before
  v0.38 PR.
- [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework".

---

## Results

**Status:** executed 2026-05-06. Reducer
([[scripts/leader_advantage_replay.py]]) ran over the same 96-run
corpus v0.34 / v0.35 / v0.37 reduced. Outputs under
`runs/lineage-v0.38/` (gitignored). Re-anchor (H2a + H2b) against
v0.34's `run_summary.csv:top_lineage_id` AND v0.35's
`pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
eventual_top_lineage_id)` passed for all 96 runs (no mismatch). All
invariants (H1, H1b, H2c, H2d, H3, H4) held.

### Headline

**Verdict: H5 — LEADER-ADVANTAGE-AMPLIFIED.** Firing direction:
**O1_up** (`mean_O1` strictly monotone non-decreasing across hazards
with spread well above the locked 1.5 threshold).

> **Locked H5 phrase:** "Tick-50 leadership's post-50 birth advantage
> rises with hazard on the v0.34 corpus; v0.37's
> stabler-early-leadership signal cashes out as a hazard-amplified
> post-50 reproductive advantage. Correlational; not a mechanism
> declaration."

### Per-hazard summary

| hazard | n_runs | n_wad_true | n_wad_false | n_no_winner | mean_O1 | mean_O1_wT | mean_O1_wF | mean_overt_wF |
|-------:|------:|-----------:|------------:|------------:|--------:|-----------:|-----------:|--------------:|
| 0      | 24    | 11         | 13          | 0           | **3.948** | 8.182    | 0.365      | 4.000         |
| 4      | 24    | 17         | 7           | 0           | 7.375   | 10.221     | 0.464      | 4.143         |
| 8      | 24    | 18         | 6           | 0           | 8.531   | 11.097     | 0.833      | 3.667         |
| 12     | 24    | 19         | 5           | 0           | **8.990** | 11.079   | 1.050      | 3.400         |

`mean_O1` is the all-runs (24 per hazard) mean of `leader_advantage`
= `b50(tick50_leader) - mean(b50(non_leaders))`. `mean_O1_wT` and
`mean_O1_wF` are the same observable computed within the
wad=True / wad=False subsets respectively. `mean_overt_wF` is the
mean `winner_overtake = b50(eventual_winner) - b50(tick50_leader)`
within the wad=False subset; meaningful only when eventual winner ≠
tick-50 leader.

### Indicator (O1 driver)

| condition | result |
|---|---|
| monotone non-decreasing across hazards | **True** (3.948 ≤ 7.375 ≤ 8.531 ≤ 8.990) |
| monotone non-increasing across hazards | False |
| spread `mean_O1(12) - mean_O1(0)` | **+5.042** |
| spread threshold | 1.5 |
| `O1_passes_up` | **True** |
| `O1_passes_down` | False |
| verdict_direction | **up** |

### Internal consistency check (not a verdict input)

`n_wad_true` per hazard matches v0.35's
`winner_already_dominant_at_tick_50_rate × 24` byte-identical:
- h=0: 11/24 = 0.458 (v0.35: 0.458) ✓
- h=4: 17/24 = 0.708 (v0.35: 0.708) ✓
- h=8: 18/24 = 0.750 (v0.35: 0.750) ✓
- h=12: 19/24 = 0.792 (v0.35: 0.792) ✓

This is a structural sanity check, not a separate anchor — both
v0.35 and v0.38 derive `wad` from the same v0.34 helpers
(`compute_leader_at_tick_50`, `compute_eventual_top_lineage`). The
match confirms that v0.38's per-run wad classification is
byte-identical to v0.35's.

### Why H5 fires (not H6 or H7)

For H7 LEADER-ADVANTAGE-INVERTED to fire, `mean_O1` would need to
decline monotonically with hazard with reverse-spread ≥ 1.5. The
observed sequence (3.948 → 7.375 → 8.531 → 8.990) is strictly
non-decreasing with positive spread of +5.042; H7 is excluded.

For H6 LEADER-ADVANTAGE-FLAT to fire, neither directional rule may
fire. `O1_passes_up` fires (monotone non-decreasing AND spread
+5.042 ≥ 1.5); H6 is excluded.

H5 fires unambiguously by the locked rule.

### Decomposition of the verdict-firing signal (descriptive)

The pooled `mean_O1` rise from 3.948 (h=0) to 8.990 (h=12) is a
spread of +5.042, ~3.4× the locked threshold. Two structural
contributors decompose this:

1. **Within-bucket effect (wad=True):** `mean_O1_wT` rises 8.182 →
   10.221 → 11.097 → 11.079 (spread +2.897 from h=0 to h=12;
   monotone for the first three steps, slight noise at h=12). Even
   when leader IS winner, the post-50 advantage grows with hazard.
2. **Bucket-shift effect (wad_rate):** the fraction of runs in the
   `wad=True` bucket rises 11/24 → 17/24 → 18/24 → 19/24 with
   hazard. Since `mean_O1_wT >> mean_O1_wF` (~10 vs ~0.7), more runs
   shifting into the high-advantage bucket as hazard rises pushes
   the pooled mean up.
3. **Within-bucket effect (wad=False):** `mean_O1_wF` rises 0.365
   → 0.464 → 0.833 → 1.050 (spread +0.685; monotone). Even when
   leader is NOT eventual winner, the leader's small advantage over
   non-leaders grows modestly with hazard.

A non-pre-committed counterfactual: holding the wad-rate fixed at
the h=0 value (11/24) for all hazards, the projected `mean_O1(12)`
would be `(11/24) × 11.079 + (13/24) × 1.050 = 5.646`. The implied
"within-bucket-only" spread would be `5.646 − 3.948 = +1.698`,
which still clears the locked 1.5 bar. The H5 firing is **not**
purely an artifact of wad-rate-shift; the within-bucket advantage
also rises. (Decomposition is descriptive only and does not change
the locked verdict.)

### Why the H5 reading is timing-locus level only (locked caveat)

- **Correlational, not mechanistic.** v0.38 identifies that
  tick-50 leadership and post-50 reproductive advantage are
  positively correlated and that the correlation strengthens with
  hazard. It does NOT declare that hazard *causes* leaders to
  reproduce more or that leadership *causes* reproductive
  advantage. Both observables are measured on the same
  end-of-window snapshot (b50 = post-tick-50 birth count) reduced
  from the same 96-run corpus.
- **No fresh-stream calibration.** Promotion to a robust mechanism
  requires fresh-stream replay (analogous to v0.30..v0.33 for the
  hazard-axis aggregate finding). v0.38 closes this single
  question on the v0.34 corpus only.
- **Compound interpretation across v0.34 / v0.35 / v0.36 / v0.37 /
  v0.38** (cautious, locked):
  - v0.34: late-window dominance share rises with hazard.
  - v0.35: pre-50 leader more often equals post-50 winner with
    hazard (wad_rate 0.46 → 0.79).
  - v0.36: founder-trait predictors of winning are large but
    hazard-flat.
  - v0.37: early-leadership turnover drops AND tick-50 margin
    widens with hazard (H6 + supporting O3); eventual-winner
    timing fails clean monotone (O1).
  - v0.38: the tick-50 leader's post-50 birth advantage rises with
    hazard (H5). Decomposition shows both within-bucket
    amplification AND bucket-shift contribution.

  Together, this points to: **hazard amplifies the post-50
  reproductive payoff of holding the early lead, and amplifies the
  probability that the early leader becomes the eventual winner**,
  on the v0.34 corpus.

### Hypothesis adjudication

| H | claim | result |
|---|---|---|
| H1 | v0.34 + v0.35 helpers imported additively; no modification | **HOLDS.** Imports succeed; constants byte-match. |
| H1b | `B_POOL_ANCHORS = {4: 312, 8: 321, 12: 312}` and `EXPECTED_FOUNDERS = 5` re-asserted | **HOLDS.** |
| H2a | Re-derived `top_lineage_id` byte-identical to v0.34 `run_summary.csv` | **HOLDS.** All 96 runs match. |
| H2b | Re-derived `(leader_lineage_id_at_tick_50, eventual_top_lineage_id)` byte-identical to v0.35 `pre_post_dominance.csv` | **HOLDS.** All 96 runs match both columns. |
| H2c | Every run has exactly 5 founders | **HOLDS.** Inherited from v0.34's `assign_founder_lineages`. |
| H2d | `n_ticks == 200` for every run | **HOLDS.** All 96 runs pass. |
| H3 | v0.21..v0.37 prior tests pass after v0.38 additions | **HOLDS.** Suite **1005 → 1039** (+34 v0.38 tests; 6 skips remain v0.23 / v0.27 corpus-dependent, non-regression); all green. |
| H4 | Pre-v0.38 surface byte-unchanged | **HOLDS.** Zero edits to `lineage_replay.py`, `lineage_survival_replay.py`, `trait_replay.py`, `lock_in_timing_replay.py`, prior `v0.NN_*.py`, `comparison_grid.py`, `core/`, `model.py`, chamber / population / policy modules. |
| H5 | LEADER-ADVANTAGE-AMPLIFIED | **FIRES.** O1 strictly monotone non-decreasing 3.948 → 7.375 → 8.531 → 8.990; spread +5.042 well above 1.5. |
| H6 | LEADER-ADVANTAGE-FLAT | **FAILS** (H5 fires). |
| H7 | LEADER-ADVANTAGE-INVERTED | **FAILS** (H5 fires). |

### Secondary observations (NOT pre-committed; descriptive only)

These are striking but explicitly outside the verdict logic. They
must not be promoted to mechanism claims without fresh-stream
calibration.

**1. Within-bucket advantage at wad=True is essentially saturated by
h=8.** `mean_O1_wT` is 8.182 / 10.221 / 11.097 / 11.079 — the h=8
to h=12 step is essentially flat (+−0.018). When the tick-50
leader IS the eventual winner, the advantage size plateaus around
~11 b50 by h=8 and does not grow further. The pooled mean_O1
continues to rise at h=12 only because of bucket-shift (more runs
falling into the wad=True bucket).

**2. Winner-overtake in wad=False runs is hazard-flat or slightly
declining.** `mean_overt_wF` is 4.00 / 4.14 / 3.67 / 3.40 — the
late-emerging winner overtakes the early leader by about 3–4 b50,
roughly independent of hazard (and slightly *declining* at high
hazard). When the eventual winner emerges from non-leadership at
tick 50, their post-50 reproductive margin over the early leader
does not grow with hazard; what changes with hazard is the *rate*
at which this scenario occurs (1 − wad_rate), not the magnitude
when it does.

**3. Leader advantage in wad=False is small but rising.** 0.365
→ 0.464 → 0.833 → 1.050. The early leader, even when they are
not the eventual winner, still has a small post-50 advantage over
the average non-leader, and that small advantage grows with
hazard. Combined with v0.37's wider tick-50 margin (O3) and
stabler turnover (O2), this is consistent with the early
leader's structural position predicting near-top-of-pack post-50
reproduction even when they don't ultimately win.

**4. Combined, the v0.34 → v0.38 arc presents a coherent
correlational story.** Hazard does multiple things in concert on
this corpus: it makes the early-leadership contest stabler
(v0.37), increases the rate at which the early leader becomes the
eventual winner (v0.35), and amplifies the post-50 reproductive
payoff of leadership status (v0.38). Founder traits (v0.36) are
robust but hazard-flat — they appear to set who can compete, not
how strongly hazard amplifies the winner's payoff. None of this
is a mechanism declaration; all of it is correlational on the
single 96-run corpus.

### Cautious forward-reference phrasing

For v0.34 / v0.35 / v0.36 / v0.37 / v0.38 forward-mention sites:

> v0.37's stabler-early-leadership signal cashes out as a
> hazard-amplified post-50 reproductive advantage on the v0.34
> corpus (v0.38 H5: `mean_leader_advantage` rises 3.948 → 8.990
> across hazards, spread +5.042 ≥ locked 1.5 bar). Decomposition
> shows the rise has two components: (a) within the wad=True
> bucket (leader == eventual winner), advantage rises 8.18 → 11.08
> (saturating around h=8); (b) the wad-rate itself rises with
> hazard per v0.35 (11/24 → 19/24 of 24 runs). Within wad=False
> runs, the late-emerging winner's overtake magnitude over the
> early leader is hazard-flat (~3–4 b50). Cautious framing locked:
> consistent with hazard-amplified post-50 reproductive payoff of
> early-leadership on the v0.34 corpus; promotion to a robust
> mechanism would require fresh-stream calibration not yet
> performed.

### Implementation summary

- **New script:** `scripts/leader_advantage_replay.py` (~485 LOC).
  Imports `lineage_replay.py` + `lineage_survival_replay.py` via
  `importlib.util`; no modification to v0.34 / v0.35 surface.
  Pure-function pipeline producing four output CSVs.
- **New tests:** `tests/test_leader_advantage_replay.py` (~520 LOC,
  **34 tests**). Suite **1005 → 1039** (+34); all green. Six
  skips remain v0.23 / v0.27 corpus artifacts (non-regression).
- **Pre-reg-locked constants in code:** `LEADER_TICK = 50`,
  `O1_SPREAD_THRESHOLD = 1.5`, `N_NON_LEADERS = 4`,
  `EXPECTED_N_TICKS = 200`.
- **Double re-anchor (with v0.35 two-column anchor):** v0.34
  `run_summary.csv:top_lineage_id` AND v0.35
  `pre_post_dominance.csv:(leader_lineage_id_at_tick_50,
  eventual_top_lineage_id)`. All 96 runs match all three columns
  byte-identical.
- **Zero edits** to `scripts/lineage_replay.py`,
  `scripts/lineage_survival_replay.py`,
  `scripts/trait_replay.py`,
  `scripts/lock_in_timing_replay.py`, prior `scripts/v0.NN_*.py`,
  `src/`, or any pre-v0.38 module.
- **Pre-pre-reg scratch removed:**
  `scripts/v0_38_inventory_scratch.py` (committed during the
  inventory phase as audit artifact; removed before the v0.38 PR
  per the locked cleanup convention).
- **CI gate at handoff time:**
  ```
  uv run ruff check .                                   ok
  uv run ruff format --check .                          ok
  uv run pytest                                         1039 passed, 6 skipped
                                                        (skips: v0.23/v0.27 corpus
                                                        artifacts; non-regression)
  uv run python scripts/core_smoke_test.py              ok
  uv run python scripts/leader_advantage_replay.py      H5 LEADER-ADVANTAGE-AMPLIFIED
                                                        (O1_up firing)
  ```

## Conclusion

v0.38 fires **H5 — LEADER-ADVANTAGE-AMPLIFIED** on the 96-run
v0.34 corpus. The mean leader_advantage = `b50(tick50_leader) -
mean(b50(non_leaders))` rises strictly monotonically across hazards
{0, 4, 8, 12}: **3.948 → 7.375 → 8.531 → 8.990**, with a total
spread of +5.042 (~3.4× the locked +1.5 bar). The locked
conjunctive rule (monotone non-decreasing AND spread ≥ 1.5) fires
unambiguously in the up direction.

The locked H5 phrase is the verdict:

> **"Tick-50 leadership's post-50 birth advantage rises with hazard
> on the v0.34 corpus; v0.37's stabler-early-leadership signal
> cashes out as a hazard-amplified post-50 reproductive advantage.
> Correlational; not a mechanism declaration."**

Decision:
- **v0.37 H6 cashes out as measurable post-50 reproductive
  advantage that strengthens with hazard.** The "stabler early
  leadership" structural signal v0.37 identified is not just
  topology — it maps to actual b50 differentials that grow with
  hazard.
- **The hazard-amplified effect decomposes into two components:**
  within-bucket amplification (when leader == winner, advantage
  size grows with hazard, plateauing by h=8) AND bucket-shift
  (more runs fall into the wad=True bucket as hazard rises). A
  descriptive counterfactual holding wad-rate fixed at h=0 still
  yields a within-bucket spread above the threshold (+1.698 ≥
  1.5), so the H5 firing is not purely an artifact of v0.35's
  wad_rate-with-hazard trend.
- **Winner-overtake in wad=False runs is hazard-flat.** When the
  late-emerging winner overtakes the early leader, they do so by
  ~3–4 b50 regardless of hazard. The hazard-axis effect is on the
  *rate* of the wad=False scenario (which decreases with hazard
  per v0.35), not on the overtake magnitude.
- **No mechanism declaration.** The five-slice arc (v0.34..v0.38)
  builds a coherent correlational story on the v0.34 corpus, but
  promotion to a robust mechanism requires fresh-stream
  calibration analogous to v0.30..v0.33.
- **v0.39+ candidates (per the pre-reg's deferred-list):**
  - **If H5 fires (this slice).** v0.39 candidate: fresh-stream
    calibration on H5 — replay the locked verdict against a fresh
    seed range to test whether the hazard-amplified-leader-
    advantage effect compounds across streams. This is the most
    direct path to mechanism promotion.
  - **Alternative v0.39 candidates** (if user direction shifts):
    per-lineage post-50 mortality / extinction-tick analysis (to
    disentangle "leader reproduces more" vs "non-leaders die more"
    as the source of leader_advantage); descendant-trait drift
    lens (the original v0.37 deferred branch, still live as a
    later slice).
