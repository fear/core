"""The SIRO integration."""
import asyncio
import logging as log

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from siro.siro import Bridge, Helper, RadioMotor
# from .siro.siro import Bridge, Helper, RadioMotor

PLATFORMS = ["cover", "sensor"]


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
    print(entry.data)
    hass.data[DOMAIN][entry.entry_id] = await Helper.bridge_factory(
        key=entry.data['key'],
        bridge_address=entry.data['bridge'],
        loglevel=log.INFO)
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
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
