"""
Unit tests for Adaptive Paging Scheduling Algorithm (AdaPaging).
"""

import pytest
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.models.device import IoTDevice
from src.models.traffic import Packet


def test_adapaging_bounds_enforcement():
    """Verify that AdaPaging strictly respects [T_min, T_max] bounds."""
    t_min = 0.64
    t_max = 10.24
    algo = AdaptivePagingAlgorithm(
        t_min_sec=t_min,
        t_max_sec=t_max,
        t_burst_sec=t_min,
        ewma_alpha=0.35,
        qos_beta=0.75,
        ramp_up_factor=0.35,
    )

    dev = IoTDevice(ue_id=0, initial_wake_interval=t_min, initial_wakeup_time=0.5)

    # 1. Idle ramp-up test: interval should grow but never exceed t_max
    for _ in range(30):
        next_int = algo.calculate_next_interval(
            device=dev, current_time=10.0, had_pending_data=False, packet=None
        )
        assert t_min <= next_int <= t_max
        dev.current_wake_interval = next_int

    assert dev.current_wake_interval == pytest.approx(t_max)

    # 2. Burst collapse test: should collapse immediately down to t_min
    burst_int = algo.calculate_next_interval(
        device=dev, current_time=20.0, had_pending_data=True, packet=None
    )
    assert burst_int == pytest.approx(t_min)


def test_adapaging_qos_deadline_clamping():
    """Verify that QoS latency deadline budget clamps the upper bound."""
    algo = AdaptivePagingAlgorithm(
        t_min_sec=0.64,
        t_max_sec=10.24,
        qos_beta=0.75,
    )

    # Case 1: Strict deadline D_max = 2.0s -> beta * D_max = 0.75 * 2.0 = 1.5s
    upper1 = algo.get_effective_upper_bound(deadline_budget=2.0)
    assert upper1 == pytest.approx(1.50)

    # Case 2: Very relaxed deadline D_max = 30.0s -> 0.75 * 30.0 = 22.5s, but t_max is 10.24s
    upper2 = algo.get_effective_upper_bound(deadline_budget=30.0)
    assert upper2 == pytest.approx(10.24)

    # Case 3: Ultra strict deadline D_max = 0.5s -> should clamp at t_min
    upper3 = algo.get_effective_upper_bound(deadline_budget=0.5)
    assert upper3 == pytest.approx(0.64)


def test_adapaging_ewma_traffic_tracking():
    """Verify EWMA updates when packets arrive."""
    algo = AdaptivePagingAlgorithm(
        t_min_sec=0.64,
        t_max_sec=10.24,
        ewma_alpha=0.5,
    )
    dev = IoTDevice(ue_id=0, initial_wake_interval=2.0, initial_wakeup_time=0.5)
    dev.ewma_inter_arrival = 10.0

    pkt1 = Packet(1, 0, arrival_time=5.0, payload_bytes=256, deadline_budget_sec=5.0)
    algo.on_packet_arrived(dev, pkt1, current_time=5.0)
    assert dev.last_packet_arrival_time == 5.0

    # Next packet arrives 2.0 seconds later at t=7.0
    pkt2 = Packet(2, 0, arrival_time=7.0, payload_bytes=256, deadline_budget_sec=5.0)
    algo.on_packet_arrived(dev, pkt2, current_time=7.0)
    # EWMA = 0.5 * 2.0 + 0.5 * 10.0 = 6.0
    assert dev.ewma_inter_arrival == pytest.approx(6.0)

