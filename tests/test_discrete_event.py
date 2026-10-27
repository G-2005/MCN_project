"""
Unit tests for Discrete-Event Simulation Engine.
"""

import pytest
from src.core.event_engine import SimulationEngine, EventType


def test_simulation_engine_chronological_ordering():
    """Verify that events pop in strict non-decreasing chronological order."""
    engine = SimulationEngine()
    engine.schedule_event(10.5, EventType.PACKET_ARRIVE, "event3")
    engine.schedule_event(2.0, EventType.UE_WAKEUP, "event1")
    engine.schedule_event(5.2, EventType.DATA_DELIVER, "event2")
    engine.schedule_event(2.0, EventType.INACTIVITY_EXPIRE, "event1_tie")

    t1, ev1, p1 = engine.pop_event()
    assert t1 == 2.0
    assert p1 == "event1"

    t2, ev2, p2 = engine.pop_event()
    assert t2 == 2.0
    assert p2 == "event1_tie"

    t3, ev3, p3 = engine.pop_event()
    assert t3 == 5.2
    assert p3 == "event2"

    t4, ev4, p4 = engine.pop_event()
    assert t4 == 10.5
    assert p4 == "event3"

    assert not engine.has_events()
    assert engine.pop_event() is None


def test_simulation_engine_no_backward_scheduling():
    """Verify that scheduling in the past clamps to current simulation time."""
    engine = SimulationEngine()
    engine.schedule_event(10.0, EventType.UE_WAKEUP, "first")
    engine.pop_event()
    assert engine.current_time == 10.0

    # Attempt to schedule event at t=5.0 (earlier than current time 10.0)
    engine.schedule_event(5.0, EventType.PACKET_ARRIVE, "past_event")
    t, _, p = engine.pop_event()
    assert t == 10.0
    assert p == "past_event"

