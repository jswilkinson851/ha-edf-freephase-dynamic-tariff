"""
Slot colour and next-slot sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import (
    edf_device_info,
    format_phase_block,
    find_current_block,
    find_next_phase_block,
)


# ---------------------------------------------------------------------------
# Current Slot Colour
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the current slot's colour, including full block details."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"
        self._attr_icon = "mdi:circle-slice-3"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] if current else None

    @property
    def extra_state_attributes(self):
        current = self.coordinator.data.get("current_slot")
        all_slots = self.coordinator.data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        if not block:
            return {}

        return format_phase_block(block)

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Current Block Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentBlockSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of the current colour block, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Block Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_block_summary"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:timeline-clock"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        all_slots = self.coordinator.data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        current = self.coordinator.data.get("current_slot")
        all_slots = self.coordinator.data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        if not block:
            return {}

        return format_phase_block(block)

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Block Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextBlockSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of the next colour block, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Block Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_block_summary"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:timeline-clock-outline"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        next_slots = self.coordinator.data.get("next_24_hours", [])

        if not current:
            return None

        current_phase = current["phase"]
        block = find_next_phase_block(
            next_slots,
            phase=current_phase  # find next block of a *different* phase
        )

        # Actually find next block of a different phase
        block = next(
            (find_next_phase_block(next_slots, p)
             for p in ("green", "amber", "red")
             if p != current_phase),
            None
        )

        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        current = self.coordinator.data.get("current_slot")
        next_slots = self.coordinator.data.get("next_24_hours", [])

        if not current:
            return {}

        current_phase = current["phase"]

        block = next(
            (find_next_phase_block(next_slots, p)
             for p in ("green", "amber", "red")
             if p != current_phase),
            None
        )

        if not block:
            return {}

        return format_phase_block(block)

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next {Colour} Slot — parameterised class
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextPhaseSlotSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor for the next slot of a given phase."""

    def __init__(self, coordinator, phase, name, unique_id, icon):
        super().__init__(coordinator)
        self._phase = phase
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = icon

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        block = find_next_phase_block(slots, self._phase)
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        block = find_next_phase_block(slots, self._phase)
        if not block:
            return {}

        return format_phase_block(block)

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Concrete Next {Colour} Slot sensors (names + IDs preserved)
# ---------------------------------------------------------------------------

def create_next_phase_sensors(coordinator):
    return [
        EDFFreePhaseDynamicNextPhaseSlotSensor(
            coordinator,
            phase="green",
            name="Next Green Slot",
            unique_id="edf_freephase_dynamic_tariff_next_green_slot",
            icon="mdi:leaf",
        ),
        EDFFreePhaseDynamicNextPhaseSlotSensor(
            coordinator,
            phase="amber",
            name="Next Amber Slot",
            unique_id="edf_freephase_dynamic_tariff_next_amber_slot",
            icon="mdi:clock-outline",
        ),
        EDFFreePhaseDynamicNextPhaseSlotSensor(
            coordinator,
            phase="red",
            name="Next Red Slot",
            unique_id="edf_freephase_dynamic_tariff_next_red_slot",
            icon="mdi:alert",
        ),
    ]


# ---------------------------------------------------------------------------
# Is Green Slot (Binary)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, SensorEntity):
    """Binary sensor to show if the current slot is green."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Is Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] == "green" if current else None

    @property
    def extra_state_attributes(self):
        slot = self.coordinator.data.get("current_slot")
        if not slot:
            return {}

        return format_phase_block([slot])

    @property
    def device_info(self):
        return edf_device_info()