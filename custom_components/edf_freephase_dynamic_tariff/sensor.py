from __future__ import annotations
import aiohttp
import async_timeout
import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
DOMAIN = "edf_freephase_dynamic_tariff"

from datetime import datetime, time
import dateutil.parser

#HELPER: Slot classification
def classify_slot(start_time, price):
    """Return green/amber/red classification for a slot."""

    # Parse ISO timestamp from EDF API
    dt = dateutil.parser.isoparse(start_time)
    t = dt.time()

    # Free electricity override (negative wholesale)
    if price <= 0:
        return "green"

    # Daily schedule
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
    
    #Entities list
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
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(self.api_url)
                data = await resp.json()
    
                results = data["results"]
    
                # --- Determine the correct current price ---
                from datetime import datetime, timezone
                import dateutil.parser
                
                # --- Determine the correct current slot ---
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
                
                # --- Determine the correct current price ---
                if current_slot:
                    current_price = current_slot["value"]
                else:
                    # Fallback to EDF's own "current" price (first item)
                    current_price = results[0]["value_inc_vat"]
                
                # --- Fallback current_slot if forecast doesn't include the current time ---
                if not current_slot:
                    current_slot = {
                        "start": None,
                        "end": None,
                        "value": current_price,
                        "phase": classify_slot(results[0]["valid_from"], results[0]["value_inc_vat"]),
                    }

                # Next slot price (first future slot)
                next_price = None
                for item in results:
                    start = dateutil.parser.isoparse(item["valid_from"])
                    if start > now:
                        next_price = item["value_inc_vat"]
                        break
    
                # Build the next 24 hours forecast (48 half‑hour slots)
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

                return {
                    "current_price": current_price,
                    "next_price": next_price,
                    "next_24_hours": next_24_hours,
                    "current_slot": current_slot,
                }

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

#EDF FreePhase Dynamic Current Price Sensor
class EDFFreePhaseDynamicCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Current Price"
        self._attr_unique_id = "edf_freephase_dynamic_current_price"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:currency-gbp"

    @property
    def native_value(self):
        return self.coordinator.data.get("current_price")

    @property
    def extra_state_attributes(self):
        return {
            "forecast": self.coordinator.data.get("next_24_hours")
        }
    
    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }

#EDF FreePhase Dynamic Next Slot Price Sensor
class EDFFreePhaseDynamicNextSlotPriceSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Next Slot Price"
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

#EDF FreePhase Dynamic Next 24-hours of Slots Price Sensor
class EDFFreePhaseDynamic24HourForecastSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic 24‑Hour Tariff Forecast"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_forecast"
        self._attr_icon = "mdi:chart-line"

    @property
    def native_value(self):
        # sensors must return a string, number, or boolean
        return len(self.coordinator.data.get("next_24_hours", []))

    @property
    def extra_state_attributes(self):
        return {
            "forecast": self.coordinator.data.get("next_24_hours")
        }
    
    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }

#EDF FreePhase Dynamic Cheapest Sensor
class EDFFreePhaseDynamicCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Cheapest Slot (Next 24 Hours)"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_cheapest_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-down-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        cheapest = min(slots, key=lambda x: x["value"])
        return cheapest["value"]

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }
    
    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        cheapest = min(slots, key=lambda x: x["value"])
        return {
            "start": cheapest["start"],
            "end": cheapest["end"],
            "value": cheapest["value"],
            "phase": cheapest["phase"],
        }

#EDF FreePhase Dynamic Most Expensive Sensor
class EDFFreePhaseDynamicMostExpensiveSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Most Expensive Slot (Next 24 Hours)"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_most_expensive_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:arrow-up-bold"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return None
        expensive = max(slots, key=lambda x: x["value"])
        return expensive["value"]

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        if not slots:
            return {}
        expensive = max(slots, key=lambda x: x["value"])
        return {
            "start": expensive["start"],
            "end": expensive["end"],
            "value": expensive["value"],
            "phase": expensive["phase"],
        }

#Next Dynamic Green Slot Sensor
class EDFFreePhaseDynamicNextGreenSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Next Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_green_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:leaf"

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "green":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "green":
                return slot
        return {}

#Next Dynamic Amber Slot Sensor
class EDFFreePhaseDynamicNextAmberSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Next Amber Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_amber_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "amber":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
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

#Next Dynamic Red Slot Sensor
class EDFFreePhaseDynamicNextRedSlotSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Next Red Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_next_red_slot"
        self._attr_native_unit_of_measurement = "GBP"
        self._attr_icon = "mdi:alert"

    @property
    def native_value(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
            if slot["phase"] == "red":
                return slot["value"]
        return None

    @property
    def extra_state_attributes(self):
        slots = self.coordinator.data.get("next_24_hours", [])
        for slot in slots:
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

#Current Dynamic Slot Colour
class EDFFreePhaseDynamicCurrentSlotColourSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Current Slot Colour"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_current_slot_colour"
        self._attr_icon = "mdi:circle-slice-3"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        # Re‑classify the current slot using your helper
        current = data.get("current_slot")
        return current["phase"] if current else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}

        current = data.get("current_slot")
        return current or {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }

#Binary sensor which shows if the current clot is a Green slot
class EDFFreePhaseDynamicIsGreenSlotBinarySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "EDF FreePhase Dynamic Is Now a Green Slot"
        self._attr_unique_id = "edf_freephase_dynamic_tariff_is_green_slot"
        self._attr_icon = "mdi:leaf-circle"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        current = data.get("current_slot")
        return current["phase"] == "green" if current else None

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}

        current = data.get("current_slot")
        return current or {}

    @property
    def device_info(self):
        return {
            "identifiers": {("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")},
            "name": "EDF FreePhase Dynamic Tariff",
            "manufacturer": "EDF",
            "model": "FreePhase Dynamic Tariff API",
            "entry_type": "service",
        }
