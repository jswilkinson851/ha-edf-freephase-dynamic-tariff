"""
Classification rules for EDF FreePhase Dynamic Tariff slots.

This module encapsulates the logic used to determine the phase classification
(Green, Amber, or Red) for each half‑hour tariff slot. By isolating this logic
from the coordinator and sensor layers, the integration keeps the rules easy
to understand, test, and evolve independently of the rest of the system.

Classification is based on EDF’s published FreePhase Dynamic rules, combining
time‑of‑day windows with price‑based overrides:

    • Green:
        - price <= 0 (negative or free electricity), or
        - any slot starting between 23:00–06:00
    • Red:
        - slots starting between 16:00–19:00
    • Amber:
        - all remaining times

The module provides two entry points:

    • classify_slot(start_time, price)
        Classifies a single slot based on its timestamp and VAT‑inclusive price.

    • classify_slots(slots)
        Bulk‑classifies a list of slot dictionaries in place, adding a "phase"
        key to each item.

Keeping this logic centralised ensures consistent classification across the
coordinator, sensors, event entities, and diagnostics output, and makes future
adjustments to EDF’s rules straightforward to implement.
"""

from __future__ import annotations

from datetime import time

import dateutil.parser  # pyright: ignore[reportMissingModuleSource] # pylint: disable=import-error # pylance: disable=reportMissingModuleSource


def classify_slot(start_time: str, price: float) -> str:
    """
    Determine the phase (Green/Amber/Red) for a tariff slot.

    Parameters:
        start_time: ISO timestamp string for the slot start.
        price: The slot price including VAT.

    Returns:
        A string representing the phase classification:
            - "Green"
            - "Amber"
            - "Red"

    Notes:
        Classification is based on EDF FreePhase rules:
        - Green: price <= 0 or 23:00–06:00
        - Red: 16:00–19:00
        - Amber: all other times
    """

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

    # Fallback: any unclassified time defaults to Amber
    return "Amber"

def classify_slots(slots: list[dict]) -> list[dict]:
    """
    Bulk-classify a list of slot dicts in-place.

    Expects each slot to have:
        - "start": ISO timestamp string
        - "value": price including VAT

    Returns the same list with "phase" set on each slot.
    """
    for slot in slots:
        start = slot.get("start")
        value = slot.get("value")
        if start is not None and value is not None:
            slot["phase"] = classify_slot(start, value)
    return slots  # pylint: disable=missing-final-newline
