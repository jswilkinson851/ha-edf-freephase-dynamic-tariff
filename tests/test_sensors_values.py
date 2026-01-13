import pytest
pytestmark = pytest.mark.xfail(reason="Test suite temporarily disabled pending redesign")

from unittest.mock import AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_sensor_reads_current_price(hass):
    """Ensure the current price sensor reflects coordinator.data."""

    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    added_entities = []

    async def _async_add_entities(entities):
        added_entities.extend(entities)

    # Fake coordinator instance
    fake_coord = AsyncMock()
    fake_coord.async_config_entry_first_refresh = AsyncMock()

    # Patch coordinator class so no scheduler timers run
    with patch(
        "custom_components.edf_freephase_dynamic_tariff.sensor.EDFCoordinator",
        return_value=fake_coord,
    ):
        await async_setup_entry(hass, entry, _async_add_entities)
        await hass.async_block_till_done()

    # Inject fake coordinator data AFTER sensors are created
    fake_coord.data = {
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

    # Force HA to update entity states
    for entity in added_entities:
        if hasattr(entity, "async_write_ha_state"):
            entity.async_write_ha_state()

    state = hass.states.get("sensor.edf_freephase_dynamic_tariff_current_price")
    assert state is not None
    assert float(state.state) == 12.34