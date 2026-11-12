# Sensor entity schema

The integration creates one total-value sensor per portfolio and two sensors
per holding: price and market value. All belong to the portfolio's
**Investment Portfolio** device.

Entity IDs below are examples, not guaranteed names. Home Assistant generates
entity IDs and allows users to change them; find the actual IDs under
**Developer Tools > States**. The integration's unique IDs are separate from
the entity IDs.

## Common properties

| Property | Value |
| --- | --- |
| Domain | `sensor` |
| Device class | `monetary` |
| Unit of measurement | Configured portfolio currency, such as `USD` |
| Suggested display precision | 2 decimal places |
| Native value | A number when available; Home Assistant exposes entity states as strings |

The configured currency is not converted. A quote in another currency cannot
be used to value a holding.

## Holding price

One sensor per configured holding reports the latest usable quote price per
unit.

| Property | Schema |
| --- | --- |
| Example entity ID | `sensor.investment_portfolio_aapl_price` |
| Entity name | `<SYMBOL> Price` |
| Unique ID | `<config_entry_id>_<lowercase_symbol>_price` |
| State | Quote price as a number, or `unavailable` |
| State class | None |

### Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `symbol` | string | Configured symbol, normalized to uppercase. |
| `quantity` | string | Configured quantity, represented as a decimal string. |
| `currency` | string | Quote currency if a quote exists; otherwise the configured portfolio currency. |
| `quote_updated_at` | string, optional | Quote timestamp in ISO 8601 format. Omitted if the source did not provide a usable timestamp. |

The sensor is unavailable if its quote is missing, its quote currency differs
from the portfolio currency, or the coordinator is unavailable. The quote
timestamp is the source's quote time, not necessarily the latest refresh time.

## Holding market value

One sensor per configured holding reports the value of the holding.

| Property | Schema |
| --- | --- |
| Example entity ID | `sensor.investment_portfolio_aapl_market_value` |
| Entity name | `<SYMBOL> Market Value` |
| Unique ID | `<config_entry_id>_<lowercase_symbol>_market_value` |
| State | Quote price multiplied by configured quantity, or `unavailable` |
| State class | `total` |

This sensor has the same `symbol`, `quantity`, `currency`, and optional
`quote_updated_at` attributes and the same availability conditions as the
holding price sensor.

## Portfolio total value

One sensor per portfolio reports the sum of all holding market values.

| Property | Schema |
| --- | --- |
| Example entity ID | `sensor.investment_portfolio_total_value` |
| Entity name | `Total Value` |
| Unique ID | `<config_entry_id>_total_value` |
| State | Sum of all holding market values, or `unavailable` |
| State class | `total` |

### Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `currency` | string | Configured portfolio currency. |
| `holding_count` | integer | Number of configured holdings. |

The total is unavailable when there are no holdings, any holding lacks a
usable quote, any quote has a different currency from the portfolio, or the
coordinator is unavailable. It is not a partial total.

## Accessing sensor values in Home Assistant YAML

The following built-in Markdown card reads the state of each sensor with
`states()` and its attributes with `state_attr()`. Paste it into a dashboard's
**Manual card editor** and replace the example entity IDs with your own.

```yaml
type: markdown
title: Portfolio sensor example
content: |
  {% set total_entity = 'sensor.investment_portfolio_total_value' %}
  {% set price_entity = 'sensor.investment_portfolio_aapl_price' %}
  {% set value_entity = 'sensor.investment_portfolio_aapl_market_value' %}
  {% set total = states(total_entity) %}
  {% set price = states(price_entity) %}
  {% set value = states(value_entity) %}
  {% set symbol = state_attr(price_entity, 'symbol') %}
  {% set quantity = state_attr(price_entity, 'quantity') %}
  {% set quote_currency = state_attr(price_entity, 'currency') %}
  {% set quote_time = state_attr(price_entity, 'quote_updated_at') %}
  {% set portfolio_currency = state_attr(total_entity, 'currency') %}
  {% set holding_count = state_attr(total_entity, 'holding_count') %}

  **Portfolio total:** {{ total if is_number(total) else 'Unavailable' }}
  {{ portfolio_currency if portfolio_currency is not none else '' }}

  **Holding count:** {{ holding_count if holding_count is not none else 'Unavailable' }}

  **Symbol:** {{ symbol if symbol is not none else 'Unavailable' }}

  **Quantity:** {{ quantity if quantity is not none else 'Unavailable' }}

  **Price:** {{ price if is_number(price) else 'Unavailable' }}
  {{ quote_currency if quote_currency is not none else '' }}

  **Market value:** {{ value if is_number(value) else 'Unavailable' }}
  {{ portfolio_currency if portfolio_currency is not none else '' }}

  **Quote timestamp:** {{ quote_time if quote_time is not none else 'Unavailable' }}

  **Allocation:** {% if is_number(value) and is_number(total) and (total | float) > 0 %}
  {{ '{:.1f}'.format((value | float) / (total | float) * 100) }}%
  {% else %}Unavailable{% endif %}
```

`states()` returns strings, including `unavailable` or `unknown`, so check `is_number()` before converting a value for calculations. `state_attr()` returns `None` when an attribute or entity is missing. Both holding sensors expose the same holding attributes; this example reads them from the price sensor. Quote and portfolio currencies can differ when a quote is unusable.

## Derived values

Allocation is not a separate sensor. The [example dashboard card](../examples/portfolio-overview.yaml) calculates each holding's allocation as its market value divided by the portfolio total, multiplied by 100. It omits the percentage when either value is unavailable or the total is zero.
