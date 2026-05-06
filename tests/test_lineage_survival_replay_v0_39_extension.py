"""v0.35 lineage_survival_replay v0.39 fresh-extension tests.

Validates the thin-wrapper structure that anchors against the FRESH
v0.34 output (not the sealed 96-row file) and writes to a SEPARATE
output dir without modifying v0.34 / v0.35 surface.
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
        / "lineage_survival_replay_v0_39_extension.py"
    )
    spec = importlib.util.spec_from_file_location("lineage_survival_replay_v0_39_extension", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lineage_survival_replay_v0_39_extension"] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_ls():
    path = Path(__file__).resolve().parents[1] / "scripts" / "lineage_survival_replay.py"
    spec = importlib.util.spec_from_file_location("lineage_survival_replay", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lineage_survival_replay"] = mod
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
    assert ext.FRESH_SOURCE_VERSION == "v0.39"
    assert tuple(range(25, 33)) == ext.FRESH_SEEDS
    assert Path("runs/fear-hunger-v0.39-tight_gradient/arms") == ext.FRESH_RUNS_ROOT
    assert Path("runs/lineage-v0.34-fresh/run_summary.csv") == ext.V0_34_FRESH_RUN_SUMMARY
    assert Path("runs/lineage-v0.35-fresh") == ext.OUT_DIR_FRESH


def test_v0_34_anchor_source_is_fresh_not_sealed():
    """Critical: anchor source must point to the v0.39 fresh extension
    output, NOT the sealed 96-row v0.34 output."""
    ext = _load_extension_module()
    assert Path("runs/lineage-v0.34/run_summary.csv") != ext.V0_34_FRESH_RUN_SUMMARY
    assert "fresh" in str(ext.V0_34_FRESH_RUN_SUMMARY)


def test_stream_configs_fresh_shape():
    ext = _load_extension_module()
    assert len(ext.STREAM_CONFIGS_FRESH) == 1
    source_version, runs_root, seeds = ext.STREAM_CONFIGS_FRESH[0]
    assert source_version == "v0.39"
    assert runs_root == ext.FRESH_RUNS_ROOT
    assert seeds == tuple(range(25, 33))


def test_discover_fresh_runs_count():
    ext = _load_extension_module()
    runs = ext.discover_fresh_runs()
    assert len(runs) == 32


def test_discover_fresh_runs_deterministic_order():
    ext = _load_extension_module()
    runs_a = ext.discover_fresh_runs()
    runs_b = ext.discover_fresh_runs()
    assert runs_a == runs_b
    hazards_in_order = [h for _, _, h, _, _ in runs_a]
    expected = [h for h in (0, 4, 8, 12) for _ in range(8)]
    assert hazards_in_order == expected


def test_discover_fresh_runs_source_version_constant():
    ext = _load_extension_module()
    runs = ext.discover_fresh_runs()
    sources = {sv for sv, _, _, _, _ in runs}
    assert sources == {"v0.39"}


def test_extension_does_not_overwrite_v0_35_out_dir():
    ext = _load_extension_module()
    ls = _load_ls()
    assert ext.OUT_DIR_FRESH != ls.OUT_DIR
    assert Path("runs/lineage-v0.35-fresh") == ext.OUT_DIR_FRESH
    assert Path("runs/lineage-v0.35") == ls.OUT_DIR


def test_ls_helpers_present():
    ls = _load_ls()
    assert callable(ls.load_run_agents)
    assert callable(ls.summarise_run_survival)
    assert callable(ls.cross_check_top_lineage_b50_against_v0_34)
    assert callable(ls.aggregate_pruning_summary)
    assert callable(ls.write_outputs)
    assert callable(ls.load_v0_34_anchors)
    assert callable(ls.reassert_b_pool_anchors)


def test_v0_35_b_pool_anchors_unchanged():
    """The reassert_b_pool_anchors call inside main() should not raise
    on the imported lr module."""
    lr = _load_lr()
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}


def test_main_halts_on_run_count_drift(monkeypatch):
    ext = _load_extension_module()

    def _bad_discover():
        return [("v0.39", "transfer-1500-hzd0-influx-1.0", 0, 25, Path("/nonexistent"))]

    monkeypatch.setattr(ext, "discover_fresh_runs", _bad_discover)
    with pytest.raises(ext.lr.LineageReplayError, match="discover_fresh_runs returned"):
        ext.main()


def test_main_halts_on_missing_v0_34_fresh_anchor(tmp_path, monkeypatch):
    """If the fresh v0.34 anchor file doesn't exist, ls.load_v0_34_anchors halts.
    Uses ext.ls.lr because the error is raised inside ls, which has its own
    importlib-loaded lr instance distinct from ext.lr.
    """
    ext = _load_extension_module()

    monkeypatch.setattr(ext, "V0_34_FRESH_RUN_SUMMARY", tmp_path / "missing.csv")
    with pytest.raises(ext.ls.lr.LineageReplayError, match="missing at"):
        ext.main()
