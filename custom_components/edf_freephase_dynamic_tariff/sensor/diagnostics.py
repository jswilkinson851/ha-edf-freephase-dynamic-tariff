from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL


class EDFFreePhaseAPILastCheckedSensor(CoordinatorEntity, SensorEntity):
    """When the API was last queried."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "API Last Checked"
        self._attr_unique_id = "edf_freephase_api_last_checked"
        self._attr_icon = "mdi:clock-check"

    @property
    def native_value(self):
        return self.coordinator.data.get("last_checked")

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseLastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """When forecast data was last updated."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Data Last Updated"
        self._attr_unique_id = "edf_freephase_data_last_updated"
        self._attr_icon = "mdi:update"

    @property
    def native_value(self):
        return self.coordinator.data.get("last_updated")

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseAPILatencySensor(CoordinatorEntity, SensorEntity):
    """API response latency in milliseconds."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "API Latency"
        self._attr_unique_id = "edf_freephase_api_latency"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self):
        return self.coordinator.data.get("api_latency")

    @property
    def device_info(self):
        return edf_device_info()