"""
Product metadata fetcher for EDF FreePhase Dynamic Tariff.

This module retrieves the full product definition from the EDF Kraken API,
including descriptive fields, flags, availability windows, and contract term.
"""

from __future__ import annotations

import aiohttp
import async_timeout
import html
import logging

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