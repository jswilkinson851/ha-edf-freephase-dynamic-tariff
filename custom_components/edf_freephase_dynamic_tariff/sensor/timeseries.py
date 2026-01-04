from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL


class EDFFreePhaseDynamicCurrentPriceTimeseriesSensor(CoordinatorEntity, SensorEntity):
    """Timeseries sensor for current price (for charts and statistics)."""

    _attr_name = "Current Price (Timeseries)"
    _attr_unique_id = "edf_freephase_dynamic_current_price_timeseries"
    _attr_native_unit_of_measurement = "GBP"
    _attr_icon = "mdi:currency-gbp"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("current_price")

    @property
    def extra_state_attributes(self):
        return {
            "last_updated": self.coordinator.data.get("last_updated"),
            "api_latency": self.coordinator.data.get("api_latency"),
        }

    @property
    def device_info(self):
        return edf_device_info()