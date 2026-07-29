"""Notify entities for XiaoAI TTS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import XiaoAiTtsConfigEntry
from .client import XiaoAiTtsClient
from .const import CONF_DEVICES, CONF_HARDWARE, CONF_MIOT_DID, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: XiaoAiTtsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up XiaoAI TTS notify entities."""
    async_add_entities(
        XiaoAiTtsNotifyEntity(entry, entry.runtime_data.client, device)
        for device in entry.data[CONF_DEVICES]
    )


class XiaoAiTtsNotifyEntity(NotifyEntity):
    """A XiaoAI speaker exposed as a notify entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        entry: ConfigEntry,
        client: XiaoAiTtsClient,
        device: dict[str, Any],
    ) -> None:
        miot_did = str(device[CONF_MIOT_DID])
        name = str(device["name"])
        hardware = str(device.get(CONF_HARDWARE) or "XiaoAI Speaker")

        self._client = client
        self._miot_did = miot_did
        self._attr_unique_id = f"{entry.unique_id}_{miot_did}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_{miot_did}")},
            manufacturer="Xiaomi",
            model=hardware,
            name=name,
        )

    async def async_send_message(
        self, message: str, title: str | None = None
    ) -> None:
        """Broadcast text through the speaker."""
        await self._client.async_speak(self._miot_did, message)
