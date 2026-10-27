"""
Experiment 3: Sensitivity to QoS Latency Deadlines.

Evaluates how AdaPaging dynamically caps wake-up intervals based on
application latency requirements (D_max) compared to static DRX cycles.
"""

from typing import List, Dict, Any
from src.models.energy import EnergyModel
from src.models.traffic import TrafficGenerator
from src.core.base_station import BaseStation
from src.algorithms.baseline_drx import BaselinePeriodicDRX
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.metrics.tracker import MetricsTracker


def run_experiment_3(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute Experiment 3 and return latency sensitivity metrics."""
    sim_cfg = config["simulation"]
    energy_cfg = config["energy_model"]
    traffic_cfg = config["traffic"]
    ada_cfg = config["adaptive_paging"]

    duration = float(sim_cfg.get("duration_sec", 300.0))
    population = 80
    seeds = [42, 101, 2024]
    deadlines = [1.5, 3.0, 5.0, 8.0, 12.0, 16.0]
    pattern = "moderate_poisson"

    energy_model = EnergyModel(**energy_cfg)
    raw_results: List[Dict[str, Any]] = []

    print("\n--- Running Experiment 3: QoS Latency Deadline Sensitivity ---")
    for d_max in deadlines:
        print(f"  [QoS Latency Deadline: {d_max}s]")
        for seed in seeds:
            trace = TrafficGenerator.generate_trace(
                pattern_name=pattern,
                config=traffic_cfg,
                num_devices=population,
                duration_sec=duration,
                seed=seed,
                payload_bytes=traffic_cfg.get("payload_bytes", 256),
                override_deadline=d_max,
            )

            # Baseline 2.56s
            drx_algo = BaselinePeriodicDRX(cycle_sec=2.56)
            bs_drx = BaseStation(
                energy_model=energy_model,
                algorithm=drx_algo,
                num_devices=population,
                initial_wake_interval=2.56,
            )
            delivered_drx = bs_drx.run_simulation(traffic_trace=trace, duration_sec=duration)
            res_drx = MetricsTracker.compute_run_metrics(
                delivered_packets=delivered_drx,
                devices=bs_drx.devices,
                paging_controller=bs_drx.paging_controller,
                energy_model=energy_model,
                simulation_duration_sec=duration,
                algorithm_name=drx_algo.get_algorithm_name(),
                traffic_pattern=pattern,
                seed=seed,
            )
            res_drx["deadline_budget_sec"] = d_max
            raw_results.append(res_drx)

            # AdaPaging
            ada_algo = AdaptivePagingAlgorithm(**ada_cfg)
            bs_ada = BaseStation(
                energy_model=energy_model,
                algorithm=ada_algo,
                num_devices=population,
                initial_wake_interval=ada_cfg.get("t_min_sec", 0.64),
            )
            delivered_ada = bs_ada.run_simulation(traffic_trace=trace, duration_sec=duration)
            res_ada = MetricsTracker.compute_run_metrics(
                delivered_packets=delivered_ada,
                devices=bs_ada.devices,
                paging_controller=bs_ada.paging_controller,
                energy_model=energy_model,
                simulation_duration_sec=duration,
                algorithm_name=ada_algo.get_algorithm_name(),
                traffic_pattern=pattern,
                seed=seed,
            )
            res_ada["deadline_budget_sec"] = d_max
            raw_results.append(res_ada)

    print(f"Experiment 3 complete: {len(raw_results)} simulation runs executed.")
    return raw_results

