"""
Metrics collection, statistical evaluation, and confidence interval computation.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from src.models.traffic import Packet
from src.models.device import IoTDevice
from src.core.paging_controller import PagingController
from src.models.energy import EnergyModel


class MetricsTracker:
    """
    Collects, aggregates, and computes statistical metrics with confidence intervals.
    """

    @staticmethod
    def compute_run_metrics(
        delivered_packets: List[Packet],
        devices: Dict[int, IoTDevice],
        paging_controller: PagingController,
        energy_model: EnergyModel,
        simulation_duration_sec: float,
        algorithm_name: str,
        traffic_pattern: str,
        seed: int,
    ) -> Dict[str, Any]:
        """
        Compute full statistical metrics for a single simulation run.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing scalar metrics, percentiles, and confidence intervals.
        """
        # Latency metrics
        if delivered_packets:
            delays = np.array([p.delay_sec for p in delivered_packets])
            mean_delay = float(np.mean(delays))
            median_delay = float(np.median(delays))
            p95_delay = float(np.percentile(delays, 95))
            p99_delay = float(np.percentile(delays, 99))
            deadline_misses = sum(1 for p in delivered_packets if p.deadline_missed)
            deadline_miss_rate_pct = (deadline_misses / len(delivered_packets)) * 100.0
        else:
            mean_delay = 0.0
            median_delay = 0.0
            p95_delay = 0.0
            p99_delay = 0.0
            deadline_misses = 0
            deadline_miss_rate_pct = 0.0

        # Energy and device metrics
        device_energies = np.array([d.accumulated_energy_joules for d in devices.values()])
        mean_energy_j = float(np.mean(device_energies))
        std_energy_j = float(np.std(device_energies, ddof=1)) if len(device_energies) > 1 else 0.0

        # 95% Confidence Interval for energy per device
        if len(device_energies) > 1:
            sem = stats.sem(device_energies)
            ci95_energy = float(sem * stats.t.ppf((1 + 0.95) / 2.0, len(device_energies) - 1))
        else:
            ci95_energy = 0.0

        # Battery lifetime estimates
        lifetimes = np.array([
            energy_model.estimate_battery_lifetime_years(e, simulation_duration_sec)
            for e in device_energies
        ])
        mean_lifetime_years = float(np.mean(lifetimes))
        median_lifetime_years = float(np.median(lifetimes))

        # Wake-up counts
        total_wakeups = sum(d.total_wakeups for d in devices.values())
        idle_wakeups = sum(d.idle_wakeups for d in devices.values())
        data_wakeups = sum(d.data_wakeups for d in devices.values())
        idle_ratio_pct = (idle_wakeups / max(1, total_wakeups)) * 100.0

        # Paging overhead
        total_paging_msgs = paging_controller.total_paging_messages_transmitted
        total_paging_records = paging_controller.total_paging_records_transmitted
        num_delivered = len(delivered_packets)
        paging_overhead = (
            (total_paging_msgs / max(1, num_delivered)) if num_delivered > 0 else 0.0
        )

        return {
            "algorithm": algorithm_name,
            "traffic_pattern": traffic_pattern,
            "seed": seed,
            "simulation_duration_sec": simulation_duration_sec,
            "num_devices": len(devices),
            "packets_delivered": num_delivered,
            "deadline_misses": deadline_misses,
            "deadline_miss_rate_pct": deadline_miss_rate_pct,
            "mean_delay_sec": mean_delay,
            "median_delay_sec": median_delay,
            "p95_delay_sec": p95_delay,
            "p99_delay_sec": p99_delay,
            "mean_energy_joules": mean_energy_j,
            "std_energy_joules": std_energy_j,
            "ci95_energy_joules": ci95_energy,
            "mean_lifetime_years": mean_lifetime_years,
            "median_lifetime_years": median_lifetime_years,
            "total_wakeups": total_wakeups,
            "idle_wakeups": idle_wakeups,
            "data_wakeups": data_wakeups,
            "idle_wakeup_ratio_pct": idle_ratio_pct,
            "total_paging_messages": total_paging_msgs,
            "total_paging_records": total_paging_records,
            "paging_overhead": paging_overhead,
        }

    @staticmethod
    def aggregate_multi_seed(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results across multiple random seeds and compute overall confidence intervals.
        """
        if not runs:
            return {}

        base = runs[0]
        n_seeds = len(runs)

        def get_stat(key: str):
            vals = np.array([r[key] for r in runs if key in r])
            m = float(np.mean(vals))
            s = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
            if len(vals) > 1:
                sem = stats.sem(vals)
                ci = float(sem * stats.t.ppf((1 + 0.95) / 2.0, len(vals) - 1))
            else:
                ci = 0.0
            return m, s, ci

        mean_energy, std_energy, ci_energy = get_stat("mean_energy_joules")
        mean_delay, std_delay, ci_delay = get_stat("mean_delay_sec")
        p95_delay, _, ci_p95 = get_stat("p95_delay_sec")
        miss_rate, _, ci_miss = get_stat("deadline_miss_rate_pct")
        lifetime, _, ci_lifetime = get_stat("mean_lifetime_years")
        paging_msgs, _, _ = get_stat("total_paging_messages")
        paging_ovh, _, ci_ovh = get_stat("paging_overhead")
        idle_ratio, _, _ = get_stat("idle_wakeup_ratio_pct")

        return {
            "algorithm": base["algorithm"],
            "traffic_pattern": base["traffic_pattern"],
            "num_devices": base["num_devices"],
            "seeds_evaluated": n_seeds,
            "mean_energy_joules": mean_energy,
            "ci95_energy_joules": ci_energy,
            "mean_delay_sec": mean_delay,
            "ci95_delay_sec": ci_delay,
            "p95_delay_sec": p95_delay,
            "ci95_p95_delay_sec": ci_p95,
            "deadline_miss_rate_pct": miss_rate,
            "ci95_deadline_miss_rate_pct": ci_miss,
            "mean_lifetime_years": lifetime,
            "ci95_lifetime_years": ci_lifetime,
            "total_paging_messages": paging_msgs,
            "paging_overhead": paging_ovh,
            "ci95_paging_overhead": ci_ovh,
            "idle_wakeup_ratio_pct": idle_ratio,
        }

