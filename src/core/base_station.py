"""
5G Base Station (gNodeB) and Cell Simulation Orchestrator.
"""

from typing import Dict, List, Optional
from src.core.event_engine import SimulationEngine, EventType
from src.core.paging_controller import PagingController
from src.models.device import IoTDevice
from src.models.energy import EnergyModel, EnergyState
from src.models.traffic import Packet
from src.algorithms.base_algorithm import BasePagingAlgorithm


class BaseStation:
    """
    Simulates a 5G gNodeB coordinating with a population of IoT devices.
    """

    def __init__(
        self,
        energy_model: EnergyModel,
        algorithm: BasePagingAlgorithm,
        num_devices: int,
        initial_wake_interval: float = 2.56,
    ):
        self.energy_model = energy_model
        self.algorithm = algorithm
        self.num_devices = num_devices
        self.initial_wake_interval = float(initial_wake_interval)

        self.engine = SimulationEngine()
        self.paging_controller = PagingController()

        # Initialize devices with staggered initial wake-up times to model unsynchronized cells
        self.devices: Dict[int, IoTDevice] = {}
        for ue_id in range(num_devices):
            stagger = (ue_id / max(1, num_devices)) * self.initial_wake_interval
            initial_t = max(0.01, stagger)
            self.devices[ue_id] = IoTDevice(
                ue_id=ue_id,
                initial_wake_interval=self.initial_wake_interval,
                initial_wakeup_time=initial_t,
            )

        self.delivered_packets: List[Packet] = []

    def reset(self) -> None:
        """Reset base station, devices, and event engine."""
        self.engine.reset()
        self.paging_controller.reset()
        self.delivered_packets.clear()

        for ue_id, dev in self.devices.items():
            stagger = (ue_id / max(1, self.num_devices)) * self.initial_wake_interval
            initial_t = max(0.01, stagger)
            dev.reset(self.initial_wake_interval, initial_t)

    def run_simulation(
        self, traffic_trace: List[Packet], duration_sec: float
    ) -> List[Packet]:
        """
        Execute the discrete-event simulation over the given traffic trace.

        Parameters
        ----------
        traffic_trace : List[Packet]
            Sorted list of downlink packets.
        duration_sec : float
            Total simulation time in seconds.

        Returns
        -------
        List[Packet]
            List of delivered packets with latency and deadline metrics.
        """
        self.reset()

        # 1. Schedule all packet arrival events
        for pkt in traffic_trace:
            if pkt.arrival_time < duration_sec:
                self.engine.schedule_event(
                    pkt.arrival_time, EventType.PACKET_ARRIVE, pkt
                )

        # 2. Schedule initial wake-ups for all devices
        for dev in self.devices.values():
            if dev.next_wakeup_time < duration_sec:
                self.engine.schedule_event(
                    dev.next_wakeup_time, EventType.UE_WAKEUP, dev.ue_id
                )

        # 3. Main event processing loop
        while self.engine.has_events():
            event = self.engine.pop_event()
            if event is None:
                break

            current_time, event_type, payload = event
            if current_time > duration_sec:
                break

            if event_type == EventType.PACKET_ARRIVE:
                self._handle_packet_arrive(current_time, payload)

            elif event_type == EventType.UE_WAKEUP:
                self._handle_ue_wakeup(current_time, payload, duration_sec)

        # 4. Finalize energy tracking for all devices
        for dev in self.devices.values():
            dev.finalize_simulation(duration_sec, self.energy_model)

        return self.delivered_packets

    def _handle_packet_arrive(self, current_time: float, packet: Packet) -> None:
        """Process packet arriving at gNodeB from core network."""
        ue_id = packet.ue_id
        dev = self.devices[ue_id]

        # Queue packet in paging controller
        self.paging_controller.enqueue_packet(packet)

        # Notify algorithm of traffic arrival
        self.algorithm.on_packet_arrived(dev, packet, current_time)

    def _handle_ue_wakeup(
        self, current_time: float, ue_id: int, duration_sec: float
    ) -> None:
        """Process device waking up at its scheduled Paging Occasion (PO)."""
        dev = self.devices[ue_id]

        # Device transitions from DEEP_SLEEP to PO_MONITOR
        dev.transition_to(EnergyState.PO_MONITOR, current_time, self.energy_model)

        t_listen = self.energy_model.t_listen_sec
        t_after_listen = current_time + t_listen

        has_data = self.paging_controller.has_pending_packets(ue_id)
        # Record wake-up in device counters
        dev.record_wakeup(has_data)

        if not has_data:
            # Case A: Idle Wake-Up (No paging for this UE)
            dev.transition_to(EnergyState.DEEP_SLEEP, t_after_listen, self.energy_model)

            self.algorithm.on_device_wakeup(dev, had_pending_data=False, current_time=t_after_listen)
            next_interval = self.algorithm.calculate_next_interval(
                dev, current_time=t_after_listen, had_pending_data=False, packet=None
            )
            dev.current_wake_interval = next_interval
            dev.next_wakeup_time = t_after_listen + next_interval

            # Schedule next wake-up event
            if dev.next_wakeup_time < duration_sec:
                self.engine.schedule_event(
                    dev.next_wakeup_time, EventType.UE_WAKEUP, ue_id
                )

        else:
            # Case B: Paged (Downlink packets waiting)
            # Paging message transmission over the air
            self.paging_controller.record_paging_transmission({ue_id})

            # Handshake: Uplink RACH/ACK (ACTIVE_TX)
            t_tx_end = t_after_listen + self.energy_model.t_tx_sec
            dev.transition_to(EnergyState.ACTIVE_TX, t_after_listen, self.energy_model)

            # Downlink Data Reception (ACTIVE_RX)
            t_rx_end = t_tx_end + self.energy_model.t_rx_sec
            dev.transition_to(EnergyState.ACTIVE_RX, t_tx_end, self.energy_model)

            # Dequeue and mark delivered
            packets = self.paging_controller.dequeue_packets(ue_id)
            for pkt in packets:
                pkt.mark_delivered(delivery_time=t_rx_end)
                self.delivered_packets.append(pkt)
                dev.total_packets_received += 1

            # Inactivity Timer monitoring prior to sleep
            t_inact_end = t_rx_end + self.energy_model.t_inactivity_sec
            dev.transition_to(EnergyState.INACTIVITY, t_rx_end, self.energy_model)

            # Return to deep sleep
            dev.transition_to(EnergyState.DEEP_SLEEP, t_inact_end, self.energy_model)

            # Update algorithm state and schedule next wake-up
            last_pkt = packets[-1] if packets else None
            self.algorithm.on_device_wakeup(dev, had_pending_data=True, current_time=t_inact_end)
            next_interval = self.algorithm.calculate_next_interval(
                dev, current_time=t_inact_end, had_pending_data=True, packet=last_pkt
            )
            dev.current_wake_interval = next_interval
            dev.next_wakeup_time = t_inact_end + next_interval

            if dev.next_wakeup_time < duration_sec:
                self.engine.schedule_event(
                    dev.next_wakeup_time, EventType.UE_WAKEUP, ue_id
                )

