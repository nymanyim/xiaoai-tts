"""MiService token stores for XiaoAI TTS Bridge."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN


class MemoryTokenStore:
    """Keep a MiService token in memory during a config flow."""

    def __init__(self, token: dict[str, Any] | None = None) -> None:
        self._token = deepcopy(token)

    async def load_token(self) -> dict[str, Any] | None:
        """Return the stored token."""
        return deepcopy(self._token)

    async def save_token(self, token: dict[str, Any] | None = None) -> None:
        """Save or clear the token."""
        self._token = deepcopy(token)

    @property
    def token(self) -> dict[str, Any] | None:
        """Return a copy of the current token."""
        return deepcopy(self._token)


class ConfigEntryTokenStore:
    """Persist a MiService token in a Home Assistant config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry

    async def load_token(self) -> dict[str, Any] | None:
        """Load the token from the config entry."""
        token = self._entry.data.get(CONF_TOKEN)
        return deepcopy(token) if token else None

    async def save_token(self, token: dict[str, Any] | None = None) -> None:
        """Save or clear the token in the config entry."""
        data = dict(self._entry.data)
        if token:
            data[CONF_TOKEN] = deepcopy(token)
        else:
            data.pop(CONF_TOKEN, None)
        self._hass.config_entries.async_update_entry(self._entry, data=data)
