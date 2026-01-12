# EDF FreePhase Dynamic — Entities Documentation

> **Planned:** _To be implemented in v0.3.8._

## Overview

The EDF FreePhase Dynamic integration exposes a set of sensors that provide real‑time and forecasted tariff information. These entities allow dashboards, automations, and scripts to react to:

- the current tariff slot  
- the current phase  
- the upcoming phase window  
- the full 48‑slot forecast  
- summary statistics (cheapest, most expensive, free slots)

All entities are updated whenever new tariff data is fetched from EDF or when the current slot boundary is reached.

---

# Sensor Entities

## 1. `sensor.edf_fpd_current_price`

### Description
Shows the **current half‑hour slot price** for the EDF FreePhase Dynamic tariff.

### Attributes

| Attribute | Type   | Description                          |
|-----------|--------|--------------------------------------|
| unit      | string | Price unit (e.g., `p/kWh`)           |
| slot_start | datetime | Start time of the current slot     |
| slot_end   | datetime | End time of the current slot       |
| slot_index | integer | Index of the slot (0–47)           |

### Example State
`33.55`

---

## 2. `sensor.edf_fpd_current_phase`

### Description
Shows the **current phase** derived from the current slot price.

Possible values:

- `green`
- `amber`
- `red`
- `free`

### Attributes

| Attribute | Type     | Description                              |
|-----------|----------|------------------------------------------|
| phase_start | datetime | Start of the current phase window       |
| phase_end   | datetime | End of the current phase window         |
| phase_duration | string | Total duration of the phase window     |
| slot_index | integer | Index of the current slot                |

### Example State
`amber`

---

## 3. `sensor.edf_fpd_next_phase`

### Description
Shows the **next upcoming phase**, based on the forecast.

### Attributes

| Attribute | Type     | Description                              |
|-----------|----------|------------------------------------------|
| next_phase_start | datetime | When the next phase begins         |
| next_phase_end   | datetime | When the next phase ends           |
| next_phase_duration | string | Duration of the next phase        |

### Example State
`green`

---

## 4. `sensor.edf_fpd_cheapest_slot`

### Description
Shows the **start time of the cheapest slot** in the current 48‑slot forecast.

### Attributes

| Attribute | Type   | Description                          |
|-----------|--------|--------------------------------------|
| price     | float  | Price of the cheapest slot           |
| unit      | string | Price unit (e.g., `p/kWh`)           |

### Example State
`2026-01-13T03:00:00+00:00`

---

## 5. `sensor.edf_fpd_most_expensive_slot`

### Description
Shows the **start time of the most expensive slot** in the forecast.

### Attributes

| Attribute | Type   | Description                              |
|-----------|--------|------------------------------------------|
| price     | float  | Price of the most expensive slot         |
| unit      | string | Price unit                               |

### Example State
`2026-01-13T17:00:00+00:00`

---

## 6. `sensor.edf_fpd_free_slots`

### Description
Shows the **number of free (negative‑price) slots** in the forecast.

### Example State
`0`

---

## 7. `sensor.edf_fpd_forecast_window`

### Description
Shows the **start and end timestamps** of the current EDF forecast window.

### Attributes

| Attribute      | Type     | Description                              |
|----------------|----------|------------------------------------------|
| effective_from | datetime | Start of the forecast window (23:00 D)   |
| effective_to   | datetime | End of the forecast window (23:00 D+1)   |
| slots          | integer  | Number of slots (always 48)              |

### Example State
`2026-01-12T23:00:00+00:00 → 2026-01-13T23:00:00+00:00`

---

# Internal / Debug Entities

These entities are optional but useful for troubleshooting and advanced dashboards.

## 8. `sensor.edf_fpd_slot_index`

### Description
Shows the **current slot index** (0–47).

### Example State
`32`

---

## 9. `sensor.edf_fpd_raw_forecast`

### Description
Contains the **full 48‑slot forecast** as a JSON attribute.

### Attributes

| Attribute | Type  | Description                          |
|-----------|-------|--------------------------------------|
| forecast  | list  | List of 48 slot objects              |

### Example State
`48 slots`

---

# Notes

- All timestamps are in ISO 8601 format.  
- All price values use the unit provided by EDF (typically `p/kWh`).  
- Entities update at slot boundaries and when new data is fetched.  
- Phase windows are derived from consecutive slots with the same phase classification.