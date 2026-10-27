"""
Report generation utility for benchmark results and comparisons.
"""

import os
import json
from typing import List, Dict, Any
import pandas as pd


def export_results_csv(
    records: List[Dict[str, Any]], filepath: str
) -> None:
    """Save records as CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df = pd.DataFrame(records)
    df.to_csv(filepath, index=False)


def export_results_json(
    records: Any, filepath: str
) -> None:
    """Save records as structured JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def generate_markdown_summary(
    aggregated_results: List[Dict[str, Any]], output_path: str
) -> str:
    """
    Format aggregated experimental comparisons into an academic-grade markdown table.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = [
        "# 5G Adaptive Paging: Quantitative Benchmark Results",
        "",
        "| Traffic Regime | Algorithm | Mean Energy (J) (95% CI) | Mean Delay (s) | P95 Delay (s) | Deadline Miss (%) | Paging Overhead | Est. Battery (Years) |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for row in aggregated_results:
        pat = row["traffic_pattern"].replace("_", " ").title()
        algo = row["algorithm"]
        energy_str = f"{row['mean_energy_joules']:.4f} ± {row.get('ci95_energy_joules', 0.0):.4f}"
        delay_str = f"{row['mean_delay_sec']:.3f} ± {row.get('ci95_delay_sec', 0.0):.3f}"
        p95_str = f"{row['p95_delay_sec']:.3f}"
        miss_str = f"{row['deadline_miss_rate_pct']:.2f}%"
        ovh_str = f"{row['paging_overhead']:.2f}"
        life_str = f"{row['mean_lifetime_years']:.2f} ± {row.get('ci95_lifetime_years', 0.0):.2f}"

        lines.append(
            f"| {pat} | {algo} | {energy_str} | {delay_str} | {p95_str} | {miss_str} | {ovh_str} | {life_str} |"
        )

    lines.extend([
        "",
        "> **Note on Energy Reporting:** All energy metrics and battery life estimates represent modeled values derived from 3GPP TR 38.840 RF/baseband power parameters, not measured physical hardware power consumption.",
        "",
    ])

    report_content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_content

