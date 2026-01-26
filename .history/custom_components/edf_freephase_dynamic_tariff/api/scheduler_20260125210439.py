"""
Aligned refresh scheduler for the EDF FreePhase Dynamic Tariff integration.

This module implements time‑aligned refresh intervals with optional jitter
to avoid API load spikes. It encapsulates all scheduling behaviour used by
the coordinator, exposing timing details for diagnostics while keeping the
coordinator itself clean and focused.

Type‑Safety Improvements
------------------------
Recent updates introduce explicit type‑narrowing and defensive fallbacks to
satisfy static type checkers such as Pylance. These checks do not alter runtime
behaviour: `_initialise_boundary()` and `_advance_boundary()` still guarantee
that `_next_boundary_utc` is a valid `datetime`. The additional guards simply
make this contract explicit for static analysis tools.

Design Notes
------------
The scheduler guarantees:
    - All refreshes occur on aligned boundaries (e.g., every 30 minutes).
    - Jitter is applied to avoid API stampedes.
    - `_next_boundary_utc` always represents the next valid aligned boundary.
    - Defensive `None` checks exist only for type‑safety and should never be
      hit during normal operation.
    - The scheduler exposes its internal timing state for diagnostics, but
      never performs API calls itself.

Inline Comments for Contributors
--------------------------------
Developers modifying this module should:
    - Preserve the alignment logic in `_initialise_boundary()`.
    - Keep type‑narrowing guards (`if boundary is None: return`) even if they
      appear redundant — they are required for static analysis correctness.
    - Avoid introducing blocking I/O; all scheduling must remain async.
    - Ensure any new diagnostic fields are updated in `_compute_delay()`.
"""


from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from homeassistant.helpers.event import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    async_call_later,
)


class AlignedScheduler:
    """
    Aligned refresh scheduler for the EDF FreePhase Dynamic Tariff integration.

    This class computes aligned refresh boundaries based on the configured
    scan interval, applies jitter to avoid API load spikes, and schedules
    callbacks using Home Assistant's async_call_later.
    """

    def __init__(self, hass, scan_interval: timedelta):
        self.hass = hass
        self.scan_interval = scan_interval

        self._next_boundary_utc = None
        self._unsub = None

        # exposed for diagnostics
        self.next_refresh_datetime = None
        self.next_refresh_delay = None
        self.next_refresh_jitter = None

    # -------------------------------------------------------------

    def _initialise_boundary(self) -> None:
        """
        Initialise the next aligned boundary based on the current UTC time.

        Notes:
            - The boundary is aligned to the scan interval.
            - This method is idempotent and only sets the boundary once.
        """

        if self._next_boundary_utc is not None:
            return

        now = datetime.now(timezone.utc)
        interval_seconds = int(self.scan_interval.total_seconds())

        seconds_today = now.hour * 3600 + now.minute * 60 + now.second
        next_boundary_seconds = ((seconds_today // interval_seconds) + 1) * interval_seconds

        day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        self._next_boundary_utc = day_start + timedelta(seconds=next_boundary_seconds)

    def _advance_boundary(self) -> None:
        """
        Advance the internal boundary until it lies in the future.

        Notes:
            - Ensures the next refresh always targets a future aligned interval.
            - Includes a defensive None‑check to satisfy static type checkers,
            though `_initialise_boundary()` guarantees a datetime at runtime.
        """

        if self._next_boundary_utc is None:
            self._initialise_boundary()

        now = datetime.now(timezone.utc)
        boundary = self._next_boundary_utc
        if boundary is None:
            return # defensive, but satisfies type checkers
        while boundary <= now:
            boundary += self.scan_interval

        self._next_boundary_utc = boundary

    def _seconds_until_boundary(self) -> float:
        """
        Compute the number of seconds until the next aligned boundary.

        Returns:
            A positive float representing the delay until the next refresh.

        Notes:
            - `_initialise_boundary()` and `_advance_boundary()` ensure the
              boundary is set, but a defensive fallback is included for type
              checkers.
            - If the computed delta is non‑positive, the scan interval is used.
        """

        self._initialise_boundary()
        self._advance_boundary()

        now = datetime.now(timezone.utc)
        boundary = self._next_boundary_utc
        if boundary is None:
            # Defensive fallback — should never happen, but satisfies type checkers
            return float(self.scan_interval.total_seconds())

        delta = (boundary - now).total_seconds()

        if delta <= 0:
            delta = self.scan_interval.total_seconds()

        return float(delta)

    # -------------------------------------------------------------

    def _compute_delay(self) -> float:
        """
        Compute the next refresh delay including jitter.

        Returns:
            The total delay in seconds before the next scheduled callback.

        Notes:
            - Jitter is uniformly random between 0 and 5 seconds.
            - Diagnostic fields are updated for visibility in HA.
        """

        base = self._seconds_until_boundary()
        jitter = random.uniform(0, 5)
        delay = base + jitter

        self.next_refresh_delay = delay
        self.next_refresh_jitter = jitter
        self.next_refresh_datetime = datetime.now(timezone.utc) + timedelta(seconds=delay)

        return delay

    # -------------------------------------------------------------

    async def schedule(self, callback: Callable[..., Awaitable]) -> None:
        """
        Schedule the next refresh callback.

        Parameters:
            callback: The coroutine to invoke when the delay expires.

        Notes:
            Any existing scheduled callback is cancelled before scheduling a new one.
        """

        if self._unsub:
            self._unsub()
            self._unsub = None

        delay = self._compute_delay()
        self._unsub = async_call_later(self.hass, delay, callback)

    async def shutdown(self) -> None:
        """
        Cancel any pending scheduled callback.

        Notes:
            Called when the integration is unloaded or Home Assistant shuts down.
        """

        if self._unsub:
            self._unsub()
            self._unsub = None
