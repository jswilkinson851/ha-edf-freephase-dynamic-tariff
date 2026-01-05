# EDF FreePhase Dynamic Tariff — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
![GitHub release](https://img.shields.io/github/v/release/jswilkinson851/edf_freephase_dynamic_tariff)
![GitHub license](https://img.shields.io/github/license/jswilkinson851/edf_freephase_dynamic_tariff)
![GitHub last commit](https://img.shields.io/github/last-commit/jswilkinson851/edf_freephase_dynamic_tariff)

This custom integration provides live and forecasted pricing for the **EDF FreePhase Dynamic 12‑month half‑hourly tariff**, using data from the EDF/Octopus Kraken API. It is designed for UK users on the FreePhase Dynamic tariff and supports multiple regions, multiple devices, and fully dynamic tariff‑code detection.

The integration retrieves tariff information directly from the Kraken API and exposes it as Home Assistant sensors, allowing you to automate, visualise, and optimise your energy usage based on real‑time and forecasted pricing.

---

## Features

- **Dynamic tariff code detection**  
  Tariff codes are fetched directly from the Kraken API, ensuring the region list stays accurate even if EDF updates their product codes.

- **Human‑friendly region selection**  
  Regions are displayed as:  
  **Region A: Eastern England**, **Region B: East Midlands**, etc.  
  This mapping follows Ofgem’s official DNO region definitions.

- **Multiple devices supported**  
  You can add more than one region as separate devices, each with its own sensors and coordinator.

- **Configurable scan interval**  
  Entered in minutes, stored internally in seconds.

- **Forecast window control**  
  Choose how many hours of future pricing to fetch.

- **Option to include past slots**  
  Useful for visualisations, graphs, and energy‑usage analysis.

- **Prefix‑agnostic tariff handling**  
  If EDF changes the tariff code prefix in future, the integration will automatically adapt.

---

## Installation (HACS)

### Option 1 — Add via HACS (Custom Repository)

1. Go to **HACS → Integrations → Custom Repositories**  
2. Add your repository URL  
3. Select category: **Integration**  
4. Install the integration  
5. Restart Home Assistant  
6. Add the integration via **Settings → Devices & Services → Add Integration**

### Option 2 — Manual Installation

1. Copy this repository into your Home Assistant `custom_components` directory  
2. Restart Home Assistant  
3. Add the integration via **Settings → Devices & Services → Add Integration**

---

## Region Codes

The integration automatically retrieves tariff codes from:

https://api.edfgb-kraken.energy/v1/products/EDF_FREEPHASE_DYNAMIC_12M_HH/


Each tariff code ends with a letter (A, B, C, … P) that corresponds to a UK DNO region.

For a clear explanation of these region letters, you can refer to:

**https://energy-stats.uk/dno-region-codes-explained/#UK_DNO_Region_Codes_A%E2%80%93P_List_and_Map**

This page provides a helpful breakdown of each region and its operator.

If the API is temporarily unavailable, the integration falls back to a complete static list of regions A–P (excluding I and O, which do not exist).

---

## Configuration Options

- **Region Code**  
  Select your region from the dynamically generated list.

- **Scan Interval (minutes)**  
  How often to refresh tariff data.  
  Default: 5 minutes.

- **Forecast Window (hours)**  
  How many hours of future pricing to fetch.  
  Default: 24 hours.

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

This is useful if you want to compare regions or monitor multiple properties.

---

## Troubleshooting

- If the region list only shows a few entries, the API may be temporarily unavailable.  
  The integration will fall back to a complete static list of regions A–P.

- If you previously added the integration before updating, removing and re‑adding it ensures the new dynamic region list is used.

- If tariff codes ever change in future, the integration will automatically detect the new prefix and continue working without modification.

---

## License

MIT License.  
Feel free to fork, improve, and contribute.