"""Config flow for Hello World integration."""
# Modifications copyright (C) 2020 Felix Arnold
# based on @sillyfrog's "detailed_hello_world_push": https://git.io/JTeqd

__author__ = "Felix Arnold (@fear)"
__copyright__ = "Copyright (c) 2020 Felix Arnold"
__credits__ = ["@sillyfrog", "Paulus Schoutsen (@balloob)",
               "everybody working on home assistant", "everybody helping others"]
__license__ = "Apache-2.0"
__version__ = "0.3"
__maintainer__ = "Felix Arnold (@fear)"
__email__ = "hello@felix-arnold.dev"
__status__ = "Beta"
__topic__ = "Home Automation"


import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from .const import DOMAIN
# from .siro.siro import Driver
from siro.siro import Driver

_LOGGER = logging.getLogger(__name__)
DATA_SCHEMA = {
    vol.Required("title", description="name of the integration", default="my Bridge"): str,
    vol.Required("key", description="Connector+ account key"): str,
    vol.Optional("bridge", description="IP of the SIRO bridge", default=""): str
}


# noinspection PyUnusedLocal
async def validate_input(hass: core.HomeAssistant, data: dict):
    """
    Validate the user input allows us to connect.
    """
    valid_data = data

    if len(data["key"]) != 16:
        raise InvalidKey

    if data["bridge"] == '':
        try:
            valid_data["bridge"] = Driver.find_bridge()
        except UserWarning:
            raise CannotConnect

    if not Driver.check_key(data["key"], valid_data["bridge"]):
        raise InvalidKey

    return valid_data


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


class InvalidKey(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
