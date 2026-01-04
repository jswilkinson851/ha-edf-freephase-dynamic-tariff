from __future__ import annotations
import aiohttp
import async_timeout
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "edf_freephase_dynamic_tariff"

from datetime import datetime, time, timezone
import dateutil.parser
from time import monotonic

#HELPER: Slot classification
def classify_slot(start_time, price):
    dt = dateutil.parser.isoparse(start_time)
    t = dt.time()

    if price <= 0:
        return "green"

    if time(23, 0) <= t or t < time(6, 0):
        return "green"
    if time(6, 0) <= t < time(16, 0):
        return "amber"
    if time(16, 0) <= t < time(19, 0):
        return "red"
    if time(19, 0) <= t < time(23, 0):
        return "amber"

    return "amber"


async def async_setup_entry(hass, entry, async_add_entities):
    tariff_code = entry.data["tariff_code"]
    api_url = (
        f"https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"
        f"electricity-tariffs/{tariff_code}/standard-unit-rates/"
    )
    scan_interval = timedelta(minutes=entry.data["scan_interval"])

    coordinator = EDFCoordinator(hass, api_url, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        EDFFreePhaseDynamicCurrentPriceSensor(coordinator),
        EDFFreePhaseDynamicNextSlotPriceSensor(coordinator),
        EDFFreePhaseDynamic24HourForecastSensor(coordinator),
        EDFFreePhaseDynamicCheapestSlotSensor(coordinator),
        EDFFreePhaseDynamicMostExpensiveSlotSensor(coordinator),
        EDFFreePhaseDynamicNextGreenSlotSensor(coordinator),
        EDFFreePhaseDynamicNextAmberSlotSensor(coordinator),
        EDFFreePhaseDynamicNextRedSlotSensor(coordinator),
        EDFFreePhaseDynamicCurrentSlotColourSensor(coordinator),
        EDFFreePhaseDynamicIsGreenSlotBinarySensor(coordinator),
        EDFFreePhaseDynamicLastUpdatedSensor(coordinator),
        EDFFreePhaseDynamicAPILatencySensor(coordinator),
    ])


#EDF FreePhase Dynamic Coordinator
class EDFCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url, scan_interval):
        self.api_url = api_url
        super().__init__(
            hass,
            _LOGGER,
            name="EDF FreePhase Dynamic Tariff Integration",
            update_interval=scan_interval,
        )

    async def _async_update_data(self):
        start_time = monotonic()

        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(self.api_url)
                data = await resp.json()

        api_latency = monotonic() - start_time

        results = data["results"]
        now = datetime.now(timezone.utc)

        current_slot = None
        for item in results:
            start = dateutil.parser.isoparse(item["valid_from"])
            end = dateutil.parser.isoparse(item["valid_to"])
            if start <= now < end:
                current_slot = {
                    "start": item["valid_from"],
                    "end": item["valid_to"],
                    "value": item["value_inc_vat"],
                    "phase": classify_slot(item["valid_from"], item["value_inc_vat"]),
                }
                break

        if current_slot:
            current_price = current_slot["value"]
        else:
            current_price = results[0]["value_inc_vat"]

        if not current_slot:
            current_slot = {
                "start": None,
                "end": None,
                "value": current_price,
                "phase": classify_slot(results[0]["valid_from"], results[0]["value_inc_vat"]),
            }

        next_price = None
        for item in results:
            start = dateutil.parser.isoparse(item["valid_from"])
            if start > now:
                next_price = item["value_inc_vat"]
                break

        next_24_hours = []
        for item in results[:48]:
            start = item["valid_from"]
            end = item["valid_to"]
            value = item["value_inc_vat"]
            phase = classify_slot(start, value)

            next_24_hours.append({
                "start": start,
                "end": end,
                "value": value,
                "phase": phase,
            })

        last_updated = datetime.now(timezone.utc).isoformat()

        return {
            "current_price": current_price,
            "next_price": next_price,
            "next_24_hours": next_24_hours,
            "current_slot": current_slot,
            "api_latency": api_latency,
            "last_updated": last_updated,
        }


from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


# Current Price
class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_current_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:currency-gbp"

    @property
    def native_value(self):
        return self.coordinator.data.get("current_price")

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Next Slot Price
class EDFFreePhaseDynamicNextSlotPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Slot Price"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_slot_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        return self.coordinator.data.get("next_price")

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# 24‑Hour Forecast
class EDFFreePhaseDynamic24HourForecastSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "24‑Hour Forecast"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_forecast"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        return len(self.coordinator.data.get("next_24_hours", []))

    @property
    def extra_state_attributes(self):
        return {"forecast": self.coordinator.data.get("next_24_hours")}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Cheapest Slot
class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Cheapest Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-down-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        return min(slots, key=lambda x: x["value"])["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        cheapest = min(slots, key=lambda x: x["value"])
        return cheapest

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Most Expensive Slot
class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Most Expensive Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-up-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        return max(slots, key=lambda x: x["value"])["value"]

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        return max(slots, key=lambda x: x["value"])

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Next Green Slot
class EDFFreePhaseDynamicNextGreenSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_green_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:leaf"

    @property
    def native_value(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "green":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "green":
                return slot
        return {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Next Amber Slot
class EDFFreePhaseDynamicNextAmberSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Amber Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_amber_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "amber":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "amber":
                return slot
        return {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Next Red Slot
class EDFFreePhaseDynamicNextRedSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Next Red Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_red_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "red":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        for slot in self.coordinator.data.get("next_24_hours", []):
            if slot["phase"] == "red":
                return slot
        return {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Current Slot Colour
class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"
        self._attr_icon = "mdi:circle-slice-3"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] if current else None

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("current_slot") or {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Is Green Slot (Binary)
class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Is Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self):
        current = self.coordinator.data.get("current_slot")
        return current["phase"] == "green" if current else None

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("current_slot") or {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# Last Updated Sensor
class EDFFreePhaseDynamicLastUpdatedSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Last Updated"
        self._attr_unique_id = "edf_freephase_dynamic_last_updated"
        self._attr_icon = "mdi:update"

    @property
    def native_value(self):
        ts = self.coordinator.data.get("last_updated")
        if not ts:
            return None
    
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%H:%M on %d/%m/%Y")

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }


# API Latency Sensor
class EDFFreePhaseDynamicAPILatencySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "API Latency"
        self._attr_unique_id = "edf_freephase_dynamic_api_latency"
        self._attr_native_unit_of_measurement = "s"
        self._attr_icon = "mdi:timer-sand"

    @property
    def native_value(self):
        return round(self.coordinator.data.get("api_latency", 0), 3)

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }