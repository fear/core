"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.

from homeassistant.const import DEVICE_CLASS_BATTERY, PERCENTAGE
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .siro_conn.siro import RadioMotor


# See cover.py for more details.
# Note how both entities for each blind sensor (battery and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""
    bridge = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for device in bridge.get_devices():
        new_devices.append(BatterySensor(device))
    if new_devices:
        async_add_devices(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = True

    def __init__(self, blind: RadioMotor):
        """Initialize the sensor."""
        self._blind = blind
        self._status = self.update()

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._blind.get_mac())}}

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will reflect this.
    @property
    def available(self) -> bool:
        """Return True if blind and hub is available."""
        return self._blind.is_online() and self._blind.get_bridge().is_online()

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        # TODO self._blind.register_callback(self.async_write_ha_state)
        pass

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        # TODO self._blind.remove_callback(self.async_write_ha_state)
        pass

    def update(self) -> dict:
        self._status = self._blind.get_status()
        return self._status


class BatterySensor(SensorBase):
    """Representation of a Sensor."""

    # The class of this device. Note the value should come from the home assistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_BATTERY

    def __init__(self, blind: RadioMotor):
        """Initialize the sensor."""
        super().__init__(blind)
        self._state = self._status['data']['batteryLevel']/10

    # As per the sensor, this must be a unique value within this domain. This is done
    # by using the device ID, and appending "_battery"
    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"{self._blind.get_mac()}_battery"

    # The value of this sensor. As this is a DEVICE_CLASS_BATTERY, this value must be
    # the battery level as a percentage (between 0 and 100)
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._status['data']['batteryLevel']/10

    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    # The same of this entity, as displayed in the entity UI.
    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._blind.get_mac()} Battery"
