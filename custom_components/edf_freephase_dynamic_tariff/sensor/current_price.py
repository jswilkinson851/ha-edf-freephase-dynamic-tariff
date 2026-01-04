from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL


class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Current unit rate."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_current_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:currency-gbp"

    @property
    def native_value(self):
        return self.coordinator.data.get("current_price")

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseDynamicNextSlotPriceSensor(CoordinatorEntity, SensorEntity):
    """Next half-hour slot price."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Next Slot Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_slot_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get("next_price")

    @property
    def device_info(self):
        return edf_device_info()