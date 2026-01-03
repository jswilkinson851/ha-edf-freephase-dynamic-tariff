from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up EDF FreePhase Dynamic Tariff Integration from YAML (not used, but required)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EDF FreePhase Dynamic Tariff Integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if DOMAIN in hass.data:
        hass.data.pop(DOMAIN)
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return True