"""
Config flow for the EDF FreePhase Dynamic Tariff integration.

This module implements the full user-facing configuration workflow for the
integration, including both the initial setup flow and the options flow used
to adjust settings after installation.

The flow performs several key responsibilities:

1. Region and tariff discovery
   The integration attempts to fetch the latest region → tariff_code mapping
   from EDF’s public product metadata endpoint. If the API is unavailable or
   returns incomplete data, a built‑in fallback mapping is used so the user
   can still complete setup. Region labels are presented to the user via a
   selector, and the chosen label is resolved to a tariff code when the entry
   is created.

2. Import sensor validation (soft validation)
   Users may optionally provide an import sensor (e.g., whole‑home electricity
   consumption). The flow performs a medium‑strict validation step that checks
   whether the sensor is suitable for tariff‑aware calculations. If validation
   fails, the user is redirected to a confirmation step that explains the
   issues and allows them to continue anyway. This avoids blocking setup while
   still providing clear guidance.

3. Scan interval configuration
   The user selects how frequently the coordinator should refresh EDF’s API.
   This value is stored in the config entry and used by the DataUpdateCoordinator
   to schedule periodic updates.

4. Options flow
   The OptionsFlowHandler mirrors the main flow, allowing users to adjust the
   tariff region, scan interval, import sensor, and debug logging flag after
   installation. Import sensor validation is repeated here using the same
   confirmation pattern as the initial flow.

5. Robustness and user experience
   The flow is designed to be resilient to EDF API outages, malformed metadata,
   and user‑provided sensors that may not meet expectations. All validation
   failures are surfaced clearly, but the user retains control over whether to
   proceed.

This file is responsible only for user interaction and config entry creation.
All runtime behaviour (API polling, tariff parsing, slot/phase logic, event
generation, diagnostics, etc.) is handled by the coordinator and platform
entities.
"""


from __future__ import annotations

# pylint: disable=import-error
import aiohttp  # pyright: ignore[reportMissingImports] 
import async_timeout  # pyright: ignore[reportMissingImports]
import voluptuous as vol  # pyright: ignore[reportMissingImports]

from homeassistant import config_entries  # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant  # pyright: ignore[reportMissingImports]
from homeassistant.helpers.selector import selector  # pyright: ignore[reportMissingImports]
# pylint: enable=import-error

from .const import DOMAIN
from .helpers import get_product_base_url, validate_import_sensor  # pylint: disable=no-name-in-module

# Canonical product metadata endpoint
PRODUCT_URL = get_product_base_url()

# Fallback region → tariff_code mapping (same as v0.5.0)
FALLBACK_REGIONS = {
    "Region A – Eastern England": "EDF_FREEPHASE_DYNAMIC_12M_HH-A",
    "Region B – East Midlands": "EDF_FREEPHASE_DYNAMIC_12M_HH-B",
    "Region C – London": "EDF_FREEPHASE_DYNAMIC_12M_HH-C",
    "Region D – Merseyside & North Wales": "EDF_FREEPHASE_DYNAMIC_12M_HH-D",
    "Region E – West Midlands": "EDF_FREEPHASE_DYNAMIC_12M_HH-E",
    "Region F – North East England": "EDF_FREEPHASE_DYNAMIC_12M_HH-F",
    "Region G – North West England": "EDF_FREEPHASE_DYNAMIC_12M_HH-G",
    "Region H – Southern England": "EDF_FREEPHASE_DYNAMIC_12M_HH-H",
    "Region J – South Eastern England": "EDF_FREEPHASE_DYNAMIC_12M_HH-J",
    "Region K – South Wales": "EDF_FREEPHASE_DYNAMIC_12M_HH-K",
    "Region L – South Western England": "EDF_FREEPHASE_DYNAMIC_12M_HH-L",
    "Region M – Yorkshire": "EDF_FREEPHASE_DYNAMIC_12M_HH-M",
    "Region N – Southern Scotland": "EDF_FREEPHASE_DYNAMIC_12M_HH-N",
    "Region P – Northern Scotland": "EDF_FREEPHASE_DYNAMIC_12M_HH-P",
}


async def validate_product_url(hass: HomeAssistant) -> bool:
    """Validate that PRODUCT_URL is reachable and returns JSON."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(PRODUCT_URL)
                if resp.status != 200:
                    return False
                await resp.json()
                return True
    except Exception:
        return False


async def fetch_regions(hass: HomeAssistant):
    """Fetch region → tariff_code mapping from the product metadata endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(PRODUCT_URL)
                data = await resp.json()
                tariffs_section = data.get("single_register_electricity_tariffs", {})
                if not tariffs_section:
                    raise ValueError("No tariffs in API response")
                regions: dict[str, str] = {}
                for item in tariffs_section.values():
                    ddm = item.get("direct_debit_monthly")
                    if ddm and "code" in ddm:
                        code = ddm["code"]
                        region_letter = code.split("-")[-1]
                        for label, fallback_code in FALLBACK_REGIONS.items():
                            if fallback_code.endswith(region_letter):
                                regions[label] = code
                                break
                if not regions:
                    raise ValueError("API returned no usable region codes")
                return regions
    except Exception:  # pylint: disable=broad-except
        # Fallback if API fails
        return FALLBACK_REGIONS.copy()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc]
    """Handle a config flow for EDF FreePhase Dynamic Tariff."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user selects region, scan interval and optional import sensor."""  # pylint: disable=line-too-long
        errors: dict[str, str] = {}

        # Fetch region list for the form
        self._regions = await fetch_regions(self.hass)
        region_labels = sorted(self._regions.keys())

        if user_input is not None:
            # If an import sensor was provided, validate it (soft validation)
            import_sensor = user_input.get("import_sensor")
            if import_sensor:
                ok, reasons = await validate_import_sensor(self.hass, import_sensor)
                if not ok:
                    # Redirect to confirmation step with reasons so the user can choose to continue
                    return await self.async_step_confirm_import_sensor({"user_input": user_input, "reasons": reasons})  # pylint: disable=line-too-long

            # If validation passed or no import sensor provided, create the entry
            selected_label = user_input["tariff_code"]
            tariff_code = self._regions[selected_label]
            return self.async_create_entry(
                title=f"EDF FreePhase Dynamic Tariff ({selected_label})",
                data={
                    "tariff_code": tariff_code,
                    "tariff_region_label": selected_label,
                    "scan_interval": user_input["scan_interval"],
                    "import_sensor": user_input.get("import_sensor"),
                    "product_url": PRODUCT_URL,
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required("tariff_code"): selector({"select": {"options": region_labels}}),
                vol.Required("scan_interval", default=30): selector({"number": {"min": 1, "max": 120, "step": 1}}),  # pylint: disable=line-too-long
                vol.Optional("import_sensor"): selector({"entity": {"domain": "sensor"}}),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_confirm_import_sensor(self, data):
        """
        Confirmation step shown when the selected import sensor fails validation.

        The user can either continue anyway or go back and choose another sensor.
        """
        user_input = data.get("user_input", {})
        reasons = data.get("reasons", [])
        import_sensor = user_input.get("import_sensor")

        # If the user confirmed, create the entry regardless of validation warnings
        if user_input and user_input.get("confirm_import_sensor"):
            selected_label = user_input["tariff_code"]
            tariff_code = self._regions[selected_label]
            return self.async_create_entry(
                title=f"EDF FreePhase Dynamic Tariff ({selected_label})",
                data={
                    "tariff_code": tariff_code,
                    "tariff_region_label": selected_label,
                    "scan_interval": user_input["scan_interval"],
                    "import_sensor": import_sensor,
                    "product_url": PRODUCT_URL,
                },
            )

        # Build a human readable reasons string for the form description
        reason_text = "\n".join(f"• {r}" for r in reasons) if reasons else "Unknown issue."

        data_schema = vol.Schema(
            {
                vol.Required("confirm_import_sensor", default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="confirm_import_sensor",
            data_schema=data_schema,
            description_placeholders={"entity_id": import_sensor or "", "reasons": reason_text},
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow handler for this integration."""
        return OptionsFlowHandler(config_entry)


# ---------------------------------------------------------------------------
# Options flow is implemented in OptionsFlowHandler below
# ---------------------------------------------------------------------------
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for EDF FreePhase Dynamic Tariff."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Show the options form and validate import sensor if provided."""
        errors: dict[str, str] = {}

        regions = await fetch_regions(self.hass)
        region_labels = sorted(regions.keys())

        current_tariff_code = self._config_entry.data.get("tariff_code")
        current_region_label = None
        for label, code in regions.items():
            if code == current_tariff_code:
                current_region_label = label
                break

        current_scan = self._config_entry.data.get("scan_interval", 30)
        current_import_sensor = self._config_entry.data.get("import_sensor")
        stored_region_label = self._config_entry.data.get("tariff_region_label")
        if stored_region_label:
            current_region_label = stored_region_label
        elif current_region_label is None:
            current_region_label = region_labels[0]

        if user_input is not None:
            import_sensor = user_input.get("import_sensor")
            if import_sensor:
                ok, reasons = await validate_import_sensor(self.hass, import_sensor)
                if not ok:
                    # Redirect to confirmation step in options flow
                    return await self.async_step_confirm_import_sensor({"user_input": user_input, "reasons": reasons})  # pylint: disable=line-too-long

            # Apply changes
            selected_label = user_input["tariff_code"]
            tariff_code = regions[selected_label]
            new_data = {
                **self._config_entry.data,
                "tariff_code": tariff_code,
                "tariff_region_label": selected_label,
                "scan_interval": user_input["scan_interval"],
                "import_sensor": user_input.get("import_sensor"),
                "product_url": PRODUCT_URL,
            }
            self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)

            # This ensures: `entry.data` holds the core config & `entry.options` holds the debug flag
            # if you do NOT put `debug_logging` into `new_data`
            return self.async_create_entry(
                title="",
                data={"debug_logging": user_input.get("debug_logging", False)},
            )

        # Build the options form
        data_schema = vol.Schema(
            {
                vol.Required("tariff_code", default=current_region_label): selector(
                    {"select": {"options": region_labels}}
                ),
                vol.Required("scan_interval", default=current_scan): selector(
                    {"number": {"min": 1, "max": 120, "step": 1}}
                ),
                vol.Optional("import_sensor", default=current_import_sensor): selector(
                    {"entity": {"domain": "sensor"}}
                ),
                vol.Optional(
                    "debug_logging",
                    default=self._config_entry.options.get("debug_logging", False),
                ): selector({"boolean": {}}),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)

    async def async_step_confirm_import_sensor(self, data):
        """Confirmation step for options flow when import sensor validation fails."""
        user_input = data.get("user_input", {})
        reasons = data.get("reasons", [])
        import_sensor = user_input.get("import_sensor")

        if user_input and user_input.get("confirm_import_sensor"):
            # Apply changes even though validation warned
            regions = await fetch_regions(self.hass)
            selected_label = user_input["tariff_code"]
            tariff_code = regions[selected_label]
            new_data = {
                **self._config_entry.data,
                "tariff_code": tariff_code,
                "tariff_region_label": selected_label,
                "scan_interval": user_input["scan_interval"],
                "import_sensor": import_sensor,
                "product_url": PRODUCT_URL,
            }
            self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)

            # Ensures the debug flag is preserved even when the user confirms a failing sensor
            return self.async_create_entry(
                title="",
                data={"debug_logging": user_input.get("debug_logging", False)},
            )

        reason_text = "\n".join(f"• {r}" for r in reasons) if reasons else "Unknown issue."

        data_schema = vol.Schema({vol.Required("confirm_import_sensor", default=False): bool})

        return self.async_show_form(
            step_id="confirm_import_sensor",
            data_schema=data_schema,
            description_placeholders={"entity_id": import_sensor or "", "reasons": reason_text},
        )
