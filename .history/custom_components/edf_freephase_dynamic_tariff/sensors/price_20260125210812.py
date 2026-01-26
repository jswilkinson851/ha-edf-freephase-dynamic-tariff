"""
Price‑related sensor entities for the EDF FreePhase Dynamic Tariff integration.

This module exposes sensors that report the current and next half‑hour electricity
prices derived from the coordinator’s normalised forecast data. These sensors
provide user‑facing tariff values suitable for dashboards, automations, and
energy‑aware decision‑making.

All sensors inherit from CoordinatorEntity so they update automatically whenever
the coordinator refreshes. Device metadata is provided via `edf_device_info()`
to ensure all entities group cleanly under a single device in the Home Assistant
UI.

Sensors included in this module:

1. EDFFreePhaseDynamicCurrentPriceSensor
   - Reports the price of the current half‑hour slot.
   - Exposes a structured attribute block describing the slot.

2. EDFFreePhaseDynamicNextSlotPriceSensor
   - Reports the price of the next upcoming half‑hour slot.
   - Uses normalised timestamps (`start_dt`) when available to ensure correct
     ordering.
   - Exposes a structured attribute block describing the slot.

These sensors represent the primary user‑facing tariff values in the integration.
"""

from __future__ import annotations

# pylint: disable=import-error
from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]
# pylint: disableenable=import-error

from ..helpers import (
    edf_device_info,
    format_phase_block,
)

# ---------------------------------------------------------------------------
# Current Price Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the price of the current half‑hour electricity slot.

    The entity’s state is the price in p/kWh for the slot that is active at the
    time of the coordinator’s most recent refresh. Attributes expose the full
    slot metadata using `format_phase_block()`, enabling dashboards and
    automations to inspect timing, duration, and pricing context.

    If no current slot is available (e.g., during initial startup or API
    failure), the sensor returns None and exposes no attributes.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_price"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:currency-gbp"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the current slot's price."""
        data = self.coordinator.data or {}
        slot = data.get("current_slot")
        return slot.get("value") if slot else None

    @property
    def extra_state_attributes(self):
        """Return the current slot's attributes formatted via `helpers.py`."""
        data = self.coordinator.data or {}
        slot = data.get("current_slot")
        if not slot:
            return {}

        return format_phase_block([slot])

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Next Slot Price Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicNextSlotPriceSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the price of the next upcoming half‑hour electricity slot.

    The entity’s state is the price in p/kWh for the earliest future slot
    returned by the coordinator. Slot ordering uses the normalised `start_dt`
    timestamp when available to ensure correct chronological behaviour.

    Attributes expose the full slot metadata using `format_phase_block()`,
    enabling dashboards and automations to understand when the next price change
    occurs and what the upcoming tariff context looks like.

    If no forecast data is available, the sensor returns None and exposes no
    attributes.
    """

    def __init__(self, coordinator):
        """Initialize the Next Slot Price sensor."""
        super().__init__(coordinator)
        self._attr_name = "Next Slot Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_slot_price"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:currency-gbp"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    def _find_next_slot(self):
        """
        Identify the next upcoming half‑hour slot from the coordinator’s forecast.

        The coordinator exposes a `next_24_hours` list containing normalised slot
        dictionaries. This helper sorts the list using the normalised `start_dt`
        field when available, falling back to the raw `start` string if necessary.

        Returns the earliest upcoming slot dictionary, or None if no forecast data
        is available.
        """

        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return None

        # Use start_dt (normalised) instead of raw start string
        try:
            slots = sorted(slots, key=lambda s: s["start_dt"])
        except KeyError:
            slots = sorted(slots, key=lambda s: s.get("start"))

        return slots[0] if slots else None

    @property
    def native_value(self):
        """
        Return the price of the next half‑hour slot.

        This value is extracted directly from the coordinator’s forecast data and
        represents the tariff that will apply once the current slot ends.
        """
        slot = self._find_next_slot()
        return slot.get("value") if slot else None

    @property
    def extra_state_attributes(self):
        """
        Return a structured attribute block describing the next slot.

        The block includes timing, duration, and pricing metadata, formatted via
        `format_phase_block()` for consistency across the integration.
        """

        slot = self._find_next_slot()
        if not slot:
            return {}

        return format_phase_block([slot])

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------
