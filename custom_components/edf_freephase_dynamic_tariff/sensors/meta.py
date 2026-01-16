"""
Metadata sensors such as last-updated time, API latency, coordinator status,
next refresh time, and full tariff metadata.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime, as_local

from .helpers import edf_device_info

_LOGGER = logging.getLogger(__name__)

def _format_timestamp(ts: str | None):
    """Format an ISO timestamp into 'HH:MM on DD/MM/YYYY'."""
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
    """Sensor showing when the API data was last updated."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Last Updated"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_last_updated"
        self._attr_icon = "mdi:update"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return _format_timestamp(data.get("last_updated"))

    @property
    def extra_state_attributes(self):
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
        return edf_device_info()


# ---------------------------------------------------------------------------
# API Latency Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicAPILatencySensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the API response latency."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "API Latency"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_api_latency"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_icon = "mdi:speedometer"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return data.get("api_latency_ms")

    @property
    def extra_state_attributes(self):
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
        return edf_device_info()


# ---------------------------------------------------------------------------
# Coordinator Status Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCoordinatorStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing coordinator health."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Coordinator Status"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_coordinator_status"
        self._attr_icon = "mdi:heart-pulse"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return data.get("coordinator_status")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "last_updated": data.get("last_updated"),
            "api_latency_ms": data.get("api_latency_ms"),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Refresh Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextRefreshSensor(CoordinatorEntity, SensorEntity):
    """Debug sensor showing when the next coordinator refresh is scheduled."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Refresh Time"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_refresh_time"
        self._attr_icon = "mdi:clock-start"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        dt = self.coordinator._next_refresh_datetime
        if not dt:
            return None
        return dt.astimezone().strftime("%H:%M:%S on %d/%m/%Y")

    @property
    def extra_state_attributes(self):
        return {
            "next_refresh_datetime": (
                self.coordinator._next_refresh_datetime.isoformat()
                if self.coordinator._next_refresh_datetime
                else None
            ),
            "aligned_boundary_utc": (
                self.coordinator._next_boundary_utc.isoformat()
                if self.coordinator._next_boundary_utc
                else None
            ),
            "seconds_until_refresh": self.coordinator._next_refresh_delay,
            "jitter_seconds": self.coordinator._next_refresh_jitter,
            # Using coordinator._scan_interval because update_interval is disabled for aligned scheduling
            "scan_interval_minutes": (
                self.coordinator._scan_interval.total_seconds() / 60
                if getattr(self.coordinator, "_scan_interval", None)
                else None
            )
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Tariff Metadata Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTariffMetadataSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor exposing full tariff metadata."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tariff Metadata"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_metadata"
        self._attr_icon = "mdi:information-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        """Human-readable summary."""
        data = self.coordinator.data or {}
        meta = data.get("tariff_metadata") or {}
        
        # TEMP DEBUG: Inspect what the sensor is actually receiving
        _LOGGER.warning("META SENSOR DEBUG: %s", meta)

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
        return edf_device_info()