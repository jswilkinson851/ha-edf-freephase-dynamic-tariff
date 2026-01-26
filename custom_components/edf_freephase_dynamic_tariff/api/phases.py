"""
Phase‑window computation utilities for the EDF FreePhase Dynamic Tariff integration.

This module provides the logic for deriving human‑readable phase‑window
summaries (Green/Amber/Red blocks) from the normalised slot dataset produced by
the parsing layer. By isolating this logic here, the coordinator remains focused
on orchestration and state management, while all phase‑window reasoning stays
centralised and easy to maintain.

A “phase window” represents a contiguous block of half‑hour slots that share the
same phase classification. These blocks are used throughout the integration to
summarise tariff behaviour, drive UI elements, and trigger event‑based
automations.

The module’s primary responsibility is:

    • compute_phase_summaries(all_slots, current_slot)
        Determines:
          - the phase window currently active at the given time
          - the next upcoming phase window, if any

        It does this by:
          - locating the current block via `find_current_block()`
          - grouping all slots into contiguous phase blocks using
            `group_phase_blocks()`
          - formatting the resulting blocks into compact, serialisable summaries
            via `format_phase_block()`

The returned summaries are used by the coordinator, sensors, event entities, and
diagnostics to present a consistent, high‑level view of the tariff’s current and
upcoming behaviour.
"""

from __future__ import annotations

from ..helpers import (
    find_current_block,
    format_phase_block,
    group_phase_blocks,
)


def compute_phase_summaries(all_slots: list[dict], current_slot: dict | None):
    """
    Compute formatted summaries for the current and next phase windows.

    Parameters:
        all_slots: A list of normalised slot dictionaries.
        current_slot: The slot representing the current time window.

    Returns:
        A tuple: (current_phase_summary, next_phase_summary)
    """

    if not all_slots or not current_slot:
        return None, None

    current_phase = find_current_block(all_slots, current_slot)
    if not current_phase:
        return None, None

    phases = group_phase_blocks(all_slots)

    next_phase = None
    try:
        idx = phases.index(current_phase)
        if idx + 1 < len(phases):
            next_phase = phases[idx + 1]
    except ValueError:
        next_phase = None

    return (
        format_phase_block(current_phase) if current_phase else None,
        format_phase_block(next_phase) if next_phase else None,
    )
