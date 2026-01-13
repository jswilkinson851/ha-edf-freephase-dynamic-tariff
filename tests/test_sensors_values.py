import pytest
from unittest.mock import patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_sensor_reads_current_price(hass):
    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    fake_data = {
        "current_price": 12.34,
        "current_slot": {"phase": "Green"},
        "next_price": 20,
        "next_24_hours": [],
        "today_24_hours": [],
        "tomorrow_24_hours": [],
        "yesterday_24_hours": [],
        "all_slots_sorted": [],
        "api_latency_ms": 10,
        "last_updated": "2024-01-01T00:00:00Z",
        "coordinator_status": "ok",
    }

    with patch(
        "custom_components.edf_freephase_dynamic_tariff.coordinator.EDFCoordinator.async_refresh",
        return_value=None,
    ), patch(
        "custom_components.edf_freephase_dynamic_tariff.coordinator.EDFCoordinator.data",
        fake_data,
    ):
        await async_setup_entry(
            hass, entry, hass.helpers.entity_component.async_add_entities
        )
        await hass.async_block_till_done()

    state = hass.states.get("sensor.edf_freephase_dynamic_tariff_current_price")
    assert state is not None
    assert float(state.state) == 12.34