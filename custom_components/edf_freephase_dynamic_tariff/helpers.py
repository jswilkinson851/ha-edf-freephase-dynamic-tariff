"""
Helper utilities for EDF FreePhase Dynamic Tariff integration.

This module provides:
    - device info helper
    - URL builders
    - tariff metadata extraction (with HTML cleaning + region label)
    - phase block grouping (Slots → Phases)
    - phase block formatting for summary sensors
"""

from __future__ import annotations

import re
from homeassistant.helpers.entity import DeviceInfo


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
# Tariff metadata extraction
# ---------------------------------------------------------------------------

def extract_tariff_metadata(product_meta: dict, region_label: str | None = None) -> dict:
    """
    Extract and normalise tariff metadata from the product metadata endpoint.

    Enhancements:
        - Normalises keys to snake_case
        - Cleans HTML from description fields
        - Adds region_label if provided
    """
    if not isinstance(product_meta, dict):
        return {}

    cleaned: dict = {}

    for key, value in product_meta.items():
        if value is None:
            continue

        # Normalise keys
        norm_key = key.lower().replace(" ", "_")

        # Clean HTML description → plain text
        if norm_key == "description" and isinstance(value, str):
            text = re.sub(r"<[^>]+>", " ", value)  # strip tags
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

def edf_device_info() -> DeviceInfo:
    """Return the device info for all EDF FreePhase Dynamic entities."""
    return DeviceInfo(
        identifiers={("edf_freephase_dynamic", "edf_freephase_dynamic_tariff")},
        name="EDF FreePhase Dynamic Tariff",
        manufacturer="EDF",
        model="FreePhase Dynamic",
    )


# ---------------------------------------------------------------------------
# Phase grouping logic
# ---------------------------------------------------------------------------

def group_phase_blocks(slots: list[dict]) -> list[dict]:
    """Convert classified slots into merged phase blocks."""
    if not slots:
        return []

    slots = sorted(slots, key=lambda s: s["start"])

    blocks: list[dict] = []
    current_block: dict | None = None

    for slot in slots:
        phase = slot.get("phase", "Unknown")

        if current_block is None:
            current_block = {
                "phase": phase,
                "start": slot["start"],
                "end": slot["end"],
                "slots": [slot],
            }
            continue

        if slot["phase"] == current_block["phase"]:
            current_block["end"] = slot["end"]
            current_block["slots"].append(slot)
        else:
            blocks.append(current_block)
            current_block = {
                "phase": phase,
                "start": slot["start"],
                "end": slot["end"],
                "slots": [slot],
            }

    if current_block:
        blocks.append(current_block)

    # Compute min/max/avg prices
    for block in blocks:
        prices = [
            s["price"]
            for s in block["slots"]
            if isinstance(s.get("price"), (int, float))
        ]
        if prices:
            block["min_price"] = min(prices)
            block["max_price"] = max(prices)
            block["avg_price"] = sum(prices) / len(prices)
        else:
            block["min_price"] = None
            block["max_price"] = None
            block["avg_price"] = None

    return blocks


# ---------------------------------------------------------------------------
# Phase block formatting for summary sensors
# ---------------------------------------------------------------------------

def format_phase_block(block: dict) -> dict:
    """Convert a phase block into a clean attribute dictionary for sensors."""
    return {
        "phase": block.get("phase"),
        "start": block.get("start"),
        "end": block.get("end"),
        "duration_slots": len(block.get("slots", [])),
        "min_price": block.get("min_price"),
        "max_price": block.get("max_price"),
        "avg_price": block.get("avg_price"),
    }