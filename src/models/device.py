"""
IoT Device (User Equipment - UE) model for 5G Paging Simulation.
"""

from typing import Dict, Any, Optional
from .energy import EnergyModel, EnergyState


class IoTDevice:
    """
    Represents a low-power 5G IoT User Equipment (UE) operating in RRC_IDLE / RRC_INACTIVE.
    """

    def __init__(
        self,
        ue_id: int,
        initial_wake_interval: float,
        initial_wakeup_time: float,
        qos_deadline_sec: Optional[float] = None,
    ):
        self.ue_id = ue_id
        self.initial_wake_interval = float(initial_wake_interval)
        self.current_wake_interval = float(initial_wake_interval)
        self.next_wakeup_time = float(initial_wakeup_time)
        self.qos_deadline_sec: Optional[float] = qos_deadline_sec

        # Operational state
        self.state: EnergyState = EnergyState.DEEP_SLEEP
        self.state_start_time: float = 0.0

        # Energy tracking
        self.accumulated_energy_joules: float = 0.0
        self.state_durations: Dict[EnergyState, float] = {
            state: 0.0 for state in EnergyState
        }

        # Wake-up and traffic metrics
        self.consecutive_idle_wakeups: int = 0
        self.total_wakeups: int = 0
        self.idle_wakeups: int = 0
        self.data_wakeups: int = 0
        self.total_packets_received: int = 0

        # Adaptive algorithm state tracking
        self.last_packet_arrival_time: float = -1.0
        self.ewma_inter_arrival: float = initial_wake_interval

    def record_wakeup(self, had_data: bool) -> None:
        """Record device wake-up occurrence."""
        self.total_wakeups += 1
        if had_data:
            self.data_wakeups += 1
            self.consecutive_idle_wakeups = 0
        else:
            self.idle_wakeups += 1
            self.consecutive_idle_wakeups += 1

    def transition_to(
        self, new_state: EnergyState, current_time: float, energy_model: EnergyModel
    ) -> float:
        """
        Transition device to a new state, calculating and recording energy spent in prior state.

        Returns
        -------
        float
            Energy in Joules consumed in the prior state.
        """
        duration = max(0.0, current_time - self.state_start_time)
        delta_energy = energy_model.compute_energy_joules(self.state, duration)

        self.accumulated_energy_joules += delta_energy
        self.state_durations[self.state] += duration

        self.state = new_state
        self.state_start_time = current_time
        return delta_energy

    def finalize_simulation(self, final_time: float, energy_model: EnergyModel) -> None:
        """Complete energy accounting up to the end of the simulation."""
        if final_time > self.state_start_time:
            duration = final_time - self.state_start_time
            delta_energy = energy_model.compute_energy_joules(self.state, duration)
            self.accumulated_energy_joules += delta_energy
            self.state_durations[self.state] += duration
            self.state_start_time = final_time

    def reset(self, initial_wake_interval: float, initial_wakeup_time: float) -> None:
        """Reset internal metrics for a clean simulation run."""
        self.current_wake_interval = float(initial_wake_interval)
        self.next_wakeup_time = float(initial_wakeup_time)
        self.state = EnergyState.DEEP_SLEEP
        self.state_start_time = 0.0
        self.accumulated_energy_joules = 0.0
        self.state_durations = {state: 0.0 for state in EnergyState}
        self.consecutive_idle_wakeups = 0
        self.total_wakeups = 0
        self.idle_wakeups = 0
        self.data_wakeups = 0
        self.total_packets_received = 0
        self.last_packet_arrival_time = -1.0
        self.ewma_inter_arrival = float(initial_wake_interval)

    def to_dict(self) -> Dict[str, Any]:
        """Export device summary statistics."""
        return {
            "ue_id": self.ue_id,
            "accumulated_energy_joules": self.accumulated_energy_joules,
            "total_wakeups": self.total_wakeups,
            "idle_wakeups": self.idle_wakeups,
            "data_wakeups": self.data_wakeups,
            "total_packets_received": self.total_packets_received,
            "current_wake_interval": self.current_wake_interval,
            "qos_deadline_sec": self.qos_deadline_sec,
            "state_durations_sec": {
                state.value: dur for state, dur in self.state_durations.items()
            },
        }

