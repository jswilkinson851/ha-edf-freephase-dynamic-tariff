
# EDF FreePhase Dynamic Tariff — Event Documentation (v0.6.0)

The integration exposes **two events**.  
Their behaviour is unchanged from earlier versions, but the system now includes richer metadata and more reliable scheduling.

---

# 🔹 Event 1: `edf_fpd_phase_changed`

Fires exactly when the tariff phase changes at a slot boundary.

Useful for:
- reacting to green/amber/red changes  
- adjusting energy usage  
- triggering notifications  

**Payload includes:**
- old_phase  
- new_phase  
- slot_start  
- slot_end  
- phase_start  
- phase_end  
- duration_minutes  
- price  
- unit  
- slot_index  

---

# 🔹 Event 2: `edf_fpd_new_forecast_available`

Fires when EDF publishes a new 48‑slot forecast.

**Payload includes:**
- effective_from  
- effective_to  
- slots  
- cheapest_slot  
- cheapest_price  
- most_expensive_slot  
- most_expensive_price  
- free_slots  

---

# Additional Notes for v0.6.0

- Events still fire even if the API is degraded — the coordinator uses fallback data.  
- Diagnostics now include metadata fields that may help developers.  
- CostCoordinator does not emit events but updates in sync with EDFCoordinator.

---