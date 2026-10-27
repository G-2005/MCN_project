"""
Edge Case and Boundary Testing for 5G Paging Simulation.
"""

import pytest
from src.models.energy import EnergyModel
from src.models.traffic import TrafficGenerator, Packet
from src.core.base_station import BaseStation
from src.algorithms.baseline_drx import BaselinePeriodicDRX
from src.algorithms.adaptive_paging import AdaptivePagingAlgorithm
from src.metrics.tracker import MetricsTracker


@pytest.fixture
def test_setup():
    energy_model = EnergyModel(
        p_sleep_mw=0.015,
        p_listen_mw=45.0,
        p_rx_mw=110.0,
        p_tx_mw=320.0,
    )
    ada_algo = AdaptivePagingAlgorithm(
        t_min_sec=0.64,
        t_max_sec=10.24,
        t_burst_sec=0.64,
        ewma_alpha=0.35,
        qos_beta=0.75,
        ramp_up_factor=0.35,
    )
    drx_algo = BaselinePeriodicDRX(cycle_sec=2.56)
    return energy_model, ada_algo, drx_algo


def test_edge_case_zero_traffic(test_setup):
    """
    Edge case: Simulation with zero downlink traffic.
    Verifies that devices smoothly ramp up to T_max and consume significantly
    less energy under AdaPaging than Baseline DRX without errors.
    """
    energy_model, ada_algo, drx_algo = test_setup
    duration = 100.0
    num_devices = 5

    empty_trace = []

    # Run Baseline DRX
    bs_drx = BaseStation(energy_model, drx_algo, num_devices, initial_wake_interval=2.56)
    del_drx = bs_drx.run_simulation(empty_trace, duration)
    m_drx = MetricsTracker.compute_run_metrics(
        del_drx, bs_drx.devices, bs_drx.paging_controller, energy_model, duration, "DRX", "zero", 42
    )

    # Run AdaPaging
    bs_ada = BaseStation(energy_model, ada_algo, num_devices, initial_wake_interval=0.64)
    del_ada = bs_ada.run_simulation(empty_trace, duration)
    m_ada = MetricsTracker.compute_run_metrics(
        del_ada, bs_ada.devices, bs_ada.paging_controller, energy_model, duration, "AdaPaging", "zero", 42
    )

    assert m_drx["packets_delivered"] == 0
    assert m_ada["packets_delivered"] == 0
    assert m_drx["total_paging_messages"] == 0
    assert m_ada["total_paging_messages"] == 0

    # Under zero traffic, AdaPaging reaches T_max (10.24s) while DRX is stuck at 2.56s.
    # Therefore, AdaPaging should perform approximately 4x fewer wake-ups and consume less energy!
    assert m_ada["total_wakeups"] < m_drx["total_wakeups"]
    assert m_ada["mean_energy_joules"] < m_drx["mean_energy_joules"]


def test_edge_case_extreme_burst(test_setup):
    """
    Edge case: Rapid burst of 10 packets arriving within 50 milliseconds for a single UE.
    Verifies that all burst packets are delivered cleanly.
    """
    energy_model, ada_algo, _ = test_setup
    duration = 50.0

    burst_packets = [
        Packet(
            packet_id=i,
            ue_id=0,
            arrival_time=5.0 + (i * 0.005),  # 5 ms spacing
            payload_bytes=256,
            deadline_budget_sec=4.0,
        )
        for i in range(10)
    ]

    bs = BaseStation(energy_model, ada_algo, num_devices=1, initial_wake_interval=0.64)
    delivered = bs.run_simulation(burst_packets, duration)

    assert len(delivered) == 10
    for p in delivered:
        assert p.delivered
        assert not p.deadline_missed
        assert p.delay_sec < 4.0


def test_edge_case_strict_deadline(test_setup):
    """
    Edge case: Devices with very strict latency deadline (D_max = 1.0s).
    AdaPaging must clamp wake-up interval to beta * D_max = 0.75s.
    """
    energy_model, ada_algo, _ = test_setup
    duration = 60.0

    strict_packets = [
        Packet(
            packet_id=i,
            ue_id=0,
            arrival_time=10.0 + i * 8.0,
            payload_bytes=256,
            deadline_budget_sec=1.0,
        )
        for i in range(5)
    ]

    bs = BaseStation(energy_model, ada_algo, num_devices=1, initial_wake_interval=0.64)
    delivered = bs.run_simulation(strict_packets, duration)

    assert len(delivered) == 5
    # Max wake interval should never exceed 0.75s (or t_min 0.64s)
    dev = bs.devices[0]
    assert dev.current_wake_interval <= 0.75 + 1e-5

