"""Portfolio data update coordinator."""

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import async_get_quote
from .models import Holding, Quote

_LOGGER = logging.getLogger(__name__)


class PortfolioCoordinator(DataUpdateCoordinator[dict[str, Quote | None]]):
    """Fetch quotes for all configured portfolio holdings."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        entry: ConfigEntry,
        holdings: tuple[Holding, ...],
        currency: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the portfolio coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="investment portfolio",
            update_interval=update_interval,
        )
        self.session = session
        self.holdings = holdings
        self.currency = currency

    async def _async_update_data(self) -> dict[str, Quote | None]:
        """Retrieve the latest quote for every configured holding."""
        quotes = await asyncio.gather(
            *(async_get_quote(self.session, holding.symbol) for holding in self.holdings)
        )
        for holding, quote in zip(self.holdings, quotes, strict=True):
            if quote is not None and quote.currency != self.currency:
                _LOGGER.warning(
                    "Quote for %s uses %s, but the portfolio currency is %s",
                    holding.symbol,
                    quote.currency,
                    self.currency,
                )
        return {
            holding.symbol: quote
            for holding, quote in zip(self.holdings, quotes, strict=True)
        }
