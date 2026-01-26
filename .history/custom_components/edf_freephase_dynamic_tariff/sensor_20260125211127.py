"""
Sensor platform for the EDF FreePhase Dynamic Tariff integration.

This module is responsible for creating and registering all sensor entities
exposed by the integration. It acts as the bridge between Home Assistant’s
entity platform and the integration’s coordinators, wiring together the EDF
API data, cost‑computation logic, and the various sensor classes defined under
`sensors/`.

The platform performs the following responsibilities:

1. Coordinator wiring
   The integration exposes two coordinators:
     • `coordinator` — fetches EDF’s dynamic tariff data (slots, phases, metadata)
     • `cost_coordinator` — computes cost summaries and standing‑charge data
   Both coordinators are initialised and refreshed in `__init__.py`, so this
   platform simply receives them and passes them to the appropriate sensor
   classes.

2. Sensor instantiation
   The list of all sensor classes and factories is defined in `sensors.ALL_SENSORS`.
   This platform iterates through that list and instantiates each sensor using a
   universal pattern:
     • If the item is a factory function (e.g., next‑phase sensor generator),
       it is called with the EDF coordinator and expected to return an iterable
       of sensor entities.
     • Otherwise, the platform attempts to instantiate the sensor class with
       `(edf_coordinator, cost_coordinator)`, falling back to `(edf_coordinator)`
       if the class only accepts a single argument.

   This approach keeps the platform generic and allows each sensor class to
   declare its own constructor signature without requiring special‑case logic
   here.

3. Entity registration
   Once instantiated, all sensor entities are added to Home Assistant via
   `async_add_entities()`. The platform does not refresh the coordinators,
   avoiding duplicate API calls and ensuring consistent update timing.

4. Graceful degradation
   If the cost coordinator is not yet available (e.g., during startup or if the
   cost API is temporarily unavailable), the platform logs a warning and still
   registers all sensors that do not depend on cost data. Cost‑dependent sensors
   will remain unavailable until the cost coordinator becomes ready.

This module contains no tariff logic itself; all computation, parsing, and
state derivation is handled by the coordinators and the individual sensor
classes under `sensors/`.
"""

from __future__ import annotations

import logging
from typing import Iterable, cast

# pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.entity import Entity  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

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
