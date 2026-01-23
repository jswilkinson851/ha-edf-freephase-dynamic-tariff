"""
Standing Charge sensor for EDF FreePhase Dynamic Tariff.

Exposes the region‑specific standing charge (inc VAT) as the native value,
with additional attributes for exc VAT, validity dates, and raw EDF data.
"""

from __future__ import annotations

from typing import Any, Optional

from homeassistant.components.sensor import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    SensorEntity,
)
from homeassistant.helpers.update_coordinator import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    CoordinatorEntity,
)

from ..helpers import edf_device_info


class EDFFreePhaseDynamicStandingChargeSensor(CoordinatorEntity, SensorEntity):
    """Standing Charge sensor."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "p/day"
    _attr_device_class = None
    _attr_state_class = "measurement"

    def __init__(self, edf_coordinator):
        super().__init__(edf_coordinator)

        self.edf_coordinator = edf_coordinator
        entry = edf_coordinator.config_entry

        # Device linking
        self._attr_device_info = edf_device_info(entry.entry_id)

        # Identity
        self._attr_unique_id = f"{entry.entry_id}_standing_charge"
        self._attr_name = "Standing Charge"
        self.entity_id = "sensor.standing_charge"

    @property
    def native_value(self) -> Optional[float]:
        """Return the standing charge (inc VAT) in p/day."""
        data = self.edf_coordinator.data or {}
        return data.get("standing_charge_inc_vat")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed standing‑charge attributes."""
        data = self.edf_coordinator.data or {}
        inc = data.get("standing_charge_inc_vat")
        gbp_per_day = inc / 100.0 if isinstance(inc, (int, float)) else None

        return {
            "inc_vat_p_per_day": data.get("standing_charge_inc_vat"),
            "exc_vat_p_per_day": data.get("standing_charge_exc_vat"),
            "gbp_per_day": gbp_per_day,
            "valid_from": data.get("standing_charge_valid_from"),
            "valid_to": data.get("standing_charge_valid_to"),
            "region": self.edf_coordinator.config_entry.data.get("tariff_region_label"),
            "last_successful_update": self.edf_coordinator.data.get("last_updated"),
            "raw": data.get("standing_charge_raw"),
        }
