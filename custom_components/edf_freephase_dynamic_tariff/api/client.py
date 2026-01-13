"""
HTTP client for retrieving EDF FreePhase Dynamic Tariff data.

This module handles all communication with the EDF Kraken API, including
pagination, response validation, and error handling. It returns raw API
items that are later transformed into unified slot structures by the
parsing module.
"""

from __future__ import annotations

import aiohttp
import async_timeout
import logging

# Using a local session because the EDF API is lightweight and short‑lived.
# If future API calls become more frequent, consider async_get_clientsession(hass).

_LOGGER = logging.getLogger(__name__)


async def fetch_all_pages(api_url: str, max_pages: int = 3) -> list[dict]:
    """
    Fetch all paginated EDF API results from the given URL.

    Parameters:
        api_url: The initial EDF API endpoint for tariff unit rates.
        max_pages: Maximum number of pages to follow via the "next" link.

    Returns:
        A flat list of raw result dictionaries returned by the EDF API.

    Notes:
        - Each page is expected to contain a "results" list.
        - Pagination stops early if a page is malformed or missing data.
        - Errors are logged but not raised; callers should validate output.
    """
    
    results = []
    url = api_url
    page_count = 0

    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(10):
            while url and page_count < max_pages:
                page_count += 1
                
                _LOGGER.debug("Fetching EDF API page %s: %s", page_count, url)
                
                resp = await session.get(url)
                resp.raise_for_status()

                try:
                    data = await resp.json()
                except Exception:
                    _LOGGER.error("EDF API returned non‑JSON on page %s", page_count)
                    break

                page_results = data.get("results")
                if not isinstance(page_results, list):
                    _LOGGER.error("EDF API page %s missing/invalid results", page_count)
                    break

                results.extend(page_results)
                url = data.get("next")

    return results