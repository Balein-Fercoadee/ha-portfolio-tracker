# Home Assistant Investment Portfolio

A custom Home Assistant integration that tracks manually configured investment holdings using Yahoo Finance quote data.

## Installation through HACS

1. In Home Assistant, open **HACS → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/Balein-Fercoadee/ha-portfolio-tracker` with category **Integration**.
4. Find **Investment Portfolio** in HACS and install it.
5. Restart Home Assistant, then add **Investment Portfolio** from **Settings → Devices & services → Add integration**.

HACS custom repositories install from the repository's default branch or published GitHub releases. Releases should use version tags matching the integration's `manifest.json` version.

## Manual installation

Copy `custom_components/portfolio_tracker` into the `custom_components` directory in your Home Assistant configuration directory, then restart Home Assistant.

## Setup and holdings

Add **Investment Portfolio** from **Settings → Devices & services → Add integration**. Choose a three-letter portfolio currency and enter one holding per line in `SYMBOL,QUANTITY` format, for example:

```text
AAPL,10
MSFT,2.5
```

Use the integration's options to add, edit, or remove holdings. Leave the holdings list empty to keep the portfolio configured without holdings; its total value sensor will be unavailable. Each holding must have a unique symbol and a positive quantity.

The integration creates a price and market-value sensor for each holding, along with a total portfolio value sensor. Values are reported in the selected portfolio currency. Quotes reported in a different currency are unavailable and are not included in the total.

## Quote limitations

Quotes are fetched from Yahoo Finance on a 30-minute schedule. Yahoo Finance's quote endpoint is unofficial and may be delayed, unavailable, or subject to change or throttling. This integration does not connect to broker accounts and is not intended for trading or real-time pricing.

## Tests

With Home Assistant and pytest installed in your Python environment, run:

```powershell
python -m pytest -p no:sugar --force-enable-socket
```

The test fixtures use local sockets for Home Assistant's test server. Yahoo Finance calls are mocked and tests do not fetch live quotes.
