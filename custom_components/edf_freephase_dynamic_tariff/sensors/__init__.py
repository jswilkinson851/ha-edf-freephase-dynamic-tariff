from __future__ import annotations

"""
Sensor registry for the EDF FreePhase Dynamic Tariff integration.

This module exposes ALL_SENSORS, a flat list of sensor classes and
factory functions used by sensor.py to instantiate entities.
"""

# ---------------------------------------------------------------------------
# Forecast sensors
# ---------------------------------------------------------------------------
from .forecast import (
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
)

# ---------------------------------------------------------------------------
# Metadata sensors
# ---------------------------------------------------------------------------
from .meta import (
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicNextRefreshSensor,
    EDFFreePhaseDynamicTariffMetadataSensor,   # Added in v0.4.3
)

# ---------------------------------------------------------------------------
# Price sensors
# ---------------------------------------------------------------------------
from .price import (
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
)

# ---------------------------------------------------------------------------
# Rates sensors
# ---------------------------------------------------------------------------
from .rates import (
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
    EDFFreePhaseDynamicYesterdayPhasesSummarySensor,
)

# ---------------------------------------------------------------------------
# Slot sensors
# ---------------------------------------------------------------------------
from .slots import (
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
    create_next_phase_sensors,
)

# ---------------------------------------------------------------------------
# Exported sensor registry
# ---------------------------------------------------------------------------

ALL_SENSORS = [
    # Forecast sensors
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,

    # Metadata sensors
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicNextRefreshSensor,
    EDFFreePhaseDynamicTariffMetadataSensor,

    # Price sensors
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,

    # Rates sensors
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
    EDFFreePhaseDynamicYesterdayPhasesSummarySensor,

    # Slot sensors
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,

    # Next-phase sensors (factory)
    create_next_phase_sensors,
]