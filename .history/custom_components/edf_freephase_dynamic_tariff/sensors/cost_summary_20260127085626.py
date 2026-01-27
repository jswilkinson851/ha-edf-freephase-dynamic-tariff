"""
sensors/cost_summary.py — Modernised, DRY, Mixins, Normalised Attributes

Cost and consumption summary sensors for the EDF FreePhase Dynamic Tariff integration.

This module defines six sensors that expose per-phase cost and consumption
summaries for yesterday and today, plus per-slot cost breakdowns. Each sensor
is a CoordinatorEntity that reads precomputed summaries from the CostCoordinator.

Friendly names, unique IDs, and entity_ids remain exactly as they are:
- Yesterday Cost (Phase)            -> sensor.edf_fpd_yesterday_cost_phase
- Today Cost (Phase)                -> sensor.edf_fpd_today_cost_phase
- Yesterday Consumption (Phase)     -> sensor.edf_fpd_yesterday_consumption_phase
- Today Consumption (Phase)         -> sensor.edf_fpd_today_consumption_phase
- Yesterday Cost (Slots)            -> sensor.edf_fpd_yesterday_cost_slots
- Today Cost (Slots)                -> sensor.edf_fpd_today_cost_slots
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from homeassistant.components.sensor import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    SensorEntity,
)
from homeassistant.helpers.update_coordinator import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    CoordinatorEntity,
)

from ..helpers import (
    build_entity_id,
    edf_device_info,
)

# ---------------------------------------------------------------------------
# Protocol for mixins (Pylance-safe)
# ---------------------------------------------------------------------------


class SummaryProvider(Protocol):
    """Protocol for sensors providing a summary property."""

    @property
    def summary(self) -> Optional[Dict[str, Any]]: ...  # noqa: E800 # pylint: disable=missing-function-docstring


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class BaseSummarySensor(CoordinatorEntity, SensorEntity):
    """Shared logic for all cost/consumption summary sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        edf_coordinator,
        cost_coordinator,
        period: str,
        unique_id: str,
        name: str,
        icon: str | None,
    ) -> None:
        super().__init__(cost_coordinator)

        self.edf_coordinator = edf_coordinator
        self.cost_coordinator = cost_coordinator
        self.period = period

        # Cache config entry for correct device linking
        self._entry = edf_coordinator.config_entry

        # Device linking
        self._attr_device_info = edf_device_info(self._entry.entry_id)

        # Identity
        self._attr_unique_id = unique_id
        self._attr_name = name
        if icon:
            self._attr_icon = icon

        # Enabled by default
        self._attr_entity_registry_enabled_default = True

    @property
    def summary(self) -> Optional[dict]:
        """Return the summary dict for this sensor's period from the cost coordinator."""
        data = self.cost_coordinator.data or {}
        return data.get(self.period)

    @property
    def available(self) -> bool:
        """Sensor is available only if the coordinator has produced a summary for the period."""
        return self.summary is not None


# ---------------------------------------------------------------------------
# Mixins for attribute patterns
# ---------------------------------------------------------------------------


class PhaseCostMixin:
    """Adds cost-per-phase native value and attributes."""

    @property
    def native_value(self: SummaryProvider) -> Optional[float]:
        """Return total cost from the summary."""
        s = self.summary
        return s.get("total_cost") if s else None

    @property
    def extra_state_attributes(self: SummaryProvider) -> dict[str, Any]:
        """Return detailed per-phase cost attributes."""
        s = self.summary or {}
        per_phase = s.get("per_phase") or {}

        return {
            "period_info": {
                "start": s.get("period_start"),
                "end": s.get("period_end"),
            },
            "phase_summary": {
                "items": per_phase,
                "count": len(per_phase),
                "unit": "phase",
            },
            "total_summary": {
                "kwh": s.get("total_kwh"),
                "cost": s.get("total_cost"),
            },

            # --------------------------------------------------------------
            # Standing charge fields
            # --------------------------------------------------------------
            "standing_charge": {
                "inc_vat_p_per_day": s.get("standing_charge_inc_vat"),
                "exc_vat_p_per_day": s.get("standing_charge_exc_vat"),
                "valid_from": s.get("standing_charge_valid_from"),
                "valid_to": s.get("standing_charge_valid_to"),
                "cost_today_gbp": s.get("standing_charge_cost_gbp"),
                "total_cost_including_standing_gbp": s.get("total_cost_including_standing_gbp"),
            },
        }


class PhaseConsumptionMixin:
    """Adds consumption-per-phase native value and attributes."""

    @property
    def native_value(self: SummaryProvider) -> Optional[float]:
        """Return total kWh from the summary."""
        s = self.summary
        return s.get("total_kwh") if s else None

    @property
    def extra_state_attributes(self: SummaryProvider) -> dict[str, Any]:
        """Return detailed per-phase consumption attributes."""
        s = self.summary or {}
        per_phase = s.get("per_phase") or {}

        return {
            "period_info": {
                "start": s.get("period_start"),
                "end": s.get("period_end"),
            },
            "phase_summary": {
                "items": per_phase,
                "count": len(per_phase),
                "unit": "phase",
            },
            "total_summary": {
                "kwh": s.get("total_kwh"),
                "cost": s.get("total_cost"),
            },

            # --------------------------------------------------------------
            # Standing charge fields
            # --------------------------------------------------------------
            "standing_charge": {
                "inc_vat_p_per_day": s.get("standing_charge_inc_vat"),
                "exc_vat_p_per_day": s.get("standing_charge_exc_vat"),
                "valid_from": s.get("standing_charge_valid_from"),
                "valid_to": s.get("standing_charge_valid_to"),
                "cost_today_gbp": s.get("standing_charge_cost_gbp"),
                "total_cost_including_standing_gbp": s.get("total_cost_including_standing_gbp"),
            },
        }


class SlotCostMixin:
    """Adds slot-level cost breakdown native value and attributes."""

    @property
    def native_value(self: SummaryProvider) -> Optional[int]:
        """Return number of slots from the summary."""
        s = self.summary
        per_slot = s.get("per_slot") if s else None
        return len(per_slot) if per_slot else None

    @property
    def extra_state_attributes(self: SummaryProvider) -> dict[str, Any]:
        """Return detailed per-slot cost attributes."""
        s = self.summary or {}
        per_slot = s.get("per_slot") or []

        avg_price = sum(x.get("price_p_per_kwh", 0) for x in per_slot) / len(per_slot) if per_slot else None  # pylint: disable=line-too-long

        return {
            "period_info": {
                "start": s.get("period_start"),
                "end": s.get("period_end"),
            },
            "slot_summary": {
                "items": per_slot,
                "count": len(per_slot),
            },
            "total_summary": {
                "kwh": s.get("total_kwh"),
                "cost": s.get("total_cost"),
            },
            "price_summary": {
                "value": avg_price,
                "unit": "p/kWh",
            },

            # --------------------------------------------------------------
            # Standing charge fields
            # --------------------------------------------------------------
            "standing_charge": {
                "inc_vat_p_per_day": s.get("standing_charge_inc_vat"),
                "exc_vat_p_per_day": s.get("standing_charge_exc_vat"),
                "valid_from": s.get("standing_charge_valid_from"),
                "valid_to": s.get("standing_charge_valid_to"),
                "cost_today_gbp": s.get("standing_charge_cost_gbp"),
                "total_cost_including_standing_gbp": s.get("total_cost_including_standing_gbp"),
            },
        }


# ---------------------------------------------------------------------------
# Concrete sensors (renamed classes, entity_ids preserved)
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicYesterdayCostPhaseSensor(PhaseCostMixin, BaseSummarySensor):
    """Yesterday Cost (Phase) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="yesterday",
            unique_id="yesterday_cost_phase",
            name="EDF FPD Yesterday Cost (Phase)",
            icon="mdi:currency-gbp",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "yesterday_cost_phase",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"


class EDFFreePhaseDynamicTodayCostPhaseSensor(PhaseCostMixin, BaseSummarySensor):
    """Today Cost (Phase) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="today",
            unique_id="today_cost_phase",
            name="EDF FPD Today Cost (Phase)",
            icon="mdi:currency-gbp",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "today_cost_phase",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_device_class = "monetary"
        self._attr_state_class = "total"


class EDFFreePhaseDynamicYesterdayConsumptionPhaseSensor(PhaseConsumptionMixin, BaseSummarySensor):
    """Yesterday Consumption (Phase) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="yesterday",
            unique_id="yesterday_consumption_phase",
            name="EDF FPD Yesterday Consumption (Phase)",
            icon="mdi:flash",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "yesterday_consumption_phase",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total"


class EDFFreePhaseDynamicTodayConsumptionPhaseSensor(PhaseConsumptionMixin, BaseSummarySensor):
    """Today Consumption (Phase) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="today",
            unique_id="today_consumption_phase",
            name="EDF FPD Today Consumption (Phase)",
            icon="mdi:flash",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "today_consumption_phase",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total"


class EDFFreePhaseDynamicYesterdayCostSlotsSensor(SlotCostMixin, BaseSummarySensor):
    """Yesterday Cost (Slots) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="yesterday",
            unique_id="yesterday_cost_slots",
            name="EDF FPD Yesterday Cost (Slots)",
            icon="mdi:chart-bar",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "yesterday_cost_slots",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "Slots"
        self._attr_device_class = None


class EDFFreePhaseDynamicTodayCostSlotsSensor(SlotCostMixin, BaseSummarySensor):
    """Today Cost (Slots) sensor."""

    def __init__(self, edf_coordinator, cost_coordinator):
        super().__init__(
            edf_coordinator,
            cost_coordinator,
            period="today",
            unique_id="today_cost_slots",
            name="EDF FPD Today Cost (Slots)",
            icon="mdi:chart-bar",
        )
        self._attr_entity_id = build_entity_id(
            "sensor",
            "today_cost_slots",
            "fpd",
        )
        self._attr_native_unit_of_measurement = "Slots"
        self._attr_device_class = None


# ---------------------------------------------------------------------------
# End of cost_summary.py
# ---------------------------------------------------------------------------
