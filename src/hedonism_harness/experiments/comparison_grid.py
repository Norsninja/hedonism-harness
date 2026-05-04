"""v0.14 3-arm comparison driver: deliberative vs reflex cell.

Three arms x N seeds per chamber, identical chamber/founder/trait/
reproduction configuration except for the policy and reproduction
trigger:

  - A: HedonismPolicy + voluntary REPRODUCE (deliberative-voluntary,
    reproduces v0.13 mem-off baseline)
  - B: HedonismPolicy + automatic reproduction (deliberative-auto)
  - C: GradientPolicy + automatic reproduction (reflex-auto)

The driver writes per-run trait_fingerprints.csv (for speciation
analysis), per-arm aggregate.csv, and a comparison.csv across arms.
Headline metrics include births_after_tick_50 (the v0.13 H2 ceiling
test) and still_tick_fraction (action == STAY rate per agent-tick).

See [[docs/specs/v0.2_reflex_cell_spec.md]] §"Comparison framework"
and [[docs/experiments/fear_hunger_v0.14.md]] (pre-registration).
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from hedonism_harness.core.traits import TraitConfig
from hedonism_harness.experiments.fear_hunger_chamber import (
    ChamberRunResult,
    run_chamber,
)
from hedonism_harness.experiments.layouts import (
    food_ladder_layout,
    tight_gradient_layout,
)
from hedonism_harness.experiments.repro_configs import tuned_reproduction_config
from hedonism_harness.model import HHModel
from hedonism_harness.policies.base import Policy
from hedonism_harness.policies.gradient_policy import GradientPolicy
from hedonism_harness.policies.hedonism_policy import HedonismPolicy

# v0.14 fixed substrate parameters per pre-reg.
DEFAULT_N_FOUNDERS: int = 5
DEFAULT_N_TICKS: int = 200
DEFAULT_TICK_THRESHOLD: int = 50  # the v0.13 H2 ceiling test boundary.
FIXED_ENERGY_THRESHOLD: float = 50.0
FIXED_ENERGY_COST: float = 35.0

_LAYOUT_FACTORIES = {
    "tight_gradient": tight_gradient_layout,
    "food_ladder": food_ladder_layout,
}


# ---------------------------------------------------------------------------
# Arm definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Arm:
    """One leg of a comparison.

    ``memory_type`` (v0.15) selects the per-agent memory representation
    constructed by the chamber driver. ``None`` (v0.14 default) is the
    no-memory arm. ``"scalar"`` (v0.15) attaches a ``ScalarMemory`` to
    every founder + descendant. Other values (``"cell_exact"``,
    ``"directional"``) feed the existing memory machinery and are
    available if a future comparison wants to reuse this driver.
    """

    label: str
    policy_factory: Callable[[], Policy]
    auto_reproduction: bool
    memory_type: str | None = None


def _hedonism_policy_factory() -> Policy:
    return HedonismPolicy(exploration_noise=0.05)


def _gradient_policy_factory() -> Policy:
    return GradientPolicy()


def _gradient_policy_persistence_only_factory() -> Policy:
    return GradientPolicy(blackout_mode="persistence_only")


def _gradient_policy_chemotaxis_factory() -> Policy:
    return GradientPolicy(blackout_mode="chemotaxis")


# v0.14 arms (A / B / C) — preserved for re-runs and bit-identity checks.
ARMS: tuple[Arm, ...] = (
    Arm(
        label="deliberative-voluntary",
        policy_factory=_hedonism_policy_factory,
        auto_reproduction=False,
    ),
    Arm(
        label="deliberative-auto",
        policy_factory=_hedonism_policy_factory,
        auto_reproduction=True,
    ),
    Arm(
        label="reflex-auto",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
    ),
)


# v0.15 arms — chemotaxis-tier scalar memory comparison. Arm A reproduces
# the v0.14 reflex-auto baseline; B isolates persistence; C tests the full
# persistence + derivative-tumble mechanism. See
# [[docs/experiments/fear_hunger_v0.15.md]].
V0_15_ARMS: tuple[Arm, ...] = (
    Arm(
        label="reflex-baseline",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
    ),
    Arm(
        label="reflex-persistence",
        policy_factory=_gradient_policy_persistence_only_factory,
        auto_reproduction=True,
        memory_type="scalar",
    ),
    Arm(
        label="reflex-chemotaxis",
        policy_factory=_gradient_policy_chemotaxis_factory,
        auto_reproduction=True,
        memory_type="scalar",
    ),
)


# ---------------------------------------------------------------------------
# Per-run analysis from events.jsonl (cheap, on already-written artifacts).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunDiagnostics:
    """Per-run derived metrics computed from events.jsonl."""

    births_after_tick_50: int
    still_ticks: int
    move_ticks: int
    eat_ticks: int
    other_ticks: int

    @property
    def total_action_ticks(self) -> int:
        return self.still_ticks + self.move_ticks + self.eat_ticks + self.other_ticks

    @property
    def still_tick_fraction(self) -> float:
        total = self.total_action_ticks
        return (self.still_ticks / total) if total > 0 else 0.0


def _read_run_diagnostics(
    events_jsonl: Path, *, threshold: int = DEFAULT_TICK_THRESHOLD
) -> RunDiagnostics:
    """Walk events.jsonl once to derive birth-tick + per-action counts."""
    births_after = 0
    still = move = eat = other = 0
    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = row.get("type")
            tick = int(row.get("tick", 0))
            if kind == "AgentBorn" and tick > threshold:
                births_after += 1
            elif kind == "AgentStayed":
                still += 1
            elif kind == "AgentMoved":
                move += 1
            elif kind == "AteFood":
                eat += 1
            elif kind in {"HazardDamageApplied", "HazardEntered"}:
                # Body-physics events; not action emissions.
                pass
            elif kind == "ReproductionRequested":
                # Reproduction is auto-substrate (B, C) or voluntary action
                # (A). In A it's an action emission alongside AgentStayed
                # (apply_action(REPRODUCE) emits both? — actually no, only
                # ReproductionRequested). Count it separately as "other".
                other += 1
            else:
                other += 1
    return RunDiagnostics(
        births_after_tick_50=births_after,
        still_ticks=still,
        move_ticks=move,
        eat_ticks=eat,
        other_ticks=other,
    )


# ---------------------------------------------------------------------------
# Per-cell aggregate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmCellAggregate:
    """Per-(arm, chamber) aggregate across a seed sweep."""

    arm_label: str
    layout_name: str
    n_seeds: int
    total_births: int
    seeds_with_any_births: int
    births_after_tick_50: int
    max_population_end: int
    seeds_with_survivors: int
    still_tick_fraction: float
    total_food_events: int
    total_hazard_entries: int
    total_starvation_deaths: int
    total_reproduction_requests: int


def _aggregate(
    arm: Arm,
    layout_name: str,
    pairs: list[tuple[ChamberRunResult, RunDiagnostics]],
) -> ArmCellAggregate:
    if not pairs:
        return ArmCellAggregate(
            arm_label=arm.label,
            layout_name=layout_name,
            n_seeds=0,
            total_births=0,
            seeds_with_any_births=0,
            births_after_tick_50=0,
            max_population_end=0,
            seeds_with_survivors=0,
            still_tick_fraction=0.0,
            total_food_events=0,
            total_hazard_entries=0,
            total_starvation_deaths=0,
            total_reproduction_requests=0,
        )
    results = [r for r, _d in pairs]
    diags = [d for _r, d in pairs]
    n = len(pairs)
    still_fractions = [d.still_tick_fraction for d in diags]
    return ArmCellAggregate(
        arm_label=arm.label,
        layout_name=layout_name,
        n_seeds=n,
        total_births=sum(r.births for r in results),
        seeds_with_any_births=sum(1 for r in results if r.births > 0),
        births_after_tick_50=sum(d.births_after_tick_50 for d in diags),
        max_population_end=max(r.population_end for r in results),
        seeds_with_survivors=sum(1 for r in results if r.population_end > 0),
        still_tick_fraction=sum(still_fractions) / n if n > 0 else 0.0,
        total_food_events=sum(r.food_events for r in results),
        total_hazard_entries=sum(r.hazard_entries for r in results),
        total_starvation_deaths=sum(r.starvation_deaths for r in results),
        total_reproduction_requests=sum(r.reproduction_requests for r in results),
    )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _resolve_layout(name: str):
    if name not in _LAYOUT_FACTORIES:
        msg = f"Unknown layout {name!r}; valid: {sorted(_LAYOUT_FACTORIES)}"
        raise ValueError(msg)
    return _LAYOUT_FACTORIES[name]()


def _write_trait_fingerprints(path: Path, fingerprints: list[dict]) -> None:
    if not fingerprints:
        # Still write a header-only file so the analysis script can
        # detect "ran but produced no agents" without raising.
        path.write_text("agent_id,parent_id,lineage_id,birth_tick,spawn_x,spawn_y\n")
        return
    fieldnames = list(fingerprints[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in fingerprints:
            writer.writerow(row)


def _run_one_arm_seed(
    *,
    arm: Arm,
    layout_name: str,
    seed: int,
    runs_root: Path,
    n_ticks: int,
    n_founders: int,
) -> tuple[ChamberRunResult, RunDiagnostics]:
    """One (arm, layout, seed) execution. Persists outputs under runs_root."""
    layout = _resolve_layout(layout_name)
    repro_cfg = tuned_reproduction_config(
        energy_threshold=FIXED_ENERGY_THRESHOLD,
        energy_cost=FIXED_ENERGY_COST,
    )
    trait_cfg = TraitConfig(unbounded_mutation=True)

    captured: dict[str, object] = {}

    def setup(model: HHModel) -> None:
        model.auto_reproduction_enabled = arm.auto_reproduction
        captured["model"] = model

    use_memory = arm.memory_type is not None
    memory_type = arm.memory_type or "cell_exact"  # only consulted when use_memory=True

    result = run_chamber(
        seed=seed,
        runs_root=runs_root,
        run_id=f"seed-{seed}",
        n_founders=n_founders,
        n_ticks=n_ticks,
        layout=layout,
        policy_factory=arm.policy_factory,
        trait_config=trait_cfg,
        reproduction_config=repro_cfg,
        use_memory=use_memory,
        memory_type=memory_type,
        condition=arm.label,
        setup_observer=setup,
    )

    # Snapshot trait fingerprints from the run model and write per-run.
    model = captured.get("model")
    fingerprints: list[dict] = []
    if isinstance(model, HHModel):
        fingerprints = list(model.trait_fingerprints)
    _write_trait_fingerprints(result.output_dir / "trait_fingerprints.csv", fingerprints)

    diagnostics = _read_run_diagnostics(result.output_dir / "events.jsonl")
    return result, diagnostics


def _write_comparison_csv(path: Path, aggregates: list[ArmCellAggregate]) -> None:
    if not aggregates:
        path.write_text("")
        return
    fieldnames = list(asdict(aggregates[0]).keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for agg in aggregates:
            row = asdict(agg)
            row["still_tick_fraction"] = round(agg.still_tick_fraction, 6)
            writer.writerow(row)


def run_comparison_grid(
    *,
    seeds: Iterable[int],
    runs_root: Path,
    batch_id: str,
    layout_name: str,
    n_ticks: int = DEFAULT_N_TICKS,
    n_founders: int = DEFAULT_N_FOUNDERS,
    arms: tuple[Arm, ...] = ARMS,
) -> list[ArmCellAggregate]:
    """Run the v0.14 3-arm comparison on one chamber and return per-arm aggregates."""
    seeds_list = list(seeds)
    if not seeds_list:
        msg = "run_comparison_grid requires at least one seed"
        raise ValueError(msg)

    batch_root = runs_root / batch_id
    batch_root.mkdir(parents=True, exist_ok=True)
    arms_root = batch_root / "arms"
    arms_root.mkdir(parents=True, exist_ok=True)

    aggregates: list[ArmCellAggregate] = []
    for arm in arms:
        arm_root = arms_root / arm.label
        arm_root.mkdir(parents=True, exist_ok=True)
        pairs: list[tuple[ChamberRunResult, RunDiagnostics]] = []
        for seed in seeds_list:
            pair = _run_one_arm_seed(
                arm=arm,
                layout_name=layout_name,
                seed=seed,
                runs_root=arm_root,
                n_ticks=n_ticks,
                n_founders=n_founders,
            )
            pairs.append(pair)
        aggregates.append(_aggregate(arm, layout_name, pairs))

    _write_comparison_csv(batch_root / "comparison.csv", aggregates)
    return aggregates
