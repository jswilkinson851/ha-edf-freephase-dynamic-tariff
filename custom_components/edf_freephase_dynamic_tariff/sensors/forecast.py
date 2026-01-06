"""
Forecast and pricing trend sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime, as_local
from .helpers import edf_device_info


# 24-Hour Forecast Sensor
class EDFFreePhaseDynamic24HourForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor providing the next 24-hour price forecast."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "24-Hour Forecast"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_24h_forecast"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        return len(self.coordinator.data.get("next_24_hours", []))

    @property
    def extra_state_attributes(self):
        attrs = {}
        for i, slot in enumerate(self.coordinator.data.get("next_24_hours", [])):
            start = parse_datetime(slot["start"])
            end = parse_datetime(slot["end"])

            if start:
                start = as_local(start)
                start_fmt = start.strftime("%H:%M on %d/%m/%Y")
            else:
                start_fmt = None

            if end:
                end = as_local(end)
                end_fmt = end.strftime("%H:%M on %d/%m/%Y")
                duration = (end - start).total_seconds() / 60 if start else None
            else:
                end_fmt = None
                duration = None

            attrs[f"slot_{i+1}"] = {
                "phase": slot["phase"],
                "value": slot["value"],
                "start": start_fmt,
                "end": end_fmt,
                "duration_minutes": duration,
                "icon": self._icon_for_phase(slot["phase"]),
            }

        return attrs

    def _icon_for_phase(self, phase):
        return {
            "green": "mdi:leaf",
            "amber": "mdi:clock-outline",
            "red": "mdi:alert",
        }.get(phase, "mdi:help-circle")

    @property
    def device_info(self):
        return edf_device_info()


# Cheapest Slot Sensor
class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the cheapest slot in the next 24 hours."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:cash"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        return min(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = min(slots, key=lambda s: s["value"])

        start = parse_datetime(slot["start"])
        end = parse_datetime(slot["end"])

        if start:
            start = as_local(start)
            start_fmt = start.strftime("%H:%M on %d/%m/%Y")
        else:
            start_fmt = None

        if end:
            end = as_local(end)
            end_fmt = end.strftime("%H:%M on %d/%m/%Y")
            duration = (end - start).total_seconds() / 60 if start else None
        else:
            end_fmt = None
            duration = None

        return {
            "phase": slot["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": self._icon_for_phase(slot["phase"]),
        }

    def _icon_for_phase(self, phase):
        return {
            "green": "mdi:leaf",
            "amber": "mdi:clock-outline",
            "red": "mdi:alert",
        }.get(phase, "mdi:help-circle")

    @property
    def device_info(self):
        return edf_device_info()


# Most Expensive Slot Sensor
class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the most expensive slot in the next 24 hours."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:cash-remove"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        return max(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = max(slots, key=lambda s: s["value"])

        start = parse_datetime(slot["start"])
        end = parse_datetime(slot["end"])

        if start:
            start = as_local(start)
            start_fmt = start.strftime("%H:%M on %d/%m/%Y")
        else:
            start_fmt = None

        if end:
            end = as_local(end)
            end_fmt = end.strftime("%H:%M on %d/%m/%Y")
            duration = (end - start).total_seconds() / 60 if start else None
        else:
            end_fmt = None
            duration = None

        return {
            "phase": slot["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": self._icon_for_phase(slot["phase"]),
        }

    def _icon_for_phase(self, phase):
        return {
            "green": "mdi:leaf",
            "amber": "mdi:clock-outline",
            "red": "mdi:alert",
        }.get(phase, "mdi:help-circle")

    @property
    def device_info(self):
        return edf_device_info()