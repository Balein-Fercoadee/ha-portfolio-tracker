"""Config flow for the investment portfolio integration."""

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_CURRENCY,
    CONF_HOLDINGS,
    DEFAULT_CURRENCY,
    DOMAIN,
)
from .models import serialize_portfolio


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up a portfolio."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Create a portfolio config entry."""
        if user_input is not None:
            try:
                data = serialize_portfolio(
                    user_input.get(CONF_CURRENCY),
                    user_input.get(CONF_HOLDINGS),
                    allow_empty=False,
                )
            except ValueError as err:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._user_schema(),
                    errors={"base": str(err)},
                )
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Investment Portfolio", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=self._user_schema(),
        )

    @staticmethod
    def _user_schema() -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_CURRENCY, default=DEFAULT_CURRENCY): str,
                vol.Required(CONF_HOLDINGS): str,
            }
        )
