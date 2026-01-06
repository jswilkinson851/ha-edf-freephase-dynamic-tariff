from __future__ import annotations
import aiohttp
import async_timeout
import logging
from datetime import datetime, time, timezone, timedelta
from time import monotonic

import dateutil.parser

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
        self.api_url = api_url
        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=scan_interval,
        )

    async def _async_update_data(self):
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

            #
            # ---- BUILD UNIFIED SORTED DATASET ----
            #
            unified = []
            for item in all_results:
                start_raw = item["valid_from"]
                end_raw = item["valid_to"]

                start_dt = dateutil.parser.isoparse(start_raw)
                end_dt = dateutil.parser.isoparse(end_raw)

                unified.append({
                    "start": start_raw,                     # raw EDF UTC
                    "end": end_raw,                         # raw EDF UTC
                    "start_dt": start_dt.isoformat(),       # parsed ISO8601
                    "end_dt": end_dt.isoformat(),
                    "value": item["value_inc_vat"],
                    "phase": classify_slot(start_raw, item["value_inc_vat"]),
                    "currency": "GBP",
                    "_start_dt_obj": start_dt,              # internal only
                    "_end_dt_obj": end_dt,
                })

            # Sort ascending by parsed datetime
            unified.sort(key=lambda s: s["_start_dt_obj"])

            #
            # ---- ROLLING 24-HOUR FORECAST ----
            #
            future = [slot for slot in unified if slot["_start_dt_obj"] >= now]
            next_24_hours = future[:48]

            #
            # ---- TOMORROW'S FORECAST ----
            #
            tomorrow_24_hours = [
                slot for slot in unified
                if slot["_start_dt_obj"].date() == tomorrow
            ]

            #
            # ---- CURRENT SLOT ----
            #
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
                # fallback to most recent price
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

            #
            # ---- NEXT PRICE ----
            #
            next_price = None
            for slot in unified:
                if slot["_start_dt_obj"] > now:
                    next_price = slot["value"]
                    break

            #
            # ---- CLEAN INTERNAL FIELDS ----
            #
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

            #
            # ---- RETURN PAYLOAD ----
            #
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