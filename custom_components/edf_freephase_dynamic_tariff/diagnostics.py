"""
Diagnostics support for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .sensors.helpers import (
    group_phase_blocks,
    format_phase_block,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
):
    """Return diagnostics for a config entry."""

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return {"error": "Coordinator not found"}

    coordinator = data["coordinator"]
    coord_data = coordinator.data or {}

    # ----------------------------------------------------------------------
    # Internal scheduler state
    # ----------------------------------------------------------------------
    internal = {
        "next_refresh_datetime": getattr(coordinator, "_next_refresh_datetime", None),
        "next_refresh_delay": getattr(coordinator, "_next_refresh_delay", None),
        "next_refresh_jitter": getattr(coordinator, "_next_refresh_jitter", None),
        "scan_interval_seconds": int(coordinator._scan_interval.total_seconds()),
    }

    # ----------------------------------------------------------------------
    # Raw forecast datasets
    # ----------------------------------------------------------------------
    raw_forecast = {
        "all_slots_sorted": coord_data.get("all_slots_sorted"),
        "next_24_hours": coord_data.get("next_24_hours"),
        "today_24_hours": coord_data.get("today_24_hours"),
        "tomorrow_24_hours": coord_data.get("tomorrow_24_hours"),
        "yesterday_24_hours": coord_data.get("yesterday_24_hours"),
    }

    # ----------------------------------------------------------------------
    # Phase windows (grouped blocks)
    # ----------------------------------------------------------------------
    yesterday_slots = coord_data.get("yesterday_24_hours") or []
    today_slots = coord_data.get("today_24_hours") or []
    tomorrow_slots = coord_data.get("tomorrow_24_hours") or []
    next24_slots = coord_data.get("next_24_hours") or []

    diagnostics_phase_windows = {
        "yesterday_phase_windows": [
            format_phase_block(block)
            for block in group_phase_blocks(yesterday_slots)
        ],
        "today_phase_windows": [
            format_phase_block(block)
            for block in group_phase_blocks(today_slots)
        ],
        "tomorrow_phase_windows": [
            format_phase_block(block)
            for block in group_phase_blocks(tomorrow_slots)
        ],
        "next_24_hours_phase_windows": [
            format_phase_block(block)
            for block in group_phase_blocks(next24_slots)
        ],
    }

    # ----------------------------------------------------------------------
    # Classification thresholds (static)
    # ----------------------------------------------------------------------
    thresholds = {
        "green": "price <= 0 OR 23:00–06:00",
        "amber": "06:00–16:00 and 19:00–23:00",
        "red": "16:00–19:00",
    }

    # ----------------------------------------------------------------------
    # Final diagnostics structure
    # ----------------------------------------------------------------------
    return {
        "config_entry": {
            "title": entry.title,
            "tariff_code": entry.data.get("tariff_code"),
            "scan_interval": entry.data.get("scan_interval"),
            "tariff_region_label": entry.data.get("tariff_region_label"),
            "product_url": data.get("product_url"),
            "api_url": data.get("api_url"),
        },
        "coordinator_internal": internal,
        "coordinator_status": coord_data.get("coordinator_status"),
        "api_latency_ms": coord_data.get("api_latency_ms"),
        "last_updated": coord_data.get("last_updated"),

        # NEW: extremely useful for debugging
        "current_slot": coord_data.get("current_slot"),
        "current_block_summary": coord_data.get("current_block_summary"),
        "next_block_summary": coord_data.get("next_block_summary"),

        # Forecasts + phase windows
        "raw_forecast": raw_forecast,
        "phase_windows": diagnostics_phase_windows,
        "classification_thresholds": thresholds,

        # NEW: full tariff metadata (cleaned + region label)
        "tariff_metadata": coord_data.get("tariff_metadata"),
    }