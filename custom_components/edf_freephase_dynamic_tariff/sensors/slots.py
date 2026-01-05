"""
Slot colour and next-slot sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations
#---DO NOT ADD ANYTHING ABOVE THIS LINE---

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime, as_local
from .helpers import edf_device_info


# Utility: format start/end/duration consistently
def _format_slot_times(slot):
    start = parse_datetime(slot["start"])
    end = parse_datetime(slot["end"])

    if start:
        start_local = as_local(start)
        start_fmt = start_local.strftime("%H:%M on %d/%m/%Y")
    else:
        start_fmt = None

    if end:
        end_local = as_local(end)
        end_fmt = end_local.strftime("%H:%M on %d/%m/%Y")
        duration = (end_local - start_local).total_seconds() / 60 if start else None
    else:
        end_fmt = None
        duration = None

    return start_fmt, end_fmt, duration


def _icon_for_phase(phase):
    return {
        "green": "mdi:leaf",
        "amber": "mdi:clock-outline",
        "red": "mdi:alert",
    }.get(phase, "mdi:help-circle")


# ---------------------------------------------------------------------------
# Current Slot Colour
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the current slot's colour, including full block details."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"
        self._attr_icon = "mdi:circle-slice-3"

    def _find_block(self):
        current = self.coordinator.data.get("current_slot")
        if not current:
            return None

        phase = current["phase"]

        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        try:
            idx = next(i for i, s in enumerate(slots) if s["start"] == current["start"])
        except StopIteration:
            return None

        block = [current]

        # Backwards
        for s in reversed(slots[:idx]):
            if s["phase"] == phase:
                block.insert(0, s)
            else:
                break

        # Forwards
        for s in slots[idx + 1:]:
            if s["phase"] == phase:
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] if current else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": block[0]["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase(block[0]["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Current Block Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicCurrentBlockSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of the current colour block, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Block Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_block_summary"
        self._attr_icon = "mdi:timeline-clock"

    def _find_block(self):
        current = self.coordinator.data.get("current_slot")
        if not current:
            return None

        phase = current["phase"]

        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        try:
            idx = next(i for i, s in enumerate(slots) if s["start"] == current["start"])
        except StopIteration:
            return None

        block = [current]

        # Backwards
        for s in reversed(slots[:idx]):
            if s["phase"] == phase:
                block.insert(0, s)
            else:
                break

        # Forwards
        for s in slots[idx + 1:]:
            if s["phase"] == phase:
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["value"] if current else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": block[0]["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "current_price": block[0]["value"],
            "icon": _icon_for_phase(block[0]["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Block Summary
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextBlockSummarySensor(CoordinatorEntity, SensorEntity):
    """Summary of the next colour block, including start, end, duration, and price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Block Summary"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_block_summary"
        self._attr_icon = "mdi:timeline-clock-outline"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        if not slots:
            return None

        first = slots[0]
        phase = first["phase"]

        block = [first]

        for s in slots[1:]:
            if s["phase"] == phase:
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        block = self._find_block()
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": block[0]["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "first_slice_price": block[0]["value"],
            "icon": _icon_for_phase(block[0]["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Green Slot
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextGreenSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the next green slot's price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_green_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:leaf"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        first = next((s for s in slots if s["phase"] == "green"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"] == "green":
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        block = self._find_block()
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": "green",
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase("green"),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Amber Slot
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextAmberSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the next amber slot's price."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Amber Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_amber_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        first = next((s for s in slots if s["phase"] == "amber"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"] == "amber":
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        block = self._find_block()
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": "amber",
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase("amber"),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Next Red Slot
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicNextRedSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the next red slot."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Red Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_red_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:alert"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("todays_24_hours", []),
            key=lambda s: s["start"]
        )

        first = next((s for s in slots if s["phase"] == "red"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"] == "red":
                block.append(s)
            else:
                break

        return block

    @property
    def native_value(self):
        block = self._find_block()
        return block[0]["value"] if block else None

    @property
    def extra_state_attributes(self):
        block = self._find_block()
        if not block:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times({
            "start": block[0]["start"],
            "end": block[-1]["end"]
        })

        return {
            "phase": "red",
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase("red"),
        }

    @property
    def device_info(self):
        return edf_device_info()


# ---------------------------------------------------------------------------
# Is Green Slot (Binary)
# ---------------------------------------------------------------------------

class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, SensorEntity):
    """Binary sensor to show if the current slot is green."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Is Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] == "green" if current else None

    @property
    def extra_state_attributes(self):
        slot = self.coordinator.data.get("current_slot")
        if not slot:
            return {}

        start_fmt, end_fmt, duration = _format_slot_times(slot)

        return {
            "phase": slot["phase"],
            "start": start_fmt,
            "end": end_fmt,
            "duration_minutes": duration,
            "icon": _icon_for_phase(slot["phase"]),
        }

    @property
    def device_info(self):
        return edf_device_info()