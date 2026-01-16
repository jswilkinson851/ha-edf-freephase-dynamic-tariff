# EDF FreePhase Dynamic — Event Documentation (v0.4.0)

This document describes the Home Assistant events exposed by the **EDF FreePhase Dynamic Tariff** integration as of v0.4.0.

A future release (v0.5.x) may expand or refine these events.

---

# Overview

The integration exposes two events that allow automations to react to:

- changes in the current tariff phase  
- publication of a new 48‑slot forecast  

These events are aligned with EDF’s behaviour:

- half‑hourly slot pricing  
- derived phases (green, amber, red)  
- a daily forecast window running from 23:00 Day D → 23:00 Day D+1  

There is **no longer a `free` phase**.  
Negative prices are represented as **red** slots.

---

# Event #1: `edf_fpd_phase_changed`

## Description

This event fires **exactly at the boundary of a 30‑minute slot** when the tariff’s phase changes.

This is ideal for automations such as:

- running appliances during green phases  
- reducing consumption during red phases  
- pre‑charging or pre‑heating before a red phase  
- adjusting EV charging rates dynamically  

---

## Firing Rules

The event fires when:

- a new slot begins, **and**
- the new slot’s phase differs from the previous slot’s phase.

The integration guarantees:

- no duplicate events  
- no missed transitions  
- events always aligned to slot boundaries  

---

## Payload Schema

### Phase Information

| Field      | Type   | Description                                           |
|------------|--------|-------------------------------------------------------|
| old_phase  | string | Previous phase (`green`, `amber`, `red`)              |
| new_phase  | string | New phase (`green`, `amber`, `red`)                   |

### Slot Timing

| Field      | Type     | Description                                      |
|------------|----------|--------------------------------------------------|
| slot_start | datetime | Start of the slot where the phase changed        |
| slot_end   | datetime | End of the slot                                  |

### Phase Window Timing

| Field      | Type     | Description                                      |
|------------|----------|--------------------------------------------------|
| phase_start | datetime | Start of the new phase window                   |
| phase_end   | datetime | End of the new phase window                     |
| duration_minutes | integer | Total duration of the phase window         |

### Price Information

| Field | Type   | Description                                 |
|-------|--------|---------------------------------------------|
| price | float  | Price of the first slot in the new phase    |
| unit  | string | Always `p/kWh`                              |

### Raw Slot Data

| Field      | Type    | Description                                      |
|------------|---------|--------------------------------------------------|
| slot_index | integer | Index of the slot within the 48‑slot forecast    |

---

## Example Payload

{
  "old_phase": "amber",
  "new_phase": "red",
  "slot_start": "2026-01-11T16:00:00+00:00",
  "slot_end": "2026-01-11T16:30:00+00:00",
  "phase_start": "2026-01-11T16:00:00+00:00",
  "phase_end": "2026-01-11T19:00:00+00:00",
  "duration_minutes": 180,
  "price": 33.55,
  "unit": "p/kWh",
  "slot_index": 32
}

---

# Developer Notes

## Phase Calculation

Phases are derived from slot prices using EDF’s published thresholds:

- green — cheapest  
- amber — normal  
- red — expensive or negative  

There is **no separate `free` phase**.

## Phase Windows

A phase window is defined as:

- a consecutive run of slots with the same phase classification.

## Slot Index

`slot_index` is the position of the slot within the 48‑slot forecast window (0–47).

---

# Event #2: `edf_fpd_new_forecast_available`

## Description

This event fires whenever EDF publishes a **new 48‑slot forecast** covering:

- 23:00 on Day D  
- to 23:00 on Day D+1  

This event is ideal for:

- rebuilding heating or EV schedules  
- detecting negative‑price periods  
- updating dashboards  
- notifying users of price changes  

---

## Firing Rules

The event fires when:

- new tariff data is fetched, **and**
- the forecast window changes.

The integration guarantees:

- exactly one event per forecast update  
- no duplicate events  
- accurate identification of cheapest and most expensive slots  

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

---

# EDF FreePhase Dynamic — Event Documentation (v0.5.0)

Events remain unchanged in behaviour, but now include access to richer coordinator data.

The following additional fields are now available to developers via diagnostics:

- tariff_metadata
- tariff_region_label
- product_url
- api_url

Event payloads themselves are unchanged in this release.

---

# Notes

- All price values use **p/kWh**.  
- Zero‑price and negative‑price slots are treated as green, since they represent free electricity.  
- Forecast windows always run 23:00 → 23:00.  
- Events fire only when meaningful changes occur.  