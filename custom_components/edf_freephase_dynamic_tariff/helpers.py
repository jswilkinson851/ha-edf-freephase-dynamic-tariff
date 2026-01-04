from __future__ import annotations

from datetime import time

import dateutil.parser


def classify_slot(start_time: str, price: float) -> str:
    """Return green/amber/red classification for a slot."""
    dt = dateutil.parser.isoparse(start_time)
    t = dt.time()

    # Free electricity override (negative wholesale)
    if price <= 0:
        return "green"

    # Daily schedule
    if time(23, 0) <= t or t < time(6, 0):
        return "green"
    if time(6, 0) <= t < time(16, 0):
        return "amber"
    if time(16, 0) <= t < time(19, 0):
        return "red"
    if time(19, 0) <= t < time(23, 0):
        return "amber"

    return "amber"
    
def edf_device_info():
    """Return consistent device info for all EDF sensors."""
    from .const import DEVICE_IDENTIFIERS, DEVICE_NAME, MANUFACTURER, DEVICE_MODEL

    return {
        "identifiers": DEVICE_IDENTIFIERS,
        "name": DEVICE_NAME,
        "manufacturer": MANUFACTURER,
        "model": DEVICE_MODEL,
        "entry_type": "service",
    }