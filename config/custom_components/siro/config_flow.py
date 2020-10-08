"""Config flow for Hello World integration."""


import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from .const import DOMAIN
# from siro.siro import Bridge, Helper
# from .siro.siro import Bridge, Helper

_LOGGER = logging.getLogger(__name__)
DATA_SCHEMA = {
    vol.Required("title", description="name of the integration", default="SIRO Bridge"): str,
    vol.Required("key", description="Connector+ account key"): str,
    vol.Optional("bridge", description="IP of the SIRO bridge", default=""): str
}


async def validate_input(hass: core.HomeAssistant, data: dict):
    """
    Validate the user input allows us to connect.
    """

    if len(data["key"]) != 16:
        raise InvalidKey

    # if not Helper.bridge_factory('30b9217c-6d18-4d').validate_key():
    #     raise CannotConnect

    return {
        "title": data["title"],
        "key": data["key"],
        "bridge": data["bridge"]
    }


class SiroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle a config flow for SIRO.
    """
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """
        Handle the initial step.
        """
        errors = {}
        if user_input is not None:
            # noinspection PyBroadException
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=info)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["title"] = "cannot_connect"
            except InvalidKey:
                errors["title"] = "wrong_key"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(DATA_SCHEMA), errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class InvalidKey(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
