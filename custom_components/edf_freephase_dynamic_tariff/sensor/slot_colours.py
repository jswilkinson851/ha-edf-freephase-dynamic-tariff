from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL


class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    """Colour of the currently active slot."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"
        self._attr_icon = "mdi:circle-slice-3"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        current = data.get("current_slot")
        return current["phase"] if current else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}

        current = data.get("current_slot")
        return current or {}

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, SensorEntity):
    """Whether the current slot is green."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Is Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        current = data.get("current_slot")
        return current["phase"] == "green" if current else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}

        current = data.get("current_slot")
        return current or {}
    
    @property
    def device_info(self):
        return edf_device_info()