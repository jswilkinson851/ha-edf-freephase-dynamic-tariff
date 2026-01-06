"""
Daily rate summary sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from datetime import datetime, timezone, timedelta
import dateutil.parser

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .helpers import edf_device_info
from .slots import _format_slot_times, _icon_for_phase


# ---------------------------------------------------------------------------
# Utility: filter slots to a specific date
# ---------------------------------------------------------------------------

def _slots_for_date(coordinator, target_date):
    """Return all slots whose start_dt matches the given date."""
    all_slots = coordinator.data.get("all_slots_sorted", [])
    return [
        s for s in all_slots
        if dateutil.parser.isoparse(s["start"]).date() == target_date
    ]


# ---------------------------------------------------------------------------
# Today's Rates Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTodaysRatesSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of today's merged colour blocks, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Today's Rates Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_todays_rates_summary"
        self._attr_icon = "mdi:calendar-clock"

    def _merge_blocks(self):
        today = datetime.now(timezone.utc).date()

        # Strictly today's slots only
        slots = sorted(
            _slots_for_date(self.coordinator, today),
            key=lambda s: s["start_dt"]
        )

        if not slots:
            return []

        blocks = []
        current_block = [slots[0]]

        for slot in slots[1:]:
            if slot["phase"].lower() == current_block[-1]["phase"].lower():
                current_block.append(slot)
            else:
                blocks.append(current_block)
                current_block = [slot]

        blocks.append(current_block)
        return blocks

    @property
    def native_value(self):
        blocks = self._merge_blocks()
        return f"{len(blocks)} blocks" if blocks else None

    @property
    def extra_state_attributes(self):
        blocks = self._merge_blocks()
        if not blocks:
            return {}

        attrs = {}

        for i, block in enumerate(blocks, start=1):
            start_fmt, end_fmt, duration = _format_slot_times({
                "start": block[0]["start"],
                "end": block[-1]["end"]
            })

            attrs[f"block_{i}"] = {
                "phase": block[0]["phase"],
                "start": start_fmt,
                "end": end_fmt,
                "duration_minutes": duration,
                "price_gbp": block[0]["value"],
                "icon": _icon_for_phase(block[0]["phase"]),
            }

        return attrs

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Tomorrow's Rates Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTomorrowsRatesSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of tomorrow's merged colour blocks, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tomorrow's Rates Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_tomorrows_rates_summary"
        self._attr_icon = "mdi:calendar-arrow-right"

    def _merge_blocks(self):
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)

        slots = sorted(
            _slots_for_date(self.coordinator, tomorrow),
            key=lambda s: s["start_dt"]
        )

        if not slots:
            return []

        blocks = []
        current_block = [slots[0]]

        for slot in slots[1:]:
            if slot["phase"].lower() == current_block[-1]["phase"].lower():
                current_block.append(slot)
            else:
                blocks.append(current_block)
                current_block = [slot]

        blocks.append(current_block)
        return blocks

    @property
    def native_value(self):
        blocks = self._merge_blocks()
        return f"{len(blocks)} blocks" if blocks else None

    @property
    def extra_state_attributes(self):
        blocks = self._merge_blocks()
        if not blocks:
            return {}

        attrs = {}

        for i, block in enumerate(blocks, start=1):
            start_fmt, end_fmt, duration = _format_slot_times({
                "start": block[0]["start"],
                "end": block[-1]["end"]
            })

            attrs[f"block_{i}"] = {
                "phase": block[0]["phase"],
                "start": start_fmt,
                "end": end_fmt,
                "duration_minutes": duration,
                "price_gbp": block[0]["value"],
                "icon": _icon_for_phase(block[0]["phase"]),
            }

        return attrs

    @property
    def device_info(self):
        return edf_device_info()