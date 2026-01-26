"""
Sensor platform setup for the EDF FreePhase Dynamic Tariff integration.

This module is responsible for creating and registering all sensor entities
exposed by the integration. It wires together the EDF API coordinator, the cost
computation coordinator, and the various entity classes defined under sensors/.
"""

from __future__ import annotations

import logging
from typing import Iterable, cast

from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.entity import Entity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from .const import DOMAIN
from .sensors import ALL_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up EDF FreePhase Dynamic Tariff sensors."""

    data = hass.data[DOMAIN][entry.entry_id]

    # Coordinators
    edf_coordinator = data["coordinator"]
    cost_coordinator = data.get("cost_coordinator")

    if cost_coordinator is None:
        _LOGGER.warning(
            "EDF FreePhase Dynamic Tariff: cost_coordinator is missing for entry %s. "
            "Cost summary sensors will remain unavailable until cost_coordinator becomes ready.",
            entry.entry_id,
        )

    # Coordinators have already been refreshed in __init__.py
    # No need to refresh again here — avoids double API calls.

    entities: list[Entity] = []

    for sensor in ALL_SENSORS:
        # Factory function for next-phase sensors
        if callable(sensor) and sensor.__name__ == "create_next_phase_sensors":
            factory_result = cast(Iterable[Entity], sensor(edf_coordinator))
            entities.extend(factory_result)
            continue

        # Universal instantiation logic:
        # Try (edf_coordinator, cost_coordinator)
        # Fall back to (edf_coordinator) if the class only accepts one argument.
        try:
            entity = sensor(edf_coordinator, cost_coordinator)
        except TypeError:
            entity = sensor(edf_coordinator)

        entities.append(entity)

    async_add_entities(entities)

    _LOGGER.debug(
        "EDF FreePhase Dynamic Tariff: Added %d sensor entities for entry %s",
        len(entities),
        entry.entry_id,
    )
