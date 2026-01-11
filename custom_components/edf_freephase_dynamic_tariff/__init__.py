from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import EDFCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up EDF FreePhase Dynamic Tariff Integration from YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EDF FreePhase Dynamic Tariff from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Build API URL
    tariff_code = entry.data["tariff_code"]
    api_url = (
        f"https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"
        f"electricity-tariffs/{tariff_code}/standard-unit-rates/"
    )

    # Build scan interval
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    # Create coordinator
    coordinator = EDFCoordinator(hass, api_url, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator for sensors + diagnostics
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator
    }

    # Listen for config entry updates (e.g., scan interval changes)
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