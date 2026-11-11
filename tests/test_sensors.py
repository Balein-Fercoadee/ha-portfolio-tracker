"""Tests for portfolio sensor values and availability."""

from decimal import Decimal
from types import SimpleNamespace

from custom_components.portfolio_tracker.models import Holding, Quote
from custom_components.portfolio_tracker.sensor import (
    HoldingSensor,
    PortfolioTotalSensor,
)
from custom_components.portfolio_tracker.sensor import async_setup_entry
from homeassistant.helpers import entity_registry as er


def _coordinator(quotes, holdings=None, *, currency="USD", successful=True):
    return SimpleNamespace(
        data=quotes,
        holdings=holdings or (),
        currency=currency,
        last_update_success=successful,
    )


def _entry():
    return SimpleNamespace(entry_id="portfolio-entry")


def test_holding_price_and_value_sensors():
    holding = Holding("AAPL", Decimal("2.5"))
    coordinator = _coordinator({"AAPL": Quote(Decimal("10"), "USD")})

    price_sensor = HoldingSensor(coordinator, _entry(), holding, "price")
    value_sensor = HoldingSensor(coordinator, _entry(), holding, "market_value")

    assert price_sensor.native_value == 10
    assert value_sensor.native_value == 25
    assert value_sensor.extra_state_attributes["quantity"] == "2.5"
    assert value_sensor.extra_state_attributes["currency"] == "USD"
    assert price_sensor.unique_id == "portfolio-entry_aapl_price"


def test_holding_sensors_are_unavailable_for_missing_or_foreign_quote():
    holding = Holding("AAPL", Decimal("1"))
    missing = HoldingSensor(_coordinator({"AAPL": None}), _entry(), holding, "price")
    foreign = HoldingSensor(
        _coordinator({"AAPL": Quote(Decimal("10"), "EUR")}),
        _entry(),
        holding,
        "price",
    )

    assert missing.native_value is None
    assert foreign.native_value is None


def test_total_sensor_requires_every_holding_quote():
    holdings = (
        Holding("AAPL", Decimal("2")),
        Holding("MSFT", Decimal("3")),
    )
    complete = PortfolioTotalSensor(
        _coordinator(
            {
                "AAPL": Quote(Decimal("10"), "USD"),
                "MSFT": Quote(Decimal("5"), "USD"),
            },
            holdings,
        ),
        _entry(),
    )
    incomplete = PortfolioTotalSensor(
        _coordinator(
            {
                "AAPL": Quote(Decimal("10"), "USD"),
                "MSFT": None,
            },
            holdings,
        ),
        _entry(),
    )

    assert complete.native_value == 35
    assert incomplete.native_value is None


def test_empty_portfolio_total_is_unavailable():
    sensor = PortfolioTotalSensor(_coordinator({}, ()), _entry())

    assert sensor.native_value is None
    assert sensor.extra_state_attributes["holding_count"] == 0


def test_coordinator_failure_makes_sensor_unavailable():
    sensor = PortfolioTotalSensor(
        _coordinator(
            {"AAPL": Quote(Decimal("10"), "USD")},
            (Holding("AAPL", Decimal("1")),),
            successful=False,
        ),
        _entry(),
    )

    assert sensor.available is False


async def test_sensor_setup_removes_entities_for_removed_holdings(monkeypatch):
    entry = _entry()
    coordinator = _coordinator(
        {},
        (Holding("MSFT", Decimal("1")),),
    )
    hass = SimpleNamespace(data={"portfolio_tracker": {entry.entry_id: coordinator}})
    old_price = SimpleNamespace(
        config_entry_id=entry.entry_id,
        platform="portfolio_tracker",
        unique_id=f"{entry.entry_id}_aapl_price",
        entity_id="sensor.old_aapl_price",
    )
    old_value = SimpleNamespace(
        config_entry_id=entry.entry_id,
        platform="portfolio_tracker",
        unique_id=f"{entry.entry_id}_aapl_market_value",
        entity_id="sensor.old_aapl_market_value",
    )
    registry = SimpleNamespace(
        entities={old_price.entity_id: old_price, old_value.entity_id: old_value},
        removed=[],
        async_remove=lambda entity_id: registry.removed.append(entity_id),
    )
    added = []
    monkeypatch.setattr(er, "async_get", lambda _hass: registry)

    await async_setup_entry(hass, entry, added.extend)

    assert registry.removed == [
        "sensor.old_aapl_price",
        "sensor.old_aapl_market_value",
    ]
    assert len(added) == 3
