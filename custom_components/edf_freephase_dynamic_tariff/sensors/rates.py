"""
Daily rate summary sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import (
    edf_device_info,
    group_phase_blocks,
    format_phase_block,
)


# ---------------------------------------------------------------------------
# Today's Rates Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTodaysRatesSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of today's merged phase windows."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Today's Rates Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_todays_rates_summary"
        self._attr_icon = "mdi:calendar-clock"

    def _merge_blocks(self):
        slots = self.coordinator.data.get("today_24_hours") or []
        return group_phase_blocks(slots)

    @property
    def native_value(self):
        blocks = self._merge_blocks()
        return len(blocks) if blocks else None

    @property
    def extra_state_attributes(self):
        blocks = self._merge_blocks()
        if not blocks:
            return {}

        return {
            f"phase_{i}": format_phase_block(block)
            for i, block in enumerate(blocks, start=1)
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Tomorrow's Rates Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTomorrowsRatesSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of tomorrow's merged phase windows."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tomorrow's Rates Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_tomorrows_rates_summary"
        self._attr_icon = "mdi:calendar-arrow-right"

    def _merge_blocks(self):
        slots = self.coordinator.data.get("tomorrow_24_hours") or []
        return group_phase_blocks(slots)

    @property
    def native_value(self):
        blocks = self._merge_blocks()
        return len(blocks) if blocks else None

    @property
    def extra_state_attributes(self):
        blocks = self._merge_blocks()
        if not blocks:
            return {}

        return {
            f"phase_{i}": format_phase_block(block)
            for i, block in enumerate(blocks, start=1)
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Yesterday's Rates Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicYesterdayPhasesSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of yesterday's merged phase windows."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Yesterday Phases Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_yesterdays_phases_summary"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("yesterday_24_hours", [])
        if not slots:
            return None

        windows = group_phase_blocks(slots)
        return len(windows)

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("yesterday_24_hours", [])
        if not slots:
            return {}

        windows = group_phase_blocks(slots)

        return {
            f"phase_{i}": format_phase_block(block)
            for i, block in enumerate(windows, start=1)
        }

    @property
    def device_info(self):
        return edf_device_info()