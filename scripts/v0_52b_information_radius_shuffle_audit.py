"""v0.52b sensor_radius information-radius assignment shuffle (first-class intervention).

Pre-reg: [[docs/experiments/fear_hunger_v0.52b.md]]. Question: does the
sensor_radius spatial / foraging bridge depend on between-lineage
information-radius assignment when the global information economy is preserved?

Corpus (locked, same as v0.46-v0.52): A_null arm only across v0.42 / v0.43R
/ v0.44 / v0.45, hazards {0, 8}, seeds 41..72. 64 runs per arm; 2 arms;
128 runs total.

Arms (locked):
  A_null:                                  default V0_25 (no per-agent / per-model overrides).
  B_effective_radius_shuffle_distribution: shuffle effective sensing radius
                                           across founders by permuting their
                                           original sensor_radius values into
                                           each founder's traits.effective_sensor_radius_override.
                                           Trait sensor_radius UNCHANGED;
                                           apply_metabolism still reads trait;
                                           descendants inherit the override
                                           via mutate_traits (Option alpha).

Lineage-coherent inheritance via mutate_traits (Option alpha, locked): the
v0.52b src/ change widens mutate_traits to use dataclasses.replace(parent,
**values), which preserves any field on parent not in TRAIT_NAMES (the
override is filtered out of TRAIT_NAMES). No AgentBorn listener is required
for inheritance. An AgentBorn listener IS registered for descendant
auditing — counts inheritance vs missing.

Halt-loud invariant: any descendant under arm B with
effective_sensor_radius_override=None at AgentBorn-emit time fires
SHUFFLE_DESCENDANT_INHERITANCE_HALT (priority 4).

Primary observables (locked, identical to v0.48-v0.52):
  pre50_food_events_count           (+)
  pre50_food_energy_acquired        (+)
  mean_distance_to_nearest_food_cell(-)

Labels (both gate for both arms):
  Label A: argmax(traits.effective_sensor_radius_override if not None
           else int(traits.sensor_radius)), tiebreak min(lineage_id).
           Under A_null falls through to trait; identical to v0.48-v0.52
           Label A. Under B picks by ASSIGNED effective override.
  Label B: identical to v0.47-v0.52 (3-tier readiness fraction tiebreak).

Effect-size rule (locked, sign-aware, identical to v0.48-v0.52):
  signed_d = paired_d * expected_sign
  fires iff signed_d >= +0.5
  halts iff signed_d <= -0.5

Per-arm sub-verdicts (locked):
  A_null:     A_NULL_BRIDGE_PRESENT / _PARTIAL / _NOT_FOUND / _OPPOSITE_SIGN_HALT
  B_shuffle:  B_SHUFFLE_BRIDGE_PRESENT / _PARTIAL / _NOT_FOUND / _OPPOSITE_SIGN_HALT

Slice rollup (locked, 7 outcomes, priority-ordered):
  1. CORPUS_REDERIVE_DRIFT_HALT
  2. INTERVENTION_OPPOSITE_SIGN_HALT
  3. BRIDGE_REPLICATION_HALT             (A_null vs v0.48; only Tier-1)
  4. SHUFFLE_DESCENDANT_INHERITANCE_HALT (lineage coherence guard)
  5. INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT          (A_null PRESENT, B PRESENT)
  6. INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT  (A_null PRESENT, B NOT_FOUND)
  7. INFORMATION_RADIUS_ASSIGNMENT_PARTIAL          (A_null PRESENT, B PARTIAL)

Conservation framing (one minimal default-preserving src/ extension):
no traits_override; no biologically-mutable trait modified; no Mesa cell
modification; no descendant-time intervention beyond mechanical inheritance.

Usage:
    uv run python scripts/v0_52b_information_radius_shuffle_audit.py
    uv run python scripts/v0_52b_information_radius_shuffle_audit.py \
        --out-dir runs/v0.52b-information-radius-shuffle
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import math
import statistics
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from hedonism_harness.core.events import (
    AgentBorn,
    AteFood,
    HazardDamageApplied,
    signal_for,
)
from hedonism_harness.core.interventions import KIND_NULL, InterventionConfig
from hedonism_harness.core.traits import TraitConfig, Traits
from hedonism_harness.experiments.comparison_grid import (
    FIXED_ENERGY_COST,
    FIXED_ENERGY_THRESHOLD,
    V0_42_INTERVENTION_ARMS,
    V0_43R_INTERVENTION_ARMS,
    V0_44_INTERVENTION_ARMS,
    V0_45_INTERVENTION_ARMS,
    Arm,
    _resolve_layout,
    tuned_reproduction_config,
)
from hedonism_harness.experiments.fear_hunger_chamber import run_chamber
from hedonism_harness.model import HHModel

# ---------------------------------------------------------------------------
# Locked configuration (pre-reg)
# ---------------------------------------------------------------------------

SEEDS_BY_VERSION: dict[str, tuple[int, ...]] = {
    "v0.42": tuple(range(41, 49)),
    "v0.43R": tuple(range(49, 57)),
    "v0.44": tuple(range(57, 65)),
    "v0.45": tuple(range(65, 73)),
}

HAZARDS: tuple[int, ...] = (0, 8)
N_TICKS: int = 200
N_FOUNDERS: int = 5
TICK_50: int = 50
LAYOUT_NAME: str = "tight_gradient"

# Arms (locked).
ARM_A_NULL: str = "A_null"
ARM_B_SHUFFLE: str = "B_effective_radius_shuffle_distribution"
ARMS: tuple[str, ...] = (ARM_A_NULL, ARM_B_SHUFFLE)

# Hardcoded re-anchor reference values (A_null arm only; Tier-1 only).
PUBLISHED_A_SHARE_H8: dict[str, float | None] = {
    "v0.42": 0.652,
    "v0.43R": None,
    "v0.44": 0.878,
    "v0.45": 0.818,
}
RE_ANCHOR_DRIFT_TOLERANCE: float = 1e-3

COHENS_D_THRESHOLD: float = 0.5

EXPECTED_FOUNDERS: int = 5

# Primary observables (identical to v0.48-v0.52).
PRIMARY_OBSERVABLES: tuple[tuple[str, int], ...] = (
    ("pre50_food_events_count", +1),
    ("pre50_food_energy_acquired", +1),
    ("mean_distance_to_nearest_food_cell", -1),
)

# Label fields and names.
LABEL_A_FIELD = "is_high_information_radius_lineage"
LABEL_B_FIELD = "is_high_tick50_readiness_fraction_lineage"
LABEL_A_NAME = "label_a_information_radius"
LABEL_B_NAME = "label_b_readiness_fraction"

# v0.48's published bridge cells (label, observable) -> signed_d.
# v0.52b's Label A under A_null resolves to int(body.traits.sensor_radius)
# (override is None) — identical to v0.48-v0.52 Label A. The Tier-1 cells
# therefore reproduce v0.48 byte-equivalently under A_null.
V048_PUBLISHED_SIGNED_D: dict[tuple[str, str], float] = {
    (LABEL_A_NAME, "pre50_food_events_count"): +1.066,
    (LABEL_A_NAME, "pre50_food_energy_acquired"): +1.066,
    (LABEL_A_NAME, "mean_distance_to_nearest_food_cell"): +1.916,
    (LABEL_B_NAME, "pre50_food_events_count"): +0.916,
    (LABEL_B_NAME, "pre50_food_energy_acquired"): +0.916,
    (LABEL_B_NAME, "mean_distance_to_nearest_food_cell"): +1.179,
}

# Per-arm sub-verdicts.
SUBVERDICT_A_NULL_PRESENT = "A_NULL_BRIDGE_PRESENT"
SUBVERDICT_A_NULL_PARTIAL = "A_NULL_BRIDGE_PARTIAL"
SUBVERDICT_A_NULL_NOT_FOUND = "A_NULL_BRIDGE_NOT_FOUND"
SUBVERDICT_A_NULL_OPPOSITE = "A_NULL_BRIDGE_OPPOSITE_SIGN_HALT"

SUBVERDICT_B_PRESENT = "B_SHUFFLE_BRIDGE_PRESENT"
SUBVERDICT_B_PARTIAL = "B_SHUFFLE_BRIDGE_PARTIAL"
SUBVERDICT_B_NOT_FOUND = "B_SHUFFLE_BRIDGE_NOT_FOUND"
SUBVERDICT_B_OPPOSITE = "B_SHUFFLE_OPPOSITE_SIGN_HALT"

# Slice rollup verdicts (locked, priority-ordered).
ROLLUP_CORPUS_DRIFT_HALT = "CORPUS_REDERIVE_DRIFT_HALT"
ROLLUP_INTERVENTION_OPPOSITE_HALT = "INTERVENTION_OPPOSITE_SIGN_HALT"
ROLLUP_BRIDGE_REPLICATION_HALT = "BRIDGE_REPLICATION_HALT"
ROLLUP_SHUFFLE_INHERITANCE_HALT = "SHUFFLE_DESCENDANT_INHERITANCE_HALT"
ROLLUP_FOLLOWS_ASSIGNMENT = "INFORMATION_RADIUS_FOLLOWS_ASSIGNMENT"
ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT = "INFORMATION_RADIUS_DOES_NOT_FOLLOW_ASSIGNMENT"
ROLLUP_ASSIGNMENT_PARTIAL = "INFORMATION_RADIUS_ASSIGNMENT_PARTIAL"

# Locked phrases (verbatim per pre-reg).
LOCKED_PHRASES: dict[str, str] = {
    ROLLUP_CORPUS_DRIFT_HALT: (
        "Halt: A_null re-anchor drifted from the published Results value for {version}; "
        "v0.52b's deterministic re-execution does not reproduce the published metric within "
        "1e-3."
    ),
    ROLLUP_INTERVENTION_OPPOSITE_HALT: (
        "Halt: a v0.52b spatial / foraging primary fires in the WRONG direction under a "
        "gating label; the between-lineage information-radius shuffle is incompatible with "
        "the locked expected signs."
    ),
    ROLLUP_BRIDGE_REPLICATION_HALT: (
        "Halt: v0.52b's A_null arm does not reproduce v0.48's spatial bridge — either a "
        "paired_d cell drifts beyond 1e-3 of the published value, or the A_null sub-verdict "
        "does not resolve to PRESENT. v0.52b cannot interpret the B arm without an "
        "established baseline."
    ),
    ROLLUP_SHUFFLE_INHERITANCE_HALT: (
        "Halt: at least one descendant agent in v0.52b's shuffle arm has "
        "`effective_sensor_radius_override = None` at end-of-run, violating lineage "
        "coherence. v0.52b cannot interpret the shuffle arm without verified descendant "
        "inheritance."
    ),
    ROLLUP_FOLLOWS_ASSIGNMENT: (
        "On the modern A_null corpus with global information economy preserved "
        "(between-lineage shuffle of effective `sensor_radius` over a corpus-wide "
        "preserved distribution), the v0.48 spatial / foraging bridge follows the "
        "assigned effective information radius. The information-radius assignment is "
        "sufficient to track the bridge under the locked V0_25 anchor."
    ),
    ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT: (
        "On the modern A_null corpus with global information economy preserved, the "
        "v0.48 spatial / foraging bridge does not follow the assigned effective "
        "information radius under between-lineage shuffle. The original trait/lineage "
        "package or another confound is implicated; the information-radius assignment "
        "alone is not sufficient to track the bridge."
    ),
    ROLLUP_ASSIGNMENT_PARTIAL: (
        "On the modern A_null corpus, v0.52b's shuffle arm does not resolve to a single "
        "categorical outcome under the locked criteria; the bridge fires under one label "
        "but not the other. The planned v0.52b uniform-4 secondary follow-up is "
        "recommended for disambiguation."
    ),
}


class V052bReducerError(Exception):
    """Halt condition raised when a v0.52b invariant is violated."""


# ---------------------------------------------------------------------------
# Per-run capture (per-arm)
# ---------------------------------------------------------------------------


@dataclass
class _TickRecord:
    tick: int
    agents: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    food_cells: tuple[tuple[int, int], ...] = ()
    hazard_cells: tuple[tuple[int, int], ...] = ()


@dataclass
class _Tick50Readiness:
    agent_id: int
    lineage_id: int
    energy: float
    age: int


@dataclass
class _FounderRecord:
    """Per-founder original / assigned snapshot for the v0.52b audit.

    Captured from live ``model.agents`` post-patch — NOT from
    ``model.trait_fingerprints``.
    """

    lineage_id: int
    founder_index: int
    founder_original_sensor_radius: int
    founder_assigned_effective_sensor_radius: int  # equals original under A_null
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    permutation_map_index: int  # equals founder_index under A_null
    applied_identity_rotation_fallback: bool  # False under A_null


@dataclass
class _DescendantInheritanceCounters:
    """Per-run descendant-audit counters (B arm only).

    Incremented by an AgentBorn listener that does NOT modify state — it
    reads each newborn body's traits.effective_sensor_radius_override and
    classifies as inherited (non-None) vs missing (None).
    """

    n_births_seen: int = 0
    n_overrides_inherited: int = 0
    n_overrides_missing: int = 0


@dataclass
class _RunCapture:
    arm: str
    version: str
    seed: int
    hazard: int
    tick_records: dict[int, _TickRecord] = field(default_factory=dict)
    tick50_readiness: list[_Tick50Readiness] = field(default_factory=list)
    birth_tick_by_agent: dict[int, int] = field(default_factory=dict)
    lineage_by_agent: dict[int, int] = field(default_factory=dict)
    founder_records: list[_FounderRecord] = field(default_factory=list)
    descendant_counters: _DescendantInheritanceCounters = field(
        default_factory=_DescendantInheritanceCounters
    )
    pre50_food_events_by_agent: dict[int, int] = field(default_factory=dict)
    pre50_food_energy_by_agent: dict[int, float] = field(default_factory=dict)
    pre50_hazard_damage_events_by_agent: dict[int, int] = field(default_factory=dict)
    n_observer_fires: int = 0
    energy_threshold: float = 0.0
    min_age: int = 0
    effective_sensor_radius_changed_count: int = 0


def _select_a_null_arm(version: str, hazard: int) -> Arm:
    armset = {
        "v0.42": V0_42_INTERVENTION_ARMS,
        "v0.43R": V0_43R_INTERVENTION_ARMS,
        "v0.44": V0_44_INTERVENTION_ARMS,
        "v0.45": V0_45_INTERVENTION_ARMS,
    }[version]
    candidates = [a for a in armset if "A_null" in a.label and a.hazard_damage == hazard]
    if len(candidates) != 1:
        msg = (
            f"v0.52b: failed to find unique A_null arm for {version} h={hazard}; "
            f"got {len(candidates)} candidates"
        )
        raise V052bReducerError(msg)
    return candidates[0]


# ---------------------------------------------------------------------------
# Shuffle helpers (founder permutation + single-channel invariant)
# ---------------------------------------------------------------------------


def _compute_permutation_with_rotate_fallback(rng: object, n: int) -> tuple[list[int], bool]:
    """Draw a permutation of range(n); rotate-by-one fallback if identity drawn.

    Mirrors v0.49 / v0.50 C-arm pattern verbatim. Returns
    ``(perm, applied_fallback)``. The fallback fires only when the drawn
    permutation is exactly the identity, guaranteeing a non-identity
    permutation for every B-arm run.
    """
    drawn = rng.permutation(n)
    if list(int(x) for x in drawn) == list(range(n)):
        return [(i + 1) % n for i in range(n)], True
    return [int(x) for x in drawn], False


def _assert_single_channel_override_invariant(
    original: Traits, assigned: Traits, *, lineage_id: int
) -> None:
    """Assert every Traits field except effective_sensor_radius_override
    is byte-identical between ``original`` and ``assigned``.

    v0.52b's patch only touches the override field. ``sensor_radius``
    (the trait) is unchanged so metabolic cost remains trait-tied.
    """
    for f in dataclasses.fields(original):
        name = f.name
        if name == "effective_sensor_radius_override":
            continue
        if getattr(original, name) != getattr(assigned, name):
            msg = (
                f"v0.52b single-channel invariant violated under shuffle arm "
                f"lineage_id={lineage_id}: field {name!r} differs between original "
                f"({getattr(original, name)!r}) and assigned ({getattr(assigned, name)!r})"
            )
            raise V052bReducerError(msg)


def _apply_shuffle_patch(arm: str, seed: int, model: HHModel, capture: _RunCapture) -> None:
    """Patch founder traits per the arm spec; record per-founder audit.

    Called inside the reducer's setup_observer, after HHModel construction
    and before any model.step() runs. Single-channel by construction:
    only the effective_sensor_radius_override field on each founder body's
    traits is replaced.
    """
    founders = sorted(model.agents, key=lambda a: int(a.body.lineage_id))
    if len(founders) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.52b invariant: expected exactly {EXPECTED_FOUNDERS} founders "
            f"at setup_observer time; got {len(founders)}"
        )
        raise V052bReducerError(msg)

    original_traits_per_founder: list[Traits] = [a.body.traits for a in founders]
    original_sr: list[int] = [int(t.sensor_radius) for t in original_traits_per_founder]

    perm: list[int]
    applied_fallback = False
    if arm == ARM_B_SHUFFLE:
        perm, applied_fallback = _compute_permutation_with_rotate_fallback(
            np.random.default_rng(seed), EXPECTED_FOUNDERS
        )
    elif arm == ARM_A_NULL:
        perm = list(range(EXPECTED_FOUNDERS))
    else:
        msg = f"v0.52b: unknown arm {arm!r}"
        raise V052bReducerError(msg)

    if arm == ARM_B_SHUFFLE:
        assigned_effective: list[int] = [original_sr[perm[i]] for i in range(EXPECTED_FOUNDERS)]
    else:
        # A_null: no override; assigned == original; record original_sr for audit.
        assigned_effective = list(original_sr)

    for i, agent in enumerate(founders):
        original = original_traits_per_founder[i]
        if arm == ARM_B_SHUFFLE:
            new_traits = dataclasses.replace(
                original, effective_sensor_radius_override=int(assigned_effective[i])
            )
            _assert_single_channel_override_invariant(
                original, new_traits, lineage_id=int(agent.body.lineage_id)
            )
            agent.body = dataclasses.replace(agent.body, traits=new_traits)

    changed = sum(1 for i in range(EXPECTED_FOUNDERS) if assigned_effective[i] != original_sr[i])
    capture.effective_sensor_radius_changed_count = changed if arm == ARM_B_SHUFFLE else 0

    for i, agent in enumerate(founders):
        capture.founder_records.append(
            _FounderRecord(
                lineage_id=int(agent.body.lineage_id),
                founder_index=i,
                founder_original_sensor_radius=original_sr[i],
                founder_assigned_effective_sensor_radius=int(assigned_effective[i]),
                founder_reproduction_drive=float(original_traits_per_founder[i].reproduction_drive),
                founder_metabolic_rate=float(original_traits_per_founder[i].metabolic_rate),
                permutation_map_index=int(perm[i]),
                applied_identity_rotation_fallback=applied_fallback,
            )
        )


# ---------------------------------------------------------------------------
# Per-tick capture (read-only)
# ---------------------------------------------------------------------------


def _capture_tick_record(model: HHModel, tick_label: int, capture: _RunCapture) -> None:
    if tick_label in capture.tick_records:
        return
    capture.n_observer_fires += 1
    record = _TickRecord(tick=tick_label)
    for agent in model.agents:
        body = getattr(agent, "body", None)
        if body is None or not getattr(body, "alive", False):
            continue
        traits = body.traits
        record.agents.append(
            (
                int(body.id),
                int(body.lineage_id),
                int(body.x),
                int(body.y),
                int(traits.sensor_radius),
            )
        )
    food_mask = np.asarray(model.world.food_value) > 0
    food_xs, food_ys = np.where(food_mask)
    record.food_cells = tuple(zip(food_xs.tolist(), food_ys.tolist(), strict=True))
    hazard_mask = np.asarray(model.world.hazard_damage) > 0
    hazard_xs, hazard_ys = np.where(hazard_mask)
    record.hazard_cells = tuple(zip(hazard_xs.tolist(), hazard_ys.tolist(), strict=True))
    capture.tick_records[tick_label] = record


def _make_setup_observer(
    arm: str,
    seed: int,
    capture: _RunCapture,
    disconnect_callbacks: list[Callable[[], None]],
) -> Callable[[HHModel], None]:
    """setup_observer factory: applies shuffle patch, wires listeners, captures tick 0.

    Order (locked by pre-reg):
      (a) apply founder trait patch (B) or no-op (A_null); records founder audit.
      (b) seed lineage_by_agent + birth_tick_by_agent for the founders.
      (c) wire AgentBorn listener (lineage tracking + descendant inheritance audit).
      (d) wire AteFood + HazardDamageApplied listeners.
      (e) capture tick 0 snapshot.
    """

    def setup(model: HHModel) -> None:
        _apply_shuffle_patch(arm, seed, model, capture)

        for agent in model.agents:
            body = getattr(agent, "body", None)
            if body is None:
                continue
            lineage_id = int(body.lineage_id)
            capture.lineage_by_agent[int(body.id)] = lineage_id
            capture.birth_tick_by_agent[int(body.id)] = 0

        # AgentBorn listener: lineage tracking + descendant inheritance audit
        # (B arm only — under A_null, override is None for everyone, so the
        # audit counters increment only under arm B but the listener is wired
        # for both arms for consistency; A_null counters end at 0 / total / 0
        # if a newborn has override=None, which is the default behavior).
        def _on_agent_born(_sender: object, *, event: AgentBorn) -> None:
            aid = int(event.agent_id)
            capture.birth_tick_by_agent[aid] = int(event.tick)
            capture.lineage_by_agent[aid] = int(event.lineage_id)
            # Descendant audit: only meaningful under arm B.
            if arm != ARM_B_SHUFFLE:
                return
            target = next((a for a in model.agents if int(a.body.id) == aid), None)
            counters = capture.descendant_counters
            counters.n_births_seen += 1
            if target is None:
                # Pathological: AgentBorn fired but agent not in model.agents.
                # Treat as missing — will surface as inheritance halt.
                counters.n_overrides_missing += 1
                return
            if target.body.traits.effective_sensor_radius_override is not None:
                counters.n_overrides_inherited += 1
            else:
                counters.n_overrides_missing += 1

        signal_for(AgentBorn).connect(_on_agent_born, sender=model, weak=False)
        disconnect_callbacks.append(
            lambda: signal_for(AgentBorn).disconnect(_on_agent_born, sender=model)
        )

        def _on_ate_food(_sender: object, *, event: AteFood) -> None:
            if int(model.tick_count) > TICK_50:
                return
            aid = int(event.agent_id)
            capture.pre50_food_events_by_agent[aid] = (
                capture.pre50_food_events_by_agent.get(aid, 0) + 1
            )
            capture.pre50_food_energy_by_agent[aid] = capture.pre50_food_energy_by_agent.get(
                aid, 0.0
            ) + float(event.food_gained)

        def _on_hazard_damage(_sender: object, *, event: HazardDamageApplied) -> None:
            if int(model.tick_count) > TICK_50:
                return
            aid = int(event.agent_id)
            capture.pre50_hazard_damage_events_by_agent[aid] = (
                capture.pre50_hazard_damage_events_by_agent.get(aid, 0) + 1
            )

        signal_for(AteFood).connect(_on_ate_food, sender=model)
        signal_for(HazardDamageApplied).connect(_on_hazard_damage, sender=model)
        disconnect_callbacks.append(
            lambda: signal_for(AteFood).disconnect(_on_ate_food, sender=model)
        )
        disconnect_callbacks.append(
            lambda: signal_for(HazardDamageApplied).disconnect(_on_hazard_damage, sender=model)
        )

        capture.energy_threshold = float(model.reproduction_config.energy_threshold)
        capture.min_age = int(model.reproduction_config.min_age)

        _capture_tick_record(model, tick_label=0, capture=capture)

    return setup


def _make_per_tick_observer(capture: _RunCapture) -> Callable[[HHModel], None]:
    def observer(model: HHModel) -> None:
        tick = int(model.tick_count)
        if tick == 0 or tick > TICK_50:
            return
        _capture_tick_record(model, tick_label=tick, capture=capture)
        if tick == TICK_50:
            for agent in model.agents:
                body = getattr(agent, "body", None)
                if body is None or not getattr(body, "alive", False):
                    continue
                capture.tick50_readiness.append(
                    _Tick50Readiness(
                        agent_id=int(body.id),
                        lineage_id=int(body.lineage_id),
                        energy=float(body.energy),
                        age=int(body.age),
                    )
                )

    return observer


def _run_one_arm(arm: str, version: str, seed: int, hazard: int, runs_root: Path) -> _RunCapture:
    """Execute one (arm, version, seed, hazard) run, returning its capture."""
    if arm not in ARMS:
        msg = f"v0.52b: unknown arm {arm!r}"
        raise V052bReducerError(msg)
    base_arm = _select_a_null_arm(version, hazard)
    layout = _resolve_layout(LAYOUT_NAME)
    repro_kwargs: dict[str, float] = {
        "energy_threshold": (
            base_arm.energy_threshold
            if base_arm.energy_threshold is not None
            else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": (
            base_arm.energy_cost if base_arm.energy_cost is not None else FIXED_ENERGY_COST
        ),
    }
    if base_arm.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = base_arm.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
    trait_cfg = TraitConfig(unbounded_mutation=True)

    capture = _RunCapture(arm=arm, version=version, seed=seed, hazard=hazard)
    disconnects: list[Callable[[], None]] = []
    base_setup = _make_setup_observer(arm, seed, capture, disconnects)

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = base_arm.auto_reproduction
        base_setup(model)

    use_memory = base_arm.memory_type is not None
    memory_type = base_arm.memory_type or "cell_exact"

    optional_intervention: InterventionConfig | None = None
    if base_arm.intervention_kind is not None:
        optional_intervention = InterventionConfig(kind=base_arm.intervention_kind)
    if optional_intervention is not None and optional_intervention.kind != KIND_NULL:
        msg = (
            f"v0.52b: base arm must be A_null only; got "
            f"intervention_kind={base_arm.intervention_kind!r}"
        )
        raise V052bReducerError(msg)

    run_id = f"{arm}-{version}-A_null-hzd{hazard}-seed-{seed}"
    try:
        run_chamber(
            seed=seed,
            runs_root=runs_root,
            run_id=run_id,
            n_founders=N_FOUNDERS,
            n_ticks=N_TICKS,
            layout=layout,
            policy_factory=base_arm.policy_factory,
            trait_config=trait_cfg,
            reproduction_config=repro_cfg,
            use_memory=use_memory,
            memory_type=memory_type,
            food_respawn_cooldown=base_arm.food_respawn_cooldown,
            energy_pool_initial=base_arm.energy_pool_initial,
            ambient_influx_rate=base_arm.ambient_influx_rate,
            child_funding_mode=base_arm.child_funding_mode,
            hazard_damage=base_arm.hazard_damage,
            hazard_avoidance_weight=base_arm.hazard_avoidance_weight,
            condition=f"v0.52b-{arm}-{version}-A_null-hzd{hazard}",
            setup_observer=setup,
            tick_observer=_make_per_tick_observer(capture),
            optional_intervention=optional_intervention,
        )
    finally:
        for disconnect in disconnects:
            disconnect()

    expected_ticks = TICK_50 + 1
    if len(capture.tick_records) != expected_ticks:
        msg = (
            f"v0.52b invariant: per-tick observer must capture {expected_ticks} ticks for "
            f"{run_id}; got {len(capture.tick_records)}"
        )
        raise V052bReducerError(msg)
    if len(capture.founder_records) != EXPECTED_FOUNDERS:
        msg = (
            f"v0.52b invariant: expected exactly {EXPECTED_FOUNDERS} founder records for "
            f"{run_id}; got {len(capture.founder_records)}"
        )
        raise V052bReducerError(msg)
    return capture


# ---------------------------------------------------------------------------
# Per-lineage row + label assignment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerLineageRow:
    arm: str
    version: str
    seed: int
    hazard: int
    run_id: str
    lineage_id: int
    founder_original_sensor_radius: int
    founder_assigned_effective_sensor_radius: int
    permutation_map_index: int
    applied_identity_rotation_fallback: bool
    effective_sensor_radius_changed_count: int
    founder_reproduction_drive: float
    founder_metabolic_rate: float
    pre50_food_events_count: int
    pre50_food_energy_acquired: float
    mean_distance_to_nearest_food_cell: float
    tick50_living_count: int
    tick50_above_threshold_count: int
    tick50_above_threshold_fraction: float
    b50_count: int
    is_eventual_top_b50_label: bool
    is_high_information_radius_lineage: bool
    is_high_tick50_readiness_fraction_lineage: bool


PER_LINEAGE_FIELDNAMES: list[str] = [
    "arm",
    "version",
    "seed",
    "hazard",
    "run_id",
    "lineage_id",
    "founder_original_sensor_radius",
    "founder_assigned_effective_sensor_radius",
    "permutation_map_index",
    "applied_identity_rotation_fallback",
    "effective_sensor_radius_changed_count",
    "founder_reproduction_drive",
    "founder_metabolic_rate",
    "pre50_food_events_count",
    "pre50_food_energy_acquired",
    "mean_distance_to_nearest_food_cell",
    "tick50_living_count",
    "tick50_above_threshold_count",
    "tick50_above_threshold_fraction",
    "b50_count",
    "is_eventual_top_b50_label",
    "is_high_information_radius_lineage",
    "is_high_tick50_readiness_fraction_lineage",
]


def _manhattan_distance_to_nearest(
    x: int, y: int, cells: tuple[tuple[int, int], ...]
) -> float | None:
    if not cells:
        return None
    return float(min(abs(cx - x) + abs(cy - y) for (cx, cy) in cells))


def _per_tick_lineage_distance_means(capture: _RunCapture) -> dict[int, float]:
    all_lineages = sorted(set(capture.lineage_by_agent.values()))
    sums: dict[int, float] = dict.fromkeys(all_lineages, 0.0)
    counts: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for tick in range(TICK_50 + 1):
        record = capture.tick_records.get(tick)
        if record is None:
            continue
        living_by_lineage: dict[int, list[tuple[int, int, int, int, int]]] = {}
        for row in record.agents:
            living_by_lineage.setdefault(row[1], []).append(row)
        for lid, agents in living_by_lineage.items():
            agent_distances: list[float] = []
            for _aid, _lid, ax, ay, _r in agents:
                d = _manhattan_distance_to_nearest(ax, ay, record.food_cells)
                if d is not None:
                    agent_distances.append(d)
            if agent_distances:
                sums[lid] = sums.get(lid, 0.0) + statistics.mean(agent_distances)
                counts[lid] = counts.get(lid, 0) + 1
    out: dict[int, float] = {}
    for lid in all_lineages:
        out[lid] = sums[lid] / counts[lid] if counts.get(lid, 0) > 0 else float("nan")
    return out


def _select_information_radius_label(
    information_radius_by_lineage: dict[int, int],
) -> int | None:
    """argmax(information_radius), tiebreak min(lineage_id).

    Under A_null the value is the trait sensor_radius (override is None for
    every founder, so the resolver in _aggregate_per_lineage falls through
    to trait). Under B the value is the assigned effective override.
    """
    if not information_radius_by_lineage:
        return None
    best_lid: int | None = None
    best_value = float("-inf")
    for lid in sorted(information_radius_by_lineage):
        v = float(information_radius_by_lineage[lid])
        if v > best_value:
            best_value = v
            best_lid = lid
    return best_lid


def _select_fraction_label(candidates: list[tuple[int, float, int]]) -> int | None:
    """v0.47/v0.48 3-tier tiebreak: fraction -> count -> min(lineage_id)."""
    if not candidates:
        return None
    best = candidates[0]
    for cand in candidates[1:]:
        if (
            cand[1] > best[1]
            or (cand[1] == best[1] and cand[2] > best[2])
            or (cand[1] == best[1] and cand[2] == best[2] and cand[0] < best[0])
        ):
            best = cand
    return best[0]


def _aggregate_per_lineage(capture: _RunCapture) -> list[PerLineageRow]:
    all_lineages = sorted(set(capture.lineage_by_agent.values()))

    b50_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    for aid, btick in capture.birth_tick_by_agent.items():
        if btick > TICK_50:
            lid = capture.lineage_by_agent.get(aid)
            if lid is None:
                msg = f"v0.52b: agent_id {aid} has birth_tick {btick} but no lineage_id"
                raise V052bReducerError(msg)
            b50_by_lineage[lid] = b50_by_lineage.get(lid, 0) + 1
    total_b50 = sum(b50_by_lineage.values())

    eventual_top: int | None
    if total_b50 == 0:
        eventual_top = None
    else:
        best_id = -1
        best_count = -1
        for lid in sorted(all_lineages):
            count = b50_by_lineage.get(lid, 0)
            if count > best_count:
                best_id = lid
                best_count = count
        eventual_top = best_id

    living_at_50_by_lineage: dict[int, list[_Tick50Readiness]] = {lid: [] for lid in all_lineages}
    for snap in capture.tick50_readiness:
        living_at_50_by_lineage.setdefault(snap.lineage_id, []).append(snap)

    fraction_by_lineage: dict[int, float] = {}
    count_by_lineage: dict[int, int] = {}
    living_count_by_lineage: dict[int, int] = {}
    for lid in all_lineages:
        living = living_at_50_by_lineage.get(lid, [])
        n_living = len(living)
        living_count_by_lineage[lid] = n_living
        n_above = sum(
            1 for s in living if s.energy >= capture.energy_threshold and s.age >= capture.min_age
        )
        count_by_lineage[lid] = n_above
        fraction_by_lineage[lid] = (n_above / n_living) if n_living > 0 else float("nan")

    fraction_candidates = [
        (lid, fraction_by_lineage[lid], count_by_lineage[lid])
        for lid in all_lineages
        if not math.isnan(fraction_by_lineage[lid])
    ]
    fraction_label = _select_fraction_label(fraction_candidates)

    founder_by_lineage: dict[int, _FounderRecord] = {
        rec.lineage_id: rec for rec in capture.founder_records
    }
    # Label A: under A_null, info radius == trait sensor_radius (override None);
    # under B, info radius == assigned effective override. The
    # founder_assigned_effective_sensor_radius field captures both cases
    # cleanly (it equals the original sensor_radius under A_null).
    info_radius_by_lineage: dict[int, int] = {
        lid: founder_by_lineage[lid].founder_assigned_effective_sensor_radius
        for lid in all_lineages
    }
    info_label = _select_information_radius_label(info_radius_by_lineage)

    distance_by_lineage = _per_tick_lineage_distance_means(capture)

    pre50_food_events_by_lineage: dict[int, int] = dict.fromkeys(all_lineages, 0)
    pre50_food_energy_by_lineage: dict[int, float] = {lid: 0.0 for lid in all_lineages}
    for aid, lid in capture.lineage_by_agent.items():
        pre50_food_events_by_lineage[lid] = pre50_food_events_by_lineage.get(
            lid, 0
        ) + capture.pre50_food_events_by_agent.get(aid, 0)
        pre50_food_energy_by_lineage[lid] = pre50_food_energy_by_lineage.get(
            lid, 0.0
        ) + capture.pre50_food_energy_by_agent.get(aid, 0.0)

    rows: list[PerLineageRow] = []
    run_id = f"{capture.arm}-{capture.version}-A_null-hzd{capture.hazard}-seed-{capture.seed}"
    for lid in all_lineages:
        founder = founder_by_lineage[lid]
        rows.append(
            PerLineageRow(
                arm=capture.arm,
                version=capture.version,
                seed=capture.seed,
                hazard=capture.hazard,
                run_id=run_id,
                lineage_id=lid,
                founder_original_sensor_radius=founder.founder_original_sensor_radius,
                founder_assigned_effective_sensor_radius=(
                    founder.founder_assigned_effective_sensor_radius
                ),
                permutation_map_index=founder.permutation_map_index,
                applied_identity_rotation_fallback=founder.applied_identity_rotation_fallback,
                effective_sensor_radius_changed_count=(
                    capture.effective_sensor_radius_changed_count
                ),
                founder_reproduction_drive=float(founder.founder_reproduction_drive),
                founder_metabolic_rate=float(founder.founder_metabolic_rate),
                pre50_food_events_count=pre50_food_events_by_lineage.get(lid, 0),
                pre50_food_energy_acquired=pre50_food_energy_by_lineage.get(lid, 0.0),
                mean_distance_to_nearest_food_cell=distance_by_lineage.get(lid, float("nan")),
                tick50_living_count=living_count_by_lineage[lid],
                tick50_above_threshold_count=count_by_lineage[lid],
                tick50_above_threshold_fraction=fraction_by_lineage[lid],
                b50_count=b50_by_lineage.get(lid, 0),
                is_eventual_top_b50_label=(eventual_top is not None and lid == eventual_top),
                is_high_information_radius_lineage=(info_label is not None and lid == info_label),
                is_high_tick50_readiness_fraction_lineage=(
                    fraction_label is not None and lid == fraction_label
                ),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Effect-size + per-arm sub-verdicts
# ---------------------------------------------------------------------------


def _per_run_paired_delta(
    rows_in_run: list[PerLineageRow], observable_field: str, label_field: str
) -> float | None:
    label_rows = [r for r in rows_in_run if getattr(r, label_field)]
    if len(label_rows) != 1:
        return None
    label_value = getattr(label_rows[0], observable_field)
    if isinstance(label_value, float) and math.isnan(label_value):
        return None
    non_label = [r for r in rows_in_run if not getattr(r, label_field)]
    non_label_values = [
        getattr(r, observable_field)
        for r in non_label
        if not (
            isinstance(getattr(r, observable_field), float)
            and math.isnan(getattr(r, observable_field))
        )
    ]
    if not non_label_values:
        return None
    return float(label_value) - statistics.mean(non_label_values)


def _paired_cohens_d(deltas: list[float]) -> float:
    if len(deltas) < 2:
        return float("nan")
    mean = statistics.mean(deltas)
    sd = statistics.stdev(deltas)
    if sd == 0:
        return float("nan")
    return mean / sd


@dataclass(frozen=True)
class ObservableSummary:
    arm: str
    observable: str
    label: str
    sign: int
    n_runs_contributing: int
    paired_d: float
    signed_d: float
    delta_mean: float
    delta_stdev: float
    delta_min: float
    delta_max: float
    fires_expected: bool
    fires_wrong: bool


def _index_rows_by_arm_run(
    rows: list[PerLineageRow],
) -> dict[tuple[str, str, int, int], list[PerLineageRow]]:
    out: dict[tuple[str, str, int, int], list[PerLineageRow]] = {}
    for r in rows:
        out.setdefault((r.arm, r.version, r.seed, r.hazard), []).append(r)
    return out


def _summarise_observable_for_arm(
    *,
    arm: str,
    observable: str,
    sign: int,
    label: str,
    label_field: str,
    all_rows: list[PerLineageRow],
    runs: list[tuple[str, int, int]],
) -> ObservableSummary:
    deltas: list[float] = []
    by_arm_run = _index_rows_by_arm_run(all_rows)
    for run_key in runs:
        run_rows = by_arm_run.get((arm, run_key[0], run_key[1], run_key[2]), [])
        delta = _per_run_paired_delta(run_rows, observable, label_field)
        if delta is not None:
            deltas.append(delta)
    d = _paired_cohens_d(deltas)
    if not deltas:
        delta_mean = float("nan")
        delta_min = float("nan")
        delta_max = float("nan")
    else:
        delta_mean = statistics.mean(deltas)
        delta_min = min(deltas)
        delta_max = max(deltas)
    delta_stdev = statistics.stdev(deltas) if len(deltas) >= 2 else float("nan")
    signed_d = d * sign if not math.isnan(d) else d
    fires_expected = (not math.isnan(signed_d)) and signed_d >= COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed_d)) and signed_d <= -COHENS_D_THRESHOLD
    return ObservableSummary(
        arm=arm,
        observable=observable,
        label=label,
        sign=sign,
        n_runs_contributing=len(deltas),
        paired_d=d,
        signed_d=signed_d,
        delta_mean=delta_mean,
        delta_stdev=delta_stdev,
        delta_min=delta_min,
        delta_max=delta_max,
        fires_expected=fires_expected,
        fires_wrong=fires_wrong,
    )


_SUBVERDICT_TABLE: dict[str, tuple[str, str, str, str]] = {
    # (PRESENT, PARTIAL, NOT_FOUND, OPPOSITE)
    ARM_A_NULL: (
        SUBVERDICT_A_NULL_PRESENT,
        SUBVERDICT_A_NULL_PARTIAL,
        SUBVERDICT_A_NULL_NOT_FOUND,
        SUBVERDICT_A_NULL_OPPOSITE,
    ),
    ARM_B_SHUFFLE: (
        SUBVERDICT_B_PRESENT,
        SUBVERDICT_B_PARTIAL,
        SUBVERDICT_B_NOT_FOUND,
        SUBVERDICT_B_OPPOSITE,
    ),
}


def _arm_subverdict(
    arm: str,
    summaries_a: list[ObservableSummary],
    summaries_b: list[ObservableSummary],
) -> str:
    """Per-arm 4-way sub-verdict; both labels gate for both arms in v0.52b."""
    if arm not in _SUBVERDICT_TABLE:
        msg = f"v0.52b: unknown arm {arm!r} in subverdict"
        raise V052bReducerError(msg)
    present, partial, not_found, opposite = _SUBVERDICT_TABLE[arm]
    n_wrong = sum(1 for s in summaries_a + summaries_b if s.fires_wrong)
    if n_wrong > 0:
        return opposite
    n_fire_a = sum(1 for s in summaries_a if s.fires_expected)
    n_fire_b = sum(1 for s in summaries_b if s.fires_expected)
    a_clears = n_fire_a >= 2
    b_clears = n_fire_b >= 2
    if a_clears and b_clears:
        return present
    if a_clears != b_clears:
        return partial
    return not_found


# ---------------------------------------------------------------------------
# Re-anchor (corpus + Tier-1 bridge only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReAnchorRow:
    arm: str
    version: str
    hazard: int
    n_runs_contributing: int
    a_share_h8_derived: float
    a_share_h8_published: float | None
    drift_abs: float | None
    halts: bool


def _compute_a_share_h8(all_rows: list[PerLineageRow], arm: str, version: str) -> tuple[float, int]:
    by_arm_run = _index_rows_by_arm_run(all_rows)
    shares: list[float] = []
    for (a, ver, _seed, haz), rows_in_run in by_arm_run.items():
        if a != arm or ver != version or haz != 8:
            continue
        total_b50 = sum(r.b50_count for r in rows_in_run)
        if total_b50 == 0:
            continue
        max_b50 = max(r.b50_count for r in rows_in_run)
        shares.append(max_b50 / total_b50)
    if not shares:
        return float("nan"), 0
    return statistics.mean(shares), len(shares)


def _check_corpus_re_anchor(all_rows: list[PerLineageRow]) -> list[ReAnchorRow]:
    out: list[ReAnchorRow] = []
    for arm in ARMS:
        for version in ("v0.42", "v0.43R", "v0.44", "v0.45"):
            derived, n_runs = _compute_a_share_h8(all_rows, arm, version)
            published = PUBLISHED_A_SHARE_H8[version] if arm == ARM_A_NULL else None
            if published is None or math.isnan(derived):
                drift_abs: float | None = None
                halts = False
            else:
                drift_abs = abs(derived - published)
                halts = drift_abs > RE_ANCHOR_DRIFT_TOLERANCE
            out.append(
                ReAnchorRow(
                    arm=arm,
                    version=version,
                    hazard=8,
                    n_runs_contributing=n_runs,
                    a_share_h8_derived=derived,
                    a_share_h8_published=published,
                    drift_abs=drift_abs,
                    halts=halts,
                )
            )
    return out


@dataclass(frozen=True)
class BridgeReAnchorRow:
    label: str
    observable: str
    published_signed_d: float
    derived_signed_d: float
    drift_abs: float
    halts: bool


def _check_bridge_re_anchor(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
) -> list[BridgeReAnchorRow]:
    out: list[BridgeReAnchorRow] = []
    for (label, observable), published in V048_PUBLISHED_SIGNED_D.items():
        derived = _lookup_signed_d(summaries_by_arm_label, ARM_A_NULL, label, observable)
        if math.isnan(derived):
            drift_abs = float("inf")
            halts = True
        else:
            drift_abs = abs(derived - published)
            halts = drift_abs > RE_ANCHOR_DRIFT_TOLERANCE
        out.append(
            BridgeReAnchorRow(
                label=label,
                observable=observable,
                published_signed_d=published,
                derived_signed_d=derived,
                drift_abs=drift_abs,
                halts=halts,
            )
        )
    return out


def _lookup_signed_d(
    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]],
    arm: str,
    label: str,
    observable: str,
) -> float:
    for s in summaries_by_arm_label.get((arm, label), []):
        if s.observable == observable:
            return s.signed_d
    return float("nan")


# ---------------------------------------------------------------------------
# Slice rollup (priority-ordered)
# ---------------------------------------------------------------------------


def _evaluate_rollup(  # noqa: PLR0911 — 7-way priority match is the explicit verdict structure.
    *,
    a_null_subverdict: str,
    b_subverdict: str,
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    descendant_overrides_missing_total: int,
) -> tuple[str, str]:
    """7-outcome priority-ordered rollup. Returns (verdict, locked_phrase)."""
    drift_halt = next(
        (r for r in corpus_re_anchor if r.halts and r.arm == ARM_A_NULL),
        None,
    )
    if drift_halt is not None:
        return ROLLUP_CORPUS_DRIFT_HALT, LOCKED_PHRASES[ROLLUP_CORPUS_DRIFT_HALT].format(
            version=drift_halt.version
        )

    if a_null_subverdict == SUBVERDICT_A_NULL_OPPOSITE:
        return ROLLUP_INTERVENTION_OPPOSITE_HALT, LOCKED_PHRASES[ROLLUP_INTERVENTION_OPPOSITE_HALT]
    if b_subverdict == SUBVERDICT_B_OPPOSITE:
        return ROLLUP_INTERVENTION_OPPOSITE_HALT, LOCKED_PHRASES[ROLLUP_INTERVENTION_OPPOSITE_HALT]

    if any(r.halts for r in bridge_re_anchor):
        return ROLLUP_BRIDGE_REPLICATION_HALT, LOCKED_PHRASES[ROLLUP_BRIDGE_REPLICATION_HALT]
    if a_null_subverdict != SUBVERDICT_A_NULL_PRESENT:
        return ROLLUP_BRIDGE_REPLICATION_HALT, LOCKED_PHRASES[ROLLUP_BRIDGE_REPLICATION_HALT]

    if descendant_overrides_missing_total > 0:
        return (
            ROLLUP_SHUFFLE_INHERITANCE_HALT,
            LOCKED_PHRASES[ROLLUP_SHUFFLE_INHERITANCE_HALT],
        )

    if b_subverdict == SUBVERDICT_B_PRESENT:
        return ROLLUP_FOLLOWS_ASSIGNMENT, LOCKED_PHRASES[ROLLUP_FOLLOWS_ASSIGNMENT]
    if b_subverdict == SUBVERDICT_B_NOT_FOUND:
        return (
            ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT,
            LOCKED_PHRASES[ROLLUP_DOES_NOT_FOLLOW_ASSIGNMENT],
        )
    if b_subverdict == SUBVERDICT_B_PARTIAL:
        return ROLLUP_ASSIGNMENT_PARTIAL, LOCKED_PHRASES[ROLLUP_ASSIGNMENT_PARTIAL]
    msg = (
        f"v0.52b: rollup partition broke — A_null={a_null_subverdict}, B={b_subverdict}. "
        f"Re-anchor halts should have fired before this point under correct implementation."
    )
    raise V052bReducerError(msg)


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return repr(value)
    return str(value)


def _write_per_lineage_csv(rows: list[PerLineageRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PER_LINEAGE_FIELDNAMES)
        for row in rows:
            d = asdict(row)
            writer.writerow([_format_value(d[name]) for name in PER_LINEAGE_FIELDNAMES])


DESCENDANT_AUDIT_FIELDNAMES: list[str] = [
    "arm",
    "version",
    "seed",
    "hazard",
    "run_id",
    "n_births_seen",
    "n_overrides_inherited",
    "n_overrides_missing",
]


def _write_descendant_audit_csv(captures: list[_RunCapture], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(DESCENDANT_AUDIT_FIELDNAMES)
        for cap in captures:
            run_id = f"{cap.arm}-{cap.version}-A_null-hzd{cap.hazard}-seed-{cap.seed}"
            c = cap.descendant_counters
            writer.writerow(
                [
                    cap.arm,
                    cap.version,
                    str(cap.seed),
                    str(cap.hazard),
                    run_id,
                    str(c.n_births_seen),
                    str(c.n_overrides_inherited),
                    str(c.n_overrides_missing),
                ]
            )


def _write_audit_summary_csv(
    summaries: list[ObservableSummary],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    a_null_subverdict: str,
    b_subverdict: str,
    rollup_verdict: str,
    rollup_phrase: str,
    descendant_aggregates: dict[str, int],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "key", "value"])
        for r in corpus_re_anchor:
            for field_name, value in (
                ("derived", r.a_share_h8_derived),
                ("published", r.a_share_h8_published),
                ("drift_abs", r.drift_abs),
                ("n_runs", r.n_runs_contributing),
                ("halts", r.halts),
            ):
                writer.writerow(
                    [
                        "reanchor_a_share_h8",
                        f"{r.arm}/{r.version}/h{r.hazard}/{field_name}",
                        _format_value(value),
                    ]
                )
        for br in bridge_re_anchor:
            for field_name, value in (
                ("published_signed_d", br.published_signed_d),
                ("derived_signed_d", br.derived_signed_d),
                ("drift_abs", br.drift_abs),
                ("halts", br.halts),
            ):
                writer.writerow(
                    [
                        "bridge_reanchor",
                        f"{br.label}/{br.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        for s in summaries:
            for field_name, value in (
                ("paired_d", s.paired_d),
                ("signed_d", s.signed_d),
                ("n_runs", s.n_runs_contributing),
                ("fires_expected", s.fires_expected),
                ("fires_wrong", s.fires_wrong),
                ("delta_mean", s.delta_mean),
                ("delta_stdev", s.delta_stdev),
                ("delta_min", s.delta_min),
                ("delta_max", s.delta_max),
            ):
                writer.writerow(
                    [
                        "paired_d",
                        f"{s.arm}/{s.label}/{s.observable}/{field_name}",
                        _format_value(value),
                    ]
                )
        for k, v in descendant_aggregates.items():
            writer.writerow(["descendant_audit", k, str(v)])
        writer.writerow(["sub_verdicts", "A_null", a_null_subverdict])
        writer.writerow(["sub_verdicts", "B_effective_radius_shuffle_distribution", b_subverdict])
        writer.writerow(["rollup_verdict", "verdict", rollup_verdict])
        writer.writerow(["rollup_verdict", "locked_phrase", rollup_phrase])


def _observable_line(s: ObservableSummary) -> str:
    d_str = "nan" if math.isnan(s.paired_d) else f"{s.paired_d:+.3f}"
    signed_str = "nan" if math.isnan(s.signed_d) else f"{s.signed_d:+.3f}"
    flag = ""
    if s.fires_expected:
        flag = " FIRES"
    if s.fires_wrong:
        flag = " WRONG-SIGN"
    sign_label = "+" if s.sign > 0 else "-"
    mean_str = "nan" if math.isnan(s.delta_mean) else f"{s.delta_mean:+.4f}"
    sd_str = "nan" if math.isnan(s.delta_stdev) else f"{s.delta_stdev:.4f}"
    min_str = "nan" if math.isnan(s.delta_min) else f"{s.delta_min:+.4f}"
    max_str = "nan" if math.isnan(s.delta_max) else f"{s.delta_max:+.4f}"
    return (
        f"  {s.observable:<38} sign={sign_label}  d={d_str}  signed_d={signed_str}  "
        f"n={s.n_runs_contributing:>2}  "
        f"delta_mean={mean_str}  sd={sd_str}  min={min_str}  max={max_str}{flag}\n"
    )


def _write_audit_log(
    summaries: list[ObservableSummary],
    corpus_re_anchor: list[ReAnchorRow],
    bridge_re_anchor: list[BridgeReAnchorRow],
    a_null_subverdict: str,
    b_subverdict: str,
    rollup_verdict: str,
    rollup_phrase: str,
    descendant_aggregates: dict[str, int],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("=== v0.52b sensor_radius information-radius assignment shuffle ===\n")
    lines.append("\nCorpus re-anchor (per (arm, version, h=8)):\n")
    for r in corpus_re_anchor:
        published_str = "—" if r.a_share_h8_published is None else f"{r.a_share_h8_published:.3f}"
        derived_str = "nan" if math.isnan(r.a_share_h8_derived) else f"{r.a_share_h8_derived:.3f}"
        drift_str = "—" if r.drift_abs is None else f"{r.drift_abs:.4f}"
        halt_str = " HALT" if r.halts else ""
        lines.append(
            f"  {r.arm:<48} {r.version} h={r.hazard}  n={r.n_runs_contributing:>2}  "
            f"derived={derived_str}  published={published_str}  drift={drift_str}{halt_str}\n"
        )
    lines.append("\nTier-1 bridge re-anchor (A_null arm vs v0.48 published signed_d):\n")
    for br in bridge_re_anchor:
        drift_str = "inf" if math.isinf(br.drift_abs) else f"{br.drift_abs:.4f}"
        halt_str = " HALT" if br.halts else ""
        lines.append(
            f"  {br.label}/{br.observable:<38} "
            f"published={br.published_signed_d:+.3f}  derived={br.derived_signed_d:+.3f}  "
            f"drift={drift_str}{halt_str}\n"
        )
    for arm in ARMS:
        lines.append(f"\nArm {arm} — paired_d per (gating-label, primary observable):\n")
        for s in summaries:
            if s.arm != arm:
                continue
            lines.append(f"  [{s.label}] {_observable_line(s)}")
    lines.append(f"\nDescendant audit (B arm only): {descendant_aggregates}\n")
    lines.append(
        f"\nSub-verdicts: A_null={a_null_subverdict}  "
        f"B_effective_radius_shuffle_distribution={b_subverdict}\n"
    )
    lines.append(f"\nRollup verdict: {rollup_verdict}\n")
    lines.append(f'Locked phrase fired: "{rollup_phrase}"\n')
    path.write_text("".join(lines))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_audit(out_dir: Path) -> tuple[str, str]:  # noqa: PLR0912, PLR0915
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== v0.52b sensor_radius information-radius assignment shuffle ===")
    print(f"Arms: {list(ARMS)}")
    print(f"Corpus per arm: A_null over {list(SEEDS_BY_VERSION)}; hazards={HAZARDS}")
    print(
        f"Total runs: {len(ARMS) * sum(len(s) for s in SEEDS_BY_VERSION.values()) * len(HAZARDS)}"
    )
    print(
        "Primary observables: "
        + ", ".join(f"{n} ({'+' if s > 0 else '-'})" for n, s in PRIMARY_OBSERVABLES)
    )
    print()

    captures: list[_RunCapture] = []
    all_rows: list[PerLineageRow] = []
    runs_meta: list[tuple[str, int, int]] = []

    with tempfile.TemporaryDirectory() as td:
        runs_root = Path(td)
        for arm in ARMS:
            for version, seeds in SEEDS_BY_VERSION.items():
                for hazard in HAZARDS:
                    for seed in seeds:
                        capture = _run_one_arm(arm, version, seed, hazard, runs_root)
                        rows = _aggregate_per_lineage(capture)
                        captures.append(capture)
                        all_rows.extend(rows)
                        if arm == ARM_A_NULL:
                            runs_meta.append((version, seed, hazard))
                        a_lid = next(
                            (r.lineage_id for r in rows if r.is_high_information_radius_lineage),
                            None,
                        )
                        b_lid = next(
                            (
                                r.lineage_id
                                for r in rows
                                if r.is_high_tick50_readiness_fraction_lineage
                            ),
                            None,
                        )
                        extra = ""
                        if arm == ARM_B_SHUFFLE:
                            c = capture.descendant_counters
                            extra = (
                                f"  changed={capture.effective_sensor_radius_changed_count}"
                                f"  births={c.n_births_seen}"
                                f"  inherited={c.n_overrides_inherited}"
                                f"  missing={c.n_overrides_missing}"
                            )
                        print(
                            f"  {arm:<48} {version} h={hazard:>2} seed={seed:>2}  "
                            f"a_top={a_lid}  b_top={b_lid}{extra}"
                        )

    print()

    summaries: list[ObservableSummary] = []
    label_pairs = (
        (LABEL_A_NAME, LABEL_A_FIELD),
        (LABEL_B_NAME, LABEL_B_FIELD),
    )
    for arm in ARMS:
        for label_name, label_field in label_pairs:
            for name, sign in PRIMARY_OBSERVABLES:
                summaries.append(
                    _summarise_observable_for_arm(
                        arm=arm,
                        observable=name,
                        sign=sign,
                        label=label_name,
                        label_field=label_field,
                        all_rows=all_rows,
                        runs=runs_meta,
                    )
                )

    summaries_by_arm_label: dict[tuple[str, str], list[ObservableSummary]] = {}
    for s in summaries:
        summaries_by_arm_label.setdefault((s.arm, s.label), []).append(s)

    a_null_subverdict = _arm_subverdict(
        ARM_A_NULL,
        summaries_by_arm_label.get((ARM_A_NULL, LABEL_A_NAME), []),
        summaries_by_arm_label.get((ARM_A_NULL, LABEL_B_NAME), []),
    )
    b_subverdict = _arm_subverdict(
        ARM_B_SHUFFLE,
        summaries_by_arm_label.get((ARM_B_SHUFFLE, LABEL_A_NAME), []),
        summaries_by_arm_label.get((ARM_B_SHUFFLE, LABEL_B_NAME), []),
    )

    corpus_re_anchor = _check_corpus_re_anchor(all_rows)
    bridge_re_anchor = _check_bridge_re_anchor(summaries_by_arm_label)

    descendant_aggregates: dict[str, int] = {
        "n_births_seen_total_b": sum(
            c.descendant_counters.n_births_seen for c in captures if c.arm == ARM_B_SHUFFLE
        ),
        "n_overrides_inherited_total_b": sum(
            c.descendant_counters.n_overrides_inherited for c in captures if c.arm == ARM_B_SHUFFLE
        ),
        "n_overrides_missing_total_b": sum(
            c.descendant_counters.n_overrides_missing for c in captures if c.arm == ARM_B_SHUFFLE
        ),
    }

    rollup_verdict, rollup_phrase = _evaluate_rollup(
        a_null_subverdict=a_null_subverdict,
        b_subverdict=b_subverdict,
        corpus_re_anchor=corpus_re_anchor,
        bridge_re_anchor=bridge_re_anchor,
        descendant_overrides_missing_total=descendant_aggregates["n_overrides_missing_total_b"],
    )

    per_lineage_path = out_dir / "per_run_per_lineage_v052b.csv"
    descendant_audit_path = out_dir / "per_run_descendant_audit.csv"
    audit_summary_path = out_dir / "audit_summary.csv"
    audit_log_path = out_dir / "audit_log.txt"
    _write_per_lineage_csv(all_rows, per_lineage_path)
    _write_descendant_audit_csv(captures, descendant_audit_path)
    _write_audit_summary_csv(
        summaries,
        corpus_re_anchor,
        bridge_re_anchor,
        a_null_subverdict,
        b_subverdict,
        rollup_verdict,
        rollup_phrase,
        descendant_aggregates,
        audit_summary_path,
    )
    _write_audit_log(
        summaries,
        corpus_re_anchor,
        bridge_re_anchor,
        a_null_subverdict,
        b_subverdict,
        rollup_verdict,
        rollup_phrase,
        descendant_aggregates,
        audit_log_path,
    )

    print("Corpus re-anchor (per (arm, version, h=8)):")
    for r in corpus_re_anchor:
        published_str = "—" if r.a_share_h8_published is None else f"{r.a_share_h8_published:.3f}"
        derived_str = "nan" if math.isnan(r.a_share_h8_derived) else f"{r.a_share_h8_derived:.3f}"
        drift_str = "—" if r.drift_abs is None else f"{r.drift_abs:.4f}"
        halt_str = " HALT" if r.halts else ""
        print(
            f"  {r.arm:<48} {r.version} h={r.hazard}  n={r.n_runs_contributing:>2}  "
            f"derived={derived_str}  published={published_str}  drift={drift_str}{halt_str}"
        )
    print("\nTier-1 bridge re-anchor (A_null arm vs v0.48 published signed_d):")
    for br in bridge_re_anchor:
        drift_str = "inf" if math.isinf(br.drift_abs) else f"{br.drift_abs:.4f}"
        halt_str = " HALT" if br.halts else ""
        print(
            f"  {br.label}/{br.observable:<38} "
            f"published={br.published_signed_d:+.3f}  derived={br.derived_signed_d:+.3f}  "
            f"drift={drift_str}{halt_str}"
        )

    for arm in ARMS:
        print(f"\nArm {arm} — paired_d per (gating-label, primary observable):")
        for s in summaries:
            if s.arm != arm:
                continue
            print(f"  [{s.label}] {_observable_line(s).rstrip()}")

    print(f"\nDescendant audit aggregates (B arm only): {descendant_aggregates}")
    print(
        f"Sub-verdicts: A_null={a_null_subverdict}  "
        f"B_effective_radius_shuffle_distribution={b_subverdict}"
    )
    print(f"\nRollup verdict: {rollup_verdict}")
    print(f'Locked phrase: "{rollup_phrase}"')
    print()
    print(f"Wrote {per_lineage_path}")
    print(f"Wrote {descendant_audit_path}")
    print(f"Wrote {audit_summary_path}")
    print(f"Wrote {audit_log_path}")

    if rollup_verdict in {
        ROLLUP_CORPUS_DRIFT_HALT,
        ROLLUP_INTERVENTION_OPPOSITE_HALT,
        ROLLUP_BRIDGE_REPLICATION_HALT,
        ROLLUP_SHUFFLE_INHERITANCE_HALT,
    }:
        raise V052bReducerError(rollup_phrase)
    return rollup_verdict, rollup_phrase


def main() -> None:
    parser = argparse.ArgumentParser(
        description="v0.52b information-radius assignment shuffle audit"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.52b-information-radius-shuffle"),
        help=("Directory for v0.52b outputs (default: runs/v0.52b-information-radius-shuffle)."),
    )
    args = parser.parse_args()
    run_audit(args.out_dir)


if __name__ == "__main__":
    main()
