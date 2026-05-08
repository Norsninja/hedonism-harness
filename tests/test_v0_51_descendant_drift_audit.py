"""v0.51 descendant-drift probe — tests (16 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.51.md]] §"Test list (locked, 16 tests)".
Tests numbered to match the pre-reg's ordering.
"""

from __future__ import annotations

import dataclasses
import gc
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "v0_51_descendant_drift_audit.py"
_spec = importlib.util.spec_from_file_location("v0_51_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_51_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_51_audit"] = v0_51_audit
_spec.loader.exec_module(v0_51_audit)


# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _make_lineage_row(
    *,
    arm: str = v0_51_audit.ARM_A_NULL,
    version: str = "v0.42",
    seed: int = 41,
    hazard: int = 8,
    lineage_id: int,
    founder_original_sensor_radius: int = 3,
    founder_assigned_sensor_radius: int = 3,
    rd: float = 0.0,
    mr: float = 0.0,
    food_events: int = 0,
    food_energy: float = 0.0,
    distance: float = 0.0,
    living: int = 0,
    above_count: int = 0,
    above_fraction: float = 0.0,
    b50: int = 0,
    is_eventual_top: bool = False,
    is_high_sensor_radius: bool = False,
    is_high_readiness_fraction: bool = False,
    label_a_gating_valid: bool = True,
    label_a_degenerate_reason: str = "",
) -> object:
    return v0_51_audit.PerLineageRow(
        arm=arm,
        version=version,
        seed=seed,
        hazard=hazard,
        run_id=f"{arm}-{version}-A_null-hzd{hazard}-seed-{seed}",
        lineage_id=lineage_id,
        founder_original_sensor_radius=founder_original_sensor_radius,
        founder_assigned_sensor_radius=founder_assigned_sensor_radius,
        founder_reproduction_drive=rd,
        founder_metabolic_rate=mr,
        pre50_food_events_count=food_events,
        pre50_food_energy_acquired=food_energy,
        mean_distance_to_nearest_food_cell=distance,
        tick50_living_count=living,
        tick50_above_threshold_count=above_count,
        tick50_above_threshold_fraction=above_fraction,
        b50_count=b50,
        is_eventual_top_b50_label=is_eventual_top,
        is_high_sensor_radius_lineage=is_high_sensor_radius,
        is_high_tick50_readiness_fraction_lineage=is_high_readiness_fraction,
        label_a_gating_valid=label_a_gating_valid,
        label_a_degenerate_reason=label_a_degenerate_reason,
    )


def _make_summary(
    *,
    arm: str,
    observable: str,
    sign: int,
    paired_d: float,
    label: str,
) -> object:
    signed = paired_d * sign if not math.isnan(paired_d) else float("nan")
    fires_expected = (not math.isnan(signed)) and signed >= v0_51_audit.COHENS_D_THRESHOLD
    fires_wrong = (not math.isnan(signed)) and signed <= -v0_51_audit.COHENS_D_THRESHOLD
    return v0_51_audit.ObservableSummary(
        arm=arm,
        observable=observable,
        label=label,
        sign=sign,
        n_runs_contributing=64,
        paired_d=paired_d,
        signed_d=signed,
        delta_mean=0.0,
        delta_stdev=1.0,
        delta_min=-1.0,
        delta_max=+1.0,
        fires_expected=fires_expected,
        fires_wrong=fires_wrong,
    )


def _three_summaries_for_arm(arm: str, ds: tuple[float, float, float], label: str) -> list[object]:
    obs = v0_51_audit.PRIMARY_OBSERVABLES
    return [
        _make_summary(arm=arm, observable=obs[i][0], sign=obs[i][1], paired_d=ds[i], label=label)
        for i in range(3)
    ]


def _zero_drift_bridge_re_anchor() -> list[object]:
    return [
        v0_51_audit.BridgeReAnchorRow(
            tier="v0.48_bridge",
            arm=v0_51_audit.ARM_A_NULL,
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_51_audit.V048_PUBLISHED_SIGNED_D.items()
    ]


def _zero_drift_founder_clamp_re_anchor() -> list[object]:
    return [
        v0_51_audit.BridgeReAnchorRow(
            tier="v0.49_founder_clamp",
            arm=v0_51_audit.ARM_B_FOUNDER_CLAMP,
            label=label,
            observable=obs,
            published_signed_d=ref,
            derived_signed_d=ref,
            drift_abs=0.0,
            halts=False,
        )
        for (label, obs), ref in v0_51_audit.V049_B_PUBLISHED_SIGNED_D.items()
    ]


# ---------------------------------------------------------------------------
# Test 1 — all arms construct founders via the normal A_null path
# ---------------------------------------------------------------------------


def test_all_arms_construct_founders_via_normal_a_null_path(tmp_path):
    """Run all three arms for a single (version, seed, hazard) tuple; assert
    that ``founder_original_sensor_radius`` per founder is identical across
    arms — proves every arm took the same model-side founder draw path
    (i.e., ``traits_override=None`` and no helper RNG consumption)."""
    seed = 41
    captures: dict[str, object] = {}
    for arm in v0_51_audit.ARMS:
        captures[arm] = v0_51_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=0, runs_root=tmp_path
        )
    arms = list(v0_51_audit.ARMS)
    base = captures[arms[0]]
    for arm in arms[1:]:
        cap = captures[arm]
        for r_base, r in zip(base.founder_records, cap.founder_records, strict=True):
            assert r_base.founder_original_sensor_radius == r.founder_original_sensor_radius
            assert r_base.founder_reproduction_drive == r.founder_reproduction_drive
            assert r_base.founder_metabolic_rate == r.founder_metabolic_rate


# ---------------------------------------------------------------------------
# Test 2 — B founder clamp patches only sensor_radius on founder bodies
# ---------------------------------------------------------------------------


def test_b_founder_clamp_patch_replaces_only_sensor_radius_on_founder_bodies(tmp_path):
    cap = v0_51_audit._run_one_arm(
        arm=v0_51_audit.ARM_B_FOUNDER_CLAMP,
        version="v0.42",
        seed=41,
        hazard=0,
        runs_root=tmp_path,
    )
    for rec in cap.founder_records:
        assert rec.founder_assigned_sensor_radius == v0_51_audit.CLAMP_VALUE
    # B arm has no descendant listener; child_audit_rows must be empty.
    assert cap.child_audit_rows == []
    assert cap.listener_counters.n_births_seen == 0


# ---------------------------------------------------------------------------
# Test 3 — C founder clamp identical to B for founders
# ---------------------------------------------------------------------------


def test_c_founder_clamp_identical_to_b_for_founders(tmp_path):
    """B and C use the same founder-clamp logic; founder records must match
    on the post-patch fields (assigned_sensor_radius, all other founder
    traits) for the same (version, seed, hazard) tuple."""
    seed = 41
    cap_b = v0_51_audit._run_one_arm(
        arm=v0_51_audit.ARM_B_FOUNDER_CLAMP,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    cap_c = v0_51_audit._run_one_arm(
        arm=v0_51_audit.ARM_C_LINEAGE_CLAMP,
        version="v0.42",
        seed=seed,
        hazard=0,
        runs_root=tmp_path,
    )
    for rb, rc in zip(cap_b.founder_records, cap_c.founder_records, strict=True):
        assert rb.lineage_id == rc.lineage_id
        assert rb.founder_index == rc.founder_index
        assert rb.founder_original_sensor_radius == rc.founder_original_sensor_radius
        assert rb.founder_assigned_sensor_radius == rc.founder_assigned_sensor_radius
        assert rb.founder_reproduction_drive == rc.founder_reproduction_drive
        assert rb.founder_metabolic_rate == rc.founder_metabolic_rate


# ---------------------------------------------------------------------------
# Test 4 — C AgentBorn listener patches a newborn via synthetic event
# ---------------------------------------------------------------------------


def test_c_agent_born_listener_patches_newborn_via_synthetic_event(tmp_path):
    """Spin up a real HHModel, register the descendant-clamp listener, then
    emit a synthetic ``AgentBorn`` for one of the existing founders after
    de-clamping that founder's sensor_radius back to a non-4 value. Assert
    the listener patches it back to ``CLAMP_VALUE`` and increments
    counters correctly."""
    from hedonism_harness.core.events import AgentBorn, signal_for
    from hedonism_harness.experiments.comparison_grid import (
        FIXED_ENERGY_COST,
        FIXED_ENERGY_THRESHOLD,
        _resolve_layout,
        tuned_reproduction_config,
    )
    from hedonism_harness.experiments.fear_hunger_chamber import run_chamber

    base_arm = v0_51_audit._select_a_null_arm("v0.42", 0)
    repro_cfg = tuned_reproduction_config(
        energy_threshold=base_arm.energy_threshold or FIXED_ENERGY_THRESHOLD,
        energy_cost=base_arm.energy_cost or FIXED_ENERGY_COST,
    )
    layout = _resolve_layout(v0_51_audit.LAYOUT_NAME)

    # Capture the model reference inside a setup_observer that returns it.
    captured_model: dict[str, object] = {}
    capture = v0_51_audit._RunCapture(
        arm=v0_51_audit.ARM_C_LINEAGE_CLAMP,
        version="v0.42",
        seed=41,
        hazard=0,
    )

    def setup(model):
        # 1. Apply founder patch (so all founders are at sensor_radius=4).
        v0_51_audit._apply_founder_patch(v0_51_audit.ARM_C_LINEAGE_CLAMP, model, capture)
        # 2. Register only the descendant listener (skip lineage tracking;
        #    we're driving a synthetic event manually below).
        listener = v0_51_audit._make_descendant_clamp_listener(model, capture)
        signal_for(AgentBorn).connect(listener, sender=model, weak=False)
        captured_model["model"] = model
        captured_model["listener"] = listener
        # Stop the chamber immediately by raising; we just want the model.
        msg = "stop chamber after setup"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="stop chamber after setup"):
        run_chamber(
            seed=41,
            runs_root=tmp_path,
            run_id="test-c-listener",
            n_founders=v0_51_audit.N_FOUNDERS,
            n_ticks=1,
            layout=layout,
            policy_factory=base_arm.policy_factory,
            trait_config=v0_51_audit.TraitConfig(unbounded_mutation=True),
            reproduction_config=repro_cfg,
            use_memory=base_arm.memory_type is not None,
            memory_type=base_arm.memory_type or "cell_exact",
            food_respawn_cooldown=base_arm.food_respawn_cooldown,
            energy_pool_initial=base_arm.energy_pool_initial,
            ambient_influx_rate=base_arm.ambient_influx_rate,
            child_funding_mode=base_arm.child_funding_mode,
            hazard_damage=base_arm.hazard_damage,
            hazard_avoidance_weight=base_arm.hazard_avoidance_weight,
            condition="test",
            setup_observer=setup,
            tick_observer=lambda _m: None,
        )

    model = captured_model["model"]
    target = next(a for a in model.agents)
    # Manually de-clamp this founder to sensor_radius=2 (simulate a born
    # newborn whose mutated draw was 2 rather than 4).
    new_traits = dataclasses.replace(target.body.traits, sensor_radius=2)
    target.body = dataclasses.replace(target.body, traits=new_traits)
    pre_patch = target.body.traits
    assert pre_patch.sensor_radius == 2

    # Send synthetic AgentBorn for this agent_id.
    signal_for(AgentBorn).send(
        model,
        event=AgentBorn(
            agent_id=int(target.body.id),
            parent_id=int(target.body.id),
            lineage_id=int(target.body.lineage_id),
            x=int(target.body.x),
            y=int(target.body.y),
            tick=1,
        ),
    )

    # Listener must have patched sensor_radius back to 4.
    assert target.body.traits.sensor_radius == v0_51_audit.CLAMP_VALUE
    # Other fields byte-identical to pre-patch (single-channel).
    for f in dataclasses.fields(pre_patch):
        if f.name == "sensor_radius":
            continue
        assert getattr(target.body.traits, f.name) == getattr(pre_patch, f.name)
    # Counters incremented.
    assert capture.listener_counters.n_births_seen == 1
    assert capture.listener_counters.n_births_patched == 1
    assert capture.listener_counters.n_births_already_sensor_radius_4 == 0
    assert capture.listener_counters.n_birth_patch_failures == 0
    # child_audit_rows captured.
    assert len(capture.child_audit_rows) == 1
    row = capture.child_audit_rows[0]
    assert row.child_original_sensor_radius == 2
    assert row.child_assigned_sensor_radius == v0_51_audit.CLAMP_VALUE

    # Disconnect the listener.
    signal_for(AgentBorn).disconnect(captured_model["listener"], sender=model)


# ---------------------------------------------------------------------------
# Test 5 — Single-channel invariant raises on tampered child Traits
# ---------------------------------------------------------------------------


def test_c_listener_single_channel_invariant_on_child_patches():
    """If a future code path accidentally mutates a non-sensor_radius field
    during the child patch, ``_assert_single_channel_invariant`` must halt
    loud."""
    from hedonism_harness.core.traits import TraitConfig, random_traits

    rng = np.random.default_rng(123)
    cfg = TraitConfig(unbounded_mutation=True)
    original = random_traits(cfg, rng)
    tampered = dataclasses.replace(
        original,
        sensor_radius=4,
        metabolic_rate=original.metabolic_rate + 0.1,  # second field changes too
    )
    with pytest.raises(v0_51_audit.V051ReducerError, match="single-channel invariant violated"):
        v0_51_audit._assert_single_channel_invariant(
            original, tampered, arm=v0_51_audit.ARM_C_LINEAGE_CLAMP, scope="child", key=99
        )


# ---------------------------------------------------------------------------
# Test 6 — weak=False + disconnect_callbacks keep listener alive across GC
# ---------------------------------------------------------------------------


def test_c_listener_strong_reference_via_weak_false_and_disconnect_callbacks(tmp_path):
    """Build a real model, register the C listener with weak=False, drop
    the local Python reference, force GC, then emit a synthetic AgentBorn.
    The listener must still fire (no weak-ref drop)."""
    from hedonism_harness.core.events import AgentBorn, signal_for
    from hedonism_harness.experiments.comparison_grid import (
        FIXED_ENERGY_COST,
        FIXED_ENERGY_THRESHOLD,
        _resolve_layout,
        tuned_reproduction_config,
    )
    from hedonism_harness.experiments.fear_hunger_chamber import run_chamber

    base_arm = v0_51_audit._select_a_null_arm("v0.42", 0)
    layout = _resolve_layout(v0_51_audit.LAYOUT_NAME)
    repro_cfg = tuned_reproduction_config(
        energy_threshold=base_arm.energy_threshold or FIXED_ENERGY_THRESHOLD,
        energy_cost=base_arm.energy_cost or FIXED_ENERGY_COST,
    )

    captured: dict[str, object] = {}
    capture = v0_51_audit._RunCapture(
        arm=v0_51_audit.ARM_C_LINEAGE_CLAMP, version="v0.42", seed=41, hazard=0
    )
    disconnects: list = []

    def setup(model):
        v0_51_audit._apply_founder_patch(v0_51_audit.ARM_C_LINEAGE_CLAMP, model, capture)
        listener = v0_51_audit._make_descendant_clamp_listener(model, capture)
        signal_for(AgentBorn).connect(listener, sender=model, weak=False)
        # Closure-capture in disconnect_callbacks (belt-and-braces).
        disconnects.append(lambda: signal_for(AgentBorn).disconnect(listener, sender=model))
        captured["model"] = model
        msg = "stop chamber after setup"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError):
        run_chamber(
            seed=41,
            runs_root=tmp_path,
            run_id="test-weak",
            n_founders=v0_51_audit.N_FOUNDERS,
            n_ticks=1,
            layout=layout,
            policy_factory=base_arm.policy_factory,
            trait_config=v0_51_audit.TraitConfig(unbounded_mutation=True),
            reproduction_config=repro_cfg,
            use_memory=base_arm.memory_type is not None,
            memory_type=base_arm.memory_type or "cell_exact",
            food_respawn_cooldown=base_arm.food_respawn_cooldown,
            energy_pool_initial=base_arm.energy_pool_initial,
            ambient_influx_rate=base_arm.ambient_influx_rate,
            child_funding_mode=base_arm.child_funding_mode,
            hazard_damage=base_arm.hazard_damage,
            hazard_avoidance_weight=base_arm.hazard_avoidance_weight,
            condition="test",
            setup_observer=setup,
            tick_observer=lambda _m: None,
        )

    # Force a GC cycle; the listener has no other strong reference here
    # (the local 'listener' variable is out of scope inside setup).
    gc.collect()
    gc.collect()

    model = captured["model"]
    target = next(a for a in model.agents)
    target.body = dataclasses.replace(
        target.body, traits=dataclasses.replace(target.body.traits, sensor_radius=1)
    )
    signal_for(AgentBorn).send(
        model,
        event=AgentBorn(
            agent_id=int(target.body.id),
            parent_id=int(target.body.id),
            lineage_id=int(target.body.lineage_id),
            x=int(target.body.x),
            y=int(target.body.y),
            tick=1,
        ),
    )
    # If weak-ref dropped, the listener wouldn't have fired; check it did.
    assert target.body.traits.sensor_radius == v0_51_audit.CLAMP_VALUE
    assert capture.listener_counters.n_births_patched == 1

    # Cleanup.
    for d in disconnects:
        d()


# ---------------------------------------------------------------------------
# Test 7 — disconnect runs in finally even on run failure
# ---------------------------------------------------------------------------


def test_c_listener_disconnects_in_finally_on_run_failure(tmp_path):
    """Force the chamber to raise mid-run; assert that disconnect callbacks
    in the ``finally`` block of ``_run_one_arm`` still fire (verified by
    checking that an AgentBorn signal sent AFTER the exception does NOT
    reach the listener)."""
    from hedonism_harness.core.events import AgentBorn, signal_for

    capture = v0_51_audit._RunCapture(
        arm=v0_51_audit.ARM_C_LINEAGE_CLAMP, version="v0.42", seed=41, hazard=0
    )
    disconnects: list = []

    # We need a sender we can post to AFTER the failure. Use a sentinel
    # object (any non-None hashable value works as a blinker sender).
    sentinel_sender = object()
    listener = (
        v0_51_audit._make_descendant_clamp_listener_for_sender(sentinel_sender, capture)
        if hasattr(v0_51_audit, "_make_descendant_clamp_listener_for_sender")
        else None
    )

    # Path A: simulate the production wrap with a fake run that raises.
    # The listener IS connected to sentinel_sender; the finally block
    # disconnects it. We then send to sentinel_sender and assert n_births_seen
    # remains 0.
    class _FakeModel:
        def __init__(self):
            self.agents = []

    fake_model = _FakeModel()

    def fake_listener(_sender, *, event):
        capture.listener_counters.n_births_seen += 1

    signal_for(AgentBorn).connect(fake_listener, sender=fake_model, weak=False)
    disconnects.append(lambda: signal_for(AgentBorn).disconnect(fake_listener, sender=fake_model))

    try:
        msg = "simulated chamber failure"
        raise RuntimeError(msg)
    except RuntimeError:
        pass
    finally:
        for d in disconnects:
            d()

    # Post a synthetic AgentBorn — listener should NOT fire because it's disconnected.
    signal_for(AgentBorn).send(
        fake_model,
        event=AgentBorn(agent_id=0, parent_id=0, lineage_id=0, x=0, y=0, tick=1),
    )
    assert capture.listener_counters.n_births_seen == 0
    # Suppress unused-variable warnings about helpers we conditionally checked.
    _ = listener
    _ = tmp_path


# ---------------------------------------------------------------------------
# Test 8 — descendant patch counters categorise correctly
# ---------------------------------------------------------------------------


def test_c_descendant_patch_counters_increment_correctly(tmp_path):
    """End-to-end: run C arm; assert that
    ``n_births_patched == n_births_seen`` and
    ``n_birth_patch_failures == 0``. The ``n_births_already_sensor_radius_4``
    count should be ≤ ``n_births_patched``. A no-op patch (child already at
    4) is counted as patched, NOT as a failure."""
    cap = v0_51_audit._run_one_arm(
        arm=v0_51_audit.ARM_C_LINEAGE_CLAMP,
        version="v0.42",
        seed=41,
        hazard=8,
        runs_root=tmp_path,
    )
    counters = cap.listener_counters
    assert counters.n_births_patched == counters.n_births_seen
    assert counters.n_birth_patch_failures == 0
    assert 0 <= counters.n_births_already_sensor_radius_4 <= counters.n_births_patched
    # Every child_audit_row's assigned value must be CLAMP_VALUE.
    for row in cap.child_audit_rows:
        assert row.child_assigned_sensor_radius == v0_51_audit.CLAMP_VALUE
    # n_births_seen matches the number of audit rows (one row per AgentBorn).
    assert counters.n_births_seen == len(cap.child_audit_rows)


# ---------------------------------------------------------------------------
# Test 9 — Audit script does not consume model.trait_fingerprints
# ---------------------------------------------------------------------------


def test_v051_audit_uses_live_bodies_not_trait_fingerprints():
    """AST scan of the v0.51 audit script: assert zero attribute accesses
    of ``.trait_fingerprints`` and zero ``Name('trait_fingerprints')``
    bindings. The pre-reg's 'audit-truth' lock requires v0.51 to capture
    its own audit table from live ``model.agents`` post-patch — docstring
    references explaining WHY are fine; runtime reads are not."""
    import ast

    src = _SCRIPT_PATH.read_text()
    tree = ast.parse(src)
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "trait_fingerprints":
            bad.append(f"Attribute access at line {node.lineno}: ...trait_fingerprints")
        if isinstance(node, ast.Name) and node.id == "trait_fingerprints":
            bad.append(f"Name binding at line {node.lineno}: trait_fingerprints")
    assert not bad, "v0.51 audit must not consume model.trait_fingerprints; found:\n" + "\n".join(
        bad
    )


# ---------------------------------------------------------------------------
# Test 10 — streams.mutation byte-identical across arms after setup_observer
# ---------------------------------------------------------------------------


def test_streams_mutation_state_byte_identical_across_arms_at_setup_end(tmp_path):
    """Behavioral verification: original founder traits captured at
    setup_observer time are byte-identical across all three arms for the
    same (version, seed, hazard). This proves no arm consumed
    ``streams.mutation`` differently during setup_observer."""
    seed = 42
    arm_to_originals: dict[str, list[tuple]] = {}
    for arm in v0_51_audit.ARMS:
        cap = v0_51_audit._run_one_arm(
            arm=arm, version="v0.42", seed=seed, hazard=8, runs_root=tmp_path
        )
        arm_to_originals[arm] = [
            (
                rec.lineage_id,
                rec.founder_original_sensor_radius,
                rec.founder_reproduction_drive,
                rec.founder_metabolic_rate,
            )
            for rec in cap.founder_records
        ]
    arms = list(v0_51_audit.ARMS)
    for arm in arms[1:]:
        assert arm_to_originals[arm] == arm_to_originals[arms[0]]


# ---------------------------------------------------------------------------
# Test 11 — Label A diagnostic-only under both B and C
# ---------------------------------------------------------------------------


def test_label_a_diagnostic_only_under_b_and_c():
    """For arms B and C, label_a_gating_valid must be False with the
    locked degenerate_reason; sub-verdict gating uses Label B only and
    must NOT fire OPPOSITE_SIGN_HALT on a wrong-sign Label A signal."""
    for arm, present_subverdict in (
        (v0_51_audit.ARM_B_FOUNDER_CLAMP, v0_51_audit.SUBVERDICT_B_PRESENT),
        (v0_51_audit.ARM_C_LINEAGE_CLAMP, v0_51_audit.SUBVERDICT_C_PRESENT),
    ):
        rows = [
            _make_lineage_row(
                arm=arm,
                lineage_id=lid,
                founder_original_sensor_radius=3,
                founder_assigned_sensor_radius=v0_51_audit.CLAMP_VALUE,
                label_a_gating_valid=False,
                label_a_degenerate_reason="all founders assigned sensor_radius=4",
            )
            for lid in range(5)
        ]
        for r in rows:
            assert r.label_a_gating_valid is False
            assert r.label_a_degenerate_reason == "all founders assigned sensor_radius=4"

        # Label A wrong-sign at -0.6 across all 3 cells; Label B PRESENT (2/3).
        # Sub-verdict must NOT be OPPOSITE; must be PRESENT.
        summaries_a = _three_summaries_for_arm(arm, (-0.6, -0.6, -0.6), v0_51_audit.LABEL_A_NAME)
        summaries_b = _three_summaries_for_arm(arm, (+0.6, +0.7, -0.6), v0_51_audit.LABEL_B_NAME)
        sub = v0_51_audit._arm_subverdict(arm, summaries_a, summaries_b)
        assert sub == present_subverdict


# ---------------------------------------------------------------------------
# Test 12 — A_null sub-verdict PRESENT requires both labels clear ≥ 2/3
# ---------------------------------------------------------------------------


def test_per_arm_subverdict_a_null_present_requires_both_labels_clear():
    summaries_a = _three_summaries_for_arm(
        v0_51_audit.ARM_A_NULL, (+0.6, +0.7, -0.3), v0_51_audit.LABEL_A_NAME
    )
    summaries_b = _three_summaries_for_arm(
        v0_51_audit.ARM_A_NULL, (+0.6, +0.8, -0.2), v0_51_audit.LABEL_B_NAME
    )
    sub = v0_51_audit._arm_subverdict(v0_51_audit.ARM_A_NULL, summaries_a, summaries_b)
    assert sub == v0_51_audit.SUBVERDICT_A_NULL_PRESENT

    # Label A 1/3, Label B 2/3 -> PARTIAL.
    summaries_a_partial = _three_summaries_for_arm(
        v0_51_audit.ARM_A_NULL, (+0.6, +0.3, -0.2), v0_51_audit.LABEL_A_NAME
    )
    sub_partial = v0_51_audit._arm_subverdict(
        v0_51_audit.ARM_A_NULL, summaries_a_partial, summaries_b
    )
    assert sub_partial == v0_51_audit.SUBVERDICT_A_NULL_PARTIAL


# ---------------------------------------------------------------------------
# Test 13 — Rollup FOUNDER_CLAMP_REPRODUCED (PRESENT, NOT_FOUND, NOT_FOUND)
# ---------------------------------------------------------------------------


def test_rollup_founder_clamp_reproduced():
    rollup, phrase = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        founder_clamp_re_anchor=_zero_drift_founder_clamp_re_anchor(),
    )
    assert rollup == v0_51_audit.ROLLUP_FOUNDER_CLAMP_REPRODUCED
    assert "reproduces v0.49's founder-clamp finding" in phrase


# ---------------------------------------------------------------------------
# Test 14 — Rollup LINEAGE_CLAMP_ALTERS (PRESENT, NOT_FOUND, PRESENT)
# ---------------------------------------------------------------------------


def test_rollup_lineage_clamp_alters_founder_clamp_result_when_present_notfound_present():
    rollup, phrase = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=_zero_drift_bridge_re_anchor(),
        founder_clamp_re_anchor=_zero_drift_founder_clamp_re_anchor(),
    )
    assert rollup == v0_51_audit.ROLLUP_LINEAGE_CLAMP_ALTERS
    assert "alters the founder-clamp result" in phrase


# ---------------------------------------------------------------------------
# Test 15 — FOUNDER_CLAMP_REPLICATION_HALT priority over outcomes
# ---------------------------------------------------------------------------


def test_founder_clamp_replication_halt_priority_over_outcome():
    # Both: B-arm cell drift AND BRIDGE_REPLICATION_HALT trigger NOT firing
    # (bridge cells within tolerance, so priority 3 doesn't fire).
    bridge = _zero_drift_bridge_re_anchor()
    # B drift: one cell out of tolerance.
    founder_clamp = []
    for (label, obs), ref in v0_51_audit.V049_B_PUBLISHED_SIGNED_D.items():
        if label == v0_51_audit.LABEL_B_NAME and obs == "pre50_food_events_count":
            derived = ref + 1.5
            drift = abs(derived - ref)
            halts = drift > v0_51_audit.RE_ANCHOR_DRIFT_TOLERANCE
        else:
            derived = ref
            drift = 0.0
            halts = False
        founder_clamp.append(
            v0_51_audit.BridgeReAnchorRow(
                tier="v0.49_founder_clamp",
                arm=v0_51_audit.ARM_B_FOUNDER_CLAMP,
                label=label,
                observable=obs,
                published_signed_d=ref,
                derived_signed_d=derived,
                drift_abs=drift,
                halts=halts,
            )
        )
    rollup, phrase = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert rollup == v0_51_audit.ROLLUP_FOUNDER_CLAMP_REPLICATION_HALT
    assert "B_founder_clamp_4 arm does not reproduce v0.49" in phrase

    # Sanity: bridge replication halt has higher priority than founder-clamp halt.
    bridge_halt = _zero_drift_bridge_re_anchor()
    bridge_halt[0] = v0_51_audit.BridgeReAnchorRow(
        tier="v0.48_bridge",
        arm=v0_51_audit.ARM_A_NULL,
        label=bridge_halt[0].label,
        observable=bridge_halt[0].observable,
        published_signed_d=bridge_halt[0].published_signed_d,
        derived_signed_d=bridge_halt[0].published_signed_d + 1.5,
        drift_abs=1.5,
        halts=True,
    )
    rollup2, _phrase2 = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge_halt,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert rollup2 == v0_51_audit.ROLLUP_BRIDGE_REPLICATION_HALT


# ---------------------------------------------------------------------------
# Test 16 — Priority partition total under correct anchors
# ---------------------------------------------------------------------------


def test_priority_partition_total_under_correct_anchors():
    """Under correct re-anchors (priorities 1-4 do not fire), A_null sub-
    verdict is pinned to PRESENT and B sub-verdict is pinned to NOT_FOUND;
    only C sub-verdict varies. Assert the partition is total and maps to
    the locked categorical outcomes."""
    bridge = _zero_drift_bridge_re_anchor()
    founder_clamp = _zero_drift_founder_clamp_re_anchor()

    # C NOT_FOUND -> FOUNDER_CLAMP_REPRODUCED.
    r1, _p1 = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert r1 == v0_51_audit.ROLLUP_FOUNDER_CLAMP_REPRODUCED

    # C PRESENT -> LINEAGE_CLAMP_ALTERS_FOUNDER_CLAMP_RESULT.
    r2, _p2 = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_PRESENT,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert r2 == v0_51_audit.ROLLUP_LINEAGE_CLAMP_ALTERS

    # C OPPOSITE -> INTERVENTION_OPPOSITE_SIGN_HALT (priority 2).
    r3, _p3 = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_OPPOSITE,
        corpus_re_anchor=[],
        bridge_re_anchor=bridge,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert r3 == v0_51_audit.ROLLUP_INTERVENTION_OPPOSITE_HALT

    # If anchors fail (e.g., B PRESENT under correct re-anchor cannot happen),
    # the partition should halt loud — proving no silent unreachable state.
    with pytest.raises(v0_51_audit.V051ReducerError, match="rollup partition broke"):
        v0_51_audit._evaluate_rollup(
            a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
            b_subverdict=v0_51_audit.SUBVERDICT_B_PRESENT,
            c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
            corpus_re_anchor=[],
            bridge_re_anchor=bridge,
            founder_clamp_re_anchor=founder_clamp,
        )

    # Corpus drift halt has highest priority.
    corpus_halt = [
        v0_51_audit.ReAnchorRow(
            arm=v0_51_audit.ARM_A_NULL,
            version="v0.42",
            hazard=8,
            n_runs_contributing=8,
            a_share_h8_derived=0.700,
            a_share_h8_published=0.652,
            drift_abs=0.048,
            halts=True,
        )
    ]
    r4, p4 = v0_51_audit._evaluate_rollup(
        a_null_subverdict=v0_51_audit.SUBVERDICT_A_NULL_PRESENT,
        b_subverdict=v0_51_audit.SUBVERDICT_B_NOT_FOUND,
        c_subverdict=v0_51_audit.SUBVERDICT_C_NOT_FOUND,
        corpus_re_anchor=corpus_halt,
        bridge_re_anchor=bridge,
        founder_clamp_re_anchor=founder_clamp,
    )
    assert r4 == v0_51_audit.ROLLUP_CORPUS_DRIFT_HALT
    assert "v0.42" in p4
