"""MiService token stores for XiaoAI TTS Bridge."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TOKEN

_SERVICE_SID = "micoapi"
_REFRESH_TOKEN_KEYS = ("deviceId", "userId", "passToken")


def _token_after_clear(token: dict[str, Any] | None) -> dict[str, Any] | None:
    """Keep refresh credentials on the first MiService token clear."""
    if not token or _SERVICE_SID not in token:
        return None
    if any(key not in token for key in _REFRESH_TOKEN_KEYS):
        return None
    return {key: deepcopy(token[key]) for key in _REFRESH_TOKEN_KEYS}


class MemoryTokenStore:
    """Keep a MiService token in memory during a config flow."""

    def __init__(self, token: dict[str, Any] | None = None) -> None:
        self._token = deepcopy(token)

    async def load_token(self) -> dict[str, Any] | None:
        """Return the stored token."""
        return deepcopy(self._token)

    async def save_token(self, token: dict[str, Any] | None = None) -> None:
        """Save the token or retain credentials needed for one refresh attempt."""
        self._token = deepcopy(token) if token else _token_after_clear(self._token)

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
        """Save the token or retain credentials needed for one refresh attempt."""
        data = dict(self._entry.data)
        if token:
            data[CONF_TOKEN] = deepcopy(token)
        else:
            refresh_token = _token_after_clear(data.get(CONF_TOKEN))
            if refresh_token:
                data[CONF_TOKEN] = refresh_token
            else:
                data.pop(CONF_TOKEN, None)
        self._hass.config_entries.async_update_entry(self._entry, data=data)
