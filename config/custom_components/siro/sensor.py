"""Platform for SIRO sensor integration."""
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


from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE, DEVICE_CLASS_SIGNAL_STRENGTH
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
# from siro.siro import RadioMotor
from .siro.siro import RadioMotor


async def async_setup_entry(hass, config_entry, async_add_devices):
    """
    Add sensors for passed config_entry in HA.
    """
    bridge = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for device in bridge.devices:
        new_devices.append(BatterySensor(device))
        new_devices.append(RSSISensor(device))
    if new_devices:
        async_add_devices(new_devices)


class _SensorBase(Entity):
    """
    Base representation of a Hello World Sensor.
    """
    should_poll = False

    def __init__(self, blind: RadioMotor):
        """
        Initialize the sensor.
        """
        self._blind = blind
        self._status = self.update()

    @property
    def device_info(self):
        """
        Return information to link this entity with the correct device.
        """
        return {"identifiers": {(DOMAIN, self._blind.mac)}}

    @property
    def available(self) -> bool:
        """
        Return True if blind and hub is available.
        """
        return self._blind.is_online and self._blind.bridge.is_online

    async def async_added_to_hass(self):
        """
        Run when this Entity has been added to HA.
        """
        self._blind.register_callback(self._callback)

    def _callback(self):
        """
        Is called when hass got the notification for an update
        """
        self.schedule_update_ha_state(force_refresh=True)

    async def async_will_remove_from_hass(self):
        """
        Entity being removed from hass.
        """
        self._blind.remove_callback(self._callback)

    def update(self) -> None:
        print('update...')
        self._status = self._blind.status


class BatterySensor(_SensorBase):
    """
    Representation of a Sensor.
    """

    device_class = DEVICE_CLASS_BATTERY

    def __init__(self, blind: RadioMotor):
        """
        Initialize the sensor.
        """
        super().__init__(blind)
        self._battery = None
        self._name = None

        self.update()

    def update(self) -> dict:
        """
        Called when there are updates.
        """
        self._status = self._blind.status
        self._battery = self.battery_level
        self._name = self.name
        return self._status

    @property
    def battery_level(self) -> float:
        """
        Function for setting the battery level.
        """
        if self._status:
            self._blind.logger.debug(self._status)
            return float(self._status['data']['batteryLevel'])/10

    @property
    def unique_id(self):
        """
        Return Unique ID string.
        """
        return f"{self._blind.mac}_battery"

    @property
    def state(self):
        """
        Return the state of the sensor.
        """
        return self._battery

    @property
    def unit_of_measurement(self):
        """
        Return the unit of measurement.
        """
        return PERCENTAGE

    @property
    def name(self):
        """
        Return the name of the sensor.
        """
        return f"{self._blind.mac}_battery"


class RSSISensor(_SensorBase):
    """
    Representation of a Sensor.
    """
    device_class = DEVICE_CLASS_SIGNAL_STRENGTH
    DECIBEL = "dB"

    def __init__(self, blind: RadioMotor):
        """
        Initialize the sensor.
        """
        super().__init__(blind)
        self._status = None
        self._name = None
        self._rssi = None
        self.update()

    def update(self):
        """
        Called when there are updates.
        """
        self._status = self._blind.status
        self._name = f"{self._blind.mac}_rssi"
        self._rssi = self.rssi

    @property
    def rssi(self) -> int:
        """
        Reading the RSSI state.
        """
        if self._status:
            return int(self._status['data']['RSSI'])
        else:
            return 0

    @property
    def unique_id(self):
        """
        Return Unique ID string.
        """
        return self._name

    @property
    def name(self):
        """
        Return the name of the sensor.
        """
        return self._name

    @property
    def state(self):
        """
        Return the state of the sensor.
        """
        return self._rssi

    @property
    def unit_of_measurement(self):
        """
        Return the unit of measurement.
        """
        return self.DECIBEL
