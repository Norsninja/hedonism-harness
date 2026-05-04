"""Tests for the named NumPy RNG stream factory (SPEC §27.3)."""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from hedonism_harness.core.rng import STREAM_NAMES, make_streams, spawn_agent_rng


@pytest.mark.determinism
def test_streams_are_named_consistently() -> None:
    """The dataclass exposes one Generator per name in STREAM_NAMES."""
    streams = make_streams(seed=42)
    for name in STREAM_NAMES:
        assert isinstance(getattr(streams, name), np.random.Generator)


@pytest.mark.determinism
@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_same_seed_produces_identical_stream_output(seed: int) -> None:
    """Two stream sets from the same seed emit byte-identical sequences."""
    a = make_streams(seed)
    b = make_streams(seed)
    for name in STREAM_NAMES:
        np.testing.assert_array_equal(
            getattr(a, name).random(64),
            getattr(b, name).random(64),
        )


@pytest.mark.determinism
def test_named_streams_are_independent() -> None:
    """Drawing from one stream does not advance another's sequence."""
    a = make_streams(seed=7)
    b = make_streams(seed=7)

    # Exhaust 1000 draws on a.world_gen only.
    a.world_gen.random(1000)

    # mutation streams of a and b should still emit identical sequences.
    np.testing.assert_array_equal(a.mutation.random(32), b.mutation.random(32))


@pytest.mark.determinism
def test_spawn_agent_rng_produces_independent_generator() -> None:
    """A spawned agent RNG is a real Generator distinct from its parent."""
    streams = make_streams(seed=99)
    parent_before = streams.mutation.random(8).copy()

    streams_clone = make_streams(seed=99)
    streams_clone.mutation.random(8)  # advance to same point as parent_before draw
    child = spawn_agent_rng(streams_clone.mutation)

    assert isinstance(child, np.random.Generator)
    # Child sequence is independent of further parent draws (sanity).
    child_seq = child.random(8)
    parent_after = streams_clone.mutation.random(8)
    assert not np.array_equal(child_seq, parent_after)
    # parent_before is just used to anchor the sequence — not asserted further.
    assert parent_before.shape == (8,)
