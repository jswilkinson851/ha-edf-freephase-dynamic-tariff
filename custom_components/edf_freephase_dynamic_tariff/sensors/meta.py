"""
Metadata sensors such as last-updated time and API latency.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from datetime import datetime, timezone
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime, as_local
from .helpers import edf_device_info


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

    @property
    def native_value(self):
        ts = self.coordinator.data.get("last_updated")
        return _format_timestamp(ts)

    @property
    def extra_state_attributes(self):
        ts = self.coordinator.data.get("last_updated")
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

    @property
    def native_value(self):
        return self.coordinator.data.get("api_latency_ms")

    @property
    def extra_state_attributes(self):
        latency = self.coordinator.data.get("api_latency_ms")
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
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Coordinator Status"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_coordinator_status"
        self._attr_icon = "mdi:heart-pulse"

    @property
    def native_value(self):
        return self.coordinator.data.get("coordinator_status")

    @property
    def extra_state_attributes(self):
        return {
            "last_updated": self.coordinator.data.get("last_updated"),
            "api_latency_ms": self.coordinator.data.get("api_latency_ms"),
        }

    @property
    def device_info(self):
        return edf_device_info()