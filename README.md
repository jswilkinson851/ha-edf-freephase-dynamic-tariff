# EDF FreePhase Dynamic Tariff – Home Assistant Integration

![Version](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![License](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff?refresh=1)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://hacs.xyz/)

A custom Home Assistant integration that provides real‑time and forecasted electricity pricing for the **EDF FreePhase Dynamic** tariff.  
This integration fetches half‑hourly unit rates directly from the EDF Kraken API and exposes them as rich, structured sensors for automations, dashboards, and energy optimisation.

---

## ✨ Features

- Live **current unit rate**
- **Next half‑hour** slot price
- Full **forecast window** (configurable, default 24 hours)
- Cheapest and most expensive slots
- Next **green**, **amber**, and **red** slots
- Current slot colour (green/amber/red)
- API diagnostics:
  - Last checked
  - Last updated
  - API latency
- Timeseries‑friendly current price sensor for charts
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
[![Install with HACS](https://img.shields.io/badge/HACS-Install-41BDF5.svg)](https://github.com/hacs/integration)

Once this repository is added to HACS as a custom repository:

1. Go to **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add your repository URL  
   Category: **Integration**
4. Search for **EDF FreePhase Dynamic Tariff**
5. Install and restart Home Assistant

### Option 2 — Manual installation (not recommended)

Copy the folder:

```
custom_components/edf_freephase_dynamic_tariff
```

into:

```
config/custom_components/
```

Then restart Home Assistant.

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **EDF FreePhase Dynamic Tariff**
4. Enter your **tariff code**, e.g.:

```
E-1R-EDF_FREEPHASE_DYNAMIC_12M_HH-E
```

After setup, you can adjust advanced settings in the **Options** menu.

---

## 🧠 Sensors Provided

| Sensor | Description |
|-------|-------------|
| Current Price | Current half‑hour unit rate |
| Next Slot Price | Price of the next half‑hour slot |
| 24-Hour Forecast | Full forecast list (attributes) |
| Cheapest Slot | Lowest price in forecast window |
| Most Expensive Slot | Highest price in forecast window |
| Next Green Slot | Next green‑phase slot |
| Next Amber Slot | Next amber‑phase slot |
| Next Red Slot | Next red‑phase slot |
| Current Slot Colour | green / amber / red |
| Is Green Slot | Boolean indicator |
| Last Updated | Timestamp of last processed data |
| API Latency | Response time in ms |

---

## 🛠️ Requirements

- Home Assistant 2024.6 or newer
- Internet access to EDF Kraken API
- Python dependencies installed automatically

---

## 🧩 Known Limitations

- The integration currently supports electricity unit rates only.
- EDF may occasionally return incomplete forecast windows during maintenance.

---

## 🤝 Contributing

Pull requests, issues, and feature suggestions are welcome.  
This integration was built with UK users in mind, but contributions for wider tariff support are encouraged.

---

## 📄 License

MIT License.
