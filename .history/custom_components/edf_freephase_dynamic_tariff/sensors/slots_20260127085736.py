"""
Slot‑level and block‑level colour sensors for the EDF FreePhase Dynamic Tariff
integration.

This module exposes sensors that describe the current and upcoming tariff
phases at both slot and merged‑block granularity. These sensors provide
user‑facing insight into the tariff’s colour‑coded structure, enabling
dashboards, automations, and energy‑aware decision‑making.

The coordinator exposes:
    - current_slot
    - all_slots_sorted
    - next_24_hours

Each slot contains:
    {
        "start": ISO timestamp,
        "end": ISO timestamp,
        "value": float (p/kWh),
        "phase": "green" | "amber" | "red" | "free" | ...
    }

Helpers used in this module:
    - find_current_block(): identify the merged block containing the current slot
    - find_next_phase_block(): find the next block of a specific phase
    - group_phase_blocks(): merge consecutive slots with the same phase
    - format_phase_block(): convert a block into a structured attribute dict

Sensors included:
    1. Current Slot Colour
    2. Current Block Summary
    3. Next Block Summary
    4. Next {Colour} Slot (parameterised)
    5. Factory for concrete next‑phase sensors

All sensors inherit from CoordinatorEntity so they update automatically whenever
the coordinator refreshes. Device metadata is provided via `edf_device_info()`
to ensure all entities group cleanly under a single device in the Home Assistant
UI.
"""

from __future__ import annotations

# pylint: disable=import-error
from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]

# pylint: enable=import-error
from ..helpers import (
    build_entity_id,
    edf_device_info,
    find_current_block,
    find_next_phase_block,
    format_phase_block,
    group_phase_blocks,
)

# ---------------------------------------------------------------------------
# Current Slot Colour
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the colour (phase) of the current half‑hour slot.

    The entity’s state is the phase string (e.g., "green", "amber", "red").
    Attributes expose the full merged block containing the current slot,
    including start/end times, duration, and pricing context.

    This sensor provides a simple, user‑friendly view of the tariff’s current
    state and is ideal for dashboards and automations that react to phase
    changes.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FPD Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"

        self._attr_entity_id = build_entity_id(
            domain="sensor",
            object_id="current_slot_colour",
            tariff="fpd",
        )

        self._attr_icon = "mdi:circle-slice-3"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the current slot's colour phase."""
        data = self.coordinator.data or {}
        current = data.get("current_slot")
        return current.get("phase") if current else None

    @property
    def extra_state_attributes(self):
        """Return full details of the current block as extra attributes."""
        data = self.coordinator.data or {}
        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        return format_phase_block(block) if block else {}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Current Phase Summary
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCurrentPhaseSummarySensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing a detailed summary of the current merged colour phase.

    A "phase" is a consecutive run of slots with the same phase (N.B. "block"
    is the legacy name for "phase" in the integration). This sensor reports
    the phase’s price (in p/kWh) as its state and exposes a structured attribute
    block describing:

        - Start and end timestamps
        - Duration
        - Phase colour
        - Slot count
        - Pricing metadata

    This provides a richer view than the simple current‑slot sensor and is
    useful for dashboards that visualise tariff windows.

    """

    def __init__(self, coordinator):
        """Initialize the Current Phase Summary sensor."""
        super().__init__(coordinator)
        self._attr_name = "EDF FPD Current Phase Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_block_summary"

        self._attr_entity_id = build_entity_id(
            domain="sensor",
            object_id="current_phase_summary",
            tariff="fpd",
        )

        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:timeline-clock"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the current phase's price value."""
        data = self.coordinator.data or {}
        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        return block[0].get("value") if block else None

    @property
    def extra_state_attributes(self):
        """Return full details of the current block as extra attributes."""
        data = self.coordinator.data or {}
        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])

        block = find_current_block(all_slots, current)
        return format_phase_block(block) if block else {}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Next Phase Summary
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicNextPhaseSummarySensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing a summary of the next merged colour phase.

    The entity identifies the phase immediately following the current one by:
        1. Locating the current phase via `find_current_phase()`.
        2. Merging all slots into phases via `group_phase_phases()`.
        3. Selecting the next phase in chronological order.

    The sensor’s state is the next phase’s price (in p/kWh). Attributes expose
    the full phase metadata via `format_phase_block()`.

    This sensor is ideal for planning ahead — e.g., determining when a cheaper
    or more expensive phase is about to begin.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FPD Next Phase Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_block_summary"

        self._attr_entity_id = build_entity_id(
            domain="sensor",
            object_id="next_phase_summary",
            tariff="fpd",
        )

        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:timeline-clock-outline"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    def _find_next_block(self):
        """
        Identify the merged colour block that follows the current one.

        Steps:
            - Retrieve all sorted slots from the coordinator.
            - Identify the current block using `find_current_block()`.
            - Merge all slots into blocks using `group_phase_blocks()`.
            - Return the block immediately after the current one, if any.

        Returns:
            A list of slot dictionaries representing the next block, or None if
            no such block exists.
        """

        data = self.coordinator.data or {}
        all_slots = data.get("all_slots_sorted", [])
        current = data.get("current_slot")

        if not current or not all_slots:
            return None

        current_block = find_current_block(all_slots, current)
        if not current_block:
            return None

        blocks = group_phase_blocks(all_slots)

        try:
            idx = blocks.index(current_block)
            return blocks[idx + 1] if idx + 1 < len(blocks) else None
        except ValueError:
            return None

    @property
    def native_value(self):
        """Return the next block's price value."""
        block = self._find_next_block()
        return block[0].get("value") if block else None

    @property
    def extra_state_attributes(self):
        """Return full details of the next block as extra attributes."""
        block = self._find_next_block()
        return format_phase_block(block) if block else {}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Next {Colour} Slot — parameterised class
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicNextPhaseSlotSensor(CoordinatorEntity, SensorEntity):
    """
    Generic sensor exposing the next upcoming slot of a specific phase.

    This parameterised entity is instantiated with:
        - phase: the target phase (e.g., "green", "amber", "red")
        - name: user‑friendly entity name
        - unique_id: stable unique identifier
        - icon: Material Design icon for the phase

    The sensor’s state is the price (in p/kWh) of the next slot matching the
    requested phase. Attributes expose the full block metadata via
    `format_phase_block()`.

    This class underpins the concrete “Next Green Slot”, “Next Amber Slot”, and
    “Next Red Slot” sensors created by `create_next_phase_sensors()`.
    """

    def __init__(self, coordinator, phase, name, unique_id, icon):
        super().__init__(coordinator)
        self._phase = phase
        self._attr_name = f"EDF FPD {name}"
        self._attr_unique_id = unique_id

        self._attr_entity_id = build_entity_id(
            domain="sensor",
            object_id=f"next_{phase}_slot",
            tariff="fpd",
        )

        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = icon
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the next block's price value for the specified phase."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        block = find_next_phase_block(slots, self._phase)
        return block[0].get("value") if block else None

    @property
    def extra_state_attributes(self):
        """Return full details of the next block for the specified phase as extra attributes."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        block = find_next_phase_block(slots, self._phase)
        return format_phase_block(block) if block else {}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Concrete Next {Colour} Slot sensors
# ---------------------------------------------------------------------------


def create_next_phase_sensors(coordinator):
    """
    Factory function creating concrete next‑phase slot sensors.

    Returns a list of EDFFreePhaseDynamicNextPhaseSlotSensor instances for:
        - Next Green Slot
        - Next Amber Slot
        - Next Red Slot

    These sensors provide a simple, user‑friendly way to monitor when the next
    slot of each phase will occur, enabling dashboards and automations that
    react to specific tariff colours.
    """

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
# End of slots.py
# ---------------------------------------------------------------------------
