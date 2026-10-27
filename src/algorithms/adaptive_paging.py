"""
Adaptive Wake-Up Scheduling Algorithm (AdaPaging) for 5G IoT Devices.

Dynamically adapts wake-up intervals based on traffic inter-arrival estimation (EWMA),
burst detection, latency deadline budgets (QoS), and configurable bounds.
"""

from typing import Optional
from .base_algorithm import BasePagingAlgorithm
from src.models.device import IoTDevice
from src.models.traffic import Packet


class AdaptivePagingAlgorithm(BasePagingAlgorithm):
    """
    AdaPaging: Traffic-Aware, QoS-Bounded Adaptive Wake-Up Scheduling.

    Parameters
    ----------
    t_min_sec : float
        Absolute minimum wake-up interval (seconds), e.g. 0.64s.
    t_max_sec : float
        Absolute maximum allowable wake-up interval (seconds), e.g. 10.24s.
    t_burst_sec : float
        Interval used during active burst traffic regimes (seconds), e.g. 0.64s.
    ewma_alpha : float
        Exponential smoothing factor for inter-arrival estimation in (0, 1].
    qos_beta : float
        QoS safety fraction (interval <= beta * deadline_budget) in (0, 1].
    ramp_up_factor : float
        Multiplicative backoff rate upon idle wake-ups (gamma).
    """

    def __init__(
        self,
        t_min_sec: float = 0.64,
        t_max_sec: float = 10.24,
        t_burst_sec: float = 0.64,
        ewma_alpha: float = 0.35,
        qos_beta: float = 0.75,
        ramp_up_factor: float = 0.35,
    ):
        self.t_min_sec = float(t_min_sec)
        self.t_max_sec = float(t_max_sec)
        self.t_burst_sec = float(t_burst_sec)
        self.ewma_alpha = float(ewma_alpha)
        self.qos_beta = float(qos_beta)
        self.ramp_up_factor = float(ramp_up_factor)

        # Invariant validation
        if self.t_min_sec > self.t_max_sec:
            raise ValueError(
                f"t_min_sec ({self.t_min_sec}) cannot exceed t_max_sec ({self.t_max_sec})"
            )
        if not (0.0 < self.ewma_alpha <= 1.0):
            raise ValueError("ewma_alpha must be in (0, 1]")
        if not (0.0 < self.qos_beta <= 1.0):
            raise ValueError("qos_beta must be in (0, 1]")

    def get_algorithm_name(self) -> str:
        return "AdaPaging (Proposed Adaptive)"

    def get_effective_upper_bound(self, deadline_budget: Optional[float]) -> float:
        """
        Compute QoS-constrained upper bound:
        T_upper = min(T_max, max(T_min, beta * deadline_budget))
        """
        if deadline_budget is not None and deadline_budget > 0.0:
            qos_cap = self.qos_beta * deadline_budget
            upper_bound = min(self.t_max_sec, max(self.t_min_sec, qos_cap))
        else:
            upper_bound = self.t_max_sec
        return upper_bound

    def calculate_next_interval(
        self,
        device: IoTDevice,
        current_time: float,
        had_pending_data: bool,
        packet: Optional[Packet] = None,
    ) -> float:
        """
        Compute next wake-up sleep interval.

        - If packet or pending data is present: collapse interval to burst mode.
        - If idle wake-up: ramp up interval multiplicatively toward T_upper.
        - Bound strictly within [T_min, T_upper].
        """
        deadline_budget = None
        if packet is not None and packet.deadline_budget_sec > 0.0:
            deadline_budget = packet.deadline_budget_sec
        elif device.qos_deadline_sec is not None and device.qos_deadline_sec > 0.0:
            deadline_budget = device.qos_deadline_sec

        upper_bound = self.get_effective_upper_bound(deadline_budget)

        if had_pending_data:
            # Active burst regime: collapse interval
            candidate = max(
                self.t_min_sec,
                min(self.t_burst_sec, device.ewma_inter_arrival * 0.5),
            )
        else:
            # Idle backoff: smoothly scale up interval as silence continues
            candidate = device.current_wake_interval * (1.0 + self.ramp_up_factor)

        # Enforce strict bounds: T_min <= candidate <= T_upper
        next_interval = max(self.t_min_sec, min(upper_bound, candidate))
        return next_interval

    def on_packet_arrived(
        self, device: IoTDevice, packet: Packet, current_time: float
    ) -> None:
        """Update EWMA inter-arrival estimate and record QoS requirement."""
        device.qos_deadline_sec = packet.deadline_budget_sec
        if device.last_packet_arrival_time > 0.0:
            inter_arrival = max(0.001, current_time - device.last_packet_arrival_time)
            device.ewma_inter_arrival = (
                self.ewma_alpha * inter_arrival
                + (1.0 - self.ewma_alpha) * device.ewma_inter_arrival
            )
        device.last_packet_arrival_time = current_time

    def on_device_wakeup(
        self, device: IoTDevice, had_pending_data: bool, current_time: float
    ) -> None:
        """Algorithm hook for wake-up event."""
        pass

