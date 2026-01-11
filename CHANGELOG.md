# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.3.7.1] — 2026-01-11 (hotfix release)

### 🛠 Fixes & Improvements

- Corrected aligned scheduling logic to ensure refreshes occur exactly on the next boundary.
- Fixed timing issue where the "Next Refresh Time" sensor displayed the previous boundary instead of the upcoming one.
- Added `async_update_listeners()` to ensure metadata sensors update immediately after boundary advancement.
- Replaced unsafe `async_create_task` usage with proper async callback handling via `async_call_later`.
- Eliminated Home Assistant warnings about thread safety and un-awaited coroutines.
- Improved stability and predictability of the 2‑minute aligned refresh cycle.
- Enhanced debug sensor accuracy by switching from `_next_refresh_datetime` to `_next_boundary_utc`.

### 📦 Notes

This release contains **no breaking changes** and is safe for all users to install.  
Recommended for anyone running v0.3.7, as it resolves several timing and async‑related issues.

---

## [0.3.7] — 2026‑01‑11

### Added
- **Aligned scheduling** for API polling. Refreshes now occur on precise wall‑clock boundaries based on the configured scan interval (e.g., every 5 minutes at :00, :05, :10, etc.).
- **Random jitter** (0–5 seconds) added to each refresh to reduce simultaneous API hits across multiple Home Assistant instances.
- **New debug sensor**: `sensor.edf_freephase_dynamic_next_refresh_time`, exposing:
  - Next scheduled refresh time (local timezone)
  - UTC timestamp of the next refresh
  - Seconds until refresh
  - Jitter applied
  - Configured scan interval

### Changed
- Coordinator now manages its own refresh cycle instead of relying on `update_interval`.
- Improved logging around refresh timing and scheduling behaviour.

### Notes
- No breaking changes.
- All existing sensors continue to function normally.

---

## [0.3.6] — 2026-01-11

### Changed
- Refactored the root `__init__.py` to follow modern Home Assistant integration architecture.
- Moved `EDFCoordinator` creation into `async_setup_entry`, ensuring a single coordinator instance per config entry.
- Coordinator is now stored under `hass.data[DOMAIN][entry.entry_id]` for shared access across platforms.
- Added an update listener so changes made in the Options Flow (e.g., region or scan interval) trigger a clean integration reload.
- Ensured the coordinator performs its initial refresh before sensor entities are created, improving startup reliability.
- Improved unload behaviour by removing coordinator data from `hass.data` and unloading platforms cleanly.

### Notes
- These changes affect internal architecture only; no breaking changes for users.
- All existing sensors continue to function normally, now backed by a more robust and maintainable setup flow.

---

## [0.3.5] – 2026-01-09
- **Enhanced setup and options flows** with Home Assistant–native selectors for region, scan interval, and import sensor.
- **Added number selector** for *Scan Interval (minutes)*, providing both slider and free‑text input for improved usability.
- **Implemented alphabetical region ordering** for a cleaner, more intuitive dropdown experience.
- **Moved all field labels to translation files**, ensuring consistent, localised UI text across setup and options flows.
- **Refactored config flow schema** to align with Home Assistant’s selector requirements, resolving previous 400/500 errors.
- **Improved internal region‑mapping logic**, ensuring reliable fallback behaviour when the EDF API is unavailable.
- General code cleanup and structural improvements for long‑term maintainability.

---

## [0.3.4] — 2026‑01‑06
### Added
- Unified slot dataset (`all_slots_sorted`) used consistently across all sensors.
- Clean, merged daily summaries for today and tomorrow with consistent formatting.
- Improved dashboard‑friendly attributes for Lovelace and ApexCharts.

### Changed
- Reworked next‑block detection to correctly identify the next *different* colour block.
- Updated block‑merging logic to expand forward until the phase changes.
- Normalised phase comparisons using `.lower()` for consistent behaviour.
- Replaced string‑based datetime sorting with `start_dt` everywhere.
- Improved internal readability and maintainability across sensor modules.

### Fixed
- Corrected next‑block logic that previously returned the current block instead of the next one.
- Prevented tomorrow’s early‑morning slots from leaking into today’s summary.
- Fixed inconsistent sorting of slots and blocks across sensors.
- Resolved mismatches between slot‑based and block‑based sensors.
- Fixed inconsistent formatting of start, end, duration, and price attributes.
- Ensured all sensors attach to the same device via `edf_device_info()`.

### Documentation
- README updated to reflect the new unified data model and sensor behaviour.
- Improved examples for daily summaries and block‑based dashboards.

### Summary
This release stabilises the integration, corrects several subtle logic issues, and ensures all sensors behave consistently using the unified slot dataset. It lays a clean foundation for future enhancements.

---

## [0.3.3] — 2026‑01‑05
### Added
- New full‑day pricing model with coordinator outputs:
  - `todays_24_hours`
  - `tomorrow_24_hours`
- Full‑day sensors:
  - `sensor.todays_rates_full`
  - `sensor.tomorrows_rates_full`
- Updated summary sensors for today and tomorrow using the new data model.
- Updated pricing sensors (cheapest slot, most expensive slot, next slot price).
- Updated slot/block sensors (current slot colour, current block summary, next block summary, next green/amber/red slot, is‑green‑slot binary).

### Changed
- Replaced the rolling 24‑hour forecast model with a predictable full‑day structure aligned with EDF’s API.
- All sensors now use the new full‑day dataset and load cleanly without `unknown` states.
- Improved duration handling and timestamp formatting.
- Coordinator behaviour made more predictable and consistent.
- Documentation updated to reflect the new data model and sensor structure.
- ApexCharts examples updated for full‑day sensors.

### Removed
- Rolling 24‑hour forecast model.
- `forecast.py` module.
- Forecast window configuration option.
- `sensor.24_hour_forecast`.
- All references to `next_24_hours`.

### Fixed
- Import errors and incorrect module references.
- Issues caused by deprecated forecast logic.
- Inconsistencies in duration and timestamp formatting.

### Documentation
- README fully updated.
- Removed references to forecast windows.
- Added full‑day sensor documentation.
- Clarified behaviour and internal data model.

### Upgrade Notes
- Users of the old forecast sensor should update dashboards to use the new full‑day sensors.
- If the region list appears incomplete, remove and re‑add the integration to refresh dynamic region detection.
- No configuration changes required unless the forecast window option was previously used.

---

## [0.3.2] — 2026‑01‑05
### Added
- `last_successful_update` sensor providing timestamp of the most recent successful API fetch.
- `data_age` sensor showing how long ago the last successful update occurred.

### Changed
- Coordinator now includes automatic retry and backoff logic to reduce transient API failures.
- Improved fallback behaviour: if all retries fail, the integration uses the last successful data instead of going `unavailable`.
- Updated `coordinator_status` values to provide clearer diagnostics:
  - `ok` – fresh data retrieved
  - `degraded` – using cached data
  - `error` – no valid data available
- Updated health sensors (`api_latency`, `last_updated`, `coordinator_status`) for richer diagnostics.
- Improved consistency across forecast, price, slot, and rate sensors.
- Updated `sensors/__init__.py` to correctly map all sensor classes.

### Fixed
- Corrected all sensor imports and class names to prevent startup errors.
- Ensured clean initialisation with no missing‑sensor or import issues.
- Improved handling of missing or stale data.
- More robust timestamp formatting and safer error handling.

### Documentation
- README expanded with:
  - Full sensor list
  - Health & diagnostics section
  - Example Health Panel
  - Updated feature list
- Improved dashboard examples and formatting.

### General Improvements
- Better error logging for API failures and coordinator behaviour.
- Cleaner internal structure to support future development.

### Upgrade Notes
- Restart Home Assistant after updating to ensure new sensors and coordinator behaviour load correctly.

---

## [0.3.1] — 2026‑01‑05
### Added
- Dynamic tariff code detection using live data from the Kraken API.
- Automatic extraction of the region letter from the final character of each tariff code.
- Full fallback list for all Ofgem DNO regions (A–P, excluding I and O).
- Human‑friendly region labels (e.g., “Region A: Eastern England”).
- New configuration options:
  - Region Code (dropdown)
  - Scan Interval (minutes)
  - Forecast Window (hours)
  - Include Past Slots

### Changed
- Config flow updated to support new dynamic region detection and additional setup fields.
- Reconfigure flow updated to match new configuration options.
- Added User‑Agent header to improve API reliability.
- Translations updated (`en.json`, `en-GB.json`, `strings.json`) to reflect new fields and descriptions.
- README updated with HACS‑friendly formatting, badges, installation steps, and region‑code documentation.

### Fixed
- Improved fallback behaviour when the API is unavailable.
- Ensured region dropdown always displays the full A–P region list.
- Corrected several translation and formatting inconsistencies.

### Testing Notes
- Verified dynamic tariff code retrieval.
- Confirmed fallback region behaviour.
- Confirmed multiple instances work as separate devices.
- Verified translations and README formatting.

### Summary
This update improves robustness, simplifies configuration, and ensures long‑term compatibility even if EDF updates their tariff code structure.


---

## [0.3.0] — 2026‑01‑05
### Added
- New merged rate summary sensors for **today** and **tomorrow**, grouping half‑hour slots into colour‑based blocks.
- Each merged block now includes start time, end time, duration, colour, price, and icon.
- Coordinator now extracts tomorrow’s full 24‑hour slot data directly from the EDF API.
- New `coordinator_status` diagnostic sensor reporting `ok` or `error` states.

### Changed
- Coordinator architecture significantly enhanced for stability and resilience.
- API calls wrapped in robust error‑handling with graceful fallback behaviour.
- Improved logging for API failures, latency, and retry behaviour.
- Modularised sensor layout for improved readability and maintainability.
- Updated `manifest.json` and `hacs.json` for better HACS compatibility.
- Documentation links and metadata cleaned up.

### Fixed
- Resolved issue where sensors could become permanently `Unavailable` after API errors.
- Corrected tomorrow’s date calculation.
- Improved slot classification consistency across sensors.
- Fixed several internal references and imports.

### Documentation
- README fully rewritten with clearer installation steps.
- Updated sensor descriptions and examples.
- Improved explanation of merged block summaries and diagnostics.

### Upgrade Notes
- No breaking changes.
- Existing configurations continue to work without modification.
- Home Assistant restart recommended after updating.

---

## [Unreleased]

- Future improvements will be tracked here.

