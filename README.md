# ha-edf-freephase-dynamic-tariff

EDF FreePhase Dynamic Tariff — Home Assistant Integration

![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)
![Version](https://img.shields.io/github/v/release/jswilkinson851/ha-edf-freephase-dynamic-tariff)
![License](https://img.shields.io/github/license/jswilkinson851/ha-edf-freephase-dynamic-tariff)

This custom integration brings EDF’s FreePhase Dynamic 12‑month tariff into Home Assistant, giving you live pricing, colour‑coded slot classification, and a full 24‑hour forecast directly from the EDF Kraken API.

It’s designed for UK users on the FreePhase tariff who want deeper insight into when electricity is cheapest, most expensive, or completely free.

✨ Features
Live current price updated automatically

Next slot price (the upcoming 30‑minute period)

Full 24‑hour forecast (48 half‑hour slots)

Cheapest and most expensive slots

Next green, amber, and red slots

Current slot colour (green/amber/red)

Binary sensor for “Is it green right now?”

Device grouping for a clean Home Assistant UI

Automatic slot classification based on EDF’s schedule and negative wholesale prices

📦 Installation
Manual installation
Download or clone this repository.

Copy the folder:

Code
custom_components/edf_freephase_dynamic_tariff
into your Home Assistant custom_components directory.

Restart Home Assistant.

Go to Settings → Devices & Services → Add Integration.

Search for EDF FreePhase Dynamic Tariff.

Select your tariff code from the dropdown and choose your scan interval.

⚙️ Configuration
When adding the integration, you’ll be asked for:

Tariff Code  
Pulled live from the EDF API (e.g., E-1R-EDF_FREEPHASE_DYNAMIC_12M_HH-A)

Scan Interval (minutes)  
How often to refresh pricing (default: 30 minutes)

No API keys or authentication are required.

🧠 How slot classification works
Each half‑hour slot is assigned a colour:

Green — free or overnight

Amber — daytime or evening

Red — peak (16:00–19:00)

Negative wholesale prices automatically count as green.

🗂️ Entities created
You’ll get the following sensors:

Current price

Next slot price

24‑hour forecast

Cheapest slot

Most expensive slot

Next green slot

Next amber slot

Next red slot

Current slot colour

Binary sensor: Is now a green slot?

Each sensor includes useful attributes such as start time, end time, value, and phase.

🧪 Known limitations
This integration currently supports single‑register electricity tariffs only.

Pricing is pulled directly from the EDF Kraken API; outages or changes in structure may affect availability.

No standing charge data is included yet (planned).

🤝 Contributing
Pull requests, issues, and suggestions are always welcome.
If you’re using this integration and want to help improve it, feel free to open an issue or PR.

📄 License
This project is licensed under the MIT License.
