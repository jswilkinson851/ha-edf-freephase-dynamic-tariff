"""
Slot classification logic for EDF FreePhase Dynamic Tariff.

This module contains the rules that determine whether a slot is Green,
Amber, or Red based on time-of-day and price. Keeping this logic isolated
makes it easier to adjust or extend classification rules in the future.
"""

from __future__ import annotations

from datetime import time
import dateutil.parser


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
    return slots