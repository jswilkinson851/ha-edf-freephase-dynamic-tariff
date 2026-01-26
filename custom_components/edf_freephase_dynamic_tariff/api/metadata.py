"""
Metadata builder for the EDF FreePhase Dynamic Tariff integration.

This module constructs a unified tariff‑metadata dictionary by combining
product‑level information retrieved from EDF’s product metadata endpoint with
the region label selected by the user during configuration. The resulting
structure provides a single, coherent source of truth describing the tariff,
including both static product attributes and user‑specific regional context.

The metadata produced here is used throughout the integration—for example in
diagnostics, device information, and UI presentation—to ensure that all
components reference consistent, human‑readable tariff details.

Only lightweight merging is performed in this module. Retrieval of the raw
product metadata is delegated to `fetch_product_metadata()` in `api/product.py`,
and no interpretation or transformation of EDF’s fields occurs here. If the
API returns no metadata, a minimal dictionary containing only the product name
and region label is returned to guarantee predictable behaviour.
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
    }  # pylint: disable=missing-final-newline # noqa: W292