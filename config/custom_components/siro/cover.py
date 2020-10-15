"""Platform for SIRO cover integration."""
# Modifications copyright (C) 2020 Felix Arnold
# based on @sillyfrog's "detailed_hello_world_push": https://git.io/JTeqd

__author__ = "Felix Arnold (@fear)"
__copyright__ = "Copyright (c) 2020 Felix Arnold"
__credits__ = ["@sillyfrog", "Paulus Schoutsen (@balloob)",
               "everybody working on home assistant", "everybody helping others"]
__license__ = "Apache-2.0"
__version__ = "0.4"
__maintainer__ = "Felix Arnold (@fear)"
__email__ = "hello@felix-arnold.dev"
__status__ = "Beta"
__topic__ = "Home Automation"


from homeassistant.components.cover import (
    ATTR_POSITION,
    DEVICE_CLASS_BLIND,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)

from .const import DOMAIN
from siro.const import DEVICE_TYPES, CURRENT_STATE
from siro.siro import RadioMotor


async def async_setup_entry(hass, config_entry, async_add_devices):
    """
    Add cover for passed config_entry in HA.
    """
    bridge = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for device in bridge.devices:
        siro_cover = SiroCover(device)
        new_devices.append(siro_cover)
    if new_devices:
        async_add_devices(new_devices)


# noinspection PyAbstractClass
class SiroCover(CoverEntity):
    """
    Representation of a dummy Cover.
    """

    should_poll = False
    supported_features = SUPPORT_SET_POSITION | SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP
    device_class = DEVICE_CLASS_BLIND

    def __init__(self, blind: RadioMotor):
        """
        Initialize the sensor.
        """
        self._blind = blind
        self._device_status = None
        self._position = None
        self._blind_online = None
        self._bridge_online = None
        self._movement_state = None
        self.update()

    async def async_added_to_hass(self):
        """
        Run when this Entity has been added to HA.
        """
        self._blind.register_callback(self._callback)

    def _callback(self):
        """
        Method which is called when hass got notified.
        """
        self.schedule_update_ha_state(force_refresh=True)

    async def async_will_remove_from_hass(self):
        """
        Entity being removed from hass.
        """
        self._blind.remove_callback(self._callback)

    @property
    def unique_id(self):
        """
        Return Unique ID string.
        """
        return f"{self._blind.mac}_cover"

    @property
    def device_info(self):
        """
        Information about this device.
        """
        return {
            "identifiers": {(DOMAIN, self._blind.mac)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
            "sw_version": self._blind.firmware,
            "model": DEVICE_TYPES[self._blind.devicetype],
            "manufacturer": "SIRO",
        }

    @property
    def name(self):
        """
        Return the name of the roller.
        """
        return self.unique_id

    @property
    def available(self) -> bool:
        """
        Return True if roller and hub is available.
        """
        return self._blind_online and self._bridge_online

    @property
    def current_cover_position(self):
        """
        Return the current position of the cover.
        """
        return 100 - self._position

    @property
    def is_closed(self):
        """
        Return if the cover is closed. When the cover ist 23 out it will show closed.
        """
        state_open = 23
        return self._position > state_open

    @property
    def is_closing(self):
        """
        Return if the cover is closing or not.
        """
        return self._movement_state == CURRENT_STATE['State']['CLOSING']

    @property
    def is_opening(self):
        """
        Return if the cover is opening or not.
        """
        return self._movement_state == CURRENT_STATE['State']['OPENING']

    def open_cover(self, **kwargs):
        """
        Open the cover.
        """
        self._blind.move_up()

    def close_cover(self, **kwargs):
        """
        Close the cover.
        """
        self._blind.move_down()

    def set_cover_position(self, **kwargs):
        """
        Set the cover to the given position.
        """
        position = 100 - kwargs[ATTR_POSITION]
        self._blind.move_to_position(position)

    def stop_cover(self, **kwargs):
        """
        Stop the cover.
        """
        self._blind.move_stop()

    def update(self):
        """
        Called when there are updates.
        """
        self._device_status = self._blind.status
        self._position = self._blind.position
        self._blind_online = self._blind.is_online
        self._movement_state = self._blind.movement_state
        self._bridge_online = self._blind.bridge.is_online
