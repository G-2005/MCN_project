"""
Unit tests for explicit bounds compliance and Paging Controller multiplexing.
"""

import pytest
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.core.paging_controller import PagingController
from src.models.traffic import Packet
from src.models.device import IoTDevice


def test_strict_bounds_and_invalid_inputs():
    """Verify invalid constructor arguments raise expected errors."""
    with pytest.raises(ValueError, match="t_min_sec.*cannot exceed t_max_sec"):
        AdaptivePagingAlgorithm(t_min_sec=10.0, t_max_sec=2.0)

    with pytest.raises(ValueError, match="ewma_alpha must be in"):
        AdaptivePagingAlgorithm(ewma_alpha=0.0)

    with pytest.raises(ValueError, match="qos_beta must be in"):
        AdaptivePagingAlgorithm(qos_beta=1.5)


def test_paging_controller_multiplexing():
    """Verify bundling of paging records into transport blocks."""
    ctrl = PagingController(max_records_per_message=4, paging_message_bytes=100)

    # Empty set
    assert ctrl.record_paging_transmission(set()) == 0

    # 3 UEs paged -> 1 message
    assert ctrl.record_paging_transmission({1, 2, 3}) == 1
    assert ctrl.total_paging_records_transmitted == 3
    assert ctrl.total_paging_messages_transmitted == 1
    assert ctrl.total_paging_bytes_transmitted == 100

    # 9 UEs paged -> (9 + 4 - 1) // 4 = 3 messages
    assert ctrl.record_paging_transmission(set(range(9))) == 3
    assert ctrl.total_paging_records_transmitted == 12
    assert ctrl.total_paging_messages_transmitted == 4
    assert ctrl.total_paging_bytes_transmitted == 400


def test_paging_controller_queue_and_dequeue():
    """Verify packet enqueue and dequeue functionality."""
    ctrl = PagingController()
    assert not ctrl.has_pending_packets(42)

    p1 = Packet(1, 42, 1.0, 256, 5.0)
    p2 = Packet(2, 42, 1.5, 256, 5.0)
    ctrl.enqueue_packet(p1)
    ctrl.enqueue_packet(p2)

    assert ctrl.has_pending_packets(42)
    assert ctrl.get_pending_count(42) == 2

    dequeued = ctrl.dequeue_packets(42)
    assert len(dequeued) == 2
    assert dequeued[0].packet_id == 1
    assert dequeued[1].packet_id == 2
    assert not ctrl.has_pending_packets(42)

