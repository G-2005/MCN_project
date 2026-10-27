"""
Baseline 3GPP Periodic DRX / eDRX Wake-Up Scheduling Algorithm.
"""

from typing import Optional
from .base_algorithm import BasePagingAlgorithm
from src.models.device import IoTDevice
from src.models.traffic import Packet


class BaselinePeriodicDRX(BasePagingAlgorithm):
    """
    Standard 3GPP fixed periodic DRX/eDRX paging mechanism.
    The device wakes up at fixed intervals T_drx regardless of traffic characteristics.
    """

    def __init__(self, cycle_sec: float = 2.56):
        self.cycle_sec = float(cycle_sec)

    def get_algorithm_name(self) -> str:
        return f"Baseline Periodic DRX ({self.cycle_sec:.2f}s)"

    def calculate_next_interval(
        self,
        device: IoTDevice,
        current_time: float,
        had_pending_data: bool,
        packet: Optional[Packet] = None,
    ) -> float:
        # Fixed periodic DRX interval
        return self.cycle_sec

    def on_packet_arrived(
        self, device: IoTDevice, packet: Packet, current_time: float
    ) -> None:
        # Static baseline maintains fixed schedule; no dynamic state adaptation
        pass

    def on_device_wakeup(
        self, device: IoTDevice, had_pending_data: bool, current_time: float
    ) -> None:
        # Device continues periodic cycle
        pass

