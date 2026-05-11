# Hedonism Harness — fear_hunger experiment index

**Status as of 2026-05-11:** v0.53 mechanism arc closed by v0.54 synthesis. Tag `fear-hunger-v0.54-arc-close` marks the arc boundary.

## Canonical interpretation

For any v0.53-era claim about the v0.48 sensor_radius spatial / foraging bridge — read **[[docs/experiments/fear_hunger_v0.54.md]] first**. It is the historical contract for what v0.53b..v0.53n observed under the tested envelope, including the claim ladder (can-claim / cannot-claim) and the explicit "not run" cells in the coverage × alignment matrix. Individual v0.53k/l/m/n slice docs hold the locked-phrase verdicts; v0.54 holds the synthesis.

## Major arc map

| arc | versions | status | closing artifact |
|---|---|---|---|
| Substrate / chamber / memory / reproduction MVP | v0.1..v0.20 | engineering complete | (see SPEC §16, §27, §13.4) |
| Aggregate-optimum audit | v0.27..v0.33 | **closed** | `H6_pool WEAK` ("directionally persistent, not mechanistically robust") |
| Lineage observability MVP | v0.34 | H7 mostly-concentrated | [[docs/experiments/fear_hunger_v0.34.md]] |
| Founder-survival timing | v0.35 | `H6 EXPANSION-SUPPORTED ≡ EARLY-LEADER CONTINUITY` | [[docs/experiments/fear_hunger_v0.35.md]] |
| Founder-trait heritability | v0.36 | `H6 TRAIT-LINKED-FLAT` (`sensor_radius` firing) | [[docs/experiments/fear_hunger_v0.36.md]] |
| v0.48 spatial / foraging bridge framework | v0.48 | bridge defined; Label A + Label B | [[docs/experiments/fear_hunger_v0.48.md]] |
| Causal-generalization on v0.48 bridge | v0.49..v0.52b | observational corpus extended | [[docs/experiments/fear_hunger_v0.52b.md]] |
| v0.53 mechanism probe (geometry × budget × horizon × perception × alignment) | v0.53..v0.53n | **closed** by v0.54 synthesis | [[docs/experiments/fear_hunger_v0.54.md]] |

Intermediate engineering slices (v0.21–v0.26, v0.37–v0.47) are best understood by reading their individual pre-regs.

## Open framing (as of 2026-05-11)

- **v0.53o (OPTIONAL).** Per-lineage trait-package + dose-response diagnostic. Only opens if the next user-directed question is to explain the v0.53n survival asymmetry (`D 0.953 > E 0.875 > C 0.594`). **Not required** to validate the v0.53 arc or the v0.54 claim ladder. Locked precondition: explicit user direction.
- **v0.55 (candidate, planning underway).** Fresh-stream calibration on an independent corpus to elevate the alignment-mediation reading from "consistent with" to "mechanism established." Analogous to the v0.30..v0.33 cross-stream pattern that closed the aggregate-optimum arc. **No empirical work has begun**; the planning pre-reg defines replication semantics and claim scope before any sweep is locked.
- **Mesa-side migration arc** (engineering; not science). Separate long-running thread referenced in [[docs/CORE_ARCHITECTURE.md]] and [[docs/SPEC.md]]. Open when dev velocity calls for it.
- **Reframe question** (project-level, not slice-level). What does this harness become — research simulator, methodological playground, publishable artifact? Latent until raised.

## How to navigate

- **Where I left off:** read the latest [[docs/handoffs/]] entry (filename-sorted, last wins). Run `/resume` skill to load it + wikilinked files.
- **Latest pre-reg:** `ls docs/experiments/fear_hunger_v*.md | sort -V | tail -1`.
- **Locked working agreement:** [[CLAUDE.md]] (per-PR cadence, re-anchor discipline, locked phrases, cautious framing, halt-loud, conservation framing).
- **Long-lived contracts:** [[docs/SPEC.md]] (sim semantics), [[docs/CORE_ARCHITECTURE.md]] (Mesa-free orchestration), [[tests/sha_pins.py]] (chamber + model SHAs at v0.53l-tip).

## Index maintenance

Update this file when:
- A new arc closes (add a row + closing artifact link).
- An "Open framing" item resolves (move to arc map; remove from open framing).
- The canonical interpretation pointer shifts (rare — happens only when a new synthesis supersedes an existing one).

Do **NOT** rewrite the canonical interpretation pointer to soften or expand a prior synthesis. v0.54 is the v0.53-arc contract; downstream work adds rows, does not retrofit existing rows.
