"""
Constants for the EDF FreePhase Dynamic Tariff integration.

This module centralises all top‑level identifiers used across the integration.
Keeping these values in a dedicated file ensures consistency between the
config flow, coordinator, platforms, diagnostics, and event entities.

DOMAIN:
    The canonical integration domain used by Home Assistant for:
    - config entry registration
    - platform forwarding (sensor, binary_sensor, switch, event)
    - storage under hass.data
    - logging namespaces
    - device and entity identifiers

Additional constants (API endpoints, attribute keys, default values, etc.)
should be added here as the integration evolves to keep configuration and
runtime modules clean and maintainable.
"""

DOMAIN = "edf_freephase_dynamic_tariff"

# End of constants.py
