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

from hedonism_harness.core.config import ChildFundingMode
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

    ``energy_cost`` / ``energy_threshold`` (v0.16) override the
    `tuned_reproduction_config` defaults (``FIXED_ENERGY_COST=35.0``,
    ``FIXED_ENERGY_THRESHOLD=50.0``). ``None`` preserves v0.14/v0.15
    bit-identity. Used by ``V0_16_ARMS`` to sweep reproduction
    economics under a single policy arm.

    ``offspring_start_energy`` (v0.17) overrides the
    ``tuned_reproduction_config`` default (``30.0``). ``None``
    preserves v0.14/v0.15/v0.16 bit-identity. Used by ``V0_17_ARMS``
    to sweep newborn starting energy under reflex-baseline + cost-15.

    ``food_respawn_cooldown`` (v0.18) configures per-tile food
    respawn under the cooldown mechanism. ``None`` (default)
    disables respawn — preserves v0.7..v0.17 bit-identity. An
    integer ``K >= 1`` enables respawn: a consumed FOOD cell refills
    after K ticks. Used by ``V0_18_ARMS`` to sweep K under
    reflex-baseline + cost-15 + offspring=30.

    ``energy_pool_initial`` / ``ambient_influx_rate`` (v0.19) configure
    the strict mass-energy conservation substrate. ``None`` (default)
    on the pool field disables the conservation path — preserves
    v0.7..v0.18 bit-identity. A finite ``energy_pool_initial`` enables
    closed-pool / open-ecology arms; ``ambient_influx_rate`` may be
    set with the pool to add per-tick deterministic influx (open
    ecology). Used by ``V0_19_ARMS`` to sweep the conservation axis.

    ``child_funding_mode`` (v0.20) selects the reproduction-funding
    semantics. ``None`` (default) leaves the ReproductionConfig default
    (POOL_FULL — preserves v0.7..v0.19 bit-identity).
    ``ChildFundingMode.PARENT_TRANSFER_POOL_GAP`` routes the parent's
    ``energy_cost`` into the child's body energy and reduces the pool's
    per-birth debit to the gap (``offspring_start_energy - energy_cost``).
    Used by ``V0_20_ARMS`` to test whether eliminating reproduction
    heat loss lifts compounding under v0.19's binding-conservation
    regime.

    ``hazard_damage`` (v0.22) overrides the per-tile hazard damage
    threaded into ``WorldConfig.hazard_damage_default`` via
    ``build_chamber_layout``. ``None`` (default) preserves
    v0.7..v0.21 bit-identity (``build_chamber_layout`` default = 8.0).
    A finite value enables narrow hazard-damage sweeps such as
    ``V0_22_ARMS`` (sweeps {0, 4, 8, 12} on food_ladder under transfer
    mode at influx=1.0/tick to test whether hazard-injury death-residual
    recycling is load-bearing for the v0.21 productivity plateau).

    ``hazard_avoidance_weight`` (v0.26) overrides the multiplier on
    GradientPolicy's pain-pull (perception-vs-damage decoupling).
    ``None`` (default) preserves v0.7..v0.25 bit-identity (factory
    not wrapped; policy default 1.0 is a no-op multiplier). A finite
    value wraps the policy_factory so each GradientPolicy instance
    receives the configured weight. Used by ``V0_26_ARMS`` to test
    whether tight's small cull-tax under v0.25 was driven by
    GradientPolicy avoidance routing (weight=0 vs 1 at hazard=8) or
    chamber geometry alone.
    """

    label: str
    policy_factory: Callable[[], Policy]
    auto_reproduction: bool
    memory_type: str | None = None
    energy_cost: float | None = None
    energy_threshold: float | None = None
    offspring_start_energy: float | None = None
    food_respawn_cooldown: int | None = None
    energy_pool_initial: float | None = None
    ambient_influx_rate: float | None = None
    child_funding_mode: ChildFundingMode | None = None
    hazard_damage: float | None = None
    hazard_avoidance_weight: float | None = None


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


# v0.16 arms — reproduction-economics substrate variants under
# reflex-baseline (no scalar memory). Sweeps energy_cost in {35, 25, 15}
# while holding energy_threshold at 50; tests whether the v0.14/v0.15 H2
# compounding ceiling is imposed by the parent's post-birth energy
# retention. See [[docs/experiments/fear_hunger_v0.16.md]].
V0_16_ARMS: tuple[Arm, ...] = (
    Arm(
        label="cost-35",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=35.0,
        energy_threshold=50.0,
    ),
    Arm(
        label="cost-25",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=25.0,
        energy_threshold=50.0,
    ),
    Arm(
        label="cost-15",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
    ),
)


# v0.17 arms — offspring-start-energy substrate variants under
# reflex-baseline + cost-15 (the v0.16 best). Sweeps
# offspring_start_energy in {30, 60, 100} while holding the v0.16
# cost-15 economics fixed; tests whether child survival is the
# binding constraint on lineage compounding. The
# offspring_start_energy=30 arm reproduces v0.16 cost-15
# bit-identically. See [[docs/experiments/fear_hunger_v0.17.md]].
V0_17_ARMS: tuple[Arm, ...] = (
    Arm(
        label="start-30",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
    ),
    Arm(
        label="start-60",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=60.0,
    ),
    Arm(
        label="start-100",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=100.0,
    ),
)


# v0.18 arms — food-respawn-cooldown variants under reflex-baseline +
# cost-15 + offspring_start_energy=30 (the v0.17 baseline). Sweeps
# food_respawn_cooldown in {None, 100, 50, 20}; tests whether
# non-saturating food alone (without raising offspring energy)
# supports lineage compounding. The K-inf arm reproduces v0.17
# start-30 bit-identically. See [[docs/experiments/fear_hunger_v0.18.md]].
V0_18_ARMS: tuple[Arm, ...] = (
    Arm(
        label="K-inf",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=None,
    ),
    Arm(
        label="K-100",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=100,
    ),
    Arm(
        label="K-50",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
    ),
    Arm(
        label="K-20",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=20,
    ),
)


# v0.19 arms — strict mass-energy conservation. Builds on v0.18's K=50
# productive cooldown and adds a finite ambient energy pool (respawn +
# child-startup pool-funded; metabolism + parent repro = heat loss;
# death residual recycles).
#
# Brackets are anchored on the per-RUN demand observed empirically
# under v0.18 K-50: ~11 energy/tick total drain (7.2 respawn + 3.8
# child startup) on tight_gradient, ~9/tick on food_ladder, with
# near-zero death recycling on tight (starvation dominates) and
# ~80 energy/seed recycling on food_ladder (hazard injuries). The
# initial v0.19 sweep (commit b6a43c5) ran with brackets
# {5K, 15K, 30K} that were 8x too generous — every closed-pool arm
# trivially had budget for the full 200-tick run, so no arm
# stressed the conservation question. The corrected brackets below
# bracket the 200-tick demand from below (500 starves early),
# at-target (1500 sits near 200-tick demand of ~2200), and above
# (3000 has comfortable margin).
#
# Seven arms: 4 closed-pool sizes at K=50 (A inf-pool reference,
# B/C/D 500/1500/3000), 1 K=100 cooldown hedge at 1500, 2 open-
# ecology arms at influx 2/7 per tick (low-influx and v0.18-
# equivalent flux). The ``inf-pool`` arm reproduces v0.18 K-50
# bit-identically (energy_pool_initial=None disables the pool path).
# See [[docs/experiments/fear_hunger_v0.19.md]].
V0_19_ARMS: tuple[Arm, ...] = (
    Arm(
        label="inf-pool",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=None,
        ambient_influx_rate=None,
    ),
    Arm(
        label="closed-500",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=500.0,
        ambient_influx_rate=0.0,
    ),
    Arm(
        label="closed-1500",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
    ),
    Arm(
        label="closed-3000",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
    ),
    Arm(
        label="closed-1500-K100",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=100,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
    ),
    Arm(
        label="open-low",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=2.0,
    ),
    Arm(
        label="open-equiv",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=7.0,
    ),
)


# v0.20 arms — parent-transfer + pool-gap reproduction. Tests whether
# routing the parent's reproduction cost into offspring startup energy
# (with the pool funding only the remaining gap) lifts compounding in
# regimes where v0.19's pool was the binding constraint. Six arms across
# three regimes:
#
#   - closed-1500 (v0.19's binding-conservation regime, the headline
#     comparison): A POOL_FULL reference vs B PARENT_TRANSFER_POOL_GAP test.
#   - open-low influx=2 (v0.19's partial-rescue regime): C POOL_FULL
#     reference vs D PARENT_TRANSFER_POOL_GAP test.
#   - closed-3000 (v0.19's null regime, pool not binding): E POOL_FULL
#     reference vs F PARENT_TRANSFER_POOL_GAP NEGATIVE CONTROL — F must
#     equal E byte-for-byte on per-agent observables (per-tick agent
#     state is mode-invariant when neither pool gate fires); pool ledger
#     fields legitimately differ.
#
# K=50 throughout; offspring_start_energy=30, energy_cost=15 (gap=15).
# Drops v0.19's K=100 hedge and open-equiv arms (settled). Reflex-baseline
# policy. See [[docs/experiments/fear_hunger_v0.20.md]].
V0_20_ARMS: tuple[Arm, ...] = (
    Arm(
        label="pool-full-1500",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    ),
    Arm(
        label="transfer-1500",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="pool-full-open-low",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=2.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    ),
    Arm(
        label="transfer-open-low",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=2.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="pool-full-3000",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.POOL_FULL,
    ),
    Arm(
        label="transfer-3000",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=3_000.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
)


# v0.21 arms — influx frontier under PARENT_TRANSFER_POOL_GAP at fixed
# pool_initial=1500. Sweeps ambient_influx_rate uniformly between v0.20's
# two endpoints (0 and 2 / tick) to map where the productivity transition
# lies under conservation-faithful reproduction.
#
# Endpoints A (influx=0.0) and E (influx=2.0) are deliberate anchors:
#   A reproduces v0.20 transfer-1500 byte-identically on both chambers
#     (influx=0.0 is a no-op by construction).
#   E reproduces v0.20 transfer-open-low byte-identically on food_ladder
#     and via semantic-regression on tight_gradient (v0.20 transfer-open-
#     low tight had 3 r_blk + 9 b_blk timing perturbation; aggregate
#     metrics must match exactly, event stream is not required).
#
# Three intermediate arms B/C/D (influx 0.5 / 1.0 / 1.5) map the frontier.
# Operational primary i* is the lowest arm whose births_after_tick_50
# clears 90% of arm E's b>50 (= 117 tight, 83 food_ladder); secondary i*
# uses total_births (= 184 tight, 129 food_ladder).
#
# K=50, energy_cost=15, energy_threshold=50, offspring_start_energy=30,
# pool_initial=1500 throughout. Reflex-baseline policy. See
# [[docs/experiments/fear_hunger_v0.21.md]].
V0_21_ARMS: tuple[Arm, ...] = (
    Arm(
        label="transfer-1500-influx-0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="transfer-1500-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="transfer-1500-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="transfer-1500-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
    Arm(
        label="transfer-1500-influx-2.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=2.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
    ),
)


# v0.22 arms — narrow hazard-damage sweep on food_ladder under
# PARENT_TRANSFER_POOL_GAP at pool_initial=1500 + ambient_influx_rate=1.0
# (the v0.21 productivity transition). Tests whether the v0.21 food_ladder
# productivity plateau (143/92 b>50 at influx>=1.0) is fueled by hazard-
# injury death-residual recycling or by chamber geometry.
#
# hazard_damage in {0, 4, 8, 12}:
#   - 0 is the crucial control: zero injury deaths -> zero residual
#     recycling; chamber geometry preserved. If productivity drops,
#     recycling/injury dynamics are load-bearing under this layout.
#   - 4 sub-default: agents survive ~25 ticks of continuous residency;
#     reduced recycling pressure.
#   - 8 = build_chamber_layout default. **Byte-identity anchor against
#     v0.21 transfer-1500-influx-1.0 food_ladder** (143/92).
#   - 12 super-default: agents survive ~8 ticks of continuous residency;
#     elevated recycling pressure.
#
# Same 8 seeds (1..8) as v0.21 so per-seed comparisons are interpretable.
# food_ladder only — tight_gradient is starvation-dominated with near-
# zero recycling already; sweeping hazard_damage on tight tests a near-
# null channel. See [[docs/experiments/fear_hunger_v0.22.md]].
V0_22_ARMS: tuple[Arm, ...] = (
    Arm(
        label="hazard-0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="hazard-4",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=4.0,
    ),
    Arm(
        label="hazard-8",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
    ),
    Arm(
        label="hazard-12",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=12.0,
    ),
)


# v0.23 arms — hazard-zero influx frontier on both chambers. Mirrors the
# v0.21 V0_21_ARMS structure (5 arms across ambient_influx_rate ∈
# {0, 0.5, 1.0, 1.5, 2.0} at PARENT_TRANSFER_POOL_GAP, pool_initial=1500)
# but pins hazard_damage=0.0 on every arm. Tests whether the v0.21
# food_ladder vs tight_gradient 1.0/tick chamber asymmetry survives when
# hazard injury/cull/recycling is removed.
#
# v0.22 falsified the recycling-as-fuel hypothesis (hazard=0 food_ladder
# at influx=1.0 produces b>50=116, 26% above the v0.21 saturation
# plateau) — the recycling channel was a net tax, not a fuel. v0.23 now
# isolates the chamber-asymmetry mechanism by re-running the v0.21
# influx frontier on both chambers under hazard=0.
#
# Endpoints + anchors:
#   A (influx=0.0): closed-pool, no influx, no recycling. New regime;
#     no prior anchor.
#   C (influx=1.0): byte-identity anchor against v0.22 hazard-0 on
#     food_ladder (the v0.22 sweep already ran this exact arm; same
#     8 seeds make this a deductive identity).
#   E (influx=2.0): high-influx endpoint. Self-referential 90%
#     threshold for primary i*.
#
# K=50, energy_cost=15, energy_threshold=50, offspring_start_energy=30,
# pool_initial=1500, hazard_damage=0 throughout. Reflex-baseline policy.
# See [[docs/experiments/fear_hunger_v0.23.md]].
V0_23_ARMS: tuple[Arm, ...] = (
    Arm(
        label="transfer-1500-hzd0-influx-0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-2.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=2.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
)


# v0.25 arms — hazard x influx timing-regulation sweep on both chambers.
# Tests the pool-exhaustion-timing mechanism candidate that emerged from
# v0.24's diagnostic. Cross-product of hazard ∈ {0, 4, 8, 12} x influx ∈
# {0.5, 1.0, 1.5} = 12 arms, run on both food_ladder and tight_gradient
# under PARENT_TRANSFER_POOL_GAP at pool_initial=1500. Same 8 seeds as
# v0.21/v0.22/v0.23.
#
# Pre-committed predictions (see [[docs/experiments/fear_hunger_v0.25.md]]):
#   - H6: tick-of-peak monotonically decreases as hazard decreases on
#     both chambers (direct mechanism observable).
#   - H7: food_ladder b>50 monotone non-increasing in hazard at every
#     influx (cull-tax dominates throughout).
#   - H8: tight b>50 non-monotonic in hazard at some influx (cull-tax +
#     timing penalty net out with an interior optimum).
#
# 14 byte-identity anchors built into the grid:
#   - hazard=0, influx ∈ {0.5, 1.0, 1.5}, both chambers (= V0_23_ARMS B/C/D).
#   - hazard=8, influx ∈ {0.5, 1.0, 1.5}, both chambers (= V0_21_ARMS B/C/D).
#   - hazard ∈ {4, 12}, influx=1.0, food_ladder (= V0_22_ARMS hazard-4,
#     hazard-12).
# 10 truly-new cells; the remainder reproduce prior aggregates exactly.
V0_25_ARMS: tuple[Arm, ...] = (
    # Hazard 0 row (= V0_23_ARMS B/C/D): byte-identity anchors on both chambers.
    Arm(
        label="transfer-1500-hzd0-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    Arm(
        label="transfer-1500-hzd0-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
    ),
    # Hazard 4 row: 1 anchor (food_ladder influx=1.0 = V0_22 hazard-4),
    # 5 new cells (tight x all 3 influxes; food_ladder x influx ∈ {0.5, 1.5}).
    Arm(
        label="transfer-1500-hzd4-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=4.0,
    ),
    Arm(
        label="transfer-1500-hzd4-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=4.0,
    ),
    Arm(
        label="transfer-1500-hzd4-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=4.0,
    ),
    # Hazard 8 row (= V0_21_ARMS B/C/D): byte-identity anchors on both chambers.
    Arm(
        label="transfer-1500-hzd8-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
    ),
    Arm(
        label="transfer-1500-hzd8-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
    ),
    Arm(
        label="transfer-1500-hzd8-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
    ),
    # Hazard 12 row: 1 anchor (food_ladder influx=1.0 = V0_22 hazard-12),
    # 5 new cells.
    Arm(
        label="transfer-1500-hzd12-influx-0.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=0.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=12.0,
    ),
    Arm(
        label="transfer-1500-hzd12-influx-1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=12.0,
    ),
    Arm(
        label="transfer-1500-hzd12-influx-1.5",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.5,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=12.0,
    ),
)


# v0.26 arms — perception-vs-damage decoupling. 2x2 grid:
# hazard_damage in {0, 8} x hazard_avoidance_weight in {0.0, 1.0}, run on
# both food_ladder and tight_gradient at influx=1.0 under
# PARENT_TRANSFER_POOL_GAP, pool_initial=1500. Same 8 seeds as
# v0.21/v0.22/v0.23/v0.25.
#
# Reading A — pure policy seam: hazard_avoidance_weight multiplies pain_w
# in GradientPolicy. At hazard_damage=0 the world's hazard layer is zero,
# so hazard_signal_* is zero, and the multiplier is dormant. Therefore
# arms C (phantom: damage=0, weight=1.0) and D (no-hazard: damage=0,
# weight=0.0) are deductively identical to v0.25 hazard=0 cells; the
# substantive new cell is B (invisible: damage=8, weight=0.0), which
# isolates "damage applies, no avoidance pull" — the decisive observable
# for whether tight's small cull-tax under v0.25 was avoidance-driven.
#
# Six byte-identity anchors (against v0.25 sweep artifacts at influx=1.0):
#   - A on tight       = V0_25 transfer-1500-hzd8-influx-1.0 (b>50=116)
#   - C on tight       = V0_25 transfer-1500-hzd0-influx-1.0 (b>50=100)
#   - D on tight       = V0_25 transfer-1500-hzd0-influx-1.0 (b>50=100)
#   - A on food_ladder = V0_25 transfer-1500-hzd8-influx-1.0 (b>50= 92)
#   - C on food_ladder = V0_25 transfer-1500-hzd0-influx-1.0 (b>50=116)
#   - D on food_ladder = V0_25 transfer-1500-hzd0-influx-1.0 (b>50=116)
# B (invisible) on each chamber is the truly new cell. See
# [[docs/experiments/fear_hunger_v0.26.md]].
V0_26_ARMS: tuple[Arm, ...] = (
    Arm(
        label="hzd8-avd1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=1.0,
    ),
    Arm(
        label="hzd8-avd0.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=0.0,
    ),
    Arm(
        label="hzd0-avd1.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
        hazard_avoidance_weight=1.0,
    ),
    Arm(
        label="hzd0-avd0.0",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=0.0,
        hazard_avoidance_weight=0.0,
    ),
)


# v0.27 arms — avoidance-weight frontier on both chambers at fixed
# hazard=8, influx=1.0, transfer/pool=1500. Fills the v0.26 binary
# endpoint pair (weight in {0.0, 1.0}) with three interior points
# (weight in {0.25, 0.5, 0.75}) to discriminate the curve shape:
# monotone, concave-monotone (diminishing returns), or interior optimum.
#
# Central question (per [[docs/experiments/fear_hunger_v0.27.md]]):
# is avoidance monotonically beneficial, monotonically costly, or
# does it have an interior optimum?
#
# Four byte-identity anchors against v0.26:
#   - tight       w=0.0 = V0_26 hzd8-avd0.0 (invisible-tight, b>50=107)
#   - tight       w=1.0 = V0_26 hzd8-avd1.0 (coupled-tight,   b>50=116)
#   - food_ladder w=0.0 = V0_26 hzd8-avd0.0 (invisible-food,  b>50= 88)
#   - food_ladder w=1.0 = V0_26 hzd8-avd1.0 (coupled-food,    b>50= 92)
# 6 truly-new cells (3 interior weights x 2 chambers); the remainder
# reproduce v0.26 aggregates exactly.
V0_27_ARMS: tuple[Arm, ...] = (
    Arm(
        label="hzd8-avd0.00",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=0.0,
    ),
    Arm(
        label="hzd8-avd0.25",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=0.25,
    ),
    Arm(
        label="hzd8-avd0.50",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=0.5,
    ),
    Arm(
        label="hzd8-avd0.75",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=0.75,
    ),
    Arm(
        label="hzd8-avd1.00",
        policy_factory=_gradient_policy_factory,
        auto_reproduction=True,
        memory_type=None,
        energy_cost=15.0,
        energy_threshold=50.0,
        offspring_start_energy=30.0,
        food_respawn_cooldown=50,
        energy_pool_initial=1_500.0,
        ambient_influx_rate=1.0,
        child_funding_mode=ChildFundingMode.PARENT_TRANSFER_POOL_GAP,
        hazard_damage=8.0,
        hazard_avoidance_weight=1.0,
    ),
)


# v0.29 — food_ladder w=0.75 dip reproducibility on a fresh seed stream.
# The arms are a literal 3-tuple slice of V0_27_ARMS at the dip-neighborhood
# weights {0.5, 0.75, 1.0} (the v0.28 paired-comparison cells).
# Substrate-byte-identity to V0_27_ARMS is by-construction (same Arm
# instances) — the v0.29 sweep differs from v0.27 *only* in the seed set
# (9..16 instead of 1..8). Pre-reg:
# [[docs/experiments/fear_hunger_v0.29.md]].
V0_29_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_27_ARMS if arm.label in ("hzd8-avd0.50", "hzd8-avd0.75", "hzd8-avd1.00")
)


# v0.30 — tight w*=0.75 small-margin robustness audit on a fresh seed stream.
# Same 3-arm literal slice of V0_27_ARMS as V0_29_ARMS at the same labels
# (the substrate arm objects are shared); the sweep differs from v0.29 in
# the chamber (tight_gradient instead of food_ladder) and from v0.27 in
# the seed set (9..16 instead of 1..8). Pre-reg:
# [[docs/experiments/fear_hunger_v0.30.md]].
V0_30_TIGHT_W_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_27_ARMS if arm.label in ("hzd8-avd0.50", "hzd8-avd0.75", "hzd8-avd1.00")
)


# v0.31 — tight w*=0.75 third-stream calibration on a third independent seed
# stream (17..24). Same 3-arm literal slice of V0_27_ARMS as V0_29_ARMS /
# V0_30_TIGHT_W_ARMS at the same labels (substrate arm objects are shared);
# the sweep differs from v0.30 only in the seed set (17..24 instead of 9..16).
# The v0.31 audit then pools streams 1..8, 9..16, 17..24 and applies a
# pre-committed pooled 24-seed classifier with linearly-scaled thresholds.
# Pre-reg: [[docs/experiments/fear_hunger_v0.31.md]].
V0_31_TIGHT_W_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_27_ARMS if arm.label in ("hzd8-avd0.50", "hzd8-avd0.75", "hzd8-avd1.00")
)


# v0.32 — tight h*=8 hazard-axis reproducibility audit on seeds 9..16. Literal
# 4-arm slice of V0_25_ARMS at influx=1.0 across hazards {0, 4, 8, 12}.
# Substrate: hazard_avoidance_weight=None (true v0.25 substrate, pre-v0.26
# default avoidance behaviour). The H1c semantic determinism anchor pins
# hzd=8/seeds 9..16/B=96 against v0.30 stream 2 explicit-w=1.0; failure halts
# the audit. Classifier slice {h=4, h=8, h=12} maps to (0.50, 0.75, 1.00)
# slots; h=0 is descriptive baseline only.
# Pre-reg: [[docs/experiments/fear_hunger_v0.32.md]].
V0_32_TIGHT_H_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_25_ARMS if arm.label.endswith("-influx-1.0")
)


# v0.33 — tight h*=8 hazard-axis third-stream calibration on seeds 17..24.
# Literal 4-arm slice of V0_25_ARMS at influx=1.0 across hazards {0, 4, 8, 12}
# — element-wise identical to V0_32_TIGHT_H_ARMS by construction. The
# distinct binding name pins the v0.33 audit's intent (third-stream
# calibration mirroring v0.31's weight-axis pattern); substrate-byte-identity
# is guarded by H1 / H1b literal-subset and arm-object-identity tests.
# Pre-reg: [[docs/experiments/fear_hunger_v0.33.md]].
V0_33_TIGHT_H_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_25_ARMS if arm.label.endswith("-influx-1.0")
)


# v0.39 — fresh-stream calibration of v0.38's H5 LEADER-ADVANTAGE-AMPLIFIED
# on seeds 25..32. Literal 4-arm slice of V0_25_ARMS at influx=1.0 across
# hazards {0, 4, 8, 12} — element-wise identical to V0_32_TIGHT_H_ARMS and
# V0_33_TIGHT_H_ARMS by construction. The distinct binding name pins v0.39's
# fresh-stream-calibration intent (first new sweep added since v0.34; tests
# whether the v0.38 leader post-50 advantage effect reproduces on an
# independent seed stream).
# Pre-reg: [[docs/experiments/fear_hunger_v0.39.md]].
V0_39_TIGHT_H_ARMS: tuple[Arm, ...] = tuple(
    arm for arm in V0_25_ARMS if arm.label.endswith("-influx-1.0")
)


# ---------------------------------------------------------------------------
# Per-run analysis from events.jsonl (cheap, on already-written artifacts).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunDiagnostics:
    """Per-run derived metrics computed from events.jsonl.

    v0.16 adds compounding telemetry:
      - ``total_distinct_parents`` — count of unique parent_ids that
        appear in any AgentBorn event.
      - ``total_post_birth_lifespan_ticks`` — sum across distinct
        parents of (death_tick - first_birth_tick); death_tick falls
        back to ``max_event_tick`` for parents alive at run end.

    v0.17 adds the direct compounding metric:
      - ``total_grandchildren_count`` — number of AgentBorn events
        whose parent_id is itself an agent_id that appeared as the
        new agent in some prior AgentBorn event. Founders never
        appear as AgentBorn (they spawn via ``_spawn_founder`` with
        no event), so first-generation births (parent = founder)
        do not count; only second-generation-and-beyond births do.

    v0.18 adds the respawn telemetry:
      - ``total_food_respawn_events`` — count of FoodRespawned
        emissions. Always 0 when no cooldown is configured.

    v0.19 adds the pool-block telemetry:
      - ``total_pool_respawn_denied`` — count of PoolRespawnDenied
        emissions (respawn attempts blocked by empty pool). Always
        0 when no pool is configured.
      - ``total_pool_birth_denied`` — count of PoolBirthDenied
        emissions (birth attempts blocked by empty pool). Always
        0 when no pool is configured.

    v0.20 adds the parent-energy block telemetry:
      - ``total_births_blocked_by_parent_energy`` — count of
        BirthDeniedParentEnergy emissions (queued births denied because
        the parent's energy fell below ``energy_cost`` between queue
        and process time). Always 0 under POOL_FULL mode (the gate
        fires only under PARENT_TRANSFER_POOL_GAP).
    """

    births_after_tick_50: int
    still_ticks: int
    move_ticks: int
    eat_ticks: int
    other_ticks: int
    total_distinct_parents: int
    total_post_birth_lifespan_ticks: int
    total_grandchildren_count: int
    total_food_respawn_events: int
    total_pool_respawn_denied: int
    total_pool_birth_denied: int
    total_births_blocked_by_parent_energy: int = 0

    @property
    def total_action_ticks(self) -> int:
        return self.still_ticks + self.move_ticks + self.eat_ticks + self.other_ticks

    @property
    def still_tick_fraction(self) -> float:
        total = self.total_action_ticks
        return (self.still_ticks / total) if total > 0 else 0.0


def _read_run_diagnostics(  # noqa: PLR0912, PLR0915 — single-pass dispatch is cohesive.
    events_jsonl: Path, *, threshold: int = DEFAULT_TICK_THRESHOLD
) -> RunDiagnostics:
    """Walk events.jsonl once to derive birth-tick + per-action counts.

    Single pass. Tracks distinct parent_ids and the first AgentBorn tick
    per parent for post-birth-lifespan computation; tracks AgentDied
    ticks per agent_id for the matching death tick. Parents alive at
    run end use ``max_event_tick`` as the lifespan endpoint.
    """
    births_after = 0
    still = move = eat = other = 0
    first_birth_tick: dict[int, int] = {}
    death_tick: dict[int, int] = {}
    born_agent_ids: set[int] = set()
    grandchildren_count = 0
    food_respawn_count = 0
    pool_respawn_denied_count = 0
    pool_birth_denied_count = 0
    parent_energy_denied_count = 0
    max_event_tick = 0
    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = row.get("type")
            tick = int(row.get("tick", 0))
            max_event_tick = max(max_event_tick, tick)
            event = row.get("event", {})
            if kind == "AgentBorn":
                if tick > threshold:
                    births_after += 1
                parent_id = event.get("parent_id")
                if parent_id is not None:
                    pid = int(parent_id)
                    # First birth tick wins; later births update the
                    # parent's birth count via total_births in
                    # ChamberRunResult (we do not double-count here).
                    if pid not in first_birth_tick:
                        first_birth_tick[pid] = tick
                    # Grandchild check: a birth whose parent was itself
                    # born during this run (i.e. not a founder). Causal
                    # ordering guarantees the parent's AgentBorn event
                    # is in the JSONL before any of its children's, so
                    # a single forward pass is correct.
                    if pid in born_agent_ids:
                        grandchildren_count += 1
                agent_id = event.get("agent_id")
                if agent_id is not None:
                    born_agent_ids.add(int(agent_id))
            elif kind == "AgentDied":
                aid = event.get("agent_id")
                if aid is not None:
                    death_tick[int(aid)] = tick
            elif kind == "AgentStayed":
                still += 1
            elif kind == "AgentMoved":
                move += 1
            elif kind == "AteFood":
                eat += 1
            elif kind in {"HazardDamageApplied", "HazardEntered"}:
                # Body-physics events; not action emissions.
                pass
            elif kind == "FoodRespawned":
                # Environmental event (v0.18). Counted; not an action emission.
                food_respawn_count += 1
            elif kind == "PoolRespawnDenied":
                # v0.19: respawn attempt blocked by empty pool. Counted;
                # not an action emission.
                pool_respawn_denied_count += 1
            elif kind == "PoolBirthDenied":
                # v0.19: birth attempt blocked by empty pool. Counted;
                # not an action emission.
                pool_birth_denied_count += 1
            elif kind == "BirthDeniedParentEnergy":
                # v0.20: birth attempt blocked because parent's energy
                # dropped below energy_cost between queue and process
                # time. Counted; not an action emission. Always 0 under
                # POOL_FULL.
                parent_energy_denied_count += 1
            elif kind == "ReproductionRequested":
                # Reproduction is auto-substrate (B, C) or voluntary action
                # (A). In A it's an action emission alongside AgentStayed
                # (apply_action(REPRODUCE) emits both? — actually no, only
                # ReproductionRequested). Count it separately as "other".
                other += 1
            else:
                other += 1

    total_lifespan = 0
    for pid, first_tick in first_birth_tick.items():
        end_tick = death_tick.get(pid, max_event_tick)
        total_lifespan += max(0, end_tick - first_tick)

    return RunDiagnostics(
        births_after_tick_50=births_after,
        still_ticks=still,
        move_ticks=move,
        eat_ticks=eat,
        other_ticks=other,
        total_distinct_parents=len(first_birth_tick),
        total_post_birth_lifespan_ticks=total_lifespan,
        total_grandchildren_count=grandchildren_count,
        total_food_respawn_events=food_respawn_count,
        total_pool_respawn_denied=pool_respawn_denied_count,
        total_pool_birth_denied=pool_birth_denied_count,
        total_births_blocked_by_parent_energy=parent_energy_denied_count,
    )


# ---------------------------------------------------------------------------
# Per-cell aggregate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmCellAggregate:
    """Per-(arm, chamber) aggregate across a seed sweep.

    v0.16 adds compounding telemetry summed across seeds:
      - ``total_distinct_parents`` — number of unique parent_ids that
        produced at least one AgentBorn event.
      - ``total_post_birth_lifespan_ticks`` — sum across distinct
        parents of (death_or_run_end_tick - first_birth_tick).

    v0.17 adds the direct compounding metric summed across seeds:
      - ``total_grandchildren_count`` — total AgentBorn events whose
        parent was itself born during the run. The seed-denominator
        rate is exposed via ``mean_grandchildren_per_seed`` below.

    v0.18 adds respawn telemetry + the conservation-accounting ratio:
      - ``total_food_respawn_events`` — count of FoodRespawned
        emissions (always 0 when no cooldown is configured).
      - ``food_consumed_per_birth`` (property) — environmental energy
        per birth = (food_events * food_value_default) / total_births.
        Quantifies "is the substrate paying for births with food."
    """

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
    total_distinct_parents: int
    total_post_birth_lifespan_ticks: int
    total_grandchildren_count: int
    total_food_respawn_events: int
    # v0.18: snapshot of WorldConfig.food_value_default at sweep time so
    # food_consumed_per_birth is computed without re-reading config.
    food_value_default: float
    # v0.19 strict-conservation telemetry (all default to 0 / 0.0 when
    # no ambient pool was configured on the arm).
    total_pool_respawn_denied: int = 0
    total_pool_birth_denied: int = 0
    total_pool_out_respawn: float = 0.0
    total_pool_out_child_startup: float = 0.0
    total_pool_in_death_residual: float = 0.0
    total_pool_in_ambient_influx: float = 0.0
    pool_min_observed: float | None = None
    pool_max_observed: float | None = None
    mean_pool_end: float | None = None
    # v0.20 conservation-ledger telemetry. Under POOL_FULL only
    # ``total_reproduction_heat_loss`` is non-zero; under
    # PARENT_TRANSFER_POOL_GAP only
    # ``total_parent_energy_transferred_to_child`` is non-zero.
    # ``total_births_blocked_by_parent_energy`` counts the new
    # transfer-mode-only failure path.
    total_reproduction_heat_loss: float = 0.0
    total_parent_energy_transferred_to_child: float = 0.0
    total_births_blocked_by_parent_energy: int = 0
    # v0.22 injury-death telemetry. Surfaced from
    # ``ChamberRunResult.injury_deaths`` so v0.22's hazard_damage sweep
    # can distinguish "no injuries because hazard=0" from "no injuries
    # because agents avoided hazards" — both produce low
    # pool_in_death_residual but mean different things mechanistically.
    # Default 0 preserves bit-identity for prior aggregates.
    total_injury_deaths: int = 0

    @property
    def mean_births_per_parent(self) -> float:
        """Mean births per parent. >1 indicates compounding."""
        return (
            (self.total_births / self.total_distinct_parents)
            if self.total_distinct_parents > 0
            else 0.0
        )

    @property
    def mean_post_birth_lifespan_ticks(self) -> float:
        """Mean ticks a parent survives after its first birth."""
        return (
            (self.total_post_birth_lifespan_ticks / self.total_distinct_parents)
            if self.total_distinct_parents > 0
            else 0.0
        )

    @property
    def mean_grandchildren_per_seed(self) -> float:
        """Mean grandchildren per run (denominator = ``n_seeds``).

        Different denominator from ``mean_births_per_parent``: this is
        a per-run rate of second-generation-and-beyond births, useful
        for comparing arms whose ``total_distinct_parents`` differ.
        """
        return (self.total_grandchildren_count / self.n_seeds) if self.n_seeds > 0 else 0.0

    @property
    def food_consumed_per_birth(self) -> float:
        """Environmental energy per birth (v0.18 conservation-accounting).

        ``(total_food_events * food_value_default) / total_births``.

        Under v0.17 start-100 (handout) this ratio is artificially low
        (~9.5) — many births were "free" from offspring_start_energy.
        Under v0.18 (no handout, baseline offspring=30) the floor for
        self-sustaining births is ``energy_cost + offspring_start_energy
        = 45``; values approaching that floor indicate the substrate
        is paying for births with food. Returns 0.0 when total_births
        is zero (vacuous early-termination runs).
        """
        return (
            (self.total_food_events * self.food_value_default) / self.total_births
            if self.total_births > 0
            else 0.0
        )


def _aggregate(
    arm: Arm,
    layout_name: str,
    pairs: list[tuple[ChamberRunResult, RunDiagnostics]],
) -> ArmCellAggregate:
    # ``food_value_default`` matches ``build_chamber_layout`` (20.0); update
    # both if the chamber spec ever varies food yield.
    food_value_default = 20.0
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
            total_distinct_parents=0,
            total_post_birth_lifespan_ticks=0,
            total_grandchildren_count=0,
            total_food_respawn_events=0,
            food_value_default=food_value_default,
        )
    results = [r for r, _d in pairs]
    diags = [d for _r, d in pairs]
    n = len(pairs)
    still_fractions = [d.still_tick_fraction for d in diags]
    # v0.19 pool aggregation. Min/max are taken across seeds; mean_pool_end
    # averages across seeds. None when no seed configured a pool (the
    # v0.7..v0.18 path).
    pool_results = [r for r in results if r.pool_initial is not None]
    if pool_results:
        pool_min_observed: float | None = min(
            r.pool_min for r in pool_results if r.pool_min is not None
        )
        pool_max_observed: float | None = max(
            r.pool_max for r in pool_results if r.pool_max is not None
        )
        ends = [r.pool_end for r in pool_results if r.pool_end is not None]
        mean_pool_end: float | None = sum(ends) / len(ends) if ends else None
    else:
        pool_min_observed = None
        pool_max_observed = None
        mean_pool_end = None
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
        total_distinct_parents=sum(d.total_distinct_parents for d in diags),
        total_post_birth_lifespan_ticks=sum(d.total_post_birth_lifespan_ticks for d in diags),
        total_grandchildren_count=sum(d.total_grandchildren_count for d in diags),
        total_food_respawn_events=sum(d.total_food_respawn_events for d in diags),
        food_value_default=food_value_default,
        total_pool_respawn_denied=sum(d.total_pool_respawn_denied for d in diags),
        total_pool_birth_denied=sum(d.total_pool_birth_denied for d in diags),
        total_pool_out_respawn=sum(r.pool_out_respawn for r in results),
        total_pool_out_child_startup=sum(r.pool_out_child_startup for r in results),
        total_pool_in_death_residual=sum(r.pool_in_death_residual for r in results),
        total_pool_in_ambient_influx=sum(r.pool_in_ambient_influx for r in results),
        pool_min_observed=pool_min_observed,
        pool_max_observed=pool_max_observed,
        mean_pool_end=mean_pool_end,
        total_reproduction_heat_loss=sum(r.reproduction_heat_loss for r in results),
        total_parent_energy_transferred_to_child=sum(
            r.parent_energy_transferred_to_child for r in results
        ),
        total_births_blocked_by_parent_energy=sum(
            d.total_births_blocked_by_parent_energy for d in diags
        ),
        total_injury_deaths=sum(r.injury_deaths for r in results),
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
    repro_kwargs: dict[str, float] = {
        "energy_threshold": (
            arm.energy_threshold if arm.energy_threshold is not None else FIXED_ENERGY_THRESHOLD
        ),
        "energy_cost": arm.energy_cost if arm.energy_cost is not None else FIXED_ENERGY_COST,
    }
    # offspring_start_energy override (v0.17). Omitted when None so the
    # factory's default (30.0) preserves v0.14/v0.15/v0.16 bit-identity.
    if arm.offspring_start_energy is not None:
        repro_kwargs["offspring_start_energy"] = arm.offspring_start_energy
    repro_cfg = tuned_reproduction_config(**repro_kwargs)
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
        food_respawn_cooldown=arm.food_respawn_cooldown,
        energy_pool_initial=arm.energy_pool_initial,
        ambient_influx_rate=arm.ambient_influx_rate,
        child_funding_mode=arm.child_funding_mode,
        hazard_damage=arm.hazard_damage,
        hazard_avoidance_weight=arm.hazard_avoidance_weight,
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
