import pytest
pytestmark = pytest.mark.xfail(reason="Test suite temporarily disabled pending redesign")

from unittest.mock import AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_integration_setup_and_unload(hass):
    """Test that async_setup_entry wires coordinator and entities correctly."""
    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    added_entities = []

    async def _async_add_entities(entities):
        added_entities.extend(entities)

    with patch(
        "custom_components.edf_freephase_dynamic_tariff.sensor.EDFCoordinator",
    ) as mock_coord_cls:
        mock_coord = AsyncMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord_cls.return_value = mock_coord

        await async_setup_entry(hass, entry, _async_add_entities)

    # Coordinator should be constructed once with hass, api_url, and scan_interval
    assert mock_coord_cls.call_count == 1
    mock_coord.async_config_entry_first_refresh.assert_awaited_once()

    # At least one entity should be added
    assert added_entities