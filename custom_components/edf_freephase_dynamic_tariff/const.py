DOMAIN = "edf_freephase_dynamic_tariff"

# Config entry keys
CONF_TARIFF_CODE = "tariff_code"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FORECAST_WINDOW = "forecast_window"
CONF_INCLUDE_PAST_SLOTS = "include_past_slots"

# Options-only keys (for options_flow.py later)
CONF_CUSTOM_API_URL = "custom_api_url"
CONF_API_TIMEOUT = "api_timeout"
CONF_RETRY_ATTEMPTS = "retry_attempts"

# Defaults
DEFAULT_SCAN_INTERVAL_SECONDS = 300  # 5 minutes
DEFAULT_FORECAST_WINDOW = 24
DEFAULT_INCLUDE_PAST_SLOTS = True
DEFAULT_API_TIMEOUT = 10
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_CUSTOM_API_URL = None