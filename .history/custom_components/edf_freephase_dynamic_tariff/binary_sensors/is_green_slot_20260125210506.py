"""
Binary sensor indicating whether the current tariff slot is classified as green.

This module exposes a single diagnostic‑friendly binary sensor that evaluates the
current half‑hour slot provided by the coordinator and reports whether its phase
is "green". Green slots typically represent the lowest‑cost or most favourable
tariff periods, making this sensor ideal for automations that trigger during
cheap or environmentally preferred windows.

The coordinator exposes a `current_slot` dictionary containing:
    {
        "start": ISO timestamp,
        "end": ISO timestamp,
        "value": float (p/kWh),
        "phase": "green" | "amber" | "red" | "free" | ...
    }

This sensor:
    - Reports `True` when the current slot’s phase is "green".
    - Reports `False` when the slot exists but is not green.
    - Returns `None` when no current slot is available (e.g., during startup or
      API failure).
    - Exposes the full `current_slot` dictionary as attributes for debugging and
      automation logic.

Device metadata is provided via `edf_device_info()` so the entity groups cleanly
under the integration’s main device in the Home Assistant UI.
"""

from __future__ import annotations

from typing import Any, Optional

from homeassistant.components.binary_sensor import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    BinarySensorEntity,
)
from homeassistant.helpers.update_coordinator import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    CoordinatorEntity,
)

from ..helpers import edf_device_info


class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """
    Binary sensor indicating whether the current half‑hour slot is green.

    The entity evaluates the coordinator’s `current_slot` dictionary and returns:
        - True  → if the slot exists and its phase is "green"
        - False → if the slot exists but is not green
        - None  → if no current slot is available

    This makes the sensor ideal for:
        - Triggering automations during low‑cost or environmentally preferred
          tariff periods.
        - Building dashboards that highlight favourable energy windows.
        - Debugging slot classification via the exposed `current_slot` attribute.

    The sensor is linked to the integration’s main device via `edf_device_info()`
    to ensure consistent grouping in the Home Assistant UI.
    """

    _attr_name = "Is Green Slot"
    _attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
    _attr_entity_registry_enabled_default = True
    _attr_device_class = "power"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        # Cache config entry for correct device linking
        self._entry = coordinator.config_entry

        # Device assignment
        self._attr_device_info = edf_device_info(self._entry.entry_id)

    @property
    def is_on(self) -> Optional[bool]:
        """
        Return True if the current slot is classified as green.

        Returns:
            True if the slot exists and its phase is "green".
            False if the slot exists but is a different phase.
            None if no current slot is available.
        """

        data = self.coordinator.data or {}
        current = data.get("current_slot")
        return current.get("phase") == "green" if current else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """
        Expose the full `current_slot` dictionary for debugging and automation.

        This allows advanced automations to inspect timing, duration, and pricing
        metadata without needing to reference the coordinator directly.
        """
        data = self.coordinator.data or {}
        current = data.get("current_slot") or {}
        return {"current_slot": current}
