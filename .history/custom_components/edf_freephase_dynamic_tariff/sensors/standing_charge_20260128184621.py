"""
Standing‑charge sensor implementation for the EDF FreePhase Dynamic Tariff integration.

This module defines the sensor entity responsible for exposing the region‑specific
standing charge associated with the tariff. The standing charge is retrieved and
maintained by the main EDF coordinator, and this sensor provides a clean,
Home‑Assistant‑native interface for presenting that information to users.

The sensor reports the VAT‑inclusive standing charge as its primary state
(pence per day), and supplements it with a detailed set of attributes including:

    • exc‑VAT standing charge
    • GBP/day conversion
    • validity window (valid_from / valid_to)
    • region label selected during configuration
    • timestamp of the last successful coordinator update
    • raw EDF metadata for diagnostics and debugging

The entity links itself to the integration’s device entry so that it appears
alongside other tariff‑related sensors in the UI. All computation and data
preparation occur within the coordinator; this module focuses solely on
exposing those values in a structured, user‑friendly form.
"""

from __future__ import annotations

from typing import Any, Optional

# pylint: disable=import-error
from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]

# pylint: enable=import-error
from ..helpers import (
    build_entity_id,
    edf_device_info,
)


class EDFFreePhaseDynamicStandingChargeSensor(CoordinatorEntity, SensorEntity):
    """
    Sensor entity exposing the daily standing charge for the EDF FreePhase Dynamic Tariff.

    This sensor reports the region‑specific standing charge (inclusive of VAT) as its
    primary state, expressed in pence per day. It supplements this with a rich set of
    attributes derived from the coordinator’s tariff metadata, including:

        • exc‑VAT standing charge
        • GBP/day conversion
        • validity window (valid_from / valid_to)
        • region label selected during configuration
        • timestamp of the last successful coordinator update
        • raw EDF metadata for debugging and diagnostics

    The entity is backed by the main EDF coordinator, ensuring that updates occur in
    sync with all other tariff data. It links itself to the integration’s device entry
    so that the standing charge appears alongside other tariff‑related sensors in the
    Home Assistant UI.

    No computation is performed here; the sensor simply exposes values prepared by the
    coordinator, providing a clean and reliable interface for automations, dashboards,
    and diagnostics.
    """

    _attr_has_entity_name = False
    _attr_native_unit_of_measurement = "p/day"
    _attr_device_class = None
    _attr_state_class = "measurement"

    def __init__(self, edf_coordinator):
        super().__init__(edf_coordinator)

        self.edf_coordinator = edf_coordinator
        entry = edf_coordinator.config_entry

        self._attr_device_info = edf_device_info(entry.entry_id)

        self._attr_unique_id = f"{entry.entry_id}_standing_charge"
        self._attr_name = "EDF FPD Standing Charge"
        self._attr_entity_id = build_entity_id(
            domain="sensor",
            object_id="standing_charge",
            tariff="fpd",
        )

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
