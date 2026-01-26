"""
Binary sensor platform for the EDF FreePhase Dynamic Tariff integration.

This module registers binary sensors that expose simple, automation‑friendly
boolean signals derived from the coordinator’s tariff dataset. These sensors
provide high‑level “is this condition true right now?” flags that complement
the richer slot/phase entities and event stream.

Binary sensors in this platform are backed by the shared DataUpdateCoordinator,
ensuring they always reflect the most recent tariff information fetched from
EDF’s FreePhase Dynamic API. The coordinator is initialised and refreshed in
the integration’s root setup, so by the time this platform is loaded the
dataset is already available for immediate evaluation.

Currently implemented:
    • EDFFreePhaseDynamicIsGreenSlotBinarySensor
        Indicates whether the *current* tariff slot is classified as “green”
        (i.e., lowest‑cost period). This is useful for simple automations such
        as opportunistic charging, heating, or load‑shifting behaviours.

Additional binary sensors may be added in future to expose other boolean
conditions (e.g., “is_red_slot”, “is_amber_slot”, “is_offpeak_window”),
following the same coordinator‑driven pattern.

This file is responsible only for entity registration. All behavioural logic
lives inside the individual binary sensor classes under `binary_sensors/`.
"""

from __future__ import annotations

# pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .binary_sensors.is_green_slot import (
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
)
from .const import DOMAIN


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
