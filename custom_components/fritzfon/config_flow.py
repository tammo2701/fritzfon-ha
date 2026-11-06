"""Config flow for FRITZ!Fon Call Alert."""

from __future__ import annotations

import asyncio
import voluptuous as vol
from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from fritzconnection.lib.fritzphonebook import FritzPhonebook
from requests.exceptions import RequestException

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import DOMAIN


class FritzFonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().removeprefix("http://").removeprefix("https://").rstrip("/")
            host = host.split("/")[0].split(":")[0]
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()
            try:
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, 1012), timeout=4)
                writer.close()
                await writer.wait_closed()
            except (OSError, asyncio.TimeoutError):
                errors["base"] = "call_monitor_unavailable"
            else:
                try:
                    await self.hass.async_add_executor_job(
                        lambda: FritzPhonebook(address=host, user=user_input[CONF_USERNAME],
                                               password=user_input[CONF_PASSWORD]).phonebook_ids
                    )
                except FritzSecurityError:
                    errors["base"] = "insufficient_permissions"
                except FritzConnectionException:
                    errors["base"] = "invalid_auth"
                except (RequestException, OSError, asyncio.TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"FRITZ!Box ({host})",
                        data={**user_input, CONF_HOST: host},
                    )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="fritz.box"): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

