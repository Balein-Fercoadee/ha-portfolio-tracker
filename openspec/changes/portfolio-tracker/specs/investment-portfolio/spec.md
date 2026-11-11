# Spec Delta

## Purpose

Allows Home Assistant users to track manually configured investment holdings and their market value using Yahoo Finance price data.

## ADDED Requirements

### Requirement: Configure investment holdings
The integration MUST allow a user to configure one or more investment symbols and their positive holding quantities.

#### Scenario: Configure a holding
- **WHEN** a user configures a valid symbol and positive quantity
- **THEN** the holding is included in the portfolio

#### Scenario: Reject invalid quantity
- **WHEN** a user configures a holding with a zero, negative, or non-numeric quantity
- **THEN** the integration rejects that holding and reports a configuration error

### Requirement: Remove investment holdings
The integration MUST allow a user to remove a previously configured holding.

#### Scenario: Remove a holding
- **WHEN** a user removes a configured holding
- **THEN** the holding is removed from the active portfolio, its sensors are no longer provided, and the total reflects the remaining holdings

#### Scenario: Remove the final holding
- **WHEN** a user removes the last configured holding
- **THEN** the portfolio remains configured with no holdings and its total value is unavailable

### Requirement: Report holding price and market value
The integration MUST expose each configured holding's latest available Yahoo Finance price and calculated market value in Home Assistant.

#### Scenario: Price data is available
- **WHEN** a price is available for a configured holding
- **THEN** Home Assistant exposes that price and the holding's market value calculated as quantity multiplied by price

#### Scenario: Price data is unavailable
- **WHEN** the integration cannot retrieve a usable price for a configured holding
- **THEN** that holding's price and market value are reported as unavailable rather than as zero or a newly refreshed value

### Requirement: Report total portfolio value
The integration MUST expose a total portfolio market value calculated from the configured holdings in a single currency, or report it as unavailable when no holdings are configured.

#### Scenario: All holding prices are available
- **WHEN** each configured holding has a usable price in the portfolio currency
- **THEN** Home Assistant exposes the total as the sum of the configured holdings' market values

#### Scenario: A holding price is unavailable
- **WHEN** at least one configured holding has no usable price
- **THEN** the total portfolio value is reported as unavailable rather than as a partial total

#### Scenario: No holdings are configured
- **WHEN** the portfolio contains no configured holdings
- **THEN** the total portfolio value is reported as unavailable

### Requirement: Keep portfolio currency consistent
The integration MUST prevent a portfolio total from combining holding values denominated in different currencies.

#### Scenario: Configure a holding in a different currency
- **WHEN** a configured holding's price currency differs from the portfolio currency
- **THEN** the integration reports a configuration or data error and does not include that holding in a misleading total

### Requirement: Support HACS custom repository installation
The integration MUST provide the repository structure and metadata required for users to install and update it through HACS as a custom integration repository.

#### Scenario: Add the repository to HACS
- **WHEN** a user adds the project's GitHub repository to HACS as a custom integration repository
- **THEN** HACS recognizes the integration and offers it for installation

#### Scenario: Install or update through HACS
- **WHEN** a user installs or updates the integration through HACS
- **THEN** the integration files are placed in the expected `custom_components/portfolio_tracker` location and its Home Assistant manifest and release version metadata remain valid
