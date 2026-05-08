"""v0.50 preflight: founder trait covariance descriptive (no simulation).

Replicates the model-side founder trait draws under V0_25's TraitConfig
across the modern A_null 64-run corpus (v0.42 / v0.43R / v0.44 / v0.45,
seeds 41..72) and computes correlations among the 13 founder trait fields.

Purpose: before designing v0.50's founder-position intervention, check
whether ``sensor_radius`` is empirically correlated with any other
founder trait in the V0_25 draw distribution. If correlations are weak,
v0.49's "trait covariance" confound is closed cheaply. If strong,
the finding informs v0.50's arm design (joint vs single-trait probe).

This script does NOT step the simulation. It only consumes RNG bytes
in the same order ``HHModel._spawn_founder`` would, so the founder trait
vectors are byte-identical to what v0.42-v0.49's A_null arms produced.

Usage:
    uv run python scripts/v0_50_founder_trait_covariance_preflight.py
    uv run python scripts/v0_50_founder_trait_covariance_preflight.py \
        --out-dir runs/v0.50-preflight
"""

from __future__ import annotations

import argparse
import csv
import statistics
from dataclasses import fields
from pathlib import Path

from hedonism_harness.core.rng import make_streams, spawn_agent_rng
from hedonism_harness.core.traits import TraitConfig, Traits, random_traits

SEEDS_BY_VERSION: dict[str, tuple[int, ...]] = {
    "v0.42": tuple(range(41, 49)),
    "v0.43R": tuple(range(49, 57)),
    "v0.44": tuple(range(57, 65)),
    "v0.45": tuple(range(65, 73)),
}
N_FOUNDERS: int = 5

TRAIT_FIELDS: tuple[str, ...] = tuple(f.name for f in fields(Traits))


def replicate_founder_traits(seed: int) -> list[Traits]:
    """Draw 5 founder Traits in the exact RNG-consumption order HHModel uses.

    Per ``model.py:355-377``, ``_spawn_founder`` calls
    ``random_traits(trait_config, streams.mutation)`` then
    ``spawn_agent_rng(streams.mutation)`` per founder. Replicating both
    calls in order gives byte-identical founder traits to what HHModel
    produces under the V0_25 anchor.
    """
    streams = make_streams(seed)
    trait_cfg = TraitConfig(unbounded_mutation=True)
    out: list[Traits] = []
    for _ in range(N_FOUNDERS):
        t = random_traits(trait_cfg, streams.mutation)
        _ = spawn_agent_rng(streams.mutation)
        out.append(t)
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    """Pearson correlation. Returns NaN on zero variance or n < 2."""
    n = len(xs)
    if n < 2 or len(ys) != n:
        return float("nan")
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    sx2 = sum((xs[i] - mx) ** 2 for i in range(n))
    sy2 = sum((ys[i] - my) ** 2 for i in range(n))
    if sx2 == 0 or sy2 == 0:
        return float("nan")
    return num / (sx2**0.5 * sy2**0.5)


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation via Pearson on ranks (with average ties)."""

    def ranks(vs: list[float]) -> list[float]:
        order = sorted(range(len(vs)), key=lambda i: vs[i])
        rank = [0.0] * len(vs)
        i = 0
        while i < len(vs):
            j = i
            while j + 1 < len(vs) and vs[order[j + 1]] == vs[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1  # 1-based average of tied positions
            for k in range(i, j + 1):
                rank[order[k]] = avg
            i = j + 1
        return rank

    return pearson(ranks(xs), ranks(ys))


def main() -> None:  # noqa: PLR0912, PLR0915 — single-driver descriptive: arg-parse + draw + correlations + matrix + I/O.
    parser = argparse.ArgumentParser(description="v0.50 founder-trait covariance preflight")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/v0.50-preflight"),
        help="Directory for preflight outputs (default: runs/v0.50-preflight).",
    )
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build the full 320-row table: one row per (version, seed, founder_index).
    rows: list[dict[str, object]] = []
    for version, seeds in SEEDS_BY_VERSION.items():
        for seed in seeds:
            traits_list = replicate_founder_traits(seed)
            for idx, t in enumerate(traits_list):
                row: dict[str, object] = {
                    "version": version,
                    "seed": seed,
                    "founder_index": idx,
                }
                for f in TRAIT_FIELDS:
                    row[f] = float(getattr(t, f))
                rows.append(row)

    # Per-trait vectors for correlation.
    by_field: dict[str, list[float]] = {f: [float(r[f]) for r in rows] for f in TRAIT_FIELDS}

    # Sensor_radius vs every other trait (Pearson + Spearman).
    print("=== v0.50 preflight: founder trait covariance ===")
    print(f"Rows (founders): {len(rows)}  ({len(SEEDS_BY_VERSION) * 8} seeds x {N_FOUNDERS})")
    print(f"Trait fields:    {len(TRAIT_FIELDS)}")
    print()
    print("sensor_radius vs other founder traits:")
    print(f"  {'field':<32}  pearson    spearman")
    sr = by_field["sensor_radius"]
    sensor_corrs: list[tuple[str, float, float]] = []
    for f in TRAIT_FIELDS:
        if f == "sensor_radius":
            continue
        p = pearson(sr, by_field[f])
        s = spearman(sr, by_field[f])
        sensor_corrs.append((f, p, s))
        print(f"  {f:<32}  {p:+.4f}    {s:+.4f}")
    print()

    # Highlight correlations |rho| > 0.3.
    flagged = [(f, p, s) for (f, p, s) in sensor_corrs if abs(p) > 0.3 or abs(s) > 0.3]
    if flagged:
        print("FLAGGED (|rho| > 0.3 by either Pearson or Spearman):")
        for f, p, s in flagged:
            print(f"  {f:<32}  pearson={p:+.4f}  spearman={s:+.4f}")
    else:
        print("No correlations |rho| > 0.3 — confound #2 (trait covariance) is closed cheaply.")
    print()

    # Full pairwise matrix (descriptive; not used to fire any verdict).
    print("Full pairwise Pearson matrix:")
    header = ["field", *TRAIT_FIELDS]
    print("  " + "  ".join(f"{h:>10}" for h in header))
    for f1 in TRAIT_FIELDS:
        cells = [f"{f1:>10}"]
        for f2 in TRAIT_FIELDS:
            r = pearson(by_field[f1], by_field[f2]) if f1 != f2 else 1.0
            cells.append(f"{r:+10.4f}")
        print("  " + "  ".join(cells))
    print()

    # Write CSVs.
    rows_path = out_dir / "founder_traits.csv"
    fieldnames = ["version", "seed", "founder_index", *TRAIT_FIELDS]
    with rows_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {rows_path}")

    corr_path = out_dir / "sensor_radius_correlations.csv"
    with corr_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["other_trait", "pearson", "spearman"])
        for field_name, p, s in sensor_corrs:
            writer.writerow([field_name, repr(p), repr(s)])
    print(f"Wrote {corr_path}")


if __name__ == "__main__":
    main()
