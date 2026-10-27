"""
Energy Model for 5G IoT Devices (RedCap / NB-IoT / eDRX).

Based on 3GPP TR 38.840 UE power saving specifications.
All values represent estimated modeled energy consumption.
Hardware power values are configurable and represent realistic RF transceivers.
"""

from enum import Enum
from typing import Dict, Any


class EnergyState(Enum):
    """Operational states of the 5G IoT User Equipment (UE)."""
    DEEP_SLEEP = "DEEP_SLEEP"         # Baseband/RF powered off, RTC clock active
    PO_MONITOR = "PO_MONITOR"         # Waking up, RF warmup, PDCCH blind decoding
    ACTIVE_RX = "ACTIVE_RX"           # Receiving PDSCH downlink data & RRC messages
    ACTIVE_TX = "ACTIVE_TX"           # RACH preamble, PUCCH ACK/NACK, uplink response
    INACTIVITY = "INACTIVITY"         # Inactivity timer monitoring PDCCH prior to sleep


class EnergyModel:
    """
    State-based energy calculation model for 5G IoT devices.

    Parameters
    ----------
    p_sleep_mw : float
        Power in deep sleep state (mW). Default: 0.015 mW (15 uW).
    p_listen_mw : float
        Power during Paging Occasion (PO) monitoring (mW). Default: 45.0 mW.
    p_rx_mw : float
        Power during active downlink reception (mW). Default: 110.0 mW.
    p_tx_mw : float
        Power during uplink transmission (RACH/ACK) (mW). Default: 320.0 mW.
    t_listen_sec : float
        Duration of PO monitoring window (seconds). Default: 0.015 s (15 ms).
    t_rx_sec : float
        Duration of downlink packet reception & processing (seconds). Default: 0.060 s (60 ms).
    t_tx_sec : float
        Duration of uplink transmission (RACH, PUCCH) (seconds). Default: 0.040 s (40 ms).
    t_inactivity_sec : float
        Duration of RRC inactivity timer before returning to sleep (seconds). Default: 0.100 s (100 ms).
    battery_voltage_v : float
        Nominal battery voltage (V). Default: 3.0 V.
    battery_capacity_mah : float
        Battery rated capacity (mAh). Default: 1200.0 mAh.
    """

    def __init__(
        self,
        p_sleep_mw: float = 0.015,
        p_listen_mw: float = 45.0,
        p_rx_mw: float = 110.0,
        p_tx_mw: float = 320.0,
        t_listen_sec: float = 0.015,
        t_rx_sec: float = 0.060,
        t_tx_sec: float = 0.040,
        t_inactivity_sec: float = 0.100,
        battery_voltage_v: float = 3.0,
        battery_capacity_mah: float = 1200.0,
    ):
        self.p_sleep_mw = float(p_sleep_mw)
        self.p_listen_mw = float(p_listen_mw)
        self.p_rx_mw = float(p_rx_mw)
        self.p_tx_mw = float(p_tx_mw)

        self.t_listen_sec = float(t_listen_sec)
        self.t_rx_sec = float(t_rx_sec)
        self.t_tx_sec = float(t_tx_sec)
        self.t_inactivity_sec = float(t_inactivity_sec)

        self.battery_voltage_v = float(battery_voltage_v)
        self.battery_capacity_mah = float(battery_capacity_mah)

        # Total battery energy in Joules: E = V * I * t = V * (mAh / 1000) * 3600
        self.battery_total_joules = (
            self.battery_voltage_v * (self.battery_capacity_mah / 1000.0) * 3600.0
        )

    def power_mw_for_state(self, state: EnergyState) -> float:
        """Return power draw in milliwatts for a given state."""
        if state == EnergyState.DEEP_SLEEP:
            return self.p_sleep_mw
        elif state == EnergyState.PO_MONITOR:
            return self.p_listen_mw
        elif state == EnergyState.ACTIVE_RX:
            return self.p_rx_mw
        elif state == EnergyState.ACTIVE_TX:
            return self.p_tx_mw
        elif state == EnergyState.INACTIVITY:
            # During inactivity timer, baseband listens for further PDCCH allocations
            return self.p_listen_mw
        else:
            raise ValueError(f"Unknown EnergyState: {state}")

    def compute_energy_joules(self, state: EnergyState, duration_sec: float) -> float:
        """
        Compute energy consumed in Joules:
        E (Joules) = (P (mW) / 1000) * duration (s).
        """
        power_w = self.power_mw_for_state(state) / 1000.0
        return power_w * max(0.0, duration_sec)

    def estimate_battery_lifetime_years(
        self, total_energy_joules: float, simulation_duration_sec: float
    ) -> float:
        """
        Estimate device operational battery lifetime in years based on average power:
        P_avg (W) = total_energy_joules / simulation_duration_sec
        Lifetime (seconds) = battery_total_joules / P_avg
        Lifetime (years) = Lifetime (seconds) / (3600 * 24 * 365.25)
        """
        if total_energy_joules <= 0.0 or simulation_duration_sec <= 0.0:
            return float("inf")

        avg_power_w = total_energy_joules / simulation_duration_sec
        lifetime_sec = self.battery_total_joules / avg_power_w
        return lifetime_sec / (3600.0 * 24.0 * 365.25)

    def to_dict(self) -> Dict[str, Any]:
        """Export parameters as dictionary."""
        return {
            "p_sleep_mw": self.p_sleep_mw,
            "p_listen_mw": self.p_listen_mw,
            "p_rx_mw": self.p_rx_mw,
            "p_tx_mw": self.p_tx_mw,
            "t_listen_sec": self.t_listen_sec,
            "t_rx_sec": self.t_rx_sec,
            "t_tx_sec": self.t_tx_sec,
            "t_inactivity_sec": self.t_inactivity_sec,
            "battery_voltage_v": self.battery_voltage_v,
            "battery_capacity_mah": self.battery_capacity_mah,
            "battery_total_joules": self.battery_total_joules,
        }

