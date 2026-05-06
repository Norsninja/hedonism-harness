"""v0.29 food_ladder w=0.75 dip reproducibility diagnostic.

Thin caller that re-runs the v0.28 trajectory diagnostic against the
v0.29 events.jsonl artifacts (food_ladder, seeds 9..16). Reuses the
same H5/H6/H7 classifier; the scientific contract is to apply the
**same** classifier to a different seed stream.

After classifying, evaluates the v0.29 outcome partition
(H9 / H10 / H11 / H12 from `docs/experiments/fear_hunger_v0.29.md`)
against the shared `dip_present` predicate.

Pre-reg: [[docs/experiments/fear_hunger_v0.29.md]].
Sweep:   [[scripts/v0.29_sweep.py]] writes the artifacts this driver
         consumes.

Usage:
    uv run python scripts/v0.29_sweep.py
    uv run python scripts/v0.29_diagnostic.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Import the v0.28 diagnostic module directly. The v0.28 driver lives
# at scripts/v0.28_trajectory_diagnostic.py and is not packaged; do a
# spec-based import to avoid hyphen-vs-underscore dotted-path issues.
_V028_PATH = Path(__file__).parent / "v0.28_trajectory_diagnostic.py"
_spec = importlib.util.spec_from_file_location("v028_diagnostic", _V028_PATH)
if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
    msg = f"could not load v0.28 diagnostic module from {_V028_PATH}"
    raise ImportError(msg)
v028 = importlib.util.module_from_spec(_spec)
sys.modules["v028_diagnostic"] = v028
_spec.loader.exec_module(v028)


SEEDS = tuple(range(9, 17))
RUNS_ROOT = Path("runs/fear-hunger-v0.29-food_ladder/arms")
OUT_DIR = Path("runs/fear-hunger-v0.29-food_ladder")
TITLE = "v0.29 food_ladder w=0.75 dip reproducibility (seeds 9..16) — report"
SOURCE = (
    "v0.29 events.jsonl artifacts at "
    "`runs/fear-hunger-v0.29-food_ladder/arms/hzd8-avd0.{50,75,1.00}/"
    "seed-{9..16}/events.jsonl` (24 runs)."
)

# v0.29 dip predicate (pre-reg, both-neighbors strict valley).
DIP_DELTA_MAX = -5  # B(0.75) <= B(neighbor) - 5 against both w=0.5 and w=1.0


def _aggregate_b50(obs: dict, weight: float) -> int:
    return sum(obs[(s, weight)].b50 for s in SEEDS)


def _evaluate_v0_29_partition(
    obs: dict,
    classification: str,
) -> tuple[str, str, str]:
    """Return (outcome_label, hypothesis_name, dip_summary).

    Implements the v0.29 H9 / H10 / H11 / H12 partition over
    ``dip_present`` and the v0.28 classifier verdict.
    """
    b50 = _aggregate_b50(obs, 0.50)
    b75 = _aggregate_b50(obs, 0.75)
    b100 = _aggregate_b50(obs, 1.00)
    delta_vs_50 = b75 - b50
    delta_vs_100 = b75 - b100
    dip_present = delta_vs_50 <= DIP_DELTA_MAX and delta_vs_100 <= DIP_DELTA_MAX
    summary = (
        f"B(0.5)={b50} B(0.75)={b75} B(1.0)={b100}; "
        f"delta(0.75-0.50)={delta_vs_50:+d}; "
        f"delta(0.75-1.00)={delta_vs_100:+d}; "
        f"dip_present={dip_present} (need both deltas <= {DIP_DELTA_MAX})"
    )

    if not dip_present:
        return ("Outcome alpha — sample artefact, no dip", "H9", summary)

    if classification.startswith("TAIL-SEED CRASH") or classification.startswith(
        "ROUTING-LINKED TAIL CRASH"
    ):
        return ("Outcome beta — stochastic seed-concentrated mechanism", "H10", summary)
    if classification.startswith("UNIFORM POPULATION-WIDE DEGRADATION"):
        return ("Outcome gamma — broad uniform regime", "H11", summary)
    if classification.startswith("STATISTICAL NOISE") or classification.startswith(
        "ROUTING-THRESHOLD FLIP"
    ):
        return ("Outcome delta — ambiguous / mixed", "H12", summary)
    # Halt path (operationally contradictory pair fired).
    return (
        "HALT — re-evaluate operational definitions",
        "(none)",
        summary + f" | classifier verdict: {classification}",
    )


def main() -> None:
    config = v028.DiagnosticConfig(
        runs_root=RUNS_ROOT,
        out_dir=OUT_DIR,
        seeds=SEEDS,
        title=TITLE,
        source_description=SOURCE,
    )

    outcome = v028.run_diagnostic(config)

    # Re-load observables for the v0.29 partition evaluation. (run_diagnostic
    # could be extended to return the obs dict, but keeping its surface
    # narrow; reload is < 1s and avoids breaking the v0.28 contract.)
    obs = v028.load_all(config)
    outcome_label, hypothesis, dip_summary = _evaluate_v0_29_partition(obs, outcome.classification)

    print(f"v0.28 classifier verdict: {outcome.classification}")
    print(f"v0.29 outcome:            {outcome_label}  ({hypothesis} fires)")
    print(f"  dip predicate:          {dip_summary}")
    print(f"Diagnostic report written to {outcome.out_path}")
    for r in (outcome.h5, outcome.h6, outcome.h7):
        marker = "FIRES" if r.fired else "does not fire"
        print(f"  {r.name} {marker}: {r.detail}")


if __name__ == "__main__":
    main()
