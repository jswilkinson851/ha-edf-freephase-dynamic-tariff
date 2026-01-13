from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import monotonic

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.client import fetch_all_pages
from .api.parsing import build_unified_dataset, build_forecasts, strip_internal
from .api.scheduler import AlignedScheduler
from .sensors.helpers import normalise_slot

_LOGGER = logging.getLogger(__name__)


class EDFCoordinator(DataUpdateCoordinator):
    """Coordinator for EDF FreePhase Dynamic Tariff."""

    def __init__(self, hass, api_url, scan_interval):
        self.hass = hass
        self.api_url = api_url

        # Scan interval (used by diagnostics + scheduler)
        self._scan_interval = scan_interval

        # Scheduler (aligned refresh with jitter)
        self.scheduler = AlignedScheduler(hass, scan_interval)

        # Exposed for diagnostics (kept for backward compatibility)
        self._next_boundary_utc = None
        self._next_refresh_datetime = None
        self._next_refresh_delay = None
        self._next_refresh_jitter = None

        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=None,  # We now schedule manually
        )

    async def _async_update_data(self):
        """Fetch data from EDF API and build unified datasets."""
        start_time = monotonic()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        try:
            # --------------------------------------
            # Fetch raw pages from EDF API
            # --------------------------------------
            raw_items = await fetch_all_pages(self.api_url, max_pages=3)

            if not raw_items:
                raise ValueError("EDF API returned no results")

            # --------------------------------------
            # Build unified internal dataset
            # --------------------------------------
            unified = build_unified_dataset(raw_items)

            # --------------------------------------
            # Build forecast views (today/tomorrow/yesterday/next24)
            # --------------------------------------
            forecasts = build_forecasts(unified, now)

            # --------------------------------------
            # Determine current slot
            # --------------------------------------
            current_raw = next(
                (
                    slot
                    for slot in unified
                    if slot["_start_dt_obj"] <= now < slot["_end_dt_obj"]
                ),
                None,
            )

            if current_raw:
                current_slot = normalise_slot(strip_internal([current_raw])[0])
                current_price = current_slot["value"]
            else:
                # Fallback: if now is outside all slot ranges, use the first slot’s phase
                first = unified[0]
                current_price = first["value"]
                current_slot = normalise_slot(
                    {
                        "start": None,
                        "end": None,
                        "start_dt": None,
                        "end_dt": None,
                        "value": current_price,
                        "phase": first["phase"],
                        "currency": "GBP",
                    }
                )

            # --------------------------------------
            # Next price
            # --------------------------------------
            next_price = next(
                (slot["value"] for slot in unified if slot["_start_dt_obj"] > now),
                None,
            )

            # --------------------------------------
            # Strip internal fields + normalise
            # --------------------------------------
            all_slots_sorted = [
                normalise_slot(slot) for slot in strip_internal(unified)
            ]

            next_24_hours = [
                normalise_slot(slot)
                for slot in strip_internal(forecasts["next_24_hours"])
            ]
            today_24_hours = [
                normalise_slot(slot)
                for slot in strip_internal(forecasts["today_24_hours"])
            ]
            tomorrow_24_hours = [
                normalise_slot(slot)
                for slot in strip_internal(forecasts["tomorrow_24_hours"])
            ]
            yesterday_24_hours = [
                normalise_slot(slot)
                for slot in strip_internal(forecasts["yesterday_24_hours"])
            ]

            api_latency_ms = int((monotonic() - start_time) * 1000)

            # --------------------------------------
            # Final coordinator data
            # --------------------------------------
            return {
                "current_price": current_price,
                "next_price": next_price,
                "current_slot": current_slot,
                "next_24_hours": next_24_hours,
                "today_24_hours": today_24_hours,
                "tomorrow_24_hours": tomorrow_24_hours,
                "yesterday_24_hours": yesterday_24_hours,
                "all_slots_sorted": all_slots_sorted,
                "api_latency_ms": api_latency_ms,
                "last_updated": now_iso,
                "coordinator_status": "ok",
            }

        except Exception as err:
            _LOGGER.error("API request failed: %s", err)
            return {
                "current_price": None,
                "next_price": None,
                "current_slot": None,
                "next_24_hours": [],
                "today_24_hours": [],
                "tomorrow_24_hours": [],
                "yesterday_24_hours": [],
                "all_slots_sorted": [],
                "api_latency_ms": None,
                "last_updated": None,
                "coordinator_status": "error",
            }

    # -------------------------------------------------------------------------
    # Aligned scheduling (delegated to AlignedScheduler)
    # -------------------------------------------------------------------------

    def _sync_scheduler_state(self) -> None:
        """Copy scheduler state onto coordinator fields for diagnostics."""
        self._next_boundary_utc = getattr(self.scheduler, "_next_boundary_utc", None)
        self._next_refresh_datetime = getattr(
            self.scheduler, "next_refresh_datetime", None
        )
        self._next_refresh_delay = self.scheduler.next_refresh_delay
        self._next_refresh_jitter = getattr(
            self.scheduler, "next_refresh_jitter", None
        )

    async def async_config_entry_first_refresh(self) -> None:
        """Perform the first refresh immediately, then start aligned scheduling."""
        _LOGGER.debug("Performing immediate first refresh for EDF coordinator")
        await super().async_config_entry_first_refresh()
        await self.scheduler.schedule(self._handle_refresh)
        self._sync_scheduler_state()

    async def _handle_refresh(self, _now=None) -> None:
        """Perform a refresh and then schedule the next one."""
        _LOGGER.debug("Running aligned EDF coordinator refresh")
        await self.async_refresh()
        self.async_update_listeners()
        await self.scheduler.schedule(self._handle_refresh)
        self._sync_scheduler_state()

    async def async_shutdown(self) -> None:
        """Clean up scheduled callbacks."""
        await self.scheduler.shutdown()