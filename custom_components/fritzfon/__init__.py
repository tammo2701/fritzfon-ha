"""FRITZ!Box incoming call alerts."""

from __future__ import annotations

from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN, PLATFORMS
from .coordinator import FritzFonCallMonitor

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    from homeassistant.components.http import StaticPathConfig

    card_path = str(Path(__file__).parent / "www" / "fritzfon-card.js")
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/fritzfon/fritzfon-card.js", card_path, True)]
    )
    hass.data.setdefault("frontend_extra_module_url", set()).add("/fritzfon/fritzfon-card.js")
    monitor = FritzFonCallMonitor(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = monitor
    await monitor.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    monitor = hass.data[DOMAIN].pop(entry.entry_id)
    await monitor.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
