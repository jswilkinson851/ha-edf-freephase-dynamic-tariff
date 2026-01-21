# 📚 EDF FreePhase Dynamic Tariff — Example Packs

This directory contains optional example files that show how to get the most out of the **EDF FreePhase Dynamic Tariff** integration.  
They are completely optional, but they’re a great way to explore what’s possible with the tariff data, cost engine, and your wider Home Assistant setup.

Examples are grouped into two categories:

- **Automations** — practical, ready‑to‑use YAML automations  
- **Dashboards** — Lovelace cards and UI ideas for visualising tariff and cost data  

Each example is self‑contained, documented, and easy to adapt to your own system.

---

## 📂 Folder Structure

### **`automations/`**
A collection of real‑world automations that react to tariff changes, send daily summaries, or optimise energy usage.

Examples include:
- Daily energy summaries  
- Tomorrow’s price breakdown notifications  
- Green‑slot‑only control  
- Pre‑heat before red periods  
- Cheapest‑slot scheduling  

Each file includes:
- A short description  
- Required sensors  
- Notes or tips  
- A clean YAML block  

Browse automations:  
`/examples/automations`

---

### **`dashboards/`**
Lovelace cards and dashboard layouts that help you visualise:
- Current and next slot  
- Phase windows  
- Cost today/yesterday  
- Cheapest/most expensive slots  
- Coordinator health and diagnostics  

These examples are ideal for:
- Energy dashboards  
- Wall tablets  
- Mobile views  
- Quick‑glance summaries  

Browse dashboards:  
`/examples/dashboards`

---

## 🧩 How to Use These Examples

1. Open any file in the `automations` or `dashboards` folder.  
2. Adjust entity IDs to match your setup (solar sensors, import meters, etc.).  
3. Paste the YAML into Home Assistant:
   - **Automations:** Settings → Automations → Add → Edit in YAML  
   - **Dashboards:** Edit Dashboard → Add Card → Manual  
4. Save and customise as needed.

All examples are intentionally simple and easy to extend.

---

## 💡 Contributing Your Own Examples

If you create an automation or dashboard that others might find useful, feel free to open a pull request.  
Clear examples help everyone get more value from the integration.

---

## ⭐ Recommended Starting Points

If you’re new to the examples, start with:

- **Daily EDF FPD Energy Summary**  
- **Tomorrow’s Price Breakdown Notification**  
- **Green Slot Indicator Card**  

These give you a great feel for how the tariff data fits into your daily energy workflow.

---

Enjoy exploring — and feel free to adapt, remix, and build on these examples to suit your own home.
