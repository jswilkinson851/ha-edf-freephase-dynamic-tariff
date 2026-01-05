# EDF FreePhase Dynamic Tariff — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub license](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub last commit](https://img.shields.io/github/last-commit/jswilkinson851/ha-edf-freephase-dynamic-tariff)

This custom integration provides **live pricing and full‑day half‑hourly rate data** for the **EDF FreePhase Dynamic 12‑month tariff**, using the EDF/Octopus Kraken API.  
It is designed for UK users on the FreePhase Dynamic tariff and supports multiple regions, multiple devices, and fully dynamic tariff‑code detection.

The integration retrieves tariff information directly from the Kraken API and exposes it as Home Assistant sensors, allowing you to automate, visualise, and optimise your energy usage based on real‑time and upcoming pricing.

---

## Features

- **Dynamic tariff code detection**  
  Tariff codes are fetched directly from the Kraken API, ensuring the region list stays accurate even if EDF updates their product codes.

- **Human‑friendly region selection**  
  Regions are displayed as:  
  **Region A: Eastern England**, **Region B: East Midlands**, etc.

- **Multiple devices supported**  
  Add more than one region as separate devices, each with its own coordinator and sensors.

- **Configurable scan interval**  
  Entered in minutes, stored internally in seconds.

- **Full‑day pricing sensors**  
  Provides all available half‑hour slots for **today** and **tomorrow**, including raw UTC timestamps and local formatted times.

- **Option to include past slots**  
  Useful for charts and energy‑usage analysis.

- **Coordinator failsafe & retry logic**  
  Automatic retry/backoff and a “last known good data” fallback prevent sensors from going unavailable during temporary API outages.

- **Rich metadata sensors**  
  Includes API latency, coordinator health, last successful update, and data age.

---

## Installation (HACS)

### Option 1 — Add via HACS (Custom Repository)

1. Go to **HACS → Integrations → Custom Repositories**  
2. Add:  
   `https://github.com/jswilkinson851/ha-edf-freephase-dynamic-tariff`
3. Select category: **Integration**  
4. Install  
5. Restart Home Assistant  
6. Add the integration via **Settings → Devices & Services → Add Integration**

### Option 2 — Manual Installation

1. Copy this repository into your Home Assistant `custom_components` directory  
2. Restart Home Assistant  
3. Add the integration via **Settings → Devices & Services → Add Integration**

---

## Region Codes

Tariff codes are retrieved from:

https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/

Each tariff code ends with a letter (A–P, excluding I and O) corresponding to a UK DNO region.

For a clear explanation of these region letters:

**https://energy-stats.uk/dno-region-codes-explained/#UK_DNO_Region_Codes_A%E2%80%93P_List_and_Map**

If the API is unavailable, the integration falls back to a complete static list of regions.

---

## Configuration Options

- **Region Code**  
  Select your region from the dynamically generated list.

- **Scan Interval (minutes)**  
  How often to refresh tariff data.  
  Default: 5 minutes.

- **Include Past Slots**  
  Whether to include historical half‑hour slots.  
  Default: enabled.

---

## Multiple Instances

You can add multiple regions as separate devices.  
Each instance creates its own:

- device  
- coordinator  
- sensors  
- entity IDs  

Useful for comparing regions or monitoring multiple properties.

---

## Available Sensors

### Pricing Sensors
- `sensor.current_price`
- `sensor.next_slot_price`
- `sensor.cheapest_slot`
- `sensor.most_expensive_slot`

### Full‑Day Rate Sensors
- `sensor.todays_rates_full`
- `sensor.tomorrows_rates_full`

### Daily Summary Sensors
- `sensor.today_s_rates_summary`
- `sensor.tomorrow_s_rates_summary`

### Slot & Block Sensors
- `sensor.current_slot_colour`
- `sensor.current_block_summary`
- `sensor.next_block_summary`
- `sensor.next_green_slot`
- `sensor.next_amber_slot`
- `sensor.next_red_slot`
- `sensor.is_green_slot`

### Metadata / Health Sensors
- `sensor.api_latency`
- `sensor.last_updated`
- `sensor.last_successful_update`
- `sensor.data_age`
- `sensor.coordinator_status`

---

## Example Dashboards (ApexCharts & Lovelace)

### Daily Summary Card

```yaml
type: entities
title: Daily Tariff Summary
entities:
  - entity: sensor.today_s_rates_summary
    name: Today’s Rates
  - entity: sensor.tomorrow_s_rates_summary
    name: Tomorrow’s Rates
  - type: divider
  - entity: sensor.current_price
    name: Current Price
  - entity: sensor.next_slot_price
    name: Next Slot Price
  - entity: sensor.current_slot_colour
    name: Current Slot Colour
```

A clean line chart showing the next 24 hours of half‑hourly pricing.

```yaml
type: custom:apexcharts-card
header:
  title: Today’s Price Profile
  show: true
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.todays_rates_full
    name: Price
    type: line
    stroke_width: 2
    color: '#3b82f6'
    data_generator: |
      const out = [];
      for (const [key, slot] of Object.entries(entity.attributes)) {
        if (!key.startsWith("slot_")) continue;
        out.push([new Date(slot.start_utc).getTime(), slot.value]);
      }
      return out.sort((a,b) => a[0] - b[0]);
apex_config:
  yaxis:
    labels:
      formatter: |
        EVAL:function (value) { return value.toFixed(2) + 'p'; }
  xaxis:
    labels:
      datetimeUTC: false
```

---

## Integration Health & Diagnostics

This integration includes several metadata sensors that help you understand the health of the EDF FreePhase Dynamic Tariff API and the coordinator.

### Included Health Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.coordinator_status` | Shows `ok`, `degraded`, or `error` depending on API success and fallback behaviour. |
| `sensor.last_successful_update` | Timestamp of the last time fresh data was successfully fetched. |
| `sensor.data_age` | Number of seconds since the last successful update. |
| `sensor.last_updated` | When the coordinator last ran (even if the API failed). |
| `sensor.api_latency` | API response time in milliseconds. |

These sensors make it easy to build a “Health Panel” in Lovelace:

```yaml
type: entities
title: EDF FreePhase Dynamic – Health Panel
entities:
  - entity: sensor.coordinator_status
  - entity: sensor.last_successful_update
  - entity: sensor.data_age
  - entity: sensor.last_updated
  - entity: sensor.api_latency
```

This helps you quickly diagnose API outages, stale data, or connectivity issues.

---

## Troubleshooting

- If the region list only shows a few entries, the API may be temporarily unavailable.
The integration will fall back to a complete static list of regions A–P.

- If you previously added the integration before updating, removing and re‑adding it ensures the new dynamic region list is used.

- If tariff codes ever change in future, the integration will automatically detect the new prefix and continue working without modification.

- If the API becomes unavailable, the integration will continue operating using the last successful data until the API recovers.

---

## License

MIT License.  
Feel free to fork, improve, and contribute.