import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry
from custom_components.edf_freephase_dynamic_tariff.sensors import ALL_SENSORS
from custom_components.edf_freephase_dynamic_tariff.sensors.slots import (
    create_next_phase_sensors,
)


@pytest.mark.asyncio
async def test_all_sensors_register_correctly(hass):
    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    await async_setup_entry(hass, entry, hass.helpers.entity_component.async_add_entities)
    await hass.async_block_till_done()

    expected_entities = []

    for sensor in ALL_SENSORS:
        if sensor is create_next_phase_sensors:
            expected_entities.extend([
                "edf_freephase_dynamic_tariff_next_green_slot",
                "edf_freephase_dynamic_tariff_next_amber_slot",
                "edf_freephase_dynamic_tariff_next_red_slot",
            ])
        else:
            instance = sensor(None)
            expected_entities.append(instance.unique_id)

    entity_registry = er.async_get(hass)

    missing = []
    for unique_id in expected_entities:
        entity = entity_registry.async_get_entity_id(
            "sensor", "edf_freephase_dynamic_tariff", unique_id
        )
        if entity is None:
            missing.append(unique_id)

    assert not missing, f"Missing sensors: {missing}"