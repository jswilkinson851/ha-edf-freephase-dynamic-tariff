"""
Parsing and transformation utilities for EDF FreePhase Dynamic Tariff slot data.

This module forms the core of the integration’s data‑model layer. It takes the
raw, heterogeneous structures returned by EDF’s Kraken API and converts them
into a unified, internally consistent representation that the rest of the
integration can rely on. The parsing layer is intentionally isolated from both
the HTTP client and the Home Assistant entity platforms, ensuring that all
components operate on clean, predictable slot dictionaries.

The responsibilities of this module include:

1. Normalising raw API items
   `build_unified_dataset()` converts EDF’s unit‑rate objects into a standard
   slot structure with:
       • start/end timestamps (raw + ISO)
       • VAT‑inclusive price
       • phase classification (via `classification.classify_slot`)
       • currency metadata
       • internal datetime objects used for sorting and boundary calculations

   The unified dataset is always returned in chronological order.

2. Stripping internal fields
   `strip_internal()` removes private datetime objects used for sorting
   (`_start_dt_obj`, `_end_dt_obj`) before data is exposed to sensors,
   diagnostics, or event entities. This keeps the public representation clean
   while preserving efficient internal operations.

3. Building forecast windows
   `build_forecasts()` constructs the four key forecast datasets used
   throughout the integration:
       • next 24 hours (48 half‑hour slots)
       • today’s slots
       • tomorrow’s slots
       • yesterday’s slots

   These datasets are derived from the unified list and anchored to the
   current UTC time.

4. Producing normalised forecast output
   `build_normalised_forecasts()` converts all forecast datasets into the
   final, sensor‑ready slot format using `normalise_slot()`. This ensures that
   every consumer—sensors, diagnostics, event entities—receives a consistent,
   minimal, and serialisable structure.

By centralising all parsing and transformation logic here, the integration
maintains a clear separation of concerns: the HTTP client retrieves raw data,
this module shapes it into a coherent model, and the coordinators and entities
consume that model without needing to understand EDF’s API quirks.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import dateutil.parser  # pyright: ignore[reportMissingImports, reportMissingModuleSource] # pylint: disable=import-error

from ..helpers import normalise_slot
from .classification import classify_slot


def build_unified_dataset(raw_items: list[dict]) -> list[dict]:
    """
    Convert raw EDF API items into a unified internal slot structure.

    Parameters:
        raw_items: A list of dictionaries returned directly from the EDF API.

    Returns:
        A list of slot dictionaries containing:
            - start/end timestamps (raw + ISO)
            - price and currency
            - phase classification
            - internal datetime objects for sorting

    Notes:
        - The returned list is sorted chronologically by start time.

        - Internal datetime objects (_start_dt_obj, _end_dt_obj) are included
          to support efficient sorting and comparisons before being stripped
          out for sensor exposure.
    """

    unified = []

    for item in raw_items:
        start_raw = item["valid_from"]
        end_raw = item["valid_to"]

        start_dt = dateutil.parser.isoparse(start_raw)
        end_dt = dateutil.parser.isoparse(end_raw)

        unified.append(
            {
                "start": start_raw,
                "end": end_raw,
                "start_dt": start_dt.isoformat(),
                "end_dt": end_dt.isoformat(),
                "value": item["value_inc_vat"],
                "phase": classify_slot(start_raw, item["value_inc_vat"]),
                "currency": "GBP",
                "_start_dt_obj": start_dt,
                "_end_dt_obj": end_dt,
            }
        )

    unified.sort(key=lambda s: s["_start_dt_obj"])
    return unified


def strip_internal(slots: list[dict]) -> list[dict]:
    """
    Remove internal datetime objects from slot dictionaries.

    Parameters:
        slots: A list of unified slot dictionaries containing internal fields.

    Returns:
        A new list of dictionaries with internal keys removed:
            - _start_dt_obj
            - _end_dt_obj

    Notes:
        This is used before exposing data to sensors or diagnostics.
    """

    cleaned = []
    for s in slots:
        s2 = dict(s)
        s2.pop("_start_dt_obj", None)
        s2.pop("_end_dt_obj", None)
        cleaned.append(s2)
    return cleaned


def build_forecasts(unified: list[dict], now: datetime) -> dict:
    """
    Build forecast datasets for today, tomorrow, yesterday, and the next 24 hours.

    Parameters:
        unified: A chronologically sorted list of unified slot dictionaries.
        now: The current UTC datetime used to determine boundaries.

    Returns:
        A dictionary containing:
            - next_24_hours
            - today_24_hours
            - tomorrow_24_hours
            - yesterday_24_hours

    Notes:
        next_24_hours returns the next 48 half‑hour slots starting from 'now'.
    """

    today = now.date()
    tomorrow = (now + timedelta(days=1)).date()
    yesterday = (now - timedelta(days=1)).date()

    future = [s for s in unified if s["_start_dt_obj"] >= now]

    return {
        "next_24_hours": future[:48],
        "today_24_hours": [s for s in unified if s["_start_dt_obj"].date() == today],
        "tomorrow_24_hours": [s for s in unified if s["_start_dt_obj"].date() == tomorrow],
        "yesterday_24_hours": [s for s in unified if s["_start_dt_obj"].date() == yesterday],
    }


def build_normalised_forecasts(unified: list[dict], forecasts: dict) -> dict:
    """
    Convert all forecast datasets into normalised slot structures.

    Returns:
        {
            "all_slots_sorted": [...],
            "next_24_hours": [...],
            "today_24_hours": [...],
            "tomorrow_24_hours": [...],
            "yesterday_24_hours": [...],
        }
    """

# pylint: disable=line-too-long
    return {
        "all_slots_sorted": [normalise_slot(s) for s in strip_internal(unified)],
        "next_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["next_24_hours"])],
        "today_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["today_24_hours"])],
        "tomorrow_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["tomorrow_24_hours"])],  # pylint: disable=line-too-long
        "yesterday_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["yesterday_24_hours"])],  # pylint: disable=line-too-long
    }
# pylint: disable=line-too-long
