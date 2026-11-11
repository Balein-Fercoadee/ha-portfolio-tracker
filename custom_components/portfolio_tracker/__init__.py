"""Home Assistant integration for an investment portfolio."""

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http.server import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import websocket
from .const import (
    CONF_CURRENCY,
    CONF_HOLDINGS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PANEL_ELEMENT,
    PANEL_JS_PATH,
    PANEL_URL,
    PLATFORMS,
)
from .coordinator import PortfolioCoordinator
from .models import load_holdings, validate_currency

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
DEPENDENCIES = ["http", "websocket_api"]
RELOADS = f"{DOMAIN}_reloads"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    websocket.async_register_commands(hass)
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PANEL_JS_PATH,
                str(Path(__file__).parent / "www" / "portfolio-tracker.js"),
                cache_headers=False,
            )
        ]
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a portfolio config entry."""
    settings = entry.options or entry.data
    try:
        currency = validate_currency(settings[CONF_CURRENCY])
        holdings = load_holdings(settings[CONF_HOLDINGS])
    except (KeyError, ValueError) as err:
        raise ConfigEntryNotReady("Invalid portfolio configuration") from err

    coordinator = PortfolioCoordinator(
        hass,
        async_get_clientsession(hass),
        entry,
        holdings,
        currency,
        DEFAULT_SCAN_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not frontend.async_panel_exists(hass, PANEL_URL):
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title="Investment Portfolio",
            sidebar_icon="mdi:chart-line",
            frontend_url_path=PANEL_URL,
            config={
                "_panel_custom": {
                    "name": PANEL_ELEMENT,
                    "js_url": PANEL_JS_PATH,
                    "embed_iframe": False,
                    "trust_external": False,
                }
            },
            require_admin=True,
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a portfolio config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    if entry.entry_id not in hass.data.get(RELOADS, {}):
        frontend.async_remove_panel(hass, PANEL_URL, warn_if_unknown=False)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when its options change."""
    # Concurrent options updates must all finish before panel cleanup.
    reloads = hass.data.setdefault(RELOADS, {})
    reloads[entry.entry_id] = reloads.get(entry.entry_id, 0) + 1
    try:
        await hass.config_entries.async_reload(entry.entry_id)
    finally:
        reloads[entry.entry_id] -= 1
        if not reloads[entry.entry_id]:
            del reloads[entry.entry_id]
            if entry.state not in (
                ConfigEntryState.LOADED,
                ConfigEntryState.FAILED_UNLOAD,
            ):
                frontend.async_remove_panel(hass, PANEL_URL, warn_if_unknown=False)
