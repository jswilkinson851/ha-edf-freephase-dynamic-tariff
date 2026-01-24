"""
EDF FreePhase Dynamic Tariff – Data Coordinator

This module implements the primary DataUpdateCoordinator for the EDF FreePhase
Dynamic Tariff integration. It is responsible for orchestrating all data
retrieval, parsing, scheduling, and health‑state reporting for the integration.

Overview
--------
The EDFCoordinator performs three core functions:

1. **Data Acquisition**
   - Fetches tariff product metadata (region‑specific information, tariff name,
     unit type, etc.) from the EDF product endpoint.
   - Fetches the dynamic unit‑rate dataset from the EDF pricing API, including
     all half‑hourly slots for the current day and surrounding periods.
   - Ensures type‑safety and structural validation of API responses before
     passing them to the parsing layer.

2. **Dataset Construction**
   - Normalises raw EDF API responses into a unified internal representation.
   - Builds forecast datasets (today, tomorrow, next 24 hours, yesterday).
   - Identifies the current and next pricing slots.
   - Groups slots into phase blocks and produces human‑readable summaries.
   - Computes API latency and timestamps for diagnostics.

3. **Strict Heartbeat & Health Monitoring**
   - Implements a strict, multi‑flag heartbeat model that evaluates the health
     of every subsystem involved in data retrieval and processing.
   - Produces a single authoritative `coordinator_status` value based on a
     severity‑ordered priority list (e.g., `api_error`, `no_data`,
     `unexpected_format`, `stale`, `partial`, `ok`).
   - Exposes flat boolean attributes for each potential failure mode, enabling
     dashboards, automations, and diagnostics to understand the precise cause
     of degraded behaviour.
   - Ensures no silent failures: any deviation from perfect health is surfaced.

Scheduling Model
----------------
The coordinator does not use Home Assistant's built‑in timed refresh. Instead,
it delegates refresh timing to the `AlignedScheduler`, which:
   - Aligns refreshes to half‑hour boundaries (or other configured intervals).
   - Applies jitter to avoid API stampedes.
   - Ensures refreshes remain predictable and efficient.

The coordinator synchronises scheduler state for diagnostics, exposing:
   - Next boundary time
   - Next refresh datetime
   - Refresh delay and jitter

Error Handling
--------------
All API and parsing operations are wrapped in defensive try/except blocks.
Failures do not break the integration; instead:
   - The coordinator returns a fallback dataset.
   - The heartbeat flags are updated to reflect the failure.
   - The integration continues running and will retry on the next scheduled
     refresh.

This ensures the integration remains resilient even when EDF services are
unstable or return malformed data.

Integration Responsibilities
----------------------------
The EDFCoordinator is the authoritative source of:
   - Current price
   - Next price
   - Current slot
   - Forecast datasets
   - Block summaries
   - Tariff metadata
   - API latency
   - Heartbeat state and flags

Other parts of the integration (sensors, diagnostics, cost coordinator, etc.)
consume this data but do not perform their own API calls.

In summary, this module provides a robust, fault‑tolerant, strictly monitored
data pipeline for the EDF FreePhase Dynamic Tariff integration, ensuring that
Home Assistant always has a clear, accurate, and transparent view of tariff
state and coordinator health.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import monotonic

from homeassistant.config_entries import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    ConfigEntry,
)
from homeassistant.helpers.update_coordinator import (  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
    DataUpdateCoordinator,
)

from .api.client import fetch_all_pages
from .api.parsing import build_forecasts, build_unified_dataset, strip_internal
from .api.scheduler import AlignedScheduler
from .const import DOMAIN
from .helpers import (
    extract_tariff_metadata,
    find_current_block,
    format_phase_block,
    group_phase_blocks,
    normalise_slot,
)

_LOGGER = logging.getLogger(__name__)

HEARTBEAT_PRIORITY = [
    "api_error",
    "no_data",
    "parsing_error",
    "unexpected_format",
    "rate_limited",
    "scheduler_error",
    "import_sensor_missing",
    "import_sensor_unavailable",
    "metadata_error",
    "standing_charge_error",
    "standing_charge_missing",
    "stale",
    "partial",
    "healthy",
]


class EDFCoordinator(DataUpdateCoordinator):
    """Coordinator for EDF FreePhase Dynamic Tariff."""

    def __init__(
        self,
        hass,
        product_url: str,
        api_url: str,
        standing_charges_url: str,
        scan_interval,
    ):
        """Initialise the EDF FreePhase coordinator.

        Parameters:
        - hass: Home Assistant instance
        - product_url: product metadata endpoint (region‑agnostic)
        - api_url: unit‑rate endpoint for the selected region
        - standing_charges_url: standing‑charges endpoint for the selected region
        - scan_interval: refresh interval used by the aligned scheduler
        """
        self.hass = hass
        self.product_url = product_url
        self.api_url = api_url
        self.standing_charges_url = standing_charges_url
        self._scan_interval = scan_interval

        # Rolling debug buffer
        self.debug_buffer = []
        self.debug_times = []

        self.config_entry: ConfigEntry | None = None

        self.scheduler = AlignedScheduler(hass, scan_interval)

        self._next_boundary_utc = None
        self._next_refresh_datetime = None
        self._next_refresh_delay = None
        self._next_refresh_jitter = None

        self._debug = self.hass.data[DOMAIN].get("debug_enabled", False)
        self.debug_counter = 0

        # Inline debug wrapper (WORKING VERSION)
        def debug(msg, *args):
            if self.debug_enabled:
                formatted = msg % args if args else msg
                timestamp = datetime.now(timezone.utc).isoformat()

                self.debug_buffer.append(formatted)
                self.debug_times.append(timestamp)
                if len(self.debug_buffer) > 10:
                    self.debug_buffer.pop(0)
                    self.debug_times.pop(0)

                _LOGGER.info("EDF INT. EC | %s", formatted)

        self.debug = debug

        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=None,
        )
        # ------------------------------------------------------------------

    # Standing charges fetcher (self‑contained, not yet wired into refresh)
    # ------------------------------------------------------------------
    async def async_fetch_standing_charges(self) -> dict:
        """
        Fetch standing charges for the selected region.

        Returns a dict:
            {
                "value_inc_vat": float | None,
                "value_exc_vat": float | None,
                "valid_from": str | None,
                "valid_to": str | None,
                "raw": <full JSON or None>,
                "error": str | None,
            }

        This method is intentionally self‑contained and does not modify
        coordinator state. Integration into the main refresh loop happens
        in the next step.
        """
        url = self.standing_charges_url

        try:
            from aiohttp import ClientSession  # pyright: ignore[reportMissingImports] # pylint: disable=import-error disable=import-outside-toplevel # noqa: I001
            import async_timeout  # pyright: ignore[reportMissingImports] # pylint: disable=import-error  disable=import-outside-toplevel # noqa: I001

            async with ClientSession() as session:
                async with async_timeout.timeout(15):
                    resp = await session.get(url)

                    if resp.status != 200:
                        return {
                            "value_inc_vat": None,
                            "value_exc_vat": None,
                            "valid_from": None,
                            "valid_to": None,
                            "raw": None,
                            "error": f"HTTP {resp.status}",
                        }

                    data = await resp.json()

        except Exception as err:  # pylint: disable=broad-except
            return {
                "value_inc_vat": None,
                "value_exc_vat": None,
                "valid_from": None,
                "valid_to": None,
                "raw": None,
                "error": str(err),
            }

        # Expected EDF format:
        # {
        #   "count": 1,
        #   "results": [
        #       {
        #           "value_inc_vat": 48.6444,
        #           "value_exc_vat": 46.328,
        #           "valid_from": "...",
        #           "valid_to": null
        #       }
        #   ]
        # }

        try:
            results = data.get("results") or []
            first = results[0] if results else {}

            return {
                "value_inc_vat": first.get("value_inc_vat"),
                "value_exc_vat": first.get("value_exc_vat"),
                "valid_from": first.get("valid_from"),
                "valid_to": first.get("valid_to"),
                "raw": data,
                "error": None,
            }

        except Exception as err:  # pylint: disable=broad-except
            return {
                "value_inc_vat": None,
                "value_exc_vat": None,
                "valid_from": None,
                "valid_to": None,
                "raw": data,
                "error": f"parse_error: {err}",
            }

    @property
    def debug_enabled(self) -> bool:
        """
        Docstring for debug_enabled

        :param self: Description
        :return: Description
        :rtype: bool
        """
        return self._debug

    async def _async_update_data(self):
        if self.config_entry is None:
            _LOGGER.error("EDFCoordinator: config_entry not attached before refresh")
            return {}

        # Refresh debug flag
        self._debug = self.config_entry.options.get("debug_logging", False)

        # Rebind wrapper so it sees updated flag
        def debug(msg, *args):
            if self.debug_enabled:
                formatted = msg % args if args else msg
                timestamp = datetime.now(timezone.utc).isoformat()
                self.debug_buffer.append(formatted)
                self.debug_times.append(timestamp)
                if len(self.debug_buffer) > 10:
                    self.debug_buffer.pop(0)
                    self.debug_times.pop(0)
                _LOGGER.info("EDF INT. EC | %s", formatted)

        self.debug = debug

        if self._debug:
            self.debug_counter += 1

        self.debug("Starting _async_update_data")

        start_time = monotonic()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        flags = {
            "metadata_error": False,
            "api_error": False,
            "no_data": False,
            "parsing_error": False,
            "unexpected_format": False,
            "rate_limited": False,
            "scheduler_error": False,
            "import_sensor_missing": False,
            "import_sensor_unavailable": False,
            "stale": False,
            "partial": False,
            "standing_charge_error": False,
            "standing_charge_missing": False,
        }

        # 1. Product metadata
        try:
            self.debug("Fetching product metadata from %s", self.product_url)
            product_raw = await fetch_all_pages(self.product_url, max_pages=1)
            self.debug("Product metadata fetch complete")

            if isinstance(product_raw, dict):
                product_meta = product_raw
            elif isinstance(product_raw, list) and product_raw:
                product_meta = product_raw[0]
            else:
                product_meta = {}

            region_label = None
            if self.config_entry:
                region_label = self.config_entry.data.get("tariff_region_label")

            tariff_metadata = extract_tariff_metadata(product_meta, region_label)
            self.debug("Extracted tariff metadata: keys=%s", list(tariff_metadata.keys()))

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("EDF INT. EC: Failed to fetch or parse product metadata: %s", err)
            flags["metadata_error"] = True
            tariff_metadata = {}

        # --------------------------------------------------------------
        # NEW: Standing charges fetch
        # --------------------------------------------------------------
        self.debug("Fetching standing charges from %s", self.standing_charges_url)
        standing = await self.async_fetch_standing_charges()

        if standing["error"]:
            flags["standing_charge_error"] = True
            flags["standing_charge_missing"] = True
            self.debug("Standing charge fetch failed: %s", standing["error"])
        else:
            flags["standing_charge_error"] = False
            flags["standing_charge_missing"] = standing["value_inc_vat"] is None
            self.debug(
                "Standing charges fetched: inc_vat=%s exc_vat=%s",
                standing.get("value_inc_vat"),
                standing.get("value_exc_vat"),
            )

        # 2. Unit rates + unified dataset
        try:
            self.debug("Fetching unit rates from %s", self.api_url)
            raw_items = await fetch_all_pages(self.api_url, max_pages=3)
            self.debug("Fetched %d raw unit-rate items", len(raw_items) if isinstance(raw_items, list) else -1)  # pylint: disable=line-too-long

            if not isinstance(raw_items, list):
                flags["unexpected_format"] = True
                raise ValueError("EDF API returned unexpected structure")

            if not all(isinstance(i, dict) for i in raw_items):
                flags["unexpected_format"] = True
                raise ValueError("EDF API returned unexpected structure")

            if not raw_items:
                flags["no_data"] = True
                raise ValueError("EDF API returned no results")

            unified = build_unified_dataset(raw_items)
            self.debug("Unified dataset built: %d slots", len(unified))

            forecasts = build_forecasts(unified, now)
            self.debug(
                "Forecasts built: next=%d today=%d tomorrow=%d yesterday=%d",
                len(forecasts["next_24_hours"]),
                len(forecasts["today_24_hours"]),
                len(forecasts["tomorrow_24_hours"]),
                len(forecasts["yesterday_24_hours"]),
            )

            # Current slot
            current_raw = next(
                (slot for slot in unified if slot["_start_dt_obj"] <= now < slot["_end_dt_obj"]),
                None,
            )

            if current_raw:
                self.debug("Current slot found")
                current_slot = normalise_slot(strip_internal([current_raw])[0])
                current_price = current_slot["value"]
            else:
                self.debug("No current slot found, falling back to first slot")
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

            next_price = next(
                (slot["value"] for slot in unified if slot["_start_dt_obj"] > now),
                None,
            )
            self.debug("Next price determined: %s", next_price)

            all_slots_sorted = [normalise_slot(slot) for slot in strip_internal(unified)]
            self.debug("Normalised all slots: %d", len(all_slots_sorted))

            next_24_hours = [normalise_slot(slot) for slot in strip_internal(forecasts["next_24_hours"])]  # pylint: disable=line-too-long
            today_24_hours = [normalise_slot(slot) for slot in strip_internal(forecasts["today_24_hours"])]  # pylint: disable=line-too-long
            tomorrow_24_hours = [normalise_slot(slot) for slot in strip_internal(forecasts["tomorrow_24_hours"])]  # pylint: disable=line-too-long
            yesterday_24_hours = [normalise_slot(slot) for slot in strip_internal(forecasts["yesterday_24_hours"])]  # pylint: disable=line-too-long

            current_block = find_current_block(all_slots_sorted, current_slot)
            blocks = group_phase_blocks(all_slots_sorted)

            next_block = None
            if current_block and blocks:
                try:
                    idx = blocks.index(current_block)
                    if idx + 1 < len(blocks):
                        next_block = blocks[idx + 1]
                except ValueError:
                    next_block = None

            current_block_summary = format_phase_block(current_block) if current_block else None
            next_block_summary = format_phase_block(next_block) if next_block else None

            api_latency_ms = int((monotonic() - start_time) * 1000)
            self.debug("Block summaries computed")

            # Heartbeat stale detection
            if self.data and self.data.get("last_updated"):
                try:
                    last_dt = datetime.fromisoformat(self.data["last_updated"])
                    if (now - last_dt).total_seconds() > self._scan_interval.total_seconds() * 2:
                        flags["stale"] = True
                        self.debug("Data marked stale")
                except Exception:  # pylint: disable=broad-exception-caught
                    flags["parsing_error"] = True

            if flags["metadata_error"]:
                flags["partial"] = True

            primary_state = "healthy"
            for state in HEARTBEAT_PRIORITY:
                if flags.get(state):
                    primary_state = state
                    break

            self.debug("Primary coordinator state: %s", primary_state)
            self.debug("Returning dataset")

            return {
                "current_price": current_price,
                "next_price": next_price,
                "current_slot": current_slot,
                "next_24_hours": next_24_hours,
                "today_24_hours": today_24_hours,
                "tomorrow_24_hours": tomorrow_24_hours,
                "yesterday_24_hours": yesterday_24_hours,
                "all_slots_sorted": all_slots_sorted,
                "current_block_summary": current_block_summary,
                "next_block_summary": next_block_summary,
                "api_latency_ms": api_latency_ms,
                "last_updated": now_iso,
                "coordinator_status": primary_state,
                "tariff_metadata": tariff_metadata,
                "debug_counter": self.debug_counter,

                # Standing Charges fields.
                "standing_charge_inc_vat": standing.get("value_inc_vat"),
                "standing_charge_exc_vat": standing.get("value_exc_vat"),
                "standing_charge_valid_from": standing.get("valid_from"),
                "standing_charge_valid_to": standing.get("valid_to"),
                "standing_charge_raw": standing.get("raw"),
                **flags,
            }

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOGGER.error("EDF INT. EC: API request failed: %s", err)
            flags["api_error"] = True

            return {
                "current_price": None,
                "next_price": None,
                "current_slot": None,
                "next_24_hours": [],
                "today_24_hours": [],
                "tomorrow_24_hours": [],
                "yesterday_24_hours": [],
                "all_slots_sorted": [],
                "current_block_summary": None,
                "next_block_summary": None,
                "api_latency_ms": None,
                "last_updated": None,
                "coordinator_status": "api_error",
                "tariff_metadata": tariff_metadata or {},
                "scan_interval_seconds": int(self._scan_interval.total_seconds()),
                **flags,
            }

    # Scheduler sync + refresh
    def _sync_scheduler_state(self) -> None:
        self._next_boundary_utc = getattr(self.scheduler, "_next_boundary_utc", None)
        self._next_refresh_datetime = getattr(self.scheduler, "next_refresh_datetime", None)
        self._next_refresh_delay = self.scheduler.next_refresh_delay
        self._next_refresh_jitter = getattr(self.scheduler, "next_refresh_jitter", None)

    async def async_config_entry_first_refresh(self) -> None:
        """
        Docstring for async_config_entry_first_refresh

        :param self: Description
        """
        self.debug("Performing immediate first refresh for EDF coordinator")
        await self.async_refresh()
        await self.scheduler.schedule(self._handle_refresh)
        self._sync_scheduler_state()

    async def _handle_refresh(self, _now=None) -> None:
        """
        Docstring for _handle_refresh

        :param self: Description
        :param _now: Description
        """
        self.debug("Running aligned EDF coordinator refresh")
        await self.scheduler.schedule(self._handle_refresh)
        self._sync_scheduler_state()
        await self.async_refresh()
        self.async_update_listeners()

    async def async_shutdown(self) -> None:
        """
        Docstring for async_shutdown

        :param self: Description
        """
        await self.scheduler.shutdown()
