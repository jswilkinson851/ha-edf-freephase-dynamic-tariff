"""
Price-related sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import (
    edf_device_info,
    format_phase_block,
)


# ---------------------------------------------------------------------------
# Current Price Sensor
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the current electricity price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_price"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:currency-gbp"

    @property
    def native_value(self):
        slot = self.coordinator.data.get("current_slot")
        return slot["value"] if slot else None

    @property
    def extra_state_attributes(self):
        slot = self.coordinator.data.get("current_slot")
        if not slot:
            return {}

        return format_phase_block([slot])

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
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:currency-gbp"

    def _find_next_slot(self):
        slots = sorted(
            self.coordinator.data.get("next_24_hours", []),
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

        return format_phase_block([slot])

    @property
    def device_info(self):
        return edf_device_info()