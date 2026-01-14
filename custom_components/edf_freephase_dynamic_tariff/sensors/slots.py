"""
Slot colour and next-slot sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import (
    edf_device_info,
    format_phase_block,
    find_current_block,
    find_next_phase_block,
    group_phase_blocks,
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

    def _find_next_block(self):
        all_slots = self.coordinator.data.get("all_slots_sorted", [])
        current = self.coordinator.data.get("current_slot")

        if not current or not all_slots:
            return None

        # Find current block
        current_block = find_current_block(all_slots, current)
        if not current_block:
            return None

        # Group all blocks
        blocks = group_phase_blocks(all_slots)

        # Find next block after current block
        try:
            idx = blocks.index(current_block)
            return blocks[idx + 1] if idx + 1 < len(blocks) else None
        except ValueError:
            return None

    @property
    def native_value(self):
        block = self._find_next_block()
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        block = self._find_next_block()
        return format_phase_block(block) if block else {}

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