from .meta import (
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicLastSuccessfulUpdateSensor,
    EDFFreePhaseDynamicDataAgeSensor,
)

from .forecast import (
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
)

from .price import (
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
)

from .slots import (
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicNextGreenSlotSensor,
    EDFFreePhaseDynamicNextAmberSlotSensor,
    EDFFreePhaseDynamicNextRedSlotSensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,
)

from .rates import (
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
)

ALL_SENSORS = [
    # Meta sensors
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicLastSuccessfulUpdateSensor,
    EDFFreePhaseDynamicDataAgeSensor,

    # Forecast sensors
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,

    # Price sensors
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,

    # Slot sensors
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    EDFFreePhaseDynamicNextGreenSlotSensor,
    EDFFreePhaseDynamicNextAmberSlotSensor,
    EDFFreePhaseDynamicNextRedSlotSensor,
    EDFFreePhaseDynamicIsGreenSlotBinarySensor,

    # Rates sensors
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
]