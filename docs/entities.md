# EDF FreePhase Dynamic — Entities Documentation (v0.4.0)

This document describes all entities exposed by the **EDF FreePhase Dynamic Tariff** integration as of v0.4.0.

A future release (v0.5.x) will introduce a simplified naming scheme.

---

# Overview

The integration exposes sensors that provide:

- the current tariff slot and phase  
- next slot information for each phase  
- block summaries (current and next)  
- cheapest and most expensive slots  
- yesterday/tomorrow phase summaries  
- forecast window information  
- internal/debug sensors  

All price‑based sensors use **p/kWh** as the native unit.  
All timestamps are ISO 8601.

---

# Sensor Entities

Below is the authoritative list of all sensors created by the integration.

---

# Detailed Sensors

These sensors expose structured attributes and are typically used in dashboards and automations.

---

## Current Price  
**Entity ID:** `sensor.current_price`  
**Unit:** `p/kWh`

Shows the **current half‑hour slot price**.

### Attributes

| Attribute | Description |
|----------|-------------|
| start | Slot start time |
| end | Slot end time |
| duration_minutes | Duration of the slot |
| price_pen_per_kwh | Price formatted in p/kWh |
| price_pou_per_kwh | Price formatted in £/kWh |
| icon | Phase icon |

### Example State  
33.55

---

## Current Block Summary  
**Entity ID:** `sensor.current_block_summary`  
**Unit:** `p/kWh`

Shows the **average price of the current phase block** (all consecutive slots of the same phase).

### Attributes  
- phase  
- start  
- end  
- duration_minutes  
- price fields  
- icon  

---

## Next Block Summary  
**Entity ID:** `sensor.next_block_summary`  
**Unit:** `p/kWh`

Shows the **average price of the next phase block** (of a different colour).

### Attributes  
Same as above.

---

## Next Slot Price  
**Entity ID:** `sensor.edf_freephase_dynamic_next_slot_price`  
**Unit:** `p/kWh`

Shows the **price of the next half‑hour slot**, regardless of phase.

### Attributes  
- start  
- end  
- duration_minutes  
- price fields  
- icon  

---

## Next Green Slot  
**Entity ID:** `sensor.edf_freephase_dynamic_next_green_slot`  
**Unit:** `p/kWh`

Shows the **price of the next green slot**.

### Attributes  
Full block details via `format_phase_block`.

---

## Next Amber Slot  
**Entity ID:** `sensor.edf_freephase_dynamic_next_amber_slot`  
**Unit:** `p/kWh`

Shows the **price of the next amber slot**.

---

## Next Red Slot  
**Entity ID:** `sensor.edf_freephase_dynamic_next_red_slot`  
**Unit:** `p/kWh`

Shows the **price of the next red slot**.

---

## Cheapest Slot (Next 24 Hours)  
**Entity ID:** `sensor.edf_freephase_dynamic_cheapest_slot_next_24_hours`  
**Unit:** `p/kWh`

Shows the **price of the cheapest slot** in the next 24 hours.

### Attributes  
- start  
- end  
- duration_minutes  
- price fields  
- icon  

---

## Most Expensive Slot (Next 24 Hours)  
**Entity ID:** `sensor.edf_freephase_dynamic_most_expensive_slot_next_24_hours`  
**Unit:** `p/kWh`

Shows the **price of the most expensive slot** in the next 24 hours.

---

## Yesterday Phases Summary  
**Entity ID:** `sensor.yesterday_phases_summary`

Shows the **number of phase windows** yesterday.

### Attributes  
`phase_1`, `phase_2`, … each containing:

- phase  
- start  
- end  
- duration_minutes  
- price fields  
- icon  

---

## Today’s Rates Summary  
**Entity ID:** `sensor.today_s_rates_summary`

Shows the **number of phase windows** today.

### Attributes  
Same structure as yesterday’s summary.

---

## Tomorrow’s Rates Summary  
**Entity ID:** `sensor.tomorrow_s_rates_summary`

Shows the **number of phase windows** tomorrow.

### Attributes  
Same structure as yesterday’s summary.

---

# Forecast & API Sensors

These sensors provide metadata about the EDF API and forecast window.

---

## 24‑Hour Forecast  
**Entity ID:** `sensor.24_hour_forecast`

Contains the **full 48‑slot forecast** as attributes.

### Attributes  
- forecast: list of slot dictionaries  

---

## Next Refresh Time  
**Entity ID:** `sensor.next_refresh_time`

Shows when the integration will next refresh data from EDF.

---

## Last Updated  
**Entity ID:** `sensor.last_updated`

Shows the timestamp of the last successful data update.

---

## API Latency  
**Entity ID:** `sensor.api_latency`  
**Unit:** milliseconds

Shows the **round‑trip latency** of the EDF API request.

---

# Internal / Debug Sensors

These sensors are primarily for troubleshooting.

---

## Coordinator Status  
**Entity ID:** `sensor.coordinator_status`

Shows the internal state of the update coordinator.

---

## Is Now a Green Slot  
**Entity ID:** `sensor.edf_freephase_dynamic_is_now_a_green_slot`

Boolean‑style sensor indicating whether the **current slot is green**.

---

## Current Slot Colour  
**Entity ID:** `sensor.edf_freephase_dynamic_current_slot_colour`

Shows the **current phase colour** (`green`, `amber`, `red`).

---

## Metadata Sensors (New in v0.5.0)

The coordinator now exposes cleaned tariff metadata retrieved from the EDF product endpoint.

This metadata is available in diagnostics and may be used by future sensors.

---

# EDF FreePhase Dynamic — Entities Documentation (v0.5.0)

This version introduces tariff metadata exposure and expanded diagnostics.
All existing entity IDs remain unchanged.

New coordinator fields now available to sensors and diagnostics:

- tariff_metadata
- tariff_region_label
- product_url
- api_url

---

# Notes

- All price sensors use **p/kWh**.  
- Negative prices represent “free” slots; there is no separate `free` phase.  
- Phase windows are derived from consecutive slots with the same phase.  
- Entities update at slot boundaries and when new data is fetched.