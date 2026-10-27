"""
Master Benchmark Runner for 5G Adaptive Paging Simulation.
Executes all experiments, aggregates metrics, exports CSV/JSON, and generates publication plots.
"""

import os
import json
from typing import Dict, Any, List
from collections import defaultdict
from src.metrics.tracker import MetricsTracker
from src.utils.report_gen import (
    export_results_csv,
    export_results_json,
    generate_markdown_summary,
)
from src.utils.plotting import (
    plot_traffic_regimes,
    plot_pareto_frontier,
    plot_population_scaling,
    plot_latency_budget_sensitivity,
    plot_adaptation_time_series,
)
from experiments.exp1_traffic_regimes import run_experiment_1
from experiments.exp2_population_scale import run_experiment_2
from experiments.exp3_latency_budgets import run_experiment_3
from experiments.exp4_energy_sensitivity import run_experiment_4


def load_config(config_path: str = "config/default_config.json") -> Dict[str, Any]:
    """Load JSON simulation configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_all_benchmarks(
    config_path: str = "config/default_config.json",
    results_dir: str = "results",
    plots_dir: str = "plots",
) -> Dict[str, Any]:
    """
    Execute full experimental suite and generate all artifacts.
    """
    config = load_config(config_path)
    os.makedirs(os.path.join(results_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(results_dir, "summaries"), exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    print("======================================================================")
    print(" 5G ADAPTIVE PAGING FOR ENERGY-EFFICIENT IOT - EXPERIMENT SUITE")
    print("======================================================================")

    # 1. Experiment 1: Traffic Regimes
    exp1_raw = run_experiment_1(config)
    exp1_raw_path = os.path.join(results_dir, "raw", "exp1_traffic_regimes_raw.csv")
    export_results_csv(exp1_raw, exp1_raw_path)

    # Group Exp 1 across seeds and compute aggregate metrics with 95% CIs
    grouped = defaultdict(list)
    for row in exp1_raw:
        key = (row["algorithm"], row["traffic_pattern"])
        grouped[key].append(row)

    exp1_aggregated: List[Dict[str, Any]] = []
    for (algo, pat), runs in grouped.items():
        agg = MetricsTracker.aggregate_multi_seed(runs)
        exp1_aggregated.append(agg)

    exp1_agg_json = os.path.join(results_dir, "summaries", "exp1_aggregated.json")
    exp1_agg_csv = os.path.join(results_dir, "summaries", "exp1_aggregated.csv")
    export_results_json(exp1_aggregated, exp1_agg_json)
    export_results_csv(exp1_aggregated, exp1_agg_csv)

    # Markdown Summary Report
    report_md_path = os.path.join(results_dir, "summaries", "benchmark_report.md")
    generate_markdown_summary(exp1_aggregated, report_md_path)

    # Plots for Exp 1
    plot_traffic_regimes(exp1_aggregated, output_dir=plots_dir)
    plot_pareto_frontier(exp1_aggregated, output_dir=plots_dir)

    # 2. Experiment 2: Population Scaling
    exp2_raw = run_experiment_2(config)
    exp2_raw_path = os.path.join(results_dir, "raw", "exp2_population_scaling_raw.csv")
    export_results_csv(exp2_raw, exp2_raw_path)

    # Aggregate Exp 2 across seeds
    grouped_exp2 = defaultdict(list)
    for row in exp2_raw:
        key = (row["algorithm"], row["num_devices"])
        grouped_exp2[key].append(row)
    exp2_aggregated: List[Dict[str, Any]] = []
    for (algo, pop), runs in grouped_exp2.items():
        agg = MetricsTracker.aggregate_multi_seed(runs)
        agg["num_devices"] = pop
        exp2_aggregated.append(agg)
    plot_population_scaling(exp2_aggregated, output_dir=plots_dir)

    # 3. Experiment 3: Latency Deadline Sensitivity
    exp3_raw = run_experiment_3(config)
    exp3_raw_path = os.path.join(results_dir, "raw", "exp3_latency_budgets_raw.csv")
    export_results_csv(exp3_raw, exp3_raw_path)

    grouped_exp3 = defaultdict(list)
    for row in exp3_raw:
        key = (row["algorithm"], row["deadline_budget_sec"])
        grouped_exp3[key].append(row)
    exp3_aggregated: List[Dict[str, Any]] = []
    for (algo, d_max), runs in grouped_exp3.items():
        agg = MetricsTracker.aggregate_multi_seed(runs)
        agg["deadline_budget_sec"] = d_max
        exp3_aggregated.append(agg)
    plot_latency_budget_sensitivity(exp3_aggregated, output_dir=plots_dir)

    # 4. Experiment 4: Energy Sensitivity & Microscopic Trace
    exp4_raw, time_series = run_experiment_4(config)
    exp4_raw_path = os.path.join(results_dir, "raw", "exp4_energy_sensitivity_raw.csv")
    export_results_csv(exp4_raw, exp4_raw_path)
    plot_adaptation_time_series(time_series, output_dir=plots_dir)

    print("\n======================================================================")
    print(" ALL EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print(" Results saved to:")
    print(f"   - Raw: {results_dir}/raw/")
    print(f"   - Summaries: {results_dir}/summaries/")
    print(f"   - Figures: {plots_dir}/")
    print("======================================================================\n")

    return {
        "exp1_aggregated": exp1_aggregated,
        "exp2_aggregated": exp2_aggregated,
        "exp3_aggregated": exp3_aggregated,
    }


if __name__ == "__main__":
    run_all_benchmarks()

