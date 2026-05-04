"""DataCollector snapshot reporter tests."""

from __future__ import annotations

from hedonism_harness.core.config import WorldConfig
from hedonism_harness.metrics.collectors import (
    SNAPSHOT_TRAIT_NAMES,
    build_default_collector,
)
from hedonism_harness.model import FounderSpec, HHModel
from hedonism_harness.policies.random_policy import RandomPolicy


def test_default_collector_records_population_and_traits() -> None:
    cfg = WorldConfig(seed=42, width=8, height=8, food_density=0.0, hazard_density=0.0)
    model = HHModel(
        cfg,
        founders=[
            FounderSpec(x=2, y=2, policy_factory=RandomPolicy),
            FounderSpec(x=5, y=5, policy_factory=RandomPolicy),
        ],
    )
    collector = build_default_collector()

    # Tick 0 snapshot.
    collector.collect(model)
    model.step()
    collector.collect(model)
    model.step()
    collector.collect(model)

    df = collector.get_model_vars_dataframe()
    assert list(df["population"]) == [2, 2, 2]
    assert all(df["avg_energy"] > 0)
    # Each tracked trait column exists and is non-zero (random_traits draws from
    # a uniform within-range, so the population mean is finite).
    for trait_name in SNAPSHOT_TRAIT_NAMES:
        col = f"avg_trait_{trait_name}"
        assert col in df.columns
        assert df[col].iloc[0] != 0
