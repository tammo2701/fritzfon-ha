"""Call state entity."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    monitor = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FritzFonRingingSensor(monitor, entry)])


class FritzFonRingingSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Incoming call"
    _attr_icon = "mdi:phone-incoming"

    def __init__(self, monitor, entry):
        self.monitor = monitor
        self._attr_unique_id = f"{entry.entry_id}_incoming_call"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="AVM",
            model="FRITZ!Box call monitor",
        )

    async def async_added_to_hass(self):
        self.monitor.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self.monitor.remove_listener(self.async_write_ha_state)

    @property
    def is_on(self):
        return bool(self.monitor.call and self.monitor.call.get("state") == "ringing")

    @property
    def available(self):
        return self.monitor.connected

    @property
    def extra_state_attributes(self):
        return self.monitor.call or {}
