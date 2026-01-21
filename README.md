# ⚡ EDF FreePhase Dynamic Tariff — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub license](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![GitHub last commit](https://img.shields.io/github/last-commit/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![installation_badge](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.edf_freephase_dynamic_tariff.total)

This integration brings **live electricity prices**, **half‑hourly rate data**, and **cost tracking** for the **EDF FreePhase Dynamic** tariff directly into Home Assistant.

It’s built for UK users on the FreePhase Dynamic tariff and gives you everything you need to automate, plan, and understand your energy usage — all using the same Kraken API that EDF themselves rely on.

---

# ✨ What This Integration Can Do

## 🔹 Automatic Region & Tariff Detection
Just choose your region — the integration fetches the correct tariff code for you.  
If EDF’s API is down, it falls back to a complete built‑in list.

## 🔹 Smarter Refresh Timing (Aligned Scheduler)
Updates happen exactly on the minute or half‑hour (depending on your settings), with a tiny bit of random delay to avoid everyone hitting the API at once.

## 🔹 Cost Tracking (NEW in v0.6.0)
If you provide your electricity import sensor, the integration can now calculate:
- Today’s cost  
- Yesterday’s cost  
- Cost per slot  
- Cost per phase (Green/Amber/Red)

This uses your real meter readings, so the numbers are accurate.

**N.B.** Currently, standing charges are not included, but this will be added in a future release.

## 🔹 Debug Logging Switch (NEW)
Turn detailed logging on or off from the Options Flow — no YAML, no restarts.

## 🔹 Better Diagnostics (NEW)
A single diagnostic sensor now shows:
- API health  
- Scheduler timing  
- Current/next slot  
- Phase windows  
- Tariff metadata  
- Debug logs  
- Cost engine status  

Perfect for troubleshooting or building a “health panel”.

## 🔹 Binary Sensor (NEW)
- **Is it a Green slot right now?**  
  Now you have a simple yes/no sensor for that.

## 🔹 Clean Device Grouping
All sensors and binary sensors appear under one device in Home Assistant.

---

# 🛠️ Installation (HACS)

## Option 1 — HACS Custom Repository (recommended)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jswilkinson851&repository=ha-edf-freephase-dynamic-tariff)

1. Open **HACS → Integrations → Custom Repositories**  
2. Add this URL:  
   https://github.com/jswilkinson851/ha-edf-freephase-dynamic-tariff  
3. Choose **Integration**  
4. Install  
5. Restart Home Assistant  
6. Add the integration via **Settings → Devices & Services**

## Option 2 — Manual Install
Copy the folder into `custom_components/`, restart HA, and add the integration.

---

# 🗺️ Region Codes

The integration fetches region‑specific tariff codes from EDF’s public API.  
Each region has a letter (A–P).  
If the API is down, the integration uses a built‑in list so setup still works.

---

# ⚙️ Configuration Options

### **Region**
Pick your region from the list. The integration handles the tariff code.

### **Scan Interval**
How often the integration refreshes prices.  
Updates happen on exact clock boundaries (e.g., 12:00, 12:30).

### **Import Sensor (optional, but recommended)**
If you provide your electricity import meter, the integration can calculate:
- Today’s cost  
- Yesterday’s cost  
- Slot‑level cost  

### **Debug Logging**
A simple toggle in the Options Flow.  
Useful if you’re troubleshooting or want to see what the coordinator is doing.

---

# 📡 Available Entities

## 🔹 Pricing Sensors
- `Current price`  
- `Next slot price`  
- `Cheapest slot in next 24 hours`  
- `Most expensive slot in next 24 hours`  

## 🔹 Cost Sensors (NEW)
- `Cost today`  
- `Cost yesterday`  
- `Cost per slot`  
- `Cost per phase`  

## 🔹 Slot & Block Sensors
- `Current slot colour`  
- `Current block summary`  
- `Next block summary`  
- `Next green/amber/red slot`  

## 🔹 Binary Sensors
- `Is the current slot green?`

## 🔹 Debug Sensors
- `Next refresh time`  
- `Debug logging enabled`  
- `Debug buffers` (helpful for troubleshooting)

## 🔹 Health & Metadata Sensors
- `API latency`  
- `Last updated`  
- `Last successful update`  
- `Data age`  
- `Coordinator status`  

---

# 📊 Example Dashboard Card

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

# 🩺 Diagnostics

The downloadable diagnostics include:
- `Tariff metadata`  
- `Region label`  
- `API URLs`  
- `Current slot`  
- `Block summaries`  
- `Scheduler timing`  
- `Heartbeat flags`  
- `Debug logs`  
- `Cost engine status`  

This makes it much easier to understand what’s happening behind the scenes.

---

# 🛟 Troubleshooting

- If the region list looks short, EDF’s API may be having a moment — try again later.  
- Removing and re‑adding the integration refreshes the region list.  
- If the API goes offline, the integration keeps using the last good data.  
- Turn on debug logging in the Options Flow if you need deeper insight.

---

# 📜 Changelog

Full release notes:  
https://github.com/jswilkinson851/ha-edf-freephase-dynamic-tariff/releases

---

# 📄 License

MIT License.

---

# ⚠️ Disclaimer

This is a community project and is **not affiliated with EDF Energy** or the Kraken platform.  
All trademarks belong to their respective owners.
