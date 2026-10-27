"""
Experiment 2: Scalability with IoT Device Populations.

Evaluates base station paging messages, overhead, and device energy
as cell device density scales from 50 to 500 devices.
"""

from typing import List, Dict, Any
from src.models.energy import EnergyModel
from src.models.traffic import TrafficGenerator
from src.core.base_station import BaseStation
from src.algorithms.baseline_drx import BaselinePeriodicDRX
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.metrics.tracker import MetricsTracker


def run_experiment_2(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute Experiment 2 and return list of population scaling metrics."""
    sim_cfg = config["simulation"]
    energy_cfg = config["energy_model"]
    traffic_cfg = config["traffic"]
    ada_cfg = config["adaptive_paging"]

    duration = float(sim_cfg.get("duration_sec", 300.0))
    populations = [50, 100, 200, 350, 500]
    seeds = [42, 101, 2024]  # representative seeds
    pattern = "moderate_poisson"

    energy_model = EnergyModel(**energy_cfg)
    raw_results: List[Dict[str, Any]] = []

    print("\n--- Running Experiment 2: Device Population Scalability ---")
    for pop in populations:
        print(f"  [Device Population: {pop} UEs]")
        for seed in seeds:
            trace = TrafficGenerator.generate_trace(
                pattern_name=pattern,
                config=traffic_cfg,
                num_devices=pop,
                duration_sec=duration,
                seed=seed,
                payload_bytes=traffic_cfg.get("payload_bytes", 256),
            )

            # Baseline 2.56s DRX
            drx_algo = BaselinePeriodicDRX(cycle_sec=2.56)
            bs_drx = BaseStation(
                energy_model=energy_model,
                algorithm=drx_algo,
                num_devices=pop,
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
            raw_results.append(res_drx)

            # AdaPaging
            ada_algo = AdaptivePagingAlgorithm(**ada_cfg)
            bs_ada = BaseStation(
                energy_model=energy_model,
                algorithm=ada_algo,
                num_devices=pop,
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
            raw_results.append(res_ada)

    print(f"Experiment 2 complete: {len(raw_results)} simulation runs executed.")
    return raw_results

