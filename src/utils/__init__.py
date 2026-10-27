"""Utilities package: Plotting, reports, and formatting."""
from .plotting import (
    plot_traffic_regimes,
    plot_pareto_frontier,
    plot_population_scaling,
    plot_latency_budget_sensitivity,
    plot_adaptation_time_series,
)
from .report_gen import (
    export_results_csv,
    export_results_json,
    generate_markdown_summary,
)

__all__ = [
    "plot_traffic_regimes",
    "plot_pareto_frontier",
    "plot_population_scaling",
    "plot_latency_budget_sensitivity",
    "plot_adaptation_time_series",
    "export_results_csv",
    "export_results_json",
    "generate_markdown_summary",
]

