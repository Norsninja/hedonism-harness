"""v0.14 speciation analysis — descriptive enumeration of successful lineages.

Reads per-run trait_fingerprints.csv files written by
``experiments.comparison_grid``, joins them with per-run events.jsonl
(for offspring counts and survivor identification), and reports:

  - Per-arm count of agents who produced offspring (offspring_count >= 1).
  - For each successful agent, its full trait vector, lineage_id, and
    parent_id (founder vs descendant).
  - Per-trait min / median / max across successful agents per arm.
  - A simple cluster-by-inspection table over (pleasure_sensitivity,
    fear_sensitivity, risk_tolerance) at low precision.

Per v0.14 pre-reg, formal clustering (k-means) is deferred to v0.15+
when the population of successful lineages warrants it. v0.14 reports
descriptively.

Usage:
  uv run python scripts/v0.14_speciation_analysis.py \
      --runs runs/fear-hunger-v0.14a runs/fear-hunger-v0.14b \
      --output runs/fear-hunger-v0.14-speciation.md
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

# Trait columns we display in the descriptive table. These match the
# fields the comparison driver writes to trait_fingerprints.csv.
DISPLAY_TRAITS: tuple[str, ...] = (
    "pleasure_sensitivity",
    "fear_sensitivity",
    "risk_tolerance",
    "hunger_pain_sensitivity",
    "injury_pain_sensitivity",
    "metabolic_rate",
    "sensor_radius",
)


def _read_fingerprints(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _read_offspring_counts(events_jsonl: Path) -> dict[int, int]:
    """Walk events.jsonl, return {parent_id: offspring_count}."""
    counts: Counter[int] = Counter()
    if not events_jsonl.exists():
        return {}
    with events_jsonl.open() as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") != "AgentBorn":
                continue
            event = row.get("event", {})
            parent_id = event.get("parent_id")
            if parent_id is not None:
                counts[int(parent_id)] += 1
    return dict(counts)


def _gather_arm_results(arm_dir: Path) -> list[dict]:
    """Walk seed-* dirs under one arm, return list of successful-agent rows.

    Each row carries: arm, seed, layout, agent_id, lineage_id, parent_id,
    birth_tick, offspring_count, traits...
    """
    out: list[dict] = []
    for seed_dir in sorted(arm_dir.glob("seed-*")):
        fingerprints = _read_fingerprints(seed_dir / "trait_fingerprints.csv")
        offspring = _read_offspring_counts(seed_dir / "events.jsonl")
        for fp in fingerprints:
            try:
                agent_id = int(fp["agent_id"])
            except (KeyError, ValueError):
                continue
            count = offspring.get(agent_id, 0)
            if count == 0:
                continue
            row = dict(fp)
            row["seed"] = seed_dir.name
            row["offspring_count"] = count
            out.append(row)
    return out


def _format_trait_summary(rows: list[dict]) -> str:
    """Markdown table: per-trait min / median / max across rows."""
    if not rows:
        return "*No successful lineages.*\n"
    out: list[str] = []
    out.append("| trait | n | min | median | max |")
    out.append("|---|---:|---:|---:|---:|")
    for trait in DISPLAY_TRAITS:
        try:
            values = [float(r[trait]) for r in rows if trait in r]
        except ValueError:
            continue
        if not values:
            continue
        out.append(
            f"| {trait} | {len(values)} | {min(values):.3f} |"
            f" {statistics.median(values):.3f} | {max(values):.3f} |"
        )
    return "\n".join(out) + "\n"


def _format_cluster_inspection(rows: list[dict]) -> str:
    """Bin successful agents into a low-precision cluster table.

    Bins (pleasure_sensitivity, fear_sensitivity, risk_tolerance) at
    precision 0.5 and reports counts. Useful for "did this trait corner
    win in N seeds?" reading; not formal clustering.
    """
    if not rows:
        return "*No successful lineages to cluster.*\n"

    def _bin(value: float, step: float = 0.5) -> float:
        return round(value / step) * step

    bins: Counter[tuple[float, float, float]] = Counter()
    for r in rows:
        try:
            ps = _bin(float(r["pleasure_sensitivity"]))
            fs = _bin(float(r["fear_sensitivity"]))
            rt = _bin(float(r["risk_tolerance"]))
        except (KeyError, ValueError):
            continue
        bins[(ps, fs, rt)] += 1

    out: list[str] = []
    out.append(
        "| pleasure_sensitivity (~0.5) | fear_sensitivity (~0.5) | risk_tolerance (~0.5) | count |"
    )
    out.append("|---:|---:|---:|---:|")
    for (ps, fs, rt), n in bins.most_common():
        out.append(f"| {ps:.1f} | {fs:.1f} | {rt:.1f} | {n} |")
    return "\n".join(out) + "\n"


def _format_full_listing(rows: list[dict]) -> str:
    """One row per successful agent with the key trait fields."""
    if not rows:
        return "*No successful lineages.*\n"
    out: list[str] = []
    header_traits = (
        "pleasure_sensitivity",
        "fear_sensitivity",
        "risk_tolerance",
        "metabolic_rate",
        "sensor_radius",
    )
    out.append(
        "| seed | agent_id | lineage_id | parent_id | birth_tick | offspring | "
        + " | ".join(header_traits)
        + " |"
    )
    out.append("|---|---:|---:|---:|---:|---:|" + ":|---".join("" for _ in header_traits) + ":|")
    for r in rows:
        trait_vals = []
        for t in header_traits:
            try:
                trait_vals.append(f"{float(r[t]):.2f}")
            except (KeyError, ValueError):
                trait_vals.append("?")
        parent = r.get("parent_id") or "-"
        out.append(
            f"| {r.get('seed', '?')} | {r.get('agent_id', '?')} | "
            f"{r.get('lineage_id', '?')} | {parent} | "
            f"{r.get('birth_tick', '?')} | {r.get('offspring_count', '?')} | "
            + " | ".join(trait_vals)
            + " |"
        )
    return "\n".join(out) + "\n"


def analyze_run_root(run_root: Path) -> str:
    """Emit a markdown section for one v0.14 run root (one chamber)."""
    chamber = run_root.name
    sections: list[str] = [f"## {chamber}\n"]
    arms_root = run_root / "arms"
    if not arms_root.is_dir():
        sections.append(f"*No arms/ directory under {run_root}.*\n")
        return "\n".join(sections)

    by_arm: dict[str, list[dict]] = defaultdict(list)
    for arm_dir in sorted(arms_root.iterdir()):
        if not arm_dir.is_dir():
            continue
        rows = _gather_arm_results(arm_dir)
        by_arm[arm_dir.name] = rows

    for arm_label, rows in by_arm.items():
        sections.append(f"### {arm_label}\n")
        sections.append(f"successful agents (offspring_count >= 1): {len(rows)}\n")
        sections.append("\n**Per-trait summary**\n")
        sections.append(_format_trait_summary(rows))
        sections.append("\n**Cluster inspection (binned at 0.5)**\n")
        sections.append(_format_cluster_inspection(rows))
        sections.append("\n**Full listing**\n")
        sections.append(_format_full_listing(rows))
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs",
        nargs="+",
        type=Path,
        required=True,
        help="One or more v0.14 batch run roots (e.g. runs/fear-hunger-v0.14a).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Markdown output path.",
    )
    args = parser.parse_args()

    sections: list[str] = [
        "# v0.14 speciation analysis (descriptive)\n",
        "Per-arm enumeration of agents whose offspring_count >= 1, with",
        "trait-vector summaries and a low-precision cluster-by-inspection table.",
        "Per v0.14 pre-reg, formal clustering is deferred until sample size",
        "warrants it; this script is descriptive enumeration only.\n",
    ]
    for run_root in args.runs:
        sections.append(analyze_run_root(run_root))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
