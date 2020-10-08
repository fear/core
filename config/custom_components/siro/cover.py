"""Platform for sensor integration."""
# These constants are relevant to the type of entity we are using.
# See below for how they are used.
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
from .siro.const import DEVICE_TYPES  # , CURRENT_STATE
from .siro.siro import RadioMotor
# from siro.const import DEVICE_TYPES  # , CURRENT_STATE
# from siro.siro import RadioMotor

# This function is called as part of the __init__.async_setup_entry (via the
# hass.config_entries.async_forward_entry_setup call)
async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add cover for passed config_entry in HA."""
    # The hub is loaded from the associated hass.data entry that was created in the
    # __init__.async_setup_entry function
    bridge = hass.data[DOMAIN][config_entry.entry_id]

    # The next few lines find all of the entities that will need to be added
    # to HA. Note these are all added to a list, so async_add_devices can be
    # called just once.
    new_devices = []
    for device in bridge.get_devices():
        siro_cover = SiroCover(device)
        new_devices.append(siro_cover)

    # If we have any new devices, add them
    if new_devices:
        async_add_devices(new_devices)


# This entire class could be written to extend a base class to ensure common attributes
# are kept identical/in sync. It's broken apart here between the Cover and Sensors to
# be explicit about what is returned, and the comments outline where the overlap is.
# noinspection PyAbstractClass
class SiroCover(CoverEntity):
    """Representation of a dummy Cover."""

    # Our dummy class is PUSH, so we tell HA that it should not be polled
    should_poll = False
    # The supported features of a cover are done using a bitmask. Using the constants
    # imported above, we can tell HA the features that are supported by this entity.
    # If the supported features were dynamic (ie: different depending on the external
    # device it connected to), then this should be function with an @property decorator.
    supported_features = SUPPORT_SET_POSITION | SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP
    device_class = DEVICE_CLASS_BLIND

    def __init__(self, blind: RadioMotor):
        """Initialize the sensor."""
        # Usual setup is done here. Callbacks are added in async_added_to_hass.
        self._blind = blind
        self._device_status = None
        self._position = None
        self._blind_online = None
        self._bridge_online = None
        self.update()

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Importantly for a push integration, the module that will be getting updates
        # needs to notify HA of changes. The dummy device has a register callback
        # method, so to this we add the 'self.async_write_ha_state' method, to be
        # called where ever there are changes.
        # The call back registration is done once this entity is registered with HA
        # (rather than in the __init__)
        self._blind.register_callback(self._callback)

    def _callback(self, message):
        self.schedule_update_ha_state(force_refresh=True)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._blind.remove_callback(self.schedule_update_ha_state(force_refresh=True))

    # A unique_id for this entity with in this domain. This means for example if you
    # have a sensor on this cover, you must ensure the value returned is unique,
    # which is done here by appending "_cover". For more information, see:
    # https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
    # Note: This is NOT used to generate the user visible Entity ID used in automations.
    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"{self._blind.get_mac()}_cover"

    # Information about the devices that is partially visible in the UI.
    # The most critical thing here is to give this entity a name so it is displayed
    # as a "device" in the HA UI. This name is used on the Devices overview table,
    # and the initial screen when the device is added (rather than the entity name
    # property below). You can then associate other Entities (eg: a battery
    # sensor) with this device, so it shows more like a unified element in the UI.
    # For example, an associated battery sensor will be displayed in the right most
    # column in the Configuration > Devices view for a device.
    # To associate an entity with this device, the device_info must also return an
    # identical "identifiers" attribute, but not return a name attribute.
    # See the sensors.py file for the corresponding example setup.
    # Additional meta data can also be returned here, including sw_version (displayed
    # as Firmware), model and manufacturer (displayed as <model> by <manufacturer>)
    # shown on the device info screen. The Manufacturer and model also have their
    # respective columns on the Devices overview table. Note: Many of these must be
    # set when the device is first added, and they are not always automatically
    # refreshed by HA from it's internal cache.
    # For more information see:
    # https://developers.home-assistant.io/docs/device_registry_index/#device-properties
    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._blind.get_mac())},
            # If desired, the name for the device could be different to the entity
            "name": f"{self._blind.get_mac()}_cover",
            "sw_version": self._blind.get_firmware(),
            "model": DEVICE_TYPES[self._blind.get_devicetype()],
            "manufacturer": "SIRO",
        }

    # This is the name for this *entity*, the "name" attribute from "device_info"
    # is used as the device name for device screens in the UI. This name is used on
    # entity screens, and used to build the Entity ID that's used is automations etc.
    @property
    def name(self):
        """Return the name of the roller."""
        return f"{self._blind.get_mac()}_cover"

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will reflect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._blind_online and self._bridge_online

    # The following properties are how HA knows the current state of the device.
    # These must return a value from memory, not make a live query to the device/hub
    # etc when called (hence they are properties). For a push based integration,
    # HA is notified of changes via the async_write_ha_state call. See the __init__
    # method for hos this is implemented in this example.
    # The properties that are expected for a cover are based on the supported_features
    # property of the object. In the case of a cover, see the following for more
    # details: https://developers.home-assistant.io/docs/core/entity/cover/
    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return 100 - self._position

    @property
    def is_closed(self):
        """Return if the cover is closed, same as position 0."""
        state_open = 23
        return self._position > state_open

    # These methods allow HA to tell the actual device what to do. In this case, move
    # the cover to the desired position, or open and close it all the way.
    def open_cover(self, **kwargs):
        """Open the cover."""
        self._blind.move_up()

    def close_cover(self, **kwargs):
        """Close the cover."""
        self._blind.move_down()

    def set_cover_position(self, **kwargs):
        """Close the cover."""
        position = 100 - kwargs[ATTR_POSITION]
        self._blind.move_to_position(position)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._blind.move_stop()

    def update(self):
        self._device_status = self._blind.get_status()
        self._position = self._blind.get_position()
        self._blind_online = self._blind.is_online()
        self._bridge_online = self._blind.get_bridge().is_online()
