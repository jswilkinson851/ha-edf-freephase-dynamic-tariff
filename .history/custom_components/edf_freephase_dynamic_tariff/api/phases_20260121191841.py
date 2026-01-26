"""
Phase summary utilities for EDF FreePhase Dynamic Tariff integration.

This module encapsulates logic for determining the current and next
phase windows, keeping the coordinator focused on orchestration.
"""

from __future__ import annotations

from ..helpers import (
    find_current_block,
    group_phase_blocks,
    format_phase_block,
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
