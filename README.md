# EDF FreePhase Dynamic Tariff – Home Assistant Integration

![Version](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![License](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff?refresh=1)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://hacs.xyz/)

A custom Home Assistant integration providing real‑time and forecasted electricity pricing for the **EDF FreePhase Dynamic** tariff.  
Half‑hourly unit rates are retrieved directly from the EDF Kraken API and exposed as structured sensors designed for automations, dashboards, and energy optimisation.

---

## ✨ Features

- Live **current unit rate**
- **Next half‑hour** slot price
- Full **24‑hour forecast**
- Cheapest and most expensive slots
- Next **green**, **amber**, and **red** slots
- Current slot colour (green / amber / red)
- **Today’s merged rate blocks** (colour, start, end, duration, price)
- **Tomorrow’s merged rate blocks**
- API diagnostics:
  - Last updated
  - API latency
  - Coordinator status (OK / Error)
- Timeseries‑friendly sensors for charts
- Resilient coordinator with graceful error‑handling
- Options flow for:
  - Scan interval  
  - Forecast window  
  - API timeout  
  - Retry attempts  
  - Custom API URL  
  - Include/exclude past slots  

---

## 📦 Installation

### Option 1 — HACS (recommended)

Once this repository is added to HACS as a custom repository:

1. Go to **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add the repository URL  
   Category: **Integration**
4. Search for **EDF FreePhase Dynamic Tariff**
5. Install and restart Home Assistant

### Option 2 — Manual installation

Copy the folder:

custom_components/edf_freephase_dynamic_tariff

into:

config/custom_components/


Then restart Home Assistant.

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **EDF FreePhase Dynamic Tariff**
4. Enter your **tariff code**, for example:

E-1R-EDF_FREEPHASE_DYNAMIC_12M_HH-E


Advanced settings can be adjusted later via the **Options** menu.

---

## 🧠 Sensors Provided

### Pricing & Forecast

| Sensor | Description |
|-------|-------------|
| Current Price | Current half‑hour unit rate |
| Next Slot Price | Price of the next half‑hour slot |
| 24‑Hour Forecast | Full forecast list (attributes) |
| Cheapest Slot | Lowest price in the forecast window |
| Most Expensive Slot | Highest price in the forecast window |

### Slot Colour & Phase

| Sensor | Description |
|-------|-------------|
| Current Slot Colour | green / amber / red |
| Next Green Slot | Next green‑phase slot |
| Next Amber Slot | Next amber‑phase slot |
| Next Red Slot | Next red‑phase slot |
| Is Green Slot | Boolean indicator |

### Merged Block Summaries

| Sensor | Description |
|-------|-------------|
| Today’s Rates Summary | Merged blocks for today (colour, start, end, duration, price) |
| Tomorrow’s Rates Summary | Merged blocks for tomorrow |

### Diagnostics

| Sensor | Description |
|-------|-------------|
| Last Updated | Timestamp of last processed data |
| API Latency | Response time in ms |
| Coordinator Status | OK / Error |

---

## 🛠️ Requirements

- Home Assistant 2024.6 or newer  
- Internet access to the EDF Kraken API  
- Python dependencies installed automatically  

---

## 🧩 Known Limitations

- Only electricity unit rates are supported at this time  
- EDF may occasionally return incomplete or delayed forecast data  
- Tomorrow’s data depends on EDF publishing the next day’s slots  (normally avalable by around 16:00 on the previous day)

---

## 🤝 Contributing

Issues, feature requests, and pull requests are welcome.  
This integration is built primarily for UK users, but contributions for broader tariff support are encouraged.

---

## 📄 License

MIT License.