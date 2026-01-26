"""
Event entity exports for the EDF FreePhase Dynamic Tariff integration.

This package groups all event‑related entity classes used by the integration.
It currently exposes a single event entity,
`EDFFreePhaseDynamicSlotEventEntity`, which emits structured slot and phase
transition events derived from the coordinator’s tariff data.

The `__all__` definition ensures that platform modules can import the event
entity cleanly via:

    from .events import EDFFreePhaseDynamicSlotEventEntity

Additional event entity types may be added here in the future as the
integration evolves.
"""

from .slot_events import EDFFreePhaseDynamicSlotEventEntity

__all__ = ["EDFFreePhaseDynamicSlotEventEntity"]
