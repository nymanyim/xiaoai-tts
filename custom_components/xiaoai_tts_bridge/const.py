"""Constants for the XiaoAI TTS Bridge integration."""

from homeassistant.const import Platform

DOMAIN = "xiaoai_tts_bridge"
PLATFORMS = [Platform.NOTIFY]

CONF_DEVICES = "devices"
CONF_HARDWARE = "hardware"
CONF_MIOT_DID = "miot_did"
CONF_TOKEN = "token"

DEFAULT_NAME = "XiaoAI TTS Bridge"
CONNECT_TIMEOUT = 30
AUTH_TIMEOUT = 300
