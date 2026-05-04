"""Shared pytest configuration and Hypothesis profiles.

Two profiles:
- `dev` (default): fast, low example count, suitable for tight TDD loops.
- `ci`: more examples, longer deadlines, used in CI and nightly runs.

Select via env var: ``HYPOTHESIS_PROFILE=ci pytest``.
"""

from __future__ import annotations

import os

from hypothesis import HealthCheck, settings

settings.register_profile(
    "dev",
    max_examples=25,
    deadline=200,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "ci",
    max_examples=200,
    deadline=1000,
)

settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
