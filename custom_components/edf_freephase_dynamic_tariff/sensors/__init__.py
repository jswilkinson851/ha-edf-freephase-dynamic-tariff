from .meta import (
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicLastSuccessfulUpdateSensor,
    EDFFreePhaseDynamicDataAgeSensor,
)

from .price import (
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
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
    EDFFreePhaseDynamicTodaysRatesFullSensor,
    EDFFreePhaseDynamicTomorrowsRatesFullSensor,
)

ALL_SENSORS = [
    # Meta sensors
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicLastSuccessfulUpdateSensor,
    EDFFreePhaseDynamicDataAgeSensor,

    # Price sensors
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,

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
    EDFFreePhaseDynamicTodaysRatesFullSensor,
    EDFFreePhaseDynamicTomorrowsRatesFullSensor,
]