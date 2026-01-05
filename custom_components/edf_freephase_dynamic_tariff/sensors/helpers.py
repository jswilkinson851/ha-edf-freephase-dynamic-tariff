"""
Helpers used by the various sensors for the EDF FreePhase Dynamic Tariff integration.
"""

#Helper: Device info dictionary
def edf_device_info():
    return {
        "identifiers": {
            ("edf_freephase_dynamic_tariff_integration", "edf_freephase_dynamic_tariff_device")
        },
        "name": "EDF FreePhase Dynamic Tariff",
        "manufacturer": "EDF",
        "model": "FreePhase Dynamic Tariff API",
        "entry_type": "service",
    }