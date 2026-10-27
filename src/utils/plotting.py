"""
Publication-quality plotting module for 5G Paging Simulation.
Generates multi-panel comparison figures in high-resolution PNG and PDF formats.
"""

import os
from typing import List, Dict, Any
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt


def set_plot_style():
    """Configure matplotlib rcParams for IEEE/ACM publication aesthetics."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 13,
        "lines.linewidth": 1.8,
        "lines.markersize": 6,
        "grid.linestyle": "--",
        "grid.alpha": 0.5,
        "axes.grid": True,
    })


def plot_traffic_regimes(
    summary_data: List[Dict[str, Any]], output_dir: str = "plots"
) -> str:
    """
    Generate 4-panel comparison figure across traffic patterns:
    - Mean Energy per Device (J)
    - P95 Delivery Delay (s)
    - Deadline Miss Rate (%)
    - Battery Lifetime (Years)
    """
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    fig.suptitle("5G Paging Performance across Traffic Regimes", fontweight="bold")

    # Filter algorithms
    algos = sorted(list(set(d["algorithm"] for d in summary_data)))
    patterns = sorted(list(set(d["traffic_pattern"] for d in summary_data)))

    x = np.arange(len(patterns))
    width = 0.8 / len(algos)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    # 1. Energy per device
    ax = axes[0, 0]
    for idx, algo in enumerate(algos):
        vals = []
        errs = []
        for pat in patterns:
            match = next((d for d in summary_data if d["algorithm"] == algo and d["traffic_pattern"] == pat), None)
            vals.append(match["mean_energy_joules"] if match else 0.0)
            errs.append(match.get("ci95_energy_joules", 0.0) if match else 0.0)
        ax.bar(x + idx * width - 0.4 + width / 2, vals, width, yerr=errs, label=algo, color=colors[idx % len(colors)], capsize=3)
    ax.set_title("(a) Estimated Energy per Device (J)")
    ax.set_ylabel("Energy (Joules)")
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace("_", " ").title() for p in patterns], rotation=15)
    ax.legend(loc="upper right")

    # 2. P95 Delivery Delay
    ax = axes[0, 1]
    for idx, algo in enumerate(algos):
        vals = []
        errs = []
        for pat in patterns:
            match = next((d for d in summary_data if d["algorithm"] == algo and d["traffic_pattern"] == pat), None)
            vals.append(match["p95_delay_sec"] if match else 0.0)
            errs.append(match.get("ci95_p95_delay_sec", 0.0) if match else 0.0)
        ax.bar(x + idx * width - 0.4 + width / 2, vals, width, yerr=errs, label=algo, color=colors[idx % len(colors)], capsize=3)
    ax.set_title("(b) 95th Percentile (P95) Delivery Delay (s)")
    ax.set_ylabel("P95 Delay (seconds)")
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace("_", " ").title() for p in patterns], rotation=15)

    # 3. Deadline Miss Rate
    ax = axes[1, 0]
    for idx, algo in enumerate(algos):
        vals = []
        for pat in patterns:
            match = next((d for d in summary_data if d["algorithm"] == algo and d["traffic_pattern"] == pat), None)
            vals.append(match["deadline_miss_rate_pct"] if match else 0.0)
        ax.bar(x + idx * width - 0.4 + width / 2, vals, width, label=algo, color=colors[idx % len(colors)])
    ax.set_title("(c) Packet Deadline Miss Rate (%)")
    ax.set_ylabel("Miss Rate (%)")
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace("_", " ").title() for p in patterns], rotation=15)

    # 4. Battery Lifetime
    ax = axes[1, 1]
    for idx, algo in enumerate(algos):
        vals = []
        errs = []
        for pat in patterns:
            match = next((d for d in summary_data if d["algorithm"] == algo and d["traffic_pattern"] == pat), None)
            vals.append(match["mean_lifetime_years"] if match else 0.0)
            errs.append(match.get("ci95_lifetime_years", 0.0) if match else 0.0)
        ax.bar(x + idx * width - 0.4 + width / 2, vals, width, yerr=errs, label=algo, color=colors[idx % len(colors)], capsize=3)
    ax.set_title("(d) Estimated Battery Lifetime (Years)")
    ax.set_ylabel("Lifetime (Years)")
    ax.set_xticks(x)
    ax.set_xticklabels([p.replace("_", " ").title() for p in patterns], rotation=15)

    plt.tight_layout()
    out_png = os.path.join(output_dir, "traffic_regimes_comparison.png")
    out_pdf = os.path.join(output_dir, "traffic_regimes_comparison.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    return out_png


def plot_pareto_frontier(
    summary_data: List[Dict[str, Any]], output_dir: str = "plots"
) -> str:
    """
    Generate Energy-Delay Pareto frontier plot.
    """
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    algos = sorted(list(set(d["algorithm"] for d in summary_data)))
    markers = ["o", "s", "^", "D", "v"]
    colors = ["#1f77b4", "#e377c2", "#2ca02c", "#d62728"]

    for idx, algo in enumerate(algos):
        pts = [d for d in summary_data if d["algorithm"] == algo]
        delays = [p["mean_delay_sec"] for p in pts]
        energies = [p["mean_energy_joules"] for p in pts]
        patterns = [p["traffic_pattern"] for p in pts]

        ax.scatter(
            delays,
            energies,
            label=algo,
            s=80,
            marker=markers[idx % len(markers)],
            color=colors[idx % len(colors)],
            edgecolors="black",
            alpha=0.85,
        )
        for i, pat in enumerate(patterns):
            ax.annotate(
                pat.replace("_", " "),
                (delays[i], energies[i]),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=7.5,
                alpha=0.8,
            )

    ax.set_title("Pareto Trade-off: Delivery Delay vs Estimated Energy", fontweight="bold")
    ax.set_xlabel("Mean Delivery Delay (seconds)")
    ax.set_ylabel("Mean Estimated Energy per Device (Joules)")
    ax.legend(loc="upper right")

    plt.tight_layout()
    out_png = os.path.join(output_dir, "tradeoff_energy_delay.png")
    out_pdf = os.path.join(output_dir, "tradeoff_energy_delay.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    return out_png


def plot_population_scaling(
    scaling_data: List[Dict[str, Any]], output_dir: str = "plots"
) -> str:
    """
    Plot scaling curves across device populations (50 to 500 UEs).
    """
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle("Scalability Analysis Across Device Population", fontweight="bold")

    algos = sorted(list(set(d["algorithm"] for d in scaling_data)))
    colors = ["#1f77b4", "#2ca02c", "#d62728"]
    markers = ["o", "s", "^"]

    # 1. Total Paging Messages
    ax = axes[0]
    for idx, algo in enumerate(algos):
        pts = sorted([d for d in scaling_data if d["algorithm"] == algo], key=lambda x: x["num_devices"])
        pops = [p["num_devices"] for p in pts]
        msgs = [p["total_paging_messages"] for p in pts]
        ax.plot(pops, msgs, marker=markers[idx % len(markers)], label=algo, color=colors[idx % len(colors)])
    ax.set_title("(a) Base Station Paging Messages")
    ax.set_xlabel("Device Population (UEs)")
    ax.set_ylabel("Total Paging Messages")
    ax.legend()

    # 2. Paging Overhead
    ax = axes[1]
    for idx, algo in enumerate(algos):
        pts = sorted([d for d in scaling_data if d["algorithm"] == algo], key=lambda x: x["num_devices"])
        pops = [p["num_devices"] for p in pts]
        ovh = [p["paging_overhead"] for p in pts]
        ax.plot(pops, ovh, marker=markers[idx % len(markers)], label=algo, color=colors[idx % len(colors)])
    ax.set_title("(b) Paging Signaling Overhead")
    ax.set_xlabel("Device Population (UEs)")
    ax.set_ylabel("Paging Msgs / Delivered Packet")

    # 3. Energy per Device
    ax = axes[2]
    for idx, algo in enumerate(algos):
        pts = sorted([d for d in scaling_data if d["algorithm"] == algo], key=lambda x: x["num_devices"])
        pops = [p["num_devices"] for p in pts]
        energy = [p["mean_energy_joules"] for p in pts]
        ax.plot(pops, energy, marker=markers[idx % len(markers)], label=algo, color=colors[idx % len(colors)])
    ax.set_title("(c) Mean Estimated Energy per Device")
    ax.set_xlabel("Device Population (UEs)")
    ax.set_ylabel("Energy (Joules)")

    plt.tight_layout()
    out_png = os.path.join(output_dir, "population_scaling.png")
    out_pdf = os.path.join(output_dir, "population_scaling.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    return out_png


def plot_latency_budget_sensitivity(
    sensitivity_data: List[Dict[str, Any]], output_dir: str = "plots"
) -> str:
    """
    Plot sensitivity to QoS latency deadline budgets D_max.
    """
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    fig.suptitle("QoS Latency Budget Sensitivity Analysis", fontweight="bold")

    algos = sorted(list(set(d["algorithm"] for d in sensitivity_data)))
    colors = ["#1f77b4", "#2ca02c", "#d62728"]
    markers = ["o", "s", "^"]

    # 1. P95 Delay vs Budget
    ax = axes[0]
    for idx, algo in enumerate(algos):
        pts = sorted([d for d in sensitivity_data if d["algorithm"] == algo], key=lambda x: x["deadline_budget_sec"])
        budgets = [p["deadline_budget_sec"] for p in pts]
        delays = [p["p95_delay_sec"] for p in pts]
        ax.plot(budgets, delays, marker=markers[idx % len(markers)], label=algo, color=colors[idx % len(colors)])
    # Plot y = x line (deadline boundary)
    if sensitivity_data:
        max_b = max(p["deadline_budget_sec"] for p in sensitivity_data)
        ax.plot([0, max_b], [0, max_b], "k--", alpha=0.5, label="Deadline Limit (y=x)")
    ax.set_title("(a) P95 Delivery Delay vs Latency Budget")
    ax.set_xlabel("Latency Budget D_max (seconds)")
    ax.set_ylabel("P95 Delivery Delay (seconds)")
    ax.legend()

    # 2. Energy vs Budget
    ax = axes[1]
    for idx, algo in enumerate(algos):
        pts = sorted([d for d in sensitivity_data if d["algorithm"] == algo], key=lambda x: x["deadline_budget_sec"])
        budgets = [p["deadline_budget_sec"] for p in pts]
        energy = [p["mean_energy_joules"] for p in pts]
        ax.plot(budgets, energy, marker=markers[idx % len(markers)], label=algo, color=colors[idx % len(colors)])
    ax.set_title("(b) Energy per Device vs Latency Budget")
    ax.set_xlabel("Latency Budget D_max (seconds)")
    ax.set_ylabel("Mean Energy (Joules)")

    plt.tight_layout()
    out_png = os.path.join(output_dir, "latency_budget_sensitivity.png")
    out_pdf = os.path.join(output_dir, "latency_budget_sensitivity.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    return out_png


def plot_adaptation_time_series(
    time_series_data: Dict[str, Any], output_dir: str = "plots"
) -> str:
    """
    Plot time series showing wake-up intervals contracting during bursts and ramping up during idle.
    """
    set_plot_style()
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    timestamps = time_series_data["timestamps"]
    intervals = time_series_data["intervals"]
    packet_times = time_series_data["packet_times"]

    ax.step(timestamps, intervals, where="post", color="#1f77b4", label="Adaptive Interval T_wake(t)", linewidth=2.0)
    if packet_times:
        ax.vlines(
            packet_times,
            ymin=0,
            ymax=max(intervals) * 1.15,
            color="#d62728",
            linestyle=":",
            alpha=0.7,
            label="Downlink Packet Arrival",
        )

    ax.set_title("AdaPaging Dynamic Interval Adaptation over Time", fontweight="bold")
    ax.set_xlabel("Simulation Time (seconds)")
    ax.set_ylabel("Wake-Up Interval (seconds)")
    ax.set_ylim(bottom=0.0, top=max(intervals) * 1.2)
    ax.legend(loc="upper right")

    plt.tight_layout()
    out_png = os.path.join(output_dir, "dynamic_adaptation_trace.png")
    out_pdf = os.path.join(output_dir, "dynamic_adaptation_trace.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    return out_png

