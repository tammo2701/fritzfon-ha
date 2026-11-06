"""FRITZ!Box call monitor TCP client."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime

from homeassistant.core import HomeAssistant

from .const import EVENT_CALL

_LOGGER = logging.getLogger(__name__)


class FritzFonCallMonitor:
    def __init__(self, hass: HomeAssistant, host: str, username: str, password: str) -> None:
        self.hass = hass
        self.host = host
        self.username = username
        self.password = password
        self.phonebook = None
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.task: asyncio.Task | None = None
        self.connected = False
        self.call: dict | None = None
        self._listeners = []
        self._stopped = False

    async def async_start(self) -> None:
        from fritzconnection.lib.fritzphonebook import FritzPhonebook

        self.phonebook = FritzPhonebook(address=self.host, user=self.username, password=self.password)
        def load_phonebook():
            ids = self.phonebook.phonebook_ids
            if ids:
                self.phonebook.get_all_name_numbers(ids[0])

        await self.hass.async_add_executor_job(load_phonebook)
        self._phone_numbers = {}
        for contact in self.phonebook.phonebook.contacts:
            for number in contact.numbers:
                self._phone_numbers[self._normalize(number)] = contact.name
        self.task = self.hass.async_create_task(self._run())

    @staticmethod
    def _normalize(number: str) -> str:
        return re.sub(r"\D", "", number)

    def _name_for_number(self, number: str) -> str | None:
        if not number or not self.phonebook:
            return None
        normalized = self._normalize(number)
        name = self._phone_numbers.get(normalized)
        if name:
            return name
        # FRITZ!Box may send national format while the phonebook uses +country code.
        return next((value for key, value in self._phone_numbers.items() if key.endswith(normalized.lstrip("0"))), None)

    async def async_stop(self) -> None:
        self._stopped = True
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self._close()

    def _close(self) -> None:
        self.connected = False
        if self.writer:
            self.writer.close()
            self.writer = None

    async def _run(self) -> None:
        delay = 2
        while not self._stopped:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host, 1012)
                self.connected = True
                delay = 2
                while line := await self.reader.readline():
                    self._handle_line(line.decode("utf-8", errors="replace").strip())
                raise ConnectionError("FRITZ!Box call monitor disconnected")
            except asyncio.CancelledError:
                raise
            except (OSError, ConnectionError, asyncio.TimeoutError) as err:
                self.connected = False
                _LOGGER.warning("Call monitor connection failed (%s); retrying", err)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 60)
            finally:
                self._close()

    def _handle_line(self, line: str) -> None:
        fields = line.split(";")
        if len(fields) < 5:
            return
        kind, _timestamp, connection_id = fields[:3]
        if kind == "RING":
            if len(fields) < 5:
                return
            self.call = {"state": "ringing", "call_id": connection_id,
                         "from": fields[3], "to": fields[4]}
            self.call["from_name"] = self._name_for_number(fields[3])
            self._emit("ringing")
        elif kind == "CALL":
            if len(fields) < 6:
                return
            extension = fields[3]
            self.call = {"state": "dialing", "call_id": connection_id, "extension": extension,
                         "from": fields[4], "to": fields[5]}
            self._emit("dialing")
        elif kind == "CONNECT" and len(fields) >= 5 and self.call and self.call.get("call_id") == connection_id:
            self.call["state"] = "talking"
            self._emit("talking")
        elif kind == "DISCONNECT" and self.call and self.call.get("call_id") == connection_id:
            self.call["state"] = "idle"
            self._emit("idle")
            self.call = None

    def _emit(self, state: str) -> None:
        assert self.call is not None
        payload = {**self.call, "state": state, "host": self.host,
                   "timestamp": datetime.now().astimezone().isoformat()}
        self.hass.loop.call_soon_threadsafe(
            self.hass.bus.async_fire, EVENT_CALL, payload
        )
        for callback in tuple(self._listeners):
            self.hass.loop.call_soon_threadsafe(callback)

    def add_listener(self, callback) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)
