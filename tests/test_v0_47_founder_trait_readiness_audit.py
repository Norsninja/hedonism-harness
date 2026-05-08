"""v0.47 founder-trait predictivity for tick-50 readiness — tests (14 locked).

Pre-reg: [[docs/experiments/fear_hunger_v0.47.md]] §"Test list (locked,
per v0.45 7-point review pattern)". Tests numbered to match the
pre-reg's ordering.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

# Load the underscore-named script as a module via importlib.
_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "v0_47_founder_trait_readiness_audit.py"
_spec = importlib.util.spec_from_file_location("v0_47_audit", _SCRIPT_PATH)
assert _spec is not None
assert _spec.loader is not None
v0_47_audit = importlib.util.module_from_spec(_spec)
sys.modules["v0_47_audit"] = v0_47_audit
_spec.loader.exec_module(v0_47_audit)


# ---------------------------------------------------------------------------
# Synthetic _RunCapture / PerLineageRow helpers
# ---------------------------------------------------------------------------


def _empty_capture(*, version: str = "v0.42", seed: int = 41, hazard: int = 8) -> object:
    cap = v0_47_audit._RunCapture(version=version, seed=seed, hazard=hazard)
    cap.energy_threshold = 50.0
    cap.min_age = 10
    return cap


def _founder_traits(rd: float, mr: float, sr: float) -> dict[str, float]:
    return {
        "reproduction_drive": rd,
        "metabolic_rate": mr,
        "sensor_radius": sr,
    }


def _make_lineage_row(
    *,
    version: str = "v0.42",
    seed: int = 41,
    hazard: int = 8,
    lineage_id: int,
    rd: float = 0.0,
    mr: float = 0.0,
    sr: float = 0.0,
    fraction: float = 0.0,
    count: int = 0,
    living: int = 0,
    b50: int = 0,
    is_high_frac: bool = False,
    is_high_count: bool = False,
) -> object:
    return v0_47_audit.PerLineageRow(
        version=version,
        seed=seed,
        hazard=hazard,
        run_id=f"{version}-A_null-hzd{hazard}-seed-{seed}",
        lineage_id=lineage_id,
        founder_reproduction_drive=rd,
        founder_metabolic_rate=mr,
        founder_sensor_radius=sr,
        tick50_above_threshold_fraction=fraction,
        tick50_above_threshold_count=count,
        tick50_living_count=living,
        b50_count=b50,
        is_high_tick50_readiness_fraction_lineage=is_high_frac,
        is_high_tick50_readiness_count_lineage=is_high_count,
    )


def _make_summary(trait: str, sign: int, paired_d: float, label: str = "fraction") -> object:
    """Construct a TraitSummary directly for verdict-evaluation tests."""
    signed = paired_d * sign if not math.isnan(paired_d) else float("nan")
    return v0_47_audit.TraitSummary(
        trait=trait,
        label=label,
        sign=sign,
        n_runs_contributing=64,
        paired_d=paired_d,
        delta_mean=0.0,
        delta_stdev=1.0,
        delta_min=-1.0,
        delta_max=+1.0,
        fires_expected=(not math.isnan(signed)) and signed >= v0_47_audit.COHENS_D_THRESHOLD,
        fires_wrong=(not math.isnan(signed)) and signed <= -v0_47_audit.COHENS_D_THRESHOLD,
    )


# ---------------------------------------------------------------------------
# Test 1 — setup_observer captures founder traits per lineage
# ---------------------------------------------------------------------------


def test_setup_observer_captures_founder_traits_per_lineage(tmp_path):
    """Run_chamber once with v0.47's setup_observer; assert exactly 5 founders
    captured with all three primary trait names present and within
    TraitConfig's declared ranges."""
    cap = v0_47_audit._run_one_a_null_run(version="v0.42", seed=41, hazard=0, runs_root=tmp_path)
    assert len(cap.founder_traits_by_lineage) == v0_47_audit.EXPECTED_FOUNDERS
    assert set(cap.founder_traits_by_lineage) == {0, 1, 2, 3, 4}
    for lid, traits in cap.founder_traits_by_lineage.items():
        assert set(traits) == {"reproduction_drive", "metabolic_rate", "sensor_radius"}, lid
        # reproduction_drive is float in [0, 3] per default TraitConfig.
        assert 0.0 <= traits["reproduction_drive"] <= 3.0, traits
        # metabolic_rate is float; default range is [0.5, 2.0].
        assert 0.5 <= traits["metabolic_rate"] <= 2.0, traits
        # sensor_radius is integer-valued (coerced to float in capture).
        assert traits["sensor_radius"] >= 1.0, traits
        assert traits["sensor_radius"] == int(traits["sensor_radius"]), traits


# ---------------------------------------------------------------------------
# Test 2 — fraction-label argmax with 3-tier tiebreak
# ---------------------------------------------------------------------------


def test_fraction_label_argmax_with_3tier_tiebreak():
    # Tier 1: pure fraction.
    cands = [(0, 0.4, 4), (1, 0.6, 6), (2, 0.5, 5)]
    assert v0_47_audit._select_fraction_label(cands) == 1

    # Tier 2: same fraction; count tiebreaks.
    cands = [(0, 0.5, 3), (1, 0.5, 5), (2, 0.5, 4)]
    assert v0_47_audit._select_fraction_label(cands) == 1

    # Tier 3: same fraction AND count; lowest lineage_id tiebreaks.
    cands = [(2, 0.5, 5), (0, 0.5, 5), (1, 0.5, 5)]
    assert v0_47_audit._select_fraction_label(cands) == 0

    # Empty input returns None (no non-NaN-fraction lineage).
    assert v0_47_audit._select_fraction_label([]) is None


# ---------------------------------------------------------------------------
# Test 3 — count-label tiebreak count -> fraction -> id
# ---------------------------------------------------------------------------


def test_count_label_tiebreak_is_count_then_fraction_then_id():
    # Tier 1: pure count.
    cands = [(0, 5, 0.5), (1, 7, 0.4), (2, 6, 0.6)]
    assert v0_47_audit._select_count_label(cands) == 1

    # Tier 2: same count; fraction tiebreaks.
    cands = [(0, 5, 0.5), (1, 5, 0.7), (2, 5, 0.6)]
    assert v0_47_audit._select_count_label(cands) == 1

    # Tier 3: same count AND fraction; lowest lineage_id tiebreaks.
    cands = [(2, 5, 0.5), (0, 5, 0.5), (1, 5, 0.5)]
    assert v0_47_audit._select_count_label(cands) == 0

    # NaN-fraction loses ties to non-NaN.
    cands = [(0, 5, 0.5), (1, 5, float("nan")), (2, 5, 0.4)]
    assert v0_47_audit._select_count_label(cands) == 0

    # All-zero counts: no comparison possible.
    cands = [(0, 0, float("nan")), (1, 0, float("nan"))]
    assert v0_47_audit._select_count_label(cands) is None


# ---------------------------------------------------------------------------
# Test 4 — verdict driven by fraction label, not count label
# ---------------------------------------------------------------------------


def test_paired_d_uses_fraction_label_for_verdict():
    """Construct fraction-label summaries (2/3 fire) AND count-label summaries
    (all wrong-sign halt). Verdict consults fraction summaries only."""
    fraction_summaries = [
        _make_summary("reproduction_drive", +1, +0.8),  # FIRES (signed +0.8)
        _make_summary("metabolic_rate", -1, -0.7),  # FIRES (signed +0.7)
        _make_summary("sensor_radius", +1, +0.2),  # not fire
    ]
    # Count summaries (irrelevant to verdict; here all wrong-sign):
    _ = [
        _make_summary("reproduction_drive", +1, -0.8, label="count"),
        _make_summary("metabolic_rate", -1, +0.8, label="count"),
        _make_summary("sensor_radius", +1, -0.8, label="count"),
    ]
    assert v0_47_audit._evaluate_verdict(fraction_summaries) == v0_47_audit.VERDICT_PREDICTS


# ---------------------------------------------------------------------------
# Test 5 — metabolic_rate (-) fires when paired_d is sufficiently negative
# ---------------------------------------------------------------------------


def test_metabolic_rate_sign_inversion_fires_correctly():
    """metabolic_rate has expected sign -. paired_d = -0.6 -> signed = +0.6
    >= 0.5 -> fires in expected direction."""
    s = _make_summary("metabolic_rate", -1, -0.6)
    assert s.fires_expected is True
    assert s.fires_wrong is False


# ---------------------------------------------------------------------------
# Test 6 — metabolic_rate wrong-sign halts
# ---------------------------------------------------------------------------


def test_metabolic_rate_wrong_sign_halts():
    """metabolic_rate with paired_d = +0.6 (positive) is opposite to expected
    sign; signed = -0.6 -> wrong-sign halt."""
    s = _make_summary("metabolic_rate", -1, +0.6)
    assert s.fires_expected is False
    assert s.fires_wrong is True


# ---------------------------------------------------------------------------
# Tests 7-10 - verdict structure
# ---------------------------------------------------------------------------


def test_verdict_2_of_3_fires_predicts():
    summaries = [
        _make_summary("reproduction_drive", +1, +0.6),
        _make_summary("metabolic_rate", -1, -0.6),
        _make_summary("sensor_radius", +1, +0.2),
    ]
    assert v0_47_audit._evaluate_verdict(summaries) == v0_47_audit.VERDICT_PREDICTS


def test_verdict_1_of_3_fires_partial():
    summaries = [
        _make_summary("reproduction_drive", +1, +0.6),
        _make_summary("metabolic_rate", -1, -0.2),
        _make_summary("sensor_radius", +1, +0.2),
    ]
    assert v0_47_audit._evaluate_verdict(summaries) == v0_47_audit.VERDICT_PARTIAL


def test_verdict_0_of_3_fires_not_predictive():
    summaries = [
        _make_summary("reproduction_drive", +1, +0.2),
        _make_summary("metabolic_rate", -1, -0.2),
        _make_summary("sensor_radius", +1, +0.3),
    ]
    assert v0_47_audit._evaluate_verdict(summaries) == v0_47_audit.VERDICT_NOT


def test_verdict_wrong_sign_halt_overrides_fires():
    """2 fire in expected direction, 1 wrong-sign -> halt cell wins."""
    summaries = [
        _make_summary("reproduction_drive", +1, +0.6),
        _make_summary("metabolic_rate", -1, +0.6),  # wrong-sign (signed -0.6)
        _make_summary("sensor_radius", +1, +0.6),
    ]
    assert v0_47_audit._evaluate_verdict(summaries) == v0_47_audit.VERDICT_HALT_OPPOSITE


# ---------------------------------------------------------------------------
# Test 11 — re-anchor drift halt
# ---------------------------------------------------------------------------


def test_reanchor_drift_halt():
    """v0.42 published reference is 0.652. Construct synthetic per-lineage
    rows yielding derived a_share_h8 = 0.5 (drift = 0.152)."""
    rows: list = []
    for seed in range(41, 49):
        rows.append(
            _make_lineage_row(
                version="v0.42",
                seed=seed,
                hazard=8,
                lineage_id=0,
                b50=5,
                is_high_count=True,
            )
        )
        rows.append(
            _make_lineage_row(
                version="v0.42",
                seed=seed,
                hazard=8,
                lineage_id=1,
                b50=5,
                is_high_count=False,
            )
        )
    re_anchor = v0_47_audit._check_re_anchor(rows)
    v042 = next(r for r in re_anchor if r.version == "v0.42")
    assert v042.halts is True
    assert v042.drift_abs is not None
    assert v042.drift_abs > v0_47_audit.RE_ANCHOR_DRIFT_TOLERANCE


# ---------------------------------------------------------------------------
# Test 12 — corpus includes modern A_null only
# ---------------------------------------------------------------------------


def test_corpus_includes_modern_a_null_only():
    assert set(v0_47_audit.SEEDS_BY_VERSION) == {"v0.42", "v0.43R", "v0.44", "v0.45"}
    for version, seeds in v0_47_audit.SEEDS_BY_VERSION.items():
        assert len(seeds) == 8, f"{version} should have 8 seeds; got {len(seeds)}"
    for version in v0_47_audit.SEEDS_BY_VERSION:
        for hazard in v0_47_audit.HAZARDS:
            arm = v0_47_audit._select_a_null_arm(version, hazard)
            assert "A_null" in arm.label
            assert arm.intervention_kind == "null"
            assert arm.hazard_damage == hazard


# ---------------------------------------------------------------------------
# Test 13 — fraction/count agreement rate; well-defined gate
# ---------------------------------------------------------------------------


def test_fraction_count_agreement_rate_well_defined():
    """Synthetic capture across 5 runs: 4 well-defined (both labels assigned),
    of which 3 have matching labels. Fifth run has neither label (all zero)
    and is excluded from the well-defined denominator."""
    rows: list = []
    seed_match = [(41, True), (42, True), (43, True), (44, False)]  # 4 well-defined: 3 match
    for seed, match in seed_match:
        rows.append(
            _make_lineage_row(
                version="v0.42",
                seed=seed,
                hazard=8,
                lineage_id=0,
                fraction=0.5,
                count=2,
                is_high_frac=True,
                is_high_count=match,
            )
        )
        rows.append(
            _make_lineage_row(
                version="v0.42",
                seed=seed,
                hazard=8,
                lineage_id=1,
                fraction=0.4,
                count=3,
                is_high_frac=False,
                is_high_count=not match,
            )
        )
    # Fifth run: no label assigned (synthesizing the all-zero case).
    rows.append(
        _make_lineage_row(
            version="v0.42",
            seed=45,
            hazard=8,
            lineage_id=0,
            is_high_frac=False,
            is_high_count=False,
        )
    )
    rows.append(
        _make_lineage_row(
            version="v0.42",
            seed=45,
            hazard=8,
            lineage_id=1,
            is_high_frac=False,
            is_high_count=False,
        )
    )
    agreement = v0_47_audit._compute_agreement(rows)
    assert agreement.n_runs_well_defined == 4
    assert agreement.n_runs_match == 3
    assert agreement.agreement_rate == 0.75


# ---------------------------------------------------------------------------
# Test 14 — descendant traits not consulted
# ---------------------------------------------------------------------------


def test_descendant_traits_not_consulted():
    """v0.47's reducer reads founder traits from setup_observer-time capture
    only. Even if an agent's body.traits diverged post-mutation, the
    aggregator emits the founder value stored in
    capture.founder_traits_by_lineage."""
    cap = _empty_capture()
    # Lineage 0: founder reproduction_drive = 1.0 (locked initial draw).
    cap.founder_traits_by_lineage[0] = _founder_traits(rd=1.0, mr=1.0, sr=1.0)
    cap.lineage_by_agent = {0: 0, 1: 0}  # agent 0 founder, agent 1 descendant
    cap.birth_tick_by_agent = {0: 0, 1: 30}
    # Tick-50 snapshot only contains the descendant; even if some
    # downstream code WERE to read traits from the snapshot, this test
    # would fail. v0.47 stores no traits in _AgentSnapshot; reducer
    # consults founder_traits_by_lineage exclusively.
    cap.tick50_snapshot = [
        v0_47_audit._AgentSnapshot(agent_id=1, lineage_id=0, energy=60.0, age=20),
    ]
    # Add a second lineage so the per-lineage row machinery emits >= 1 row.
    cap.founder_traits_by_lineage[1] = _founder_traits(rd=2.0, mr=0.5, sr=2.0)
    cap.lineage_by_agent[2] = 1
    cap.birth_tick_by_agent[2] = 0
    cap.tick50_snapshot.append(
        v0_47_audit._AgentSnapshot(agent_id=2, lineage_id=1, energy=55.0, age=15)
    )

    rows = v0_47_audit._aggregate_per_lineage(cap)
    by_lineage = {r.lineage_id: r for r in rows}
    assert by_lineage[0].founder_reproduction_drive == 1.0
    assert by_lineage[0].founder_metabolic_rate == 1.0
    assert by_lineage[0].founder_sensor_radius == 1.0
    assert by_lineage[1].founder_reproduction_drive == 2.0
    assert by_lineage[1].founder_metabolic_rate == 0.5
    assert by_lineage[1].founder_sensor_radius == 2.0
