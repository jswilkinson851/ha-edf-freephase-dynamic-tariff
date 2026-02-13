"""
EDF FreePhase Dynamic Tariff – Data Coordinator

This module implements the primary DataUpdateCoordinator for the EDF FreePhase
Dynamic Tariff integration. It is responsible for orchestrating all data
retrieval, parsing, scheduling, and health‑state reporting for the integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from time import monotonic

# pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.event import async_call_later  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .api.client import fetch_all_pages
from .api.parsing import build_forecasts, build_unified_dataset, strip_internal
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
        scan_interval: int,
    ):
        """Initialise the EDF FreePhase coordinator.

        Parameters:
        - hass: Home Assistant instance
        - product_url: product metadata endpoint (region‑agnostic)
        - api_url: unit‑rate endpoint for the selected region
        - standing_charges_url: standing‑charges endpoint for the selected region
        - scan_interval: refresh interval in MINUTES (from config entry)
        """
        self.hass = hass
        self.product_url = product_url
        self.api_url = api_url
        self.standing_charges_url = standing_charges_url

        # Convert minutes → timedelta
        self._scan_interval = timedelta(minutes=scan_interval)
        _LOGGER.info(
            "EDF INT. EC | scan_interval raw=%s minutes, resolved=%s seconds",
            scan_interval,
            self._scan_interval.total_seconds(),
        )

        # Rolling debug buffer
        self.debug_buffer: list[str] = []
        self.debug_times: list[str] = []

        self.config_entry: ConfigEntry | None = None

        # Simple, coordinator‑local scheduling diagnostics
        self._next_boundary_utc: datetime | None = None
        self._next_refresh_datetime: datetime | None = None
        self._next_refresh_delay: int | None = None
        self._next_refresh_jitter: int | None = None
        self._unsub_next_refresh = None

        self._debug = self.hass.data[DOMAIN].get("debug_enabled", False)
        self.debug_counter = 0

        # Inline debug wrapper
        def debug(msg, *args):
            if self.debug_enabled:
                try:
                    formatted = msg % args if args else msg
                except Exception:  # pragma: no cover
                    formatted = f"{msg} | ARGS={args}"

                timestamp = datetime.now(timezone.utc).isoformat()
                self.debug_buffer.append(formatted)
                self.debug_times.append(timestamp)
                if len(self.debug_buffer) > 10:
                    self.debug_buffer.pop(0)
                    self.debug_times.pop(0)

                _LOGGER.info("EDF INT. EC | %s", formatted)

        self.debug = debug

        # IMPORTANT: we handle scheduling manually for aligned refreshes
        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=None,
        )

        # Initialise coordinator data with a valid timestamp so timestamp sensors
        # never start in an unavailable state.
        self.data = {
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    # ---------------------------------------------------------------------
    # Aligned scheduling helpers
    # ---------------------------------------------------------------------

    @property
    def debug_enabled(self) -> bool:
        """Return whether debug logging is enabled."""
        return self._debug

    def _compute_next_boundary(self, now: datetime) -> datetime:
        """Return the next aligned refresh boundary as a UTC datetime.

        Alignment is based on whole multiples of the scan interval since
        midnight UTC, so:
          • 5‑minute interval → :00, :05, :10, ...
          • 30‑minute interval → :00, :30, :00, ...
        """
        interval_seconds = int(self._scan_interval.total_seconds())
        if interval_seconds <= 0:
            # Fallback: just use a simple interval from now
            return now + self._scan_interval

        seconds_today = now.hour * 3600 + now.minute * 60 + now.second
        next_boundary_seconds = ((seconds_today // interval_seconds) + 1) * interval_seconds
        delta_seconds = next_boundary_seconds - seconds_today
        if delta_seconds <= 0:
            delta_seconds = interval_seconds

        return now + timedelta(seconds=delta_seconds)

    def _schedule_next_refresh(self) -> None:
        """Schedule the next aligned refresh using async_call_later."""
        # Cancel any existing timer
        if self._unsub_next_refresh:
            self._unsub_next_refresh()
            self._unsub_next_refresh = None

        now = datetime.now(timezone.utc)
        next_boundary = self._compute_next_boundary(now)
        delay = (next_boundary - now).total_seconds()
        delay = max(delay, 1)

        # Update diagnostics
        self._next_boundary_utc = next_boundary
        self._next_refresh_datetime = next_boundary
        self._next_refresh_delay = int(delay)
        self._next_refresh_jitter = 0

        self.debug(
            "Scheduling next aligned refresh in %s seconds at %s",
            int(delay),
            next_boundary.isoformat(),
        )

        async def _handle_scheduled_refresh(_now):
            self.debug("Aligned timer fired; requesting coordinator refresh")
            await self.async_request_refresh()

        self._unsub_next_refresh = async_call_later(
            self.hass,
            delay,
            _handle_scheduled_refresh,
        )

    # ---------------------------------------------------------------------
    # Standing charges fetcher (self‑contained)
    # ---------------------------------------------------------------------
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
        """
        url = self.standing_charges_url

        try:
            from aiohttp import ClientSession  # pyright: ignore[reportMissingImports]  # pylint: disable=import-error,import-outside-toplevel
            import async_timeout  # pyright: ignore[reportMissingImports]  # pylint: disable=import-error,import-outside-toplevel

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

    # ---------------------------------------------------------------------
    # Main update logic
    # ---------------------------------------------------------------------
    async def _async_update_data(self):
        """Fetch and build the full coordinator dataset."""
        self.debug("EDF INT. DEBUG: REAL API REFRESH OCCURRED")

        if self.config_entry is None:
            _LOGGER.error("EDFCoordinator: config_entry not attached before refresh")
            return {}

        # Refresh debug flag from options
        self._debug = self.config_entry.options.get("debug_logging", False)

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
            product_raw = await fetch_all_pages(self.product_url, max_pages=1)  # pyright: ignore[reportGeneralTypeIssues]
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
            _LOGGER.warning(
                "EDF INT. EC: Failed to fetch or parse product metadata: %s", err
            )
            flags["metadata_error"] = True
            tariff_metadata = {}

        # 2. Standing charges
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

        # 3. Unit rates + unified dataset
        try:
            self.debug("Fetching unit rates from %s", self.api_url)
            raw_items = await fetch_all_pages(self.api_url, max_pages=3)  # pyright: ignore[reportGeneralTypeIssues]
            self.debug(
                "Fetched %d raw unit-rate items",
                len(raw_items) if isinstance(raw_items, list) else -1,
            )

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

            current_block_summary = (
                format_phase_block(current_block) if current_block else None
            )
            next_block_summary = (
                format_phase_block(next_block) if next_block else None
            )

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

            # For aligned scheduling, compute and expose the *aligned* next refresh
            next_boundary = self._compute_next_boundary(now)
            delay = (next_boundary - now).total_seconds()
            delay = max(delay, 1)

            self._next_boundary_utc = next_boundary
            self._next_refresh_datetime = next_boundary
            self._next_refresh_delay = int(delay)
            self._next_refresh_jitter = 0

            self.debug(
                "Aligned next refresh: in %s seconds at %s",
                int(delay),
                next_boundary.isoformat(),
            )

            # Schedule the next aligned refresh
            self._schedule_next_refresh()

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
                "standing_charge_inc_vat": standing.get("value_inc_vat"),
                "standing_charge_exc_vat": standing.get("value_exc_vat"),
                "standing_charge_valid_from": standing.get("valid_from"),
                "standing_charge_valid_to": standing.get("valid_to"),
                "standing_charge_raw": standing.get("raw"),
                "next_refresh_datetime": (
                    self._next_refresh_datetime.isoformat()
                    if self._next_refresh_datetime
                    else None
                ),
                "next_refresh_delay_seconds": self._next_refresh_delay,
                "next_refresh_jitter_seconds": self._next_refresh_jitter,
                **flags,
            }

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOGGER.error("EDF INT. EC: API request failed: %s", err)
            flags["api_error"] = True

            # Even on error, keep aligned scheduling going
            now = datetime.now(timezone.utc)
            next_boundary = self._compute_next_boundary(now)
            delay = (next_boundary - now).total_seconds()
            delay = max(delay, 1)

            self._next_boundary_utc = next_boundary
            self._next_refresh_datetime = next_boundary
            self._next_refresh_delay = int(delay)
            self._next_refresh_jitter = 0

            self.debug(
                "Error path: aligned next refresh in %s seconds at %s",
                int(delay),
                next_boundary.isoformat(),
            )

            self._schedule_next_refresh()

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
                "next_refresh_datetime": (
                    self._next_refresh_datetime.isoformat()
                    if self._next_refresh_datetime
                    else None
                ),
                "next_refresh_delay_seconds": self._next_refresh_delay,
                "next_refresh_jitter_seconds": self._next_refresh_jitter,
                **flags,
            }

    async def async_shutdown(self) -> None:
        """Shutdown hook: cancel aligned refresh timer."""
        if self._unsub_next_refresh:
            self._unsub_next_refresh()
            self._unsub_next_refresh = None

# ----------------------------------------------------------------------------
# End of coordinator.py file
# ----------------------------------------------------------------------------