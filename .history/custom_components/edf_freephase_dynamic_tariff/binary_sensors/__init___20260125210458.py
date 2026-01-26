"""
Binary sensor entity exports for the EDF FreePhase Dynamic Tariff integration.

This package groups all binary‑sensor entity classes used by the integration.
Binary sensors expose simple boolean conditions derived from the coordinator’s
tariff data, such as whether the current slot is classified as “green”.

The `__all__` definition ensures that platform modules can import binary sensor
classes cleanly via:

    from .binary_sensors import EDFFreePhaseDynamicIsGreenSlotBinarySensor

Additional binary sensor types may be added here in the future as the
integration evolves and new boolean conditions become useful for automations.
"""

# Required so Python treats this directory as a package
