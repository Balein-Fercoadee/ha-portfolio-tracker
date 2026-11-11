"""Tests for portfolio setup and options flows."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.portfolio_tracker.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_user_flow_creates_portfolio(hass, enable_custom_integrations):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "currency": "usd",
            "holdings": "aapl,2.5\nMSFT,1",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Investment Portfolio"
    assert result["data"] == {
        "currency": "USD",
        "holdings": [
            {"symbol": "AAPL", "quantity": "2.5"},
            {"symbol": "MSFT", "quantity": "1"},
        ],
    }


async def test_user_flow_rejects_invalid_holdings(hass, enable_custom_integrations):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"currency": "USD", "holdings": "AAPL,1\nAAPL,2"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "duplicate_symbol"}


async def test_options_flow_allows_removing_all_holdings(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        data={
            "currency": "USD",
            "holdings": [{"symbol": "AAPL", "quantity": "2"}],
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"currency": "USD", "holdings": ""},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"currency": "USD", "holdings": []}
