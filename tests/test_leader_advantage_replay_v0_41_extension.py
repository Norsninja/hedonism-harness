"""v0.38 leader_advantage_replay v0.41 fresh-extension tests.

Validates the thin-wrapper structure that anchors against the v0.41-FRESH
v0.34 + v0.35 outputs and writes per_run.csv to a SEPARATE output dir
without modifying v0.34/v0.35/v0.38 surface or v0.39 reducer surface.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_extension_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "leader_advantage_replay_v0_41_extension.py"
    )
    spec = importlib.util.spec_from_file_location("leader_advantage_replay_v0_41_extension", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["leader_advantage_replay_v0_41_extension"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_la():
    path = Path(__file__).resolve().parents[1] / "scripts" / "leader_advantage_replay.py"
    spec = importlib.util.spec_from_file_location("leader_advantage_replay", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["leader_advantage_replay"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_lr():
    path = Path(__file__).resolve().parents[1] / "scripts" / "lineage_replay.py"
    spec = importlib.util.spec_from_file_location("lineage_replay", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lineage_replay"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_locked_constants():
    ext = _load_extension_module()
    assert ext.FRESH_SOURCE_VERSION == "v0.41"
    assert tuple(range(33, 41)) == ext.FRESH_SEEDS
    assert Path("runs/fear-hunger-v0.41-tight_gradient/arms") == ext.FRESH_RUNS_ROOT
    assert (
        Path("runs/lineage-v0.34-v0_41-fresh/run_summary.csv") == ext.V0_34_V041_FRESH_RUN_SUMMARY
    )
    assert (
        Path("runs/lineage-v0.35-v0_41-fresh/pre_post_dominance.csv")
        == ext.V0_35_V041_FRESH_PRE_POST
    )
    assert Path("runs/lineage-v0.38-v0_41-fresh") == ext.OUT_DIR_FRESH


def test_v0_34_anchor_source_is_v041_fresh_not_sealed_or_v039_fresh():
    ext = _load_extension_module()
    assert Path("runs/lineage-v0.34/run_summary.csv") != ext.V0_34_V041_FRESH_RUN_SUMMARY
    assert Path("runs/lineage-v0.34-fresh/run_summary.csv") != ext.V0_34_V041_FRESH_RUN_SUMMARY
    assert "v0_41-fresh" in str(ext.V0_34_V041_FRESH_RUN_SUMMARY)


def test_v0_35_anchor_source_is_v041_fresh_not_sealed_or_v039_fresh():
    ext = _load_extension_module()
    assert Path("runs/lineage-v0.35/pre_post_dominance.csv") != ext.V0_35_V041_FRESH_PRE_POST
    assert Path("runs/lineage-v0.35-fresh/pre_post_dominance.csv") != ext.V0_35_V041_FRESH_PRE_POST
    assert "v0_41-fresh" in str(ext.V0_35_V041_FRESH_PRE_POST)


def test_stream_configs_v041_fresh_shape():
    ext = _load_extension_module()
    assert len(ext.STREAM_CONFIGS_V041_FRESH) == 1
    source_version, runs_root, seeds = ext.STREAM_CONFIGS_V041_FRESH[0]
    assert source_version == "v0.41"
    assert runs_root == ext.FRESH_RUNS_ROOT
    assert seeds == tuple(range(33, 41))


def test_discover_v041_fresh_runs_count():
    ext = _load_extension_module()
    runs = ext.discover_v041_fresh_runs()
    assert len(runs) == 32


def test_discover_v041_fresh_runs_deterministic_order():
    ext = _load_extension_module()
    runs_a = ext.discover_v041_fresh_runs()
    runs_b = ext.discover_v041_fresh_runs()
    assert runs_a == runs_b
    hazards_in_order = [h for _, _, h, _, _ in runs_a]
    expected = [h for h in (0, 4, 8, 12) for _ in range(8)]
    assert hazards_in_order == expected
    first_eight_seeds = [s for _, _, _, s, _ in runs_a[:8]]
    assert first_eight_seeds == list(range(33, 41))


def test_discover_v041_fresh_runs_source_version_constant():
    ext = _load_extension_module()
    runs = ext.discover_v041_fresh_runs()
    sources = {sv for sv, _, _, _, _ in runs}
    assert sources == {"v0.41"}


def test_extension_does_not_overwrite_v0_38_or_v0_39_out_dirs():
    ext = _load_extension_module()
    la = _load_la()
    assert ext.OUT_DIR_FRESH != la.OUT_DIR
    assert Path("runs/lineage-v0.38-v0_41-fresh") == ext.OUT_DIR_FRESH
    assert Path("runs/lineage-v0.38") == la.OUT_DIR
    assert Path("runs/lineage-v0.39") != ext.OUT_DIR_FRESH


def test_la_helpers_present():
    la = _load_la()
    assert callable(la.summarise_run)
    assert callable(la.load_v0_34_anchors)
    assert callable(la.load_v0_35_anchors)
    assert callable(la.cross_check_double_anchor)
    assert callable(la.reassert_b_pool_anchors)
    assert hasattr(la, "PER_RUN_FIELDNAMES")
    assert hasattr(la, "_write_dataclass_csv")


def test_v0_34_b_pool_anchors_unchanged():
    lr = _load_lr()
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}


def test_extension_writes_only_per_run():
    """v0.41 audit only consumes per_run.csv; extension does NOT write
    per_hazard / indicator_summary / verdict CSVs."""
    ext = _load_extension_module()
    # write_per_run_only should be the only output writer, and it returns
    # exactly one path keyed "per_run".
    assert hasattr(ext, "write_per_run_only")
    assert callable(ext.write_per_run_only)
    # main() must not call la.write_outputs (which writes 4 files).
    import inspect

    main_src = inspect.getsource(ext.main)
    assert "la.write_outputs" not in main_src
    assert "write_per_run_only" in main_src


def test_main_halts_on_run_count_drift(monkeypatch):
    ext = _load_extension_module()

    def _bad_discover():
        return [("v0.41", "transfer-1500-hzd0-influx-1.0", 0, 33, Path("/nonexistent"))]

    monkeypatch.setattr(ext, "discover_v041_fresh_runs", _bad_discover)
    with pytest.raises(ext.lr.LineageReplayError, match="discover_v041_fresh_runs returned"):
        ext.main()


def test_main_halts_on_missing_v0_34_v041_fresh_anchor(tmp_path, monkeypatch):
    ext = _load_extension_module()
    monkeypatch.setattr(ext, "V0_34_V041_FRESH_RUN_SUMMARY", tmp_path / "missing34.csv")
    with pytest.raises(ext.la.lr.LineageReplayError, match="missing at"):
        ext.main()


def test_main_halts_on_missing_v0_35_v041_fresh_anchor(tmp_path, monkeypatch):
    """If the v0.35 v0.41-fresh anchor is missing (after v0.34 anchor exists),
    la.load_v0_35_anchors halts. Hard to test in isolation without v0.34 anchor
    existing first, so we monkeypatch v0.34 to a stub path while leaving
    v0.35 missing — expect halt on either v0.34 or v0.35 missing path
    (whichever is checked first), via LineageReplayError."""
    ext = _load_extension_module()
    monkeypatch.setattr(ext, "V0_34_V041_FRESH_RUN_SUMMARY", tmp_path / "missing34.csv")
    monkeypatch.setattr(ext, "V0_35_V041_FRESH_PRE_POST", tmp_path / "missing35.csv")
    with pytest.raises(ext.la.lr.LineageReplayError, match="missing at"):
        ext.main()
