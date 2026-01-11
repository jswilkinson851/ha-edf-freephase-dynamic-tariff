from __future__ import annotations

import aiohttp
import async_timeout
import logging
import random

from datetime import datetime, time, timezone, timedelta
from time import monotonic

import dateutil.parser

from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def classify_slot(start_time, price):
    """Return capitalised phase name based on time-of-day and price."""
    dt = dateutil.parser.isoparse(start_time)
    t = dt.time()

    if price <= 0:
        return "Green"

    if time(23, 0) <= t or t < time(6, 0):
        return "Green"
    if time(6, 0) <= t < time(16, 0):
        return "Amber"
    if time(16, 0) <= t < time(19, 0):
        return "Red"
    if time(19, 0) <= t < time(23, 0):
        return "Amber"

    return "Amber"


class EDFCoordinator(DataUpdateCoordinator):
    """Coordinator for EDF FreePhase Dynamic Tariff."""

    def __init__(self, hass, api_url, scan_interval):
        self.hass = hass
        self.api_url = api_url

        # Store scan interval for aligned scheduling
        self._scan_interval = scan_interval

        # Debug fields for the new debug sensor
        self._next_refresh_datetime = None
        self._next_refresh_delay = None
        self._next_refresh_jitter = None
        self._unsub_refresh = None

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
        tomorrow = (now + timedelta(days=1)).date()

        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    all_results = []
                    url = self.api_url
                    page_count = 0
                    max_pages = 3  # yesterday + today + tomorrow

                    while url and page_count < max_pages:
                        page_count += 1
                        resp = await session.get(url)
                        resp.raise_for_status()

                        try:
                            data = await resp.json()
                        except Exception:
                            _LOGGER.error("EDF API returned non-JSON on page %s", page_count)
                            break

                        results_page = data.get("results")
                        if not isinstance(results_page, list):
                            _LOGGER.error("EDF API page %s missing/invalid results", page_count)
                            break

                        all_results.extend(results_page)
                        url = data.get("next")

            api_latency_ms = int((monotonic() - start_time) * 1000)

            if not all_results:
                raise ValueError("EDF API returned no results")

            # ---- BUILD UNIFIED SORTED DATASET ----
            unified = []
            for item in all_results:
                start_raw = item["valid_from"]
                end_raw = item["valid_to"]

                start_dt = dateutil.parser.isoparse(start_raw)
                end_dt = dateutil.parser.isoparse(end_raw)

                unified.append({
                    "start": start_raw,
                    "end": end_raw,
                    "start_dt": start_dt.isoformat(),
                    "end_dt": end_dt.isoformat(),
                    "value": item["value_inc_vat"],
                    "phase": classify_slot(start_raw, item["value_inc_vat"]),
                    "currency": "GBP",
                    "_start_dt_obj": start_dt,
                    "_end_dt_obj": end_dt,
                })

            unified.sort(key=lambda s: s["_start_dt_obj"])

            # ---- ROLLING 24-HOUR FORECAST ----
            future = [slot for slot in unified if slot["_start_dt_obj"] >= now]
            next_24_hours = future[:48]

            # ---- TOMORROW'S FORECAST ----
            tomorrow_24_hours = [
                slot for slot in unified
                if slot["_start_dt_obj"].date() == tomorrow
            ]

            # ---- CURRENT SLOT ----
            current_slot = None
            for slot in unified:
                if slot["_start_dt_obj"] <= now < slot["_end_dt_obj"]:
                    current_slot = {
                        "start": slot["start"],
                        "end": slot["end"],
                        "start_dt": slot["start_dt"],
                        "end_dt": slot["end_dt"],
                        "value": slot["value"],
                        "phase": slot["phase"],
                        "currency": "GBP",
                    }
                    break

            if current_slot:
                current_price = current_slot["value"]
            else:
                current_price = unified[0]["value"]
                current_slot = {
                    "start": None,
                    "end": None,
                    "start_dt": None,
                    "end_dt": None,
                    "value": current_price,
                    "phase": unified[0]["phase"],
                    "currency": "GBP",
                }

            # ---- NEXT PRICE ----
            next_price = None
            for slot in unified:
                if slot["_start_dt_obj"] > now:
                    next_price = slot["value"]
                    break

            # ---- CLEAN INTERNAL FIELDS ----
            def strip_internal(slots):
                cleaned = []
                for s in slots:
                    s2 = dict(s)
                    s2.pop("_start_dt_obj", None)
                    s2.pop("_end_dt_obj", None)
                    cleaned.append(s2)
                return cleaned

            all_slots_sorted = strip_internal(unified)
            next_24_hours = strip_internal(next_24_hours)
            tomorrow_24_hours = strip_internal(tomorrow_24_hours)

            return {
                "current_price": current_price,
                "next_price": next_price,
                "current_slot": current_slot,
                "next_24_hours": next_24_hours,
                "tomorrow_24_hours": tomorrow_24_hours,
                "all_slots_sorted": all_slots_sorted,
                "api_latency_ms": api_latency_ms,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "coordinator_status": "ok",
            }

        except Exception as err:
            _LOGGER.error("API request failed: %s", err)
            return {
                "current_price": None,
                "next_price": None,
                "current_slot": None,
                "next_24_hours": [],
                "tomorrow_24_hours": [],
                "all_slots_sorted": [],
                "api_latency_ms": None,
                "last_updated": None,
                "coordinator_status": "error",
            }

    # -------------------------------------------------------------------------
    # Aligned scheduling logic
    # -------------------------------------------------------------------------

    def _seconds_until_next_boundary(self) -> float:
        now = datetime.now(timezone.utc)
        interval_seconds = int(self._scan_interval.total_seconds())

        seconds_today = now.hour * 3600 + now.minute * 60 + now.second
        next_boundary = ((seconds_today // interval_seconds) + 1) * interval_seconds
        delta = next_boundary - seconds_today

        if delta <= 0:
            delta = interval_seconds

        return float(delta)

    def _compute_next_delay_with_jitter(self) -> float:
        base_delay = self._seconds_until_next_boundary()
        jitter = random.uniform(0, 5)
        delay_with_jitter = base_delay + jitter

        self._next_refresh_delay = delay_with_jitter
        self._next_refresh_jitter = jitter
        self._next_refresh_datetime = datetime.now(timezone.utc) + timedelta(seconds=delay_with_jitter)

        _LOGGER.debug(
            "Next aligned refresh in %.1f seconds (base=%.1f, jitter=%.1f) at %s",
            delay_with_jitter,
            base_delay,
            jitter,
            self._next_refresh_datetime,
        )

        return delay_with_jitter

    async def _schedule_next_refresh(self) -> None:
        if self._unsub_refresh is not None:
            self._unsub_refresh()
            self._unsub_refresh = None

        delay = self._compute_next_delay_with_jitter()

        def _cb(_now):
            self.hass.async_create_task(self._handle_refresh())

        _LOGGER.debug("Scheduling next EDF coordinator refresh in %.1f seconds", delay)
        self._unsub_refresh = async_call_later(self.hass, delay, _cb)

    async def _handle_refresh(self) -> None:
        _LOGGER.debug("Running aligned EDF coordinator refresh")
        await self.async_refresh()
        await self._schedule_next_refresh()

    async def async_config_entry_first_refresh(self) -> None:
        await super().async_config_entry_first_refresh()
        await self._schedule_next_refresh()

    async def async_shutdown(self) -> None:
        if self._unsub_refresh is not None:
            self._unsub_refresh()
            self._unsub_refresh = None
