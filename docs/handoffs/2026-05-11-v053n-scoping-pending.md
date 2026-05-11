# Handoff: v0.53m shipped; v0.53n scoping pending (lowest-sensor adversarial control)

**Date:** 2026-05-11
**Branch:** `claude/review-hedonism-harness-Ryyx0` (aligned with `origin/main` after squash-merge of PR #64; working tree clean)
**Tip commit:** `9e7418f` (v0.53m squash-merge on main)
**Status:** v0.53m shipped; coverage curve at 1/5/2/5/5/5 in the record; v0.53n locked as the next probe; **implementation NOT started — paused per user direction for handoff before next session scopes/discusses v0.53n.**

## Where we left off

This session shipped four PRs end-to-end (v0.53k #62 squash `65f5319`, v0.53l #63 squash `e271172`, v0.53m #64 squash `9e7418f`) plus a session-mid handoff. v0.53m completed the **lineage-coverage curve** at three coverage points: max-only 1/5 (v0.53l reproduction anchor, drift_abs=0.0), top-2 2/5 (NEW verdict-gating, BRIDGE_PRESENT), model-wide 5/5 (v0.53k reproduction anchor, drift_abs=0.0). Three monotone curves on the coverage axis: Label A decay `+4.4 → +1.2 → −0.0` (super-linear on food-event cells); Label B decay `+44.8 → +2.1 → +0.7` (structural-concentration channel collapse — Label B's large max-only magnitude is structural-concentration under asymmetric access, NOT a linear biological-strength measure); population survival monotone increase `0.594 → 0.672 → 0.875`. **v0.53n is locked as the immediate next probe** (per user direction this session) — non-max-lineage adversarial control, preferentially the **lowest-sensor lineage** (sharper than random; deterministic adversarial control), under the same FOOD_NEAR1 × combined-budget × n_ticks=400 envelope. Tests trait-vs-access disambiguation. User explicitly paused for handoff before scoping discussion in the next session.

## What this session shipped

- v0.53k — `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8` (PR #62 squash `65f5319`). Model-wide perception override lifted reachability `0/64 → 64/64` but collapsed Label A by construction. First priority-6 PARTIAL.
- v0.53l — `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8` (PR #63 squash `e271172`). Per-lineage override on max-sensor founder only; Label A reactivated (`+4.4/+4.4/+3.8`). **Two src/ carve-outs landed**: `run_chamber()` gained `per_founder_traits_overrides` parameter + `model.py:_spawn_founder` adopted always-consume founder-construction RNG-invariance correction. New `tests/sha_pins.py` shared-pins module; 7 prior test #8s migrated.
- v0.53m — `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8` (PR #64 squash `9e7418f`). Top-2 coverage; Label A `+1.166/+1.166/+2.347` (weakened but firing). Zero src/ changes; v0.53l-tip seams sufficient. Eight-sub-condition anchor cascade with C/E in-slice anchors both at drift_abs=0.0.
- Mid-session handoff `[[docs/handoffs/2026-05-10-v053k-pre-reg-locked.md]]` (committed earlier this session).
- This handoff `[[docs/handoffs/2026-05-11-v053n-scoping-pending.md]]` (lands at HEAD+1).

## Files touched (wikilinks for fast load)

- [[docs/experiments/fear_hunger_v0.53k.md]] — pre-reg + Results; `WIDENED_BRIDGE_PARTIALLY_RESCUED_BY_SENSOR_RADIUS_8`.
- [[docs/experiments/fear_hunger_v0.53l.md]] — pre-reg + Results; `WIDENED_BRIDGE_RESCUED_BY_MAX_LINEAGE_SENSOR_RADIUS_8`; two src/ carve-outs documented.
- [[docs/experiments/fear_hunger_v0.53m.md]] — pre-reg + Results; `WIDENED_BRIDGE_RESCUED_BY_TOP2_LINEAGE_SENSOR_RADIUS_8`; coverage curve documented.
- [[src/hedonism_harness/experiments/fear_hunger_chamber.py]] — `per_founder_traits_overrides` parameter (v0.53l carve-out 1). Chamber SHA = `e9aaca05…` (v0.53l-tip).
- [[src/hedonism_harness/model.py]] — always-consume invariant in `_spawn_founder` (v0.53l carve-out 2). Model SHA = `d4541371…` (v0.53l-tip).
- [[tests/sha_pins.py]] — shared chamber + model SHA pins (NEW v0.53l).
- [[scripts/v0_53k_perception_sensor_radius_8_audit.py]] / [[scripts/v0_53l_perception_max_lineage_sensor_radius_8_audit.py]] / [[scripts/v0_53m_perception_top2_lineage_sensor_radius_8_audit.py]] — reducers.
- [[tests/test_v0_53k_perception_sensor_radius_8_audit.py]] / [[tests/test_v0_53l_perception_max_lineage_sensor_radius_8_audit.py]] / [[tests/test_v0_53m_perception_top2_lineage_sensor_radius_8_audit.py]] — 16 tests each.

## Decisions locked in

- **`BodyConfig.effective_sensor_radius_override` vs `Traits.effective_sensor_radius_override` distinction** (per `[[src/hedonism_harness/core/sensors.py]]:138-142` resolver): per-trait field wins over body_config when both set. v0.53k uses body_config; v0.53l/m use per-trait via `per_founder_traits_overrides`.
- **Always-consume invariant is the locked behavior** for founder construction. Every founder consumes one `random_traits` draw regardless of override presence. WITHOUT this invariant, per-founder override would also shift downstream mutation-stream state, confounding the intervention. Default no-override paths byte-identical.
- **`tests/sha_pins.py` is the canonical home** for chamber + model SHAs. Science-core five files stay pinned to v0.52b-tip in each slice's test #8 Part A. Mutable seam files (chamber, model) update via the shared module on additive carve-outs.
- **Predecessor stack now ELEVEN long**: v0.53c..v0.53m — all referenced verbatim in v0.53m locked phrases.
- **v0.53n locked as immediate next probe (NOT optional).** Trait-vs-access disambiguation is the immediate scientific bottleneck after v0.53m. **Preferred intervention: lowest-sensor lineage override** (sharper adversarial control than random; random introduces sampling ambiguity).
- **Goal-tree honesty**: original project goal (late-window birth concentration) closed in v0.27–v0.33. The v0.53 series is studying the v0.48 sensor_radius bridge MECHANISM, which is downstream-of-original-goal but legitimate science. **Natural arc shape**: 1–2 more slices (v0.53n + optional v0.53o) then v0.54 synthesis / fresh-stream calibration.

## Open questions / blockers

- **v0.53n scope discussion is the immediate next-session task.** User will discuss/lock design points before drafting pre-reg.
- Specific open scope questions to expect: (1) Lowest-sensor selection rule (argmin with `min(lineage_id)` tiebreak? or some other deterministic adversarial pick?); (2) arm structure — 4 arms or 5 (carry forward C max-only + E model-wide as in-slice anchors, like v0.53m, or simpler)?; (3) verdict family naming (`MIN_LINEAGE_SENSOR_RADIUS_8` or `NONMAX_LINEAGE_SENSOR_RADIUS_8`?); (4) what does PARTIAL outcome mean here (rescue access without trait-aligned Label A firing = strong access-mediated reading).
- No `src/` changes expected for v0.53n — v0.53l-tip seams are sufficient. `tests/sha_pins.py` unchanged.

## Next concrete step

**`/resume` first; then discuss v0.53n scope with the user before drafting pre-reg.** User explicitly wants to scope/discuss in the next session, not jump straight to draft. Likely scoping shape (per user direction at end of this session): Primary question — "Does r=8 rescue Label A because the boosted lineage is the max-sensor lineage, OR because any lineage receiving r=8 gains access and dominates?" Preferred intervention — override exactly one **lowest-sensor** founder per run (deterministic adversarial control). Probable arms — A_null_V0_25 (Tier-1), B_widened_V0_25 (Tier-2), C_max_only_anchor_vs_v0.53l (anchor reproduction), D_lowest_sensor_lineage_sr8 (NEW, verdict-gating), and possibly E_modelwide_anchor_vs_v0.53k OR E_top2_anchor_vs_v0.53m. Use the established v0.53m pattern (in-slice anchors with drift_abs ≤ 1e-3; `tests/sha_pins.py` unchanged; `build_lowest_k_per_founder_overrides` or similar new helper extending v0.53l's pre-sampling pattern). After scoping is locked, draft pre-reg → implement reducer + 16-test suite via subagent (matches v0.53k/l/m pattern) → run reducer → Results → PR → squash-merge → force-align.

## Watch-outs

- **Anti-rename trap (persistent across all v0.53k/l/m builds):** when copying v0.53m templates as starting seed, predecessor refs to `v0.53m` (and earlier) in priority-4/5/6 locked phrases AND test #16 substring assertions must be PRESERVED VERBATIM, NOT bulk-replaced to v0.53n. Only the slice's own self-reference (version label, output dir, file name, current verdict name) becomes v0.53n. Predecessor stack in v0.53n locked phrases will be ELEVEN long: v0.53c..v0.53m.
- **Lowest-sensor != min-sensor-radius lineage label.** v0.48 Label A picks the MAX-sensor lineage. v0.53n's adversarial override targets a NON-Label-A lineage — the min-sensor lineage. Label A's expected behavior: if Label A STILL fires (max-sensor lineage acquires more food than non-label pool), the bridge is trait-mediated (the max-sensor lineage still wins despite no perception advantage). If Label A does NOT fire (the override-boosted min-sensor lineage wins), the bridge is access-mediated. **Sub-verdict expected to be either NOT_FOUND or wrong-sign** under the access-mediated reading — design the priority-3 halt accordingly.
- **`build_lowest_k_per_founder_overrides` helper should mirror v0.53m's `build_top_k_per_founder_overrides` shape:** returns `(overrides, bottom_lineage_ids)`. Pre-sampling pattern carries forward; the always-consume invariant guarantees deterministic founder Traits regardless of which lineages are targeted.
- **In-slice C anchor against v0.53l** uses the same drift_abs ≤ 1e-3 spec from v0.53m. v0.53m empirically observed drift_abs = 0.0 — v0.53n should reproduce.
- **Bounded-causality framing carries forward.** Locked phrases must say "consistent with trait-mediated bridge expression" not "trait-mediated bridge" (priority 4 case); "consistent with access-mediated bridge expression" not "access-mediated bridge" (priority 5 case with reachable D but no Label A firing).
- **Test #8 SHA-pinning unchanged from v0.53l-tip.** Three-part (Part A v0.52b science-core; Part B chamber via sha_pins; Part C model via sha_pins). No prior-test migration needed.
- **Holistic-assessment note (from this session's mid-discussion):** the v0.53 mechanism arc has converged to a 1–2-slice closure. v0.53n is the cleanest remaining disambiguation question. Optional v0.53o (top-3 dose-response) has lower marginal value. v0.54 synthesis is the natural arc-closing artifact. Do NOT propose v0.53o reflexively — surface the synthesis/wrap question to user after v0.53n Results.

## CI gate at handoff time

```
uv run ruff check .             ok
uv run ruff format --check .    ok (249 files already formatted)
uv run pytest                   1904 passed, 7 skipped
uv run python scripts/core_smoke_test.py  ok (all three determinism stages pass; v0.53l-tip src/ invariant intact)
```
