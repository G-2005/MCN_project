"""
Experiment 4: Energy Model Sensitivity and Microscopic Time-Series Trace.

Evaluates performance sensitivity to hardware transceiver power parameters
and captures sample dynamic adaptation time-series.
"""

from typing import List, Dict, Any, Tuple
from src.models.energy import EnergyModel
from src.models.traffic import TrafficGenerator
from src.core.base_station import BaseStation
from src.algorithms.baseline_drx import BaselinePeriodicDRX
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.metrics.tracker import MetricsTracker


def run_experiment_4(
    config: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Execute Experiment 4 and return sensitivity results plus time-series trace."""
    sim_cfg = config["simulation"]
    energy_cfg = config["energy_model"].copy()
    traffic_cfg = config["traffic"]
    ada_cfg = config["adaptive_paging"]

    duration = 200.0
    population = 50
    seed = 42
    pattern = "bursty_mmpp"

    listen_powers = [25.0, 45.0, 75.0]
    sleep_powers = [0.005, 0.015, 0.030]

    sensitivity_results: List[Dict[str, Any]] = []

    print("\n--- Running Experiment 4: Energy Parameter Sensitivity ---")
    trace = TrafficGenerator.generate_trace(
        pattern_name=pattern,
        config=traffic_cfg,
        num_devices=population,
        duration_sec=duration,
        seed=seed,
        payload_bytes=traffic_cfg.get("payload_bytes", 256),
    )

    for p_listen in listen_powers:
        for p_sleep in sleep_powers:
            m_cfg = energy_cfg.copy()
            m_cfg["p_listen_mw"] = p_listen
            m_cfg["p_sleep_mw"] = p_sleep
            model = EnergyModel(**m_cfg)

            # Baseline DRX
            drx = BaselinePeriodicDRX(cycle_sec=2.56)
            bs_drx = BaseStation(
                energy_model=model,
                algorithm=drx,
                num_devices=population,
                initial_wake_interval=2.56,
            )
            del_drx = bs_drx.run_simulation(trace, duration)
            r_drx = MetricsTracker.compute_run_metrics(
                del_drx, bs_drx.devices, bs_drx.paging_controller, model, duration, drx.get_algorithm_name(), pattern, seed
            )
            r_drx["p_listen_mw"] = p_listen
            r_drx["p_sleep_mw"] = p_sleep
            sensitivity_results.append(r_drx)

            # AdaPaging
            ada = AdaptivePagingAlgorithm(**ada_cfg)
            bs_ada = BaseStation(
                energy_model=model,
                algorithm=ada,
                num_devices=population,
                initial_wake_interval=ada_cfg.get("t_min_sec", 0.64),
            )
            del_ada = bs_ada.run_simulation(trace, duration)
            r_ada = MetricsTracker.compute_run_metrics(
                del_ada, bs_ada.devices, bs_ada.paging_controller, model, duration, ada.get_algorithm_name(), pattern, seed
            )
            r_ada["p_listen_mw"] = p_listen
            r_ada["p_sleep_mw"] = p_sleep
            sensitivity_results.append(r_ada)

    # Generate a sample microscopic time-series trace for UE 0 under bursty traffic
    print("  [Capturing Microscopic Time-Series Trace for Representative Device]")
    sample_trace = TrafficGenerator.generate_trace(
        pattern_name="bursty_mmpp",
        config=traffic_cfg,
        num_devices=1,
        duration_sec=120.0,
        seed=42,
    )
    model_default = EnergyModel(**config["energy_model"])
    ada_single = AdaptivePagingAlgorithm(**ada_cfg)
    bs_single = BaseStation(
        energy_model=model_default,
        algorithm=ada_single,
        num_devices=1,
        initial_wake_interval=ada_cfg.get("t_min_sec", 0.64),
    )

    timestamps = [0.0]
    intervals = [ada_cfg.get("t_min_sec", 0.64)]

    # Hook device wakeups to record interval evolution
    original_calc = ada_single.calculate_next_interval

    def logging_calc(device, current_time, had_pending_data, packet=None):
        next_val = original_calc(device, current_time, had_pending_data, packet)
        timestamps.append(current_time)
        intervals.append(next_val)
        return next_val

    ada_single.calculate_next_interval = logging_calc
    bs_single.run_simulation(sample_trace, 120.0)

    time_series_data = {
        "timestamps": timestamps,
        "intervals": intervals,
        "packet_times": [p.arrival_time for p in sample_trace if p.arrival_time <= 120.0],
    }

    return sensitivity_results, time_series_data

