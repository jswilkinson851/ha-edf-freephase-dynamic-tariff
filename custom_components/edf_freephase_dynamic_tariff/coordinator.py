from __future__ import annotations

import asyncio
import logging
import time as time_module
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import async_timeout
import dateutil.parser
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .helpers import classify_slot

_LOGGER = logging.getLogger(__name__)


class EDFCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for EDF FreePhase Dynamic tariff data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_url: str,
        scan_interval: timedelta,
        forecast_hours: int,
        include_past_slots: bool,
        timeout: int,
        retry_attempts: int,
    ) -> None:
        self.api_url = api_url
        self.forecast_hours = forecast_hours
        self.include_past_slots = include_past_slots
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)

        last_checked = now.isoformat()
        latency_ms: int | None = None
        data: dict[str, Any] | None = None

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.retry_attempts + 1):
                try:
                    start = time_module.monotonic()
                    async with async_timeout.timeout(self.timeout):
                        resp = await session.get(self.api_url)
                        resp.raise_for_status()
                        data = await resp.json()
                    latency_ms = int((time_module.monotonic() - start) * 1000)
                    break
                except Exception as err:
                    if attempt == self.retry_attempts:
                        raise UpdateFailed(f"Error fetching data: {err}") from err
                    await asyncio.sleep(1)

        assert data is not None
        results = data["results"]

        # Determine current slot
        current_slot: dict[str, Any] | None = None
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

        # Determine current price
        if current_slot:
            current_price = current_slot["value"]
        else:
            current_price = results[0]["value_inc_vat"]

        # Fallback current_slot if forecast doesn't include the current time
        if not current_slot:
            current_slot = {
                "start": None,
                "end": None,
                "value": current_price,
                "phase": classify_slot(
                    results[0]["valid_from"],
                    results[0]["value_inc_vat"],
                ),
            }

        # Next slot price (first future slot)
        next_price: float | None = None
        for item in results:
            start = dateutil.parser.isoparse(item["valid_from"])
            if start > now:
                next_price = item["value_inc_vat"]
                break

        # Build the forecast window
        slots_to_include = int(self.forecast_hours * 2)  # half-hour slots
        next_slots = results[:slots_to_include]

        next_24_hours: list[dict[str, Any]] = []
        for item in next_slots:
            start_str = item["valid_from"]
            end_str = item["valid_to"]
            value = item["value_inc_vat"]

            start_dt = dateutil.parser.isoparse(start_str)
            end_dt = dateutil.parser.isoparse(end_str)

            if not self.include_past_slots and end_dt <= now:
                continue

            phase = classify_slot(start_str, value)

            next_24_hours.append(
                {
                    "start": start_str,
                    "end": end_str,
                    "value": value,
                    "phase": phase,
                }
            )

        last_updated = datetime.now(timezone.utc).isoformat()

        return {
            "current_price": current_price,
            "next_price": next_price,
            "next_24_hours": next_24_hours,
            "current_slot": current_slot,
            "last_checked": last_checked,
            "last_updated": last_updated,
            "api_latency": latency_ms,
        }