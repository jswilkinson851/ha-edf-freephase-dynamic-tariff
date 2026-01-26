"""
Shared helper utilities for the EDF FreePhase Dynamic Tariff integration.

This module centralises all cross‑cutting helper functions used throughout the
integration, providing a single, well‑documented source of truth for:

1. URL Construction
   - Canonical EDF product metadata endpoint.
   - Unit‑rate API URL builder with caching.

2. Tariff Metadata Normalisation
   - HTML cleaning.
   - Key normalisation to snake_case.
   - Region label injection.

3. Device Metadata
   - A consistent DeviceInfo object ensuring all entities group under a single
     device in Home Assistant.

4. Slot and Phase Normalisation
   - Parsing and normalising slot dictionaries.
   - Grouping consecutive slots into phase blocks.
   - Formatting blocks for sensors (start/end/duration/price/icon).

5. Phase‑Block and Price Formatting
   - Human‑readable timestamps.
   - Price conversions (p/kWh → £/kWh).
   - Phase‑appropriate MDI icons.

6. Import Sensor Validation
   - Used by config_flow and options_flow.
   - Ensures candidate import sensors provide cumulative kWh readings suitable
     for cost calculations.

These helpers are intentionally stateless (except for small LRU caches) and are
safe to use across coordinators, sensors, and flows. They form the integration’s
utility layer and are designed for clarity, maintainability, and correctness.
"""

from __future__ import annotations

import re
import html
import logging

from functools import lru_cache
from typing import Tuple, Optional
from datetime import datetime, timezone

# pylint: disable=import-error
from homeassistant.util.dt import parse_datetime, as_local  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.device_registry import DeviceInfo  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL helpers (canonical source of truth)
# ---------------------------------------------------------------------------


def get_product_base_url() -> str:
    """
    Return the canonical EDF product metadata endpoint.

    This is the authoritative base URL for all tariff metadata and unit‑rate
    queries. Centralising it here ensures consistency across coordinators,
    validators, and metadata extractors.
    """

    return "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"


@lru_cache(maxsize=64)
def build_edf_urls(tariff_code: str) -> dict[str, str]:
    """
    Build and return the product and unit‑rate URLs for a given tariff code.

    The result is cached to avoid repeated string manipulation and to ensure
    consistent URL construction across the integration.

    Returns:
        {
            "product_url": <canonical metadata URL>,
            "api_url": <unit‑rate endpoint for the given tariff code>,
            "standing_charges_url": <standing‑charges endpoint for the given tariff code>,
        }
    """

    base = get_product_base_url()
    code = (tariff_code or "").strip()
    return {
        "product_url": base,
        "api_url": f"{base}electricity-tariffs/{code}/standard-unit-rates/",
        "standing_charges_url": f"{base}electricity-tariffs/{code}/standing-charges/",
    }


# ---------------------------------------------------------------------------
# Tariff metadata extraction
# ---------------------------------------------------------------------------


def extract_tariff_metadata(product_meta: dict, region_label: str | None = None) -> dict:
    """
    Extract, clean, and normalise tariff metadata returned by the EDF product
    metadata endpoint.

    Behaviour:
        - Keys are normalised to snake_case.
        - HTML content in description fields is stripped and unescaped.
        - Whitespace is collapsed for readability.
        - A region_label is injected if provided.

    This function ensures that all metadata exposed to sensors and diagnostics
    is clean, predictable, and safe for UI display.
    """

    if not isinstance(product_meta, dict):
        return {}  # Defensive check # type: ignore[unreachable]

    cleaned: dict = {}
    for key, value in product_meta.items():
        if value is None:
            continue

        # Normalise keys
        norm_key = key.lower().replace(" ", "_")

        # Clean HTML description → plain text
        if norm_key == "description" and isinstance(value, str):
            text = re.sub(r"<[^>]+>", " ", value)
            text = html.unescape(text)
            text = re.sub(r"\s+", " ", text).strip()
            cleaned[norm_key] = text
        else:
            cleaned[norm_key] = value

    # Add region label if provided
    if region_label:
        cleaned["region_label"] = region_label

    return cleaned


# ---------------------------------------------------------------------------
# Device Info
# ---------------------------------------------------------------------------


def edf_device_info(entry_id: str) -> DeviceInfo:
    """
    Return a DeviceInfo object representing the EDF FreePhase Dynamic Tariff
    integration.

    Using the config entry ID as the device identifier ensures that all entities
    created for the same config entry are grouped under a single device in the
    Home Assistant UI. This improves clarity and discoverability for users.
    """

    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="EDF FreePhase Dynamic Tariff",
        manufacturer="EDF",
        model="FreePhase Dynamic",
    )


# ---------------------------------------------------------------------------
# Phase/slot helpers
# ---------------------------------------------------------------------------


def normalise_phase(phase: str | None) -> str:
    """
    Normalise a phase string into a clean, lowercase value.

    Returns an empty string if the input is None or empty. This ensures
    consistent comparisons across the integration.
    """

    if not phase:
        return ""
    return phase.strip().lower()


def normalise_slot(slot: dict) -> dict:
    """
    Normalise a raw slot dictionary by parsing timestamps and cleaning fields.

    Adds:
        - start_dt / end_dt: parsed datetime objects (or None)
        - phase: normalised lowercase phase
        - currency: defaults to GBP if missing

    This function ensures that all slot dictionaries used by coordinators and
    sensors have a consistent, predictable structure.
    """

    start_raw = slot.get("start")
    end_raw = slot.get("end")

    start_dt = None
    end_dt = None
    try:
        if start_raw:
            start_dt = parse_datetime(start_raw) or None
        if end_raw:
            end_dt = parse_datetime(end_raw) or None
    except Exception:  # pylint: disable=broad-except
        start_dt = None
        end_dt = None

    return {
        "start": start_raw,
        "end": end_raw,
        "start_dt": start_dt,
        "end_dt": end_dt,
        "value": slot.get("value"),
        "phase": normalise_phase(slot.get("phase")),
        "currency": slot.get("currency", "GBP"),
    }


def group_phase_blocks(slots: list[dict]) -> list[list[dict]]:
    """
    Group consecutive slots with the same phase into merged blocks.

    Returns:
        A list of blocks, where each block is a list of slot dictionaries.

    This is used by summary sensors and block‑level sensors to present a
    high‑level view of tariff phases rather than individual half‑hour slots.
    """

    if not slots:
        return []

    try:
        # Sort all None timestamps last, without errors.
        slots = sorted(slots, key=lambda s: (s["start_dt"] is None, s["start_dt"]))
    except KeyError:
        slots = sorted(slots, key=lambda s: s["start"])

    blocks: list[list[dict]] = []
    current: list[dict] = [slots[0]]

    for slot in slots[1:]:
        if slot["phase"] == current[-1]["phase"]:
            current.append(slot)
        else:
            blocks.append(current)
            current = [slot]

    blocks.append(current)
    return blocks


def format_slot_times(
    start_raw: str | None, end_raw: str | None
) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    """
    Convert raw ISO timestamps into human‑readable local times and compute
    duration in minutes.

    Returns:
        (start_fmt, end_fmt, duration_minutes)
    """

    start = parse_datetime(start_raw) if start_raw else None
    end = parse_datetime(end_raw) if end_raw else None

    if start:
        start = as_local(start)
        start_fmt = start.strftime("%H:%M on %d/%m/%Y")
    else:
        start_fmt = None

    if end:
        end = as_local(end)
        end_fmt = end.strftime("%H:%M on %d/%m/%Y")
    else:
        end_fmt = None

    if start and end:
        duration = (end - start).total_seconds() / 60
    else:
        duration = None

    return start_fmt, end_fmt, duration


def format_price_fields(price_pence_per_kwh: float | None) -> dict:
    """
    Format a price expressed in pence per kWh into multiple representations:

        - Raw pence value
        - Formatted pence string (e.g., "34.500 p/kWh")
        - Formatted GBP string (e.g., "0.34500 £/kWh")

    Returns a dictionary suitable for merging into a phase‑block structure.
    """

    if price_pence_per_kwh is None:
        return {"price_pence_per_kwh": None, "price_pen_per_kwh": None, "price_gbp_per_kwh": None}

    gbp = price_pence_per_kwh / 100.0
    return {
        "price_pence_per_kwh": price_pence_per_kwh,
        "price_pen_per_kwh": f"{price_pence_per_kwh:.3f} p/kWh",
        "price_gbp_per_kwh": f"{gbp:.5f} £/kWh",
    }


def icon_for_phase(phase: str | None) -> str:
    """
    Return an appropriate MDI icon for a tariff phase.

    Provides user‑friendly visual cues for dashboards and sensors.
    """

    if not phase:
        return "mdi:help-circle"

    phase = phase.lower()

    if phase == "green":
        return "mdi:leaf"
    if phase == "amber":
        return "mdi:clock-outline"
    if phase == "red":
        return "mdi:alert"

    return "mdi:help-circle"


def format_phase_block(block: list[dict]) -> dict:
    """
    Format a merged phase block into a structured dictionary containing:

        - phase
        - start / end (human‑readable)
        - duration_minutes
        - start_dt / end_dt (ISO format for dashboards & automations)
        - price fields (raw + formatted)
        - icon

    This is the canonical representation used by all block‑level sensors.
    """

    if not block:
        return {}

    start_raw = block[0].get("start")
    end_raw = block[-1].get("end")
    phase = block[0].get("phase")
    price = block[0].get("value")

    start_fmt, end_fmt, duration = format_slot_times(start_raw, end_raw)

    return {
        "phase": phase,
        "start": start_fmt,
        "end": end_fmt,
        "start_dt": block[0].get("start_dt"),
        "end_dt": block[-1].get("end_dt"),
        "duration_minutes": duration,
        **format_price_fields(price),
        "icon": icon_for_phase(phase),
    }


def find_current_block(all_slots: list[dict], current_slot: dict | None):
    """
    Identify and return the merged block containing the current slot.

    Behaviour:
        - Filters out slots without parsed timestamps.
        - Sorts chronologically.
        - Expands backwards and forwards to collect all consecutive slots with
          the same phase.

    Returns:
        A list of slot dictionaries representing the current block, or None.
    """

    if not current_slot or not current_slot.get("start_dt"):
        return None

    current_phase = current_slot["phase"]
    current_start = current_slot["start_dt"]

    # NEW: filter out slots with no start_dt
    slots = [s for s in all_slots if s.get("start_dt") is not None]

    # Sort safely
    slots = sorted(slots, key=lambda s: s["start_dt"])

    try:
        idx = next(i for i, s in enumerate(slots) if s["start_dt"] == current_start)
    except StopIteration:
        return None

    block = [slots[idx]]

    # Extend backwards
    for s in reversed(slots[:idx]):
        if s["phase"] == current_phase:
            block.insert(0, s)
        else:
            break

    # Extend forwards
    for s in slots[idx + 1 :]:
        if s["phase"] == current_phase:
            block.append(s)
        else:
            break

    return block


def find_next_phase_block(slots: list[dict], phase: str):
    """
    Identify the next merged block for a given phase.

    Behaviour:
        - Filters out slots without parsed timestamps.
        - Sorts chronologically.
        - Finds the first slot matching the requested phase.
        - Extends forward to collect all consecutive slots of that phase.

    Returns:
        A list of slot dictionaries representing the next block, or None.
    """

    if not slots:
        return None

    # NEW: filter out slots with no start_dt
    slots = [s for s in slots if s.get("start_dt") is not None]

    if not slots:
        return None

    slots = sorted(slots, key=lambda s: s["start_dt"])

    first = next((s for s in slots if s["phase"] == phase), None)
    if not first:
        return None

    block = [first]
    idx = slots.index(first)

    for s in slots[idx + 1 :]:
        if s["phase"] == phase:
            block.append(s)
        else:
            break

    return block


# ---------------------------------------------------------------------------
# Import sensor validation (used by config_flow and options flow)
# ---------------------------------------------------------------------------


async def validate_import_sensor(hass, entity_id: str) -> tuple[bool, list[str]]:
    """
    Validate whether a candidate import sensor is suitable for cumulative kWh
    tracking.

    Returns:
        (ok, reasons)
        - ok=True  → sensor is acceptable
        - ok=False → reasons contains human‑readable issues

    Validation rules:
        1. Entity must exist.
        2. Unit of measurement must be kWh or Wh.
        3. state_class must be 'total' or 'total_increasing'.
        4. If the current state is numeric, accept immediately (subject to attrs).
        5. Otherwise, attempt to read recorder history:
            - Require at least two numeric states in the last 24 hours.
        6. If recorder is unavailable, return a soft warning.

    This function is used by both the config flow and options flow to ensure
    users select a valid import sensor for cost calculations.
    """

    reasons: list[str] = []

    # ---- 1. Basic existence and attribute checks ----
    st = hass.states.get(entity_id)
    if st is None:
        return False, [f"Entity {entity_id} not found"]

    unit = st.attributes.get("unit_of_measurement")
    state_class = st.attributes.get("state_class")

    if unit not in ("kWh", "Wh"):
        reasons.append("Unit must be kWh or Wh")

    if state_class not in ("total", "total_increasing"):
        reasons.append("state_class should be 'total' or 'total_increasing'")

    # Helper to test numeric state
    def is_numeric_state(value: str) -> bool:
        try:
            float(value)
            return True
        except Exception:  # pylint: disable=broad-except
            return False

    # ---- 2. If current state is numeric, we can accept immediately ----
    current_state_str = st.state
    if is_numeric_state(current_state_str):
        # Attributes OK → accept
        if not reasons:
            return True, []
        # Attributes not OK → return issues
        return False, reasons

    # 3. ---- Current state is NOT numeric → try recorder history ----
    try:
        # Import recorder *inside* the function to avoid import-time overhead
        from homeassistant.components.recorder import history as recorder_history  # pyright: ignore[reportMissingImports] # pylint: disable=import-error disable=import-outside-toplevel

        # Query last 24 hours of significant states
        recent = await recorder_history.get_significant_states(
            hass,
            entity_id,
            24 * 3600,  # seconds
        )

        # Filter numeric states
        numeric_states = [s for s in recent if s is not None and is_numeric_state(s.state)]

        if len(numeric_states) >= 2:
            # Enough numeric history → accept if attributes OK
            if not reasons:
                return True, []
            return False, reasons

        # Not enough numeric history
        reasons.append("Not enough numeric history (recorder returned fewer than 2 numeric entries)")  # pylint: disable=line-too-long
        return False, reasons

    except Exception:  # pylint: disable=broad-except
        # ---- 4. Recorder unavailable → soft warning ----
        reasons.append("Could not verify recorder history (recorder may be disabled or DB inaccessible)")  # pylint: disable=line-too-long

        # If this is the ONLY issue, return a soft warning
        if len(reasons) == 1:
            return False, reasons

        # Otherwise return all issues
        return False, reasons


# ---------------------------------------------------------------------------
# End of shared helpers
# ---------------------------------------------------------------------------
