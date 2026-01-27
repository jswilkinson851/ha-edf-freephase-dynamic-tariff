"""
HTTP client for EDF FreePhase Dynamic Tariff API access.

This module provides the low‑level HTTP retrieval layer used by the
integration to communicate with EDF’s Kraken API. It encapsulates all
network‑facing behaviour, including pagination handling, timeout management,
response validation, and defensive error handling. By isolating this logic,
the rest of the integration can operate on clean, predictable Python
structures without needing to worry about transport‑level concerns.

The client supports three categories of EDF API responses:

1. Single‑object metadata endpoints
   Returned as a flat dictionary containing product‑level information such as
   tariff codes, standing charges, and region mappings.

2. Paginated endpoints (unit‑rate data)
   Returned as a dictionary containing a `results` list and an optional `next`
   URL. The client automatically follows pagination links up to a configurable
   maximum number of pages, merging all results into a single list.

3. Raw list endpoints
   Rare but valid responses where the API returns a top‑level list without
   pagination or metadata.

Any unexpected or malformed responses are logged and returned as an empty
dictionary to ensure the coordinator can fail gracefully without raising
exceptions.

This module performs no transformation or interpretation of the returned
data; parsing, normalisation, and slot construction are handled by the
parsing layer under `api/`. The client’s sole responsibility is to retrieve
data reliably and return it in whatever structure the API provides.
"""

from __future__ import annotations

import logging

import aiohttp  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
import async_timeout  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

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
            except Exception:  # pylint: disable=broad-exception-caught
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
            return {}  # pylint: disable=missing-final-newline
