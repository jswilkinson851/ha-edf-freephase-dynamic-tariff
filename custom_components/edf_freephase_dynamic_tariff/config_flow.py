import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import selector

from .const import DOMAIN

PRODUCT_URL = (
    "https://api.edfgb-kraken.energy/v1/products/"
    "EDF_FREEPHASE_DYNAMIC_12M_HH/"
)

# ---------------------------------------------------------------------------
# Fallback DNO Region Table (used if API fails)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Fetch region list from EDF API
# ---------------------------------------------------------------------------
async def fetch_regions(hass: HomeAssistant):
    """Fetch tariff regions from EDF API. Returns dict of label → tariff_code."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                resp = await session.get(PRODUCT_URL)
                data = await resp.json()

        tariffs_section = data.get("single_register_electricity_tariffs", {})
        if not tariffs_section:
            raise ValueError("No tariffs in API response")

        regions = {}
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

    except Exception:
        return FALLBACK_REGIONS.copy()


# ---------------------------------------------------------------------------
# Config Flow
# ---------------------------------------------------------------------------
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            selected_label = user_input["tariff_code"]
            tariff_code = self._regions[selected_label]

            return self.async_create_entry(
                title=f"EDF FreePhase Dynamic Tariff ({selected_label})",
                data={
                    "tariff_code": tariff_code,
                    "scan_interval": user_input["scan_interval"],
                    "import_sensor": user_input.get("import_sensor"),
                },
            )

        # Fetch region list
        self._regions = await fetch_regions(self.hass)
        region_labels = sorted(self._regions.keys())  # A1-a alphabetical

        data_schema = vol.Schema({
            vol.Required("tariff_code"): selector({
                "select": {
                    "options": region_labels
                }
            }),

            vol.Required("scan_interval", default=30): selector({
                "number": {
                    "min": 1,
                    "max": 120,
                    "step": 1
                }
            }),

            vol.Optional("import_sensor"): selector({
                "entity": {
                    "domain": "sensor"
                }
            }),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


# ---------------------------------------------------------------------------
# Options Flow
# ---------------------------------------------------------------------------
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for existing config entry."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        regions = await fetch_regions(self.hass)
        region_labels = sorted(regions.keys())  # A1-a alphabetical

        current_tariff_code = self._config_entry.data.get("tariff_code")
        current_region_label = None

        for label, code in regions.items():
            if code == current_tariff_code:
                current_region_label = label
                break

        if current_region_label is None:
            current_region_label = region_labels[0]

        current_scan = self._config_entry.data.get("scan_interval", 30)
        current_import_sensor = self._config_entry.data.get("import_sensor")

        if user_input is not None:
            selected_label = user_input["tariff_code"]
            tariff_code = regions[selected_label]

            new_data = {
                **self._config_entry.data,
                "tariff_code": tariff_code,
                "scan_interval": user_input["scan_interval"],
                "import_sensor": user_input.get("import_sensor"),
            }

            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        data_schema = vol.Schema({
            vol.Required("tariff_code", default=current_region_label): selector({
                "select": {
                    "options": region_labels
                }
            }),

            vol.Required("scan_interval", default=current_scan): selector({
                "number": {
                    "min": 1,
                    "max": 120,
                    "step": 1
                }
            }),

            vol.Optional("import_sensor", default=current_import_sensor): selector({
                "entity": {
                    "domain": "sensor"
                }
            }),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )