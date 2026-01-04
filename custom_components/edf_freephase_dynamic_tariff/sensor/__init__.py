from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from ..coordinator import EDFCoordinator
from ..const import DOMAIN
from .current_price import (
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
)
from .forecast import (
    EDFFreePhaseDynamicForecastListSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
)
from .slots import (
    EDFFreePhaseDynamicNextGreenSlotSensor,
    EDFFreePhaseDynamicNextAmberSlotSensor,
    EDFFreePhaseDynamicNextRedSlotSensor,
)
from .slot_colours import (
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
)
from .diagnostics import (
    EDFFreePhaseAPILastCheckedSensor,
    EDFFreePhaseLastUpdatedSensor,
    EDFFreePhaseAPILatencySensor,
)
from .timeseries import EDFFreePhaseDynamicCurrentPriceTimeseriesSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EDF FreePhase Dynamic tariff sensors from a config entry."""
    tariff_code = entry.data["tariff_code"]

    default_api_url = (
        "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"
        f"electricity-tariffs/{tariff_code}/standard-unit-rates/"
    )

    api_url = entry.options.get("api_url", default_api_url)

    scan_interval = timedelta(
        minutes=entry.options.get(
            "scan_interval",
            entry.data["scan_interval"],
        )
    )

    forecast_hours = entry.options.get(
        "forecast_hours",
        entry.data.get("forecast_hours", 24),
    )

    include_past_slots = entry.options.get(
        "include_past_slots",
        entry.data.get("include_past_slots", False),
    )

    timeout = entry.options.get(
        "timeout",
        entry.data.get("timeout", 10),
    )

    retry_attempts = entry.options.get(
        "retry_attempts",
        entry.data.get("retry_attempts", 0),
    )

    coordinator = EDFCoordinator(
        hass,
        api_url,
        scan_interval,
        forecast_hours,
        include_past_slots,
        timeout,
        retry_attempts,
    )

    await coordinator.async_config_entry_first_refresh()

    entities: list[Any] = [
        EDFFreePhaseDynamicCurrentPriceSensor(coordinator),
        EDFFreePhaseDynamicNextSlotPriceSensor(coordinator),
        EDFFreePhaseDynamicCheapestSlotSensor(coordinator),
        EDFFreePhaseDynamicMostExpensiveSlotSensor(coordinator),
        EDFFreePhaseDynamicNextGreenSlotSensor(coordinator),
        EDFFreePhaseDynamicNextAmberSlotSensor(coordinator),
        EDFFreePhaseDynamicNextRedSlotSensor(coordinator),
        EDFFreePhaseDynamicCurrentSlotColourSensor(coordinator),
        EDFFreePhaseDynamicIsGreenSlotBinarySensor(coordinator),
        EDFFreePhaseAPILastCheckedSensor(coordinator),
        EDFFreePhaseLastUpdatedSensor(coordinator),
        EDFFreePhaseAPILatencySensor(coordinator),
        EDFFreePhaseDynamicForecastListSensor(coordinator),
        EDFFreePhaseDynamicCurrentPriceTimeseriesSensor(coordinator),
    ]

    async_add_entities(entities)