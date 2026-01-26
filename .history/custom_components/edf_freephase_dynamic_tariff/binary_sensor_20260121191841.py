"""
Binary sensor platform setup for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from .const import DOMAIN
from .binary_sensors.is_green_slot import (
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Set up EDF FreePhase Dynamic Tariff binary sensors."""

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    # Coordinator has already been refreshed in __init__.py

    entities = [
        EDFFreePhaseDynamicIsGreenSlotBinarySensor(coordinator),
    ]

    async_add_entities(entities)
