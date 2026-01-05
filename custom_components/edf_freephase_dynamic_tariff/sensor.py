from __future__ import annotations
#---DO NOT INSERT ANYTHING BEFORE THIS LINE---

from datetime import timedelta

from .coordinator import EDFCoordinator
from .sensors import ALL_SENSORS
from .const import (
    DEFAULT_API_TIMEOUT,
    DEFAULT_RETRY_ATTEMPTS,
)


async def async_setup_entry(hass, entry, async_add_entities):
    tariff_code = entry.data["tariff_code"]

    api_url = (
        "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"
        f"electricity-tariffs/{tariff_code}/standard-unit-rates/"
    )

    # Existing behaviour: scan_interval is stored in minutes in the config entry
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    # New: timeout and retry settings, with safe defaults
    api_timeout = entry.data.get("api_timeout", DEFAULT_API_TIMEOUT)
    retry_attempts = entry.data.get("retry_attempts", DEFAULT_RETRY_ATTEMPTS)

    coordinator = EDFCoordinator(
        hass=hass,
        api_url=api_url,
        scan_interval=scan_interval,
        api_timeout=api_timeout,
        retry_attempts=retry_attempts,
    )
    await coordinator.async_config_entry_first_refresh()

    entities = [sensor_class(coordinator) for sensor_class in ALL_SENSORS]
    async_add_entities(entities)