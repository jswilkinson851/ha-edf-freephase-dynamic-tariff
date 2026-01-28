"""
Phase‑transition event engine for the EDF FreePhase Dynamic Tariff integration.

This module defines a single event entity responsible for emitting a clean,
semantic stream of tariff‑transition events derived from the coordinator’s
slot‑level data. It provides Home Assistant with a stable, automation‑friendly
interface for reacting to changes in the tariff’s colour‑coded phases.

Overview
--------

The EDF FreePhase Dynamic Tariff is expressed as a sequence of half‑hour slots,
each carrying a colour (phase), price, and validity window. While slot‑level
sensors expose the raw data, this module focuses on higher‑level transitions
that matter for automations and dashboards:

    • When the current phase changes (e.g., red → amber)
    • When the current phase is approaching its end
    • When the *next* phase colour changes (e.g., the next window becomes cheaper)

The event entity listens to the main coordinator and emits three event types:

    • ``edf_fpd_phase_changed``
        Fired whenever the tariff colour changes. Payload includes a structured
        ``phase`` object describing the new merged phase window.

    • ``edf_fpd_phase_ending_soon``
        Fired once per phase window when the current phase is within 30 minutes
        of ending.

    • ``edf_fpd_next_phase_changed``
        Fired when the colour of the upcoming phase window changes.

Payload Structure
-----------------

All events use a semantic, phase‑centric payload rather than exposing raw slot
dictionaries. A typical payload looks like:

    {
        "from": "red",
        "to": "amber",
        "phase": {
            "colour": "amber",
            "start": "2026‑01‑27T19:00:00+00:00",
            "end": "2026‑01‑27T21:30:00+00:00",
            "price_p_per_kwh": 33.5223,
            "slot_count": 5
        }
    }

Here, ``start`` and ``end`` describe the full merged phase window (all
consecutive slots with the same colour), and ``slot_count`` reflects the number
of slots in that window. This structure is stable, predictable, and easy to
consume in automations, templates, and dashboards.

Diagnostics
-----------

The entity maintains a persistent diagnostic record using Home Assistant’s
``Store`` helper. It tracks:

    • last event type
    • last event timestamp
    • last event payload
    • per‑event‑type counters
    • a rolling history of recent events

These diagnostics are exposed as state attributes and are also available to the
integration’s diagnostic sensor.

Initialisation Behaviour
------------------------

The entity is resilient to late or missing coordinator data. It waits for the
first valid slot before initialising its internal state and will not emit
spurious “null → phase” events. Once initialised, it compares each coordinator
update against its previous state to determine whether a transition has
occurred.

This module provides a robust, automation‑ready event stream that complements
the integration’s slot‑level and summary sensors, enabling users to build
responsive, energy‑aware behaviours around the dynamic tariff.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

# pylint: disable=import-error
from homeassistant.components.event import EventEntity  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.storage import Store  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # pyright: ignore[reportMissingImports]

# pylint: enable=import-error
from ..const import DOMAIN
from ..helpers import build_entity_id, edf_device_info, find_current_block

LOGGER = logging.getLogger(__name__)


# =====================================================================
# Persistent Diagnostics
# =====================================================================

class EventDiagnostics:
    """Persistent diagnostics helper for EDF FPD events."""

    def __init__(self, hass, entry_id: str, event_types: list[str]) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._event_types = event_types

        self._store = Store(
            hass,
            version=1,
            key=f"edf_fpd_event_diag_{entry_id}",
        )

        self._last_event_type: str | None = None
        self._last_event_timestamp: str | None = None
        self._counts: dict[str, int] = {etype: 0 for etype in event_types}
        self._history: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        saved = await self._store.async_load()
        if not saved:
            return

        self._last_event_type = saved.get("last_event_type")
        self._last_event_timestamp = saved.get("last_event_timestamp")
        self._counts.update(saved.get("counts", {}))
        self._history = saved.get("history", []) or []

    async def record(self, event_type: str, payload: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()

        self._last_event_type = event_type
        self._last_event_timestamp = now
        self._counts[event_type] = self._counts.get(event_type, 0) + 1

        self._history.append(
            {
                "event_type": event_type,
                "timestamp": now,
                "payload": payload,
            }
        )
        self._history = self._history[-5:]

        await self._store.async_save(
            {
                "last_event_type": self._last_event_type,
                "last_event_timestamp": self._last_event_timestamp,
                "counts": self._counts,
                "history": self._history,
            }
        )

    def get(self) -> dict[str, Any]:
        return {
            "last_event_type": self._last_event_type,
            "last_event_timestamp": self._last_event_timestamp,
            "event_counts": self._counts,
            "event_history": self._history,
        }


# =====================================================================
# Event Entity
# =====================================================================

class EDFFreePhaseDynamicSlotEventEntity(CoordinatorEntity, EventEntity):
    """Event entity emitting simplified, persistent tariff transition events."""

    _attr_name = "EDF FPD Phase Events"
    _attr_has_entity_name = False
    _attr_unique_id = "edf_freephase_dynamic_tariff_tariff_slot_phase_events"
    _attr_entity_registry_enabled_default = True

    _attr_event_types = [
        "edf_fpd_phase_changed",
        "edf_fpd_phase_ending_soon",
        "edf_fpd_next_phase_changed",
    ]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)

        self._entry = coordinator.config_entry

        self._attr_entity_id = build_entity_id(
            domain="event",
            object_id="phase_events",
            tariff="fpd",
        )

        self._attr_device_info = edf_device_info(self._entry.entry_id)

        # Previous state
        self._prev_phase: str | None = None
        self._prev_slot: dict[str, Any] | None = None
        self._prev_next_phase_colour: str | None = None

        # Track whether "ending soon" has fired for this phase window
        self._ending_soon_fired_for_end_dt: str | None = None

        # Persistent diagnostics
        self._diag = EventDiagnostics(
            coordinator.hass,
            self._entry.entry_id,
            self._attr_event_types,
        )

        self._last_event_payload: dict[str, Any] | None = None

    async def async_added_to_hass(self) -> None:
        """Initialise diagnostics and subscribe to coordinator updates."""
        await super().async_added_to_hass()

        await self._diag.async_load()

        # Register for diagnostic sensor
        self.hass.data.setdefault(DOMAIN, {}).setdefault(self._entry.entry_id, {})[
            "event_entity"
        ] = self

        # Always subscribe to coordinator updates
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @property
    def native_value(self) -> str | None:
        diag = self._diag.get()
        return diag.get("last_event_timestamp")

    # ------------------------------------------------------------------
    # Emit helper
    # ------------------------------------------------------------------

    def _emit(self, event_type: str, payload: dict) -> None:
        debug_enabled = self.hass.states.is_state("switch.edf_debug_logging", "on")

        self._last_event_payload = {
            "event_type": event_type,
            "payload": payload,
        }

        if debug_enabled:
            LOGGER.debug(
                "EDF INT. EVENTS | %-25s | payload=%s",
                event_type,
                payload,
            )
            self.hass.bus.async_fire(
                "edf_fpd_debug",
                {"event_type": event_type, "payload": payload},
            )

        self._trigger_event(event_type, {"entity_id": self.entity_id, **payload})
        self.hass.async_create_task(self._diag.record(event_type, payload))
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
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

    def _handle_coordinator_update(self) -> None:
        self.hass.async_create_task(self.async_update())

    # ------------------------------------------------------------------
    # Phase payload helper (merged phase window)
    # ------------------------------------------------------------------

    def _build_phase_payload(self, block: list[dict[str, Any]] | None) -> dict[str, Any]:
        """Convert a merged phase block into a semantic phase payload."""
        if not block:
            return {}

        first = block[0]
        last = block[-1]

        return {
            "colour": first.get("phase"),
            "start": first.get("start_dt"),
            "end": last.get("end_dt"),
            "price_p_per_kwh": first.get("value"),
            "slot_count": len(block),
        }

    def _find_current_phase_block(
        self,
        current_slot: dict[str, Any],
        all_slots: list[dict[str, Any]],
    ) -> list[dict[str, Any]] | None:
        """Return the full merged phase block containing the current slot."""
        if not current_slot or not all_slots:
            return None

        block = find_current_block(all_slots, current_slot)
        return block or None

    # ------------------------------------------------------------------
    # Next phase colour helper
    # ------------------------------------------------------------------

    def _find_next_phase_colour(
        self,
        current_slot: dict[str, Any],
        all_slots: list[dict[str, Any]],
    ) -> str | None:
        current_end = current_slot.get("end_dt")
        if not current_end:
            return None

        try:
            current_end_dt = datetime.fromisoformat(current_end)
        except Exception:
            return None

        for slot in all_slots:
            try:
                start_dt = datetime.fromisoformat(slot["start_dt"])
            except Exception:
                continue

            if start_dt > current_end_dt and slot.get("phase") != current_slot.get("phase"):
                return slot.get("phase")

        return None

    # ------------------------------------------------------------------
    # Main update logic
    # ------------------------------------------------------------------

    async def async_update(self) -> None:
        """Handle coordinator updates and emit simplified events."""
        await super().async_update()

        data = self.coordinator.data or {}
        current = data.get("current_slot")
        all_slots = data.get("all_slots_sorted", [])

        # If coordinator still has no data, remain available but do nothing
        if not current:
            return

        phase = current.get("phase")

        # First valid coordinator data — initialise state but do NOT emit events
        if self._prev_slot is None or self._prev_phase is None:
            self._prev_slot = current
            self._prev_phase = phase
            self._prev_next_phase_colour = self._find_next_phase_colour(current, all_slots)
            self._ending_soon_fired_for_end_dt = None
            return

        # Compute the full merged phase block for the current slot
        current_block = self._find_current_phase_block(current, all_slots)

        # -------------------------
        # 1. Phase change detection
        # -------------------------
        if phase != self._prev_phase:
            self._emit(
                "edf_fpd_phase_changed",
                {
                    "from": self._prev_phase,
                    "to": phase,
                    "phase": self._build_phase_payload(current_block),
                },
            )
            self._prev_phase = phase
            self._ending_soon_fired_for_end_dt = None

        # -------------------------
        # 2. Phase ending soon (30 minutes)
        # -------------------------
        end_dt_str = current.get("end_dt")
        if end_dt_str:
            try:
                end_dt = datetime.fromisoformat(end_dt_str)
            except Exception:
                end_dt = None

            if end_dt:
                now = datetime.now(timezone.utc)
                if (
                    end_dt - now <= timedelta(minutes=30)
                    and self._ending_soon_fired_for_end_dt != end_dt_str
                ):
                    self._emit(
                        "edf_fpd_phase_ending_soon",
                        {
                            "phase": phase,
                            "ends_at": end_dt_str,
                            "phase_window": self._build_phase_payload(current_block),
                        },
                    )
                    self._ending_soon_fired_for_end_dt = end_dt_str

        # -------------------------
        # 3. Next phase change detection
        # -------------------------
        next_phase_colour = self._find_next_phase_colour(current, all_slots)

        if next_phase_colour != self._prev_next_phase_colour:
            self._emit(
                "edf_fpd_next_phase_changed",
                {
                    "from": self._prev_next_phase_colour,
                    "to": next_phase_colour,
                },
            )
            self._prev_next_phase_colour = next_phase_colour


# ----------------------------------------------------------------------
# End of `/events/slot_events.py`
# ----------------------------------------------------------------------
