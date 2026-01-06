from __future__ import annotations

#Import: Forecast sensors
from .forecast import (
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
)

#Import: Meta data sensors
from .meta import (
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
)

#Import: Price sensors
from .price import (
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
)

#Import: Rates sensors
from .rates import (
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
)

#Import: Slots sensors
from .slots import (
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicNextGreenSlotSensor,
    EDFFreePhaseDynamicNextAmberSlotSensor,
    EDFFreePhaseDynamicNextRedSlotSensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
)


ALL_SENSORS = [
    # Forecast sensors
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,

    # Meta sensors
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,

    # Price sensors
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,

    # Rates sensors
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,

    # Slot sensors
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicNextGreenSlotSensor,
    EDFFreePhaseDynamicNextAmberSlotSensor,
    EDFFreePhaseDynamicNextRedSlotSensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
]