#!/usr/bin/env python3
"""
Main entry point for reproducing the entire 5G Adaptive Paging experimental study.

Usage:
    python run_experiments.py [--config config/default_config.json]
"""

import sys
import argparse
from experiments.benchmark_runner import run_all_benchmarks


def main():
    parser = argparse.ArgumentParser(
        description="5G Adaptive Paging for Energy-Efficient IoT Simulation Runner"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/default_config.json",
        help="Path to simulation configuration JSON file (default: config/default_config.json)",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory to save raw and summarized CSV/JSON results (default: results)",
    )
    parser.add_argument(
        "--plots-dir",
        type=str,
        default="plots",
        help="Directory to save generated comparison plots (default: plots)",
    )

    args = parser.parse_args()
    run_all_benchmarks(
        config_path=args.config,
        results_dir=args.results_dir,
        plots_dir=args.plots_dir,
    )


if __name__ == "__main__":
    main()

