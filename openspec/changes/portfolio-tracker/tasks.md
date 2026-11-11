# Tasks

## 1. Home Assistant Integration Foundation

- [x] 1.1 Create the Python custom integration scaffold, manifest, and required Home Assistant metadata; verify Home Assistant recognizes the integration.
- [x] 1.2 Implement config-entry setup and an options flow to add, edit, and remove symbols with positive quantities and one portfolio currency; test valid setup, invalid or duplicate holdings, and allowing all holdings to be removed.

## 2. Yahoo Finance Data and Valuation

- [x] 2.1 Implement an asynchronous Yahoo Finance quote adapter using Home Assistant's shared HTTP session; add mocked-response tests for valid, malformed, missing, and mismatched-currency quotes.
- [x] 2.2 Implement shared coordinator refresh and per-holding and total-value calculations; add tests proving the total is unavailable when any holding lacks a usable quote.

## 3. Home Assistant Entities

- [x] 3.1 Add per-holding price and market-value sensors and a total portfolio sensor with stable unique IDs and currency metadata; add tests for sensor values, attributes, and availability on refresh failures.
- [x] 3.2 Handle config option changes, including holding removal, and integration unload/reload without duplicate requests or stale entities; test sensor removal, updated totals, and an unavailable total for an empty portfolio.

## 4. Documentation and Integration Verification

- [x] 4.1 Add HACS repository metadata and document adding this GitHub repository as a HACS custom integration, installing/updating it, setup, supported configuration, quote limitations, and single-currency behavior; verify the documented steps match the repository structure and config flow.
- [ ] 4.2 Run unit and Home Assistant integration tests without live Yahoo Finance requests, validate the integration manifest and release version metadata, and run HACS validation in CI; verify all portfolio and HACS installation requirements pass.
