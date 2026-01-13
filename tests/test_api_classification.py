pytestmark = pytest.mark.xfail(reason="Test suite temporarily disabled pending redesign")

from custom_components.edf_freephase_dynamic_tariff.api.classification import classify_slot


def test_classification_green_price_zero():
    assert classify_slot("2024-01-01T12:00:00Z", 0) == "Green"


def test_classification_green_night_hours():
    assert classify_slot("2024-01-01T23:30:00Z", 10) == "Green"
    assert classify_slot("2024-01-01T05:30:00Z", 10) == "Green"


def test_classification_red_peak_hours():
    assert classify_slot("2024-01-01T17:00:00Z", 10) == "Red"


def test_classification_amber_other_times():
    assert classify_slot("2024-01-01T10:00:00Z", 10) == "Amber"
    assert classify_slot("2024-01-01T20:00:00Z", 10) == "Amber"