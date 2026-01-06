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
    }.get(phase.lower(), "mdi:help-circle")


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
        if not current or not current.get("start_dt"):
            return None

        phase = current["phase"].lower()
        current_start = current["start_dt"]

        # Use unified dataset so current slot is always included
        slots = sorted(
            self.coordinator.data.get("all_slots_sorted", []),
            key=lambda s: s["start_dt"]
        )

        try:
            idx = next(i for i, s in enumerate(slots) if s["start_dt"] == current_start)
        except StopIteration:
            return None

        block = [slots[idx]]

        # Expand backwards
        for s in reversed(slots[:idx]):
            if s["phase"].lower() == phase:
                block.insert(0, s)
            else:
                break

        # Expand forwards
        for s in slots[idx + 1:]:
            if s["phase"].lower() == phase:
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
        if not current or not current.get("start_dt"):
            return None

        phase = current["phase"].lower()
        current_start = current["start_dt"]

        slots = sorted(
            self.coordinator.data.get("all_slots_sorted", []),
            key=lambda s: s["start_dt"]
        )

        try:
            idx = next(i for i, s in enumerate(slots) if s["start_dt"] == current_start)
        except StopIteration:
            return None

        block = [slots[idx]]

        for s in reversed(slots[:idx]):
            if s["phase"].lower() == phase:
                block.insert(0, s)
            else:
                break

        for s in slots[idx + 1:]:
            if s["phase"].lower() == phase:
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
        current = self.coordinator.data.get("current_slot")
        if not current:
            return None

        current_phase = current["phase"].lower()

        # Sorted future slots
        slots = sorted(
            self.coordinator.data.get("next_24_hours", []),
            key=lambda s: s["start_dt"]
        )

        if not slots:
            return None

        # Find first slot whose phase differs from current block
        first_next = next(
            (s for s in slots if s["phase"].lower() != current_phase),
            None
        )

        if not first_next:
            return None

        next_phase = first_next["phase"].lower()
        block = [first_next]
        idx = slots.index(first_next)

        # Merge forward
        for s in slots[idx + 1:]:
            if s["phase"].lower() == next_phase:
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
    """Sensor for the next green slot."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_green_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:leaf"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("next_24_hours", []),
            key=lambda s: s["start_dt"]
        )

        first = next((s for s in slots if s["phase"].lower() == "green"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"].lower() == "green":
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
            "phase": "Green",
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
    """Sensor for the next amber slot."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Amber Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_amber_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    def _find_block(self):
        slots = sorted(
            self.coordinator.data.get("next_24_hours", []),
            key=lambda s: s["start_dt"]
        )

        first = next((s for s in slots if s["phase"].lower() == "amber"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"].lower() == "amber":
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
            "phase": "Amber",
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
            self.coordinator.data.get("next_24_hours", []),
            key=lambda s: s["start_dt"]
        )

        first = next((s for s in slots if s["phase"].lower() == "red"), None)
        if not first:
            return None

        block = [first]
        idx = slots.index(first)

        for s in slots[idx + 1:]:
            if s["phase"].lower() == "red":
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
            "phase": "Red",
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
        return current["phase"].lower() == "green" if current else None

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