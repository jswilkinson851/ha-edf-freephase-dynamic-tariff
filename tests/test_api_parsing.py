from datetime import datetime, timezone, timedelta

from custom_components.edf_freephase_dynamic_tariff.api.parsing import (
    build_unified_dataset,
    strip_internal,
    build_forecasts,
)


def test_build_unified_dataset_sorts_and_parses():
    raw = [
        {
            "valid_from": "2024-01-01T01:00:00Z",
            "valid_to": "2024-01-01T01:30:00Z",
            "value_inc_vat": 10,
        },
        {
            "valid_from": "2024-01-01T00:30:00Z",
            "valid_to": "2024-01-01T01:00:00Z",
            "value_inc_vat": 5,
        },
    ]

    unified = build_unified_dataset(raw)

    assert unified[0]["value"] == 5
    assert unified[1]["value"] == 10
    assert "_start_dt_obj" in unified[0]


def test_strip_internal_removes_private_fields():
    raw = [
        {
            "start": "x",
            "end": "y",
            "_start_dt_obj": 123,
            "_end_dt_obj": 456,
        }
    ]

    cleaned = strip_internal(raw)
    assert "_start_dt_obj" not in cleaned[0]
    assert "_end_dt_obj" not in cleaned[0]


def test_build_forecasts_next_24_hours():
    now = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    unified = []
    for i in range(48):
        start = now + timedelta(minutes=30 * i)
        end = start + timedelta(minutes=30)
        unified.append(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "value": i,
                "phase": "Green",
                "currency": "GBP",
                "_start_dt_obj": start,
                "_end_dt_obj": end,
            }
        )

    forecasts = build_forecasts(unified, now)
    assert len(forecasts["next_24_hours"]) == 48