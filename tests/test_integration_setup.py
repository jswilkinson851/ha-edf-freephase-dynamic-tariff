import pytest

from custom_components.edf_freephase_dynamic_tariff import async_setup_entry, async_unload_entry


@pytest.mark.asyncio
async def test_integration_setup_and_unload(hass):
    entry = hass.config_entries.async_create_entry(
        domain="edf_freephase_dynamic_tariff",
        data={"tariff_code": "X", "scan_interval": 30},
        title="EDF",
    )

    assert await async_setup_entry(hass, entry)
    assert await async_unload_entry(hass, entry)