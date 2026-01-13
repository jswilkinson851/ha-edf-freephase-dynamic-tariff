import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edf_freephase_dynamic_tariff import (
    async_setup_entry,
    async_unload_entry,
)


@pytest.mark.asyncio
async def test_integration_setup_and_unload(hass):
    entry = MockConfigEntry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )
    entry.add_to_hass(hass)

    assert await async_setup_entry(hass, entry)
    assert await async_unload_entry(hass, entry)