"""
Discrete-Event Simulation Engine for 5G Paging.
"""

import heapq
from enum import Enum, auto
from typing import Any, Tuple, Optional, List


class EventType(Enum):
    """Event types handled by the discrete-event simulation engine."""
    PACKET_ARRIVE = auto()        # Downlink packet arrives at gNodeB
    UE_WAKEUP = auto()            # UE wakes up at its Paging Occasion (PO)
    PAGING_TRANSMIT = auto()      # gNodeB broadcasts paging frame
    DATA_DELIVER = auto()         # Packet transmission completes
    INACTIVITY_EXPIRE = auto()    # UE inactivity timer expires -> return to sleep


class SimulationEngine:
    """
    Priority-queue discrete-event simulation engine with microsecond fidelity.
    """

    def __init__(self):
        self.current_time: float = 0.0
        self.event_queue: List[Tuple[float, int, EventType, Any]] = []
        self._event_counter: int = 0

    def reset(self):
        """Reset the simulation engine."""
        self.current_time = 0.0
        self.event_queue.clear()
        self._event_counter = 0

    def schedule_event(
        self, timestamp: float, event_type: EventType, payload: Any = None
    ) -> int:
        """
        Schedule an event at a future simulation time.

        Parameters
        ----------
        timestamp : float
            Simulation time at which the event should execute.
        event_type : EventType
            Type of the event.
        payload : Any
            Associated payload data (e.g. packet or device ID).

        Returns
        -------
        int
            Unique event ID.
        """
        if timestamp < self.current_time:
            # Prevent scheduling in the past
            timestamp = self.current_time

        self._event_counter += 1
        event_id = self._event_counter
        heapq.heappush(
            self.event_queue, (float(timestamp), event_id, event_type, payload)
        )
        return event_id

    def pop_event(self) -> Optional[Tuple[float, EventType, Any]]:
        """
        Pop and advance time to the next earliest event.

        Returns
        -------
        Optional[Tuple[float, EventType, Any]]
            (timestamp, event_type, payload) or None if queue is empty.
        """
        if not self.event_queue:
            return None

        timestamp, _, event_type, payload = heapq.heappop(self.event_queue)
        self.current_time = timestamp
        return timestamp, event_type, payload

    def has_events(self) -> bool:
        """Check whether pending events exist."""
        return len(self.event_queue) > 0

    def peek_next_time(self) -> Optional[float]:
        """Return the timestamp of the next upcoming event without popping."""
        if not self.event_queue:
            return None
        return self.event_queue[0][0]

