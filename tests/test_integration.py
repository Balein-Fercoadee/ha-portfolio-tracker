"""Tests for config-entry setup and option updates."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.portfolio_tracker.const import DOMAIN, PANEL_URL
from custom_components.portfolio_tracker.models import Quote
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.enable_socket
async def test_setup_and_removing_final_holding_removes_entities(
    hass, enable_custom_integrations, monkeypatch, hass_ws_client
):
    get_quote = AsyncMock(return_value=Quote(Decimal("10"), "USD"))
    monkeypatch.setattr(
        "custom_components.portfolio_tracker.coordinator.async_get_quote",
        get_quote,
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={
            "currency": "USD",
            "holdings": [{"symbol": "AAPL", "quantity": "2"}],
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert frontend.async_panel_exists(hass, PANEL_URL)
    panel = hass.data[frontend.DATA_PANELS][PANEL_URL]
    assert panel.require_admin
    assert panel.config["_panel_custom"]["name"] == "portfolio-tracker-panel"

    registry = er.async_get(hass)
    holding_entities = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.unique_id.startswith(f"{entry.entry_id}_aapl_")
    ]
    assert len(holding_entities) == 2
    assert get_quote.await_count == 1
    total = next(
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.unique_id == f"{entry.entry_id}_total_value"
    )
    assert hass.states.get(total.entity_id).state == "20.0"

    client = await hass_ws_client(hass)
    script_response = await client.client.get(
        "/portfolio_tracker/portfolio-tracker.js"
    )
    assert script_response.status == 200
    assert "portfolio-tracker-panel" in await script_response.text()
    with patch.object(
        frontend, "async_remove_panel", wraps=frontend.async_remove_panel
    ) as remove_panel:
        await client.send_json_auto_id(
            {"type": f"{DOMAIN}/remove_holding", "symbol": "AAPL"}
        )
        response = await client.receive_json()
        assert response["success"] is True
        await hass.async_block_till_done()
        remove_panel.assert_not_called()

    assert frontend.async_panel_exists(hass, PANEL_URL)
    assert hass.data[frontend.DATA_PANELS][PANEL_URL] is panel
    holding_entities = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.unique_id.startswith(f"{entry.entry_id}_aapl_")
    ]
    assert holding_entities == []
    total = next(
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.unique_id == f"{entry.entry_id}_total_value"
    )
    assert hass.states.get(total.entity_id).state == "unavailable"
    assert get_quote.await_count == 1

    with patch.object(
        frontend, "async_remove_panel", wraps=frontend.async_remove_panel
    ) as remove_panel:
        await client.send_json_auto_id(
            {"type": f"{DOMAIN}/add_holding", "symbol": "AAPL", "amount": "3"}
        )
        response = await client.receive_json()
        assert response["success"] is True
        await hass.async_block_till_done()
        remove_panel.assert_not_called()
    await client.close()

    assert hass.data[frontend.DATA_PANELS][PANEL_URL] is panel
    holding_entities = [
        entity
        for entity in registry.entities.values()
        if entity.config_entry_id == entry.entry_id
        and entity.unique_id.startswith(f"{entry.entry_id}_aapl_")
    ]
    assert len(holding_entities) == 2
    assert hass.states.get(total.entity_id).state == "30.0"
    assert get_quote.await_count == 2


async def test_unloading_entry_removes_panel(
    hass, enable_custom_integrations, monkeypatch
):
    monkeypatch.setattr(
        "custom_components.portfolio_tracker.coordinator.async_get_quote",
        AsyncMock(),
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={"currency": "USD", "holdings": []},
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert frontend.async_panel_exists(hass, PANEL_URL)

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not frontend.async_panel_exists(hass, PANEL_URL)


async def test_failed_options_reload_removes_panel(hass, enable_custom_integrations):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={"currency": "USD", "holdings": []},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    with patch(
        "custom_components.portfolio_tracker.PortfolioCoordinator.async_config_entry_first_refresh",
        new=AsyncMock(side_effect=ConfigEntryNotReady),
    ):
        hass.config_entries.async_update_entry(
            entry, options={"currency": "USD", "holdings": []}
        )
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert not frontend.async_panel_exists(hass, PANEL_URL)
