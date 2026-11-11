from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "portfolio_tracker"
PLATFORMS = [Platform.SENSOR]
PANEL_URL = "portfolio-tracker"
PANEL_ELEMENT = "portfolio-tracker-panel"
PANEL_JS_PATH = "/portfolio_tracker/portfolio-tracker.js"

CONF_CURRENCY = "currency"
CONF_HOLDINGS = "holdings"
CONF_SYMBOL = "symbol"
CONF_QUANTITY = "quantity"

DEFAULT_CURRENCY = "USD"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
