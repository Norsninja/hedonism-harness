"""Named NumPy RNG streams spawned from a master seed.

Per SPEC §27.3, the simulation uses NumPy's ``Generator`` exclusively (no Python
``random``, no Mesa ``model.random``). A master generator is created from the
configured seed; named child streams are spawned for each subsystem so that
adding randomness to one subsystem cannot perturb the sequence consumed by
others. Per-agent RNGs are spawned at birth from the ``mutation`` stream,
giving lineage-reproducible behavior independent of population call order.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

STREAM_NAMES: tuple[str, ...] = (
    "world_gen",
    "mutation",
    "action_noise",
    "hazard_resolution",
    "agent_order",
)


@dataclass(frozen=True)
class RngStreams:
    """Container for the named per-subsystem RNG streams."""

    world_gen: np.random.Generator
    mutation: np.random.Generator
    action_noise: np.random.Generator
    hazard_resolution: np.random.Generator
    agent_order: np.random.Generator


def make_streams(seed: int) -> RngStreams:
    """Build the canonical set of named RNG streams from a master seed."""
    master = np.random.default_rng(seed)
    children = master.spawn(len(STREAM_NAMES))
    return RngStreams(**dict(zip(STREAM_NAMES, children, strict=True)))


def spawn_agent_rng(parent_stream: np.random.Generator) -> np.random.Generator:
    """Spawn a child RNG for a newborn agent from its lineage's parent stream."""
    return parent_stream.spawn(1)[0]
