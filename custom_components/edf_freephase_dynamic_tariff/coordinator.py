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
    dt = dateutil.parser.isoparse(start_time)
    t = dt.time()

    if price <= 0:
        return "green"

    if time(23, 0) <= t or t < time(6, 0):
        return "green"
    if time(6, 0) <= t < time(16, 0):
        return "amber"
    if time(16, 0) <= t < time(19, 0):
        return "red"
    if time(19, 0) <= t < time(23, 0):
        return "amber"

    return "amber"


class EDFCoordinator(DataUpdateCoordinator):
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
                    resp = await session.get(self.api_url)
                    resp.raise_for_status()
                    data = await resp.json()

            api_latency_ms = int((monotonic() - start_time) * 1000)
            _LOGGER.debug("API latency: %sms", api_latency_ms)

            results = data["results"]

            tomorrow_24_hours = []
            for item in results:
                start_dt = dateutil.parser.isoparse(item["valid_from"])
                if start_dt.date() == tomorrow:
                    tomorrow_24_hours.append({
                        "start": item["valid_from"],
                        "end": item["valid_to"],
                        "value": item["value_inc_vat"],
                        "phase": classify_slot(item["valid_from"], item["value_inc_vat"]),
                    })

            current_slot = None
            for item in results:
                start = dateutil.parser.isoparse(item["valid_from"])
                end = dateutil.parser.isoparse(item["valid_to"])
                if start <= now < end:
                    current_slot = {
                        "start": item["valid_from"],
                        "end": item["valid_to"],
                        "value": item["value_inc_vat"],
                        "phase": classify_slot(item["valid_from"], item["value_inc_vat"]),
                    }
                    break

            if current_slot:
                current_price = current_slot["value"]
            else:
                current_price = results[0]["value_inc_vat"]

            if not current_slot:
                current_slot = {
                    "start": None,
                    "end": None,
                    "value": current_price,
                    "phase": classify_slot(results[0]["valid_from"], results[0]["value_inc_vat"]),
                }

            next_price = None
            for item in results:
                start = dateutil.parser.isoparse(item["valid_from"])
                if start > now:
                    next_price = item["value_inc_vat"]
                    break

            next_24_hours = []
            for item in results[:48]:
                start = item["valid_from"]
                end = item["valid_to"]
                value = item["value_inc_vat"]
                phase = classify_slot(start, value)

                next_24_hours.append({
                    "start": start,
                    "end": end,
                    "value": value,
                    "phase": phase,
                })

            last_updated = datetime.now(timezone.utc).isoformat()

            return {
                "current_price": current_price,
                "next_price": next_price,
                "next_24_hours": next_24_hours,
                "current_slot": current_slot,
                "api_latency_ms": api_latency_ms,
                "last_updated": last_updated,
                "tomorrow_24_hours": tomorrow_24_hours,
                "coordinator_status": "ok",
            }

        except Exception as err:
            _LOGGER.error("API request failed: %s", err)

            return {
                "current_price": None,
                "next_price": None,
                "next_24_hours": [],
                "current_slot": None,
                "api_latency_ms": None,
                "last_updated": None,
                "tomorrow_24_hours": [],
                "coordinator_status": "error",
            }