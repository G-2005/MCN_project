"""
5G Base Station Paging Controller.

Manages downlink buffer queues, paging records, P-RNTI paging frame scheduling,
and paging overhead tracking.
"""

from typing import Dict, List, Set, Any
from collections import defaultdict
from src.models.traffic import Packet


class PagingController:
    """
    Paging Controller operating within the 5G gNodeB / AMF.

    Parameters
    ----------
    max_records_per_message : int
        Maximum number of paged UEs bundled in a single PCH transport block.
        3GPP TS 38.331 typically allows up to 16 or 32 paging records per message.
    paging_message_bytes : int
        Estimated protocol overhead in bytes for one paging transport block (e.g. 128 bytes).
    """

    def __init__(
        self, max_records_per_message: int = 16, paging_message_bytes: int = 128
    ):
        self.max_records_per_message = int(max_records_per_message)
        self.paging_message_bytes = int(paging_message_bytes)

        # Buffer: ue_id -> list of pending Packets
        self.pending_queues: Dict[int, List[Packet]] = defaultdict(list)

        # Paging stats
        self.total_paging_messages_transmitted: int = 0
        self.total_paging_records_transmitted: int = 0
        self.total_paging_bytes_transmitted: int = 0

    def enqueue_packet(self, packet: Packet) -> None:
        """Add a downlink packet to the UE's pending queue."""
        self.pending_queues[packet.ue_id].append(packet)

    def has_pending_packets(self, ue_id: int) -> bool:
        """Check whether packets are queued for the given UE."""
        return len(self.pending_queues[ue_id]) > 0

    def get_pending_count(self, ue_id: int) -> int:
        """Return number of pending packets for the UE."""
        return len(self.pending_queues[ue_id])

    def dequeue_packets(self, ue_id: int) -> List[Packet]:
        """Retrieve and remove all queued packets for the given UE."""
        packets = self.pending_queues.pop(ue_id, [])
        return packets

    def record_paging_transmission(self, paged_ue_ids: Set[int]) -> int:
        """
        Record transmission of paging message(s) containing the set of paged UEs.

        Returns
        -------
        int
            Number of physical paging messages broadcast.
        """
        num_records = len(paged_ue_ids)
        if num_records == 0:
            return 0

        # Number of transport blocks required to bundle the records
        num_messages = (num_records + self.max_records_per_message - 1) // self.max_records_per_message

        self.total_paging_records_transmitted += num_records
        self.total_paging_messages_transmitted += num_messages
        self.total_paging_bytes_transmitted += num_messages * self.paging_message_bytes

        return num_messages

    def reset(self) -> None:
        """Reset internal queues and counters."""
        self.pending_queues.clear()
        self.total_paging_messages_transmitted = 0
        self.total_paging_records_transmitted = 0
        self.total_paging_bytes_transmitted = 0

    def to_dict(self) -> Dict[str, Any]:
        """Export controller metrics."""
        return {
            "total_paging_messages": self.total_paging_messages_transmitted,
            "total_paging_records": self.total_paging_records_transmitted,
            "total_paging_bytes": self.total_paging_bytes_transmitted,
            "current_queued_devices": len(self.pending_queues),
        }

