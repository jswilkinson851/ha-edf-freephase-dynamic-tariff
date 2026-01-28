"""
Entity ID + Friendly Name migration helper for EDF FreePhase Dynamic Tariff.

This module rewrites old entity_ids AND old friendly names to the new
build_entity_id() format while preserving unique_ids, history, dashboards,
and automations.

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
#
# Keys here are *object_ids* (the part after "domain." in entity_id),
# NOT friendly names. Values are the new canonical object_ids that
# will be wrapped by build_entity_id(domain, object_id, tariff="fpd").
# ---------------------------------------------------------------------------

ENTITY_ID_MIGRATIONS = {
    # -----------------------------------------------------------------------
    # Forecast & price sensors
    # -----------------------------------------------------------------------
    "current_price": "current_price",
    "edf_freephase_dynamic_tariff_current_price": "current_price",

    "next_slot_price": "next_slot_price",
    "edf_freephase_dynamic_tariff_next_slot_price": "next_slot_price",

    "24_hour_forecast": "24_hour_forecast",
    "edf_freephase_dynamic_tariff_24_hour_forecast": "24_hour_forecast",

    "cheapest_slot": "cheapest_slot",
    "edf_freephase_dynamic_tariff_cheapest_slot": "cheapest_slot",

    "most_expensive_slot": "most_expensive_slot",
    "edf_freephase_dynamic_tariff_most_expensive_slot": "most_expensive_slot",

    # -----------------------------------------------------------------------
    # Cost & consumption summary sensors
    # -----------------------------------------------------------------------
    "today_cost_phase": "today_cost_phase",
    "edf_freephase_dynamic_tariff_today_cost_phase": "today_cost_phase",

    "yesterday_cost_phase": "yesterday_cost_phase",
    "edf_freephase_dynamic_tariff_yesterday_cost_phase": "yesterday_cost_phase",

    "today_consumption_phase": "today_consumption_phase",
    "edf_freephase_dynamic_tariff_today_consumption_phase": "today_consumption_phase",

    "yesterday_consumption_phase": "yesterday_consumption_phase",
    "edf_freephase_dynamic_tariff_yesterday_consumption_phase": "yesterday_consumption_phase",

    "today_cost_slots": "today_cost_slots",
    "edf_freephase_dynamic_tariff_today_cost_slots": "today_cost_slots",

    "yesterday_cost_slots": "yesterday_cost_slots",
    "edf_freephase_dynamic_tariff_yesterday_cost_slots": "yesterday_cost_slots",

    # -----------------------------------------------------------------------
    # Phase summaries (rates → phases)
    # -----------------------------------------------------------------------
    "today_phases_summary": "today_phases_summary",
    "tomorrow_phases_summary": "tomorrow_phases_summary",
    "yesterday_phases_summary": "yesterday_phases_summary",

    # Fix HA’s old apostrophe-slugified object_ids
    "today_s_phases_summary": "today_phases_summary",
    "tomorrow_s_phases_summary": "tomorrow_phases_summary",
    "yesterday_s_phases_summary": "yesterday_phases_summary",

    # -----------------------------------------------------------------------
    # Slot/phase sensors
    # -----------------------------------------------------------------------
    "current_slot_colour": "current_slot_colour",
    "edf_freephase_dynamic_tariff_current_slot_colour": "current_slot_colour",

    "current_block_summary": "current_phase_summary",
    "edf_freephase_dynamic_tariff_current_block_summary": "current_phase_summary",

    "next_block_summary": "next_phase_summary",
    "edf_freephase_dynamic_tariff_next_block_summary": "next_phase_summary",

    # -----------------------------------------------------------------------
    # Next-phase slot sensors
    #
    # These are the ones that were reverting to:
    #   sensor.next_green_slot
    #   sensor.next_amber_slot
    #   sensor.next_red_slot
    #
    # We normalise both the short and legacy long object_ids to the
    # canonical "next_{colour}_slot" and then let build_entity_id()
    # apply the edf_fpd_* prefix.
    # -----------------------------------------------------------------------
    "next_green_slot": "next_green_slot",
    "edf_freephase_dynamic_tariff_next_green_slot": "next_green_slot",

    "next_amber_slot": "next_amber_slot",
    "edf_freephase_dynamic_tariff_next_amber_slot": "next_amber_slot",

    "next_red_slot": "next_red_slot",
    "edf_freephase_dynamic_tariff_next_red_slot": "next_red_slot",

    # -----------------------------------------------------------------------
    # Standing charge
    #
    # Also one of the reverting entities: sensor.standing_charge
    # -----------------------------------------------------------------------
    "standing_charge": "standing_charge",
    "edf_freephase_dynamic_tariff_standing_charge": "standing_charge",

    # -----------------------------------------------------------------------
    # Diagnostic sensors
    # -----------------------------------------------------------------------
    "last_updated": "last_updated",
    "api_latency": "api_latency",
    "coordinator_status": "coordinator_status",
    "cost_coordinator_status": "cost_coordinator_status",
    "next_refresh_time": "next_refresh_time",
    "tariff_metadata": "tariff_metadata",

    "diagnostic_sensor": "diagnostic_sensor",
    "edf_freephase_dynamic_tariff_edf_fpd_diagnostic_sensor": "diagnostic_sensor",

    # -----------------------------------------------------------------------
    # Binary sensors
    # -----------------------------------------------------------------------
    "is_green_slot": "is_green_slot",
    "edf_freephase_dynamic_tariff_is_green_slot": "is_green_slot",

    # -----------------------------------------------------------------------
    # Event entity
    # -----------------------------------------------------------------------
    "tariff_slot_phase_events": "phase_events",
    "edf_freephase_dynamic_tariff_edf_fpd_phase_events": "phase_events",

    # -----------------------------------------------------------------------
    # Switch
    # -----------------------------------------------------------------------
    "debug_logging": "debug_logging",
    "edf_freephase_dynamic_tariff_debug_logging": "debug_logging",
}

# ---------------------------------------------------------------------------
# Mapping of old friendly names → new friendly names
#
# Keys here are *friendly names* (entity.original_name / entity.name),
# NOT object_ids. Values are the new canonical friendly names.
# ---------------------------------------------------------------------------

FRIENDLY_NAME_MIGRATIONS = {
    # -----------------------------------------------------------------------
    # Phase summaries
    # -----------------------------------------------------------------------
    "EDF FPD Today’s Phases Summary": "EDF FPD Today Phases Summary",
    "EDF FPD Tomorrow’s Phases Summary": "EDF FPD Tomorrow Phases Summary",
    "EDF FPD Yesterday’s Phases Summary": "EDF FPD Yesterday Phases Summary",

    # -----------------------------------------------------------------------
    # Cost & consumption
    # -----------------------------------------------------------------------
    "EDF FreePhase Dynamic Tariff EDF FPD Today Cost (Phase)": "EDF FPD Today Cost (Phase)",
    "EDF FreePhase Dynamic Tariff EDF FPD Yesterday Cost (Phase)": "EDF FPD Yesterday Cost (Phase)",
    "EDF FreePhase Dynamic Tariff EDF FPD Today Consumption (Phase)": "EDF FPD Today Consumption (Phase)",
    "EDF FreePhase Dynamic Tariff EDF FPD Yesterday Consumption (Phase)": "EDF FPD Yesterday Consumption (Phase)",
    "EDF FreePhase Dynamic Tariff EDF FPD Today Cost (Slots)": "EDF FPD Today Cost (Slots)",
    "EDF FreePhase Dynamic Tariff EDF FPD Yesterday Cost (Slots)": "EDF FPD Yesterday Cost (Slots)",

    # -----------------------------------------------------------------------
    # Next {Colour} Slot — bare legacy names
    # -----------------------------------------------------------------------
    "Next Green Slot": "EDF FPD Next Green Slot",
    "Next Amber Slot": "EDF FPD Next Amber Slot",
    "Next Red Slot": "EDF FPD Next Red Slot",

    # -----------------------------------------------------------------------
    # Standing charge
    # -----------------------------------------------------------------------
    "EDF FreePhase Dynamic Tariff EDF FPD Standing Charge": "EDF FPD Standing Charge",

    # -----------------------------------------------------------------------
    # Diagnostic
    # -----------------------------------------------------------------------
    "EDF FreePhase Dynamic Tariff EDF FPD Diagnostic Sensor": "EDF FPD Diagnostic Sensor",

    # -----------------------------------------------------------------------
    # Event entity
    # -----------------------------------------------------------------------
    "EDF FreePhase Dynamic Tariff EDF FPD Phase Events": "EDF FPD Phase Events",
}

# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

async def async_migrate_entity_ids(hass, entry):
    """
    Rewrite old entity_ids AND old friendly names to the new format.

    Safe to run multiple times (idempotent).
    """

    registry: EntityRegistry = async_get_entity_registry(hass)

    for entity_id, entity in list(registry.entities.items()):
        if entity.config_entry_id != entry.entry_id:
            continue

        # Current object_id and friendly name
        old_object_id = entity_id.split(".")[1]
        old_name = entity.original_name or entity.name

        # -----------------------------
        # 1. ENTITY ID MIGRATION
        # -----------------------------
        if old_object_id in ENTITY_ID_MIGRATIONS:
            new_object_id = ENTITY_ID_MIGRATIONS[old_object_id]

            new_entity_id = build_entity_id(
                domain=entity.domain,
                object_id=new_object_id,
                tariff="fpd",
            )

            if new_entity_id != entity_id:
                registry.async_update_entity(entity_id, new_entity_id=new_entity_id)

        # -----------------------------
        # 2. FRIENDLY NAME MIGRATION
        # -----------------------------
        if old_name in FRIENDLY_NAME_MIGRATIONS:
            new_name = FRIENDLY_NAME_MIGRATIONS[old_name]
            registry.async_update_entity(entity_id, name=new_name)
