"""
EDF FreePhase Dynamic Tariff – Home Assistant Integration

This module implements the integration's lifecycle and orchestrates all
top‑level setup, teardown, and coordinator management for the
EDF FreePhase Dynamic Tariff custom component.

Overview
--------
Home Assistant loads this module when the integration is installed or a
config entry is created. Its responsibilities include:

• Creating and initialising the two coordinators used by the integration:
  - EDFCoordinator: Handles communication with EDF’s product and pricing API.
  - CostCoordinator: Computes cost‑based values using import sensor data and
    the EDFCoordinator’s tariff information.

• Performing the first refresh for both coordinators so that entities receive
  initial data immediately after setup.

• Registering a device in the Home Assistant device registry so that all
  sensors and binary sensors attach cleanly to a single logical device.

• Forwarding the config entry to supported platforms (sensor, binary_sensor),
  allowing them to create entities bound to the coordinators.

• Managing integration lifecycle events:
  - async_setup: Present for completeness; YAML setup is not used.
  - async_setup_entry: Main entry point for config‑entry‑based setup.
  - async_unload_entry: Ensures coordinators shut down cleanly and platforms
    unload correctly.
  - _async_update_listener: Reloads the integration when options change.

Stored Data Structure
---------------------
During setup, the integration stores all runtime objects under:

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": EDFCoordinator,
        "cost_coordinator": CostCoordinator,
        "tariff_code": str,
        "product_url": str,
        "api_url": str,
        "tariff_region_label": Optional[str],
        "version": str (from manifest.json),
    }

This allows platforms and services to access coordinators and metadata
without re‑creating or re‑fetching them.

Coordinator Lifecycle
---------------------
Both coordinators follow Home Assistant’s DataUpdateCoordinator pattern.
This module ensures:

• First refresh is awaited before platforms load.
• Coordinators are shut down gracefully during unload.
• Errors during refresh or shutdown are logged but do not prevent the
  integration from loading or unloading.

Device Registration
-------------------
A single device is created in the device registry using the config entry ID
as its unique identifier. All entities created by the integration attach to
this device, ensuring a clean and predictable device/entity structure.

Platform Forwarding
-------------------
Supported platforms are forwarded via:

    hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])

This ensures entities are created only after coordinators are ready and
metadata is stored.

In summary, this module provides the integration’s high‑level orchestration:
coordinator creation, device registration, platform setup, lifecycle
management, and safe teardown.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers.typing import ConfigType  # pyright: ignore[reportMissingImports] # pylint: disable=import-error
from homeassistant.helpers import device_registry as dr  # pyright: ignore[reportMissingImports] # pylint: disable=import-error

from .const import DOMAIN
from .coordinator import EDFCoordinator
from .cost_coordinator import CostCoordinator
from .helpers import build_edf_urls

_LOGGER = logging.getLogger(__name__)

startup_logger = logging.getLogger("homeassistant.core")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up EDF FreePhase Dynamic Tariff Integration from YAML (not used)."""
    _ = hass, config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EDF FreePhase Dynamic Tariff from a config entry."""

    # Ensure options exist
    if not entry.options:
        hass.config_entries.async_update_entry(entry, options={"debug_logging": False})

    # Store debug flag in hass.data for convenience
    hass.data.setdefault(DOMAIN, {})

    # Enable structured debug logging if option is set
    hass.data[DOMAIN]["debug_enabled"] = entry.options.get("debug_logging", False)

    # Build URLs using helper
    urls = build_edf_urls(entry.data["tariff_code"])
    product_url = urls["product_url"]
    api_url = urls["api_url"]

    # Build scan interval
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    # Create EDF coordinator and attach config entry
    coordinator = EDFCoordinator(hass, product_url, api_url, scan_interval)
    coordinator.config_entry = entry
    startup_logger.info("EDF INT. EC | Coordinator created, preparing first refresh")
    coordinator.entry = entry

    # Create CostCoordinator (do not refresh yet)
    import_sensor = entry.data.get("import_sensor")
    cost_coordinator = CostCoordinator(
        hass=hass,
        edf_coordinator=coordinator,
        import_sensor_entity_id=import_sensor,
        scan_interval=scan_interval,
    )
    cost_coordinator.config_entry = entry
    cost_coordinator.entry = entry  # <-- OPTIONAL, but consistent

    # ---------------------------------------------------------------
    # NEW: Load manifest version (correct integration version)
    # ---------------------------------------------------------------
    from homeassistant.loader import (  # pylance: ignore[reportMissingImports] # type: ignore # pylint: disable=import-error disable=import-outside-toplevel
        async_get_integration,
    )

    integration = await async_get_integration(hass, DOMAIN)
    manifest_version = integration.manifest.get("version")

    # Store coordinators + metadata BEFORE any refresh or platform forwarding
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "cost_coordinator": cost_coordinator,
        "tariff_code": entry.data["tariff_code"],
        "product_url": product_url,
        "api_url": api_url,
        "tariff_region_label": entry.data.get("tariff_region_label"),
        "version": manifest_version,
    }

    async def _update_listener(hass, entry):
        """Handle options updates."""
        # Mirror the updated option into hass.data (optional but harmless)
        hass.data[DOMAIN]["debug_enabled"] = entry.options.get("debug_logging", False)

        # Ensure coordinators see the updated config entry
        data = hass.data[DOMAIN].get(entry.entry_id)
        if data:
            coordinator = data.get("coordinator")
            cost_coordinator = data.get("cost_coordinator")

            if coordinator:
                coordinator.config_entry = entry
            if cost_coordinator:
                cost_coordinator.config_entry = entry

    entry.async_on_unload(entry.add_update_listener(_update_listener))

    # ------------------------------------------------------------------
    # Register the device BEFORE forwarding platforms
    # Ensures all sensors attach to this device cleanly
    # ------------------------------------------------------------------
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="EDF",
        name="EDF FreePhase Dynamic Tariff",
        model="FreePhase Dynamic",
    )

    startup_logger.info("EDF INT. EC | Starting first refresh (main thread)")

    # --------------------------------------------------------------
    # Immediate first refresh for EDFCoordinator (guaranteed)
    # Ensures debug logs appear immediately after restart
    # --------------------------------------------------------------
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("EDFCoordinator: immediate first refresh completed")
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("EDFCoordinator: immediate refresh failed: %s", err)

    startup_logger.info("EDF INT. CC | Starting first cost refresh (main thread)")

    # --------------------------------------------------------------
    # Immediate first refresh for CostCoordinator
    # Must run AFTER EDFCoordinator so tariff data exists
    # --------------------------------------------------------------
    try:
        await cost_coordinator.async_refresh()
        cost_coordinator.async_update_listeners()
        _LOGGER.debug("CostCoordinator: immediate first refresh completed")
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.exception("CostCoordinator: immediate refresh failed: %s", err)

    # Forward to sensor, binary_sensor (entities attach to coordinators here) and
    # switch platforms (for debug logging switch)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "switch"])  # pylint: disable=line-too-long

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id, {})

    # Shut down the cost coordinator first (if present)
    cost_coordinator = data.get("cost_coordinator")
    if cost_coordinator:
        try:
            await cost_coordinator.async_shutdown()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("CostCoordinator: shutdown failed: %s", err)

    # Shut down the EDF coordinator (if present)
    edf_coordinator = data.get("coordinator")
    if edf_coordinator:
        try:
            await edf_coordinator.async_shutdown()
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("EDFCoordinator: shutdown failed: %s", err)

    # Unload the sensor, binary_sensor and switch platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "switch"])  # pylint: disable=line-too-long

    # Remove stored data
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
