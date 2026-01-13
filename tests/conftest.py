import pytest
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.edf_freephase_dynamic_tariff.coordinator import EDFCoordinator


@pytest.fixture
def fake_scan_interval():
    return timedelta(seconds=30)


@pytest.fixture
def fake_api_url():
    return "https://example.com/api/unit-rates"


@pytest.fixture
def coordinator(hass: HomeAssistant, fake_api_url, fake_scan_interval):
    """Create a coordinator instance without running refresh."""
    return EDFCoordinator(hass, fake_api_url, fake_scan_interval)


@pytest.fixture
async def setup_integration(hass: HomeAssistant):
    """Load the integration (without config flow)."""
    assert await async_setup_component(
        hass,
        "custom_components.edf_freephase_dynamic_tariff",
        {},
    )
    await hass.async_block_till_done()