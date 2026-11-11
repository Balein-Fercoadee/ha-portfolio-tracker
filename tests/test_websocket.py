"""Tests for authenticated portfolio management commands."""

from types import SimpleNamespace

from homeassistant.components.websocket_api import ERR_NOT_ALLOWED
import pytest

from custom_components.portfolio_tracker.const import DOMAIN
from custom_components.portfolio_tracker.websocket import (
    websocket_add_holding,
    websocket_get_holdings,
    websocket_remove_holding,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.enable_socket
async def test_websocket_commands_add_and_remove_holdings(
    hass, enable_custom_integrations, hass_ws_client
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={"currency": "USD", "holdings": []},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/get_holdings"})
    assert await client.receive_json() == {
        "id": 1,
        "type": "result",
        "success": True,
        "result": {
            "currency": "USD",
            "scan_interval": 30,
            "min_scan_interval": 10,
            "max_scan_interval": 120,
            "holdings": [],
        },
    }

    await client.send_json_auto_id({"type": f"{DOMAIN}/set_scan_interval", "minutes": 5})
    assert (await client.receive_json())["success"] is False
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_scan_interval", "minutes": 121}
    )
    assert (await client.receive_json())["success"] is False
    assert entry.options == {}

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/set_scan_interval", "minutes": 60}
    )
    saved = await client.receive_json()
    assert saved["success"] is True
    assert saved["result"] == {"scan_interval": 60}
    await hass.async_block_till_done()
    assert entry.options["scan_interval"] == 60

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/add_holding", "symbol": "aapl", "amount": "2.5"}
    )
    result = await client.receive_json()
    assert result["success"] is True
    assert result["result"]["holdings"] == [{"symbol": "AAPL", "quantity": "2.5"}]
    assert entry.options["currency"] == "USD"
    assert entry.options["holdings"] == [{"symbol": "AAPL", "quantity": "2.5"}]

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/add_holding", "symbol": "AAPL", "amount": "1"}
    )
    duplicate = await client.receive_json()
    assert duplicate["success"] is False
    assert duplicate["error"]["code"] == "duplicate_symbol"

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/remove_holding", "symbol": "AAPL"}
    )
    removed = await client.receive_json()
    assert removed["success"] is True
    assert removed["result"] == {
        "currency": "USD",
        "holdings": [],
        "scan_interval": 60,
    }
    assert entry.options["holdings"] == []

    await client.close()
    await hass.async_block_till_done()


async def test_websocket_rejects_invalid_holding(hass, enable_custom_integrations):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={"currency": "USD", "holdings": []},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    class Connection:
        user = SimpleNamespace(is_admin=True)

        def send_error(self, msg_id, code, message):
            self.error = {"id": msg_id, "code": code, "message": message}

        def send_result(self, msg_id, result):
            self.result = result

    connection = Connection()
    websocket_add_holding(
        hass,
        connection,
        {"id": 1, "symbol": "AAPL", "amount": "-1"},
    )

    assert connection.error["code"] == "invalid_quantity"
    assert entry.options == {}


async def test_websocket_commands_require_administrator(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Investment Portfolio",
        unique_id=DOMAIN,
        data={"currency": "USD", "holdings": []},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    class Connection:
        user = SimpleNamespace(is_admin=False)

        def send_error(self, msg_id, code, message):
            self.error = {"id": msg_id, "code": code, "message": message}

        def send_result(self, msg_id, result):
            self.result = result

    connection = Connection()
    websocket_get_holdings(hass, connection, {"id": 1})

    assert connection.error["code"] == ERR_NOT_ALLOWED
    assert not hasattr(connection, "result")

    websocket_add_holding(
        hass,
        connection,
        {"id": 2, "symbol": "AAPL", "amount": "1"},
    )
    assert connection.error["code"] == ERR_NOT_ALLOWED

    websocket_remove_holding(
        hass,
        connection,
        {"id": 3, "symbol": "AAPL"},
    )
    assert connection.error["code"] == ERR_NOT_ALLOWED
    assert entry.options == {}
