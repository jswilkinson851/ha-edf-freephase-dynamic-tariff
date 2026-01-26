"""
Sensor registry for the EDF FreePhase Dynamic Tariff integration.

This module exposes ALL_SENSORS, a flat list of sensor classes and
factory functions used by sensor.py to instantiate entities.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cost + consumption summary sensors <-- Added in v0.6.0
# ---------------------------------------------------------------------------
from .cost_summary import (  # pylint: disable=no-name-in-module disable=wrong-import-position # noqa: E402
    EDFFreePhaseDynamicTodayConsumptionPhaseSensor,
    EDFFreePhaseDynamicTodayCostPhaseSensor,
    EDFFreePhaseDynamicTodayCostSlotsSensor,
    EDFFreePhaseDynamicYesterdayConsumptionPhaseSensor,
    EDFFreePhaseDynamicYesterdayCostPhaseSensor,
    EDFFreePhaseDynamicYesterdayCostSlotsSensor,
)

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
    EDFFreePhaseDynamicAPILatencySensor,
    EDFFreePhaseDynamicCoordinatorStatusSensor,
    EDFFreePhaseDynamicCostCoordinatorStatusSensor,  # Added in v0.6.0
    EDFFreePhaseDynamicLastUpdatedSensor,
    EDFFreePhaseDynamicNextRefreshSensor,
    EDFFreePhaseDynamicTariffDiagnosticSensor,  # Added in v0.6.0
    EDFFreePhaseDynamicTariffMetadataSensor,  # Added in v0.4.3
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
    EDFFreePhaseDynamicCurrentBlockSummarySensor,
    EDFFreePhaseDynamicCurrentSlotColourSensor,
    EDFFreePhaseDynamicNextBlockSummarySensor,
    create_next_phase_sensors,
)
from .standing_charge import EDFFreePhaseDynamicStandingChargeSensor

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
    # Standing charges sensor <-- Added in v0.6.1
    EDFFreePhaseDynamicStandingChargeSensor,
]

# ---------------------------------------------------------------------------
# End of file
# ---------------------------------------------------------------------------
