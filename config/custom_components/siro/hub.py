"""A demonstration 'hub' that connects several devices."""
# In a real implementation, this would be in an external library that's on PyPI.
# The PyPI package needs to be included in the `requirements` section of manifest.json
# See https://developers.home-assistant.io/docs/creating_integration_manifest
# for more information.
# This dummy hub always returns 3 siro_blinds.
import asyncio
import random

from .siro_conn.siro import Bridge, RadioMotor, Device

class Hub:
    """Dummy hub for Hello World example."""

    manufacturer = "SIRO"

    def __init__(self, hass, host, siro_bridge: Bridge):
        """Init dummy hub."""
        self._host = host
        self._hass = hass
        self._bridge = siro_bridge
        self._name = host
        self._id = host.lower()

        for device in self._bridge.get_devices():
            SiroBlind(device.get_mac(), device.get_name(), self, device),

        self.online = self._bridge.validate_key()

    @property
    def hub_id(self):
        """ID for dummy hub."""
        return self._id

    async def test_connection(self):
        """Test connectivity to the Dummy hub is OK."""
        self._bridge.
        return True


class SiroBlind:
    """Dummy siro_blind (device for HA) for Hello World example."""

    def __init__(self, siro_blind_id, name, hub, device: Device):
        """Init dummy siro_blind."""
        self._id = siro_blind_id
        self.hub = hub
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._target_position = 100
        self._current_position = 100
        # Reports if the siro_blind is moving up or down.
        # >0 is up, <0 is down. This very much just for demonstration.
        self.moving = 0

        # Some static information about this device
        self.firmware_version = "0.0.{}".format(random.randint(1, 9))
        self.model = "Test Device"

    @property
    def siro_blind_id(self):
        """Return ID for siro_blind."""
        return self._id

    @property
    def position(self):
        """Return position for siro_blind."""
        return self._current_position

    async def set_position(self, position):
        """
        Set dummy cover to the given position.

        State is announced a random number of seconds later.
        """
        self._target_position = position

        # Update the moving status, and broadcast the update
        self.moving = position - 50
        await self.publish_updates()

        self._loop.create_task(self.delayed_update())

    async def delayed_update(self):
        """Publish updates, with a random delay to emulate interaction with device."""
        await asyncio.sleep(random.randint(1, 10))
        self.moving = 0
        await self.publish_updates()

    def register_callback(self, callback):
        """Register callback, called when SiroBlind changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        self._current_position = self._target_position
        for callback in self._callbacks:
            callback()

    @property
    def online(self):
        """SiroBlind is online."""
        # The dummy siro_blind is offline about 10% of the time. Returns True if online,
        # False if offline.
        return True

    @property
    def battery_level(self):
        """Battery level as a percentage."""
        return random.randint(30, 100)

