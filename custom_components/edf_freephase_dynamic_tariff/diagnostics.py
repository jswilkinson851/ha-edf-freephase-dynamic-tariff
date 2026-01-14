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

    # ---------------------------------------------------------------
    # Coordinator internal fields
    # ---------------------------------------------------------------
    internal = {
        "next_refresh_datetime": getattr(
            coordinator, "_next_refresh_datetime", None
        ),
        "next_refresh_delay": getattr(
            coordinator, "_next_refresh_delay", None
        ),
        "next_refresh_jitter": getattr(
            coordinator, "_next_refresh_jitter", None
        ),
        "scan_interval_seconds": int(
            coordinator._scan_interval.total_seconds()
        ),
    }

    # ---------------------------------------------------------------
    # Raw forecast data
    # ---------------------------------------------------------------
    raw_forecast = {
        "all_slots_sorted": coordinator.data.get("all_slots_sorted"),
        "next_24_hours": coordinator.data.get("next_24_hours"),
        "today_24_hours": coordinator.data.get("today_24_hours"),
        "tomorrow_24_hours": coordinator.data.get("tomorrow_24_hours"),
        "yesterday_24_hours": coordinator.data.get("yesterday_24_hours"),
    }

    # ---------------------------------------------------------------
    # Build phase window breakdowns using unified helpers
    # ---------------------------------------------------------------
    yesterday_slots = coordinator.data.get("yesterday_24_hours") or []
    today_slots = coordinator.data.get("today_24_hours") or []
    tomorrow_slots = coordinator.data.get("tomorrow_24_hours") or []
    next24_slots = coordinator.data.get("next_24_hours") or []

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

    # ---------------------------------------------------------------
    # Classification thresholds (static for now)
    # ---------------------------------------------------------------
    thresholds = {
        "green": "price <= 0 OR 23:00–06:00",
        "amber": "06:00–16:00 and 19:00–23:00",
        "red": "16:00–19:00",
    }

    # ---------------------------------------------------------------
    # Final diagnostics output
    # ---------------------------------------------------------------
    return {
        "config_entry": {
            "title": entry.title,
            "tariff_code": entry.data.get("tariff_code"),
            "scan_interval": entry.data.get("scan_interval"),
        },
        "coordinator_internal": internal,
        "raw_forecast": raw_forecast,
        "phase_windows": diagnostics_phase_windows,
        "classification_thresholds": thresholds,
        "coordinator_status": coordinator.data.get("coordinator_status"),
        "api_latency_ms": coordinator.data.get("api_latency_ms"),
        "last_updated": coordinator.data.get("last_updated"),
    }