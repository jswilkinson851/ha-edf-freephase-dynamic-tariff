from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .sensors import ALL_SENSORS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up EDF FreePhase Dynamic Tariff sensors."""

    # Retrieve the coordinator created in __init__.py
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Ensure the coordinator has fresh data before adding sensors
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Build all sensors defined in sensors/__init__.py
    for sensor in ALL_SENSORS:
        if callable(sensor) and sensor.__name__ == "create_next_phase_sensors":
            # This factory returns multiple sensors
            entities.extend(sensor(coordinator))
        else:
            # Normal sensor class
            entities.append(sensor(coordinator))

    async_add_entities(entities)