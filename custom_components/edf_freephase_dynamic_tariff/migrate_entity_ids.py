"""
Entity ID migration helper for EDF FreePhase Dynamic Tariff.

This module rewrites old entity_ids to the new build_entity_id() format
while preserving unique_ids, history, dashboards, and automations.

It is invoked once during async_setup_entry() and is safe to run repeatedly.
"""

from __future__ import annotations

# pylint: disable=import-error
from homeassistant.helpers.entity_registry import (  # pyright: ignore[reportMissingImports]
    EntityRegistry,
)
from homeassistant.helpers.entity_registry import (  # pyright: ignore[reportMissingImports]
    async_get as async_get_entity_registry,
)

# pylint: enable=import-error
from .helpers import build_entity_id

# ---------------------------------------------------------------------------
# Mapping of old object_ids → new object_ids
# ---------------------------------------------------------------------------

ENTITY_ID_MIGRATIONS = {
    # Sensors
    "current_price": "current_price",
    "next_slot_price": "next_slot_price",
    "24_hour_forecast": "24_hour_forecast",
    "cheapest_slot": "cheapest_slot",
    "most_expensive_slot": "most_expensive_slot",

    # Phase summaries
    "today_phases_summary": "today_phases_summary",
    "tomorrow_phases_summary": "tomorrow_phases_summary",
    "yesterday_phases_summary": "yesterday_phases_summary",

    # Slot/phase sensors
    "current_slot_colour": "current_slot_colour",
    "current_block_summary": "current_phase_summary",   # renamed
    "next_block_summary": "next_phase_summary",      # renamed

    # Next-phase slot sensors
    "next_green_slot": "next_green_slot",
    "next_amber_slot": "next_amber_slot",
    "next_red_slot": "next_red_slot",

    # Standing charge
    "standing_charge": "standing_charge",

    # Binary sensors
    "is_green_slot": "is_green_slot",

    # Event entity
    "tariff_slot_phase_events": "tariff_slot_phase_events",

    # Switch
    "debug_logging": "debug_logging",
}


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

async def async_migrate_entity_ids(hass, entry):
    """
    Rewrite old entity_ids to the new build_entity_id() format.

    This function:
        - Loads the entity registry
        - Finds all entities belonging to this config entry
        - Computes the new entity_id using build_entity_id()
        - Updates the registry entry if the entity_id has changed

    It is safe to run multiple times (idempotent).
    """

    registry: EntityRegistry = async_get_entity_registry(hass)

    for entity_id, entity in list(registry.entities.items()):
        if entity.config_entry_id != entry.entry_id:
            continue

        old_object_id = entity_id.split(".")[1]

        if old_object_id not in ENTITY_ID_MIGRATIONS:
            continue

        new_object_id = ENTITY_ID_MIGRATIONS[old_object_id]

        new_entity_id = build_entity_id(
            domain=entity.domain,
            object_id=new_object_id,
            tariff="fpd",
        )

        if new_entity_id != entity_id:
            registry.async_update_entity(entity_id, new_entity_id=new_entity_id)
