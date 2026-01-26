"""
Debug‑logging switch entity for the EDF FreePhase Dynamic Tariff integration.

This module exposes a single switch entity that allows users to enable or
disable debug logging at runtime without modifying configuration files or
reloading the integration. The switch updates both:

1. The config entry options (persistent across restarts).
2. A domain‑level in‑memory flag used by coordinators to immediately adjust
   their logging behaviour.

This provides a convenient, UI‑driven mechanism for troubleshooting and
diagnostics while keeping the integration lightweight and user‑friendly.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from .const import DOMAIN
from .helpers import edf_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Set up the debug‑logging switch for a config entry.

    This function is invoked by Home Assistant when the integration's platforms
    are loaded. It registers a single EDFDebugLoggingSwitch instance, which
    exposes a user‑controllable toggle for enabling or disabling verbose
    diagnostic logging across the integration.
    """

    async_add_entities([EDFDebugLoggingSwitch(hass, entry)])


class EDFDebugLoggingSwitch(SwitchEntity):
    """
    Switch entity controlling the integration's debug‑logging mode.

    This entity provides a simple UI toggle that allows users to enable or
    disable verbose diagnostic logging without restarting Home Assistant or
    editing configuration files.

    Behaviour:
        - The switch state reflects the `debug_logging` option stored in the
          config entry.
        - Turning the switch on/off updates the config entry options.
        - A domain‑level in‑memory flag (`hass.data[DOMAIN]["debug_enabled"]`)
          is updated immediately so coordinators can adjust logging behaviour
          without waiting for a reload.

    The switch is grouped under the integration's main device via
    `edf_device_info()`, ensuring consistent presentation in the UI.
    """

    _attr_name = "EDF Debug Logging"
    _attr_icon = "mdi:bug"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_debug_logging"

    @property
    def is_on(self) -> bool:
        """
        Return True if debug logging is currently enabled.

        The value is read directly from the config entry options, ensuring that the
        switch reflects the persistent state stored by Home Assistant.
        """

        return self.entry.options.get("debug_logging", False)

    async def async_turn_on(self, **kwargs) -> None:
        """
        Enable debug logging.

        Updates both:
            - The config entry options (persistent)
            - The in‑memory domain flag (immediate effect)

        Coordinators can use the domain flag to adjust logging behaviour without
        requiring a reload.
        """

        new_options = {**self.entry.options, "debug_logging": True}
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        # Immediate in-memory flag
        self.hass.data.setdefault(DOMAIN, {})["debug_enabled"] = True

        self.async_write_ha_state()

    @property
    def device_info(self):
        """
        Return the DeviceInfo object linking this switch to the integration's
        primary device.

        This ensures the switch appears alongside all other EDF FreePhase Dynamic
        Tariff entities in the Home Assistant UI.
        """

        return edf_device_info(self.entry.entry_id)

    async def async_turn_off(self, **kwargs) -> None:
        """
        Disable debug logging.

        Mirrors the behaviour of `async_turn_on` by updating both the persistent
        config entry options and the in‑memory domain flag.
        """
        new_options = {**self.entry.options, "debug_logging": False}
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

        # Immediate in-memory flag
        self.hass.data.setdefault(DOMAIN, {})["debug_enabled"] = False

        self.async_write_ha_state()
