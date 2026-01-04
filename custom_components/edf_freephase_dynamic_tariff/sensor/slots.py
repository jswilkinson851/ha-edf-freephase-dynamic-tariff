from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL


class EDFFreePhaseDynamicNextGreenSlotSensor(CoordinatorEntity, SensorEntity):
    """Next green slot in the forecast."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Next Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_green_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:leaf"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "green":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "green":
                return {
                    "start": slot["start"],
                    "end": slot["end"],
                    "value": slot["value"],
                    "phase": slot["phase"],
                    "next_slot_start": slot["start"],
                }
        return {}

    @property
    def device_info(self):
        return edf_device_info()


class EDFFreePhaseDynamicNextAmberSlotSensor(CoordinatorEntity, SensorEntity):
    """Next amber slot in the forecast."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Next Amber Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_amber_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "amber":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "amber":
                return {
                    "start": slot["start"],
                    "end": slot["end"],
                    "value": slot["value"],
                    "phase": slot["phase"],
                    "next_slot_start": slot["start"],
                }
        return {}

    @property
    def device_info(self):
        return edf_device_info()


class EDFFreePhaseDynamicNextRedSlotSensor(CoordinatorEntity, SensorEntity):
    """Next red slot in the forecast."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Next Red Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_red_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "red":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "red":
                return {
                    "start": slot["start"],
                    "end": slot["end"],
                    "value": slot["value"],
                    "phase": slot["phase"],
                    "next_slot_start": slot["start"],
                }
        return {}

    @property
    def device_info(self):
        return edf_device_info()