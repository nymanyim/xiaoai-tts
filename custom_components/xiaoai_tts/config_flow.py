"""Config flow for XiaoAI TTS."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

from miservice import MiAccount, MiNAService
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    AUTH_TIMEOUT,
    CONNECT_TIMEOUT,
    CONF_DEVICES,
    CONF_HARDWARE,
    CONF_MIOT_DID,
    CONF_TOKEN,
    DOMAIN,
)
from .token_store import MemoryTokenStore

CONF_OTP = "otp"
CONF_SELECTED_DEVICES = "selected_devices"


class XiaoAiTtsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the XiaoAI TTS configuration flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._username = ""
        self._password = ""
        self._token_store: MemoryTokenStore | None = None
        self._session = None
        self._account: MiAccount | None = None
        self._login_task: asyncio.Task[list[dict[str, Any]]] | None = None
        self._otp_code: asyncio.Future[str] | None = None
        self._otp_requested = asyncio.Event()
        self._otp_method = ""
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect Xiaomi credentials and start authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME].strip()
            self._password = user_input[CONF_PASSWORD]
            result = await self._async_start_login()
            if result == "devices":
                return await self.async_step_devices()
            if result == "otp":
                return await self.async_step_otp()
            errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=self._credentials_schema(self._username),
            errors=errors,
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Submit the OTP to the still-running Xiaomi login session."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if self._otp_code is None or self._login_task is None:
                errors["base"] = "login_expired"
            else:
                self._otp_code.set_result(user_input[CONF_OTP].strip())
                try:
                    self._devices = await asyncio.wait_for(
                        self._login_task, timeout=AUTH_TIMEOUT
                    )
                except TimeoutError:
                    await self._async_cleanup_login()
                    return self.async_abort(reason="login_expired")
                except Exception:
                    await self._async_cleanup_login()
                    return self.async_abort(reason="invalid_auth")
                else:
                    return await self.async_step_devices()

        return self.async_show_form(
            step_id="otp",
            data_schema=vol.Schema(
                {vol.Required(CONF_OTP): TextSelector(TextSelectorConfig())}
            ),
            errors=errors,
            description_placeholders={"method": self._otp_method or "SMS/Email"},
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user select one or more MiNA speakers."""
        available_devices = self._normalized_devices(self._devices)
        if not available_devices:
            await self._async_cleanup_login()
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            selected = set(user_input[CONF_SELECTED_DEVICES])
            devices = [
                device
                for device in available_devices
                if device[CONF_MIOT_DID] in selected
            ]
            if not devices:
                return self.async_show_form(
                    step_id="devices",
                    data_schema=self._devices_schema(available_devices),
                    errors={"base": "no_device_selected"},
                )

            token = self._token_store.token if self._token_store else None
            if not token or not token.get("userId"):
                await self._async_cleanup_login()
                return self.async_abort(reason="invalid_auth")

            user_id = str(token["userId"])
            await self.async_set_unique_id(user_id)

            data = {
                CONF_USERNAME: self._username,
                CONF_TOKEN: token,
                CONF_DEVICES: devices,
            }
            title = f"XiaoAI TTS ({self._username})"

            if self.source == "reauth":
                entry = self._get_reauth_entry()
                self._abort_if_unique_id_mismatch()
                await self._async_cleanup_login()
                return self.async_update_reload_and_abort(
                    entry,
                    title=title,
                    data_updates=data,
                )

            self._abort_if_unique_id_configured()
            await self._async_cleanup_login()
            return self.async_create_entry(title=title, data=data)

        default = None
        if self.source == "reauth":
            default = [
                str(device[CONF_MIOT_DID])
                for device in self._get_reauth_entry().data[CONF_DEVICES]
            ]
        return self.async_show_form(
            step_id="devices",
            data_schema=self._devices_schema(available_devices, default),
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Start Xiaomi account reauthentication."""
        self._username = str(entry_data[CONF_USERNAME])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect credentials for reauthentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME].strip()
            self._password = user_input[CONF_PASSWORD]
            result = await self._async_start_login()
            if result == "devices":
                return await self.async_step_devices()
            if result == "otp":
                return await self.async_step_otp()
            errors["base"] = result

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self._credentials_schema(self._username),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Refresh and change the selected speakers."""
        entry = self._get_reconfigure_entry()
        self._username = str(entry.data[CONF_USERNAME])
        self._password = ""
        self._session = async_get_clientsession(self.hass)
        self._token_store = MemoryTokenStore(entry.data.get(CONF_TOKEN))
        self._account = MiAccount(
            self._session,
            self._username,
            "",
            self._token_store,
            otp_callback=self._otp_callback,
        )
        try:
            self._devices = await MiNAService(self._account).device_list() or []
        except Exception:
            await self._async_cleanup_login()
            return self.async_abort(reason="invalid_auth")

        devices = self._normalized_devices(self._devices)
        if not devices:
            await self._async_cleanup_login()
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            selected = set(user_input[CONF_SELECTED_DEVICES])
            selected_devices = [
                device for device in devices if device[CONF_MIOT_DID] in selected
            ]
            if selected_devices:
                await self._async_cleanup_login()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_DEVICES: selected_devices},
                )

        current = [
            str(device[CONF_MIOT_DID]) for device in entry.data[CONF_DEVICES]
        ]
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._devices_schema(devices, current),
            errors={"base": "no_device_selected"} if user_input is not None else {},
        )

    async def _async_start_login(self) -> str:
        """Start login and wait until OTP is requested or devices are returned."""
        await self._async_cleanup_login()
        self._session = async_get_clientsession(self.hass)
        self._token_store = MemoryTokenStore()
        self._otp_requested = asyncio.Event()
        self._otp_code = self.hass.loop.create_future()
        self._account = MiAccount(
            self._session,
            self._username,
            self._password,
            self._token_store,
            otp_callback=self._otp_callback,
        )
        self._login_task = self.hass.async_create_task(
            self._async_login_and_fetch_devices(),
            "xiaoai_tts_login",
        )

        otp_waiter = self.hass.async_create_task(
            self._otp_requested.wait(),
            "xiaoai_tts_wait_otp",
        )
        done, _ = await asyncio.wait(
            {self._login_task, otp_waiter},
            timeout=CONNECT_TIMEOUT,
            return_when=asyncio.FIRST_COMPLETED,
        )

        if not done:
            otp_waiter.cancel()
            await self._async_cleanup_login()
            return "cannot_connect"

        if self._login_task in done:
            otp_waiter.cancel()
            try:
                self._devices = self._login_task.result()
            except Exception:
                await self._async_cleanup_login()
                return "invalid_auth"
            return "devices"

        return "otp"

    async def _async_login_and_fetch_devices(self) -> list[dict[str, Any]]:
        """Authenticate and return the MiNA device list."""
        if self._account is None:
            raise RuntimeError("Xiaomi account was not initialized")
        devices = await MiNAService(self._account).device_list()
        if devices is None:
            raise RuntimeError("Xiaomi MiNA returned no device list")
        return devices

    async def _otp_callback(self, method: str) -> str:
        """Pause MiService login until the config flow receives an OTP."""
        self._otp_method = method
        self._otp_requested.set()
        if self._otp_code is None:
            raise RuntimeError("OTP future was not initialized")
        return await asyncio.wait_for(self._otp_code, timeout=AUTH_TIMEOUT)

    async def _async_cleanup_login(self) -> None:
        """Cancel unfinished login work."""
        if self._login_task and not self._login_task.done():
            self._login_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._login_task
        self._login_task = None
        self._session = None
        self._account = None
        self._otp_code = None

    async def async_remove(self) -> None:
        """Clean up when Home Assistant removes the flow."""
        await self._async_cleanup_login()

    @staticmethod
    def _credentials_schema(username: str) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=username): TextSelector(
                    TextSelectorConfig()
                ),
                vol.Required(CONF_PASSWORD): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )

    @staticmethod
    def _normalized_devices(devices: list[dict[str, Any]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for device in devices:
            miot_did = device.get("miotDID")
            device_id = device.get("deviceID")
            if miot_did is None or not device_id:
                continue
            normalized.append(
                {
                    CONF_MIOT_DID: str(miot_did),
                    "name": str(
                        device.get("alias") or device.get("name") or "XiaoAI Speaker"
                    ),
                    CONF_HARDWARE: str(device.get("hardware") or "Unknown"),
                }
            )
        return normalized

    @staticmethod
    def _devices_schema(
        devices: list[dict[str, str]], default: list[str] | None = None
    ) -> vol.Schema:
        options = [
            SelectOptionDict(
                value=device[CONF_MIOT_DID],
                label=(
                    f"{device['name']} ({device[CONF_HARDWARE]} / "
                    f"MIoT DID: {device[CONF_MIOT_DID]})"
                ),
            )
            for device in devices
        ]
        field = vol.Required(
            CONF_SELECTED_DEVICES,
            default=default or [device[CONF_MIOT_DID] for device in devices],
        )
        return vol.Schema(
            {
                field: SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
