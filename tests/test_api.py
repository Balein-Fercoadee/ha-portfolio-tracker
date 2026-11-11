"""Tests for Yahoo Finance quote retrieval."""

from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

import aiohttp
import pytest

from custom_components.portfolio_tracker.api import async_get_quote
from custom_components.portfolio_tracker.models import Quote


def _response(payload, *, error=None):
    response = MagicMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    response.raise_for_status.side_effect = error
    response.json = AsyncMock(return_value=payload)
    return response


async def test_get_quote_parses_valid_response():
    response = _response(
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "currency": "USD",
                            "regularMarketPrice": 123.45,
                            "regularMarketTime": 1_700_000_000,
                        }
                    }
                ]
            }
        }
    )
    session = MagicMock()
    session.get.return_value = response

    quote = await async_get_quote(session, "AAPL")

    assert quote == Quote(
        price=Decimal("123.45"),
        currency="USD",
        timestamp=quote.timestamp,
    )
    assert quote.timestamp is not None
    session.get.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"chart": {"result": None}},
        {"chart": {"result": [{"meta": {"currency": "USD"}}]}},
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "currency": "USD",
                            "regularMarketPrice": "not-a-price",
                        }
                    }
                ]
            }
        },
    ],
)
async def test_get_quote_returns_none_for_missing_or_malformed_response(payload):
    session = MagicMock()
    session.get.return_value = _response(payload)

    assert await async_get_quote(session, "AAPL") is None


async def test_get_quote_preserves_foreign_currency_for_validation():
    session = MagicMock()
    session.get.return_value = _response(
        {
            "chart": {
                "result": [
                    {"meta": {"currency": "EUR", "regularMarketPrice": 25}}
                ]
            }
        }
    )

    quote = await async_get_quote(session, "AAPL")

    assert quote == Quote(price=Decimal("25"), currency="EUR")


async def test_get_quote_handles_http_errors():
    session = MagicMock()
    session.get.return_value = _response(
        {},
        error=aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=503,
        ),
    )

    assert await async_get_quote(session, "AAPL") is None
