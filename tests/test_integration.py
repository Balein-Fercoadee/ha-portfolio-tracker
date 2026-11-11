"""Tests for config-entry setup and option updates."""

from decimal import Decimal
from unittest.mock import AsyncMock

from homeassistant.helpers import entity_registry as er

from custom_components.portfolio_tracker.const import DOMAIN
from custom_components.portfolio_tracker.models import Quote
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_and_removing_final_holding_removes_entities(
    hass, enable_custom_integrations, monkeypatch
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

    hass.config_entries.async_update_entry(
        entry,
        options={"currency": "USD", "holdings": []},
    )
    await hass.async_block_till_done()

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
