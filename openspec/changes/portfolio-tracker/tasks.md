# Tasks

## 1. Home Assistant Integration Foundation

- [x] 1.1 Create the Python custom integration scaffold, manifest, and required Home Assistant metadata; verify Home Assistant recognizes the integration.
- [x] 1.2 Implement authenticated, administrator-only backend commands to add and remove validated holdings, persist them in config-entry options while preserving the portfolio currency, and test authorization, validation, and persistence.
- [x] 1.3 Build and register a dedicated Home Assistant frontend panel, package its assets with the integration, and provide symbol/amount entry with plus-to-add and per-row minus-to-remove actions; verify the frontend build and interaction tests.

## 2. Yahoo Finance Data and Valuation

- [x] 2.1 Implement an asynchronous Yahoo Finance quote adapter using Home Assistant's shared HTTP session; add mocked-response tests for valid, malformed, missing, and mismatched-currency quotes.
- [x] 2.2 Implement shared coordinator refresh and per-holding and total-value calculations; add tests proving the total is unavailable when any holding lacks a usable quote.

## 3. Home Assistant Entities

- [x] 3.1 Add per-holding price and market-value sensors and a total portfolio sensor with stable unique IDs and currency metadata; add tests for sensor values, attributes, and availability on refresh failures.
- [x] 3.2 Handle holding changes made through the custom panel, including removal and integration reload without duplicate requests or stale entities; test that sensors and totals update and the total is unavailable when all holdings are removed.

## 4. Documentation and Integration Verification

- [x] 4.1 Add HACS repository metadata and document custom-repository installation, initial setup, using the portfolio panel to add and remove holdings, quote limitations, and single-currency behavior; verify the steps match the packaged panel and config flow.
- [ ] 4.2 Run unit, Home Assistant integration, and frontend build/interaction tests without live Yahoo Finance requests, validate the integration manifest and release version metadata, and run HACS validation in CI; verify the portfolio panel and HACS custom-repository requirements.
