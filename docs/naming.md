# EDF FreePhase Dynamic Tariff — Naming Conventions (v0.6.1)

This document describes the naming rules used across the integration.

The goal is to keep entity names:
- predictable  
- readable  
- consistent  
- easy to use in dashboards and automations  

---

# 🏷 Naming Conventions

This integration follows strict naming conventions to ensure consistency across sensors, diagnostics, events, and internal modules.

---

# 📡 Event Naming (NEW in v0.7.0)

All event types follow this pattern:

`edf_fpd_<description>`


Where:
- `edf_fpd` = integration prefix  
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

# 🧙‍♂️ Event Entity Naming

Event entities follow:

`event.<integration>_<description>`

For this integration:

`event.tariff_slot_phase_events`


This entity emits all tariff‑related events.

---

# 📦 Attribute Naming (NEW in v0.7.0)

Event diagnostics attributes follow snake_case:

- `last_event_type`
- `last_event_timestamp`
- `event_counts`
- `event_history`

---

# 📘 Summary

- All event types use the `edf_fpd_` prefix.  
- All attributes use snake_case.  
- The event entity uses a descriptive, human‑friendly name.  
- Debug events follow the same naming pattern as functional events.  