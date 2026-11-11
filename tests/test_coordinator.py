"""Tests for coordinated quote refreshes."""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from custom_components.portfolio_tracker.coordinator import PortfolioCoordinator
from custom_components.portfolio_tracker.models import Holding, Quote


async def test_coordinator_fetches_each_configured_holding(monkeypatch):
    holdings = (
        Holding("AAPL", Decimal("2")),
        Holding("MSFT", Decimal("1")),
    )
    get_quote = AsyncMock(
        side_effect=[
            Quote(Decimal("10"), "USD"),
            Quote(Decimal("5"), "USD"),
        ]
    )
    monkeypatch.setattr(
        "custom_components.portfolio_tracker.coordinator.async_get_quote",
        get_quote,
    )
    coordinator = object.__new__(PortfolioCoordinator)
    coordinator.holdings = holdings
    coordinator.session = object()
    coordinator.currency = "USD"

    data = await PortfolioCoordinator._async_update_data(coordinator)

    assert data == {
        "AAPL": Quote(Decimal("10"), "USD"),
        "MSFT": Quote(Decimal("5"), "USD"),
    }
    assert get_quote.await_count == 2


async def test_coordinator_logs_quote_currency_mismatch(monkeypatch, caplog):
    holding = Holding("AAPL", Decimal("1"))
    monkeypatch.setattr(
        "custom_components.portfolio_tracker.coordinator.async_get_quote",
        AsyncMock(return_value=Quote(Decimal("10"), "EUR")),
    )
    coordinator = object.__new__(PortfolioCoordinator)
    coordinator.holdings = (holding,)
    coordinator.session = object()
    coordinator.currency = "USD"

    await PortfolioCoordinator._async_update_data(coordinator)

    assert "Quote for AAPL uses EUR, but the portfolio currency is USD" in caplog.text
