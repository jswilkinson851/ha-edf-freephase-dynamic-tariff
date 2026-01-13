import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry
from custom_components.edf_freephase_dynamic_tariff.sensors import ALL_SENSORS
from custom_components.edf_freephase_dynamic_tariff.sensors.slots import (
    create_next_phase_sensors,
)


@pytest.mark.asyncio
async def test_all_sensors_register_correctly(hass):
    """Ensure all sensors register in the entity registry."""

    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    added_entities = []

    async def _async_add_entities(entities):
        added_entities.extend(entities)

    # Patch coordinator so no scheduler timers run
    with patch(
        "custom_components.edf_freephase_dynamic_tariff.sensor.EDFCoordinator"
    ) as mock_coord_cls:
        mock_coord = AsyncMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coord

        await async_setup_entry(hass, entry, _async_add_entities)
        await hass.async_block_till_done()

    # Build expected unique IDs
    expected_unique_ids = []

    for sensor in ALL_SENSORS:
        if sensor is create_next_phase_sensors:
            expected_unique_ids.extend(
                [
                    "edf_freephase_dynamic_tariff_next_green_slot",
                    "edf_freephase_dynamic_tariff_next_amber_slot",
                    "edf_freephase_dynamic_tariff_next_red_slot",
                ]
            )
        else:
            instance = sensor(mock_coord)
            expected_unique_ids.append(instance.unique_id)

    entity_registry = er.async_get(hass)

    missing = []
    for unique_id in expected_unique_ids:
        entity_id = entity_registry.async_get_entity_id(
            "sensor", "edf_freephase_dynamic_tariff", unique_id
        )
        if entity_id is None:
            missing.append(unique_id)

    assert not missing, f"Missing sensors: {missing}"