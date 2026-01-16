"""
Forecast and pricing trend sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import (
    edf_device_info,
    format_phase_block,
)


# ---------------------------------------------------------------------------
# 24‑Hour Forecast Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamic24HourForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor providing the next 24‑hour price forecast."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "24‑Hour Forecast"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_24h_forecast"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        return len(slots) if slots else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        return {
            f"slot_{i+1}": format_phase_block([slot])
            for i, slot in enumerate(slots)
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Cheapest Slot Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the cheapest slot in the next 24 hours."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:cash"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return None

        return min(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = min(slots, key=lambda s: s["value"])
        return format_phase_block([slot])

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Most Expensive Slot Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the most expensive slot in the next 24 hours."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:cash-remove"

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return None

        return max(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = max(slots, key=lambda s: s["value"])
        return format_phase_block([slot])

    @property
    def device_info(self):
        return edf_device_info()