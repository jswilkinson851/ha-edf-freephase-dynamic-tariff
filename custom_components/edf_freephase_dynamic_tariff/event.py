"""
Event platform for the EDF FreePhase Dynamic Tariff integration.

This module registers the integration’s event entity, which emits structured
slot‑ and phase‑transition events derived from the coordinator’s tariff data.
Unlike sensors or binary sensors, event entities do not expose a numeric or
boolean state; instead, they publish discrete, timestamped events that can be
consumed by automations, scripts, or other integrations.

The event entity defined in `events/` listens to the shared
DataUpdateCoordinator and reacts whenever new tariff data is fetched from EDF’s
API. When the coordinator detects a transition—such as a slot change, phase
change, or a new upcoming phase window—the event entity generates a
corresponding Home Assistant event with a rich payload describing the change.

This platform is responsible only for:

1. Creating the event entity instance.
2. Registering it with Home Assistant.
3. Subscribing the entity to coordinator updates using the correct lifecycle
   ordering (subscription occurs after the entity is added).
4. Ensuring the entity is automatically unsubscribed when removed.

All transition‑detection logic, payload construction, and event emission
behaviour lives inside the `EDFFreePhaseDynamicSlotEventEntity` class.
"""

import logging

# pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .const import DOMAIN
from .events import EDFFreePhaseDynamicSlotEventEntity

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """
    Event entity responsible for emitting slot‑ and phase‑transition events for
    the EDF FreePhase Dynamic Tariff integration.

    This entity listens to the shared DataUpdateCoordinator and reacts whenever
    new tariff data is fetched from EDF’s API. On each coordinator update, the
    entity compares the newly‑computed slot and phase information with its
    previously stored state. When a transition is detected—such as a slot
    change, a phase starting or ending, or a change in the next upcoming phase
    window—the entity emits a Home Assistant event with a structured payload
    describing the transition.

    The entity’s responsibilities include:
      • Tracking the previous slot, phase, and block context.
      • Detecting transitions between tariff phases (green/amber/red).
      • Detecting slot changes and merged‑block changes.
      • Emitting rich Home Assistant events via `_trigger_event()`.
      • Updating its own state to reflect the timestamp and details of the
        most recent transition.

    Unlike sensors, this entity does not expose a numeric or textual state
    representing the tariff. Instead, its state is the timestamp of the most
    recent event, and all meaningful information is delivered through event
    payloads and attributes. This makes the entity ideal for automations that
    need to react to discrete changes in tariff conditions rather than poll
    for values.

    All transition‑detection logic and event‑emission behaviour is implemented
    within this class; the platform module (`event.py`) is responsible only for
    instantiation and coordinator subscription.
    """
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    # Create the entity
    entity = EDFFreePhaseDynamicSlotEventEntity(coordinator)
    async_add_entities([entity])

    # Subscribe AFTER the entity is added AND using the correct coordinator reference
    entity.async_on_remove(
        coordinator.async_add_listener(entity._handle_coordinator_update)
    )

