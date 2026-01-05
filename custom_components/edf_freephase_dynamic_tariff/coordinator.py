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
    def __init__(self, hass, api_url, scan_interval, api_timeout, retry_attempts):
        self.api_url = api_url
        self._api_timeout = api_timeout
        self._retry_attempts = retry_attempts
        self.last_successful_data: dict = {}
        self.last_successful_update: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=scan_interval,
        )

    async def _async_update_data(self):
        """Fetch and process data from the EDF API with retries and fallback."""

        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).date()
        api_latency_ms: int | None = None

        # --- Retry loop for transient failures ---
        last_error: Exception | None = None
        for attempt in range(1, self._retry_attempts + 1):
            start_time = monotonic()
            try:
                async with aiohttp.ClientSession() as session:
                    async with async_timeout.timeout(self._api_timeout):
                        resp = await session.get(self.api_url)
                        resp.raise_for_status()
                        data = await resp.json()

                api_latency_ms = int((monotonic() - start_time) * 1000)
                _LOGGER.debug(
                    "API call succeeded on attempt %s (latency: %sms)",
                    attempt,
                    api_latency_ms,
                )

                break  # Success, exit retry loop

            except Exception as err:  # Broad by design: we never want to kill the coordinator
                last_error = err
                _LOGGER.warning(
                    "API request attempt %s/%s failed: %s",
                    attempt,
                    self._retry_attempts,
                    err,
                )

        # If all attempts failed, fall back to last_successful_data if available
        if last_error is not None and api_latency_ms is None:
            _LOGGER.error("All API attempts failed: %s", last_error)

            if self.last_successful_data:
                _LOGGER.warning("Using last successful data due to repeated API failures")
                # Enrich the cached data with current health info
                payload = dict(self.last_successful_data)
                payload["coordinator_status"] = "degraded"
                if self.last_successful_update:
                    age = (now - self.last_successful_update).total_seconds()
                    payload["data_age_seconds"] = int(age)
                else:
                    payload["data_age_seconds"] = None
                return payload

            # No cached data to fall back to: return a safe error payload
            return {
                "current_price": None,
                "next_price": None,
                "next_24_hours": [],
                "current_slot": None,
                "api_latency_ms": None,
                "last_updated": None,
                "tomorrow_24_hours": [],
                "coordinator_status": "error",
                "last_successful_update": None,
                "data_age_seconds": None,
            }

        # At this point, we have a successful `data` from the API
        results = data.get("results", [])

        tomorrow_24_hours = []
        for item in results:
            start_dt = dateutil.parser.isoparse(item["valid_from"])
            if start_dt.date() == tomorrow:
                tomorrow_24_hours.append(
                    {
                        "start": item["valid_from"],
                        "end": item["valid_to"],
                        "value": item["value_inc_vat"],
                        "phase": classify_slot(
                            item["valid_from"], item["value_inc_vat"]
                        ),
                    }
                )

        current_slot = None
        for item in results:
            start = dateutil.parser.isoparse(item["valid_from"])
            end = dateutil.parser.isoparse(item["valid_to"])
            if start <= now < end:
                current_slot = {
                    "start": item["valid_from"],
                    "end": item["valid_to"],
                    "value": item["value_inc_vat"],
                    "phase": classify_slot(
                        item["valid_from"], item["value_inc_vat"]
                    ),
                }
                break

        if current_slot:
            current_price = current_slot["value"]
        else:
            current_price = results[0]["value_inc_vat"] if results else None

        if not current_slot:
            if results:
                current_slot = {
                    "start": None,
                    "end": None,
                    "value": current_price,
                    "phase": classify_slot(
                        results[0]["valid_from"], results[0]["value_inc_vat"]
                    ),
                }
            else:
                current_slot = None

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

            next_24_hours.append(
                {
                    "start": start,
                    "end": end,
                    "value": value,
                    "phase": phase,
                }
            )

        last_updated_iso = datetime.now(timezone.utc).isoformat()

        # Successful update: track last successful update time
        self.last_successful_update = now

        payload = {
            "current_price": current_price,
            "next_price": next_price,
            "next_24_hours": next_24_hours,
            "current_slot": current_slot,
            "api_latency_ms": api_latency_ms,
            "last_updated": last_updated_iso,
            "tomorrow_24_hours": tomorrow_24_hours,
            "coordinator_status": "ok",
            "last_successful_update": last_updated_iso,
            "data_age_seconds": 0,
        }

        self.last_successful_data = payload
        return payload