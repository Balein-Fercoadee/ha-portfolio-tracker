"""Tests for portfolio configuration and quote parsing."""

from decimal import Decimal

import pytest

from custom_components.portfolio_tracker.models import (
    format_holdings,
    load_holdings,
    parse_holdings,
    parse_quote_response,
    serialize_portfolio,
    calculate_total,
    Holding,
    Quote,
)

def test_parse_holdings_normalizes_symbols_and_quantities():
    holdings = parse_holdings(" aapl, 2.50\nMSFT,3 ", allow_empty=False)

    assert [(holding.symbol, holding.quantity) for holding in holdings] == [
        ("AAPL", Decimal("2.50")),
        ("MSFT", Decimal("3")),
    ]


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ("", "holdings_required"),
        ("AAPL,0", "invalid_quantity"),
        ("AAPL,-1", "invalid_quantity"),
        ("AAPL,nope", "invalid_quantity"),
        ("AAPL,1\n aapl,2", "duplicate_symbol"),
        ("invalid", "invalid_holdings"),
    ],
)
def test_parse_holdings_rejects_invalid_input(value, error):
    with pytest.raises(ValueError, match=error):
        parse_holdings(value, allow_empty=False)


def test_empty_holdings_are_allowed_when_editing():
    assert parse_holdings("", allow_empty=True) == ()


def test_portfolio_settings_round_trip():
    settings = serialize_portfolio(
        "usd",
        "AAPL,2.5\nMSFT,1",
        allow_empty=False,
    )

    assert settings["currency"] == "USD"
    assert load_holdings(settings["holdings"]) == parse_holdings(
        "AAPL,2.5\nMSFT,1",
        allow_empty=False,
    )
    assert format_holdings(settings["holdings"]) == "AAPL,2.5\nMSFT,1"


@pytest.mark.parametrize("price", [None, 0, -1, "NaN", "Infinity", "invalid"])
def test_parse_quote_rejects_unusable_prices(price):
    payload = {"chart": {"result": [{"meta": {"currency": "USD", "regularMarketPrice": price}}]}}

    assert parse_quote_response(payload) is None


def test_parse_quote_rejects_missing_quote():
    assert parse_quote_response({"chart": {"result": None}}) is None


def test_parse_quote_reads_price_currency_and_timestamp():
    quote = parse_quote_response(
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "currency": "usd",
                            "regularMarketPrice": 123.45,
                            "regularMarketTime": 1_700_000_000,
                        }
                    }
                ]
            }
        }
    )

    assert quote is not None
    assert quote.price == Decimal("123.45")
    assert quote.currency == "USD"
    assert quote.timestamp is not None
    assert quote.timestamp.utcoffset().total_seconds() == 0


def test_calculate_total_uses_all_holdings():
    holdings = parse_holdings("AAPL,2\nMSFT,3", allow_empty=False)
    quotes = {
        "AAPL": Quote(Decimal("10"), "USD"),
        "MSFT": Quote(Decimal("5"), "USD"),
    }

    assert calculate_total(holdings, quotes, "USD") == Decimal("35")


@pytest.mark.parametrize(
    ("holdings", "quotes", "currency"),
    [
        ((), {}, "USD"),
        (
            (Holding("AAPL", Decimal("1")),),
            {"AAPL": None},
            "USD",
        ),
        (
            (Holding("AAPL", Decimal("1")),),
            {"AAPL": Quote(Decimal("10"), "EUR")},
            "USD",
        ),
    ],
)
def test_calculate_total_is_unavailable_for_empty_or_incomplete_quotes(
    holdings,
    quotes,
    currency,
):
    assert calculate_total(holdings, quotes, currency) is None
