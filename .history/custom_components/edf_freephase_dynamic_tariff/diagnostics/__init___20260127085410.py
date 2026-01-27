"""
Diagnostics package for EDF FreePhase Dynamic Tariff.

This package exposes helper utilities used by diagnostic sensors and
event‑emitting entities. Currently includes:

    - EventDiagnostics: centralised diagnostics store for event entities
"""

from .events import EventDiagnostics

__all__ = ["EventDiagnostics"]
