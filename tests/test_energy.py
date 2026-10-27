"""
Unit tests for 3GPP State-Based Energy Model and Battery Lifetime Estimations.
"""

import pytest
from src.models.energy import EnergyModel, EnergyState
from src.models.device import IoTDevice


def test_energy_model_joule_computation():
    """Verify conversion of state power (mW) to energy (Joules)."""
    model = EnergyModel(
        p_sleep_mw=0.015,
        p_listen_mw=45.0,
        p_rx_mw=110.0,
        p_tx_mw=320.0,
    )

    # 100 seconds in deep sleep: (0.015 / 1000) * 100 = 0.0015 Joules
    e_sleep = model.compute_energy_joules(EnergyState.DEEP_SLEEP, 100.0)
    assert e_sleep == pytest.approx(0.0015)

    # 15 ms in PO_MONITOR: (45.0 / 1000) * 0.015 = 0.000675 Joules
    e_listen = model.compute_energy_joules(EnergyState.PO_MONITOR, 0.015)
    assert e_listen == pytest.approx(0.000675)

    # Negative duration should yield 0.0
    assert model.compute_energy_joules(EnergyState.DEEP_SLEEP, -5.0) == 0.0


def test_battery_lifetime_estimation():
    """Verify theoretical battery lifetime formula."""
    # 3.0V, 1000 mAh battery = 3.0 * 1.0 * 3600 = 10,800 Joules
    model = EnergyModel(
        battery_voltage_v=3.0,
        battery_capacity_mah=1000.0,
    )
    assert model.battery_total_joules == pytest.approx(10800.0)

    # Suppose a device consumes 108 Joules over 3600 seconds (P_avg = 108/3600 = 0.03 W)
    # Total battery duration = 10800 / 0.03 = 360,000 seconds
    # Years = 360000 / (3600 * 24 * 365.25) ~ 0.0114077 years
    lifetime_years = model.estimate_battery_lifetime_years(
        total_energy_joules=108.0, simulation_duration_sec=3600.0
    )
    expected_years = 360000.0 / (3600.0 * 24.0 * 365.25)
    assert lifetime_years == pytest.approx(expected_years)


def test_device_state_transitions():
    """Verify that IoTDevice records time and energy spent across states."""
    model = EnergyModel(p_sleep_mw=0.015, p_listen_mw=45.0)
    dev = IoTDevice(ue_id=1, initial_wake_interval=2.56, initial_wakeup_time=1.0)

    # Start at t=0 in DEEP_SLEEP
    # At t=2.0 transition to PO_MONITOR
    dev.transition_to(EnergyState.PO_MONITOR, current_time=2.0, energy_model=model)
    assert dev.state_durations[EnergyState.DEEP_SLEEP] == pytest.approx(2.0)
    # Energy spent in sleep = 2.0 * (0.015 / 1000) = 0.000030 J
    assert dev.accumulated_energy_joules == pytest.approx(0.000030)

    # At t=2.015 transition back to DEEP_SLEEP
    dev.transition_to(EnergyState.DEEP_SLEEP, current_time=2.015, energy_model=model)
    assert dev.state_durations[EnergyState.PO_MONITOR] == pytest.approx(0.015)
    # Additional energy for listen = 0.015 * (45.0 / 1000) = 0.000675 J
    assert dev.accumulated_energy_joules == pytest.approx(0.000030 + 0.000675)

