# Design

## Context

See proposal.md for motivation and specs/investment-portfolio/spec.md for user-visible requirements. The repository has no existing integration code or conventions to extend, so the first implementation establishes the custom integration structure and its tests.

## Goals / Non-Goals

**Goals:**
- Follow Home Assistant's config-entry integration patterns and keep network I/O asynchronous.
- Separate Yahoo Finance retrieval and validation from portfolio calculations and entity presentation.
- Make current data freshness and provider failures visible instead of presenting stale values as refreshed.

**Non-Goals:**
- Broker account connections, transaction history, cost basis, or profit/loss reporting.
- Currency conversion or portfolio totals spanning multiple currencies.
- User-configurable provider credentials.
- Inclusion in Home Assistant Core or HACS's default store.

## Decisions

- **Implement a Home Assistant config-entry integration in Python.** A config flow creates a portfolio entry, and its options flow manages the configured symbols, quantities, and portfolio currency. This provides a native UI instead of requiring YAML configuration. A separate standalone service or command-line tool would not integrate as naturally with Home Assistant entity lifecycle and configuration.
- **Use a shared `DataUpdateCoordinator` for quote retrieval and portfolio calculations.** Fetch configured symbols on a bounded polling interval, validate returned quote values and currencies, and calculate per-holding and total market values centrally. Sensors consume the same coordinator data to avoid redundant requests. Home Assistant's entity availability reflects failed or incomplete quote refreshes; a failed refresh must not masquerade as fresh data. Independent sensor-level polling was rejected because it can duplicate requests and produce inconsistent totals.
- **Isolate Yahoo Finance access behind a small asynchronous provider adapter using Home Assistant's shared HTTP session.** Do not block the event loop or introduce a synchronous price-fetching dependency. Keep response parsing and validation in the adapter so provider changes do not affect calculations or entities. Yahoo Finance does not provide a stable, supported public portfolio API, and its quote interfaces may change or throttle requests; no broker holdings will be fetched.
- **Expose one price and market-value sensor per configured symbol, plus a total portfolio value sensor.** Include symbol, quantity, and currency as entity attributes where applicable. Use stable entity unique IDs derived from the config entry and symbol so reloads preserve entity identity. A single-currency portfolio is selected at setup; quotes in another currency are treated as invalid for valuation, not converted.
- **Test without live Yahoo Finance requests.** Unit tests cover quote parsing, invalid or missing prices, currency mismatches, and value calculations using recorded/mock responses. Integration tests cover configuration, options updates, sensor availability, and coordinator refresh behavior.
- **Distribute as a HACS custom integration repository.** Keep the integration under `custom_components/portfolio_tracker`, include HACS repository metadata and a valid Home Assistant integration manifest, and document adding this GitHub repository through HACS's custom-repository flow. Align version metadata with GitHub releases and run HACS validation in CI. HACS default-store listing and Home Assistant Core review are separate processes and are not promised by repository compatibility.

## Risks / Trade-offs

- [Yahoo Finance endpoints are unofficial and may change or throttle traffic] -> Isolate the client, validate responses, handle provider errors explicitly, and test with mocked responses; disclose that values depend on provider availability.
- [Polling may increase request volume as the portfolio grows] -> Fetch symbols through a shared coordinator at a conservative fixed interval and avoid per-entity requests.
- [Quotes may be delayed or reflect a prior market close] -> Expose the provider's latest available quote and update timestamp where available; do not imply real-time execution pricing.
- [A quote currency may differ from the selected portfolio currency] -> Refuse to include an incompatible quote in a total rather than silently combining currencies.

## Migration Plan

This is a new integration with no existing user configuration to migrate. Install and configure it through Home Assistant, then remove the config entry to roll back; removing it also removes its entities.
