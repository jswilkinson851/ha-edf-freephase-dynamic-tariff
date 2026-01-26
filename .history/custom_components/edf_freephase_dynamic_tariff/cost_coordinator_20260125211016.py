"""
Cost computation coordinator for the EDF FreePhase Dynamic Tariff integration.

This module provides the logic required to transform cumulative import‑meter
readings and EDF tariff slot data into structured monetary and consumption
summaries. It acts as a secondary DataUpdateCoordinator layered on top of the
EDFCoordinator, combining historical energy usage with half‑hourly tariff
windows to produce accurate cost calculations for both yesterday and today.

Purpose
-------
The CostCoordinator is responsible for converting raw cumulative kWh readings
(from a user‑selected import sensor) into interval‑based deltas, aligning those
deltas with EDF tariff slots, and computing per‑slot, per‑phase, and total
cost summaries. These summaries are consumed by sensor entities to expose
real‑time and historical cost information in Home Assistant.

Data Flow
---------
1. EDFCoordinator fetches tariff slot data for yesterday and today.
2. CostCoordinator retrieves cumulative import‑meter history from the Recorder
   using `get_significant_states`, ensuring efficient database access.
3. Cumulative readings are converted into kWh deltas representing actual
   consumption over each interval.
4. Each delta is proportionally distributed across overlapping tariff slots,
   allowing precise cost attribution even when meter updates do not align with
   tariff boundaries.
5. Slot‑level costs are aggregated into:
   • total_kwh / total_cost for the period
   • per‑phase breakdowns (e.g., Peak, Off‑Peak, Boost)
   • a detailed per‑slot list for diagnostics and transparency

Computed Periods
----------------
The coordinator computes two summaries on each update:
• yesterday — full 24‑hour period using EDF's “yesterday_24_hours” slots
• today — from midnight to now, using “today_24_hours” slots with an end‑time
  override to prevent projecting into the future

Both summaries are returned as structured dictionaries suitable for direct use
by Home Assistant sensor entities.

Recorder Interaction
--------------------
The coordinator uses the Recorder’s supported synchronous helper
`recorder_history.get_significant_states` via `async_add_executor_job`. This
ensures:
• efficient database queries
• correct handling of state transitions
• inclusion of the state at the period start time

Delta Computation
-----------------
Import‑meter readings are cumulative. The coordinator:
• sorts states chronologically
• computes positive deltas only (ignoring resets or invalid values)
• clamps intervals to the requested period window
• returns a list of {start, end, kwh} entries representing real consumption

Slot Alignment Algorithm
------------------------
Each delta interval is intersected with each tariff slot:
• overlapping seconds are calculated
• a fractional kWh contribution is derived
• cost is computed using the slot’s unit rate (p/kWh)
• results are accumulated into SlotCost dataclass instances

This proportional‑overlap method ensures accuracy even when:
• meter updates are infrequent
• slot boundaries do not align with meter timestamps
• tariff phases change rapidly

Coordinator Lifecycle
---------------------
The CostCoordinator:
• runs on the same scan interval as the EDFCoordinator
• performs no network I/O
• gracefully handles missing sensors, missing tariff data, or empty history
• exposes its results via the standard DataUpdateCoordinator `.data` attribute
• supports clean shutdown via `async_shutdown` (called in __init__.py)

Returned Data Structure
-----------------------
Each computed summary has the form:

    {
        "period_start": ISO timestamp,
        "period_end": ISO timestamp,
        "total_kwh": float,
        "total_cost": float,
        "per_phase": {
            "PhaseName": {"kwh": float, "cost": float},
            ...
        },
        "per_slot": [
            {
                "start": ISO timestamp,
                "end": ISO timestamp,
                "kwh": float,
                "price_p_per_kwh": float,
                "cost_gbp": float,
                "phase": Optional[str],
            },
            ...
        ],
    }

This structure is intentionally explicit and stable, making it suitable for
sensor entities, dashboards, diagnostics, and future extensions.

In summary, the CostCoordinator provides the integration’s cost‑calculation
engine: a deterministic, transparent, and recorder‑backed mechanism for
turning raw import‑meter data and EDF tariff slots into meaningful cost
insights for Home Assistant.
"""

# cost_coordinator.py

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

# pylint: disable=import-error
from homeassistant.components.recorder import history as recorder_history  # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator  # pyright: ignore[reportMissingImports]
from homeassistant.util import dt as dt_util  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class SlotCost:
    """
    Docstring for SlotCost
    """

    start: datetime
    end: datetime
    kwh: float
    price_p_per_kwh: float
    cost_gbp: float
    phase: Optional[str]


class CostCoordinator(DataUpdateCoordinator):
    """Coordinator to compute real cost from import sensor + EDF tariff slots."""

    def __init__(
        self,
        hass: HomeAssistant,
        edf_coordinator,
        import_sensor_entity_id: Optional[str],
        scan_interval: timedelta,
    ) -> None:
        self.hass = hass
        self._edf_coordinator = edf_coordinator
        self._import_sensor = import_sensor_entity_id
        self._scan_interval = scan_interval

        self.debug_buffer = []
        self.debug_times = []

        self._debug = self.hass.data.get(DOMAIN, {}).get("debug_enabled", False)
        self.debug_counter = 0

        # Inline wrapper (WORKING VERSION)
        def debug(msg, *args):
            if self.debug_enabled:
                formatted = msg % args if args else msg
                timestamp = datetime.now(timezone.utc).isoformat()
                self.debug_buffer.append(formatted)
                self.debug_times.append(timestamp)
                if len(self.debug_buffer) > 10:
                    self.debug_buffer.pop(0)
                    self.debug_times.pop(0)
                _LOGGER.info("EDF INT. CC | %s", formatted)

        self.debug = debug

        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Cost Coordinator",
            update_interval=scan_interval,
        )

    @property
    def debug_enabled(self) -> bool:
        return self._debug

    async def _async_update_data(self) -> dict:
        self._debug = self.config_entry.options.get("debug_logging", False)

        # Rebind wrapper
        def debug(msg, *args):
            if self.debug_enabled:
                formatted = msg % args if args else msg
                timestamp = datetime.now(timezone.utc).isoformat()
                self.debug_buffer.append(formatted)
                self.debug_times.append(timestamp)
                if len(self.debug_buffer) > 10:
                    self.debug_buffer.pop(0)
                    self.debug_times.pop(0)
                _LOGGER.info("EDF INT. CC | %s", formatted)

        self.debug = debug

        flags = {
            "history_missing": False,
            "no_deltas": False,
            "partial": False,
            "error": False,
        }

        if self._debug:
            self.debug_counter += 1

        self.debug("ENTER _async_update_data")

        if not self._import_sensor:
            self.debug("No import sensor configured; skipping cost computation")
            return {"yesterday": None, "today": None, "import_sensor": None}

        edf_data = self._edf_coordinator.data or {}
        yesterday_slots = edf_data.get("yesterday_24_hours") or []
        today_slots = edf_data.get("today_24_hours") or []

        # --------------------------------------------------------------
        # NEW: Standing charges from EDFCoordinator
        # --------------------------------------------------------------
        standing_inc = edf_data.get("standing_charge_inc_vat")
        standing_exc = edf_data.get("standing_charge_exc_vat")
        standing_from = edf_data.get("standing_charge_valid_from")
        standing_to = edf_data.get("standing_charge_valid_to")

        self.debug("yesterday_slots=%s today_slots=%s", len(yesterday_slots), len(today_slots))

        if not yesterday_slots and not today_slots:
            self.debug("No tariff slots available from EDF coordinator; skipping")
            return {"yesterday": None, "today": None, "import_sensor": self._import_sensor}

        now = dt_util.utcnow()

        # Yesterday
        yesterday_summary = None
        if yesterday_slots:
            self.debug("Calling _compute_period_cost for yesterday")
            try:
                yesterday_summary = await self._compute_period_cost(
                    slots=yesterday_slots,
                    label="yesterday",
                )
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOGGER.exception("EDF INT. CC: ERROR computing yesterday: %s", err)
                yesterday_summary = None
                flags["error"] = True

        # Today
        today_summary = None
        if today_slots:
            self.debug("Calling _compute_period_cost for today")
            try:
                today_summary = await self._compute_period_cost(
                    slots=today_slots,
                    label="today",
                    end_override=now,
                )
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOGGER.exception("EDF INT. CC: ERROR computing today: %s", err)
                today_summary = None
                flags["error"] = True

        # Primary state
        if flags["error"]:
            primary_state = "error"
        elif flags["history_missing"]:
            primary_state = "history_missing"
        elif flags["no_deltas"]:
            primary_state = "no_deltas"
        elif flags["partial"]:
            primary_state = "partial"
        else:
            primary_state = "healthy"

        coordinator_status = primary_state

        self.debug("EXIT _async_update_data")

        return {
            "yesterday": yesterday_summary,
            "today": today_summary,
            "import_sensor": self._import_sensor,
            # Standing charge values (top‑level)
            "standing_charge_inc_vat": standing_inc,
            "standing_charge_exc_vat": standing_exc,
            "standing_charge_valid_from": standing_from,
            "standing_charge_valid_to": standing_to,
            **flags,
            "coordinator_status": coordinator_status,
            "last_updated": dt_util.utcnow().isoformat(),
        }

    async def _compute_period_cost(
        self,
        slots: list[dict],
        label: str,
        end_override: Optional[datetime] = None,
    ) -> Optional[dict]:
        self.debug("ENTER _compute_period_cost label=%s", label)

        norm_slots = []
        for s in slots:
            start = self._parse_dt(s.get("start_dt") or s.get("start"))
            end = self._parse_dt(s.get("end_dt") or s.get("end"))
            if not start or not end:
                continue
            if end_override and end > end_override:
                end = end_override
            if end <= start:
                continue
            price = s.get("value") or s.get("price")
            phase = s.get("phase")
            if price is None:
                continue
            norm_slots.append(
                {
                    "start": start,
                    "end": end,
                    "price_p_per_kwh": float(price),
                    "phase": phase,
                }
            )

        self.debug("norm_slots count=%s", len(norm_slots))

        if not norm_slots:
            self.debug("No valid slots for %s cost computation", label)
            return None

        norm_slots.sort(key=lambda x: x["start"])
        period_start = norm_slots[0]["start"]
        period_end = norm_slots[-1]["end"]

        self.debug("period_start=%s period_end=%s", period_start, period_end)

        # Recorder: fetch significant states using the supported sync helper
        self.debug("Calling recorder_history.get_significant_states via hass.async_add_executor_job")

        def _fetch_history():
            return recorder_history.get_significant_states(
                self.hass,
                period_start,
                period_end,
                [self._import_sensor],
                include_start_time_state=True,
            )

        history = await self.hass.async_add_executor_job(_fetch_history)

        self.debug("get_significant_states returned history=%s", history)

        entity_states = history.get(self._import_sensor)
        self.debug("entity_states count=%s", len(entity_states or []))

        if not entity_states:
            self.debug("No history...")
            return None

        # Convert cumulative kWh → deltas
        deltas = self._compute_deltas(entity_states, period_start, period_end)
        self.debug("deltas count=%s", len(deltas))

        if not deltas:
            self.debug("No usable deltas...")
            return None

        # Align deltas with slots
        slot_costs: list[SlotCost] = self._align_deltas_to_slots(norm_slots, deltas)
        self.debug("slot_costs count=%s", len(slot_costs))

        total_kwh = sum(sc.kwh for sc in slot_costs)
        total_cost = sum(sc.cost_gbp for sc in slot_costs)

        self.debug(
            "finished period '%s' total_kwh=%s total_cost=%s",
            label,
            total_kwh,
            total_cost,
        )

        # Aggregate per phase
        per_phase: dict[str, dict[str, float]] = defaultdict(lambda: {"kwh": 0.0, "cost": 0.0})

        for sc in slot_costs:
            phase = sc.phase or "Unknown"
            per_phase[phase]["kwh"] += sc.kwh
            per_phase[phase]["cost"] += sc.cost_gbp

        # Per-slot breakdown
        per_slot = [
            {
                "start": sc.start.isoformat(),
                "end": sc.end.isoformat(),
                "kwh": round(sc.kwh, 4),
                "price_p_per_kwh": round(sc.price_p_per_kwh, 4),
                "cost_gbp": round(sc.cost_gbp, 4),
                "phase": sc.phase,
            }
            for sc in slot_costs
        ]

        self.debug("EXIT _compute_period_cost label=%s", label)

        # --------------------------------------------------------------
        # Standing charge cost contribution
        # --------------------------------------------------------------
        standing_inc = self._edf_coordinator.data.get("standing_charge_inc_vat")
        standing_exc = self._edf_coordinator.data.get("standing_charge_exc_vat")
        standing_from = self._edf_coordinator.data.get("standing_charge_valid_from")
        standing_to = self._edf_coordinator.data.get("standing_charge_valid_to")

        standing_cost_gbp = None
        total_cost_including_standing = None

        if standing_inc is not None:
            # p/day → £/day
            standing_cost_gbp = standing_inc / 100.0
            total_cost_including_standing = round(total_cost + standing_cost_gbp, 4)

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_kwh": round(total_kwh, 4),
            "total_cost": round(total_cost, 4),
            "per_phase": {
                phase: {
                    "kwh": round(vals["kwh"], 4),
                    "cost": round(vals["cost"], 4),
                }
                for phase, vals in per_phase.items()
            },
            "per_slot": per_slot,
            "standing_charge_inc_vat": standing_inc,
            "standing_charge_exc_vat": standing_exc,
            "standing_charge_valid_from": standing_from,
            "standing_charge_valid_to": standing_to,
            "standing_charge_cost_gbp": standing_cost_gbp,
            "total_cost_including_standing_gbp": total_cost_including_standing,
        }

    @staticmethod
    def _parse_dt(value) -> Optional[datetime]:
        """Parse a datetime-like value into an aware UTC datetime, or None."""
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        try:
            dt = dt_util.parse_datetime(value)
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    @staticmethod
    def _compute_deltas(states, period_start: datetime, period_end: datetime):
        """Convert cumulative meter states into interval deltas."""
        if not states or len(states) < 2:
            return []

        deltas = []
        prev_state = None

        for state in states:
            try:
                ts = state.last_updated or state.last_changed
                if ts is None:
                    continue
                ts = ts.astimezone(timezone.utc)
                value = float(state.state)
            except Exception:
                continue

            if prev_state is None:
                prev_state = (ts, value)
                continue

            prev_ts, prev_val = prev_state
            if ts <= prev_ts:
                continue

            start = max(prev_ts, period_start)
            end = min(ts, period_end)
            if end <= start:
                prev_state = (ts, value)
                continue

            delta = value - prev_val
            if delta < 0:
                prev_state = (ts, value)
                continue

            deltas.append({"start": start, "end": end, "kwh": delta})
            prev_state = (ts, value)

        return deltas

    @staticmethod
    def _align_deltas_to_slots(slots: list[dict], deltas: list[dict]) -> list[SlotCost]:
        """Distribute delta kWh across slot windows and compute costs."""
        slot_costs: list[SlotCost] = []

        for slot in slots:
            s_start: datetime = slot["start"]
            s_end: datetime = slot["end"]
            price = slot["price_p_per_kwh"]
            phase = slot.get("phase")

            if (s_end - s_start).total_seconds() <= 0:
                continue

            slot_kwh = 0.0
            for d in deltas:
                d_start: datetime = d["start"]
                d_end: datetime = d["end"]
                d_kwh: float = d["kwh"]

                overlap_start = max(s_start, d_start)
                overlap_end = min(s_end, d_end)
                overlap = (overlap_end - overlap_start).total_seconds()

                if overlap <= 0:
                    continue

                frac = overlap / (d_end - d_start).total_seconds()
                if frac <= 0:
                    continue

                slot_kwh += d_kwh * frac

            if slot_kwh <= 0:
                continue

            cost_gbp = slot_kwh * (price / 100.0)

            slot_costs.append(
                SlotCost(
                    start=s_start,
                    end=s_end,
                    kwh=slot_kwh,
                    price_p_per_kwh=price,
                    cost_gbp=cost_gbp,
                    phase=phase,
                )
            )

        return slot_costs
