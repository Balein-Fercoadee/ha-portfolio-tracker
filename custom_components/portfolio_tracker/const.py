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
CONF_SCAN_INTERVAL = "scan_interval"
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 120
DEFAULT_SCAN_INTERVAL_MINUTES = 30
DEFAULT_SCAN_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
