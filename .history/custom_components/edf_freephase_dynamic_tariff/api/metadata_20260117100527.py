"""
Tariff metadata builder for EDF FreePhase Dynamic Tariff.

This module merges product metadata from the EDF product endpoint with
region metadata from the config entry, producing a unified metadata dict.
"""

from __future__ import annotations

from .product import fetch_product_metadata


async def build_tariff_metadata(product_url: str, region_label: str) -> dict:
    """
    Build a unified metadata dictionary describing the tariff product.

    Parameters:
        product_url: The EDF product metadata endpoint.
        region_label: The human-readable region label selected in config flow.

    Returns:
        A dictionary containing merged product + region metadata.
    """

    product_meta = await fetch_product_metadata(product_url)

    base = {
        "product_name": "EDF FreePhase Dynamic Tariff",
        "region_label": region_label,
    }

    if not product_meta:
        return base

    return {
        **base,
        **product_meta,
    }