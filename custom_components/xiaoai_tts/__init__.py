"""XiaoAI TTS integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry, ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.core import HomeAssistant

from .client import XiaoAiAuthenticationError, XiaoAiTtsClient, XiaoAiTtsError
from .const import DOMAIN, PLATFORMS


@dataclass
class XiaoAiTtsRuntimeData:
    """Runtime data for a XiaoAI TTS config entry."""

    client: XiaoAiTtsClient


type XiaoAiTtsConfigEntry = ConfigEntry[XiaoAiTtsRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant, entry: XiaoAiTtsConfigEntry
) -> bool:
    """Set up XiaoAI TTS from a config entry."""

    async def start_reauth() -> None:
        entry.async_start_reauth(hass)

    client = XiaoAiTtsClient(hass, entry, start_reauth)
    try:
        await client.async_initialize()
    except XiaoAiAuthenticationError as err:
        raise ConfigEntryAuthFailed from err
    except XiaoAiTtsError as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = XiaoAiTtsRuntimeData(client)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: XiaoAiTtsConfigEntry
) -> bool:
    """Unload a XiaoAI TTS config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
