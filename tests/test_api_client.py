import pytest
from aioresponses import aioresponses

from custom_components.edf_freephase_dynamic_tariff.api.client import fetch_all_pages


@pytest.mark.asyncio
async def test_fetch_all_pages_single_page():
    url = "https://example.com/api"

    # Disable global thread checker once per test
    with aioresponses() as mock:
        mock._thread_checker = lambda: True

        mock.get(
            url,
            payload={"results": [{"x": 1}], "next": None},
        )

        results = await fetch_all_pages(url)
        assert results == [{"x": 1}]


@pytest.mark.asyncio
async def test_fetch_all_pages_pagination():
    url = "https://example.com/api"

    with aioresponses() as mock:
        mock._thread_checker = lambda: True

        mock.get(
            url,
            payload={"results": [{"x": 1}], "next": url + "?page=2"},
        )
        mock.get(
            url + "?page=2",
            payload={"results": [{"x": 2}], "next": None},
        )

        results = await fetch_all_pages(url)
        assert results == [{"x": 1}, {"x": 2}]


@pytest.mark.asyncio
async def test_fetch_all_pages_invalid_json():
    url = "https://example.com/api"

    with aioresponses() as mock:
        mock._thread_checker = lambda: True

        mock.get(
            url,
            body="not json",
            status=200,
        )

        results = await fetch_all_pages(url)
        assert results == []