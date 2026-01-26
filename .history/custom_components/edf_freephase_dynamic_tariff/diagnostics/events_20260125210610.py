"""
Event Diagnostics Helper for EDF FreePhase Dynamic Tariff.

This module provides a small, structured helper class used by event‑emitting
entities (e.g., SlotEventEntity) to record:

    - last event type
    - last event timestamp
    - per‑event counters

The diagnostics sensor can then read these values cleanly without needing to
know how they are stored internally.

This keeps the event entity focused on transition detection, and the
diagnostics sensor focused on presentation, while this module handles the
shared state and structure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from ..const import DOMAIN


class EventDiagnostics:
    """
    Centralised diagnostics store for event entities.

    Each config entry gets its own diagnostics bucket under:

        hass.data[DOMAIN]["event_diagnostics"][entry_id]

    This helper wraps that structure and provides:

        - record(event_type): increment counters + update timestamps
        - get(): return a structured diagnostics dict
    """

    def __init__(self, hass, entry_id: str, event_types: list[str]):
        self.hass = hass
        self.entry_id = entry_id

        # Ensure the global structure exists
        domain_store = hass.data.setdefault(DOMAIN, {})
        diag_store = domain_store.setdefault("event_diagnostics", {})

        # Ensure this entry has a diagnostics bucket
        if entry_id not in diag_store:
            diag_store[entry_id] = {
                "last_event_type": None,
                "last_event_timestamp": None,
                "counters": {etype: 0 for etype in event_types},
            }

        self._store = diag_store[entry_id]

        # Ensure counters always exist (defensive)
        self._store.setdefault("counters", {etype: 0 for etype in event_types})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, event_type: str, payload: dict | None = None) -> None:
        """Record an event occurrence."""
        now = datetime.now(timezone.utc).isoformat()

        self._store["last_event_type"] = event_type
        self._store["last_event_timestamp"] = now

        # Increment counter
        self._store["counters"][event_type] = self._store["counters"].get(event_type, 0) + 1

        # Store last payload
        self._store["last_event_payload"] = payload

        # Append to history (rolling 20)
        history = self._store.setdefault("history", [])
        history.append({
            "timestamp": now,
            "event_type": event_type,
            "payload": payload,
        })
        if len(history) > 20:
            history.pop(0)

    def get(self) -> Dict[str, Any]:
        return {
            "last_event_type": self._store.get("last_event_type"),
            "last_event_timestamp": self._store.get("last_event_timestamp"),
            "last_event_payload": self._store.get("last_event_payload"),
            "event_counters": dict(self._store.get("counters", {})),
            "event_history": list(self._store.get("history", [])),
        }

