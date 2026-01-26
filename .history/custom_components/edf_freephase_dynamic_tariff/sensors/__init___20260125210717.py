"""
Sensor registry for the EDF FreePhase Dynamic Tariff integration.

This package aggregates all sensor entity classes and factory functions used by
the integration. The `ALL_SENSORS` list acts as the single source of truth for
the sensor platform (`sensor.py`), allowing it to instantiate every sensor
without needing to know their individual modules or constructor signatures.

The registry includes several categories of sensors:

1. Forecast sensors
   Provide forward‑looking information such as the next 24 hours of prices,
   cheapest/most expensive slots, and other predictive summaries.

2. Metadata sensors
   Expose coordinator status, API latency, tariff metadata, diagnostic
   information, and other integration‑level attributes.

3. Price sensors
   Report the current slot price and the upcoming slot price.

4. Rates sensors
   Summarise today’s, tomorrow’s, and yesterday’s rate structures.

5. Slot sensors
   Provide high‑level information about the current and next phase blocks,
   slot colours, and next‑phase transitions. Some of these are generated via
   factory functions (e.g., `create_next_phase_sensors`).

6. Cost and consumption summary sensors
   Added in later versions of the integration, these sensors expose aggregated
   cost and consumption data for today and yesterday.

7. Standing charge sensor
   Reports the daily standing charge and its validity window.

By centralising all sensor exports here, the integration keeps the sensor
platform simple, avoids circular imports, and ensures consistent ordering and
discoverability of all sensor types.
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
