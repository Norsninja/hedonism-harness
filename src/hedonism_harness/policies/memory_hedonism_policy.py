"""MemoryHedonismPolicy — HedonismPolicy paired with a non-None memory (SPEC §15.4).

Mechanically identical to ``HedonismPolicy``: scoring already reads memory
through the sensor layer (zero contribution when ``ctx.memory is None``,
non-zero when a ``ValenceMemory`` is present). The distinct class exists to
make experiment configurations and metrics labels self-documenting.

The Mesa agent wrapper is responsible for constructing a ``ValenceMemory`` for
agents using this policy and passing it through ``DecisionContext.memory``.
"""

from __future__ import annotations

from hedonism_harness.policies.hedonism_policy import HedonismPolicy


class MemoryHedonismPolicy(HedonismPolicy):
    """HedonismPolicy variant that expects ``DecisionContext.memory`` to be set."""
