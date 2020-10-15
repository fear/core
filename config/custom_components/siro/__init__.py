"""The SIRO integration."""
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


import asyncio
import logging as log

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
# from siro.siro import Bridge, Helper, RadioMotor
from .siro.siro import Bridge, Driver, RadioMotor

PLATFORMS = ["cover", "sensor"]


# noinspection PyUnusedLocal
async def async_setup(hass: HomeAssistant, config: dict):
    """
    Set up the SIRO component.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up SIRO from a config entry.
    """
    driver = Driver()
    bridge = await driver.bridge_factory(
        key=entry.data['key'],
        addr=entry.data['bridge'],
        loglevel=log.INFO
    )
    hass.data[DOMAIN][entry.entry_id] = bridge
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """
    Unload a config entry.
    """
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        await hass.data[DOMAIN][entry.entry_id].stop()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
