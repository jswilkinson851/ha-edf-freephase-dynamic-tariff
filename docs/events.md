# EDF FreePhase Dynamic — Event Documentation

> **Planned:** _To be implemented in v0.3.8._

## Overview

The EDF FreePhase Dynamic integration exposes two Home Assistant events that allow automations to react to changes in the tariff:

- **edf_fpd_phase_changed**
- **edf_fpd_new_forecast_available**

These events are built around the tariff’s real behaviour: half‑hourly slot pricing, derived phases, and a daily forecast window running from 23:00 on Day D to 23:00 on Day D+1.

---

# Event #1: 'edf_fpd_phase_changed'

## Description

This event fires exactly at the boundary of a 30‑minute slot when the tariff’s current phase changes. A phase change can only occur when EDF publishes a new slot price.

This event is ideal for automations such as:

- Running appliances during green phases
- Reducing consumption during red phases
- Pre‑heating or pre‑charging before a red phase begins
- Adjusting EV charging rates based on phase

---

## Firing Rules

The event fires when:

- A new slot begins, **and**
- The phase classification differs from the previous slot.

The integration guarantees:

- No duplicate events  
- No missed transitions  
- Events always aligned to slot boundaries  
- Accurate phase window calculation  

---

## Payload Schema

### Phase Information

| Field      | Type   | Description                                           |
|------------|--------|-------------------------------------------------------|
| old_phase  | string | Previous phase (`green`, `amber`, `red`, `free`)      |
| new_phase  | string | New phase (`green`, `amber`, `red`, `free`)           |

### Slot Timing

| Field         | Type     | Description                                      |
|---------------|----------|--------------------------------------------------|
| slot_start    | datetime | Start of the slot where the phase changed        |
| slot_end      | datetime | End of the slot                                  |
| slot_duration | string   | Duration of the slot (`00:30:00`)                |

### Phase Timing

| Field          | Type     | Description                                      |
|----------------|----------|--------------------------------------------------|
| phase_start    | datetime | Start of the new phase window                    |
| phase_end      | datetime | End of the new phase window                      |
| phase_duration | string   | Total duration of the phase window               |

### Price Information

| Field | Type   | Description                                 |
|-------|--------|---------------------------------------------|
| price | float  | Price of the first slot in the new phase    |
| unit  | string | Unit of the price (e.g., `p/kWh`)           |

### Raw Slot Data

| Field      | Type    | Description                                      |
|------------|---------|--------------------------------------------------|
| slot_index | integer | Index of the slot within the 48‑slot forecast    |

---

## Example Payload

```json
{
  "old_phase": "amber",
  "new_phase": "red",
  "slot_start": "2026-01-11T16:00:00+00:00",
  "slot_end": "2026-01-11T16:30:00+00:00",
  "slot_duration": "00:30:00",
  "phase_start": "2026-01-11T16:00:00+00:00",
  "phase_end": "2026-01-11T19:00:00+00:00",
  "phase_duration": "03:00:00",
  "price": 33.55,
  "unit": "p/kWh",
  "slot_index": 32
}
```

# Developer Notes

## Phase Calculation
Phases are derived from slot prices using EDF’s published thresholds:

- green — cheapest

- amber — normal

- red — expensive

- free — negative wholesale

## Phase Windows
A phase window is defined as:

- A consecutive run of slots with the same phase classification.

## 'Slot Index'

`slot_index` is the position of the slot within the 48‑slot forecast window (0–47).

---
# Event #2: 'edf_fpd_new_forecast_available'

## Description

This event fires whenever EDF publishes a new 48‑slot forecast covering:

- 23:00 on Day D  
- to 23:00 on Day D+1

This event is ideal for:

- Rebuilding heating or EV schedules  
- Detecting free electricity periods  
- Updating dashboards  
- Notifying users of price changes  

---

## Firing Rules

The event fires when:

- New tariff data is fetched, **and**  
- The forecast window changes.

The integration guarantees:

- Exactly one event per forecast update  
- No duplicate events  
- Accurate identification of cheapest and most expensive slots  

---

## Payload Schema

### Forecast Metadata

| Field          | Type     | Description                                      |
|----------------|----------|--------------------------------------------------|
| effective_from | datetime | Start of the forecast window (23:00 Day D)       |
| effective_to   | datetime | End of the forecast window (23:00 Day D+1)       |
| slots          | integer  | Number of slots (always 48)                      |

### Highlights

| Field                | Type     | Description                                  |
|----------------------|----------|----------------------------------------------|
| cheapest_slot        | datetime | Start time of the cheapest slot              |
| cheapest_price       | float    | Price of the cheapest slot                   |
| most_expensive_slot  | datetime | Start time of the most expensive slot        |
| most_expensive_price | float    | Price of the most expensive slot             |
| free_slots           | integer  | Number of slots with negative price          |

---

## Example Payload

```json
{
  "effective_from": "2026-01-12T23:00:00+00:00",
  "effective_to": "2026-01-13T23:00:00+00:00",
  "slots": 48,
  "cheapest_slot": "2026-01-13T03:00:00+00:00",
  "cheapest_price": 11.95,
  "most_expensive_slot": "2026-01-13T17:00:00+00:00",
  "most_expensive_price": 28.35,
  "free_slots": 0
}
```