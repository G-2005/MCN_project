"""
Unit tests for Traffic Generator and Packet Trace Models.
"""

import pytest
from src.models.traffic import TrafficGenerator, Packet


@pytest.fixture
def base_traffic_config():
    return {
        "patterns": {
            "poisson": {"type": "poisson", "rate_lambda": 0.2, "default_deadline_sec": 5.0},
            "bursty": {
                "type": "bursty",
                "rate_on": 2.0,
                "rate_off": 0.05,
                "p_on_to_off": 0.2,
                "p_off_to_on": 0.1,
                "step_interval_sec": 1.0,
                "default_deadline_sec": 4.0,
            },
            "periodic": {"type": "periodic", "interval_sec": 10.0, "jitter_pct": 0.05, "default_deadline_sec": 8.0},
        }
    }


def test_traffic_reproducibility(base_traffic_config):
    """Ensure identical random seeds produce byte-identical packet traces."""
    trace1 = TrafficGenerator.generate_trace(
        pattern_name="poisson",
        config=base_traffic_config,
        num_devices=10,
        duration_sec=100.0,
        seed=12345,
    )
    trace2 = TrafficGenerator.generate_trace(
        pattern_name="poisson",
        config=base_traffic_config,
        num_devices=10,
        duration_sec=100.0,
        seed=12345,
    )

    assert len(trace1) == len(trace2)
    assert len(trace1) > 0
    for p1, p2 in zip(trace1, trace2):
        assert p1.packet_id == p2.packet_id
        assert p1.ue_id == p2.ue_id
        assert p1.arrival_time == pytest.approx(p2.arrival_time)
        assert p1.deadline_budget_sec == pytest.approx(p2.deadline_budget_sec)


def test_traffic_distinct_seeds(base_traffic_config):
    """Ensure different random seeds generate statistically distinct traces."""
    trace1 = TrafficGenerator.generate_trace(
        pattern_name="poisson",
        config=base_traffic_config,
        num_devices=10,
        duration_sec=100.0,
        seed=111,
    )
    trace2 = TrafficGenerator.generate_trace(
        pattern_name="poisson",
        config=base_traffic_config,
        num_devices=10,
        duration_sec=100.0,
        seed=222,
    )

    # Different seeds should not produce identical arrival sequences
    times1 = [p.arrival_time for p in trace1]
    times2 = [p.arrival_time for p in trace2]
    assert times1 != times2


def test_traffic_sorted_chronologically(base_traffic_config):
    """Verify generated trace is strictly non-decreasing in arrival time."""
    for pattern in ["poisson", "bursty", "periodic"]:
        trace = TrafficGenerator.generate_trace(
            pattern_name=pattern,
            config=base_traffic_config,
            num_devices=15,
            duration_sec=100.0,
            seed=42,
        )
        for i in range(1, len(trace)):
            assert trace[i].arrival_time >= trace[i - 1].arrival_time


def test_packet_delivery_metrics():
    """Verify packet latency and deadline calculations."""
    pkt = Packet(
        packet_id=1,
        ue_id=0,
        arrival_time=10.0,
        payload_bytes=256,
        deadline_budget_sec=5.0,
    )
    assert pkt.delivery_deadline == 15.0
    assert not pkt.delivered

    # Delivered on-time at t=13.0
    pkt.mark_delivered(13.0)
    assert pkt.delivered
    assert pkt.delay_sec == pytest.approx(3.0)
    assert not pkt.deadline_missed

    # Another packet delivered late at t=18.0
    pkt2 = Packet(
        packet_id=2,
        ue_id=0,
        arrival_time=10.0,
        payload_bytes=256,
        deadline_budget_sec=5.0,
    )
    pkt2.mark_delivered(18.0)
    assert pkt2.delivered
    assert pkt2.delay_sec == pytest.approx(8.0)
    assert pkt2.deadline_missed

