"""
Product‑metadata retrieval for the EDF FreePhase Dynamic Tariff integration.

This module provides the logic for fetching and lightly sanitising the full
product definition from EDF’s Kraken API. The product metadata endpoint
contains descriptive fields, tariff flags, availability windows, and contract
details that are used throughout the integration to enrich diagnostics, device
information, and UI presentation.

Responsibilities of this module include:

1. HTTP retrieval
   The function `fetch_product_metadata()` performs a single request to the
   product metadata endpoint, handling:
       • network timeouts
       • non‑200 responses
       • JSON decoding errors
       • defensive logging for malformed or unexpected payloads

2. Data validation
   The function ensures that the returned structure contains at least one
   meaningful field. If the API returns an empty or unusable object, the
   function logs the issue and returns `None` so the caller can degrade
   gracefully.

3. Description sanitisation
   EDF’s product descriptions may contain HTML markup. This module performs
   minimal cleanup—unescaping entities and converting list items into readable
   bullet points—while leaving the rest of the content intact.

No interpretation or transformation of tariff logic occurs here; the module’s
sole purpose is to retrieve and lightly clean the product metadata so that
other layers (metadata builder, diagnostics, sensors) can rely on a consistent
structure.
"""

from __future__ import annotations

import html
import logging

import aiohttp  # type: ignore
import async_timeout  # type: ignore

_LOGGER = logging.getLogger(__name__)


async def fetch_product_metadata(product_url: str) -> dict | None:
    """
    Fetch full product metadata from the EDF product endpoint.

    Parameters:
        product_url: The canonical EDF product metadata URL.

    Returns:
        A dictionary containing product metadata fields, or None on failure.
    """

    if not product_url:
        _LOGGER.error("Product metadata fetch aborted: product_url is missing")
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(product_url)

                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error(
                        "Product metadata fetch failed (%s): %s — Response: %s",
                        resp.status,
                        product_url,
                        text[:300],
                    )
                    return None

                try:
                    data = await resp.json()
                except Exception as json_err:
                    text = await resp.text()
                    _LOGGER.error(
                        "Product metadata JSON decode failed: %s — Raw response: %s",
                        json_err,
                        text[:300],
                    )
                    return None

        raw_description = data.get("description", "")
        try:
            cleaned_description = html.unescape(
                raw_description.replace("<li>", "• ").replace("</li>", "\n")
            ).strip()
        except Exception:
            cleaned_description = raw_description

        meta = {
            "code": data.get("code"),
            "full_name": data.get("full_name"),
            "display_name": data.get("display_name"),
            "description": cleaned_description,
            "is_variable": data.get("is_variable"),
            "is_green": data.get("is_green"),
            "is_tracker": data.get("is_tracker"),
            "is_prepay": data.get("is_prepay"),
            "is_business": data.get("is_business"),
            "is_restricted": data.get("is_restricted"),
            "term_months": data.get("term"),
            "available_from": data.get("available_from"),
            "available_to": data.get("available_to"),
            "tariffs_active_at": data.get("tariffs_active_at"),
        }

        if not any(v is not None for v in meta.values()):
            _LOGGER.error(
                "Product metadata fetch returned empty structure from %s — raw data: %s",
                product_url,
                str(data)[:300],
            )
            return None

        return meta

    except Exception as err:
        _LOGGER.error("Unexpected error fetching product metadata from %s: %s", product_url, err)
        return None
