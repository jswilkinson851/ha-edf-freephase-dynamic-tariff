"""
Price-related sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime, as_local
from .helpers import edf_device_info


# Shared formatting helpers
def _format_slot_times(slot):
    start = parse_datetime(slot["start"])
    end = parse_datetime(slot["end"])

    if start:
        start_local = as_local(start)
        start_fmt = start_local.strftime("%H:%M on %d/%m/%Y")
    else:
        start_fmt = None

    if end:
        end_local = as_local(end)
        end_fmt = end_local.strftime("%H:%M on %d/%m/%Y")
        duration = (end_local - start_local).total_seconds() / 60 if start else None
    else:
        end_fmt = None
        duration = None

    return start_fmt, end_fmt, duration


def _icon_for_phase(phase):
    return {
        "green": "mdi:leaf",
        "amber": "mdi:clock-outline",
        "red": "mdi:alert",
    }.get(phase, "mdi:help-circle")


# ---------------------------------------------------------------------------
# Current Price Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the current electricity price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:currency-gbp"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["value"] if current else None

    @property
    def extra_state_attributes(self):
        slot = self.coordinator.data.get("current_slot")
        if not slot:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times(slot)

        return {
            "phase": slot["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase(slot["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Slot Price Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextSlotPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the next slot's price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Slot Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_slot_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:currency-gbp"

    def _find_next_slot(self):
        """Return the next future slot from today's data."""
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )
        return slots[0] if slots else None

    @property
    def native_value(self):
        slot = self._find_next_slot()
        return slot["value"] if slot else None

    @property
    def extra_state_attributes(self):
        slot = self._find_next_slot()
        if not slot:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times(slot)

        return {
            "phase": slot["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase(slot["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()

# ---------------------------------------------------------------------------
# Cheapest Slot (Today)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Cheapest remaining slot today."""

    _attr_icon = "mdi:cash"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("todays_24_hours", [])
        if not slots:
            return None
        cheapest = min(slots, key=lambda s: s["value"])
        return cheapest["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("todays_24_hours", [])
        if not slots:
            return {}
        cheapest = min(slots, key=lambda s: s["value"])
        return cheapest

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Most Expensive Slot (Today)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    """Most expensive remaining slot today."""

    _attr_icon = "mdi:cash-remove"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("todays_24_hours", [])
        if not slots:
            return None
        expensive = max(slots, key=lambda s: s["value"])
        return expensive["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("todays_24_hours", [])
        if not slots:
            return {}
        expensive = max(slots, key=lambda s: s["value"])
        return expensive

    @property
    def device_info(self):
        return edf_device_info()