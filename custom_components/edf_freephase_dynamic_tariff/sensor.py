from __future__ import annotations
#---DO NOT INSERT ANYTHING BEFORE THIS LINE---

from datetime import timedelta

from .coordinator import EDFCoordinator
from .sensors import ALL_SENSORS

async def async_setup_entry(hass, entry, async_add_entities):
    tariff_code = entry.data["tariff_code"]
    api_url = (
        f"https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"
        f"electricity-tariffs/{tariff_code}/standard-unit-rates/"
    )
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    coordinator = EDFCoordinator(hass, api_url, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for sensor in ALL_SENSORS:
        if callable(sensor) and sensor.__name__ == "create_next_phase_sensors":
            entities.extend(sensor(coordinator))
        else:
            entities.append(sensor(coordinator))
    
    async_add_entities(entities)