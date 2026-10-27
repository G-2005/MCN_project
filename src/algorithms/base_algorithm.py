"""
Base class for 5G wake-up and paging scheduling algorithms.
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.models.device import IoTDevice
from src.models.traffic import Packet


class BasePagingAlgorithm(ABC):
    """Abstract interface for paging and wake-up scheduling algorithms."""

    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Return human-readable algorithm name."""
        pass

    @abstractmethod
    def calculate_next_interval(
        self,
        device: IoTDevice,
        current_time: float,
        had_pending_data: bool,
        packet: Optional[Packet] = None,
    ) -> float:
        """Calculate next wake-up sleep interval in seconds."""
        pass

    @abstractmethod
    def on_packet_arrived(
        self, device: IoTDevice, packet: Packet, current_time: float
    ) -> None:
        """Handle new downlink packet arrival event at the paging controller."""
        pass

    @abstractmethod
    def on_device_wakeup(
        self, device: IoTDevice, had_pending_data: bool, current_time: float
    ) -> None:
        """Handle device wake-up occasion event."""
        pass

