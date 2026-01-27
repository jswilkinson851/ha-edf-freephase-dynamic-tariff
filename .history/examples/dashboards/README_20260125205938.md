# 📊 EDF FreePhase Dynamic Tariff — Dashboard Examples

This folder contains Lovelace dashboard examples designed to help you visualise
the EDF FreePhase Dynamic tariff, cost engine, and diagnostic data in a clear,
actionable way.

These dashboards are optional, but they provide an excellent starting point for
building your own energy‑aware Home Assistant UI.

---

## 📂 Included Dashboards

### **overall_dashboard.yaml**
A full, multi‑section dashboard that brings together:

- Coordinator health and diagnostic metadata  
- Current and next tariff slot information  
- Phase windows and block summaries  
- Cheapest and most expensive slots in the next 24 hours  
- Daily summaries (yesterday, today, tomorrow)  
- Cost and consumption breakdowns (by phase and by slot)  
- Live scheduler timing (refresh delay, jitter, next refresh)  
- Debug logging controls  
- Advanced diagnostic attributes  

This is the most complete view of the integration and works beautifully on
tablets, desktops, or wall‑mounted displays.

---

## 🧩 How to Use These Dashboards

1. Open any `.yaml` file in this folder.  
2. Copy the contents.  
3. In Home Assistant, go to:  
   **Settings → Dashboards → ⋮ → Edit Dashboard → Raw Configuration Editor**  
4. Paste the YAML into a new view or a new dashboard.  
5. Save and adjust entity IDs if needed.

Most dashboards rely on:
- `sensor.diagnostic_sensor`  
- `sensor.coordinator_status`  
- `sensor.cost_coordinator_status`  
- Tariff and cost sensors from the integration  

If you have renamed entities, update them accordingly.

---

## 💡 Tips for Customisation

- You can rearrange sections or collapse them using `expander-card`.  
- Add your own solar, battery, or EV sensors to extend the dashboard.  
- Combine this with your `/automations` examples for a full energy workflow.  
- Screenshots can be added to `/examples/screenshots` if you want to showcase layouts.

---

## 🤝 Contributing

If you create a dashboard layout that others might find useful, feel free to
open a pull request. Clear visual examples help everyone get more value from
the integration.

---

Enjoy exploring — and feel free to adapt these dashboards to suit your own
energy setup and Home Assistant style.
