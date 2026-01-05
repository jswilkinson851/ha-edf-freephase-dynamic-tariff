from __future__ import annotations

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_TARIFF_CODE,
    CONF_SCAN_INTERVAL,
    CONF_FORECAST_WINDOW,
    CONF_INCLUDE_PAST_SLOTS,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_FORECAST_WINDOW,
    DEFAULT_INCLUDE_PAST_SLOTS,
)

API_URL = "https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/"

# Static region name mapping (Ofgem DNO regions)
REGION_NAME_MAP = {
    "A": "Eastern England",
    "B": "East Midlands",
    "C": "London",
    "D": "Merseyside & North Wales",
    "E": "West Midlands",
    "F": "North East England",
    "G": "North West England",
    "H": "Southern England",
    "J": "South Eastern England",
    "K": "South Wales",
    "L": "South Western England",
    "M": "Yorkshire",
    "N": "Southern Scotland",
    "P": "Northern Scotland",
}

# Default prefix (used only if API returns nothing)
DEFAULT_PREFIX = "E-1R-EDF_FREEPHASE_DYNAMIC_12M_HH"


async def fetch_tariff_codes() -> list[str]:
    """Fetch tariff codes dynamically from the Kraken API."""
    try:
        async with aiohttp.ClientSession() as session:
            with async_timeout.timeout(10):
                async with session.get(
                    API_URL,
                    headers={"User-Agent": "HomeAssistant-EDF-Integration"},
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()

        tariffs = data.get("single_register_electricity_tariffs", [])
        return [t.get("code") for t in tariffs if t.get("code")]

    except Exception:
        return []


def build_fallback_codes(prefix: str) -> list[str]:
    """Generate a full fallback list using the detected or default prefix."""
    return [f"{prefix}-{letter}" for letter in REGION_NAME_MAP.keys()]


def build_dropdown_labels(codes: list[str]) -> dict[str, str]:
    """
    Build a mapping of:
        "Region A: Eastern England" → "actual tariff code"
    """
    result = {}

    for code in codes:
        region_letter = code[-1]
        region_name = REGION_NAME_MAP.get(region_letter, f"Region {region_letter}")
        label = f"Region {region_letter}: {region_name}"
        result[label] = code

    return result


class EDFFreePhaseDynamicConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for the EDF FreePhase Dynamic Tariff integration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Initial setup step."""
        errors = {}

        # Fetch tariff codes dynamically
        tariff_codes = await fetch_tariff_codes()

        # Detect prefix if API returned anything
        if tariff_codes:
            prefix = tariff_codes[0].rsplit("-", 1)[0]
        else:
            prefix = DEFAULT_PREFIX

        # Build fallback list if API failed
        if not tariff_codes:
            tariff_codes = build_fallback_codes(prefix)

        dropdown_map = build_dropdown_labels(tariff_codes)
        dropdown_labels = list(dropdown_map.keys())

        if user_input is not None:
            selected_label = user_input.get(CONF_TARIFF_CODE)
            tariff_code = dropdown_map.get(selected_label)

            scan_interval_minutes = user_input.get(CONF_SCAN_INTERVAL)
            forecast_window = user_input.get(CONF_FORECAST_WINDOW)
            include_past_slots = user_input.get(CONF_INCLUDE_PAST_SLOTS)

            if not tariff_code:
                errors[CONF_TARIFF_CODE] = "required"

            if not errors:
                scan_interval_seconds = scan_interval_minutes * 60

                return self.async_create_entry(
                    title="EDF FreePhase Dynamic Tariff",
                    data={
                        CONF_TARIFF_CODE: tariff_code,
                        CONF_SCAN_INTERVAL: scan_interval_seconds,
                        CONF_FORECAST_WINDOW: forecast_window,
                        CONF_INCLUDE_PAST_SLOTS: include_past_slots,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TARIFF_CODE,
                    default=dropdown_labels[0],
                ): vol.In(dropdown_labels),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL_SECONDS // 60,
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    CONF_FORECAST_WINDOW,
                    default=DEFAULT_FORECAST_WINDOW,
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    CONF_INCLUDE_PAST_SLOTS,
                    default=DEFAULT_INCLUDE_PAST_SLOTS,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors = {}

        tariff_codes = await fetch_tariff_codes()

        if tariff_codes:
            prefix = tariff_codes[0].rsplit("-", 1)[0]
        else:
            prefix = DEFAULT_PREFIX

        if not tariff_codes:
            tariff_codes = build_fallback_codes(prefix)

        dropdown_map = build_dropdown_labels(tariff_codes)
        dropdown_labels = list(dropdown_map.keys())

        stored_code = entry.data.get(CONF_TARIFF_CODE)
        stored_label = next(
            (label for label, code in dropdown_map.items() if code == stored_code),
            dropdown_labels[0],
        )

        if user_input is not None:
            selected_label = user_input.get(CONF_TARIFF_CODE)
            tariff_code = dropdown_map.get(selected_label)

            scan_interval_minutes = user_input.get(CONF_SCAN_INTERVAL)
            forecast_window = user_input.get(CONF_FORECAST_WINDOW)
            include_past_slots = user_input.get(CONF_INCLUDE_PAST_SLOTS)

            if not tariff_code:
                errors[CONF_TARIFF_CODE] = "required"

            if not errors:
                scan_interval_seconds = scan_interval_minutes * 60

                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        CONF_TARIFF_CODE: tariff_code,
                        CONF_SCAN_INTERVAL: scan_interval_seconds,
                        CONF_FORECAST_WINDOW: forecast_window,
                        CONF_INCLUDE_PAST_SLOTS: include_past_slots,
                    },
                )
                return self.async_abort(reason="reconfigure_successful")

        current_scan_minutes = entry.data.get(CONF_SCAN_INTERVAL, 300) // 60

        schema = vol.Schema(
            {
                vol.Required(CONF_TARIFF_CODE, default=stored_label): vol.In(dropdown_labels),
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan_minutes): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Required(
                    CONF_FORECAST_WINDOW,
                    default=entry.data.get(CONF_FORECAST_WINDOW, DEFAULT_FORECAST_WINDOW),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    CONF_INCLUDE_PAST_SLOTS,
                    default=entry.data.get(CONF_INCLUDE_PAST_SLOTS, DEFAULT_INCLUDE_PAST_SLOTS),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )