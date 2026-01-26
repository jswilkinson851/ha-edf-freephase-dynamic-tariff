"""
Diagnostic and metadata sensor entities for the EDF FreePhase Dynamic Tariff
integration.

This module exposes a suite of read‑only sensors designed to provide visibility
into the integration’s internal state, timing behaviour, API performance, and
tariff metadata. These sensors do not represent user‑facing tariff values; they
exist to support debugging, monitoring, and long‑term reliability.

All sensors inherit from CoordinatorEntity so they update automatically whenever
the coordinator refreshes. Device metadata is provided via `edf_device_info()`
to ensure all entities group cleanly under a single device in the Home Assistant
UI.

Sensors included in this module:

1. EDFFreePhaseDynamicLastUpdatedSensor
   - Shows when the API data was last updated.
   - Exposes raw timestamps and age calculations.

2. EDFFreePhaseDynamicAPILatencySensor
   - Reports API response latency in milliseconds.
   - Useful for diagnosing network or upstream performance issues.

3. EDFFreePhaseDynamicCoordinatorStatusSensor
   - Surfaces the coordinator’s strict heartbeat state and all boolean health
     flags (API errors, metadata issues, stale data, scheduler alignment, etc.).

4. EDFFreePhaseDynamicNextRefreshSensor
   - Shows the next scheduled refresh time and internal scheduler parameters
     (delay, jitter, aligned boundaries).

5. EDFFreePhaseDynamicTariffMetadataSensor
   - Exposes full tariff metadata returned by the EDF product endpoint.
   - Useful for verifying region mappings and tariff correctness.

6. EDFFreePhaseDynamicTariffDiagnosticSensor
   - A consolidated “black box recorder” exposing coordinator health, timing,
     metadata, and slot context in a single structured entity.

These sensors are intended for advanced users, developers, and diagnostic
dashboards. They provide transparency into the integration’s behaviour without
requiring access to logs or developer tools.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

# pylint: disable=import-error
from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.entity import EntityCategory  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]
from homeassistant.util.dt import as_local, parse_datetime  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from ..const import DOMAIN
from ..helpers import edf_device_info

_LOGGER = logging.getLogger(__name__)


def _format_timestamp(ts: str | None):
    """
    Convert an ISO‑8601 timestamp into a human‑readable local time string.

    The coordinator stores timestamps in ISO format. This helper normalises the
    value into the user's local timezone and formats it as:

        "HH:MM on DD/MM/YYYY"

    Returns None if the timestamp is missing or cannot be parsed.
    """

    if not ts:
        return None

    dt = parse_datetime(ts)
    if not dt:
        return None

    dt = as_local(dt)
    return dt.strftime("%H:%M on %d/%m/%Y")


# ---------------------------------------------------------------------------
# Last Updated Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicLastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing when the coordinator last received valid data from the API.

    The entity’s state is a formatted timestamp representing the most recent
    successful update. Attributes include:
    - The raw ISO timestamp.
    - A human‑readable formatted version.
    - The age of the data in seconds.

    This sensor is useful for diagnosing stale data, scheduler issues, or API
    outages.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Last Updated"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_last_updated"
        self._attr_icon = "mdi:update"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the formatted last-updated timestamp."""
        data = self.coordinator.data or {}
        return _format_timestamp(data.get("last_updated"))

    @property
    def extra_state_attributes(self):
        """Expose raw timestamp and age in seconds."""
        data = self.coordinator.data or {}
        ts = data.get("last_updated")
        if not ts:
            return {}

        dt = parse_datetime(ts)
        if dt:
            dt = as_local(dt)
            age_seconds = (datetime.now(timezone.utc).astimezone() - dt).total_seconds()
        else:
            age_seconds = None

        return {
            "raw_timestamp": ts,
            "formatted": _format_timestamp(ts),
            "age_seconds": age_seconds,
            "icon": "mdi:update",
        }

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# API Latency Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicAPILatencySensor(CoordinatorEntity, SensorEntity):
    """
    Sensor reporting the API response latency for the most recent refresh.

    The entity’s state is the latency in milliseconds. Attributes expose both
    milliseconds and seconds for convenience.

    This sensor helps diagnose slow upstream responses, network congestion, or
    intermittent API performance issues.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "API Latency"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_api_latency"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_icon = "mdi:speedometer"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the API latency in milliseconds."""
        data = self.coordinator.data or {}
        return data.get("api_latency_ms")

    @property
    def extra_state_attributes(self):
        """Expose latency in both milliseconds and seconds."""
        data = self.coordinator.data or {}
        latency = data.get("api_latency_ms")
        if latency is None:
            return {}

        return {
            "latency_ms": latency,
            "latency_seconds": latency / 1000,
            "icon": "mdi:speedometer",
        }

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# EDF Coordinator Status Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCoordinatorStatusSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the coordinator’s strict heartbeat status and health flags.

    The entity’s state is a severity‑ordered status string (e.g., "ok",
    "api_error", "no_data", "stale", "partial"). Attributes expose the full set
    of boolean heartbeat flags, including:

    - API errors
    - Metadata errors
    - Scheduler alignment issues
    - Rate‑limit detection
    - Import sensor availability
    - Parsing and format errors
    - Staleness and partial‑data conditions

    This sensor provides a structured, machine‑readable view of the
    coordinator’s internal health model.
    """

    def __init__(self, coordinator):
        """Initialize the coordinator status sensor."""
        super().__init__(coordinator)
        self._attr_name = "Coordinator Status"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_coordinator_status"
        self._attr_icon = "mdi:heart-pulse"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the coordinator status string."""
        data = self.coordinator.data or {}
        return data.get("coordinator_status")

    @property
    def extra_state_attributes(self):
        """
        Expose a human‑readable health model for the EDFCoordinator.

        This replaces boolean error flags with descriptive health states such as:
            - "healthy"
            - "error"
            - "missing"
            - "unavailable"
            - "limited"

        It also exposes tariff‑slot availability for yesterday, today, and tomorrow.
        """
        data = self.coordinator.data or {}

        # Tariff availability
        yesterday_slots = data.get("yesterday_24_hours") or []
        today_slots = data.get("today_24_hours") or []
        tomorrow_slots = data.get("tomorrow_24_hours") or []

        # Helper to convert boolean error flags into readable health states
        def _health(flag, bad: str = "error"):
            return bad if bool(flag) else "healthy"

        # Import sensor health is a tri‑state
        if data.get("import_sensor_missing"):
            import_sensor_health = "missing"
        elif data.get("import_sensor_unavailable"):
            import_sensor_health = "unavailable"
        else:
            import_sensor_health = "healthy"

        # Rate‑limit health
        rate_limit_health = "limited" if data.get("rate_limited") else "healthy"

        return {
            "last_updated": data.get("last_updated"),
            "api_latency_ms": data.get("api_latency_ms"),
            # Health model (replaces boolean error flags)
            "api_health": _health(data.get("api_error")),
            "metadata_health": _health(data.get("metadata_error")),
            "parsing_health": _health(data.get("parsing_error")),
            "format_health": _health(data.get("unexpected_format")),
            "scheduler_health": _health(data.get("scheduler_error")),
            "import_sensor_health": import_sensor_health,
            "rate_limit_health": rate_limit_health,
            "stale_health": _health(data.get("stale"), bad="stale"),
            "partial_health": _health(data.get("partial"), bad="partial"),
            # Tariff availability
            "yesterday_available": len(yesterday_slots) > 0,
            "today_available": len(today_slots) > 0,
            "tomorrow_available": len(tomorrow_slots) > 0,
            # Debug
            "debug_counter": data.get("debug_counter"),
        }

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Cost Coordinator Status Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCostCoordinatorStatusSensor(SensorEntity):
    """
    Diagnostic sensor exposing the internal health state of the CostCoordinator.

    This entity provides a structured, human‑readable view of the cost‑pipeline
    lifecycle. It replaces boolean error flags with descriptive health states
    such as "healthy", "missing", "no_deltas", "partial", and "error".

    The sensor reports:
        • health of history retrieval
        • health of delta computation
        • partial‑data conditions
        • error conditions
        • import sensor availability
        • availability of yesterday/today cost summaries
        • debug counter for tracing coordinator cycles
    """

    _attr_name = "Cost Coordinator Status"
    _attr_icon = "mdi:chart-line"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, _, cost_coordinator):
        """
        Initialise the CostCoordinator heartbeat sensor.

        Parameters
        ----------
        _ : Any
            Unused placeholder for EDFCoordinator, required to match the
            integration’s universal sensor‑instantiation signature.
        cost_coordinator : CostCoordinator
            The coordinator responsible for computing cost and consumption
            summaries. Its `.data` dictionary is the source of all state and
            attributes exposed by this sensor.
        """
        self.coordinator = cost_coordinator
        self.entry = cost_coordinator.config_entry
        self._attr_unique_id = f"{self.entry.entry_id}_cost_coordinator_status"

    @property
    def device_info(self):
        """Return device metadata linking this sensor to the integration’s main device."""
        return edf_device_info(self.entry.entry_id)

    @property
    def native_value(self):
        """
        Return the primary cost‑pipeline status string.

        The value is derived from flags stored in the CostCoordinator’s `.data`
        dictionary and reflects the most severe condition detected during the
        most recent refresh cycle.
        """
        data = self.coordinator.data or {}

        if not data:
            return "initialising"
        if data.get("error"):
            return "error"
        if data.get("history_missing"):
            return "history_missing"
        if data.get("no_deltas"):
            return "no_deltas"
        if data.get("partial"):
            return "partial"

        return "healthy"

    @property
    def extra_state_attributes(self):
        """
        Expose a human‑readable health model for the CostCoordinator.

        This replaces boolean error flags with descriptive health states such as:
            - "healthy"
            - "missing"
            - "no_deltas"
            - "partial"
            - "error"

        It also exposes availability of yesterday/today cost summaries and
        the import sensor used for cost computation.
        """
        data = self.coordinator.data or {}

        # Helper to convert truthy/falsy flags into readable health states
        def _health(flag, bad: str = "error"):
            return bad if bool(flag) else "healthy"

        # Import sensor health (tri‑state)
        if data.get("import_sensor") is None:
            import_sensor_health = "missing"
        else:
            import_sensor_health = "healthy"

        return {
            "last_updated": data.get("last_updated"),
            "debug_counter": getattr(self.coordinator, "debug_counter", None),
            # Health model (replaces boolean flags)
            "history_health": _health(data.get("history_missing"), bad="missing"),
            "delta_health": _health(data.get("no_deltas"), bad="no_deltas"),
            "partial_health": _health(data.get("partial"), bad="partial"),
            "error_health": _health(data.get("error"), bad="error"),
            "import_sensor_health": import_sensor_health,
            # Availability of computed summaries
            "yesterday_available": data.get("yesterday") is not None,
            "today_available": data.get("today") is not None,
        }


# ---------------------------------------------------------------------------
# Next Refresh Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicNextRefreshSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the next scheduled refresh time for the coordinator.

    The entity’s state is a formatted timestamp representing the next refresh.
    Attributes expose internal scheduler parameters, including:

    - The raw datetime of the next refresh.
    - The aligned boundary used for half‑hour slot scheduling.
    - The computed delay until the next refresh.
    - The jitter applied to avoid thundering‑herd behaviour.
    - The configured scan interval (in minutes).

    This sensor is primarily intended for debugging the aligned scheduler and
    verifying that refresh timing behaves as expected.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Refresh Time"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_refresh_time"
        self._attr_icon = "mdi:clock-start"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the next refresh time as a formatted string."""
        dt = self.coordinator._next_refresh_datetime  # pylint: disable=protected-access
        if not dt:
            return None
        return dt.astimezone().strftime("%H:%M:%S on %d/%m/%Y")

    @property
    def extra_state_attributes(self):
        """Expose detailed scheduling attributes."""
        return {
            "next_refresh_datetime": (
                self.coordinator._next_refresh_datetime.isoformat() if self.coordinator._next_refresh_datetime else None  # pylint: disable=protected-access disable=line-too-long
            ),
            "aligned_boundary_utc": (
                self.coordinator._next_boundary_utc.isoformat() if self.coordinator._next_boundary_utc else None  # pylint: disable=protected-access disable=line-too-long
            ),
            "seconds_until_refresh": self.coordinator._next_refresh_delay,  # pylint: disable=protected-access
            "jitter_seconds": self.coordinator._next_refresh_jitter,  # pylint: disable=protected-access
            # Using coordinator._scan_interval because update_interval is disabled for aligned scheduling # pylint: disable=line-too-long
            "scan_interval_minutes": (
                self.coordinator._scan_interval.total_seconds() / 60  # pylint: disable=protected-access
                if getattr(self.coordinator, "_scan_interval", None)
                else None
            ),
        }

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Tariff Metadata Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicTariffMetadataSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing full tariff metadata returned by the EDF product endpoint.

    The entity’s state is a human‑readable summary (e.g., product name and
    region). Attributes expose the complete metadata dictionary, allowing
    dashboards and developers to inspect:

    - Product identifiers
    - Region mappings
    - Display names
    - Contract details
    - Any additional metadata fields returned by the API

    This sensor is useful for verifying tariff correctness and diagnosing region
    mismatches.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tariff Metadata"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_metadata"
        self._attr_icon = "mdi:information-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Human-readable summary."""
        data = self.coordinator.data or {}
        meta = data.get("tariff_metadata") or {}

        # TEMP DEBUG: Inspect what the sensor is actually receiving
        # _LOGGER.warning("META SENSOR DEBUG: %s", meta)

        display = meta.get("display_name") or meta.get("full_name") or meta.get("product_name")
        region = meta.get("region_label")

        if display and region:
            return f"{display} — {region}"
        if display:
            return display
        return "Tariff Metadata"

    @property
    def extra_state_attributes(self):
        """Expose full product metadata."""
        data = self.coordinator.data or {}
        meta = data.get("tariff_metadata") or {}

        return {k: v for k, v in meta.items() if v is not None}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Tariff Diagnostic Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicTariffDiagnosticSensor(CoordinatorEntity, SensorEntity):
    """
    Diagnostic sensor for the EDF FreePhase Dynamic Tariff integration.

    This entity exposes a consolidated, read‑only diagnostic view of the
    coordinator’s internal state. It is designed to give users, developers, and
    Home Assistant itself a clear understanding of the integration’s health,
    timing, and data‑quality characteristics without requiring access to logs or
    developer tools.

    Overview
    --------
    The diagnostic sensor surfaces both high‑level and low‑level information
    generated by the EDFCoordinator, including:

    1. **Heartbeat State**
    - The coordinator’s strict health status (e.g., "ok", "api_error",
        "no_data", "stale", "partial", etc.), derived from a severity‑ordered
        priority model.
    - Flat boolean flags for every subsystem (API, metadata, scheduler,
        parsing, rate‑limit detection, import sensor availability, etc.).

    2. **Timing & Scheduling**
    - Last successful update timestamp.
    - API latency for the most recent refresh.
    - Next scheduled refresh time, delay, and jitter (mirroring the aligned
        scheduler’s internal state).

    3. **Tariff Metadata**
    - Region‑specific tariff information extracted from the EDF product
        endpoint.
    - Useful for debugging region mismatches or unexpected tariff behaviour.

    4. **Current & Next Slot Context**
    - The normalised current pricing slot.
    - The next upcoming slot.
    - Current and next phase‑block summaries.

    Purpose
    -------
    This sensor is intentionally diagnostic‑only. It does not represent a
    user‑facing tariff value; instead, it provides transparency into the
    integration’s operation and is intended for:

    - Troubleshooting API failures or stale data.
    - Verifying scheduler alignment and jitter behaviour.
    - Confirming metadata correctness.
    - Building advanced dashboards or developer‑oriented monitoring views.
    - Supporting future automated health checks or notifications.

    The diagnostic sensor does not perform any computation itself. All values are
    directly sourced from the coordinator’s data dictionary, ensuring that the
    sensor always reflects the coordinator’s true internal state.

    In summary, this entity acts as the integration’s “black box recorder”,
    exposing a complete, structured snapshot of coordinator health and timing to
    assist with debugging, monitoring, and long‑term reliability.
    """

    _attr_icon = "mdi:information-outline"
    _attr_has_entity_name = True
    _attr_name = "Diagnostic Sensor"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, cost_coordinator):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.cost_coordinator = cost_coordinator
        self.hass = coordinator.hass

        # coordinator.entry must exist — ensure you set coordinator.entry = entry in __init__.py
        self.entry = coordinator.entry

        self._attr_unique_id = f"{self.entry.entry_id}_diagnostics"

    @property
    def native_value(self):
        """Return the coordinator status string."""
        data = self.coordinator.data or {}
        return data.get("coordinator_status", "unknown")

    @property
    def extra_state_attributes(self):
        """Expose detailed diagnostic attributes."""
        data = self.coordinator.data or {}

        version = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get("version", "unknown")  # pylint: disable=line-too-long

        # ------------------------------------------------------------------
        # Event diagnostics (populated by the SlotEventEntity)
        # ------------------------------------------------------------------
        event_diag = self.hass.data.get(DOMAIN, {}).get("event_diagnostics", {})
        entry_diag = event_diag.get(self.entry.entry_id, {})

        event_section = {
            "last_event_type": entry_diag.get("last_event_type"),
            "last_event_timestamp": entry_diag.get("last_event_timestamp"),
            "event_counters": entry_diag.get("event_counts", {}),
            "event_history": entry_diag.get("event_history", []),
        }

        return {
            "integration_version": version,
            "config_entry_title": self.entry.title,
            "debug_logging_enabled": self.coordinator.debug_enabled,
            "tariff_code": self.entry.data.get("tariff_code"),
            "scan_interval": self.entry.data.get("scan_interval"),
            # Coordinator health
            "coordinator_status": data.get("coordinator_status"),
            "cost_coordinator_status": (
                self.cost_coordinator.data.get("coordinator_status") if self.cost_coordinator.data else None  # pylint: disable=line-too-long
            ),
            # Timing
            "api_latency_ms": data.get("api_latency_ms"),
            "last_updated": data.get("last_updated"),
            "next_refresh_datetime": getattr(self.coordinator, "_next_refresh_datetime", None),
            "next_refresh_delay": getattr(self.coordinator, "_next_refresh_delay", None),
            "next_refresh_jitter": getattr(self.coordinator, "_next_refresh_jitter", None),
            # Slot context
            "current_slot": data.get("current_slot"),
            "current_phase_summary": data.get("current_block_summary"),
            "next_phase_summary": data.get("next_block_summary"),
            # Standing charge
            "standing_charge_inc_vat_p_per_day": data.get("standing_charge_inc_vat"),
            "standing_charge_exc_vat_p_per_day": data.get("standing_charge_exc_vat"),
            "standing_charge_valid_from": data.get("standing_charge_valid_from"),
            "standing_charge_valid_to": data.get("standing_charge_valid_to"),
            "standing_charge_raw": data.get("standing_charge_raw"),
            "standing_charge_error": data.get("standing_charge_error"),
            "standing_charge_missing": data.get("standing_charge_missing"),
            # Event entities
            "event_diagnostics": event_section,
            # Debug buffers (10‑message rolling logs)
            "ec_debug_buffer": self.coordinator.debug_buffer,
            "ec_debug_times": self.coordinator.debug_times,
            "cc_debug_buffer": self.cost_coordinator.debug_buffer,
            "cc_debug_times": self.cost_coordinator.debug_times,
        }

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)
