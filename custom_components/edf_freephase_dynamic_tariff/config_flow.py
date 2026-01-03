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

        # New correct location for tariffs
        tariffs_section = data.get("single_register_electricity_tariffs", {})

        tariff_codes = []

        for item in tariffs_section.values():
            ddm = item.get("direct_debit_monthly")
            if ddm and "code" in ddm:
                tariff_codes.append(ddm["code"])

        return tariff_codes

    except Exception:
        raise HomeAssistantError("cannot_connect")

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the EDF Dynamic Tariff integration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # User submitted the form — create the entry
            return self.async_create_entry(
                title=f"EDF FreePhase Dynamic Tariff ({user_input['tariff_code']})",
                data=user_input,
            )

        # Fetch tariff list for dropdown
        try:
            tariff_codes = await fetch_tariffs(self.hass)
        except HomeAssistantError:
            errors["base"] = "cannot_connect"
            tariff_codes = []

        # Build the form schema dynamically
        data_schema = vol.Schema({
            vol.Required("tariff_code", description="Relevant Tariff Code"): vol.In(tariff_codes),
            vol.Required("scan_interval", default=30): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )