"""
HTTP client for retrieving EDF FreePhase Dynamic Tariff data.

This module handles all communication with the EDF Kraken API, including
pagination, response validation, and error handling. It returns raw API
items that are later transformed into unified slot structures by the
parsing module.
"""

from __future__ import annotations
import logging

import aiohttp # pyright: ignore[reportMissingImports]
import async_timeout # pyright: ignore[reportMissingImports]

# Using a local session because the EDF API is lightweight and short‑lived.
# If future API calls become more frequent, consider async_get_clientsession(hass).

_LOGGER = logging.getLogger(__name__)


async def fetch_all_pages(api_url: str, max_pages: int = 3):
    """
    Fetch EDF API data from either:
      - a paginated endpoint (unit rates)
      - a single-object endpoint (product metadata)
      - a list endpoint (rare but supported)

    Returns:
        dict | list
    """

    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(10):
            resp = await session.get(api_url)
            resp.raise_for_status()

            try:
                data = await resp.json()
            except Exception:
                _LOGGER.error("EDF API returned non‑JSON for URL: %s", api_url)
                return {}

            # ------------------------------------------
            # CASE 1: Product metadata (flat dict)
            # ------------------------------------------
            if isinstance(data, dict) and "results" not in data:
                _LOGGER.debug("EDF API returned single-object metadata")
                return data

            # ------------------------------------------
            # CASE 2: Paginated endpoint (unit rates)
            # ------------------------------------------
            if isinstance(data, dict) and isinstance(data.get("results"), list):
                results = []
                page = data
                page_count = 1

                while page and page_count <= max_pages:
                    page_results = page.get("results")
                    if not isinstance(page_results, list):
                        _LOGGER.error("EDF API page %s missing/invalid results", page_count)
                        break

                    results.extend(page_results)

                    next_url = page.get("next")
                    if not next_url:
                        break

                    _LOGGER.debug("Fetching EDF API page %s: %s", page_count + 1, next_url)
                    resp = await session.get(next_url)
                    resp.raise_for_status()
                    page = await resp.json()
                    page_count += 1

                return results

            # ------------------------------------------
            # CASE 3: Unexpected but valid list response
            # ------------------------------------------
            if isinstance(data, list):
                _LOGGER.debug("EDF API returned a raw list")
                return data

            # ------------------------------------------
            # CASE 4: Unknown structure
            # ------------------------------------------
            _LOGGER.error("EDF API returned unexpected structure: %s", type(data))
            return {}