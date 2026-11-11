"""Authenticated WebSocket commands for portfolio management."""

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CURRENCY,
    CONF_HOLDINGS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .models import load_holdings, serialize_portfolio


def async_register_commands(hass: HomeAssistant) -> None:
    """Register portfolio management commands."""
    websocket_api.async_register_command(hass, websocket_get_holdings)
    websocket_api.async_register_command(hass, websocket_add_holding)
    websocket_api.async_register_command(hass, websocket_remove_holding)
    websocket_api.async_register_command(hass, websocket_set_scan_interval)


def _with_interval(updated: dict, settings) -> dict:
    """Carry an existing update frequency over to rewritten options."""
    if CONF_SCAN_INTERVAL in settings:
        updated[CONF_SCAN_INTERVAL] = settings[CONF_SCAN_INTERVAL]
    return updated


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_scan_interval",
        vol.Required("minutes"): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
        ),
    }
)
def websocket_set_scan_interval(hass, connection, msg):
    """Persist the update frequency, in minutes."""
    if not _is_admin(connection, msg):
        return
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return

    settings = entry.options or entry.data
    updated = {**settings, CONF_SCAN_INTERVAL: msg["minutes"]}
    hass.config_entries.async_update_entry(entry, options=updated)
    connection.send_result(msg["id"], {CONF_SCAN_INTERVAL: msg["minutes"]})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/get_holdings"}
)
def websocket_get_holdings(hass, connection, msg):
    """Return the configured portfolio to an administrator."""
    if not _is_admin(connection, msg):
        return
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return
    settings = entry.options or entry.data
    connection.send_result(
        msg["id"],
        {
            CONF_CURRENCY: settings[CONF_CURRENCY],
            CONF_SCAN_INTERVAL: settings.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
            ),
            "min_scan_interval": MIN_SCAN_INTERVAL,
            "max_scan_interval": MAX_SCAN_INTERVAL,
            CONF_HOLDINGS: [
                {"symbol": holding.symbol, "quantity": str(holding.quantity)}
                for holding in load_holdings(settings[CONF_HOLDINGS])
            ],
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add_holding",
        vol.Required("symbol"): cv.string,
        vol.Required("amount"): cv.string,
    }
)
def websocket_add_holding(hass, connection, msg):
    """Validate and persist a new holding."""
    if not _is_admin(connection, msg):
        return
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return

    settings = entry.options or entry.data
    try:
        current_holdings = load_holdings(settings[CONF_HOLDINGS])
        lines = [
            f"{holding.symbol},{holding.quantity}" for holding in current_holdings
        ]
        lines.append(f"{msg['symbol']},{msg['amount']}")
        updated = serialize_portfolio(
            settings[CONF_CURRENCY],
            "\n".join(lines),
            allow_empty=False,
        )
    except ValueError as err:
        _send_validation_error(connection, msg, err)
        return

    updated = _with_interval(updated, settings)
    hass.config_entries.async_update_entry(entry, options=updated)
    connection.send_result(msg["id"], updated)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/remove_holding",
        vol.Required("symbol"): cv.string,
    }
)
def websocket_remove_holding(hass, connection, msg):
    """Remove and persist a configured holding."""
    if not _is_admin(connection, msg):
        return
    entry = _get_entry(hass, connection, msg)
    if entry is None:
        return

    settings = entry.options or entry.data
    try:
        current_holdings = load_holdings(settings[CONF_HOLDINGS])
        symbol = msg["symbol"].strip().upper()
        if not any(holding.symbol == symbol for holding in current_holdings):
            connection.send_error(
                msg["id"],
                websocket_api.ERR_NOT_FOUND,
                "Holding not found",
            )
            return
        remaining = "\n".join(
            f"{holding.symbol},{holding.quantity}"
            for holding in current_holdings
            if holding.symbol != symbol
        )
        updated = serialize_portfolio(
            settings[CONF_CURRENCY],
            remaining,
            allow_empty=True,
        )
    except ValueError as err:
        _send_validation_error(connection, msg, err)
        return

    updated = _with_interval(updated, settings)
    hass.config_entries.async_update_entry(entry, options=updated)
    connection.send_result(msg["id"], updated)


def _is_admin(connection, msg) -> bool:
    """Ensure portfolio commands are limited to administrators."""
    if connection.user is not None and connection.user.is_admin:
        return True
    connection.send_error(
        msg["id"],
        websocket_api.ERR_NOT_ALLOWED,
        "Administrator access required",
    )
    return False


def _get_entry(hass, connection, msg):
    """Return the configured portfolio entry or report it missing."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if entries:
        return entries[0]
    connection.send_error(
        msg["id"],
        websocket_api.ERR_NOT_FOUND,
        "Portfolio is not configured",
    )
    return None


def _send_validation_error(connection, msg, err: ValueError) -> None:
    """Return a user-visible validation error."""
    code = str(err)
    connection.send_error(
        msg["id"],
        code,
        code.replace("_", " "),
    )
