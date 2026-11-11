"""Portfolio configuration and quote models."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from homeassistant.util import dt as dt_util

from .const import CONF_CURRENCY, CONF_HOLDINGS, CONF_QUANTITY, CONF_SYMBOL

_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.^=-]{1,32}$")


@dataclass(frozen=True)
class Holding:
    """A configured investment holding."""

    symbol: str
    quantity: Decimal


@dataclass(frozen=True)
class Quote:
    """A market quote for one investment."""

    price: Decimal
    currency: str
    timestamp: datetime | None = None


def parse_quote_response(payload: Any) -> Quote | None:
    """Parse a Yahoo Finance chart response into a validated quote."""
    try:
        result = payload["chart"]["result"][0]
        metadata = result["meta"]
        price = Decimal(str(metadata["regularMarketPrice"]))
        currency = validate_currency(metadata["currency"])
        timestamp_value = metadata.get("regularMarketTime")
    except (KeyError, IndexError, TypeError, ValueError, InvalidOperation):
        return None

    if not price.is_finite() or price <= 0:
        return None

    timestamp = None
    if timestamp_value is not None:
        try:
            timestamp = dt_util.utc_from_timestamp(timestamp_value)
        except (OverflowError, OSError, TypeError, ValueError):
            timestamp = None

    return Quote(price=price, currency=currency, timestamp=timestamp)


def validate_currency(currency: Any) -> str:
    """Return a normalized currency code or raise ValueError."""
    if not isinstance(currency, str):
        raise ValueError("invalid_currency")
    normalized = currency.strip().upper()
    if not _CURRENCY_PATTERN.fullmatch(normalized):
        raise ValueError("invalid_currency")
    return normalized


def parse_holdings(value: Any, *, allow_empty: bool) -> tuple[Holding, ...]:
    """Parse lines in SYMBOL,QUANTITY format."""
    if not isinstance(value, str):
        raise ValueError("invalid_holdings")

    holdings: list[Holding] = []
    seen_symbols: set[str] = set()
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 2:
            raise ValueError("invalid_holdings")

        symbol = parts[0].upper()
        if not _SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError("invalid_holdings")
        if symbol in seen_symbols:
            raise ValueError("duplicate_symbol")

        try:
            quantity = Decimal(parts[1])
        except InvalidOperation as err:
            raise ValueError("invalid_quantity") from err
        if not quantity.is_finite() or quantity <= 0:
            raise ValueError("invalid_quantity")

        holdings.append(Holding(symbol, quantity))
        seen_symbols.add(symbol)

    if not holdings and not allow_empty:
        raise ValueError("holdings_required")
    return tuple(holdings)


def serialize_portfolio(currency: Any, holdings: Any, *, allow_empty: bool) -> dict:
    """Validate and serialize portfolio settings for a config entry."""
    normalized_currency = validate_currency(currency)
    parsed_holdings = parse_holdings(holdings, allow_empty=allow_empty)
    return {
        CONF_CURRENCY: normalized_currency,
        CONF_HOLDINGS: [
            {CONF_SYMBOL: holding.symbol, CONF_QUANTITY: str(holding.quantity)}
            for holding in parsed_holdings
        ],
    }


def load_holdings(value: Any) -> tuple[Holding, ...]:
    """Load holdings stored in config entry data or options."""
    if not isinstance(value, list):
        raise ValueError("invalid_holdings")

    lines: list[str] = []
    for holding in value:
        if not isinstance(holding, dict):
            raise ValueError("invalid_holdings")
        symbol = holding.get(CONF_SYMBOL)
        quantity = holding.get(CONF_QUANTITY)
        if not isinstance(symbol, str):
            raise ValueError("invalid_holdings")
        lines.append(f"{symbol},{quantity}")
    return parse_holdings("\n".join(lines), allow_empty=True)


def format_holdings(value: Any) -> str:
    """Format stored holdings for the options form."""
    return "\n".join(
        f"{holding.symbol},{holding.quantity}" for holding in load_holdings(value)
    )


def calculate_total(
    holdings: tuple[Holding, ...],
    quotes: dict[str, Quote | None],
    currency: str,
) -> Decimal | None:
    """Return a complete portfolio total, or None if any quote is unusable."""
    if not holdings:
        return None

    total = Decimal(0)
    for holding in holdings:
        quote = quotes.get(holding.symbol)
        if quote is None or quote.currency != currency:
            return None
        total += quote.price * holding.quantity
    return total
