"""Asynchronous access to Yahoo Finance chart quotes."""

import logging
from urllib.parse import quote

import aiohttp

from .models import Quote, parse_quote_response

_LOGGER = logging.getLogger(__name__)
_YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


async def async_get_quote(
    session: aiohttp.ClientSession, symbol: str
) -> Quote | None:
    """Fetch and validate the latest available quote for a symbol."""
    url = _YAHOO_CHART_URL.format(symbol=quote(symbol, safe=""))
    try:
        async with session.get(
            url,
            params={"range": "1d", "interval": "1d"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        _LOGGER.warning("Unable to retrieve Yahoo Finance quote for %s: %s", symbol, err)
        return None

    quote_data = parse_quote_response(payload)
    if quote_data is None:
        _LOGGER.warning("Yahoo Finance returned no usable quote for %s", symbol)
    return quote_data
