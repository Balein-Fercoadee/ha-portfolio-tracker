# Home Assistant Investment Portfolio

[![Tests](https://github.com/Balein-Fercoadee/ha-portfolio-tracker/actions/workflows/validate.yml/badge.svg)](https://github.com/Balein-Fercoadee/ha-portfolio-tracker/actions/workflows/validate.yml)

A custom Home Assistant integration that tracks manually configured investment holdings using Yahoo Finance quote data.

The idea is to have the integration pull the data and have it available for the user to display as they see fit.

## Installation through HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/Balein-Fercoadee/ha-portfolio-tracker` with category **Integration**.
4. Find **Investment Portfolio** in HACS and install it.
5. Restart Home Assistant, then add **Investment Portfolio** from **Settings → Devices & services → Add integration**.

HACS custom repositories install from the repository's default branch or published GitHub releases. Releases should use version tags matching the integration's `manifest.json` version.

## Manual installation

Copy `custom_components/portfolio_tracker` into the `custom_components` directory in your Home Assistant configuration directory, then restart Home Assistant.

## Setup and holdings management

Add **Investment Portfolio** from **Settings → Devices & services → Add integration**. Choose a three-letter portfolio currency (ex 'USD') and enter at least one initial holding per line in `SYMBOL,QUANTITY` format, for example:

```text
AAPL,10
```

The portfolio currency is used only for context and is not actually validated against actual currency symbols.

After setup, open **Investment Portfolio** from the Home Assistant sidebar. From there you can add more symbol/quantity pairs, as well as the update frequency.

To add: Enter a symbol and quantity, then click **+** to add it.

Rules for adding holdings:

- Symbol cannot be blank.
- Symbol must not already be tracked.
- Quantity cannot be blank.
- Quantity must be numeric.
- Quantity must be greater than 0.

To remove: Click **-** next to the listing you want to remove.

For each holding a price and market-value sensor is created when saved. The total portfolio value sensor is updated at this time as well.

## Quote limitations

Quotes are fetched from Yahoo Finance on a 30-minute schedule (defualt time that can be changed). Yahoo Finance's quote endpoint is unofficial and may be delayed, unavailable, or subject to change or throttling. This integration does not connect to broker accounts and is not intended for trading or real-time pricing.

## Uses

Once holdings have been added, next step is to do something useful with the data. Included is a [simple example](examples/portfolio-overview.yaml) of what to do with the sensors in a HA card.

See the [sensor entity schema](docs/sensor-schema.md) for available values and attributes.

## Tests

With Home Assistant and pytest installed in your Python environment, run:

```powershell
python -m pytest -p no:sugar --force-enable-socket
```

The test fixtures use local sockets for Home Assistant's test server. Yahoo Finance calls are mocked and tests do not fetch live quotes.
