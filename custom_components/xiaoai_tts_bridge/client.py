"""MiNA client wrapper for XiaoAI TTS Bridge."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from miservice import MiAccount, MiNAService

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .token_store import ConfigEntryTokenStore


class XiaoAiTtsError(HomeAssistantError):
    """Base XiaoAI TTS Bridge error."""


class XiaoAiAuthenticationError(XiaoAiTtsError):
    """Raised when Xiaomi authentication is no longer valid."""


class XiaoAiDeviceNotFoundError(XiaoAiTtsError):
    """Raised when a configured speaker is no longer available."""


class XiaoAiTtsClient:
    """Manage MiService access for one Xiaomi account."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        reauth_callback: Callable[[], Awaitable[None]],
    ) -> None:
        self._reauth_callback = reauth_callback
        self._session = async_get_clientsession(hass)
        self._token_store = ConfigEntryTokenStore(hass, entry)
        self._account = MiAccount(
            self._session,
            entry.data["username"],
            "",
            self._token_store,
            otp_callback=self._otp_required,
        )
        self._service = MiNAService(self._account)
        self._device_ids: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def _otp_required(self, _method: str) -> str:
        """Reject interactive authentication during normal operation."""
        raise XiaoAiAuthenticationError("Xiaomi account reauthentication required")

    async def async_initialize(self) -> None:
        """Validate authentication and build the device ID mapping."""
        await self.async_refresh_devices(trigger_reauth=False)

    async def async_refresh_devices(self, trigger_reauth: bool = True) -> None:
        """Refresh the MIoT DID to MiNA device ID mapping."""
        try:
            devices = await self._service.device_list()
        except Exception as err:
            if await self._token_store.load_token() is None:
                if trigger_reauth:
                    await self._reauth_callback()
                raise XiaoAiAuthenticationError(
                    "Unable to authenticate with Xiaomi MiNA"
                ) from err
            raise XiaoAiTtsError("Unable to reach Xiaomi MiNA") from err

        if devices is None:
            raise XiaoAiTtsError("Xiaomi MiNA returned no device list")

        self._device_ids = {
            str(device["miotDID"]): str(device["deviceID"])
            for device in devices
            if device.get("miotDID") and device.get("deviceID")
        }

    async def async_speak(self, miot_did: str, text: str) -> None:
        """Send text to one XiaoAI speaker."""
        message = text.strip()
        if not message:
            raise XiaoAiTtsError("TTS message must not be empty")

        async with self._lock:
            device_id = self._device_ids.get(miot_did)
            if device_id is None:
                await self.async_refresh_devices()
                device_id = self._device_ids.get(miot_did)

            if device_id is None:
                raise XiaoAiDeviceNotFoundError(
                    f"XiaoAI speaker not found: miotDID={miot_did}"
                )

            try:
                success = await self._service.text_to_speech(device_id, message)
            except Exception as err:
                if await self._token_store.load_token() is None:
                    await self._reauth_callback()
                    raise XiaoAiAuthenticationError(
                        "Xiaomi account reauthentication required"
                    ) from err
                raise XiaoAiTtsError("Xiaomi MiNA TTS request failed") from err

            if not success:
                raise XiaoAiTtsError("Xiaomi MiNA rejected the TTS request")
