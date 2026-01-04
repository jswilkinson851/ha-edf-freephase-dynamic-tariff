from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class EDFConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            tariff_code = user_input.get("tariff_code")

            if not tariff_code or not isinstance(tariff_code, str):
                errors["tariff_code"] = "invalid_tariff"
            else:
                return self.async_create_entry(
                    title=f"EDF FreePhase Dynamic Tariff ({tariff_code})",
                    data={
                        "tariff_code": tariff_code,
                        "scan_interval": 30,
                        "forecast_hours": 24
                    },
                )

        schema = vol.Schema({
            vol.Required("tariff_code"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_import(self, user_input=None) -> FlowResult:
        """Support YAML import (not used, but required)."""
        return await self.async_step_user(user_input)


class EDFOptionsFlow(config_entries.OptionsFlow):
    """Handle options for the integration."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry = self.config_entry

        schema = vol.Schema({
            vol.Optional(
                "api_url",
                default=entry.options.get("api_url", "")
            ): str,

            vol.Optional(
                "scan_interval",
                default=entry.options.get("scan_interval", entry.data["scan_interval"])
            ): int,

            vol.Optional(
                "forecast_hours",
                default=entry.options.get("forecast_hours", entry.data.get("forecast_hours", 24))
            ): int,

            vol.Optional(
                "include_past_slots",
                default=entry.options.get("include_past_slots", False)
            ): bool,

            vol.Optional(
                "timeout",
                default=entry.options.get("timeout", 10)
            ): int,

            vol.Optional(
                "retry_attempts",
                default=entry.options.get("retry_attempts", 0)
            ): int,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )


async def async_get_options_flow(config_entry):
    return EDFOptionsFlow(config_entry)