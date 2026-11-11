# Spec Delta

## Purpose

Allows Home Assistant users to track manually configured investment holdings and their market value using Yahoo Finance price data.

## ADDED Requirements

### Requirement: Configure investment holdings

The integration MUST provide symbol and amount fields and a plus-sign action to add a valid holding to a visible list of configured holdings.

#### Scenario: Add a holding

- **WHEN** a user enters a valid symbol and positive amount and activates the plus-sign action
- **THEN** the symbol and amount appear as a holding in the list below the entry fields and are included in the portfolio

#### Scenario: Reject invalid quantity

- **WHEN** a user enters a holding with a zero, negative, or non-numeric amount and activates the plus-sign action
- **THEN** the integration rejects the holding and reports a configuration error

### Requirement: Access portfolio management panel

The integration MUST provide an authorized Home Assistant frontend panel for managing portfolio holdings. The panel MUST display configured holdings as symbol and amount pairs and provide fields to enter another pair.

#### Scenario: Open the portfolio management panel

- **WHEN** an authorized Home Assistant user opens the Investment Portfolio panel
- **THEN** the panel displays the configured holding symbol and amount pairs and provides fields to enter another pair

### Requirement: Add and remove holdings in the integration panel

The panel MUST provide a plus-sign action to add a valid holding and a minus-sign action on each listed holding to remove it. Changes MUST be validated and persisted so the integration's entities reflect the updated holdings. To modify a holding, the user removes it and adds the updated pair.

#### Scenario: Add a holding through the panel

- **WHEN** an authorized user enters a valid, unique symbol and positive amount and activates the plus-sign action
- **THEN** the pair appears in the holdings list, is persisted, and is included in the portfolio

#### Scenario: Reject invalid or duplicate panel input

- **WHEN** a user submits a non-positive or non-numeric amount, an invalid symbol, or a duplicate symbol
- **THEN** the panel reports the validation error and leaves the configured holdings unchanged

#### Scenario: Remove a holding through the panel

- **WHEN** an authorized user activates the minus-sign action for a listed holding
- **THEN** the pair is removed from the list and persisted, its sensors are no longer provided, and the total reflects the remaining holdings

#### Scenario: Modify a holding through the panel

- **WHEN** a user wants to change a holding's symbol or amount
- **THEN** the user removes the existing pair with its minus-sign action and adds the updated pair with the plus-sign action

#### Scenario: Remove the final holding through the panel

- **WHEN** a user removes the last holding from the panel list
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
