"""
Aligned refresh scheduler for the EDF FreePhase Dynamic Tariff integration.

This module implements time‑aligned refresh intervals with optional jitter
to avoid API load spikes. It encapsulates all scheduling behaviour used by
the coordinator, exposing timing details for diagnostics while keeping the
coordinator itself clean and focused.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta
from typing import Callable, Awaitable

from homeassistant.helpers.event import async_call_later


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
            This ensures that scheduling always targets the next valid interval.
        """

        if self._next_boundary_utc is None:
            self._initialise_boundary()

        now = datetime.now(timezone.utc)
        while self._next_boundary_utc <= now:
            self._next_boundary_utc += self.scan_interval

    def _seconds_until_boundary(self) -> float:
        """
        Compute the number of seconds until the next aligned boundary.

        Returns:
            A positive float representing the delay until the next refresh.

        Notes:
            If the computed delta is non‑positive, the scan interval is used.
        """

        self._initialise_boundary()
        self._advance_boundary()

        now = datetime.now(timezone.utc)
        delta = (self._next_boundary_utc - now).total_seconds()

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