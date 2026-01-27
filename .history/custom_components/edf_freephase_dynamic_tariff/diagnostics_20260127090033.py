"""
Diagnostics support for the EDF FreePhase Dynamic Tariff integration.

This module provides the structured diagnostics payload returned when a user
requests diagnostics for a config entry via Home Assistant’s built‑in
diagnostics system. The goal is to surface all relevant internal state needed
to understand how the integration is behaving, without exposing sensitive
information or overwhelming the user with raw coordinator internals.

The diagnostics output is intentionally comprehensive and includes:

1. Integration metadata
   Extracted from the integration manifest, including the installed version.
   This helps users and maintainers confirm which release is generating the
   diagnostics bundle.

2. Config entry details
   The user‑selected tariff code, region label, scan interval, and the API
   endpoints being used. This section reflects the configuration stored in
   `entry.data` and is useful for verifying that the integration is using the
   expected tariff and region.

3. Coordinator internal state
   Low‑level scheduler information such as the next refresh timestamp, jitter,
   and the effective scan interval. These values help diagnose timing issues,
   API throttling, or unexpected refresh behaviour.

4. Raw forecast datasets
   The unprocessed slot/phase data returned by EDF’s API, including:
       • all_slots_sorted
       • yesterday/today/tomorrow 24‑hour windows
       • next 24‑hour forecast
   These datasets form the basis for all slot/phase logic in the integration.

5. Phase windows (grouped blocks)
   Human‑readable representations of merged phase blocks (green/amber/red)
   generated via `group_phase_blocks()` and `format_phase_block()`. This helps
   users and maintainers verify that the integration is correctly interpreting
   EDF’s half‑hourly data into meaningful phase windows.

6. Classification thresholds
   The static rules used to classify slots into green/amber/red phases. These
   are included for transparency and to help users understand how the
   integration interprets EDF’s pricing structure.

7. Coordinator status and debug buffers
   Includes:
       • coordinator_status (EC)
       • cost_coordinator_status (CC)
       • debug buffers and timestamps for both coordinators
   These values are essential when diagnosing API failures, timing issues, or
   unexpected slot/phase transitions.

8. Slot and block summaries
   High‑level summaries of the current and next phase blocks, as computed by
   the coordinator. These help confirm that the integration’s internal state
   matches what the user sees in the UI.

9. Tariff metadata
   Any tariff‑level metadata returned by EDF’s API, such as product details or
   pricing structures.

10. Standing charge diagnostics
    A detailed breakdown of the standing charge information returned by the
    API, including:
        • inc/exc VAT values
        • validity windows
        • raw API payload
        • error/missing flags
    This section helps diagnose issues where EDF’s metadata is incomplete or
    inconsistent.

The diagnostics payload is designed to be stable, structured, and safe to
share when reporting issues. It provides a complete snapshot of the
integration’s runtime state without exposing credentials or sensitive user
data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
from collections import deque
from datetime import datetime, timezone

# pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]
from homeassistant.loader import async_get_integration  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .const import DOMAIN
from .helpers import (
    group_phase_blocks,
    format_phase_block,
)

class StandingChargeDiagnostics(TypedDict, total=False):
    """Diagnostics structure for standing charge information."""

    inc_vat_p_per_day: Optional[float]
    exc_vat_p_per_day: Optional[float]
    valid_from: Optional[str]
    valid_to: Optional[str]
    raw: Any
    error: Any
    missing: Any

# ----------------------------------------------------------------------
# Event diagnostics (history + last event)
# ----------------------------------------------------------------------

class EventDiagnostics:
    """Diagnostics helper for event entities (slot/phase transitions)."""

    def __init__(self, hass, entry_id: str, event_types: list[str]):
        self.hass = hass
        self.entry_id = entry_id
        self.event_types = event_types

        # Last event info
        self._last_event_type: str | None = None
        self._last_event_timestamp: str | None = None

        # Rolling history (last 20 events)
        self._history = deque(maxlen=20)

        # Event counts
        self._event_counts = {etype: 0 for etype in event_types}

    def record(self, event_type: str, payload: dict | None = None):
        """Record an event occurrence and update history."""
        now = datetime.now(timezone.utc).isoformat()

        self._last_event_type = event_type
        self._last_event_timestamp = now
        self._event_counts[event_type] += 1

        self._history.append(
            {
                "timestamp": now,
                "event_type": event_type,
                "payload": payload,
            }
        )

    def get(self) -> dict:
        """Return diagnostics snapshot."""
        return {
            "last_event_type": self._last_event_type,
            "last_event_timestamp": self._last_event_timestamp,
            "event_counts": self._event_counts,
            "event_history": list(self._history),
        }

class CoordinatorInternalDiagnostics(TypedDict, total=False):
    """Diagnostics structure for internal coordinator scheduling state."""

    next_refresh_datetime: Optional[str]
    next_refresh_delay: Optional[float]
    next_refresh_jitter: Optional[float]
    scan_interval_seconds: int


class ForecastDiagnostics(TypedDict, total=False):
    """Diagnostics structure for raw forecast datasets."""

    all_slots_sorted: Any
    next_24_hours: Any
    today_24_hours: Any
    tomorrow_24_hours: Any
    yesterday_24_hours: Any


class PhaseWindowDiagnostics(TypedDict, total=False):
    """Diagnostics structure for grouped phase windows."""

    yesterday_phase_windows: List[Any]
    today_phase_windows: List[Any]
    tomorrow_phase_windows: List[Any]
    next_24_hours_phase_windows: List[Any]


class IntegrationDiagnostics(TypedDict, total=False):
    """Top-level diagnostics structure for the integration."""

    integration: Dict[str, Any]
    config_entry: Dict[str, Any]
    coordinator_internal: CoordinatorInternalDiagnostics
    coordinator_status: Any
    cost_coordinator_status: Any
    api_latency_ms: Optional[int]
    last_updated: Optional[str]
    ec_debug_buffer: List[Any]
    ec_debug_times: List[Any]
    cc_debug_buffer: List[Any]
    cc_debug_times: List[Any]
    current_slot: Any
    current_block_summary: Any
    next_block_summary: Any
    raw_forecast: ForecastDiagnostics
    phase_windows: PhaseWindowDiagnostics
    classification_thresholds: Dict[str, str]
    tariff_metadata: Any
    standing_charge: StandingChargeDiagnostics


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> Dict[str, Any]:
    """Return diagnostics for a config entry."""

    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return {"error": "Coordinator not found"}

    coordinator = data["coordinator"]
    coord_data: Dict[str, Any] = coordinator.data or {}

    # ----------------------------------------------------------------------
    # Internal scheduler state
    # ----------------------------------------------------------------------
    internal: CoordinatorInternalDiagnostics = {
        "next_refresh_datetime": getattr(coordinator, "_next_refresh_datetime", None),
        "next_refresh_delay": getattr(coordinator, "_next_refresh_delay", None),
        "next_refresh_jitter": getattr(coordinator, "_next_refresh_jitter", None),
        # Coordinator exposes _scan_interval by design; safe to read for diagnostics.
        "scan_interval_seconds": int(coordinator._scan_interval.total_seconds()),  # pylint: disable=protected-access
    }

    # ----------------------------------------------------------------------
    # Raw forecast datasets
    # ----------------------------------------------------------------------
    raw_forecast: ForecastDiagnostics = {
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

    diagnostics_phase_windows: PhaseWindowDiagnostics = {
        "yesterday_phase_windows": [
            format_phase_block(block) for block in group_phase_blocks(yesterday_slots)
        ],
        "today_phase_windows": [
            format_phase_block(block) for block in group_phase_blocks(today_slots)
        ],
        "tomorrow_phase_windows": [
            format_phase_block(block) for block in group_phase_blocks(tomorrow_slots)
        ],
        "next_24_hours_phase_windows": [
            format_phase_block(block) for block in group_phase_blocks(next24_slots)
        ],
    }

    # ----------------------------------------------------------------------
    # Classification thresholds (static)
    # ----------------------------------------------------------------------
    thresholds: Dict[str, str] = {
        "green": "price <= 0 OR 23:00–06:00",
        "amber": "06:00–16:00 and 19:00–23:00",
        "red": "16:00–19:00",
    }

    # ----------------------------------------------------------------------
    # Integration metadata (version from manifest.json)
    # ----------------------------------------------------------------------
    try:
        integration = await async_get_integration(hass, DOMAIN)
        version = getattr(integration, "version", "unknown")
    except Exception:  # pylint: disable=broad-except
        version = "unknown"

    # ----------------------------------------------------------------------
    # Standing charge diagnostics
    # ----------------------------------------------------------------------
    standing_charge: StandingChargeDiagnostics = {
        "inc_vat_p_per_day": coord_data.get("standing_charge_inc_vat"),
        "exc_vat_p_per_day": coord_data.get("standing_charge_exc_vat"),
        "valid_from": coord_data.get("standing_charge_valid_from"),
        "valid_to": coord_data.get("standing_charge_valid_to"),
        "raw": coord_data.get("standing_charge_raw"),
        "error": coord_data.get("standing_charge_error"),
        "missing": coord_data.get("standing_charge_missing"),
    }

    # ----------------------------------------------------------------------
    # Final diagnostics structure
    # ----------------------------------------------------------------------
    diagnostics: IntegrationDiagnostics = {
        "integration": {
            "version": version,
        },
        "config_entry": {
            "title": entry.title,
            "tariff_code": entry.data.get("tariff_code"),
            "tariff_region_label": entry.data.get("tariff_region_label"),
            "scan_interval": entry.data.get("scan_interval"),
            "product_url": data.get("product_url"),
            "api_url": data.get("api_url"),
        },

        # Coordinator internal state
        "coordinator_internal": internal,

        # Coordinator status (EC + CC)
        "coordinator_status": coord_data.get("coordinator_status"),
        "cost_coordinator_status": (
            data.get("cost_coordinator").data.get("coordinator_status")
            if data.get("cost_coordinator") and data.get("cost_coordinator").data
            else None
        ),

        # Timing + metadata
        "api_latency_ms": coord_data.get("api_latency_ms"),
        "last_updated": coord_data.get("last_updated"),

        # Debug buffers (EC + CC)
        "ec_debug_buffer": getattr(coordinator, "debug_buffer", []),
        "ec_debug_times": getattr(coordinator, "debug_times", []),
        "cc_debug_buffer": getattr(data.get("cost_coordinator"), "debug_buffer", []),
        "cc_debug_times": getattr(data.get("cost_coordinator"), "debug_times", []),

        # Slot + block summaries
        "current_slot": coord_data.get("current_slot"),
        "current_block_summary": coord_data.get("current_block_summary"),
        "next_block_summary": coord_data.get("next_block_summary"),

        # Forecasts + phase windows
        "raw_forecast": raw_forecast,
        "phase_windows": diagnostics_phase_windows,

        # Classification thresholds
        "classification_thresholds": thresholds,

        # Tariff metadata
        "tariff_metadata": coord_data.get("tariff_metadata"),

        # Standing charge diagnostics
        "standing_charge": standing_charge,
    }

    # We return a plain dict for Home Assistant, but the structure is fully typed.
    return dict(diagnostics)

# End of diagnostics payload