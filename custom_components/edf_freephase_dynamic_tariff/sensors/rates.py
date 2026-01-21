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

from homeassistant.components.sensor import SensorEntity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from ..helpers import (
    edf_device_info,
    group_phase_blocks,
    format_phase_block,
)


# ---------------------------------------------------------------------------
# Base class for summary sensors
# ---------------------------------------------------------------------------


class _EDFFreePhaseDynamicBaseSummarySensor(CoordinatorEntity, SensorEntity):
    """
    Base class for daily phase‑summary sensors (yesterday, today, tomorrow).

    The coordinator exposes three lists of classified half‑hour slots:
        - yesterday_24_hours
        - today_24_hours
        - tomorrow_24_hours

    Each list contains normalised slot dictionaries with:
        {
            "start": ISO timestamp,
            "end": ISO timestamp,
            "value": float (p/kWh),
            "phase": "green" | "red" | "amber" | "free" | ...
        }

    This base class:
        - Selects the appropriate list via `day_key`.
        - Merges consecutive slots with the same phase using `group_phase_blocks()`.
        - Exposes the number of merged blocks as the sensor’s state.
        - Exposes each merged block as a formatted attribute via `format_phase_block()`.

    Subclasses define:
        - `day_key` (which dataset to read)
        - `friendly_name`
        - `icon`
        - `unique_id_suffix`

    The result is a compact, human‑readable summary of the day’s tariff phases,
    ideal for dashboards, automations, and energy‑planning visualisations.
    """

    day_key: str | None = None
    friendly_name: str | None = None
    icon: str | None = None
    unique_id_suffix: str | None = None

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = self.friendly_name
        self._attr_unique_id = f"edf_freephase_dynamic_tariff_{self.unique_id_suffix}"
        self._attr_icon = self.icon
        self._attr_native_unit_of_measurement = "Slots"

        # Ensure HA updates when coordinator updates
        self.async_on_remove(coordinator.async_add_listener(self.async_write_ha_state))

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

        return {f"phase_{i}": format_phase_block(block) for i, block in enumerate(blocks, start=1)}

    @property
    def device_info(self):
        """Return device info for this sensor from `helpers.py`."""
        return edf_device_info(self.coordinator.config_entry.entry_id)


# ---------------------------------------------------------------------------
# Today's Summary
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicTodaysRatesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """
    Summary of today's merged tariff phase windows.

    This sensor groups all half‑hour slots for the current day into contiguous
    phase blocks (e.g., a continuous “green” period). The state reports the
    number of merged blocks, while attributes expose each block’s timing,
    duration, and pricing context.

    Useful for:
        - Daily tariff overviews
        - Dashboard visualisation
        - Automations that react to phase changes
    """

    day_key = "today_24_hours"
    friendly_name = "Today's Phases Summary"
    icon = "mdi:calendar-clock"
    unique_id_suffix = "todays_phases_summary"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True


# ---------------------------------------------------------------------------
# Tomorrow's Summary
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicTomorrowsRatesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """
    Summary of tomorrow's merged tariff phase windows.

    This sensor provides a forward‑looking view of tomorrow’s pricing phases,
    allowing users and automations to plan ahead. Consecutive slots with the
    same phase are merged into a single block, giving a clean, high‑level
    representation of the next day’s tariff structure.

    Ideal for:
        - Pre‑heating / pre‑charging strategies
        - Energy‑aware scheduling
        - Visual dashboards showing tomorrow’s tariff profile
    """

    day_key = "tomorrow_24_hours"
    friendly_name = "Tomorrow's Phases Summary"
    icon = "mdi:calendar-arrow-right"
    unique_id_suffix = "tomorrows_phases_summary"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True


# ---------------------------------------------------------------------------
# Yesterday's Summary
# ---------------------------------------------------------------------------


class EDFFreePhaseDynamicYesterdayPhasesSummarySensor(_EDFFreePhaseDynamicBaseSummarySensor):
    """
    Summary of yesterday's merged tariff phase windows.

    This sensor provides a retrospective view of the previous day’s tariff
    phases, useful for analysis, reporting, and validating expected behaviour.
    As with other summary sensors, consecutive slots with the same phase are
    merged into a single block for clarity.

    Common use cases:
        - Comparing yesterday’s usage to tariff phases
        - Debugging or validating historical pricing behaviour
        - Building retrospective energy dashboards
    """

    day_key = "yesterday_24_hours"
    friendly_name = "Yesterday's Phases Summary"
    icon = "mdi:calendar-clock"
    unique_id_suffix = "yesterdays_phases_summary"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        # Ensure this entity is enabled and visible by default in Home Assistant's entity registry
        self._attr_entity_registry_enabled_default = True


# ---------------------------------------------------------------------------
# End of File
# ---------------------------------------------------------------------------
