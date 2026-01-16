"""
Daily phase summary sensors for the EDF FreePhase Dynamic Tariff integration.

These sensors summarise the merged phase windows for:
    - Yesterday
    - Today
    - Tomorrow

They rely on the coordinator providing:
    - yesterday_24_hours
    - today_24_hours
    - tomorrow_24_hours

Each of these is a list of classified slots:
    {
        "start": ISO string,
        "end": ISO string,
        "value": float,
        "phase": "green" | "red" | "amber" | "amber 1" | ... | "free"
    }

The helper `group_phase_blocks()` merges consecutive slots with the same
phase into a single phase block, preserving chronological order.
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
# Base class for summary sensors
# ---------------------------------------------------------------------------

class _EDFFreePhaseDynamicBaseSummarySensor(CoordinatorEntity, SensorEntity):
    """Base class for Today/Yesterday/Tomorrow summary sensors."""

    day_key: str = None
    friendly_name: str = None
    icon: str = None
    unique_id_suffix: str = None

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = self.friendly_name
        self._attr_unique_id = f"edf_freephase_dynamic_tariff_{self.unique_id_suffix}"
        self._attr_icon = self.icon

        # Ensure HA updates when coordinator updates
        self.async_on_remove(
            coordinator.async_add_listener(self.async_write_ha_state)
        )

    # ---------------------------------------------------------------------

    def _merge_blocks(self):
        """Return merged phase blocks for the configured day."""
        data = self.coordinator.data or {}
        slots = data.get(self.day_key) or []
        return group_phase_blocks(slots)

    # ---------------------------------------------------------------------

    @property
    def native_value(self):
        """Number of merged phase blocks."""
        blocks = self._merge_blocks()
        return len(blocks) if blocks else None

    @property
    def extra_state_attributes(self):
        """Return formatted phase blocks."""
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
# Today's Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTodaysRatesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """Summary of today's merged phase windows."""

    day_key = "today_24_hours"
    friendly_name = "Today's Phases Summary"
    icon = "mdi:calendar-clock"
    unique_id_suffix = "todays_phases_summary"


# ---------------------------------------------------------------------------
# Tomorrow's Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicTomorrowsRatesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """Summary of tomorrow's merged phase windows."""

    day_key = "tomorrow_24_hours"
    friendly_name = "Tomorrow's Phases Summary"
    icon = "mdi:calendar-arrow-right"
    unique_id_suffix = "tomorrows_phases_summary"


# ---------------------------------------------------------------------------
# Yesterday's Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicYesterdayPhasesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """Summary of yesterday's merged phase windows."""

    day_key = "yesterday_24_hours"
    friendly_name = "Yesterday's Phases Summary"
    icon = "mdi:calendar-clock"
    unique_id_suffix = "yesterdays_phases_summary"