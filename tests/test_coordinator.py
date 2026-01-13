import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from custom_components.edf_freephase_dynamic_tariff.coordinator import EDFCoordinator


@pytest.mark.asyncio
async def test_coordinator_success(hass):
    coordinator = EDFCoordinator(
        hass,
        "https://example.com/api",
        30,
    )

    fake_raw = [
        {
            "valid_from": "2024-01-01T00:00:00Z",
            "valid_to": "2024-01-01T00:30:00Z",
            "value_inc_vat": 10,
        }
    ]

    with patch(
        "custom_components.edf_freephase_dynamic_tariff.api.client.fetch_all_pages",
        return_value=fake_raw,
    ), patch(
        "custom_components.edf_freephase_dynamic_tariff.api.parsing.build_unified_dataset",
        return_value=[
            {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-01T00:30:00Z",
                "value": 10,
                "phase": "Green",
            }
        ],
    ), patch(
        "custom_components.edf_freephase_dynamic_tariff.api.parsing.build_forecasts",
        return_value={"next_24_hours": []},
    ):
        data = await coordinator._async_update_data()

    assert data["current_price"] == 10
    assert data["coordinator_status"] == "ok"


@pytest.mark.asyncio
async def test_coordinator_error(hass):
    coordinator = EDFCoordinator(hass, "https://example.com/api", 30)

    with patch(
        "custom_components.edf_freephase_dynamic_tariff.api.client.fetch_all_pages",
        side_effect=Exception("boom"),
    ):
        data = await coordinator._async_update_data()

    assert data["coordinator_status"] == "error"
    assert data["current_price"] is None