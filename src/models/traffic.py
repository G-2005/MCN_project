"""
Traffic models and packet trace generation for 5G IoT simulation.

Provides deterministic, reproducible synthetic downlink traffic traces.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class Packet:
    """Represents a downlink data packet destined for an IoT device."""
    packet_id: int
    ue_id: int
    arrival_time: float
    payload_bytes: int
    deadline_budget_sec: float
    delivery_deadline: float = 0.0
    delivered: bool = False
    delivery_time: float = -1.0
    delay_sec: float = -1.0
    deadline_missed: bool = False

    def __post_init__(self):
        if self.delivery_deadline <= 0.0:
            self.delivery_deadline = self.arrival_time + self.deadline_budget_sec

    def mark_delivered(self, delivery_time: float):
        """Mark packet as delivered and compute latency metrics."""
        self.delivered = True
        self.delivery_time = delivery_time
        self.delay_sec = max(0.0, delivery_time - self.arrival_time)
        self.deadline_missed = delivery_time > self.delivery_deadline


class TrafficGenerator:
    """
    Generates reproducible synthetic traffic traces for 5G IoT devices.
    """

    @staticmethod
    def generate_trace(
        pattern_name: str,
        config: Dict[str, Any],
        num_devices: int,
        duration_sec: float,
        seed: int,
        payload_bytes: int = 256,
        override_deadline: Optional[float] = None,
    ) -> List[Packet]:
        """
        Generate a globally timestamp-sorted list of downlink packets.

        Parameters
        ----------
        pattern_name : str
            Traffic regime: 'poisson', 'sparse_poisson', 'moderate_poisson',
            'bursty', 'bursty_mmpp', 'periodic', 'pareto', 'heavy_tail_pareto',
            'zero_traffic', 'extreme_burst'.
        config : dict
            Configuration dictionary containing pattern parameters.
        num_devices : int
            Number of simulated IoT devices.
        duration_sec : float
            Simulation time horizon in seconds.
        seed : int
            Random seed for reproducibility.
        payload_bytes : int
            Payload size per packet in bytes.
        override_deadline : float, optional
            If provided, overrides pattern's default deadline budget.

        Returns
        -------
        List[Packet]
            Sorted list of downlink packets.
        """
        rng = np.random.default_rng(seed)
        packets: List[Packet] = []
        packet_counter = 0

        # Resolve pattern parameters
        patterns_cfg = config.get("patterns", {})
        pat_cfg = patterns_cfg.get(pattern_name, {})
        pat_type = pat_cfg.get("type", pattern_name).lower()
        default_deadline = pat_cfg.get("default_deadline_sec", 5.0)
        deadline = override_deadline if override_deadline is not None else default_deadline

        if pat_type in ("zero", "zero_traffic"):
            # Edge case: zero traffic (evaluates background wake-up energy)
            return []

        for ue_id in range(num_devices):
            # Per-device seed derivation for isolated, consistent generation
            dev_seed = int(rng.integers(0, 2**31 - 1))
            dev_rng = np.random.default_rng(dev_seed)

            t = float(dev_rng.uniform(0.1, 2.0))  # initial warm-up offset

            if pat_type in ("poisson", "sparse_poisson", "moderate_poisson"):
                rate = pat_cfg.get("rate_lambda", 0.1)
                while t < duration_sec:
                    # Exponential inter-arrival time
                    inter_arrival = dev_rng.exponential(1.0 / rate)
                    t += inter_arrival
                    if t < duration_sec:
                        packets.append(
                            Packet(
                                packet_id=packet_counter,
                                ue_id=ue_id,
                                arrival_time=float(t),
                                payload_bytes=payload_bytes,
                                deadline_budget_sec=float(deadline),
                            )
                        )
                        packet_counter += 1

            elif pat_type in ("bursty", "bursty_mmpp"):
                # Markov-Modulated Poisson Process (MMPP) / On-Off model
                rate_on = pat_cfg.get("rate_on", 2.5)
                rate_off = pat_cfg.get("rate_off", 0.01)
                p_on_to_off = pat_cfg.get("p_on_to_off", 0.25)
                p_off_to_on = pat_cfg.get("p_off_to_on", 0.05)
                step_interval = pat_cfg.get("step_interval_sec", 1.0)

                state = 1 if dev_rng.random() < 0.2 else 0  # 1 = ON, 0 = OFF

                curr_t = t
                while curr_t < duration_sec:
                    # Transition Markov state
                    if state == 1:
                        if dev_rng.random() < p_on_to_off:
                            state = 0
                    else:
                        if dev_rng.random() < p_off_to_on:
                            state = 1

                    # Generate packets within this time step window
                    window_end = min(duration_sec, curr_t + step_interval)
                    sub_t = curr_t
                    rate = rate_on if state == 1 else rate_off

                    if rate > 0.0:
                        while sub_t < window_end:
                            ia = dev_rng.exponential(1.0 / rate)
                            sub_t += ia
                            if sub_t < window_end:
                                packets.append(
                                    Packet(
                                        packet_id=packet_counter,
                                        ue_id=ue_id,
                                        arrival_time=float(sub_t),
                                        payload_bytes=payload_bytes,
                                        deadline_budget_sec=float(deadline),
                                    )
                                )
                                packet_counter += 1

                    curr_t = window_end

            elif pat_type in ("periodic",):
                base_interval = pat_cfg.get("interval_sec", 15.0)
                jitter_pct = pat_cfg.get("jitter_pct", 0.10)
                while t < duration_sec:
                    jitter = dev_rng.uniform(-jitter_pct, jitter_pct) * base_interval
                    inter_arrival = max(0.1, base_interval + jitter)
                    t += inter_arrival
                    if t < duration_sec:
                        packets.append(
                            Packet(
                                packet_id=packet_counter,
                                ue_id=ue_id,
                                arrival_time=float(t),
                                payload_bytes=payload_bytes,
                                deadline_budget_sec=float(deadline),
                            )
                        )
                        packet_counter += 1

            elif pat_type in ("pareto", "heavy_tail_pareto"):
                alpha = pat_cfg.get("alpha", 1.8)
                scale = pat_cfg.get("scale", 5.0)
                while t < duration_sec:
                    # Pareto distributed inter-arrival times
                    inter_arrival = (dev_rng.pareto(alpha) + 1.0) * scale
                    t += inter_arrival
                    if t < duration_sec:
                        packets.append(
                            Packet(
                                packet_id=packet_counter,
                                ue_id=ue_id,
                                arrival_time=float(t),
                                payload_bytes=payload_bytes,
                                deadline_budget_sec=float(deadline),
                            )
                        )
                        packet_counter += 1

            elif pat_type in ("extreme_burst",):
                # Generates periodic sudden bursts of multiple packets
                burst_size = 8
                burst_interval = 20.0
                while t < duration_sec:
                    for _ in range(burst_size):
                        micro_offset = float(dev_rng.uniform(0.001, 0.050))
                        burst_t = t + micro_offset
                        if burst_t < duration_sec:
                            packets.append(
                                Packet(
                                    packet_id=packet_counter,
                                    ue_id=ue_id,
                                    arrival_time=burst_t,
                                    payload_bytes=payload_bytes,
                                    deadline_budget_sec=float(deadline),
                                )
                            )
                            packet_counter += 1
                    t += burst_interval

            else:
                raise ValueError(f"Unsupported traffic pattern type: '{pat_type}'")

        # Sort all packets strictly by arrival time
        packets.sort(key=lambda p: p.arrival_time)
        # Re-index packet IDs consecutively
        for idx, pkt in enumerate(packets):
            pkt.packet_id = idx

        return packets

