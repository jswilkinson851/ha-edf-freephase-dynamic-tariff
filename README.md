# ⚡ EDF FreePhase Dynamic Tariff — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub license](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub last commit](https://img.shields.io/github/last-commit/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![installation_badge](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.edf_freephase_dynamic_tariff.total)

This custom integration provides **live pricing and full half‑hourly rate data** for the **EDF FreePhase Dynamic 12‑month tariff**, using the EDF/Octopus Kraken API.  
It is designed for UK users on the FreePhase Dynamic tariff and supports multiple regions, multiple devices, and fully dynamic tariff‑code detection.

The integration retrieves tariff information directly from the Kraken API and exposes it as Home Assistant sensors, allowing you to automate, visualise, and optimise your energy usage based on real‑time and upcoming pricing.

---

## ✨ Features

- **Dynamic tariff code detection**  
  Tariff codes are fetched directly from the Kraken API, ensuring the region list stays accurate even if EDF updates their product codes.

- **Human‑friendly region selection**  
  Regions are displayed as:  
  **Region A: Eastern England**, **Region B: East Midlands**, etc.

- **Multiple devices supported**  
  Add more than one region as separate devices, each with its own coordinator and sensors.

- **Configurable scan interval**  
  Entered in minutes, stored internally in seconds.  
  API refreshes occur on precise wall‑clock boundaries based on your configured scan interval.  
  Examples:  
  - 30 minutes → 12:00, 12:30, 13:00, 13:30  
  - 5 minutes → 12:00, 12:05, 12:10, 12:15  
  - 1 minute → exactly on the minute  
  A small random jitter (0–5 seconds) is added to avoid simultaneous API hits across multiple Home Assistant instances.

- **Unified slot dataset**  
  All sensors now use a single authoritative list of half‑hour slots, ensuring consistent behaviour across the integration.

- **Accurate block detection**  
  Current and next block summaries merge consecutive slots of the same colour, matching the real tariff structure.

- **Daily summaries**  
  Clean, merged summaries for **today** and **tomorrow**, including start, end, duration, price, and colour.

- **Coordinator failsafe & retry logic**  
  Automatic retry/backoff and a “last known good data” fallback prevent sensors from going unavailable during temporary API outages.

- **Rich metadata sensors**  
  Includes API latency, coordinator health, last successful update, and data age.

---

## 🛠️ Installation (HACS)

### Option 1 — Add via HACS Custom Repository (recommended)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jswilkinson851&repository=ha-edf-freephase-dynamic-tariff)

1. Go to **HACS → Integrations → Custom Repositories**  
2. Add:  
   https://github.com/jswilkinson851/ha-edf-freephase-dynamic-tariff  
3. Select category: **Integration**  
4. Install  
5. Restart Home Assistant  
6. Add the integration via **Settings → Devices & Services → Add Integration → "EDF FreePhase Dynamic Tariff"**

### Option 2 — Manual Installation (not recommended)

1. Copy this repository into your Home Assistant `custom_components` directory  
2. Restart Home Assistant  
3. Add the integration via **Settings → Devices & Services → Add Integration → "EDF FreePhase Dynamic Tariff"**

---

## 🗺️ Region Codes

Tariff codes are retrieved from:

- https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/

Each tariff code ends with a letter (A–P, excluding I and O) corresponding to a UK DNO region.

For a clear explanation of these region letters:

- https://energy-stats.uk/dno-region-codes-explained/#UK_DNO_Region_Codes_A%E2%80%93P_List_and_Map

If the API is unavailable, the integration falls back to a complete static list of regions.

---

## ⚙️ Configuration Options

- **Region Code**  
  Select your region from the dynamically generated list.  
  The selected region label is now stored internally and shown in diagnostics.

- **Scan Interval (minutes)**  
  How often to refresh tariff data.  
  API refreshes occur on aligned wall‑clock boundaries with a small jitter.

- **Import Sensor (optional)**  
  Your electricity import sensor.  
  This will be used in future releases to compare real usage against historic EDF slots.

- **Product URL (internal)**  
  The integration now validates the EDF product metadata endpoint before setup.  
  This field is for internal use only and should not be modified.

---

## 📡 Available Sensors

Below is the list of **short, user‑friendly entity names**, matching your dashboard usage.

### Pricing Sensors
- `sensor.current_price`
- `sensor.edf_freephase_dynamic_next_slot_price`
- `sensor.edf_freephase_dynamic_cheapest_slot_next_24_hours`
- `sensor.edf_freephase_dynamic_most_expensive_slot_next_24_hours`

### Daily Summary Sensors
- `sensor.today_s_rates_summary`
- `sensor.tomorrow_s_rates_summary`

### Slot & Block Sensors
- `sensor.edf_freephase_dynamic_current_slot_colour`
- `sensor.current_block_summary`
- `sensor.next_block_summary`
- `sensor.edf_freephase_dynamic_next_green_slot`
- `sensor.edf_freephase_dynamic_next_amber_slot`
- `sensor.edf_freephase_dynamic_next_red_slot`
- `sensor.edf_freephase_dynamic_is_now_a_green_slot`

### Metadata / Health Sensors
- `sensor.api_latency`
- `sensor.last_updated`
- `sensor.last_successful_update`
- `sensor.data_age`
- `sensor.coordinator_status`

### Debug Sensors
- `sensor.edf_freephase_dynamic_next_refresh_time` (added in v0.3.7)

---

## 📊 Example Dashboards (ApexCharts & Lovelace)

### Daily Summary Card
```
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
  - entity: sensor.edf_freephase_dynamic_next_slot_price  
    name: Next Slot Price  
  - entity: sensor.edf_freephase_dynamic_current_slot_colour  
    name: Current Slot Colour  
```
---

## 🩺 Integration Health & Diagnostics

This integration includes several metadata sensors that help you understand the health of the EDF FreePhase Dynamic Tariff API and the coordinator.

### Included Health Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.coordinator_status` | Shows ok, degraded, or error depending on API success and fallback behaviour. |
| `sensor.last_successful_update` | Timestamp of the last time fresh data was successfully fetched. |
| `sensor.data_age` | Number of seconds since the last successful update. |
| `sensor.last_updated` | When the coordinator last ran (even if the API failed). |
| `sensor.api_latency` | API response time in milliseconds. |

These sensors make it easy to build a “Health Panel” in Lovelace.

---

## 🧪 Downloadable Diagnostics Enhancements (v0.5.0)

Diagnostics (download) now include:

- tariff metadata (cleaned and normalised)  
- region label  
- product_url and api_url  
- current slot  
- current and next block summaries  
- expanded scheduler internals  

These additions make troubleshooting and verification significantly easier.

---

## 🛟 Troubleshooting

- If the region list only shows a few entries, the API may be temporarily unavailable.  
  The integration will fall back to a complete static list of regions A–P.

- If you previously added the integration before updating, removing and re‑adding it ensures the new dynamic region list is used.

- If tariff codes ever change in future, the integration will automatically detect the new prefix and continue working without modification.

- If the API becomes unavailable, the integration will continue operating using the last successful data until the API recovers.

---

## 📄 License

MIT License.  
Feel free to fork, improve, and contribute.

---

## ⚠️ Disclaimer

This project is an **independent, community‑developed integration** and is **not affiliated with, endorsed by, or supported by EDF Energy** or the Octopus/EDF Kraken platform.  
All trademarks, logos, and brand names remain the property of their respective owners.  
This integration interacts with publicly accessible endpoints of the Kraken API but is **not an official EDF product**.
Use at your own risk. The author accepts no responsibility for any issues arising from its use.
