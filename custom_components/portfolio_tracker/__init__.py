"""Home Assistant integration for an investment portfolio."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_CURRENCY, CONF_HOLDINGS, DEFAULT_SCAN_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import PortfolioCoordinator
from .models import load_holdings, validate_currency


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
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
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a portfolio config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
