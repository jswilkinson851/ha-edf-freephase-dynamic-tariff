"""
Forecast and pricing‑trend sensor entities for the EDF FreePhase Dynamic Tariff
integration.

This module exposes three read‑only sensors derived from the coordinator’s
forecast payload:

1. EDFFreePhaseDynamic24HourForecastSensor
   - Reports the number of forecast slots available in the next 24 hours.
   - Exposes each slot as a structured attribute block for dashboards,
     automations, and advanced analysis.

2. EDFFreePhaseDynamicCheapestSlotSensor
   - Identifies the cheapest half‑hour slot in the next 24 hours.
   - Provides both the price and a detailed attribute block describing the slot.

3. EDFFreePhaseDynamicMostExpensiveSlotSensor
   - Identifies the most expensive half‑hour slot in the next 24 hours.
   - Provides both the price and a detailed attribute block describing the slot.

All sensors inherit from CoordinatorEntity to ensure they update automatically
whenever the forecast coordinator refreshes. Device metadata is provided via
`edf_device_info()` so all entities group cleanly under a single device in the
Home Assistant UI.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from ..helpers import (
    edf_device_info,
    format_phase_block,
)


# ---------------------------------------------------------------------------
# 24‑Hour Forecast Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamic24HourForecastSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor exposing the number of forecast slots available in the next 24 hours.

    This entity does not report prices directly. Instead, it provides:
    - A numeric state representing the count of forecast slots returned by the
      coordinator.
    - A rich attribute set where each slot is represented as a formatted block
      (via `format_phase_block()`), enabling dashboards and automations to
      inspect the full forecast structure.

    The coordinator is expected to expose a `next_24_hours` list containing
    half‑hour forecast entries with pricing and timing metadata.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "24‑Hour Forecast"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_24h_forecast"
        self._attr_icon = "mdi:chart-line"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the number of forecast slots available."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        return len(slots) if slots else None

    @property
    def extra_state_attributes(self):
        """Return attributes for each forecast slot."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        return {f"slot_{i + 1}": format_phase_block([slot]) for i, slot in enumerate(slots)}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Cheapest Slot Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor representing the cheapest half‑hour slot in the next 24 hours.

    The entity’s state is the price (in p/kWh) of the cheapest slot. Additional
    attributes expose the full slot metadata using `format_phase_block()`,
    allowing dashboards and automations to understand when the cheapest period
    occurs and how it compares to surrounding slots.

    If no forecast data is available, the sensor returns `None` and exposes no
    attributes.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:cash"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the price of the cheapest slot."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return None

        return min(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        """Return attributes for the cheapest slot."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = min(slots, key=lambda s: s["value"])
        return format_phase_block([slot])

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Most Expensive Slot Sensor
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor representing the most expensive half‑hour slot in the next 24 hours.

    The entity’s state is the price (in p/kWh) of the most expensive slot.
    Attributes expose the full slot metadata using `format_phase_block()`,
    enabling dashboards and automations to identify peak‑cost periods and plan
    around them.

    If no forecast data is available, the sensor returns `None` and exposes no
    attributes.
    """

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "p/kWh"
        self._attr_icon = "mdi:cash-remove"

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True

    @property
    def native_value(self):
        """Return the value of the most expensive slot."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return None

        return max(slots, key=lambda s: s["value"])["value"]

    @property
    def extra_state_attributes(self):
        """Return attributes for the most expensive slot."""
        data = self.coordinator.data or {}
        slots = data.get("next_24_hours", [])
        if not slots:
            return {}

        slot = max(slots, key=lambda s: s["value"])
        return format_phase_block([slot])

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------
