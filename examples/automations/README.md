# 📘 EDF FreePhase Dynamic Tariff — Automation Examples

This folder contains ready‑to‑use Home Assistant automations designed to help you get the most out of the **EDF FreePhase Dynamic Tariff** integration.

Each example focuses on a practical, real‑world use case and demonstrates how to combine tariff data with your existing Home Assistant setup (solar, batteries, heating, EV charging, etc.).

All examples are written in plain YAML so you can copy, adapt, and extend them however you like.

---

## 📂 What You’ll Find Here

### **Daily Summaries**
Automations that send a daily snapshot of your energy usage, cost, or tariff information.

- **Daily EDF FPD Energy Summary**  
  A combined cost, solar generation, and grid import summary sent at a fixed time each evening.

- **Tomorrow’s Price Breakdown Notification**  
  A friendly breakdown of tomorrow’s green/amber/red windows as soon as EDF publishes the next day’s rates.

---

### **Tariff‑Aware Control**
Automations that react to the tariff in real time.

- **Run During Green Slots**  
  Turn devices on only when the current slot is green.

- **Pre‑Heat Before a Red Period**  
  Start heating or charging before an expensive block begins.

- **Cheapest‑Slot Scheduling**  
  Trigger devices during the cheapest periods in the next 24 hours.

---

### **Advanced Examples (Optional)**
More complex automations inspired by tools like Predbat and GivTCP.

- **Overnight Cheapest‑Window Control**  
  Identify and run during the cheapest overnight slots.

- **Cost‑Optimised Load Shifting**  
  Combine tariff data with your import meter to minimise daily cost.

---

## 🧩 How to Use These Examples

1. Open any `.yaml` file in this folder.  
2. Replace the `notify.*` service with your own notification target.  
3. Adjust entity IDs to match your setup (solar sensors, import meters, etc.).  
4. Paste the automation into **Settings → Automations & Scenes → Add Automation → Edit in YAML**.  
5. Save and enjoy.

Each file includes:
- A short description  
- Required sensors  
- Notes or tips  
- The full YAML block  

---

## 💡 Want to Contribute?

If you create an automation you think others would find useful, feel free to open a pull request.  
Clear examples help everyone get more value from the integration.

---

## 📄 Related Example Packs

You may also want to explore:

- `/examples/dashboards` — Lovelace cards and dashboards  
- `/examples/blueprints` — Reusable automation blueprints (optional)

---

If you’re browsing this folder for the first time, a great place to start is:

**Daily EDF FPD Energy Summary**  
and  
**Tomorrow’s Price Breakdown Notification**

They’re simple, practical, and show off the integration’s strengths beautifully.
