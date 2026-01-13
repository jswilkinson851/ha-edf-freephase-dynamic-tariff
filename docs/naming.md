# EDF FreePhase Dynamic — Naming Conventions

> **Planned:** _To be implemented in a later version_

## Overview

This document defines the naming conventions used throughout the EDF FreePhase Dynamic integration.  
Consistent naming ensures:

- predictable entity IDs  
- clear and readable dashboards  
- intuitive automation references  
- maintainable code and documentation  

These conventions follow Home Assistant’s official guidelines and the patterns used by high‑quality core integrations.

---

# General Principles

1. **All entity IDs use the `edf_fpd_` prefix**  
   This keeps the namespace clean and avoids collisions with other integrations.

2. **Names are descriptive, not abbreviated**  
   Abbreviations are only used where they are unambiguous (`fpd`, `kWh`, etc.).

3. **Snake_case for entity IDs**  
   Example:  
   `sensor.edf_fpd_current_price`

4. **Human‑readable names for UI display**  
   Example:  
   `EDF FPD Current Price`

5. **Timestamps always use ISO 8601**  
   Example:  
   `2026-01-12T23:00:00+00:00`

6. **Units always follow EDF’s published format**  
   Typically `p/kWh`.

---

# Entity Naming

## Sensors

### Current Slot Sensors

| Entity ID                      | Friendly Name               | Description                                 |
|--------------------------------|------------------------------|---------------------------------------------|
| `sensor.edf_fpd_current_price`   | EDF FPD Current Price        | Current slot price                          |
| `sensor.edf_fpd_current_phase`   | EDF FPD Current Phase        | Current phase classification                |
| `sensor.edf_fpd_slot_index`      | EDF FPD Slot Index           | Current slot index (0–47)                   |

### Forecast Summary Sensors

| Entity ID                             | Friendly Name                     | Description                                   |
|---------------------------------------|-----------------------------------|-----------------------------------------------|
| `sensor.edf_fpd_cheapest_slot`          | EDF FPD Cheapest Slot             | Start time of cheapest slot                   |
| `sensor.edf_fpd_most_expensive_slot`    | EDF FPD Most Expensive Slot       | Start time of most expensive slot             |
| `sensor.edf_fpd_free_slots`             | EDF FPD Free Slots                | Number of negative‑price slots                |
| `sensor.edf_fpd_forecast_window`        | EDF FPD Forecast Window           | Start/end of the 48‑slot forecast             |

### Phase Window Sensors

| Entity ID                      | Friendly Name               | Description                                 |
|--------------------------------|------------------------------|---------------------------------------------|
| `sensor.edf_fpd_next_phase`      | EDF FPD Next Phase          | Next upcoming phase                         |

---

# Event Naming

Two events are exposed by the integration:

| Event Name                     | Description                                   |
|--------------------------------|-----------------------------------------------|
| `edf_fpd_phase_changed`          | Fires when the current phase changes          |
| `edf_fpd_new_forecast_available` | Fires when a new 48‑slot forecast is fetched  |

### Event Naming Rules

1. **Prefix all events with `edf_fpd_`**  
   Ensures uniqueness and clarity.

2. **Use past tense for state‑change events**  
   Example: `phase_changed`

3. **Use descriptive names for data‑availability events**  
   Example: `new_forecast_available`

4. **Avoid abbreviations inside event names**  
   Except the integration prefix.

---

# Attribute Naming

Attributes follow these conventions:

- **snake_case** for attribute keys  
- **ISO 8601** for timestamps  
- **HH:MM:SS** for durations  
- **lowercase strings** for phases (`green`, `amber`, `red`, `free`)  
- **float** for prices  
- **integer** for slot indices  

### Examples

| Attribute          | Example Value                         |
|--------------------|----------------------------------------|
| `slot_start`         | 2026-01-11T16:00:00+00:00              |
| `slot_duration`      | 00:30:00                               |
| `phase_duration`     | 03:00:00                               |
| `price`              | 33.55                                  |
| `unit`               | p/kWh                                  |
| `slot_index`         | 32                                     |

---

# File Naming

All integration files follow Home Assistant’s standard structure:

| File Name          | Purpose                                 |
|--------------------|-------------------------------------------|
| `__init__.py`      | Integration setup                        |
| `coordinator.py`   | Data update coordinator                  |
| `sensor.py`        | Sensor entity definitions                |
| `manifest.json`    | Integration metadata                     |
| `const.py`         | Constants (prefixes, defaults, phases)   |
| `events.py`        | Event dispatching logic (optional)       |
| `docs/*.md`        | Documentation                            |

---

# Prefix Reference

The integration uses the following prefixes consistently:

- **Integration prefix:** `edf_fpd_`
- **Sensor domain:** `sensor.edf_fpd_*`
- **Event prefix:** `edf_fpd_*`
- **Attribute prefix:** none (attributes use descriptive names)

---

# Summary

These naming conventions ensure:

- clarity for users  
- consistency across entities and events  
- predictable automation references  
- maintainable code and documentation  

They also align with Home Assistant’s best practices and the conventions used by other dynamic‑tariff integrations.