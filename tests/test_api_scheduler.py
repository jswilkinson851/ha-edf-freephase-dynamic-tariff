import pytest
from datetime import datetime, timedelta, timezone

from custom_components.edf_freephase_dynamic_tariff.api.scheduler import AlignedScheduler


@pytest.mark.asyncio
async def test_scheduler_initial_boundary(hass):
    scheduler = AlignedScheduler(hass, timedelta(seconds=30))

    scheduler._initialise_boundary()
    assert scheduler._next_boundary_utc is not None
    assert scheduler._next_boundary_utc.tzinfo == timezone.utc


def test_scheduler_advances_boundary(hass):
    scheduler = AlignedScheduler(hass, timedelta(seconds=30))

    # Force a boundary in the past
    scheduler._next_boundary_utc = datetime.now(timezone.utc) - timedelta(seconds=10)

    scheduler._advance_boundary()
    assert scheduler._next_boundary_utc > datetime.now(timezone.utc)


def test_scheduler_delay_includes_jitter(hass):
    scheduler = AlignedScheduler(hass, timedelta(seconds=30))

    delay = scheduler._compute_delay()
    assert delay > 0
    assert scheduler.next_refresh_jitter >= 0
    assert scheduler.next_refresh_jitter <= 5
    assert scheduler.next_refresh_datetime is not None
