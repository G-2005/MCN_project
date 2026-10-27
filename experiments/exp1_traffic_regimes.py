"""
Experiment 1: Evaluation across Diverse IoT Traffic Regimes.

Compares Baseline Periodic DRX (different fixed cycles) vs AdaPaging
across Sparse Poisson, Moderate Poisson, Bursty MMPP, Periodic, and Heavy-Tailed Pareto.
Both approaches process the EXACT same synthetic packet traces per seed.
"""

from typing import List, Dict, Any
from src.models.energy import EnergyModel
from src.models.traffic import TrafficGenerator
from src.core.base_station import BaseStation
from src.algorithms.baseline_drx import BaselinePeriodicDRX
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.metrics.tracker import MetricsTracker


def run_experiment_1(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute Experiment 1 and return list of raw run metrics."""
    sim_cfg = config["simulation"]
    energy_cfg = config["energy_model"]
    traffic_cfg = config["traffic"]
    ada_cfg = config["adaptive_paging"]
    drx_cfg = config["baseline_drx"]

    duration = float(sim_cfg.get("duration_sec", 300.0))
    population = int(sim_cfg.get("default_population", 100))
    seeds = sim_cfg.get("seeds", [42, 101, 2024, 777, 999])

    patterns = [
        "sparse_poisson",
        "moderate_poisson",
        "bursty_mmpp",
        "periodic",
        "heavy_tail_pareto",
    ]

    # DRX baseline cycles to evaluate
    baseline_cycles = [1.28, 2.56, 5.12]
    
    energy_model = EnergyModel(**energy_cfg)
    raw_results: List[Dict[str, Any]] = []

    print("\n--- Running Experiment 1: Traffic Regimes Benchmark ---")
    for pattern in patterns:
        print(f"  [Traffic Regime: {pattern}]")
        for seed in seeds:
            # Generate deterministic trace shared across all evaluated algorithms
            trace = TrafficGenerator.generate_trace(
                pattern_name=pattern,
                config=traffic_cfg,
                num_devices=population,
                duration_sec=duration,
                seed=seed,
                payload_bytes=traffic_cfg.get("payload_bytes", 256),
            )

            # 1. Baseline DRX runs
            for cycle in baseline_cycles:
                algo = BaselinePeriodicDRX(cycle_sec=cycle)
                bs = BaseStation(
                    energy_model=energy_model,
                    algorithm=algo,
                    num_devices=population,
                    initial_wake_interval=cycle,
                )
                delivered = bs.run_simulation(traffic_trace=trace, duration_sec=duration)
                run_metrics = MetricsTracker.compute_run_metrics(
                    delivered_packets=delivered,
                    devices=bs.devices,
                    paging_controller=bs.paging_controller,
                    energy_model=energy_model,
                    simulation_duration_sec=duration,
                    algorithm_name=algo.get_algorithm_name(),
                    traffic_pattern=pattern,
                    seed=seed,
                )
                run_metrics["cycle_sec"] = cycle
                raw_results.append(run_metrics)

            # 2. Proposed AdaPaging run
            ada_algo = AdaptivePagingAlgorithm(**ada_cfg)
            bs_ada = BaseStation(
                energy_model=energy_model,
                algorithm=ada_algo,
                num_devices=population,
                initial_wake_interval=ada_cfg.get("t_min_sec", 0.64),
            )
            delivered_ada = bs_ada.run_simulation(traffic_trace=trace, duration_sec=duration)
            run_metrics_ada = MetricsTracker.compute_run_metrics(
                delivered_packets=delivered_ada,
                devices=bs_ada.devices,
                paging_controller=bs_ada.paging_controller,
                energy_model=energy_model,
                simulation_duration_sec=duration,
                algorithm_name=ada_algo.get_algorithm_name(),
                traffic_pattern=pattern,
                seed=seed,
            )
            run_metrics_ada["cycle_sec"] = "adaptive"
            raw_results.append(run_metrics_ada)

    print(f"Experiment 1 complete: {len(raw_results)} simulation runs executed.")
    return raw_results

