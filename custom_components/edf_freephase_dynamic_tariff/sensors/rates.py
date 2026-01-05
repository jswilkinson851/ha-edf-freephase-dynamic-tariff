"""
Daily rate summary sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .helpers import edf_device_info
from homeassistant.util.dt import parse_datetime, as_local
from .slots import _format_slot_times, _icon_for_phase

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
        """Merge consecutive slots of the same phase into continuous blocks."""
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        if not slots:
            return []

        blocks = []
        current_block = [slots[0]]

        for slot in slots[1:]:
            if slot["phase"] == current_block[-1]["phase"]:
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
        slots = sorted(
            self.coordinator.data.get("tomorrow_24_hours", []),
            key=lambda s: s["start"]
        )

        if not slots:
            return []

        blocks = []
        current_block = [slots[0]]

        for slot in slots[1:]:
            if slot["phase"] == current_block[-1]["phase"]:
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
# Full-Day Rates (Today)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTodaysRatesFullSensor(CoordinatorEntity, SensorEntity):
    """Full set of today's half-hour slots, including raw UTC timestamps."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Today's Rates Full"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_todays_rates_full"

    def _get_slots(self):
        slots = self.coordinator.data.get("todays_24_hours", [])
        return sorted(slots, key=lambda s: s["start"])

    @property
    def native_value(self):
        slots = self._get_slots()
        return f"{len(slots)} slots" if slots else None

    @property
    def extra_state_attributes(self):
        slots = self._get_slots()
        attrs = {}

        for i, slot in enumerate(slots, start=1):
            start_utc = slot["start"]
            end_utc = slot["end"]

            start_fmt, end_fmt, duration = _format_slot_times(
                {"start": start_utc, "end": end_utc}
            )

            attrs[f"slot_{i}"] = {
                "phase": slot["phase"],
                "value": slot["value"],
                "start": start_fmt,
                "end": end_fmt,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "duration_minutes": duration,
                "icon": _icon_for_phase(slot["phase"]),
            }

        return attrs

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Full-Day Rates (Tomorrow)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTomorrowsRatesFullSensor(CoordinatorEntity, SensorEntity):
    """Full set of tomorrow's half-hour slots, including raw UTC timestamps."""

    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tomorrow's Rates Full"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_tomorrows_rates_full"

    def _get_slots(self):
        slots = self.coordinator.data.get("tomorrow_24_hours", [])
        return sorted(slots, key=lambda s: s["start"])

    @property
    def native_value(self):
        slots = self._get_slots()
        return f"{len(slots)} slots" if slots else None

    @property
    def extra_state_attributes(self):
        slots = self._get_slots()
        attrs = {}

        for i, slot in enumerate(slots, start=1):
            start_utc = slot["start"]
            end_utc = slot["end"]

            start_fmt, end_fmt, duration = _format_slot_times(
                {"start": start_utc, "end": end_utc}
            )

            attrs[f"slot_{i}"] = {
                "phase": slot["phase"],
                "value": slot["value"],
                "start": start_fmt,
                "end": end_fmt,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "duration_minutes": duration,
                "icon": _icon_for_phase(slot["phase"]),
            }

        return attrs

    @property
    def device_info(self):
        return edf_device_info()