"""
Sensor registry for the EDF FreePhase Dynamic Tariff integration.

This module exposes ALL_SENSORS, a flat list of sensor classes and
factory functions used by sensor.py to instantiate entities.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Forecast sensors
# ---------------------------------------------------------------------------
from .forecast import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamic24HourForecastSensor,
    EDFFreePhaseDynamicCheapestSlotSensor,
    EDFFreePhaseDynamicMostExpensiveSlotSensor,
)

# ---------------------------------------------------------------------------
# Metadata sensors
# ---------------------------------------------------------------------------
from .meta import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicNextRefreshSensor,
    EDFFreePhaseDynamicTariffMetadataSensor,  # Added in v0.4.3
    EDFFreePhaseDynamicTariffDiagnosticSensor,  # Added in v0.6.0
    EDFFreePhaseDynamicCostCoordinatorStatusSensor,  # Added in v0.6.0
)

# ---------------------------------------------------------------------------
# Price sensors
# ---------------------------------------------------------------------------
from .price import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicCurrentPriceSensor,
    EDFFreePhaseDynamicNextSlotPriceSensor,
)

# ---------------------------------------------------------------------------
# Rates sensors
# ---------------------------------------------------------------------------
from .rates import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicTodaysRatesSummarySensor,
    EDFFreePhaseDynamicTomorrowsRatesSummarySensor,
    EDFFreePhaseDynamicYesterdayPhasesSummarySensor,
)

# ---------------------------------------------------------------------------
# Slot sensors
# ---------------------------------------------------------------------------
from .slots import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    create_next_phase_sensors,
)

# ---------------------------------------------------------------------------
# Cost + consumption summary sensors <-- Added in v0.6.0
# ---------------------------------------------------------------------------
from .cost_summary import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicYesterdayCostPhaseSensor,
    EDFFreePhaseDynamicTodayCostPhaseSensor,
    EDFFreePhaseDynamicYesterdayConsumptionPhaseSensor,
    EDFFreePhaseDynamicTodayConsumptionPhaseSensor,
    EDFFreePhaseDynamicYesterdayCostSlotsSensor,
    EDFFreePhaseDynamicTodayCostSlotsSensor,
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
    EDFFreePhaseDynamicTariffDiagnosticSensor,
    EDFFreePhaseDynamicCostCoordinatorStatusSensor,  # <-- Added in v0.6.0
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
    # Next-phase sensors (factory)
    create_next_phase_sensors,
    # Cost + consumption summary sensors  <-- Added in v0.6.0
    EDFFreePhaseDynamicYesterdayCostPhaseSensor,
    EDFFreePhaseDynamicTodayCostPhaseSensor,
    EDFFreePhaseDynamicYesterdayConsumptionPhaseSensor,
    EDFFreePhaseDynamicTodayConsumptionPhaseSensor,
    EDFFreePhaseDynamicYesterdayCostSlotsSensor,
    EDFFreePhaseDynamicTodayCostSlotsSensor,
]

# ---------------------------------------------------------------------------
# End of file
# ---------------------------------------------------------------------------
