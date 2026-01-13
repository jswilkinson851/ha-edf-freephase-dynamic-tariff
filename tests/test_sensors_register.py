import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry
from custom_components.edf_freephase_dynamic_tariff.sensors import ALL_SENSORS
from custom_components.edf_freephase_dynamic_tariff.sensors.slots import (
    create_next_phase_sensors,
)


@pytest.mark.asyncio
async def test_all_sensors_register_correctly(hass):
    """Verify that all sensors (including factory-generated ones) register correctly."""

    # ------------------------------------------------------------------
    # 1. Create a fake config entry
    # ------------------------------------------------------------------
    entry = hass.config_entries.async_create_entry(
        domain="edf_freephase_dynamic_tariff",
        data={
            "tariff_code": "E-1R-EDF-FREEPHASE-DYNAMIC",
            "scan_interval": 30,
        },
        title="EDF FreePhase Dynamic Tariff",
    )

    # ------------------------------------------------------------------
    # 2. Run setup
    # ------------------------------------------------------------------
    await async_setup_entry(hass, entry, hass.helpers.entity_component.async_add_entities)
    await hass.async_block_till_done()

    # ------------------------------------------------------------------
    # 3. Build expected entity list
    # ------------------------------------------------------------------
    expected_entities = []

    # Classes in ALL_SENSORS
    for sensor in ALL_SENSORS:
        if sensor is create_next_phase_sensors:
            # Factory returns 3 sensors
            expected_entities.extend([
                "edf_freephase_dynamic_tariff_next_green_slot",
                "edf_freephase_dynamic_tariff_next_amber_slot",
                "edf_freephase_dynamic_tariff_next_red_slot",
            ])
        else:
            # Instantiate to inspect unique_id
            instance = sensor(None)  # coordinator not needed for unique_id
            expected_entities.append(instance.unique_id)

    # ------------------------------------------------------------------
    # 4. Verify entity registry contains all expected sensors
    # ------------------------------------------------------------------
    entity_registry = er.async_get(hass)

    missing = []
    for unique_id in expected_entities:
        entity = entity_registry.async_get_entity_id(
            "sensor", "edf_freephase_dynamic_tariff", unique_id
        )
        if entity is None:
            missing.append(unique_id)

    assert not missing, f"Missing sensors: {missing}"

    # ------------------------------------------------------------------
    # 5. Verify correct total count
    # ------------------------------------------------------------------
    registered = [
        e for e in entity_registry.entities.values()
        if e.platform == "edf_freephase_dynamic_tariff"
    ]

    assert len(registered) == len(expected_entities)