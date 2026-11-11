# Proposal

## Why

Home Assistant users need a way to monitor the market value of investment holdings alongside their other home data. This change introduces a Python-based Home Assistant integration that values manually configured holdings using Yahoo Finance prices, without requiring users to connect broker accounts.

## What Changes

- Add a dedicated Home Assistant frontend panel for managing holdings. Users enter a symbol and amount and activate a plus-sign action to add it to the visible list; each listed holding has a minus-sign action to remove it. To change a holding, remove it and add the updated symbol and amount.
- Retrieve current prices from Yahoo Finance and expose per-holding and combined portfolio value in Home Assistant.
- Package and document the integration for installation and updates through HACS as a custom repository.
- Keep the initial portfolio in one currency; mixed-currency conversion and broker account synchronization are out of scope.

## Capabilities

### New Capabilities

- `investment-portfolio`: Configure investment holdings and monitor their prices and market values in Home Assistant.

### Modified Capabilities

- None.

## Impact

- Adds a Python custom integration for Home Assistant, including configuration, data retrieval, entities, an integration-specific frontend panel, its authenticated backend interface, and tests.
- Packages the frontend with the integration so it works without an externally hosted UI.
- Adds HACS repository metadata and community-store installation documentation; users add the GitHub repository as a custom HACS repository.
- Depends on Yahoo Finance price availability and must account for its limits and possible service changes.
- The repository currently contains no integration code or existing capability specs; implementation conventions and compatibility targets will need to be established during design.
- Official inclusion in Home Assistant Core or HACS default-store listing is not part of this change.
