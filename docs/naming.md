# EDF FreePhase Dynamic Tariff — Naming Conventions (v0.7.1)

This document describes the naming rules used across the integration.

The goal is to keep entity names:
- predictable  
- readable  
- consistent  
- future‑proof for multi‑tariff support  
- easy to use in dashboards and automations  

---

# 🏷 Overview

As of **v0.7.1**, the integration uses a unified naming scheme across:

- entity IDs  
- friendly names  
- event types  
- internal helpers  
- diagnostics  

This ensures long‑term stability and prepares the integration for additional EDF tariffs in future releases.

---

# 🧩 Entity ID Naming (NEW in v0.7.1)

All entity IDs now follow this pattern:

- `<domain>.edf_fpd_<object_id>`

Where:

- `edf_fpd` = integration + tariff prefix  
- `<object_id>` = descriptive, snake_case identifier  
- `<domain>` = `sensor`, `binary_sensor`, `switch`, or `event`  

### Examples

- `sensor.edf_fpd_current_price`
- `sensor.edf_fpd_next_slot_price`
- `binary_sensor.edf_fpd_is_green_slot`
- `switch.edf_fpd_debug_logging`
- `event.edf_fpd_tariff_slot_phase_events`

Entity IDs are generated using the internal helper:

- `build_entity_id(domain, object_id, tariff="fpd")`

This ensures consistency and future multi‑tariff support.

---

# 🏷 Friendly Name Conventions (NEW in v0.7.1)

All friendly names now begin with:

- `EDF FPD …`

Examples:

- `EDF FPD Current Price`
- `EDF FPD Next Green Slot`
- `EDF FPD Standing Charge`
- `EDF FPD Tariff Slot & Phase Events`
- `EDF FPD Debug Logging`

This ensures clarity when multiple EDF tariffs are supported.

---

# 📡 Event Naming (Introduced in v0.7.0)

All event types follow this pattern:

- `edf_fpd_<description>`

Where:

- `edf_fpd` = integration + tariff prefix  
- `<description>` = snake_case description of the transition  

### Event Types

- `edf_fpd_slot_changed`
- `edf_fpd_phase_changed`
- `edf_fpd_phase_started`
- `edf_fpd_phase_ended`
- `edf_fpd_phase_block_changed`
- `edf_fpd_next_phase_changed`
- `edf_fpd_next_green_phase_changed`
- `edf_fpd_next_amber_phase_changed`
- `edf_fpd_next_red_phase_changed`
- `edf_fpd_debug` (debug event stream)

---

# 🧙‍♂️ Event Entity Naming (UPDATED in v0.7.1)

Event entities follow:

- `event.<integration>_<description>`

For this integration:

- `event.edf_fpd_tariff_slot_phase_events`

This entity emits all tariff‑related events.

---

# 📦 Attribute Naming

All attributes follow **snake_case**, including:

- `last_event_type`
- `last_event_timestamp`
- `event_counts`
- `event_history`
- `phase`
- `slot`
- `colour`
- `start`
- `end`

This ensures consistency across diagnostics, events, and sensors.

---

# 🧱 Internal Naming Rules

### File & Module Names
- Lowercase  
- Underscore‑separated  
- Descriptive of function  

Examples:

- `coordinator.py`
- `cost_coordinator.py`
- `slot_events.py`
- `helpers.py`


### Class Names
- PascalCase  
- Suffix indicates entity type  

Examples:

- `EDFFreePhaseDynamicPriceSensor`
- `EDFFreePhaseDynamicNextPhaseSlotSensor`
- `EDFFreePhaseDynamicCostCoordinatorStatusSensor`

---

# 📘 Summary

- All entity IDs use the `edf_fpd_` prefix.  
- All friendly names begin with `EDF FPD`.  
- All event types use the `edf_fpd_` prefix.  
- All attributes use snake_case.  
- The event entity is now `event.edf_fpd_tariff_slot_phase_events`.  
- Entity IDs are generated using `build_entity_id()` for consistency and future multi‑tariff support.  
