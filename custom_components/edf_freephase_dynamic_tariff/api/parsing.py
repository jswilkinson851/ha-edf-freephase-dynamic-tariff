"""
Data parsing and transformation utilities for EDF tariff slot data.

This module converts raw EDF API responses into a unified internal
representation, strips internal fields for sensor exposure, and builds
forecast datasets (today, tomorrow, yesterday, next 24 hours). It forms
the core of the integration’s data model.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import dateutil.parser

from .classification import classify_slot
from ..helpers import normalise_slot


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

    return {
        "all_slots_sorted": [normalise_slot(s) for s in strip_internal(unified)],
        "next_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["next_24_hours"])],
        "today_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["today_24_hours"])],
        "tomorrow_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["tomorrow_24_hours"])],
        "yesterday_24_hours": [normalise_slot(s) for s in strip_internal(forecasts["yesterday_24_hours"])],
    }
