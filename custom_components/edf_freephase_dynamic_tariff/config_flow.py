import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

PRODUCT_URL = "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"

async def fetch_tariffs(hass):
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(PRODUCT_URL)
                data = await resp.json()

        tariffs_section = data.get("single_register_electricity_tariffs", {})

        regions = {}

        for item in tariffs_section.values():
            ddm = item.get("direct_debit_monthly")
            if ddm and "code" in ddm:
                code = ddm["code"]
                region_letter = code.split("-")[-1]
                regions[f"Region {region_letter}"] = code

        return regions

    except Exception:
        raise HomeAssistantError("cannot_connect")


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            selected_region = user_input["tariff_code"]
            tariff_code = self._regions[selected_region]

            return self.async_create_entry(
                title=f"EDF FreePhase Dynamic Tariff ({selected_region})",
                data={
                    "tariff_code": tariff_code,
                    "scan_interval": user_input["scan_interval"],
                },
            )

        try:
            regions = await fetch_tariffs(self.hass)
        except HomeAssistantError:
            errors["base"] = "cannot_connect"
            regions = {}

        region_names = list(regions.keys())
        self._regions = regions

        data_schema = vol.Schema({
            vol.Required("tariff_code", description="Region"): vol.In(region_names),
            vol.Required("scan_interval", default=30): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )