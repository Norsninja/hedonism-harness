"""v0.34 lineage_replay v0.41 fresh-extension tests.

Validates the thin-wrapper structure that runs v0.34's helpers over
the v0.41-only fresh stream (seeds 33..40) and writes to a SEPARATE
output dir without modifying v0.34's surface or v0.39's extension.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load_extension_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "lineage_replay_v0_41_extension.py"
    spec = importlib.util.spec_from_file_location("lineage_replay_v0_41_extension", path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lineage_replay_v0_41_extension"] = mod
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
    assert Path("runs/fear-hunger-v0.41-tight_gradient/arms") == ext.FRESH_RUNS_ROOT
    assert tuple(range(33, 41)) == ext.FRESH_SEEDS
    assert Path("runs/lineage-v0.34-v0_41-fresh") == ext.OUT_DIR_FRESH


def test_stream_configs_v041_fresh_shape():
    ext = _load_extension_module()
    assert len(ext.STREAM_CONFIGS_V041_FRESH) == 1
    source_version, runs_root, seeds = ext.STREAM_CONFIGS_V041_FRESH[0]
    assert source_version == "v0.41"
    assert runs_root == ext.FRESH_RUNS_ROOT
    assert seeds == tuple(range(33, 41))


def test_stream_configs_v041_distinct_from_prior_streams():
    """Extension's STREAM_CONFIGS_V041_FRESH must NOT include any prior stream."""
    ext = _load_extension_module()
    fresh_versions = {sv for sv, _, _ in ext.STREAM_CONFIGS_V041_FRESH}
    assert fresh_versions == {"v0.41"}
    assert "v0.25" not in fresh_versions
    assert "v0.32" not in fresh_versions
    assert "v0.33" not in fresh_versions
    assert "v0.39" not in fresh_versions


def test_discover_v041_fresh_runs_count():
    ext = _load_extension_module()
    runs = ext.discover_v041_fresh_runs()
    # 4 hazards x 8 seeds = 32
    assert len(runs) == 32


def test_discover_v041_fresh_runs_deterministic_order():
    """hazard-major, seed-minor; identical between calls."""
    ext = _load_extension_module()
    runs_a = ext.discover_v041_fresh_runs()
    runs_b = ext.discover_v041_fresh_runs()
    assert runs_a == runs_b
    hazards_in_order = [h for _, _, h, _, _ in runs_a]
    expected_hazard_seq = [h for h in (0, 4, 8, 12) for _ in range(8)]
    assert hazards_in_order == expected_hazard_seq
    first_eight_seeds = [s for _, _, _, s, _ in runs_a[:8]]
    assert first_eight_seeds == list(range(33, 41))


def test_discover_v041_fresh_runs_source_version_constant():
    ext = _load_extension_module()
    runs = ext.discover_v041_fresh_runs()
    sources = {sv for sv, _, _, _, _ in runs}
    assert sources == {"v0.41"}


def test_discover_v041_fresh_runs_arm_label_format():
    ext = _load_extension_module()
    lr = _load_lr()
    runs = ext.discover_v041_fresh_runs()
    expected_labels = {lr.ARM_LABEL_FMT.format(h) for h in (0, 4, 8, 12)}
    actual_labels = {arm for _, arm, _, _, _ in runs}
    assert actual_labels == expected_labels


def test_v0_34_b_pool_anchors_unchanged():
    """B_POOL_ANCHORS must remain byte-identical at extension entry."""
    lr = _load_lr()
    assert lr.B_POOL_ANCHORS == {4: 312, 8: 321, 12: 312}


def test_lr_helpers_present():
    """v0.34 helpers the extension wraps must still be importable."""
    lr = _load_lr()
    assert callable(lr.process_run)
    assert callable(lr.aggregate_pool)
    assert callable(lr.write_outputs)
    assert callable(lr.discover_runs)
    assert hasattr(lr, "ARM_LABEL_FMT")
    assert hasattr(lr, "HAZARDS")


def test_extension_does_not_overwrite_v0_34_or_v0_39_out_dirs():
    """OUT_DIR_FRESH must point to a different dir than v0.34's or v0.39 extension's."""
    ext = _load_extension_module()
    lr = _load_lr()
    assert ext.OUT_DIR_FRESH != lr.OUT_DIR
    assert Path("runs/lineage-v0.34-v0_41-fresh") == ext.OUT_DIR_FRESH
    assert Path("runs/lineage-v0.34") == lr.OUT_DIR
    assert Path("runs/lineage-v0.34-fresh") != ext.OUT_DIR_FRESH


def test_main_halts_on_run_count_drift(monkeypatch):
    """If discover_v041_fresh_runs returns wrong count, main halts."""
    ext = _load_extension_module()

    def _bad_discover():
        return [("v0.41", "transfer-1500-hzd0-influx-1.0", 0, 33, Path("/nonexistent"))]

    monkeypatch.setattr(ext, "discover_v041_fresh_runs", _bad_discover)
    with pytest.raises(ext.lr.LineageReplayError, match="discover_v041_fresh_runs returned"):
        ext.main()


def test_main_halts_on_missing_corpus(tmp_path, monkeypatch):
    """If v0.41 fresh corpus not on disk, process_run raises LineageReplayError."""
    ext = _load_extension_module()

    monkeypatch.setattr(ext, "FRESH_RUNS_ROOT", tmp_path / "nonexistent")
    monkeypatch.setattr(
        ext,
        "STREAM_CONFIGS_V041_FRESH",
        (("v0.41", tmp_path / "nonexistent", tuple(range(33, 41))),),
    )
    with pytest.raises((ext.lr.LineageReplayError, FileNotFoundError)):
        ext.main()
