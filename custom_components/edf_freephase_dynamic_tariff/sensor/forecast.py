from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..helpers import edf_device_info

from ..const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL

class EDFFreePhaseDynamicForecastListSensor(CoordinatorEntity, SensorEntity):
    """Forecast list exposed via attributes."""

    _attr_name = "Tariff Forecast"
    _attr_unique_id = "edf_freephase_dynamic_forecast"
    _attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        # State is the number of slots, not the list itself
        slots = self.coordinator.data.get("next_24_hours", [])
        return len(slots)

    @property
    def extra_state_attributes(self):
        # The actual forecast list lives here
        return {
            "forecast": self.coordinator.data.get("next_24_hours", []),
            "generated_at": self.coordinator.data.get("last_updated"),
        }

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Cheapest slot in the forecast window."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-down-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        cheapest = min(slots, key=lambda x: x["value"])
        return cheapest["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        cheapest = min(slots, key=lambda x: x["value"])
        return {
            "start": cheapest["start"],
            "end": cheapest["end"],
            "value": cheapest["value"],
            "phase": cheapest["phase"],
        }

    @property
    def device_info(self):
        return edf_device_info()

class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    """Most expensive slot in the forecast window."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-up-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        expensive = max(slots, key=lambda x: x["value"])
        return expensive["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        expensive = max(slots, key=lambda x: x["value"])
        return {
            "start": expensive["start"],
            "end": expensive["end"],
            "value": expensive["value"],
            "phase": expensive["phase"],
        }

    @property
    def device_info(self):
        return edf_device_info()