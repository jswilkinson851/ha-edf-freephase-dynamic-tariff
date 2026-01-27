"""
Slot and Phase Transition Events for EDF FreePhase Dynamic Tariff.

This module defines a single EventEntity that emits structured Home Assistant
events whenever tariff slot or phase transitions occur.

Events emitted:
    - slot_changed
    - phase_changed
    - phase_started
    - phase_ended
    - phase_block_changed
    - next_phase_changed
    - next_green_phase_changed
    - next_amber_phase_changed
    - next_red_phase_changed

The entity listens to the main EDFCoordinator and compares the new dataset
against previously-seen values. Only transitions emit events; steady-state
conditions do not.

This entity is intentionally phase‑first in naming. Internally, the integration
still uses "block" for merged phases, but events expose canonical "phase"
terminology to users for long‑term consistency.
"""

from __future__ import annotations

import logging

# pylint: disable=import-error
from homeassistant.components.event import EventEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]

from ..diagnostics import EventDiagnostics

# pylint: enable=import-error
from ..helpers import (
    build_entity_id,
    edf_device_info,
    find_current_block,
    find_next_phase_block,
    format_phase_block,
    group_phase_blocks,
)

LOGGER = logging.getLogger(__name__)


class EDFFreePhaseDynamicSlotEventEntity(CoordinatorEntity, EventEntity):
    """
    Event entity emitting slot‑ and phase‑transition events.

    This entity exposes the timestamp of the last event fired as its state,
    and emits structured events whenever the coordinator's dataset changes
    in a meaningful way.
    """

    _attr_name = "EDF FPD Tariff Slot & Phase Events"
    _attr_has_entity_name = True
    _attr_unique_id = "edf_freephase_dynamic_tariff_tariff_slot_phase_events"

    # enable the entity by default
    _attr_entity_registry_enabled_default = True

    # Canonical event types exposed to Home Assistant
    _attr_event_types = [
        "edf_fpd_slot_changed",
        "edf_fpd_phase_changed",
        "edf_fpd_phase_started",
        "edf_fpd_phase_ended",
        "edf_fpd_phase_block_changed",
        "edf_fpd_next_phase_changed",
        "edf_fpd_next_green_phase_changed",
        "edf_fpd_next_amber_phase_changed",
        "edf_fpd_next_red_phase_changed",
    ]

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._entry = coordinator.config_entry

        self._attr_entity_id = build_entity_id(
            domain="event",
            object_id="tariff_slot_phase_events",
            tariff="fpd",
        )

        self._attr_device_info = edf_device_info(self._entry.entry_id)

        # Previous values for comparison
        self._prev_slot = None
        self._prev_phase = None
        self._prev_block = None
        self._prev_next_phase = None
        self._prev_next_green = None
        self._prev_next_amber = None
        self._prev_next_red = None

        # Centralised diagnostics helper
        self._diag = EventDiagnostics(
            coordinator.hass,
            self._entry.entry_id,
            self._attr_event_types,
        )

        self._last_event_payload = None

    async def async_added_to_hass(self):
        """Subscribe to coordinator updates after entity is added."""
        await super().async_added_to_hass()

        data = self.coordinator.data or {}

        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])
        next_24 = data.get("next_24_hours", [])

        # If coordinator hasn't populated data yet, avoid false transitions
        if current is None:
            return

        self._prev_slot = current
        self._prev_phase = current.get("phase")
        self._prev_block = find_current_block(all_slots, current)

        blocks = group_phase_blocks(all_slots)
        if self._prev_block and self._prev_block in blocks:
            idx = blocks.index(self._prev_block)
            self._prev_next_phase = blocks[idx + 1] if idx + 1 < len(blocks) else None
        else:
            self._prev_next_phase = None

        self._prev_next_green = find_next_phase_block(next_24, "green")
        self._prev_next_amber = find_next_phase_block(next_24, "amber")
        self._prev_next_red = find_next_phase_block(next_24, "red")

        # Subscribe AFTER entity is fully registered
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @property
    def native_value(self):
        """Return the timestamp of the last event fired."""
        diag = self._diag.get()
        return diag.get("last_event_timestamp")

    # ------------------------------------------------------------------
    # Internal helper: emit event + diagnostics + debug logging
    # ------------------------------------------------------------------

    def _emit(self, event_type: str, payload: dict):
        """Emit an event, update diagnostics, and log if debug is enabled."""
        debug_enabled = self.hass.states.is_state("switch.edf_debug_logging", "on")

        # Store last payload for entity attributes
        self._last_event_payload = {
            "event_type": event_type,
            "payload": payload,
        }

        if debug_enabled:
            LOGGER.debug(
                "EDF INT. EVE ¦ EVENT FIRED | %-25s | payload=%s",
                event_type,
                payload,
            )

            # Fire a structured debug event onto the HA event bus
            self.hass.bus.async_fire(
                "edf_fpd_debug",
                {
                    "event_type": event_type,
                    "payload": payload,
                },
            )

        # Emit event to Home Assistant
        self._trigger_event(event_type, {"entity_id": self.entity_id, **payload})

        # Update diagnostics
        self._diag.record(event_type, payload)

        # Update entity state in Home Assistant
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Expose last event metadata for UI and automations."""
        diag = self._diag.get()
        return {
            "last_event_type": diag.get("last_event_type"),
            "last_event_timestamp": diag.get("last_event_timestamp"),
            "last_event_payload": self._last_event_payload,
            "event_counts": diag.get("event_counts"),
            "event_history": diag.get("event_history"),
        }

    # ------------------------------------------------------------------
    # Coordinator update hook
    # ------------------------------------------------------------------

    def _handle_coordinator_update(self):
        """Schedule async_update when coordinator refreshes."""
        LOGGER.debug("EDF INT. EVE ¦ EVENT ENTITY RECEIVED COORDINATOR UPDATE")
        self.hass.async_create_task(self.async_update())

    async def async_update(self):
        """Handle coordinator updates and emit events for transitions."""
        await super().async_update()

        data = self.coordinator.data or {}
        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])
        next_24 = data.get("next_24_hours", [])

        # -------------------------
        # 1. Slot change detection
        # -------------------------
        if current != self._prev_slot:
            self._emit(
                "edf_fpd_slot_changed",
                {
                    "from": self._prev_slot,
                    "to": current,
                },
            )
            self._prev_slot = current

        # -------------------------
        # 2. Phase change detection
        # -------------------------
        phase = current.get("phase") if current else None

        if phase != self._prev_phase:
            if self._prev_phase is not None:
                self._emit("edf_fpd_phase_ended", {"phase": self._prev_phase})

            if phase is not None:
                self._emit("edf_fpd_phase_started", {"phase": phase})

            self._emit(
                "edf_fpd_phase_changed",
                {"from": self._prev_phase, "to": phase, "slot": current},
            )

            self._prev_phase = phase

        # -------------------------
        # 3. Merged phase block change
        # -------------------------
        block = find_current_block(all_slots, current)
        if block != self._prev_block:
            self._emit(
                "edf_fpd_phase_block_changed",
                {
                    "from": format_phase_block(self._prev_block) if self._prev_block else None,
                    "to": format_phase_block(block) if block else None,
                },
            )
            self._prev_block = block

        # -------------------------
        # 4. Next phase block change
        # -------------------------
        blocks = group_phase_blocks(all_slots)
        next_phase = None
        if block and block in blocks:
            idx = blocks.index(block)
            if idx + 1 < len(blocks):
                next_phase = blocks[idx + 1]

        if next_phase != self._prev_next_phase:
            self._emit(
                "edf_fpd_next_phase_changed",
                {
                    "from": format_phase_block(self._prev_next_phase) if self._prev_next_phase else None,
                    "to": format_phase_block(next_phase) if next_phase else None,
                },
            )
            self._prev_next_phase = next_phase

        # -------------------------
        # 5. Next {colour} phase changes
        # -------------------------
        for colour in ("green", "amber", "red"):
            block = find_next_phase_block(next_24, colour)
            prev = getattr(self, f"_prev_next_{colour}")

            if block != prev:
                self._emit(
                    f"edf_fpd_next_{colour}_phase_changed",
                    {
                        "phase": colour,
                        "from": format_phase_block(prev) if prev else None,
                        "to": format_phase_block(block) if block else None,
                    },
                )
                setattr(self, f"_prev_next_{colour}", block)

# ----------------------------------------------------------------------------------
# End of slot_events.py
# ----------------------------------------------------------------------------------
