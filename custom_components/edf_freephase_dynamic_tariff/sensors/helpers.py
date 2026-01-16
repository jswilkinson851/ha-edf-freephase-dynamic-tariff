"""
Helpers used by the various sensors for the EDF FreePhase Dynamic Tariff integration.
"""

from __future__ import annotations

from homeassistant.util.dt import parse_datetime, as_local


# ---------------------------------------------------------------------------
# URL helpers (canonical source of truth)
# ---------------------------------------------------------------------------

def get_product_base_url() -> str:
    """Return the canonical EDF product metadata endpoint."""
    return "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"


def build_edf_urls(tariff_code: str) -> dict[str, str]:
    """Return product and unit-rate URLs for a given tariff code."""
    base = get_product_base_url()
    return {
        "product_url": base,
        "api_url": f"{base}electricity-tariffs/{tariff_code}/standard-unit-rates/",
    }


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_tariff_metadata(product_meta: dict) -> dict:
    """
    Extract and normalise tariff metadata from the product metadata endpoint.
    """
    if not isinstance(product_meta, dict):
        return {}

    cleaned = {}
    for key, value in product_meta.items():
        if value is None:
            continue
        cleaned[key.lower().replace(" ", "_")] = value

    return cleaned


# ---------------------------------------------------------------------------
# Shared helper: Device info dictionary
# ---------------------------------------------------------------------------

def edf_device_info():
    """Return device metadata for all EDF FreePhase sensors."""
    return {
        "identifiers": {
            ("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")
        },
        "name": "EDF FreePhase Dynamic Tariff",
        "manufacturer": "EDF",
        "model": "FreePhase Dynamic Tariff API",
        "entry_type": "service",
    }


# ---------------------------------------------------------------------------
# Shared helper: normalise phase names
# ---------------------------------------------------------------------------

def normalise_phase(phase: str | None) -> str:
    """Return a clean lowercase phase string."""
    if not phase:
        return ""
    return phase.strip().lower()


# ---------------------------------------------------------------------------
# Shared helper: normalise a slot dict
# ---------------------------------------------------------------------------

def normalise_slot(slot: dict) -> dict:
    """Return a normalised slot dictionary with consistent keys and phase."""
    return {
        "start": slot.get("start"),
        "end": slot.get("end"),
        "start_dt": slot.get("start_dt"),
        "end_dt": slot.get("end_dt"),
        "value": slot.get("value"),
        "phase": normalise_phase(slot.get("phase")),
        "currency": slot.get("currency", "GBP"),
    }


# ---------------------------------------------------------------------------
# Shared helper: group consecutive slots into phase blocks
# ---------------------------------------------------------------------------

def group_phase_blocks(slots: list[dict]) -> list[list[dict]]:
    """Group consecutive slots with the same (normalised) phase."""
    if not slots:
        return []

    try:
        slots = sorted(slots, key=lambda s: s["start_dt"])
    except KeyError:
        slots = sorted(slots, key=lambda s: s["start"])

    blocks = []
    current = [slots[0]]

    for slot in slots[1:]:
        if slot["phase"] == current[-1]["phase"]:
            current.append(slot)
        else:
            blocks.append(current)
            current = [slot]

    blocks.append(current)
    return blocks


# ---------------------------------------------------------------------------
# Shared helper: format start/end/duration for a block
# ---------------------------------------------------------------------------

def format_slot_times(start_raw: str | None, end_raw: str | None):
    """Return (start_fmt, end_fmt, duration_minutes)."""
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


# ---------------------------------------------------------------------------
# Shared helper: format price fields
# ---------------------------------------------------------------------------

def format_price_fields(price: float | None) -> dict:
    """Return dict with price, p/kWh, £/kWh."""
    if price is None:
        return {
            "price": None,
            "price_pen_per_kwh": None,
            "price_pou_per_kwh": None,
        }

    return {
        "price": price,
        "price_pen_per_kwh": f"{price:.3f} p/kWh",
        "price_pou_per_kwh": f"{price/100:.5f} £/kWh",
    }


# ---------------------------------------------------------------------------
# Shared helper: map phase → icon
# ---------------------------------------------------------------------------

def icon_for_phase(phase: str | None) -> str:
    """Return the appropriate MDI icon for a tariff phase."""
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


# ---------------------------------------------------------------------------
# Shared helper: format a merged phase block into a standard dict
# ---------------------------------------------------------------------------

def format_phase_block(block: list[dict]) -> dict:
    """
    Given a list of consecutive slots with the same phase, return a fully
    formatted dictionary containing start/end/duration/price/icon.
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
        "duration_minutes": duration,
        **format_price_fields(price),
        "icon": icon_for_phase(phase),
    }


# ---------------------------------------------------------------------------
# Shared helper: current block detection
# ---------------------------------------------------------------------------

def find_current_block(all_slots: list[dict], current_slot: dict | None):
    """Return the full block (list of slots) containing the current slot."""
    if not current_slot or not current_slot.get("start_dt"):
        return None

    current_phase = current_slot["phase"]
    current_start = current_slot["start_dt"]

    slots = sorted(all_slots, key=lambda s: s["start_dt"])

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
    for s in slots[idx + 1:]:
        if s["phase"] == current_phase:
            block.append(s)
        else:
            break

    return block


# ---------------------------------------------------------------------------
# Shared helper: next phase block detection
# ---------------------------------------------------------------------------

def find_next_phase_block(slots: list[dict], phase: str):
    """Return the next block (list of slots) for a given phase."""
    if not slots:
        return None

    slots = sorted(slots, key=lambda s: s["start_dt"])

    first = next((s for s in slots if s["phase"] == phase), None)
    if not first:
        return None

    block = [first]
    idx = slots.index(first)

    for s in slots[idx + 1:]:
        if s["phase"] == phase:
            block.append(s)
        else:
            break

    return block