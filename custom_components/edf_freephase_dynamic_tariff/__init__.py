import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import EDFCoordinator
from .helpers import build_edf_urls

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up EDF FreePhase Dynamic Tariff Integration from YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EDF FreePhase Dynamic Tariff from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Build URLs using helper
    urls = build_edf_urls(entry.data["tariff_code"])
    product_url = urls["product_url"]
    api_url = urls["api_url"]

    # Optional debug (commented out)
    # _LOGGER.warning("EDF DEBUG INIT: product_url=%s api_url=%s", product_url, api_url)

    # Build scan interval
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    # Create coordinator
    coordinator = EDFCoordinator(hass, product_url, api_url, scan_interval)

    # Attach config entry so coordinator can access region label
    coordinator.config_entry = entry

    # Perform first refresh (non-blocking)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator + URLs for sensors/diagnostics
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "tariff_code": entry.data["tariff_code"],
        "product_url": product_url,
        "api_url": api_url,
        "tariff_region_label": entry.data.get("tariff_region_label"),
    }

    # Listen for config entry updates
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options updates by reloading the integration."""
    await hass.config_entries.async_reload(entry.entry_id)
